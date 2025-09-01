#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python App模式配置文件
"""

import os

# 基础配置
APP_NAME = "自动化测试系统"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "基于Python的自动化测试工具"

# 服务器配置
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080

# 脚本存储配置
SCRIPT_STORAGE_FILE = "scripts_storage.json"
SCRIPT_COUNTER_FILE = "script_counter.json"
SCRIPT_MAX_SIZE = 1024 * 1024  # 1MB
SCRIPT_TIMEOUT = 30  # 30秒

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "app.log"

# 界面配置
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"

# 允许的图片格式
ALLOWED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".gif"]

# 默认脚本模板
DEFAULT_SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试脚本
"""

def main():
    """主函数"""
    print("Hello, AutoTest!")
    
    # 在这里添加你的测试逻辑
    # 例如：
    # - 截图
    # - 点击元素
    # - 输入文本
    # - 等待操作
    
    print("测试完成!")

if __name__ == "__main__":
    main()
'''

# 创建必要的目录
def ensure_directories():
    """确保必要的目录存在"""
    # 对于当前目录的文件，不需要创建目录
    # 如果需要创建子目录，可以在这里添加
    pass

# 初始化时创建目录
ensure_directories()
