import * as vscode from 'vscode';
import { EventEmitter } from 'events';

export interface MachineInfo {
    id: string;
    host: string;
    port: number;
    status: 'connected' | 'disconnected' | 'error';
    lastSeen: Date;
    apps: string[];
}

export interface AppInfo {
    name: string;
    machineId: string;
    status: 'running' | 'stopped' | 'error';
    region?: number[];
    lastUpdate: Date;
}

export interface TestResult {
    success: boolean;
    data?: any;
    error?: string;
    timestamp: Date;
}

export class TestServerManager extends EventEmitter {
    private isRunning: boolean = false;
    private serverHost: string = '0.0.0.0';
    private serverPort: number = 8888;
    private machines: Map<string, MachineInfo> = new Map();
    private apps: Map<string, AppInfo> = new Map();
    private currentTarget: { machineId: string; appName: string } | null = null;
    private pythonProcess: any = null;

    constructor() {
        super();
    }

    async startServer(host: string = '0.0.0.0', port: number = 8888): Promise<boolean> {
        try {
            this.serverHost = host;
            this.serverPort = port;

            // 启动Python测试服务器进程
            await this.startPythonServer();
            
            this.isRunning = true;
            this.emit('serverStarted', { host, port });
            
            vscode.window.showInformationMessage(`测试服务器已启动 (${host}:${port})`);
            return true;
        } catch (error) {
            vscode.window.showErrorMessage(`启动测试服务器失败: ${error}`);
            return false;
        }
    }

    async stopServer(): Promise<void> {
        try {
            if (this.pythonProcess) {
                this.pythonProcess.kill();
                this.pythonProcess = null;
            }
            
            this.isRunning = false;
            this.machines.clear();
            this.apps.clear();
            this.currentTarget = null;
            
            this.emit('serverStopped');
            vscode.window.showInformationMessage('测试服务器已停止');
        } catch (error) {
            vscode.window.showErrorMessage(`停止测试服务器失败: ${error}`);
        }
    }

    private async startPythonServer(): Promise<void> {
        return new Promise((resolve, reject) => {
            const { spawn } = require('child_process');
            
            // 启动Python测试服务器
            this.pythonProcess = spawn('python', [
                '-m', 'communicators.operation_multi_machine',
                '--host', this.serverHost,
                '--port', this.serverPort.toString()
            ], {
                cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd(),
                stdio: ['pipe', 'pipe', 'pipe']
            });

            this.pythonProcess.stdout.on('data', (data: Buffer) => {
                const output = data.toString().trim();
                if (output.includes('测试服务器已启动')) {
                    resolve();
                }
            });

            this.pythonProcess.stderr.on('data', (data: Buffer) => {
                console.error(`Python服务器错误: ${data.toString()}`);
            });

            this.pythonProcess.on('error', (error: Error) => {
                reject(error);
            });

            // 超时处理
            setTimeout(() => {
                if (this.pythonProcess && !this.isRunning) {
                    reject(new Error('启动超时'));
                }
            }, 10000);
        });
    }

    async setTarget(machineId: string, appName: string): Promise<boolean> {
        try {
            if (!this.machines.has(machineId)) {
                throw new Error(`机器 ${machineId} 不存在`);
            }

            const appKey = `${machineId}:${appName}`;
            if (!this.apps.has(appKey)) {
                throw new Error(`应用 ${appName} 在机器 ${machineId} 上不存在`);
            }

            this.currentTarget = { machineId, appName };
            this.emit('targetChanged', { machineId, appName });
            
            return true;
        } catch (error) {
            console.error(`设置目标失败: ${error}`);
            return false;
        }
    }

    async executeTestScript(scriptPath: string): Promise<TestResult> {
        try {
            if (!this.currentTarget) {
                throw new Error('未设置目标机器和应用');
            }

            // 这里应该调用Python服务器的API来执行测试脚本
            // 暂时返回模拟结果
            const result: TestResult = {
                success: true,
                data: {
                    scriptPath,
                    machineId: this.currentTarget.machineId,
                    appName: this.currentTarget.appName,
                    executionTime: new Date()
                },
                timestamp: new Date()
            };

            this.emit('testExecuted', result);
            return result;
        } catch (error) {
            const result: TestResult = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                timestamp: new Date()
            };
            return result;
        }
    }

    async getMachineStatus(machineId: string): Promise<MachineInfo | null> {
        return this.machines.get(machineId) || null;
    }

    async getAppStatus(appName: string, machineId?: string): Promise<AppInfo | null> {
        if (machineId) {
            const appKey = `${machineId}:${appName}`;
            return this.apps.get(appKey) || null;
        }

        // 如果没有指定机器ID，返回第一个匹配的应用
        for (const [key, app] of this.apps) {
            if (app.name === appName) {
                return app;
            }
        }
        return null;
    }

    async refreshMachines(): Promise<void> {
        try {
            // 这里应该调用Python服务器的API来刷新机器状态
            // 暂时使用模拟数据
            this.machines.set('machine_001', {
                id: 'machine_001',
                host: '192.168.1.100',
                port: 8888,
                status: 'connected',
                lastSeen: new Date(),
                apps: ['calculator', 'notepad']
            });

            this.emit('machinesUpdated', Array.from(this.machines.values()));
        } catch (error) {
            console.error(`刷新机器状态失败: ${error}`);
        }
    }

    async refreshApps(): Promise<void> {
        try {
            // 这里应该调用Python服务器的API来刷新应用状态
            // 暂时使用模拟数据
            this.apps.set('machine_001:calculator', {
                name: 'calculator',
                machineId: 'machine_001',
                status: 'running',
                region: [100, 100, 400, 300],
                lastUpdate: new Date()
            });

            this.apps.set('machine_001:notepad', {
                name: 'notepad',
                machineId: 'machine_001',
                status: 'running',
                region: [500, 100, 800, 400],
                lastUpdate: new Date()
            });

            this.emit('appsUpdated', Array.from(this.apps.values()));
        } catch (error) {
            console.error(`刷新应用状态失败: ${error}`);
        }
    }

    getServerStatus(): { isRunning: boolean; host: string; port: number } {
        return {
            isRunning: this.isRunning,
            host: this.serverHost,
            port: this.serverPort
        };
    }

    getAvailableMachines(): string[] {
        return Array.from(this.machines.keys());
    }

    getAvailableApps(): string[] {
        return Array.from(this.apps.keys());
    }

    getCurrentTarget(): { machineId: string; appName: string } | null {
        return this.currentTarget;
    }

    isServerRunning(): boolean {
        return this.isRunning;
    }
}
