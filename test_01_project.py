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


    def test_project_creation(self):
        # 创建新地图项目
        prj_bars = self.qgis.child(name='Project Toolbar', roleName='tool bar')
        new_project = prj_bars.child(name='New', roleName='push button')
        new_project.click()
        self.logger.info("新地图项目已创建")

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

        self.addVectorLayerFromBrowser('BeiJing.geojson')
        self.addVectorLayerFromBrowser('ShangHai.geojson')

        map_view = self.qgis.child(roleName="frame")
        self.drag_map_percentage(0.6, 0.7, 0.5, 0.6)
        map_bars = self.qgis.child(name='Map Navigation Toolbar', roleName='tool bar')
        zoom_to_layer = map_bars.child(name='Zoom to Layer(s)', roleName='push button')
        zoom_to_layer.click()
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
        
        # 调整图层
        layers_panel = self.qgis.child(name='Layers', roleName='frame')
        layer_tree = layers_panel.child(roleName='tree')
        layers = [child for child in layer_tree.children if child.roleName == 'table cell']
        layers[0].click()  # 选中第一个图层
        zoom_to_layer.click()
        self.right_click_element(layers[0])
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
        self.input_text(f'my_project_{idx}')
        self.hotkey('enter')


if __name__ == '__main__':
    unittest.main()
