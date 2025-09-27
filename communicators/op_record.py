#!/usr/bin/env python3
"""
OpRecord类 - 用于辅助Python脚本解析

这个类提供了与operation_multi_machine.py中相同的方法接口，
用于在Python脚本中编写操作指令，并最终转换为JSON格式。

使用方式：
```python
from op_record import OpRecord

# 设置目标机器和应用
OpRecord.setMachine("192.168.1.100", "calculator")

# 执行操作
OpRecord.click_element("按钮1", ["push button"])
OpRecord.input_text("输入框", "测试文本")
OpRecord.hotkey(["Ctrl", "c"])

# 转换为JSON
json_script = OpRecord.transToJson()
```
"""

import json
import time
from typing import Dict, List, Optional, Any, Union


class OpRecord:
    """
    操作记录类，用于在Python脚本中编写操作指令
    """
    
    # 类变量，用于存储操作记录
    _steps = []
    _target_machine_ip = None
    _target_app_name = None
    _current_step_id = 0
    
    @classmethod
    def setMachine(cls, machine_ip: str, app_name: str) -> None:
        """
        设置目标机器IP和应用名称
        
        :param machine_ip: 机器IP地址
        :param app_name: 应用名称
        """
        cls._target_machine_ip = machine_ip
        cls._target_app_name = app_name
        print(f"设置目标机器: {machine_ip}, 应用: {app_name}")
    
    @classmethod
    def _generate_step_id(cls) -> str:
        """生成步骤ID"""
        cls._current_step_id += 1
        return str(cls._current_step_id)
    
    @classmethod
    def _add_step(cls, step_type: str, params: Dict[str, Any], description: str = "") -> None:
        """
        添加操作步骤
        
        :param step_type: 步骤类型
        :param params: 步骤参数
        :param description: 步骤描述
        """
        step = {
            "id": cls._generate_step_id(),
            "type": step_type,
            "description": description,
            **params
        }
        cls._steps.append(step)
        print(f"添加步骤: {step_type} - {description}")
    
    @classmethod
    def clear(cls) -> None:
        """清空所有操作记录"""
        cls._steps = []
        cls._target_machine_ip = None
        cls._target_app_name = None
        cls._current_step_id = 0
        print("已清空操作记录")
    
    # ==================== 元素定位操作 ====================
    
    @classmethod
    def get_location(cls, element_path: str, role_name_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取元素位置信息（模拟方法，实际执行时由operation_multi_machine处理）
        
        :param element_path: 元素路径
        :param role_name_list: 元素角色名列表
        :return: 位置信息字典
        """
        # 这里只是记录操作，实际位置获取在JSON执行时处理
        return {
            "x": 0, "y": 0, "width": 100, "height": 30,
            "center_x": 50, "center_y": 15
        }
    
    # ==================== 鼠标操作 ====================
    
    @classmethod
    def click_element(cls, element_path: str, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
        """
        点击元素
        
        :param element_path: 元素路径
        :param role_name_list: 元素角色名列表
        :param description: 操作描述
        """
        if not description:
            description = f"点击元素: {element_path}"
        
        cls._add_step("click_element", {
            "element_path": element_path,
            "role_name_list": role_name_list or []
        }, description)
    
    @classmethod
    def right_click_element(cls, element_path: str, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
        """
        右键点击元素
        
        :param element_path: 元素路径
        :param role_name_list: 元素角色名列表
        :param description: 操作描述
        """
        if not description:
            description = f"右键点击元素: {element_path}"
        
        cls._add_step("right_click_element", {
            "element_path": element_path,
            "role_name_list": role_name_list or []
        }, description)
    
    @classmethod
    def double_click_element(cls, element_path: str, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
        """
        双击元素
        
        :param element_path: 元素路径
        :param role_name_list: 元素角色名列表
        :param description: 操作描述
        """
        if not description:
            description = f"双击元素: {element_path}"
        
        cls._add_step("double_click_element", {
            "element_path": element_path,
            "role_name_list": role_name_list or []
        }, description)
    
    @classmethod
    def move_to(cls, x: int, y: int, description: str = "") -> None:
        """
        移动鼠标到指定位置
        
        :param x: X坐标
        :param y: Y坐标
        :param description: 操作描述
        """
        if not description:
            description = f"移动鼠标到 ({x}, {y})"
        
        cls._add_step("move_to", {
            "x": x,
            "y": y
        }, description)
    
    @classmethod
    def move_to_element_center(cls, element_path: str, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
        """
        移动鼠标到元素中心
        
        :param element_path: 元素路径
        :param role_name_list: 元素角色名列表
        :param description: 操作描述
        """
        if not description:
            description = f"移动鼠标到元素中心: {element_path}"
        
        cls._add_step("move_to_element_center", {
            "element_path": element_path,
            "role_name_list": role_name_list or []
        }, description)
    
    @classmethod
    def drag_and_drop(cls, start_element: str, end_element: str, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
        """
        拖拽操作
        
        :param start_element: 起始元素路径
        :param end_element: 目标元素路径
        :param role_name_list: 元素角色名列表
        :param description: 操作描述
        """
        if not description:
            description = f"拖拽: {start_element} -> {end_element}"
        
        cls._add_step("drag_and_drop", {
            "start_element": start_element,
            "end_element": end_element,
            "role_name_list": role_name_list or []
        }, description)
    
    # ==================== 键盘操作 ====================
    
    @classmethod
    def input_text(cls, element_path: Optional[str], text: str, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
        """
        输入文本
        
        :param element_path: 元素路径（可选）
        :param text: 要输入的文本
        :param role_name_list: 元素角色名列表
        :param description: 操作描述
        """
        if not description:
            if element_path:
                description = f"在 {element_path} 输入文本: {text}"
            else:
                description = f"输入文本: {text}"
        
        params = {"text": text}
        if element_path:
            params["element_path"] = element_path
        if role_name_list:
            params["role_name_list"] = role_name_list
        
        cls._add_step("input_text", params, description)
    
    @classmethod
    def set_element_text(cls, element_path: str, text: str, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
        """
        设置元素文本
        
        :param element_path: 元素路径
        :param text: 要设置的文本
        :param role_name_list: 元素角色名列表
        :param description: 操作描述
        """
        if not description:
            description = f"设置 {element_path} 文本为: {text}"
        
        cls._add_step("set_element_text", {
            "element_path": element_path,
            "text": text,
            "role_name_list": role_name_list or []
        }, description)
    
    @classmethod
    def hotkey(cls, keys: List[str], description: str = "") -> None:
        """
        组合键操作
        
        :param keys: 按键列表，如["Ctrl", "c"]
        :param description: 操作描述
        """
        if not description:
            description = f"组合键: {'+'.join(keys)}"
        
        cls._add_step("hotkey", {
            "keys": keys
        }, description)
    
    @classmethod
    def key_press(cls, key: str, description: str = "") -> None:
        """
        按键操作
        
        :param key: 按键名称
        :param description: 操作描述
        """
        if not description:
            description = f"按键: {key}"
        
        cls._add_step("key_press", {
            "key": key
        }, description)
    
    @classmethod
    def key_release(cls, key: str, description: str = "") -> None:
        """
        按键释放
        
        :param key: 按键名称
        :param description: 操作描述
        """
        if not description:
            description = f"释放按键: {key}"
        
        cls._add_step("key_release", {
            "key": key
        }, description)
    
    # ==================== 等待和验证操作 ====================
    
    @classmethod
    def wait_for_element(cls, element_path: str, timeout: int = 30, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
        """
        等待元素出现
        
        :param element_path: 元素路径
        :param timeout: 超时时间（秒）
        :param role_name_list: 元素角色名列表
        :param description: 操作描述
        """
        if not description:
            description = f"等待元素出现: {element_path} (超时: {timeout}s)"
        
        cls._add_step("wait_element", {
            "element_path": element_path,
            "timeout": timeout,
            "role_name_list": role_name_list or []
        }, description)
    
    @classmethod
    def wait_for_image(cls, image_path: str, threshold: float = 0.8, timeout: int = 30, region: Optional[List[int]] = None, description: str = "") -> None:
        """
        等待图片出现
        
        :param image_path: 图片路径
        :param threshold: 匹配阈值
        :param timeout: 超时时间（秒）
        :param region: 查找区域
        :param description: 操作描述
        """
        if not description:
            description = f"等待图片出现: {image_path} (超时: {timeout}s)"
        
        params = {
            "image_path": image_path,
            "threshold": threshold,
            "timeout": timeout
        }
        if region:
            params["region"] = region
        
        cls._add_step("wait_image", params, description)
    
    # ==================== 图像识别操作 ====================
    
    @classmethod
    def click_image(cls, image_path: str, threshold: float = 0.8, region: Optional[List[int]] = None, description: str = "") -> None:
        """
        点击图片
        
        :param image_path: 图片路径
        :param threshold: 匹配阈值
        :param region: 查找区域
        :param description: 操作描述
        """
        if not description:
            description = f"点击图片: {image_path}"
        
        params = {
            "image_path": image_path,
            "threshold": threshold
        }
        if region:
            params["region"] = region
        
        cls._add_step("click_image", params, description)
    
    @classmethod
    def find_image(cls, image_path: str, threshold: float = 0.8, region: Optional[List[int]] = None, description: str = "") -> None:
        """
        查找图片
        
        :param image_path: 图片路径
        :param threshold: 匹配阈值
        :param region: 查找区域
        :param description: 操作描述
        """
        if not description:
            description = f"查找图片: {image_path}"
        
        params = {
            "image_path": image_path,
            "threshold": threshold
        }
        if region:
            params["region"] = region
        
        cls._add_step("find_image", params, description)
    
    # ==================== 截图操作 ====================
    
    @classmethod
    def get_screenshot(cls, region: Optional[List[int]] = None, description: str = "") -> None:
        """
        获取截图
        
        :param region: 截图区域
        :param description: 操作描述
        """
        if not description:
            description = "获取截图"
        
        params = {}
        if region:
            params["region"] = region
        
        cls._add_step("get_screenshot", params, description)
    
    # ==================== 转换方法 ====================
    
    @classmethod
    def transToJson(cls) -> Dict[str, Any]:
        """
        将操作记录转换为JSON格式
        
        :return: JSON格式的脚本对象
        """
        if not cls._target_machine_ip or not cls._target_app_name:
            raise ValueError("请先使用 setMachine() 设置目标机器和应用")
        
        if not cls._steps:
            raise ValueError("没有操作步骤，请先添加操作")
        
        json_script = {
            "target_machine_ip": cls._target_machine_ip,
            "target_app_name": cls._target_app_name,
            "steps": cls._steps.copy()
        }
        
        return json_script

    # ==================== 验证操作 ====================

    @classmethod
    def validate_result(cls, element_path: str, expect_value: Any, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
        """
        添加断言步骤，转换为 JSON:
        { id, type: "assert", element_path, role_name_list, expect_value }

        :param element_path: 要检验的元素路径
        :param expect_value: 期望值
        :param role_name_list: 角色名列表（可选）
        :param description: 描述（可选）
        """
        if not description:
            description = f"校验元素 {element_path} 值为: {expect_value}"

        params = {
            "element_path": element_path,
            "expect_value": expect_value
        }
        if role_name_list:
            params["role_name_list"] = role_name_list

        cls._add_step("assert", params, description)
    
    @classmethod
    def getStepsCount(cls) -> int:
        """获取操作步骤数量"""
        return len(cls._steps)
    
    @classmethod
    def getSteps(cls) -> List[Dict[str, Any]]:
        """获取操作步骤列表"""
        return cls._steps.copy()
    
    @classmethod
    def getTargetInfo(cls) -> Dict[str, str]:
        """获取目标信息"""
        return {
            "machine_ip": cls._target_machine_ip,
            "app_name": cls._target_app_name
        }


# 为了兼容性，也可以直接使用类名作为实例
def setMachine(machine_ip: str, app_name: str) -> None:
    """设置目标机器和应用（函数形式）"""
    OpRecord.setMachine(machine_ip, app_name)

def click_element(element_path: str, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
    """点击元素（函数形式）"""
    OpRecord.click_element(element_path, role_name_list, description)

def input_text(element_path: Optional[str], text: str, role_name_list: Optional[List[str]] = None, description: str = "") -> None:
    """输入文本（函数形式）"""
    OpRecord.input_text(element_path, text, role_name_list, description)

def hotkey(keys: List[str], description: str = "") -> None:
    """组合键操作（函数形式）"""
    OpRecord.hotkey(keys, description)

def transToJson() -> Dict[str, Any]:
    """转换为JSON（函数形式）"""
    return OpRecord.transToJson()

def clear() -> None:
    """清空操作记录（函数形式）"""
    OpRecord.clear()
