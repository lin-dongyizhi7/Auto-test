import socket
import json
import time
from typing import Dict, List, Optional

class TestMachineCommunicator:
    """测试者机器的通信类，用于向被测试机器发送请求并接收响应"""
    
    def __init__(self, target_host: str, target_port: int):
        self.target_host = target_host
        self.target_port = target_port
        self.socket = None
        self._connect()

    def _connect(self) -> None:
        """建立与被测试机器的TCP连接"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.target_host, self.target_port))
            print(f"成功连接到被测试机器 {self.target_host}:{self.target_port}")
        except Exception as e:
            raise ConnectionError(f"无法连接到被测试机器: {str(e)}")

    def _send_request(self, request_type: str, data: Dict) -> Dict:
        """
        发送请求到被测试机器并接收响应
        :param request_type: 请求类型（get_element/exec_commands）
        :param data: 请求数据
        :return: 被测试机器的响应结果
        """
        if not self.socket:
            self._connect()

        try:
            # 构建请求格式
            request = {
                "type": request_type,
                "data": data,
                "timestamp": time.time()
            }
            # 发送请求
            sendJson = json.dumps(request).encode('utf-8')
            print(f"发送请求: {request_type}, 数据: {data}")
            # 发送请求长度和内容
            self.socket.sendall(sendJson)
            
            # 接收响应（设置1024*1024字节缓冲区）
            response_data = self.socket.recv(1024 * 1024).decode('utf-8')
            return json.loads(response_data)
        except Exception as e:
            self.socket = None  # 连接异常时重置
            raise RuntimeError(f"通信错误: {str(e)}")

    def get_element_info(self, element_path: str, role_name: Optional[str] = None) -> Dict:
        """
        请求获取元素信息
        :param element_path: 元素路径（如"菜单/文件/新建"）
        :param role_name: 元素角色名（如"push button"）
        :return: 元素信息字典，包含position和size等
        """
        return self._send_request(
            request_type="get_element",
            data={
                "element_path": element_path,
                "role_name": role_name
            }
        )

    def execute_commands(self, commands: List[Dict]) -> Dict:
        """
        发送指令集到被测试机器执行
        :param commands: 指令集列表（如mouse_move, mouse_click等）
        :return: 执行结果
        """
        return self._send_request(
            request_type="exec_commands",
            data={"commands": commands}
        )
    
    def disconnect(self) -> Dict:
        """
        主动断开与被测试机器的连接
        :return: 断开连接的响应结果
        """
        return self._send_request(
            request_type="disconnect",
            data={}
        )

    def close(self) -> None:
        """关闭连接"""
        if self.socket:
            self.socket.close()
            print("连接已关闭")
