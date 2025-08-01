import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { OperationResult, ConnectionStatus } from '@/api/types'
import { operationAPI } from '@/api/operation'

export interface OperationHistory {
  id: string
  type: string
  params: any
  result: OperationResult
  timestamp: number
}

export const useOperationStore = defineStore('operation', () => {
  // 状态
  const isConnected = ref(false)
  const targetHost = ref('localhost')
  const targetPort = ref(8888)
  const currentOperation = ref('')
  const operationHistory = ref<OperationHistory[]>([])
  const connectionStatus = ref<ConnectionStatus>('disconnected')

  // 计算属性
  const recentOperations = computed(() => 
    operationHistory.value.slice(-10).reverse()
  )

  const successRate = computed(() => {
    if (operationHistory.value.length === 0) return 0
    const successCount = operationHistory.value.filter(
      op => op.result.success
    ).length
    return Math.round((successCount / operationHistory.value.length) * 100)
  })

  // 动作
  const connect = async (host: string, port: number) => {
    try {
      const result = await operationAPI.connect(host, port)
      if (result) {
        isConnected.value = true
        targetHost.value = host
        targetPort.value = port
        connectionStatus.value = 'connected'
        addOperationHistory('connect', { host, port }, { success: true })
      }
      return result
    } catch (error) {
      connectionStatus.value = 'error'
      addOperationHistory('connect', { host, port }, { 
        success: false, 
        error: error instanceof Error ? error.message : '连接失败' 
      })
      throw error
    }
  }

  const disconnect = async () => {
    try {
      await operationAPI.disconnect()
      isConnected.value = false
      connectionStatus.value = 'disconnected'
      addOperationHistory('disconnect', {}, { success: true })
    } catch (error) {
      addOperationHistory('disconnect', {}, { 
        success: false, 
        error: error instanceof Error ? error.message : '断开连接失败' 
      })
      throw error
    }
  }

  const clickElement = async (path: string, roles?: string[]) => {
    if (!isConnected.value) {
      throw new Error('未连接到目标机器')
    }

    try {
      const result = await operationAPI.clickElement(path, roles)
      addOperationHistory('clickElement', { path, roles }, result)
      return result
    } catch (error) {
      const errorResult = { 
        success: false, 
        error: error instanceof Error ? error.message : '点击元素失败' 
      }
      addOperationHistory('clickElement', { path, roles }, errorResult)
      throw error
    }
  }

  const clickImage = async (imagePath: string, threshold = 0.8) => {
    if (!isConnected.value) {
      throw new Error('未连接到目标机器')
    }

    try {
      const result = await operationAPI.clickImage(imagePath, threshold)
      addOperationHistory('clickImage', { imagePath, threshold }, result)
      return result
    } catch (error) {
      const errorResult = { 
        success: false, 
        error: error instanceof Error ? error.message : '点击图片失败' 
      }
      addOperationHistory('clickImage', { imagePath, threshold }, errorResult)
      throw error
    }
  }

  const dragTo = async (startX: number, startY: number, endX: number, endY: number) => {
    if (!isConnected.value) {
      throw new Error('未连接到目标机器')
    }

    try {
      const result = await operationAPI.dragTo(startX, startY, endX, endY)
      addOperationHistory('dragTo', { startX, startY, endX, endY }, result)
      return result
    } catch (error) {
      const errorResult = { 
        success: false, 
        error: error instanceof Error ? error.message : '拖拽操作失败' 
      }
      addOperationHistory('dragTo', { startX, startY, endX, endY }, errorResult)
      throw error
    }
  }

  const inputText = async (text: string, elementPath?: string) => {
    if (!isConnected.value) {
      throw new Error('未连接到目标机器')
    }

    try {
      const result = await operationAPI.inputText(text, elementPath)
      addOperationHistory('inputText', { text, elementPath }, result)
      return result
    } catch (error) {
      const errorResult = { 
        success: false, 
        error: error instanceof Error ? error.message : '文本输入失败' 
      }
      addOperationHistory('inputText', { text, elementPath }, errorResult)
      throw error
    }
  }

  const addOperationHistory = (
    type: string, 
    params: any, 
    result: OperationResult
  ) => {
    const operation: OperationHistory = {
      id: Date.now().toString(),
      type,
      params,
      result,
      timestamp: Date.now()
    }
    operationHistory.value.push(operation)
  }

  const clearHistory = () => {
    operationHistory.value = []
  }

  return {
    // 状态
    isConnected,
    targetHost,
    targetPort,
    currentOperation,
    operationHistory,
    connectionStatus,
    
    // 计算属性
    recentOperations,
    successRate,
    
    // 动作
    connect,
    disconnect,
    clickElement,
    clickImage,
    dragTo,
    inputText,
    addOperationHistory,
    clearHistory
  }
}) 