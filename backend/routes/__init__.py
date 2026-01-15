#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路由模块包
包含所有API端点的路由定义
"""

from .server import router as server_router
from .machine import router as machine_router
from .operation import router as operation_router
from .script import router as script_router

__all__ = [
    'server_router',
    'machine_router', 
    'operation_router',
    'script_router'
]
