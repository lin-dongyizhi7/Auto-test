<template>
  <div class="operation-page">
    <!-- 连接控制面板 -->
    <el-card class="connection-panel" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>连接控制</span>
          <el-tag :type="isConnected ? 'success' : 'danger'" size="small">
            {{ isConnected ? '已连接' : '未连接' }}
          </el-tag>
        </div>
      </template>
      
      <el-form :model="connectionForm" label-width="80px" inline>
        <el-form-item label="目标主机">
          <el-input 
            v-model="connectionForm.host" 
            placeholder="192.168.1.100"
            :disabled="isConnected"
          />
        </el-form-item>
        <el-form-item label="端口">
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
            连接
          </el-button>
          <el-button 
            v-else
            type="danger" 
            @click="handleDisconnect"
          >
            断开
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作控制面板 -->
    <el-row :gutter="20" class="operation-panels">
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
                :disabled="!isConnected"
              />
            </el-form-item>
            <el-form-item label="角色名称">
              <el-select 
                v-model="elementForm.roles" 
                multiple 
                placeholder="选择角色"
                :disabled="!isConnected"
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
                  :disabled="!isConnected"
                >
                  点击
                </el-button>
                <el-button 
                  @click="handleRightClickElement"
                  :disabled="!isConnected"
                >
                  右键
                </el-button>
                <el-button 
                  @click="handleDoubleClickElement"
                  :disabled="!isConnected"
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
                v-model="imageForm.path" 
                placeholder="qgis_image/button.png"
                :disabled="!isConnected"
              />
            </el-form-item>
            <el-form-item label="匹配阈值">
              <el-slider 
                v-model="imageForm.threshold" 
                :min="0.1" 
                :max="1" 
                :step="0.1"
                :disabled="!isConnected"
                show-input
              />
            </el-form-item>
            <el-form-item>
              <el-button 
                type="primary" 
                @click="handleClickImage"
                :disabled="!isConnected"
              >
                点击图片
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 拖拽操作面板 -->
    <el-card class="drag-panel" shadow="hover">
      <template #header>
        <span>拖拽操作</span>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="6">
          <el-form :model="dragForm" label-width="80px">
            <el-form-item label="起点X">
              <el-input-number 
                v-model="dragForm.startX" 
                :min="0"
                :disabled="!isConnected"
              />
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="6">
          <el-form :model="dragForm" label-width="80px">
            <el-form-item label="起点Y">
              <el-input-number 
                v-model="dragForm.startY" 
                :min="0"
                :disabled="!isConnected"
              />
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="6">
          <el-form :model="dragForm" label-width="80px">
            <el-form-item label="终点X">
              <el-input-number 
                v-model="dragForm.endX" 
                :min="0"
                :disabled="!isConnected"
              />
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="6">
          <el-form :model="dragForm" label-width="80px">
            <el-form-item label="终点Y">
              <el-input-number 
                v-model="dragForm.endY" 
                :min="0"
                :disabled="!isConnected"
              />
            </el-form-item>
          </el-form>
        </el-col>
      </el-row>
      
      <el-form-item>
        <el-button 
          type="primary" 
          @click="handleDragTo"
          :disabled="!isConnected"
        >
          执行拖拽
        </el-button>
      </el-form-item>
    </el-card>

    <!-- 文本输入面板 -->
    <el-card class="text-panel" shadow="hover">
      <template #header>
        <span>文本输入</span>
      </template>
      
      <el-form :model="textForm" label-width="80px" inline>
        <el-form-item label="文本内容">
          <el-input 
            v-model="textForm.content" 
            placeholder="输入要输入的文本"
            style="width: 300px"
            :disabled="!isConnected"
          />
        </el-form-item>
        <el-form-item label="目标元素">
          <el-input 
            v-model="textForm.elementPath" 
            placeholder="可选：指定目标元素路径"
            style="width: 300px"
            :disabled="!isConnected"
          />
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleInputText"
            :disabled="!isConnected"
          >
            输入文本
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作历史 -->
    <el-card class="history-panel" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>操作历史</span>
          <div>
            <el-tag type="info" size="small">
              成功率: {{ successRate }}%
            </el-tag>
            <el-button 
              type="text" 
              size="small" 
              @click="clearHistory"
              style="margin-left: 10px"
            >
              清空历史
            </el-button>
          </div>
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
            {{ new Date(row.timestamp).toLocaleString() }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useOperationStore } from '@/stores/operation'

