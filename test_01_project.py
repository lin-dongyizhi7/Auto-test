from test_base import QGISDogtailTest
import unittest
import time

class TestQGISProjectCreation(unittest.TestCase):

    def test_project_creation(self):
        # 创建新地图项目
        prj_bars = self.qgis.child(name='Project Toolbar', roleName='tool bar')
        new_project = prj_bars.child(name='New', roleName='push button')
        new_project.click()

        # 添加底图
        web_bar = self.menubar.child(name='Web')
        web_bar.click()
        QMS = web_bar.child(name='QuickMapServices')
        QMS.click()
        OSM = QMS.child(name='OSM')
        OSM.click()
        OSM_standard = OSM.child(name='OSM Standard')
        OSM_standard.click()
        self.logger.info("OSM底图添加成功")
        
        # 添加本地Shapefile图层
        layer_mb = self.menubar.menuItem('Layer')
        layer_mb.click()
        addLayer = layer_mb.child('Add Layer')
        addLayer.click()
        addVectorLayer = addLayer.child('Add Vector Layer…')
        addVectorLayer.click()
        
        # 浏览并选择Shapefile文件
        file_dialog = self.qgis.child(name='Data Source Manager | Vector', roleName='dialog')
        file_input = file_dialog.child(name='Vector Dataset(s)', roleName='filter')

        self.input_text(file_input, '/home/yys/auto-test/qgis-automation-tests/QGIS-Training-Data/exercise_data/shapefile/places.shp')
        add_btn = file_dialog.child(name='Add', roleName='push button')
        add_btn.click()

        self.input_text(file_input, '/home/yys/auto-test/qgis-automation-tests/QGIS-Training-Data/exercise_data/shapefile/water.shp')
        add_btn = file_dialog.child(name='Add', roleName='push button')
        add_btn.click()

        self.input_text(file_input, '/home/yys/auto-test/qgis-automation-tests/QGIS-Training-Data/exercise_data/shapefile/rivers.shp')
        add_btn = file_dialog.child(name='Add', roleName='push button')
        add_btn.click()

        self.input_text(file_input, '/home/yys/auto-test/qgis-automation-tests/QGIS-Training-Data/exercise_data/shapefile/protected_areas.shp')
        add_btn = file_dialog.child(name='Add', roleName='push button')
        add_btn.click()

        close_btn = file_dialog.child(name='关闭(C)', roleName='push button')
        close_btn.click()

        map_bars = self.qgis.child(name='Map Navigation Toolbar', roleName='tool bar')
        zoom_in = map_bars.child(name='Zoom In', roleName='push button')
        zoom_in.click()
        self.move_to_window_center()
        self.click()
        self.click()
        zoom_out = map_bars.child(name='Zoom Out', roleName='push button')
        zoom_out.click()
        self.move_to_window_center()
        self.click()

        pan = map_bars.child(name='Pan Map', roleName='push button')
        pan.click()
        self.scroll(-2)
        self.scroll(5)

        zoom_to_native = map_bars.child(name='Zoom to Native Resolution(100%)', roleName='push button')
        zoom_to_native.click()
        
        # 调整图层顺序
        layers_panel = self.qgis.child(name='Layers', roleName='frame')
        layerTree = layers_panel.child(roleName='tree')
        layers = layerTree.children(roleName='table cell')
        if len(layers) > 1:
            layer1 = layers[0]
            layer2 = layers[1]
            layer1.dragAndDrop(layer2, 'below')
            self.logger.info("调整图层顺序: 将第一个图层移到第二个图层下方")
        layers[0].click()  # 选中第一个图层
        zoom_to_layer = map_bars.child(name='Zoom to Layer(s)', roleName='push button')
        zoom_to_layer.click()
        zoom_last = map_bars.child(name='Zoom Last', roleName='push button')
        zoom_last.click()
        zoom_next = map_bars.child(name='Zoom Next', roleName='push button')
        zoom_next.click()
                
        # 保存项目文件
        save_project = prj_bars.child(name='Save Project', roleName='push button')
        save_project.click()
        idx = int(time.time())
        self.input_text(f'my_project_{idx}')
        self.dialog_app.child(name='保存', roleName='push button').click()


if __name__ == '__main__':
    unittest.main()
