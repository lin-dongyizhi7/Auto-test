# 多机器通信系统使用说明

## 概述

本系统是对原有 `test_communicator.py` 和 `tested_communicator.py` 的改造升级，支持：

1. **多机器连接**：测试服务器可以同时连接多台被测试机器
2. **多应用通信**：每台机器可以运行多个应用，支持独立通信
3. **事件同步**：多台机器之间可以通过测试服务器进行事件同步
4. **向后兼容**：保持原有单机器通信的API兼容性

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   测试服务器     │    │   被测试机器1    │    │   被测试机器2    │
│  (8889端口)     │◄──►│   (8888端口)    │    │   (8888端口)    │
│                 │    │                 │    │                 │
│ - 机器管理      │    │ - 应用管理      │    │ - 应用管理      │
│ - 应用注册      │    │ - 元素查询      │    │ - 元素查询      │
│ - 事件同步      │    │ - 截图获取      │    │ - 截图获取      │
│ - 请求转发      │    │ - 命令执行      │    │ - 命令执行      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 文件说明

### 核心文件

- **`test_communicator.py`**：测试服务器，管理多机器连接和事件同步
- **`tested_communicator.py`**：被测试机器客户端，支持多应用通信
- **`config.py`**：系统配置文件
- **`multi_machine_example.py`**：使用示例脚本

### 兼容性

- **`TestMachineCommunicator`**：新的多机器通信类（默认）
- **`SingleMachineCommunicator`**：保持向后兼容的单机器通信类

## 使用方法

### 1. 启动测试服务器

```bash
# 在测试控制机器上运行
python multi_machine_example.py server
```

或者直接使用Python代码：

```python
from test_communicator import TestMachineCommunicator

# 创建测试服务器
server = TestMachineCommunicator(server_host="0.0.0.0", server_port=8889)

# 启动服务器
server.start_server()

# 保持运行
try:
    while True:
        time.sleep(1)
        # 显示状态
        machines = server.get_connected_machines()
        apps = server.get_registered_apps()
        print(f"已连接机器: {len(machines)}, 已注册应用: {len(apps)}")
except KeyboardInterrupt:
    server.stop_server()
```

### 2. 启动被测试机器

```bash
# 在被测试机器上运行
python multi_machine_example.py client machine_001
```

或者直接使用Python代码：

```python
from tested_communicator import TestedMachineCommunicator

# 创建被测试机器实例
client = TestedMachineCommunicator(
    bind_port=8888,
    test_server_host="192.168.1.100",  # 测试服务器地址
    test_server_port=8889,
    machine_id="machine_001"
)

# 启动服务，指定要监控的应用
client.start(app_names=["calculator", "gedit"])

# 或者监控所有应用
# client.start()
```

### 3. 与多机器通信

```python
from test_communicator import SingleMachineCommunicator

# 连接到测试服务器
connector = SingleMachineCommunicator("192.168.1.100", 8889)

# 获取机器列表
response = connector._send_request("get_machines", {})
if response.get("success"):
    machines = response["data"]["machines"]
    print(f"找到 {len(machines)} 台机器")

# 获取应用列表
response = connector._send_request("get_apps", {})
if response.get("success"):
    apps = response["data"]["apps"]
    print(f"找到 {len(apps)} 个应用")

# 与特定机器上的应用通信
machine_id = "machine_001"
app_name = "calculator"

# 获取应用窗口区域
response = connector._send_request("get_app_region", {
    "machine_id": machine_id,
    "app_name": app_name
})

# 获取截图
response = connector._send_request("get_screenshot", {
    "machine_id": machine_id,
    "app_name": app_name
})

# 执行命令
commands = [
    {"action": "mouse_click", "params": {"x": 100, "y": 100}},
    {"action": "key_press", "params": {"key": "enter"}}
]
response = connector._send_request("exec_commands", {
    "machine_id": machine_id,
    "app_name": app_name,
    "commands": commands
})
```

## 事件同步

### 事件类型

系统支持以下事件类型：

- `machine_connected`：机器连接
- `machine_disconnected`：机器断开
- `app_launched`：应用启动
- `app_closed`：应用关闭
- `command_executed`：命令执行
- `screenshot_taken`：截图获取
- `element_found`：元素查找
- `error_occurred`：错误发生

### 订阅事件

```python
# 订阅事件通知
response = connector._send_request("subscribe_events", {})

# 取消订阅
response = connector._send_request("unsubscribe_events", {})
```

### 事件同步

```python
# 同步事件到服务器
event_data = {
    "type": "sync_event",
    "data": {
        "type": "command_executed",
        "app_name": "calculator",
        "data": {"command": "click", "result": "success"}
    }
}
response = connector._send_request("sync_event", event_data)
```

