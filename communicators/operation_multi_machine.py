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
        print(commands)
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
            {"x": loc["center_x"], "y": loc["center_y"], "button": "left", "clicks": 2}
        ))
        
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
    
    def validate_result(self, rule: Dict) -> Dict:
        """
        单次断言校验：发送断言请求到被测机器，由被测机器处理元素查找和断言比较。

        典型用法：对计算显示区域的文本进行比对
        - rule = {"type": "equal", "element_path": "主窗体/结果显示区域", "attr": "text", "expected": "8", "role_name_list": ["text"]}

        支持的 type：
        - equal, notequal, regex, contains, gt, gte, lt, lte, isnone, isnotnone, approx

        :param rule: 单条断言规则
        :return: { success: bool, error?: str, actual?: any, expected?: any }
        """
        if not self._check_target_set():
            return {"success": False, "error": "未设置目标机器和应用"}

        if not isinstance(rule, dict):
            return {"success": False, "error": "规则必须为对象"}

        element_path = rule.get("element_path")
        role_name_list = rule.get("role_name_list")
        # 兼容两种入参：新接口 expected，和 op_record 产出的 expect_value（attr 默认 text）
        attr_path = rule.get("attr") or "text"
        expected = rule.get("expected", rule.get("expect_value"))
        assert_type = rule.get("type", "equal")

        if not element_path:
            return {"success": False, "error": "规则缺少 element_path"}

        if expected is None:
            return {"success": False, "error": "期望值不能为空"}

        # 发送断言请求到被测机器
        try:
            assert_resp = self.communicator._forward_request_to_machine(
                self.current_machine_id,
                "assert",
                {
                    "element_path": element_path,
                    "role_name_list": role_name_list,
                    "expect_value": expected,
                    "attr": attr_path,
                    "type": assert_type
                }
            )
            
            return {
                "success": assert_resp.get("success", False),
                "actual": assert_resp.get("actual"),
                "expected": assert_resp.get("expected"),
                "error": assert_resp.get("error")
            }
            
        except Exception as e:
            return {"success": False, "error": f"断言请求异常: {str(e)}"}

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
        target_machine_id = self.current_machine_id
        target_app_name = script.get("target_app_name")
        self.logger.info(f"执行脚本: {target_machine_id}/{target_app_name}")
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
            try:
                commands = self.click_element(element_path, role_name_list)
                if commands:
                    result = self._execute_commands_on_target(commands)
                    return result
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": f"点击元素失败: {str(e)}"}
        if step_type == "right_click_element":
            try:
                commands = self.right_click_element(element_path, role_name_list)
                if commands:
                    result = self._execute_commands_on_target(commands)
                    return result
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": f"右键点击元素失败: {str(e)}"}
        if step_type == "double_click_element":
            try:
                commands = self.double_click_element(element_path, role_name_list)
                if commands:
                    result = self._execute_commands_on_target(commands)
                    return result
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": f"双击元素失败: {str(e)}"}
        if step_type == "move_to_element_center":
            res = self.move_to_element_center(element_path, role_name_list)
            return res if isinstance(res, dict) else {"success": True}
        if step_type == "input_text":
            text = step.get("text", "")
            try:
                commands = self.input_text(element_path, text, role_name_list)
                if commands:
                    result = self._execute_commands_on_target(commands)
                    return result
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": f"输入文本失败: {str(e)}"}
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
        if step_type == "assert":
            return self.validate_result(step)
        # 未知类型：忽略或失败，这里选择失败以便提示
        return {"success": False, "error": f"不支持的步骤类型: {step_type}"}

    # ==================== Python脚本执行 ====================

    def run_python_script(self, script_content: str, target_machine_id: str = None, target_app_name: str = None) -> Dict[str, Any]:
        """
        执行Python脚本内容（解析为JSON后执行）
        
        :param script_content: Python脚本内容字符串
        :param target_machine_id: 目标机器ID（可选，如果脚本中未设置则使用此参数）
        :param target_app_name: 目标应用名称（可选，如果脚本中未设置则使用此参数）
        :return: 执行结果字典
        """
        try:
            self.logger.info("开始解析Python脚本")
            
            # 解析Python脚本为JSON格式
            json_script = self._parse_python_script(script_content, target_machine_id, target_app_name)
            
            if not json_script.get("success"):
                return json_script
            
            script_data = json_script["data"]
            self.logger.info(f"Python脚本解析成功，目标: {script_data['target_machine_ip']}/{script_data['target_app_name']}")
            
            # 将机器IP转换为机器ID（这里需要根据实际系统调整）
            machine_id = self._get_machine_id_by_ip(script_data["target_machine_ip"])
            if not machine_id:
                return {"success": False, "error": f"未找到IP为 {script_data['target_machine_ip']} 的机器"}
            
            # 执行解析后的JSON脚本
            return self.run_script(script_data)
            
        except Exception as e:
            error_msg = f"执行Python脚本时发生异常: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def _parse_python_script(self, script_content: str, default_machine_id: str = None, default_app_name: str = None) -> Dict[str, Any]:
        """
        使用 AST 静态解析 Python 脚本，将 OpRecord 操作转换为 JSON 结构（不运行脚本）。
        """
        try:
            import ast

            class OpRecordAstVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.steps: List[Dict[str, Any]] = []
                    self.step_counter: int = 0
                    self.target_machine_ip: Optional[str] = None
                    self.target_app_name: Optional[str] = None

                def _next_id(self) -> str:
                    self.step_counter += 1
                    return str(self.step_counter)

                def _lit(self, node: ast.AST) -> Any:
                    if isinstance(node, ast.Constant):
                        return node.value
                    if isinstance(node, ast.Str):
                        return node.s
                    if isinstance(node, ast.Num):
                        return node.n
                    if isinstance(node, ast.List):
                        return [self._lit(e) for e in node.elts]
                    if isinstance(node, ast.Tuple):
                        return [self._lit(e) for e in node.elts]
                    if isinstance(node, ast.Dict):
                        return {self._lit(k): self._lit(v) for k, v in zip(node.keys, node.values)}
                    if isinstance(node, ast.NameConstant):
                        return node.value
                    return None

                def visit_Call(self, node: ast.Call):
                    try:
                        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'OpRecord':
                            method = node.func.attr
                            args_vals = [self._lit(a) for a in node.args]
                            kwargs = {kw.arg: self._lit(kw.value) for kw in node.keywords if kw.arg}

                            if method == 'setMachine':
                                ip = args_vals[0] if len(args_vals) > 0 else kwargs.get('machine_ip')
                                app = args_vals[1] if len(args_vals) > 1 else kwargs.get('app_name')
                                if isinstance(ip, str):
                                    self.target_machine_ip = ip
                                if isinstance(app, str):
                                    self.target_app_name = app
                                return

                            step: Dict[str, Any] = {"id": self._next_id()}

                            if method == 'click_element':
                                step.update({"type": "click_element", "element_path": (args_vals[0] if len(args_vals) > 0 else kwargs.get('element_path')), "role_name_list": (args_vals[1] if len(args_vals) > 1 else kwargs.get('role_name_list')) or []})
                            elif method == 'right_click_element':
                                step.update({"type": "right_click_element", "element_path": (args_vals[0] if len(args_vals) > 0 else kwargs.get('element_path')), "role_name_list": (args_vals[1] if len(args_vals) > 1 else kwargs.get('role_name_list')) or []})
                            elif method == 'double_click_element':
                                step.update({"type": "double_click_element", "element_path": (args_vals[0] if len(args_vals) > 0 else kwargs.get('element_path')), "role_name_list": (args_vals[1] if len(args_vals) > 1 else kwargs.get('role_name_list')) or []})
                            elif method == 'move_to_element_center':
                                step.update({"type": "move_to_element_center", "element_path": (args_vals[0] if len(args_vals) > 0 else kwargs.get('element_path')), "role_name_list": (args_vals[1] if len(args_vals) > 1 else kwargs.get('role_name_list')) or []})
                            elif method == 'move_to':
                                step.update({"type": "move_to", "x": (args_vals[0] if len(args_vals) > 0 else kwargs.get('x')), "y": (args_vals[1] if len(args_vals) > 1 else kwargs.get('y'))})
                            elif method == 'drag_and_drop':
                                step.update({"type": "drag_and_drop", "start_element": (args_vals[0] if len(args_vals) > 0 else kwargs.get('start_element')), "end_element": (args_vals[1] if len(args_vals) > 1 else kwargs.get('end_element')), "role_name_list": (args_vals[2] if len(args_vals) > 2 else kwargs.get('role_name_list')) or []})
                            elif method == 'input_text':
                                if len(args_vals) >= 2:
                                    element_path = args_vals[0]
                                    text = args_vals[1]
                                elif len(args_vals) == 1:
                                    element_path = None
                                    text = args_vals[0]
                                else:
                                    element_path = kwargs.get('element_path')
                                    text = kwargs.get('text')
                                step.update({"type": "input_text", "element_path": element_path, "text": text, "role_name_list": kwargs.get('role_name_list')})
                            elif method == 'set_element_text':
                                step.update({"type": "input_text", "element_path": (args_vals[0] if len(args_vals) > 0 else kwargs.get('element_path')), "text": (args_vals[1] if len(args_vals) > 1 else kwargs.get('text')), "role_name_list": (args_vals[2] if len(args_vals) > 2 else kwargs.get('role_name_list')) or []})
                            elif method == 'hotkey':
                                step.update({"type": "hotkey", "keys": (args_vals[0] if len(args_vals) > 0 else kwargs.get('keys')) or []})
                            elif method == 'key_press':
                                step.update({"type": "key_press", "key": (args_vals[0] if len(args_vals) > 0 else kwargs.get('key'))})
                            elif method == 'key_release':
                                step.update({"type": "key_release", "key": (args_vals[0] if len(args_vals) > 0 else kwargs.get('key'))})
                            elif method == 'wait_for_element':
                                step.update({"type": "wait_element", "element_path": (args_vals[0] if len(args_vals) > 0 else kwargs.get('element_path')), "timeout": (args_vals[1] if len(args_vals) > 1 else kwargs.get('timeout', 30)), "role_name_list": (args_vals[2] if len(args_vals) > 2 else kwargs.get('role_name_list')) or []})
                            elif method == 'wait_for_image':
                                step.update({"type": "wait_image", "image_path": (args_vals[0] if len(args_vals) > 0 else kwargs.get('image_path')), "threshold": (args_vals[1] if len(args_vals) > 1 else kwargs.get('threshold', 0.8)), "timeout": (args_vals[2] if len(args_vals) > 2 else kwargs.get('timeout', 30)), "region": (args_vals[3] if len(args_vals) > 3 else kwargs.get('region'))})
                            elif method == 'click_image':
                                step.update({"type": "click_image", "image_path": (args_vals[0] if len(args_vals) > 0 else kwargs.get('image_path')), "threshold": (args_vals[1] if len(args_vals) > 1 else kwargs.get('threshold', 0.8)), "region": (args_vals[2] if len(args_vals) > 2 else kwargs.get('region'))})
                            elif method == 'find_image':
                                step.update({"type": "find_image", "image_path": (args_vals[0] if len(args_vals) > 0 else kwargs.get('image_path')), "threshold": (args_vals[1] if len(args_vals) > 1 else kwargs.get('threshold', 0.8)), "region": (args_vals[2] if len(args_vals) > 2 else kwargs.get('region'))})
                            elif method == 'get_screenshot':
                                step.update({"type": "get_screenshot", "region": (args_vals[0] if len(args_vals) > 0 else kwargs.get('region'))})
                            else:
                                return

                            if 'type' in step:
                                self.steps.append(step)
                    finally:
                        self.generic_visit(node)

            tree = ast.parse(script_content)
            visitor = OpRecordAstVisitor()
            visitor.visit(tree)

            json_script: Dict[str, Any] = {"steps": visitor.steps}

            if visitor.target_machine_ip:
                json_script['target_machine_ip'] = visitor.target_machine_ip
            if visitor.target_app_name:
                json_script['target_app_name'] = visitor.target_app_name

            if 'target_machine_ip' not in json_script or 'target_app_name' not in json_script:
                if default_machine_id and default_app_name:
                    json_script['target_machine_ip'] = self._get_machine_ip_by_id(default_machine_id)
                    json_script['target_app_name'] = default_app_name
                else:
                    return {"success": False, "error": "Python脚本中未设置目标机器和应用，且未提供默认值", "need_target_info": True}

            return {"success": True, "data": json_script}

        except SyntaxError as e:
            return {"success": False, "error": f"Python语法错误: {e}"}
        except Exception as e:
            return {"success": False, "error": f"解析Python脚本时发生异常: {str(e)}"}

    def _get_machine_id_by_ip(self, machine_ip: str) -> Optional[str]:
        """
        根据IP地址获取机器ID
        
        :param machine_ip: 机器IP地址
        :return: 机器ID或None
        """
        try:
            for machine_id, machine_info in self.communicator.machines.items():
                if isinstance(machine_info.get("address"), list) and len(machine_info["address"]) >= 1:
                    if machine_info["address"][0] == machine_ip:
                        return machine_id
                elif isinstance(machine_info.get("address"), str):
                    if machine_info["address"] == machine_ip:
                        return machine_id
            return None
        except Exception as e:
            self.logger.error(f"根据IP获取机器ID失败: {str(e)}")
            return None

    def _get_machine_ip_by_id(self, machine_id: str) -> Optional[str]:
        """
        根据机器ID获取IP地址
        
        :param machine_id: 机器ID
        :return: IP地址或None
        """
        try:
            machine_info = self.communicator.machines.get(machine_id)
            if machine_info:
                address = machine_info.get("address")
                if isinstance(address, list) and len(address) >= 1:
                    return address[0]
                elif isinstance(address, str):
                    return address
            return None
        except Exception as e:
            self.logger.error(f"根据机器ID获取IP失败: {str(e)}")
            return None

    def run_python_script_from_file(self, file_path: str, target_machine_id: str = None, target_app_name: str = None) -> Dict[str, Any]:
        """
        从文件读取Python脚本并执行
        
        :param file_path: Python脚本文件路径
        :param target_machine_id: 目标机器ID（可选）
        :param target_app_name: 目标应用名称（可选）
        :return: 执行结果字典
        """
        try:
            # 读取Python脚本文件
            with open(file_path, "r", encoding="utf-8") as f:
                script_content = f.read()
            
            self.logger.info(f"从文件读取Python脚本: {file_path}")
            return self.run_python_script(script_content, target_machine_id, target_app_name)
            
        except FileNotFoundError:
            error_msg = f"Python脚本文件不存在: {file_path}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"读取Python脚本文件失败: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def validate_python_script(self, script_content: str) -> Dict[str, Any]:
        """
        验证Python脚本语法（占位实现）
        
        :param script_content: Python脚本内容
        :return: 验证结果字典
        """
        try:
            # 这里应该实现Python语法检查
            # 可以使用ast模块进行语法验证
            import ast
            
            # 尝试解析Python代码
            ast.parse(script_content)
            
            return {
                "success": True,
                "message": "Python脚本语法正确"
            }
            
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Python语法错误: {str(e)}",
                "line": e.lineno,
                "column": e.offset
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"验证Python脚本时发生异常: {str(e)}"
            }

    def get_python_script_info(self, script_content: str) -> Dict[str, Any]:
        """
        获取Python脚本信息（占位实现）
        
        :param script_content: Python脚本内容
        :return: 脚本信息字典
        """
        try:
            lines = script_content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            return {
                "success": True,
                "data": {
                    "total_lines": len(lines),
                    "non_empty_lines": len(non_empty_lines),
                    "characters": len(script_content),
                    "estimated_complexity": "low" if len(non_empty_lines) < 50 else "medium" if len(non_empty_lines) < 200 else "high"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"分析Python脚本信息时发生异常: {str(e)}"
            }

