import socket
import json
import time
import cv2
import numpy as np
from PIL import Image
import io
from typing import Dict, List, Optional

class TestMachineCommunicator:
    """测试者机器的通信类，用于向被测试机器发送请求并接收响应"""
    
    def __init__(self, target_host: str, target_port: int):
        self.target_host = target_host
        self.target_port = target_port
        self.socket = None
        self.app_region = None  # 应用区域，默认为None表示全屏
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
            
            # 接收响应（设置4096*1024字节缓冲区）
            response_data = self.socket.recv(4096 * 1024).decode('utf-8')
            return json.loads(response_data)
        
        except Exception as e:
            self.socket = None  # 连接异常时重置
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
        """
        获取被测试机的屏幕截图
        :param region: 可选区域 [x, y, width, height]
        :return: 截图的OpenCV图像对象
        """
        use_region = region if region is not None else self.app_region

        response = self._send_request("get_screenshot", {"region": use_region})
        if not response.get("success"):
            print(f"获取截图失败: {response.get('error')}")
            return None

        # 解码16进制图片数据
        try:
            img_hex = response["data"]["screenshot"]
            # 校验数据长度
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
        """
        在被测试机屏幕上查找目标图片
        :param image_path: 目标图片本地路径
        :param threshold: 匹配阈值（0-1），越高越精确
        :param region: 限制查找区域 [x, y, width, height]
        :return: 包含位置信息的字典
        """
        use_region = region if region is not None else self.app_region

        # 读取本地目标图片
        try:
            template = cv2.imread(image_path)
            if template is None:
                return {"success": False, "error": "目标图片不存在或无法读取"}
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            t_height, t_width = template_gray.shape[:2]
        except Exception as e:
            return {"success": False, "error": f"读取目标图片失败: {str(e)}"}

        # 获取被测试机截图
        screenshot = self.get_screenshot(use_region)
        if screenshot is None:
            return {"success": False, "error": "无法获取屏幕截图"}

        # 图片匹配
        try:
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)

            # 提取匹配位置（取最匹配的第一个结果）
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
        """
        请求获取元素信息
        :param element_path: 元素路径（如"菜单/文件/新建"）
        :param role_name_list: 元素角色名（如"push button"）
        :return: 元素信息字典，包含position和size等
        """
        return self._send_request(
            request_type="get_element",
            data={
                "element_path": element_path,
                "role_name_list": role_name_list
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
