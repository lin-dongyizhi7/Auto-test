#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试后端API服务
支持多机器多应用连接，接收前端请求，调用operation_multi_machine.py中的函数
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from datetime import datetime
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 导入自定义模块
from communicators.operation_multi_machine import MultiMachineOperation
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
multi_machine_operation: Optional[MultiMachineOperation] = None
test_server: Optional[TestMachineCommunicator] = None
is_connected = False
current_machine_id: Optional[str] = None
current_app_name: Optional[str] = None

# 连接配置
connection_config = {
    "test_server_host": "localhost",
    "test_server_port": 8889
}

# Pydantic模型定义
class TestServerConnectionRequest(BaseModel):
    host: str = Field(..., description="测试服务器IP地址")
    port: int = Field(8889, description="测试服务器端口")

class MachineAppTargetRequest(BaseModel):
    machine_id: str = Field(..., description="目标机器ID")
    app_name: str = Field(..., description="目标应用名称")

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

class MachineInfo(BaseModel):
    id: str
    address: str
    status: str
    apps: List[str]

class AppInfo(BaseModel):
    id: str
    name: str
    machine_id: str
    status: str
    region: Optional[List[int]] = None

# 脚本管理相关模型
class ScriptInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    content: str
    createdAt: str
    updatedAt: str
    status: str = "idle"
    lastRunTime: Optional[str] = None
    runCount: int = 0
    target_machine_id: Optional[str] = None
    target_app_name: Optional[str] = None

class CreateScriptRequest(BaseModel):
    name: str = Field(..., description="脚本名称")
    description: Optional[str] = Field(None, description="脚本描述")
    content: str = Field(..., description="脚本内容")
    target_machine_id: Optional[str] = Field(None, description="目标机器ID")
    target_app_name: Optional[str] = Field(None, description="目标应用名称")

class UpdateScriptRequest(BaseModel):
    name: Optional[str] = Field(None, description="脚本名称")
    description: Optional[str] = Field(None, description="脚本描述")
    content: Optional[str] = Field(None, description="脚本内容")
    target_machine_id: Optional[str] = Field(None, description="目标机器ID")
    target_app_name: Optional[str] = Field(None, description="目标应用名称")

class ScriptRunResult(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    executionTime: Optional[int] = None

# 模拟脚本存储（实际项目中应该使用数据库）
scripts_storage: Dict[str, ScriptInfo] = {}
script_counter = 0

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("自动化测试后端服务启动")
    yield
    # 关闭时执行
    if multi_machine_operation:
        try:
            multi_machine_operation.close()
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
    if not is_connected or not multi_machine_operation:
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
        "host": connection_config["test_server_host"] if is_connected else None,
        "port": connection_config["test_server_port"] if is_connected else None
    }

@app.post("/connect")
async def connect(request: TestServerConnectionRequest):
    """连接到测试服务器"""
    global multi_machine_operation, test_server, is_connected, connection_config
    
    try:
        logger.info(f"尝试连接到 {request.host}:{request.port}")
        
        # 创建操作实例
        multi_machine_operation = MultiMachineOperation(request.host, request.port)
        test_server = TestMachineCommunicator(request.host, request.port)
        
        # 测试连接
        test_result = test_server.get_screenshot()
        if test_result is not None:
            is_connected = True
            connection_config["test_server_host"] = request.host
            connection_config["test_server_port"] = request.port
            
            logger.info(f"成功连接到 {request.host}:{request.port}")
            return create_operation_result(
                success=True,
                message=f"成功连接到 {request.host}:{request.port}"
            )
        else:
            raise Exception("无法获取屏幕截图，连接测试失败")
            
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        multi_machine_operation = None
        test_server = None
        is_connected = False
        return create_operation_result(
            success=False,
            error=str(e),
            message="连接失败"
        )

@app.post("/disconnect")
async def disconnect():
    """断开与被测试机器的连接"""
    global multi_machine_operation, test_server, is_connected
    
    try:
        if multi_machine_operation:
            multi_machine_operation.close()
            multi_machine_operation = None
        
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
        result = multi_machine_operation.click_element(request.path, request.roles)
        
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
        result = multi_machine_operation.click_image(request.imagePath, request.threshold)
        
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
        result = multi_machine_operation.drag_to(request.startX, request.startY, request.endX, request.endY)
        
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
        result = multi_machine_operation.input_text(request.text, request.elementPath)
        
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
        result = multi_machine_operation.hotkey(request.keys)
        
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
        result = multi_machine_operation.get_location(path, role_list)
        
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
        result = multi_machine_operation.find_image(request.imagePath, request.threshold)
        
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

