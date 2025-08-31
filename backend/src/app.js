#!/usr/bin/env node

/**
 * 自动化测试后端服务 - Node.js版本
 * 使用Express.js框架，提供RESTful API接口
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const path = require('path');
require('dotenv').config();

// 导入路由
const machineRoutes = require('./routes/machines');
const appRoutes = require('./routes/apps');
const scriptRoutes = require('./routes/scripts');
const operationRoutes = require('./routes/operations');

// 导入中间件
const { errorHandler, notFound } = require('./middleware/errorHandler');
const { requestLogger } = require('./middleware/logger');

// 导入服务
const TestServerService = require('./services/testServerService');
const ScriptService = require('./services/scriptService');

// 创建Express应用
const app = express();
const PORT = process.env.PORT || 8080;

// 安全中间件
app.use(helmet());

// CORS配置
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:8080'],
  credentials: true
}));

// 请求解析中间件
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 日志中间件
app.use(morgan('combined'));
app.use(requestLogger);

// 静态文件服务
app.use('/static', express.static(path.join(__dirname, '../public')));

// 健康检查端点
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: process.env.npm_package_version || '1.0.0'
  });
});

// 根端点
app.get('/', (req, res) => {
  res.json({
    name: 'AutoTest Backend',
    version: '1.0.0',
    mode: 'nodejs',
    status: 'running',
    timestamp: new Date().toISOString()
  });
});

// API路由
app.use('/api/machines', machineRoutes);
app.use('/api/apps', appRoutes);
app.use('/api/scripts', scriptRoutes);
app.use('/api/operations', operationRoutes);

// 状态端点
app.get('/api/status', (req, res) => {
  const testServer = TestServerService.getInstance();
  const status = testServer.getStatus();
  
  res.json({
    connected: status.isRunning,
    host: status.host,
    port: status.port,
    mode: 'nodejs',
    timestamp: new Date().toISOString()
  });
});

// 连接/断开端点
app.post('/api/connect', async (req, res) => {
  try {
    const { port = 8888 } = req.body;
    const testServer = TestServerService.getInstance();
    const result = await testServer.startServer(port);
    
    if (result.success) {
      res.json({
        success: true,
        message: `测试服务器已启动 0.0.0.0:${port}`,
        data: { host: '0.0.0.0', port }
      });
    } else {
      res.status(400).json({
        success: false,
        error: result.error,
        message: '测试服务器启动失败'
      });
    }
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
      message: '服务器内部错误'
    });
  }
});

app.post('/api/disconnect', async (req, res) => {
  try {
    const testServer = TestServerService.getInstance();
    await testServer.stopServer();
    
    res.json({
      success: true,
      message: '测试服务器已停止'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
      message: '停止服务器失败'
    });
  }
});

// 设置目标端点
app.post('/api/set-target', async (req, res) => {
  try {
    const { machine_id, app_name } = req.body;
    
    if (!machine_id || !app_name) {
      return res.status(400).json({
        success: false,
        error: '缺少必要参数',
        message: '需要提供 machine_id 和 app_name'
      });
    }
    
    const testServer = TestServerService.getInstance();
    const result = await testServer.setTarget(machine_id, app_name);
    
    if (result.success) {
      res.json({
        success: true,
        data: { machine_id, app_name },
        message: '设置目标成功'
      });
    } else {
      res.status(400).json({
        success: false,
        error: result.error,
        message: '设置目标失败'
      });
    }
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
      message: '设置目标失败'
    });
  }
});

app.get('/api/current-target', (req, res) => {
  try {
    const testServer = TestServerService.getInstance();
    const target = testServer.getCurrentTarget();
    
    res.json({
      success: true,
      data: target
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
      message: '获取当前目标失败'
    });
  }
});

// 错误处理中间件
app.use(notFound);
app.use(errorHandler);

// 启动服务器
async function startServer() {
  try {
    // 初始化服务
    await TestServerService.getInstance().initialize();
    await ScriptService.getInstance().initialize();
    
    app.listen(PORT, () => {
      console.log(`🚀 自动化测试后端服务已启动`);
      console.log(`📍 服务地址: http://localhost:${PORT}`);
      console.log(`📅 启动时间: ${new Date().toLocaleString()}`);
      console.log(`🔧 运行模式: Node.js + Express`);
    });
  } catch (error) {
    console.error('❌ 启动服务器失败:', error);
    process.exit(1);
  }
}

// 优雅关闭
process.on('SIGTERM', async () => {
  console.log('收到SIGTERM信号，正在关闭服务器...');
  
  try {
    const testServer = TestServerService.getInstance();
    await testServer.stopServer();
    console.log('测试服务器已关闭');
  } catch (error) {
    console.error('关闭测试服务器时发生错误:', error);
  }
  
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('收到SIGINT信号，正在关闭服务器...');
  
  try {
    const testServer = TestServerService.getInstance();
    await testServer.stopServer();
    console.log('测试服务器已关闭');
  } catch (error) {
    console.error('关闭测试服务器时发生错误:', error);
  }
  
  process.exit(0);
});

// 启动服务器
if (require.main === module) {
  startServer();
}

module.exports = app;
