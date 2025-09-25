"""
通信协议常量与基础校验工具

提供：
- 消息类型常量
- 基础校验函数（最小化依赖、与现有实现解耦）
"""

from typing import Dict, Any, Optional


# 协议版本
PROTOCOL_VERSION: str = "1.0.0"


# 消息类型
class MessageTypes:
    # 握手/注册
    # 兼容现有实现采用的命名
    CONNECTION_REQUEST = "connection_request"
    CONNECTION_RESPONSE = "connection_response"
    MACHINE_REGISTRATION = "machine_registration"
    MACHINE_REGISTRATION_RESPONSE = "machine_registration_response"

    # 会话/保活
    HEARTBEAT = "heartbeat"
    DISCONNECT_NOTICE = "disconnect_notice"

    # 应用管理
    # 现有实现使用 register_app
    APP_REGISTRATION = "app_registration"
    REGISTER_APP = "register_app"
    APP_LIST_SYNC = "app_list_sync"
    APP_STATUS_UPDATE = "app_status_update"

    # 操作执行
    ELEMENT_CLICK = "element_click"
    ELEMENT_INPUT = "element_input"
    ELEMENT_WAIT = "element_wait"
    GET_SCREENSHOT = "get_screenshot"
    GET_ELEMENT = "get_element"
    EXEC_COMMANDS = "exec_commands"
    RUN_STEPS = "run_steps"
    RUN_SCRIPT = "run_script"
    DISCONNECT = "disconnect"
    SUBSCRIBE_EVENTS = "subscribe_events"
    UNSUBSCRIBE_EVENTS = "unsubscribe_events"

    # 事件/日志
    EVENT_SYNC = "event_sync"
    EVENT_NOTIFICATION = "event_notification"
    LOG_SYNC = "log_sync"


def is_response_message(msg: Dict[str, Any]) -> bool:
    """判断消息是否为响应类消息"""
    if not isinstance(msg, dict):
        return False
    return msg.get("flag") == "response"


def get_request_id(msg: Dict[str, Any]) -> Optional[str]:
    """提取请求ID（若存在）"""
    if not isinstance(msg, dict):
        return None
    rid = msg.get("request_id")
    return rid if isinstance(rid, str) and len(rid) > 0 else None


def basic_validate_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """最小化校验：检查基础字段合法性。

    返回：{ success, error? }
    """
    if not isinstance(msg, dict):
        return {"success": False, "error": "消息必须为对象"}

    msg_type = msg.get("type")
    if not isinstance(msg_type, str) or not msg_type:
        return {"success": False, "error": "缺少或非法的type"}

    # 对响应类消息，必须回传 request_id
    if is_response_message(msg):
        rid = get_request_id(msg)
        if not rid:
            return {"success": False, "error": "响应缺少request_id"}

    return {"success": True}


__all__ = [
    "PROTOCOL_VERSION",
    "MessageTypes",
    "is_response_message",
    "get_request_id",
    "basic_validate_message",
]


