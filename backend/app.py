#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全新后端（服务端运行模式）
 - 使用 FastAPI 暴露 HTTP API
 - 在本进程内启动并管理内置测试服务器（通过 communicators.operation_multi_machine.MultiMachineOperation）
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

from communicators.operation_multi_machine import MultiMachineOperation
from config import config

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger("backend.app")

# 全局运行状态
server: Optional[MultiMachineOperation] = None
is_running = False
current_machine_id: Optional[str] = None
current_app_name: Optional[str] = None

# 脚本存储文件路径（从配置文件获取）
SCRIPT_STORAGE_FILE = config.SCRIPT_STORAGE_FILE
SCRIPT_COUNTER_FILE = config.SCRIPT_COUNTER_FILE

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

# 脚本存储管理类
class ScriptStorageManager:
    def __init__(self, storage_file: str, counter_file: str):
        self.storage_file = storage_file
        self.counter_file = counter_file
        self.scripts_storage: Dict[str, ScriptInfo] = {}
        self.script_counter = 0
        self._ensure_storage_dir()
        self._load_data()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        storage_dir = os.path.dirname(self.storage_file)
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
            logger.info(f"创建脚本存储目录: {storage_dir}")
    
    def _load_data(self):
        """从JSON文件加载脚本数据"""
        try:
            # 加载脚本存储
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    scripts_data = json.load(f)
                    # 将字典数据转换为ScriptInfo对象
                    for script_id, script_data in scripts_data.items():
                        self.scripts_storage[script_id] = ScriptInfo(**script_data)
                logger.info(f"从文件加载了 {len(self.scripts_storage)} 个脚本")
            else:
                logger.info("脚本存储文件不存在，使用空存储")
            
            # 加载脚本计数器
            if os.path.exists(self.counter_file):
                with open(self.counter_file, 'r', encoding='utf-8') as f:
                    counter_data = json.load(f)
                    self.script_counter = counter_data.get('counter', 0)
                logger.info(f"脚本计数器: {self.script_counter}")
            else:
                logger.info("脚本计数器文件不存在，使用默认值0")
                
        except Exception as e:
            logger.error(f"加载脚本数据失败: {e}")
            # 使用默认值
            self.scripts_storage = {}
            self.script_counter = 0
    
    def _save_data(self):
        """保存脚本数据到JSON文件"""
        try:
            # 确保存储目录存在
            self._ensure_storage_dir()
            
            # 保存脚本存储
            scripts_data = {}
            for script_id, script_info in self.scripts_storage.items():
                scripts_data[script_id] = script_info.model_dump()
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(scripts_data, f, ensure_ascii=False, indent=2)
            
            # 保存脚本计数器
            with open(self.counter_file, 'w', encoding='utf-8') as f:
                json.dump({'counter': self.script_counter}, f, ensure_ascii=False, indent=2)
                
            logger.info("脚本数据保存成功")
            
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
        
        now = datetime.now().isoformat()
        script_info = ScriptInfo(
            id=script_id,
            name=req.name,
            description=req.description,
            content=req.content,
            createdAt=now,
            updatedAt=now,
            target_machine_id=req.target_machine_id,
            target_app_name=req.target_app_name
        )
        
        self.scripts_storage[script_id] = script_info
        self._save_data()
        
        logger.info(f"创建脚本成功: {script_id} - {req.name}")
        return script_info
    
    def update_script(self, script_id: str, req: UpdateScriptRequest) -> Optional[ScriptInfo]:
        """更新脚本"""
        if script_id not in self.scripts_storage:
            return None
        
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
            script_info.content = req.content
        if req.target_machine_id is not None:
            script_info.target_machine_id = req.target_machine_id
        if req.target_app_name is not None:
            script_info.target_app_name = req.target_app_name
        
        script_info.updatedAt = datetime.now().isoformat()
        
        self._save_data()
        
        logger.info(f"更新脚本成功: {script_id}")
        return script_info
    
    def delete_script(self, script_id: str) -> bool:
        """删除脚本"""
        if script_id not in self.scripts_storage:
            return False
        
        script_name = self.scripts_storage[script_id].name
        del self.scripts_storage[script_id]
        self._save_data()
        
        logger.info(f"删除脚本成功: {script_id} - {script_name}")
        return True
    
    def update_script_status(self, script_id: str, status: str, run_count: int = None, last_run_time: str = None):
        """更新脚本状态"""
        if script_id not in self.scripts_storage:
            return False
        
        script_info = self.scripts_storage[script_id]
        script_info.status = status
        script_info.updatedAt = datetime.now().isoformat()
        
        if run_count is not None:
            script_info.runCount = run_count
        if last_run_time is not None:
            script_info.lastRunTime = last_run_time
        
        self._save_data()
        return True
    
    def backup_data(self, backup_dir: str = None):
        """备份脚本数据"""
        if not backup_dir:
            backup_dir = os.path.join(os.path.dirname(self.storage_file), "backup")
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 备份脚本存储文件
        backup_storage_file = os.path.join(backup_dir, f"scripts_storage_{timestamp}.json")
        if os.path.exists(self.storage_file):
            import shutil
            shutil.copy2(self.storage_file, backup_storage_file)
            logger.info(f"脚本存储备份到: {backup_storage_file}")
        
        # 备份计数器文件
        backup_counter_file = os.path.join(backup_dir, f"script_counter_{timestamp}.json")
        if os.path.exists(self.counter_file):
            import shutil
            shutil.copy2(self.counter_file, backup_counter_file)
            logger.info(f"脚本计数器备份到: {backup_counter_file}")

# 创建脚本存储管理器实例
script_manager = ScriptStorageManager(SCRIPT_STORAGE_FILE, SCRIPT_COUNTER_FILE)

