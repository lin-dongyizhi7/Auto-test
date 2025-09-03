#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全新后端（服务端运行模式）
 - 使用 FastAPI 暴露 HTTP API
 - 在本进程内启动并管理内置测试服务器（通过 communicators.test_communicator.TestMachineCommunicator）
 - 提供多机器/多应用的管理与操作端点
 - 提供脚本管理端点（使用JSON文件持久化存储）
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

# 项目根目录加入路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from communicators.test_communicator import TestMachineCommunicator
from communicators.operation_multi_machine import MultiMachineOperation
from config import config

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger("backend.app")

# 全局运行状态
communicator: Optional[TestMachineCommunicator] = None
operation: Optional[MultiMachineOperation] = None
is_running = False
current_machine_id: Optional[str] = None
current_app_name: Optional[str] = None

# 脚本存储路径（从配置文件获取）
SCRIPT_INFO_FILE = config.SCRIPT_INFO_FILE
SCRIPTS_STORE_DIR = config.SCRIPTS_STORE_DIR

class OperationResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

class StartServerRequest(BaseModel):
    port: int = Field(config.DEFAULT_PORT, description="内置测试服务器监听端口")

class MachineAppTargetRequest(BaseModel):
    machine_id: str
    app_name: str

class ElementOperationRequest(BaseModel):
    path: str
    roles: Optional[List[str]] = None

class ImageOperationRequest(BaseModel):
    imagePath: str
    threshold: float = 0.8

class DragRequest(BaseModel):
    startX: int
    startY: int
    endX: int
    endY: int

class TextInputRequest(BaseModel):
    text: str
    elementPath: Optional[str] = None

class HotkeyRequest(BaseModel):
    keys: List[str]

class ScriptInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    path: str
    content: Optional[str] = None
    createdAt: str
    updatedAt: str
    status: str = "idle"
    lastRunTime: Optional[str] = None
    runCount: int = 0
    target_machine_id: Optional[str] = None
    target_app_name: Optional[str] = None

class CreateScriptRequest(BaseModel):
    name: str
    description: Optional[str] = None
    content: str
    target_machine_id: Optional[str] = None
    target_app_name: Optional[str] = None

class UpdateScriptRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    target_machine_id: Optional[str] = None
    target_app_name: Optional[str] = None

