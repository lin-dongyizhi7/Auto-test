import * as vscode from 'vscode';
import { TestServerManager, TestResult, MachineInfo, AppInfo } from './testServerManager';

export interface MachineConnectionResult {
    success: boolean;
    machineId?: string;
    error?: string;
}

export interface TestExecutionOptions {
    machineId?: string;
    appName?: string;
    timeout?: number;
    retryCount?: number;
}

export class MachineController {
    constructor(private testServerManager: TestServerManager) {}

    async connectMachine(machineId: string): Promise<MachineConnectionResult> {
        try {
            // 检查机器是否已连接
            const existingMachine = await this.testServerManager.getMachineStatus(machineId);
            if (existingMachine && existingMachine.status === 'connected') {
                return {
                    success: true,
                    machineId: machineId
                };
            }

            // 尝试连接机器
            // 这里应该调用Python服务器的API来连接机器
            // 暂时返回成功
            return {
                success: true,
                machineId: machineId
            };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    async disconnectMachine(machineId: string): Promise<boolean> {
        try {
            // 这里应该调用Python服务器的API来断开机器连接
            // 暂时返回成功
            return true;
        } catch (error) {
            console.error(`断开机器连接失败: ${error}`);
            return false;
        }
    }

    async executeTest(scriptPath: string, options: TestExecutionOptions = {}): Promise<TestResult> {
        try {
            // 如果指定了机器和应用，先设置目标
            if (options.machineId && options.appName) {
                const targetSet = await this.testServerManager.setTarget(options.machineId, options.appName);
                if (!targetSet) {
                    throw new Error(`无法设置目标: ${options.machineId}:${options.appName}`);
                }
            }

            // 执行测试脚本
            const result = await this.testServerManager.executeTestScript(scriptPath);
            return result;
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                timestamp: new Date()
            };
        }
    }

    async executeCommands(commands: any[], options: TestExecutionOptions = {}): Promise<TestResult> {
        try {
            // 如果指定了机器和应用，先设置目标
            if (options.machineId && options.appName) {
                const targetSet = await this.testServerManager.setTarget(options.machineId, options.appName);
                if (!targetSet) {
                    throw new Error(`无法设置目标: ${options.machineId}:${options.appName}`);
                }
            }

            // 这里应该调用Python服务器的API来执行命令
            // 暂时返回模拟结果
            const result: TestResult = {
                success: true,
                data: {
                    commands: commands,
                    executionTime: new Date(),
                    machineId: options.machineId,
                    appName: options.appName
                },
                timestamp: new Date()
            };

            return result;
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                timestamp: new Date()
            };
        }
    }

