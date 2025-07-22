from test_base import QGISDogtailTest
import unittest
import time


class TestNewShapefileCreation(QGISDogtailTest):
    """测试创建点、线、面Shapefile并绘制要素"""

    def create_shapefile(self, shape_type, name):
        """
        创建指定类型的Shapefile
        :param shape_type: 形状类型（'Point'/'LineString'/'Polygon'）
        :param name: Shapefile名称
        :return: 创建成功返回图层元素，失败返回None
        """
        # 1. 点击Data Source Manager Toolbar中的"New Shapefile Layer"按钮
        self.qgis.child(name='Data Source Manager Toolbar', roleName='tool bar').child(name='New Shapefile Layer', roleName='push button').click()
        # 2. 等待"New Shapefile Layer"对话框加载
        dialog_title = "New Shapefile Layer"
        self.assertTrue(
            self.wait_for_element(dialog_title, roleName="dialog"),
            f"{dialog_title}对话框未弹出"
        )
        dialog = self.find_element(dialog_title, roleName="dialog")
        self.logger.info(f"已打开{dialog_title}对话框")

        # 3. 选择形状类型（点/线/面）
        # 定位"Type"下拉框并选择对应类型
        type_combo = dialog.child(name="", roleName="combo box")
        self.assertTrue(type_combo, "未找到Type下拉框")
        self.select_combo_item(type_combo,item_text=shape_type, roleName="list item")
        self.logger.info(f"已选择形状类型：{shape_type}")

        # 4. 输入名称（Name）
        self.click_image('qgis_image/inputFileName.png')  # 假设有输入框图像
        self.input_text(name)
        self.logger.info(f"已输入Shapefile名称：{name}")

        # 5. 点击"OK"创建（不设置其他属性）
        ok_btn = dialog.child(name="OK", roleName="push button")
        self.assertTrue(ok_btn, "未找到OK按钮")
        ok_btn.click()

        # 6. 验证图层是否创建成功（图层列表中出现对应名称）
        layer = self.wait_for_element('Layers/' + name)
        # layers_panel = self.qgis.child(name='Layers', roleName='frame')
        # layer_tree = layers_panel.child(roleName='tree')
        # layer = layer_tree.child(name=name, roleName='table cell')
        self.assertIsNotNone(layer, f"{name}图层创建失败")
        self.logger.info(f"{name}（{shape_type}）创建成功")
        return layer

    def draw_feature(self, layer_name, shape_type):
        """
        在指定图层绘制要素
        :param layer_name: 图层名称
        :param shape_type: 形状类型（'Point'/'LineString'/'Polygon'）
        """
        # 1. 激活编辑（Digitizing Toolbar -> Toggle Editing）
        digitizing_bars = self.qgis.child(name='Digitizing Toolbar', roleName='tool bar')
        toggle_edit = digitizing_bars.child(name='Toggle Editing', roleName='check box')
        toggle_edit.click()
        
        # 验证是否进入编辑模式（图层名旁出现铅笔图标，或通过图像识别）
        self.assertTrue(
            self.find_image("qgis_image/editing_active.png", timeout=3),  # 编辑中状态图标
            f"{layer_name}未进入编辑模式"
        )
        self.logger.info(f"{layer_name}已激活编辑模式")

        # 2. 选择对应绘制工具（Digitizing Toolbar）
        shape_type_map = {
            "Point": "Add Point Feature",
            "LineString": "Add Line Feature",
            "Polygon": "Add Polygon Feature"
        }
        tool_bar = digitizing_bars.child(name=shape_type_map[shape_type], roleName='check box')
        self.assertTrue(
            tool_bar,
            f"未找到{shape_type}绘制工具"
        )
        tool_bar.click()
        self.logger.info(f"已选择{shape_type}绘制工具")

        # 3. 在地图区域绘制
        map_view = self.find_element("QGIS Map Canvas")
        self.assertIsNotNone(map_view, "未找到地图画布")
        center_x, center_y = self.get_element_center(map_view)  # 基类需实现获取元素中心的方法

        # 根据形状类型执行不同绘制动作
        if shape_type == "Point":
            # 点：直接点击
            self.click(center_x, center_y)
        elif shape_type == "LineString":
            # 线：点击起点和终点
            self.click(center_x, center_y)
            self.click(center_x + 100, center_y + 50)  # 终点
            self.rightClick()  # 结束绘制
        elif shape_type == "Polygon":
            # 面：点击三个顶点
            self.click(center_x, center_y)
            self.click(center_x + 100, center_y)
            self.click(center_x + 50, center_y + 80)
            self.rightClick()  # 结束绘制

        time.sleep(1)
        self.logger.info(f"{shape_type}要素绘制完成")

        # 4. 处理属性对话框（填写id）
        self.assertTrue(
            self.wait_for_element("Attributes", roleName="dialog", timeout=5),
            "属性对话框未弹出"
        )
        # 输入id（假设输入1）
        self.type_text("1", element_path="Attributes/id", roleName="text")
        self.click_element("Attributes/OK", roleName="push button")
        self.logger.info("已填写id属性并确认")

        # 5. 保存编辑
        self.click_image("qgis_image/save_edits.png", timeout=5)  # 保存编辑按钮图像

    def test_create_and_draw_shapefiles(self):
        """测试创建点、线、面Shapefile并绘制要素"""
        # 定义要创建的Shapefile类型和名称
        shapefiles = [
            ("Point", "Test_Point"),
            ("LineString", "Test_Line"),
            ("Polygon", "Test_Polygon")
        ]

        # 逐个创建并绘制
        for shape_type, name in shapefiles:
            self.logger.info(f"===== 开始创建{shape_type}：{name} =====")
            # 1. 创建Shapefile
            layer = self.create_shapefile(shape_type, name)
            # 2. 绘制要素
            self.draw_feature(name, shape_type)
            # 3. 验证要素是否绘制成功（通过图层右键"Open Attribute Table"查看记录数）
            self.right_click_element(f"Layers/{name}")
            self.click_image("qgis_image/open_attr_table.png", timeout=5)  # 打开属性表图像
            # 验证属性表中有1条记录（图像识别"1 of 1"或表格行数）
            self.assertTrue(
                self.find_image("qgis_image/attr_table_1record.png", timeout=5),
                f"{name}属性表中未找到绘制的要素"
            )
            self.click_element("Attributes/Close")  # 关闭属性表
            self.logger.info(f"{name}（{shape_type}）测试通过")

        self.logger.info("所有Shapefile创建和绘制测试完成")


if __name__ == '__main__':
    unittest.main()