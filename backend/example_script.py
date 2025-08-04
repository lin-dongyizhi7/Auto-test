#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例脚本 - 用于测试脚本管理功能
"""

import time
import sys

def main():
    """主函数"""
    print("=== 示例脚本开始执行 ===")
    print(f"Python版本: {sys.version}")
    print(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 模拟一些操作
    print("正在执行操作...")
    time.sleep(1)
    
    # 模拟数据处理
    data = [1, 2, 3, 4, 5]
    result = sum(data)
    print(f"数据处理结果: {result}")
    
    # 模拟文件操作
    print("正在写入文件...")
    with open("test_output.txt", "w", encoding="utf-8") as f:
        f.write("这是测试输出文件\n")
        f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"处理结果: {result}\n")
    
    print("=== 示例脚本执行完成 ===")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"脚本执行出错: {e}")
        sys.exit(1) 