    async getScreenshot(region?: number[], options: TestExecutionOptions = {}): Promise<TestResult> {
        try {
            // 如果指定了机器和应用，先设置目标
            if (options.machineId && options.appName) {
                const targetSet = await this.testServerManager.setTarget(options.machineId, options.appName);
                if (!targetSet) {
                    throw new Error(`无法设置目标: ${options.machineId}:${options.appName}`);
                }
            }

            // 这里应该调用Python服务器的API来获取截图
            // 暂时返回模拟结果
            const result: TestResult = {
                success: true,
                data: {
                    screenshot: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
                    region: region,
                    timestamp: new Date()
                },
                timestamp: new Date()
            };

            return result;
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                timestamp: new Date()
            };
        }
    }

    async findElement(elementPath: string, roleNames?: string[], options: TestExecutionOptions = {}): Promise<TestResult> {
        try {
            // 如果指定了机器和应用，先设置目标
            if (options.machineId && options.appName) {
                const targetSet = await this.testServerManager.setTarget(options.machineId, options.appName);
                if (!targetSet) {
                    throw new Error(`无法设置目标: ${options.machineId}:${options.appName}`);
                }
            }

            // 这里应该调用Python服务器的API来查找元素
            // 暂时返回模拟结果
            const result: TestResult = {
                success: true,
                data: {
                    element: {
                        path: elementPath,
                        role: roleNames?.[0] || 'unknown',
                        bounds: [100, 100, 200, 150],
                        text: '模拟元素'
                    },
                    timestamp: new Date()
                },
                timestamp: new Date()
            };

            return result;
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                timestamp: new Date()
            };
        }
    }

    async clickElement(elementPath: string, options: TestExecutionOptions = {}): Promise<TestResult> {
        try {
            // 如果指定了机器和应用，先设置目标
            if (options.machineId && options.appName) {
                const targetSet = await this.testServerManager.setTarget(options.machineId, options.appName);
                if (!targetSet) {
                    throw new Error(`无法设置目标: ${options.machineId}:${options.appName}`);
                }
            }

            // 这里应该调用Python服务器的API来点击元素
            // 暂时返回模拟结果
            const result: TestResult = {
                success: true,
                data: {
                    action: 'click',
                    element: elementPath,
                    timestamp: new Date()
                },
                timestamp: new Date()
            };

            return result;
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                timestamp: new Date()
            };
        }
    }

    async typeText(text: string, options: TestExecutionOptions = {}): Promise<TestResult> {
        try {
            // 如果指定了机器和应用，先设置目标
            if (options.machineId && options.appName) {
                const targetSet = await this.testServerManager.setTarget(options.machineId, options.appName);
                if (!targetSet) {
                    throw new Error(`无法设置目标: ${options.machineId}:${options.appName}`);
                }
            }

            // 这里应该调用Python服务器的API来输入文本
            // 暂时返回模拟结果
            const result: TestResult = {
                success: true,
                data: {
                    action: 'type',
                    text: text,
                    timestamp: new Date()
                },
                timestamp: new Date()
            };

            return result;
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                timestamp: new Date()
            };
        }
    }

    async waitForElement(elementPath: string, timeout: number = 5000, options: TestExecutionOptions = {}): Promise<TestResult> {
        try {
            // 如果指定了机器和应用，先设置目标
            if (options.machineId && options.appName) {
                const targetSet = await this.testServerManager.setTarget(options.machineId, options.appName);
                if (!targetSet) {
                    throw new Error(`无法设置目标: ${options.machineId}:${options.appName}`);
                }
            }

            // 这里应该调用Python服务器的API来等待元素
            // 暂时返回模拟结果
            const result: TestResult = {
                success: true,
                data: {
                    action: 'wait',
                    element: elementPath,
                    timeout: timeout,
                    timestamp: new Date()
                },
                timestamp: new Date()
            };

            return result;
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                timestamp: new Date()
            };
        }
    }

    async getMachineList(): Promise<MachineInfo[]> {
        try {
            await this.testServerManager.refreshMachines();
            return Array.from(this.testServerManager.getAvailableMachines()).map(id => 
                this.testServerManager.getMachineStatus(id)
            ).filter(Boolean) as MachineInfo[];
        } catch (error) {
            console.error(`获取机器列表失败: ${error}`);
            return [];
        }
    }

    async getAppList(machineId?: string): Promise<AppInfo[]> {
        try {
            await this.testServerManager.refreshApps();
            if (machineId) {
                return Array.from(this.testServerManager.getAvailableApps())
                    .filter(key => key.startsWith(machineId + ':'))
                    .map(key => this.testServerManager.getAppStatus(key.split(':')[1], machineId))
                    .filter(Boolean) as AppInfo[];
            } else {
                return Array.from(this.testServerManager.getAvailableApps()).map(key => {
                    const [mid, appName] = key.split(':');
                    return this.testServerManager.getAppStatus(appName, mid);
                }).filter(Boolean) as AppInfo[];
            }
        } catch (error) {
            console.error(`获取应用列表失败: ${error}`);
            return [];
        }
    }

    getCurrentTarget(): { machineId: string; appName: string } | null {
        return this.testServerManager.getCurrentTarget();
    }

    isServerRunning(): boolean {
        return this.testServerManager.isServerRunning();
    }
}
