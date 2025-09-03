// 基础响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 连接相关类型
export interface TestServerConnection {
  host: string;
  port: number;
}

export interface ConnectionStatus {
  is_running: boolean;
  current_machine_id?: string;
  current_app_name?: string;
  connection_summary?: {
    machines: {
      total: number;
      connected: number;
      disconnected: number;
    };
    apps: {
      total: number;
      running: number;
    };
    events: {
      total: number;
      subscribers: number;
    };
  };
}

// 多机器多应用类型
export interface MachineInfo {
  machine_id: string;
  status: string;
  address: string | [string, number];
  info: any;
  connected_at: number;
  last_seen: number;
  apps_count: number;
  apps: string[];
}

export interface AppInfo {
  app_id: string;
  machine_id: string;
  app_name: string;
  status: string;
  info: any;
  registered_at: number;
  machine_status: string;
  machine_address: string | [string, number];
}

export interface MachineAppTarget {
  machine_id: string;
  app_name: string;
}

export interface CurrentTarget {
  machine_id: string;
  app_name: string;
}

// 元素操作类型
export interface ElementOperation {
  path: string;
  roles?: string[];
}

export interface ImageOperation {
  imagePath: string;
  threshold: number;
}

export interface DragOperation {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

export interface TextInput {
  text: string;
  elementPath?: string;
}

export interface HotkeyOperation {
  keys: string[];
}

// 截图类型
export interface ScreenshotRequest {
  region?: string; // "x,y,width,height" 格式
}

export interface ScreenshotData {
  screenshot: string; // base64编码的图片数据
  size: {
    width: number;
    height: number;
  };
  machine_id: string;
  app_name: string;
}

// 脚本管理类型
export interface ScriptInfo {
  id: string;
  name: string;
  description?: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  lastRunTime?: string;
  runCount: number;
  target_app_name?: string;
  last_run_machine_id?: string;
}

export interface CreateScriptRequest {
  name: string;
  description?: string;
  content: string;
  target_app_name?: string;
}

export interface UpdateScriptRequest {
  name?: string;
  description?: string;
  content?: string;
  target_app_name?: string;
}

export interface ScriptRunResult {
  success: boolean;
  output?: string;
  error?: string;
  executionTime: number;
}

// 操作结果类型
export interface OperationResult {
  success: boolean;
  data?: any;
  error?: string;
  message?: string;
}

// 事件类型
export interface EventInfo {
  type: string;
  machine_id: string;
  app_name?: string;
  timestamp: number;
  data: any;
  source_machine: string;
} 