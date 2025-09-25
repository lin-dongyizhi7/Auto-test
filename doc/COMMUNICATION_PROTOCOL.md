# 通信协议规范（测试中心 ↔ 被测机）

本文档定义测试中心（Test Server）与被测机（Agent）之间的通信协议，涵盖传输层、消息通用结构、握手注册、保活、操作执行、事件与日志、安全与错误等。

## 1. 传输层与编码

- 传输: TCP 长连接，默认端口 8888
  - 测试中心作为服务端监听 8888
  - 被测机也可本地监听，用于测试中心主动连接
- 编码: JSON（UTF-8）
- 加密/签名（可选）: 由配置项 `enable_encryption` 与 `shared_secret` 控制。
  - 发送使用 `wrap_outgoing(payload, enable, secret)`
  - 接收使用 `unwrap_incoming(bytes, enable, secret)`，失败回退到明文 JSON。

## 2. 通用消息结构

所有消息均应尽量遵循以下结构：

```json
{
  "type": "message_type",          // 必填，消息类型
  "request_id": "uuid-...",        // 请求唯一ID；响应需回传同值（事件/心跳可省略）
  "flag": "response",              // 仅响应消息携带；用于快速判别响应
  "timestamp": 1732451000.12,       // 可选，发送时刻（秒）
  "source": "machine_001",         // 可选，发送方标识
  "success": true,                  // 响应与流程确认类消息建议携带
  "data": { /* 载荷，根据类型定义 */ },
  "error": "错误信息（失败时）"
}
```

约定：

- 请求方负责生成 `request_id` 并等待匹配响应；响应必须包含同一 `request_id` 与 `flag: "response"`。
- 历史兼容路径可不带 `request_id`/`flag`，但新实现应遵循该约定。

## 3. 握手与注册

时序：

1. 测试中心 → 被测机：连接校验 `connection_check`
2. 被测机 → 测试中心：连接确认 `connection_response`
3. 被测机 → 测试中心：机器注册 `machine_registration`
4. 测试中心 → 被测机：注册响应 `machine_registration_response`

消息定义：

- connection_check（测试中心→被测机）
  - type: `connection_check`
  - data: `{ server_id, host, port, nonce }`

- connection_response（被测机→测试中心）
  - type: `connection_response`
  - success: true|false
  - data: `{ message }` 或 error

- machine_registration（被测机→测试中心）
  - type: `machine_registration`
  - data: `{ machine_id, machine_info }`
  - `machine_info`: `{ host, port, platform, timestamp, server_id }`

- machine_registration_response（测试中心→被测机）
  - type: `machine_registration_response`
  - success: true|false
  - data: `{ message }` 或 error

## 4. 保活与会话管理

- 心跳（被测机→测试中心）
  - type: `heartbeat`
  - data: `{ machine_id, metrics?, uptime?, ts }`
- 测试中心维护 `last_seen/last_heartbeat`，超时标记离线并清理会话。

## 5. 应用注册/同步

- 被测机上报或更新可控应用：
  - type: `app_registration`
  - data: `{ machine_id, app_name, app_info }`

## 6. 操作请求与响应

用于元素点击、输入、等待、截图、脚本执行等。

请求（测试中心→被测机）：

- 公共：`type`, `request_id`, `timestamp`, `data`
- `data` 至少包含：`machine_id`, `app_name`, 以及具体操作参数。

响应（被测机→测试中心）：

- 公共：`type`（与请求同名或统一 `operation_response`）、`flag: "response"`, `request_id`, `timestamp`, `success`, `data|error`

常见类型示例：

- `element_click`, `element_input`, `element_wait`, `get_screenshot`, `run_steps`, `run_script`

示例：点击请求/响应

```json
// request
{
  "type": "element_click",
  "request_id": "req-9d2f",
  "timestamp": 1732451000.12,
  "data": {
    "machine_id": "machine_001",
    "app_name": "calculator",
    "selector": {"by": "text", "value": "7"},
    "options": {"timeout_ms": 5000}
  }
}

// response
{
  "type": "element_click",
  "flag": "response",
  "request_id": "req-9d2f",
  "timestamp": 1732451000.36,
  "success": true,
  "data": { "elapsed_ms": 122 }
}
```

批量步骤/脚本：

- `run_steps`：`data: { machine_id, app_name, steps: [ {type, data}, ... ] }`
- `run_script`：`data` 与脚本 JSON 结构一致（Python 脚本在测试中心解析为 JSON 后再下发）。

## 7. 事件与日志

- 异步事件（被测机→测试中心）
  - type: `event_sync`
  - data: `{ event_type, payload, machine_id, app_id?, occurred_at }`
- 日志同步（被测机→测试中心）
  - type: `log_sync`
  - data: `{ level, message, source, machine_id, ts }`

## 8. 错误与重试

错误响应：

- `success: false`
- `error`: 简明描述
- `data`: 可选 `{ code, detail }`

建议错误码：

- `E_BAD_REQUEST`, `E_NOT_FOUND`, `E_TIMEOUT`, `E_BUSY`, `E_INTERNAL`, `E_UNAVAILABLE`

超时重试：请求侧对每个 `request_id` 设定超时时间与重试策略（次数/退避）。

## 9. 安全

- 开启通道加密/签名：`enable_encryption`, `shared_secret`
- 来源白名单：被测机仅接受来自指定服务器地址与端口的连接

## 10. 版本与向后兼容

- 在 `data` 中可携带 `protocol_version` 用于演进（如 `"1.0.0"`）
- 响应在不破坏字段的前提下可增加可选字段；新增消息类型不影响旧类型处理

## 11. 示例时序

1) 连接：Server → Agent `connection_check` → Agent `connection_response(success)`
2) 注册：Agent → Server `machine_registration` → Server `machine_registration_response(success)`
3) 操作：Server → Agent `element_click(request_id)` → Agent → Server 响应（同 `request_id`）
4) 心跳：Agent → Server `heartbeat`（周期性）
