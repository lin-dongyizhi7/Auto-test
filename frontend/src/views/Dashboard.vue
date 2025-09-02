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

    <!-- 机器列表（新的卡片） -->
    <el-card class="machines-overview-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>已连接的机器</span>
          <div class="actions">
            <el-button type="primary" size="small" @click="openCreateConnection">新建连接</el-button>
          </div>
        </div>
      </template>

      <div v-if="machines.length === 0" class="no-machines">
        <el-empty description="暂无可用机器" />
      </div>

      <el-row v-else :gutter="16">
        <el-col v-for="m in machines" :key="m.machine_id" :span="8">
          <el-card class="machine-card" shadow="hover">
            <div class="machine-row" @click="$router.push(`/machine/${m.machine_id}`)">
              <el-tag :type="m.status === 'connected' ? 'success' : 'danger'" size="small">{{ m.status }}</el-tag>
              <span class="machine-name">{{ Array.isArray(m.address) ? `${m.address[0]}:${m.address[1]}` : m.address }}</span>
            </div>
            <div class="machine-meta">
              <span>应用数：{{ m.apps_count || 0 }}</span>
              <span>ID：{{ m.machine_id }}</span>
            </div>
            <div class="machine-info">
              <span>连接时间：{{ new Date(m.connected_at * 1000).toLocaleString() }}</span>
              <span>最后活跃：{{ new Date(m.last_seen * 1000).toLocaleString() }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 快速操作 -->
    <el-row :gutter="20" class="quick-actions-row">
      <el-col :span="12">
        <el-card class="quick-actions-card" shadow="hover">
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="success" size="large" @click="handleTakeScreenshot" :disabled="!isTargetSet">
              <el-icon><Camera /></el-icon>
              截图
            </el-button>
            <el-button type="warning" size="large" @click="handleRefreshStatus">
              <el-icon><Refresh /></el-icon>
              刷新状态
            </el-button>
            <el-button type="danger" size="large" @click="handleStopServer" :disabled="!isConnected">
              <el-icon><Close /></el-icon>
              停止服务器
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
              <el-tag :type="isConnected ? 'success' : 'danger'">{{ isConnected ? '已连接' : '未连接' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="运行时间">
              {{ uptime }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近操作日志（保留） -->
    <el-card class="recent-operations-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>最近操作日志</span>
          <el-button type="text" @click="$router.push('/operation')">查看全部</el-button>
        </div>
      </template>
      <div v-if="recentLogs.length === 0" class="no-logs">
        <el-empty description="暂无操作日志" />
      </div>
      <div v-else class="log-list">
        <div v-for="(log, index) in recentLogs" :key="index" class="log-item">
          <div class="log-content">{{ log }}</div>
        </div>
      </div>
    </el-card>

    <!-- 新建连接对话框 -->
    <el-dialog v-model="connectionDialogVisible" title="新建连接" width="420px">
      <el-form label-width="100px">
        <el-form-item label="目标机器IP" required>
          <el-input v-model="targetMachineIP" placeholder="192.168.1.100" />
        </el-form-item>
        <el-form-item label="目标机器端口">
          <el-input v-model.number="targetMachinePort" type="number" placeholder="8888" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="connectionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="connecting" @click="createConnection">连接</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useOperationStore } from '@/stores/operation'
// 移除不再需要的导入，因为机器连接管理已移至后端

const operationStore = useOperationStore()

// 响应式数据
const uptime = ref('00:00:00')
const startTime = ref(Date.now())

// 新建连接对话框
const connectionDialogVisible = ref(false)
const targetMachineIP = ref('')
const targetMachinePort = ref(8888)
const connecting = ref(false)

// 计算属性
const isConnected = computed(() => operationStore.isConnected)
const isTargetSet = computed(() => operationStore.isTargetSet)
const machines = computed(() => operationStore.machines)
const apps = computed(() => operationStore.apps)
const operationLogs = computed(() => operationStore.operationLogs)

const testServerInfo = computed(() => {
  if (!isConnected.value) return '未启动'
  return 'localhost:8888 (默认启动)'
})

const currentTargetInfo = computed(() => {
  if (!isTargetSet.value) return '未设置'
  const target = operationStore.currentTarget
  return `${target?.machine_id} / ${target?.app_name}`
})

const totalOperations = computed(() => operationLogs.value.length)
const availableMachines = computed(() => machines.value.length)

const recentLogs = computed(() => operationLogs.value.slice(-5).reverse())

const lastOperationTime = computed(() => {
  if (recentLogs.value.length === 0) return '无'
  const lastLog = recentLogs.value[0]
  const timeMatch = lastLog.match(/\[(.*?)\]/)
  return timeMatch ? timeMatch[1] : '未知'
})

// 方法
const openCreateConnection = () => { 
  if (!isConnected.value) {
    ElMessage.warning('测试服务器未启动，请稍后再试')
    return
  }
  connectionDialogVisible.value = true 
}

const createConnection = async () => {
  if (!targetMachineIP.value) {
    ElMessage.warning('请输入目标机器IP')
    return
  }
  
  connecting.value = true
  try {
    const success = await operationStore.connectToTargetMachine(
      targetMachineIP.value,
      targetMachinePort.value
    )
    if (success) {
      ElMessage.success(`成功连接到目标机器 ${targetMachineIP.value}:${targetMachinePort.value}`)
      connectionDialogVisible.value = false
      // 清空输入
      targetMachineIP.value = ''
      targetMachinePort.value = 8888
    } else {
      ElMessage.error('连接目标机器失败')
    }
  } catch (error) {
    ElMessage.error(`连接失败: ${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    connecting.value = false
  }
}



const handleStopServer = async () => {
  try {
    const success = await operationStore.stopTestServer()
    if (success) ElMessage.success('测试服务器已停止')
    else ElMessage.error('停止测试服务器失败')
  } catch (error) {
    ElMessage.error(`停止失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleTakeScreenshot = async () => {
  try {
    const result = await operationStore.takeScreenshot()
    if (result) ElMessage.success('截图成功')
    else ElMessage.error('截图失败')
  } catch (error) {
    ElMessage.error(`截图失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleRefreshStatus = async () => {
  try {
    await operationStore.refreshServerStatus()
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
  const pad = (num: number) => String(num).padStart(2, '0')
  uptime.value = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`
}

// 生命周期
onMounted(async () => {
  setInterval(updateUptime, 1000)
  await operationStore.initialize()
  await operationStore.refreshMachines().catch(() => {})
})
</script>

<style lang="less" scoped>
.dashboard-page {
  .stats-row { margin-bottom: 20px; }
  .machines-overview-card { margin-bottom: 20px; }
  .machine-card { cursor: pointer; }
  .machine-row { display: flex; align-items: center; gap: 10px; }
  .machine-name { font-weight: 600; }
  .machine-meta { margin-top: 8px; color: #909399; display: flex; justify-content: space-between; }
  .machine-info { margin-top: 8px; color: #909399; font-size: 12px; display: flex; flex-direction: column; gap: 4px; }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 