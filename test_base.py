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
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        # 获取QGIS应用实例
        self.qgis = root.application('QGIS3')
        self.dialog_app = root.application('qgis')
        self.logger.info("QGIS应用已启动")
        self.menubar = self.qgis.child(roleName='menu bar')
        
        # 等待主界面加载完成
        time.sleep(5)
    
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

    def click_element(self, element, roleName=None):
        """
        点击元素
        :param element: 元素
        :param roleName: 元素角色名（可选）
        :return: 操作成功返回True，失败返回False
        """
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
        element.contextClick()
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
                return True
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
                pyautogui.click(x, y)
                self.logger.info(f"图像识别点击: {image_path}")
                time.sleep(0.5)
                return True
            time.sleep(0.5)
        
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
                pyautogui.doubleClick(x, y)
                self.logger.info(f"图像识别双击: {image_path}")
                time.sleep(0.5)
                return True
            time.sleep(0.5)
        
        self.logger.warning(f"图像识别双击失败: {image_path}")
        return False
    
    def input_text(self, text, element):
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
        rect = self.qgis.getBounds()
        center_x = rect.x + rect.width // 2
        center_y = rect.y + rect.height // 2
        pyautogui.moveTo(center_x, center_y)
        self.logger.info(f"鼠标移动到窗口中心: ({center_x}, {center_y})")
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