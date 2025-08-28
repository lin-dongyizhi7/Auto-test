import request from '@/utils/request'
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
  ScreenshotData,
  ScriptInfo,
  CreateScriptRequest,
  UpdateScriptRequest,
  ScriptRunResult,
  OperationResult,
  ApiResponse
} from './types'

// 连接管理API
export const connectToTestServer = (data: TestServerConnection): Promise<ApiResponse> => {
  return request.post('/connect', data)
}

export const disconnectFromTestServer = (): Promise<ApiResponse> => {
  return request.post('/disconnect')
}

export const getConnectionStatus = (): Promise<ApiResponse<ConnectionStatus>> => {
  return request.get('/status')
}

// 多机器多应用管理API
export const getMachines = (): Promise<ApiResponse<{ machines: MachineInfo[] }>> => {
  return request.get('/machines')
}

export const getApps = (machineId?: string): Promise<ApiResponse<{ apps: AppInfo[] }>> => {
  const params = machineId ? { machine_id: machineId } : {}
  return request.get('/apps', { params })
}

export const setTarget = (data: MachineAppTarget): Promise<ApiResponse> => {
  return request.post('/set-target', data)
}

export const getCurrentTarget = (): Promise<ApiResponse<CurrentTarget>> => {
  return request.get('/current-target')
}

export const getScreenshot = (data?: ScreenshotRequest): Promise<ApiResponse<ScreenshotData>> => {
  return request.post('/screenshot', data)
}

// 元素操作API
export const clickElement = (data: ElementOperation): Promise<ApiResponse> => {
  return request.post('/click-element', data)
}

export const clickImage = (data: ImageOperation): Promise<ApiResponse> => {
  return request.post('/click-image', data)
}

export const dragTo = (data: DragOperation): Promise<ApiResponse> => {
  return request.post('/drag-to', data)
}

export const inputText = (data: TextInput): Promise<ApiResponse> => {
  return request.post('/input-text', data)
}

export const hotkey = (data: HotkeyOperation): Promise<ApiResponse> => {
  return request.post('/hotkey', data)
}

export const getElementInfo = (path: string, roles?: string): Promise<ApiResponse> => {
  const params = { path, ...(roles && { roles }) }
  return request.get('/element-info', { params })
}

export const findImage = (data: ImageOperation): Promise<ApiResponse> => {
  return request.post('/find-image', data)
}

// 脚本管理API
export const getScripts = (): Promise<ApiResponse<ScriptInfo[]>> => {
  return request.get('/scripts')
}

export const getScript = (id: string): Promise<ApiResponse<ScriptInfo>> => {
  return request.get(`/scripts/${id}`)
}

export const createScript = (data: CreateScriptRequest): Promise<ApiResponse<ScriptInfo>> => {
  return request.post('/scripts', data)
}

export const updateScript = (id: string, data: UpdateScriptRequest): Promise<ApiResponse<ScriptInfo>> => {
  return request.put(`/scripts/${id}`, data)
}

export const deleteScript = (id: string): Promise<ApiResponse> => {
  return request.delete(`/scripts/${id}`)
}

export const runScript = (id: string): Promise<ApiResponse<ScriptRunResult>> => {
  return request.post(`/scripts/${id}/run`)
}

export const importScript = (file: File): Promise<ApiResponse<ScriptInfo>> => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/scripts/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const exportScript = (id: string): Promise<Blob> => {
  return request.get(`/scripts/${id}/export`, {
    responseType: 'blob'
  })
} 