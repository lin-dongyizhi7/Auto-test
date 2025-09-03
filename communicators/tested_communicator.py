'''
Author: 凛冬已至 2985956026@qq.com
Date: 2025-07-24 13:25:17
LastEditors: 凛冬已至 2985956026@qq.com
LastEditTime: 2025-09-03 13:13:31
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
        
        # 常用组件预加载
        self.common_components: Dict[str, Dict] = {}  # app_name -> components
        self.preload_enabled = False

        # 本地UI事件队列（供可视化界面消费）
        self.ui_event_queue: "queue.Queue" = queue.Queue()

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

    def _handle_test_server_connection(self, test_server_socket: socket.socket, test_server_addr: tuple) -> bool:
        """
        处理测试服务器的连接请求，验证IP和端口
        :param test_server_socket: 客户端socket
        :param test_server_addr: 客户端地址 (ip, port)
        :return: 是否接受连接
        """
        try:
            # 接收连接验证请求
            request_data = test_server_socket.recv(1024).decode('utf-8')
            self._emit_event("incoming_connection", {"from": str(test_server_addr), "raw": request_data})
            if not request_data:
                return False
            
            request = json.loads(request_data)
            if request.get("type") != "connection_request":
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
                "type": "connection_response",
                "success": True,
                "data": {
                    "message": "连接已接受"
                }
            }
            test_server_socket.sendall(json.dumps(response).encode('utf-8'))
            
            # 发送机器注册请求
            registration_request = {
                "type": "machine_registration",
                "data": {
                    "machine_id": self.machine_id,
                    "machine_info": {
                        "host": self.bind_host,
                        "port": self.bind_port,
                        "platform": "linux",
                        "timestamp": time.time(),
                        "server_id": server_id
                    }
                }
            }
            test_server_socket.sendall(json.dumps(registration_request).encode('utf-8'))
            print(f"发送机器注册请求: machine_id={self.machine_id}")
            
            # 等待注册响应
            registration_response = test_server_socket.recv(1024).decode('utf-8')
            if not registration_response:
                print("未收到机器注册响应")
                return False
            
            registration_result = json.loads(registration_response)
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
            
            return True
            
        except Exception as e:
            print(f"处理测试服务器连接请求失败: {str(e)}")
            return False

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
                request_data = self.test_server_socket.recv(1024 * 1024).decode('utf-8')
                if not request_data:
                    print(f" {self.test_server_addr} 断开连接")
                    break

                # 解析请求（JSON格式）
                request = json.loads(request_data)
                self._emit_event("client_request", {"from": str(self.test_server_addr), "type": request.get("type")})
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
                    print(f"收到 {self.test_server_addr} 的断开连接请求")
                    response = {"success": True, "message": "连接已断开"}
                    self.test_server_socket.sendall(json.dumps(response).encode('utf-8'))
                    self.test_server_connected = False
                    self.test_server_socket = None
                    print(f"与测试服务器 {self.test_server_addr} 的连接已断开")
                    self._emit_event("test_server_disconnected", {"test_server_addr": str(self.test_server_addr)})
                    return

                # 发送响应
                self.test_server_socket.sendall(json.dumps(response).encode('utf-8'))
                self._emit_event("client_response", {"from": str(self.test_server_addr), "ok": bool(response.get("success"))})

        except json.JSONDecodeError:
            error_msg = {"success": False, "error": "无效的JSON格式"}
            self.test_server_socket.sendall(json.dumps(error_msg).encode('utf-8'))
            self._emit_event("client_response", {"from": str(self.test_server_addr), "ok": False, "error": "JSONDecodeError"})
        except Exception as e:
            print(f"与测试服务器 {self.test_server_addr} 通信时发生错误: {str(e)}")
            self._emit_event("server_error", {"test_server_addr": str(self.test_server_addr), "error": str(e)})
        finally:
            print("Request Handle Done")

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
    
    # 选择是否启用预加载（先于配置文件选择）
    preload_input = input("是否启用常用组件预加载功能? (y/n，默认: y): ").strip().lower()
    enable_preload = preload_input in ['', 'y', 'yes', '是']

    # 扫描 preload 目录供选择配置文件
    config_file = ""
    if enable_preload:
        print("\n扫描 preload 目录下可用的配置文件:")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        preload_dir = os.path.join(script_dir, "preload")
        available_files = []
        try:
            if os.path.isdir(preload_dir):
                for fname in os.listdir(preload_dir):
                    if fname.lower().endswith('.json'):
                        available_files.append(fname)
        except Exception:
            available_files = []

        if not available_files:
            print("未在 preload 目录发现可用 JSON 配置文件，将禁用预加载功能")
            enable_preload = False
        else:
            for idx, fname in enumerate(available_files, 1):
                print(f"{idx}. {fname}")
            choice = input(f"请选择配置文件 (1-{len(available_files)}，默认: 1): ").strip()
            try:
                idx = int(choice) if choice else 1
            except ValueError:
                idx = 1
            idx = max(1, min(idx, len(available_files)))
            # 返回相对路径，以便后续与 script_dir 拼接
            config_file = os.path.join("preload", available_files[idx - 1])

    # 获取监控应用列表（默认空=监听所有应用）
    print("\n未指定将监听所有应用，可输入应用名称（空格分隔）以限定:")
    apps_input = input("请输入要监控的应用名称 (默认: 空=监听所有): ").strip()
    if not apps_input:
        apps = []
    else:
        apps = [app.strip() for app in apps_input.split()]
    
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
    print(f"监控应用: {', '.join(config['apps']) if config['apps'] else '未指定（监听所有应用）'}")
    print(f"组件配置文件: {config['config_file'] if config['config_file'] else '（未启用预加载）'}")
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
        if config['enable_preload'] and config['config_file']:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, config['config_file'])
            print(f"\n正在加载常用组件配置文件: {config_path}")
            if communicator.load_common_components(config_path):
                print("✅ 常用组件配置文件加载成功")
            else:
                print("❌ 常用组件配置文件加载失败，将禁用预加载功能")
                config['enable_preload'] = False
        
        # 启动服务
        print(f"\n正在启动服务，监控应用: {', '.join(config['apps']) if config['apps'] else '未指定（监听所有应用）'}")
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