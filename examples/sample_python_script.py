#!/usr/bin/env python3
"""
示例Python脚本 - 演示如何使用OpRecord类

这个脚本展示了如何编写Python自动化测试脚本，
使用OpRecord类来记录操作步骤，最终转换为JSON格式执行。

新增功能：
- validate_result(): 添加断言验证步骤
- 支持元素属性值验证（如文本内容、数值比较等）
- 断言步骤会转换为JSON中的"assert"类型步骤
- 在脚本执行时，被测机器会处理具体的断言逻辑
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

# 等待结果并验证
OpRecord.wait_for_element("", 5, ["text"], "等待结果显示")

# 验证计算结果
OpRecord.validate_result("", "", "15", ["text"], "验证计算结果为15")

# 清空计算器
OpRecord.hotkey(["Ctrl", "a"], "全选")
OpRecord.key_press("Delete", "删除内容")

# 进行更复杂的计算
OpRecord.click_element("5", ["push button"], "点击数字5")
OpRecord.click_element("×", ["push button"], "点击乘号")
OpRecord.click_element("4", ["push button"], "点击数字4")
OpRecord.click_element("=", ["push button"], "点击等号")

# 验证乘法结果
OpRecord.validate_result("", "", "20", ["text"], "验证乘法计算结果为20")

# 清空计算器
OpRecord.click_element("C", ["push button"], "清空计算器")

# 小数计算测试
print("开始小数计算测试...")
OpRecord.click_element("3", ["push button"], "点击数字3")
OpRecord.click_element(".", ["push button"], "点击小数点")
OpRecord.click_element("1", ["push button"], "点击数字1")
OpRecord.click_element("4", ["push button"], "点击数字4")
OpRecord.click_element("+", ["push button"], "点击加号")
OpRecord.click_element("2", ["push button"], "点击数字2")
OpRecord.click_element(".", ["push button"], "点击小数点")
OpRecord.click_element("8", ["push button"], "点击数字8")
OpRecord.click_element("6", ["push button"], "点击数字6")
OpRecord.click_element("=", ["push button"], "点击等号")

# 验证小数计算结果
OpRecord.validate_result("", "", "6", ["text"], "验证小数计算结果为6")

# 清空计算器
OpRecord.click_element("C", ["push button"], "清空计算器")

# 组合运算测试
print("开始组合运算测试...")
OpRecord.click_element("(", ["push button"], "点击左括号")
OpRecord.click_element("1", ["push button"], "点击数字1")
OpRecord.click_element("0", ["push button"], "点击数字0")
OpRecord.click_element("+", ["push button"], "点击加号")
OpRecord.click_element("5", ["push button"], "点击数字5")
OpRecord.click_element(")", ["push button"], "点击右括号")
OpRecord.click_element("×", ["push button"], "点击乘号")
OpRecord.click_element("2", ["push button"], "点击数字2")
OpRecord.click_element("=", ["push button"], "点击等号")

# 验证组合运算结果
OpRecord.validate_result("", "", "30", ["text"], "验证组合运算结果为30")

# 清空计算器
OpRecord.click_element("C", ["push button"], "清空计算器")

# 除法测试
print("开始除法测试...")
OpRecord.click_element("1", ["push button"], "点击数字1")
OpRecord.click_element("5", ["push button"], "点击数字5")
OpRecord.click_element("÷", ["push button"], "点击除号")
OpRecord.click_element("3", ["push button"], "点击数字3")
OpRecord.click_element("=", ["push button"], "点击等号")

# 验证除法结果
OpRecord.validate_result("", "", "5", ["text"], "验证除法结果为5")

# 清空计算器
OpRecord.click_element("C", ["push button"], "清空计算器")

# 负数计算测试
print("开始负数计算测试...")
OpRecord.click_element("-", ["push button"], "点击负号")
OpRecord.click_element("8", ["push button"], "点击数字8")
OpRecord.click_element("+", ["push button"], "点击加号")
OpRecord.click_element("1", ["push button"], "点击数字1")
OpRecord.click_element("2", ["push button"], "点击数字2")
OpRecord.click_element("=", ["push button"], "点击等号")

# 验证负数计算结果
OpRecord.validate_result("", "", "4", ["text"], "验证负数计算结果为4")

# 清空计算器
OpRecord.click_element("C", ["push button"], "清空计算器")

# 百分比计算测试
print("开始百分比计算测试...")
OpRecord.click_element("5", ["push button"], "点击数字5")
OpRecord.click_element("0", ["push button"], "点击数字0")
OpRecord.click_element("%", ["push button"], "点击百分号")
OpRecord.click_element("=", ["push button"], "点击等号")

# 验证百分比结果
OpRecord.validate_result("", "", "0.5", ["text"], "验证百分比计算结果为0.5")

# 清空计算器
OpRecord.click_element("C", ["push button"], "清空计算器")

# 平方根测试
print("开始平方根测试...")
OpRecord.click_element("√", ["push button"], "点击平方根")
OpRecord.click_element("1", ["push button"], "点击数字1")
OpRecord.click_element("6", ["push button"], "点击数字6")
OpRecord.click_element("=", ["push button"], "点击等号")

# 验证平方根结果
OpRecord.validate_result("", "", "4", ["text"], "验证平方根结果为4")

# 清空计算器
OpRecord.click_element("C", ["push button"], "清空计算器")

# 幂运算测试
print("开始幂运算测试...")
OpRecord.click_element("2", ["push button"], "点击数字2")
OpRecord.click_element("^", ["push button"], "点击幂运算")
OpRecord.click_element("3", ["push button"], "点击数字3")
OpRecord.click_element("=", ["push button"], "点击等号")

# 验证幂运算结果
OpRecord.validate_result("", "", "8", ["text"], "验证幂运算结果为8")

# 清空计算器
OpRecord.click_element("C", ["push button"], "清空计算器")

# 复杂混合运算测试
print("开始复杂混合运算测试...")
OpRecord.click_element("(", ["push button"], "点击左括号")
OpRecord.click_element("2", ["push button"], "点击数字2")
OpRecord.click_element("+", ["push button"], "点击加号")
OpRecord.click_element("3", ["push button"], "点击数字3")
OpRecord.click_element(")", ["push button"], "点击右括号")
OpRecord.click_element("×", ["push button"], "点击乘号")
OpRecord.click_element("(", ["push button"], "点击左括号")
OpRecord.click_element("4", ["push button"], "点击数字4")
OpRecord.click_element("-", ["push button"], "点击减号")
OpRecord.click_element("1", ["push button"], "点击数字1")
OpRecord.click_element(")", ["push button"], "点击右括号")
OpRecord.click_element("=", ["push button"], "点击等号")

# 验证复杂混合运算结果
OpRecord.validate_result("", "", "15", ["text"], "验证复杂混合运算结果为15")

# 清空计算器
OpRecord.click_element("C", ["push button"], "清空计算器")

# 连续运算测试
print("开始连续运算测试...")
OpRecord.click_element("1", ["push button"], "点击数字1")
OpRecord.click_element("0", ["push button"], "点击数字0")
OpRecord.click_element("+", ["push button"], "点击加号")
OpRecord.click_element("5", ["push button"], "点击数字5")
OpRecord.click_element("=", ["push button"], "点击等号")
OpRecord.click_element("×", ["push button"], "点击乘号")
OpRecord.click_element("2", ["push button"], "点击数字2")
OpRecord.click_element("=", ["push button"], "点击等号")

# 验证连续运算结果
OpRecord.validate_result("", "", "30", ["text"], "验证连续运算结果为30")

print("计算器测试脚本编写完成！")
print(f"总共记录了 {OpRecord.getStepsCount()} 个操作步骤")

# 获取目标信息
target_info = OpRecord.getTargetInfo()
print(f"目标机器: {target_info['machine_ip']}")
print(f"目标应用: {target_info['app_name']}")

# 转换为JSON（这一步会在后端自动执行）
# json_script = OpRecord.transToJson()
# print("JSON脚本:")
# print(json.dumps(json_script, ensure_ascii=False, indent=2))

