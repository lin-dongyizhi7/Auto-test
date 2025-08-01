# QGIS自动化测试前端设计方案

## 1. 项目概述

### 1.1 设计目标
构建一个基于Vue3的图形化前端界面，用于：
- 可视化配置和管理QGIS自动化测试
- 实时监控测试执行状态
- 提供直观的操作界面和结果展示
- 支持测试脚本的录制、编辑和回放

### 1.2 技术栈
- **前端框架**: Vue 3 + TypeScript
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由管理**: Vue Router
- **HTTP客户端**: Axios
- **构建工具**: Vite
- **样式**: SCSS + Tailwind CSS

## 2. 系统架构

### 2.1 整体架构
```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   Vue3 前端     │ ←────────────→ │   Python 后端   │
│   (Frontend)    │    8080端口    │   (Backend)     │
└─────────────────┘                └─────────────────┘
        │                                    │
        │                                    │
        ▼                                    ▼
┌─────────────────┐                ┌─────────────────┐
│   Element Plus  │                │   FastAPI       │
│   (UI组件)      │                │   (Web服务)     │
└─────────────────┘                └─────────────────┘
        │                                    │
        ▼                                    ▼
┌─────────────────┐                ┌─────────────────┐
│   Pinia Store   │                │   Operation.py  │
│   (状态管理)     │                │   (操作封装)    │
└─────────────────┘                └─────────────────┘
```

### 2.2 目录结构
```
frontend/
├── public/
│   ├── favicon.ico
│   └── images/
├── src/
│   ├── assets/
│   │   ├── styles/
│   │   └── images/
│   ├── components/
│   │   ├── common/
│   │   ├── operation/
│   │   └── monitor/
│   ├── views/
│   │   ├── Dashboard.vue
│   │   ├── Operation.vue
│   │   ├── Monitor.vue
│   │   └── Settings.vue
│   ├── stores/
│   │   ├── operation.ts
│   │   ├── monitor.ts
│   │   └── settings.ts
│   ├── api/
│   │   ├── operation.ts
│   │   ├── monitor.ts
│   │   └── types.ts
│   ├── utils/
│   │   ├── request.ts
│   │   └── helpers.ts
│   ├── router/
│   │   └── index.ts
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 3. 核心功能模块

### 3.1 操作控制模块 (Operation)
- **连接管理**: 建立/断开与被测试机器的连接
- **元素操作**: 点击、右键、双击、文本输入等
- **图像识别**: 图片查找和点击
- **拖拽操作**: 支持绝对坐标和百分比拖拽
- **键盘操作**: 按键和组合键操作

### 3.2 监控模块 (Monitor)
- **实时截图**: 显示被测试机器的实时屏幕
- **元素定位**: 可视化显示元素位置和属性
- **操作日志**: 实时显示操作执行日志
- **状态监控**: 连接状态、执行状态等

### 3.3 脚本管理模块 (Script)
- **脚本录制**: 记录用户操作生成测试脚本
- **脚本编辑**: 可视化编辑和修改测试脚本
- **脚本回放**: 执行已保存的测试脚本
- **脚本导入/导出**: 支持JSON格式的脚本文件

### 3.4 配置管理模块 (Settings)
- **连接配置**: 被测试机器IP和端口配置
- **操作配置**: 操作延迟、重试次数等参数
- **界面配置**: 主题、布局等个性化设置

## 4. 页面设计

### 4.1 主界面布局
```
┌─────────────────────────────────────────────────────────┐
│                   顶部导航栏                              │
├─────────────┬─────────────────────────┬─────────────────┤
│             │                         │                 │
│   侧边栏    │        主内容区          │    右侧面板     │
│  (菜单)     │      (操作/监控)         │   (属性/日志)   │
│             │                         │                 │
│             │                         │                 │
│             │                         │                 │
└─────────────┴─────────────────────────┴─────────────────┘
```

### 4.2 核心页面

#### 4.2.1 仪表板 (Dashboard)
- 系统状态概览
- 快速操作按钮
- 最近执行的测试
- 统计信息展示

#### 4.2.2 操作控制台 (Operation)
- 连接状态显示
- 操作按钮面板
- 参数配置区域
- 执行结果展示

#### 4.2.3 实时监控 (Monitor)
- 屏幕截图显示
- 元素高亮显示
- 操作轨迹绘制
- 实时日志流

#### 4.2.4 脚本管理 (Script)
- 脚本列表
- 脚本编辑器
- 录制控制
- 回放控制

## 5. 数据流设计

### 5.1 状态管理 (Pinia)
```typescript
// 操作状态
interface OperationState {
  isConnected: boolean
  targetHost: string
  targetPort: number
  currentOperation: string
  operationHistory: Operation[]
}

