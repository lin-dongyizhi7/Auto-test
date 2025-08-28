# 多机器多应用自动化测试系统

## 项目概述

这是一个支持多机器多应用连接的自动化测试系统，包含前端图形化界面和后端API服务。系统通过前端页面进行图形化操作和配置，后端接收API请求并调用 `operation_multi_machine.py` 中的函数与测试服务器建立连接，支持同时管理多台被测试机器和多个应用程序的自动化操作。

## 系统架构

```
┌─────────────────┐    HTTP API    ┌─────────────────┐    TCP Socket    ┌─────────────────┐
│   前端界面      │ ──────────────→ │   后端API服务   │ ──────────────→ │   测试服务器    │
│   (Vue3)        │                │   (FastAPI)     │                │   (8889端口)    │
└─────────────────┘                └─────────────────┘                └─────────────────┘
                                                                              │
                                                                              ▼
                                                                      ┌─────────────────┐
                                                                      │   被测试机器1    │
                                                                      │   (8888端口)    │
                                                                      └─────────────────┘
                                                                              │
                                                                              ▼
                                                                      ┌─────────────────┐
                                                                      │   被测试机器2    │
                                                                      │   (8888端口)    │
                                                                      └─────────────────┘
                                                                              │
                                                                              ▼
                                                                      ┌─────────────────┐
                                                                      │   被测试机器N    │
                                                                      │   (8888端口)    │
                                                                      └─────────────────┘
```

### 技术栈

- **前端**: Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- **后端**: Python + FastAPI + Uvicorn
- **自动化**: Dogtail (Linux) + PyAutoGUI (跨平台)
- **通信**: HTTP API + TCP Socket (多机器多应用)
- **测试服务器**: 多机器连接管理和事件同步

## 项目结构

```
Auto-test/
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   └── Operation.vue   # 多机器多应用操作界面
│   │   ├── stores/             # 状态管理
│   │   │   └── operation.ts    # 多机器多应用状态管理
│   │   ├── api/                # API接口
│   │   │   ├── types.ts        # 多机器多应用类型定义
│   │   │   └── operation.ts    # 多机器多应用API调用
│   │   ├── utils/              # 工具函数
│   │   └── assets/             # 静态资源
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
├── backend/                     # 后端项目
│   ├── main.py                 # 多机器多应用主应用文件
│   ├── requirements.txt        # Python依赖
│   ├── test_api.py             # API测试脚本
│   ├── start.bat               # Windows启动脚本
│   ├── start.sh                # Linux/Mac启动脚本
│   └── README.md
├── communicators/               # 通信模块
│   ├── operation_multi_machine.py  # 多机器多应用操作封装
│   ├── test_communicator.py        # 测试服务器通信
│   ├── tested_communicator.py      # 被测试机器通信
│   ├── operation.py                # 单机器操作封装（兼容）
│   └── design_document.md          # 设计文档
├── qgis-auto-test/             # QGIS测试示例
│   ├── test_01_project.py      # 项目测试
│   └── data/                   # 测试数据
└── README.md                   # 项目说明
```

## 快速开始

### 1. 环境准备

#### 前端环境

- Node.js 16+
- npm 或 yarn

#### 后端环境

- Python 3.8+
- pip

### 2. 启动测试服务器

```bash
# 进入通信模块目录
cd communicators

# 启动测试服务器（监听8889端口）
python test_communicator.py
```

### 3. 启动被测试机器服务

```bash
# 在每台被测试机器上运行
cd communicators

# 启动被测试机器服务（监听8888端口）
python tested_communicator.py --machine-id machine_001 --test-server 192.168.1.100:8889
```

### 4. 启动后端服务

```bash
# 进入后端目录
cd backend

# Windows用户
start.bat

# Linux/Mac用户
chmod +x start.sh
./start.sh

# 或手动启动
pip install -r requirements.txt
python main.py
```

后端服务将在 http://localhost:8080 启动

### 5. 启动前端服务

```bash
# 进入前端目录
cd frontend

# Windows用户
start.bat

# Linux/Mac用户
chmod +x start.sh
./start.sh

# 或手动启动
npm install
npm run dev
```

前端服务将在 http://localhost:3000 启动

### 6. 访问系统

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8080
- **API文档**: http://localhost:8080/docs

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

- **多机器连接管理**: 通过测试服务器管理多台机器
- **多应用支持**: 支持每台机器上的多个应用程序
- **操作执行**: 调用operation_multi_machine.py中的自动化操作
- **API接口**: 完整的RESTful API服务
- **错误处理**: 统一的错误处理和响应
- **日志记录**: 详细的操作日志

