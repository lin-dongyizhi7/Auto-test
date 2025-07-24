from test_base import QGISDogtailTest
import unittest
import time


class TestQGISMeasureTool(QGISDogtailTest):
    # def setUp(self):
    #     prj_mb = self.menubar.child(name='Project')
    #     prj_mb.click()
    #     open_recent = prj_mb.child(name='Open Recent', roleName='menu item')
    #     menu = open_recent.child(roleName='popup menu')
    #     menu.children()[0].click()  # 点击最近打开的项目
    #     self.logger.info("打开最近的项目")
    #     time.sleep(3)  # 等待项目加载完成
    #     self.logger.info("项目已打开，准备进行测量工具测试")

    def test_measure_tool(self):
        # 打开测量工具
        tools = self.qgis.child(name='Attributes Toolbar', roleName='tool bar')
        measure_tools = tools.child(name='Measure Line', roleName='check box')  # 以测量线为例，可根据需求换测量面等
        measure_tools.click()
        self.logger.info("测量工具已打开")

        # 获取地图视图区域
        prj_view = self.qgis.child(roleName="frame")
        map_view = prj_view.child(roleName="layered pane")
        self.move_to_element_center(map_view)
        self.click()

        # 模拟在地图上点击测量起点和终点（示例点击两次，可根据实际测量需求调整点击次数和位置）
        self.move_to_relative_position(map_view, 100, -50)  # 点击地图中心点作为起点
        self.click()
        time.sleep(0.5)
        self.move_to_relative_position(map_view, 50, 100)
        self.click()
        time.sleep(0.5)
        self.move_to_relative_position(map_view, -50, -50)
        self.right_click()
        self.logger.info("已模拟在地图上点击测量点")

        # 查看测量结果
        measure_dialog = self.qgis.child(name='Measure', roleName='dialog')
        result_unit = measure_dialog.child(roleName='combo box')
        self.select_combo_item(result_unit, 'kilometers', 'list item')
        # self.logger.info(f"测量结果：{measure_result}")
        measure_dialog.child(name='Copy All', roleName='push button').click()  # 假设有复制全部结果按钮
        self.logger.info("测量结果已复制到剪贴板")
        measure_dialog.child(name='Close', roleName='push button').click()

        # 关闭测量工具
        self.qgis.child(name='Map Navigation Toolbar', roleName='tool bar').child(name='Pan Map', roleName='check box').click()  # 切换回平移模式
        self.logger.info("测量工具已关闭")


if __name__ == '__main__':
    unittest.main()