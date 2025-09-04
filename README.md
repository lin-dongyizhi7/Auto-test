# 多机器多应用自动化测试系统

## 项目概述

这是一个支持多机器多应用连接的自动化测试系统，包含前端图形化界面和后端API服务。系统通过前端页面进行图形化操作和配置，后端接收API请求并调用 `operation_multi_machine.py` 中的函数与测试服务器建立连接，支持同时管理多台被测试机器和多个应用程序的自动化操作。

## 被测试机器实现详解

### 架构设计

被测试机器端采用分层架构设计，实现了职责分离和代码复用：

```
┌─────────────────────────────────────────────────────────────┐
│                TestedMachineCommunicator                    │
│                     (通信层)                                │
├─────────────────────────────────────────────────────────────┤
│                MachineOperator                              │
│                   (操作层)                                  │
├─────────────────────────────────────────────────────────────┤
│              Dogtail + PyAutoGUI                           │
│                   (底层库)                                  │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. TestedMachineCommunicator (通信层)

**职责**: 网络通信、连接管理、事件同步

**主要功能**:

- 监听8888端口，接收测试服务器连接
- 处理HTTP请求和响应
- 管理测试服务器连接状态
- 事件同步和日志记录
- 交互式配置和管理界面

**关键特性**:

- 被动连接模式：等待测试服务器主动连接
- 连接验证：验证测试服务器身份和权限
- 事件队列：本地UI事件队列供可视化界面消费
- 线程安全：使用锁机制保证并发安全

#### 2. MachineOperator (操作层)

**职责**: 在被测试机器上执行具体操作

**主要功能**:

- 元素获取和查询
- 屏幕截图
- 指令执行
- 应用管理
- 预加载功能

**核心方法**:

```python
class MachineOperator:
    def get_element(self, app_name: str, element_path: str, role_name_list: Optional[List[Optional[str]]] = None) -> Dict:
        """查询应用元素信息，支持LRU缓存"""
  
    def get_screenshot(self, app_name: str, region: Optional[List[int]] = None) -> str:
        """截取屏幕，返回16进制编码"""
  
    def execute_commands(self, app_name: str, commands: List[Dict]) -> Dict:
        """执行指令集（鼠标、键盘操作）"""
  
    def register_app(self, app_name: str, app_info: Dict = None) -> bool:
        """注册应用"""
  
    def preload_components_for_app(self, app_name: str) -> Dict:
        """预加载常用组件到缓存"""
```

#### 3. LRUCache (缓存层)

**职责**: 元素查询结果缓存，提升性能

**特性**:

- LRU (Least Recently Used) 算法
- 可配置缓存容量
- 自动清理过期元素
- 父子级缓存优化

### 重构优势

#### 1. 职责分离

- **通信层**: 专注于网络通信和连接管理
- **操作层**: 专注于机器操作和自动化执行
- **缓存层**: 专注于性能优化

#### 2. 代码复用

- `MachineOperator` 可独立使用
- 机器操作逻辑与通信逻辑解耦
- 支持多种使用场景

#### 3. 维护性提升

- 修改机器操作只需在 `MachineOperator` 中进行
- 修改通信逻辑只需在 `TestedMachineCommunicator` 中进行
- 清晰的模块边界

#### 4. 测试友好

- 可独立测试机器操作功能
- 可独立测试通信功能
- 支持单元测试和集成测试

### 使用方式

#### 原有使用方式（向后兼容）

```python
# 创建通信器实例
communicator = TestedMachineCommunicator()

# 注册应用
communicator.register_app("my_app")

# 获取元素
result = communicator._get_element("my_app", "菜单/文件")

# 执行指令
commands = [{"action": "mouse_click", "params": {"x": 100, "y": 200}}]
result = communicator._execute_commands("my_app", commands)
```

#### 新的独立使用方式

```python
# 直接使用机器操作器
from machine_operator import MachineOperator

operator = MachineOperator()
operator.register_app("my_app")
result = operator.get_element("my_app", "菜单/文件")
```

### 预加载功能

#### 配置文件格式

```json
{
  "components": {
    "应用名称": {
      "elements": [
        {
          "name": "元素显示名称",
          "path": "菜单/文件/新建",
          "role_name": "menu item"
        }
      ]
    }
  }
}
```

#### 预加载流程

1. 加载配置文件
2. 解析组件定义
3. 为指定应用预加载组件
4. 缓存元素信息
5. 提供快速访问

#### 性能优化

- **LRU缓存**: 自动管理缓存大小
- **父子级缓存**: 利用元素层级关系
- **批量预加载**: 一次性加载多个组件
- **智能查找**: 从最近缓存开始查找

### 交互式管理

#### 启动方式

```bash
# 交互式启动
python tested_communicator.py

# 命令行参数启动
python tested_communicator.py --port 8888 --machine-id machine_001
```

#### 管理菜单

```
服务管理菜单
1. 查看服务状态
2. 查看已注册应用
3. 手动注册应用
4. 注销应用
5. 预加载组件
6. 查看缓存状态
7. 重新加载配置文件
8. 停止服务
```

### 错误处理

#### 连接错误

- 网络连接失败
- 端口被占用
- 权限不足

#### 操作错误

- 应用未找到
- 元素不存在
- 操作执行失败

#### 配置错误

- 配置文件格式错误
- 预加载失败
- 缓存异常

### 日志和监控

#### 日志级别

- **INFO**: 正常操作信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **DEBUG**: 调试信息

#### 监控指标

- 连接状态
- 应用注册数量
- 缓存命中率
- 操作成功率