app = FastAPI(title="AutoTest Backend (Server Mode)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
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
    return {"connected": is_running, "host": "0.0.0.0" if is_running else None, "port": config.DEFAULT_PORT if is_running else None, "mode": "embedded"}

@app.post("/connect")
def start(req: StartServerRequest):
    global server, is_running
    try:
        server = MultiMachineOperation(bind_host=config.DEFAULT_HOST, server_port=req.port)
        is_running = True
        return ok(message=f"内置测试服务器已启动 {config.DEFAULT_HOST}:{req.port}")
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

@app.delete("/machines/{machine_id}")
def disconnect_machine(machine_id: str):
    ensure_server()
    try:
        # 优先使用显式方法
        if hasattr(server, 'disconnect_machine') and callable(getattr(server, 'disconnect_machine')):
            try:
                getattr(server, 'disconnect_machine')(machine_id)
                return ok(message=f"机器 {machine_id} 已断开")
            except Exception as inner:
                # 回退到直接关闭连接
                pass
        # 回退方案：直接从服务器记录中移除并尝试关闭socket
        try:
            machines = getattr(server, 'machines', {})
            if machine_id in machines:
                info = machines.pop(machine_id)
                conn = None
                # 常见可能字段名
                for key in ['conn', 'socket', 'sock', 'connection']:
                    if isinstance(info, dict) and key in info:
                        conn = info[key]
                        break
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
                return ok(message=f"机器 {machine_id} 已断开")
            else:
                return err("断开失败", f"未找到机器 {machine_id}")
        except Exception as e2:
            return err("断开失败", str(e2))
    except Exception as e:
        return err("断开失败", str(e))

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

# 脚本管理（使用JSON文件持久化存储）
@app.get("/scripts")
def get_scripts():
    try:
        scripts = script_manager.get_all_scripts()
        return ok(scripts)
    except Exception as e:
        logger.error(f"获取脚本列表失败: {e}")
        return err("获取脚本列表失败", str(e))

@app.get("/scripts/{script_id}")
def get_script(script_id: str):
    try:
        script = script_manager.get_script(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="脚本不存在")
        return ok(script)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取脚本失败: {e}")
        return err("获取脚本失败", str(e))

@app.post("/scripts")
def create_script(req: CreateScriptRequest):
    try:
        script = script_manager.create_script(req)
        return ok(script, "脚本创建成功")
    except ValueError as e:
        return err("脚本创建失败", str(e))
    except Exception as e:
        logger.error(f"创建脚本失败: {e}")
        return err("脚本创建失败", str(e))

@app.put("/scripts/{script_id}")
def update_script(script_id: str, req: UpdateScriptRequest):
    try:
        script = script_manager.update_script(script_id, req)
        if not script:
            raise HTTPException(status_code=404, detail="脚本不存在")
        return ok(script, "脚本更新成功")
    except ValueError as e:
        return err("脚本更新失败", str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新脚本失败: {e}")
        return err("脚本更新失败", str(e))

@app.delete("/scripts/{script_id}")
def delete_script(script_id: str):
    try:
        if not script_manager.delete_script(script_id):
            raise HTTPException(status_code=404, detail="脚本不存在")
        return ok(message="脚本删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除脚本失败: {e}")
        return err("脚本删除失败", str(e))

@app.post("/scripts/{script_id}/run")
def run_script(script_id: str):
    try:
        script = script_manager.get_script(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="脚本不存在")
        
        # 更新脚本状态为运行中
        script_manager.update_script_status(script_id, "running")
        
        start = time.time()
        try:
            import subprocess, tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script.content)
                tmp = f.name
            
            result = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=config.SCRIPT_TIMEOUT)
            os.unlink(tmp)
            
            # 更新脚本状态和运行信息
            success = result.returncode == 0
            status = "completed" if success else "failed"
            run_count = script.runCount + 1
            last_run_time = datetime.now().isoformat()
            
            script_manager.update_script_status(script_id, status, run_count, last_run_time)
            
            execution_time = int((time.time() - start) * 1000)
            
            return ok({
                "success": success,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "executionTime": execution_time
            }, "脚本运行完成")
            
        except subprocess.TimeoutExpired:
            script_manager.update_script_status(script_id, "failed")
            return err("脚本执行超时")
        except Exception as e:
            script_manager.update_script_status(script_id, "failed")
            return err("脚本运行失败", str(e))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"运行脚本失败: {e}")
        return err("脚本运行失败", str(e))

@app.post("/scripts/import")
def import_script(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.py'):
            raise HTTPException(status_code=400, detail="只能导入.py文件")
        
        content = file.file.read().decode('utf-8')
        name = file.filename[:-3]
        
        # 创建导入请求
        req = CreateScriptRequest(
            name=name,
            description=f"从文件 {file.filename} 导入",
            content=content
        )
        
        script = script_manager.create_script(req)
        return ok(script, "脚本导入成功")
        
    except ValueError as e:
        return err("脚本导入失败", str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入脚本失败: {e}")
        return err("脚本导入失败", str(e))

@app.get("/scripts/{script_id}/export")
def export_script(script_id: str):
    try:
        script = script_manager.get_script(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="脚本不存在")
        
        return Response(
            content=script.content, 
            media_type="text/plain", 
            headers={"Content-Disposition": f"attachment; filename={script.name}.py"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出脚本失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出脚本失败: {str(e)}")

@app.post("/scripts/backup")
def backup_scripts():
    """备份脚本数据"""
    try:
        backup_dir = os.path.join(os.path.dirname(SCRIPT_STORAGE_FILE), "backup")
        script_manager.backup_data(backup_dir)
        return ok(message="脚本数据备份成功")
    except Exception as e:
        logger.error(f"备份脚本数据失败: {e}")
        return err("备份脚本数据失败", str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8080, reload=True)

