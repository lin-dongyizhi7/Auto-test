<template>
  <div class="script-page">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h2>脚本管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建脚本
        </el-button>
        <el-button @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>
          导入脚本
        </el-button>
        <el-button @click="refreshScripts">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 脚本列表 -->
    <el-card class="script-list-card" shadow="hover">
      <template #header>
        <span>脚本列表</span>
      </template>
      
      <el-table
        v-loading="loading"
        :data="scripts"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="脚本名称" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="viewScript(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="目标" width="200">
          <template #default="{ row }">
            <div v-if="row.target_machine_id && row.target_app_name">
              <el-tag size="small" type="info">{{ row.target_machine_id }}</el-tag>
              <span style="margin: 0 5px">/</span>
              <el-tag size="small" type="success">{{ row.target_app_name }}</el-tag>
            </div>
            <span v-else style="color: #909399">未设置</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="runCount" label="运行次数" width="100" />
        <el-table-column prop="lastRunTime" label="最后运行" width="180">
          <template #default="{ row }">
            {{ row.lastRunTime ? formatTime(row.lastRunTime) : '未运行' }}
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.updatedAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-tooltip content="运行脚本" placement="top">
                <el-button 
                  type="primary" 
                  size="small" 
                  circle
                  @click="onRunScript(row)" 
                  :loading="row.status === 'running'"
                >
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="编辑脚本" placement="top">
                <el-button 
                  type="warning" 
                  size="small" 
                  circle
                  @click="editScript(row)"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="导出脚本" placement="top">
                <el-button 
                  type="success" 
                  size="small" 
                  circle
                  @click="onExportScript(row)"
                >
                  <el-icon><Download /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="删除脚本" placement="top">
                <el-button 
                  type="danger" 
                  size="small" 
                  circle
                  @click="onDeleteScript(row)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 批量操作 -->
      <div class="batch-actions" v-if="selectedScripts.length > 0">
        <el-button size="small" @click="batchDelete">
          批量删除 ({{ selectedScripts.length }})
        </el-button>
      </div>
    </el-card>

    <!-- 新建脚本对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建脚本"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="脚本名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" placeholder="请输入脚本描述" />
        </el-form-item>
        <el-form-item label="目标机器">
          <el-select v-model="createForm.target_machine_id" placeholder="选择目标机器" style="width: 100%">
            <el-option 
              v-for="machine in availableMachines" 
              :key="machine.id"
              :label="machine.address"
              :value="machine.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="目标应用">
          <el-select v-model="createForm.target_app_name" placeholder="选择目标应用" style="width: 100%">
            <el-option 
              v-for="app in availableApps" 
              :key="app.id"
              :label="app.name"
              :value="app.name"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="脚本内容" prop="content">
          <el-input
            v-model="createForm.content"
            type="textarea"
            :rows="15"
            placeholder="请输入Python脚本内容"
            font-family="monospace"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="onCreateScript" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑脚本对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑脚本"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="脚本名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" placeholder="请输入脚本描述" />
        </el-form-item>
        <el-form-item label="目标机器">
          <el-select v-model="editForm.target_machine_id" placeholder="选择目标机器" style="width: 100%">
            <el-option 
              v-for="machine in availableMachines" 
              :key="machine.id"
              :label="machine.address"
              :value="machine.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="目标应用">
          <el-select v-model="editForm.target_app_name" placeholder="选择目标应用" style="width: 100%">
            <el-option 
              v-for="app in availableApps" 
              :key="app.id"
              :label="app.name"
              :value="app.name"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="脚本内容" prop="content">
          <el-input
            v-model="editForm.content"
            type="textarea"
            :rows="15"
            placeholder="请输入Python脚本内容"
            font-family="monospace"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="onUpdateScript" :loading="updating">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 导入脚本对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入脚本"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :before-upload="beforeUpload"
        accept=".py"
        :limit="1"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 .py 文件
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="onImportScript" :loading="importing">
          导入
        </el-button>
      </template>
    </el-dialog>

    <!-- 脚本详情对话框 -->
    <el-dialog
      v-model="showViewDialog"
      title="脚本详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="currentScript">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="脚本名称">{{ currentScript.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentScript.status)">
              {{ getStatusText(currentScript.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="运行次数">{{ currentScript.runCount }}</el-descriptions-item>
          <el-descriptions-item label="最后运行">
            {{ currentScript.lastRunTime ? formatTime(currentScript.lastRunTime) : '未运行' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(currentScript.createdAt) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(currentScript.updatedAt) }}</el-descriptions-item>
          <el-descriptions-item label="目标机器">{{ currentScript.target_machine_id || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="目标应用">{{ currentScript.target_app_name || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentScript.description || '无' }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="script-content-view">
          <h4>脚本内容</h4>
                   <el-input
           :model-value="currentScript.content"
           type="textarea"
           :rows="15"
           readonly
           font-family="monospace"
         />
        </div>
      </div>
      <template #footer>
        <el-button @click="showViewDialog = false">关闭</el-button>
        <el-button type="primary" @click="editCurrentScript">编辑</el-button>
      </template>
    </el-dialog>

    <!-- 运行结果对话框 -->
    <el-dialog
      v-model="showResultDialog"
      title="运行结果"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="runResult">
        <el-alert
          :title="runResult.success ? '运行成功' : '运行失败'"
          :type="runResult.success ? 'success' : 'error'"
          :closable="false"
          show-icon
        />
        
                 <div class="result-content">
           <h4>输出信息</h4>
           <el-input
             :model-value="runResult.output || '无输出'"
             type="textarea"
             :rows="8"
             readonly
             font-family="monospace"
           />
           
           <h4 v-if="runResult.error">错误信息</h4>
           <el-input
             v-if="runResult.error"
             :model-value="runResult.error"
             type="textarea"
             :rows="6"
             readonly
             font-family="monospace"
             class="error-output"
           />
          
          <div v-if="runResult.executionTime" class="execution-time">
            执行时间: {{ runResult.executionTime }}ms
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showResultDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Upload, Refresh, UploadFilled, VideoPlay, Edit, Download, Delete } from '@element-plus/icons-vue'
import { 
  getScripts as getScriptsApi, 
  getScript as getScriptApi, 
  createScript as createScriptApi, 
  updateScript as updateScriptApi, 
  deleteScript as deleteScriptApi, 
  runScript as runScriptApi, 
  importScript as importScriptApi, 
  exportScript as exportScriptApi 
} from '@/api/operation'
import type { ScriptInfo, CreateScriptRequest, UpdateScriptRequest, ScriptRunResult } from '@/api/types'
import { useOperationStore } from '@/stores/operation'

const operationStore = useOperationStore()

// 响应式数据
const loading = ref(false)
const scripts = ref<ScriptInfo[]>([])
const selectedScripts = ref<ScriptInfo[]>([])

// 对话框状态
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showImportDialog = ref(false)
const showViewDialog = ref(false)
const showResultDialog = ref(false)

// 计算属性
const availableMachines = computed(() => operationStore.machines)
const availableApps = computed(() => operationStore.apps)

// 表单数据
const createForm = reactive<CreateScriptRequest>({
  name: '',
  description: '',
  content: '',
  target_machine_id: '',
  target_app_name: ''
})

const editForm = reactive<UpdateScriptRequest>({
  name: '',
  target_machine_id: '',
  target_app_name: '',
  description: '',
  content: ''
})

// 当前操作的脚本
const currentScript = ref<ScriptInfo | null>(null)
const runResult = ref<ScriptRunResult | null>(null)

// 加载状态
const creating = ref(false)
const updating = ref(false)
const importing = ref(false)

// 表单引用
const createFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()
const uploadRef = ref()

// 表单验证规则（保持不变）
const createRules: FormRules = {
  name: [
    { required: true, message: '请输入脚本名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  target_machine_id: [
    { required: true, message: '请选择目标机器', trigger: 'change' }
  ],
  target_app_name: [
    { required: true, message: '请选择目标应用', trigger: 'change' }
  ],
  content: [
    { required: true, message: '请输入脚本内容', trigger: 'blur' }
  ]
}

const editRules: FormRules = {
  name: [
    { required: true, message: '请输入脚本名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  target_machine_id: [
    { required: true, message: '请选择目标机器', trigger: 'change' }
  ],
  target_app_name: [
    { required: true, message: '请选择目标应用', trigger: 'change' }
  ],
  content: [
    { required: true, message: '请输入脚本内容', trigger: 'blur' }
  ]
}

// 生命周期
onMounted(async () => {
  await operationStore.initialize()
  loadScripts()
})

// 方法
const loadScripts = async () => {
  loading.value = true
  try {
    const response = await getScriptsApi()
    // response.data 为 ApiResponse，真正的数据在 response.data.data
    scripts.value = (response.data && (response.data as any).data) || []
  } catch (error) {
    ElMessage.error('加载脚本列表失败')
    console.error('Load scripts error:', error)
    scripts.value = []
  } finally {
    loading.value = false
  }
}

const refreshScripts = () => {
  loadScripts()
}

const handleSelectionChange = (selection: ScriptInfo[]) => {
  selectedScripts.value = selection
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    idle: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    idle: '空闲',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || '未知'
}

const formatTime = (time: string) => new Date(time).toLocaleString('zh-CN')

const resetCreateForm = () => {
  createForm.name = ''
  createForm.description = ''
  createForm.content = ''
  createForm.target_machine_id = ''
  createForm.target_app_name = ''
}

const resetEditForm = () => {
  editForm.name = ''
  editForm.description = ''
  editForm.content = ''
  editForm.target_machine_id = ''
  editForm.target_app_name = ''
}

// 创建脚本（调用 API）
const onCreateScript = async () => {
  if (!createFormRef.value) return
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      creating.value = true
      try {
        await createScriptApi(createForm)
        ElMessage.success('脚本创建成功')
        showCreateDialog.value = false
        resetCreateForm()
        loadScripts()
      } catch (error) {
        ElMessage.error('脚本创建失败')
        console.error('Create script error:', error)
      } finally {
        creating.value = false
      }
    }
  })
}

// 编辑脚本
const editScript = (script: ScriptInfo) => {
  currentScript.value = script
  editForm.name = script.name
  editForm.description = script.description || ''
  editForm.content = script.content
  editForm.target_machine_id = script.target_machine_id || ''
  editForm.target_app_name = script.target_app_name || ''
  showEditDialog.value = true
}

const onUpdateScript = async () => {
  if (!editFormRef.value || !currentScript.value) return
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      updating.value = true
      try {
        await updateScriptApi(currentScript.value!.id, editForm)
        ElMessage.success('脚本更新成功')
        showEditDialog.value = false
        resetEditForm()
        loadScripts()
      } catch (error) {
        ElMessage.error('脚本更新失败')
        console.error('Update script error:', error)
      } finally {
        updating.value = false
      }
    }
  })
}

// 删除脚本
const onDeleteScript = async (script: ScriptInfo) => {
  try {
    await ElMessageBox.confirm(`确定要删除脚本 "${script.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteScriptApi(script.id)
    ElMessage.success('脚本删除成功')
    loadScripts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('脚本删除失败')
      console.error('Delete script error:', error)
    }
  }
}

const batchDelete = async () => {
  if (selectedScripts.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedScripts.value.length} 个脚本吗？`, '确认批量删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    for (const s of selectedScripts.value) {
      await deleteScriptApi(s.id)
    }
    ElMessage.success('批量删除成功')
    selectedScripts.value = []
    loadScripts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
      console.error('Batch delete error:', error)
    }
  }
}

