'''
Author: 凛冬已至 2985956026@qq.com
Date: 2025-08-28 13:18:09
LastEditors: 凛冬已至 2985956026@qq.com
LastEditTime: 2025-08-28 17:03:55
FilePath: \Auto-test\communicators\__init__.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
#!/usr/bin/env python3
"""
Communicators Package

这个包包含了多机器多应用通信的核心组件：

- test_communicator.py: 测试服务器，管理多机器连接
- tested_communicator.py: 被测试机器客户端，执行自动化操作
- operation_multi_machine.py: 多机器操作类，提供高级API
- operation.py: 单机器操作类（向后兼容）
- config.py: 配置管理
- multi_machine_example.py: 多机器使用示例
"""

__version__ = "2.0.0"
__author__ = "Auto Test Team"
__description__ = "多机器多应用自动化测试通信框架"

# 仅导出 MultiMachineOperation
from .operation_multi_machine import MultiMachineOperation

__all__ = [
    "MultiMachineOperation",
]
