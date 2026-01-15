import os
import json
import base64
from typing import Any, Dict, Optional

try:
    # cryptography 是常见依赖，用于 AES-GCM 对称加密
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    _CRYPTO_AVAILABLE = True
except Exception:
    _CRYPTO_AVAILABLE = False


def _derive_key_from_secret(secret: str, salt: bytes) -> bytes:
    """
    由共享口令派生 32 字节 AES 密钥。注意：为最小改动示例，此处使用固定长度 PBKDF2。
    生产环境建议使用设备唯一盐值并安全分发。
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
        backend=default_backend(),
    )
    return kdf.derive(secret.encode("utf-8"))


def is_crypto_available() -> bool:
    return _CRYPTO_AVAILABLE


def encrypt_payload(payload: Dict[str, Any], secret: str) -> Dict[str, Any]:
    """加密字典负载，返回加密信封（可 JSON 序列化）。"""
    if not _CRYPTO_AVAILABLE:
        # 回退：不加密，打上标记
        return {"enc": "none", "data": payload}

    # 固定盐值用于示例（最小侵入）。可改为通过环境变量注入。
    salt = b"AutoTestSalt_v1\x00\x01"
    key = _derive_key_from_secret(secret, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    plaintext = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return {
        "enc": "aes-gcm",
        "n": base64.b64encode(nonce).decode("ascii"),
        "c": base64.b64encode(ciphertext).decode("ascii"),
    }


def decrypt_envelope(envelope: Dict[str, Any], secret: str) -> Optional[Dict[str, Any]]:
    """解密加密信封，返回字典负载；若不可解密返回 None。"""
    enc_type = envelope.get("enc")
    if enc_type == "none":
        return envelope.get("data")
    if enc_type != "aes-gcm":
        return None

    if not _CRYPTO_AVAILABLE:
        return None

    salt = b"AutoTestSalt_v1\x00\x01"
    key = _derive_key_from_secret(secret, salt)
    aesgcm = AESGCM(key)
    try:
        nonce = base64.b64decode(envelope.get("n", ""))
        ciphertext = base64.b64decode(envelope.get("c", ""))
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(plaintext.decode("utf-8"))
    except Exception:
        return None


def wrap_outgoing(obj: Dict[str, Any], enable_encryption: bool, secret: Optional[str]) -> bytes:
    """将对象序列化；若启用加密则加密后再序列化为 JSON bytes。"""
    if enable_encryption and secret:
        envelope = encrypt_payload(obj, secret)
        data = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
        return data
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def unwrap_incoming(data_bytes: bytes, enable_encryption: bool, secret: Optional[str]) -> Dict[str, Any]:
    """解析接收数据。兼容明文与加密信封。"""
    text = data_bytes.decode("utf-8")
    obj = json.loads(text)
    if not isinstance(obj, dict):
        return obj
    if not enable_encryption:
        # 兼容对端已加密但本端未开启的情况：尝试解密
        if obj.get("enc"):
            if secret:
                decrypted = decrypt_envelope(obj, secret)
                if decrypted is not None:
                    return decrypted
        return obj
    # 启用了加密：若是信封则解密，否则按明文兼容
    if obj.get("enc"):
        decrypted = decrypt_envelope(obj, secret or "")
        if decrypted is not None:
            return decrypted
    return obj


