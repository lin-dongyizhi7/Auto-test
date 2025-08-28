'''
Author: lin-dongyizhi7 2985956026@qq.com
Date: 2025-07-24 13:25:17
LastEditors: lin-dongyizhi7 2985956026@qq.com
LastEditTime: 2025-07-28 15:43:01
FilePath: \Auto-test\communicators\test_calculator.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from operation import Operation
import os


if __name__ == "__main__":
    # 1. 实例化操作类
    op = Operation(test_machine_ip="192.168.197.128", test_machine_port=8888)

    # 2. 执行一系列计算器操作
    multiplication_sign = b'\303\227'.decode('utf-8')
    divide_sign = b'\303\267'.decode('utf-8')
    point_sign = chr(0x2e)

    # 计算 12 + 34 的过程
    op.click_element(element_path="1", role_name_list=["push button"])  # 点击数字1
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path="+", role_name_list=["push button"])  # 点击加号
    op.click_element(element_path="3", role_name_list=["push button"])  # 点击数字3
    op.click_element(element_path="4", role_name_list=["push button"])  # 点击数字4
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号

    # 计算 5 * 6 - 7 的过程
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path=multiplication_sign, role_name_list=["push button"])  # 点击乘号
    op.click_element(element_path="6", role_name_list=["push button"])  # 点击数字6
    op.click_element(element_path="-", role_name_list=["push button"])  # 点击减号
    op.click_element(element_path="7", role_name_list=["push button"])  # 点击数字7
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号

    # 计算 81 / 9 的过程
    op.click_element(element_path="8", role_name_list=["push button"])  # 点击数字8
    op.click_element(element_path="1", role_name_list=["push button"])  # 点击数字1
    op.click_element(element_path=divide_sign, role_name_list=["push button"])  # 点击除号
    op.click_element(element_path="9", role_name_list=["push button"])  # 点击数字9
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号

    # 计算 6.5 + 8.5 - 3.4 的过程
    op.click_element(element_path="6", role_name_list=["push button"])  # 点击数字6
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path="+", role_name_list=["push button"])  # 点击加号
    op.click_element(element_path="8", role_name_list=["push button"])  # 点击数字8
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path="-", role_name_list=["push button"])  # 点击减号
    op.click_element(element_path="3", role_name_list=["push button"])  # 点击数字3
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="4", role_name_list=["push button"])  # 点击数字4
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号

    # 计算 2.5 * 4.2 / 1.2 的过程
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path=multiplication_sign, role_name_list=["push button"])  # 点击乘号
    op.click_element(element_path="4", role_name_list=["push button"])  # 点击数字4
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path=divide_sign, role_name_list=["push button"])  # 点击除号
    op.click_element(element_path="1", role_name_list=["push button"])  # 点击数字1
    op.click_element(element_path=point_sign, role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号