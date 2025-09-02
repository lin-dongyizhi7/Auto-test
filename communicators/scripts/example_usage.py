#!/usr/bin/env python3
"""
重构后的类使用示例

这个脚本展示了如何使用重构后的 TestMachineCommunicator 和 MultiMachineOperation 类
"""

import time
import logging
from communicators.test_communicator import TestMachineCommunicator
from communicators.operation_multi_machine import MultiMachineOperation

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数 - 演示重构后的类的使用"""
    
    print("=" * 60)
    print("🤖 重构后的类使用示例")
    print("=" * 60)
    
    try:
        # 1. 创建并启动通信器
        print("\n🚀 步骤1: 创建并启动通信器")
        communicator = TestMachineCommunicator(
            server_host="0.0.0.0",
            server_port=8888,
            server_id="example_server"
        )
        communicator.start_server()
        print("✅ 通信器启动成功")
        
        # 2. 创建操作类
        print("\n🎯 步骤2: 创建操作类")
        operation = MultiMachineOperation(communicator)
        print("✅ 操作类创建成功")
        
        # 3. 等待机器连接（模拟）
        print("\n⏳ 步骤3: 等待机器连接...")
        print("💡 请在其他终端运行 tested_communicator.py 来模拟机器连接")
        print("💡 或者等待5秒继续演示...")
        time.sleep(5)
        
        # 4. 获取连接状态
        print("\n📊 步骤4: 获取连接状态")
        try:
            summary = communicator.get_connection_summary()
            if summary.get("success"):
                data = summary["data"]
                print(f"📈 机器总数: {data['machines']['total']}")
                print(f"🔗 已连接: {data['machines']['connected']}")
                print(f"📱 应用总数: {data['apps']['total']}")
                print(f"🔄 运行中: {data['apps']['running']}")
                print(f"📝 事件总数: {data['events']['total']}")
                print(f"👥 订阅者: {data['events']['subscribers']}")
            else:
                print("❌ 获取连接状态失败")
        except Exception as e:
            print(f"❌ 获取连接状态异常: {e}")
        
        # 5. 演示机器管理功能
        print("\n🖥️ 步骤5: 演示机器管理功能")
        machines = communicator.get_connected_machines()
        if machines:
            print(f"📋 已连接机器: {machines}")
            
            # 获取第一个机器的详细信息
            first_machine = machines[0]
            machine_status = communicator.get_machine_status(first_machine)
            if machine_status.get("success"):
                data = machine_status["data"]
                print(f"🔍 机器 {first_machine} 详情:")
                print(f"   📍 地址: {data['address']}")
                print(f"   📱 应用数量: {data['apps_count']}")
                print(f"   🕒 连接时间: {data['connected_at']}")
                print(f"   👀 最后活跃: {data['last_seen']}")
        else:
            print("📭 暂无机器连接")
        
        # 6. 演示应用管理功能
        print("\n📱 步骤6: 演示应用管理功能")
        apps = communicator.get_registered_apps()
        if apps:
            print(f"📋 已注册应用: {apps}")
            
            # 获取第一个应用的详细信息
            first_app = apps[0]
            app_status = communicator.get_app_status(first_app)
            if app_status.get("success"):
                data = app_status["data"]
                print(f"🔍 应用 {first_app} 详情:")
                print(f"   🖥️ 机器ID: {data['machine_id']}")
                print(f"   📱 应用名: {data['app_name']}")
                print(f"   📊 状态: {data['status']}")
                print(f"   🕒 注册时间: {data['registered_at']}")
        else:
            print("📭 暂无应用注册")
        
        # 7. 演示事件管理功能
        print("\n📝 步骤7: 演示事件管理功能")
        try:
            events = communicator.get_event_history(limit=5)
            if events:
                print(f"📋 最近5个事件:")
                for i, event in enumerate(events, 1):
                    print(f"   {i}. {event.type.value} - {event.machine_id} - {event.timestamp}")
            else:
                print("📭 暂无事件记录")
        except Exception as e:
            print(f"❌ 获取事件历史异常: {e}")
        
        # 8. 演示操作类功能（如果有目标机器和应用）
        print("\n🎮 步骤8: 演示操作类功能")
        if machines and apps:
            # 设置目标
            target_machine = machines[0]
            target_app = apps[0].split(":")[1] if ":" in apps[0] else "unknown"
            
            print(f"🎯 设置目标: 机器 {target_machine}, 应用 {target_app}")
            success = operation.set_target(target_machine, target_app)
            
            if success:
                print("✅ 目标设置成功")
                
                # 演示获取截图
                print("📸 尝试获取截图...")
                try:
                    screenshot_result = operation.get_screenshot()
                    if screenshot_result.get("success"):
                        print("✅ 截图获取成功")
                    else:
                        print(f"❌ 截图获取失败: {screenshot_result.get('error')}")
                except Exception as e:
                    print(f"❌ 截图获取异常: {e}")
                
                # 演示其他操作（这里只是演示，实际需要真实的元素）
                print("🎮 演示其他操作...")
                print("💡 注意: 以下操作需要真实的GUI元素才能成功")
                
                # 获取操作统计
                stats = operation.get_commands_count()
                print(f"📊 操作统计: {stats}")
                
            else:
                print("❌ 目标设置失败")
        else:
            print("📭 需要机器和应用才能演示操作功能")
        
        # 9. 演示连接清理功能
        print("\n🧹 步骤9: 演示连接清理功能")
        try:
            cleaned_count = communicator.cleanup_inactive_connections(timeout_seconds=1)
            print(f"🧹 清理了 {cleaned_count} 个超时连接")
        except Exception as e:
            print(f"❌ 连接清理异常: {e}")
        
        # 10. 总结
        print("\n" + "=" * 60)
        print("🎉 演示完成！")
        print("=" * 60)
        print("📋 重构后的类特点:")
        print("   ✅ TestMachineCommunicator: 专注于多机器连接和事件管理")
        print("   ✅ MultiMachineOperation: 专注于元素操作和指令生成")
        print("   ✅ 职责分离，代码更清晰")
        print("   ✅ 新增了更多实用方法")
        print("   ✅ 更好的错误处理和状态监控")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断演示")
    except Exception as e:
        print(f"\n\n❌ 演示过程中发生错误: {e}")
        logger.error(f"演示错误: {e}", exc_info=True)
    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        try:
            if 'operation' in locals():
                operation.close()
                print("✅ 操作类已关闭")
            
            if 'communicator' in locals():
                communicator.stop_server()
                print("✅ 通信器已停止")
                
        except Exception as e:
            print(f"❌ 清理资源时发生错误: {e}")
        
        print("👋 演示结束")

if __name__ == "__main__":
    main()
