import request from '@/utils/request'
import type { OperationResult } from './types'

// 操作API接口
export const operationAPI = {
  // 连接目标机器
  async connect(host: string, port: number): Promise<boolean> {
    const response = await request.post('/api/connect', { host, port })
    return response.data.success
  },

  // 断开连接
  async disconnect(): Promise<void> {
    await request.post('/api/disconnect')
  },

  // 点击元素
  async clickElement(path: string, roles?: string[]): Promise<OperationResult> {
    const response = await request.post('/api/click-element', { path, roles })
    return response.data
  },

  // 右键点击元素
  async rightClickElement(path: string, roles?: string[]): Promise<OperationResult> {
    const response = await request.post('/api/right-click-element', { path, roles })
    return response.data
  },

  // 双击元素
  async doubleClickElement(path: string, roles?: string[]): Promise<OperationResult> {
    const response = await request.post('/api/double-click-element', { path, roles })
    return response.data
  },

  // 点击图片
  async clickImage(imagePath: string, threshold = 0.8): Promise<OperationResult> {
    const response = await request.post('/api/click-image', { imagePath, threshold })
    return response.data
  },

  // 拖拽操作
  async dragTo(startX: number, startY: number, endX: number, endY: number): Promise<OperationResult> {
    const response = await request.post('/api/drag-to', { startX, startY, endX, endY })
    return response.data
  },

  // 百分比拖拽
  async dragToPercentage(startX: number, startY: number, endX: number, endY: number): Promise<OperationResult> {
    const response = await request.post('/api/drag-percentage', { startX, startY, endX, endY })
    return response.data
  },

  // 输入文本
  async inputText(text: string, elementPath?: string): Promise<OperationResult> {
    const response = await request.post('/api/input-text', { text, elementPath })
    return response.data
  },

  // 设置元素文本
  async setElementText(path: string, text: string, roles?: string[]): Promise<OperationResult> {
    const response = await request.post('/api/set-element-text', { path, text, roles })
    return response.data
  },

  // 组合键操作
  async hotkey(keys: string[]): Promise<OperationResult> {
    const response = await request.post('/api/hotkey', { keys })
    return response.data
  },

  // 鼠标滚动
  async scroll(clicks: number): Promise<OperationResult> {
    const response = await request.post('/api/scroll', { clicks })
    return response.data
  },

  // 鼠标移动
  async moveTo(x: number, y: number): Promise<OperationResult> {
    const response = await request.post('/api/move-to', { x, y })
    return response.data
  },

  // 移动到元素中心
  async moveToElementCenter(path: string, roles?: string[]): Promise<OperationResult> {
    const response = await request.post('/api/move-to-element', { path, roles })
    return response.data
  },

  // 获取元素信息
  async getElementInfo(path: string, roles?: string[]): Promise<OperationResult> {
    const response = await request.get('/api/element-info', { params: { path, roles } })
    return response.data
  },

  // 查找图片
  async findImage(imagePath: string, threshold = 0.8): Promise<OperationResult> {
    const response = await request.post('/api/find-image', { imagePath, threshold })
    return response.data
  },

  // 执行自定义指令
  async executeCommands(commands: any[]): Promise<OperationResult> {
    const response = await request.post('/api/execute-commands', { commands })
    return response.data
  }
} 