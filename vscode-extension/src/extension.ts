import * as vscode from 'vscode';
import { TestServerManager } from './core/testServerManager';
import { TestServerPanel } from './ui/testServerPanel';
import { StatusBarManager } from './ui/statusBarManager';
import { MachineController } from './core/machineController';

export function activate(context: vscode.ExtensionContext) {
    console.log('自动化测试服务器扩展已激活');

    // 创建核心管理器
    const testServerManager = new TestServerManager();
    const machineController = new MachineController(testServerManager);
    
    // 创建UI组件
    const statusBarManager = new StatusBarManager(testServerManager);
    const testServerPanel = new TestServerPanel(context.extensionUri, testServerManager, machineController);

    // 注册命令
    context.subscriptions.push(
        vscode.commands.registerCommand('autoTestServer.start', async () => {
            try {
                const config = vscode.workspace.getConfiguration('autoTestServer');
                const host = config.get<string>('host', '0.0.0.0');
                const port = config.get<number>('port', 8888);
                
                await testServerManager.startServer(host, port);
                vscode.window.showInformationMessage(`测试服务器已启动 (${host}:${port})`);
                statusBarManager.updateStatus();
            } catch (error) {
                vscode.window.showErrorMessage(`启动测试服务器失败: ${error}`);
            }
        }),

        vscode.commands.registerCommand('autoTestServer.stop', async () => {
            try {
                await testServerManager.stopServer();
                vscode.window.showInformationMessage('测试服务器已停止');
                statusBarManager.updateStatus();
            } catch (error) {
                vscode.window.showErrorMessage(`停止测试服务器失败: ${error}`);
            }
        }),

        vscode.commands.registerCommand('autoTestServer.showPanel', () => {
            testServerPanel.show();
        }),

        vscode.commands.registerCommand('autoTestServer.executeTest', async (scriptPath?: string) => {
            if (!scriptPath) {
                const uris = await vscode.window.showOpenDialog({
                    canSelectFiles: true,
                    canSelectFolders: false,
                    canSelectMany: false,
                    filters: {
                        'Python Files': ['py'],
                        'JavaScript Files': ['js'],
                        'TypeScript Files': ['ts']
                    }
                });
                
                if (uris && uris.length > 0) {
                    scriptPath = uris[0].fsPath;
                }
            }

            if (scriptPath) {
                try {
                    const result = await machineController.executeTest(scriptPath);
                    if (result.success) {
                        vscode.window.showInformationMessage('测试脚本执行成功');
                    } else {
                        vscode.window.showErrorMessage(`测试脚本执行失败: ${result.error}`);
                    }
                } catch (error) {
                    vscode.window.showErrorMessage(`执行测试脚本时发生错误: ${error}`);
                }
            }
        }),

        vscode.commands.registerCommand('autoTestServer.connectMachine', async () => {
            const machineId = await vscode.window.showInputBox({
                prompt: '请输入机器ID',
                placeHolder: '例如: machine_001'
            });

            if (machineId) {
                try {
                    const result = await machineController.connectMachine(machineId);
                    if (result.success) {
                        vscode.window.showInformationMessage(`成功连接到机器: ${machineId}`);
                    } else {
                        vscode.window.showErrorMessage(`连接机器失败: ${result.error}`);
                    }
                } catch (error) {
                    vscode.window.showErrorMessage(`连接机器时发生错误: ${error}`);
                }
            }
        })
    );

    // 注册视图提供者
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            'testServerPanel',
            testServerPanel,
            {
                webviewOptions: {
                    retainContextWhenHidden: true
                }
            }
        )
    );

    // 初始化状态栏
    statusBarManager.createStatusBar();

    // 定期更新状态
    const statusUpdateInterval = setInterval(() => {
        statusBarManager.updateStatus();
    }, 5000);

    context.subscriptions.push({
        dispose: () => {
            clearInterval(statusUpdateInterval);
        }
    });
}

export function deactivate() {
    console.log('自动化测试服务器扩展已停用');
}
