import os
from test_base import QGISDogtailTest
import unittest
import time


class TestQGISProjectCreation(QGISDogtailTest):  

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
        # 验证：新项目创建后，标题栏是否符合预期（假设标题栏会显示“无标题”之类内容，需根据实际改）
        window_title = self.rect.name
        self.assertEqual(window_title, "Untitled Project - QGIS", "新建项目后窗口标题不符合预期")

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

        # 添加矢量图层并验证
        beijing_layer = self.addVectorLayerFromBrowser('BeiJing.geojson')
        self.assertIsNotNone(beijing_layer, "BeiJing.geojson 图层添加失败")
        # 验证图层名称是否正确
        self.assertEqual(beijing_layer.name, 'BeiJing', "BeiJing.geojson 图层名称显示不正确")

        shanghai_layer = self.addVectorLayerFromBrowser('ShangHai.geojson')
        self.assertIsNotNone(shanghai_layer, "ShangHai.geojson 图层添加失败")
        self.assertEqual(shanghai_layer.name, 'ShangHai', "ShangHai.geojson 图层名称显示不正确")

        map_view = self.qgis.child(roleName="frame")
        self.drag_map_percentage(0.6, 0.7, 0.5, 0.6)
        map_bars = self.qgis.child(name='Map Navigation Toolbar', roleName='tool bar')
        zoom_to_layer = map_bars.child(name='Zoom to Layer(s)', roleName='push button')
        scale_bar = self.statusbar.child(roleName='combo box', description='Current map scale (formatted as x:y)')
        before_zoom_scale = scale_bar.name
        zoom_to_layer.click()
        # 验证：点击缩放至图层后，地图范围是否有变化（简单对比点击前后地图视图位置，可更精细实现）
        time.sleep(0.2)
        after_zoom_scale = scale_bar.name
        self.assertNotEqual(before_zoom_scale, after_zoom_scale, "点击缩放至图层后，地图范围未变化")
        zoom_in = map_bars.child(name='Zoom In', roleName='check box')
        zoom_in.click()
        self.move_to_element_center(map_view)
        self.click()
        self.click()
        zoom_out = map_bars.child(name='Zoom Out', roleName='check box')
        zoom_out.click()
        self.move_to_element_center(map_view)
        self.click()
        pan = map_bars.child(name='Pan Map', roleName='check box')
        pan.click()
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
        self.assertEqual(len(layers), 3, "图层列表数量不符合预期（OSM底图 + 两个矢量图层）")
        layers[0].click()  # 选中第一个图层
        zoom_to_layer.click()
        self.right_click_element(layers[0])
        # 验证右键菜单是否弹出（简单判断右键点击后相关菜单元素是否可找到，需根据实际菜单结构改）
        menu_pos = self.find_image('qgis_image/layerContextMenu.png', confidence=0.6)
        self.assertIsNotNone(menu_pos, "右键菜单未弹出（图像识别失败）")
        # 设置样式
        self.click_image('qgis_image/styles.png')
        self.click_image('qgis_image/editSymbol.png')
        self.click_image('qgis_image/hashedBlack1.png')
        self.click_image('qgis_image/okNoIcon.png')
        zoom_last = map_bars.child(name='Zoom Last', roleName='push button')
        zoom_last.click()
        zoom_next = map_bars.child(name='Zoom Next', roleName='push button')
        zoom_next.click()
        
        self.drag_item_to_cousin(layers[0], layers[1])
        layer_bar = layers_panel.child(roleName='tool bar')
        layer_bar.child(name='Add Group', roleName='push button').click()
        beijing_layer = layer_tree.child(name='BeiJing', roleName='table cell')
        shanghai_layer = layer_tree.child(name='ShangHai', roleName='table cell')
        group = layer_tree.child(name='group1', roleName='table cell')
        self.drag_item_to_parent(beijing_layer, group)
        self.drag_item_to_parent(shanghai_layer, group)
        layer_bar.child(name='Collapse All', roleName='push button').click()
        layer_bar.child(name='Expand All', roleName='push button').click()
                
        # 保存项目文件
        save_project = prj_bars.child(name='Save', roleName='push button')
        save_project.click()
        time.sleep(2)
        self.logger.info("项目文件保存对话框已打开")
        self.click_image('qgis_image/saveInput.png')
        idx = int(time.time())
        self.input_text(f'my_project_{idx}.qgs')
        self.hotkey('enter')
        # 验证：项目是否成功保存（可检查文件是否存在，需结合实际保存路径）
        project_save_path = f'/home/yys/QGIS/prj/my_project_{idx}.qgs'  # 假设保存路径，需根据实际改
        self.assertTrue(os.path.exists(project_save_path), "项目文件未成功保存")


if __name__ == '__main__':
    unittest.main()