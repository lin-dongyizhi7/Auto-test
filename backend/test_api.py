#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QGIS自动化测试后端API测试脚本
用于测试后端API接口是否正常工作
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8080"

def test_api():
    """测试API接口"""
    print("开始测试QGIS自动化测试后端API...")
    print("=" * 50)
    
    # 测试1: 获取服务状态
    print("1. 测试获取服务状态...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 服务状态: {data}")
        else:
            print(f"✗ 获取服务状态失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 连接服务失败: {e}")
        return
    
    # 测试2: 获取连接状态
    print("\n2. 测试获取连接状态...")
    try:
        response = requests.get(f"{BASE_URL}/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 连接状态: {data}")
        else:
            print(f"✗ 获取连接状态失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 获取连接状态失败: {e}")
    
    # 测试3: 测试连接（需要被测试机器运行）
    print("\n3. 测试连接到被测试机器...")
    print("注意: 此测试需要被测试机器运行并监听8888端口")
    
    connect_data = {
        "host": "localhost",
        "port": 8888
    }
    
    try:
        response = requests.post(f"{BASE_URL}/connect", json=connect_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✓ 连接成功: {data.get('message')}")
                
                # 如果连接成功，测试其他操作
                test_operations()
            else:
                print(f"✗ 连接失败: {data.get('message')}")
        else:
            print(f"✗ 连接请求失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 连接测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("API测试完成")

def test_operations():
    """测试操作接口（需要先建立连接）"""
    print("\n4. 测试操作接口...")
    
    # 测试获取元素信息
    print("  4.1 测试获取元素信息...")
    try:
        response = requests.get(f"{BASE_URL}/element-info?path=button[0]")
        if response.status_code == 200:
            data = response.json()
            print(f"    ✓ 获取元素信息: {data.get('message')}")
        else:
            print(f"    ✗ 获取元素信息失败: {response.status_code}")
    except Exception as e:
        print(f"    ✗ 获取元素信息失败: {e}")
    
    # 测试查找图片
    print("  4.2 测试查找图片...")
    find_image_data = {
        "imagePath": "test_image.png",
        "threshold": 0.8
    }
    
    try:
        response = requests.post(f"{BASE_URL}/find-image", json=find_image_data)
        if response.status_code == 200:
            data = response.json()
            print(f"    ✓ 查找图片: {data.get('message')}")
        else:
            print(f"    ✗ 查找图片失败: {response.status_code}")
    except Exception as e:
        print(f"    ✗ 查找图片失败: {e}")
    
    # 测试快捷键
    print("  4.3 测试快捷键操作...")
    hotkey_data = {
        "keys": ["ctrl", "c"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/hotkey", json=hotkey_data)
        if response.status_code == 200:
            data = response.json()
            print(f"    ✓ 快捷键操作: {data.get('message')}")
        else:
            print(f"    ✗ 快捷键操作失败: {response.status_code}")
    except Exception as e:
        print(f"    ✗ 快捷键操作失败: {e}")
    
    # 测试断开连接
    print("\n5. 测试断开连接...")
    try:
        response = requests.post(f"{BASE_URL}/disconnect")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 断开连接: {data.get('message')}")
        else:
            print(f"✗ 断开连接失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 断开连接失败: {e}")

def test_error_handling():
    """测试错误处理"""
    print("\n6. 测试错误处理...")
    
    # 测试未连接时的操作
    print("  6.1 测试未连接时的操作...")
    try:
        response = requests.post(f"{BASE_URL}/click-element", json={"path": "button[0]"})
        if response.status_code == 400:
            print("    ✓ 正确返回未连接错误")
        else:
            print(f"    ✗ 错误处理异常: {response.status_code}")
    except Exception as e:
        print(f"    ✗ 错误处理测试失败: {e}")
    
    # 测试无效的JSON数据
    print("  6.2 测试无效的JSON数据...")
    try:
        response = requests.post(f"{BASE_URL}/connect", data="invalid json")
        if response.status_code == 422:
            print("    ✓ 正确返回JSON格式错误")
        else:
            print(f"    ✗ JSON格式错误处理异常: {response.status_code}")
    except Exception as e:
        print(f"    ✗ JSON格式错误测试失败: {e}")

if __name__ == "__main__":
    print("QGIS自动化测试后端API测试工具")
    print("请确保后端服务已启动在 http://localhost:8080")
    print()
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✓ 后端服务正在运行")
            test_api()
            test_error_handling()
        else:
            print(f"✗ 后端服务响应异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到后端服务，请确保服务已启动")
        print("启动命令: python main.py")
    except Exception as e:
        print(f"✗ 测试失败: {e}") 