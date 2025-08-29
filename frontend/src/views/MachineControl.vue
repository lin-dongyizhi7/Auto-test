<template>
  <div class="machine-control-page">
    <el-page-header @back="$router.back()" content="机器控制" />

    <el-card class="machine-card" shadow="hover">
      <template #header>
        <span>机器信息</span>
      </template>
      <div class="machine-info">
        <div><b>ID：</b>{{ machineId }}</div>
        <div><b>状态：</b><el-tag :type="'success'">connected</el-tag></div>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>应用列表</span>
          </template>
          <div v-if="apps.length === 0" class="empty-box">
            <el-empty description="暂无应用" />
          </div>
          <el-table v-else :data="apps" height="360">
            <el-table-column prop="name" label="应用名" />
            <el-table-column prop="id" label="ID" />
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button size="small" @click="selectApp(row)">选择</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>脚本运行</span>
          </template>
          <div v-if="!currentApp">
            <el-empty description="请先在左侧选择应用" />
          </div>
          <div v-else class="run-panel">
            <div class="target-line">
              当前目标：<el-tag type="info">{{ machineId }}</el-tag>
              <span style="margin: 0 6px">/</span>
              <el-tag type="success">{{ currentApp.name }}</el-tag>
            </div>
            <el-button type="primary" @click="applyTarget" :loading="applying">设置为当前目标</el-button>

            <el-divider />

            <el-select v-model="selectedScriptId" placeholder="选择脚本" style="width: 100%">
              <el-option v-for="s in scripts" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
            <el-button style="margin-top: 10px" type="success" @click="runSelectedScript" :disabled="!selectedScriptId" :loading="running">
              运行脚本
            </el-button>

            <el-divider />
            <el-input v-model="runOutput" type="textarea" :rows="12" readonly placeholder="运行输出..." />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getApps, setTarget, getScripts, runScript } from '@/api/operation'

const route = useRoute()
const machineId = route.params.id as string

const apps = ref<any[]>([])
const scripts = ref<any[]>([])
const currentApp = ref<any | null>(null)
const selectedScriptId = ref<string>('')
const applying = ref(false)
const running = ref(false)
const runOutput = ref('')

const loadApps = async () => {
  try {
    const res = await getApps(machineId)
    apps.value = res.data?.apps || []
  } catch (e) {
    apps.value = []
  }
}

const loadScripts = async () => {
  try {
    const res = await getScripts()
    scripts.value = res.data || []
  } catch (e) {
    scripts.value = []
  }
}

const selectApp = (app: any) => {
  currentApp.value = app
}

const applyTarget = async () => {
  if (!currentApp.value) return
  applying.value = true
  try {
    const res = await setTarget({ machine_id: machineId, app_name: currentApp.value.name })
    if (res.success) ElMessage.success('目标已设置')
    else ElMessage.error(res.message || '设置失败')
  } finally {
    applying.value = false
  }
}

const runSelectedScript = async () => {
  if (!selectedScriptId.value) return
  running.value = true
  runOutput.value = ''
  try {
    const res = await runScript(selectedScriptId.value)
    if (res.success) {
      runOutput.value = res.data?.output || ''
      ElMessage.success('脚本运行完成')
    } else {
      runOutput.value = res.data?.error || res.message || '运行失败'
      ElMessage.error('脚本运行失败')
    }
  } finally {
    running.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadApps(), loadScripts()])
})
</script>

<style scoped>
.machine-card { margin-bottom: 16px; }
.machine-info { display: flex; gap: 20px; }
.empty-box { padding: 20px; }
.run-panel { display: flex; flex-direction: column; gap: 10px; }
.target-line { margin-bottom: 6px; }
</style>
