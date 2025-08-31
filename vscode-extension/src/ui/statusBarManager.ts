import * as vscode from 'vscode';
import { TestServerManager } from '../core/testServerManager';

export class StatusBarManager {
    private statusBarItem: vscode.StatusBarItem;
    private testServerManager: TestServerManager;

    constructor(testServerManager: TestServerManager) {
        this.testServerManager = testServerManager;
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
    }

    createStatusBar(): void {
        this.statusBarItem.command = 'autoTestServer.showPanel';
        this.statusBarItem.tooltip = '点击显示测试服务器控制台';
        this.updateStatus();
        this.statusBarItem.show();
    }

    updateStatus(): void {
        const status = this.testServerManager.getServerStatus();
        const currentTarget = this.testServerManager.getCurrentTarget();
        
        if (status.isRunning) {
            this.statusBarItem.text = `$(testing-icon) 测试服务器运行中 (${status.host}:${status.port})`;
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
            
            if (currentTarget) {
                this.statusBarItem.tooltip = `目标: ${currentTarget.machineId}:${currentTarget.appName}`;
            } else {
                this.statusBarItem.tooltip = '测试服务器运行中，未设置目标';
            }
        } else {
            this.statusBarItem.text = '$(testing-icon) 测试服务器已停止';
            this.statusBarItem.backgroundColor = undefined;
            this.statusBarItem.tooltip = '点击启动测试服务器';
        }
    }

    dispose(): void {
        this.statusBarItem.dispose();
    }
}
