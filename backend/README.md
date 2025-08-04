# 自动化测试后端API服务

## 概述

这是一个基于FastAPI的Python后端服务，用于接收前端页面发起的API请求，并调用 `operation.py`中的函数与被测试机器建立连接和执行对应的自动化操作。

## 功能特性

- **连接管理**: 建立和断开与被测试机器的TCP连接
- **元素操作**: 点击、右键点击、双击元素
- **图片操作**: 查找和点击图片
- **拖拽操作**: 支持坐标拖拽
- **文本输入**: 支持文本输入和元素文本设置
- **快捷键**: 支持快捷键操作
- **元素信息**: 获取元素位置和属性信息
- **实时监控**: 获取屏幕截图

## 技术栈

- **Python 3.8+**
- **FastAPI**: Web框架
- **Uvicorn**: ASGI服务器
- **Pydantic**: 数据验证
- **OpenCV**: 图像处理
- **Pillow**: 图像处理
- **NumPy**: 数值计算

## 项目结构

```
backend/
├── main.py              # 主应用文件
├── requirements.txt     # Python依赖
├── start.bat           # Windows启动脚本
├── start.sh            # Linux/Mac启动脚本
├── README.md           # 说明文档
└── backend.log         # 日志文件（运行时生成）
```

## 快速开始

### 1. 环境准备

确保已安装Python 3.8或更高版本：

```bash
python --version
```

### 2. 安装依赖

```bash
# 使用pip安装
pip install -r requirements.txt

# 或使用conda
conda install --file requirements.txt
```

### 3. 启动服务

#### Windows用户

```bash
# 双击运行
start.bat

# 或命令行运行
python main.py
```

#### Linux/Mac用户

```bash
# 添加执行权限
chmod +x start.sh

# 运行启动脚本
./start.sh

# 或直接运行
python3 main.py
```

### 4. 访问服务

- **服务地址**: http://localhost:8080
- **API文档**: http://localhost:8080/docs
- **交互式API文档**: http://localhost:8080/redoc

## API接口

### 基础接口

#### GET /

获取服务状态

```json
{
  "message": "自动化测试后端API服务",
  "version": "1.0.0",
  "status": "running",
  "connected": false
}
```

#### GET /status

获取连接状态

```json
{
  "connected": false,
  "host": null,
  "port": null
}
```

### 连接管理

#### POST /connect

连接到被测试机器

```json
{
  "host": "192.168.1.100",
  "port": 8888
}
```

#### POST /disconnect

断开连接

### 元素操作

#### POST /click-element

点击元素

```json
{
  "path": "button[0]",
  "roles": ["push button"]
}
```

#### POST /click-image

点击图片

```json
{
  "imagePath": "/path/to/image.png",
  "threshold": 0.8
}
```

### 拖拽操作

#### POST /drag-to

拖拽到指定坐标

```json
{
  "startX": 100,
  "startY": 100,
  "endX": 200,
  "endY": 200
}
```

### 文本操作

#### POST /input-text

输入文本

```json
{
  "text": "Hello World",
  "elementPath": "textbox[0]"
}
```

### 快捷键操作

#### POST /hotkey

执行快捷键

```json
{
  "keys": ["ctrl", "c"]
}
```

### 信息获取

#### GET /element-info

获取元素信息

```
GET /element-info?path=button[0]&roles=push%20button
```

#### POST /find-image

查找图片

```json
{
  "imagePath": "/path/to/image.png",
  "threshold": 0.8
}
```

## 配置说明

### 环境变量

可以通过环境变量配置服务：

```bash
# 服务端口
export PORT=8080

# 日志级别
export LOG_LEVEL=INFO

# 允许的源站
export ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 日志配置

日志文件位置：`backend.log`

日志级别：

- DEBUG: 详细调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息

## 错误处理

### 常见错误

1. **连接失败**

   - 检查被测试机器是否启动
   - 检查IP地址和端口是否正确
   - 检查网络连接
2. **元素未找到**

   - 检查元素路径是否正确
   - 检查元素是否在当前页面
   - 检查角色名称是否正确
3. **图片未找到**

   - 检查图片路径是否正确
   - 调整匹配阈值
   - 检查图片是否在当前屏幕

### 错误响应格式

```json
{
  "success": false,
  "error": "错误描述",
  "message": "用户友好的错误信息"
}
```

## 开发指南

### 添加新的API接口

1. 在 `main.py`中添加新的路由函数
2. 定义请求和响应的Pydantic模型
3. 实现业务逻辑
4. 添加错误处理
5. 更新文档

### 测试API

使用curl测试API：

```bash
# 测试连接
curl -X POST "http://localhost:8080/connect" \
     -H "Content-Type: application/json" \
     -d '{"host": "192.168.1.100", "port": 8888}'

# 测试点击元素
curl -X POST "http://localhost:8080/click-element" \
     -H "Content-Type: application/json" \
     -d '{"path": "button[0]", "roles": ["push button"]}'
```

## 部署

### 生产环境部署

1. 使用Gunicorn作为WSGI服务器：

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

2. 使用Nginx作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker部署

创建Dockerfile：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

构建和运行：

```bash
docker build -t qgis-backend .
docker run -p 8080:8080 qgis-backend
```

## 故障排除

### 常见问题

1. **端口被占用**

   ```bash
   # 查找占用端口的进程
   netstat -ano | findstr :8080

   # 杀死进程
   taskkill /PID <进程ID> /F
   ```
2. **依赖安装失败**

   ```bash
   # 升级pip
   pip install --upgrade pip

   # 使用国内镜像
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```
3. **权限问题**

   ```bash
   # Linux/Mac添加执行权限
   chmod +x start.sh
   ```