const operationStore = useOperationStore()

// 响应式数据
const connecting = ref(false)

// 连接表单
const connectionForm = ref({
  host: 'localhost',
  port: 8888
})

// 元素操作表单
const elementForm = ref({
  path: '',
  roles: [] as string[]
})

// 图片操作表单
const imageForm = ref({
  path: '',
  threshold: 0.8
})

// 拖拽操作表单
const dragForm = ref({
  startX: 0,
  startY: 0,
  endX: 100,
  endY: 100
})

// 文本输入表单
const textForm = ref({
  content: '',
  elementPath: ''
})

// 计算属性
const isConnected = computed(() => operationStore.isConnected)
const recentOperations = computed(() => operationStore.recentOperations)
const successRate = computed(() => operationStore.successRate)

// 方法
const handleConnect = async () => {
  if (!connectionForm.value.host || !connectionForm.value.port) {
    ElMessage.warning('请输入主机地址和端口')
    return
  }

  connecting.value = true
  try {
    await operationStore.connect(connectionForm.value.host, connectionForm.value.port)
    ElMessage.success('连接成功')
  } catch (error) {
    ElMessage.error(`连接失败: ${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    connecting.value = false
  }
}

const handleDisconnect = async () => {
  try {
    await operationStore.disconnect()
    ElMessage.success('断开连接成功')
  } catch (error) {
    ElMessage.error(`断开连接失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleClickElement = async () => {
  if (!elementForm.value.path) {
    ElMessage.warning('请输入元素路径')
    return
  }

  try {
    await operationStore.clickElement(elementForm.value.path, elementForm.value.roles)
    ElMessage.success('点击元素成功')
  } catch (error) {
    ElMessage.error(`点击元素失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleRightClickElement = async () => {
  if (!elementForm.value.path) {
    ElMessage.warning('请输入元素路径')
    return
  }

  try {
    await operationStore.rightClickElement(elementForm.value.path, elementForm.value.roles)
    ElMessage.success('右键点击元素成功')
  } catch (error) {
    ElMessage.error(`右键点击元素失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleDoubleClickElement = async () => {
  if (!elementForm.value.path) {
    ElMessage.warning('请输入元素路径')
    return
  }

  try {
    await operationStore.doubleClickElement(elementForm.value.path, elementForm.value.roles)
    ElMessage.success('双击元素成功')
  } catch (error) {
    ElMessage.error(`双击元素失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleClickImage = async () => {
  if (!imageForm.value.path) {
    ElMessage.warning('请输入图片路径')
    return
  }

  try {
    await operationStore.clickImage(imageForm.value.path, imageForm.value.threshold)
    ElMessage.success('点击图片成功')
  } catch (error) {
    ElMessage.error(`点击图片失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleDragTo = async () => {
  try {
    await operationStore.dragTo(
      dragForm.value.startX,
      dragForm.value.startY,
      dragForm.value.endX,
      dragForm.value.endY
    )
    ElMessage.success('拖拽操作成功')
  } catch (error) {
    ElMessage.error(`拖拽操作失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const handleInputText = async () => {
  if (!textForm.value.content) {
    ElMessage.warning('请输入文本内容')
    return
  }

  try {
    await operationStore.inputText(textForm.value.content, textForm.value.elementPath)
    ElMessage.success('文本输入成功')
  } catch (error) {
    ElMessage.error(`文本输入失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

const clearHistory = () => {
  operationStore.clearHistory()
  ElMessage.success('操作历史已清空')
}
</script>

<style lang="scss" scoped>
.operation-page {
  .connection-panel {
    margin-bottom: 20px;
  }

  .operation-panels {
    margin-bottom: 20px;
  }

  .operation-panel {
    height: 100%;
  }

  .drag-panel,
  .text-panel,
  .history-panel {
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .el-form-item {
    margin-bottom: 15px;
  }

  .el-button-group {
    .el-button {
      margin-right: 0;
    }
  }
}
</style> 