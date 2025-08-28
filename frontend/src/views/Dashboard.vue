<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ isConnected ? '已连接' : '未连接' }}</div>
              <div class="stat-label">连接状态</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon primary">
              <el-icon><Operation /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ totalOperations }}</div>
              <div class="stat-label">总操作数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon warning">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ availableMachines }}</div>
              <div class="stat-label">可用机器</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon info">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ lastOperationTime }}</div>
              <div class="stat-label">最后操作</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作 -->
    <el-row :gutter="20" class="quick-actions-row">
      <el-col :span="12">
        <el-card class="quick-actions-card" shadow="hover">
          <template #header>
            <span>快速操作</span>
          </template>
          
          <div class="quick-actions">
            <el-button 
              type="primary" 
              size="large" 
              @click="handleQuickConnect"
              :disabled="isConnected"
            >
              <el-icon><Connection /></el-icon>
              快速连接
            </el-button>
            
            <el-button 
              type="success" 
              size="large" 
              @click="handleTakeScreenshot"
              :disabled="!isTargetSet"
            >
              <el-icon><Camera /></el-icon>
              截图
            </el-button>
            
            <el-button 
              type="warning" 
              size="large" 
              @click="handleRefreshStatus"
            >
              <el-icon><Refresh /></el-icon>
              刷新状态
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="system-info-card" shadow="hover">
          <template #header>
            <span>系统信息</span>
          </template>
          
          <el-descriptions :column="1" border>
            <el-descriptions-item label="测试服务器">
              {{ testServerInfo }}
            </el-descriptions-item>
            <el-descriptions-item label="当前目标">
              {{ currentTargetInfo }}
            </el-descriptions-item>
            <el-descriptions-item label="连接状态">
              <el-tag :type="isConnected ? 'success' : 'danger'">
                {{ isConnected ? '已连接' : '未连接' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="运行时间">
              {{ uptime }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近操作日志 -->
    <el-card class="recent-operations-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>最近操作日志</span>
          <el-button type="text" @click="$router.push('/operation')">
            查看全部
          </el-button>
        </div>
      </template>
      
      <div v-if="recentLogs.length === 0" class="no-logs">
        <el-empty description="暂无操作日志" />
      </div>
      
      <div v-else class="log-list">
        <div 
          v-for="(log, index) in recentLogs" 
          :key="index"
          class="log-item"
        >
          <div class="log-content">{{ log }}</div>
        </div>
      </div>
    </el-card>

    <!-- 机器和应用状态 -->
    <el-row v-if="isConnected" :gutter="20" class="status-row">
      <el-col :span="12">
        <el-card class="machines-card" shadow="hover">
          <template #header>
            <span>机器状态</span>
          </template>
          
          <div v-if="machines.length === 0" class="no-machines">
            <el-empty description="暂无可用机器" />
          </div>
          
          <div v-else class="machine-list">
            <div 
              v-for="machine in machines" 
              :key="machine.id"
              class="machine-item"
            >
              <el-tag :type="machine.status === 'connected' ? 'success' : 'danger'" size="small">
                {{ machine.status }}
              </el-tag>
              <span class="machine-name">{{ machine.address }}</span>
              <span class="machine-apps">应用: {{ machine.apps.length }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="apps-card" shadow="hover">
          <template #header>
            <span>应用状态</span>
          </template>
          
          <div v-if="apps.length === 0" class="no-apps">
            <el-empty description="暂无可用应用" />
          </div>
          
          <div v-else class="app-list">
            <div 
              v-for="app in apps" 
              :key="app.id"
              class="app-item"
            >
              <el-tag :type="app.status === 'running' ? 'success' : 'warning'" size="small">
                {{ app.status }}
              </el-tag>
              <span class="app-name">{{ app.name }}</span>
              <span class="app-machine">机器: {{ app.machine_id }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useOperationStore } from '@/stores/operation'

const operationStore = useOperationStore()

// 响应式数据
const uptime = ref('00:00:00')
const startTime = ref(Date.now())

// 计算属性
const isConnected = computed(() => operationStore.isConnected)
const isTargetSet = computed(() => operationStore.isTargetSet)
const machines = computed(() => operationStore.machines)
const apps = computed(() => operationStore.apps)
const operationLogs = computed(() => operationStore.operationLogs)

const testServerInfo = computed(() => {
  if (!isConnected.value) return '未连接'
  const config = operationStore.connectionConfig
  return `${config.host}:${config.port}`
})

const currentTargetInfo = computed(() => {
  if (!isTargetSet.value) return '未设置'
  const target = operationStore.currentTarget
  return `${target?.machine_id} / ${target?.app_name}`
})

const totalOperations = computed(() => operationLogs.value.length)
const availableMachines = computed(() => machines.value.length)

const recentLogs = computed(() => {
  return operationLogs.value.slice(-5).reverse()
})

const lastOperationTime = computed(() => {
  if (recentLogs.value.length === 0) return '无'
  const lastLog = recentLogs.value[0]
  // 从日志中提取时间戳
  const timeMatch = lastLog.match(/\[(.*?)\]/)
  return timeMatch ? timeMatch[1] : '未知'
})

// 方法
const handleQuickConnect = async () => {
  try {
    const success = await operationStore.startServer(8889)
    if (success) {
      ElMessage.success('测试服务器已启动')
    } else {
      ElMessage.error('启动测试服务器失败')
    }
  } catch (error) {
    ElMessage.error(`启动失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleTakeScreenshot = async () => {
  try {
    const result = await operationStore.takeScreenshot()
    if (result) {
      ElMessage.success('截图成功')
    } else {
      ElMessage.error('截图失败')
    }
  } catch (error) {
    ElMessage.error(`截图失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleRefreshStatus = async () => {
  try {
    await operationStore.refreshConnectionStatus()
    if (isConnected.value) {
      await operationStore.refreshMachines()
      await operationStore.refreshCurrentTarget()
    }
    ElMessage.success('状态已刷新')
  } catch (error) {
    ElMessage.error(`刷新状态失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const updateUptime = () => {
  const now = Date.now()
  const diff = now - startTime.value
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)
  uptime.value = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

// 生命周期
onMounted(async () => {
  // 每秒更新运行时间
  setInterval(updateUptime, 1000)
  
  // 初始化状态
  await operationStore.initialize()
})
</script>

<style lang="less" scoped>
.dashboard-page {
  .stats-row {
    margin-bottom: 20px;
  }

  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      gap: 15px;
    }

    .stat-icon {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: white;

      &.success {
        background: linear-gradient(135deg, #67c23a, #85ce61);
      }

      &.primary {
        background: linear-gradient(135deg, #409eff, #66b1ff);
      }

      &.warning {
        background: linear-gradient(135deg, #e6a23c, #ebb563);
      }

      &.info {
        background: linear-gradient(135deg, #909399, #a6a9ad);
      }
    }

    .stat-info {
      .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 5px;
      }

      .stat-label {
        font-size: 14px;
        color: #909399;
      }
    }
  }

  .quick-actions-row {
    margin-bottom: 20px;
  }

  .quick-actions-card {
    .quick-actions {
      display: flex;
      gap: 15px;
      flex-wrap: wrap;
    }
  }

  .recent-operations-card {
    margin-bottom: 20px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .no-logs {
      padding: 20px;
      text-align: center;
    }

    .log-list {
      .log-item {
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
        
        &:last-child {
          border-bottom: none;
        }
        
        .log-content {
          font-family: 'Courier New', monospace;
          font-size: 12px;
          color: #606266;
          word-break: break-all;
        }
      }
    }
  }

  .status-row {
    margin-bottom: 20px;
  }

  .machines-card, .apps-card {
    .no-machines, .no-apps {
      padding: 20px;
      text-align: center;
    }

    .machine-list, .app-list {
      .machine-item, .app-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
        
        &:last-child {
          border-bottom: none;
        }
        
        .machine-name, .app-name {
          flex: 1;
          font-weight: 500;
        }
        
        .machine-apps, .app-machine {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }
}
</style> 