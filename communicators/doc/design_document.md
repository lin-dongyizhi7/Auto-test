# 自动化测试系统设计方案

## 1. 系统概述

这是一个基于 **Dogtail** 和 **PyAutoGUI** 的跨平台自动化测试系统，采用 **客户端-服务器架构**，支持远程控制被测试机器执行GUI自动化操作。

### 1.1 核心特性
- **跨平台支持**: 基于Dogtail的Linux桌面自动化 + PyAutoGUI的跨平台操作
- **远程控制**: 支持网络通信的分布式测试架构
- **元素定位**: 支持基于路径的元素查找和图像识别
- **操作封装**: 高级操作API封装底层鼠标键盘操作
- **缓存优化**: LRU缓存机制提升元素查询性能

## 2. 系统架构

### 2.1 整体架构图
```
┌─────────────────┐    TCP Socket    ┌─────────────────┐
│   测试者机器     │ ←──────────────→ │   被测试机器     │
│ (Test Machine)  │    8888端口      │ (Tested Machine) │
└─────────────────┘                  └─────────────────┘
        │                                      │
        │                                      │
        ▼                                      ▼
┌─────────────────┐                  ┌─────────────────┐
│  Operation.py   │                  │TestedMachine-   │
│  (操作封装层)    │                  │Communicator.py  │
└─────────────────┘                  │ (通信服务层)     │
        │                                      │
        ▼                                      ▼
┌─────────────────┐                  ┌─────────────────┐
│TestMachine-     │                  │  Dogtail        │
│Communicator.py  │                  │ (元素定位)       │
│ (通信客户端)     │                  └─────────────────┘
└─────────────────┘                          │
                                             ▼
                                    ┌─────────────────┐
                                    │  PyAutoGUI      │
                                    │ (鼠标键盘操作)   │
                                    └─────────────────┘
```

### 2.2 组件说明

#### 2.2.1 测试者机器端 (Test Machine)
- **Operation.py**: 高级操作封装类，提供用户友好的API
- **TestMachineCommunicator.py**: 通信客户端，负责与被测试机器通信

#### 2.2.2 被测试机器端 (Tested Machine)  
- **TestedMachineCommunicator.py**: 通信服务端，监听8888端口处理请求
- **Dogtail**: Linux桌面自动化框架，用于元素定位和UI交互
- **PyAutoGUI**: 跨平台自动化库，执行鼠标键盘操作

## 3. 核心技术详解

### 3.1 Dogtail 使用说明

#### 3.1.1 什么是Dogtail
Dogtail 是一个基于 **AT-SPI (Assistive Technology Service Provider Interface)** 的Linux桌面自动化框架，通过访问性API与GUI应用程序交互。

#### 3.1.2 核心概念
```python
# 获取根节点（所有应用程序）
root = dogtail.tree.root

# 获取特定应用
app = root.application("calculator")

# 元素定位方式
element = app.child(name="按钮文本", roleName="push button")
element = app.child(name="菜单项", roleName="menu item")

# 元素操作
element.click()           # 点击
element.doubleClick()     # 双击
element.point()           # 获取位置
element.size              # 获取尺寸
```

#### 3.1.3 元素路径系统
```python
# 路径格式: "父元素1/父元素2/目标元素"
element_path = "菜单栏/文件/新建"

# 角色名匹配
role_name_list = ["menu bar", "menu", "menu item"]
```

### 3.2 PyAutoGUI 使用说明

#### 3.2.1 什么是PyAutoGUI
PyAutoGUI 是一个跨平台的Python库，用于控制鼠标和键盘，实现GUI自动化操作。

#### 3.2.2 核心功能
```python
# 鼠标操作
pyautogui.moveTo(x, y, duration=0.1)           # 移动鼠标
pyautogui.click(x, y, button='left')           # 点击
pyautogui.doubleClick(x, y)                    # 双击
pyautogui.drag(startX, startY, endX, endY)     # 拖拽

# 键盘操作
pyautogui.press('enter')                       # 按键
pyautogui.hotkey('ctrl', 'c')                  # 组合键
pyautogui.typewrite('Hello World')             # 输入文本

# 截图功能
pyautogui.screenshot(region=(x, y, w, h))      # 区域截图
```

## 4. 通信协议设计

### 4.1 请求格式
```json
{
    "type": "请求类型",
    "data": {
        "参数1": "值1",
        "参数2": "值2"
    },
    "timestamp": 1234567890.123
}
```

### 4.2 响应格式
```json
{
    "success": true/false,
    "data": {
        "结果数据"
    },
    "error": "错误信息（如果失败）"
}
```

### 4.3 支持的请求类型

#### 4.3.1 get_app_region
获取应用窗口区域信息
```json
{
    "type": "get_app_region",
    "data": {}
}
```

#### 4.3.2 get_screenshot
获取屏幕截图
```json
{
    "type": "get_screenshot", 
    "data": {
        "region": [x, y, width, height]  // 可选
    }
}
```

#### 4.3.3 get_element
获取元素信息
```json
{
    "type": "get_element",
    "data": {
        "element_path": "菜单/文件/新建",
        "role_name_list": ["menu", "menu", "menu item"]
    }
}
```

