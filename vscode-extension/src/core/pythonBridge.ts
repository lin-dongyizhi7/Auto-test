import * as vscode from 'vscode';
import { EventEmitter } from 'events';

export interface PythonServerConfig {
    host: string;
    port: number;
    pythonPath: string;
    scriptPath: string;
}

export interface PythonServerResponse {
    success: boolean;
    data?: any;
    error?: string;
}

export class PythonBridge extends EventEmitter {
    private pythonProcess: any = null;
    private isRunning: boolean = false;
    private config: PythonServerConfig;
    private outputBuffer: string = '';
    private errorBuffer: string = '';

    constructor(config: PythonServerConfig) {
        super();
        this.config = config;
    }

    async startServer(): Promise<boolean> {
        try {
            if (this.isRunning) {
                return true;
            }

            const { spawn } = require('child_process');
            
            // 启动Python测试服务器
            this.pythonProcess = spawn(this.config.pythonPath, [
                this.config.scriptPath,
                '--host', this.config.host,
                '--port', this.config.port.toString(),
                '--vscode-mode'
            ], {
                cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd(),
                stdio: ['pipe', 'pipe', 'pipe'],
                env: { ...process.env, PYTHONUNBUFFERED: '1' }
            });

            // 处理输出
            this.pythonProcess.stdout.on('data', (data: Buffer) => {
                const output = data.toString();
                this.outputBuffer += output;
                
                // 检查是否启动成功
                if (output.includes('测试服务器已启动') || output.includes('Server started')) {
                    this.isRunning = true;
                    this.emit('serverStarted', { host: this.config.host, port: this.config.port });
                }
                
                // 解析JSON响应
                this.parseOutput(output);
            });

            // 处理错误
            this.pythonProcess.stderr.on('data', (data: Buffer) => {
                const error = data.toString();
                this.errorBuffer += error;
                console.error(`Python服务器错误: ${error}`);
                this.emit('serverError', error);
            });

            // 处理进程退出
            this.pythonProcess.on('close', (code: number) => {
                this.isRunning = false;
                this.emit('serverClosed', { code });
            });

            this.pythonProcess.on('error', (error: Error) => {
                this.isRunning = false;
                this.emit('serverError', error);
            });

            // 等待启动
            return new Promise((resolve) => {
                const timeout = setTimeout(() => {
                    if (!this.isRunning) {
                        resolve(false);
                    }
                }, 10000);

                this.once('serverStarted', () => {
                    clearTimeout(timeout);
                    resolve(true);
                });
            });

        } catch (error) {
            console.error('启动Python服务器失败:', error);
            return false;
        }
    }

    async stopServer(): Promise<void> {
        if (this.pythonProcess) {
            this.pythonProcess.kill();
            this.pythonProcess = null;
        }
        this.isRunning = false;
        this.emit('serverStopped');
    }

    async sendCommand(command: string, params: any = {}): Promise<PythonServerResponse> {
        if (!this.isRunning || !this.pythonProcess) {
            throw new Error('Python服务器未运行');
        }

        try {
            const request = {
                command,
                params,
                timestamp: Date.now()
            };

            // 发送命令到Python进程
            this.pythonProcess.stdin.write(JSON.stringify(request) + '\n');

            // 等待响应
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('命令执行超时'));
                }, 30000);

                const responseHandler = (response: PythonServerResponse) => {
                    clearTimeout(timeout);
                    this.removeListener('commandResponse', responseHandler);
                    resolve(response);
                };

                this.once('commandResponse', responseHandler);
            });

        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    private parseOutput(output: string): void {
        try {
            // 尝试解析JSON响应
            const lines = output.split('\n');
            for (const line of lines) {
                if (line.trim() && line.startsWith('{') && line.endsWith('}')) {
                    try {
                        const response = JSON.parse(line);
                        if (response.type === 'commandResponse') {
                            this.emit('commandResponse', response);
                        } else if (response.type === 'event') {
                            this.emit('serverEvent', response);
                        }
                    } catch (e) {
                        // 忽略解析错误
                    }
                }
            }
        } catch (error) {
            // 忽略解析错误
        }
    }

    async getMachines(): Promise<any[]> {
        const response = await this.sendCommand('get_machines');
        return response.success ? response.data : [];
    }

    async getApps(machineId?: string): Promise<any[]> {
        const response = await this.sendCommand('get_apps', { machineId });
        return response.success ? response.data : [];
    }

    async setTarget(machineId: string, appName: string): Promise<boolean> {
        const response = await this.sendCommand('set_target', { machineId, appName });
        return response.success;
    }

    async executeTestScript(scriptPath: string): Promise<PythonServerResponse> {
        return await this.sendCommand('execute_test', { scriptPath });
    }

    async executeCommands(commands: any[]): Promise<PythonServerResponse> {
        return await this.sendCommand('execute_commands', { commands });
    }

    async getScreenshot(region?: number[]): Promise<PythonServerResponse> {
        return await this.sendCommand('get_screenshot', { region });
    }

    async findElement(elementPath: string, roleNames?: string[]): Promise<PythonServerResponse> {
        return await this.sendCommand('find_element', { elementPath, roleNames });
    }

    async clickElement(elementPath: string): Promise<PythonServerResponse> {
        return await this.sendCommand('click_element', { elementPath });
    }

    async typeText(text: string): Promise<PythonServerResponse> {
        return await this.sendCommand('type_text', { text });
    }

    async waitForElement(elementPath: string, timeout: number = 5000): Promise<PythonServerResponse> {
        return await this.sendCommand('wait_for_element', { elementPath, timeout });
    }

    isServerRunning(): boolean {
        return this.isRunning;
    }

    getServerConfig(): PythonServerConfig {
        return { ...this.config };
    }

    getOutputBuffer(): string {
        return this.outputBuffer;
    }

    getErrorBuffer(): string {
        return this.errorBuffer;
    }

    clearBuffers(): void {
        this.outputBuffer = '';
        this.errorBuffer = '';
    }
}
