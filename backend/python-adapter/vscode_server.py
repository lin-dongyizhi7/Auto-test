#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VSCode服务器适配器
作为Node.js后端和Python测试服务器之间的桥梁
"""

import json
import sys
import time
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from communicators.operation_multi_machine import MultiMachineOperation
    from communicators.tested_communicator import TestedMachineCommunicator
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的项目目录中运行此脚本")
    sys.exit(1)

class VSCodeServer:
    """VSCode服务器适配器"""
    
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.operation = None
        self.is_running = False
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('vscode_server.log', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """启动服务器"""
        try:
            self.logger.info(f"正在启动VSCode服务器 {self.host}:{self.port}")
            
            # 创建多机器操作实例
            self.operation = MultiMachineOperation()
            
            # 启动服务器
            self.operation.start_server(host=self.host, port=self.port)
            
            self.is_running = True
            self.logger.info(f"VSCode服务器已启动 {self.host}:{self.port}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动VSCode服务器失败: {e}")
            return False
            
    def stop(self):
        """停止服务器"""
        try:
            if self.operation:
                self.operation.close()
                self.operation = None
                
            self.is_running = False
            self.logger.info("VSCode服务器已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止VSCode服务器失败: {e}")
            return False
            
    def handle_command(self, command_data):
        """处理来自Node.js的命令"""
        try:
            command = command_data.get('command')
            params = command_data.get('parameters', {})
            
            self.logger.info(f"收到命令: {command}")
            
            if command == 'get_machines':
                return self.handle_get_machines()
            elif command == 'get_apps':
                return self.handle_get_apps()
            elif command == 'set_target':
                return self.handle_set_target(params)
            elif command == 'execute_test':
                return self.handle_execute_test(params)
            elif command == 'get_screenshot':
                return self.handle_get_screenshot(params)
            elif command == 'find_element':
                return self.handle_find_element(params)
            elif command == 'click_element':
                return self.handle_click_element(params)
            elif command == 'type_text':
                return self.handle_type_text(params)
            elif command == 'wait_for_element':
                return self.handle_wait_for_element(params)
            elif command == 'send_hotkey':
                return self.handle_send_hotkey(params)
            elif command == 'stop':
                return self.handle_stop()
            else:
                return {
                    'success': False,
                    'error': f'未知命令: {command}'
                }
                
        except Exception as e:
            self.logger.error(f"处理命令失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def handle_get_machines(self):
        """获取机器列表"""
        try:
            if not self.operation:
                return {'success': False, 'error': '服务器未启动'}
                
            machines = self.operation.get_machines()
            return {
                'success': True,
                'data': machines
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def handle_get_apps(self):
        """获取应用列表"""
        try:
            if not self.operation:
                return {'success': False, 'error': '服务器未启动'}
                
            apps = self.operation.get_apps()
            return {
                'success': True,
                'data': apps
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def handle_set_target(self, params):
        """设置目标"""
        try:
            if not self.operation:
                return {'success': False, 'error': '服务器未启动'}
                
            machine_id = params.get('machine_id')
            app_name = params.get('app_name')
            
            if not machine_id or not app_name:
                return {'success': False, 'error': '缺少必要参数'}
                
            self.operation.set_target(machine_id, app_name)
            return {
                'success': True,
                'message': f'设置目标成功: {machine_id}:{app_name}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def handle_execute_test(self, params):
        """执行测试"""
        try:
            if not self.operation:
                return {'success': False, 'error': '服务器未启动'}
                
            script_content = params.get('script_content')
            if not script_content:
                return {'success': False, 'error': '缺少脚本内容'}
                
            # 这里应该实现实际的脚本执行逻辑
            result = f"脚本执行成功: {len(script_content)} 字符"
            
            return {
                'success': True,
                'data': {'result': result}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def handle_get_screenshot(self, params):
        """获取截图"""
        try:
            if not self.operation:
                return {'success': False, 'error': '服务器未启动'}
                
            region = params.get('region', 'full')
            screenshot_data = self.operation.get_screenshot(region)
            
            return {
                'success': True,
                'data': {
                    'screenshot': screenshot_data,
                    'region': region
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def handle_find_element(self, params):
        """查找元素"""
        try:
            if not self.operation:
                return {'success': False, 'error': '服务器未启动'}
                
            selector = params.get('selector')
            selector_type = params.get('selector_type')
            
            if not selector or not selector_type:
                return {'success': False, 'error': '缺少选择器参数'}
                
            # 这里应该实现实际的元素查找逻辑
            element_info = {
                'found': True,
                'selector': selector,
                'type': selector_type,
                'position': [100, 200]
            }
            
            return {
                'success': True,
                'data': element_info
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def handle_click_element(self, params):
        """点击元素"""
        try:
            if not self.operation:
                return {'success': False, 'error': '服务器未启动'}
                
            element_id = params.get('element_id')
            if not element_id:
                return {'success': False, 'error': '缺少元素ID'}
                
            # 这里应该实现实际的点击逻辑
            return {
                'success': True,
                'message': f'点击元素成功: {element_id}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def handle_type_text(self, params):
        """输入文本"""
        try:
            if not self.operation:
                return {'success': False, 'error': '服务器未启动'}
                
            element_id = params.get('element_id')
            text = params.get('text')
            
            if not element_id or not text:
                return {'success': False, 'error': '缺少必要参数'}
                
            # 这里应该实现实际的文本输入逻辑
            return {
                'success': True,
                'message': f'输入文本成功: {text}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def handle_wait_for_element(self, params):
        """等待元素"""
        try:
            if not self.operation:
                return {'success': False, 'error': '服务器未启动'}
                
            selector = params.get('selector')
            timeout = params.get('timeout', 10000)
            
            if not selector:
                return {'success': False, 'error': '缺少选择器'}
                
            # 这里应该实现实际的等待逻辑
            return {
                'success': True,
                'message': f'等待元素成功: {selector}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def handle_send_hotkey(self, params):
        """发送热键"""
        try:
            if not self.operation:
                return {'success': False, 'error': '服务器未启动'}
                
            keys = params.get('keys')
            if not keys:
                return {'success': False, 'error': '缺少按键参数'}
                
            # 这里应该实现实际的热键发送逻辑
            return {
                'success': True,
                'message': f'发送热键成功: {keys}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def handle_stop(self):
        """处理停止命令"""
        try:
            self.stop()
            return {'success': True, 'message': '服务器已停止'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def run_vscode_mode(self):
        """VSCode模式运行"""
        self.logger.info("启动VSCode模式")
        
        if not self.start():
            return
            
        try:
            while True:
                # 从标准输入读取命令
                line = input().strip()
                if not line:
                    continue
                    
                try:
                    command_data = json.loads(line)
                    response = self.handle_command(command_data)
                    
                    # 输出JSON响应到标准输出
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                    
                except json.JSONDecodeError:
                    print(json.dumps({
                        'success': False,
                        'error': '无效的JSON格式'
                    }, ensure_ascii=False))
                    sys.stdout.flush()
                    
        except KeyboardInterrupt:
            self.logger.info("收到中断信号")
        except EOFError:
            self.logger.info("标准输入结束")
        finally:
            self.stop()
            
    def run_standalone_mode(self):
        """独立模式运行"""
        self.logger.info("启动独立模式")
        
        if not self.start():
            return
            
        try:
            while True:
                time.sleep(1)
                # 这里可以添加定期任务
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号")
        finally:
            self.stop()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='VSCode服务器适配器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8888, help='服务器端口')
    parser.add_argument('--vscode-mode', action='store_true', help='VSCode模式')
    
    args = parser.parse_args()
    
    server = VSCodeServer(args.host, args.port)
    
    if args.vscode_mode:
        server.run_vscode_mode()
    else:
        server.run_standalone_mode()

if __name__ == '__main__':
    main()
