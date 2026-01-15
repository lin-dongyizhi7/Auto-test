# 自动化测试前端

基于 Vue3 + TypeScript + Element Plus 的多机器多应用自动化测试图形化界面。

## 功能特性

- 🎯 **多机器管理**: 支持同时连接和管理多台被测试机器
- 🔗 **连接管理**: 图形化配置与被测试机器的连接
- 🖱️ **元素操作**: 点击、右键、双击、文本输入等基础操作
- 🖼️ **图像识别**: 基于图片匹配的自动化操作
- 📊 **实时监控**: 实时显示操作状态和结果
- 📝 **脚本管理**: 创建、编辑、运行 JSON 格式的测试脚本
- ⚙️ **系统设置**: 灵活的配置选项

## 技术栈

- **前端框架**: Vue 3.3.4
- **开发语言**: TypeScript
- **UI组件库**: Element Plus 2.3.8
- **状态管理**: Pinia 2.1.6
- **路由管理**: Vue Router 4.2.4
- **HTTP客户端**: Axios 1.4.0
- **构建工具**: Vite 4.4.5
- **样式预处理**: SCSS

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API接口
│   │   ├── operation.ts   # 操作相关API
│   │   └── types.ts       # 类型定义
│   ├── assets/            # 资源文件
│   │   └── styles/        # 样式文件
│   │       ├── main.less  # Less样式
│   │       └── main.scss  # SCSS样式
│   ├── router/            # 路由配置
│   │   └── index.ts       # 路由定义
│   ├── stores/            # 状态管理
│   │   └── operation.ts   # 操作状态
│   ├── utils/             # 工具函数
│   │   └── request.ts     # HTTP请求工具
│   ├── views/             # 页面组件
│   │   ├── Dashboard.vue  # 仪表板
│   │   ├── MachineControl.vue # 机器控制
│   │   ├── Operation.vue  # 操作控制
│   │   ├── Monitor.vue    # 实时监控
│   │   ├── Script.vue     # 脚本管理
│   │   └── Settings.vue   # 系统设置
│   ├── App.vue            # 根组件
│   └── main.ts            # 入口文件
├── package.json           # 依赖配置
├── vite.config.ts         # Vite配置
├── tsconfig.json          # TypeScript配置
├── start.bat              # Windows启动脚本
└── start.sh               # Linux/macOS启动脚本
```

## 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

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
npm run dev
```

访问 http://localhost:3000 查看应用

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist` 目录

### 代码检查

```bash
npm run lint
```

### 类型检查

```bash
npm run type-check
```

## 核心功能

### 1. 仪表板 (Dashboard)

- **系统状态**: 显示连接状态、操作统计等
- **快速操作**: 提供常用操作的快捷入口
- **最近操作**: 显示最近的操作记录
- **统计信息**: 成功率、操作次数等统计

### 2. 机器控制 (MachineControl)

- **机器管理**: 连接/断开多台被测试机器
- **应用管理**: 查看和管理每台机器上的应用
- **目标设置**: 选择当前操作的机器和应用
- **状态监控**: 实时显示机器和应用状态

### 3. 操作控制 (Operation)

- **元素操作**: 点击、右键、双击、文本输入等
- **图像识别**: 图片查找和点击操作
- **键盘操作**: 快捷键和文本输入
- **等待操作**: 等待元素或图片出现
- **操作历史**: 实时记录和显示操作结果

### 4. 实时监控 (Monitor)

- **实时截图**: 显示被测试机器的屏幕截图
- **元素定位**: 可视化显示元素位置和属性
- **操作日志**: 实时显示操作执行日志
- **状态监控**: 连接状态、执行状态等

### 5. 脚本管理 (Script)

- **脚本创建**: 创建新的测试脚本
- **脚本编辑**: 可视化编辑和修改测试脚本
- **脚本运行**: 执行已保存的测试脚本
- **脚本存储**: 支持JSON格式的脚本文件

### 6. 系统设置 (Settings)

- **连接配置**: 后端API地址配置
- **操作配置**: 操作延迟、重试次数等参数
- **界面配置**: 主题、布局等个性化设置

## API接口

前端通过 HTTP API 与后端通信，主要接口包括：

### 服务器管理

```typescript
// 获取服务器状态
getServerStatus(): Promise<ServerStatus>

