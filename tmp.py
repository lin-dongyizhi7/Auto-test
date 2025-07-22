from test_base import QGISDogtailTest
import unittest
import time


class TestQGISTmp(QGISDogtailTest):  

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

        try: 
            self.click_image('qgis_image/cleanInput.png')
        except Exception as e:
            self.logger.error(f"清除输入框失败: {e}")
        self.click_image('qgis_image/vectorFileInput.png')
        # file_dialog = self.qgis.child(name="Data Source Manager | Vector", roleName='dialog')
        # file_input = file_dialog.child(name='Vector Dataset(s)', roleName='filter')
        # file_input.click()
        self.input_text(layer_path)
        self.click_image('qgis_image/apply.png')
        self.click_image('qgis_image/close.png')
        self.logger.info(f"矢量图层 {layer_path} 已添加")
      

    def test_tmp(self):
        self.addVectorLayer('/home/yys/QGIS/qgis-auto-test/data/BeiJing.geojson')
        self.addVectorLayer('/home/yys/QGIS/qgis-auto-test/data/ShangHai.geojson')


if __name__ == '__main__':
    unittest.main()