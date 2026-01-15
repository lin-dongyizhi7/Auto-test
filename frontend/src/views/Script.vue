<template>
  <div class="script-page">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h2>脚本管理</h2>
      <div class="header-actions">
        <el-button v-if="activeTab === 'json'" @click="showImportDialog = true">
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
      
      <!-- 页签切换 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- JSON脚本页签 -->
        <el-tab-pane label="JSON脚本" name="json">
          <el-table
            v-loading="loading"
            :data="jsonScripts"
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
                <div v-if="row.target_app_name">
                  <span style="margin: 0 5px">/</span>
                  <el-tag size="small" type="success">{{ row.target_app_name }}</el-tag>
                </div>
                <span v-else style="color: #909399">未设置</span>
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
        </el-tab-pane>
        
        <!-- PY脚本页签 -->
        <el-tab-pane label="PY脚本" name="python">
          <div class="py-script-container">
            <!-- 上传区域 -->
            <div class="upload-section">
              <el-upload
                ref="pyUploadRef"
                class="py-upload-demo"
                drag
                :auto-upload="false"
                :on-change="handlePyFileChange"
                :before-upload="beforePyUpload"
                accept=".py"
                :limit="1"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  将Python脚本文件拖到此处，或<em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    只能上传 .py 文件，上传后可直接运行
                  </div>
                </template>
              </el-upload>
            </div>
            
            <!-- 当前脚本信息 -->
            <div class="current-script-info" v-if="currentPyScript">
              <el-card shadow="hover">
                <template #header>
                  <div class="script-header">
                    <span>当前脚本: {{ currentPyScript.name }}</span>
                    <div class="script-actions">
                      <el-button 
                        type="primary" 
                        :loading="runningPy"
                        @click="onRunCurrentPyScript"
                      >
                        <el-icon><VideoPlay /></el-icon>
                        运行脚本
                      </el-button>
                      <el-button 
                        type="success" 
                        :loading="convertingPy"
                        @click="onConvertPyScript"
                      >
                        <el-icon><Download /></el-icon>
                        转存为JSON
                      </el-button>
                      <el-button @click="clearCurrentPyScript">
                        <el-icon><Delete /></el-icon>
                        清除
                      </el-button>
                    </div>
                  </div>
                </template>
                <div class="script-details">
                  <p><strong>文件大小:</strong> {{ formatFileSize(currentPyScript.size) }}</p>
                  <p><strong>上传时间:</strong> {{ formatTime(currentPyScript.uploadTime) }}</p>
                </div>
              </el-card>
            </div>
            
            <!-- 使用说明 -->
            <div class="usage-guide" v-if="!currentPyScript">
              <el-card shadow="hover">
                <template #header>
                  <span>使用说明</span>
                </template>
                <div class="guide-content">
                  <h4>Python脚本编写规范：</h4>
                  <ol>
                    <li>导入OpRecord类：<code>from op_record import OpRecord</code></li>
                    <li>设置目标机器和应用：<code>OpRecord.setMachine("192.168.1.100", "calculator")</code></li>
                    <li>编写操作步骤：<code>OpRecord.click_element("按钮", ["push button"])</code></li>
                    <li>支持的操作：点击、输入、键盘、等待、图像识别等</li>
                  </ol>
                  <p><strong>注意：</strong>脚本中必须包含<code>OpRecord.setMachine()</code>调用，否则需要手动设置目标机器和应用。</p>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- 批量操作 -->
      <div class="batch-actions" v-if="activeTab === 'json' && selectedScripts.length > 0">
        <el-button size="small" @click="batchDelete">
          批量删除 ({{ selectedScripts.length }})
        </el-button>
      </div>
    </el-card>


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
        accept=".json"
        :limit="1"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 .json 脚本文件
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
          
          <el-descriptions-item label="运行次数">{{ currentScript.runCount }}</el-descriptions-item>
          <el-descriptions-item label="最后运行">
            {{ currentScript.lastRunTime ? formatTime(currentScript.lastRunTime) : '未运行' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(currentScript.createdAt) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(currentScript.updatedAt) }}</el-descriptions-item>
          
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

    <!-- 选择运行机器对话框 -->
    <el-dialog
      v-model="showRunDialog"
      title="选择运行机器"
      width="420px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="目标机器" required>
          <el-select v-model="runTargetMachineId" placeholder="请选择机器" style="width: 100%">
            <el-option 
              v-for="m in availableMachines"
              :key="m.machine_id"
              :label="Array.isArray(m.address) ? `${m.address[0]}:${m.address[1]}` : m.address"
              :value="m.machine_id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRunDialog = false">取消</el-button>
        <el-button type="primary" :loading="running" @click="confirmRunScript">运行</el-button>
      </template>
    </el-dialog>

    <!-- Python脚本目标设置对话框 -->
    <el-dialog
      v-model="showPyTargetDialog"
      title="设置Python脚本目标"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form ref="pyTargetFormRef" :model="pyTargetForm" :rules="pyTargetRules" label-width="120px">
        <el-form-item label="目标机器IP" prop="machineIp" required>
          <el-input v-model="pyTargetForm.machineIp" placeholder="请输入机器IP地址" />
        </el-form-item>
        <el-form-item label="目标应用" prop="appName" required>
          <el-select v-model="pyTargetForm.appName" placeholder="请选择应用" style="width: 100%">
            <el-option 
              v-for="app in availableApps" 
              :key="app.id"
              :label="app.name"
              :value="app.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="脚本内容预览">
          <el-input
            v-model="pyScriptPreview"
            type="textarea"
            :rows="8"
            readonly
            font-family="monospace"
            style="font-size: 12px;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPyTargetDialog = false">取消</el-button>
        <el-button type="primary" :loading="runningPy" @click="confirmRunPyScript">运行Python脚本</el-button>
      </template>
    </el-dialog>

    <!-- Python脚本转存对话框 -->
    <el-dialog
      v-model="showPyConvertDialog"
      title="转存为JSON脚本"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="pyConvertFormRef" :model="pyConvertForm" :rules="pyConvertRules" label-width="120px">
        <el-form-item label="脚本名称" prop="scriptName" required>
          <el-input v-model="pyConvertForm.scriptName" placeholder="请输入JSON脚本名称" />
        </el-form-item>
        <el-form-item label="脚本描述">
          <el-input v-model="pyConvertForm.description" type="textarea" placeholder="请输入脚本描述（可选）" />
        </el-form-item>
        <el-form-item label="目标机器IP">
          <el-input v-model="pyConvertForm.machineIp" placeholder="请输入机器IP地址（可选）" />
        </el-form-item>
        <el-form-item label="目标应用">
          <el-select v-model="pyConvertForm.appName" placeholder="请选择应用（可选）" style="width: 100%">
            <el-option 
              v-for="app in availableApps" 
              :key="app.id"
              :label="app.name"
              :value="app.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="转换预览">
          <el-input
            v-model="pyConvertPreview"
            type="textarea"
            :rows="10"
            readonly
            font-family="monospace"
            style="font-size: 12px;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPyConvertDialog = false">取消</el-button>
        <el-button type="primary" :loading="convertingPy" @click="confirmConvertPyScript">确认转存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Upload, Refresh, UploadFilled, VideoPlay, Edit, Download, Delete } from '@element-plus/icons-vue'
