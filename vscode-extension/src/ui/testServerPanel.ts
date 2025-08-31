import * as vscode from 'vscode';
import { TestServerManager } from '../core/testServerManager';
import { MachineController } from '../core/machineController';

export class TestServerPanel implements vscode.WebviewViewProvider {
    public static readonly viewType = 'testServerPanel';
    private _view?: vscode.WebviewView;

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private readonly testServerManager: TestServerManager,
        private readonly machineController: MachineController
    ) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                this._extensionUri
            ]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // 处理来自webview的消息
        webviewView.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'startServer':
                    await this.handleStartServer(message.host, message.port);
                    break;
                case 'stopServer':
                    await this.handleStopServer();
                    break;
                case 'refreshMachines':
                    await this.handleRefreshMachines();
                    break;
                case 'refreshApps':
                    await this.handleRefreshApps();
                    break;
                case 'setTarget':
                    await this.handleSetTarget(message.machineId, message.appName);
                    break;
                case 'executeTest':
                    await this.handleExecuteTest(message.scriptPath);
                    break;
                case 'getScreenshot':
                    await this.handleGetScreenshot(message.region);
                    break;
                case 'findElement':
                    await this.handleFindElement(message.elementPath, message.roleNames);
                    break;
                case 'clickElement':
                    await this.handleClickElement(message.elementPath);
                    break;
                case 'typeText':
                    await this.handleTypeText(message.text);
                    break;
            }
        });

        // 定期更新状态
        this.startStatusUpdates();
    }

    private async handleStartServer(host: string, port: number): Promise<void> {
        try {
            const success = await this.testServerManager.startServer(host, port);
            if (success) {
                this._view?.webview.postMessage({
                    command: 'serverStarted',
                    host,
                    port
                });
            } else {
                this._view?.webview.postMessage({
                    command: 'serverError',
                    error: '启动服务器失败'
                });
            }
        } catch (error) {
            this._view?.webview.postMessage({
                command: 'serverError',
                error: error instanceof Error ? error.message : String(error)
            });
        }
    }

    private async handleStopServer(): Promise<void> {
        try {
            await this.testServerManager.stopServer();
            this._view?.webview.postMessage({
                command: 'serverStopped'
            });
        } catch (error) {
            this._view?.webview.postMessage({
                command: 'serverError',
                error: error instanceof Error ? error.message : String(error)
            });
        }
    }

    private async handleRefreshMachines(): Promise<void> {
        try {
            await this.testServerManager.refreshMachines();
            const machines = this.testServerManager.getAvailableMachines();
            this._view?.webview.postMessage({
                command: 'machinesUpdated',
                machines: machines.map(id => this.testServerManager.getMachineStatus(id)).filter(Boolean)
            });
        } catch (error) {
            console.error('刷新机器状态失败:', error);
        }
    }

    private async handleRefreshApps(): Promise<void> {
        try {
            await this.testServerManager.refreshApps();
            const apps = this.testServerManager.getAvailableApps();
            this._view?.webview.postMessage({
                command: 'appsUpdated',
                apps: apps.map(key => {
                    const [machineId, appName] = key.split(':');
                    return this.testServerManager.getAppStatus(appName, machineId);
                }).filter(Boolean)
            });
        } catch (error) {
            console.error('刷新应用状态失败:', error);
        }
    }

    private async handleSetTarget(machineId: string, appName: string): Promise<void> {
        try {
            const success = await this.testServerManager.setTarget(machineId, appName);
            if (success) {
                this._view?.webview.postMessage({
                    command: 'targetSet',
                    machineId,
                    appName
                });
            } else {
                this._view?.webview.postMessage({
                    command: 'targetError',
                    error: '设置目标失败'
                });
            }
        } catch (error) {
            this._view?.webview.postMessage({
                command: 'targetError',
                error: error instanceof Error ? error.message : String(error)
            });
        }
    }

    private async handleExecuteTest(scriptPath: string): Promise<void> {
        try {
            const result = await this.machineController.executeTest(scriptPath);
            this._view?.webview.postMessage({
                command: 'testExecuted',
                result
            });
        } catch (error) {
            this._view?.webview.postMessage({
                command: 'testError',
                error: error instanceof Error ? error.message : String(error)
            });
        }
    }

    private async handleGetScreenshot(region?: number[]): Promise<void> {
        try {
            const result = await this.machineController.getScreenshot(region);
            this._view?.webview.postMessage({
                command: 'screenshotTaken',
                result
            });
        } catch (error) {
            this._view?.webview.postMessage({
                command: 'screenshotError',
                error: error instanceof Error ? error.message : String(error)
            });
        }
    }

    private async handleFindElement(elementPath: string, roleNames?: string[]): Promise<void> {
        try {
            const result = await this.machineController.findElement(elementPath, roleNames);
            this._view?.webview.postMessage({
                command: 'elementFound',
                result
            });
        } catch (error) {
            this._view?.webview.postMessage({
                command: 'elementError',
                error: error instanceof Error ? error.message : String(error)
            });
        }
    }

    private async handleClickElement(elementPath: string): Promise<void> {
        try {
            const result = await this.machineController.clickElement(elementPath);
            this._view?.webview.postMessage({
                command: 'elementClicked',
                result
            });
        } catch (error) {
            this._view?.webview.postMessage({
                command: 'clickError',
                error: error instanceof Error ? error.message : String(error)
            });
        }
    }

    private async handleTypeText(text: string): Promise<void> {
        try {
            const result = await this.machineController.typeText(text);
            this._view?.webview.postMessage({
                command: 'textTyped',
                result
            });
        } catch (error) {
            this._view?.webview.postMessage({
                command: 'typeError',
                error: error instanceof Error ? error.message : String(error)
            });
        }
    }

    private startStatusUpdates(): void {
        const updateInterval = setInterval(() => {
            if (this._view) {
                const status = this.testServerManager.getServerStatus();
                const currentTarget = this.testServerManager.getCurrentTarget();
                
                this._view.webview.postMessage({
                    command: 'statusUpdate',
                    status,
                    currentTarget
                });
            }
        }, 2000);

        // 清理定时器
        this._view?.onDidDispose(() => {
            clearInterval(updateInterval);
        });
    }

    public show(): void {
        if (this._view) {
            this._view.show(true);
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview): string {
        return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试服务器控制台</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            margin: 0;
            padding: 16px;
        }
        
        .container {
            max-width: 100%;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        
        .controls {
            display: flex;
            gap: 8px;
        }
        
        .btn {
            padding: 6px 12px;
            border: 1px solid var(--vscode-button-border);
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .btn:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        
        .btn-primary {
            background-color: var(--vscode-button-prominentBackground);
            color: var(--vscode-button-prominentForeground);
        }
        
        .btn-danger {
            background-color: var(--vscode-errorForeground);
            color: var(--vscode-button-foreground);
        }
        
        .status-section, .machines-section, .apps-section, .test-section {
            margin-bottom: 20px;
            padding: 16px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            background-color: var(--vscode-editor-background);
        }
        
        .status-info {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 8px;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        
        .status-running {
            background-color: var(--vscode-debugIcon-startForeground);
        }
        
        .status-stopped {
            background-color: var(--vscode-errorForeground);
        }
        
        .machines-grid, .apps-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }
        
        .machine-card, .app-card {
            padding: 12px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            background-color: var(--vscode-input-background);
        }
        
        .machine-card.connected {
            border-color: var(--vscode-debugIcon-startForeground);
        }
        
        .app-card.running {
            border-color: var(--vscode-debugIcon-startForeground);
        }
        
        .test-controls {
            display: flex;
            gap: 12px;
            align-items: center;
            margin-top: 12px;
        }
        
        .file-input {
            flex: 1;
            padding: 6px;
            border: 1px solid var(--vscode-input-border);
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 4px;
        }
        
        .btn-success {
            background-color: var(--vscode-debugIcon-startForeground);
            color: var(--vscode-button-foreground);
        }
        
        .log-section {
            margin-top: 20px;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            background-color: var(--vscode-input-background);
            padding: 12px;
        }
        
        .log-entry {
            margin-bottom: 8px;
            padding: 4px 0;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        
        .log-timestamp {
            color: var(--vscode-descriptionForeground);
            font-size: 11px;
        }
        
        .log-message {
            margin-top: 2px;
        }
        
        .log-success {
            color: var(--vscode-debugIcon-startForeground);
        }
        
        .log-error {
            color: var(--vscode-errorForeground);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>测试服务器控制台</h2>
            <div class="controls">
                <button id="startBtn" class="btn btn-primary">启动服务器</button>
                <button id="stopBtn" class="btn btn-danger">停止服务器</button>
                <button id="refreshBtn" class="btn">刷新状态</button>
            </div>
        </div>
        
        <div class="status-section">
            <h3>服务器状态</h3>
            <div id="serverStatus" class="status-info">
                <span class="status-indicator status-stopped"></span>
                <span>服务器已停止</span>
            </div>
        </div>
        
        <div class="machines-section">
            <h3>已连接机器</h3>
            <div id="machinesList" class="machines-grid">
                <div class="machine-card">
                    <div>暂无机器连接</div>
                </div>
            </div>
        </div>
        
        <div class="apps-section">
            <h3>可用应用</h3>
            <div id="appsList" class="apps-grid">
                <div class="app-card">
                    <div>暂无应用可用</div>
                </div>
            </div>
        </div>
        
        <div class="test-section">
            <h3>测试执行</h3>
            <div class="test-controls">
                <input type="file" id="scriptFile" class="file-input" accept=".py,.js,.ts" />
                <button id="executeBtn" class="btn btn-success">执行测试</button>
                <button id="screenshotBtn" class="btn">截图</button>
            </div>
        </div>
        
        <div class="log-section">
            <h3>操作日志</h3>
            <div id="logEntries"></div>
        </div>
    </div>
    
    <script>
        const vscode = acquireVsCodeApi();
        
        // 状态管理
        let serverStatus = { isRunning: false, host: '0.0.0.0', port: 8888 };
        let currentTarget = null;
        let machines = [];
        let apps = [];
        
        // DOM元素
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const refreshBtn = document.getElementById('refreshBtn');
        const executeBtn = document.getElementById('executeBtn');
        const screenshotBtn = document.getElementById('screenshotBtn');
        const scriptFile = document.getElementById('scriptFile');
        const serverStatusEl = document.getElementById('serverStatus');
        const machinesListEl = document.getElementById('machinesList');
        const appsListEl = document.getElementById('appsList');
        const logEntriesEl = document.getElementById('logEntries');
        
        // 事件监听
        startBtn.addEventListener('click', () => {
            vscode.postMessage({
                command: 'startServer',
                host: serverStatus.host,
                port: serverStatus.port
            });
        });
        
        stopBtn.addEventListener('click', () => {
            vscode.postMessage({
                command: 'stopServer'
            });
        });
        
        refreshBtn.addEventListener('click', () => {
            vscode.postMessage({ command: 'refreshMachines' });
            vscode.postMessage({ command: 'refreshApps' });
        });
        
        executeBtn.addEventListener('click', () => {
            if (scriptFile.files.length > 0) {
                vscode.postMessage({
                    command: 'executeTest',
                    scriptPath: scriptFile.files[0].path
                });
            }
        });
        
        screenshotBtn.addEventListener('click', () => {
            vscode.postMessage({
                command: 'getScreenshot'
            });
        });
        
        // 消息处理
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.command) {
                case 'statusUpdate':
                    updateStatus(message.status, message.currentTarget);
                    break;
                case 'serverStarted':
                    updateServerStatus(true, message.host, message.port);
                    addLogEntry('服务器已启动', 'success');
                    break;
                case 'serverStopped':
                    updateServerStatus(false);
                    addLogEntry('服务器已停止', 'success');
                    break;
                case 'machinesUpdated':
                    updateMachinesList(message.machines);
                    break;
                case 'appsUpdated':
                    updateAppsList(message.apps);
                    break;
                case 'targetSet':
                    currentTarget = { machineId: message.machineId, appName: message.appName };
                    addLogEntry(\`目标已设置: \${message.machineId}:\${message.appName}\`, 'success');
                    break;
                case 'testExecuted':
                    if (message.result.success) {
                        addLogEntry('测试脚本执行成功', 'success');
                    } else {
                        addLogEntry(\`测试脚本执行失败: \${message.result.error}\`, 'error');
                    }
                    break;
                case 'screenshotTaken':
                    if (message.result.success) {
                        addLogEntry('截图已获取', 'success');
                    } else {
                        addLogEntry(\`截图失败: \${message.result.error}\`, 'error');
                    }
                    break;
            }
        });
        
        // 更新服务器状态
        function updateServerStatus(isRunning, host = '0.0.0.0', port = 8888) {
            serverStatus = { isRunning, host, port };
            updateStatus(serverStatus, currentTarget);
        }
        
        // 更新状态显示
        function updateStatus(status, target) {
            const statusEl = serverStatusEl.querySelector('span:last-child');
            const indicatorEl = serverStatusEl.querySelector('.status-indicator');
            
            if (status.isRunning) {
                statusEl.textContent = \`服务器运行中 (\${status.host}:\${status.port})\`;
                indicatorEl.className = 'status-indicator status-running';
                startBtn.disabled = true;
                stopBtn.disabled = false;
            } else {
                statusEl.textContent = '服务器已停止';
                indicatorEl.className = 'status-indicator status-stopped';
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
        }
        
        // 更新机器列表
        function updateMachinesList(machinesList) {
            machines = machinesList;
            if (machines.length === 0) {
                machinesListEl.innerHTML = '<div class="machine-card">暂无机器连接</div>';
                return;
            }
            
            machinesListEl.innerHTML = machines.map(machine => \`
                <div class="machine-card \${machine.status === 'connected' ? 'connected' : ''}">
                    <div><strong>\${machine.id}</strong></div>
                    <div>\${machine.host}:\${machine.port}</div>
                    <div>状态: \${machine.status}</div>
                    <div>应用: \${machine.apps.join(', ')}</div>
                </div>
            \`).join('');
        }
        
        // 更新应用列表
        function updateAppsList(appsList) {
            apps = appsList;
            if (apps.length === 0) {
                appsListEl.innerHTML = '<div class="app-card">暂无应用可用</div>';
                return;
            }
            
            appsListEl.innerHTML = apps.map(app => \`
                <div class="app-card \${app.status === 'running' ? 'running' : ''}">
                    <div><strong>\${app.name}</strong></div>
                    <div>机器: \${app.machineId}</div>
                    <div>状态: \${app.status}</div>
                    <button onclick="setTarget('\${app.machineId}', '\${app.name}')" class="btn">设为目标</button>
                </div>
            \`).join('');
        }
        
        // 设置目标
        function setTarget(machineId, appName) {
            vscode.postMessage({
                command: 'setTarget',
                machineId,
                appName
            });
        }
        
        // 添加日志条目
        function addLogEntry(message, type = 'info') {
            const logEntry = document.createElement('div');
            logEntry.className = \`log-entry log-\${type}\`;
            
            const timestamp = document.createElement('div');
            timestamp.className = 'log-timestamp';
            timestamp.textContent = new Date().toLocaleTimeString();
            
            const messageEl = document.createElement('div');
            messageEl.className = 'log-message';
            messageEl.textContent = message;
            
            logEntry.appendChild(timestamp);
            logEntry.appendChild(messageEl);
            
            logEntriesEl.appendChild(logEntry);
            logEntriesEl.scrollTop = logEntriesEl.scrollHeight;
            
            // 限制日志条目数量
            while (logEntriesEl.children.length > 50) {
                logEntriesEl.removeChild(logEntriesEl.firstChild);
            }
        }
        
        // 初始化
        updateStatus(serverStatus, currentTarget);
        addLogEntry('测试服务器控制台已加载', 'success');
    </script>
</body>
</html>`;
    }
}
