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
                 test_server_host: str = None, test_server_port: int = 8889,
                 machine_id: str = None, cache_capacity: int = 20):
        """
        初始化通信服务
        :param bind_host: 绑定的IP地址（0.0.0.0表示允许所有网络连接）
        :param bind_port: 监听的端口（默认8888）
        :param test_server_host: 测试服务器地址（用于事件同步）
        :param test_server_port: 测试服务器端口
        :param machine_id: 机器唯一标识符
        :param cache_capacity: 元素缓存的最大容量
        """
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.test_server_host = test_server_host
        self.test_server_port = test_server_port
        self.machine_id = machine_id or f"machine_{random.randint(1000, 9999)}"
        
        # 本地服务
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False
        
        # 多应用管理
        self.apps: Dict[str, Dict] = {}  # app_name -> app_info
        self.app_regions: Dict[str, List[int]] = {}  # app_name -> region
        self.element_caches: Dict[str, LRUCache] = {}  # app_name -> cache
        
        # 测试服务器连接
        self.test_server_socket = None
        self.test_server_connected = False
        self.test_server_thread = None
        self.test_server_send_lock = threading.Lock()
        
        # 事件同步
        self.event_queue = queue.Queue()
        self.event_thread = None
        
        # 线程管理
        self.server_thread = None
        self.client_threads: Set[threading.Thread] = set()

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

    def connect_to_test_server(self) -> bool:
        """连接到测试服务器"""
        if not self.test_server_host:
            print("未配置测试服务器地址，跳过连接")
            return False
            
        try:
            self.test_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.test_server_socket.connect((self.test_server_host, self.test_server_port))
            self.test_server_connected = True
            
            # 发送机器注册信息
            register_info = {
                "machine_id": self.machine_id,
                "machine_info": {
                    "host": self.bind_host,
                    "port": self.bind_port,
                    "platform": "linux",
                    "timestamp": time.time()
                }
            }
            with self.test_server_send_lock:
                self.test_server_socket.sendall(json.dumps(register_info).encode('utf-8'))
            
            # 接收注册响应
            response_data = self.test_server_socket.recv(1024).decode('utf-8')
            response = json.loads(response_data)
            
            if response.get("success"):
                print(f"成功连接到测试服务器 {self.test_server_host}:{self.test_server_port}")
                
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
            else:
                print(f"连接测试服务器失败: {response.get('error')}")
                return False
                
        except Exception as e:
            print(f"连接测试服务器失败: {str(e)}")
            self.test_server_connected = False
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

            # 尝试连接到测试服务器
            if self.test_server_host:
                self.connect_to_test_server()

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