import { 
  getScripts as getScriptsApi, 
  getScript as getScriptApi, 
  createScript as createScriptApi, 
  updateScript as updateScriptApi, 
  deleteScript as deleteScriptApi, 
  runScript as runScriptApi, 
  importScript as importScriptApi, 
  exportScript as exportScriptApi,
  runPythonScript as runPythonScriptApi,
  validatePythonScript as validatePythonScriptApi,
  convertPythonScript as convertPythonScriptApi
} from '@/api/operation'
import type { ScriptInfo, UpdateScriptRequest, ScriptRunResult } from '@/api/types'
import { useOperationStore } from '@/stores/operation'

const operationStore = useOperationStore()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const scripts = ref<ScriptInfo[]>([])
const selectedScripts = ref<ScriptInfo[]>([])

// 页签相关
const activeTab = ref('json')
const jsonScripts = ref<ScriptInfo[]>([])
const currentPyScript = ref<any>(null)

// 对话框状态
 
const showEditDialog = ref(false)
const showImportDialog = ref(false)
const showViewDialog = ref(false)
const showRunDialog = ref(false)
const showPyTargetDialog = ref(false)
const showPyConvertDialog = ref(false)

// 计算属性
const availableMachines = computed(() => operationStore.machines)
const availableApps = computed(() => operationStore.apps)

