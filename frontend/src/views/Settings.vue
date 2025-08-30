<template>
  <div class="settings-page">
    <el-card class="settings-card" shadow="hover">
      <template #header>
        <span>系统设置</span>
      </template>
      
      <el-form :model="settings" label-width="120px">
        <el-divider content-position="left">测试服务器设置</el-divider>
        
        <el-form-item label="默认服务器地址">
          <el-input v-model="settings.testServer.host" placeholder="localhost" />
        </el-form-item>
        
        <el-form-item label="默认服务器端口">
          <el-input-number v-model="settings.testServer.port" :min="1" :max="65535" />
        </el-form-item>
        
        <el-form-item label="连接超时">
          <el-input-number v-model="settings.testServer.timeout" :min="1" :max="60" />
          <span style="margin-left: 5px">秒</span>
        </el-form-item>
        
        <el-form-item label="重连次数">
          <el-input-number v-model="settings.testServer.retryCount" :min="0" :max="10" />
        </el-form-item>
        
        <el-divider content-position="left">多机器设置</el-divider>
        
        <el-form-item label="自动发现机器">
          <el-switch v-model="settings.multiMachine.autoDiscovery" />
        </el-form-item>
        
        <el-form-item label="机器心跳间隔" v-if="settings.multiMachine.autoDiscovery">
          <el-input-number v-model="settings.multiMachine.heartbeatInterval" :min="5" :max="60" />
          <span style="margin-left: 5px">秒</span>
        </el-form-item>
        
        <el-form-item label="应用状态检查">
          <el-switch v-model="settings.multiMachine.appStatusCheck" />
        </el-form-item>
        
        <el-form-item label="状态检查间隔" v-if="settings.multiMachine.appStatusCheck">
          <el-input-number v-model="settings.multiMachine.statusCheckInterval" :min="10" :max="300" />
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
        
        <el-form-item label="拖拽延迟">
          <el-input-number v-model="settings.operation.dragDelay" :min="0" :max="5000" />
          <span style="margin-left: 5px">毫秒</span>
        </el-form-item>
        
        <el-form-item label="图片匹配阈值">
          <el-slider v-model="settings.operation.imageThreshold" :min="0.1" :max="1" :step="0.1" show-input />
        </el-form-item>
        
        <el-form-item label="最大重试次数">
          <el-input-number v-model="settings.operation.maxRetries" :min="0" :max="10" />
        </el-form-item>
        
        <el-divider content-position="left">监控设置</el-divider>
        
        <el-form-item label="实时监控">
          <el-switch v-model="settings.monitoring.realTimeMonitoring" />
        </el-form-item>
        
        <el-form-item label="截图更新频率" v-if="settings.monitoring.realTimeMonitoring">
          <el-input-number v-model="settings.monitoring.screenshotInterval" :min="1" :max="30" />
          <span style="margin-left: 5px">秒</span>
        </el-form-item>
        
        <el-form-item label="日志保留天数">
          <el-input-number v-model="settings.monitoring.logRetentionDays" :min="1" :max="365" />
        </el-form-item>
        
        <el-form-item label="性能监控">
          <el-switch v-model="settings.monitoring.performanceMonitoring" />
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
        
        <el-form-item label="显示机器状态">
          <el-switch v-model="settings.ui.showMachineStatus" />
        </el-form-item>
        
        <el-form-item label="显示应用状态">
          <el-switch v-model="settings.ui.showAppStatus" />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
          <el-button @click="resetSettings">重置设置</el-button>
          <el-button @click="exportSettings">导出设置</el-button>
          <el-button @click="importSettings">导入设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

interface TestServerSettings {
  host: string
  port: number
  timeout: number
  retryCount: number
}

interface MultiMachineSettings {
  autoDiscovery: boolean
  heartbeatInterval: number
  appStatusCheck: boolean
  statusCheckInterval: number
}

interface OperationSettings {
  defaultDelay: number
  clickDelay: number
  dragDelay: number
  imageThreshold: number
  maxRetries: number
}

