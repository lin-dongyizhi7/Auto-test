# 多机器多应用自动化测试系统

## 项目概述

这是一个支持多机器多应用连接的自动化测试系统，包含前端图形化界面和后端 API 服务。后端基于 FastAPI，默认在进程内启动并管理“内置测试服务器”（基于 `communicators.test_communicator`），前端通过 HTTP API 调用后端执行元素操作、图片识别、键鼠输入、脚本管理等能力。

## 系统架构

```
┌─────────────────┐   HTTP API    ┌──────────────────────┐   内置测试服务器   ┌─────────────────┐
│   前端界面      │ ────────────→ │   后端 API (FastAPI) │ ─────────────────→ │  被测试机器们   │
│   (Vue3)        │               │   端口: 8080         │                   │  客户端端口:8888 │
└─────────────────┘               └──────────────────────┘                   └─────────────────┘
```

### 技术栈

- **前端**: Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- **后端**: Python + FastAPI + Uvicorn
- **自动化**: Dogtail (Linux) + PyAutoGUI (跨平台)
- **通信**: HTTP API（前端⇄后端）+ TCP Socket（后端内置测试服务器⇄被测机）

## 项目结构

```
Auto-test/
├── frontend/                     # 前端项目
│   ├── src/
│   │   ├── views/
│   │   ├── stores/
│   │   ├── api/
│   │   ├── utils/
│   │   └── assets/
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
├── backend/                      # 后端项目
│   ├── app.py                    # FastAPI 应用入口（内置测试服务器）
│   ├── config.py                 # 配置
│   ├── requirements.txt          # Python 依赖
│   ├── start.bat / start.sh      # 启动脚本
│   ├── scripts_storage.json      # 脚本存储（JSON）
│   └── script_counter.json       # 脚本计数器
├── communicators/                # 通信与多机操作
│   ├── test_communicator.py      # 测试服务器实现（也被后端内置使用）
│   ├── tested_communicator.py    # 被测机客户端（连接到测试服务器）
│   ├── operation_multi_machine.py# 多机器/应用操作封装
│   └── operation.py              # 单机操作封装（兼容）
└── README.md
```

## 快速开始

### 1) 环境准备

- 前端: Node.js 16+，npm
- 后端: Python 3.8+，pip

### 2) 启动后端服务（包含内置测试服务器）

```bash
cd backend
# Windows
start.bat
# Linux / macOS
chmod +x start.sh && ./start.sh
# 或手动
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8080
```

默认启动后，后端会在启动事件中尝试开启内置测试服务器，监听端口 8888。

### 3) 在每台被测机上启动客户端

```bash
cd communicators
python tested_communicator.py --machine-id machine_001 --test-server <后端IP>:8888
```

将 `<后端IP>` 替换为运行后端的机器 IP。每台被测机使用不同 `--machine-id`。

### 4) 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问前端: http://localhost:3000

### 5) API 文档

- 后端根地址: http://localhost:8080
- Swagger 文档: http://localhost:8080/docs

## 功能特性

### 多机器多应用管理

- **测试服务器连接**: 连接到中央测试服务器
- **机器管理**: 自动发现和管理多台被测试机器
- **应用管理**: 在每台机器上管理多个应用程序
- **目标设置**: 动态选择操作目标机器和应用
- **状态监控**: 实时监控机器和应用状态

### 前端功能

- **仪表板**: 系统状态概览和快速操作
- **多机器操作控制**: 图形化多机器多应用操作界面
  - 测试服务器连接管理
  - 目标机器和应用选择
  - 元素点击（左键、右键、双击）
  - 图片点击和查找
  - 拖拽操作
  - 文本输入
  - 快捷键操作
  - 截图功能
- **实时监控**: 操作日志和状态更新
- **脚本管理**: 支持多机器多应用的自动化脚本
- **系统设置**: 连接参数和操作配置

### 后端功能

- **内置测试服务器**: 后端进程内启动测试服务器
- **多机器连接管理**: 管理已连接的被测机与应用
- **多应用支持**: 支持每台机器上的多个应用程序
- **操作执行**: 基于 `operation_multi_machine.py` 的自动化操作
- **脚本管理**: JSON 持久化的脚本增删改查与运行标记
- **REST API**: 标准化的 API 端点与统一错误处理

### 自动化操作

- **元素操作**: 基于Dogtail的元素定位和操作
- **图像识别**: 基于OpenCV的图像查找和点击
- **鼠标操作**: 移动、点击、拖拽
- **键盘操作**: 文本输入、快捷键
- **窗口操作**: 窗口管理、截图
- **多机器协调**: 跨机器的操作协调和同步

## API 接口（后端主要端点）

以下为 `backend/app.py` 已实现的关键端点（更多细节见 Swagger 文档）：

- 服务器管理
  - `POST /api/server/start` 启动内置测试服务器（Body: `{ "port": 8888 }`）
  - `POST /api/server/stop` 停止内置测试服务器
  - `GET /api/server/status` 获取状态
- 机器与应用
  - `GET /api/machines` 获取机器列表与状态
  - `POST /api/machine/connect` 连接指定机器（可选能力）
  - `POST /api/machine/disconnect` 断开指定机器
  - `GET /api/apps` 获取注册的应用列表与状态
  - `POST /api/target/set` 设置当前机器与应用
  - `GET /api/target/current` 获取当前目标
