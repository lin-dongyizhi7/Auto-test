#!/usr/bin/env python3
"""
多机器环境下的操作类

这个类专注于在多机器环境下的元素操作，包括：
1. 鼠标操作（点击、移动、拖拽）
2. 键盘操作（输入、快捷键）
3. 元素查找和定位
4. 截图和图像识别
5. 操作指令的生成和执行

多机器连接和事件管理由 TestMachineCommunicator 负责
"""

import json
import time
import logging
from typing import Dict, List, Optional, Union, Any
from .test_communicator import TestMachineCommunicator, EventType, Event

class MultiMachineOperation:
    """
    多机器环境下的操作类，专注于元素操作
    多机器连接和事件管理由 TestMachineCommunicator 负责
    """
    
    def __init__(self, communicator: TestMachineCommunicator):
        """
        初始化多机器操作类
        
        :param communicator: TestMachineCommunicator 实例，负责多机器连接和事件管理
        """
        self.communicator = communicator
        
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
        
        self.logger.info("多机器操作类已初始化")
    
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
            if target_app_id not in self.communicator.apps:
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
            return list(self.communicator.machines.keys())
        except Exception as e:
            self.logger.error(f"获取机器列表失败: {str(e)}")
            return []
    
    def get_available_apps(self, machine_id: str = None) -> List[Dict]:
        """获取可用的应用列表"""
        try:
            apps = self.communicator.apps
            if machine_id:
                return [app for aid, app in apps.items() if app["machine_id"] == machine_id]
            return list(apps.values())
        except Exception as e:
            self.logger.error(f"获取应用列表失败: {str(e)}")
            return []
    
    def get_machine_status(self, machine_id: str) -> Dict[str, Any]:
        """获取指定机器的状态"""
        return self.communicator.get_machine_status(machine_id)
    
    def get_app_status(self, app_id: str) -> Dict[str, Any]:
        """获取指定应用的状态"""
        return self.communicator.get_app_status(app_id)
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """获取连接状态摘要"""
        return self.communicator.get_connection_summary()
    
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
    
    # ==================== 图像识别和截图操作 ====================
    
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
        
        # 获取截图（通过通信器转发到目标机器）
        response = self.communicator._forward_request_to_machine(
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
    
    def get_screenshot(self, region: Optional[List[int]] = None) -> Dict:
        """
        获取当前目标应用的截图
        
        :param region: 可选区域 [x, y, width, height]
        :return: 截图结果
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        return self.communicator._forward_request_to_machine(
            self.current_machine_id,
            "get_screenshot",
            {"app_name": self.current_app_name, "region": region}
        )
    
    # ==================== 元素定位操作 ====================
    
    def get_location(self, element_path: str, role_name_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取元素位置信息
        
        :param element_path: 元素路径，格式"父元素1/父元素2/目标元素"
        :param role_name_list: 元素角色名列表（可选），支持多个角色名匹配
        :return: 元素位置信息字典，包含{x,y,width,height,center_x,center_y}
        """
        if not self._check_target_set():
            raise ValueError("请先使用 set_target() 设置目标机器和应用")
        
        # 通过通信器转发到目标机器
        response = self.communicator._forward_request_to_machine(
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
    
    # ==================== 鼠标操作 ====================
    
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
    
    def drag_and_drop(self, start_element: str, end_element: str, role_name_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成拖拽操作的指令
        
        :param start_element: 起始元素路径
        :param end_element: 目标元素路径
        :param role_name_list: 元素角色名列表（可选）
        """
        if not self._check_target_set():
            return []
        
        start_loc = self.get_location(start_element, role_name_list)
        end_loc = self.get_location(end_element, role_name_list)
        commands = []
        
        # 移动到起始元素
        commands.append(self._generate_command(
            "mouse_move",
            {"x": start_loc["center_x"], "y": start_loc["center_y"]}
        ))
        
        # 按下鼠标左键
        commands.append(self._generate_command(
            "mouse_press",
            {"x": start_loc["center_x"], "y": start_loc["center_y"], "button": "left"}
        ))
        
        # 拖拽到目标位置
        commands.append(self._generate_command(
            "mouse_drag",
            {"start_x": start_loc["center_x"], "start_y": start_loc["center_y"],
             "end_x": end_loc["center_x"], "end_y": end_loc["center_y"]}
        ))
        
        # 释放鼠标左键
        commands.append(self._generate_command(
            "mouse_release",
            {"x": end_loc["center_x"], "y": end_loc["center_y"], "button": "left"}
        ))
        
        self.finish_current_opts(commands)
        return commands
    
    # ==================== 键盘操作 ====================
    
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
    
    def key_press(self, key: str) -> Dict:
        """
        生成按键操作的指令
        
        :param key: 按键名称
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        commands = [self._generate_command("key_press", {"key": key})]
        self.finish_current_opts(commands)
        return {"success": True, "commands": commands}
    
    def key_release(self, key: str) -> Dict:
        """
        生成按键释放的指令
        
        :param key: 按键名称
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        commands = [self._generate_command("key_release", {"key": key})]
        self.finish_current_opts(commands)
        return {"success": True, "commands": commands}
    
    # ==================== 等待和验证操作 ====================
    
    def wait_for_element(self, element_path: str, timeout: int = 30, role_name_list: Optional[List[str]] = None) -> Dict:
        """
        等待元素出现
        
        :param element_path: 元素路径
        :param timeout: 超时时间（秒）
        :param role_name_list: 元素角色名列表（可选）
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                loc = self.get_location(element_path, role_name_list)
                return {"success": True, "data": loc}
            except ValueError:
                time.sleep(0.5)
                continue
        
        return {"success": False, "error": f"等待元素 {element_path} 超时"}
    
    def wait_for_image(self, image_path: str, threshold: float = 0.8, timeout: int = 30, region: Optional[List[int]] = None) -> Dict:
        """
        等待图片出现
        
        :param image_path: 图片路径
        :param threshold: 匹配阈值
        :param timeout: 超时时间（秒）
        :param region: 查找区域
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.find_image(image_path, threshold, region)
            if result.get("success"):
                return result
            time.sleep(0.5)
        
        return {"success": False, "error": f"等待图片 {image_path} 超时"}
    
    # ==================== 指令执行管理 ====================
    
    def _execute_commands_on_target(self, commands: List[Dict]) -> Dict:
        """
        在目标机器和应用上执行指令集
        
        :param commands: 指令列表
        :return: 执行结果
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}
        
        try:
            response = self.communicator._forward_request_to_machine(
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
    
    def execute_commands(self) -> Dict[str, Any]:
        """
        执行当前指令集中的所有指令
        
        :return: 执行结果字典
        """
        if not self.opts:
            return {"success": False, "error": "没有可执行的指令"}
        
        result = self._execute_commands_on_target(self.opts)
        self.opts = []
        return result
    
    # ==================== 工具方法 ====================
    
    def export_to_json(self, file_path: str) -> None:
        """
        将.commands_list导出为JSON文件
        
        :param file_path: 导出JSON文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.commands_list, f, ensure_ascii=False, indent=2)
    
    def clear_commands(self) -> None:
        """清空所有指令"""
        self.opts = []
        self.commands_list = []
        self.logger.info("已清空所有指令")
    
    def get_commands_count(self) -> Dict[str, int]:
        """获取指令统计信息"""
        return {
            "current_opts": len(self.opts),
            "total_commands": len(self.commands_list),
            "total_individual_commands": sum(len(cmd_list) for cmd_list in self.commands_list)
        }
    
    def close(self) -> None:
        """清理资源"""
        self.logger.info("多机器操作类已关闭")

    # ==================== 脚本执行（JSON） ====================

    def run_script_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        从 JSON 文件读取测试脚本并执行

        脚本示例结构：
        {
            "target_machine_id": "machine_001",
            "target_app_name": "calculator",
            "steps": [
                {"id": "1", "type": "wait_element", "element_path": "菜单/文件", "role_name_list": ["menu item"], "description": "等待菜单"},
                {"id": "2", "type": "click_element", "element_path": "菜单/文件/新建", "role_name_list": ["menu item"], "children": [
                    {"id": "2.1", "type": "wait_element", "element_path": "新建对话框/确定", "role_name_list": ["push button"]},
                    {"id": "2.2", "type": "click_element", "element_path": "新建对话框/确定", "role_name_list": ["push button"]}
                ]}
            ]
        }
        """
        with open(file_path, "r", encoding="utf-8") as f:
            script_obj = json.load(f)
        return self.run_script(script_obj)

    def run_script(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行传入的脚本对象（同 run_script_from_file 的结构）
        - 若提供 target_machine_id/target_app_name，则先 set_target
        - 递归执行 steps，父步骤等待所有子步骤完成
        - 任一步失败将停止并返回错误
        """
        target_machine_id = script.get("target_machine_id")
        target_app_name = script.get("target_app_name")
        if target_machine_id and target_app_name:
            ok = self.set_target(target_machine_id, target_app_name)
            if not ok:
                return {"success": False, "error": f"设置目标失败: {target_machine_id}/{target_app_name}"}

        steps: List[Dict[str, Any]] = script.get("steps", [])
        if not isinstance(steps, list) or not steps:
            return {"success": False, "error": "脚本缺少 steps 或 steps 为空"}

        for step in steps:
            result = self._execute_step(step)
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "未知错误"), "failed_step": step.get("id")}

        return {"success": True}

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个步骤并在存在子步骤时递归执行：
        - 先执行当前步骤自身操作（若 type 可映射到现有方法）
        - 然后依次执行 children（若存在），父步骤等待所有子步骤成功
        - 任意失败立即返回失败
        支持的 type（可扩展）：
        - click_element, right_click_element, double_click_element
        - input_text（需 text 字段，可选 element_path）
        - hotkey（需 keys: List[str]）
        - wait_element
        - click_image（需 image_path, 可选 threshold）
        - move_to_element_center
        """
        step_type = step.get("type")
        if not step_type:
            return {"success": False, "error": "步骤缺少 type"}

        # 1) 执行当前步骤
        try:
            exec_result = self._dispatch_step(step)
            if exec_result is not None and isinstance(exec_result, dict) and not exec_result.get("success", True):
                return exec_result
        except Exception as e:
            return {"success": False, "error": f"执行步骤异常: {e}"}

        # 2) 执行子步骤（若存在）
        children = step.get("children") or step.get("steps")
        if children and isinstance(children, list):
            for child in children:
                child_result = self._execute_step(child)
                if not child_result.get("success"):
                    return child_result

        return {"success": True}

    def _dispatch_step(self, step: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        将 step 映射到已有操作方法并执行。
        返回：
        - 对需要返回状态的操作，返回 {success: bool, ...}
        - 对仅生成/发送指令的方法，返回 None 或成功结构
        """
        step_type = step.get("type")
        element_path = step.get("element_path")
        role_name_list = step.get("role_name_list")

        if step_type == "click_element":
            self.click_element(element_path, role_name_list)
            return {"success": True}
        if step_type == "right_click_element":
            self.right_click_element(element_path, role_name_list)
            return {"success": True}
        if step_type == "double_click_element":
            self.double_click_element(element_path, role_name_list)
            return {"success": True}
        if step_type == "move_to_element_center":
            res = self.move_to_element_center(element_path, role_name_list)
            return res if isinstance(res, dict) else {"success": True}
        if step_type == "input_text":
            text = step.get("text", "")
            self.input_text(element_path, text, role_name_list)
            return {"success": True}
        if step_type == "hotkey":
            keys = step.get("keys") or []
            return self.hotkey(keys)
        if step_type == "wait_element":
            timeout = int(step.get("timeout", 30))
            return self.wait_for_element(element_path, timeout=timeout, role_name_list=role_name_list)
        if step_type == "click_image":
            image_path = step.get("image_path") or step.get("imagePath")
            threshold = float(step.get("threshold", 0.8))
            return self.click_image(image_path, threshold)

        # 未知类型：忽略或失败，这里选择失败以便提示
        return {"success": False, "error": f"不支持的步骤类型: {step_type}"}