# 多机器多应用管理API
@app.get("/machines")
async def get_machines():
    """获取可用机器列表"""
    check_connection()
    
    try:
        machines = multi_machine_operation.get_available_machines()
        machine_list = []
        
        for machine_id in machines:
            machine_info = {
                "id": machine_id,
                "address": f"机器_{machine_id}",
                "status": "connected",
                "apps": []
            }
            machine_list.append(machine_info)
        
        return create_operation_result(
            success=True,
            data={"machines": machine_list},
            message="获取机器列表成功"
        )
    except Exception as e:
        logger.error(f"获取机器列表失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="获取机器列表失败"
        )

@app.get("/apps")
async def get_apps(machine_id: Optional[str] = None):
    """获取可用应用列表"""
    check_connection()
    
    try:
        apps = multi_machine_operation.get_available_apps(machine_id)
        app_list = []
        
        for app in apps:
            app_info = {
                "id": f"{app['machine_id']}:{app['name']}",
                "name": app['name'],
                "machine_id": app['machine_id'],
                "status": "running",
                "region": app.get('region')
            }
            app_list.append(app_info)
        
        return create_operation_result(
            success=True,
            data={"apps": app_list},
            message="获取应用列表成功"
        )
    except Exception as e:
        logger.error(f"获取应用列表失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="获取应用列表失败"
        )

@app.post("/set-target")
async def set_target(request: MachineAppTargetRequest):
    """设置当前操作的目标机器和应用"""
    check_connection()
    
    try:
        success = multi_machine_operation.set_target(request.machine_id, request.app_name)
        
        if success:
            global current_machine_id, current_app_name
            current_machine_id = request.machine_id
            current_app_name = request.app_name
            
            logger.info(f"设置目标成功: 机器 {request.machine_id}, 应用 {request.app_name}")
            return create_operation_result(
                success=True,
                data={
                    "machine_id": request.machine_id,
                    "app_name": request.app_name
                },
                message="设置目标成功"
            )
        else:
            return create_operation_result(
                success=False,
                error="设置目标失败",
                message="设置目标失败"
            )
    except Exception as e:
        logger.error(f"设置目标失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="设置目标失败"
        )

@app.get("/current-target")
async def get_current_target():
    """获取当前操作目标"""
    check_connection()
    
    try:
        return create_operation_result(
            success=True,
            data={
                "machine_id": current_machine_id,
                "app_name": current_app_name
            },
            message="获取当前目标成功"
        )
    except Exception as e:
        logger.error(f"获取当前目标失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="获取当前目标失败"
        )

@app.post("/screenshot")
async def get_screenshot(region: Optional[str] = None):
    """获取当前目标应用的截图"""
    check_connection()
    
    try:
        # 解析区域参数
        region_list = None
        if region:
            try:
                region_list = [int(x) for x in region.split(',')]
                if len(region_list) != 4:
                    raise ValueError("区域参数格式错误")
            except ValueError:
                return create_operation_result(
                    success=False,
                    error="区域参数格式错误，应为 x,y,width,height",
                    message="区域参数格式错误"
                )
        
        result = multi_machine_operation.get_screenshot(region_list)
        
        return create_operation_result(
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error"),
            message="获取截图成功" if result.get("success") else "获取截图失败"
        )
    except Exception as e:
        logger.error(f"获取截图失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="获取截图失败"
        )

# 脚本管理API
@app.get("/scripts")
async def get_scripts():
    """获取脚本列表"""
    try:
        scripts = list(scripts_storage.values())
        return create_operation_result(
            success=True,
            data=scripts,
            message="获取脚本列表成功"
        )
    except Exception as e:
        logger.error(f"获取脚本列表失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="获取脚本列表失败"
        )

@app.get("/scripts/{script_id}")
async def get_script(script_id: str):
    """获取单个脚本"""
    try:
        if script_id not in scripts_storage:
            raise HTTPException(status_code=404, detail="脚本不存在")
        
        script = scripts_storage[script_id]
        return create_operation_result(
            success=True,
            data=script,
            message="获取脚本成功"
        )
    except Exception as e:
        logger.error(f"获取脚本失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="获取脚本失败"
        )

@app.post("/scripts")
async def create_script(request: CreateScriptRequest):
    """创建脚本"""
    global script_counter
    try:
        script_counter += 1
        script_id = f"script_{script_counter}"
        
        now = datetime.now().isoformat()
        script = ScriptInfo(
            id=script_id,
            name=request.name,
            description=request.description,
            content=request.content,
            createdAt=now,
            updatedAt=now
        )
        
        scripts_storage[script_id] = script
        
        logger.info(f"创建脚本成功: {script_id}")
        return create_operation_result(
            success=True,
            data=script,
            message="脚本创建成功"
        )
    except Exception as e:
        logger.error(f"创建脚本失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="脚本创建失败"
        )

