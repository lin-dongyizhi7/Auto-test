<template>
  <div class="operation-page">
    <!-- 服务端测试服务器状态面板 -->
    <el-card class="status-panel" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>测试服务器状态</span>
          <el-tag :type="isConnected ? 'success' : 'danger'" size="small">
            {{ isConnected ? '已连接' : '未连接' }}
          </el-tag>
        </div>
      </template>
      
      <el-descriptions :column="3" border>
        <el-descriptions-item label="监听端口">
          {{ connectionForm.port }}
        </el-descriptions-item>
        <el-descriptions-item label="当前目标">
          {{ currentTarget ? `${currentTarget.machine_id} / ${currentTarget.app_name}` : '未设置' }}
        </el-descriptions-item>
        <el-descriptions-item label="可用机器">
          {{ availableMachines.length }} 台
        </el-descriptions-item>
      </el-descriptions>
      
      <div class="status-actions">
        <el-button 
          v-if="!isConnected"
          type="primary" 
          @click="handleConnect"
          :loading="connecting"
        >
          启动测试服务器
        </el-button>
        <el-button 
          v-else
          type="danger" 
          @click="handleDisconnect"
        >
          停止测试服务器
        </el-button>
        <el-button 
          type="success"
          @click="refreshStatus"
          :disabled="!isConnected"
        >
          刷新状态
        </el-button>
      </div>
    </el-card>

    <!-- 目标机器和应用选择面板 -->
    <el-card v-if="isConnected" class="target-panel" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>目标机器和应用</span>
          <el-tag v-if="currentTarget" type="info" size="small">
            当前: {{ currentTarget.machine_id }} / {{ currentTarget.app_name }}
          </el-tag>
        </div>
      </template>
      
      <el-row :gutter="20">
        <!-- 机器选择 -->
        <el-col :span="8">
          <el-form label-width="80px">
            <el-form-item label="选择机器">
              <el-select 
                v-model="selectedMachineId" 
                placeholder="选择目标机器"
                @change="handleMachineChange"
                :loading="loadingMachines"
                style="width: 100%"
              >
                <el-option 
                  v-for="machine in availableMachines" 
                  :key="machine.id"
                  :label="machine.address"
                  :value="machine.id"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </el-col>
        
        <!-- 应用选择 -->
        <el-col :span="8">
          <el-form label-width="80px">
            <el-form-item label="选择应用">
              <el-select 
                v-model="selectedAppName" 
                placeholder="选择目标应用"
                @change="handleAppChange"
                :loading="loadingApps"
                :disabled="!selectedMachineId"
                style="width: 100%"
              >
                <el-option 
                  v-for="app in availableApps" 
                  :key="app.id"
                  :label="app.name"
                  :value="app.name"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </el-col>
        
        <!-- 设置目标按钮 -->
        <el-col :span="8">
          <el-form-item>
            <el-button 
              type="primary" 
              @click="handleSetTarget"
              :disabled="!selectedMachineId || !selectedAppName"
              style="margin-top: 32px"
            >
              设置目标
            </el-button>
          </el-form-item>
        </el-col>
      </el-row>
    </el-card>

    <!-- 操作控制面板 -->
    <el-row v-if="isTargetSet" :gutter="20" class="operation-panels">
      <!-- 元素操作面板 -->
      <el-col :span="12">
        <el-card class="operation-panel" shadow="hover">
          <template #header>
            <span>元素操作</span>
          </template>
          
          <el-form :model="elementForm" label-width="80px">
            <el-form-item label="元素路径">
              <el-input 
                v-model="elementForm.path" 
                placeholder="菜单/文件/新建"
              />
            </el-form-item>
            <el-form-item label="角色名称">
              <el-select 
                v-model="elementForm.roles" 
                multiple 
                placeholder="选择角色"
                style="width: 100%"
              >
                <el-option label="push button" value="push button" />
                <el-option label="menu item" value="menu item" />
                <el-option label="text" value="text" />
                <el-option label="table cell" value="table cell" />
                <el-option label="combo box" value="combo box" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button-group>
                <el-button 
                  type="primary" 
                  @click="handleClickElement"
                >
                  点击
                </el-button>
                <el-button 
                  @click="handleRightClickElement"
                >
                  右键
                </el-button>
                <el-button 
                  @click="handleDoubleClickElement"
                >
                  双击
                </el-button>
              </el-button-group>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 图片操作面板 -->
      <el-col :span="12">
        <el-card class="operation-panel" shadow="hover">
          <template #header>
            <span>图片操作</span>
          </template>
          
          <el-form :model="imageForm" label-width="80px">
            <el-form-item label="图片路径">
              <el-input 
                v-model="imageForm.imagePath" 
                placeholder="/path/to/image.png"
              />
            </el-form-item>
            <el-form-item label="匹配阈值">
              <el-slider 
                v-model="imageForm.threshold" 
                :min="0.1" 
                :max="1.0" 
                :step="0.1"
                show-input
              />
            </el-form-item>
            <el-form-item>
              <el-button-group>
                <el-button 
                  type="primary" 
                  @click="handleClickImage"
                >
                  点击图片
                </el-button>
                <el-button 
                  @click="handleFindImage"
                >
                  查找图片
                </el-button>
              </el-button-group>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 其他操作面板 -->
    <el-row v-if="isTargetSet" :gutter="20" class="operation-panels">
      <!-- 拖拽操作面板 -->
      <el-col :span="12">
        <el-card class="operation-panel" shadow="hover">
          <template #header>
            <span>拖拽操作</span>
          </template>
          
          <el-form :model="dragForm" label-width="80px">
            <el-form-item label="起始坐标">
              <el-input-number v-model="dragForm.startX" placeholder="X" style="width: 80px" />
              <el-input-number v-model="dragForm.startY" placeholder="Y" style="width: 80px" />
            </el-form-item>
            <el-form-item label="结束坐标">
              <el-input-number v-model="dragForm.endX" placeholder="X" style="width: 80px" />
              <el-input-number v-model="dragForm.endY" placeholder="Y" style="width: 80px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleDragTo">
                执行拖拽
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 文本输入面板 -->
      <el-col :span="12">
        <el-card class="operation-panel" shadow="hover">
          <template #header>
            <span>文本输入</span>
          </template>
          
          <el-form :model="textForm" label-width="80px">
            <el-form-item label="输入文本">
              <el-input 
                v-model="textForm.text" 
                placeholder="要输入的文本"
              />
            </el-form-item>
            <el-form-item label="元素路径">
              <el-input 
                v-model="textForm.elementPath" 
                placeholder="目标元素路径（可选）"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleInputText">
                输入文本
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷键操作和截图面板 -->
    <el-row v-if="isTargetSet" :gutter="20" class="operation-panels">
      <el-col :span="12">
        <el-card class="operation-panel" shadow="hover">
          <template #header>
            <span>快捷键操作</span>
          </template>
          
          <el-form :model="hotkeyForm" label-width="80px">
            <el-form-item label="按键组合">
              <el-select 
                v-model="hotkeyForm.keys" 
                multiple 
                placeholder="选择按键"
                style="width: 100%"
              >
                <el-option label="Ctrl" value="Ctrl" />
                <el-option label="Alt" value="Alt" />
                <el-option label="Shift" value="Shift" />
                <el-option label="a" value="a" />
                <el-option label="c" value="c" />
                <el-option label="v" value="v" />
                <el-option label="x" value="x" />
                <el-option label="z" value="z" />
                <el-option label="Enter" value="Enter" />
                <el-option label="Tab" value="Tab" />
                <el-option label="Escape" value="Escape" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleHotkey">
                执行快捷键
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 截图面板 -->
      <el-col :span="12">
        <el-card class="operation-panel" shadow="hover">
          <template #header>
            <span>截图功能</span>
          </template>
          
          <el-form label-width="80px">
            <el-form-item label="截图区域">
              <el-input 
                v-model="screenshotRegion" 
                placeholder="x,y,width,height（可选）"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleTakeScreenshot">
                获取截图
              </el-button>
            </el-form-item>
          </el-form>
          
          <!-- 截图显示 -->
          <div v-if="currentScreenshot" class="screenshot-display">
            <img 
              :src="`data:image/png;base64,${currentScreenshot.screenshot}`" 
              :alt="`截图 - ${currentScreenshot.app_name}`"
              style="max-width: 100%; max-height: 200px; border: 1px solid #ddd;"
            />
            <p class="screenshot-info">
              尺寸: {{ currentScreenshot.size.width }} x {{ currentScreenshot.size.height }}
            </p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 机器视图监控面板 -->
    <el-card v-if="isConnected && availableMachines.length > 0" class="machine-view-panel" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>机器视图监控</span>
          <div class="view-controls">
            <el-button 
              size="small" 
              @click="previousMachine" 
              :disabled="currentMachineIndex === 0"
            >
              <el-icon><ArrowLeft /></el-icon>
              上一个
            </el-button>
            <span class="machine-counter">
              {{ currentMachineIndex + 1 }} / {{ availableMachines.length }}
            </span>
            <el-button 
              size="small" 
              @click="nextMachine"
              :disabled="currentMachineIndex === availableMachines.length - 1"
            >
              下一个
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="machine-view-content">
        <div class="current-machine-info">
          <el-tag size="large" type="primary">
            {{ currentViewMachine?.address || '未知机器' }}
          </el-tag>
          <el-tag size="large" type="info">
            ID: {{ currentViewMachine?.id || 'N/A' }}
          </el-tag>
        </div>
        
        <div class="machine-apps-grid">
          <div 
            v-for="app in currentViewMachineApps" 
            :key="app.id"
            class="app-card"
            :class="{ 'current-target': isCurrentTarget(app) }"
            @click="setAsTarget(app)"
          >
            <div class="app-header">
              <el-tag 
                :type="getAppStatusType(app.status)" 
                size="small"
              >
                {{ app.status || 'running' }}
              </el-tag>
              <span class="app-name">{{ app.name }}</span>
            </div>
            <div class="app-details">
              <span class="app-region" v-if="app.region">
                区域: {{ app.region }}
              </span>
              <span class="app-machine-id">
                机器: {{ app.machine_id }}
              </span>
            </div>
            <div class="app-actions">
              <el-button 
                size="small" 
                type="primary"
                @click.stop="takeMachineScreenshot(app)"
              >
                截图
              </el-button>
            </div>
          </div>
        </div>
        
        <div v-if="currentViewMachineApps.length === 0" class="no-apps">
          <el-empty description="该机器暂无可用应用" />
        </div>
      </div>
    </el-card>

    <!-- 操作日志面板 -->
    <el-card class="log-panel" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>操作日志</span>
          <div class="log-actions">
            <el-button size="small" @click="refreshLogs">刷新</el-button>
            <el-button size="small" @click="clearLogs">清空日志</el-button>
          </div>
        </div>
      </template>
      
      <div class="log-content">
        <div v-if="operationLogs.length === 0" class="no-logs">
          <el-empty description="暂无操作日志" />
        </div>
        <div 
          v-else
          v-for="(log, index) in operationLogs" 
          :key="index"
          class="log-entry"
        >
          <span class="log-time">{{ formatLogTime(log) }}</span>
          <span class="log-message">{{ log }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useOperationStore } from '@/stores/operation'
