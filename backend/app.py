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
import logging
from typing import Optional
from datetime import datetime

# 项目根目录加入路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from communicators.test_communicator import TestMachineCommunicator
from communicators.operation_multi_machine import MultiMachineOperation
from config import config

# 导入路由模块
from routes.server import router as server_router, set_global_state as set_server_state
from routes.machine import router as machine_router, set_global_state as set_machine_state
from routes.operation import router as operation_router, set_global_state as set_operation_state
from routes.script import router as script_router

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

# 注册路由
app.include_router(server_router)
app.include_router(machine_router)
app.include_router(operation_router)
app.include_router(script_router)



# ==================== 事件管理端点 ====================

@app.get("/api/events")
async def get_events(limit: int = 100, event_type: Optional[str] = None):
    """获取事件历史"""
    global communicator
    
    if not communicator:
        return {
            "success": False,
            "error": "服务器未运行"
        }
    
    try:
        if event_type:
            try:
                from communicators.test_communicator import EventType
                event_enum = EventType(event_type)
                events = communicator.get_event_history(limit, event_enum)
            except ValueError:
                return {
                    "success": False,
                    "error": f"无效的事件类型: {event_type}"
                }
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
        
        return {
            "success": True,
            "data": {"events": events_data}
        }
        
    except Exception as e:
        logger.error(f"获取事件历史失败: {e}")
        return {
            "success": False,
            "error": f"获取事件历史失败: {str(e)}"
        }

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
        
        # 设置全局状态到各个路由模块
        set_server_state(communicator, operation, is_running)
        set_machine_state(communicator, operation, is_running)
        set_operation_state(communicator, operation, is_running)
        
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