### 自动化操作

- **元素操作**: 基于Dogtail的元素定位和操作
- **图像识别**: 基于OpenCV的图像查找和点击
- **鼠标操作**: 移动、点击、拖拽
- **键盘操作**: 文本输入、快捷键
- **窗口操作**: 窗口管理、截图
- **多机器协调**: 跨机器的操作协调和同步

## API接口

### 连接管理

- `POST /connect` - 连接到测试服务器
- `POST /disconnect` - 断开连接
- `GET /status` - 获取连接状态

### 多机器多应用管理

- `GET /machines` - 获取可用机器列表
- `GET /apps` - 获取可用应用列表
- `POST /set-target` - 设置当前操作目标机器和应用
- `GET /current-target` - 获取当前操作目标
- `POST /screenshot` - 获取当前目标应用的截图

### 元素操作

- `POST /click-element` - 点击元素
- `GET /element-info` - 获取元素信息

### 图像操作

- `POST /click-image` - 点击图片
- `POST /find-image` - 查找图片

### 其他操作

- `POST /drag-to` - 拖拽操作
- `POST /input-text` - 文本输入
- `POST /hotkey` - 快捷键操作

### 脚本管理

- `GET /scripts` - 获取脚本列表
- `POST /scripts` - 创建脚本
- `PUT /scripts/{id}` - 更新脚本
- `DELETE /scripts/{id}` - 删除脚本
- `POST /scripts/{id}/run` - 运行脚本
- `POST /scripts/import` - 导入脚本
- `GET /scripts/{id}/export` - 导出脚本

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
python main.py
```

### 测试服务器开发

```bash
cd communicators
python test_communicator.py
```

### 被测试机器开发

```bash
cd communicators
python tested_communicator.py --machine-id machine_001 --test-server 192.168.1.100:8889
```

### API测试

```bash
cd backend
python test_api.py
```

## 部署

### 生产环境部署

#### 前端部署

```bash
cd frontend
npm run build
# 将dist目录部署到Web服务器
```

#### 后端部署

```bash
cd backend
pip install -r requirements.txt
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

#### 测试服务器部署

```bash
cd communicators
python test_communicator.py --host 0.0.0.0 --port 8889
```

#### 被测试机器部署

```bash
cd communicators
python tested_communicator.py --bind-host 0.0.0.0 --bind-port 8888 --test-server 192.168.1.100:8889 --machine-id machine_001
```

### Docker部署

创建docker-compose.yml：

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  backend:
    build: ./backend
    ports:
      - "8080:8080"
    depends_on:
      - test-server
  
  test-server:
    build: ./communicators
    ports:
      - "8889:8889"
    command: python test_communicator.py --host 0.0.0.0 --port 8889
```

## 配置说明

### 端口配置

- **测试服务器**: 8889 (默认)
- **被测试机器**: 8888 (默认)
- **后端API**: 8080 (默认)
- **前端开发服务器**: 3000 (默认)

### 网络配置

- 确保测试服务器可以被所有被测试机器访问
- 确保前端可以访问后端API
- 配置防火墙规则允许相应端口通信

## 故障排除

### 常见问题

1. **前端无法连接后端**

   - 检查后端服务是否启动
   - 检查端口8080是否被占用
   - 检查CORS配置

2. **后端无法连接测试服务器**

   - 检查测试服务器是否启动
   - 检查IP地址和端口是否正确
   - 检查网络连接

3. **无法发现被测试机器**

   - 检查被测试机器服务是否启动
   - 检查被测试机器是否连接到测试服务器
   - 检查网络连接和防火墙设置

4. **操作执行失败**

   - 确认已设置正确的目标机器和应用
   - 检查元素路径是否正确
   - 检查图片路径是否存在
   - 查看后端日志获取详细错误信息

### 日志查看

- **前端日志**: 浏览器开发者工具控制台
- **后端日志**: backend/backend.log文件
- **测试服务器日志**: 控制台输出
- **被测试机器日志**: 控制台输出

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

本项目采用MIT许可证。

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。

## 更新日志

### v2.0.0 - 多机器多应用架构重构
- 重构为多机器多应用连接架构
- 新增测试服务器和被测试机器分离
- 支持同时管理多台机器和多个应用
- 重构前端界面，支持多机器多应用管理
- 新增目标设置和状态监控功能
- 优化API接口和错误处理
- 增强用户体验和操作安全性
