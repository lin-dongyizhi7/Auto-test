from operation import Operation
import os


if __name__ == "__main__":
    # 1. 实例化操作类
    op = Operation(test_machine_ip="192.168.5.130", test_machine_port=8888)

    # 2. 执行一系列计算器操作
    multiplication_sign = b'\303\227'.decode('utf-8')
    divide_sign = b'\303\267'.decode('utf-8')
    # 计算 5² 的过程
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    result = op.click_image(os.path.abspath("communicators/image/square.png"), threshold=0.8)
    if result["success"]:
        print(f"找到目标图片，位置: {result['data']}")
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号

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
    op.click_element(element_path=".", role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path="+", role_name_list=["push button"])  # 点击加号
    op.click_element(element_path="8", role_name_list=["push button"])  # 点击数字8
    op.click_element(element_path=".", role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path="-", role_name_list=["push button"])  # 点击减号
    op.click_element(element_path="3", role_name_list=["push button"])  # 点击数字3
    op.click_element(element_path=".", role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="4", role_name_list=["push button"])  # 点击数字4
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号

    # 计算 2.5 * 4.2 / 1.2 的过程
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path=".", role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="5", role_name_list=["push button"])  # 点击数字5
    op.click_element(element_path=multiplication_sign, role_name_list=["push button"])  # 点击乘号
    op.click_element(element_path="4", role_name_list=["push button"])  # 点击数字4
    op.click_element(element_path=".", role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path=divide_sign, role_name_list=["push button"])  # 点击除号
    op.click_element(element_path="1", role_name_list=["push button"])  # 点击数字1
    op.click_element(element_path=".", role_name_list=["push button"])  # 点击小数点
    op.click_element(element_path="2", role_name_list=["push button"])  # 点击数字2
    op.click_element(element_path="=", role_name_list=["push button"])  # 点击等号