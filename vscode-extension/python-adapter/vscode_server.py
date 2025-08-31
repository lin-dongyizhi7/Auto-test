#!/usr/bin/env python3
"""
VSCode 插件适配器

这个模块为原有的测试服务器代码提供 VSCode 插件支持，
通过标准输入/输出与 VSCode 插件进行通信。
"""

import sys
import json
import time
import logging
import argparse
from typing import Dict, Any, Optional
from communicators.operation_multi_machine import MultiMachineOperation

class VSCodeServer:
    """VSCode 插件适配器服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
        self.host = host
        self.port = port
        self.operation = None
        self.is_running = False
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 命令处理器映射
        self.command_handlers = {
            'get_machines': self.handle_get_machines,
            'get_apps': self.handle_get_apps,
            'set_target': self.handle_set_target,
            'execute_test': self.handle_execute_test,
            'execute_commands': self.handle_execute_commands,
            'get_screenshot': self.handle_get_screenshot,
            'find_element': self.handle_find_element,
            'click_element': self.handle_click_element,
            'type_text': self.handle_type_text,
            'wait_for_element': self.handle_wait_for_element,
            'get_status': self.handle_get_status
        }
    
    def start(self) -> bool:
        """启动服务器"""
        try:
            self.logger.info(f"正在启动 VSCode 适配器服务器 ({self.host}:{self.port})")
            
            # 启动原有的测试服务器
            self.operation = MultiMachineOperation(
                bind_host=self.host,
                server_port=self.port
            )
            
            self.is_running = True
            self.logger.info("VSCode 适配器服务器已启动")
            
            # 发送启动成功消息
            self.send_response({
                'type': 'serverStarted',
                'host': self.host,
                'port': self.port,
                'timestamp': time.time()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动服务器失败: {e}")
            self.send_response({
                'type': 'serverError',
                'error': str(e),
                'timestamp': time.time()
            })
            return False
    
    def stop(self) -> None:
        """停止服务器"""
        try:
            if self.operation:
                self.operation.close()
                self.operation = None
            
            self.is_running = False
            self.logger.info("VSCode 适配器服务器已停止")
            
            # 发送停止消息
            self.send_response({
                'type': 'serverStopped',
                'timestamp': time.time()
            })
            
        except Exception as e:
            self.logger.error(f"停止服务器失败: {e}")
    
    def run(self) -> None:
        """运行服务器主循环"""
        if not self.start():
            return
        
        try:
            self.logger.info("开始监听 VSCode 插件命令...")
            
            # 监听标准输入的命令
            for line in sys.stdin:
                try:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析命令
                    command_data = json.loads(line)
                    self.handle_command(command_data)
                    
                except json.JSONDecodeError:
                    self.logger.warning(f"无效的JSON命令: {line}")
                    continue
                except Exception as e:
                    self.logger.error(f"处理命令失败: {e}")
                    self.send_response({
                        'type': 'commandError',
                        'error': str(e),
                        'timestamp': time.time()
                    })
                    
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在关闭服务器...")
        finally:
            self.stop()
    
    def handle_command(self, command_data: Dict[str, Any]) -> None:
        """处理来自VSCode插件的命令"""
        try:
            command = command_data.get('command')
            params = command_data.get('params', {})
            timestamp = command_data.get('timestamp')
            
            self.logger.info(f"收到命令: {command}")
            
            if command in self.command_handlers:
                # 调用对应的命令处理器
                result = self.command_handlers[command](params)
                
                # 发送响应
                self.send_response({
                    'type': 'commandResponse',
                    'command': command,
                    'success': True,
                    'data': result,
                    'timestamp': time.time()
                })
            else:
                # 未知命令
                self.send_response({
                    'type': 'commandResponse',
                    'command': command,
                    'success': False,
                    'error': f'未知命令: {command}',
                    'timestamp': time.time()
                })
                
        except Exception as e:
            self.logger.error(f"处理命令时发生错误: {e}")
            self.send_response({
                'type': 'commandResponse',
                'command': command_data.get('command', 'unknown'),
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            })
    
    def handle_get_machines(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取机器列表命令"""
        try:
            machines = self.operation.get_available_machines()
            machine_info = []
            
            for machine_id in machines:
                machine_status = self.operation.get_machine_status(machine_id)
                if machine_status:
                    machine_info.append(machine_status)
            
            return {
                'machines': machine_info,
                'count': len(machine_info)
            }
        except Exception as e:
            self.logger.error(f"获取机器列表失败: {e}")
            return {'machines': [], 'count': 0, 'error': str(e)}
    
    def handle_get_apps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取应用列表命令"""
        try:
            machine_id = params.get('machineId')
            apps = self.operation.get_available_apps()
            
            if machine_id:
                # 过滤指定机器的应用
                filtered_apps = [app for app in apps if app.startswith(f"{machine_id}:")]
                return {'apps': filtered_apps, 'count': len(filtered_apps)}
            else:
                return {'apps': apps, 'count': len(apps)}
                
        except Exception as e:
            self.logger.error(f"获取应用列表失败: {e}")
            return {'apps': [], 'count': 0, 'error': str(e)}
    
    def handle_set_target(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理设置目标命令"""
        try:
            machine_id = params.get('machineId')
            app_name = params.get('appName')
            
            if not machine_id or not app_name:
                return {'success': False, 'error': '缺少必要参数'}
            
            success = self.operation.set_target(machine_id, app_name)
            return {'success': success}
            
        except Exception as e:
            self.logger.error(f"设置目标失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_execute_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行测试命令"""
        try:
            script_path = params.get('scriptPath')
            
            if not script_path:
                return {'success': False, 'error': '缺少脚本路径'}
            
            # 这里应该调用原有的测试执行逻辑
            # 暂时返回模拟结果
            return {
                'success': True,
                'scriptPath': script_path,
                'executionTime': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"执行测试失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_execute_commands(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行命令集命令"""
        try:
            commands = params.get('commands', [])
            
            if not commands:
                return {'success': False, 'error': '缺少命令列表'}
            
            # 这里应该调用原有的命令执行逻辑
            # 暂时返回模拟结果
            return {
                'success': True,
                'commands': commands,
                'executionTime': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_get_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取截图命令"""
        try:
            region = params.get('region')
            
            # 这里应该调用原有的截图逻辑
            # 暂时返回模拟结果
            return {
                'success': True,
                'screenshot': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
                'region': region,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"获取截图失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_find_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理查找元素命令"""
        try:
            element_path = params.get('elementPath')
            role_names = params.get('roleNames', [])
            
            if not element_path:
                return {'success': False, 'error': '缺少元素路径'}
            
            # 这里应该调用原有的元素查找逻辑
            # 暂时返回模拟结果
            return {
                'success': True,
                'element': {
                    'path': element_path,
                    'role': role_names[0] if role_names else 'unknown',
                    'bounds': [100, 100, 200, 150],
                    'text': '模拟元素'
                },
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"查找元素失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_click_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理点击元素命令"""
        try:
            element_path = params.get('elementPath')
            
            if not element_path:
                return {'success': False, 'error': '缺少元素路径'}
            
            # 这里应该调用原有的点击逻辑
            # 暂时返回模拟结果
            return {
                'success': True,
                'action': 'click',
                'element': element_path,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"点击元素失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_type_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入文本命令"""
        try:
            text = params.get('text')
            
            if not text:
                return {'success': False, 'error': '缺少文本内容'}
            
            # 这里应该调用原有的文本输入逻辑
            # 暂时返回模拟结果
            return {
                'success': True,
                'action': 'type',
                'text': text,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"输入文本失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_wait_for_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理等待元素命令"""
        try:
            element_path = params.get('elementPath')
            timeout = params.get('timeout', 5000)
            
            if not element_path:
                return {'success': False, 'error': '缺少元素路径'}
            
            # 这里应该调用原有的等待逻辑
            # 暂时返回模拟结果
            return {
                'success': True,
                'action': 'wait',
                'element': element_path,
                'timeout': timeout,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"等待元素失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取状态命令"""
        try:
            current_target = self.operation.get_current_target() if hasattr(self.operation, 'get_current_target') else None
            
            return {
                'serverRunning': self.is_running,
                'host': self.host,
                'port': self.port,
                'currentTarget': current_target,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"获取状态失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_response(self, response: Dict[str, Any]) -> None:
        """发送响应到VSCode插件"""
        try:
            response_json = json.dumps(response, ensure_ascii=False)
            print(response_json, flush=True)
        except Exception as e:
            self.logger.error(f"发送响应失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='VSCode 插件适配器服务器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器绑定地址')
    parser.add_argument('--port', type=int, default=8888, help='服务器端口')
    parser.add_argument('--vscode-mode', action='store_true', help='VSCode 插件模式')
    
    args = parser.parse_args()
    
    if args.vscode_mode:
        # VSCode 插件模式
        server = VSCodeServer(args.host, args.port)
        server.run()
    else:
        # 普通模式，启动原有的服务器
        print("启动原有的测试服务器...")
        op = MultiMachineOperation(args.host, args.port)
        try:
            while True:
                time.sleep(5)
                machines = op.get_available_machines()
                apps = op.get_available_apps()
                print(f"运行中：已连接机器 {len(machines)}，已注册应用 {len(apps)}")
        except KeyboardInterrupt:
            op.close()
            print("已退出")

if __name__ == "__main__":
    main()
