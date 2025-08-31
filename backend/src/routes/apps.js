/**
 * 应用管理路由
 */

const express = require('express');
const router = express.Router();
const TestServerService = require('../services/testServerService');
const logger = require('../utils/logger');

// 获取所有应用
router.get('/', async (req, res) => {
  try {
    const testServer = TestServerService.getInstance();
    const apps = await testServer.refreshApps();
    
    logger.request('获取应用列表', { count: apps.length });
    res.json({
      success: true,
      data: apps,
      count: apps.length
    });
  } catch (error) {
    logger.error('获取应用列表失败', { error: error.message });
    res.status(500).json({
      success: false,
      error: '获取应用列表失败',
      message: error.message
    });
  }
});

// 获取指定应用信息
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const testServer = TestServerService.getInstance();
    
    // 刷新应用列表以获取最新信息
    await testServer.refreshApps();
    const apps = testServer.apps;
    
    if (!apps.has(id)) {
      return res.status(404).json({
        success: false,
        error: '应用不存在'
      });
    }
    
    const app = apps.get(id);
    logger.request('获取应用信息', { appId: id });
    
    res.json({
      success: true,
      data: app
    });
  } catch (error) {
    logger.error('获取应用信息失败', { 
      appId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '获取应用信息失败',
      message: error.message
    });
  }
});

// 启动应用
router.post('/:id/start', async (req, res) => {
  try {
    const { id } = req.params;
    const testServer = TestServerService.getInstance();
    
    logger.request('启动应用', { appId: id });
    
    // 这里应该实现实际的应用启动逻辑
    // 目前返回模拟结果
    res.json({
      success: true,
      message: '应用启动成功',
      data: {
        appId: id,
        status: 'running',
        startedAt: new Date().toISOString()
      }
    });
  } catch (error) {
    logger.error('启动应用失败', { 
      appId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '启动应用失败',
      message: error.message
    });
  }
});

// 停止应用
router.post('/:id/stop', async (req, res) => {
  try {
    const { id } = req.params;
    const testServer = TestServerService.getInstance();
    
    logger.request('停止应用', { appId: id });
    
    res.json({
      success: true,
      message: '应用停止成功',
      data: {
        appId: id,
        status: 'stopped',
        stoppedAt: new Date().toISOString()
      }
    });
  } catch (error) {
    logger.error('停止应用失败', { 
      appId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '停止应用失败',
      message: error.message
    });
  }
});

// 获取应用状态
router.get('/:id/status', async (req, res) => {
  try {
    const { id } = req.params;
    const testServer = TestServerService.getInstance();
    
    // 刷新应用列表以获取最新状态
    await testServer.refreshApps();
    const apps = testServer.apps;
    
    if (!apps.has(id)) {
      return res.status(404).json({
        success: false,
        error: '应用不存在'
      });
    }
    
    const app = apps.get(id);
    logger.request('获取应用状态', { appId: id });
    
    res.json({
      success: true,
      data: {
        appId: id,
        name: app.name,
        status: app.status,
        region: app.region,
        lastUpdate: app.lastUpdate
      }
    });
  } catch (error) {
    logger.error('获取应用状态失败', { 
      appId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '获取应用状态失败',
      message: error.message
    });
  }
});

// 获取应用截图
router.get('/:id/screenshot', async (req, res) => {
  try {
    const { id } = req.params;
    const testServer = TestServerService.getInstance();
    
    logger.request('获取应用截图', { appId: id });
    
    // 这里应该实现实际的截图获取逻辑
    // 目前返回模拟结果
    res.json({
      success: true,
      message: '截图获取成功',
      data: {
        appId: id,
        screenshotUrl: `/api/apps/${id}/screenshot/image`,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    logger.error('获取应用截图失败', { 
      appId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '获取应用截图失败',
      message: error.message
    });
  }
});

// 获取应用截图图像
router.get('/:id/screenshot/image', async (req, res) => {
  try {
    const { id } = req.params;
    
    logger.request('获取应用截图图像', { appId: id });
    
    // 这里应该返回实际的截图图像
    // 目前返回占位符
    res.status(200).json({
      success: true,
      message: '截图图像获取成功',
      data: {
        appId: id,
        imageData: 'base64_encoded_image_data_placeholder',
        format: 'png',
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    logger.error('获取应用截图图像失败', { 
      appId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '获取应用截图图像失败',
      message: error.message
    });
  }
});

// 获取应用区域信息
router.get('/:id/region', async (req, res) => {
  try {
    const { id } = req.params;
    const testServer = TestServerService.getInstance();
    
    // 刷新应用列表以获取最新信息
    await testServer.refreshApps();
    const apps = testServer.apps;
    
    if (!apps.has(id)) {
      return res.status(404).json({
        success: false,
        error: '应用不存在'
      });
    }
    
    const app = apps.get(id);
    logger.request('获取应用区域信息', { appId: id });
    
    res.json({
      success: true,
      data: {
        appId: id,
        region: app.region,
        lastUpdate: app.lastUpdate
      }
    });
  } catch (error) {
    logger.error('获取应用区域信息失败', { 
      appId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '获取应用区域信息失败',
      message: error.message
    });
  }
});

module.exports = router;
