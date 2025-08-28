#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全新后端（服务端运行模式）
 - 使用 FastAPI 暴露 HTTP API
 - 在本进程内启动并管理内置测试服务器（通过 communicators.operation_multi_machine.MultiMachineOperation）
 - 提供多机器/多应用的管理与操作端点
 - 提供脚本管理端点
"""

import os
import sys
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

from communicators.operation_multi_machine import MultiMachineOperation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("backend.app")

# 全局运行状态
server: Optional[MultiMachineOperation] = None
is_running = False
current_machine_id: Optional[str] = None
current_app_name: Optional[str] = None

DEFAULT_PORT = int(os.getenv("TEST_SERVER_PORT", "8889"))

class OperationResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None

class StartServerRequest(BaseModel):
    port: int = Field(DEFAULT_PORT, description="内置测试服务器监听端口")

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
    content: str
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

scripts_storage: Dict[str, ScriptInfo] = {}
script_counter = 0

app = FastAPI(title="AutoTest Backend (Server Mode)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ok(data: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> OperationResult:
    return OperationResult(success=True, data=data, message=message)

def err(message: str, error: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> OperationResult:
    return OperationResult(success=False, error=error or message, message=message, data=data)

def ensure_server():
    if not (is_running and server):
        raise HTTPException(status_code=400, detail="测试服务器未启动")

@app.get("/")
def root():
    return {"name": "AutoTest Backend", "mode": "server-embedded", "running": is_running}

@app.get("/status")
def status():
    return {"connected": is_running, "host": "0.0.0.0" if is_running else None, "port": DEFAULT_PORT if is_running else None, "mode": "embedded"}

@app.post("/connect")
def start(req: StartServerRequest):
    global server, is_running, DEFAULT_PORT
    try:
        DEFAULT_PORT = req.port
        server = MultiMachineOperation(bind_host="0.0.0.0", server_port=req.port)
        is_running = True
        return ok(message=f"内置测试服务器已启动 0.0.0.0:{req.port}")
    except Exception as e:
        server = None
        is_running = False
        return err("测试服务器启动失败", str(e))

@app.post("/disconnect")
def stop():
    global server, is_running
    try:
        if server:
            server.close()
        server = None
        is_running = False
        return ok(message="内置测试服务器已停止")
    except Exception as e:
        return err("停止失败", str(e))

@app.get("/machines")
def machines():
    ensure_server()
    try:
        mids = server.get_available_machines()
        return ok({"machines": [{"id": mid, "address": f"机器_{mid}", "status": "connected", "apps": []} for mid in mids]})
    except Exception as e:
        return err("获取机器列表失败", str(e))

@app.get("/apps")
def apps(machine_id: Optional[str] = None):
    ensure_server()
    try:
        apps = server.get_available_apps(machine_id)
        mapped = [{"id": f"{a['machine_id']}:{a['name']}", "name": a['name'], "machine_id": a['machine_id'], "status": "running", "region": a.get('region')} for a in apps]
        return ok({"apps": mapped})
    except Exception as e:
        return err("获取应用列表失败", str(e))

@app.post("/set-target")
def set_target(req: MachineAppTargetRequest):
    ensure_server()
    try:
        if server.set_target(req.machine_id, req.app_name):
            global current_machine_id, current_app_name
            current_machine_id = req.machine_id
            current_app_name = req.app_name
            return ok({"machine_id": req.machine_id, "app_name": req.app_name}, "设置目标成功")
        return err("设置目标失败")
    except Exception as e:
        return err("设置目标失败", str(e))

@app.get("/current-target")
def current_target():
    ensure_server()
    return ok({"machine_id": current_machine_id, "app_name": current_app_name})

@app.post("/screenshot")
def screenshot(region: Optional[str] = None):
    ensure_server()
    try:
        reg = None
        if region:
            parts = [int(x) for x in region.split(',')]
            if len(parts) != 4:
                return err("区域参数格式错误，应为 x,y,width,height")
            reg = parts
        res = server.get_screenshot(reg)
        return OperationResult(**res)
    except Exception as e:
        return err("获取截图失败", str(e))

@app.post("/click-element")
def click_element(req: ElementOperationRequest):
    ensure_server()
    try:
        cmds = server.click_element(req.path, req.roles)
        return ok({"commands": cmds}, "元素点击成功")
    except Exception as e:
        return err("元素点击失败", str(e))

@app.post("/click-image")
def click_image(req: ImageOperationRequest):
    ensure_server()
    try:
        res = server.click_image(req.imagePath, req.threshold)
        return OperationResult(**res)
    except Exception as e:
        return err("图片点击失败", str(e))

@app.post("/drag-to")
def drag_to(req: DragRequest):
    ensure_server()
    try:
        cmds = server.drag_to(req.startX, req.startY, req.endX, req.endY) if hasattr(server, 'drag_to') else []
        return ok({"commands": cmds}, "拖拽操作成功")
    except Exception as e:
        return err("拖拽操作失败", str(e))

@app.post("/input-text")
def input_text(req: TextInputRequest):
    ensure_server()
    try:
        cmds = server.input_text(req.elementPath, req.text) if hasattr(server, 'input_text') else []
        return ok({"commands": cmds}, "文本输入成功")
    except Exception as e:
        return err("文本输入失败", str(e))

@app.post("/hotkey")
def hotkey(req: HotkeyRequest):
    ensure_server()
    try:
        res = server.hotkey(req.keys)
        return OperationResult(**res)
    except Exception as e:
        return err("快捷键操作失败", str(e))

# 脚本管理（与原功能等价重建）
@app.get("/scripts")
def get_scripts():
    return ok(list(scripts_storage.values()))

@app.get("/scripts/{script_id}")
def get_script(script_id: str):
    if script_id not in scripts_storage:
        raise HTTPException(status_code=404, detail="脚本不存在")
    return ok(scripts_storage[script_id])

@app.post("/scripts")
def create_script(req: CreateScriptRequest):
    global script_counter
    script_counter += 1
    sid = f"script_{script_counter}"
    now = datetime.now().isoformat()
    s = ScriptInfo(id=sid, name=req.name, description=req.description, content=req.content, createdAt=now, updatedAt=now,
                   target_machine_id=req.target_machine_id, target_app_name=req.target_app_name)
    scripts_storage[sid] = s
    return ok(s, "脚本创建成功")

@app.put("/scripts/{script_id}")
def update_script(script_id: str, req: UpdateScriptRequest):
    if script_id not in scripts_storage:
        raise HTTPException(status_code=404, detail="脚本不存在")
    s = scripts_storage[script_id]
    if req.name is not None:
        s.name = req.name
    if req.description is not None:
        s.description = req.description
    if req.content is not None:
        s.content = req.content
    s.updatedAt = datetime.now().isoformat()
    return ok(s, "脚本更新成功")

@app.delete("/scripts/{script_id}")
def delete_script(script_id: str):
    if script_id not in scripts_storage:
        raise HTTPException(status_code=404, detail="脚本不存在")
    del scripts_storage[script_id]
    return ok(message="脚本删除成功")

@app.post("/scripts/{script_id}/run")
def run_script(script_id: str):
    if script_id not in scripts_storage:
        raise HTTPException(status_code=404, detail="脚本不存在")
    s = scripts_storage[script_id]
    start = time.time()
    try:
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(s.content)
            tmp = f.name
        result = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=30)
        os.unlink(tmp)
        s.status = "completed" if result.returncode == 0 else "failed"
        s.runCount += 1
        s.lastRunTime = datetime.now().isoformat()
        s.updatedAt = s.lastRunTime
        return ok(ScriptRunResult(success=result.returncode == 0, output=result.stdout, error=result.stderr if result.returncode != 0 else None, executionTime=int((time.time()-start)*1000)).model_dump(), "脚本运行完成")
    except subprocess.TimeoutExpired:
        s.status = "failed"
        s.updatedAt = datetime.now().isoformat()
        return err("脚本执行超时")
    except Exception as e:
        s.status = "failed"
        s.updatedAt = datetime.now().isoformat()
        return err("脚本运行失败", str(e))

@app.post("/scripts/import")
def import_script(file: UploadFile = File(...)):
    global script_counter
    if not file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="只能导入.py文件")
    content = file.file.read().decode('utf-8')
    name = file.filename[:-3]
    script_counter += 1
    sid = f"script_{script_counter}"
    now = datetime.now().isoformat()
    s = ScriptInfo(id=sid, name=name, description=f"从文件 {file.filename} 导入", content=content, createdAt=now, updatedAt=now)
    scripts_storage[sid] = s
    return ok(s, "脚本导入成功")

@app.get("/scripts/{script_id}/export")
def export_script(script_id: str):
    if script_id not in scripts_storage:
        raise HTTPException(status_code=404, detail="脚本不存在")
    s = scripts_storage[script_id]
    return Response(content=s.content, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename={s.name}.py"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8080, reload=True)

