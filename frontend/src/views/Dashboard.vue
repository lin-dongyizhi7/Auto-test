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

    <!-- 机器列表 -->
    <el-card class="machines-overview-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>机器列表</span>
          <div class="actions">
            <el-button type="primary" size="small" @click="openCreateConnection">新建连接</el-button>
            <el-button type="success" size="small" @click="openAddMachine">添加机器</el-button>
          </div>
        </div>
      </template>

      <div v-if="machineInfoList.length === 0" class="no-machines">
        <el-empty description="暂无机器信息" />
      </div>

      <el-row v-else :gutter="16">
        <el-col v-for="m in machineInfoList" :key="m.id" :span="8">
          <el-card class="machine-card" shadow="hover">
            <div class="machine-header">
              <div class="machine-row" @click="$router.push({ name: 'Operation', query: { machine: m.id } })">
                <el-tag :type="m.status === 'connected' ? 'success' : m.status === 'error' ? 'danger' : 'info'" size="small">
                  {{ m.status === 'connected' ? '已连接' : m.status === 'error' ? '连接错误' : '未连接' }}
                </el-tag>
                <span class="machine-name">{{ m.name }}</span>
              </div>
              <div class="machine-actions">
                <el-button 
                  v-if="m.status !== 'connected'"
                  type="success" 
                  size="small" 
                  :icon="Connection" 
                  circle 
                  @click.stop="handleConnectMachine(m.id)"
                  :loading="connectingMachine === m.id"
                  title="连接"
                />
                <el-button 
                  v-else
                  type="danger" 
                  size="small" 
                  :icon="Close" 
                  circle 
                  @click.stop="handleDisconnectMachine(m.id)"
                  :loading="disconnectingMachine === m.id"
                  title="断开连接"
                />
              </div>
            </div>
            <div class="machine-meta">
              <span>地址：{{ m.host }}:{{ m.port }}</span>
              <span>ID：{{ m.id }}</span>
              <span>应用数：{{ m.apps_count || 0 }}</span>
            </div>
            <div class="machine-info">
              <span v-if="m.description">描述：{{ m.description }}</span>
              <span v-if="m.connected_at">连接时间：{{ new Date(m.connected_at * 1000).toLocaleString() }}</span>
              <span v-if="m.last_connected_at">最后连接：{{ new Date(m.last_connected_at).toLocaleString() }}</span>
              <span v-if="m.connection_count">连接次数：{{ m.connection_count }}</span>
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

    <!-- 添加机器对话框 -->
    <el-dialog v-model="addMachineDialogVisible" title="添加机器" width="420px">
      <el-form label-width="100px">
        <el-form-item label="机器名称" required>
          <el-input v-model="newMachineName" placeholder="测试机器1" />
        </el-form-item>
        <el-form-item label="主机地址" required>
          <el-input v-model="newMachineHost" placeholder="192.168.1.100" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input v-model.number="newMachinePort" type="number" placeholder="8888" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newMachineDescription" type="textarea" placeholder="机器描述信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addMachineDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addingMachine" @click="addMachine">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Close, Connection } from '@element-plus/icons-vue'
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

// 断开连接状态
const disconnectingMachine = ref<string | null>(null)
const connectingMachine = ref<string | null>(null)

// 添加机器对话框
const addMachineDialogVisible = ref(false)
const newMachineName = ref('')
const newMachineHost = ref('')
const newMachinePort = ref(8888)
const newMachineDescription = ref('')
const addingMachine = ref(false)