## 配置管理

### 环境配置

```python
from config import get_config

# 获取开发环境配置
dev_config = get_config("development")

# 获取生产环境配置
prod_config = get_config("production")

# 获取测试环境配置
test_config = get_config("testing")
```

### 自定义配置

```python
# 修改网络配置
from config import NETWORK_CONFIG
NETWORK_CONFIG["test_server"]["port"] = 9999

# 修改应用配置
from config import APP_CONFIG
APP_CONFIG["default_apps"].append("new_app")
```

## 高级功能

### 1. 应用注册管理

```python
# 动态注册应用
response = connector._send_request("register_app", {
    "app_name": "new_app",
    "app_info": {"version": "1.0", "type": "desktop"}
})

# 注销应用
response = connector._send_request("unregister_app", {
    "app_name": "new_app"
})
```

### 2. 批量操作

```python
# 批量获取多台机器的截图
for machine_id in machines:
    response = connector._send_request("get_screenshot", {
        "machine_id": machine_id,
        "app_name": "calculator"
    })
    # 处理响应...

# 批量执行命令
for machine_id in machines:
    response = connector._send_request("exec_commands", {
        "machine_id": machine_id,
        "app_name": "calculator",
        "commands": commands
    })
    # 处理响应...
```

### 3. 状态监控

```python
# 获取系统状态
machines = server.get_connected_machines()
apps = server.get_registered_apps()
events = server.get_event_history(limit=100)

print(f"系统状态:")
print(f"  已连接机器: {len(machines)}")
print(f"  已注册应用: {len(apps)}")
print(f"  事件历史: {len(events)}")
```

## 故障排除

### 常见问题

1. **连接失败**
   - 检查网络连接
   - 确认端口未被占用
   - 检查防火墙设置

2. **应用未找到**
   - 确认应用已启动
   - 检查应用名称是否正确
   - 确认dogtail支持该应用

3. **事件同步失败**
   - 检查测试服务器连接
   - 确认事件订阅状态
   - 查看错误日志

### 调试模式

```python
# 启用调试模式
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看详细日志
server = TestMachineCommunicator(server_host="0.0.0.0", server_port=8889)
server.start_server()
```

## 性能优化

### 1. 缓存优化

```python
# 调整缓存容量
client = TestedMachineCommunicator(
    cache_capacity=100,  # 增加缓存容量
    # ... 其他参数
)
```

### 2. 连接池

```python
# 使用连接池管理多个连接
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = []
    for machine_id in machines:
        future = executor.submit(communicate_with_machine, machine_id)
        futures.append(future)
    
    # 等待所有操作完成
    for future in futures:
        result = future.result()
```

### 3. 异步操作

```python
import asyncio

async def async_communicate():
    # 异步执行多个操作
    tasks = []
    for machine_id in machines:
        task = asyncio.create_task(communicate_with_machine_async(machine_id))
        tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks)
    return results
```

## 安全考虑

### 1. 网络安全

- 使用防火墙限制端口访问
- 配置允许的主机列表
- 启用SSL/TLS加密（如需要）

### 2. 认证授权

```python
# 启用认证（在config.py中配置）
SECURITY_CONFIG["enable_auth"] = True
SECURITY_CONFIG["allowed_hosts"] = ["192.168.1.0/24"]
```

### 3. 速率限制

```python
# 配置速率限制
SECURITY_CONFIG["rate_limit"] = 50  # 每分钟最多50个请求
```

## 扩展开发

### 1. 添加新事件类型

```python
# 在EventType枚举中添加新类型
class EventType(Enum):
    # ... 现有类型 ...
    CUSTOM_EVENT = "custom_event"

# 在事件处理中添加新逻辑
def _handle_custom_event(self, machine_id: str, request: Dict) -> Dict:
    # 处理自定义事件
    pass
```

### 2. 添加新通信协议

```python
# 扩展通信协议
def _handle_new_protocol(self, machine_id: str, request: Dict) -> Dict:
    # 实现新的通信协议
    pass
```

### 3. 集成第三方系统

```python
# 集成监控系统
def integrate_with_monitoring(self):
    # 发送指标到监控系统
    pass

# 集成日志系统
def integrate_with_logging(self):
    # 发送日志到日志系统
    pass
```

## 总结

改造后的多机器通信系统提供了：

1. **强大的扩展性**：支持任意数量的机器和应用
2. **灵活的事件系统**：实现机器间的事件同步
3. **完整的向后兼容**：保持原有API的使用方式
4. **丰富的配置选项**：支持不同环境的配置需求
5. **完善的错误处理**：提供详细的错误信息和调试支持

通过这个系统，您可以轻松构建复杂的多机器自动化测试环境，实现跨机器的测试协调和事件同步。
