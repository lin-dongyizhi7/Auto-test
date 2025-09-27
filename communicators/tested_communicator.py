'''
Author: 凛冬已至 2985956026@qq.com
Date: 2025-07-24 13:25:17
LastEditors: 凛冬已至 2985956026@qq.com
LastEditTime: 2025-09-27 16:07:37
FilePath: \Auto-test\communicators\tested_communicator.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import socket
import json
import time
import random
import io
import base64
import dogtail.tree
import pyautogui
import threading
import queue
import os
import sys
import argparse
from typing import Dict, List, Optional, Set, Any
from .config import get_security_config
from .crypto_utils import wrap_outgoing, unwrap_incoming
from collections import OrderedDict
from .machine_operator import MachineOperator
from .log_collector import init_global_logging, cleanup_global_logging, get_global_collector
from .protocol import MessageTypes, PROTOCOL_VERSION, basic_validate_message


class TestedMachineCommunicator:
    """被测试机器的通信类，支持多应用通信和事件同步"""
    
    def __init__(self, bind_host: str = "0.0.0.0", bind_port: int = 8888, 
                 machine_id: str = None, cache_capacity: int = 20):
        """
        初始化通信服务
        :param bind_host: 绑定的IP地址（0.0.0.0表示允许所有网络连接）
        :param bind_port: 监听的端口（默认8888）
        :param machine_id: 机器唯一标识符
        :param cache_capacity: 元素缓存的最大容量
        """
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.machine_id = machine_id or f"machine_{random.randint(1000, 9999)}"
        
        # 本地服务
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False
        
        # 机器操作器（负责在被测试机器上执行操作）
        self.machine_operator = MachineOperator(cache_capacity=cache_capacity)
        
        # 测试服务器连接（被动模式）
        self.test_server_socket = None
        self.test_server_addr = None
        self.test_server_connected = False
        self.test_server_thread = None
        self.test_server_send_lock = threading.Lock()
        self.test_server_connection_info = None  # 存储测试服务器连接信息
        
        # 事件同步
        self.event_queue = queue.Queue()
        self.event_thread = None
        
        # 线程管理
        self.server_thread = None
        # 安全
        sec = get_security_config()
        self._enable_encryption = bool(sec.get("enable_encryption"))
        self._shared_secret = sec.get("shared_secret") or ""
        


        # 本地UI事件队列（供可视化界面消费）
        self.ui_event_queue: "queue.Queue" = queue.Queue()
        
        # 日志收集器
        self.log_collector = None

    def _get_app_region(self, app_name: str) -> Optional[List[int]]:
        """获取指定应用的窗口信息（位置和大小）"""
        return self.machine_operator.get_app_region(app_name)

    def _get_screenshot(self, app_name: str, region: Optional[List[int]] = None) -> str:
        """
        截取指定应用或指定区域的屏幕，返回16进制编码
        :param app_name: 应用名称
        :param region: 可选区域 [x, y, width, height]，None表示应用窗口区域
        """
        return self.machine_operator.get_screenshot(app_name, region)
        
    def _get_element(self, app_name: str, element_path: str, role_name_list: Optional[List[Optional[str]]] = None) -> Dict:
        """
        调用dogtail查询指定应用的元素信息，使用LRU缓存加速重复查询
        :param app_name: 应用名称
        :param element_path: 元素路径（如"菜单/文件/新建"）
        :param role_name_list: 角色名列表，项数与路径级数相等，每项可为空
        :return: 包含元素位置、尺寸等信息的字典
        """
        return self.machine_operator.get_element(app_name, element_path, role_name_list)

    def _execute_commands(self, app_name: str, commands: List[Dict]) -> Dict:
        """
        执行测试者发送的指令集
        :param app_name: 应用名称
        :param commands: 指令列表（如鼠标移动、点击等）
        :return: 执行结果汇总
        """
        return self.machine_operator.execute_commands(app_name, commands)

    def _handle_test_server_connection(self, test_server_socket: socket.socket, test_server_addr: tuple) -> bool:
        """
        处理测试服务器的连接请求，验证IP和端口
        :param test_server_socket: 客户端socket
        :param test_server_addr: 客户端地址 (ip, port)
        :return: 是否接受连接
        """
        try:
            # 接收连接验证请求
            request_bytes = test_server_socket.recv(1024)
            try:
                request = unwrap_incoming(request_bytes, self._enable_encryption, self._shared_secret)
            except Exception:
                request = json.loads(request_bytes.decode('utf-8'))
            # 基础校验与版本比对
            validate = basic_validate_message(request)
            if not validate.get("success"):
                print(f"收到无效连接请求: {validate.get('error')}")
                return False
            req_ver = request.get("protocol_version")
            if not req_ver:
                print("警告: 对端未携带 protocol_version，将按当前版本兼容处理")
            elif req_ver != PROTOCOL_VERSION:
                print(f"警告: 协议版本不匹配，对端={req_ver}, 本端={PROTOCOL_VERSION}，尝试兼容处理")
            self._emit_event("incoming_connection", {"from": str(test_server_addr), "raw": request})
            if not request:
                return False
            if request.get("type") != MessageTypes.CONNECTION_REQUEST:
                print(f"收到来自 {test_server_addr} 的无效连接请求类型: {request.get('type')}")
                return False
            
            # 验证连接信息
            connection_data = request.get("data", {})
            server_host = connection_data.get("server_host")
            server_port = connection_data.get("server_port")
            server_id = connection_data.get("server_id")
            
            if not server_host or not server_port:
                print(f"连接请求缺少必要信息: server_host={server_host}, server_port={server_port}")
                return False
            
            # 验证IP地址（允许本地连接和指定IP）
            allowed_hosts = ["127.0.0.1", "localhost", "0.0.0.0"]
            if server_host not in allowed_hosts and not server_host.startswith("192.168."):
                print(f"拒绝来自 {test_server_addr} 的连接，IP地址 {server_host} 不在允许列表中")
                return False
            
            # 验证端口（通常测试服务器使用8888端口）
            if server_port != 8888:
                print(f"拒绝来自 {test_server_addr} 的连接，端口 {server_port} 不在允许列表中")
                return False
            
            print(f"验证通过，接受来自测试服务器 {test_server_addr} 的连接")
            
            # 存储连接信息
            self.test_server_connection_info = {
                "host": server_host,
                "port": server_port,
                "server_id": server_id,
                "test_server_addr": test_server_addr
            }
            
            # 发送连接确认
            response = {
                "type": MessageTypes.CONNECTION_RESPONSE,
                "success": True,
                "protocol_version": PROTOCOL_VERSION,
                "data": {
                    "message": "连接已接受"
                }
            }
            test_server_socket.sendall(wrap_outgoing(response, self._enable_encryption, self._shared_secret))
            
            # 发送机器注册请求
            registration_request = {
                "type": MessageTypes.MACHINE_REGISTRATION,
                "data": {
                    "machine_id": self.machine_id,
                    "machine_info": {
                        "address": (self.bind_host, self.bind_port),
                        "host": self.bind_host,
                        "port": self.bind_port,
                        "platform": "linux",
                        "timestamp": time.time(),
                        "server_id": server_id
                    }
                },
                "protocol_version": PROTOCOL_VERSION
            }
            test_server_socket.sendall(wrap_outgoing(registration_request, self._enable_encryption, self._shared_secret))
            print(f"发送机器注册请求: machine_id={self.machine_id}")
            
            # 等待注册响应
            registration_bytes = test_server_socket.recv(1024)
            if not registration_bytes:
                print("未收到机器注册响应")
                return False
            try:
                registration_result = unwrap_incoming(registration_bytes, self._enable_encryption, self._shared_secret)
            except Exception:
                registration_result = json.loads(registration_bytes.decode('utf-8'))
            if not registration_result.get("success"):
                print(f"机器注册失败: {registration_result.get('error')}")
                return False
            
            # 更新machine_id（如果服务器生成了新的ID）
            actual_machine_id = registration_result.get("machine_id", self.machine_id)
            if actual_machine_id != self.machine_id:
                print(f"服务器分配了新的机器ID: {actual_machine_id}")
                self.machine_id = actual_machine_id
            
            self._emit_event("test_server_connected", {
                "test_server_addr": str(test_server_addr), 
                "server_host": server_host, 
                "server_port": server_port,
                "machine_id": self.machine_id
            })
            
            # 设置测试服务器连接
            self.test_server_socket = test_server_socket
            self.test_server_addr = test_server_addr
            self.test_server_connected = True
            
            # 启动测试服务器通信线程
            self.test_server_thread = threading.Thread(target=self._handle_regular_request, daemon=True)
            self.test_server_thread.start()
            
            # 机器注册成功后，同步已注册的应用到测试服务器
            print("机器注册成功，开始同步已注册的应用...")
            self._sync_registered_apps_to_server()
            
            return True
            
        except Exception as e:
            print(f"处理测试服务器连接请求失败: {str(e)}")
            return False

    def _handle_screenshot_request(self, app_name: str, region: Optional[List[int]] = None) -> Dict:
        """处理截图请求"""
        if not app_name:
            return {"success": False, "error": "应用名称不能为空"}
        
        if app_name not in self.machine_operator.apps:
            return {"success": False, "error": f"应用 {app_name} 未注册"}
        
        screenshot_data = self._get_screenshot(app_name, region)
        if isinstance(screenshot_data, dict) and not screenshot_data.get("success"):
            return screenshot_data
        
        return {
            "success": True,
            "data": {
                "screenshot": screenshot_data,
                "size": len(screenshot_data),
                "format": "png"
            }
        }

    def _handle_element_request(self, app_name: str, element_path: str, role_name_list: Optional[List[Optional[str]]] = None) -> Dict:
        """处理元素查询请求"""
        if not app_name or not element_path:
            return {"success": False, "error": "应用名称和元素路径不能为空"}
        
        if app_name not in self.machine_operator.apps:
            return {"success": False, "error": f"应用 {app_name} 未注册"}
        
        return self._get_element(app_name, element_path, role_name_list)

    def _handle_command_request(self, app_name: str, commands: List[Dict]) -> Dict:
        """处理命令执行请求"""
        if not app_name or not commands:
            return {"success": False, "error": "应用名称和命令不能为空"}
        
        if app_name not in self.machine_operator.apps:
            return {"success": False, "error": f"应用 {app_name} 未注册"}
        
        # 记录命令执行日志
        if self.log_collector:
            command_count = len(commands)
            self.log_collector.add_log("INFO", f"开始执行 {command_count} 个命令，应用: {app_name}", "command_execution")
        
        result = self._execute_commands(app_name, commands)
        
        # 记录执行结果
        if self.log_collector:
            if result.get("success"):
                self.log_collector.add_log("INFO", f"命令执行成功，应用: {app_name}", "command_execution")
            else:
                error_msg = result.get("error", "未知错误")
                self.log_collector.add_log("ERROR", f"命令执行失败: {error_msg}，应用: {app_name}", "command_execution")
        
        return result

    def _handle_assert_request(self, element_path: str, role_name_list: List[str], expect_value: Any, attr: str, assert_type: str) -> Dict:
        """处理断言请求"""
        if not element_path:
            return {"success": False, "error": "元素路径不能为空"}
        
        if not self.current_app_name:
            return {"success": False, "error": "未设置当前应用"}
        
        if self.current_app_name not in self.machine_operator.apps:
            return {"success": False, "error": f"应用 {self.current_app_name} 未注册"}
        
        try:
            # 获取元素信息
            element_result = self._get_element(self.current_app_name, element_path, role_name_list)
            if not element_result.get("success"):
                return {"success": False, "error": f"获取元素失败: {element_result.get('error')}"}
            
            element_data = element_result.get("data", {})
            
            # 提取属性值
            actual_value = self._extract_attribute_value(element_data, attr)
            
            # 执行断言比较
            assert_result = self._perform_assertion(actual_value, expect_value, assert_type)
            
            return {
                "success": assert_result["success"],
                "actual": actual_value,
                "expected": expect_value,
                "assert_type": assert_type,
                "element_path": element_path,
                "attr": attr,
                "error": assert_result.get("error")
            }
            
        except Exception as e:
            return {"success": False, "error": f"断言处理异常: {str(e)}"}

    def _extract_attribute_value(self, element_data: Dict, attr_path: str) -> Any:
        """从元素数据中提取属性值"""
        if not attr_path:
            return None
        
        current = element_data
        for part in attr_path.split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _perform_assertion(self, actual: Any, expected: Any, assert_type: str) -> Dict:
        """执行断言比较"""
        try:
            assert_type = assert_type.lower()
            
            if assert_type == "equal":
                success = (actual == expected)
            elif assert_type == "notequal":
                success = (actual != expected)
            elif assert_type == "regex":
                import re
                success = isinstance(expected, str) and re.search(expected, str(actual)) is not None
            elif assert_type == "contains":
                success = expected in actual if isinstance(actual, (str, list, dict)) else False
            elif assert_type == "gt":
                success = actual > expected
            elif assert_type == "gte":
                success = actual >= expected
            elif assert_type == "lt":
                success = actual < expected
            elif assert_type == "lte":
                success = actual <= expected
            elif assert_type == "isnone":
                success = (actual is None)
            elif assert_type == "isnotnone":
                success = (actual is not None)
            elif assert_type == "approx":
                tolerance = 1e-6
                success = abs(float(actual) - float(expected)) <= tolerance
            else:
                return {"success": False, "error": f"不支持的断言类型: {assert_type}"}
            
            if not success:
                return {
                    "success": False, 
                    "error": f"断言失败: {assert_type}, 实际值: {actual}, 期望值: {expected}"
                }
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": f"断言执行异常: {str(e)}"}

    def register_app(self, app_name: str, app_info: Dict = None) -> bool:
        """注册应用"""
        success = self.machine_operator.register_app(app_name, app_info)
        
        if success:
            # 记录日志
            if self.log_collector:
                self.log_collector.add_log("INFO", f"应用 {app_name} 注册成功", "app_registration")
            
            # 如果连接到测试服务器，同步应用注册事件
            if self.test_server_connected:
                self._sync_event_to_server("app_launched", app_name, {"app_info": app_info or {}})
        else:
            if self.log_collector:
                self.log_collector.add_log("ERROR", f"应用 {app_name} 注册失败", "app_registration")
        
        return success

    def load_common_components(self, config_file_path: str) -> bool:
        """
        从JSON配置文件加载常用组件定义
        :param config_file_path: 配置文件路径
        :return: 是否加载成功
        """
        return self.machine_operator.load_common_components(config_file_path)

    def preload_components_for_app(self, app_name: str) -> Dict:
        """
        为指定应用预加载常用组件到缓存
        :param app_name: 应用名称
        :return: 预加载结果统计
        """
        return self.machine_operator.preload_components_for_app(app_name)

    def preload_all_components(self) -> Dict:
        """
        为所有已注册的应用预加载常用组件
        :return: 预加载结果统计
        """
        return self.machine_operator.preload_all_components()

    def unregister_app(self, app_name: str) -> bool:
        """注销应用"""
        success = self.machine_operator.unregister_app(app_name)
        
        if success:
            # 如果连接到测试服务器，同步应用注销事件
            if self.test_server_connected:
                self._sync_event_to_server("app_closed", app_name, {})
        
        return success

    def _sync_event_to_server(self, event_type: str, app_name: str, data: Dict) -> None:
        """同步事件到测试服务器"""
        if not self.test_server_connected:
            return
            
        try:
            event_data = {
                "type": MessageTypes.EVENT_SYNC,
                "data": {
                    "type": event_type,
                    "app_name": app_name,
                    "data": data
                },
                "protocol_version": PROTOCOL_VERSION
            }
            self.test_server_socket.sendall(wrap_outgoing(event_data, self._enable_encryption, self._shared_secret))
        except Exception as e:
            print(f"同步事件到服务器失败: {str(e)}")

    def _sync_registered_apps_to_server(self) -> None:
        """将已注册的应用同步到测试服务器"""
        if not self.test_server_connected:
            return
            
        try:
            # 获取所有已注册的应用
            for app_name, app_info in self.machine_operator.apps.items():
                # 向测试服务器发送应用注册请求
                app_registration_request = {
                    "type": MessageTypes.REGISTER_APP,
                    "data": {
                        "app_name": app_name,
                        "app_info": app_info.get("info", {}),
                        "machine_id": self.machine_id
                    },
                    "protocol_version": PROTOCOL_VERSION
                }
                self.test_server_socket.sendall(wrap_outgoing(app_registration_request, self._enable_encryption, self._shared_secret))
                print(f"同步应用 {app_name} 到测试服务器")
                
        except Exception as e:
            print(f"同步已注册应用到服务器失败: {str(e)}")

    def _emit_event(self, event_type: str, data: Dict = None) -> None:
        """向本地UI事件队列上报事件"""
        try:
            event = {
                "timestamp": time.time(),
                "type": event_type,
                "data": data or {}
            }
            self.ui_event_queue.put(event)
        except Exception:
            pass

    def start(self, app_names: Optional[List[str]] = None) -> None:
        """
        启动通信服务，开始监听8888端口
        :param app_names: 被测应用名称列表（可选）
        """
        try:
            # 初始化日志收集器
            self.log_collector = init_global_logging(self.machine_id)
            print(f"日志收集器已启动，机器ID: {self.machine_id}")
            
            # 绑定端口并开始监听
            self.server_socket.bind((self.bind_host, self.bind_port))
            self.server_socket.listen(5)  # 最大等待连接数
            self.is_running = True
            print(f"被测试机器通信服务已启动，监听 {self.bind_host}:{self.bind_port}")
            print(f"机器ID: {self.machine_id}")

            # 如果指定了应用，注册这些应用
            if app_names:
                for app_name in app_names:
                    self.register_app(app_name)
            else:
                # 否则监控所有可用应用，并输出当前可检测到的应用列表
                print("未指定应用，将监控所有可用应用")
                try:
                    # 尝试列出可用应用名称
                    apps = []
                    root = dogtail.tree.root
                    for child in getattr(root, 'children', []) or []:
                        name = getattr(child, 'name', None)
                        if name:
                            apps.append(name)
                    if apps:
                        print("当前可用应用列表:")
                        for idx, nm in enumerate(apps, 1):
                            print(f"  {idx}. {nm}")
                    else:
                        print("未能获取可用应用列表（可能权限或环境限制）")
                except Exception as e:
                    print(f"列举可用应用失败: {str(e)}")

            # 不再主动连接测试服务器，等待测试服务器主动连接
            print("等待测试服务器主动连接...")

            # 循环处理连接
            while self.is_running:
                test_server_socket, test_server_addr = self.server_socket.accept()
                print(f"收到来自 {test_server_addr} 的连接")
                # 仅处理测试服务器连接，其他直接关闭
                if self.test_server_connected:
                    print(f"已存在测试服务器连接，拒绝新的连接 {test_server_addr}")
                    try:
                        test_server_socket.close()
                    except Exception:
                        pass
                    continue

                if not self._is_test_server_connection_request(test_server_addr):
                    print(f"来源 {test_server_addr} 不在允许范围（本机或 192.168.*.*），已拒绝")
                    try:
                        test_server_socket.close()
                    except Exception:
                        pass
                    continue

                if not self._handle_test_server_connection(test_server_socket, test_server_addr):
                    try:
                        test_server_socket.close()
                    except Exception:
                        pass
                    continue
                # 连接成功后，由测试服务器通信线程接管保持长连

        except Exception as e:
            print(f"服务启动失败: {str(e)}")
            self.stop()

    def _is_test_server_connection_request(self, test_server_addr: tuple) -> bool:
        """判断该来源是否属于测试服务器范围（用于握手触发）"""
        try:
            client_ip = test_server_addr[0]
            allowed_hosts = ["127.0.0.1", "localhost", "0.0.0.0"]
            return client_ip in allowed_hosts or client_ip.startswith("192.168.")
        except Exception:
            return False

    def _handle_regular_request(self) -> None:
        """处理普通请求"""
        try:
            # 保持连接，循环处理请求
            while self.test_server_connected and self.is_running:
                # 接收请求数据（最大1MB）
                request_bytes = self.test_server_socket.recv(1024 * 1024)
                if not request_bytes:
                    print(f" {self.test_server_addr} 断开连接")
                    break
                # 解析请求（JSON或加密信封）
                try:
                    request = unwrap_incoming(request_bytes, self._enable_encryption, self._shared_secret)
                except Exception:
                    request = json.loads(request_bytes.decode('utf-8'))
                # 基础校验与版本比对
                validate = basic_validate_message(request)
                if not validate.get("success"):
                    error_msg = {"success": False, "error": f"非法消息: {validate.get('error')}", "protocol_version": PROTOCOL_VERSION}
                    try:
                        self.test_server_socket.sendall(wrap_outgoing(error_msg, self._enable_encryption, self._shared_secret))
                    except Exception:
                        pass
                    continue
                req_ver = re