# 多机器环境下 operation.py 使用说明

## 概述

在多机器环境下，您需要按照以下步骤来使用 `operation.py` 进行自动化测试：

1. **在测试控制机器上运行 `test_communicator.py`**（作为测试服务器）
2. **在被测试机器上运行 `tested_communicator.py`**（作为客户端）
3. **使用 `operation_multi_machine.py`** 进行跨机器的自动化操作

## 环境准备

### 1. 网络配置

确保所有机器都在同一个网络中，并且可以相互通信：

```bash
# 在测试控制机器上检查网络
ping <被测试机器IP>

# 在被测试机器上检查网络
ping <测试控制机器IP>
```

### 2. 端口配置

- **测试服务器端口**: 8889（`test_communicator.py`）
- **被测试机器端口**: 8888（`tested_communicator.py`）

确保这些端口没有被防火墙阻止。

## 启动步骤

### 步骤 1: 启动测试服务器

在您的测试控制机器上运行：

```bash
# 进入 communicators 目录
cd communicators

# 启动测试服务器
python test_communicator.py
```

或者直接使用 Python 代码：

```python
from test_communicator import TestMachineCommunicator

# 创建测试服务器
server = TestMachineCommunicator(server_host="0.0.0.0", server_port=8889)

# 启动服务器
server.start_server()

# 保持运行
try:
    while True:
        import time
        time.sleep(1)
        # 显示状态
        machines = server.get_connected_machines()
        apps = server.get_registered_apps()
        print(f"已连接机器: {len(machines)}, 已注册应用: {len(apps)}")
except KeyboardInterrupt:
    server.stop_server()
```

### 步骤 2: 启动被测试机器

在每台被测试机器上运行：

```bash
# 进入 communicators 目录
cd communicators

# 启动被测试机器服务
python tested_communicator.py
```

或者直接使用 Python 代码：

```python
from tested_communicator import TestedMachineCommunicator

# 创建被测试机器实例
client = TestedMachineCommunicator(
    bind_port=8888,
    test_server_host="192.168.1.100",  # 测试控制机器的IP地址
    test_server_port=8889,
    machine_id="machine_001"  # 每台机器使用唯一的ID
)

# 启动服务，指定要监控的应用
client.start(app_names=["calculator", "gedit", "firefox"])

# 或者监控所有应用
# client.start()
```

### 步骤 3: 使用多机器操作类

现在您可以使用 `MultiMachineOperation` 类进行跨机器的自动化操作：

```python
from operation_multi_machine import MultiMachineOperation

# 创建多机器操作实例
operation = MultiMachineOperation(
    test_server_host="192.168.1.100",  # 测试控制机器的IP地址
    test_server_port=8889
)

try:
    # 查看可用的机器
    machines = operation.get_available_machines()
    print(f"可用机器: {machines}")
    
    # 查看可用的应用
    apps = operation.get_available_apps()
    print(f"可用应用: {apps}")
    
    # 设置操作目标（机器和应用）
    if operation.set_target("machine_001", "calculator"):
        print("成功设置目标: 机器 machine_001, 应用 calculator")
        
        # 执行操作
        operation.click_element("菜单/文件/新建")
        operation.input_text("输入框", "测试文本")
        operation.hotkey(["Ctrl", "s"])
        
        # 导出操作记录
        operation.export_to_json("operations.json")
        
    else:
        print("设置目标失败")
        
except Exception as e:
    print(f"操作过程中发生错误: {str(e)}")
finally:
    operation.close()
```

## 完整使用示例

### 示例 1: 多机器协作测试

```python
from operation_multi_machine import MultiMachineOperation
import time

# 创建操作实例
operation = MultiMachineOperation("192.168.1.100", 8889)

try:
    # 在机器1上操作计算器
    if operation.set_target("machine_001", "calculator"):
        print("在机器1上操作计算器...")
        operation.click_element("按钮/1")
        operation.click_element("按钮/+")
        operation.click_element("按钮/2")
        operation.click_element("按钮/=")
        
        # 获取结果截图
        screenshot = operation.get_screenshot()
        print(f"计算器结果截图: {screenshot}")
    
    # 切换到机器2上的文本编辑器
    if operation.set_target("machine_002", "gedit"):
        print("在机器2上操作文本编辑器...")
        operation.click_element("菜单/文件/新建")
        operation.input_text("文本区域", "这是从机器1计算器测试的结果")
        operation.hotkey(["Ctrl", "s"])
        
        # 同步事件
        operation.sync_event("test_completed", {
            "test_type": "multi_machine_collaboration",
            "result": "success"
        })
    
    # 导出所有操作记录
    operation.export_to_json("multi_machine_test.json")
    
except Exception as e:
    print(f"测试过程中发生错误: {str(e)}")
finally:
    operation.close()
```

### 示例 2: 批量操作多台机器