class ScriptRunResult(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    executionTime: Optional[int] = None

# 脚本存储管理类
class ScriptStorageManager:
    def __init__(self, info_file: str, store_dir: str):
        self.info_file = info_file
        self.store_dir = store_dir
        self.scripts_storage: Dict[str, ScriptInfo] = {}
        self.script_counter = 0
        self._ensure_storage_dir()
        self._load_data()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        storage_dir = os.path.dirname(self.info_file)
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
            logger.info(f"创建脚本存储目录: {storage_dir}")
        if not os.path.exists(self.store_dir):
            os.makedirs(self.store_dir, exist_ok=True)
            logger.info(f"创建脚本内容目录: {self.store_dir}")
    
    def _load_data(self):
        """从JSON文件加载脚本数据"""
        try:
            if os.path.exists(self.info_file):
                with open(self.info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                self.script_counter = int(info.get('counter', 0))
                storage_list = info.get('storage', []) or []
                for item in storage_list:
                    # 兼容老字段：若存在 content 则保留；但主要以 path 为准
                    self.scripts_storage[item['id']] = ScriptInfo(** item)
                logger.info(f"从文件加载了 {len(self.scripts_storage)} 个脚本，计数器 {self.script_counter}")
            else:
                logger.info("脚本信息文件不存在，使用空存储")
        except Exception as e:
            logger.error(f"加载脚本数据失败: {e}")
            # 使用默认值
            self.scripts_storage = {}
            self.script_counter = 0
    
    def _save_data(self):
        """保存脚本数据到JSON文件"""
        try:
            self._ensure_storage_dir()
            storage_list = []
            for script_id, script_info in self.scripts_storage.items():
                data = script_info.model_dump()
                # 避免把 content 大字段写入 info 文件
                if 'content' in data:
                    data.pop('content')
                storage_list.append(data)
            info_obj = {"counter": self.script_counter, "storage": storage_list}
            with open(self.info_file, 'w', encoding='utf-8') as f:
                json.dump(info_obj, f, ensure_ascii=False, indent=2)
            logger.info("脚本元数据保存成功")
        except Exception as e:
            logger.error(f"保存脚本数据失败: {e}")
            raise
    
    def get_all_scripts(self) -> List[ScriptInfo]:
        """获取所有脚本"""
        return list(self.scripts_storage.values())
    
    def get_script(self, script_id: str) -> Optional[ScriptInfo]:
        """获取单个脚本"""
        return self.scripts_storage.get(script_id)
    
    def create_script(self, req: CreateScriptRequest) -> ScriptInfo:
        """创建新脚本"""
        # 检查脚本大小
        if len(req.content.encode('utf-8')) > config.SCRIPT_MAX_SIZE:
            raise ValueError(f"脚本内容过大，最大允许 {config.SCRIPT_MAX_SIZE} 字节")
        
        self.script_counter += 1
        script_id = f"script_{self.script_counter}"
        
        # 创建脚本信息
        now = datetime.now().isoformat()
        # 为脚本确定存储路径（使用 .json 作为内容文件扩展名）
        file_name = f"{script_id}.json"
        file_path = os.path.join(self.store_dir, file_name)
        # 写入脚本内容到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(req.content)
        script_info = ScriptInfo(
            id=script_id,
            name=req.name,
            description=req.description,
            path=file_path,
            createdAt=now,
            updatedAt=now,
            target_machine_id=req.target_machine_id,
            target_app_name=req.target_app_name
        )
        
        # 保存到存储
        self.scripts_storage[script_id] = script_info
        self._save_data()
        
        logger.info(f"创建脚本成功: {script_id}")
        return script_info
    
    def update_script(self, script_id: str, req: UpdateScriptRequest) -> ScriptInfo:
        """更新脚本"""
        if script_id not in self.scripts_storage:
            raise ValueError(f"脚本 {script_id} 不存在")
        
        script_info = self.scripts_storage[script_id]
        
        # 更新字段
        if req.name is not None:
            script_info.name = req.name
        if req.description is not None:
            script_info.description = req.description
        if req.content is not None:
            # 检查脚本大小
            if len(req.content.encode('utf-8')) > config.SCRIPT_MAX_SIZE:
                raise ValueError(f"脚本内容过大，最大允许 {config.SCRIPT_MAX_SIZE} 字节")
            # 写回内容文件
            with open(script_info.path, 'w', encoding='utf-8') as f:
                f.write(req.content)
        if req.target_machine_id is not None:
            script_info.target_machine_id = req.target_machine_id
        if req.target_app_name is not None:
            script_info.target_app_name = req.target_app_name
        
        script_info.updatedAt = datetime.now().isoformat()
        
        # 保存到存储
        self._save_data()
        
        logger.info(f"更新脚本成功: {script_id}")
        return script_info
    
    def delete_script(self, script_id: str) -> bool:
        """删除脚本"""
        if script_id not in self.scripts_storage:
            return False
        
        # 删除内容文件
        try:
            file_path = self.scripts_storage[script_id].path
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as _:
            pass
        del self.scripts_storage[script_id]
        self._save_data()
        
        logger.info(f"删除脚本成功: {script_id}")
        return True
    
    def update_script_status(self, script_id: str, status: str, last_run_time: Optional[str] = None):
        """更新脚本状态"""
        if script_id not in self.scripts_storage:
            return
        
        script_info = self.scripts_storage[script_id]
        script_info.status = status
        
        if last_run_time:
            script_info.lastRunTime = last_run_time
            script_info.runCount += 1
        
        self._save_data()

# 初始化脚本存储管理器（新结构）
script_manager = ScriptStorageManager(SCRIPT_INFO_FILE, SCRIPTS_STORE_DIR)

# 创建FastAPI应用
app = FastAPI(
    title="自动化测试系统后端API",
    description="提供多机器自动化测试的后端服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 服务器管理端点 ====================

@app.post("/api/server/start", response_model=OperationResult)
async def start_server(request: StartServerRequest):
    """启动内置测试服务器"""
    global communicator, operation, is_running
    
    try:
        if is_running:
            return OperationResult(
                success=False,
                error="服务器已在运行中"
            )
        
        # 启动通信器
        communicator = TestMachineCommunicator(
            server_host="0.0.0.0",
            server_port=request.port,
            server_id="backend_server"
        )
        communicator.start_server()
        
        # 创建操作类
        operation = MultiMachineOperation(communicator)
        
        is_running = True
        
        logger.info(f"内置测试服务器已启动，监听端口: {request.port}")
        
        return OperationResult(
            success=True,
            message=f"内置测试服务器已启动，监听端口: {request.port}"
        )
        
    except Exception as e:
        logger.error(f"启动服务器失败: {e}")
        return OperationResult(
            success=False,
            error=f"启动服务器失败: {str(e)}"
        )

@app.post("/api/server/stop", response_model=OperationResult)
async def stop_server():
    """停止内置测试服务器"""
    global communicator, operation, is_running
    
    try:
        if not is_running:
            return OperationResult(
                success=False,
                error="服务器未运行"
            )
        
        # 停止操作类
        if operation:
            operation.close()
            operation = None
        
        # 停止通信器
        if communicator:
            communicator.stop_server()
            communicator = None
        
        is_running = False
        current_machine_id = None
        current_app_name = None
        
        logger.info("内置测试服务器已停止")
        
        return OperationResult(
            success=True,
            message="内置测试服务器已停止"
        )
        
    except Exception as e:
        logger.error(f"停止服务器失败: {e}")
        return OperationResult(
            success=False,
            error=f"停止服务器失败: {str(e)}"
        )

@app.get("/api/server/status", response_model=OperationResult)
async def get_server_status():
    """获取服务器状态"""
    global communicator, operation, is_running
    
    if not is_running or not communicator:
        return OperationResult(
            success=True,
            data={
                "is_running": False,
                "current_machine_id": None,
                "current_app_name": None
            }
        )
    
    try:
        # 获取连接摘要
        connection_summary = communicator.get_connection_summary()
        
        return OperationResult(
            success=True,
            data={
                "is_running": True,
                "current_machine_id": current_machine_id,
                "current_app_name": current_app_name,
                "connection_summary": connection_summary.get("data", {})
            }
        )
        
    except Exception as e:
        logger.error(f"获取服务器状态失败: {e}")
        return OperationResult(
            success=False,
            error=f"获取服务器状态失败: {str(e)}"
        )

# ==================== 机器和应用管理端点 ====================

@app.get("/api/machines", response_model=OperationResult)
async def get_machines():
    """获取已连接的机器列表"""
    global communicator
    
    if not communicator:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        machines = communicator.get_connected_machines()
        machines_info = {}
        
        for machine_id in machines:
            status = communicator.get_machine_status(machine_id)
            if status.get("success"):
                machines_info[machine_id] = status["data"]
        
        return OperationResult(
            success=True,
            data={"machines": machines_info}
        )
        
    except Exception as e:
        logger.error(f"获取机器列表失败: {e}")
        return OperationResult(
            success=False,
            error=f"获取机器列表失败: {str(e)}"
        )

@app.post("/api/machine/connect", response_model=OperationResult)
async def connect_to_machine(request: dict):
    """连接到目标机器"""
    global communicator
    
    if not communicator:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        host = request.get("host")
        # 按要求固定使用 8888 端口与测试机器连接
        port = 8888
        
        if not host:
            return OperationResult(
                success=False,
                error="主机地址不能为空"
            )
        
        # 生成机器ID
        machine_id = f"machine_{host}_{port}"
        
        # 尝试连接到目标机器
        result = communicator.connect_to_machine(machine_id, host, port)
        
        if result.get("success"):
            logger.info(f"成功连接到目标机器 {host}:{port}")
            return OperationResult(
                success=True,
                message=f"成功连接到目标机器 {host}:{port}"
            )
        else:
            logger.error(f"连接目标机器失败: {result.get('error')}")
            return OperationResult(
                success=False,
                error=result.get("error", "连接失败")
            )
        
    except Exception as e:
        logger.error(f"连接目标机器异常: {e}")
        return OperationResult(
            success=False,
            error=f"连接目标机器失败: {str(e)}"
        )

@app.post("/api/machine/disconnect", response_model=OperationResult)
async def disconnect_machine(request: dict):
    """断开与目标机器的连接"""
    global communicator
    
    if not communicator:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        machine_id = request.get("machine_id")
        
        if not machine_id:
            return OperationResult(
                success=False,
                error="机器ID不能为空"
            )
        
        # 尝试断开连接
        result = communicator.disconnect_machine(machine_id)
        
        if result.get("success"):
            logger.info(f"成功断开与机器 {machine_id} 的连接")
            return OperationResult(
                success=True,
                message=f"成功断开与机器 {machine_id} 的连接"
            )
        else:
            logger.error(f"断开机器连接失败: {result.get('error')}")
            return OperationResult(
                success=False,
                error=result.get("error", "断开连接失败")
            )
        
    except Exception as e:
        logger.error(f"断开机器连接异常: {e}")
        return OperationResult(
            success=False,
            error=f"断开机器连接失败: {str(e)}"
        )

@app.get("/api/apps", response_model=OperationResult)
async def get_apps():
    """获取已注册的应用列表"""
    global communicator
    
    if not communicator:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        apps = communicator.get_registered_apps()
        apps_info = {}
        
        for app_id in apps:
            status = communicator.get_app_status(app_id)
            if status.get("success"):
                apps_info[app_id] = status["data"]
        
        return OperationResult(
            success=True,
            data={"apps": apps_info}
        )
        
    except Exception as e:
        logger.error(f"获取应用列表失败: {e}")
        return OperationResult(
            success=False,
            error=f"获取应用列表失败: {str(e)}"
        )

@app.post("/api/target/set", response_model=OperationResult)
async def set_target(request: MachineAppTargetRequest):
    """设置当前操作目标"""
    global operation, current_machine_id, current_app_name
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        success = operation.set_target(request.machine_id, request.app_name)
        
        if success:
            current_machine_id = request.machine_id
            current_app_name = request.app_name
            
            return OperationResult(
                success=True,
                message=f"设置目标成功: 机器 {request.machine_id}, 应用 {request.app_name}"
            )
        else:
            return OperationResult(
                success=False,
                error="设置目标失败"
            )
            
    except Exception as e:
        logger.error(f"设置目标失败: {e}")
        return OperationResult(
            success=False,
            error=f"设置目标失败: {str(e)}"
        )

@app.get("/api/target/current", response_model=OperationResult)
async def get_current_target():
    """获取当前操作目标"""
    return OperationResult(
        success=True,
        data={
            "machine_id": current_machine_id,
            "app_name": current_app_name
        }
    )

# ==================== 元素操作端点 ====================

@app.post("/api/element/click", response_model=OperationResult)
async def click_element(request: ElementOperationRequest):
    """点击元素"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        commands = operation.click_element(request.path, request.roles)
        
        return OperationResult(
            success=True,
            data={"commands": commands}
        )
        
    except Exception as e:
        logger.error(f"点击元素失败: {e}")
        return OperationResult(
            success=False,
            error=f"点击元素失败: {str(e)}"
        )

@app.post("/api/element/right-click", response_model=OperationResult)
async def right_click_element(request: ElementOperationRequest):
    """右键点击元素"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        commands = operation.right_click_element(request.path, request.roles)
        
        return OperationResult(
            success=True,
            data={"commands": commands}
        )
        
    except Exception as e:
        logger.error(f"右键点击元素失败: {e}")
        return OperationResult(
            success=False,
            error=f"右键点击元素失败: {str(e)}"
        )

@app.post("/api/element/double-click", response_model=OperationResult)
async def double_click_element(request: ElementOperationRequest):
    """双击元素"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        commands = operation.double_click_element(request.path, request.roles)
        
        return OperationResult(
            success=True,
            data={"commands": commands}
        )
        
    except Exception as e:
        logger.error(f"双击元素失败: {e}")
        return OperationResult(
            success=False,
            error=f"双击元素失败: {str(e)}"
        )

@app.post("/api/element/set-text", response_model=OperationResult)
async def set_element_text(request: TextInputRequest):
    """设置元素文本"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        if request.elementPath:
            commands = operation.set_element_text(request.elementPath, request.text)
        else:
            commands = operation.input_text(None, request.text)
        
        return OperationResult(
            success=True,
            data={"commands": commands}
        )
        
    except Exception as e:
        logger.error(f"设置元素文本失败: {e}")
        return OperationResult(
            success=False,
            error=f"设置元素文本失败: {str(e)}"
        )

@app.post("/api/element/move-to", response_model=OperationResult)
async def move_to_element(request: ElementOperationRequest):
    """移动到元素中心"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        result = operation.move_to_element_center(request.path, request.roles)
        
        return OperationResult(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"移动到元素失败: {e}")
        return OperationResult(
            success=False,
            error=f"移动到元素失败: {str(e)}"
        )

# ==================== 图像操作端点 ====================

@app.post("/api/image/find", response_model=OperationResult)
async def find_image(request: ImageOperationRequest):
    """查找图片"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        result = operation.find_image(request.imagePath, request.threshold)
        
        return OperationResult(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"查找图片失败: {e}")
        return OperationResult(
            success=False,
            error=f"查找图片失败: {str(e)}"
        )

@app.post("/api/image/click", response_model=OperationResult)
async def click_image(request: ImageOperationRequest):
    """点击图片"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        result = operation.click_image(request.imagePath, request.threshold)
        
        return OperationResult(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"点击图片失败: {e}")
        return OperationResult(
            success=False,
            error=f"点击图片失败: {str(e)}"
        )

@app.get("/api/screenshot", response_model=OperationResult)
async def get_screenshot():
    """获取截图"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        result = operation.get_screenshot()
        
        return OperationResult(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取截图失败: {e}")
        return OperationResult(
            success=False,
            error=f"获取截图失败: {str(e)}"
        )

# ==================== 键盘操作端点 ====================

@app.post("/api/keyboard/hotkey", response_model=OperationResult)
async def send_hotkey(request: HotkeyRequest):
    """发送组合键"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        result = operation.hotkey(request.keys)
        
        return OperationResult(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"发送组合键失败: {e}")
        return OperationResult(
            success=False,
            error=f"发送组合键失败: {str(e)}"
        )

@app.post("/api/keyboard/type", response_model=OperationResult)
async def type_text(request: TextInputRequest):
    """输入文本"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        commands = operation.input_text(request.elementPath, request.text)
        
        return OperationResult(
            success=True,
            data={"commands": commands}
        )
        
    except Exception as e:
        logger.error(f"输入文本失败: {e}")
        return OperationResult(
            success=False,
            error=f"输入文本失败: {str(e)}"
        )

# ==================== 等待操作端点 ====================

@app.post("/api/wait/element", response_model=OperationResult)
async def wait_for_element(request: ElementOperationRequest):
    """等待元素出现"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        result = operation.wait_for_element(request.path, timeout=30, role_name_list=request.roles)
        
        return OperationResult(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"等待元素失败: {e}")
        return OperationResult(
            success=False,
            error=f"等待元素失败: {str(e)}"
        )

@app.post("/api/wait/image", response_model=OperationResult)
async def wait_for_image(request: ImageOperationRequest):
    """等待图片出现"""
    global operation
    
    if not operation:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        result = operation.wait_for_image(request.imagePath, request.threshold, timeout=30)
        
        return OperationResult(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"等待图片失败: {e}")
        return OperationResult(
            success=False,
            error=f"等待图片失败: {str(e)}"
        )

# ==================== 脚本管理端点 ====================

@app.get("/api/scripts", response_model=OperationResult)
async def get_scripts():
    """获取所有脚本"""
    try:
        scripts = script_manager.get_all_scripts()
        return OperationResult(
            success=True,
            data={"scripts": [script.model_dump() for script in scripts]}
        )
    except Exception as e:
        logger.error(f"获取脚本列表失败: {e}")
        return OperationResult(
            success=False,
            error=f"获取脚本列表失败: {str(e)}"
        )

@app.get("/api/scripts/{script_id}", response_model=OperationResult)
async def get_script(script_id: str):
    """获取单个脚本"""
    try:
        script = script_manager.get_script(script_id)
        if not script:
            return OperationResult(
                success=False,
                error="脚本不存在"
            )
        
        return OperationResult(
            success=True,
            data=script.model_dump()
        )
    except Exception as e:
        logger.error(f"获取脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"获取脚本失败: {str(e)}"
        )

@app.post("/api/scripts", response_model=OperationResult)
async def create_script(request: CreateScriptRequest):
    """创建新脚本"""
    try:
        script = script_manager.create_script(request)
        return OperationResult(
            success=True,
            data=script.model_dump()
        )
    except Exception as e:
        logger.error(f"创建脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"创建脚本失败: {str(e)}"
        )

@app.put("/api/scripts/{script_id}", response_model=OperationResult)
async def update_script(script_id: str, request: UpdateScriptRequest):
    """更新脚本"""
    try:
        script = script_manager.update_script(script_id, request)
        return OperationResult(
            success=True,
            data=script.model_dump()
        )
    except Exception as e:
        logger.error(f"更新脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"更新脚本失败: {str(e)}"
        )

@app.delete("/api/scripts/{script_id}", response_model=OperationResult)
async def delete_script(script_id: str):
    """删除脚本"""
    try:
        success = script_manager.delete_script(script_id)
        if success:
            return OperationResult(
                success=True,
                message="脚本删除成功"
            )
        else:
            return OperationResult(
                success=False,
                error="脚本不存在"
            )
    except Exception as e:
        logger.error(f"删除脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"删除脚本失败: {str(e)}"
        )

@app.post("/api/scripts/{script_id}/run", response_model=OperationResult)
async def run_script(script_id: str):
    """运行脚本"""
    try:
        script = script_manager.get_script(script_id)
        if not script:
            return OperationResult(
                success=False,
                error="脚本不存在"
            )
        
        # 更新脚本状态
        script_manager.update_script_status(script_id, "running", datetime.now().isoformat())
        
        # 这里应该实现脚本执行逻辑
        # 暂时返回成功
        return OperationResult(
            success=True,
            message="脚本执行成功"
        )
        
    except Exception as e:
        logger.error(f"运行脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"运行脚本失败: {str(e)}"
        )

# ==================== 事件管理端点 ====================

@app.get("/api/events", response_model=OperationResult)
async def get_events(limit: int = 100, event_type: Optional[str] = None):
    """获取事件历史"""
    global communicator
    
    if not communicator:
        return OperationResult(
            success=False,
            error="服务器未运行"
        )
    
    try:
        if event_type:
            try:
                from communicators.test_communicator import EventType
                event_enum = EventType(event_type)
                events = communicator.get_event_history(limit, event_enum)
            except ValueError:
                return OperationResult(
                    success=False,
                    error=f"无效的事件类型: {event_type}"
                )
        else:
            events = communicator.get_event_history(limit)
        
        # 转换事件为可序列化的格式
        events_data = []
        for event in events:
            events_data.append({
                "type": event.type.value,
                "machine_id": event.machine_id,
                "app_name": event.app_name,
                "timestamp": event.timestamp,
                "data": event.data,
                "source_machine": event.source_machine
            })
        
        return OperationResult(
            success=True,
            data={"events": events_data}
        )
        
    except Exception as e:
        logger.error(f"获取事件历史失败: {e}")
        return OperationResult(
            success=False,
            error=f"获取事件历史失败: {str(e)}"
        )

# ==================== 健康检查端点 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "自动化测试系统后端API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# 启动时的事件处理
@app.on_event("startup")
async def startup_event():
    """应用启动时的处理"""
    global communicator, operation, is_running
    
    logger.info("后端应用启动")
    
    # 默认启动测试服务器
    try:
        communicator = TestMachineCommunicator(
            server_host="0.0.0.0",
            server_port=8888,
            server_id="backend_server"
        )
        communicator.start_server()
        
        # 创建操作类
        operation = MultiMachineOperation(communicator)
        
        is_running = True
        
        logger.info("测试服务器已默认启动，监听端口: 8888")
        
    except Exception as e:
        logger.error(f"默认启动测试服务器失败: {e}")
        is_running = False

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的处理"""
    global communicator, operation
    
    logger.info("后端应用关闭")
    
    # 清理资源
    if operation:
        operation.close()
    
    if communicator:
        communicator.stop_server()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

