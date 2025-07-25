import socket
import json
import time
import random
import io
import base64
import dogtail.tree
import pyautogui
from typing import Dict, List, Optional
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
    """被测试机器的通信类，监听8888端口并处理测试者的请求"""
    
    def __init__(self, bind_host: str = "0.0.0.0", bind_port: int = 8888, cache_capacity: int = 20):
        """
        初始化通信服务
        :param bind_host: 绑定的IP地址（0.0.0.0表示允许所有网络连接）
        :param bind_port: 监听的端口（默认8888）
        :param cache_capacity: 元素缓存的最大容量
        """
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置端口复用，避免服务重启时出现"端口已被占用"错误
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False  # 服务运行状态
        self.app = None  # 被测应用实例
        self.element_cache = LRUCache(capacity=cache_capacity)  # 元素缓存


    def _get_app_region(self) -> Optional[List[int]]:
        """获取被监测应用的窗口信息（位置和大小）"""
        if not self.app:
            return None
            
        try:
            # 通过dogtail获取应用窗口位置和大小
            window = self.app.children[0]  # 假设第一个子元素是主窗口
            x, y = window.position
            width, height = window.size
            self.app_region = [x, y, width, height]
            print(f"获取应用窗口信息: 位置({x},{y}), 大小({width}x{height})")
            return self.app_region
        except Exception as e:
            print(f"获取应用窗口信息失败: {str(e)}")
            return None


    def _get_screenshot(self, region: Optional[List[int]] = None) -> str:
        """
        截取屏幕或指定区域，返回base64编码
        :param region: 可选区域 [x, y, width, height]，None表示全屏
        """
        try:
            # 截取屏幕
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # 转换为base64编码
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            return img_bytes.hex()  # 用16进制传输二进制数据
        except Exception as e:
            print(f"截图失败: {str(e)}")
            return ""
        

    def _get_element(self, element_path: str, role_name_list: Optional[List[Optional[str]]] = None) -> Dict:
        """
        调用dogtail查询元素信息，使用LRU缓存加速重复查询，支持基于父级缓存的增量查询
        :param element_path: 元素路径（如"菜单/文件/新建"）
        :param role_name_list: 角色名列表，项数与路径级数相等，每项可为空
                              例如：["window", "menu bar", "menu item"]
        :return: 包含元素位置、尺寸等信息的字典
        """
        print(f"查询元素: {element_path}, 角色列表: {role_name_list}")
        
        # 1. 处理路径和角色列表，生成缓存键
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

        # 2. 检查当前元素是否在缓存中
        cached_result = self.element_cache.get(full_cache_key)
        if cached_result:
            print(f"✅ 缓存命中: {element_path}")
            result = {
                "success": True,
                "data": {
                    "position": cached_result["position"],
                    "size": cached_result["size"],
                    "name": cached_result["name"],
                    "role_name": cached_result["role_name"],
                }
            }
            return cached_result

        # 3. 查找最近的已缓存父级元素
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
            parent_cached = self.element_cache.get(parent_cache_key)
            if parent_cached:
                # 父级存在缓存，提取父元素对象
                parent_element = parent_cached["data"].get("element_object")
                if parent_element:
                    # 计算剩余路径和角色
                    remaining_path_parts = path_parts[i:]
                    remaining_roles = adjusted_roles[i:]
                    print(f"🔼 找到父级缓存: {parent_path}，从父级开始查询剩余路径")
                    break

        # 4. 执行元素查找（从父级或根节点开始）
        try:
            if not self.app:
                self.app = dogtail.tree.root

            # 确定查找起点（父级缓存或根节点）
            current_element = parent_element if parent_element else self.app

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
                    error_msg = f"元素不存在: {error_path}"
                    if current_role:
                        error_msg += f" (角色: {current_role})"
                    return {"success": False, "error": error_msg}
                current_element = found_element

            # 提取元素信息
            x, y = current_element.position
            width, height = current_element.size
            print(f"🔍 查询成功: {element_path}，位置: ({x}, {y}), 尺寸: ({width}, {height})")
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

            # 5. 存入缓存
            self.element_cache.put(full_cache_key, store_data)
            print(f"📌 缓存新增: {element_path} (缓存大小: {len(self.element_cache.cache)}/{self.element_cache.capacity})")
            return result

        except Exception as e:
            return {"success": False, "error": f"元素查询失败: {str(e)}"}


    def _execute_commands(self, commands: List[Dict]) -> Dict:
        """
        执行测试者发送的指令集
        :param commands: 指令列表（如鼠标移动、点击等）
        :return: 执行结果汇总
        """
        results = []
        for cmd in commands:
            try:
                action = cmd["action"]
                params = cmd["params"]
                print(f"执行指令: {action}，参数: {params}")

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


    def start(self, app_name: Optional[str] = None) -> None:
        """
        启动通信服务，开始监听8888端口
        :param app_name: 被测应用名称（可选，如"firefox"）
        """
        try:
            # 绑定端口并开始监听
            self.server_socket.bind((self.bind_host, self.bind_port))
            self.server_socket.listen(5)  # 最大等待连接数
            self.is_running = True
            print(f"被测试机器通信服务已启动，监听 {self.bind_host}:{self.bind_port}")

            # 若指定应用，连接到该应用（否则监控所有应用）
            if app_name:
                self.app = dogtail.tree.root.application(app_name)
                print(f"已绑定被测应用: {app_name}")

            # 循环处理客户端连接
            while self.is_running:
                client_socket, client_addr = self.server_socket.accept()
                print(f"收到来自 {client_addr} 的连接，保持长连接")

                try:
                    # 保持连接，循环处理请求
                    while self.is_running:
                        # 接收请求数据（最大1MB）
                        request_data = client_socket.recv(1024 * 1024).decode('utf-8')
                        if not request_data:
                            print(f"测试者 {client_addr} 主动断开连接")
                            break

                        # 解析请求（JSON格式）
                        request = json.loads(request_data)
                        response = {"success": False, "error": "未知请求类型"}

                        # 处理不同类型的请求
                        if request["type"] == "get_app_region":
                            app_region = self._get_app_region()
                            if app_region:
                                response = {
                                    "success": True,
                                    "data": {"app_region": app_region}
                                }
                            else:
                                response = {"success": False, "error": "无法获取应用窗口信息"}

                        elif request["type"] == "get_screenshot":
                            region = request["data"].get("region")
                            screenshot_data = self._get_screenshot(region)
                            if screenshot_data:
                                response = {
                                    "success": True,
                                    "data": {"screenshot": screenshot_data}
                                }
                            else:
                                response = {"success": False, "error": "截图失败"}

                        elif request["type"] == "get_element":
                            # 处理元素查询请求
                            response = self._get_element(
                                element_path=request["data"]["element_path"],
                                role_name_list=request["data"].get("role_name_list")
                            )

                        elif request["type"] == "exec_commands":
                            # 处理指令集执行请求
                            response = self._execute_commands(request["data"]["commands"])
                            
                        elif request["type"] == "disconnect":
                            # 处理主动断开连接请求
                            print(f"收到 {client_addr} 的断开连接请求")
                            self.element_cache.clear()  # 清空缓存
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

        except Exception as e:
            print(f"服务启动失败: {str(e)}")
            self.stop()


    def stop(self) -> None:
        """停止通信服务"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        print("通信服务已停止")


# 启动服务（直接运行该脚本即可）
if __name__ == "__main__":
    # 初始化服务，监听8888端口
    communicator = TestedMachineCommunicator(bind_port=8888)
    try:
        # 可指定被测应用名称，如 communicator.start(app_name="gedit")
        # communicator.start(app_name="QGIS3")  # 启动QGIS应用的测试服务
        communicator.start(app_name="calculator")  # 启动计算器应用的测试服务
        # communicator.start()
    except KeyboardInterrupt:
        # 按Ctrl+C停止服务
        communicator.stop()