import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  TestServerConnection,
  ConnectionStatus,
  MachineInfo,
  AppInfo,
  MachineAppTarget,
  CurrentTarget,
  ElementOperation,
  ImageOperation,
  DragOperation,
  TextInput,
  HotkeyOperation,
  ScreenshotRequest,
  ScreenshotData
} from '@/api/types'
import {
  startServer,
  stopServer,
  getServerStatus,
  getMachines,
  getApps,
  setTarget,
  getCurrentTarget,
  getScreenshot,
  clickElement,
  rightClickElement,
  doubleClickElement,
  setElementText,
  moveToElement,
  dragTo,
  findImage,
  clickImage,
  sendHotkey,
  typeText,
  waitForElement,
  waitForImage,
  getEvents,
  connectToMachine,
  disconnectMachine
} from '@/api/operation'

export const useOperationStore = defineStore('operation', () => {
  // 连接状态
  const isConnected = ref(false)
  const connectionConfig = ref<TestServerConnection>({
    host: 'localhost',
            port: 8888
  })
  const connecting = ref(false)

  // 多机器多应用状态
  const machines = ref<MachineInfo[]>([])
  const apps = ref<AppInfo[]>([])
  const currentTarget = ref<CurrentTarget | null>(null)
  const loadingMachines = ref(false)
  const loadingApps = ref(false)

  // 操作状态
  const operationLogs = ref<string[]>([])
  const currentScreenshot = ref<ScreenshotData | null>(null)

  // 计算属性
  const availableMachines = computed(() => machines.value)
  const availableApps = computed(() => apps.value)
  const currentMachineId = computed(() => currentTarget.value?.machine_id)
  const currentAppName = computed(() => currentTarget.value?.app_name)
  const isTargetSet = computed(() => !!currentTarget.value)

  // 服务器管理
  const startTestServer = async (port = 8888) => {
    try {
      connecting.value = true
      const response = await startServer({ host: 'localhost', port })
      
      if (response.success) {
        isConnected.value = true
        connectionConfig.value = { host: 'localhost', port }
        addLog('服务器启动成功', 'success')
        await refreshMachines()
        return true
      } else {
        addLog(`服务器启动失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`服务器启动异常: ${error}`, 'error')
      return false
    } finally {
      connecting.value = false
    }
  }

  const stopTestServer = async () => {
    try {
      const response = await stopServer()
      if (response.success) {
        isConnected.value = false
        currentTarget.value = null
        machines.value = []
        apps.value = []
        addLog('服务器已停止', 'info')
        return true
      } else {
        addLog(`服务器停止失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`服务器停止异常: ${error}`, 'error')
      return false
    }
  }

  const refreshServerStatus = async () => {
    try {
      const response = await getServerStatus()
      if (response.success && response.data) {
        isConnected.value = response.data.is_running || false
        if (response.data.current_machine_id && response.data.current_app_name) {
          currentTarget.value = {
            machine_id: response.data.current_machine_id,
            app_name: response.data.current_app_name
          }
        }
      }
    } catch (error) {
      console.error('获取服务器状态失败:', error)
    }
  }

  // 多机器多应用管理
  const refreshMachines = async () => {
    if (!isConnected.value) return
    
    try {
      loadingMachines.value = true
      const response = await getMachines()
      if (response.success && response.data) {
        // 转换数据格式以适配新的API结构
        machines.value = Object.entries(response.data.machines).map(([id, machine]: [string, any]) => ({
          machine_id: id,
          status: machine.status,
          address: machine.address,
          info: machine.info,
          connected_at: machine.connected_at,
          last_seen: machine.last_seen,
          apps_count: machine.apps_count,
          apps: machine.apps
        }))
        addLog(`发现 ${machines.value.length} 台机器`, 'info')
      }
    } catch (error) {
      addLog(`获取机器列表失败: ${error}`, 'error')
    } finally {
      loadingMachines.value = false
    }
  }

  const refreshApps = async (machineId?: string) => {
    if (!isConnected.value) return
    
    try {
      loadingApps.value = true
      const response = await getApps(machineId)
      if (response.success && response.data) {
        // 转换数据格式以适配新的API结构
        apps.value = Object.entries(response.data.apps).map(([id, app]: [string, any]) => ({
          app_id: id,
          machine_id: app.machine_id,
          app_name: app.app_name,
          status: app.status,
          info: app.info,
          registered_at: app.registered_at,
          machine_status: app.machine_status,
          machine_address: app.machine_address
        }))
        addLog(`发现 ${apps.value.length} 个应用`, 'info')
      }
    } catch (error) {
      addLog(`获取应用列表失败: ${error}`, 'error')
    } finally {
      loadingApps.value = false
    }
  }

  const setCurrentTarget = async (target: MachineAppTarget) => {
    try {
      const response = await setTarget(target)
      if (response.success) {
        currentTarget.value = target
        addLog(`设置目标: 机器 ${target.machine_id}, 应用 ${target.app_name}`, 'success')
        return true
      } else {
        addLog(`设置目标失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`设置目标异常: ${error}`, 'error')
      return false
    }
  }

  const refreshCurrentTarget = async () => {
    try {
      const response = await getCurrentTarget()
      if (response.success && response.data) {
        currentTarget.value = response.data
      }
    } catch (error) {
      console.error('获取当前目标失败:', error)
    }
  }

  // 截图管理
  const takeScreenshot = async (region?: string) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return null
    }

    try {
      const response = await getScreenshot({ region })
      if (response.success && response.data) {
        currentScreenshot.value = response.data
        addLog('截图成功', 'success')
        return response.data
      } else {
        addLog(`截图失败: ${response.error}`, 'error')
        return null
      }
    } catch (error) {
      addLog(`截图异常: ${error}`, 'error')
      return null
    }
  }

  // 元素操作
  const performClickElement = async (operation: ElementOperation) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await clickElement(operation)
      if (response.success) {
        addLog(`点击元素成功: ${operation.path}`, 'success')
        return true
      } else {
        addLog(`点击元素失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`点击元素异常: ${error}`, 'error')
      return false
    }
  }

  const performClickImage = async (operation: ImageOperation) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await clickImage(operation)
      if (response.success) {
        addLog(`点击图片成功: ${operation.imagePath}`, 'success')
        return true
      } else {
        addLog(`点击图片失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`点击图片异常: ${error}`, 'error')
      return false
    }
  }

  const performDragTo = async (operation: DragOperation) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await dragTo(operation)
      if (response.success) {
        addLog(`拖拽操作成功: (${operation.startX}, ${operation.startY}) -> (${operation.endX}, ${operation.endY})`, 'success')
        return true
      } else {
        addLog(`拖拽操作失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`拖拽操作异常: ${error}`, 'error')
      return false
    }
  }

  const performInputText = async (operation: TextInput) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await typeText(operation)
      if (response.success) {
        addLog(`文本输入成功: ${operation.text}`, 'success')
        return true
      } else {
        addLog(`文本输入失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`文本输入异常: ${error}`, 'error')
      return false
    }
  }

  const performHotkey = async (operation: HotkeyOperation) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await sendHotkey(operation)
      if (response.success) {
        addLog(`快捷键操作成功: ${operation.keys.join('+')}`, 'success')
        return true
      } else {
        addLog(`快捷键操作失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`快捷键操作异常: ${error}`, 'error')
      return false
    }
  }

  const performTypeText = async (operation: TextInput) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await typeText(operation)
      if (response.success) {
        addLog(`文本输入成功: ${operation.text}`, 'success')
        return true
      } else {
        addLog(`文本输入失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`文本输入异常: ${error}`, 'error')
      return false
    }
  }

  const performSetElementText = async (operation: TextInput) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await setElementText(operation)
      if (response.success) {
        addLog(`设置元素文本成功: ${operation.text}`, 'success')
        return true
      } else {
        addLog(`设置元素文本失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`设置元素文本异常: ${error}`, 'error')
      return false
    }
  }

  const performRightClickElement = async (operation: ElementOperation) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await rightClickElement(operation)
      if (response.success) {
        addLog(`右键点击元素成功: ${operation.path}`, 'success')
        return true
      } else {
        addLog(`右键点击元素失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`右键点击元素异常: ${error}`, 'error')
      return false
    }
  }

  const performDoubleClickElement = async (operation: ElementOperation) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await doubleClickElement(operation)
      if (response.success) {
        addLog(`双击元素成功: ${operation.path}`, 'success')
        return true
      } else {
        addLog(`双击元素失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`双击元素异常: ${error}`, 'error')
      return false
    }
  }

  const performMoveToElement = async (operation: ElementOperation) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await moveToElement(operation)
      if (response.success) {
        addLog(`移动到元素成功: ${operation.path}`, 'success')
        return true
      } else {
        addLog(`移动到元素失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`移动到元素异常: ${error}`, 'error')
      return false
    }
  }

  const performWaitForElement = async (operation: ElementOperation) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await waitForElement(operation)
      if (response.success) {
        addLog(`等待元素成功: ${operation.path}`, 'success')
        return true
      } else {
        addLog(`等待元素失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`等待元素异常: ${error}`, 'error')
      return false
    }
  }

  const performWaitForImage = async (operation: ImageOperation) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return false
    }

    try {
      const response = await waitForImage(operation)
      if (response.success) {
        addLog(`等待图片成功: ${operation.imagePath}`, 'success')
        return true
      } else {
        addLog(`等待图片失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`等待图片异常: ${error}`, 'error')
      return false
    }
  }

  const performFindImage = async (operation: ImageOperation) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return null
    }

    try {
      const response = await findImage(operation)
      if (response.success && response.data) {
        addLog(`查找图片成功: ${operation.imagePath}`, 'success')
        return response.data
      } else {
        addLog(`查找图片失败: ${response.error}`, 'error')
        return null
      }
    } catch (error) {
      addLog(`查找图片异常: ${error}`, 'error')
      return null
    }
  }

  // 日志管理
  const addLog = (message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
    const timestamp = new Date().toLocaleTimeString()
    const logEntry = `[${timestamp}] ${message}`
    operationLogs.value.push(logEntry)
    
    // 限制日志数量
    if (operationLogs.value.length > 100) {
      operationLogs.value = operationLogs.value.slice(-100)
    }
  }

  const clearLogs = () => {
    operationLogs.value = []
  }

  // 事件管理
  const getEventHistory = async (limit?: number, eventType?: string) => {
    try {
      const response = await getEvents(limit, eventType)
      if (response.success && response.data) {
        return response.data.events
      }
      return []
    } catch (error) {
      addLog(`获取事件历史失败: ${error}`, 'error')
      return []
    }
  }

  // 机器连接管理
  const connectToTargetMachine = async (host: string, port: number) => {
    try {
      const response = await connectToMachine(host, port)
      if (response.success) {
        addLog(`成功连接到目标机器 ${host}:${port}`, 'success')
        // 连接成功后刷新机器列表
        await refreshMachines()
        return true
      } else {
        addLog(`连接目标机器失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`连接目标机器异常: ${error}`, 'error')
      return false
    }
  }

  const disconnectTargetMachine = async (machineId: string) => {
    try {
      const response = await disconnectMachine(machineId)
      if (response.success) {
        addLog(`成功断开与机器 ${machineId} 的连接`, 'success')
        // 断开连接后刷新机器列表
        await refreshMachines()
        return true
      } else {
        addLog(`断开目标机器连接失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`断开目标机器连接异常: ${error}`, 'error')
      return false
    }
  }

  // 初始化
  const initialize = async () => {
    await refreshServerStatus()
    if (isConnected.value) {
      await refreshMachines()
      await refreshCurrentTarget()
    }
    // 后端默认启动测试服务器，无需前端启动
  }

  return {
    // 状态
    isConnected,
    connectionConfig,
    connecting,
    machines,
    apps,
    currentTarget,
    loadingMachines,
    loadingApps,
    operationLogs,
    currentScreenshot,

    // 计算属性
    availableMachines,
    availableApps,
    currentMachineId,
    currentAppName,
    isTargetSet,

    // 服务器管理
    startTestServer,
    stopTestServer,
    refreshServerStatus,

    // 多机器多应用管理
    refreshMachines,
    refreshApps,
    setCurrentTarget,
    refreshCurrentTarget,

    // 截图管理
    takeScreenshot,

    // 元素操作
    performClickElement,
    performRightClickElement,
    performDoubleClickElement,
    performSetElementText,
    performMoveToElement,
    performClickImage,
    performDragTo,
    performInputText,
    performTypeText,
    performHotkey,
    performFindImage,
    performWaitForElement,
    performWaitForImage,

    // 事件管理
    getEventHistory,

    // 机器连接管理
    connectToTargetMachine,
    disconnectTargetMachine,

    // 日志管理
    addLog,
    clearLogs,

    // 初始化
    initialize
  }
}) 