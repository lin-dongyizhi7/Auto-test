# QGIS自动化测试系统

## 项目概述

这是一个完整的QGIS自动化测试系统，包含前端图形化界面和后端API服务。系统通过前端页面进行图形化操作和配置，后端接收API请求并调用`operation.py`中的函数与被测试机器建立连接和执行对应的自动化操作。

## 系统架构

```
┌─────────────────┐    HTTP API    ┌─────────────────┐    TCP Socket    ┌─────────────────┐
│   前端界面      │ ──────────────→ │   后端API服务   │ ──────────────→ │   被测试机器    │
│   (Vue3)        │                │   (FastAPI)     │                │   (Dogtail)     │
└─────────────────┘                └─────────────────┘                └─────────────────┘
```

### 技术栈

- **前端**: Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- **后端**: Python + FastAPI + Uvicorn
- **自动化**: Dogtail (Linux) + PyAutoGUI (跨平台)
- **通信**: HTTP API + TCP Socket

## 项目结构

```
Auto-test/
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   ├── stores/             # 状态管理
│   │   ├── api/                # API接口
│   │   ├── utils/              # 工具函数
│   │   └── assets/             # 静态资源
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
├── backend/                     # 后端项目
│   ├── main.py                 # 主应用文件
│   ├── requirements.txt        # Python依赖
│   ├── test_api.py             # API测试脚本
│   ├── start.bat               # Windows启动脚本
│   ├── start.sh                # Linux/Mac启动脚本
│   └── README.md
├── communicators/               # 通信模块
│   ├── operation.py            # 操作封装
│   ├── test_communicator.py    # 通信客户端
│   └── design_document.md      # 设计文档
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

### 2. 启动后端服务

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

### 3. 启动前端服务

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

### 4. 访问系统

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8080
- **API文档**: http://localhost:8080/docs

## 功能特性

### 前端功能

- **仪表板**: 系统状态概览和快速操作
- **操作控制**: 图形化操作界面
  - 元素点击（左键、右键、双击）
  - 图片点击
  - 拖拽操作
  - 文本输入
  - 快捷键操作
- **实时监控**: 屏幕截图和操作日志
- **脚本管理**: 自动化脚本录制和回放
- **系统设置**: 连接参数和操作配置

### 后端功能

- **连接管理**: 与被测试机器的TCP连接
- **操作执行**: 调用operation.py中的自动化操作
- **API接口**: RESTful API服务
- **错误处理**: 统一的错误处理和响应
- **日志记录**: 详细的操作日志

### 自动化操作

- **元素操作**: 基于Dogtail的元素定位和操作
- **图像识别**: 基于OpenCV的图像查找和点击
- **鼠标操作**: 移动、点击、拖拽
- **键盘操作**: 文本输入、快捷键
- **窗口操作**: 窗口管理、截图

## API接口

### 连接管理

- `POST /connect` - 连接到被测试机器
- `POST /disconnect` - 断开连接
- `GET /status` - 获取连接状态

### 元素操作

- `POST /click-element` - 点击元素
- `POST /right-click-element` - 右键点击元素
- `POST /double-click-element` - 双击元素
- `GET /element-info` - 获取元素信息

### 图像操作

- `POST /click-image` - 点击图片
- `POST /find-image` - 查找图片

### 其他操作

- `POST /drag-to` - 拖拽操作
- `POST /input-text` - 文本输入
- `POST /hotkey` - 快捷键操作

## 使用示例

### 1. 连接被测试机器

在前端界面中：
1. 进入"操作控制"页面
2. 输入被测试机器的IP地址和端口
3. 点击"连接"按钮

### 2. 执行自动化操作

#### 点击元素
```javascript
// 前端API调用
await operationAPI.clickElement("button[0]", ["push button"]);
```

#### 点击图片
```javascript
// 前端API调用
await operationAPI.clickImage("/path/to/image.png", 0.8);
```

#### 拖拽操作
```javascript
// 前端API调用
await operationAPI.dragTo(100, 100, 200, 200);
```

### 3. 查看操作历史

在"操作控制"页面可以查看所有执行的操作历史记录。

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
```

## 故障排除

### 常见问题

1. **前端无法连接后端**
   - 检查后端服务是否启动
   - 检查端口8080是否被占用
   - 检查CORS配置

2. **后端无法连接被测试机器**
   - 检查被测试机器是否启动
   - 检查IP地址和端口是否正确
   - 检查网络连接

3. **操作执行失败**
   - 检查元素路径是否正确
   - 检查图片路径是否存在
   - 查看后端日志获取详细错误信息

### 日志查看

- **前端日志**: 浏览器开发者工具控制台
- **后端日志**: backend/backend.log文件

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