// 运行脚本
const onRunScript = async (script: ScriptInfo) => {
  try {
    const response = await runScriptApi(script.id)
    // response.data 为 ApiResponse，运行结果在 data
    runResult.value = (response.data && (response.data as any).data) || null
    showResultDialog.value = true
    loadScripts()
  } catch (error) {
    ElMessage.error('脚本运行失败')
    console.error('Run script error:', error)
  }
}

// 导入脚本
const handleFileChange = (file: any) => {}

const beforeUpload = (file: File) => {
  const isPython = file.name.indexOf('.py') !== -1
  if (!isPython) {
    ElMessage.error('只能上传 .py 文件')
    return false
  }
  return false
}

const onImportScript = async () => {
  const uploadFiles = (uploadRef.value as any)?.uploadFiles
  if (!uploadFiles || uploadFiles.length === 0) {
    ElMessage.warning('请选择要导入的文件')
    return
  }
  importing.value = true
  try {
    await importScriptApi(uploadFiles[0].raw)
    ElMessage.success('脚本导入成功')
    showImportDialog.value = false
    ;(uploadRef.value as any)?.clearFiles()
    loadScripts()
  } catch (error) {
    ElMessage.error('脚本导入失败')
    console.error('Import script error:', error)
  } finally {
    importing.value = false
  }
}

