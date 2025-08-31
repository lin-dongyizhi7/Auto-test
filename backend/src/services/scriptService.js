/**
 * 脚本管理服务
 * 处理脚本的存储、检索、创建、更新、删除和执行
 */

const fs = require('fs').promises;
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');
const config = require('../config');

class ScriptService {
  constructor() {
    this.scriptsDir = path.join(__dirname, '../../data/scripts');
    this.scriptsFile = path.join(__dirname, '../../data/scripts_storage.json');
    this.scripts = new Map();
    this.scriptCounter = 0;
  }

  static getInstance() {
    if (!ScriptService.instance) {
      ScriptService.instance = new ScriptService();
    }
    return ScriptService.instance;
  }

  async initialize() {
    try {
      logger.info('初始化脚本服务');
      
      // 确保目录存在
      await this.ensureDirectories();
      
      // 加载现有脚本
      await this.loadScripts();
      
      logger.info(`脚本服务初始化完成，已加载 ${this.scripts.size} 个脚本`);
    } catch (error) {
      logger.error(`脚本服务初始化失败: ${error.message}`);
      throw error;
    }
  }

  async ensureDirectories() {
    try {
      await fs.mkdir(this.scriptsDir, { recursive: true });
      logger.info('脚本目录创建成功');
    } catch (error) {
      logger.error(`创建脚本目录失败: ${error.message}`);
      throw error;
    }
  }

  async loadScripts() {
    try {
      if (await this.fileExists(this.scriptsFile)) {
        const data = await fs.readFile(this.scriptsFile, 'utf8');
        const scriptsData = JSON.parse(data);
        
        this.scripts.clear();
        this.scriptCounter = scriptsData.counter || 0;
        
        for (const script of scriptsData.scripts || []) {
          this.scripts.set(script.id, script);
        }
        
        logger.info(`从文件加载了 ${this.scripts.size} 个脚本`);
      } else {
        logger.info('脚本存储文件不存在，使用空存储');
        this.scripts.clear();
        this.scriptCounter = 0;
      }
    } catch (error) {
      logger.error(`加载脚本失败: ${error.message}`);
      // 如果加载失败，使用空存储
      this.scripts.clear();
      this.scriptCounter = 0;
    }
  }

  async saveScripts() {
    try {
      const data = {
        counter: this.scriptCounter,
        scripts: Array.from(this.scripts.values()),
        lastUpdated: new Date().toISOString()
      };
      
      await fs.writeFile(this.scriptsFile, JSON.stringify(data, null, 2), 'utf8');
      logger.info('脚本数据保存成功');
    } catch (error) {
      logger.error(`保存脚本数据失败: ${error.message}`);
      throw error;
    }
  }

  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async createScript(scriptData) {
    try {
      const id = uuidv4();
      const script = {
        id,
        name: scriptData.name,
        description: scriptData.description || '',
        content: scriptData.content,
        type: scriptData.type || 'python',
        tags: scriptData.tags || [],
        created: new Date().toISOString(),
        updated: new Date().toISOString(),
        version: 1,
        status: 'active'
      };

      this.scripts.set(id, script);
      this.scriptCounter++;
      
      await this.saveScripts();
      
      logger.info(`创建脚本成功: ${id} - ${script.name}`);
      return { success: true, script };
      
    } catch (error) {
      logger.error(`创建脚本失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async updateScript(id, updateData) {
    try {
      if (!this.scripts.has(id)) {
        return { success: false, error: '脚本不存在' };
      }

      const script = this.scripts.get(id);
      const updatedScript = {
        ...script,
        ...updateData,
        updated: new Date().toISOString(),
        version: script.version + 1
      };

      this.scripts.set(id, updatedScript);
      await this.saveScripts();
      
      logger.info(`更新脚本成功: ${id} - ${updatedScript.name}`);
      return { success: true, script: updatedScript };
      
    } catch (error) {
      logger.error(`更新脚本失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async deleteScript(id) {
    try {
      if (!this.scripts.has(id)) {
        return { success: false, error: '脚本不存在' };
      }

      const script = this.scripts.get(id);
      this.scripts.delete(id);
      await this.saveScripts();
      
      logger.info(`删除脚本成功: ${id} - ${script.name}`);
      return { success: true, message: '脚本删除成功' };
      
    } catch (error) {
      logger.error(`删除脚本失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async getScript(id) {
    try {
      if (!this.scripts.has(id)) {
        return { success: false, error: '脚本不存在' };
      }

      const script = this.scripts.get(id);
      return { success: true, script };
      
    } catch (error) {
      logger.error(`获取脚本失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async getAllScripts() {
    try {
      const scripts = Array.from(this.scripts.values());
      return { success: true, scripts };
      
    } catch (error) {
      logger.error(`获取所有脚本失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async searchScripts(query) {
    try {
      const scripts = Array.from(this.scripts.values());
      const filtered = scripts.filter(script => 
        script.name.toLowerCase().includes(query.toLowerCase()) ||
        script.description.toLowerCase().includes(query.toLowerCase()) ||
        script.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
      );
      
      return { success: true, scripts: filtered };
      
    } catch (error) {
      logger.error(`搜索脚本失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async executeScript(id, parameters = {}) {
    try {
      if (!this.scripts.has(id)) {
        return { success: false, error: '脚本不存在' };
      }

      const script = this.scripts.get(id);
      logger.info(`开始执行脚本: ${id} - ${script.name}`);

      // 这里应该调用测试服务器来执行脚本
      // 目前返回模拟结果
      const result = {
        scriptId: id,
        scriptName: script.name,
        executionTime: new Date().toISOString(),
        status: 'completed',
        output: `脚本 ${script.name} 执行成功`,
        parameters,
        duration: Math.random() * 1000 + 500 // 模拟执行时间
      };

      logger.info(`脚本执行完成: ${id} - ${script.name}`);
      return { success: true, result };
      
    } catch (error) {
      logger.error(`执行脚本失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async getScriptStats() {
    try {
      const total = this.scripts.size;
      const byType = {};
      const byStatus = {};
      
      for (const script of this.scripts.values()) {
        byType[script.type] = (byType[script.type] || 0) + 1;
        byStatus[script.status] = (byStatus[script.status] || 0) + 1;
      }

      return {
        success: true,
        stats: {
          total,
          byType,
          byStatus,
          counter: this.scriptCounter
        }
      };
      
    } catch (error) {
      logger.error(`获取脚本统计失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async backupScripts() {
    try {
      const backupFile = path.join(
        this.scriptsDir, 
        `backup_${new Date().toISOString().replace(/[:.]/g, '-')}.json`
      );
      
      const data = {
        counter: this.scriptCounter,
        scripts: Array.from(this.scripts.values()),
        backupTime: new Date().toISOString()
      };
      
      await fs.writeFile(backupFile, JSON.stringify(data, null, 2), 'utf8');
      logger.info(`脚本备份成功: ${backupFile}`);
      
      return { success: true, backupFile };
      
    } catch (error) {
      logger.error(`脚本备份失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  }
}

module.exports = ScriptService;
