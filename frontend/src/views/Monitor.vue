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
            <span>实时操作日志</span>
          </template>
          
          <div class="log-content">
            <div 
              v-for="(log, index) in recentLogs" 
              :key="index"
              class="log-item"
            >
              <div class="log-time">{{ getLogTime(log) }}</div>
              <div class="log-message">{{ getLogMessage(log) }}</div>
            </div>
            <div v-if="recentLogs.length === 0" class="no-logs">
              <el-empty description="暂无操作日志" size="small" />
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useOperationStore } from '@/stores/operation'

const operationStore = useOperationStore()

// 响应式数据
const selectedTarget = ref('')
const isMonitoring = ref(false)
const monitoringInterval = ref<number | null>(null)
const currentScreenshot = ref<any>(null)

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

const totalOperations = computed(() => operationLogs.value.length)
const todayOperations = computed(() => {
  const today = new Date().toDateString()
  return operationLogs.value.filter(log => {
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

// 生命周期
onMounted(async () => {
  await operationStore.initialize()
  
  // 模拟性能数据更新
  setInterval(() => {
    cpuUsage.value = Math.floor(Math.random() * 30) + 30
    memoryUsage.value = Math.floor(Math.random() * 20) + 50
    networkLatency.value = Math.floor(Math.random() * 20) + 10
  }, 5000)
})

onUnmounted(() => {
  stopMonitoring()
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
    .log-content {
      max-height: 400px;
      overflow-y: auto;
      
      .log-item {
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
        
        &:last-child {
          border-bottom: none;
        }
        
        .log-time {
          font-size: 12px;
          color: #909399;
          margin-bottom: 4px;
        }
        
        .log-message {
          font-size: 14px;
          color: #606266;
          word-break: break-all;
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