#!/usr/bin/env python3
"""
多机器通信系统示例脚本

这个脚本演示了如何使用改造后的通信系统：
1. 启动测试服务器
2. 连接多个被测试机器
3. 与多个应用进行通信
4. 事件同步

使用方法：
1. 先运行测试服务器：python multi_machine_example.py server
2. 在被测试机器上运行：python multi_machine_example.py client <machine_id>
"""

import sys
import time
import threading
from test_communicator import TestMachineCommunicator, SingleMachineCommunicator
from tested_communicator import TestedMachineCommunicator

def start_test_server():
    """启动测试服务器"""
    print("启动测试服务器...")
    
    # 创建测试服务器实例
    server = TestMachineCommunicator(server_host="0.0.0.0", server_port=8889)
    
    try:
        # 启动服务器
        server.start_server()
        print("测试服务器已启动，等待机器连接...")
        
        # 保持服务器运行
        while True:
            time.sleep(1)
            
            # 显示当前状态
            machines = server.get_connected_machines()
            apps = server.get_registered_apps()
            
            if machines or apps:
                print(f"\n当前状态:")
                print(f"已连接机器: {len(machines)}")
                print(f"已注册应用: {len(apps)}")
                
                if machines:
                    print("机器列表:")
                    for mid in machines:
                        machine_info = server.machines[mid]
                        print(f"  - {mid}: {machine_info['address']} ({machine_info['status']})")
                
                if apps:
                    print("应用列表:")
                    for aid in apps:
                        app_info = server.apps[aid]
                        print(f"  - {aid}: {app_info['app_name']} ({app_info['status']})")
            
    except KeyboardInterrupt:
        print("\n正在停止测试服务器...")
        server.stop_server()
        print("测试服务器已停止")

def start_test_client(machine_id):
    """启动被测试机器客户端"""
    print(f"启动被测试机器客户端，机器ID: {machine_id}")
    
    # 创建被测试机器通信实例
    client = TestedMachineCommunicator(
        bind_port=8888,
        test_server_host="192.168.1.100",  # 配置为实际的测试服务器地址
        test_server_port=8889,
        machine_id=machine_id
    )
    
    try:
        # 启动服务
        client.start(app_names=["calculator", "gedit"])
        
    except KeyboardInterrupt:
        print(f"\n正在停止机器 {machine_id} 的服务...")
        client.stop()
        print(f"机器 {machine_id} 的服务已停止")

def demo_multi_machine_communication():
    """演示多机器通信功能"""
    print("演示多机器通信功能...")
    
    # 创建测试服务器连接器（用于测试）
    server_connector = SingleMachineCommunicator("192.168.1.100", 8889)
    
    try:
        # 获取机器列表
        print("获取已连接的机器列表...")
        response = server_connector._send_request("get_machines", {})
        if response.get("success"):
            machines = response["data"]["machines"]
            print(f"找到 {len(machines)} 台机器:")
            for mid, machine in machines.items():
                print(f"  - {mid}: {machine['address']}")
        else:
            print(f"获取机器列表失败: {response.get('error')}")
        
        # 获取应用列表
        print("\n获取已注册的应用列表...")
        response = server_connector._send_request("get_apps", {})
        if response.get("success"):
            apps = response["data"]["apps"]
            print(f"找到 {len(apps)} 个应用:")
            for aid, app in apps.items():
                print(f"  - {aid}: {app['app_name']} (机器: {app['machine_id']})")
        else:
            print(f"获取应用列表失败: {response.get('error')}")
        
        # 演示与特定机器和应用的通信
        if machines and apps:
            # 选择第一个机器和第一个应用进行测试
            first_machine = list(machines.keys())[0]
            first_app = list(apps.keys())[0]
            app_name = apps[first_app]["app_name"]
            
            print(f"\n测试与机器 {first_machine} 上的应用 {app_name} 的通信...")
            
            # 获取应用窗口区域
            print("获取应用窗口区域...")
            response = server_connector._send_request("get_app_region", {
                "machine_id": first_machine,
                "app_name": app_name
            })
            if response.get("success"):
                region = response["data"]["app_region"]
                print(f"应用窗口区域: {region}")
            else:
                print(f"获取应用窗口区域失败: {response.get('error')}")
            
            # 获取截图
            print("获取应用截图...")
            response = server_connector._send_request("get_screenshot", {
                "machine_id": first_machine,
                "app_name": app_name
            })
            if response.get("success"):
                print(f"截图获取成功，大小: {response['data']['size']} 字节")
            else:
                print(f"获取截图失败: {response.get('error')}")
            
            # 执行命令
            print("执行测试命令...")
            commands = [
                {"action": "mouse_move", "params": {"x": 100, "y": 100}},
                {"action": "mouse_click", "params": {"x": 100, "y": 100, "button": "left"}}
            ]
            response = server_connector._send_request("exec_commands", {
                "machine_id": first_machine,
                "app_name": app_name,
                "commands": commands
            })
            if response.get("success"):
                print("命令执行成功")
                for result in response["results"]:
                    print(f"  - {result['action']}: {'成功' if result['success'] else '失败'}")
            else:
                print(f"命令执行失败: {response.get('error')}")
        
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
    finally:
        server_connector.close()

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python multi_machine_example.py server          # 启动测试服务器")
        print("  python multi_machine_example.py client <id>     # 启动被测试机器客户端")
        print("  python multi_machine_example.py demo            # 演示多机器通信功能")
        return
    
    command = sys.argv[1]
    
    if command == "server":
        start_test_server()
    elif command == "client":
        if len(sys.argv) < 3:
            print("请指定机器ID: python multi_machine_example.py client <machine_id>")
            return
        machine_id = sys.argv[2]
        start_test_client(machine_id)
    elif command == "demo":
        demo_multi_machine_communication()
    else:
        print(f"未知命令: {command}")
        print("可用命令: server, client, demo")

if __name__ == "__main__":
    main()