@app.put("/scripts/{script_id}")
async def update_script(script_id: str, request: UpdateScriptRequest):
    """更新脚本"""
    try:
        if script_id not in scripts_storage:
            raise HTTPException(status_code=404, detail="脚本不存在")
        
        script = scripts_storage[script_id]
        
        if request.name is not None:
            script.name = request.name
        if request.description is not None:
            script.description = request.description
        if request.content is not None:
            script.content = request.content
        
        script.updatedAt = datetime.now().isoformat()
        
        logger.info(f"更新脚本成功: {script_id}")
        return create_operation_result(
            success=True,
            data=script,
            message="脚本更新成功"
        )
    except Exception as e:
        logger.error(f"更新脚本失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="脚本更新失败"
        )

@app.delete("/scripts/{script_id}")
async def delete_script(script_id: str):
    """删除脚本"""
    try:
        if script_id not in scripts_storage:
            raise HTTPException(status_code=404, detail="脚本不存在")
        
        del scripts_storage[script_id]
        
        logger.info(f"删除脚本成功: {script_id}")
        return create_operation_result(
            success=True,
            message="脚本删除成功"
        )
    except Exception as e:
        logger.error(f"删除脚本失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="脚本删除失败"
        )

@app.post("/scripts/{script_id}/run")
async def run_script(script_id: str):
    """运行脚本"""
    try:
        if script_id not in scripts_storage:
            raise HTTPException(status_code=404, detail="脚本不存在")
        
        script = scripts_storage[script_id]
        
        # 更新脚本状态为运行中
        script.status = "running"
        script.updatedAt = datetime.now().isoformat()
        
        start_time = time.time()
        
        try:
            # 这里应该实际执行Python脚本
            # 为了演示，我们只是模拟执行
            import subprocess
            import tempfile
            import os
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script.content)
                temp_file = f.name
            
            # 执行脚本
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=30  # 30秒超时
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # 清理临时文件
            os.unlink(temp_file)
            
            # 更新脚本状态
            script.status = "completed" if result.returncode == 0 else "failed"
            script.runCount += 1
            script.lastRunTime = datetime.now().isoformat()
            script.updatedAt = script.lastRunTime
            
            run_result = ScriptRunResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                executionTime=execution_time
            )
            
            logger.info(f"脚本运行成功: {script_id}")
            return create_operation_result(
                success=True,
                data=run_result,
                message="脚本运行成功"
            )
            
        except subprocess.TimeoutExpired:
            script.status = "failed"
            script.updatedAt = datetime.now().isoformat()
            
            run_result = ScriptRunResult(
                success=False,
                error="脚本执行超时",
                executionTime=30000
            )
            
            logger.error(f"脚本运行超时: {script_id}")
            return create_operation_result(
                success=False,
                data=run_result,
                message="脚本运行超时"
            )
            
        except Exception as e:
            script.status = "failed"
            script.updatedAt = datetime.now().isoformat()
            
            run_result = ScriptRunResult(
                success=False,
                error=str(e),
                executionTime=int((time.time() - start_time) * 1000)
            )
            
            logger.error(f"脚本运行失败: {script_id}, 错误: {str(e)}")
            return create_operation_result(
                success=False,
                data=run_result,
                message="脚本运行失败"
            )
            
    except Exception as e:
        logger.error(f"运行脚本失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="运行脚本失败"
        )

@app.post("/scripts/import")
async def import_script(file: UploadFile = File(...)):
    """导入脚本"""
    global script_counter
    try:
        if not file.filename.endswith('.py'):
            raise HTTPException(status_code=400, detail="只能导入.py文件")
        
        content = await file.read()
        script_content = content.decode('utf-8')
        
        # 从文件名获取脚本名称
        script_name = file.filename.replace('.py', '')
        
        script_counter += 1
        script_id = f"script_{script_counter}"
        
        now = datetime.now().isoformat()
        script = ScriptInfo(
            id=script_id,
            name=script_name,
            description=f"从文件 {file.filename} 导入",
            content=script_content,
            createdAt=now,
            updatedAt=now
        )
        
        scripts_storage[script_id] = script
        
        logger.info(f"导入脚本成功: {script_id}")
        return create_operation_result(
            success=True,
            data=script,
            message="脚本导入成功"
        )
    except Exception as e:
        logger.error(f"导入脚本失败: {str(e)}")
        return create_operation_result(
            success=False,
            error=str(e),
            message="脚本导入失败"
        )

@app.get("/scripts/{script_id}/export")
async def export_script(script_id: str):
    """导出脚本"""
    try:
        if script_id not in scripts_storage:
            raise HTTPException(status_code=404, detail="脚本不存在")
        
        script = scripts_storage[script_id]
        
        # 返回脚本内容作为文件下载
        from fastapi.responses import Response
        
        return Response(
            content=script.content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={script.name}.py"}
        )
    except Exception as e:
        logger.error(f"导出脚本失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导出脚本失败")

if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    ) 