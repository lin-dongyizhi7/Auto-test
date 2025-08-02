#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试后端API服务
接收前端请求，调用operation.py中的函数与被测试机器建立连接和执行操作
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 导入自定义模块
from communicators.operation import Operation
from communicators.test_communicator import TestMachineCommunicator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
operation_instance: Optional[Operation] = None
is_connected = False
connection_config = {
    "host": "localhost",
    "port": 8888
}

# Pydantic模型定义
class ConnectionRequest(BaseModel):
    host: str = Field(..., description="被测试机器IP地址")
    port: int = Field(8888, description="被测试机器端口")

class ElementOperationRequest(BaseModel):
    path: str = Field(..., description="元素路径")
    roles: Optional[List[str]] = Field(None, description="角色列表")

class ImageOperationRequest(BaseModel):
    imagePath: str = Field(..., description="图片路径")
    threshold: float = Field(0.8, description="匹配阈值")

class DragRequest(BaseModel):
    startX: int = Field(..., description="起始X坐标")
    startY: int = Field(..., description="起始Y坐标")
    endX: int = Field(..., description="结束X坐标")
    endY: int = Field(..., description="结束Y坐标")

class TextInputRequest(BaseModel):
    text: str = Field(..., description="输入文本")
    elementPath: Optional[str] = Field(None, description="元素路径")

class HotkeyRequest(BaseModel):
    keys: List[str] = Field(..., description="按键列表")

class OperationResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("自动化测试后端服务启动")
    yield
    # 关闭时执行
    if operation_instance:
        try:
            operation_instance.close()
            logger.info("已关闭操作实例")
        except Exception as e:
            logger.error(f"关闭操作实例时出错: {e}")

# 创建FastAPI应用
app = FastAPI(
    title="自动化测试后端API",
    description="接收前端请求，调用operation.py中的函数与被测试机器建立连接和执行操作",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 工具函数
def check_connection():
    """检查是否已连接到被测试机器"""
    if not is_connected or not operation_instance:
        raise HTTPException(status_code=400, detail="未连接到被测试机器，请先建立连接")

def create_operation_result(success: bool, data: Optional[Dict] = None, 
                          error: Optional[str] = None, message: Optional[str] = None) -> OperationResult:
    """创建标准化的操作结果"""
    return OperationResult(
        success=success,
        data=data,
        error=error,
        message=message
    )

# API路由定义

@app.get("/")
async def root():
    """根路径，返回服务状态"""
    return {
        "message": "QGIS自动化测试后端API服务",
        "version": "1.0.0",
        "status": "running",
        "connected": is_connected
    }

@app.get("/status")
async def get_status():
    """获取服务状态"""
    return {
        "connected": is_connected,
        "host": connection_config["host"] if is_connected else None,
        "port": connection_config["port"] if is_connected else None
    }

@app.post("/connect")
async def connect(request: ConnectionRequest):
    """连接到被测试机器"""
    global operation_instance, is_connected, connection_config
    
    try:
        logger.info(f"尝试连接到 {request.host}:{request.port}")
        
        # 创建操作实例
        operation_instance = Operation(request.host, request.port)
        
        # 测试连接
        test_result = operation_instance.communicator.get_screenshot()
        if test_result is not None:
            is_connected = True
            connection_config["host"] = request.host
            connection_config["port"] = request.port
            
            logger.info(f"成功连接到 {request.host}:{request.port}")
            return create_operation_result(
                success=True,
                message=f"成功连接到 {request.host}:{request.port}"
            )
        else:
            raise Exception("无法获取屏幕截图，连接测试失败")
            
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        operation_instance = None
        is_connected = False
        return create_operation_result(
            success=False,
            error=str(e),
            message="连接失败"
        )

@app.post("/disconnect")
async def disconnect():
    """断开与被测试机器的连接"""
    global operation_instance, is_connected
    
    try:
        if operation_instance:
            operation_instance.close()
            operation_instance = None
        
        is_connected = False
        logger.info("已断开连接")
        
        return create_operation_result(
            success=True,
            message="已断开连接"
        )
    except Exception as e:
        logger.error(f"断开连接时出错: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="断开连接失败"
        )

@app.post("/click-element")
async def click_element(request: ElementOperationRequest):
    """点击元素"""
    check_connection()
    
    try:
        logger.info(f"点击元素: {request.path}")
        result = operation_instance.click_element(request.path, request.roles)
        
        return create_operation_result(
            success=True,
            data={"commands": result},
            message="元素点击成功"
        )
    except Exception as e:
        logger.error(f"点击元素失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="元素点击失败"
        )

@app.post("/click-image")
async def click_image(request: ImageOperationRequest):
    """点击图片"""
    check_connection()
    
    try:
        logger.info(f"点击图片: {request.imagePath}")
        result = operation_instance.click_image(request.imagePath, request.threshold)
        
        return create_operation_result(
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error"),
            message="图片点击成功" if result.get("success") else "图片点击失败"
        )
    except Exception as e:
        logger.error(f"点击图片失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="图片点击失败"
        )

@app.post("/drag-to")
async def drag_to(request: DragRequest):
    """拖拽操作"""
    check_connection()
    
    try:
        logger.info(f"拖拽操作: ({request.startX}, {request.startY}) -> ({request.endX}, {request.endY})")
        result = operation_instance.drag_to(request.startX, request.startY, request.endX, request.endY)
        
        return create_operation_result(
            success=True,
            data={"commands": result},
            message="拖拽操作成功"
        )
    except Exception as e:
        logger.error(f"拖拽操作失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="拖拽操作失败"
        )

@app.post("/input-text")
async def input_text(request: TextInputRequest):
    """输入文本"""
    check_connection()
    
    try:
        logger.info(f"输入文本: {request.text}")
        result = operation_instance.input_text(request.text, request.elementPath)
        
        return create_operation_result(
            success=True,
            data={"commands": result},
            message="文本输入成功"
        )
    except Exception as e:
        logger.error(f"文本输入失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="文本输入失败"
        )

@app.post("/hotkey")
async def hotkey(request: HotkeyRequest):
    """快捷键操作"""
    check_connection()
    
    try:
        logger.info(f"快捷键操作: {request.keys}")
        result = operation_instance.hotkey(request.keys)
        
        return create_operation_result(
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error"),
            message="快捷键操作成功" if result.get("success") else "快捷键操作失败"
        )
    except Exception as e:
        logger.error(f"快捷键操作失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="快捷键操作失败"
        )

@app.get("/element-info")
async def get_element_info(path: str, roles: Optional[str] = None):
    """获取元素信息"""
    check_connection()
    
    try:
        logger.info(f"获取元素信息: {path}")
        role_list = roles.split(",") if roles else None
        result = operation_instance.get_location(path, role_list)
        
        return create_operation_result(
            success=True,
            data=result,
            message="获取元素信息成功"
        )
    except Exception as e:
        logger.error(f"获取元素信息失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="获取元素信息失败"
        )

@app.post("/find-image")
async def find_image(request: ImageOperationRequest):
    """查找图片"""
    check_connection()
    
    try:
        logger.info(f"查找图片: {request.imagePath}")
        result = operation_instance.find_image(request.imagePath, request.threshold)
        
        return create_operation_result(
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error"),
            message="图片查找成功" if result.get("success") else "图片查找失败"
        )
    except Exception as e:
        logger.error(f"查找图片失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="查找图片失败"
        )

if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    ) 