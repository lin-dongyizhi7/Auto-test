#!/usr/bin/env python3
"""
示例Python脚本 - 演示如何使用OpRecord类

这个脚本展示了如何编写Python自动化测试脚本，
使用OpRecord类来记录操作步骤，最终转换为JSON格式执行。
"""

# 导入OpRecord类
from op_record import OpRecord

# 设置目标机器和应用
OpRecord.setMachine("192.168.1.100", "calculator")

# 开始编写操作步骤
print("开始编写计算器测试脚本...")

# 点击数字按钮
OpRecord.click_element("1", ["push button"], "点击数字1")
OpRecord.click_element("2", ["push button"], "点击数字2")
OpRecord.click_element("+", ["push button"], "点击加号")
OpRecord.click_element("3", ["push button"], "点击数字3")
OpRecord.click_element("=", ["push button"], "点击等号")

# 等待结果
OpRecord.wait_for_element("结果显示区域", ["text"], "等待计算结果", timeout=5)

# 清空计算器
OpRecord.hotkey(["Ctrl", "a"], "全选")
OpRecord.key_press("Delete", "删除内容")

# 进行更复杂的计算
OpRecord.click_element("5", ["push button"], "点击数字5")
OpRecord.click_element("×", ["push button"], "点击乘号")
OpRecord.click_element("4", ["push button"], "点击数字4")
OpRecord.click_element("=", ["push button"], "点击等号")

# 输入文本（如果有输入框）
OpRecord.input_text("输入框", "测试文本", ["text field"], "在输入框中输入文本")

# 组合键操作
OpRecord.hotkey(["Ctrl", "c"], "复制")
OpRecord.hotkey(["Ctrl", "v"], "粘贴")

# 右键菜单操作
OpRecord.right_click_element("结果区域", ["text"], "右键点击结果区域")

# 双击操作
OpRecord.double_click_element("标题栏", ["title bar"], "双击标题栏")

# 拖拽操作
OpRecord.drag_and_drop("源元素", "目标元素", ["button"], "拖拽元素")

# 图像识别操作
OpRecord.click_image("button_image.png", 0.8, [100, 100, 200, 200], "点击图片按钮")
OpRecord.find_image("icon.png", 0.9, "查找图标")

# 截图操作
OpRecord.get_screenshot([0, 0, 800, 600], "截取全屏")

print("Python脚本编写完成！")
print(f"总共记录了 {OpRecord.getStepsCount()} 个操作步骤")

# 获取目标信息
target_info = OpRecord.getTargetInfo()
print(f"目标机器: {target_info['machine_ip']}")
print(f"目标应用: {target_info['app_name']}")

# 转换为JSON（这一步会在后端自动执行）
# json_script = OpRecord.transToJson()
# print("JSON脚本:")
# print(json.dumps(json_script, ensure_ascii=False, indent=2))
