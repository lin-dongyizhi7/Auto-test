#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作路由
提供元素操作、图像操作、键盘操作、等待操作等端点
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from communicators.test_communicator import TestMachineCommunicator
from communicators.operation_multi_machine import MultiMachineOperation

logger = logging.getLogger("backend.routes.operation")

# 创建路由器
router = APIRouter(prefix="/api", tags=["操作"])

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

def set_global_state(comm, op, running, machine_id=None, app_name=None):
    """设置全局状态变量"""
    global communicator, operation, is_running, current_machine_id, current_app_name
    communicator = comm
    operation = op
    is_running = running
    current_machine_id = machine_id
    current_app_name = app_name

# ==================== 元素操作端点 ====================

@router.post("/element/click", response_model=OperationResult)
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

@router.post("/element/right-click", response_model=OperationResult)
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

@router.post("/element/double-click", response_model=OperationResult)
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

@router.post("/element/set-text", response_model=OperationResult)
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

@router.post("/element/move-to", response_model=OperationResult)
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

@router.post("/image/find", response_model=OperationResult)
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

@router.post("/image/click", response_model=OperationResult)
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

@router.get("/screenshot", response_model=OperationResult)
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

@router.post("/keyboard/hotkey", response_model=OperationResult)
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

@router.post("/keyboard/type", response_model=OperationResult)
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

@router.post("/wait/element", response_model=OperationResult)
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

@router.post("/wait/image", response_model=OperationResult)
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