- 元素与图片操作
  - `POST /api/element/click` / `right-click` / `double-click`
  - `POST /api/element/set-text` / `move-to`
  - `POST /api/image/find` / `api/image/click`
  - `GET /api/screenshot` 获取截图
- 键盘/等待
  - `POST /api/keyboard/hotkey` / `api/keyboard/type`
  - `POST /api/wait/element` / `api/wait/image`
- 脚本管理
  - `GET /api/scripts` / `GET /api/scripts/{id}`
  - `POST /api/scripts` / `PUT /api/scripts/{id}` / `DELETE /api/scripts/{id}`
  - `POST /api/scripts/{id}/run`

## 使用示例

### 1. 连接测试服务器

在前端界面中：

1. 进入"操作控制"页面
2. 在"测试服务器连接"面板中输入测试服务器IP地址和端口（默认8889）
3. 点击"连接"按钮

### 2. 选择目标机器和应用

1. 连接成功后，在"目标机器和应用"面板中选择目标机器
2. 选择目标应用
3. 点击"设置目标"按钮确认

### 3. 执行自动化操作

#### 点击元素

```javascript
// 前端API调用
await performClickElement({
  path: "菜单/文件/新建",
  roles: ["menu item"]
});
```

#### 点击图片

```javascript
// 前端API调用
await performClickImage({
  imagePath: "/path/to/image.png",
  threshold: 0.8
});
```

#### 拖拽操作

```javascript
// 前端API调用
await performDragTo({
  startX: 100,
  startY: 100,
  endX: 200,
  endY: 200
});
```

#### 获取截图

```javascript
// 前端API调用
await takeScreenshot("100,100,400,300"); // 可选区域参数
```

### 4. 查看操作日志

在"操作日志"面板可以查看所有执行的操作记录和状态更新。

## 开发指南

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

### 后端开发

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### 测试服务器/被测机独立运行（可选高级用法）

后端已内置测试服务器，通常无需单独运行。
如需独立部署测试服务器或做联调，可：

```bash
# 独立启动测试服务器（不常用）
cd communicators
python test_communicator.py --host 0.0.0.0 --port 8888

# 启动被测机客户端，指向服务器地址
python tested_communicator.py --machine-id machine_001 --test-server <server_ip>:8888
```

### 被测试机器开发

```bash
cd communicators
python tested_communicator.py --machine-id machine_001 --test-server 192.168.1.100:8889
```

### API 测试

推荐通过 Swagger 页面调试，或使用前端页面操作。

## 部署

### 前端（生产）

```bash
cd frontend
npm run build
# 将 dist 部署至 Web 服务器
```

### 后端（生产）

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8080 --workers 4
```

### 被测机客户端

```bash
cd communicators
python tested_communicator.py --machine-id <id> --test-server <backend-ip>:8888
```

## 配置说明

### 端口配置

- **内置测试服务器**: 8888（默认，后端内置）
- **后端 API**: 8080（默认）
- **前端开发服务器**: 3000（默认）

### 网络配置

- 确保测试服务器可以被所有被测试机器访问
- 确保前端可以访问后端API
- 配置防火墙规则允许相应端口通信

## 故障排除

### 常见问题

1. **前端无法连接后端**

   - 检查后端服务是否启动
   - 检查端口 8080 是否被占用
   - 检查 CORS 配置

2. **被测机未显示/无法操作**

   - 确认后端内置测试服务器已运行（`/api/server/status`）
   - 确认被测机客户端指向了正确地址 `<后端IP>:8888`
   - 检查网络连接与防火墙

3. **无法发现被测试机器**

   - 检查被测机服务是否启动
   - 检查被测机是否成功连接到测试服务器
   - 检查网络与防火墙

4. **操作执行失败**

   - 确认已设置正确的目标（机器/应用）
   - 检查元素路径/图片路径
   - 查看后端日志与返回错误信息

### 日志查看

- **前端日志**: 浏览器开发者工具控制台
- **后端日志**: 控制台输出（或接入你自己的日志方案）
- **被测机日志**: 控制台输出

## 架构优势

### 1. 多机器支持
- 同时连接和管理多台被测试机器
- 支持分布式测试环境
- 机器状态实时监控

### 2. 多应用管理
- 在每台机器上管理多个应用程序
- 支持不同应用的自动化测试
- 应用状态独立管理

### 3. 灵活目标设置
- 动态选择操作目标
- 支持快速切换测试环境
- 操作前目标验证

### 4. 可扩展性
- 支持水平扩展更多机器
- 支持垂直扩展更多应用
- 模块化架构设计

### 5. 企业级特性
- 集中化测试管理
- 统一的操作接口
- 完整的日志和监控

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请提交 Issue 或联系开发团队。

## 更新日志

### v2.0.0 - 多机器多应用架构重构（当前）
- 后端内置测试服务器运行模式（默认 8888）
- 支持同时管理多台机器和多个应用
- 前端支持多机器多应用管理与操作
- 新增脚本管理与运行标记
- 统一 API 前缀 `/api` 与错误返回结构
