import os
import time
import unittest
import logging
import pyautogui
from dogtail.tree import root

class QGISDogtailTest(unittest.TestCase):
    """QGIS自动化测试基类，封装常用操作"""
    
    def setUp(self):
        # 初始化日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        # 获取QGIS应用实例
        self.qgis = root.application('QGIS3')
        # self.dialog_app = root.application('qgis')
        self.logger.info("QGIS应用已启动")
        self.menubar = self.qgis.child(roleName='menu bar')
        
        # 等待主界面加载完成
        time.sleep(3)
    
    def tearDown(self):
        self.logger.info("测试完成")
    
    def find_element(self, path, roleName=None, recursive=True):
        """
        通过路径查找元素
        :param path: 元素路径，格式为"父元素1/父元素2/目标元素"
        :param roleName: 元素角色名（可选）
        :param recursive: 是否递归查找（默认True）
        :return: 找到的元素或None
        """
        elements = path.split("/")
        current = self.qgis
        
        for element_name in elements:
            try:
                if recursive:
                    current = current.child(name=element_name, roleName=roleName, recursive=True)
                else:
                    current = current.child(name=element_name, roleName=roleName, recursive=False)
                self.logger.debug(f"找到元素: {element_name}")
            except LookupError:
                self.logger.error(f"未找到元素: {element_name}")
                return None
        
        return current
    
    def click(self):
        pyautogui.click()

    def move_to_element(self, element):
        """
        将鼠标移动到指定元素
        :param element: 元素对象
        :return: None
        """
        x, y = element.position
        pyautogui.moveTo(x, y)
        self.logger.info(f"鼠标移动到元素: {element.name} ({element.x}, {element.y})")
        time.sleep(0.5)

    def click_element(self, element, roleName=None):
        """
        点击元素
        :param element: 元素
        :param roleName: 元素角色名（可选）
        :return: 操作成功返回True，失败返回False
        """
        # self.move_to_element(element)
        element.click()
        self.logger.info(f"点击元素: {element.name}")
        time.sleep(0.5)
        return True
    
    def right_click_element(self, element, roleName=None):
        """
        右键点击元素
        :param element: 元素
        :param roleName: 元素角色名（可选）
        :return: 操作成功返回True，失败返回False
        """
        element.click(button=3)
        self.logger.info(f"右键点击元素: {element.name}")
        time.sleep(0.5)
        return True
    
    def set_text(self, element, text, roleName=None):
        """
        设置元素文本
        :param element: 元素
        :param text: 要设置的文本
        :param roleName: 元素角色名（可选）
        :return: 操作成功返回True，失败返回False
        """
        element.text = text
        self.logger.info(f"设置文本: {text} 到 {element.name}")
        time.sleep(0.5)
        return True
    
    def select_combo_item(self, combo, item_text, roleName=None):
        """
        下拉框选择
        :param combo: 下拉框元素
        :param item_text: 下拉框选项文本
        :param roleName: 元素角色名（可选）
        :return: 操作成功返回True，失败返回False
        """
        combo.click()
        item = combo.child(name=item_text, roleName='menu item')
        if item:
            item.click()
            self.logger.info(f"选择下拉框选项: {item_text}")
            time.sleep(0.5)
            return True
    
    def wait_for_element(self, path, roleName=None, timeout=10):
        """
        等待元素出现
        :param path: 元素路径
        :param roleName: 元素角色名（可选）
        :param timeout: 超时时间（秒）
        :return: 找到元素返回True，超时返回False
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            element = self.find_element(path, roleName)
            if element:
                return element
            time.sleep(1)
        return False
    
    # 备用的pyautogui图像识别方法
    def click_image(self, image_path, confidence=0.7, timeout=5):
        """
        使用pyautogui识别并点击图像
        :param image_path: 图像路径
        :param confidence: 识别置信度
        :param timeout: 超时时间（秒）
        :return: 点击成功返回True，失败返回False
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            pos = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if pos:
                x, y = pyautogui.center(pos)
                pyautogui.moveTo(x, y)
                pyautogui.click(x, y)
                self.logger.info(f"图像识别点击: {image_path}")
                time.sleep(0.5)
                return True
            time.sleep(0.5)
        
        if image_path == 'qgis_image/cleanInput.png':
            self.logger.info('现在不需要清空输入框')
            return True
        self.logger.warning(f"图像识别失败: {image_path}")
        return False
    
    def double_click_image(self, image_path, confidence=0.7, timeout=5):
        """
        使用pyautogui识别并双击图像
        :param image_path: 图像路径
        :param confidence: 识别置信度
        :param timeout: 超时时间（秒）
        :return: 双击成功返回True，失败返回False
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            pos = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if pos:
                x, y = pyautogui.center(pos)
                pyautogui.moveTo(x, y)
                pyautogui.doubleClick(x, y)
                self.logger.info(f"图像识别双击: {image_path}")
                time.sleep(0.5)
                return True
            time.sleep(0.5)
        
        self.logger.warning(f"图像识别双击失败: {image_path}")
        return False
    
    def input_text(self, text, element=None):
        """
        输入文本到元素
        :param element: 输入框元素
        :param text: 要输入的文本
        :return: 操作成功返回True，失败返回False
        """
        if element:
            element.click()
            pyautogui.typewrite(text)
            self.logger.info(f"输入文本: {text} 到 {element.name}")
        else:
            pyautogui.typewrite(text)
        time.sleep(0.5)
        return True
    
    def move_to_window_center(self):
        """
        将鼠标移动到QGIS窗口中心
        :return: None
        """
        rect = self.qgis.child(roleName="frame")
        x, y = rect.position
        width, height = rect.size
        center_x = x + width // 2
        center_y = y + height // 2
        pyautogui.moveTo(center_x, center_y)
        self.logger.info(f"鼠标移动到窗口中心: ({center_x}, {center_y})")
        time.sleep(0.5)

    def move_to_element_center(self, element):
        """
        将鼠标移动到指定元素中心
        :param element: 元素对象
        :return: None
        """
        x, y = element.position
        width, height = element.size
        center_x = x + width // 2
        center_y = y + height // 2
        pyautogui.moveTo(center_x, center_y)
        self.logger.info(f"鼠标移动到元素中心: ({center_x}, {center_y})")
        time.sleep(0.5)

    def hotkey(self, *keys):
        """组合键操作，例如 Ctrl+C"""
        pyautogui.hotkey(*keys)
        self.logger.info(f"按下组合键: {' + '.join(keys)}")
        time.sleep(0.5)

    def scroll(self, clicks):
        """
        滚动鼠标
        :param clicks: 滚动次数，正数向上滚动，负数向下滚动
        :return: None
        """
        pyautogui.scroll(clicks)
        self.logger.info(f"鼠标滚动: {clicks} 次")
        time.sleep(0.5)

    def trans_tuple_to_loc(self, tup):
        return {
            'x': tup[0],
            'y': tup[1]
        }

    def drag_to(self, start_x, start_y, end_x, end_y):
        """
        拖动地图
        :param start_x: 起始点X坐标
        :param start_y: 起始点Y坐标
        :param end_x: 结束点X坐标
        :param end_y: 结束点Y坐标
        :return: None
        """
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=0.5)
        self.logger.info(f"从 ({start_x}, {start_y}) 拖动到 ({end_x}, {end_y})")
        time.sleep(0.5)

    def drag_map_percentage(self, start_x_pct, start_y_pct, end_x_pct, end_y_pct):
        """
        按百分比拖动地图
        :param start_x_pct: 起始点X坐标百分比（0-1）
        :param start_y_pct: 起始点Y坐标百分比（0-1）
        :param end_x_pct: 结束点X坐标百分比（0-1）
        :param end_y_pct: 结束点Y坐标百分比（0-1）
        :return: None
        """
        rect = self.qgis.child(roleName="frame")
        x, y = rect.position
        width, height = rect.size
        start_x = x + int(width * start_x_pct)
        start_y = y + int(height * start_y_pct)
        end_x = x + int(width * end_x_pct)
        end_y = y + int(height * end_y_pct)
        
        self.drag_to(start_x, start_y, end_x, end_y)

    def drag_item_to_parent(self, item, parent):
        """
        拖动元素到其父元素
        :param item: 要拖动的元素
        :param parent: 父元素
        :return: None
        """
        item_x, item_y = item.position
        parent_x, parent_y = parent.position
        parent_width, parent_height = parent.size
        
        # 计算拖动结束位置为父元素中心
        end_x = parent_x + parent_width // 2
        end_y = parent_y + parent_height // 2
        
        self.drag_to(item_x, item_y, end_x, end_y)
        self.logger.info(f"将 {item.name} 拖动到 {parent.name} 中心")

    def drag_item_to_cousin(self, item, cousin):
        """
        拖动元素到其兄弟元素
        :param item: 要拖动的元素
        :param cousin: 兄弟元素
        :return: None
        """
        item_x, item_y = item.position
        cousin_x, cousin_y = cousin.position
        
        # 计算拖动结束位置为兄弟元素下方
        end_x = cousin_x + cousin.size[0] // 2
        end_y = cousin_y + cousin.size[1]
        
        self.drag_to(item_x, item_y, end_x, end_y)
        self.logger.info(f"将 {item.name} 拖动到 {cousin.name} 下方")