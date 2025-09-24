import socket
import json
import time
import cv2
import numpy as np
from PIL import Image
import io
import threading
import queue
from typing import Dict, List, Optional, Set, Tuple, Any
from .config import get_security_config
from .crypto_utils import wrap_outgoing, unwrap_incoming
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    """事件类型枚举"""
    MACHINE_CONNECTED = "machine_connected"
    MACHINE_DISCONNECTED = "machine_disconnected"
    APP_LAUNCHED = "app_launched"
    APP_CLOSED = "app_closed"
    COMMAND_EXECUTED = "command_executed"
    SCREENSHOT_TAKEN = "screenshot_taken"
    ELEMENT_FOUND = "element_found"
    ERROR_OCCURRED = "error_occurred"
    OPERATION_STARTED = "operation_started"
    OPERATION_COMPLETED = "operation_completed"

@dataclass
class Event:
    """事件数据结构"""
    type: EventType
    machine_id: str
    app_name: Optional[str]
    timestamp: float
    data: Dict
    source_machine: str

class TestMachineCommunicator:
    """测试者机器的通信类，支持多机器连接、多应用通信和事件同步"""
    
    def __init__(self, server_host: str = "0.0.0.0", server_port: int = 8888, server_id: str = "test_server"):
        self.server_host = server_host
        self.server_port = server_port
        self.server_id = server_id  # 当前服务器标识
        self.server_socket = None
        self.is_running = False
        
        # 多机器连接管理
        self.machines: Dict[str, Dict] = {}  # machine_id -> machine_info
        self.apps: Dict[str, Dict] = {}      # app_id -> app_info
        self.connections: Dict[str, socket.socket] = {}  # machine_id -> socket
        
        # 事件同步系统
        self.event_queue = queue.Queue()
        self.event_subscribers: Set[str] = set()  # 订阅事件的机器ID集合
        self.event_history: List[Event] = []
        self.max_event_history = 1000
        
        # 线程管理
        self.server_thread = None
        self.event_thread = None
        self.housekeeping_thread = None
        self._housekeeping_stop = False
        
        # 连接状态监控
        self.connection_status = {}
        self.last_heartbeat = {}
        # 安全
        sec = get_security_config()
        self._enable_encryption = bool(sec.get("enable_encryption"))
        self._shared_secret = sec.get("shared_secret") or ""
        
    def start_server(self) -> None:
        """启动测试服务器，监听多机器连接"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.server_host, self.server_port))
            self.server_socket.listen(10)
            self.is_running = True
            
            print(f"测试服务器已启动，监听 {self.server_host}:{self.server_port}")
            
            # 启动事件处理线程
            self.event_thread = threading.Thread(target=self._event_processor, daemon=True)
            self.event_thread.start()
            
            # 启动保洁线程：定期清理超时的非活跃连接
            self._housekeeping_stop = False
            self.housekeeping_thread = threading.Thread(target=self._housekeeping_loop, daemon=True)
            self.housekeeping_thread.start()
            
        except Exception as e:
            raise RuntimeError(f"启动测试服务器失败: {str(e)}")
    
    def _handle_machine_connection(self, client_socket: socket.socket, client_addr: tuple, machine_id: str) -> None:
        """处理单个机器连接（被动连接模式）"""
        try:
            # 保持连接，处理请求
            while self.is_running and machine_id in self.connections:
                try:
                    data_bytes = client_socket.recv(1024 * 1024)
                    if not data_bytes:
                        break
                    try:
                        request = unwrap_incoming(data_bytes, self._enable_encryption, self._shared_secret)
                    except Exception:
                        request = json.loads(data_bytes.decode('utf-8'))
                    response = self._handle_request(machine_id, request)
                    if response and "flag" in response:
                        client_socket.sendall(wrap_outgoing(response, self._enable_encryption, self._shared_secret))
                    
                    # 更新最后活跃时间
                    if machine_id in self.machines:
                        self.machines[machine_id]["last_seen"] = time.time()
                    
                except json.JSONDecodeError:
                    error_msg = {"success": False, "error": "无效的JSON格式"}
                    client_socket.sendall(json.dumps(error_msg).encode('utf-8'))
                except Exception as e:
                    # 网络异常/对端断开，尽量回应一次后中断循环
                    try:
                        error_msg = {"success": False, "error": f"处理请求失败: {str(e)}"}
                        client_socket.sendall(json.dumps(error_msg).encode('utf-8'))
                    except Exception:
                        pass
                    break
                    
        except Exception as e:
            print(f"处理机器 {machine_id} 连接时发生错误: {str(e)}")
        finally:
            if machine_id:
                self._disconnect_machine(machine_id)
            client_socket.close()
    
    def connect_to_machine(self, machine_id: str, host: str, port: int) -> Dict:
        """主动连接到目标机器"""
        if machine_id in self.connections:
            return {"success": False, "error": f"机器 {machine_id} 已连接"}

        try:
            # 创建连接
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
            print(f"主动连接到机器 {host}:{port}")

            # 发送连接请求
            connection_request = {
                "type": "connection_request",
                "data": {
                    "server_host": self.server_host,
                    "server_port": self.server_port,
                    "server_id": self.server_id
                }
            }
            print(f"发送连接请求: {connection_request}")
            client_socket.sendall(wrap_outgoing(connection_request, self._enable_encryption, self._shared_secret))

            # 等待连接确认响应
            response_bytes = client_socket.recv(1024)
            if not response_bytes:
                client_socket.close()
                return {"success": False, "error": "连接后未收到响应"}

            try:
                response_data = unwrap_incoming(response_bytes, self._enable_encryption, self._shared_secret)
            except Exception:
                response_data = json.loads(response_bytes.decode('utf-8'))
            if not response_data.get("success"):
                client_socket.close()
                return {"success": False, "error": response_data.get("error", "连接被拒绝")}

            # 等待机器注册请求
            registration_bytes = client_socket.recv(1024)
            if not registration_bytes:
                client_socket.close()
                return {"success": False, "error": "未收到机器注册请求"}

            try:
                registration_request = unwrap_incoming(registration_bytes, self._enable_encryption, self._shared_secret)
            except Exception:
                registration_request = json.loads(registration_bytes.decode('utf-8'))
            if registration_request.get("type") != "machine_registration":
                client_socket.close()
                return {"success": False, "error": "收到无效的注册请求"}

            # 处理机器注册
            registration_result = self._handle_machine_registration(client_socket, registration_request)
            if not registration_result.get("success"):
                client_socket.close()
                return registration_result

            # 获取实际的machine_id（可能由服务器生成）
            actual_machine_id = registration_result.get("machine_id", machine_id)
            
            # 注册机器信息
            self.machines[actual_machine_id] = {
                "address": (host, port),
                "info": registration_request.get("data", {}).get("machine_info", {}),
                "connected_at": time.time(),
                "status": "connected",
                "last_seen": time.time()
            }
            self.connections[actual_machine_id] = client_socket

            # 启动处理线程
            client_thread = threading.Thread(
                target=self._handle_machine_connection,
                args=(client_socket, (host, port), actual_machine_id),
                daemon=True
            )
            client_thread.start()

            # 发布连接事件
            self._publish_event(Event(
                type=EventType.MACHINE_CONNECTED,
                machine_id=actual_machine_id,
                app_name=None,
                timestamp=time.time(),
                data={"address": (host, port)},
                source_machine=self.server_id
            ))

            return {"success": True, "message": f"成功连接到机器 {actual_machine_id}", "machine_id": actual_machine_id}

        except Exception as e:
            return {"success": False, "error": f"连接失败: {str(e)}"}

    def disconnect_machine(self, machine_id: str) -> Dict:
        """主动断开与机器的连接"""
        if machine_id not in self.machines:
            return {"success": False, "error": f"机器 {machine_id} 未连接"}

        self._disconnect_machine(machine_id)
        return {"success": True, "message": f"已断开与机器 {machine_id} 的连接"}
    
    def _handle_request(self, machine_id: str, request: Dict) -> Dict:
        """处理来自机器的请求"""
        request_type = request.get("type")
        # 处理来自目标机器的响应类消息（如 get_element_response 等）
        if isinstance(request_type, str) and request_type.endswith("_response"):
            payload = request.get("data", {}) if isinstance(request.get("data"), dict) else request
            success = payload.get("success")
            error_msg = payload.get("error")
            base_action = request_type.replace("_response", "")

            # 针对常见类型给出更清晰的日志
            if base_action == "get_element":
                if success:
                    print(f"[{machine_id}] 元素查询成功")
                else:
                    print(f"[{machine_id}] 元素查询失败: {error_msg}")
            elif base_action == "get_screenshot":
                if success:
                    print(f"[{machine_id}] 截图获取成功")
                else:
                    print(f"[{machine_id}] 截图获取失败: {error_msg}")
            elif base_action == "exec_commands":
                if success:
                    print(f"[{machine_id}] 命令执行成功")
                else:
                    print(f"[{machine_id}] 命令执行失败: {error_msg}")
            else:
                # 通用响应日志
                if success:
                    print(f"[{machine_id}] {base_action} 成功")
                else:
                    print(f"[{machine_id}] {base_action} 失败: {error_msg}")

            # 返回响应数据给等待的进程
            return payload
        
        if request_type == "machine_registration":
            return None
        elif request_type == "register_app":
            responseData =  self._handle_app_registration(machine_id, request)
        elif request_type == "get_screenshot":
            responseData =  self._handle_screenshot_request(machine_id, request)
        elif request_type == "get_element":
            responseData =  self._handle_element_request(machine_id, request)
        elif request_type == "exec_commands":
            responseData =  self._handle_command_execution(machine_id, request)
        elif request_type == "subscribe_events":
            responseData =  self._handle_event_subscription(machine_id, request)
        elif request_type == "unsubscribe_events":
            responseData =  self._handle_event_unsubscription(machine_id, request)
        elif request_type == "get_machines":
            responseData =  self._handle_get_machines_request()
        elif request_type == "get_apps":
            responseData =  self._handle_get_apps_request()
        elif request_type == "sync_event":
            responseData =  self._handle_event_sync(machine_id, request)
        elif request_type == "heartbeat":
            responseData =  self._handle_heartbeat(machine_id, request)
        else:
            responseData =  {"success": False, "error": f"未知请求类型: {request_type}"}
        return {"type": f'{request_type}_response', "data": responseData, "flag": 'response'}
    
    def _handle_machine_registration(self, client_socket: socket.socket, request: Dict) -> Dict:
        """处理机器注册请求"""
        try:
            data = request.get("data", {})
            requested_machine_id = data.get("machine_id")
            machine_info = data.get("machine_info", {})
            
            # 检查machine_id是否已存在
            if requested_machine_id and requested_machine_id in self.machines:
                if self.machines['requested_machine_id']['address'] == machine_info['address']:
                    actual_machine_id = requested_machine_id
                    print(f"该机器已注册，不需要重新注册: {actual_machine_id}")
                else:
                    # 请求的ID已存在，但地址不同，生成新的ID
                    actual_machine_id = self._generate_unique_machine_id()
                    print(f"机器ID {requested_machine_id} 已存在，生成新ID: {actual_machine_id}")
            elif requested_machine_id:
                # 使用请求的ID
                actual_machine_id = requested_machine_id
                print(f"使用请求的机器ID: {actual_machine_id}")
            else:
                # 生成新的ID
                actual_machine_id = self._generate_unique_machine_id()
                print(f"未提供机器ID，生成新ID: {actual_machine_id}")
            
            # 发送注册成功响应
            response = {
                "success": True,
                "machine_id": actual_machine_id,
                "message": "机器注册成功"
            }
            
            if client_socket:
                client_socket.sendall(wrap_outgoing(response, self._enable_encryption, self._shared_secret))
            
            return {"success": True, "machine_id": actual_machine_id}
            
        except Exception as e:
            error_response = {"success": False, "error": f"机器注册失败: {str(e)}"}
            if client_socket:
                client_socket.sendall(json.dumps(error_response).encode('utf-8'))
            return {"success": False, "error": f"机器注册失败: {str(e)}"}
    
    def _generate_unique_machine_id(self) -> str:
        """生成唯一的机器ID"""
        import random
        while True:
            machine_id = f"machine_{random.randint(1000, 9999)}"
            if machine_id not in self.machines:
                return machine_id
    
    def _handle_app_registration(self, machine_id: str, request: Dict) -> Dict:
        """处理应用注册请求"""
        app_name = request.get("data", {}).get("app_name")
        app_info = request.get("data", {}).get("app_info", {})
        
        if not app_name:
            return {"success": False, "error": "应用名称不能为空"}
        
        app_id = f"{machine_id}:{app_name}"
        self.apps[app_id] = {
            "machine_id": machine_id,
            "app_name": app_name,
            "info": app_info,
            "registered_at": time.time(),
            "status": "running"
        }
        
        # 发布应用启动事件
        self._publish_event(Event(
            type=EventType.APP_LAUNCHED,
            machine_id=machine_id,
            app_name=app_name,
            timestamp=time.time(),
            data={"app_info": app_info},
            source_machine=machine_id
        ))
        
        print(f"应用 {app_name} 在机器 {machine_id} 上注册成功")
        return {"success": True, "app_id": app_id}
    
    def _handle_screenshot_request(self, machine_id: str, request: Dict) -> Dict:
        """处理截图请求，转发到对应机器"""
        app_name = request.get("data", {}).get("app_name")
        region = request.get("data", {}).get("region")
        
        if not app_name:
            return {"success": False, "error": "应用名称不能为空"}
        
        app_id = f"{machine_id}:{app_name}"
        if app_id not in self.apps:
            return {"success": False, "error": f"应用 {app_name} 未在机器 {machine_id} 上注册"}
        
        # 转发请求到对应机器
        return self._forward_request_to_machine(machine_id, "get_screenshot", {
            "app_name": app_name,
            "region": region
        })
    
    def _handle_element_request(self, machine_id: str, request: Dict) -> Dict:
        """处理元素查询请求，转发到对应机器"""
        app_name = request.get("data", {}).get("app_name")
        element_path = request.get("data", {}).get("element_path")
        role_name_list = request.get("data", {}).get("role_name_list")
        
        if not app_name or not element_path:
            return {"success": False, "error": "应用名称和元素路径不能为空"}
        
        app_id = f"{machine_id}:{app_name}"
        if app_id not in self.apps:
            return {"success": False, "error": f"应用 {app_name} 未在机器 {machine_id} 上注册"}
        
        # 转发请求到对应机器
        return self._forward_request_to_machine(machine_id, "get_element", {
            "app_name": app_name,
            "element_path": element_path,
            "role_name_list": role_name_list
        })
    
    def _handle_command_execution(self, machine_id: str, request: Dict) -> Dict:
        """处理命令执行请求，转发到对应机器"""
        app_name = request.get("data", {}).get("app_name")
        commands = request.get("data", {}).get("commands")
        
        if not app_name or not commands:
            return {"success": False, "error": "应用名称和命令不能为空"}
        
        app_id = f"{machine_id}:{app_name}"
        if app_id not in self.apps:
            return {"success": False, "error": f"应用 {app_name} 未在机器 {machine_id} 上注册"}
        
        # 发布操作开始事件
        self._publish_event(Event(
            type=EventType.OPERATION_STARTED,
            machine_id=machine_id,
            app_name=app_name,
            timestamp=time.time(),
            data={"commands": commands},
            source_machine=machine_id
        ))
        
        # 转发请求到对应机器
        result = self._forward_request_to_machine(machine_id, "exec_commands", {
            "app_name": app_name,
            "commands": commands
        })
        
        # 发布命令执行事件
        if result.get("success"):
            self._publish_event(Event(
                type=EventType.COMMAND_EXECUTED,
                machine_id=machine_id,
                app_name=app_name,
                timestamp=time.time(),
                data={"commands": commands, "result": result},
                source_machine=machine_id
            ))
            
            # 发布操作完成事件
            self._publish_event(Event(
                type=EventType.OPERATION_COMPLETED,
                machine_id=machine_id,
                app_name=app_name,
                timestamp=time.time(),
                data={"commands": commands, "result": result},
                source_machine=machine_id
            ))
        
        return result
    
    def _handle_event_subscription(self, machine_id: str, request: Dict) -> Dict:
        """处理事件订阅请求"""
        self.event_subscribers.add(machine_id)
        print(f"机器 {machine_id} 订阅了事件通知")
        return {"success": True, "message": "事件订阅成功"}
    
    def _handle_event_unsubscription(self, machine_id: str, request: Dict) -> Dict:
        """处理事件取消订阅请求"""
        self.event_subscribers.discard(machine_id)
        print(f"机器 {machine_id} 取消订阅了事件通知")
        return {"success": True, "message": "事件取消订阅成功"}
    
    def _handle_get_machines_request(self) -> Dict:
        """处理获取机器列表请求"""
        machines_info = {}
        for mid, machine in self.machines.items():
            machines_info[mid] = {
                "address": machine["address"],
                "info": machine["info"],
                "connected_at": machine["connected_at"],
                "status": machine["status"],
                "last_seen": machine.get("last_seen", 0),
                "apps": [aid for aid, app in self.apps.items() if app["machine_id"] == mid]
            }
        
        return {"success": True, "data": {"machines": machines_info}}
    
    def _handle_get_apps_request(self) -> Dict:
        """处理获取应用列表请求"""
        apps_info = {}
        for aid, app in self.apps.items():
            apps_info[aid] = {
                "machine_id": app["machine_id"],
                "app_name": app["app_name"],
                "info": app["info"],
                "registered_at": app["registered_at"],
                "status": app["status"]
            }
        
        return {"success": True, "data": {"apps": apps_info}}
    
    def _handle_event_sync(self, machine_id: str, request: Dict) -> Dict:
        """处理事件同步请求"""
        event_data = request.get("data", {})
        event_type = EventType(event_data.get("type"))
        
        # 创建事件对象
        event = Event(
            type=event_type,
            machine_id=machine_id,
            app_name=event_data.get("app_name"),
            timestamp=time.time(),
            data=event_data.get("data", {}),
            source_machine=machine_id
        )
        
        # 发布事件
        self._publish_event(event)
        
        return {"success": True, "message": "事件同步成功"}
    
    def _handle_heartbeat(self, machine_id: str, request: Dict) -> Dict:
        """处理心跳请求"""
        if machine_id in self.machines:
            self.machines[machine_id]["last_seen"] = time.time()
            self.last_heartbeat[machine_id] = time.time()
        
        return {"success": True, "timestamp": time.time()}
    
    def _forward_request_to_machine(self, machine_id: str, request_type: str, data: Dict) -> Dict:
        """转发请求到指定机器"""
        if machine_id not in self.connections:
            return {"success": False, "error": f"机器 {machine_id} 未连接"}
        
        try:
            socket = self.connections[machine_id]
            request = {
                "type": request_type,
                "data": data,
                "timestamp": time.time()
            }
            
            socket.sendall(wrap_outgoing(request, self._enable_encryption, self._shared_secret))
            
            # 接收响应
            response_bytes = socket.recv(4096 * 1024)
            try:
                return unwrap_incoming(response_bytes, self._enable_encryption, self._shared_secret)
            except Exception:
                return json.loads(response_bytes.decode('utf-8'))
            
        except Exception as e:
            # 视为意外断开，立即清理该机器连接
            try:
                self._disconnect_machine(machine_id)
            except Exception:
                pass
            return {"success": False, "error": f"转发请求失败: {str(e)}"}
    
    def _publish_event(self, event: Event) -> None:
        """发布事件到所有订阅者"""
        # 添加到事件历史
        self.event_history.append(event)
        if len(self.event_history) > self.max_event_history:
            self.event_history.pop(0)
        
        # 将事件放入队列，由事件处理线程处理
        self.event_queue.put(event)
    
    def _event_processor(self) -> None:
        """事件处理线程，负责向订阅者推送事件"""
        while self.is_running:
            try:
                event = self.event_queue.get(timeout=1)
                
                # 向所有订阅者推送事件
                for machine_id in list(self.event_subscribers):
                    if machine_id in self.connections:
                        try:
                            socket = self.connections[machine_id]
                            event_data = {
                                "type": "event_notification",
                                "data": {
                                    "event_type": event.type.value,
                                    "machine_id": event.machine_id,
                                    "app_name": event.app_name,
                                    "timestamp": event.timestamp,
                                    "data": event.data,
                                    "source_machine": event.source_machine
                                }
                            }
                            socket.sendall(wrap_outgoing(event_data, self._enable_encryption, self._shared_secret))
                        except Exception as e:
                            print(f"向机器 {machine_id} 推送事件失败: {str(e)}")
                            # 移除失效的订阅者
                            self.event_subscribers.discard(machine_id)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"事件处理线程发生错误: {str(e)}")
    
    def _disconnect_machine(self, machine_id: str) -> None:
        """断开机器连接"""
        if machine_id in self.machines:
            machine_info = self.machines[machine_id]
            machine_info["status"] = "disconnected"
            machine_info["disconnected_at"] = time.time()
            
            # 发布机器断开事件
            self._publish_event(Event(
                type=EventType.MACHINE_DISCONNECTED,
                machine_id=machine_id,
                app_name=None,
                timestamp=time.time(),
                data={"address": machine_info["address"]},
                source_machine=machine_id
            ))
            
            print(f"机器 {machine_id} 已断开连接")
        
        # 关闭连接
        if machine_id in self.connections:
            try:
                self.connections[machine_id].close()
            except:
                pass
            del self.connections[machine_id]
        
        # 移除应用注册
        apps_to_remove = [aid for aid, app in self.apps.items() if app["machine_id"] == machine_id]
        for aid in apps_to_remove:
            app_name = self.apps[aid]["app_name"]
            del self.apps[aid]
            
            # 发布应用关闭事件
            self._publish_event(Event(
                type=EventType.APP_CLOSED,
                machine_id=machine_id,
                app_name=app_name,
                timestamp=time.time(),
                data={},
                source_machine=machine_id
            ))
    
    # ==================== 新增的实用方法 ====================
    
    def get_machine_status(self, machine_id: str) -> Dict[str, Any]:
        """获取指定机器的详细状态"""
        if machine_id not in self.machines:
            return {"success": False, "error": f"机器 {machine_id} 不存在"}
        
        machine = self.machines[machine_id]
        machine_apps = [aid for aid, app in self.apps.items() if app["machine_id"] == machine_id]
        
        return {
            "success": True,
            "data": {
                "machine_id": machine_id,
                "status": machine["status"],
                "address": machine["address"],
                "info": machine["info"],
                "connected_at": machine["connected_at"],
                "last_seen": machine.get("last_seen", 0),
                "apps_count": len(machine_apps),
                "apps": machine_apps
            }
        }
    
    def get_app_status(self, app_id: str) -> Dict[str, Any]:
        """获取指定应用的详细状态"""
        if app_id not in self.apps:
            return {"success": False, "error": f"应用 {app_id} 不存在"}
        
        app = self.apps[app_id]
        machine = self.machines.get(app["machine_id"], {})
        
        return {
            "success": True,
            "data": {
                "app_id": app_id,
                "machine_id": app["machine_id"],
                "app_name": app["app_name"],
                "status": app["status"],
                "info": app["info"],
                "registered_at": app["registered_at"],
                "machine_status": machine.get("status", "unknown"),
                "machine_address": machine.get("address", "unknown")
            }
        }
    
    def ping_machine(self, machine_id: str) -> Dict[str, Any]:
        """ping指定机器，检查连接状态"""
        if machine_id not in self.connections:
            return {"success": False, "error": f"机器 {machine_id} 未连接"}
        
        try:
            result = self._forward_request_to_machine(machine_id, "heartbeat", {})
            if result.get("success"):
                return {"success": True, "latency": time.time() - result.get("timestamp", time.time())}
            else:
                return {"success": False, "error": "ping失败"}
        except Exception as e:
            return {"success": False, "error": f"ping异常: {str(e)}"}
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """获取连接状态摘要"""
        total_machines = len(self.machines)
        connected_machines = len([m for m in self.machines.values() if m["status"] == "connected"])
        total_apps = len(self.apps)
        running_apps = len([a for a in self.apps.values() if a["status"] == "running"])
        
        return {
            "success": True,
            "data": {
                "machines": {
                    "total": total_machines,
                    "connected": connected_machines,
                    "disconnected": total_machines - connected_machines
                },
                "apps": {
                    "total": total_apps,
                    "running": running_apps
                },
                "events": {
                    "total": len(self.event_history),
                    "subscribers": len(self.event_subscribers)
                }
            }
        }
    
    def cleanup_inactive_connections(self, timeout_seconds: int = 300) -> int:
        """清理超时的非活跃连接"""
        current_time = time.time()
        cleaned_count = 0
        
        for machine_id in list(self.machines.keys()):
            machine = self.machines[machine_id]
            if machine["status"] == "connected":
                last_seen = machine.get("last_seen", 0)
                if current_time - last_seen > timeout_seconds:
                    print(f"清理超时连接: {machine_id}")
                    self._disconnect_machine(machine_id)
                    cleaned_count += 1
        
        return cleaned_count
    
    def get_connected_machines(self) -> List[str]:
        """获取已连接的机器ID列表"""
        return list(self.machines.keys())
    
    def get_registered_apps(self) -> List[str]:
        """获取已注册的应用ID列表"""
        return list(self.apps.keys())
    
    def get_event_history(self, limit: int = 100, event_type: Optional[EventType] = None) -> List[Event]:
        """获取事件历史，支持按类型过滤"""
        events = self.event_history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]
    
    def stop_server(self) -> None:
        """停止测试服务器"""
        self.is_running = False
        
        # 停止保洁线程
        try:
            self._housekeeping_stop = True
            if self.housekeeping_thread and self.housekeeping_thread.is_alive():
                self.housekeeping_thread.join(timeout=2)
        except Exception:
            pass
        
        # 关闭所有连接
        for machine_id in list(self.connections.keys()):
            self._disconnect_machine(machine_id)
        
        # 关闭服务器socket
        if self.server_socket:
            self.server_socket.close()
        
        print("测试服务器已停止")

    def _housekeeping_loop(self, interval_seconds: int = 5, timeout_seconds: int = 3600) -> None:
        """后台保洁线程：周期清理超时非活跃连接"""
        while not self._housekeeping_stop and self.is_running:
            try:
                cleaned = self.cleanup_inactive_connections(timeout_seconds=timeout_seconds)
                if cleaned:
                    print(f"保洁清理了 {cleaned} 个超时连接")
            except Exception:
                pass
            time.sleep(interval_seconds)

# 兼容性类，保持向后兼容
class SingleMachineCommunicator:
    """单机器通信类，保持向后兼容"""
    
    def __init__(self, target_host: str, target_port: int):
        self.target_host = target_host
        self.target_port = target_port
        self.socket = None
        self.app_region = None
        self._connect()
        self._get_app_region()

    def _connect(self) -> None:
        """建立与被测试机器的TCP连接"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.target_host, self.target_port))
            print(f"成功连接到被测试机器 {self.target_host}:{self.target_port}")
        except Exception as e:
            raise ConnectionError(f"无法连接到被测试机器: {str(e)}")

    def _send_request(self, request_type: str, data: Dict) -> Dict:
        """发送请求到被测试机器并接收响应"""
        if not self.socket:
            self._connect()

        try:
            request = {
                "type": request_type,
                "data": data,
                "timestamp": time.time()
            }
            sendJson = json.dumps(request).encode('utf-8')
            print(f"发送请求: {request_type}, 数据: {data}")
            self.socket.sendall(sendJson)
            
            response_data = self.socket.recv(4096 * 1024).decode('utf-8')
            return json.loads(response_data)
        
        except Exception as e:
            self.socket = None
            raise RuntimeError(f"通信错误: {str(e)}")

    def _get_app_region(self) -> None:
        """从被测试机获取应用窗口信息"""
        try:
            response = self._send_request("get_app_region", {})
            if response.get("success"):
                self.app_region = response["data"]["app_region"]
                x, y, w, h = self.app_region
                print(f"获取应用窗口区域: 位置({x},{y}), 大小({w}x{h})")
            else:
                print(f"获取应用窗口区域失败: {response.get('error')}")
        except Exception as e:
            print(f"获取应用窗口区域时发生错误: {str(e)}")

    def get_screenshot(self, region: Optional[List[int]] = None) -> Optional[np.ndarray]:
        """获取被测试机的屏幕截图"""
        use_region = region if region is not None else self.app_region

        response = self._send_request("get_screenshot", {"region": use_region})
        if not response.get("success"):
            print(f"获取截图失败: {response.get('error')}")
            return None

        try:
            img_hex = response["data"]["screenshot"]
            if len(img_hex) != response["data"]["size"]:
                print(f"数据不完整：接收{len(img_hex)}字节，预期{response["data"]['size']}字节")
                return None
            img_bytes = bytes.fromhex(img_hex)
            img = Image.open(io.BytesIO(img_bytes))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"图片解码失败: {str(e)}")
            return None

    def find_image(self, image_path: str, threshold: float = 0.8, region: Optional[List[int]] = None) -> Dict:
        """在被测试机屏幕上查找目标图片"""
        use_region = region if region is not None else self.app_region

        try:
            template = cv2.imread(image_path)
            if template is None:
                return {"success": False, "error": "目标图片不存在或无法读取"}
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            t_height, t_width = template_gray.shape[:2]
        except Exception as e:
            return {"success": False, "error": f"读取目标图片失败: {str(e)}"}

        screenshot = self.get_screenshot(use_region)
        if screenshot is None:
            return {"success": False, "error": "无法获取屏幕截图"}

        try:
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)

            if len(locations[0]) > 0:
                y, x = locations[0][0], locations[1][0]
                return {
                    "success": True,
                    "data": {
                        "x": x,
                        "y": y,
                        "width": t_width,
                        "height": t_height,
                        "center_x": x + t_width // 2,
                        "center_y": y + t_height // 2,
                        "confidence": float(result[y, x])
                    }
                }
            else:
                return {"success": False, "error": "未找到匹配的图片"}
        except Exception as e:
            return {"success": False, "error": f"图片匹配失败: {str(e)}"}

    def get_element_info(self, element_path: str, role_name_list: Optional[List[Optional[str]]] = None) -> Dict:
        """请求获取元素信息"""
        return self._send_request(
            request_type="get_element",
            data={
                "element_path": element_path,
                "role_name_list": role_name_list
            }
        )

    def execute_commands(self, commands: List[Dict]) -> Dict:
        """发送指令集到被测试机器执行"""
        return self._send_request(
            request_type="exec_commands",
            data={"commands": commands}
        )
    
    def disconnect(self) -> Dict:
        """主动断开与被测试机器的连接"""
        return self._send_request(
            request_type="disconnect",
            data={}
        )

    def close(self) -> None:
        """关闭连接"""
        if self.socket:
            self.socket.close()
            print("连接已关闭")

# 保持向后兼容，TestMachineCommunicator 现在指向新的多机器版本
# 如果需要单机器版本，使用 SingleMachineCommunicator