// 监控状态
interface MonitorState {
  screenshot: string
  elementInfo: ElementInfo
  logMessages: LogMessage[]
  connectionStatus: ConnectionStatus
}

// 脚本状态
interface ScriptState {
  scripts: TestScript[]
  currentScript: TestScript | null
  isRecording: boolean
  isPlaying: boolean
}
```

### 5.2 API接口设计
```typescript
// 操作相关API
interface OperationAPI {
  connect(host: string, port: number): Promise<boolean>
  disconnect(): Promise<void>
  clickElement(path: string, roles?: string[]): Promise<Result>
  clickImage(imagePath: string, threshold?: number): Promise<Result>
  dragTo(startX: number, startY: number, endX: number, endY: number): Promise<Result>
  inputText(text: string, elementPath?: string): Promise<Result>
}

// 监控相关API
interface MonitorAPI {
  getScreenshot(): Promise<string>
  getElementInfo(path: string): Promise<ElementInfo>
  getLogs(): Promise<LogMessage[]>
  getStatus(): Promise<ConnectionStatus>
}
```

## 6. 组件设计

### 6.1 通用组件
- **ConnectionPanel**: 连接状态和配置
- **OperationPanel**: 操作按钮面板
- **ScreenshotViewer**: 截图显示组件
- **LogViewer**: 日志显示组件
- **ElementInspector**: 元素信息查看器

### 6.2 操作组件
- **ClickButton**: 点击操作按钮
- **DragPanel**: 拖拽操作面板
- **TextInput**: 文本输入组件
- **ImageSelector**: 图片选择组件
- **HotkeyPanel**: 快捷键操作面板

### 6.3 监控组件
- **RealTimeScreenshot**: 实时截图组件
- **ElementHighlighter**: 元素高亮组件
- **OperationTracker**: 操作轨迹组件
- **StatusIndicator**: 状态指示器

## 7. 交互设计

### 7.1 操作流程
1. **连接建立**: 用户输入目标机器IP和端口，点击连接
2. **操作执行**: 用户选择操作类型，配置参数，点击执行
3. **结果反馈**: 系统显示操作结果和截图
4. **日志记录**: 所有操作记录到日志中

### 7.2 脚本录制流程
1. **开始录制**: 用户点击录制按钮
2. **操作记录**: 系统自动记录用户操作
3. **停止录制**: 用户点击停止按钮
4. **脚本保存**: 系统生成可执行的测试脚本

### 7.3 脚本回放流程
1. **选择脚本**: 用户从脚本列表中选择要执行的脚本
2. **参数配置**: 用户配置脚本执行参数
3. **开始回放**: 系统按顺序执行脚本中的操作
4. **结果验证**: 系统验证每个操作的执行结果

## 8. 响应式设计

### 8.1 断点设计
- **桌面端**: ≥1200px
- **平板端**: 768px - 1199px
- **移动端**: <768px

### 8.2 布局适配
- 桌面端：三栏布局
- 平板端：双栏布局
- 移动端：单栏布局

## 9. 性能优化

### 9.1 前端优化
- 组件懒加载
- 图片懒加载
- 虚拟滚动
- 防抖节流

### 9.2 通信优化
- WebSocket实时通信
- 请求缓存
- 图片压缩
- 分页加载

## 10. 安全考虑

### 10.1 网络安全
- HTTPS通信
- API认证
- 请求限流
- 输入验证

### 10.2 数据安全
- 敏感信息加密
- 操作日志审计
- 权限控制
- 数据备份

## 11. 部署方案

### 11.1 开发环境
- Vite开发服务器
- 热重载
- 源码映射
- 调试工具

### 11.2 生产环境
- Nginx静态文件服务
- CDN加速
- 压缩优化
- 缓存策略

## 12. 测试策略

### 12.1 单元测试
- 组件测试
- 工具函数测试
- API接口测试

### 12.2 集成测试
- 页面流程测试
- 状态管理测试
- 路由测试

### 12.3 E2E测试
- 用户操作流程测试
- 跨浏览器兼容性测试
- 性能测试

## 13. 后续扩展

### 13.1 功能扩展
- 多机器管理
- 测试报告生成
- 性能监控
- 插件系统

### 13.2 技术扩展
- PWA支持
- 离线功能
- 多语言支持
- 主题定制 