#### 4.3.4 exec_commands
执行操作指令集
```json
{
    "type": "exec_commands",
    "data": {
        "commands": [
            {
                "action": "mouse_move",
                "params": {"x": 100, "y": 200}
            },
            {
                "action": "mouse_click", 
                "params": {"x": 100, "y": 200, "button": "left"}
            }
        ]
    }
}
```

## 5. 操作指令系统

### 5.1 指令格式
```json
{
    "action": "操作类型",
    "params": {
        "参数": "值"
    },
    "timestamp": 1234567890.123
}
```

### 5.2 支持的指令类型

#### 5.2.1 鼠标操作
- `mouse_move`: 鼠标移动
- `mouse_click`: 鼠标点击
- `mouse_press`: 按下鼠标键
- `mouse_release`: 释放鼠标键
- `mouse_scroll`: 鼠标滚轮

#### 5.2.2 键盘操作
- `key_press`: 按键
- `hotkey`: 组合键

### 5.3 高级操作API

#### 5.3.1 元素操作
```python
# 点击元素
op.click_element("按钮", ["push button"])

# 右键点击
op.right_click_element("菜单项", ["menu item"])

# 双击元素
op.double_click_element("文件", ["table cell"])

# 设置文本
op.set_element_text("输入框", "Hello World", ["text"])
```

#### 5.3.2 图像识别操作
```python
# 查找图片
op.find_image("button.png", threshold=0.8)

# 点击图片
op.click_image("button.png", threshold=0.8)
```

#### 5.3.3 拖拽操作
```python
# 绝对坐标拖拽
op.drag_to(start_x, start_y, end_x, end_y)

# 百分比拖拽
op.drag_to_percentage(0.2, 0.3, 0.8, 0.7)

# 元素间拖拽
op.drag_item_to_parent("源元素", "目标元素")
```

## 6. 缓存机制

### 6.1 LRU缓存设计
```python
class LRUCache:
    def __init__(self, capacity=50):
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key):
        # 获取缓存，并将访问的元素移到末尾
        pass
    
    def put(self, key, value):
        # 添加缓存，如果满了则移除最久未使用的
        pass
```

### 6.2 缓存策略
- **元素对象缓存**: 缓存Dogtail元素对象，避免重复查询
- **增量查询**: 基于父级缓存进行子元素查询
- **自动清理**: 连接断开时自动清空缓存

## 7. 使用示例

### 7.1 基础使用流程
```python
# 1. 启动被测试机器服务
# python tested_communicator.py

# 2. 测试者机器编写测试脚本
from operation import Operation

# 创建操作实例
op = Operation(test_machine_ip="192.168.1.100", test_machine_port=8888)

# 执行测试操作
op.click_element("1", ["push button"])
op.click_element("+", ["push button"]) 
op.click_element("2", ["push button"])
op.click_element("=", ["push button"])

# 关闭连接
op.close()
```

### 7.2 复杂应用测试示例
```python
# QGIS应用测试
class TestQGISProject(QGISDogtailTest):
    def test_add_layer(self):
        # 添加矢量图层
        self.addVectorLayer('/path/to/layer.geojson')
        
        # 地图操作
        self.drag_map_percentage(0.6, 0.7, 0.5, 0.6)
        
        # 验证结果
        layer = self.find_layer("layer_name")
        self.assertIsNotNone(layer)
```

## 8. 性能优化

### 8.1 缓存优化
- LRU缓存减少重复元素查询
- 父级缓存支持增量查询
- 连接断开时自动清理缓存

### 8.2 通信优化
- 长连接减少连接开销
- 二进制图片传输优化
- 请求响应异步处理

### 8.3 操作优化
- 操作间延迟控制
- 批量指令执行
- 错误重试机制

## 9. 错误处理

### 9.1 连接错误
- 自动重连机制
- 连接状态监控
- 超时处理

### 9.2 元素查找错误
- 路径验证
- 角色名匹配
- 错误信息详细化

### 9.3 操作执行错误
- 异常捕获
- 错误日志记录
- 操作回滚

## 10. 扩展性设计

### 10.1 新操作类型扩展
```python
def custom_action(self, params):
    commands = [
        self._generate_command("custom_action", params)
    ]
    self.finish_current_opts(commands)
```

### 10.2 新通信协议扩展
```python
elif request["type"] == "custom_request":
    response = self._handle_custom_request(request["data"])
```

### 10.3 多应用支持
- 应用切换机制
- 应用特定配置
- 多窗口管理

## 11. 总结

这个自动化测试系统通过 **Dogtail + PyAutoGUI + 网络通信** 的组合，实现了：

1. **跨平台支持**: 基于AT-SPI的Linux桌面自动化
2. **远程控制**: 分布式测试架构
3. **高级API**: 封装底层操作，提供易用接口
4. **性能优化**: 缓存机制和通信优化
5. **扩展性强**: 支持自定义操作和协议扩展

系统适用于GUI应用的自动化测试、演示录制、重复操作自动化等场景。 