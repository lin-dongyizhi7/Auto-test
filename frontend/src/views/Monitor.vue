<template>
  <div class="monitor-page">
    <!-- 连接状态监控 -->
    <el-row :gutter="20" class="status-row">
      <el-col :span="8">
        <el-card class="status-card" shadow="hover">
          <template #header>
            <span>测试服务器状态</span>
          </template>
          
          <div class="status-content">
            <el-tag :type="isConnected ? 'success' : 'danger'" size="large">
              {{ isConnected ? '已连接' : '未连接' }}
            </el-tag>
            <div class="status-info">
              <p>地址: {{ testServerInfo }}</p>
              <p>连接时间: {{ connectionTime }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="status-card" shadow="hover">
          <template #header>
            <span>机器状态</span>
          </template>
          
          <div class="status-content">
            <div class="status-number">{{ availableMachines }}</div>
            <div class="status-label">可用机器</div>
            <div class="status-detail">
              <el-tag v-for="machine in machines" :key="machine.id" size="small" class="machine-tag">
                {{ machine.address }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="status-card" shadow="hover">
          <template #header>
            <span>应用状态</span>
          </template>
          
          <div class="status-content">
            <div class="status-number">{{ availableApps }}</div>
            <div class="status-label">运行应用</div>
            <div class="status-detail">
              <el-tag v-for="app in apps" :key="app.id" size="small" class="app-tag">
                {{ app.name }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时截图监控 -->
    <el-row :gutter="20" class="screenshot-row">
      <el-col :span="16">
        <el-card class="screenshot-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>实时截图监控</span>
              <div class="header-actions">
                <el-select v-model="selectedTarget" placeholder="选择监控目标" style="width: 200px">
                  <el-option 
                    v-for="target in availableTargets" 
                    :key="target.id"
                    :label="`${target.machine_id} / ${target.app_name}`"
                    :value="target.id"
                  />
                </el-select>
                <el-button type="primary" @click="startMonitoring" :disabled="!selectedTarget">
                  开始监控
                </el-button>
                <el-button @click="stopMonitoring" :disabled="!isMonitoring">
                  停止监控
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="screenshot-content">
            <div v-if="!selectedTarget" class="no-target">
              <el-empty description="请选择监控目标" />
            </div>
            <div v-else-if="!isMonitoring" class="not-monitoring">
              <el-empty description="点击开始监控查看实时截图" />
            </div>
            <div v-else class="screenshot-display">
              <img 
                v-if="currentScreenshot" 
                :src="`data:image/png;base64,${currentScreenshot.screenshot}`" 
                :alt="`实时截图 - ${selectedTarget}`"
                class="screenshot-image"
              />
              <div v-else class="screenshot-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>正在获取截图...</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="log-card" shadow="hover">
          <template #header>
            <div class="log-header">
              <span>实时日志</span>
              <div class="log-controls">
                <el-select v-model="selectedMachine" placeholder="选择机器" size="small" style="width: 120px">
                  <el-option label="全部机器" value="" />
                  <el-option 
                    v-for="machine in machines" 
                    :key="machine.id"
                    :label="machine.address"
                    :value="machine.id"
                  />
                </el-select>
                <el-button size="small" @click="clearLogs">清空</el-button>
                <el-button size="small" @click="toggleAutoScroll" :type="autoScroll ? 'primary' : 'default'">
                  {{ autoScroll ? '停止' : '自动' }}
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="log-content" ref="logContainer">
            <div 
              v-for="(log, index) in displayLogs" 
              :key="index"
              class="log-item"
              :class="getLogLevelClass(log.level)"
            >
              <div class="log-header-item">
                <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
                <span class="log-machine">{{ log.machine_id }}</span>
                <span class="log-level">{{ log.level }}</span>
              </div>
              <div class="log-message">{{ log.message }}</div>
            </div>
            <div v-if="displayLogs.length === 0" class="no-logs">
              <el-empty description="暂无日志" size="small" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 性能监控 -->
    <el-row :gutter="20" class="performance-row">
      <el-col :span="12">
        <el-card class="performance-card" shadow="hover">
          <template #header>
            <span>操作统计</span>
          </template>
          
          <div class="performance-content">
            <div class="performance-item">
              <span class="label">总操作数:</span>
              <span class="value">{{ totalOperations }}</span>
            </div>
            <div class="performance-item">
              <span class="label">今日操作:</span>
              <span class="value">{{ todayOperations }}</span>
            </div>
            <div class="performance-item">
              <span class="label">平均响应时间:</span>
              <span class="value">{{ averageResponseTime }}ms</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="performance-card" shadow="hover">
          <template #header>
            <span>系统资源</span>
          </template>
          
          <div class="performance-content">
            <div class="performance-item">
              <span class="label">CPU使用率:</span>
              <span class="value">{{ cpuUsage }}%</span>
            </div>
            <div class="performance-item">
              <span class="label">内存使用率:</span>
              <span class="value">{{ memoryUsage }}%</span>
            </div>
            <div class="performance-item">
              <span class="label">网络延迟:</span>
              <span class="value">{{ networkLatency }}ms</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useOperationStore } from '@/stores/operation'

const operationStore = useOperationStore()

// 响应式数据
const selectedTarget = ref('')
const isMonitoring = ref(false)
const monitoringInterval = ref<number | null>(null)
const currentScreenshot = ref<any>(null)

// 日志相关
const selectedMachine = ref('')
const autoScroll = ref(true)
const logContainer = ref<HTMLElement>()
const realTimeLogs = ref<any[]>([])
const maxLogs = 200 // 最多显示200条日志

// 模拟性能数据
const cpuUsage = ref(45)
const memoryUsage = ref(62)
const networkLatency = ref(15)

// 计算属性
const isConnected = computed(() => operationStore.isConnected)
const machines = computed(() => operationStore.machines)
const apps = computed(() => operationStore.apps)
const operationLogs = computed(() => operationStore.operationLogs)

const testServerInfo = computed(() => {
  if (!isConnected.value) return '未连接'
  const config = operationStore.connectionConfig
  return `${config.host}:${config.port}`
})

const connectionTime = computed(() => {
  // 这里可以添加连接时间的计算逻辑
  return '刚刚'
})

const availableMachines = computed(() => machines.value.length)
const availableApps = computed(() => apps.value.length)

const availableTargets = computed(() => {
  const targets = []
  for (const machine of machines.value) {
    for (const app of apps.value) {
      if (app.machine_id === machine.id) {
        targets.push({
          id: `${machine.id}:${app.name}`,
          machine_id: machine.id,
          app_name: app.name
        })
      }
    }
  }
  return targets
})

const recentLogs = computed(() => {
  return operationLogs.value.slice(-10).reverse()
})

const displayLogs = computed(() => {
  let logs = realTimeLogs.value
  
  // 按机器过滤
  if (selectedMachine.value) {
    logs = logs.filter((log: any) => log.machine_id === selectedMachine.value)
  }
  
  // 按时间排序（最新的在前）
  logs = logs.sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  
  // 限制显示数量
  return logs.slice(0, maxLogs)
})

const totalOperations = computed(() => operationLogs.value.length)
const todayOperations = computed(() => {
  const today = new Date().toDateString()
  return operationLogs.value.filter((log: any) => {
    const logDate = new Date().toDateString()
    return logDate === today
  }).length
})

const averageResponseTime = computed(() => {
  // 这里可以添加平均响应时间的计算逻辑
  return 120
})

// 方法
const startMonitoring = async () => {
  if (!selectedTarget.value) {
    ElMessage.warning('请选择监控目标')
    return
  }

  try {
    isMonitoring.value = true
    
    // 开始定时获取截图
    monitoringInterval.value = window.setInterval(async () => {
      if (selectedTarget.value) {
        const [machineId, appName] = selectedTarget.value.split(':')
        
        // 设置目标
        await operationStore.setCurrentTarget({
          machine_id: machineId,
          app_name: appName
        })
        
        // 获取截图
        const screenshot = await operationStore.takeScreenshot()
        if (screenshot) {
          currentScreenshot.value = screenshot
        }
      }
    }, 2000) // 每2秒更新一次
    
    ElMessage.success('监控已开始')
  } catch (error) {
    ElMessage.error(`开始监控失败: ${error instanceof Error ? error.message : '未知错误'}`)
    isMonitoring.value = false
  }
}

const stopMonitoring = () => {
  if (monitoringInterval.value) {
    clearInterval(monitoringInterval.value)
    monitoringInterval.value = null
  }
  isMonitoring.value = false
  currentScreenshot.value = null
  ElMessage.info('监控已停止')
}

const getLogTime = (log: string) => {
  const timeMatch = log.match(/\[(.*?)\]/)
  return timeMatch ? timeMatch[1] : '未知时间'
}

const getLogMessage = (log: string) => {
  const messageMatch = log.match(/\]\s*(.*)/)
  return messageMatch ? messageMatch[1] : log
}

// WebSocket连接
let ws: WebSocket | null = null

const connectWebSocket = () => {
  try {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/logs/ws`
    
    ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log('WebSocket连接已建立')
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'log_update') {
          addLog(data.data)
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
      }
    }
    
    ws.onclose = () => {
      console.log('WebSocket连接已关闭')
      // 5秒后重连
      setTimeout(connectWebSocket, 5000)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }
  } catch (error) {
    console.error('WebSocket连接失败:', error)
  }
}

const addLog = (log: any) => {
  realTimeLogs.value.unshift(log)
  
  // 保持日志数量限制
  if (realTimeLogs.value.length > maxLogs * 2) {
    realTimeLogs.value = realTimeLogs.value.slice(0, maxLogs * 2)
  }
  
  // 自动滚动到底部
  if (autoScroll.value) {
    nextTick(() => {
      scrollToBottom()
    })
  }
}

const scrollToBottom = () => {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

const clearLogs = () => {
  realTimeLogs.value = []
}

const toggleAutoScroll = () => {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) {
    nextTick(() => {
      scrollToBottom()
    })
  }
}

const formatLogTime = (timestamp: string) => {
  if (!timestamp) return '未知时间'
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN')
}

const getLogLevelClass = (level: string) => {
  const levelMap: Record<string, string> = {
    'DEBUG': 'log-debug',
    'INFO': 'log-info',
    'WARNING': 'log-warning',
    'ERROR': 'log-error',
    'CRITICAL': 'log-critical'
  }
  return levelMap[level] || 'log-info'
}

// 生命周期
onMounted(async () => {
  await operationStore.initialize()
  
  // 连接WebSocket
  connectWebSocket()
  
  // 模拟性能数据更新
  setInterval(() => {
    cpuUsage.value = Math.floor(Math.random() * 30) + 30
    memoryUsage.value = Math.floor(Math.random() * 20) + 50
    networkLatency.value = Math.floor(Math.random() * 20) + 10
  }, 5000)
})

onUnmounted(() => {
  stopMonitoring()
  if (ws) {
    ws.close()
  }
})
</script>

<style lang="less" scoped>
.monitor-page {
  .status-row {
    margin-bottom: 20px;
  }

  .status-card {
    .status-content {
      text-align: center;
      padding: 20px 0;
      
      .status-info {
        margin-top: 15px;
        
        p {
          margin: 5px 0;
          color: #606266;
          font-size: 14px;
        }
      }
      
      .status-number {
        font-size: 36px;
        font-weight: bold;
        color: #409eff;
        margin-bottom: 10px;
      }
      
      .status-label {
        font-size: 16px;
        color: #606266;
        margin-bottom: 15px;
      }
      
      .status-detail {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        justify-content: center;
        
        .machine-tag, .app-tag {
          margin: 2px;
        }
      }
    }
  }

  .screenshot-row {
    margin-bottom: 20px;
  }

  .screenshot-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-actions {
        display: flex;
        gap: 10px;
        align-items: center;
      }
    }
    
    .screenshot-content {
      min-height: 400px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .no-target, .not-monitoring {
        text-align: center;
        color: #909399;
      }
      
      .screenshot-display {
        width: 100%;
        text-align: center;
        
        .screenshot-image {
          max-width: 100%;
          max-height: 400px;
          border: 1px solid #dcdfe6;
          border-radius: 4px;
        }
        
        .screenshot-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 10px;
          color: #909399;
          
          .el-icon {
            font-size: 24px;
          }
        }
      }
    }
  }

  .log-card {
    .log-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .log-controls {
        display: flex;
        gap: 8px;
        align-items: center;
      }
    }
    
    .log-content {
      max-height: 400px;
      overflow-y: auto;
      
      .log-item {
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
        border-left: 3px solid transparent;
        
        &:last-child {
          border-bottom: none;
        }
        
        .log-header-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 4px;
          
          .log-time {
            font-size: 11px;
            color: #909399;
          }
          
          .log-machine {
            font-size: 11px;
            color: #409eff;
            background: #ecf5ff;
            padding: 2px 6px;
            border-radius: 3px;
          }
          
          .log-level {
            font-size: 11px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 3px;
          }
        }
        
        .log-message {
          font-size: 13px;
          color: #606266;
          word-break: break-all;
          line-height: 1.4;
        }
        
        // 日志级别样式
        &.log-debug {
          border-left-color: #909399;
          .log-level {
            background: #f4f4f5;
            color: #909399;
          }
        }
        
        &.log-info {
          border-left-color: #409eff;
          .log-level {
            background: #ecf5ff;
            color: #409eff;
          }
        }
        
        &.log-warning {
          border-left-color: #e6a23c;
          .log-level {
            background: #fdf6ec;
            color: #e6a23c;
          }
        }
        
        &.log-error {
          border-left-color: #f56c6c;
          .log-level {
            background: #fef0f0;
            color: #f56c6c;
          }
        }
        
        &.log-critical {
          border-left-color: #f56c6c;
          background: #fef0f0;
          .log-level {
            background: #f56c6c;
            color: white;
          }
        }
      }
      
      .no-logs {
        padding: 20px;
        text-align: center;
      }
    }
  }

  .performance-row {
    margin-bottom: 20px;
  }

  .performance-card {
    .performance-content {
      .performance-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #f0f0f0;
        
        &:last-child {
          border-bottom: none;
        }
        
        .label {
          color: #606266;
          font-size: 14px;
        }
        
        .value {
          color: #409eff;
          font-weight: bold;
          font-size: 16px;
        }
      }
    }
  }
}
</style> 