import type { MachineAppTarget } from '@/api/types'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

const store = useOperationStore()

// 响应式数据
const connectionForm = ref({
  host: 'localhost',
  port: 8888
})

const selectedMachineId = ref('')
const selectedAppName = ref('')
const screenshotRegion = ref('')

// 表单数据
const elementForm = ref({
  path: '',
  roles: [] as string[]
})

const imageForm = ref({
  imagePath: '',
  threshold: 0.8
})

const dragForm = ref({
  startX: 0,
  startY: 0,
  endX: 100,
  endY: 100
})

const textForm = ref({
  text: '',
  elementPath: ''
})

const hotkeyForm = ref({
  keys: [] as string[]
})

// 计算属性
const isConnected = computed(() => store.isConnected)
const connecting = computed(() => store.connecting)
const currentTarget = computed(() => store.currentTarget)
const isTargetSet = computed(() => store.isTargetSet)
const availableMachines = computed(() => store.availableMachines)
const availableApps = computed(() => store.availableApps)
const loadingMachines = computed(() => store.loadingMachines)
const loadingApps = computed(() => store.loadingApps)
const operationLogs = computed(() => store.operationLogs)
const currentScreenshot = computed(() => store.currentScreenshot)

// 方法
const handleConnect = async () => {
  const success = await store.connect(connectionForm.value)
  if (success) {
    ElMessage.success('连接成功')
  } else {
    ElMessage.error('连接失败')
  }
}

