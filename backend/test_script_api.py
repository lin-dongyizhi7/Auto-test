#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本管理API测试脚本
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8080"

def test_script_management():
    """测试脚本管理功能"""
    print("=== 开始测试脚本管理功能 ===")
    
    # 测试创建脚本
    print("\n1. 测试创建脚本")
    create_data = {
        "name": "测试脚本",
        "description": "这是一个测试脚本",
        "content": """
import time
print("Hello from test script!")
print(f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
result = 1 + 2 + 3
print(f"Calculation result: {result}")
"""
    }
    
    response = requests.post(f"{BASE_URL}/scripts", json=create_data)
    print(f"创建脚本响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"创建成功: {result.get('message')}")
        script_id = result.get('data', {}).get('id')
        print(f"脚本ID: {script_id}")
    else:
        print(f"创建失败: {response.text}")
        return
    
    # 测试获取脚本列表
    print("\n2. 测试获取脚本列表")
    response = requests.get(f"{BASE_URL}/scripts")
    print(f"获取脚本列表响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        scripts = result.get('data', [])
        print(f"脚本数量: {len(scripts)}")
        for script in scripts:
            print(f"  - {script.get('name')} (ID: {script.get('id')})")
    
    # 测试获取单个脚本
    print(f"\n3. 测试获取单个脚本 (ID: {script_id})")
    response = requests.get(f"{BASE_URL}/scripts/{script_id}")
    print(f"获取单个脚本响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        script = result.get('data', {})
        print(f"脚本名称: {script.get('name')}")
        print(f"脚本状态: {script.get('status')}")
    
    # 测试运行脚本
    print(f"\n4. 测试运行脚本 (ID: {script_id})")
    response = requests.post(f"{BASE_URL}/scripts/{script_id}/run")
    print(f"运行脚本响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        run_result = result.get('data', {})
        print(f"运行成功: {result.get('message')}")
        print(f"执行时间: {run_result.get('executionTime')}ms")
        print(f"输出: {run_result.get('output', '无输出')}")
        if run_result.get('error'):
            print(f"错误: {run_result.get('error')}")
    else:
        print(f"运行失败: {response.text}")
    
    # 测试更新脚本
    print(f"\n5. 测试更新脚本 (ID: {script_id})")
    update_data = {
        "name": "更新后的测试脚本",
        "description": "这是更新后的测试脚本",
        "content": """
import time
import sys
print("Hello from updated test script!")
print(f"Python version: {sys.version}")
print(f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
result = sum(range(1, 11))
print(f"Sum of 1-10: {result}")
"""
    }
    
    response = requests.put(f"{BASE_URL}/scripts/{script_id}", json=update_data)
    print(f"更新脚本响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"更新成功: {result.get('message')}")
    else:
        print(f"更新失败: {response.text}")
    
    # 再次运行更新后的脚本
    print(f"\n6. 测试运行更新后的脚本 (ID: {script_id})")
    response = requests.post(f"{BASE_URL}/scripts/{script_id}/run")
    print(f"运行更新后脚本响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        run_result = result.get('data', {})
        print(f"运行成功: {result.get('message')}")
        print(f"执行时间: {run_result.get('executionTime')}ms")
        print(f"输出: {run_result.get('output', '无输出')}")
        if run_result.get('error'):
            print(f"错误: {run_result.get('error')}")
    
    # 测试导出脚本
    print(f"\n7. 测试导出脚本 (ID: {script_id})")
    response = requests.get(f"{BASE_URL}/scripts/{script_id}/export")
    print(f"导出脚本响应: {response.status_code}")
    if response.status_code == 200:
        content = response.text
        print(f"导出成功，脚本内容长度: {len(content)} 字符")
        print("脚本内容预览:")
        print(content[:200] + "..." if len(content) > 200 else content)
    else:
        print(f"导出失败: {response.text}")
    
    # 测试删除脚本
    print(f"\n8. 测试删除脚本 (ID: {script_id})")
    response = requests.delete(f"{BASE_URL}/scripts/{script_id}")
    print(f"删除脚本响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"删除成功: {result.get('message')}")
    else:
        print(f"删除失败: {response.text}")
    
    # 验证删除结果
    print(f"\n9. 验证删除结果")
    response = requests.get(f"{BASE_URL}/scripts/{script_id}")
    print(f"获取已删除脚本响应: {response.status_code}")
    if response.status_code == 404:
        print("脚本已成功删除")
    else:
        print("脚本删除验证失败")
    
    print("\n=== 脚本管理功能测试完成 ===")

def test_error_cases():
    """测试错误情况"""
    print("\n=== 开始测试错误情况 ===")
    
    # 测试获取不存在的脚本
    print("\n1. 测试获取不存在的脚本")
    response = requests.get(f"{BASE_URL}/scripts/nonexistent_id")
    print(f"响应状态码: {response.status_code}")
    if response.status_code == 404:
        print("正确处理了不存在的脚本")
    else:
        print("未正确处理不存在的脚本")
    
    # 测试运行不存在的脚本
    print("\n2. 测试运行不存在的脚本")
    response = requests.post(f"{BASE_URL}/scripts/nonexistent_id/run")
    print(f"响应状态码: {response.status_code}")
    if response.status_code == 404:
        print("正确处理了运行不存在的脚本")
    else:
        print("未正确处理运行不存在的脚本")
    
    # 测试创建无效脚本
    print("\n3. 测试创建无效脚本")
    invalid_data = {
        "name": "",  # 空名称
        "content": ""  # 空内容
    }
    response = requests.post(f"{BASE_URL}/scripts", json=invalid_data)
    print(f"响应状态码: {response.status_code}")
    if response.status_code == 422:
        print("正确处理了无效的脚本数据")
    else:
        print("未正确处理无效的脚本数据")
    
    print("\n=== 错误情况测试完成 ===")

if __name__ == "__main__":
    try:
        # 测试基本功能
        test_script_management()
        
        # 测试错误情况
        test_error_cases()
        
        print("\n所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到后端服务，请确保后端服务正在运行")
    except Exception as e:
        print(f"测试过程中发生错误: {e}") 