# 自动化测试前端

基于Vue3 + TypeScript + Element Plus的自动化测试图形化界面。

## 功能特性

- 🎯 **可视化操作控制**: 提供直观的图形界面进行QGIS自动化操作
- 🔗 **连接管理**: 支持与被测试机器的连接配置和管理
- 🖱️ **元素操作**: 点击、右键、双击、文本输入等基础操作
- 🖼️ **图像识别**: 基于图片匹配的自动化操作
- 📊 **实时监控**: 实时显示操作状态和结果
- 📝 **操作历史**: 记录和查看操作历史记录
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
│   │   ├── monitor.ts     # 监控相关API
│   │   └── types.ts       # 类型定义
│   ├── assets/            # 资源文件
│   │   └── styles/        # 样式文件
│   ├── components/        # 组件
│   ├── router/            # 路由配置
│   ├── stores/            # 状态管理
│   │   └── operation.ts   # 操作状态
│   ├── utils/             # 工具函数
│   │   └── request.ts     # HTTP请求工具
│   ├── views/             # 页面组件
│   │   ├── Dashboard.vue  # 仪表板
│   │   ├── Operation.vue  # 操作控制
│   │   ├── Monitor.vue    # 实时监控
│   │   ├── Script.vue     # 脚本管理
│   │   └── Settings.vue   # 系统设置
│   ├── App.vue            # 根组件
│   └── main.ts            # 入口文件
├── package.json           # 依赖配置
├── vite.config.ts         # Vite配置
└── tsconfig.json          # TypeScript配置
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

### 1. 操作控制 (Operation)

- **连接管理**: 建立/断开与被测试机器的连接
- **元素操作**: 点击、右键、双击、文本输入等
- **图像识别**: 图片查找和点击操作
- **拖拽操作**: 支持绝对坐标和百分比拖拽
- **操作历史**: 实时记录和显示操作结果

### 2. 仪表板 (Dashboard)

- **系统状态**: 显示连接状态、操作统计等
- **快速操作**: 提供常用操作的快捷入口
- **最近操作**: 显示最近的操作记录
- **统计信息**: 成功率、操作次数等统计

### 3. 实时监控 (Monitor)

- **实时截图**: 显示被测试机器的屏幕截图
- **元素定位**: 可视化显示元素位置和属性
- **操作日志**: 实时显示操作执行日志
- **状态监控**: 连接状态、执行状态等

### 4. 脚本管理 (Script)

- **脚本录制**: 记录用户操作生成测试脚本
- **脚本编辑**: 可视化编辑和修改测试脚本
- **脚本回放**: 执行已保存的测试脚本
- **脚本导入/导出**: 支持JSON格式的脚本文件

### 5. 系统设置 (Settings)

- **连接配置**: 被测试机器IP和端口配置
- **操作配置**: 操作延迟、重试次数等参数
- **界面配置**: 主题、布局等个性化设置

## API接口

### 操作相关API

```typescript
// 连接目标机器
connect(host: string, port: number): Promise<boolean>

// 点击元素
clickElement(path: string, roles?: string[]): Promise<OperationResult>

// 点击图片
clickImage(imagePath: string, threshold?: number): Promise<OperationResult>

// 拖拽操作
dragTo(startX: number, startY: number, endX: number, endY: number): Promise<OperationResult>

// 输入文本
inputText(text: string, elementPath?: string): Promise<OperationResult>
```

### 监控相关API

```typescript
// 获取截图
getScreenshot(): Promise<ScreenshotInfo>

// 获取元素信息
getElementInfo(path: string): Promise<ElementInfo>

// 获取日志
getLogs(): Promise<LogMessage[]>
```

## 状态管理

使用Pinia进行状态管理，主要包含：

- **操作状态**: 连接状态、操作历史、成功率等
- **监控状态**: 截图信息、元素信息、日志消息等
- **脚本状态**: 脚本列表、录制状态、回放状态等

## 样式设计

- 采用Element Plus设计规范
- 响应式布局，支持桌面端和移动端
- 自定义主题色彩和组件样式
- 流畅的动画效果和交互反馈

## 开发指南

### 添加新页面

1. 在 `src/views/` 目录下创建新的Vue组件
2. 在 `src/router/index.ts` 中添加路由配置
3. 在 `src/App.vue` 的侧边栏菜单中添加导航项

### 添加新API

1. 在 `src/api/types.ts` 中定义相关类型
2. 在 `src/api/` 目录下创建API文件
3. 在对应的store中使用API

### 添加新组件

1. 在 `src/components/` 目录下创建组件
2. 使用TypeScript和Composition API
3. 添加适当的类型定义和文档

## 部署说明

### 开发环境

- 使用Vite开发服务器
- 支持热重载和源码映射
- 配置代理到后端API服务

### 生产环境

- 构建静态文件
- 使用Nginx等Web服务器部署
- 配置API代理和缓存策略

## 浏览器支持

- Chrome >= 88
- Firefox >= 85
- Safari >= 14
- Edge >= 88

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

如有问题或建议，请提交 Issue 或联系开发团队。
