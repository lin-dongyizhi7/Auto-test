<template>
  <div class="settings-page">
    <el-card class="settings-card" shadow="hover">
      <template #header>
        <span>系统设置</span>
      </template>
      
      <el-form :model="settings" label-width="120px">
        <el-divider content-position="left">连接设置</el-divider>
        
        <el-form-item label="默认主机">
          <el-input v-model="settings.connection.host" placeholder="localhost" />
        </el-form-item>
        
        <el-form-item label="默认端口">
          <el-input-number v-model="settings.connection.port" :min="1" :max="65535" />
        </el-form-item>
        
        <el-form-item label="连接超时">
          <el-input-number v-model="settings.connection.timeout" :min="1" :max="60" />
          <span style="margin-left: 5px">秒</span>
        </el-form-item>
        
        <el-divider content-position="left">操作设置</el-divider>
        
        <el-form-item label="默认延迟">
          <el-input-number v-model="settings.operation.defaultDelay" :min="0" :max="5000" />
          <span style="margin-left: 5px">毫秒</span>
        </el-form-item>
        
        <el-form-item label="点击延迟">
          <el-input-number v-model="settings.operation.clickDelay" :min="0" :max="5000" />
          <span style="margin-left: 5px">毫秒</span>
        </el-form-item>
        
        <el-form-item label="图片匹配阈值">
          <el-slider v-model="settings.operation.imageThreshold" :min="0.1" :max="1" :step="0.1" show-input />
        </el-form-item>
        
        <el-form-item label="最大重试次数">
          <el-input-number v-model="settings.operation.maxRetries" :min="0" :max="10" />
        </el-form-item>
        
        <el-divider content-position="left">界面设置</el-divider>
        
        <el-form-item label="主题">
          <el-select v-model="settings.ui.theme">
            <el-option label="浅色主题" value="light" />
            <el-option label="深色主题" value="dark" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="语言">
          <el-select v-model="settings.ui.language">
            <el-option label="简体中文" value="zh-CN" />
            <el-option label="English" value="en-US" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="自动刷新">
          <el-switch v-model="settings.ui.autoRefresh" />
        </el-form-item>
        
        <el-form-item label="刷新间隔" v-if="settings.ui.autoRefresh">
          <el-input-number v-model="settings.ui.refreshInterval" :min="1" :max="60" />
          <span style="margin-left: 5px">秒</span>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
          <el-button @click="resetSettings">重置设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { SystemSettings } from '@/api/types'

const settings = ref<SystemSettings>({
  connection: {
    host: 'localhost',
    port: 8888,
    timeout: 30,
    retryCount: 3
  },
  operation: {
    defaultDelay: 100,
    clickDelay: 50,
    dragDelay: 200,
    imageThreshold: 0.8,
    maxRetries: 3
  },
  ui: {
    theme: 'light',
    language: 'zh-CN',
    autoRefresh: true,
    refreshInterval: 5
  }
})

const saveSettings = () => {
  // 保存设置到本地存储
  localStorage.setItem('qgis-test-settings', JSON.stringify(settings.value))
  ElMessage.success('设置已保存')
}

const resetSettings = () => {
  // 重置为默认设置
  settings.value = {
    connection: {
      host: 'localhost',
      port: 8888,
      timeout: 30,
      retryCount: 3
    },
    operation: {
      defaultDelay: 100,
      clickDelay: 50,
      dragDelay: 200,
      imageThreshold: 0.8,
      maxRetries: 3
    },
    ui: {
      theme: 'light',
      language: 'zh-CN',
      autoRefresh: true,
      refreshInterval: 5
    }
  }
  ElMessage.info('设置已重置')
}
</script>

<style lang="scss" scoped>
.settings-page {
  .settings-card {
    max-width: 800px;
    margin: 0 auto;
  }
}
</style> 