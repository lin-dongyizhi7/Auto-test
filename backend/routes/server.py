#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器管理路由
提供服务器启动、停止、状态查询等端点
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from communicators.test_communicator import TestMachineCommunicator
from communicators.operation_multi_machine import MultiMachineOperation
from config import config

logger = logging.getLogger("backend.routes.server")

# 创建路由器
router = APIRouter(prefix="/api/server", tags=["服务器管理"])

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

class StartServerRequest(BaseModel):
    port: int = Field(config.DEFAULT_PORT, description="内置测试服务器监听端口")

def set_global_state(comm, op, running, machine_id=None, app_name=None):
    """设置全局状态变量"""
    global communicator, operation, is_running, current_machine_id, current_app_name
    communicator = comm
    operation = op
    is_running = running
    current_machine_id = machine_id
    current_app_name = app_name

@router.post("/start", response_model=OperationResult)
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

@router.post("/stop", response_model=OperationResult)
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

@router.get("/status", response_model=OperationResult)
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
