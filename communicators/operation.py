import json
import time
import logging
from typing import Dict, List, Optional
from test_communicator import TestMachineCommunicator

class Operation:
    """
    封装Dogtail交互操作，生成JSON格式的.opts
    每个操作返回对应的指令拆解为基本鼠标点击和移动，参数使用元素位置信息
    """
    
    def __init__(self, test_machine_ip: str, test_machine_port: int = 8888):
        """
        初始化操作类并建立与被测试机器的通信连接
        :param test_machine_ip: 被测试机器的IP地址
        :param test_machine_port: 被测试机器的通信端口
        """
        self.opts = []  # 存储单个操作的指令序列
        self.commands_list = []  # 存储整个测试文件生成的指令列表
        # 初始化通信类，建立连接
        self.communicator = TestMachineCommunicator(test_machine_ip, test_machine_port)
        # self.communicator._connect()

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)


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


    def get_location(self, element_path: str, role_name_list: Optional[List[str]] = None) -> Dict[str, any]:
        """
        通过通信类调用被测试机器的get_element接口，获取元素位置信息
        :param element_path: 元素路径，格式"父元素1/父元素2/目标元素"
        :param role_name_list: 元素角色名列表（可选），支持多个角色名匹配
        :return: 元素位置信息字典，包含{x,y,width,height,center_x,center_y}
        """
        # 调用通信类的get_element_info方法获取元素信息
        response = self.communicator.get_element_info(
            element_path=element_path,
            role_name_list=role_name_list  # 改为传递角色名列表
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
        param element_path: 元素路径
        param role_name_list: 元素角色名列表（可选），支持多个角色名匹配
        """
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
        self.finish_current_opts(commands)  # 完成当前操作指令集的执行


    def right_click_element(self, element_path: str, role_name_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成右键点击元素的指令（移动到中心位置后右键点击）
        param element_path: 元素路径
        param role_name_list: 元素角色名列表（可选），支持多个角色名匹配
        """
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
        self.finish_current_opts(commands)  # 完成当前操作指令集的执行


    def set_element_text(self, element_path: str, text: str, role_name_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成设置元素文本的指令（点击激活→全选→删除→输入）
        param element_path: 元素路径
        param text: 要设置的文本内容
        param role_name_list: 元素角色名列表（可选），支持多个角色名匹配
        """
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
        self.finish_current_opts(commands)  # 完成当前操作指令集的执行


    def select_combo_item(self, combo_path: str, item_text: str, role_name_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成下拉框选择的指令（点击下拉框→点击选项）
        param combo_path: 下拉框元素路径
        param item_text: 要选择的选项文本
        param role_name_list: 下拉框元素角色名列表（可选）
        """
        commands = []
        # 点击下拉框
        combo_loc = self.get_location(combo_path, role_name_list)
        commands.append(self._generate_command(
            "mouse_move",
            {"x": combo_loc["center_x"], "y": combo_loc["center_y"]}
        ))
        commands.append(self._generate_command(
            "mouse_click",
            {"x": combo_loc["center_x"], "y": combo_loc["center_y"], "button": "left"}
        ))
        
        # 点击选项（指定选项角色为"menu item"）
        item_loc = self.get_location(f"{combo_path}/{item_text}", ["menu item"])
        commands.append(self._generate_command(
            "mouse_move",
            {"x": item_loc["center_x"], "y": item_loc["center_y"]}
        ))
        commands.append(self._generate_command(
            "mouse_click",
            {"x": item_loc["center_x"], "y": item_loc["center_y"], "button": "left"}
        ))
        self.finish_current_opts(commands)  # 完成当前操作指令集的执行


    def input_text(self, element_path: Optional[str], text: str, role_name_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成输入文本的指令（若有元素则先点击激活）
        param element_path: 元素路径（可选）
        param text: 要输入的文本内容
        param role_name_list: 元素角色名列表（可选），支持多个角色名匹配
        """
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
        self.finish_current_opts(commands)  # 完成当前操作指令集的执行


    def drag_to(self, start_x: int, start_y: int, end_x: int, end_y: int) -> List[Dict]:
        """
        生成拖拽操作的指令（绝对坐标）
        :param start_x: 起点X坐标
        :param start_y: 起点Y坐标
        :param end_x: 终点X坐标
        :param end_y: 终点Y坐标
        """
        print(f"拖拽从({start_x}, {start_y})到({end_x}, {end_y})")
        # 生成拖拽指令
        commands = [
            # 移动到起点
            self._generate_command("mouse_move", {"x": start_x, "y": start_y}),
            # 按下左键
            self._generate_command("mouse_press", {"x": start_x, "y": start_y, "button": "left"}),
            # 移动到终点
            self._generate_command("mouse_move", {"x": end_x, "y": end_y}),
            # 释放左键
            self._generate_command("mouse_release", {"x": end_x, "y": end_y, "button": "left"})
        ]
        self.finish_current_opts(commands)  # 完成当前操作指令集的执行


    def drag_to_percentage(self, app_name: str, start_x_pct: float, start_y_pct: float, 
                           end_x_pct: float, end_y_pct: float) -> List[Dict]:
        """
        生成按百分比拖拽地图的指令（基于屏幕尺寸计算）
        :param start_x_pct: 起点X坐标百分比（0-1）
        :param start_y_pct: 起点Y坐标百分比（0-1）
        :param end_x_pct: 终点X坐标百分比（0-1）
        :param end_y_pct: 终点Y坐标百分比（0-1)
        """
        # 获取屏幕尺寸（指定屏幕角色为["screen"]）
        screen_loc = self.get_location(app_name, ["application"])
        screen_width = screen_loc["width"]
        screen_height = screen_loc["height"]
        
        # 计算坐标
        start_x = int(screen_width * start_x_pct)
        start_y = int(screen_height * start_y_pct)
        end_x = int(screen_width * end_x_pct)
        end_y = int(screen_height * end_y_pct)
        
        return self.drag_to(start_x, start_y, end_x, end_y)


    def drag_item_to_parent(self, item_path: str, parent_path: str, 
                           item_role_list: Optional[List[str]] = None,
                           parent_role_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成拖拽元素到父元素的指令
        :param item_path: 要拖拽的元素路径
        :param parent_path: 父元素路径
        :param item_role_list: 拖拽元素的角色名列表（可选）
        :param parent_role_list: 父元素的角色名列表（可选）
        """
        item_loc = self.get_location(item_path, item_role_list)
        parent_loc = self.get_location(parent_path, parent_role_list)
        
        return self.drag_to(
            start_x=item_loc["center_x"],
            start_y=item_loc["center_y"],
            end_x=parent_loc["center_x"],
            end_y=parent_loc["center_y"]
        )


    def drag_item_to_cousin(self, item_path: str, cousin_path: str,
                           item_role_list: Optional[List[str]] = None,
                           cousin_role_list: Optional[List[str]] = None) -> List[Dict]:
        """
        生成拖拽元素到兄弟元素的指令
        :param item_path: 要拖拽的元素路径
        :param cousin_path: 兄弟元素路径
        :param item_role_list: 拖拽元素的角色名列表（可选）
        :param cousin_role_list: 兄弟元素的角色名列表（可选）
        """
        item_loc = self.get_location(item_path, item_role_list)
        cousin_loc = self.get_location(cousin_path, cousin_role_list)
        
        return self.drag_to(
            start_x=item_loc["center_x"],
            start_y=item_loc["center_y"],
            end_x=cousin_loc["center_x"],
            end_y=cousin_loc["center_y"]
        )


    def hotkey(self, keys: List[str]) -> Dict:
        """
        生成组合键操作的指令
        :param keys: 组合键列表，如["Ctrl", "c"]
        """
        commands = [ self._generate_command("hotkey", {"keys": keys}) ]
        self.finish_current_opts(commands)  # 完成当前操作指令集的执行


    def scroll(self, clicks: int) -> Dict:
        """
        生成鼠标滚动的指令
        :param clicks: 滚动次数（正数向上滚动，负数向下滚动）
        """
        commands = [ self._generate_command("mouse_scroll", {"clicks": clicks}) ]
        self.finish_current_opts(commands)  # 完成当前操作指令集的执行
    

    def move_to(self, x: int, y: int) -> Dict:
        """
        生成鼠标移动到指定位置的指令
        :param x: X坐标
        :param y: Y坐标
        """
        commands = [ self._generate_command("mouse_move", {"x": x, "y": y}) ]
        self.finish_current_opts(commands)


    def move_to_element_center(self, element_path: str, role_name_list: Optional[List[str]] = None) -> Dict:
        """
        生成鼠标移动到元素中心的指令
        :param element_path: 元素路径
        :param role_name_list: 元素角色名列表（可选），支持多个角色名匹配
        """
        loc = self.get_location(element_path, role_name_list)
        return self.move_to(loc["center_x"], loc["center_y"])


    def export_to_json(self, file_path: str) -> None:
        """
        将.commands_list导出为JSON文件
        :param file_path: 导出JSON文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.commands_list, f, ensure_ascii=False, indent=2)


    def finish_current_opts(self, commands) -> None:
        """
        结束当前操作指令集
        :param commands: 当前操作指令列表
        """
        self.commands_list.append(commands)
        self.opts = commands  # 更新当前操作指令集
        self.logger.info(f"当前操作要执行的指令集，共{len(commands)}条指令") 
        result = self.execute_commands()  # 执行指令
        self.logger.info(f"执行指令集结果: {result}")

        
    def execute_commands(self) -> Dict[str, any]:
        """
        通过通信类执行当前指令集中的所有指令
        :return: 执行结果字典
        """
        if not self.opts:
            return {"success": False, "error": "没有可执行的指令"}
        
        # 调用通信类执行指令集
        result = self.communicator.execute_commands(self.opts)
        # 执行完成后清空指令集
        self.opts = []
        return result
    

    def close(self) -> None:
        """关闭与被测试机器的通信连接"""
        self.communicator.close()