/**
 * 机器管理路由
 */

const express = require('express');
const router = express.Router();
const TestServerService = require('../services/testServerService');
const logger = require('../utils/logger');

// 获取所有机器
router.get('/', async (req, res) => {
  try {
    const testServer = TestServerService.getInstance();
    const machines = await testServer.refreshMachines();
    
    logger.request('获取机器列表', { count: machines.length });
    res.json({
      success: true,
      data: machines,
      count: machines.length
    });
  } catch (error) {
    logger.error('获取机器列表失败', { error: error.message });
    res.status(500).json({
      success: false,
      error: '获取机器列表失败',
      message: error.message
    });
  }
});

// 获取指定机器信息
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const testServer = TestServerService.getInstance();
    
    // 刷新机器列表以获取最新信息
    await testServer.refreshMachines();
    const machines = testServer.machines;
    
    if (!machines.has(id)) {
      return res.status(404).json({
        success: false,
        error: '机器不存在'
      });
    }
    
    const machine = machines.get(id);
    logger.request('获取机器信息', { machineId: id });
    
    res.json({
      success: true,
      data: machine
    });
  } catch (error) {
    logger.error('获取机器信息失败', { 
      machineId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '获取机器信息失败',
      message: error.message
    });
  }
});

// 连接机器
router.post('/:id/connect', async (req, res) => {
  try {
    const { id } = req.params;
    const { host, port } = req.body;
    
    if (!host || !port) {
      return res.status(400).json({
        success: false,
        error: '缺少必要参数',
        required: ['host', 'port']
      });
    }
    
    const testServer = TestServerService.getInstance();
    
    // 这里应该实现实际的机器连接逻辑
    // 目前返回模拟结果
    logger.request('连接机器', { machineId: id, host, port });
    
    res.json({
      success: true,
      message: '机器连接成功',
      data: {
        machineId: id,
        host,
        port,
        status: 'connected',
        connectedAt: new Date().toISOString()
      }
    });
  } catch (error) {
    logger.error('连接机器失败', { 
      machineId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '连接机器失败',
      message: error.message
    });
  }
});

// 断开机器连接
router.post('/:id/disconnect', async (req, res) => {
  try {
    const { id } = req.params;
    const testServer = TestServerService.getInstance();
    
    logger.request('断开机器连接', { machineId: id });
    
    res.json({
      success: true,
      message: '机器断开连接成功',
      data: {
        machineId: id,
        status: 'disconnected',
        disconnectedAt: new Date().toISOString()
      }
    });
  } catch (error) {
    logger.error('断开机器连接失败', { 
      machineId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '断开机器连接失败',
      message: error.message
    });
  }
});

// 获取机器状态
router.get('/:id/status', async (req, res) => {
  try {
    const { id } = req.params;
    const testServer = TestServerService.getInstance();
    
    // 刷新机器列表以获取最新状态
    await testServer.refreshMachines();
    const machines = testServer.machines;
    
    if (!machines.has(id)) {
      return res.status(404).json({
        success: false,
        error: '机器不存在'
      });
    }
    
    const machine = machines.get(id);
    logger.request('获取机器状态', { machineId: id });
    
    res.json({
      success: true,
      data: {
        machineId: id,
        status: machine.status,
        lastSeen: machine.lastSeen,
        apps: machine.apps
      }
    });
  } catch (error) {
    logger.error('获取机器状态失败', { 
      machineId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '获取机器状态失败',
      message: error.message
    });
  }
});

// 获取机器上的应用列表
router.get('/:id/apps', async (req, res) => {
  try {
    const { id } = req.params;
    const testServer = TestServerService.getInstance();
    
    // 刷新应用列表以获取最新信息
    await testServer.refreshApps();
    const apps = testServer.apps;
    
    const machineApps = Array.from(apps.values())
      .filter(app => app.machineId === id);
    
    logger.request('获取机器应用列表', { 
      machineId: id, 
      appCount: machineApps.length 
    });
    
    res.json({
      success: true,
      data: machineApps,
      count: machineApps.length
    });
  } catch (error) {
    logger.error('获取机器应用列表失败', { 
      machineId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '获取机器应用列表失败',
      message: error.message
    });
  }
});

module.exports = router;
