from operation import Operation

if __name__ == "__main__":
    # 1. 实例化操作类
    op = Operation(test_machine_ip="192.168.5.129", test_machine_port=8888)

    op.click_element(element_path="MainWindow/MenuBar/File", role_name="menu")

    op.click_element(element_path="MainWindow/MenuBar/File/New", role_name="menu item")

    op.set_element_text(element_path="NewDialog/NameInput",text="test_project",role_name="text entry")

    op.click_element(element_path="NewDialog/OKButton", role_name="push button")

    op.drag_item_to_parent(item_path="LeftPanel/Layers/LayerA",parent_path="RightWorkspace")

    op.hotkey(keys=["Ctrl", "s"])

    op.set_element_text(element_path="SaveDialog/FileNameInput",text="test_project",role_name="text entry")

    op.click_element(element_path="SaveDialog/SaveButton", role_name="push button")

    op.click_element(element_path="MainWindow/TitleBar/CloseButton", role_name="button")
