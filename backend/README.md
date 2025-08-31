# 自动化测试后端服务 - Node.js版本

这是一个基于Node.js和Express.js的自动化测试后端服务，替代了原来的Python FastAPI版本。

## 🚀 特性

- **现代化架构**: 使用Node.js + Express.js构建
- **模块化设计**: 清晰的服务层和路由分离
- **完整日志**: 基于Winston的日志系统
- **安全防护**: 集成Helmet安全中间件
- **跨域支持**: 配置化的CORS支持
- **Python集成**: 通过子进程管理Python测试服务器
- **脚本管理**: 完整的脚本CRUD操作
- **多机器支持**: 支持多机器测试环境

## 📋 系统要求

- Node.js 16.0+ 
- Python 3.8+ (用于测试服务器)
- 支持的操作系统: Windows, Linux, macOS

## 🛠️ 安装

1. 克隆项目到本地
2. 进入backend目录
3. 安装依赖:

```bash
npm install
```

## 🚀 启动服务

### Windows
```bash
start.bat
```

### Linux/macOS
```bash
chmod +x start.sh
./start.sh
```

### 手动启动
```bash
npm start
```

## 📁 项目结构

```
backend/
├── src/
│   ├── app.js              # 主应用文件
│   ├── routes/             # 路由定义
│   │   ├── machines.js     # 机器管理
│   │   ├── apps.js         # 应用管理
│   │   ├── scripts.js      # 脚本管理
│   │   └── operations.js   # 操作执行
│   ├── services/           # 业务服务
│   │   ├── testServerService.js  # 测试服务器服务
│   │   └── scriptService.js      # 脚本管理服务
│   ├── middleware/         # 中间件
│   │   ├── errorHandler.js # 错误处理
│   │   └── logger.js       # 日志中间件
│   └── utils/              # 工具类
│       └── logger.js       # 日志工具
├── python-adapter/         # Python适配器
│   └── vscode_server.py    # VSCode服务器适配器
├── config/                 # 配置文件
│   └── index.js           # 配置管理
├── data/                   # 数据存储
│   └── scripts/           # 脚本文件
├── logs/                   # 日志文件
└── package.json            # 项目配置
```

## 🔧 配置

配置文件位于 `config/index.js`，支持环境变量配置：

```bash
# 服务器配置
PORT=8080
NODE_ENV=development

# 测试服务器配置
TEST_SERVER_HOST=0.0.0.0
TEST_SERVER_PORT=8888

# 日志配置
LOG_LEVEL=info
LOG_MAX_FILE_SIZE=5MB
LOG_MAX_FILES=5

# 安全配置
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 📡 API接口

### 核心接口

- `GET /health` - 健康检查
- `GET /api/status` - 服务器状态
- `POST /api/connect` - 启动测试服务器
- `POST /api/disconnect` - 停止测试服务器
- `POST /api/set-target` - 设置测试目标
- `GET /api/current-target` - 获取当前目标

### 机器管理

- `GET /api/machines` - 获取机器列表
- `GET /api/machines/:id` - 获取机器信息
- `POST /api/machines/:id/connect` - 连接机器
- `POST /api/machines/:id/disconnect` - 断开机器
- `GET /api/machines/:id/status` - 获取机器状态
- `GET /api/machines/:id/apps` - 获取机器应用

### 应用管理

- `GET /api/apps` - 获取应用列表
- `GET /api/apps/:id` - 获取应用信息
- `POST /api/apps/:id/start` - 启动应用
- `POST /api/apps/:id/stop` - 停止应用
- `GET /api/apps/:id/status` - 获取应用状态
- `GET /api/apps/:id/screenshot` - 获取应用截图

### 脚本管理

- `GET /api/scripts` - 获取脚本列表
- `GET /api/scripts/:id` - 获取脚本详情
- `POST /api/scripts` - 创建脚本
- `PUT /api/scripts/:id` - 更新脚本
- `DELETE /api/scripts/:id` - 删除脚本
- `POST /api/scripts/:id/execute` - 执行脚本
- `GET /api/scripts/stats/overview` - 脚本统计
- `POST /api/scripts/backup` - 备份脚本

### 操作执行

- `POST /api/operations/execute` - 执行测试操作
- `POST /api/operations/screenshot` - 获取截图
- `POST /api/operations/find-element` - 查找元素
- `POST /api/operations/click-element` - 点击元素
- `POST /api/operations/type-text` - 输入文本
- `POST /api/operations/wait-for-element` - 等待元素
- `POST /api/operations/send-hotkey` - 发送热键

## 🔌 Python集成

服务通过子进程管理Python测试服务器：

1. **启动**: 自动启动Python测试服务器进程
2. **通信**: 通过标准输入/输出进行JSON消息交换
3. **管理**: 监控进程状态，处理启动/停止

Python适配器脚本支持两种模式：
- **VSCode模式**: 与Node.js后端通信
- **独立模式**: 作为独立服务器运行

## 📊 日志系统

使用Winston日志库，支持：

- 多级别日志 (error, warn, info, debug)
- 文件轮转 (大小和数量限制)
- 结构化日志输出
- 请求/响应日志记录
- 错误堆栈跟踪

## 🛡️ 安全特性

- **Helmet**: 安全HTTP头设置
- **CORS**: 可配置的跨域资源共享
- **输入验证**: 请求参数验证
- **错误处理**: 安全的错误信息

## 🧪 开发

### 开发模式启动
```bash
npm run dev
```

### 代码检查
```bash
npm run lint
```

### 测试
```bash
npm test
```

## 📝 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| PORT | 8080 | 服务器端口 |
| NODE_ENV | development | 运行环境 |
| LOG_LEVEL | info | 日志级别 |
| ALLOWED_ORIGINS | localhost:3000,8080 | 允许的跨域源 |

## 🔍 故障排除

### 常见问题

1. **Python依赖缺失**
   - 确保安装了所需的Python包
   - 检查Python路径配置

2. **端口冲突**
   - 修改配置文件中的端口设置
   - 检查端口占用情况

3. **权限问题**
   - 确保有足够的文件系统权限
   - 检查日志目录权限

### 日志查看

日志文件位于 `logs/` 目录：
- `combined.log` - 所有日志
- `error.log` - 错误日志
- `exceptions.log` - 异常日志

## 📄 许可证

本项目采用MIT许可证。

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请查看：
1. 项目文档
2. 日志文件
3. GitHub Issues
