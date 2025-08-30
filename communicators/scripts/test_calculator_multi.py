'''
Author: lin-dongyizhi7 2985956026@qq.com
Date: 2025-01-27 16:30:00
LastEditors: 凛冬已至 2985956026@qq.com
LastEditTime: 2025-08-29 09:28:09
FilePath: \Auto-test\communicators\test_calculator_multi.py
Description: 多机器环境下的计算器测试脚本，使用 MultiMachineOperation 类进行跨机器操作
'''
import time
import sys
import os

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ..operation_multi_machine import MultiMachineOperation

if __name__ == "__main__":
    # 1. 实例化多机器操作类（会自动启动测试服务器）
    print("正在启动多机器测试环境...")
    op = MultiMachineOperation(bind_host="0.0.0.0", server_port=8888)
    print("多机器测试环境启动成功")
    
    # 2. 等待机器和应用连接
    print("等待被测试机器连接...")
    timeout = 60  # 60秒超时
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        machines = op.get_available_machines()
        apps = op.get_available_apps()
        
        if machines and apps:
            print(f"检测到 {len(machines)} 台机器: {machines}")
            print(f"检测到 {len(apps)} 个应用")
            for app in apps:
                print(f"  - {app['name']} (机器: {app['machine_id']}, PID: {app['pid']})")
            break
        
        print("等待连接...")
        time.sleep(2)
    else:
        print("等待超时，未检测到可用的机器或应用")
        print("请确保在其他机器上运行了 tested_communicator.py")
        sys.exit(1)
    
    # 3. 选择第一台机器上的第一个计算器应用进行测试
    target_app = None
    for app in apps:
        if "calculator" in app['name'].lower() or "calc" in app['name'].lower():
            target_app = app
            break
    
    if not target_app:
        print("未找到计算器应用，使用第一个可用应用")
        target_app = apps[0]
    
    machine_id = target_app['machine_id']
    app_name = target_app['name']
    
    print(f"选择目标: 机器 {machine_id}, 应用 {app_name}")
    
    # 4. 设置目标机器和应用
    if not op.set_target(machine_id, app_name):
        print(f"无法设置目标: 机器 {machine_id}, 应用 {app_name}")
        sys.exit(1)
    
    print(f"目标设置成功: 机器 {machine_id}, 应用 {app_name}")
    
    # 5. 执行一系列计算器操作
    print("开始执行计算器测试...")
    
    # 定义特殊字符
    multiplication_sign = b'\303\227'.decode('utf-8')  # ×
    divide_sign = b'\303\267'.decode('utf-8')         # ÷
    point_sign = chr(0x2e)                            # .
    
    # 计算 12 + 34 的过程
    print("测试用例1: 基本加法 12 + 34 = 46")
    op.click_element(element_path="1", role_name_list=["push button"])  # 点击数字1
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path="+", role_name_list=["push button"])  # 点击加号
    op.click_element(element_path="3", role_name_list=["push button"])  # 点击数字3
    op.click_element(element_path="4", role_name_list=["push button"])  # 点击数字4
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号
    
    # 等待计算完成
    time.sleep(1)
    
    # 计算 5 * 6 - 7 的过程
    print("测试用例2: 乘法 5 × 6 = 30")
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path=multiplication_sign, role_name_list=["push button"])  # 点击乘号
    op.click_element(element_path="6", role_name_list=["push button"])  # 点击数字6
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号
    
    time.sleep(1)
    
    # 计算 81 / 9 的过程
    print("测试用例3: 除法 81 ÷ 9 = 9")
    op.click_element(element_path="8", role_name_list=["push button"])  # 点击数字8
    op.click_element(element_path="1", role_name_list=["push button"])  # 点击数字1
    op.click_element(element_path=divide_sign, role_name_list=["push button"])  # 点击除号
    op.click_element(element_path="9", role_name_list=["push button"])  # 点击数字9
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号
    
    time.sleep(1)
    
    # 计算 6.5 + 8.5 - 3.4 的过程
    print("测试用例4: 小数运算 6.5 + 8.5 = 15.0")
    op.click_element(element_path="6", role_name_list=["push button"])  # 点击数字6
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path="+", role_name_list=["push button"])  # 点击加号
    op.click_element(element_path="8", role_name_list=["push button"])  # 点击数字8
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号
    
    time.sleep(1)
    
    # 计算 2.5 * 4.2 / 1.2 的过程
    print("测试用例5: 复杂运算 2.5 × 4.2 ÷ 1.2 = 8.75")
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path=multiplication_sign, role_name_list=["push button"])  # 点击乘号
    op.click_element(element_path="4", role_name_list=["push button"])  # 点击数字4
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path=divide_sign, role_name_list=["push button"])  # 点击除号
    op.click_element(element_path="1", role_name_list=["push button"])  # 点击数字1
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号
    
    time.sleep(1)
    
    # 6. 获取测试结果截图
    print("获取测试结果截图...")
    try:
        screenshot_result = op.get_screenshot()
        if screenshot_result.get("success"):
            print("截图获取成功")
            print(f"截图大小: {screenshot_result['data']['size']}")
        else:
            print(f"截图获取失败: {screenshot_result.get('error')}")
    except Exception as e:
        print(f"截图获取异常: {e}")
    
    # 7. 导出测试结果
    print("导出测试结果...")
    try:
        op.export_to_json("calculator_test_results.json")
        print("测试结果已导出到 calculator_test_results.json")
    except Exception as e:
        print(f"结果导出失败: {e}")
    
    print("多机器计算器测试完成！")
    
    # 8. 保持运行状态，等待用户中断
    print("\n测试服务器保持运行中...")
    print("按 Ctrl+C 停止测试")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n收到中断信号，正在清理资源...")
    finally:
        op.close()
        print("资源清理完成")
