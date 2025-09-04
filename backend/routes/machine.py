#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器和应用管理路由
提供机器连接、断开、应用管理、目标设置等端点
"""

import json
import os
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from communicators.test_communicator import TestMachineCommunicator
from communicators.operation_multi_machine import MultiMachineOperation
from config import config

logger = logging.getLogger("backend.routes.machine")

# 机器信息管理类
class MachineInfo:
    """机器信息数据模型"""
    def __init__(self, machine_id: str, name: str, host: str, port: int, 
                 description: str = "", status: str = "disconnected"):
        self.id = machine_id
        self.name = name
        self.host = host
        self.port = port
        self.description = description
        self.status = status  # connected, disconnected, error
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.last_connected_at = None
        self.last_disconnected_at = None
        self.connection_count = 0

class MachineInfoManager:
    """机器信息管理器"""
    
    def __init__(self):
        self.data_file = config.MACHINE_INFO_FILE
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """确保数据文件存在"""
        # 确保 data 目录存在
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        # 如果文件不存在，创建初始结构
        if not os.path.exists(self.data_file):
            initial_data = {
                "counter": 0,
                "storage": []
            }
            self._save_data(initial_data)
            logger.info(f"创建机器信息文件: {self.data_file}")
    
    def _load_data(self) -> Dict[str, Any]:
        """加载数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"加载机器信息失败: {e}")
            return {"counter": 0, "storage": []}
    
    def _save_data(self, data: Dict[str, Any]):
        """保存数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存机器信息失败: {e}")
            raise
    
    def _generate_id(self) -> str:
        """生成新的机器ID"""
        data = self._load_data()
        data["counter"] += 1
        self._save_data(data)
        return f"machine_{data['counter']}"
    
    def add_machine(self, name: str, host: str, port: int, description: str = "") -> str:
        """添加新机器"""
        machine_id = self._generate_id()
        machine_info = MachineInfo(machine_id, name, host, port, description)
        
        data = self._load_data()
        data["storage"].append(machine_info.__dict__)
        self._save_data(data)
        
        logger.info(f"添加机器: {machine_id} ({name})")
        return machine_id
    
    def get_machine(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """获取机器信息"""
        data = self._load_data()
        for machine in data["storage"]:
            if machine["id"] == machine_id:
                return machine
        return None
    
    def get_all_machines(self) -> List[Dict[str, Any]]:
        """获取所有机器信息"""
        data = self._load_data()
        return data["storage"]
    
    def update_machine_status(self, machine_id: str, status: str):
        """更新机器连接状态"""
        data = self._load_data()
        for machine in data["storage"]:
            if machine["id"] == machine_id:
                machine["status"] = status
                machine["updated_at"] = datetime.now().isoformat()
                
                if status == "connected":
                    machine["last_connected_at"] = datetime.now().isoformat()
                    machine["connection_count"] += 1
                elif status == "disconnected":
                    machine["last_disconnected_at"] = datetime.now().isoformat()
                
                self._save_data(data)
                logger.info(f"更新机器状态: {machine_id} -> {status}")
                return True
        
        logger.warning(f"未找到机器: {machine_id}")
        return False
    
    def update_machine_info(self, machine_id: str, **kwargs) -> bool:
        """更新机器信息"""
        data = self._load_data()
        for machine in data["storage"]:
            if machine["id"] == machine_id:
                for key, value in kwargs.items():
                    if key in machine:
                        machine[key] = value
                machine["updated_at"] = datetime.now().isoformat()
                self._save_data(data)
                logger.info(f"更新机器信息: {machine_id}")
                return True
        
        logger.warning(f"未找到机器: {machine_id}")
        return False
    
    def delete_machine(self, machine_id: str) -> bool:
        """删除机器"""
        data = self._load_data()
        for i, machine in enumerate(data["storage"]):
            if machine["id"] == machine_id:
                del data["storage"][i]
                self._save_data(data)
                logger.info(f"删除机器: {machine_id}")
                return True
        
        logger.warning(f"未找到机器: {machine_id}")
        return False
    
    def find_machine_by_address(self, host: str, port: int) -> Optional[Dict[str, Any]]:
        """根据地址查找机器"""
        data = self._load_data()
        for machine in data["storage"]:
            if machine["host"] == host and machine["port"] == port:
                return machine
        return None
    
    def reset_all_machine_status(self) -> int:
        """重置所有机器的连接状态为未连接"""
        data = self._load_data()
        reset_count = 0
        
        for machine in data["storage"]:
            if machine["status"] != "disconnected":
                machine["status"] = "disconnected"
                machine["updated_at"] = datetime.now().isoformat()
                machine["last_disconnected_at"] = datetime.now().isoformat()
                reset_count += 1
        
        if reset_count > 0:
            self._save_data(data)
            logger.info(f"重置了 {reset_count} 个机器的连接状态为未连接")
        
        return reset_count

# 创建机器管理器实例
machine_manager = MachineInfoManager()

# 创建路由器
router = APIRouter(prefix="/api", tags=["机器和应用管理"])

# 全局状态（这些变量将在主应用中初始化）
communicator: Optional[TestMachineCommunicator] = None
operation: Optional[MultiMachineOperation] = None
is_running = False
current_machine_id: Optional[str] = None
current_app_name: Optional[str] = None

class OperationResult(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    message: Optional[str] = None

class MachineAppTargetRequest(BaseModel):
    machine_id: str
    app_name: str

class MachineInfoRequest(BaseModel):
    name: str
    host: str
    port: int
    description: str = ""

class MachineConnectRequest(BaseModel):
    machine_id: str

class MachineDisconnectRequest(BaseModel):
    machine_id: str

def set_global_state(comm, op, running, machine_id=None, app_name=None):
    """设置全局状态变量"""
    global communicator, operation, is_running, current_machine_id, current_app_name
    communicator = comm
    operation = op
    is_running = running
    current_machine_id = machine_id
    current_app_name = app_name

@router.get("/machines", response_model=OperationResult)
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

@router.post("/machine/connect", response_model=OperationResult)
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

@router.post("/machine/disconnect", response_model=OperationResult)
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

@router.get("/apps", response_model=OperationResult)
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

@router.post("/target/set", response_model=OperationResult)
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

# 机器信息管理端点
@router.get("/machine/info", response_model=OperationResult)
async def get_machine_info():
    """获取所有机器信息"""
    try:
        machines = machine_manager.get_all_machines()
        return OperationResult(
            success=True,
            data={"machines": machines}
        )
    except Exception as e:
        logger.error(f"获取机器信息失败: {e}")
        return OperationResult(
            success=False,
            error=f"获取机器信息失败: {str(e)}"
        )

@router.post("/machine/info", response_model=OperationResult)
async def add_machine_info(request: MachineInfoRequest):
    """添加新机器信息"""
    try:
        # 检查是否已存在相同地址的机器
        existing = machine_manager.find_machine_by_address(request.host, request.port)
        if existing:
            return OperationResult(
                success=False,
                error=f"地址 {request.host}:{request.port} 的机器已存在"
            )
        
        machine_id = machine_manager.add_machine(
            request.name, request.host, request.port, request.description
        )
        
        return OperationResult(
            success=True,
            data={"machine_id": machine_id},
            message="机器信息添加成功"
        )
    except Exception as e:
        logger.error(f"添加机器信息失败: {e}")
        return OperationResult(
            success=False,
            error=f"添加机器信息失败: {str(e)}"
        )

@router.put("/machine/info/{machine_id}", response_model=OperationResult)
async def update_machine_info(machine_id: str, request: MachineInfoRequest):
    """更新机器信息"""
    try:
        success = machine_manager.update_machine_info(
            machine_id,
            name=request.name,
            host=request.host,
            port=request.port,
            description=request.description
        )
        
        if success:
            return OperationResult(
                success=True,
                message="机器信息更新成功"
            )
        else:
            return OperationResult(
                success=False,
                error="机器不存在"
            )
    except Exception as e:
        logger.error(f"更新机器信息失败: {e}")
        return OperationResult(
            success=False,
            error=f"更新机器信息失败: {str(e)}"
        )

@router.delete("/machine/info/{machine_id}", response_model=OperationResult)
async def delete_machine_info(machine_id: str):
    """删除机器信息"""
    try:
        success = machine_manager.delete_machine(machine_id)
        
        if success:
            return OperationResult(
                success=True,
                message="机器信息删除成功"
            )
        else:
            return OperationResult(
                success=False,
                error="机器不存在"
            )
    except Exception as e:
        logger.error(f"删除机器信息失败: {e}")
        return OperationResult(
            success=False,
            error=f"删除机器信息失败: {str(e)}"
        )

@router.post("/machine/connectById", response_model=OperationResult)
async def connect_to_machine_by_id(request: MachineConnectRequest):
    """连接到指定机器"""
    global communicator
    
    if not communicator:
        return OperationResult(
            success=False,
            error="测试服务器未启动"
        )
    
    try:
        # 获取机器信息
        machine_info = machine_manager.get_machine(request.machine_id)
        if not machine_info:
            return OperationResult(
                success=False,
                error="机器不存在"
            )
        
        # 连接到机器（使用固定端口8888）
        success = communicator.connect_to_machine(request.machine_id, machine_info["host"], 8888)
        
        if success:
            # 更新机器状态
            machine_manager.update_machine_status(request.machine_id, "connected")
            
            return OperationResult(
                success=True,
                message=f"成功连接到机器 {machine_info['name']}"
            )
        else:
            # 更新机器状态为错误
            machine_manager.update_machine_status(request.machine_id, "error")
            
            return OperationResult(
                success=False,
                error="连接失败"
            )
            
    except Exception as e:
        logger.error(f"连接机器失败: {e}")
        return OperationResult(
            success=False,
            error=f"连接失败: {str(e)}"
        )

@router.post("/machine/disconnectById", response_model=OperationResult)
async def disconnect_machine_by_id(request: MachineDisconnectRequest):
    """断开与指定机器的连接"""
    global communicator
    
    if not communicator:
        return OperationResult(
            success=False,
            error="测试服务器未启动"
        )
    
    try:
        # 获取机器信息
        machine_info = machine_manager.get_machine(request.machine_id)
        if not machine_info:
            return OperationResult(
                success=False,
                error="机器不存在"
            )
        
        # 断开连接
        success = communicator.disconnect_machine(request.machine_id)
        
        if success:
            # 更新机器状态
            machine_manager.update_machine_status(request.machine_id, "disconnected")
            
            return OperationResult(
                success=True,
                message=f"已断开与机器 {machine_info['name']} 的连接"
            )
        else:
            return OperationResult(
                success=False,
                error="断开连接失败"
            )
            
    except Exception as e:
        logger.error(f"断开机器连接失败: {e}")
        return OperationResult(
            success=False,
            error=f"断开连接失败: {str(e)}"
        )

@router.get("/target/current", response_model=OperationResult)
async def get_current_target():
    """获取当前操作目标"""
    return OperationResult(
        success=True,
        data={
            "machine_id": current_machine_id,
            "app_name": current_app_name
        }
    )
