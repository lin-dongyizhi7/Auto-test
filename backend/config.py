#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端配置文件
"""

import os

# 基础配置
class Config:
    # 测试服务器配置
    DEFAULT_PORT = int(os.getenv("TEST_SERVER_PORT", "8888"))
    DEFAULT_HOST = os.getenv("TEST_SERVER_HOST", "0.0.0.0")
    
    # 脚本存储配置（新）
    SCRIPT_STORAGE_DIR = os.getenv("SCRIPT_STORAGE_DIR", os.path.dirname(__file__))
    SCRIPTS_STORE_DIR = os.path.join(SCRIPT_STORAGE_DIR, "scripts_store")
    SCRIPT_INFO_FILE = os.path.join(SCRIPT_STORAGE_DIR, "script_info.json")
    
    # 脚本执行配置
    SCRIPT_TIMEOUT = int(os.getenv("SCRIPT_TIMEOUT", "30"))  # 脚本执行超时时间（秒）
    # 使用可直接转为 int 的默认值（1MB = 1048576 字节）
    SCRIPT_MAX_SIZE = int(os.getenv("SCRIPT_MAX_SIZE", "1048576"))  # 脚本最大大小（字节）
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 安全配置
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # 性能配置
    MAX_CONCURRENT_SCRIPTS = int(os.getenv("MAX_CONCURRENT_SCRIPTS", "5"))

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "WARNING"
    SCRIPT_TIMEOUT = 60
    MAX_CONCURRENT_SCRIPTS = 10

# 测试环境配置
class TestingConfig(Config):
    TESTING = True
    SCRIPT_STORAGE_DIR = "/tmp/autotest_scripts"
    SCRIPT_TIMEOUT = 10

# 根据环境变量选择配置
def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()

# 获取当前配置
config = get_config()
