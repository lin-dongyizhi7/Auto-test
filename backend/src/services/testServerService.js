/**
 * 测试服务器服务
 * 管理测试服务器的启动、停止和状态
 */

const { spawn } = require('child_process');
const path = require('path');
const logger = require('../utils/logger');
const config = require('../config');

class TestServerService {
  constructor() {
    this.isRunning = false;
    this.serverProcess = null;
    this.host = config.testServer.defaultHost;
    this.port = config.testServer.defaultPort;
    this.currentTarget = null;
    this.machines = new Map();
    this.apps = new Map();
  }

  static getInstance() {
    if (!TestServerService.instance) {
      TestServerService.instance = new TestServerService();
    }
    return TestServerService.instance;
  }

  async initialize() {
    logger.info('初始化测试服务器服务');
    // 这里可以添加初始化逻辑
  }

  async startServer(port = this.port) {
    try {
      if (this.isRunning) {
        return { success: true, message: '测试服务器已在运行' };
      }

      this.port = port;
      logger.info(`正在启动测试服务器 ${this.host}:${this.port}`);

      // 启动Python测试服务器进程
      const pythonScript = path.join(__dirname, '../../python-adapter/vscode_server.py');
      
      this.serverProcess = spawn('python', [
        pythonScript,
        '--host', this.host,
        '--port', this.port.toString(),
        '--vscode-mode'
      ], {
        cwd: path.join(__dirname, '../../'),
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
      });

      // 处理输出
      this.serverProcess.stdout.on('data', (data) => {
        const output = data.toString();
        logger.info(`测试服务器输出: ${output.trim()}`);
        
        // 检查是否启动成功
        if (output.includes('测试服务器已启动') || output.includes('Server started')) {
          this.isRunning = true;
          logger.info('测试服务器启动成功');
        }
      });

      // 处理错误
      this.serverProcess.stderr.on('data', (data) => {
        const error = data.toString();
        logger.error(`测试服务器错误: ${error.trim()}`);
      });

      // 处理进程退出
      this.serverProcess.on('close', (code) => {
        this.isRunning = false;
        this.serverProcess = null;
        logger.info(`测试服务器进程已退出，退出码: ${code}`);
      });

      this.serverProcess.on('error', (error) => {
        this.isRunning = false;
        this.serverProcess = null;
        logger.error(`测试服务器进程错误: ${error.message}`);
      });

      // 等待启动
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          if (!this.isRunning) {
            resolve({ success: false, error: '启动超时' });
          }
        }, config.testServer.timeout);

        const checkInterval = setInterval(() => {
          if (this.isRunning) {
            clearTimeout(timeout);
            clearInterval(checkInterval);
            resolve({ success: true, message: '测试服务器启动成功' });
          }
        }, 1000);
      });

    } catch (error) {
      logger.error(`启动测试服务器失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async stopServer() {
    try {
      if (!this.isRunning || !this.serverProcess) {
        return { success: true, message: '测试服务器未运行' };
      }

      logger.info('正在停止测试服务器');
      
      // 发送停止命令到Python进程
      if (this.serverProcess.stdin && !this.serverProcess.stdin.destroyed) {
        this.serverProcess.stdin.write(JSON.stringify({
          command: 'stop',
          timestamp: Date.now()
        }) + '\n');
      }

      // 等待进程自然退出或强制终止
      setTimeout(() => {
        if (this.serverProcess && !this.serverProcess.killed) {
          this.serverProcess.kill('SIGTERM');
        }
      }, 5000);

      this.isRunning = false;
      this.currentTarget = null;
      this.machines.clear();
      this.apps.clear();

      logger.info('测试服务器已停止');
      return { success: true, message: '测试服务器已停止' };

    } catch (error) {
      logger.error(`停止测试服务器失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async setTarget(machineId, appName) {
    try {
      if (!this.isRunning) {
        return { success: false, error: '测试服务器未运行' };
      }

      // 验证机器和应用是否存在
      if (!this.machines.has(machineId)) {
        return { success: false, error: `机器 ${machineId} 不存在` };
      }

      const appKey = `${machineId}:${appName}`;
      if (!this.apps.has(appKey)) {
        return { success: false, error: `应用 ${appName} 在机器 ${machineId} 上不存在` };
      }

      this.currentTarget = { machineId, appName };
      logger.info(`设置目标: ${machineId}:${appName}`);

      return { success: true, message: '设置目标成功' };

    } catch (error) {
      logger.error(`设置目标失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  getCurrentTarget() {
    return this.currentTarget;
  }

  getStatus() {
    return {
      isRunning: this.isRunning,
      host: this.host,
      port: this.port,
      currentTarget: this.currentTarget
    };
  }

  // 模拟数据方法（用于演示）
  async refreshMachines() {
    // 模拟机器数据
    this.machines.set('machine_001', {
      id: 'machine_001',
      host: '192.168.1.100',
      port: 8888,
      status: 'connected',
      lastSeen: new Date(),
      apps: ['calculator', 'notepad']
    });

    return Array.from(this.machines.values());
  }

  async refreshApps() {
    // 模拟应用数据
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

    return Array.from(this.apps.values());
  }

  getAvailableMachines() {
    return Array.from(this.machines.keys());
  }

  getAvailableApps() {
    return Array.from(this.apps.keys());
  }
}

module.exports = TestServerService;
