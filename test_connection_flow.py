#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的连接和注册流程
"""

import time
import threading
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from communicators.test_communicator import TestMachineCommunicator
from communicators.tested_communicator import TestedMachineCommunicator

def test_connection_flow():
    """测试新的连接和注册流程"""
    print("=" * 60)
    print("测试新的连接和注册流程")
    print("=" * 60)
    
    # 启动测试服务器
    print("1. 启动测试服务器...")
    test_server = TestMachineCommunicator(
        server_host="127.0.0.1",
        server_port=8888,
        server_id="test_server_001"
    )
    
    try:
        test_server.start_server()
        print("✅ 测试服务器启动成功")
        
        # 启动被测试机器
        print("\n2. 启动被测试机器...")
        tested_machine = TestedMachineCommunicator(
            bind_host="127.0.0.1",
            bind_port=8889,
            machine_id="test_machine_001"
        )
        
        # 在单独线程中启动被测试机器
        def start_tested_machine():
            tested_machine.start()
        
        tested_thread = threading.Thread(target=start_tested_machine, daemon=True)
        tested_thread.start()
        
        # 等待被测试机器启动
        time.sleep(2)
        print("✅ 被测试机器启动成功")
        
        # 测试服务器主动连接被测试机器
        print("\n3. 测试服务器主动连接被测试机器...")
        connection_result = test_server.connect_to_machine(
            machine_id="test_machine_001",
            host="127.0.0.1",
            port=8889
        )
        
        if connection_result.get("success"):
            print(f"✅ 连接成功: {connection_result.get('message')}")
            actual_machine_id = connection_result.get("machine_id")
            print(f"   实际机器ID: {actual_machine_id}")
        else:
            print(f"❌ 连接失败: {connection_result.get('error')}")
            return False
        
        # 检查连接状态
        print("\n4. 检查连接状态...")
        machines = test_server.get_connected_machines()
        print(f"已连接的机器: {machines}")
        
        if actual_machine_id in machines:
            print("✅ 机器已正确注册到测试服务器")
        else:
            print("❌ 机器未正确注册")
            return False
        
        # 测试应用注册
        print("\n5. 测试应用注册...")
        app_registration = {
            "type": "register_app",
            "data": {
                "app_name": "test_app",
                "app_info": {
                    "version": "1.0.0",
                    "description": "测试应用"
                }
            }
        }
        
        # 通过连接发送应用注册请求
        if actual_machine_id in test_server.connections:
            socket = test_server.connections[actual_machine_id]
            socket.sendall(json.dumps(app_registration).encode('utf-8'))
            
            # 接收响应
            response_data = socket.recv(1024).decode('utf-8')
            response = json.loads(response_data)
            
            if response.get("success"):
                print("✅ 应用注册成功")
            else:
                print(f"❌ 应用注册失败: {response.get('error')}")
        
        # 检查应用列表
        print("\n6. 检查应用列表...")
        apps = test_server.get_registered_apps()
        print(f"已注册的应用: {apps}")
        
        # 测试断开连接
        print("\n7. 测试断开连接...")
        disconnect_result = test_server.disconnect_machine(actual_machine_id)
        if disconnect_result.get("success"):
            print("✅ 断开连接成功")
        else:
            print(f"❌ 断开连接失败: {disconnect_result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False
    
    finally:
        # 清理资源
        print("\n8. 清理资源...")
        try:
            test_server.stop_server()
            tested_machine.stop()
            print("✅ 资源清理完成")
        except Exception as e:
            print(f"⚠️ 资源清理时发生错误: {str(e)}")

def test_machine_id_duplication():
    """测试机器ID重复处理"""
    print("\n" + "=" * 60)
    print("测试机器ID重复处理")
    print("=" * 60)
    
    # 启动测试服务器
    test_server = TestMachineCommunicator(
        server_host="127.0.0.1",
        server_port=8888,
        server_id="test_server_002"
    )
    
    try:
        test_server.start_server()
        print("✅ 测试服务器启动成功")
        
        # 启动两个相同ID的被测试机器
        print("\n1. 启动第一个被测试机器...")
        tested_machine1 = TestedMachineCommunicator(
            bind_host="127.0.0.1",
            bind_port=8889,
            machine_id="duplicate_machine"
        )
        
        def start_tested_machine1():
            tested_machine1.start()
        
        tested_thread1 = threading.Thread(target=start_tested_machine1, daemon=True)
        tested_thread1.start()
        time.sleep(2)
        
        # 连接第一个机器
        connection_result1 = test_server.connect_to_machine(
            machine_id="duplicate_machine",
            host="127.0.0.1",
            port=8889
        )
        
        if connection_result1.get("success"):
            print("✅ 第一个机器连接成功")
            machine_id1 = connection_result1.get("machine_id")
        else:
            print(f"❌ 第一个机器连接失败: {connection_result1.get('error')}")
            return False
        
        # 启动第二个相同ID的被测试机器
        print("\n2. 启动第二个被测试机器（相同ID）...")
        tested_machine2 = TestedMachineCommunicator(
            bind_host="127.0.0.1",
            bind_port=8890,
            machine_id="duplicate_machine"
        )
        
        def start_tested_machine2():
            tested_machine2.start()
        
        tested_thread2 = threading.Thread(target=start_tested_machine2, daemon=True)
        tested_thread2.start()
        time.sleep(2)
        
        # 连接第二个机器
        connection_result2 = test_server.connect_to_machine(
            machine_id="duplicate_machine",
            host="127.0.0.1",
            port=8890
        )
        
        if connection_result2.get("success"):
            print("✅ 第二个机器连接成功")
            machine_id2 = connection_result2.get("machine_id")
        else:
            print(f"❌ 第二个机器连接失败: {connection_result2.get('error')}")
            return False
        
        # 检查机器ID是否不同
        print(f"\n3. 检查机器ID:")
        print(f"   第一个机器ID: {machine_id1}")
        print(f"   第二个机器ID: {machine_id2}")
        
        if machine_id1 != machine_id2:
            print("✅ 机器ID重复处理成功，生成了不同的ID")
        else:
            print("❌ 机器ID重复处理失败，两个机器使用了相同的ID")
            return False
        
        # 检查连接状态
        machines = test_server.get_connected_machines()
        print(f"已连接的机器: {machines}")
        
        if len(machines) == 2:
            print("✅ 两个机器都已正确连接")
        else:
            print(f"❌ 连接机器数量不正确，期望2个，实际{len(machines)}个")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False
    
    finally:
        # 清理资源
        try:
            test_server.stop_server()
            tested_machine1.stop()
            tested_machine2.stop()
        except Exception as e:
            print(f"⚠️ 资源清理时发生错误: {str(e)}")

if __name__ == "__main__":
    import json
    
    print("开始测试新的连接和注册流程...")
    
    # 测试基本连接流程
    success1 = test_connection_flow()
    
    # 测试机器ID重复处理
    success2 = test_machine_id_duplication()
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"基本连接流程: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"机器ID重复处理: {'✅ 通过' if success2 else '❌ 失败'}")
    
    if success1 and success2:
        print("\n🎉 所有测试通过！新的连接和注册流程工作正常。")
    else:
        print("\n⚠️ 部分测试失败，请检查实现。")
