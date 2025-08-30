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
  connectToTestServer,
  disconnectFromTestServer,
  getConnectionStatus,
  getMachines,
  getApps,
  setTarget,
  getCurrentTarget,
  getScreenshot,
  clickElement,
  clickImage,
  dragTo,
  inputText,
  hotkey,
  getElementInfo,
  findImage
} from '@/api/operation'

export const useOperationStore = defineStore('operation', () => {
  // 连接状态
  const isConnected = ref(false)
  const connectionConfig = ref<TestServerConnection>({
    host: 'localhost',
    port: 8889
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

  // 连接管理
  const startServer = async (port = 8889) => {
    // 服务端模式：调用后端 /connect 启动内置测试服务器
    return await connect({ host: 'server', port })
  }

  const stopServer = async () => {
    return await disconnect()
  }

  const connect = async (config: TestServerConnection) => {
    try {
      connecting.value = true
      const response = await connectToTestServer(config)
      console.log(response);
      
      if (response.success) {
        isConnected.value = true
        connectionConfig.value = config
        addLog('连接成功', 'success')
        await refreshMachines()
        return true
      } else {
        addLog(`连接失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`连接异常: ${error}`, 'error')
      return false
    } finally {
      connecting.value = false
    }
  }

  const disconnect = async () => {
    try {
      const response = await disconnectFromTestServer()
      if (response.success) {
        isConnected.value = false
        currentTarget.value = null
        machines.value = []
        apps.value = []
        addLog('已断开连接', 'info')
        return true
      } else {
        addLog(`断开连接失败: ${response.error}`, 'error')
        return false
      }
    } catch (error) {
      addLog(`断开连接异常: ${error}`, 'error')
      return false
    }
  }

  const refreshConnectionStatus = async () => {
    try {
      const response = await getConnectionStatus()
      if (response.success) {
        isConnected.value = response.data?.connected || false
        if (response.data?.host && response.data?.port) {
          connectionConfig.value = {
            host: response.data.host,
            port: response.data.port
          }
        }
      }
    } catch (error) {
      console.error('获取连接状态失败:', error)
    }
  }

  // 多机器多应用管理
  const refreshMachines = async () => {
    if (!isConnected.value) return
    
    try {
      loadingMachines.value = true
      const response = await getMachines()
      if (response.success && response.data) {
        machines.value = response.data.machines
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
        apps.value = response.data.apps
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
      const response = await inputText(operation)
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
      const response = await hotkey(operation)
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

  const getElementLocation = async (path: string, roles?: string) => {
    if (!isTargetSet.value) {
      addLog('请先设置目标机器和应用', 'warning')
      return null
    }

    try {
      const response = await getElementInfo(path, roles)
      if (response.success && response.data) {
        addLog(`获取元素信息成功: ${path}`, 'success')
        return response.data
      } else {
        addLog(`获取元素信息失败: ${response.error}`, 'error')
        return null
      }
    } catch (error) {
      addLog(`获取元素信息异常: ${error}`, 'error')
      return null
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

  // 初始化
  const initialize = async () => {
    await refreshConnectionStatus()
    if (isConnected.value) {
      await refreshMachines()
      await refreshCurrentTarget()
    } else {
      // 服务端运行模式：若未启动则尝试启动内置测试服务器
      const ok = await startServer(connectionConfig.value.port)
      if (ok) {
        await refreshMachines()
        await refreshCurrentTarget()
      }
    }
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

    // 连接管理
    startServer,
    stopServer,
    connect,
    disconnect,
    refreshConnectionStatus,

    // 多机器多应用管理
    refreshMachines,
    refreshApps,
    setCurrentTarget,
    refreshCurrentTarget,

    // 截图管理
    takeScreenshot,

    // 元素操作
    performClickElement,
    performClickImage,
    performDragTo,
    performInputText,
    performHotkey,
    getElementLocation,
    performFindImage,

    // 日志管理
    addLog,
    clearLogs,

    // 初始化
    initialize
  }
}) 