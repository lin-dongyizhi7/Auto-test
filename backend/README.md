# 自动化测试系统后端

基于 FastAPI 的多机器多应用自动化测试后端服务，采用"服务端内置测试服务器"运行模式。

## 系统架构

- **运行框架**: FastAPI + Uvicorn
- **内置测试服务器**: 基于 `communicators.test_communicator.TestMachineCommunicator`
- **操作封装**: `communicators.operation_multi_machine.MultiMachineOperation`
- **HTTP API 端口**: 8080（固定）
- **内置测试服务器端口**: 8888（固定）
- **脚本存储**: JSON 文件 + 独立脚本目录

## 快速开始

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动服务

**Windows:**
```bat
start.bat
```

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

**手动启动:**
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8080
```

### 4. 访问服务

- **后端 API**: http://localhost:8080
- **API 文档**: http://localhost:8080/docs
- **健康检查**: http://localhost:8080/health

## 运行模式

- **自动启动**: 后端启动时自动启动内置测试服务器（监听 8888 端口）
- **多机器管理**: 支持同时连接多台被测试机器
- **多应用支持**: 每台机器可注册多个应用程序
- **脚本存储**: 使用 JSON 文件存储脚本元数据，脚本内容存储在独立文件中

## API 接口

### 服务器管理

- `POST /api/server/start` - 启动内置测试服务器
- `POST /api/server/stop` - 停止内置测试服务器  
- `GET /api/server/status` - 获取服务器状态

### 机器与应用管理

- `GET /api/machines` - 获取已连接机器列表
- `POST /api/machine/connect` - 连接目标机器（固定使用 8888 端口）
- `POST /api/machine/disconnect` - 断开机器连接
- `GET /api/apps` - 获取已注册应用列表
- `POST /api/target/set` - 设置当前操作目标
- `GET /api/target/current` - 获取当前操作目标

### 元素操作

- `POST /api/element/click` - 点击元素
- `POST /api/element/right-click` - 右键点击元素
- `POST /api/element/double-click` - 双击元素
- `POST /api/element/set-text` - 设置元素文本
- `POST /api/element/move-to` - 移动到元素中心

### 图像操作

- `POST /api/image/find` - 查找图片
- `POST /api/image/click` - 点击图片
- `GET /api/screenshot` - 获取截图

### 键盘操作

- `POST /api/keyboard/hotkey` - 发送组合键
- `POST /api/keyboard/type` - 输入文本

### 等待操作

- `POST /api/wait/element` - 等待元素出现
- `POST /api/wait/image` - 等待图片出现

### 脚本管理

- `GET /api/scripts` - 获取脚本列表
- `GET /api/scripts/{id}` - 获取脚本详情
- `POST /api/scripts` - 创建脚本
- `PUT /api/scripts/{id}` - 更新脚本
- `DELETE /api/scripts/{id}` - 删除脚本
- `POST /api/scripts/{id}/run` - 运行脚本

### Python脚本管理

- `POST /api/scripts/python/run` - 运行Python脚本
- `POST /api/scripts/python/validate` - 验证Python脚本语法
- `POST /api/scripts/python/convert` - 将Python脚本转换为JSON脚本并保存

### 事件管理

- `GET /api/events` - 获取事件历史

## 使用流程

1. **启动后端服务**（自动启动内置测试服务器）
2. **连接被测试机器**：`POST /api/machine/connect`，Body: `{"host": "192.168.1.100"}`
3. **获取资源列表**：`GET /api/machines`、`GET /api/apps`
4. **设置操作目标**：`POST /api/target/set`，Body: `{"machine_id": "machine_001", "app_name": "calculator"}`
5. **执行操作**：调用各种操作 API（点击、输入、截图等）
6. **运行脚本**：`POST /api/scripts/{id}/run`
7. **运行Python脚本**：`POST /api/scripts/python/run`

## Python脚本API详细说明

### 运行Python脚本

**端点**: `POST /api/scripts/python/run`

**请求体**:
```json
{
  "script_content": "from op_record import OpRecord\nOpRecord.setMachine('192.168.1.100', 'calculator')\nOpRecord.click_element('按钮', ['push button'])",
  "target_machine_ip": "192.168.1.100",
  "target_app_name": "calculator"
}
```

**响应**:
```json
{
  "success": true,
  "data": {...},
  "message": "Python脚本执行成功"
}
```

### 验证Python脚本语法

**端点**: `POST /api/scripts/python/validate`

**请求体**:
```json
{
  "script_content": "from op_record import OpRecord\nOpRecord.setMachine('192.168.1.100', 'calculator')"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Python脚本语法正确"
}
```

### Python脚本编写规范

1. **导入OpRecord类**:
   ```python
   from op_record import OpRecord
   ```

2. **设置目标机器和应用**:
   ```python
   OpRecord.setMachine("192.168.1.100", "calculator")
   ```

3. **编写操作步骤**:
   ```python
   OpRecord.click_element("按钮", ["push button"])
   OpRecord.input_text("输入框", "测试文本")
   OpRecord.hotkey(["Ctrl", "c"])
   ```

4. **支持的操作类型**:
   - 鼠标操作：`click_element`, `right_click_element`, `double_click_element`
   - 键盘操作：`input_text`, `hotkey`, `key_press`
   - 等待操作：`wait_for_element`, `wait_for_image`
   - 图像识别：`click_image`, `find_image`
   - 截图操作：`get_screenshot`

### 转换Python脚本为JSON脚本

**端点**: `POST /api/scripts/python/convert`

**请求体**:
```json
{
  "script_content": "from op_record import OpRecord\nOpRecord.setMachine('192.168.1.100', 'calculator')\nOpRecord.click_element('按钮', ['push button'])",
  "script_name": "转换后的脚本",
  "description": "从Python脚本转换而来",
  "target_machine_ip": "192.168.1.100",
  "target_app_name": "calculator"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "script_2",
    "name": "转换后的脚本",
    "description": "从Python脚本转换而来",
    "content": "{\"target_machine_ip\":\"192.168.1.100\",\"target_app_name\":\"calculator\",\"steps\":[...]}",
    "createdAt": "2024-01-01T00:00:00",
    "updatedAt": "2024-01-01T00:00:00"
  },
  "message": "Python脚本已成功转换为JSON脚本: 转换后的脚本"
}
```

**功能说明**:
- 将Python脚本解析为JSON格式
- 自动保存为JSON脚本到后端存储
- 支持自定义脚本名称和描述
- 可选择设置目标机器和应用
- 转换成功后自动刷新脚本列表

## 脚本存储

- **元数据文件**: `script_info.json` - 存储脚本基本信息
- **脚本内容目录**: `scripts_store/` - 存储脚本内容文件
- **文件格式**: JSON 格式的测试步骤定义

## 目录结构

```
backend/
├── app.py                    # FastAPI 应用入口
├── config.py                 # 配置文件
├── requirements.txt          # Python 依赖
├── start.bat                 # Windows 启动脚本
├── start.sh                  # Linux/macOS 启动脚本
├── script_info.json          # 脚本元数据文件
├── scripts_store/            # 脚本内容目录
│   └── script_1.json        # 示例脚本
└── routes/                   # 路由模块
    ├── __init__.py
    ├── server.py            # 服务器管理路由
    ├── machine.py           # 机器管理路由
    ├── operation.py         # 操作路由
    └── script.py            # 脚本管理路由
```

## 环境变量

- `TEST_SERVER_PORT`: 内置测试服务器端口（默认 8888）
- `SCRIPT_STORAGE_DIR`: 脚本存储目录
- `LOG_LEVEL`: 日志级别（默认 INFO）

## 常见问题

- **连接失败**: 检查被测试机器是否启动客户端服务
- **操作失败**: 确认已设置正确的目标机器和应用
- **脚本执行失败**: 检查脚本格式和路径是否正确
- **端口冲突**: 检查 8080 和 8888 端口是否被占用

## 开发说明

如需扩展功能或修改 API，请：
1. 修改对应的路由文件（`routes/` 目录下）
2. 更新 `app.py` 中的路由注册
3. 同步更新前端 API 调用



