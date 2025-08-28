#!/usr/bin/env python3
"""
多机器环境下的操作类

这个类封装了在多机器环境下的Dogtail交互操作，支持：
1. 与多台被测试机器通信
2. 与不同应用进行交互
3. 跨机器的操作协调
4. 事件同步和状态监控

使用方法：
1. 在测试控制机器上运行test_communicator.py作为服务器
2. 在被测试机器上运行tested_communicator.py作为客户端
3. 使用本类进行跨机器的自动化操作
"""

import json
import time
import logging
from typing import Dict, List, Optional, Union
from .test_communicator import TestMachineCommunicator, EventType, Event

class MultiMachineOperation:
    """
    多机器环境下的操作类，支持与多台机器和多个应用进行交互
    """
    
    def __init__(self, bind_host: str = "0.0.0.0", server_port: int = 8889, retry_interval_sec: int = 3):
        """
        初始化多机器操作类，并在本机启动测试服务器（长期监听）
        
        :param bind_host: 测试服务器绑定地址
        :param server_port: 测试服务器端口
        :param retry_interval_sec: 启动失败后的重试间隔
        """
        self.bind_host = bind_host
        self.server_port = server_port
        self.retry_interval_sec = retry_interval_sec
        
        # 存储操作指令
        self.opts = []  # 当前操作的指令序列
        self.commands_list = []  # 整个测试文件生成的指令列表
        
        # 当前操作的机器和应用
        self.current_machine_id = None
        self.current_app_name = None
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        # 启动本地测试服务器（保持监听，失败重试）
        self.server = None
        self._start_server_with_retry()
    
    def _start_server_with_retry(self) -> None:
        """在本机启动测试服务器；若端口被占用或失败则定时重试，不中断运行"""
        while True:
            try:
                self.server = TestMachineCommunicator(server_host=self.bind_host, server_port=self.server_port)
                self.server.start_server()
                self.logger.info(f"测试服务器已启动并监听 {self.bind_host}:{self.server_port}")
                break
            except Exception as e:
                self.logger.error(f"测试服务器启动失败: {str(e)}，将在{self.retry_interval_sec}s后重试…")
                time.sleep(self.retry_interval_sec)
    
    def set_target(self, machine_id: str, app_name: str) -> bool:
        """
        设置当前操作的目标机器和应用
        
        :param machine_id: 目标机器ID
        :param app_name: 目标应用名称
        :return: 设置是否成功
        """
        try:
            # 验证机器和应用是否存在
            target_app_id = f"{machine_id}:{app_name}"
            if target_app_id not in self.server.apps:
                self.logger.error(f"应用 {app_name} 在机器 {machine_id} 上未注册")
                return False
            
            self.current_machine_id = machine_id
            self.current_app_name = app_name
            self.logger.info(f"设置操作目标: 机器 {machine_id}, 应用 {app_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置目标失败: {str(e)}")
            return False
    
    def get_available_machines(self) -> List[str]:
        """获取可用的机器列表"""
        try:
            return list(self.server.machines.keys())
        except Exception as e:
            self.logger.error(f"获取机器列表失败: {str(e)}")
            return []
    
    def get_available_apps(self, machine_id: str = None) -> List[Dict]:
        """获取可用的应用列表"""
        try:
            apps = self.server.apps
            if machine_id:
                return [app for aid, app in apps.items() if app["machine_id"] == machine_id]
            return list(apps.values())
        except Exception as e:
            self.logger.error(f"获取应用列表失败: {str(e)}")
            return []
    
    def _generate_command(self, action: str, params: Dict) -> Dict:
        """
        生成单个操作指令
        
        :param action: 操作类型（如"mouse_move", "mouse_click"等）
        :param params: 操作参数字典
        :return: 格式化的操作指令字典
        """
        command = {
            "action": action,
            "params": params,
            "timestamp": self._get_timestamp()
        }
        self.opts.append(command)
        return command
    
    def _get_timestamp(self) -> float:
        """获取当前时间戳"""
        return time.time()
    
    def _check_target_set(self) -> bool:
        """检查是否已设置目标机器和应用"""
        if not self.current_machine_id or not self.current_app_name:
            self.logger.error("请先使用 set_target() 设置目标机器和应用")
            return False
        return True
    
    def find_image(self, image_path: str, threshold: float = 0.8, region: Optional[List[int]] = None) -> Dict:
        """
        查找图片位置
        
        :param image_path: 目标图片本地路径
        :param threshold: 匹配阈值
        :param region: 查找区域 [x, y, width, height]
        :return: 位置信息字典
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        self.logger.info(f"在机器 {self.current_machine_id} 的应用 {self.current_app_name} 上查找图片: {image_path}")
        
        # 获取截图（通过本地测试服务器转发到目标机器）
        response = self.server._forward_request_to_machine(
            self.current_machine_id,
            "get_screenshot",
            {"app_name": self.current_app_name, "region": region}
        )
        
        if not response.get("success"):
            return response
        
        # 这里需要实现图片匹配逻辑
        # 由于图片匹配需要本地处理，这里返回截图数据供后续处理
        return {
            "success": True,
            "data": {
                "screenshot": response["data"]["screenshot"],
                "size": response["data"]["size"],
                "machine_id": self.current_machine_id,
                "app_name": self.current_app_name
            }
        }
    
    def click_image(self, image_path: str, threshold: float = 0.8, region: Optional[List[int]] = None) -> Dict:
        """
        点击图片位置
        
        :param image_path: 目标图片本地路径
        :return: 操作结果
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        # 查找图片（这里简化处理，假设已经知道位置）
        # 实际使用时需要先调用find_image获取位置
        find_result = self.find_image(image_path, threshold, region)
        if not find_result.get("success"):
            return find_result
        
        # 生成点击指令（这里使用固定坐标作为示例）
        # 实际使用时应该从find_result中获取坐标
        commands = [
            self._generate_command("mouse_move", {"x": 100, "y": 100}),
            self._generate_command("mouse_click", {"x": 100, "y": 100, "button": "left"})
        ]
        
        self.commands_list.append(commands)
        result = self._execute_commands_on_target(commands)
        self.opts = []
        return result
    
    def get_location(self, element_path: str, role_name_list: Optional[List[str]] = None) -> Dict[str, any]:
        """
        获取元素位置信息
        
        :param element_path: 元素路径，格式"父元素1/父元素2/目标元素"
        :param role_name_list: 元素角色名列表（可选），支持多个角色名匹配
        :return: 元素位置信息字典，包含{x,y,width,height,center_x,center_y}
        """
        if not self._check_target_set():
            raise ValueError("请先使用 set_target() 设置目标机器和应用")
        
        # 通过本地测试服务器转发到目标机器
        response = self.server._forward_request_to_machine(
            self.current_machine_id,
            "get_element",
            {
                "app_name": self.current_app_name,
                "element_path": element_path,
                "role_name_list": role_name_list,
            }
        )
        
        # 验证响应是否成功
        if not response.get("success", False):
            raise ValueError(f"获取元素位置失败: {response.get('error', '未知错误')}")
        
        # 提取并返回必要的位置信息
        element_data = response["data"]
        position = element_data["position"]
        size = element_data["size"]
        return {
            "x": position["x"],
            "y": position["y"],
            "width": size["width"],
            "height": size["height"],
            "center_x": position["x"] + size["width"] // 2,
            "center_y": position["y"] + size["height"] // 2
        }
    
    def click_element(self, element_path: str, role_name_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成点击元素的指令（移动到中心位置后点击）
        
        :param element_path: 元素路径
        :param role_name_list: 元素角色名列表（可选），支持多个角色名匹配
        """
        if not self._check_target_set():
            return []
        
        loc = self.get_location(element_path, role_name_list)
        commands = []
        
        # 移动到元素中心
        commands.append(self._generate_command(
            "mouse_move",
            {"x": loc["center_x"], "y": loc["center_y"]}
        ))
        
        # 左键点击
        commands.append(self._generate_command(
            "mouse_click",
            {"x": loc["center_x"], "y": loc["center_y"], "button": "left"}
        ))
        
        self.finish_current_opts(commands)
        return commands
    
    def right_click_element(self, element_path: str, role_name_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成右键点击元素的指令
        
        :param element_path: 元素路径
        :param role_name_list: 元素角色名列表（可选）
        """
        if not self._check_target_set():
            return []
        
        loc = self.get_location(element_path, role_name_list)
        commands = []
        
        commands.append(self._generate_command(
            "mouse_move",
            {"x": loc["center_x"], "y": loc["center_y"]}
        ))
        
        commands.append(self._generate_command(
            "mouse_click",
            {"x": loc["center_x"], "y": loc["center_y"], "button": "right"}
        ))
        
        self.finish_current_opts(commands)
        return commands
    
    def double_click_element(self, element_path: str, role_name_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成双击元素的指令
        
        :param element_path: 元素路径
        :param role_name_list: 元素角色名列表（可选）
        """
        if not self._check_target_set():
            return []
        
        loc = self.get_location(element_path, role_name_list)
        commands = []
        
        commands.append(self._generate_command(
            "mouse_move",
            {"x": loc["center_x"], "y": loc["center_y"]}
        ))
        
        commands.append(self._generate_command(
            "mouse_click",
            {"x": loc["center_x"], "y": loc["center_y"], "button": "left"}
        ))
        
        commands.append(self._generate_command(
            "mouse_click",
            {"x": loc["center_x"], "y": loc["center_y"], "button": "left"}
        ))
        
        self.finish_current_opts(commands)
        return commands
    
    def set_element_text(self, element_path: str, text: str, role_name_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成设置元素文本的指令
        
        :param element_path: 元素路径
        :param text: 要设置的文本内容
        :param role_name_list: 元素角色名列表（可选）
        """
        if not self._check_target_set():
            return []
        
        loc = self.get_location(element_path, role_name_list)
        commands = []
        
        # 点击激活元素
        commands.append(self._generate_command(
            "mouse_move",
            {"x": loc["center_x"], "y": loc["center_y"]}
        ))
        
        commands.append(self._generate_command(
            "mouse_click",
            {"x": loc["center_x"], "y": loc["center_y"], "button": "left"}
        ))
        
        # 全选（Ctrl+A）
        commands.append(self._generate_command(
            "hotkey",
            {"keys": ["Ctrl", "a"]}
        ))
        
        # 删除
        commands.append(self._generate_command(
            "key_press",
            {"key": "Delete"}
        ))
        
        # 输入文本
        for char in text:
            commands.append(self._generate_command(
                "key_press",
                {"key": char}
            ))
        
        self.finish_current_opts(commands)
        return commands
    
    def input_text(self, element_path: Optional[str], text: str, role_name_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成输入文本的指令
        
        :param element_path: 元素路径（可选）
        :param text: 要输入的文本内容
        :param role_name_list: 元素角色名列表（可选）
        """
        if not self._check_target_set():
            return []
        
        commands = []
        
        # 若指定元素，先点击激活
        if element_path:
            loc = self.get_location(element_path, role_name_list)
            commands.append(self._generate_command(
                "mouse_move",
                {"x": loc["center_x"], "y": loc["center_y"]}
            ))
            
            commands.append(self._generate_command(
                "mouse_click",
                {"x": loc["center_x"], "y": loc["center_y"], "button": "left"}
            ))
        
        # 输入文本
        for char in text:
            commands.append(self._generate_command(
                "key_press",
                {"key": char}
            ))
        
        self.finish_current_opts(commands)
        return commands
    
    def hotkey(self, keys: List[str]) -> Dict:
        """
        生成组合键操作的指令
        
        :param keys: 组合键列表，如["Ctrl", "c"]
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        commands = [self._generate_command("hotkey", {"keys": keys})]
        self.finish_current_opts(commands)
        return {"success": True, "commands": commands}
    
    def move_to(self, x: int, y: int) -> Dict:
        """
        生成鼠标移动到指定位置的指令
        
        :param x: X坐标
        :param y: Y坐标
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        commands = [self._generate_command("mouse_move", {"x": x, "y": y})]
        self.finish_current_opts(commands)
        return {"success": True, "commands": commands}
    
    def move_to_element_center(self, element_path: str, role_name_list: Optional[List[str]] = None) -> Dict:
        """
        生成鼠标移动到元素中心的指令
        
        :param element_path: 元素路径
        :param role_name_list: 元素角色名列表（可选）
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        loc = self.get_location(element_path, role_name_list)
        return self.move_to(loc["center_x"], loc["center_y"])
    
    def _execute_commands_on_target(self, commands: List[Dict]) -> Dict:
        """
        在目标机器和应用上执行指令集
        
        :param commands: 指令列表
        :return: 执行结果
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        try:
            response = self.server._forward_request_to_machine(
                self.current_machine_id,
                "exec_commands",
                {"app_name": self.current_app_name, "commands": commands}
            )
            
            if response.get("success"):
                self.logger.info(f"在机器 {self.current_machine_id} 的应用 {self.current_app_name} 上执行指令成功")
            else:
                self.logger.error(f"执行指令失败: {response.get('error')}")
            
            return response
            
        except Exception as e:
            error_msg = f"执行指令时发生异常: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def finish_current_opts(self, commands: List[Dict]) -> None:
        """
        结束当前操作指令集
        
        :param commands: 当前操作指令列表
        """
        self.commands_list.append(commands)
        self.opts = commands
        
        self.logger.info(f"当前操作要执行的指令集，共{len(commands)}条指令")
        result = self._execute_commands_on_target(commands)
        self.logger.info(f"执行指令集结果: {result}")
    
    def execute_commands(self) -> Dict[str, any]:
        """
        执行当前指令集中的所有指令
        
        :return: 执行结果字典
        """
        if not self.opts:
            return {"success": False, "error": "没有可执行的指令"}
        
        result = self._execute_commands_on_target(self.opts)
        self.opts = []
        return result
    
    def export_to_json(self, file_path: str) -> None:
        """
        将.commands_list导出为JSON文件
        
        :param file_path: 导出JSON文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.commands_list, f, ensure_ascii=False, indent=2)
    
    def get_screenshot(self, region: Optional[List[int]] = None) -> Dict:
        """
        获取当前目标应用的截图
        
        :param region: 可选区域 [x, y, width, height]
        :return: 截图结果
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        return self.server._forward_request_to_machine(
            self.current_machine_id,
            "get_screenshot",
            {"app_name": self.current_app_name, "region": region}
        )
    
    def subscribe_events(self) -> Dict:
        """订阅事件通知（本地调用无客户端身份，这里返回成功并依赖事件历史查询）"""
        self.logger.info("事件订阅在本地模式下为无操作（No-Op）")
        return {"success": True}
    
    def unsubscribe_events(self) -> Dict:
        """取消订阅事件通知（本地模式No-Op）"""
        self.logger.info("事件取消订阅在本地模式下为无操作（No-Op）")
        return {"success": True}
    
    def sync_event(self, event_type: str, data: Dict) -> Dict:
        """
        同步事件到测试服务器
        
        :param event_type: 事件类型
        :param data: 事件数据
        :return: 同步结果
        """
        try:
            evt = Event(
                type=EventType(event_type) if isinstance(event_type, str) else event_type,
                machine_id=self.current_machine_id or "controller",
                app_name=self.current_app_name,
                timestamp=time.time(),
                data=data or {},
                source_machine=self.current_machine_id or "controller",
            )
            self.server._publish_event(evt)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def close(self) -> None:
        """停止本地测试服务器并清理"""
        try:
            if getattr(self, "server", None):
                self.server.stop_server()
        finally:
            self.logger.info("本地测试服务器已停止")