// 导出脚本
const onExportScript = async (script: ScriptInfo) => {
  try {
    const response = await exportScriptApi(script.id)
    const blob = new Blob([response.data], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${script.name}.py`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('脚本导出成功')
  } catch (error) {
    ElMessage.error('脚本导出失败')
    console.error('Export script error:', error)
  }
}

// 查看脚本
const viewScript = (script: ScriptInfo) => {
  currentScript.value = script
  showViewDialog.value = true
}

const editCurrentScript = () => {
  if (currentScript.value) {
    showViewDialog.value = false
    editScript(currentScript.value)
  }
}
</script>

<style lang="less" scoped>
.script-page {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      margin: 0;
      color: #303133;
    }
    
    .header-actions {
      display: flex;
      gap: 10px;
    }
  }
  
  .script-list-card {
    margin-bottom: 20px;
    
    .batch-actions {
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid #ebeef5;
    }
  }
  
  .script-content-view {
    margin-top: 20px;
    
    h4 {
      margin-bottom: 10px;
      color: #606266;
    }
  }
  
  .result-content {
    margin-top: 20px;
    
    h4 {
      margin: 15px 0 10px 0;
      color: #606266;
    }
    
    .error-output {
      :deep(.el-textarea__inner) {
        color: #f56c6c;
        background-color: #fef0f0;
      }
    }
    
    .execution-time {
      margin-top: 10px;
      color: #909399;
      font-size: 14px;
    }
  }
  
  .upload-demo {
    width: 100%;
  }
  
  .action-buttons {
    display: flex;
    gap: 8px;
    justify-content: center;
    
    .el-button {
      margin: 0;
    }
  }
  
  :deep(.el-textarea__inner) {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 13px;
    line-height: 1.5;
  }
}
</style> 