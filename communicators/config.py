#!/usr/bin/env python3
"""
多机器通信系统配置文件

这个文件包含了系统的各种配置参数，可以根据实际环境进行调整。
"""

import os
from typing import Dict, List

# 网络配置
NETWORK_CONFIG = {
    # 测试服务器配置
    "test_server": {
        "host": "0.0.0.0",  # 测试服务器监听地址
        "port": 8888,        # 测试服务器端口
        "max_connections": 10,  # 最大连接数
        "timeout": 30,       # 连接超时时间（秒）
    },
    
    # 被测试机器配置
    "tested_machine": {
        "bind_host": "0.0.0.0",  # 绑定地址
        "port": 8888,            # 监听端口
        "max_clients": 5,         # 最大客户端连接数
    },
    
    # 通信配置
    "communication": {
        "buffer_size": 4096 * 1024,  # 缓冲区大小（字节）
        "heartbeat_interval": 30,     # 心跳间隔（秒）
        "reconnect_attempts": 3,      # 重连尝试次数
        "reconnect_delay": 5,         # 重连延迟（秒）
    }
}

# 应用配置
APP_CONFIG = {
    # 默认监控的应用列表
    "default_apps": [
        "calculator",    # 计算器
        "gedit",        # 文本编辑器
        "firefox",      # 浏览器
        "terminal",     # 终端
    ],
    
    # 应用特定配置
    "app_specific": {
        "calculator": {
            "cache_capacity": 30,
            "screenshot_region": None,  # None表示全屏
        },
        "gedit": {
            "cache_capacity": 50,
            "screenshot_region": None,
        },
        "firefox": {
            "cache_capacity": 100,
            "screenshot_region": None,
        },
        "terminal": {
            "cache_capacity": 20,
            "screenshot_region": None,
        }
    }
}

# 缓存配置
CACHE_CONFIG = {
    "default_capacity": 50,      # 默认缓存容量
    "max_capacity": 200,         # 最大缓存容量
    "cleanup_interval": 300,     # 缓存清理间隔（秒）
    "ttl": 3600,                # 缓存项生存时间（秒）
}

# 事件配置
EVENT_CONFIG = {
    "max_history": 1000,         # 最大事件历史记录数
    "sync_interval": 1,          # 事件同步间隔（秒）
    "event_types": [
        "machine_connected",     # 机器连接
        "machine_disconnected",  # 机器断开
        "app_launched",          # 应用启动
        "app_closed",            # 应用关闭
        "command_executed",      # 命令执行
        "screenshot_taken",      # 截图获取
        "element_found",         # 元素查找
        "error_occurred",        # 错误发生
    ]
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",             # 日志级别
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "communicator.log",  # 日志文件
    "max_size": 10 * 1024 * 1024,  # 最大日志文件大小（字节）
    "backup_count": 5,          # 备份文件数量
}

# 安全配置
SECURITY_CONFIG = {
    "enable_auth": False,        # 是否启用认证
    "allowed_hosts": [],         # 允许的主机列表（空表示允许所有）
    "max_request_size": 10 * 1024 * 1024,  # 最大请求大小（字节）
    "rate_limit": 100,           # 速率限制（请求/分钟）
}

# 性能配置
PERFORMANCE_CONFIG = {
    "thread_pool_size": 10,      # 线程池大小
    "queue_size": 1000,          # 队列大小
    "timeout": 30,               # 操作超时时间（秒）
    "retry_count": 3,            # 重试次数
}

# 环境特定配置
ENVIRONMENT_CONFIG = {
    "development": {
        "debug": True,
        "log_level": "DEBUG",
        "test_server_host": "localhost",
        "test_server_port": 8888,
    },
    "production": {
        "debug": False,
        "log_level": "WARNING",
        "test_server_host": "192.168.1.100",  # 生产环境服务器地址
        "test_server_port": 8888,
    },
    "testing": {
        "debug": True,
        "log_level": "DEBUG",
        "test_server_host": "localhost",
        "test_server_port": 8888,
    }
}

def get_config(environment: str = "development") -> Dict:
    """
    获取指定环境的配置
    
    :param environment: 环境名称（development/production/testing）
    :return: 配置字典
    """
    # 获取环境配置
    env_config = ENVIRONMENT_CONFIG.get(environment, ENVIRONMENT_CONFIG["development"])
    
    # 合并所有配置
    config = {
        "network": NETWORK_CONFIG,
        "app": APP_CONFIG,
        "cache": CACHE_CONFIG,
        "event": EVENT_CONFIG,
        "log": LOG_CONFIG,
        "security": SECURITY_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "environment": env_config,
    }
    
    return config

def get_network_config() -> Dict:
    """获取网络配置"""
    return NETWORK_CONFIG

def get_app_config() -> Dict:
    """获取应用配置"""
    return APP_CONFIG

def get_cache_config() -> Dict:
    """获取缓存配置"""
    return CACHE_CONFIG

def get_event_config() -> Dict:
    """获取事件配置"""
    return EVENT_CONFIG

def get_log_config() -> Dict:
    """获取日志配置"""
    return LOG_CONFIG

def get_security_config() -> Dict:
    """获取安全配置"""
    return SECURITY_CONFIG

def get_performance_config() -> Dict:
    """获取性能配置"""
    return PERFORMANCE_CONFIG

def get_environment_config(environment: str = "development") -> Dict:
    """获取环境配置"""
    return ENVIRONMENT_CONFIG.get(environment, ENVIRONMENT_CONFIG["development"])

# 配置验证函数
def validate_config(config: Dict) -> List[str]:
    """
    验证配置的有效性
    
    :param config: 配置字典
    :return: 错误信息列表
    """
    errors = []
    
    # 验证网络配置
    network = config.get("network", {})
    if not isinstance(network.get("test_server", {}).get("port"), int):
        errors.append("测试服务器端口必须是整数")
    
    if not isinstance(network.get("tested_machine", {}).get("port"), int):
        errors.append("被测试机器端口必须是整数")
    
    # 验证应用配置
    app = config.get("app", {})
    if not isinstance(app.get("default_apps"), list):
        errors.append("默认应用列表必须是列表")
    
    # 验证缓存配置
    cache = config.get("cache", {})
    if not isinstance(cache.get("default_capacity"), int) or cache["default_capacity"] <= 0:
        errors.append("默认缓存容量必须是正整数")
    
    return errors

if __name__ == "__main__":
    # 测试配置
    config = get_config("development")
    print("开发环境配置:")
    print(f"测试服务器: {config['network']['test_server']['host']}:{config['network']['test_server']['port']}")
    print(f"默认应用: {config['app']['default_apps']}")
    print(f"缓存容量: {config['cache']['default_capacity']}")
    
    # 验证配置
    errors = validate_config(config)
    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("配置验证通过")
