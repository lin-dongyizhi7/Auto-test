#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本管理路由
提供脚本的增删改查、运行、导入导出等端点
"""

import os
import json
import logging
from typing import Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, Field

from communicators.test_communicator import TestMachineCommunicator
from communicators.operation_multi_machine import MultiMachineOperation
from config import config

logger = logging.getLogger("backend.routes.script")

# 创建路由器
router = APIRouter(prefix="/api/scripts", tags=["脚本管理"])

# 全局状态（这些变量将在主应用中初始化）
communicator: Optional[TestMachineCommunicator] = None
operation: Optional[MultiMachineOperation] = None
is_running = False
current_machine_id: Optional[str] = None
current_app_name: Optional[str] = None

def set_global_state(comm, op, running, machine_id=None, app_name=None):
    """设置全局状态变量"""
    global communicator, operation, is_running, current_machine_id, current_app_name
    communicator = comm
    operation = op
    is_running = running
    current_machine_id = machine_id
    current_app_name = app_name

class OperationResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

class ScriptInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    path: str
    content: Optional[str] = None
    createdAt: str
    updatedAt: str
    lastRunTime: Optional[str] = None
    runCount: int = 0
    target_app_name: Optional[str] = None
    last_run_machine_id: Optional[str] = None

class CreateScriptRequest(BaseModel):
    name: str
    description: Optional[str] = None
    content: str
    target_app_name: Optional[str] = None

class UpdateScriptRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    target_app_name: Optional[str] = None

class ScriptRunResult(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    executionTime: Optional[int] = None

class PythonScriptRunRequest(BaseModel):
    script_content: str
    target_machine_ip: Optional[str] = None
    target_app_name: Optional[str] = None

class PythonScriptConvertRequest(BaseModel):
    script_content: str
    script_name: str
    description: Optional[str] = None
    target_machine_ip: Optional[str] = None
    target_app_name: Optional[str] = None

# 脚本存储管理类
class ScriptStorageManager:
    def __init__(self, info_file: str, store_dir: str):
        self.info_file = info_file
        self.store_dir = store_dir
        self.scripts_storage: dict[str, ScriptInfo] = {}
        self.script_counter = 0
        self._ensure_storage_dir()
        self._load_data()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        storage_dir = os.path.dirname(self.info_file)
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
            logger.info(f"创建脚本存储目录: {storage_dir}")
        if not os.path.exists(self.store_dir):
            os.makedirs(self.store_dir, exist_ok=True)
            logger.info(f"创建脚本内容目录: {self.store_dir}")
    
    def _load_data(self):
        """从JSON文件加载脚本数据"""
        try:
            if os.path.exists(self.info_file):
                with open(self.info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                self.script_counter = int(info.get('counter', 0))
                storage_list = info.get('storage', []) or []
                for item in storage_list:
                    # 兼容老字段：若存在 content 则保留；但主要以 path 为准
                    self.scripts_storage[item['id']] = ScriptInfo(** item)
                logger.info(f"从文件加载了 {len(self.scripts_storage)} 个脚本，计数器 {self.script_counter}")
            else:
                logger.info("脚本信息文件不存在，使用空存储")
        except Exception as e:
            logger.error(f"加载脚本数据失败: {e}")
            # 使用默认值
            self.scripts_storage = {}
            self.script_counter = 0
    
    def _save_data(self):
        """保存脚本数据到JSON文件"""
        try:
            self._ensure_storage_dir()
            storage_list = []
            for script_id, script_info in self.scripts_storage.items():
                data = script_info.model_dump()
                # 避免把 content 大字段写入 info 文件
                if 'content' in data:
                    data.pop('content')
                storage_list.append(data)
            info_obj = {"counter": self.script_counter, "storage": storage_list}
            with open(self.info_file, 'w', encoding='utf-8') as f:
                json.dump(info_obj, f, ensure_ascii=False, indent=2)
            logger.info("脚本元数据保存成功")
        except Exception as e:
            logger.error(f"保存脚本数据失败: {e}")
            raise
    
    def get_all_scripts(self) -> list[ScriptInfo]:
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
        
        # 创建脚本信息
        now = datetime.now().isoformat()
        # 为脚本确定存储路径（使用 .json 作为内容文件扩展名）
        file_name = f"{script_id}.json"
        file_path = os.path.join(self.store_dir, file_name)
        # 写入脚本内容到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(req.content)
        script_info = ScriptInfo(
            id=script_id,
            name=req.name,
            description=req.description,
            path=file_path,
            createdAt=now,
            updatedAt=now,
            target_app_name=req.target_app_name
        )
        
        # 保存到存储
        self.scripts_storage[script_id] = script_info
        self._save_data()
        
        logger.info(f"创建脚本成功: {script_id}")
        return script_info
    
    def update_script(self, script_id: str, req: UpdateScriptRequest) -> ScriptInfo:
        """更新脚本"""
        if script_id not in self.scripts_storage:
            raise ValueError(f"脚本 {script_id} 不存在")
        
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
            # 写回内容文件
            with open(script_info.path, 'w', encoding='utf-8') as f:
                f.write(req.content)
        if req.target_app_name is not None:
            script_info.target_app_name = req.target_app_name
        
        script_info.updatedAt = datetime.now().isoformat()
        
        # 保存到存储
        self._save_data()
        
        logger.info(f"更新脚本成功: {script_id}")
        return script_info
    
    def delete_script(self, script_id: str) -> bool:
        """删除脚本"""
        if script_id not in self.scripts_storage:
            return False
        
        # 删除内容文件
        try:
            file_path = self.scripts_storage[script_id].path
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as _:
            pass
        del self.scripts_storage[script_id]
        self._save_data()
        
        logger.info(f"删除脚本成功: {script_id}")
        return True
    
    def update_script_status(self, script_id: str, status: str, last_run_time: Optional[str] = None):
        """兼容旧接口：不再保存状态，仅更新时间与计数"""
        if script_id not in self.scripts_storage:
            return
        
        script_info = self.scripts_storage[script_id]
        
        if last_run_time:
            script_info.lastRunTime = last_run_time
            script_info.runCount += 1
        
        self._save_data()
    
    def import_script(self, file_content: str, filename: str) -> ScriptInfo:
        """导入脚本文件"""
        # 检查脚本大小
        if len(file_content.encode('utf-8')) > config.SCRIPT_MAX_SIZE:
            raise ValueError(f"脚本内容过大，最大允许 {config.SCRIPT_MAX_SIZE} 字节")
        
        # 从文件名提取脚本名称（去掉.py扩展名）
        script_name = os.path.splitext(filename)[0]
        
        self.script_counter += 1
        script_id = f"script_{self.script_counter}"
        
        # 创建脚本内容文件路径
        script_file_path = os.path.join(self.store_dir, f"{script_id}.json")
        
        # 创建脚本信息
        now = datetime.now().isoformat()
        script_info = ScriptInfo(
            id=script_id,
            name=script_name,
            description=f"从 {filename} 导入的脚本",
            content=file_content,
            path=script_file_path,
            createdAt=now,
            updatedAt=now,
            lastRunTime=None,
            runCount=0,
            target_app_name=""
        )
        
        # 保存脚本内容到文件
        try:
            with open(script_file_path, 'w', encoding='utf-8') as f:
                json.dump({"content": file_content}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存脚本内容文件失败: {e}")
            raise ValueError(f"保存脚本内容失败: {str(e)}")
        
        # 存储脚本信息
        self.scripts_storage[script_id] = script_info
        self._save_data()
        
        logger.info(f"成功导入脚本: {script_id} ({script_name})")
        return script_info
    
    def export_script(self, script_id: str) -> str:
        """导出脚本内容"""
        if script_id not in self.scripts_storage:
            raise ValueError(f"脚本 {script_id} 不存在")
        
        script_info = self.scripts_storage[script_id]
        
        # 从脚本内容文件读取
        try:
            if os.path.exists(script_info.path):
                with open(script_info.path, 'r', encoding='utf-8') as f:
                    script_data = json.load(f)
                    return script_data.get('content', '')
            else:
                # 如果文件不存在，返回脚本信息中的内容
                return script_info.content or ''
        except Exception as e:
            logger.error(f"读取脚本内容失败: {e}")
            raise ValueError(f"读取脚本内容失败: {str(e)}")

# 初始化脚本存储管理器
script_manager = ScriptStorageManager(config.SCRIPT_INFO_FILE, config.SCRIPTS_STORE_DIR)

@router.get("", response_model=OperationResult)
async def get_scripts():
    """获取所有脚本"""
    try:
        scripts = script_manager.get_all_scripts()
        return OperationResult(
            success=True,
            data={"scripts": [script.model_dump() for script in scripts]}
        )
    except Exception as e:
        logger.error(f"获取脚本列表失败: {e}")
        return OperationResult(
            success=False,
            error=f"获取脚本列表失败: {str(e)}"
        )

@router.get("/{script_id}", response_model=OperationResult)
async def get_script(script_id: str):
    """获取单个脚本"""
    try:
        script = script_manager.get_script(script_id)
        if not script:
            return OperationResult(
                success=False,
                error="脚本不存在"
            )
        # 读取脚本文件内容并填充
        try:
            if os.path.exists(script.path):
                with open(script.path, 'r', encoding='utf-8') as f:
                    script.content = f.read()
        except Exception as _:
            script.content = script.content or ""

        return OperationResult(
            success=True,
            data=script.model_dump()
        )
    except Exception as e:
        logger.error(f"获取脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"获取脚本失败: {str(e)}"
        )

@router.post("", response_model=OperationResult)
async def create_script(request: CreateScriptRequest):
    """创建新脚本"""
    try:
        script = script_manager.create_script(request)
        return OperationResult(
            success=True,
            data=script.model_dump()
        )
    except Exception as e:
        logger.error(f"创建脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"创建脚本失败: {str(e)}"
        )

@router.put("/{script_id}", response_model=OperationResult)
async def update_script(script_id: str, request: UpdateScriptRequest):
    """更新脚本"""
    try:
        script = script_manager.update_script(script_id, request)
        return OperationResult(
            success=True,
            data=script.model_dump()
        )
    except Exception as e:
        logger.error(f"更新脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"更新脚本失败: {str(e)}"
        )

@router.delete("/{script_id}", response_model=OperationResult)
async def delete_script(script_id: str):
    """删除脚本"""
    try:
        success = script_manager.delete_script(script_id)
        if success:
            return OperationResult(
                success=True,
                message="脚本删除成功"
            )
        else:
            return OperationResult(
                success=False,
                error="脚本不存在"
            )
    except Exception as e:
        logger.error(f"删除脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"删除脚本失败: {str(e)}"
        )

@router.post("/{script_id}/run", response_model=OperationResult)
async def run_script(script_id: str, machine_id: Optional[str] = None):
    """运行脚本"""
    global operation

    try:
        script = script_manager.get_script(script_id)
        if not script:
            return OperationResult(
                success=False,
                error="脚本不存在"
            )
        
        # 更新脚本状态
        script_manager.update_script_status(script_id, "running", datetime.now().isoformat())
        # 记录本次运行机器
        if machine_id:
            script.last_run_machine_id = machine_id
            script.updatedAt = datetime.now().isoformat()
            # 持久化到文件
            script_manager._save_data()
        
        # 这里应该实现脚本执行逻辑
        operation.run_script_from_file(script.path)

        # 暂时返回成功
        return OperationResult(
            success=True,
            message="脚本执行成功"
        )
        
    except Exception as e:
        logger.error(f"运行脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"运行脚本失败: {str(e)}"
        )

@router.post("/import", response_model=OperationResult)
async def import_script(file: UploadFile = File(...)):
    """导入脚本文件"""
    try:
        # 检查文件类型
        if not file.filename.endswith('.py'):
            return OperationResult(
                success=False,
                error="只支持导入 .py 文件"
            )
        
        # 读取文件内容
        content = await file.read()
        file_content = content.decode('utf-8')
        
        # 导入脚本
        script = script_manager.import_script(file_content, file.filename)
        
        return OperationResult(
            success=True,
            data=script.model_dump(),
            message=f"脚本 {script.name} 导入成功"
        )
        
    except Exception as e:
        logger.error(f"导入脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"导入脚本失败: {str(e)}"
        )

@router.get("/{script_id}/export")
async def export_script(script_id: str):
    """导出脚本文件"""
    try:
        # 获取脚本内容
        script_content = script_manager.export_script(script_id)
        script_info = script_manager.get_script(script_id)
        
        if not script_info:
            return OperationResult(
                success=False,
                error="脚本不存在"
            )
        
        # 创建响应
        return Response(
            content=script_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={script_info.name}.py"
            }
        )
        
    except Exception as e:
        logger.error(f"导出脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"导出脚本失败: {str(e)}"
        )

@router.post("/python/run", response_model=OperationResult)
async def run_python_script(request: PythonScriptRunRequest):
    """运行Python脚本"""
    global operation

    try:
        if not operation:
            return OperationResult(
                success=False,
                error="操作引擎未初始化"
            )
        
        logger.info("开始执行Python脚本")
        
        # 调用operation_multi_machine中的run_python_script方法
        result = operation.run_python_script(
            script_content=request.script_content,
            target_machine_id=request.target_machine_ip,
            target_app_name=request.target_app_name
        )
        
        if result.get("success"):
            logger.info("Python脚本执行成功")
            return OperationResult(
                success=True,
                data=result.get("data"),
                message="Python脚本执行成功"
            )
        else:
            error_msg = result.get("error", "Python脚本执行失败")
            logger.error(f"Python脚本执行失败: {error_msg}")
            return OperationResult(
                success=False,
                error=error_msg
            )
        
    except Exception as e:
        logger.error(f"运行Python脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"运行Python脚本失败: {str(e)}"
        )

@router.post("/python/validate", response_model=OperationResult)
async def validate_python_script(request: PythonScriptRunRequest):
    """验证Python脚本语法"""
    global operation

    try:
        if not operation:
            return OperationResult(
                success=False,
                error="操作引擎未初始化"
            )
        
        # 调用operation_multi_machine中的validate_python_script方法
        result = operation.validate_python_script(request.script_content)
        
        if result.get("success"):
            return OperationResult(
                success=True,
                data=result.get("data"),
                message="Python脚本语法正确"
            )
        else:
            error_msg = result.get("error", "Python脚本语法错误")
            return OperationResult(
                success=False,
                error=error_msg
            )
        
    except Exception as e:
        logger.error(f"验证Python脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"验证Python脚本失败: {str(e)}"
        )

@router.post("/python/convert", response_model=OperationResult)
async def convert_python_script(request: PythonScriptConvertRequest):
    """将Python脚本转换为JSON脚本并保存"""
    global operation

    try:
        if not operation:
            return OperationResult(
                success=False,
                error="操作引擎未初始化"
            )
        
        logger.info("开始转换Python脚本为JSON脚本")
        
        # 解析Python脚本为JSON格式
        json_script = operation._parse_python_script(
            request.script_content, 
            request.target_machine_ip, 
            request.target_app_name
        )
        
        if not json_script.get("success"):
            return OperationResult(
                success=False,
                error=json_script.get("error", "Python脚本解析失败")
            )
        
        script_data = json_script["data"]
        
        # 将解析后的JSON脚本保存为JSON脚本
        json_content = json.dumps(script_data, ensure_ascii=False, indent=2)
        
        # 创建JSON脚本
        create_request = CreateScriptRequest(
            name=request.script_name,
            description=request.description or f"从Python脚本转换: {request.script_name}",
            content=json_content,
            target_app_name=script_data.get("target_app_name")
        )
        
        # 保存脚本
        saved_script = script_manager.create_script(create_request)
        
        logger.info(f"Python脚本转换成功，保存为JSON脚本: {saved_script.id}")
        
        return OperationResult(
            success=True,
            data=saved_script.model_dump(),
            message=f"Python脚本已成功转换为JSON脚本: {saved_script.name}"
        )
        
    except Exception as e:
        logger.error(f"转换Python脚本失败: {e}")
        return OperationResult(
            success=False,
            error=f"转换Python脚本失败: {str(e)}"
        )