const handleDisconnect = async () => {
  const success = await store.disconnect()
  if (success) {
    ElMessage.success('已断开连接')
    selectedMachineId.value = ''
    selectedAppName.value = ''
  } else {
    ElMessage.error('断开连接失败')
  }
}

const refreshStatus = async () => {
  try {
    await store.refreshConnectionStatus()
    if (isConnected.value) {
      await store.refreshMachines()
      await store.refreshCurrentTarget()
    }
    ElMessage.success('状态已刷新')
  } catch (error) {
    ElMessage.error(`刷新状态失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleMachineChange = async () => {
  selectedAppName.value = ''
  if (selectedMachineId.value) {
    await store.refreshApps(selectedMachineId.value)
  }
}

const handleAppChange = () => {
  // 应用选择改变时的处理
}

const handleSetTarget = async () => {
  if (!selectedMachineId.value || !selectedAppName.value) {
    ElMessage.warning('请选择机器和应用')
    return
  }

  const target: MachineAppTarget = {
    machine_id: selectedMachineId.value,
    app_name: selectedAppName.value
  }

  const success = await store.setCurrentTarget(target)
  if (success) {
    ElMessage.success('设置目标成功')
  } else {
    ElMessage.error('设置目标失败')
  }
}

const handleClickElement = async () => {
  if (!elementForm.value.path) {
    ElMessage.warning('请输入元素路径')
    return
  }

  const success = await store.performClickElement({
    path: elementForm.value.path,
    roles: elementForm.value.roles
  })

  if (success) {
    ElMessage.success('点击元素成功')
  }
}

const handleRightClickElement = async () => {
  // 实现右键点击逻辑
  ElMessage.info('右键点击功能待实现')
}

const handleDoubleClickElement = async () => {
  // 实现双击逻辑
  ElMessage.info('双击功能待实现')
}

const handleClickImage = async () => {
  if (!imageForm.value.imagePath) {
    ElMessage.warning('请输入图片路径')
    return
  }

  const success = await store.performClickImage({
    imagePath: imageForm.value.imagePath,
    threshold: imageForm.value.threshold
  })

  if (success) {
    ElMessage.success('点击图片成功')
  }
}

const handleFindImage = async () => {
  if (!imageForm.value.imagePath) {
    ElMessage.warning('请输入图片路径')
    return
  }

  const result = await store.performFindImage({
    imagePath: imageForm.value.imagePath,
    threshold: imageForm.value.threshold
  })

  if (result) {
    ElMessage.success('查找图片成功')
  }
}

const handleDragTo = async () => {
  const success = await store.performDragTo(dragForm.value)
  if (success) {
    ElMessage.success('拖拽操作成功')
  }
}

const handleInputText = async () => {
  if (!textForm.value.text) {
    ElMessage.warning('请输入要输入的文本')
    return
  }

  const success = await store.performInputText({
    text: textForm.value.text,
    elementPath: textForm.value.elementPath || undefined
  })

  if (success) {
    ElMessage.success('文本输入成功')
  }
}

const handleHotkey = async () => {
  if (hotkeyForm.value.keys.length === 0) {
    ElMessage.warning('请选择按键组合')
    return
  }

  const success = await store.performHotkey({
    keys: hotkeyForm.value.keys
  })

  if (success) {
    ElMessage.success('快捷键操作成功')
  }
}

const handleTakeScreenshot = async () => {
  const result = await store.takeScreenshot(screenshotRegion.value || undefined)
  if (result) {
    ElMessage.success('截图成功')
  }
}

const refreshLogs = () => {
  // 刷新日志的逻辑
  ElMessage.success('日志已刷新')
}

const clearLogs = () => {
  store.clearLogs()
}

const formatLogTime = (log: string) => {
  const timeMatch = log.match(/\[(.*?)\]/)
  return timeMatch ? timeMatch[1] : ''
}

// 机器视图相关
const currentMachineIndex = ref(0)
const currentViewMachine = computed(() => availableMachines.value[currentMachineIndex.value])
const currentViewMachineApps = computed(() => {
  if (!currentViewMachine.value) return []
  return store.availableApps.filter((app: any) => app.machine_id === currentViewMachine.value.id)
})

const isCurrentTarget = (app: { machine_id: string; name: string }) => {
  return currentTarget.value?.machine_id === app.machine_id && currentTarget.value?.app_name === app.name
}

const setAsTarget = async (app: { machine_id: string; name: string }) => {
  const target: MachineAppTarget = {
    machine_id: app.machine_id,
    app_name: app.name
  }
  const success = await store.setCurrentTarget(target)
  if (success) {
    ElMessage.success(`已设置目标为: ${app.machine_id} / ${app.name}`)
  } else {
    ElMessage.error('设置目标失败')
  }
}

const takeMachineScreenshot = async (app: { machine_id: string; name: string }) => {
  try {
    // 先设置目标，再截图
    const target: MachineAppTarget = {
      machine_id: app.machine_id,
      app_name: app.name
    }
    await store.setCurrentTarget(target)
    const result = await store.takeScreenshot()
    if (result) {
      ElMessage.success('截图成功')
    }
  } catch (error) {
    ElMessage.error('截图失败')
  }
}

const getAppStatusType = (status: string): 'success' | 'danger' | 'warning' | 'info' => {
  const statusMap: Record<string, 'success' | 'danger' | 'warning' | 'info'> = {
    running: 'success',
    stopped: 'danger',
    starting: 'warning',
    error: 'danger'
  }
  return statusMap[status] || 'info'
}

const previousMachine = () => {
  currentMachineIndex.value--
  if (currentMachineIndex.value < 0) {
    currentMachineIndex.value = availableMachines.value.length - 1
  }
}

const nextMachine = () => {
  currentMachineIndex.value++
  if (currentMachineIndex.value >= availableMachines.value.length) {
    currentMachineIndex.value = 0
  }
}

// 生命周期
onMounted(async () => {
  await store.initialize()
})
</script>

<style scoped lang="less">
.operation-page {
  padding: 20px;
  
  .status-panel,
  .target-panel,
  .operation-panel,
  .log-panel,
  .machine-view-panel {
    margin-bottom: 20px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .status-actions {
    margin-top: 15px;
    text-align: center;
    
    .el-button {
      margin: 0 10px;
    }
  }
  
  .operation-panels {
    margin-bottom: 20px;
  }

  .machine-view-panel {
    .view-controls {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .machine-counter {
      font-size: 14px;
      color: #606266;
    }

    .machine-view-content {
      padding: 15px;
    }

    .current-machine-info {
      text-align: center;
      margin-bottom: 15px;
      .el-tag {
        margin-right: 10px;
      }
    }

    .machine-apps-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 15px;
      margin-bottom: 15px;
    }

    .app-card {
      border: 1px solid #ebeef5;
      border-radius: 8px;
      padding: 15px;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      flex-direction: column;
      justify-content: space-between;

      &:hover {
        border-color: #409eff;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      }

      &.current-target {
        border-color: #67c23a;
        box-shadow: 0 0 10px rgba(103, 194, 58, 0.3);
      }
    }

    .app-header {
      display: flex;
      align-items: center;
      margin-bottom: 10px;
      .el-tag {
        margin-right: 8px;
      }
      .app-name {
        font-size: 16px;
        font-weight: bold;
        color: #303133;
      }
    }

    .app-details {
      font-size: 13px;
      color: #909399;
      margin-bottom: 10px;
      .app-region {
        margin-right: 10px;
      }
    }

    .app-actions {
      text-align: right;
      margin-top: 10px;
    }

    .no-apps {
      text-align: center;
      padding: 40px 0;
    }
  }
  
  .log-panel {
    .log-actions {
      display: flex;
      gap: 10px;
    }
  }
  
  .log-content {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    padding: 10px;
    background-color: #fafafa;
    
    .no-logs {
      text-align: center;
      padding: 40px 0;
    }
    
    .log-entry {
      font-family: 'Courier New', monospace;
      font-size: 12px;
      line-height: 1.5;
      margin-bottom: 8px;
      word-break: break-all;
      display: flex;
      gap: 10px;
      
      .log-time {
        color: #909399;
        min-width: 120px;
        flex-shrink: 0;
      }
      
      .log-message {
        color: #303133;
        flex: 1;
      }
    }
  }
  
  .screenshot-display {
    margin-top: 15px;
    text-align: center;
    
    .screenshot-info {
      margin-top: 10px;
      font-size: 12px;
      color: #666;
    }
  }
}
</style> 