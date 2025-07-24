import socket
import json
import time
import random
import dogtail.tree
from dogtail.rawinput import click, press, release, absoluteMotion, keyCombo
from typing import Dict, List, Optional

class TestedMachineCommunicator:
    """被测试机器的通信类，监听8888端口并处理测试者的请求"""
    
    def __init__(self, bind_host: str = "0.0.0.0", bind_port: int = 8888):
        """
        初始化通信服务
        :param bind_host: 绑定的IP地址（0.0.0.0表示允许所有网络连接）
        :param bind_port: 监听的端口（默认8888）
        """
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置端口复用，避免服务重启时出现"端口已被占用"错误
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False  # 服务运行状态
        self.app = None  # 被测应用实例

    def _get_element(self, element_path: str, role_name_list: Optional[List[Optional[str]]] = None) -> Dict:
        """
        调用dogtail查询元素信息
        :param element_path: 元素路径（如"菜单/文件/新建"）
        :param role_name_list: 角色名列表，项数与路径级数相等，每项可为空（None或""）
                              例如：["window", "menu bar", "menu item"]
        :return: 包含元素位置、尺寸等信息的字典
        """
        print(f"查询元素: {element_path}, 角色: {role_name_list}")
        # 这里使用dogtail的tree模块来查找元素
        try:
            # # 若未指定应用，使用系统根窗口（所有应用）
            if not self.app:
                self.app = dogtail.tree.root

            # 拆分路径为各级元素名称
            path_parts = [part.strip() for part in element_path.split('/') if part.strip()]
            if not path_parts:
                return {"success": False, "error": "元素路径不能为空"}

            # 处理角色名列表（默认空列表，长度不足则补None，过长则截断）
            if not role_name_list:
                role_name_list = []
            # 确保列表长度与路径级数一致
            adjusted_roles = []
            for i in range(len(path_parts)):
                if i < len(role_name_list):
                    # 空字符串视为None（不限制角色）
                    adjusted_roles.append(role_name_list[i] if role_name_list[i] else None)
                else:
                    adjusted_roles.append(None)  # 长度不足补None

            current_element = self.app
            # 遍历所有层级（每级都可能有角色名）
            for i, part in enumerate(path_parts):
                current_role = adjusted_roles[i]
                # 按名称和当前级角色名查找（角色名为None则不限制）
                if current_role:
                    found_element = current_element.child(name=part, roleName=current_role)
                else:
                    found_element = current_element.child(name=part)

                if not found_element:
                    # 构建详细错误信息
                    error_path = '/'.join(path_parts[:i+1])
                    error_msg = f"元素不存在: {error_path}"
                    if current_role:
                        error_msg += f" (角色: {current_role})"
                    return {"success": False, "error": error_msg}

                current_element = found_element  # 进入下一级

            # 提取元素信息（位置、尺寸、中心坐标等）
            x, y = current_element.position
            width, height = current_element.size
            print(f"找到元素: {current_element.name}, 位置: ({x}, {y}), 尺寸: ({width}, {height})")
            # x = random.randint(1, 1200)
            # y = random.randint(1, 800)
            # width = random.randint(100, 800)
            # height = random.randint(100, 600)
            return {
                "success": True,
                "data": {
                    "position": {"x": x, "y": y},
                    "size": {"width": width, "height": height},
                    # "name": current_element.name,
                    # "role_name_list": current_element.roleName
                }
            }
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

                # 映射指令到dogtail的实际操作
                if action == "mouse_move":
                    absoluteMotion(params["x"], params["y"])  # 鼠标移动到绝对坐标

                elif action == "mouse_click":
                    click(
                        params["x"], 
                        params["y"], 
                        button=params.get("button", "left")  # 支持左键/右键
                    )

                elif action == "mouse_press":
                    press(button=params.get("button", "left"))  # 按下鼠标键

                elif action == "mouse_release":
                    release(button=params.get("button", "left"))  # 释放鼠标键

                elif action == "hotkey":
                    keyCombo(params["keys"])  # 执行组合键（如["CtrL", "a"]）

                elif action == "key_press":
                    keyCombo([params["key"]])  # 执行单个按键

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
                        if request["type"] == "get_element":
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
        communicator.start(app_name="QGIS3")  # 启动QGIS应用的测试服务
        # communicator.startt(app_name="calculator")  # 启动计算器应用的测试服务
        # communicator.start()
    except KeyboardInterrupt:
        # 按Ctrl+C停止服务
        communicator.stop()