// 操作结果类型
export interface OperationResult {
  success: boolean
  data?: any
  error?: string
}

// 连接状态类型
export type ConnectionStatus = 'connected' | 'disconnected' | 'error' | 'connecting'

// 元素信息类型
export interface ElementInfo {
  position: {
    x: number
    y: number
  }
  size: {
    width: number
    height: number
  }
  center_x: number
  center_y: number
  name?: string
  role?: string
  description?: string
}

// 日志消息类型
export interface LogMessage {
  id: string
  level: 'info' | 'warning' | 'error' | 'success'
  message: string
  timestamp: number
  details?: any
}

// 截图信息类型
export interface ScreenshotInfo {
  data: string // base64编码的图片数据
  width: number
  height: number
  timestamp: number
}

// 测试脚本类型
export interface TestScript {
  id: string
  name: string
  description?: string
  operations: ScriptOperation[]
  created_at: number
  updated_at: number
}

// 脚本操作类型
export interface ScriptOperation {
  id: string
  type: 'clickElement' | 'clickImage' | 'dragTo' | 'inputText' | 'hotkey' | 'wait'
  params: any
  delay?: number // 操作前延迟（毫秒）
}

// 连接配置类型
export interface ConnectionConfig {
  host: string
  port: number
  timeout?: number
  retryCount?: number
}

// 操作配置类型
export interface OperationConfig {
  defaultDelay: number
  clickDelay: number
  dragDelay: number
  imageThreshold: number
  maxRetries: number
}

// 系统设置类型
export interface SystemSettings {
  connection: ConnectionConfig
  operation: OperationConfig
  ui: {
    theme: 'light' | 'dark'
    language: 'zh-CN' | 'en-US'
    autoRefresh: boolean
    refreshInterval: number
  }
} 