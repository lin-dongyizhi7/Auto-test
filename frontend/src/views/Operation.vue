<template>
  <div class="operation-page">
    <!-- 服务端测试服务器控制面板 -->
    <el-card class="connection-panel" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>测试服务器（服务端内置）</span>
          <el-tag :type="isConnected ? 'success' : 'danger'" size="small">
            {{ isConnected ? '已连接' : '未连接' }}
          </el-tag>
        </div>
      </template>
      
      <el-form :model="connectionForm" label-width="100px" inline>
        <el-form-item label="监听端口">
          <el-input-number 
            v-model="connectionForm.port" 
            :min="1" 
            :max="65535"
            :disabled="isConnected"
          />
        </el-form-item>
        <el-form-item>
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
            @click="openNewConnectionDialog"
            style="margin-left: 10px;"
          >
            新建连接
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 多机器多应用管理面板 -->
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
      
      <!-- 刷新按钮 -->
      <div class="refresh-actions">
        <el-button @click="refreshMachines" :loading="loadingMachines">
          刷新机器列表
        </el-button>
        <el-button @click="refreshApps" :loading="loadingApps" :disabled="!selectedMachineId">
          刷新应用列表
        </el-button>
      </div>
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

    <!-- 快捷键操作面板 -->
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

    <!-- 操作日志面板 -->
    <el-card v-if="isConnected" class="log-panel" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>操作日志</span>
          <el-button size="small" @click="clearLogs">清空日志</el-button>
        </div>
      </template>
      
      <div class="log-content">
        <div 
          v-for="(log, index) in operationLogs" 
          :key="index"
          class="log-entry"
        >
          {{ log }}
        </div>
      </div>
    </el-card>
    <!-- 新建连接对话框 -->
    <el-dialog
      v-model="newConnDialogVisible"
      title="新建连接"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form :model="newConnForm" :rules="newConnRules" ref="newConnFormRef" label-width="90px">
        <el-form-item label="目标IP" prop="host">
          <el-input v-model="newConnForm.host" placeholder="例如 192.168.1.101" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="newConnForm.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="应用名" prop="app">
          <el-input v-model="newConnForm.app" placeholder="例如 calculator" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="newConnDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmNewConnection" :loading="creatingConnection">确定</el-button>
        </span>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useOperationStore } from '@/stores/operation'
import type { MachineAppTarget } from '@/api/types'

const store = useOperationStore()

// 响应式数据
const connectionForm = ref({
  host: 'localhost',
  port: 8889
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

// 新建连接对话框
const newConnDialogVisible = ref(false)
const creatingConnection = ref(false)
const newConnFormRef = ref<FormInstance>()
const newConnForm = ref({
  host: '',
  port: 8889,
  app: ''
})
const newConnRules: FormRules = {
  host: [{ required: true, message: '请输入目标IP', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'change' }],
  app: [{ required: true, message: '请输入应用名', trigger: 'blur' }]
}

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

const openNewConnectionDialog = () => {
  newConnDialogVisible.value = true
}

const confirmNewConnection = async () => {
  if (!newConnFormRef.value) return
  await newConnFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      creatingConnection.value = true
      // 确保后端内置测试服务器已启动
      if (!isConnected.value) {
        const ok = await store.startServer(connectionForm.value.port)
        if (!ok) {
          ElMessage.error('启动测试服务器失败')
          return
        }
      }

      // 依据输入构造 machine_id（此处用IP:port 简化）
      const machineId = `${newConnForm.value.host}:${newConnForm.value.port}`
      const target: MachineAppTarget = { machine_id: machineId, app_name: newConnForm.value.app }

      const success = await store.setCurrentTarget(target)
      if (success) {
        ElMessage.success('连接已建立并设置为当前目标')
        selectedMachineId.value = target.machine_id
        selectedAppName.value = target.app_name
        newConnDialogVisible.value = false
      } else {
        ElMessage.error('设置目标失败，请确认被测机已注册到测试服务器')
      }
    } finally {
      creatingConnection.value = false
    }
  })
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

const refreshMachines = async () => {
  await store.refreshMachines()
}

const refreshApps = async () => {
  if (selectedMachineId.value) {
    await store.refreshApps(selectedMachineId.value)
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

const clearLogs = () => {
  store.clearLogs()
}

// 生命周期
onMounted(async () => {
  await store.initialize()
})
</script>

<style scoped lang="less">
.operation-page {
  padding: 20px;
  
  .connection-panel,
  .target-panel,
  .operation-panel,
  .log-panel {
    margin-bottom: 20px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .refresh-actions {
    margin-top: 15px;
    text-align: center;
    
    .el-button {
      margin: 0 10px;
    }
  }
  
  .operation-panels {
    margin-bottom: 20px;
  }
  
  .log-content {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    padding: 10px;
    background-color: #fafafa;
    
    .log-entry {
      font-family: 'Courier New', monospace;
      font-size: 12px;
      line-height: 1.5;
      margin-bottom: 5px;
      word-break: break-all;
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