from test_base import QGISDogtailTest
import unittest
import time


class TestQGISMeasureTool(QGISDogtailTest):
    def setUp(self):
        prj_mb = self.menubar.child(name='Project')
        prj_mb.click()
        open_recent = prj_mb.child(name='Open Recent', roleName='menu item')
        menu = open_recent.child(roleName='popup menu')
        menu.children()[0].click()  # 点击最近打开的项目
        self.logger.info("打开最近的项目")
        time.sleep(3)  # 等待项目加载完成
        self.logger.info("项目已打开，准备进行测量工具测试")

    def test_measure_tool(self):
        # 打开测量工具
        tools = self.app.child(name='Attributes Toolbar', roleName='tool bar')
        measure_tools = tools.child(name='Measure Line', roleName='menu item')  # 以测量线为例，可根据需求换测量面等
        measure_tools.click()
        self.logger.info("测量工具已打开")

        # 获取地图视图区域
        map_view = self.qgis.child(roleName="frame")
        self.move_to_element_center(map_view)

        # 模拟在地图上点击测量起点和终点（示例点击两次，可根据实际测量需求调整点击次数和位置）
        self.click()
        time.sleep(1)
        self.click()
        self.logger.info("已模拟在地图上点击测量点")

        # 查看测量结果（假设测量结果会显示在底部状态栏或专门的测量结果窗口，需根据实际 UI 调整获取逻辑）
        # 以下示例为假设从状态栏获取简单文本结果，实际可能需要更复杂的元素定位
        status_bar = self.qgis.child(roleName='status bar')
        measure_result = status_bar.child(roleName='label').name
        self.logger.info(f"测量结果：{measure_result}")

        # 关闭测量工具（通常在工具菜单或工具条上有关闭选项，需根据实际 UI 调整）
        measure_tool_close = self.qgis.child(name='Measure Line', roleName='toggle button')  # 假设是 toggle 按钮，点击关闭
        measure_tool_close.click()
        self.logger.info("测量工具已关闭")


if __name__ == '__main__':
    unittest.main()