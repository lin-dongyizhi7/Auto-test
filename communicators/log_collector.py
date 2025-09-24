#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志收集器
负责收集测试机端的日志并同步到后端
"""

import json
import logging
import requests
import threading
import time
import queue
from typing import Dict, List, Optional
from datetime import datetime
from .config import get_security_config

class LogCollector:
    """日志收集器"""
    
    def __init__(self, machine_id: str, backend_url: str = "http://localhost:8080"):
        self.machine_id = machine_id
        self.backend_url = backend_url.rstrip('/')
        self.log_queue = queue.Queue()
        self.is_running = False
        self.sync_thread = None
        self.logger = logging.getLogger(f"log_collector.{machine_id}")
        
        # 安全配置
        sec = get_security_config()
        self._enable_encryption = bool(sec.get("enable_encryption"))
        self._shared_secret = sec.get("shared_secret") or ""
        
        # 设置日志级别
        self.logger.setLevel(logging.INFO)
        
    def start(self):
        """启动日志收集器"""
        if self.is_running:
            return
            
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        self.logger.info("日志收集器已启动")
        
    def stop(self):
        """停止日志收集器"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        self.logger.info("日志收集器已停止")
        
    def add_log(self, level: str, message: str, source: str = "system"):
        """添加日志条目"""
        log_entry = {
            "level": level,
            "message": message,
            "source": source,
            "machine_id": self.machine_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            self.log_queue.put_nowait(log_entry)
        except queue.Full:
            self.logger.warning("日志队列已满，丢弃日志条目")
            
    def _sync_loop(self):
        """同步循环"""
        while self.is_running:
            try:
                # 收集一批日志
                logs = []
                while len(logs) < 10 and not self.log_queue.empty():
                    try:
                        log = self.log_queue.get_nowait()
                        logs.append(log)
                    except queue.Empty:
                        break
                
                # 如果有日志，发送到后端
                if logs:
                    self._send_logs_to_backend(logs)
                    
                time.sleep(1)  # 每秒同步一次
                
            except Exception as e:
                self.logger.error(f"日志同步循环异常: {e}")
                time.sleep(5)  # 出错时等待5秒再重试
                
    def _send_logs_to_backend(self, logs: List[Dict]):
        """发送日志到后端"""
        try:
            url = f"{self.backend_url}/api/logs/sync"
            
            for log in logs:
                response = requests.post(
                    url,
                    json=log,
                    timeout=5
                )
                
                if response.status_code == 200:
                    self.logger.debug(f"日志同步成功: {log['message'][:50]}...")
                else:
                    self.logger.warning(f"日志同步失败: {response.status_code}")
                    
        except requests.exceptions.RequestException as e:
            self.logger.error(f"发送日志到后端失败: {e}")
        except Exception as e:
            self.logger.error(f"日志同步异常: {e}")

class TestedMachineLogHandler(logging.Handler):
    """测试机日志处理器"""
    
    def __init__(self, log_collector: LogCollector):
        super().__init__()
        self.log_collector = log_collector
        
    def emit(self, record):
        """发送日志记录"""
        try:
            # 格式化日志消息
            message = self.format(record)
            
            # 确定日志级别
            level_map = {
                logging.DEBUG: "DEBUG",
                logging.INFO: "INFO", 
                logging.WARNING: "WARNING",
                logging.ERROR: "ERROR",
                logging.CRITICAL: "CRITICAL"
            }
            level = level_map.get(record.levelno, "INFO")
            
            # 添加到收集器
            self.log_collector.add_log(level, message, "python_logger")
            
        except Exception as e:
            # 避免日志处理器本身出错导致递归
            pass

def setup_machine_logging(machine_id: str, backend_url: str = "http://localhost:8080") -> LogCollector:
    """设置测试机日志收集"""
    # 创建日志收集器
    collector = LogCollector(machine_id, backend_url)
    collector.start()
    
    # 创建日志处理器
    handler = TestedMachineLogHandler(collector)
    handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # 添加到根日志记录器
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    return collector

# 全局日志收集器实例
_global_collector: Optional[LogCollector] = None

def get_global_collector() -> Optional[LogCollector]:
    """获取全局日志收集器"""
    return _global_collector

def init_global_logging(machine_id: str, backend_url: str = "http://localhost:8080"):
    """初始化全局日志收集"""
    global _global_collector
    if _global_collector is None:
        _global_collector = setup_machine_logging(machine_id, backend_url)
    return _global_collector

def cleanup_global_logging():
    """清理全局日志收集"""
    global _global_collector
    if _global_collector:
        _global_collector.stop()
        _global_collector = None
