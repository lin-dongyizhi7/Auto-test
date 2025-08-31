# 自动化测试服务器 VSCode 插件

这是一个用于管理和控制自动化测试服务器的 VSCode 插件，基于原有的 Python 测试服务器代码重构而成。

## 功能特性

- 🚀 **服务器管理**: 启动/停止测试服务器
- 🖥️ **机器监控**: 实时显示已连接机器状态
- 📱 **应用管理**: 查看和管理可用应用
- 🧪 **测试执行**: 直接在 VSCode 中执行测试脚本
- 📊 **状态监控**: 实时显示服务器运行状态
- 🎨 **现代界面**: 提供直观的图形化控制界面

## 安装说明

### 前置要求

- VSCode 1.60.0 或更高版本
- Python 3.7 或更高版本
- 原有的测试服务器代码库

### 安装步骤

1. **克隆或下载插件代码**
   ```bash
   git clone <repository-url>
   cd vscode-extension
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **编译插件**
   ```bash
   npm run compile
   ```

4. **打包插件**
   ```bash
   npm install -g vsce
   vsce package
   ```

5. **安装插件**
   - 在 VSCode 中按 `Ctrl+Shift+P`
   - 输入 "Extensions: Install from VSIX"
   - 选择生成的 `.vsix` 文件

## 使用方法

### 基本操作

1. **启动测试服务器**
   - 使用命令面板: `Ctrl+Shift+P` → "启动测试服务器"
   - 或点击状态栏的测试服务器图标

2. **查看控制台**
   - 在左侧活动栏点击"测试服务器"图标
   - 或使用命令: "显示测试控制台"

3. **管理机器和应用**
   - 在控制台中查看已连接的机器
   - 设置目标机器和应用
   - 执行测试脚本

### 命令列表

| 命令 | 描述 | 快捷键 |
|------|------|--------|
| `autoTestServer.start` | 启动测试服务器 | - |
| `autoTestServer.stop` | 停止测试服务器 | - |
| `autoTestServer.showPanel` | 显示测试控制台 | - |
| `autoTestServer.executeTest` | 执行测试脚本 | - |
| `autoTestServer.connectMachine` | 连接测试机器 | - |

### 配置选项

在 VSCode 设置中可以配置以下选项：

```json
{
    "autoTestServer.host": "0.0.0.0",
    "autoTestServer.port": 8888,
    "autoTestServer.retryInterval": 3
}
```

## 架构说明

### 核心组件

- **TestServerManager**: 测试服务器管理器，负责启动/停止服务器
- **MachineController**: 机器控制器，处理机器操作和测试执行
- **PythonBridge**: Python 桥接层，与原有 Python 服务器通信
- **TestServerPanel**: 测试服务器控制台界面
- **StatusBarManager**: 状态栏管理器

### 数据流

```
VSCode 插件 ↔ TypeScript 核心 ↔ Python 桥接 ↔ Python 测试服务器
```

### 文件结构

```
vscode-extension/
├── src/
│   ├── extension.ts              # 插件主入口
│   ├── core/                     # 核心功能模块
│   │   ├── testServerManager.ts  # 服务器管理器
│   │   ├── machineController.ts  # 机器控制器
│   │   └── pythonBridge.ts       # Python 桥接
│   └── ui/                       # 用户界面
│       ├── testServerPanel.ts    # 控制台面板
│       └── statusBarManager.ts   # 状态栏管理
├── package.json                  # 插件配置
├── tsconfig.json                 # TypeScript 配置
└── README.md                     # 说明文档
```

## 开发说明

### 开发环境设置

1. **安装开发依赖**
   ```bash
   npm install
   ```

2. **启动开发模式**
   ```bash
   npm run watch
   ```

3. **调试插件**
   - 按 `F5` 启动新的 VSCode 窗口
   - 在新窗口中测试插件功能

### 代码规范

- 使用 TypeScript 编写
- 遵循 VSCode 插件开发规范
- 使用 ESLint 进行代码检查

### 测试

```bash
npm run lint        # 代码检查
npm run compile     # 编译检查
```

## 故障排除

### 常见问题

1. **Python 服务器启动失败**
   - 检查 Python 环境是否正确安装
   - 确认原有测试服务器代码是否完整
   - 查看 VSCode 输出面板的错误信息

2. **插件无法激活**
   - 检查 VSCode 版本是否满足要求
   - 确认插件依赖是否正确安装
   - 查看开发者控制台的错误信息

3. **控制台显示异常**
   - 刷新控制台视图
   - 重启 VSCode
   - 检查网络连接状态

### 日志查看

- 在 VSCode 中按 `Ctrl+Shift+P`
- 输入 "Developer: Toggle Developer Tools"
- 查看控制台输出和网络请求

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的服务器管理功能
- 提供图形化控制界面
- 集成原有的 Python 测试服务器

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个插件。

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至 [your-email@example.com]

---

**注意**: 此插件需要配合原有的 Python 测试服务器代码使用。请确保在安装插件前，原有的测试服务器代码能够正常运行。