// 表单数据
 

const editForm = reactive<UpdateScriptRequest>({
  name: '',
  
  target_app_name: '',
  description: '',
  content: ''
})

// Python脚本目标设置表单
const pyTargetForm = reactive({
  machineIp: '',
  appName: ''
})

// Python脚本转存表单
const pyConvertForm = reactive({
  scriptName: '',
  description: '',
  machineIp: '',
  appName: ''
})

// Python脚本预览
const pyScriptPreview = ref('')
const pyConvertPreview = ref('')

// 当前操作的脚本
const currentScript = ref<ScriptInfo | null>(null)
const runningScript = ref<ScriptInfo | null>(null)
const running = ref(false)
const runTargetMachineId = ref('')

// 加载状态
 
const updating = ref(false)
const importing = ref(false)
const runningPy = ref(false)
const convertingPy = ref(false)

// 表单引用
 
const editFormRef = ref<FormInstance>()
const pyTargetFormRef = ref<FormInstance>()
const pyConvertFormRef = ref<FormInstance>()
const uploadRef = ref()
const pyUploadRef = ref()

// 表单验证规则（保持不变）
 

const editRules: FormRules = {
  name: [
    { required: true, message: '请输入脚本名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  
  target_app_name: [
    { required: true, message: '请选择目标应用', trigger: 'change' }
  ],
  content: [
    { required: true, message: '请输入脚本内容', trigger: 'blur' }
  ]
}

// Python脚本目标设置验证规则
const pyTargetRules: FormRules = {
  machineIp: [
    { required: true, message: '请输入机器IP地址', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: '请输入有效的IP地址', trigger: 'blur' }
  ],
  appName: [
    { required: true, message: '请选择目标应用', trigger: 'change' }
  ]
}

// Python脚本转存验证规则
const pyConvertRules: FormRules = {
  scriptName: [
    { required: true, message: '请输入脚本名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  machineIp: [
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: '请输入有效的IP地址', trigger: 'blur' }
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
    // API返回的数据结构是 { scripts: ScriptInfo[] }
    const allScripts = response.data?.scripts || []
    scripts.value = allScripts
    
    // 只处理JSON脚本（假设所有脚本都是JSON类型）
    jsonScripts.value = allScripts
  } catch (error) {
    ElMessage.error('加载脚本列表失败')
    console.error('Load scripts error:', error)
    scripts.value = []
    jsonScripts.value = []
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

// 页签切换处理
const handleTabChange = (tabName: string | number) => {
  activeTab.value = String(tabName)
  if (tabName === 'json') {
    selectedScripts.value = []
  }
}

 

const formatTime = (time: string) => new Date(time).toLocaleString('zh-CN')

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

 

const resetEditForm = () => {
  editForm.name = ''
  editForm.description = ''
  editForm.content = ''
  
  editForm.target_app_name = ''
}

 

// 编辑脚本
const editScript = async (script: ScriptInfo) => {
  currentScript.value = script
  try {
    const resp = await getScriptApi(script.id)
    const data = resp.data as ScriptInfo
    editForm.name = data.name
    editForm.description = data.description || ''
    editForm.content = data.content
    editForm.target_app_name = data.target_app_name || ''
  } catch (e) {
    // 回退到传入的行数据
    editForm.name = script.name
    editForm.description = script.description || ''
    editForm.content = script.content
    editForm.target_app_name = script.target_app_name || ''
  }
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

// 运行脚本（选择机器 -> 调用API -> 跳转）
const onRunScript = (script: ScriptInfo) => {
  runningScript.value = script
  runTargetMachineId.value = ''
  showRunDialog.value = true
}

const confirmRunScript = async () => {
  if (!runningScript.value) return
  if (!runTargetMachineId.value) {
    ElMessage.warning('请选择要运行的目标机器')
    return
  }
  running.value = true
  try {
    const response = await runScriptApi(runningScript.value.id, runTargetMachineId.value)
    if (response.success) {
      ElMessage.success('已触发脚本运行')
      showRunDialog.value = false
      await loadScripts()
      // 跳转到操作控制页面并带上机器ID
      router.push({ name: 'Operation', query: { machine: runTargetMachineId.value } })
    } else {
      ElMessage.error(response.error || '运行脚本失败')
    }
  } catch (error) {
    ElMessage.error('运行脚本失败')
    console.error('Run script error:', error)
  } finally {
    running.value = false
  }
}

// 导入脚本（仅支持JSON）
const handleFileChange = (file: any) => {}

const beforeUpload = (file: File) => {
  const isJson = file.name.toLowerCase().endsWith('.json')
  if (!isJson) {
    ElMessage.error('只能上传 .json 文件')
    return false
  }
  return false
}

const onImportScript = async () => {
  if (activeTab.value !== 'json') return
  const uploadFiles = (uploadRef.value as any)?.uploadFiles
  if (!uploadFiles || uploadFiles.length === 0) {
    ElMessage.warning('请选择要导入的文件')
    return
  }
  importing.value = true
  try {
    const file: File = uploadFiles[0].raw
    const content = await readFileAsText(file)
    let parsed
    try {
      parsed = JSON.parse(content)
    } catch (e) {
      ElMessage.error('JSON 解析失败，请检查文件格式')
      return
    }
    // 生成脚本保存请求
    const name = (file.name || '导入脚本').replace(/\.json$/i, '')
    const payload = {
      name,
      description: `从文件导入: ${file.name}`,
      content: JSON.stringify(parsed, null, 2),
      target_app_name: parsed.target_app_name || ''
    }
    const resp = await createScriptApi(payload as any)
    if (resp.success) {
      ElMessage.success('脚本导入成功')
      showImportDialog.value = false
      ;(uploadRef.value as any)?.clearFiles()
      await loadScripts()
    } else {
      ElMessage.error(resp.error || '脚本导入失败')
    }
  } catch (error) {
    ElMessage.error('脚本导入失败')
    console.error('Import script error:', error)
  } finally {
    importing.value = false
  }
}

const readFileAsText = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = e => resolve((e.target?.result as string) || '')
    reader.onerror = reject
    reader.readAsText(file, 'utf-8')
  })
}

// 导出脚本
const onExportScript = async (script: ScriptInfo) => {
  try {
    const response = await exportScriptApi(script.id)
    const blob = new Blob([response.data || ''], { type: 'text/plain' })
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

// 查看脚本（获取详情以填充内容）
const viewScript = async (script: ScriptInfo) => {
  try {
    const resp = await getScriptApi(script.id)
    const data = resp.data as ScriptInfo
    currentScript.value = {
      ...script,
      content: data.content || script.content || ''
    }
  } catch (e) {
    currentScript.value = script
  }
  showViewDialog.value = true
}

const editCurrentScript = () => {
  if (currentScript.value) {
    showViewDialog.value = false
    editScript(currentScript.value)
  }
}

// ==================== PY脚本相关方法 ====================

// PY文件上传处理
const handlePyFileChange = (file: any) => {
  console.log('PY文件选择:', file)
  if (file.raw) {
    setCurrentPyScript(file.raw)
  }
}

const beforePyUpload = (file: File) => {
  const isPython = file.name.toLowerCase().endsWith('.py')
  if (!isPython) {
    ElMessage.error('只能上传 .py 文件')
    return false
  }
  return false
}

// 设置当前Python脚本
const setCurrentPyScript = (file: File) => {
  try {
    currentPyScript.value = {
      name: file.name,
      size: file.size,
      uploadTime: new Date().toISOString(),
      file: file
    }
    
    ElMessage.success('Python脚本加载成功，可以运行了')
    
    // 清空上传组件
    ;(pyUploadRef.value as any)?.clearFiles()
  } catch (error) {
    ElMessage.error('Python脚本加载失败')
    console.error('Set current PY script error:', error)
  }
}

// 清除当前Python脚本
const clearCurrentPyScript = () => {
  currentPyScript.value = null
  ElMessage.info('已清除当前脚本')
}

// 运行当前Python脚本
const onRunCurrentPyScript = async () => {
  if (!currentPyScript.value) {
    ElMessage.warning('请先上传Python脚本文件')
    return
  }
  
  try {
    // 读取Python脚本内容
    const scriptContent = await readPyScriptContent(currentPyScript.value)
    if (!scriptContent) {
      ElMessage.error('无法读取Python脚本内容')
      return
    }
    
    // 检查脚本中是否设置了目标机器和应用
    const hasTargetInfo = checkPyScriptTarget(scriptContent)
    
    if (hasTargetInfo) {
      // 脚本中已设置目标，直接运行
      await executePyScript(scriptContent)
    } else {
      // 脚本中未设置目标，显示设置对话框
      pyScriptPreview.value = scriptContent
      pyTargetForm.machineIp = ''
      pyTargetForm.appName = ''
      showPyTargetDialog.value = true
    }
    
  } catch (error) {
    ElMessage.error('运行Python脚本失败')
    console.error('Run PY script error:', error)
  }
}

// 读取Python脚本内容
const readPyScriptContent = async (script: any): Promise<string | null> => {
  try {
    if (script.file) {
      // 从上传的文件读取
      return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          resolve(e.target?.result as string || null)
        }
        reader.onerror = () => {
          resolve(null)
        }
        reader.readAsText(script.file)
      })
    } else {
      return null
    }
  } catch (error) {
    console.error('Read PY script content error:', error)
    return null
  }
}

// 检查Python脚本中是否设置了目标机器和应用
const checkPyScriptTarget = (scriptContent: string): boolean => {
  // 检查是否包含setMachine调用
  const setMachinePattern = /OpRecord\.setMachine\s*\(/i
  return setMachinePattern.test(scriptContent)
}

// 执行Python脚本
const executePyScript = async (scriptContent: string, machineIp?: string, appName?: string) => {
  try {
    runningPy.value = true
    ElMessage.info('正在解析并运行Python脚本...')
    
    // 调用后端API运行Python脚本
    const response = await runPythonScriptApi({
      script_content: scriptContent,
      target_machine_ip: machineIp,
      target_app_name: appName
    })
    
    if (response.success) {
      ElMessage.success('Python脚本运行完成')
      showPyTargetDialog.value = false
    } else {
      ElMessage.error(response.error || 'Python脚本运行失败')
    }
    
  } catch (error) {
    ElMessage.error('运行Python脚本失败')
    console.error('Execute PY script error:', error)
  } finally {
    runningPy.value = false
  }
}

// 确认运行Python脚本
const confirmRunPyScript = async () => {
  if (!pyTargetFormRef.value) return
  
  await pyTargetFormRef.value.validate(async (valid) => {
    if (valid) {
      await executePyScript(
        pyScriptPreview.value,
        pyTargetForm.machineIp,
        pyTargetForm.appName
      )
    }
  })
}

// 转存Python脚本为JSON
const onConvertPyScript = async () => {
  if (!currentPyScript.value) {
    ElMessage.warning('请先上传Python脚本文件')
    return
  }
  
  try {
    // 读取Python脚本内容
    const scriptContent = await readPyScriptContent(currentPyScript.value)
    if (!scriptContent) {
      ElMessage.error('无法读取Python脚本内容')
      return
    }
    
    // 生成默认脚本名称
    const defaultName = currentPyScript.value.name.replace('.py', '') + '_converted'
    
    // 设置表单默认值
    pyConvertForm.scriptName = defaultName
    pyConvertForm.description = `从Python脚本转换: ${currentPyScript.value.name}`
    pyConvertForm.machineIp = ''
    pyConvertForm.appName = ''
    
    // 生成转换预览
    await generateConvertPreview(scriptContent)
    
    // 显示转存对话框
    showPyConvertDialog.value = true
    
  } catch (error) {
    ElMessage.error('准备转存失败')
    console.error('Prepare convert error:', error)
  }
}

// 生成转换预览
const generateConvertPreview = async (scriptContent: string) => {
  try {
    // 调用后端API生成预览（这里简化处理，直接显示脚本内容）
    pyConvertPreview.value = `# Python脚本内容预览:\n${scriptContent}\n\n# 将转换为JSON格式的脚本步骤`
  } catch (error) {
    console.error('Generate preview error:', error)
    pyConvertPreview.value = '预览生成失败'
  }
}

// 确认转存Python脚本
const confirmConvertPyScript = async () => {
  if (!pyConvertFormRef.value || !currentPyScript.value) return
  
  await pyConvertFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        convertingPy.value = true
        
        // 读取Python脚本内容
        const scriptContent = await readPyScriptContent(currentPyScript.value)
        if (!scriptContent) {
          ElMessage.error('无法读取Python脚本内容')
          return
        }
        
        // 调用后端API转换脚本
        const response = await convertPythonScriptApi({
          script_content: scriptContent,
          script_name: pyConvertForm.scriptName,
          description: pyConvertForm.description,
          target_machine_ip: pyConvertForm.machineIp || undefined,
          target_app_name: pyConvertForm.appName || undefined
        })
        
        if (response.success) {
          ElMessage.success('Python脚本已成功转换为JSON脚本')
          showPyConvertDialog.value = false
          // 刷新脚本列表
          await loadScripts()
          // 切换到JSON脚本页签
          activeTab.value = 'json'
        } else {
          ElMessage.error(response.error || '转换失败')
        }
        
      } catch (error) {
        ElMessage.error('转换Python脚本失败')
        console.error('Convert PY script error:', error)
      } finally {
        convertingPy.value = false
      }
    }
  })
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
  
  // PY脚本页签样式
  .py-script-container {
    .upload-section {
      margin-bottom: 20px;
      
      .py-upload-demo {
        width: 100%;
      }
    }
    
    .current-script-info {
      margin-top: 20px;
      
      .script-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .script-actions {
          display: flex;
          gap: 10px;
        }
      }
      
      .script-details {
        p {
          margin: 8px 0;
          color: #606266;
        }
      }
    }
    
    .usage-guide {
      margin-top: 20px;
      
      .guide-content {
        h4 {
          margin: 0 0 10px 0;
          color: #303133;
        }
        
        ol {
          margin: 10px 0;
          padding-left: 20px;
          
          li {
            margin: 8px 0;
            line-height: 1.6;
            
            code {
              background-color: #f5f7fa;
              padding: 2px 6px;
              border-radius: 3px;
              font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
              font-size: 13px;
              color: #e6a23c;
            }
          }
        }
        
        p {
          margin: 10px 0;
          color: #606266;
          line-height: 1.6;
          
          strong {
            color: #e6a23c;
          }
        }
      }
    }
  }
}
</style> 