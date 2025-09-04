#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器和应用管理路由
提供机器连接、断开、应用管理、目标设置等端点
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from communicators.test_communicator import TestMachineCommunicator
from communicators.operation_multi_machine import MultiMachineOperation

logger = logging.getLogger("backend.routes.machine")

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
