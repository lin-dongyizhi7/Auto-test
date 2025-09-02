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
        
        # 连接状态监控
        self.connection_status = {}
        self.last_heartbeat = {}
        
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
            
            # 启动服务器监听线程
            self.server_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.server_thread.start()
            
        except Exception as e:
            raise RuntimeError(f"启动测试服务器失败: {str(e)}")
    
    def _accept_connections(self) -> None:
        """接受多机器连接"""
        while self.is_running:
            try:
                client_socket, client_addr = self.server_socket.accept()
                print(f"新机器连接: {client_addr}")
                
                # 为每个连接创建处理线程
                client_thread = threading.Thread(
                    target=self._handle_machine_connection,
                    args=(client_socket, client_addr),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.is_running:
                    print(f"接受连接时发生错误: {str(e)}")
    
    def _handle_machine_connection(self, client_socket: socket.socket, client_addr: tuple) -> None:
        """处理单个机器连接"""
        machine_id = None
        try:
            # 等待机器发送注册信息
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                return
                
            register_info = json.loads(data)
            machine_id = register_info.get("machine_id")
            machine_info = register_info.get("machine_info", {})
            
            if not machine_id:
                print(f"机器 {client_addr} 未提供有效的machine_id")
                return
            
            # 注册机器
            self.machines[machine_id] = {
                "address": client_addr,
                "info": machine_info,
                "connected_at": time.time(),
                "status": "connected",
                "last_seen": time.time()
            }
            self.connections[machine_id] = client_socket
            
            # 发送注册成功响应
            response = {"success": True, "message": "机器注册成功"}
            client_socket.sendall(json.dumps(response).encode('utf-8'))
            
            # 发布机器连接事件
            self._publish_event(Event(
                type=EventType.MACHINE_CONNECTED,
                machine_id=machine_id,
                app_name=None,
                timestamp=time.time(),
                data={"address": client_addr, "info": machine_info},
                source_machine=machine_id
            ))
            
            print(f"机器 {machine_id} 注册成功，地址: {client_addr}")
            
            # 保持连接，处理请求
            while self.is_running and machine_id in self.connections:
                try:
                    data = client_socket.recv(1024 * 1024).decode('utf-8')
                    if not data:
                        break
                    
                    request = json.loads(data)
                    response = self._handle_request(machine_id, request)
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    
                    # 更新最后活跃时间
                    if machine_id in self.machines:
                        self.machines[machine_id]["last_seen"] = time.time()
                    
                except json.JSONDecodeError:
                    error_msg = {"success": False, "error": "无效的JSON格式"}
                    client_socket.sendall(json.dumps(error_msg).encode('utf-8'))
                except Exception as e:
                    error_msg = {"success": False, "error": f"处理请求失败: {str(e)}"}
                    client_socket.sendall(json.dumps(error_msg).encode('utf-8'))
                    
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

            # 发送注册信息（作为客户端向目标机器注册）
            register_info = {
                "machine_id": self.server_id,  # 当前服务器标识
                "machine_info": {"role": "test_server"}
            }
            client_socket.sendall(json.dumps(register_info).encode('utf-8'))

            # 等待响应
            response = client_socket.recv(1024).decode('utf-8')
            if not response:
                client_socket.close()
                return {"success": False, "error": "连接后未收到响应"}

            response_data = json.loads(response)
            if not response_data.get("success"):
                client_socket.close()
                return {"success": False, "error": response_data.get("error", "注册失败")}

            # 注册机器信息
            self.machines[machine_id] = {
                "address": (host, port),
                "info": {"host": host, "port": port},
                "connected_at": time.time(),
                "status": "connected",
                "last_seen": time.time()
            }
            self.connections[machine_id] = client_socket

            # 启动处理线程
            client_thread = threading.Thread(
                target=self._handle_machine_connection,
                args=(client_socket, (host, port)),
                daemon=True
            )
            client_thread.start()

            # 发布连接事件
            self._publish_event(Event(
                type=EventType.MACHINE_CONNECTED,
                machine_id=machine_id,
                app_name=None,
                timestamp=time.time(),
                data={"address": (host, port)},
                source_machine=self.server_id
            ))

            return {"success": True, "message": f"成功连接到机器 {machine_id}"}

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
        
        if request_type == "register_app":
            return self._handle_app_registration(machine_id, request)
        elif request_type == "get_screenshot":
            return self._handle_screenshot_request(machine_id, request)
        elif request_type == "get_element":
            return self._handle_element_request(machine_id, request)
        elif request_type == "exec_commands":
            return self._handle_command_execution(machine_id, request)
        elif request_type == "subscribe_events":
            return self._handle_event_subscription(machine_id, request)
        elif request_type == "unsubscribe_events":
            return self._handle_event_unsubscription(machine_id, request)
        elif request_type == "get_machines":
            return self._handle_get_machines_request()
        elif request_type == "get_apps":
            return self._handle_get_apps_request()
        elif request_type == "sync_event":
            return self._handle_event_sync(machine_id, request)
        elif request_type == "heartbeat":
            return self._handle_heartbeat(machine_id, request)
        else:
            return {"success": False, "error": f"未知请求类型: {request_type}"}
    
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
            
            socket.sendall(json.dumps(request).encode('utf-8'))
            
            # 接收响应
            response_data = socket.recv(4096 * 1024).decode('utf-8')
            return json.loads(response_data)
            
        except Exception as e:
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
                            socket.sendall(json.dumps(event_data).encode('utf-8'))
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
        
        # 关闭所有连接
        for machine_id in list(self.connections.keys()):
            self._disconnect_machine(machine_id)
        
        # 关闭服务器socket
        if self.server_socket:
            self.server_socket.close()
        
        print("测试服务器已停止")

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