// 计算属性
const isConnected = computed(() => operationStore.isConnected)
const isTargetSet = computed(() => operationStore.isTargetSet)
const machines = computed(() => operationStore.machines)
const apps = computed(() => operationStore.apps)
const operationLogs = computed(() => operationStore.operationLogs)
const machineInfoList = computed(() => operationStore.machineInfoList)

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
    // 首先添加机器信息
    const machineName = `机器_${targetMachineIP.value.replace(/\./g, '_')}`
    const addSuccess = await operationStore.addNewMachineInfo(
      machineName,
      targetMachineIP.value,
      targetMachinePort.value,
      '通过新建连接添加的机器'
    )
    
    if (addSuccess) {
      ElMessage.success(`机器信息已添加: ${machineName}`)
      const success = await operationStore.connectToTargetMachine(
        targetMachineIP.value,
        targetMachinePort.value
      )
      if (success) {
        ElMessage.success(`成功连接到目标机器 ${targetMachineIP.value}:${targetMachinePort.value}`)
      } else {
        ElMessage.error(`连接失败`)
      }
      connectionDialogVisible.value = false
      // 清空输入
      targetMachineIP.value = ''
      targetMachinePort.value = 8888
    } else {
      ElMessage.error('添加机器信息失败')
    }
  } catch (error) {
    ElMessage.error(`添加失败: ${error instanceof Error ? error.message : '未知错误'}`)
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

const handleConnectMachine = async (machineId: string) => {
  try {
    connectingMachine.value = machineId
    const success = await operationStore.connectToTargetMachineById(machineId)
    
    if (success) {
      ElMessage.success(`成功连接到机器 ${machineId}`)
    } else {
      ElMessage.error(`连接失败`)
    }
  } catch (error) {
    ElMessage.error(`连接失败: ${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    connectingMachine.value = null
  }
}

const handleDisconnectMachine = async (machineId: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要断开与机器 ${machineId} 的连接吗？`,
      '确认断开连接',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    disconnectingMachine.value = machineId
    const success = await operationStore.disconnectTargetMachine(machineId)
    
    if (success) {
      ElMessage.success(`已断开与机器 ${machineId} 的连接`)
    } else {
      ElMessage.error(`断开连接失败`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`断开连接失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  } finally {
    disconnectingMachine.value = null
  }
}

const openAddMachine = () => {
  newMachineName.value = ''
  newMachineHost.value = ''
  newMachinePort.value = 8888
  newMachineDescription.value = ''
  addMachineDialogVisible.value = true
}

const addMachine = async () => {
  if (!newMachineName.value || !newMachineHost.value) {
    ElMessage.warning('请输入机器名称和主机地址')
    return
  }
  
  addingMachine.value = true
  try {
    const success = await operationStore.addNewMachineInfo(
      newMachineName.value,
      newMachineHost.value,
      newMachinePort.value,
      newMachineDescription.value
    )
    
    if (success) {
      ElMessage.success('机器信息添加成功')
      addMachineDialogVisible.value = false
      // 清空输入
      newMachineName.value = ''
      newMachineHost.value = ''
      newMachinePort.value = 8888
      newMachineDescription.value = ''
    } else {
      ElMessage.error('添加机器信息失败')
    }
  } catch (error) {
    ElMessage.error(`添加失败: ${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    addingMachine.value = false
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
  await operationStore.refreshMachineInfo().catch(() => {})
})
</script>

<style lang="less" scoped>
.dashboard-page {
  .stats-row { margin-bottom: 20px; }
  .machines-overview-card { margin-bottom: 20px; }
  .machine-card { 
    cursor: pointer; 
    width: 320px;
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
  }
  
  .machine-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .machine-actions {
    display: flex;
    gap: 4px;
  }
  
  .machine-row { 
    display: flex; 
    align-items: center; 
    gap: 10px; 
    flex: 1;
    cursor: pointer;
  }
  
  .machine-name { 
    font-weight: 600; 
    color: #303133;
  }
  
  .machine-meta { 
    margin-top: 8px; 
    color: #909399; 
    display: flex; 
    justify-content: space-between; 
    font-size: 13px;
  }
  
  .machine-info { 
    margin-top: 8px; 
    color: #909399; 
    font-size: 12px; 
    display: flex; 
    flex-direction: column; 
    gap: 4px; 
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 