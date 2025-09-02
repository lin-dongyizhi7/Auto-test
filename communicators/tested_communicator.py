'''
Author: 凛冬已至 2985956026@qq.com
Date: 2025-07-24 13:25:17
LastEditors: 凛冬已至 2985956026@qq.com
LastEditTime: 2025-09-02 12:39:14
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
from typing import Dict, List, Optional, Set
from collections import OrderedDict



class LRUCache:
    """LRU缓存实现，用于缓存元素查询结果"""
    
    def __init__(self, capacity: int = 50):
        """
        初始化LRU缓存
        :param capacity: 缓存最大容量
        """
        self.capacity = capacity
        self.cache = OrderedDict()  # 使用OrderedDict维护元素顺序，便于实现LRU
    
    def get(self, key: str) -> Optional[any]:
        """
        获取缓存中的元素
        :param key: 元素路径作为缓存键
        :return: 缓存的元素，如果不存在则返回None
        """
        if key not in self.cache:
            return None
        
        # 将访问的元素移到末尾，表示最近使用
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value: any) -> None:
        """
        添加元素到缓存
        :param key: 元素路径作为缓存键
        :param value: 要缓存的元素
        """
        if key in self.cache:
            # 如果已存在，先移到末尾
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.capacity:
            # 如果缓存满了，移除最久未使用的元素（头部元素）
            self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()


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
        
        # 多应用管理
        self.apps: Dict[str, Dict] = {}  # app_name -> app_info
        self.app_regions: Dict[str, List[int]] = {}  # app_name -> region
        self.element_caches: Dict[str, LRUCache] = {}  # app_name -> cache
        
        # 测试服务器连接（被动模式）
        self.test_server_socket = None
        self.test_server_connected = False
        self.test_server_thread = None
        self.test_server_send_lock = threading.Lock()
        self.test_server_connection_info = None  # 存储测试服务器连接信息
        
        # 事件同步
        self.event_queue = queue.Queue()
        self.event_thread = None
        
        # 线程管理
        self.server_thread = None
        self.client_threads: Set[threading.Thread] = set()
        
        # 常用组件预加载
        self.common_components: Dict[str, Dict] = {}  # app_name -> components
        self.preload_enabled = False

    def _get_app_region(self, app_name: str) -> Optional[List[int]]:
        """获取指定应用的窗口信息（位置和大小）"""
        if app_name not in self.apps:
            return None
            
        try:
            # 通过dogtail获取应用窗口位置和大小
            app = dogtail.tree.root.application(app_name)
            if app and app.children:
                window = app.children[0]  # 假设第一个子元素是主窗口
                x, y = window.position
                width, height = window.size
                region = [x, y, width, height]
                self.app_regions[app_name] = region
                print(f"获取应用 {app_name} 窗口信息: 位置({x},{y}), 大小({width}x{height})")
                return region
        except Exception as e:
            print(f"获取应用 {app_name} 窗口信息失败: {str(e)}")
            return None

    def _get_screenshot(self, app_name: str, region: Optional[List[int]] = None) -> str:
        """
        截取指定应用或指定区域的屏幕，返回16进制编码
        :param app_name: 应用名称
        :param region: 可选区域 [x, y, width, height]，None表示应用窗口区域
        """
        # 1. 验证区域参数合法性
        use_region = region if region is not None else self.app_regions.get(app_name)
        
        if use_region:
            if len(use_region) != 4:
                return {
                    "success": False,
                    "error": f"区域参数格式错误，需为[x, y, width, height]，实际为{use_region}"
                }
            x, y, w, h = use_region
            if w <= 0 or h <= 0:
                return {
                    "success": False,
                    "error": f"区域尺寸无效（宽高必须为正数）：width={w}, height={h}"
                }

        # 2. 执行截图操作
        try:
            if use_region:
                screenshot = pyautogui.screenshot(region=use_region)
            else:
                screenshot = pyautogui.screenshot()
        except Exception as e:
            return {
                "success": False,
                "error": f"截图操作失败：{str(e)}（可能区域超出屏幕范围）"
            }

        # 3. 图片编码为十六进制
        buffer = io.BytesIO()
        try:
            # 限制图片质量，避免数据量过大
            screenshot.save(buffer, format="PNG", optimize=True)
            img_bytes = buffer.getvalue()
        except Exception as e:
            return {
                "success": False,
                "error": f"图片编码失败：{str(e)}"
            }
        
        # 4. 验证编码结果
        img_hex = img_bytes.hex()
        return img_hex
        
    def _get_element(self, app_name: str, element_path: str, role_name_list: Optional[List[Optional[str]]] = None) -> Dict:
        """
        调用dogtail查询指定应用的元素信息，使用LRU缓存加速重复查询
        :param app_name: 应用名称
        :param element_path: 元素路径（如"菜单/文件/新建"）
        :param role_name_list: 角色名列表，项数与路径级数相等，每项可为空
        :return: 包含元素位置、尺寸等信息的字典
        """
        print(f"查询应用 {app_name} 的元素: {element_path}, 角色列表: {role_name_list}")
        
        # 1. 确保应用缓存存在
        if app_name not in self.element_caches:
            self.element_caches[app_name] = LRUCache(capacity=20)
        
        cache = self.element_caches[app_name]
        
        # 2. 处理路径和角色列表，生成缓存键
        path_parts = [part.strip() for part in element_path.split('/') if part.strip()]
        if not path_parts:
            return {"success": False, "error": "元素路径不能为空"}

        # 调整角色列表长度与路径匹配
        adjusted_roles = []
        for i in range(len(path_parts)):
            if role_name_list and i < len(role_name_list):
                adjusted_roles.append(role_name_list[i] if role_name_list[i] else None)
            else:
                adjusted_roles.append(None)
        
        # 生成当前元素的完整缓存键
        full_cache_key = (element_path, tuple(adjusted_roles))

        # 3. 检查当前元素是否在缓存中
        cached_result = cache.get(full_cache_key)
        if cached_result:
            print(f"✅ 缓存命中: {app_name} - {element_path}")
            print(f"位置: {cached_result['position']}, 尺寸: {cached_result['size']}, 名称: {cached_result['name']}, 角色: {cached_result['role_name']}")
            result = {
                "success": True,
                "data": {
                    "position": cached_result["position"],
                    "size": cached_result["size"],
                    "name": cached_result["name"],
                    "role_name": cached_result["role_name"],
                }
            }
            return result

        # 4. 查找最近的已缓存父级元素
        parent_element = None
        parent_path_parts = []
        remaining_path_parts = path_parts.copy()
        remaining_roles = adjusted_roles.copy()

        # 从最长的父路径开始检查（逐级缩短路径）
        for i in range(len(path_parts)-1, 0, -1):
            parent_path_parts = path_parts[:i]
            parent_path = '/'.join(parent_path_parts)
            parent_roles = adjusted_roles[:i]
            parent_cache_key = (parent_path, tuple(parent_roles))

            # 检查父级缓存
            parent_cached = cache.get(parent_cache_key)
            if parent_cached:
                # 父级存在缓存，提取父元素对象
                parent_element = parent_cached["data"].get("element_object")
                if parent_element:
                    # 计算剩余路径和角色
                    remaining_path_parts = path_parts[i:]
                    remaining_roles = adjusted_roles[i:]
                    print(f"🔼 找到父级缓存: {app_name} - {parent_path}，从父级开始查询剩余路径")
                    break

        # 5. 执行元素查找（从父级或应用根节点开始）
        try:
            # 获取应用实例
            app = dogtail.tree.root.application(app_name)
            if not app:
                return {"success": False, "error": f"应用 {app_name} 未找到"}

            # 确定查找起点（父级缓存或应用根节点）
            current_element = parent_element if parent_element else app

            # 遍历剩余路径部分
            for i, part in enumerate(remaining_path_parts):
                current_role = remaining_roles[i]
                if current_role:
                    found_element = current_element.child(name=part, roleName=current_role)
                else:
                    found_element = current_element.child(name=part)

                if not found_element:
                    # 构建错误路径（完整路径的前半部分）
                    error_path_parts = parent_path_parts + remaining_path_parts[:i+1]
                    error_path = '/'.join(error_path_parts)
                    error_msg = f"应用 {app_name} 中元素不存在: {error_path}"
                    if current_role:
                        error_msg += f" (角色: {current_role})"
                    return {"success": False, "error": error_msg}
                current_element = found_element

            # 提取元素信息
            x, y = current_element.position
            width, height = current_element.size
            print(f"🔍 查询成功: {app_name} - {element_path}，位置: ({x}, {y}), 尺寸: ({width}, {height})")
            store_data = {
                "position": {"x": x, "y": y},
                "size": {"width": width, "height": height},
                "name": current_element.name,
                "role_name": current_element.roleName,
                "element_object": current_element  # 存储元素对象供子元素查询
            }
            result = {
                "success": True,
                "data": {
                    "position": {"x": x, "y": y},
                    "size": {"width": width, "height": height},
                    "name": current_element.name,
                    "role_name": current_element.roleName,
                }
            }

            # 6. 存入缓存
            cache.put(full_cache_key, store_data)
            print(f"📌 缓存新增: {app_name} - {element_path} (缓存大小: {len(cache.cache)}/{cache.capacity})")
            return result

        except Exception as e:
            return {"success": False, "error": f"元素查询失败: {str(e)}"}

    def _execute_commands(self, app_name: str, commands: List[Dict]) -> Dict:
        """
        执行测试者发送的指令集
        :param app_name: 应用名称
        :param commands: 指令列表（如鼠标移动、点击等）
        :return: 执行结果汇总
        """
        results = []
        for cmd in commands:
            try:
                action = cmd["action"]
                params = cmd["params"]
                print(f"在应用 {app_name} 上执行指令: {action}，参数: {params}")

                result = {"action": action, "success": True}

                # 映射指令到pyautogui的实际操作
                if action == "mouse_move":
                    # 鼠标移动到绝对坐标，duration控制移动时间（秒）
                    pyautogui.moveTo(params["x"], params["y"], duration=0.1)

                elif action == "mouse_click":
                    # 鼠标点击，支持左右键和点击次数
                    button = params.get("button", "left")
                    clicks = params.get("clicks", 1)
                    interval = params.get("interval", 0.1)
                    pyautogui.click(
                        x=params["x"], 
                        y=params["y"], 
                        button=button,
                        clicks=clicks,
                        interval=interval
                    )

                elif action == "mouse_press":
                    # 按下鼠标键
                    pyautogui.mouseDown(button=params.get("button", "left"))

                elif action == "mouse_release":
                    # 释放鼠标键
                    pyautogui.mouseUp(button=params.get("button", "left"))

                elif action == "hotkey":
                    # 执行组合键（如["ctrl", "a"]）
                    # 将参数转换为字符串并小写化（pyautogui要求小写）
                    keys = [str(key).lower() for key in params["keys"]]
                    pyautogui.hotkey(*keys)

                elif action == "key_press":
                    # 执行单个按键
                    key = str(params["key"]).lower()
                    pyautogui.press(key)
                    
                else:
                    result = {"action": action, "success": False, "error": "未知指令"}

                results.append(result)
                time.sleep(0.2)  # 操作间增加短暂延迟，确保执行稳定

            except Exception as e:
                results.append({
                    "action": action,
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": all(r["success"] for r in results),
            "results": results
        }

    def _handle_test_server_connection(self, client_socket: socket.socket, client_addr: tuple) -> bool:
        """
        处理测试服务器的连接请求，验证IP和端口
        :param client_socket: 客户端socket
        :param client_addr: 客户端地址 (ip, port)
        :return: 是否接受连接
        """
        try:
            # 接收连接验证请求
            request_data = client_socket.recv(1024).decode('utf-8')
            if not request_data:
                return False
            
            request = json.loads(request_data)
            if request.get("type") != "connection_request":
                print(f"收到来自 {client_addr} 的无效连接请求类型: {request.get('type')}")
                return False
            
            # 验证连接信息
            connection_data = request.get("data", {})
            server_host = connection_data.get("server_host")
            server_port = connection_data.get("server_port")
            
            if not server_host or not server_port:
                print(f"连接请求缺少必要信息: server_host={server_host}, server_port={server_port}")
                return False
            
            # 验证IP地址（允许本地连接和指定IP）
            allowed_hosts = ["127.0.0.1", "localhost", "0.0.0.0"]
            if server_host not in allowed_hosts and not server_host.startswith("192.168."):
                print(f"拒绝来自 {client_addr} 的连接，IP地址 {server_host} 不在允许列表中")
                return False
            
            # 验证端口（通常测试服务器使用8888端口）
            if server_port != 8888:
                print(f"拒绝来自 {client_addr} 的连接，端口 {server_port} 不在允许列表中")
                return False
            
            print(f"验证通过，接受来自测试服务器 {client_addr} 的连接")
            
            # 存储连接信息
            self.test_server_connection_info = {
                "host": server_host,
                "port": server_port,
                "client_addr": client_addr
            }
            
            # 发送连接确认
            response = {
                "type": "connection_response",
                "success": True,
                "data": {
                    "machine_id": self.machine_id,
                    "machine_info": {
                        "host": self.bind_host,
                        "port": self.bind_port,
                        "platform": "linux",
                        "timestamp": time.time()
                    }
                }
            }
            client_socket.sendall(json.dumps(response).encode('utf-8'))
            
            # 设置测试服务器连接
            self.test_server_socket = client_socket
            self.test_server_connected = True
            
            # 启动测试服务器通信线程
            self.test_server_thread = threading.Thread(target=self._test_server_communication, daemon=True)
            self.test_server_thread.start()
            
            # 将已注册的应用同步到测试服务器
            try:
                for app_name, app in self.apps.items():
                    self._register_app_to_server(app_name, app.get("info", {}))
            except Exception as e:
                print(f"同步已注册应用到测试服务器失败: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"处理测试服务器连接请求失败: {str(e)}")
            return False

    def _test_server_communication(self) -> None:
        """与测试服务器的通信线程"""
        while self.test_server_connected and self.is_running:
            try:
                # 接收来自测试服务器的请求
                data = self.test_server_socket.recv(1024 * 1024).decode('utf-8')
                if not data:
                    break
                
                request = json.loads(data)
                # 仅处理服务端发起的请求类型，忽略我们主动上报后的响应包
                if request.get("type") in {"get_screenshot", "get_element", "exec_commands"}:
                    response = self._handle_test_server_request(request)
                    # 发送响应
                    with self.test_server_send_lock:
                        self.test_server_socket.sendall(json.dumps(response).encode('utf-8'))
                else:
                    # 忽略非请求类消息（如对sync_event/register_app的响应）
                    continue
                
            except json.JSONDecodeError:
                error_msg = {"success": False, "error": "无效的JSON格式"}
                self.test_server_socket.sendall(json.dumps(error_msg).encode('utf-8'))
            except Exception as e:
                print(f"与测试服务器通信时发生错误: {str(e)}")
                break
        
        self.test_server_connected = False
        print("与测试服务器的连接已断开")

    def _register_app_to_server(self, app_name: str, app_info: Dict) -> None:
        """将应用注册到测试服务器（使用现有长连接，忽略响应）"""
        if not self.test_server_connected:
            return
        try:
            payload = {
                "type": "register_app",
                "data": {
                    "app_name": app_name,
                    "app_info": app_info or {}
                }
            }
            with self.test_server_send_lock:
                self.test_server_socket.sendall(json.dumps(payload).encode('utf-8'))
        except Exception as e:
            print(f"向测试服务器注册应用失败: {str(e)}")

    def _handle_test_server_request(self, request: Dict) -> Dict:
        """处理来自测试服务器的请求"""
        request_type = request.get("type")
        
        if request_type == "get_screenshot":
            app_name = request.get("data", {}).get("app_name")
            region = request.get("data", {}).get("region")
            return self._handle_screenshot_request(app_name, region)
        elif request_type == "get_element":
            app_name = request.get("data", {}).get("app_name")
            element_path = request.get("data", {}).get("element_path")
            role_name_list = request.get("data", {}).get("role_name_list")
            return self._handle_element_request(app_name, element_path, role_name_list)
        elif request_type == "exec_commands":
            app_name = request.get("data", {}).get("app_name")
            commands = request.get("data", {}).get("commands")
            return self._handle_command_request(app_name, commands)
        else:
            return {"success": False, "error": f"未知请求类型: {request_type}"}

    def _handle_screenshot_request(self, app_name: str, region: Optional[List[int]] = None) -> Dict:
        """处理截图请求"""
        if not app_name:
            return {"success": False, "error": "应用名称不能为空"}
        
        if app_name not in self.apps:
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
        
        if app_name not in self.apps:
            return {"success": False, "error": f"应用 {app_name} 未注册"}
        
        return self._get_element(app_name, element_path, role_name_list)

    def _handle_command_request(self, app_name: str, commands: List[Dict]) -> Dict:
        """处理命令执行请求"""
        if not app_name or not commands:
            return {"success": False, "error": "应用名称和命令不能为空"}
        
        if app_name not in self.apps:
            return {"success": False, "error": f"应用 {app_name} 未注册"}
        
        return self._execute_commands(app_name, commands)

    def register_app(self, app_name: str, app_info: Dict = None) -> bool:
        """注册应用"""
        try:
            # 检查应用是否存在
            app = dogtail.tree.root.application(app_name)
            if not app:
                print(f"应用 {app_name} 未找到，无法注册")
                return False
            
            # 注册应用
            self.apps[app_name] = {
                "name": app_name,
                "info": app_info or {},
                "registered_at": time.time(),
                "status": "running"
            }
            
            # 初始化应用缓存
            self.element_caches[app_name] = LRUCache(capacity=20)
            
            # 获取应用窗口区域
            self._get_app_region(app_name)
            
            print(f"应用 {app_name} 注册成功")
            
            # 如果连接到测试服务器，同步应用注册事件
            if self.test_server_connected:
                self._sync_event_to_server("app_launched", app_name, {"app_info": app_info or {}})
            
            return True
            
        except Exception as e:
            print(f"注册应用 {app_name} 失败: {str(e)}")
            return False

    def load_common_components(self, config_file_path: str) -> bool:
        """
        从JSON配置文件加载常用组件定义
        :param config_file_path: 配置文件路径
        :return: 是否加载成功
        """
        try:
            if not os.path.exists(config_file_path):
                print(f"配置文件不存在: {config_file_path}")
                return False
            
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if 'components' not in config_data:
                print("配置文件格式错误：缺少'components'字段")
                return False
            
            self.common_components = config_data['components']
            self.preload_enabled = True
            
            print(f"成功加载常用组件配置，包含 {len(self.common_components)} 个应用的组件定义")
            for app_name, components in self.common_components.items():
                element_count = len(components.get('elements', []))
                print(f"  - {app_name}: {element_count} 个组件")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"配置文件JSON格式错误: {str(e)}")
            return False
        except Exception as e:
            print(f"加载常用组件配置失败: {str(e)}")
            return False

    def preload_components_for_app(self, app_name: str) -> Dict:
        """
        为指定应用预加载常用组件到缓存
        :param app_name: 应用名称
        :return: 预加载结果统计
        """
        if not self.preload_enabled or app_name not in self.common_components:
            return {
                "success": False,
                "error": f"应用 {app_name} 没有预定义的常用组件"
            }
        
        if app_name not in self.apps:
            return {
                "success": False,
                "error": f"应用 {app_name} 未注册"
            }
        
        components = self.common_components[app_name]
        elements = components.get('elements', [])
        
        if not elements:
            return {
                "success": True,
                "message": f"应用 {app_name} 没有需要预加载的组件",
                "stats": {"total": 0, "success": 0, "failed": 0}
            }
        
        print(f"开始为应用 {app_name} 预加载 {len(elements)} 个常用组件...")
        
        success_count = 0
        failed_count = 0
        failed_elements = []
        
        for element in elements:
            try:
                element_path = element['path']
                role_name = element.get('role_name')
                element_name = element.get('name', element_path)
                
                # 调用_get_element方法预加载组件到缓存
                result = self._get_element(app_name, element_path, [role_name] if role_name else None)
                
                if result.get('success'):
                    success_count += 1
                    print(f"  ✅ 预加载成功: {element_name} ({element_path})")
                else:
                    failed_count += 1
                    error_msg = result.get('error', '未知错误')
                    failed_elements.append({
                        'name': element_name,
                        'path': element_path,
                        'error': error_msg
                    })
                    print(f"  ❌ 预加载失败: {element_name} ({element_path}) - {error_msg}")
                
                # 添加短暂延迟，避免过快查询导致系统负载过高
                time.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                failed_elements.append({
                    'name': element.get('name', '未知'),
                    'path': element.get('path', '未知'),
                    'error': str(e)
                })
                print(f"  ❌ 预加载异常: {element.get('name', '未知')} - {str(e)}")
        
        result = {
            "success": True,
            "message": f"应用 {app_name} 组件预加载完成",
            "stats": {
                "total": len(elements),
                "success": success_count,
                "failed": failed_count
            },
            "failed_elements": failed_elements
        }
        
        print(f"预加载完成: 总计 {len(elements)} 个，成功 {success_count} 个，失败 {failed_count} 个")
        return result

    def preload_all_components(self) -> Dict:
        """
        为所有已注册的应用预加载常用组件
        :return: 预加载结果统计
        """
        if not self.preload_enabled:
            return {
                "success": False,
                "error": "预加载功能未启用，请先加载配置文件"
            }
        
        if not self.apps:
            return {
                "success": False,
                "error": "没有已注册的应用"
            }
        
        print("开始为所有已注册应用预加载常用组件...")
        
        total_stats = {"total": 0, "success": 0, "failed": 0}
        app_results = {}
        
        for app_name in self.apps.keys():
            if app_name in self.common_components:
                result = self.preload_components_for_app(app_name)
                app_results[app_name] = result
                
                if result.get('success'):
                    stats = result.get('stats', {})
                    total_stats['total'] += stats.get('total', 0)
                    total_stats['success'] += stats.get('success', 0)
                    total_stats['failed'] += stats.get('failed', 0)
            else:
                app_results[app_name] = {
                    "success": True,
                    "message": f"应用 {app_name} 没有预定义的常用组件",
                    "stats": {"total": 0, "success": 0, "failed": 0}
                }
        
        result = {
            "success": True,
            "message": "所有应用组件预加载完成",
            "total_stats": total_stats,
            "app_results": app_results
        }
        
        print(f"全部预加载完成: 总计 {total_stats['total']} 个，成功 {total_stats['success']} 个，失败 {total_stats['failed']} 个")
        return result

    def unregister_app(self, app_name: str) -> bool:
        """注销应用"""
        if app_name in self.apps:
            del self.apps[app_name]
            
            # 清理应用缓存
            if app_name in self.element_caches:
                del self.element_caches[app_name]
            
            # 清理应用区域信息
            if app_name in self.app_regions:
                del self.app_regions[app_name]
            
            print(f"应用 {app_name} 已注销")
            
            # 如果连接到测试服务器，同步应用注销事件
            if self.test_server_connected:
                self._sync_event_to_server("app_closed", app_name, {})
            
            return True
        return False

    def _sync_event_to_server(self, event_type: str, app_name: str, data: Dict) -> None:
        """同步事件到测试服务器"""
        if not self.test_server_connected:
            return
            
        try:
            event_data = {
                "type": "sync_event",
                "data": {
                    "type": event_type,
                    "app_name": app_name,
                    "data": data
                }
            }
            self.test_server_socket.sendall(json.dumps(event_data).encode('utf-8'))
        except Exception as e:
            print(f"同步事件到服务器失败: {str(e)}")

    def start(self, app_names: Optional[List[str]] = None) -> None:
        """
        启动通信服务，开始监听8888端口
        :param app_names: 被测应用名称列表（可选）
        """
        try:
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
                # 否则监控所有可用应用
                print("未指定应用，将监控所有可用应用")

            # 不再主动连接测试服务器，等待测试服务器主动连接
            print("等待测试服务器主动连接...")

            # 循环处理客户端连接
            while self.is_running:
                client_socket, client_addr = self.server_socket.accept()
                print(f"收到来自 {client_addr} 的连接，保持长连接")

                # 为每个客户端创建处理线程
                client_thread = threading.Thread(
                    target=self._handle_client_connection,
                    args=(client_socket, client_addr),
                    daemon=True
                )
                client_thread.start()
                self.client_threads.add(client_thread)

        except Exception as e:
            print(f"服务启动失败: {str(e)}")
            self.stop()

    def _handle_client_connection(self, client_socket: socket.socket, client_addr: tuple) -> None:
        """处理客户端连接"""
        try:
            # 首先检查是否是测试服务器的连接请求
            if self._is_test_server_connection_request(client_addr):
                if self._handle_test_server_connection(client_socket, client_addr):
                    # 测试服务器连接成功，保持连接
                    self._maintain_test_server_connection(client_socket, client_addr)
                else:
                    # 测试服务器连接失败，关闭连接
                    client_socket.close()
                return
            
            # 处理普通客户端连接
            self._handle_regular_client_connection(client_socket, client_addr)

        except Exception as e:
            print(f"处理客户端连接失败: {str(e)}")
            client_socket.close()

    def _is_test_server_connection_request(self, client_addr: tuple) -> bool:
        """判断是否是测试服务器的连接请求"""
        # 检查IP地址是否在允许的测试服务器范围内
        client_ip = client_addr[0]
        allowed_hosts = ["127.0.0.1", "localhost", "0.0.0.0"]
        return client_ip in allowed_hosts or client_ip.startswith("192.168.")

    def _maintain_test_server_connection(self, client_socket: socket.socket, client_addr: tuple) -> None:
        """维护与测试服务器的连接"""
        try:
            while self.test_server_connected and self.is_running:
                # 接收来自测试服务器的请求
                request_data = client_socket.recv(1024 * 1024).decode('utf-8')
                if not request_data:
                    print(f"测试服务器 {client_addr} 主动断开连接")
                    break

                request = json.loads(request_data)
                response = self._handle_test_server_request(request)
                
                # 发送响应
                with self.test_server_send_lock:
                    client_socket.sendall(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f"与测试服务器 {client_addr} 通信时发生错误: {str(e)}")
        finally:
            self.test_server_connected = False
            if self.test_server_socket == client_socket:
                self.test_server_socket = None
            print(f"与测试服务器 {client_addr} 的连接已断开")

    def _handle_regular_client_connection(self, client_socket: socket.socket, client_addr: tuple) -> None:
        """处理普通客户端连接"""
        try:
            # 保持连接，循环处理请求
            while self.is_running:
                # 接收请求数据（最大1MB）
                request_data = client_socket.recv(1024 * 1024).decode('utf-8')
                if not request_data:
                    print(f"客户端 {client_addr} 主动断开连接")
                    break

                # 解析请求（JSON格式）
                request = json.loads(request_data)
                response = {"success": False, "error": "未知请求类型"}

                # 处理不同类型的请求
                if request["type"] == "get_app_region":
                    app_name = request["data"].get("app_name")
                    if app_name and app_name in self.apps:
                        app_region = self._get_app_region(app_name)
                        if app_region:
                            response = {
                                "success": True,
                                "data": {"app_region": app_region}
                            }
                        else:
                            response = {"success": False, "error": "无法获取应用窗口信息"}
                    else:
                        response = {"success": False, "error": "应用名称无效或未注册"}

                elif request["type"] == "get_screenshot":
                    app_name = request["data"].get("app_name")
                    region = request["data"].get("region")
                    response = self._handle_screenshot_request(app_name, region)

                elif request["type"] == "get_element":
                    # 处理元素查询请求
                    app_name = request["data"].get("app_name")
                    element_path = request["data"].get("element_path")
                    role_name_list = request["data"].get("role_name_list")
                    response = self._handle_element_request(app_name, element_path, role_name_list)

                elif request["type"] == "exec_commands":
                    # 处理指令集执行请求
                    app_name = request["data"].get("app_name")
                    commands = request["data"].get("commands")
                    response = self._handle_command_request(app_name, commands)

                elif request["type"] == "register_app":
                    # 处理应用注册请求
                    app_name = request["data"].get("app_name")
                    app_info = request["data"].get("app_info", {})
                    success = self.register_app(app_name, app_info)
                    response = {"success": success, "message": "应用注册成功" if success else "应用注册失败"}

                elif request["type"] == "unregister_app":
                    # 处理应用注销请求
                    app_name = request["data"].get("app_name")
                    success = self.unregister_app(app_name)
                    response = {"success": success, "message": "应用注销成功" if success else "应用注销失败"}

                elif request["type"] == "disconnect":
                    # 处理主动断开连接请求
                    print(f"收到 {client_addr} 的断开连接请求")
                    response = {"success": True, "message": "连接已断开"}
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    break

                # 发送响应
                client_socket.sendall(json.dumps(response).encode('utf-8'))

        except json.JSONDecodeError:
            error_msg = {"success": False, "error": "无效的JSON格式"}
            client_socket.sendall(json.dumps(error_msg).encode('utf-8'))
        except Exception as e:
            error_msg = {"success": False, "error": f"处理请求失败: {str(e)}"}
            client_socket.sendall(json.dumps(error_msg).encode('utf-8'))
        finally:
            client_socket.close()
            print(f"与 {client_addr} 的连接已关闭")

    def get_test_server_status(self) -> Dict:
        """获取测试服务器连接状态"""
        if not self.test_server_connected:
            return {
                "connected": False,
                "message": "未连接"
            }
        
        return {
            "connected": True,
            "message": "已连接",
            "server_info": self.test_server_connection_info,
            "machine_id": self.machine_id
        }

    def stop(self) -> None:
        """停止通信服务"""
        self.is_running = False
        
        # 关闭测试服务器连接
        if self.test_server_socket:
            try:
                self.test_server_socket.close()
            except:
                pass
            self.test_server_connected = False
        
        # 关闭本地服务器
        if self.server_socket:
            self.server_socket.close()
        
        # 等待所有客户端线程结束
        for thread in list(self.client_threads):
            if thread.is_alive():
                thread.join(timeout=1)
        
        print("通信服务已停止")


def interactive_setup():
    """交互式配置设置"""
    print("=" * 60)
    print("被测试机器通信服务 - 交互式配置")
    print("=" * 60)
    
    # 获取监听端口
    while True:
        try:
            port_input = input("请输入监听端口 (默认: 8888): ").strip()
            if not port_input:
                port = 8888
            else:
                port = int(port_input)
                if 1 <= port <= 65535:
                    break
                else:
                    print("❌ 端口号必须在 1-65535 范围内")
        except ValueError:
            print("❌ 请输入有效的端口号")
    
    # 获取机器ID
    machine_id = input("请输入机器ID (默认: test_machine_001): ").strip()
    if not machine_id:
        machine_id = "test_machine_001"
    
    # 获取监控应用列表
    print("\n可用的应用类型:")
    print("1. calculator (计算器)")
    print("2. gedit (文本编辑器)")
    print("3. firefox (浏览器)")
    print("4. terminal (终端)")
    print("5. nautilus (文件管理器)")
    
    apps_input = input("请输入要监控的应用名称，用空格分隔 (默认: calculator gedit): ").strip()
    if not apps_input:
        apps = ["calculator", "gedit"]
    else:
        apps = [app.strip() for app in apps_input.split()]
    
    # 获取组件配置文件路径
    print("\n可用的配置文件:")
    print("1. common_components.json (中文版)")
    print("2. common_components_en.json (英文版)")
    
    config_choice = input("请选择配置文件 (1/2，默认: 1): ").strip()
    if config_choice == "2":
        config_file = "common_components_en.json"
    else:
        config_file = "common_components.json"
    
    # 获取预加载设置
    preload_input = input("是否启用常用组件预加载功能? (y/n，默认: y): ").strip().lower()
    enable_preload = preload_input in ['', 'y', 'yes', '是']
    
    return {
        'port': port,
        'machine_id': machine_id,
        'apps': apps,
        'config_file': config_file,
        'enable_preload': enable_preload
    }

def display_config(config):
    """显示配置信息"""
    print("\n" + "=" * 60)
    print("配置确认")
    print("=" * 60)
    print(f"监听端口: {config['port']}")
    print(f"机器ID: {config['machine_id']}")
    print(f"监控应用: {', '.join(config['apps'])}")
    print(f"组件配置文件: {config['config_file']}")
    print(f"预加载功能: {'启用' if config['enable_preload'] else '禁用'}")
    print("=" * 60)
    
    confirm = input("\n确认启动服务? (y/n，默认: y): ").strip().lower()
    return confirm in ['', 'y', 'yes', '是']

def interactive_menu(communicator):
    """交互式菜单"""
    while True:
        print("\n" + "=" * 40)
        print("服务管理菜单")
        print("=" * 40)
        print("1. 查看服务状态")
        print("2. 查看已注册应用")
        print("3. 手动注册应用")
        print("4. 注销应用")
        print("5. 预加载组件")
        print("6. 查看缓存状态")
        print("7. 重新加载配置文件")
        print("8. 停止服务")
        print("0. 退出菜单")
        
        choice = input("\n请选择操作 (0-8): ").strip()
        
        if choice == "1":
            show_service_status(communicator)
        elif choice == "2":
            show_registered_apps(communicator)
        elif choice == "3":
            register_app_interactive(communicator)
        elif choice == "4":
            unregister_app_interactive(communicator)
        elif choice == "5":
            preload_components_interactive(communicator)
        elif choice == "6":
            show_cache_status(communicator)
        elif choice == "7":
            reload_config_interactive(communicator)
        elif choice == "8":
            print("正在停止服务...")
            communicator.stop()
            print("服务已停止")
            break
        elif choice == "0":
            print("退出菜单，服务继续运行...")
            break
        else:
            print("❌ 无效选择，请重新输入")

def show_service_status(communicator):
    """显示服务状态"""
    print("\n" + "-" * 30)
    print("服务状态")
    print("-" * 30)
    print(f"运行状态: {'运行中' if communicator.is_running else '已停止'}")
    print(f"监听地址: {communicator.bind_host}:{communicator.bind_port}")
    print(f"机器ID: {communicator.machine_id}")
    print(f"预加载功能: {'启用' if communicator.preload_enabled else '禁用'}")
    
    # 测试服务器连接状态
    server_status = communicator.get_test_server_status()
    print(f"测试服务器连接: {'已连接' if server_status['connected'] else '未连接'}")

def show_registered_apps(communicator):
    """显示已注册应用"""
    print("\n" + "-" * 30)
    print("已注册应用")
    print("-" * 30)
    if not communicator.apps:
        print("暂无已注册应用")
    else:
        for app_name, app_info in communicator.apps.items():
            print(f"应用: {app_name}")
            print(f"  状态: {app_info.get('status', '未知')}")
            print(f"  注册时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(app_info.get('registered_at', 0)))}")
            print()

def register_app_interactive(communicator):
    """交互式注册应用"""
    app_name = input("请输入要注册的应用名称: ").strip()
    if not app_name:
        print("❌ 应用名称不能为空")
        return
    
    if app_name in communicator.apps:
        print(f"❌ 应用 {app_name} 已经注册")
        return
    
    success = communicator.register_app(app_name)
    if success:
        print(f"✅ 应用 {app_name} 注册成功")
    else:
        print(f"❌ 应用 {app_name} 注册失败")

def unregister_app_interactive(communicator):
    """交互式注销应用"""
    if not communicator.apps:
        print("❌ 没有已注册的应用")
        return
    
    print("已注册的应用:")
    for i, app_name in enumerate(communicator.apps.keys(), 1):
        print(f"{i}. {app_name}")
    
    try:
        choice = int(input("请选择要注销的应用编号: ")) - 1
        app_names = list(communicator.apps.keys())
        if 0 <= choice < len(app_names):
            app_name = app_names[choice]
            success = communicator.unregister_app(app_name)
            if success:
                print(f"✅ 应用 {app_name} 注销成功")
            else:
                print(f"❌ 应用 {app_name} 注销失败")
        else:
            print("❌ 无效选择")
    except ValueError:
        print("❌ 请输入有效的数字")

def preload_components_interactive(communicator):
    """交互式预加载组件"""
    if not communicator.preload_enabled:
        print("❌ 预加载功能未启用")
        return
    
    if not communicator.apps:
        print("❌ 没有已注册的应用")
        return
    
    print("选择预加载范围:")
    print("1. 预加载所有应用")
    print("2. 预加载指定应用")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        print("开始预加载所有应用的组件...")
        result = communicator.preload_all_components()
    elif choice == "2":
        print("已注册的应用:")
        for i, app_name in enumerate(communicator.apps.keys(), 1):
            print(f"{i}. {app_name}")
        
        try:
            app_choice = int(input("请选择应用编号: ")) - 1
            app_names = list(communicator.apps.keys())
            if 0 <= app_choice < len(app_names):
                app_name = app_names[app_choice]
                print(f"开始预加载应用 {app_name} 的组件...")
                result = communicator.preload_components_for_app(app_name)
            else:
                print("❌ 无效选择")
                return
        except ValueError:
            print("❌ 请输入有效的数字")
            return
    else:
        print("❌ 无效选择")
        return
    
    # 显示结果
    if result.get('success'):
        stats = result.get('stats', result.get('total_stats', {}))
        print(f"✅ 预加载完成: 总计 {stats.get('total', 0)} 个组件")
        print(f"   成功: {stats.get('success', 0)} 个")
        print(f"   失败: {stats.get('failed', 0)} 个")
    else:
        print(f"❌ 预加载失败: {result.get('error', '未知错误')}")

def show_cache_status(communicator):
    """显示缓存状态"""
    print("\n" + "-" * 30)
    print("缓存状态")
    print("-" * 30)
    if not communicator.element_caches:
        print("暂无缓存数据")
    else:
        for app_name, cache in communicator.element_caches.items():
            print(f"应用: {app_name}")
            print(f"  缓存大小: {len(cache.cache)}/{cache.capacity}")
            print(f"  缓存命中率: {getattr(cache, 'hit_rate', 'N/A')}")

def reload_config_interactive(communicator):
    """交互式重新加载配置"""
    print("可用的配置文件:")
    print("1. common_components.json (中文版)")
    print("2. common_components_en.json (英文版)")
    
    choice = input("请选择配置文件 (1/2): ").strip()
    if choice == "2":
        config_file = "common_components_en.json"
    else:
        config_file = "common_components.json"
    
    # 构建完整路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, config_file)
    
    print(f"正在重新加载配置文件: {config_path}")
    success = communicator.load_common_components(config_path)
    
    if success:
        print("✅ 配置文件重新加载成功")
    else:
        print("❌ 配置文件重新加载失败")

def main():
    """主函数，交互式启动服务"""
    # 交互式配置
    config = interactive_setup()
    
    # 确认配置
    if not display_config(config):
        print("配置已取消，退出程序")
        return
    
    # 初始化服务
    communicator = TestedMachineCommunicator(
        bind_port=config['port'],
        machine_id=config['machine_id']
    )
    
    try:
        # 加载配置文件
        if config['enable_preload']:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, config['config_file'])
            
            print(f"\n正在加载常用组件配置文件: {config_path}")
            if communicator.load_common_components(config_path):
                print("✅ 常用组件配置文件加载成功")
            else:
                print("❌ 常用组件配置文件加载失败，将禁用预加载功能")
                config['enable_preload'] = False
        
        # 启动服务
        print(f"\n正在启动服务，监控应用: {', '.join(config['apps'])}")
        communicator.start(app_names=config['apps'])
        
        # 预加载组件
        if config['enable_preload']:
            print("\n开始预加载常用组件...")
            preload_result = communicator.preload_all_components()
            
            if preload_result.get('success'):
                stats = preload_result.get('total_stats', {})
                print(f"✅ 预加载完成: 总计 {stats.get('total', 0)} 个组件")
                print(f"   成功: {stats.get('success', 0)} 个")
                print(f"   失败: {stats.get('failed', 0)} 个")
            else:
                print(f"❌ 预加载失败: {preload_result.get('error', '未知错误')}")
        
        print("\n" + "=" * 60)
        print("服务已启动，等待连接...")
        print("输入 'menu' 进入管理菜单，按 Ctrl+C 停止服务")
        print("=" * 60)
        
        # 交互式运行
        import threading
        
        # 启动菜单线程
        menu_thread = threading.Thread(target=interactive_menu, args=(communicator,), daemon=True)
        menu_thread.start()
        
        # 保持服务运行
        while communicator.is_running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
            
    except KeyboardInterrupt:
        pass
    finally:
        print("\n收到停止信号，正在关闭服务...")
        communicator.stop()
        print("服务已停止")

if __name__ == "__main__":
    main()