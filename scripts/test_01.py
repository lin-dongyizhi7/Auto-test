import os
from test_base import QGISDogtailTest
import unittest
import time


class TestQGISProjectCreation(QGISDogtailTest):  

    def addVectorLayer(self, layer_path):
        """
        添加矢量图层
        :param layer_path: 矢量图层文件路径
        :return: 操作成功返回True，失败返回False
        """
        layer_mb = self.menubar.menuItem('Layer')
        layer_mb.click()
        addLayer = layer_mb.child('Add Layer')
        addLayer.click()
        addVectorLayer = addLayer.child('Add Vector Layer…')
        addVectorLayer.click()
        self.logger.info("添加矢量图层对话框已打开")

        self.click_image('qgis_image/cleanInput.png')
        self.click_image('qgis_image/input.png')
        self.input_text(layer_path)
        self.click_image('qgis_image/apply.png')
        self.click_image('qgis_image/close.png')
        self.logger.info(f"矢量图层 {layer_path} 已添加")
        

    def addVectorLayerFromBrowser(self, layerName):
        browser = self.qgis.child(name='Browser', roleName='frame')
        file_tree = browser.child(roleName='tree')
        layer = file_tree.child(name=layerName, roleName='table cell')
        if layer:
            layer.click()
            self.logger.info(f"已选中图层: {layerName}")
            layer.doubleClick()
        return layer  # 返回找到的图层，方便后续验证

    def test_project_creation(self):
        # 创建新地图项目
        prj_bars = self.qgis.child(name='Project Toolbar', roleName='tool bar')
        new_project = prj_bars.child(name='New', roleName='push button')
        new_project.click()
        self.logger.info("新地图项目已创建")
        # 验证：新项目创建后，标题栏是否符合预期（假设标题栏会显示"无标题"之类内容，需根据实际改）
        window_title = self.rect.name
        self.assertTrue(window_title.startswith("Untitled"), "新建项目后窗口标题不是以Untitled开头")

        # 添加底图
        web_mb = self.menubar.child(name='Web')
        web_mb.click()
        QMS = web_mb.child(name='QuickMapServices')
        QMS.click()
        OSM = QMS.child(name='OSM')
        OSM.click()
        OSM_standard = OSM.child(name='OSM Standard')
        OSM_standard.click()
        self.logger.info("OSM底图添加成功")
        # 验证：底图图层是否添加到图层列表
        layers_panel = self.qgis.child(name='Layers', roleName='frame')
        layer_tree = layers_panel.child(roleName='tree')
        osm_layer = layer_tree.child(name='OSM Standard', roleName='table cell')
        self.assertIsNotNone(osm_layer, "OSM 底图图层未成功添加到图层列表")
        # 验证OSM图层属性
        self.assertEqual(osm_layer.name, "OSM Standard", "OSM图层名称不正确")
        self.assertTrue(osm_layer.visible, "OSM图层应该可见")

        # 添加矢量图层
        beijing_layer = self.addVectorLayerFromBrowser('BeiJing.geojson')
        shanghai_layer = self.addVectorLayerFromBrowser('ShangHai.geojson')
        # 验证矢量图层是否成功添加
        self.assertIsNotNone(beijing_layer, "北京图层未成功添加")
        self.assertIsNotNone(shanghai_layer, "上海图层未成功添加")
        # 验证图层名称
        beijing_layer_refresh = layer_tree.child(name='BeiJing', roleName='table cell')
        shanghai_layer_refresh = layer_tree.child(name='ShangHai', roleName='table cell')
        self.assertIsNotNone(beijing_layer_refresh, "北京图层在图层树中未找到")
        self.assertIsNotNone(shanghai_layer_refresh, "上海图层在图层树中未找到")

        # 缩放工具操作
        map_view = self.qgis.child(roleName="frame")
        self.drag_map_percentage(0.6, 0.7, 0.5, 0.6)
        scale_bar = self.statusbar.child(roleName='combo box', description='Current map scale (formatted as x:y)')
        before_zoom_scale = scale_bar.name
        map_bars = self.qgis.child(name='Map Navigation Toolbar', roleName='tool bar')
        zoom_to_layer = map_bars.child(name='Zoom to Layer(s)', roleName='push button')
        zoom_to_layer.click()
        # 验证：点击缩放至图层后，地图范围是否有变化（简单对比点击前后地图视图位置，可更精细实现）
        time.sleep(0.2)
        after_zoom_scale = scale_bar.name
        self.assertNotEqual(before_zoom_scale, after_zoom_scale, "点击缩放至图层后，地图范围未变化")
        # 验证缩放按钮状态
        zoom_in = map_bars.child(name='Zoom In', roleName='check box')
        zoom_in.click()
        self.assertTrue(zoom_in.checked, "缩放工具应该被激活")
        self.move_to_element_center(map_view)
        self.click()
        self.click()
        zoom_out = map_bars.child(name='Zoom Out', roleName='check box')
        zoom_out.click()
        self.assertTrue(zoom_out.checked, "缩小工具应该被激活")
        self.move_to_element_center(map_view)
        self.click()
        pan = map_bars.child(name='Pan Map', roleName='check box')
        pan.click()
        self.assertTrue(pan.checked, "平移工具应该被激活")
        self.move_to_element_center(map_view)
        self.scroll(-2)
        self.scroll(5)
        zoom_to_native = map_bars.child(name='Zoom to Native Resolution (100%)', roleName='push button')
        zoom_to_native.click()
        self.logger.info("地图缩放和导航操作已完成")
        
        # 调整图层相关验证
        layers_panel = self.qgis.child(name='Layers', roleName='frame')
        layer_tree = layers_panel.child(roleName='tree')
        layers = [child for child in layer_tree.children if child.roleName == 'table cell']
        # 验证图层数量
        self.assertGreaterEqual(len(layers), 3, "至少应该有3个图层（OSM底图 + 两个矢量图层）")
        layers[0].click()  # 选中第一个图层
        zoom_to_layer.click()
        self.right_click_element(layers[0])
        # 验证右键菜单是否弹出（简单判断右键点击后相关菜单元素是否可找到，需根据实际菜单结构改）
        menu_pos = self.find_image('qgis_image/layerContextMenu.png', confidence=0.6)
        self.assertIsNotNone(menu_pos, "右键菜单未弹出（图像识别失败）")
        # 设置样式
        self.click_image('qgis_image/styles.png')
        self.click_image('qgis_image/editSymbol.png')
        symbol_selector = self.qgis.child(name='Symbol Selector', roleName='dialog')
        self.assertIsNotNone(symbol_selector, "符号选择器对话框未打开")
        symbol_selector.child(name='outline blue').click()
        self.click_image('qgis_image/styleList.png')
        symbol_selector.child(name='OK', roleName='push button').click()
        # self.click_image('qgis_image/okNoIcon.png')
        zoom_last = map_bars.child(name='Zoom Last', roleName='push button')
        zoom_last.click()
        zoom_next = map_bars.child(name='Zoom Next', roleName='push button')
        zoom_next.click()
        
        # 图层树操作
        self.drag_item_to_cousin(layers[0], layers[1])
        layer_bar = layers_panel.child(roleName='tool bar')
        layer_bar.child(name='Add Group', roleName='push button').click()
        # 验证组是否创建成功
        group = layer_tree.child(name='group1', roleName='table cell')
        self.assertIsNotNone(group, "图层组未成功创建")
        beijing_layer = layer_tree.child(name='BeiJing', roleName='table cell')
        shanghai_layer = layer_tree.child(name='ShangHai', roleName='table cell')
        group = layer_tree.child(name='group1', roleName='table cell')
        self.drag_item_to_parent(beijing_layer, group)
        self.drag_item_to_parent(shanghai_layer, group)
        # 验证图层是否成功移动到组中
        self.assertIsNotNone(group.child(name='BeiJing', roleName='table cell'), "北京图层未成功移动到组中")
        self.assertIsNotNone(group.child(name='ShangHai', roleName='table cell'), "上海图层未成功移动到组中")
        layer_bar.child(name='Collapse All', roleName='push button').click()
        layer_bar.child(name='Expand All', roleName='push button').click()
        self.right_click_element(group)
        self.click_image('qgis_image/moveToTop.png')
        self.hotkey('ctrl', 'shift', 'h')
        time.sleep(0.2)
        self.hotkey('ctrl', 'shift', 'u')

        # 测量工具操作
        tools = self.qgis.child(name='Attributes Toolbar', roleName='tool bar')
        measure_tools = tools.child(name='Measure Line', roleName='check box')  # 以测量线为例，可根据需求换测量面等
        measure_tools.click()
        self.logger.info("测量工具已打开")
        # 验证测量工具是否激活
        self.assertTrue(measure_tools.checked, "测量工具应该被激活")
        # 获取地图视图区域
        prj_view = self.qgis.child(roleName="frame")
        map_view = prj_view.child(roleName="layered pane")
        self.assertIsNotNone(map_view, "地图视图区域未找到")
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
        self.assertIsNotNone(measure_dialog, "测量结果对话框未打开")
        result_unit = measure_dialog.child(roleName='combo box')
        self.assertIsNotNone(result_unit, "测量单位选择器未找到")
        self.select_combo_item(result_unit, 'kilometers', 'list item')
        # self.logger.info(f"测量结果：{measure_result}")
        measure_dialog.child(name='Copy All', roleName='push button').click()  # 假设有复制全部结果按钮
        self.logger.info("测量结果已复制到剪贴板")
        measure_dialog.child(name='Close', roleName='push button').click()
        # 关闭测量工具
        map_nav_toolbar = self.qgis.child(name='Map Navigation Toolbar', roleName='tool bar')
        pan_button = map_nav_toolbar.child(name='Pan Map', roleName='check box')
        pan_button.click()  # 切换回平移模式
        self.assertTrue(pan_button.checked, "平移工具应该被激活")
        self.logger.info("测量工具已关闭")
                
        # 保存项目文件
        save_project = prj_bars.child(name='Save', roleName='push button')
        save_project.click()
        time.sleep(3)
        self.logger.info("项目文件保存对话框已打开")
        self.click_image('qgis_image/saveInput.png')
        idx = int(time.time())
        self.input_text(f'my_project_{idx}.qgs')
        self.hotkey('enter')
        # 验证：项目是否成功保存（可检查文件是否存在，需结合实际保存路径）
        project_save_path = f'/home/yys/QGIS/prj/my_project_{idx}.qgs'  # 假设保存路径，需根据实际改
        time.sleep(5)
        self.assertTrue(os.path.exists(project_save_path), "项目文件未成功保存")


if __name__ == '__main__':
    unittest.main()