// 启动/停止内置测试服务器
startServer(port: number): Promise<OperationResult>
stopServer(): Promise<OperationResult>
```

### 机器管理

```typescript
// 获取机器列表
getMachines(): Promise<MachineList>

// 连接/断开机器
connectMachine(host: string): Promise<OperationResult>
disconnectMachine(machineId: string): Promise<OperationResult>

// 获取应用列表
getApps(): Promise<AppList>

// 设置操作目标
setTarget(machineId: string, appName: string): Promise<OperationResult>
```

### 操作相关

```typescript
// 元素操作
clickElement(path: string, roles?: string[]): Promise<OperationResult>
rightClickElement(path: string, roles?: string[]): Promise<OperationResult>
doubleClickElement(path: string, roles?: string[]): Promise<OperationResult>

// 图像操作
clickImage(imagePath: string, threshold?: number): Promise<OperationResult>
findImage(imagePath: string, threshold?: number): Promise<OperationResult>

// 键盘操作
sendHotkey(keys: string[]): Promise<OperationResult>
inputText(text: string, elementPath?: string): Promise<OperationResult>

// 等待操作
waitForElement(path: string, roles?: string[]): Promise<OperationResult>
waitForImage(imagePath: string, threshold?: number): Promise<OperationResult>

// 截图
getScreenshot(): Promise<ScreenshotResult>
```

### 脚本管理

```typescript
// 脚本CRUD
getScripts(): Promise<ScriptList>
getScript(id: string): Promise<ScriptInfo>
createScript(script: CreateScriptRequest): Promise<ScriptInfo>
updateScript(id: string, script: UpdateScriptRequest): Promise<ScriptInfo>
deleteScript(id: string): Promise<OperationResult>

// 脚本执行
runScript(id: string): Promise<ScriptRunResult>
```

## 状态管理

使用 Pinia 进行状态管理，主要包含：

- **操作状态**: 连接状态、操作历史、成功率等
- **机器状态**: 机器列表、应用列表、目标设置等
- **监控状态**: 截图信息、元素信息、日志消息等
- **脚本状态**: 脚本列表、创建/编辑状态、运行状态等

## 样式设计

- 采用 Element Plus 设计规范
- 响应式布局，支持桌面端和移动端
- 自定义主题色彩和组件样式
- 流畅的动画效果和交互反馈

## 开发指南

### 添加新页面

1. 在 `src/views/` 目录下创建新的 Vue 组件
2. 在 `src/router/index.ts` 中添加路由配置
3. 在 `src/App.vue` 的侧边栏菜单中添加导航项

### 添加新API

1. 在 `src/api/types.ts` 中定义相关类型
2. 在 `src/api/operation.ts` 中添加API方法
3. 在对应的 store 中使用API

### 添加新组件

1. 在 `src/components/` 目录下创建组件
2. 使用 TypeScript 和 Composition API
3. 添加适当的类型定义和文档

## 部署说明

### 开发环境

- 使用 Vite 开发服务器
- 支持热重载和源码映射
- 配置代理到后端 API 服务（默认 http://localhost:8080）

### 生产环境

- 构建静态文件：`npm run build`
- 使用 Nginx 等 Web 服务器部署
- 配置 API 代理和缓存策略

## 浏览器支持

- Chrome >= 88
- Firefox >= 85
- Safari >= 14
- Edge >= 88

## 常见问题

- **无法连接后端**: 检查后端服务是否启动（端口 8080）
- **操作失败**: 确认已设置正确的目标机器和应用
- **脚本执行失败**: 检查脚本格式和路径是否正确
- **样式问题**: 确保 Element Plus 组件正确引入
