# Operation.py API 描述表格

| 编号 | API名称 | API描述 |
|------|---------|---------|
| 1 | `__init__(test_machine_ip, test_machine_port=8888)` | 初始化操作类并建立与被测试机器的通信连接 |
| 2 | `find_image(image_path, threshold=0.8, region=None)` | 查找图片位置，返回位置信息字典 |
| 3 | `click_image(image_path, threshold=0.8, region=None)` | 点击图片位置，先查找图片再点击 |
| 4 | `get_location(element_path, role_name_list=None)` | 获取元素位置信息，返回包含坐标和尺寸的字典 |
| 5 | `click_element(element_path, role_name_list=None)` | 生成点击元素的指令（移动到中心位置后点击） |
| 6 | `right_click_element(element_path, role_name_list=None)` | 生成右键点击元素的指令（移动到中心位置后右键点击） |
| 7 | `double_click_element(element_path, role_name_list=None)` | 生成双击元素的指令（移动到中心位置后双击） |
| 8 | `set_element_text(element_path, text, role_name_list=None)` | 生成设置元素文本的指令（点击激活→全选→删除→输入） |
| 9 | `select_combo_item(combo_path, item_text, role_name_list=None)` | 生成下拉框选择的指令（点击下拉框→点击选项） |
| 10 | `set_radio_btn(radio_btn_path, role_name_list=None)` | 生成设置单选按钮的指令（点击单选按钮） |
| 11 | `set_checkbox(checkbox_path, role_name_list=None)` | 生成设置复选框的指令（点击复选框） |
| 12 | `input_text(element_path, text, role_name_list=None)` | 生成输入文本的指令（若有元素则先点击激活） |
| 13 | `drag_to(start_x, start_y, end_x, end_y)` | 生成拖拽操作的指令（绝对坐标） |
| 14 | `drag_to_percentage(app_name, start_x_pct, start_y_pct, end_x_pct, end_y_pct)` | 生成按百分比拖拽地图的指令（基于屏幕尺寸计算） |
| 15 | `drag_item_to_parent(item_path, parent_path, item_role_list=None, parent_role_list=None)` | 生成拖拽元素到父元素的指令 |
| 16 | `drag_item_to_cousin(item_path, cousin_path, item_role_list=None, cousin_role_list=None)` | 生成拖拽元素到兄弟元素的指令 |
| 17 | `hotkey(keys)` | 生成组合键操作的指令 |
| 18 | `scroll(clicks)` | 生成鼠标滚动的指令（正数向上滚动，负数向下滚动） |
| 19 | `move_to(x, y)` | 生成鼠标移动到指定位置的指令 |
| 20 | `move_to_element_center(element_path, role_name_list=None)` | 生成鼠标移动到元素中心的指令 |
| 21 | `export_to_json(file_path)` | 将.commands_list导出为JSON文件 |
| 22 | `finish_current_opts(commands)` | 结束当前操作指令集并执行 |
| 23 | `execute_commands()` | 通过通信类执行当前指令集中的所有指令 |
| 24 | `close()` | 关闭与被测试机器的通信连接 |

## 说明

- **元素路径格式**: 使用"父元素1/父元素2/目标元素"的路径格式
- **角色名列表**: 支持多个角色名匹配，如 `["button", "menu item"]`
- **坐标系统**: 支持绝对坐标和百分比坐标
- **指令生成**: 每个操作都会生成相应的鼠标和键盘指令序列
- **通信机制**: 通过TestMachineCommunicator与被测试机器进行通信 