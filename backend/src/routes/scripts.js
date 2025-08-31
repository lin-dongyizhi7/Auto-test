/**
 * 脚本管理路由
 */

const express = require('express');
const router = express.Router();
const ScriptService = require('../services/scriptService');
const logger = require('../utils/logger');

// 获取所有脚本
router.get('/', async (req, res) => {
  try {
    const { search, type, status, page = 1, limit = 20 } = req.query;
    const scriptService = ScriptService.getInstance();
    
    let result;
    if (search) {
      result = await scriptService.searchScripts(search);
    } else {
      result = await scriptService.getAllScripts();
    }
    
    if (!result.success) {
      return res.status(500).json(result);
    }
    
    let scripts = result.scripts;
    
    // 按类型过滤
    if (type) {
      scripts = scripts.filter(script => script.type === type);
    }
    
    // 按状态过滤
    if (status) {
      scripts = scripts.filter(script => script.status === status);
    }
    
    // 分页
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + parseInt(limit);
    const paginatedScripts = scripts.slice(startIndex, endIndex);
    
    logger.request('获取脚本列表', { 
      total: scripts.length, 
      page: parseInt(page), 
      limit: parseInt(limit) 
    });
    
    res.json({
      success: true,
      data: paginatedScripts,
      pagination: {
        total: scripts.length,
        page: parseInt(page),
        limit: parseInt(limit),
        totalPages: Math.ceil(scripts.length / limit)
      }
    });
  } catch (error) {
    logger.error('获取脚本列表失败', { error: error.message });
    res.status(500).json({
      success: false,
      error: '获取脚本列表失败',
      message: error.message
    });
  }
});

// 获取指定脚本
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const scriptService = ScriptService.getInstance();
    
    const result = await scriptService.getScript(id);
    
    if (!result.success) {
      return res.status(404).json(result);
    }
    
    logger.request('获取脚本', { scriptId: id });
    res.json(result);
  } catch (error) {
    logger.error('获取脚本失败', { 
      scriptId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '获取脚本失败',
      message: error.message
    });
  }
});

// 创建新脚本
router.post('/', async (req, res) => {
  try {
    const { name, description, content, type, tags } = req.body;
    
    if (!name || !content) {
      return res.status(400).json({
        success: false,
        error: '缺少必要参数',
        required: ['name', 'content']
      });
    }
    
    const scriptService = ScriptService.getInstance();
    const result = await scriptService.createScript({
      name,
      description,
      content,
      type,
      tags
    });
    
    if (!result.success) {
      return res.status(500).json(result);
    }
    
    logger.request('创建脚本', { 
      scriptId: result.script.id, 
      name: result.script.name 
    });
    res.status(201).json(result);
  } catch (error) {
    logger.error('创建脚本失败', { error: error.message });
    res.status(500).json({
      success: false,
      error: '创建脚本失败',
      message: error.message
    });
  }
});

// 更新脚本
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const updateData = req.body;
    
    if (Object.keys(updateData).length === 0) {
      return res.status(400).json({
        success: false,
        error: '缺少更新数据'
      });
    }
    
    const scriptService = ScriptService.getInstance();
    const result = await scriptService.updateScript(id, updateData);
    
    if (!result.success) {
      return res.status(404).json(result);
    }
    
    logger.request('更新脚本', { 
      scriptId: id, 
      name: result.script.name 
    });
    res.json(result);
  } catch (error) {
    logger.error('更新脚本失败', { 
      scriptId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '更新脚本失败',
      message: error.message
    });
  }
});

// 删除脚本
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const scriptService = ScriptService.getInstance();
    
    const result = await scriptService.deleteScript(id);
    
    if (!result.success) {
      return res.status(404).json(result);
    }
    
    logger.request('删除脚本', { scriptId: id });
    res.json(result);
  } catch (error) {
    logger.error('删除脚本失败', { 
      scriptId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '删除脚本失败',
      message: error.message
    });
  }
});

// 执行脚本
router.post('/:id/execute', async (req, res) => {
  try {
    const { id } = req.params;
    const { parameters } = req.body;
    
    const scriptService = ScriptService.getInstance();
    const result = await scriptService.executeScript(id, parameters || {});
    
    if (!result.success) {
      return res.status(404).json(result);
    }
    
    logger.request('执行脚本', { 
      scriptId: id, 
      parameters: parameters || {} 
    });
    res.json(result);
  } catch (error) {
    logger.error('执行脚本失败', { 
      scriptId: req.params.id, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '执行脚本失败',
      message: error.message
    });
  }
});

// 获取脚本统计信息
router.get('/stats/overview', async (req, res) => {
  try {
    const scriptService = ScriptService.getInstance();
    const result = await scriptService.getScriptStats();
    
    if (!result.success) {
      return res.status(500).json(result);
    }
    
    logger.request('获取脚本统计信息');
    res.json(result);
  } catch (error) {
    logger.error('获取脚本统计信息失败', { error: error.message });
    res.status(500).json({
      success: false,
      error: '获取脚本统计信息失败',
      message: error.message
    });
  }
});

// 备份脚本
router.post('/backup', async (req, res) => {
  try {
    const scriptService = ScriptService.getInstance();
    const result = await scriptService.backupScripts();
    
    if (!result.success) {
      return res.status(500).json(result);
    }
    
    logger.request('备份脚本');
    res.json(result);
  } catch (error) {
    logger.error('备份脚本失败', { error: error.message });
    res.status(500).json({
      success: false,
      error: '备份脚本失败',
      message: error.message
    });
  }
});

// 搜索脚本
router.get('/search/:query', async (req, res) => {
  try {
    const { query } = req.params;
    const scriptService = ScriptService.getInstance();
    
    const result = await scriptService.searchScripts(query);
    
    if (!result.success) {
      return res.status(500).json(result);
    }
    
    logger.request('搜索脚本', { query, count: result.scripts.length });
    res.json(result);
  } catch (error) {
    logger.error('搜索脚本失败', { 
      query: req.params.query, 
      error: error.message 
    });
    res.status(500).json({
      success: false,
      error: '搜索脚本失败',
      message: error.message
    });
  }
});

module.exports = router;
