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
              <div class="stat-value">{{ successRate }}%</div>
              <div class="stat-label">成功率</div>
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
              :disabled="!isConnected"
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
            <el-descriptions-item label="目标主机">
              {{ targetHost }}
            </el-descriptions-item>
            <el-descriptions-item label="连接端口">
              {{ targetPort }}
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

    <!-- 最近操作 -->
    <el-card class="recent-operations-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>最近操作</span>
          <el-button type="text" @click="$router.push('/operation')">
            查看全部
          </el-button>
        </div>
      </template>
      
      <el-table :data="recentOperations" style="width: 100%" size="small">
        <el-table-column prop="type" label="操作类型" width="120" />
        <el-table-column prop="params" label="参数" show-overflow-tooltip />
        <el-table-column prop="result.success" label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.result.success ? 'success' : 'danger'" size="small">
              {{ row.result.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
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
const targetHost = computed(() => operationStore.targetHost)
const targetPort = computed(() => operationStore.targetPort)
const totalOperations = computed(() => operationStore.operationHistory.length)
const successRate = computed(() => operationStore.successRate)
const recentOperations = computed(() => operationStore.recentOperations.slice(0, 5))

const lastOperationTime = computed(() => {
  if (recentOperations.value.length === 0) return '无'
  const lastOp = recentOperations.value[0]
  return formatTime(lastOp.timestamp)
})

// 方法
const handleQuickConnect = async () => {
  try {
    await operationStore.connect('localhost', 8888)
    ElMessage.success('快速连接成功')
  } catch (error) {
    ElMessage.error(`快速连接失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleTakeScreenshot = () => {
  ElMessage.info('截图功能开发中...')
}

const handleRefreshStatus = () => {
  ElMessage.success('状态已刷新')
}

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  return date.toLocaleString()
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
onMounted(() => {
  // 每秒更新运行时间
  setInterval(updateUptime, 1000)
})
</script>

<style lang="scss" scoped>
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
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
}
</style> 