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
  PythonScriptRunRequest,
  PythonScriptRunResult,
  PythonScriptConvertRequest,
  OperationResult,
  ApiResponse
} from './types'

// 服务器管理API
export const startServer = (data: TestServerConnection): Promise<ApiResponse> => {
  // 后端仅需要端口，服务端模式忽略host
  return request.post('/api/server/start', { port: data.port })
}

export const stopServer = (): Promise<ApiResponse> => {
  return request.post('/api/server/stop')
}

export const getServerStatus = (): Promise<ApiResponse<ConnectionStatus>> => {
  return request.get('/api/server/status')
}

// 多机器多应用管理API
export const getMachines = (): Promise<ApiResponse<{ machines: MachineInfo[] }>> => {
  return request.get('/api/machines')
}

export const getApps = (machineId?: string): Promise<ApiResponse<{ apps: AppInfo[] }>> => {
  const params = machineId ? { machine_id: machineId } : {}
  return request.get('/api/apps', { params })
}

export const setTarget = (data: MachineAppTarget): Promise<ApiResponse> => {
  return request.post('/api/target/set', data)
}

export const getCurrentTarget = (): Promise<ApiResponse<CurrentTarget>> => {
  return request.get('/api/target/current')
}

export const getScreenshot = (data?: ScreenshotRequest): Promise<ApiResponse<ScreenshotData>> => {
  const params = data?.region ? { region: data.region } : {}
  return request.get('/api/screenshot', { params })
}

// 元素操作API
export const clickElement = (data: ElementOperation): Promise<ApiResponse> => {
  return request.post('/api/element/click', data)
}

export const rightClickElement = (data: ElementOperation): Promise<ApiResponse> => {
  return request.post('/api/element/right-click', data)
}

export const doubleClickElement = (data: ElementOperation): Promise<ApiResponse> => {
  return request.post('/api/element/double-click', data)
}

export const setElementText = (data: TextInput): Promise<ApiResponse> => {
  return request.post('/api/element/set-text', data)
}

export const moveToElement = (data: ElementOperation): Promise<ApiResponse> => {
  return request.post('/api/element/move-to', data)
}

export const dragTo = (data: DragOperation): Promise<ApiResponse> => {
  return request.post('/api/mouse/drag-to', data)
}

// 图像操作API
export const findImage = (data: ImageOperation): Promise<ApiResponse> => {
  return request.post('/api/image/find', data)
}

export const clickImage = (data: ImageOperation): Promise<ApiResponse> => {
  return request.post('/api/image/click', data)
}

// 键盘操作API
export const sendHotkey = (data: HotkeyOperation): Promise<ApiResponse> => {
  return request.post('/api/keyboard/hotkey', data)
}

export const typeText = (data: TextInput): Promise<ApiResponse> => {
  return request.post('/api/keyboard/type', data)
}

// 等待操作API
export const waitForElement = (data: ElementOperation): Promise<ApiResponse> => {
  return request.post('/api/wait/element', data)
}

export const waitForImage = (data: ImageOperation): Promise<ApiResponse> => {
  return request.post('/api/wait/image', data)
}

// 脚本管理API
export const getScripts = (): Promise<ApiResponse<{ scripts: ScriptInfo[] }>> => {
  return request.get('/api/scripts')
}

export const getScript = (id: string): Promise<ApiResponse<ScriptInfo>> => {
  return request.get(`/api/scripts/${id}`)
}

export const importScript = (data: File): Promise<ApiResponse> => {
  return request.post('/api/scripts/import', data)
}

export const exportScript = (id: string): Promise<ApiResponse<string>> => {
  return request.get(`/api/scripts/${id}/export`)
}

export const createScript = (data: CreateScriptRequest): Promise<ApiResponse<ScriptInfo>> => {
  return request.post('/api/scripts', data)
}

export const updateScript = (id: string, data: UpdateScriptRequest): Promise<ApiResponse<ScriptInfo>> => {
  return request.put(`/api/scripts/${id}`, data)
}

export const deleteScript = (id: string): Promise<ApiResponse> => {
  return request.delete(`/api/scripts/${id}`)
}

export const runScript = (id: string, machine_id?: string): Promise<ApiResponse<ScriptRunResult>> => {
  return request.post(`/api/scripts/${id}/run`, { machine_id })
}

// 事件管理API
export const getEvents = (limit?: number, eventType?: string): Promise<ApiResponse<{ events: any[] }>> => {
  const params: any = {}
  if (limit) params.limit = limit
  if (eventType) params.event_type = eventType
  return request.get('/api/events', { params })
}

// 机器信息管理API
export const getMachineInfo = (): Promise<ApiResponse<{ machines: any[] }>> => {
  return request.get('/api/machine/info')
}

export const addMachineInfo = (data: { name: string; host: string; port: number; description?: string }): Promise<ApiResponse> => {
  return request.post('/api/machine/info/add', data)
}

export const updateMachineInfo = (machineId: string, data: { name: string; host: string; port: number; description?: string }): Promise<ApiResponse> => {
  return request.put(`/api/machine/info/${machineId}`, data)
}

export const deleteMachineInfo = (machineId: string): Promise<ApiResponse> => {
  return request.delete(`/api/machine/info/${machineId}`)
}

export const batchDeleteMachineInfo = (machineIds: string[]): Promise<ApiResponse<{deleted: string[]; skipped_connected: string[]; not_found: string[]}>> => {
  return request.post('/api/machine/info/batch-delete', { machine_ids: machineIds })
}

// 机器连接管理API
export const connectToMachine = (host: string, port: number): Promise<ApiResponse> => {
  return request.post('/api/machine/connect', { host, port })
} 

export const connectToMachineById = (machineId: string): Promise<ApiResponse> => {
  return request.post('/api/machine/connectById', { machine_id: machineId })
}

export const disconnectMachineById = (machineId: string): Promise<ApiResponse> => {
  return request.post('/api/machine/disconnectById', { machine_id: machineId })
}

// Python脚本管理API
export const runPythonScript = (data: PythonScriptRunRequest): Promise<ApiResponse<PythonScriptRunResult>> => {
  return request.post('/api/scripts/python/run', data)
}

export const validatePythonScript = (data: PythonScriptRunRequest): Promise<ApiResponse<PythonScriptRunResult>> => {
  return request.post('/api/scripts/python/validate', data)
}

export const convertPythonScript = (data: PythonScriptConvertRequest): Promise<ApiResponse<ScriptInfo>> => {
  return request.post('/api/scripts/python/convert', data)
} 