```python
from operation_multi_machine import MultiMachineOperation

def batch_test_on_machines():
    """在多台机器上批量执行测试"""
    operation = MultiMachineOperation("192.168.1.100", 8889)
    
    try:
        # 获取所有可用机器
        machines = operation.get_available_machines()
        print(f"发现 {len(machines)} 台机器: {machines}")
        
        # 在每台机器上执行相同的测试
        for machine_id in machines:
            print(f"\n开始在机器 {machine_id} 上执行测试...")
            
            # 获取该机器上的应用
            apps = operation.get_available_apps(machine_id)
            
            for app in apps:
                app_name = app["app_name"]
                print(f"  测试应用: {app_name}")
                
                if operation.set_target(machine_id, app_name):
                    try:
                        # 执行基本测试
                        operation.move_to(100, 100)
                        operation.click_element("主窗口")
                        
                        # 获取截图
                        screenshot = operation.get_screenshot()
                        print(f"    截图获取成功: {screenshot['data']['size']} 字节")
                        
                    except Exception as e:
                        print(f"    应用 {app_name} 测试失败: {str(e)}")
                else:
                    print(f"    无法设置目标: {machine_id}:{app_name}")
        
        # 导出测试结果
        operation.export_to_json(f"batch_test_{int(time.time())}.json")
        print("\n批量测试完成，结果已导出")
        
    except Exception as e:
        print(f"批量测试失败: {str(e)}")
    finally:
        operation.close()

# 执行批量测试
if __name__ == "__main__":
    batch_test_on_machines()
```

### 示例 3: 事件驱动的测试

```python
from operation_multi_machine import MultiMachineOperation
import time

def event_driven_test():
    """事件驱动的测试"""
    operation = MultiMachineOperation("192.168.1.100", 8889)
    
    try:
        # 订阅事件
        operation.subscribe_events()
        print("已订阅事件通知")
        
        # 设置目标
        if operation.set_target("machine_001", "calculator"):
            print("开始事件驱动测试...")
            
            # 执行操作并同步事件
            operation.click_element("按钮/1")
            operation.sync_event("button_clicked", {
                "button": "1",
                "timestamp": time.time()
            })
            
            operation.click_element("按钮/+")
            operation.sync_event("button_clicked", {
                "button": "+",
                "timestamp": time.time()
            })
            
            operation.click_element("按钮/2")
            operation.sync_event("button_clicked", {
                "button": "2",
                "timestamp": time.time()
            })
            
            operation.click_element("按钮/=")
            operation.sync_event("calculation_completed", {
                "expression": "1+2",
                "result": "3",
                "timestamp": time.time()
            })
            
            print("事件驱动测试完成")
        
        # 取消订阅
        operation.unsubscribe_events()
        
    except Exception as e:
        print(f"事件驱动测试失败: {str(e)}")
    finally:
        operation.close()

# 执行事件驱动测试
if __name__ == "__main__":
    event_driven_test()
```

## 故障排除

### 常见问题

1. **连接失败**
   ```bash
   # 检查网络连接
   ping <目标机器IP>
   
   # 检查端口是否开放
   telnet <目标机器IP> <端口号>
   ```

2. **应用未找到**
   ```python
   # 检查应用是否已启动
   apps = operation.get_available_apps()
   print(f"可用应用: {apps}")
   
   # 检查特定机器上的应用
   machine_apps = operation.get_available_apps("machine_001")
   print(f"机器1上的应用: {machine_apps}")
   ```

3. **操作执行失败**
   ```python
   # 检查目标是否设置
   if operation.current_machine_id and operation.current_app_name:
       print(f"当前目标: {operation.current_machine_id}:{operation.current_app_name}")
   else:
       print("请先设置目标机器和应用")
   ```

### 调试模式

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 创建操作实例
operation = MultiMachineOperation("192.168.1.100", 8889)

# 查看连接状态
machines = operation.get_available_machines()
apps = operation.get_available_apps()
print(f"调试信息: 机器={machines}, 应用={apps}")
```

## 性能优化建议

### 1. 批量操作

```python
# 批量设置多个目标
targets = [
    ("machine_001", "calculator"),
    ("machine_002", "gedit"),
    ("machine_003", "firefox")
]

for machine_id, app_name in targets:
    if operation.set_target(machine_id, app_name):
        # 执行操作
        operation.click_element("主窗口")
        operation.get_screenshot()
```

### 2. 异步操作

```python
import threading

def operate_on_machine(machine_id, app_name):
    """在指定机器上执行操作"""
    op = MultiMachineOperation("192.168.1.100", 8889)
    try:
        if op.set_target(machine_id, app_name):
            op.click_element("主窗口")
            op.get_screenshot()
    finally:
        op.close()

# 并发执行
threads = []
for machine_id in ["machine_001", "machine_002", "machine_003"]:
    thread = threading.Thread(target=operate_on_machine, args=(machine_id, "calculator"))
    threads.append(thread)
    thread.start()

# 等待所有线程完成
for thread in threads:
    thread.join()
```

## 总结

通过以上步骤，您可以在多机器环境下使用 `operation.py` 进行自动化测试：

1. **启动测试服务器** - 管理多机器连接
2. **启动被测试机器** - 提供应用访问能力
3. **使用多机器操作类** - 执行跨机器的自动化操作

这种架构支持：
- 多机器并行测试
- 跨机器协作测试
- 事件同步和状态监控
- 灵活的测试脚本编写

如果您在使用过程中遇到问题，请参考故障排除部分或查看日志输出。
