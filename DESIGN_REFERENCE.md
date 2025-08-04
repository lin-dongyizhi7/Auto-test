# 自动化测试系统设计参考文档

## 系统概述

自动化测试系统是一个完整的GUI自动化测试解决方案，包含前端图形化界面、后端API服务和通信模块。

### 系统架构

```
前端界面(Vue3) ←→ 后端API(FastAPI) ←→ 通信模块 ←→ 被测试机器(Dogtail/PyAutoGUI)
```

## 前端设计

### 技术栈

- Vue 3 + TypeScript + Element Plus
- Pinia状态管理 + Vue Router路由
- Axios HTTP客户端 + Vite构建工具

### 核心模块

1. **操作控制页面**: 连接管理、元素操作、图像操作、拖拽操作
2. **仪表板页面**: 系统状态概览、快速操作、统计信息
3. **脚本管理页面**: 脚本列表、创建、编辑、导入、导出、运行
4. **状态管理**: 连接状态、操作历史、配置管理
5. **API接口层**: 统一的HTTP请求封装

### 主要功能

- 图形化操作界面
- 实时连接状态显示
- 操作历史记录
- 脚本管理功能
- 系统配置管理

## 后端设计

### 技术栈

- Python + FastAPI + Uvicorn
- Pydantic数据验证
- OpenCV图像处理

### 核心功能

1. **连接管理**: 与被测试机器的TCP连接
2. **操作执行**: 调用通信模块执行自动化操作
3. **脚本管理**: Python脚本的CRUD操作和执行
4. **API服务**: RESTful API接口
5. **错误处理**: 统一的错误处理和响应格式

### API接口

#### 操作接口
- `POST /connect` - 连接被测试机器
- `POST /click-element` - 点击元素
- `POST /click-image` - 点击图片
- `POST /drag-to` - 拖拽操作
- `POST /input-text` - 文本输入
- `POST /hotkey` - 快捷键操作

#### 脚本管理接口
- `GET /scripts` - 获取脚本列表
- `GET /scripts/{id}` - 获取单个脚本
- `POST /scripts` - 创建脚本
- `PUT /scripts/{id}` - 更新脚本
- `DELETE /scripts/{id}` - 删除脚本
- `POST /scripts/{id}/run` - 运行脚本
- `POST /scripts/import` - 导入脚本文件
- `GET /scripts/{id}/export` - 导出脚本文件

## 脚本管理功能

### 功能概述

脚本管理模块提供了完整的Python脚本生命周期管理功能，支持脚本的创建、编辑、导入、导出、运行和监控。

### 核心特性

1. **脚本列表管理**: 显示所有脚本的基本信息，包括名称、描述、状态、运行次数等
2. **脚本创建**: 通过Web界面创建新的Python脚本
3. **脚本编辑**: 在线编辑脚本内容和元数据
4. **脚本导入**: 支持从本地文件导入.py脚本
5. **脚本导出**: 将脚本导出为.py文件
6. **脚本运行**: 安全执行Python脚本并获取执行结果
7. **运行监控**: 实时显示脚本执行状态和结果
8. **批量操作**: 支持批量删除脚本

### 脚本执行机制

1. **安全执行**: 使用临时文件执行脚本，避免影响系统
2. **超时控制**: 设置30秒执行超时，防止无限循环
3. **输出捕获**: 捕获脚本的标准输出和错误输出
4. **状态跟踪**: 实时更新脚本执行状态（空闲、运行中、已完成、失败）
5. **执行统计**: 记录脚本运行次数和最后运行时间

### 数据模型

```typescript
interface ScriptInfo {
  id: string;                    // 脚本ID
  name: string;                  // 脚本名称
  description?: string;          // 脚本描述
  content: string;               // 脚本内容
  createdAt: string;             // 创建时间
  updatedAt: string;             // 更新时间
  status: 'idle' | 'running' | 'completed' | 'failed';  // 执行状态
  lastRunTime?: string;          // 最后运行时间
  runCount: number;              // 运行次数
}

interface ScriptRunResult {
  success: boolean;              // 执行是否成功
  output?: string;               // 标准输出
  error?: string;                // 错误输出
  executionTime?: number;        // 执行时间(毫秒)
}
```

## 通信模块设计

### 核心组件

1. **TestMachineCommunicator**: TCP通信客户端
2. **Operation**: 高级操作封装

### 通信协议

```json
// 命令格式
{
    "action": "操作类型",
    "params": {"参数": "值"},
    "timestamp": 1234567890.123
}

// 响应格式
{
    "success": true,
    "data": {"结果": "数据"},
    "error": null,
    "message": "操作成功"
}
```

### 支持的操作类型

- 元素操作: 点击、右键点击、双击、设置文本
- 图像操作: 查找图像、点击图像
- 鼠标操作: 移动、拖拽、滚动
- 键盘操作: 文本输入、快捷键

## 使用指南

### 环境准备

1. Python 3.8+
2. Node.js 16+
3. 被测试机器运行自动化服务

### 快速启动

```bash
# 启动后端
cd backend
python main.py

# 启动前端
cd frontend
npm install
npm run dev
```

### 基本操作流程

1. 打开前端界面 (http://localhost:3000)
2. 输入被测试机器IP和端口
3. 点击连接按钮
4. 执行各种自动化操作
5. 查看操作历史和结果

### 脚本管理操作

#### 创建脚本
1. 进入"脚本管理"页面
2. 点击"新建脚本"按钮
3. 填写脚本名称、描述和内容
4. 点击"创建"按钮

#### 导入脚本
1. 点击"导入脚本"按钮
2. 选择本地.py文件
3. 点击"导入"按钮

#### 运行脚本
1. 在脚本列表中找到目标脚本
2. 点击"运行"按钮
3. 查看运行结果对话框

#### 编辑脚本
1. 点击脚本名称或"编辑"按钮
2. 修改脚本内容
3. 点击"保存"按钮

### 操作示例

```javascript
// 点击元素
await operationAPI.clickElement("button[0]", ["push button"]);

// 点击图片
await operationAPI.clickImage("/path/to/image.png", 0.8);

// 拖拽操作
await operationAPI.dragTo(100, 100, 200, 200);

// 脚本管理
await scriptAPI.createScript({
  name: "测试脚本",
  description: "这是一个测试脚本",
  content: "print('Hello World')"
});
```

## 开发指南

### 前端开发

- 使用Vue 3 Composition API
- TypeScript类型安全
- Element Plus组件库
- Pinia状态管理

### 后端开发

- FastAPI异步处理
- Pydantic数据验证
- 统一错误处理
- 详细日志记录

### 通信模块开发

- TCP Socket通信
- JSON命令协议
- 错误重试机制
- 连接状态管理

## 部署指南

### 开发环境

```bash
# 使用启动脚本
./start.sh  # Linux/Mac
start.bat   # Windows
```

### 生产环境

```bash
# 前端构建
npm run build

# 后端部署
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker部署

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports: ["3000:80"]
  backend:
    build: ./backend
    ports: ["8080:8080"]
```

## 故障排除

### 常见问题

1. **连接失败**: 检查网络和端口
2. **操作失败**: 检查元素路径和图像文件
3. **脚本执行失败**: 检查脚本语法和依赖
4. **性能问题**: 优化网络和图像处理

### 调试方法

- 查看浏览器开发者工具
- 检查后端日志文件
- 使用API测试脚本

## 总结

系统采用前后端分离架构，提供完整的GUI自动化测试解决方案。通过模块化设计，系统具有良好的可扩展性和维护性，支持多种自动化操作类型和完整的脚本管理功能，满足QGIS等桌面应用的自动化测试需求。
