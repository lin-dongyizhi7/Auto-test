#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理路由
提供实时日志同步和查询功能
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field

from communicators.test_communicator import TestMachineCommunicator
from communicators.operation_multi_machine import MultiMachineOperation

logger = logging.getLogger("backend.routes.logs")

# 创建路由器
router = APIRouter(prefix="/api/logs", tags=["日志管理"])

# 全局状态
communicator: Optional[TestMachineCommunicator] = None
operation: Optional[MultiMachineOperation] = None
is_running = False

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.machine_logs: Dict[str, List[Dict]] = {}  # machine_id -> logs
        self.max_logs_per_machine = 1000  # 每台机器最多保存1000条日志
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
    
    async def send_log_to_clients(self, log_data: Dict):
        """向所有连接的客户端发送日志"""
        if not self.active_connections:
            return
            
        message = json.dumps({
            "type": "log_update",
            "data": log_data
        })
        
        # 发送给所有连接的客户端
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"发送日志到客户端失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)
    
    def add_machine_log(self, machine_id: str, log_entry: Dict):
        """添加机器日志"""
        if machine_id not in self.machine_logs:
            self.machine_logs[machine_id] = []
        
        # 添加时间戳
        log_entry["timestamp"] = datetime.now().isoformat()
        log_entry["machine_id"] = machine_id
        
        self.machine_logs[machine_id].append(log_entry)
        
        # 保持日志数量限制
        if len(self.machine_logs[machine_id]) > self.max_logs_per_machine:
            self.machine_logs[machine_id] = self.machine_logs[machine_id][-self.max_logs_per_machine:]
    
    def get_machine_logs(self, machine_id: str, limit: int = 100) -> List[Dict]:
        """获取指定机器的日志"""
        if machine_id not in self.machine_logs:
            return []
        return self.machine_logs[machine_id][-limit:]
    
    def get_all_logs(self, limit: int = 100) -> List[Dict]:
        """获取所有机器的日志"""
        all_logs = []
        for logs in self.machine_logs.values():
            all_logs.extend(logs)
        
        # 按时间排序
        all_logs.sort(key=lambda x: x.get("timestamp", ""))
        return all_logs[-limit:]

# 全局连接管理器
connection_manager = ConnectionManager()

class LogEntry(BaseModel):
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    source: str = Field(..., description="日志来源")
    machine_id: str = Field(..., description="机器ID")
    timestamp: Optional[str] = Field(None, description="时间戳")

class LogQuery(BaseModel):
    machine_id: Optional[str] = Field(None, description="机器ID，为空则查询所有")
    level: Optional[str] = Field(None, description="日志级别过滤")
    limit: int = Field(100, description="返回条数限制")

def set_global_state(comm, op, running):
    """设置全局状态"""
    global communicator, operation, is_running
    communicator = comm
    operation = op
    is_running = running

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，用于实时日志推送"""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # 保持连接活跃
            data = await websocket.receive_text()
            # 可以在这里处理客户端发送的指令
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
        connection_manager.disconnect(websocket)

@router.post("/sync", response_model=Dict)
async def sync_machine_log(request: LogEntry):
    """接收来自测试机器的日志同步"""
    global communicator
    
    if not communicator:
        raise HTTPException(status_code=503, detail="服务器未运行")
    
    try:
        # 添加日志到管理器
        log_data = request.dict()
        connection_manager.add_machine_log(request.machine_id, log_data)
        
        # 推送给所有连接的客户端
        await connection_manager.send_log_to_clients(log_data)
        
        return {"success": True, "message": "日志同步成功"}
        
    except Exception as e:
        logger.error(f"日志同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"日志同步失败: {str(e)}")

@router.get("/query", response_model=Dict)
async def query_logs(request: LogQuery = None):
    """查询日志"""
    global communicator
    
    if not communicator:
        raise HTTPException(status_code=503, detail="服务器未运行")
    
    try:
        if request and request.machine_id:
            # 查询指定机器的日志
            logs = connection_manager.get_machine_logs(request.machine_id, request.limit)
        else:
            # 查询所有机器的日志
            logs = connection_manager.get_all_logs(request.limit if request else 100)
        
        # 按级别过滤
        if request and request.level:
            logs = [log for log in logs if log.get("level") == request.level]
        
        return {
            "success": True,
            "data": {
                "logs": logs,
                "total": len(logs)
            }
        }
        
    except Exception as e:
        logger.error(f"查询日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询日志失败: {str(e)}")

@router.get("/machines", response_model=Dict)
async def get_log_machines():
    """获取有日志的机器列表"""
    global communicator
    
    if not communicator:
        raise HTTPException(status_code=503, detail="服务器未运行")
    
    try:
        machines = list(connection_manager.machine_logs.keys())
        return {
            "success": True,
            "data": {
                "machines": machines,
                "total": len(machines)
            }
        }
        
    except Exception as e:
        logger.error(f"获取机器列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取机器列表失败: {str(e)}")

@router.delete("/clear/{machine_id}", response_model=Dict)
async def clear_machine_logs(machine_id: str):
    """清空指定机器的日志"""
    global communicator
    
    if not communicator:
        raise HTTPException(status_code=503, detail="服务器未运行")
    
    try:
        if machine_id in connection_manager.machine_logs:
            connection_manager.machine_logs[machine_id] = []
            return {"success": True, "message": f"机器 {machine_id} 的日志已清空"}
        else:
            return {"success": False, "message": f"机器 {machine_id} 不存在或没有日志"}
            
    except Exception as e:
        logger.error(f"清空日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空日志失败: {str(e)}")

# 导出连接管理器，供其他模块使用
def get_connection_manager() -> ConnectionManager:
    return connection_manager