interface MonitoringSettings {
  realTimeMonitoring: boolean
  screenshotInterval: number
  logRetentionDays: number
  performanceMonitoring: boolean
}

interface UISettings {
  theme: 'light' | 'dark'
  language: 'zh-CN' | 'en-US'
  autoRefresh: boolean
  refreshInterval: number
  showMachineStatus: boolean
  showAppStatus: boolean
}

interface SystemSettings {
  testServer: TestServerSettings
  multiMachine: MultiMachineSettings
  operation: OperationSettings
  monitoring: MonitoringSettings
  ui: UISettings
}

const settings = ref<SystemSettings>({
  testServer: {
    host: 'localhost',
    port: 8888,
    timeout: 30,
    retryCount: 3
  },
  multiMachine: {
    autoDiscovery: true,
    heartbeatInterval: 15,
    appStatusCheck: true,
    statusCheckInterval: 60
  },
  operation: {
    defaultDelay: 100,
    clickDelay: 50,
    dragDelay: 200,
    imageThreshold: 0.8,
    maxRetries: 3
  },
  monitoring: {
    realTimeMonitoring: true,
    screenshotInterval: 5,
    logRetentionDays: 30,
    performanceMonitoring: true
  },
  ui: {
    theme: 'light',
    language: 'zh-CN',
    autoRefresh: true,
    refreshInterval: 5,
    showMachineStatus: true,
    showAppStatus: true
  }
})

const saveSettings = () => {
  try {
    // 保存设置到本地存储
    localStorage.setItem('qgis-test-settings', JSON.stringify(settings.value))
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存设置失败')
  }
}

const resetSettings = () => {
  // 重置为默认设置
  settings.value = {
    testServer: {
      host: 'localhost',
      port: 8888,
      timeout: 30,
      retryCount: 3
    },
    multiMachine: {
      autoDiscovery: true,
      heartbeatInterval: 15,
      appStatusCheck: true,
      statusCheckInterval: 60
    },
    operation: {
      defaultDelay: 100,
      clickDelay: 50,
      dragDelay: 200,
      imageThreshold: 0.8,
      maxRetries: 3
    },
    monitoring: {
      realTimeMonitoring: true,
      screenshotInterval: 5,
      logRetentionDays: 30,
      performanceMonitoring: true
    },
    ui: {
      theme: 'light',
      language: 'zh-CN',
      autoRefresh: true,
      refreshInterval: 5,
      showMachineStatus: true,
      showAppStatus: true
    }
  }
  ElMessage.info('设置已重置')
}

const exportSettings = () => {
  try {
    const dataStr = JSON.stringify(settings.value, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    
    const link = document.createElement('a')
    link.href = URL.createObjectURL(dataBlob)
    link.download = 'qgis-test-settings.json'
    link.click()
    
    ElMessage.success('设置已导出')
  } catch (error) {
    ElMessage.error('导出设置失败')
  }
}

const importSettings = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  
  input.onchange = (event) => {
    const file = (event.target as HTMLInputElement).files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const importedSettings = JSON.parse(e.target?.result as string)
          settings.value = { ...settings.value, ...importedSettings }
          ElMessage.success('设置已导入')
        } catch (error) {
          ElMessage.error('导入设置失败：文件格式错误')
        }
      }
      reader.readAsText(file)
    }
  }
  
  input.click()
}

const loadSettings = () => {
  try {
    const savedSettings = localStorage.getItem('qgis-test-settings')
    if (savedSettings) {
      const parsedSettings = JSON.parse(savedSettings)
      settings.value = { ...settings.value, ...parsedSettings }
    }
  } catch (error) {
    console.warn('加载设置失败，使用默认设置')
  }
}

// 生命周期
onMounted(() => {
  loadSettings()
})
</script>

<style lang="less" scoped>
.settings-page {
  .settings-card {
    max-width: 900px;
    margin: 0 auto;
  }
}
</style> 