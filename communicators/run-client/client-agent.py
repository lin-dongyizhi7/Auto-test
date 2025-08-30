from communicators.tested_communicator import TestedMachineCommunicator

# 启动服务（直接运行该脚本即可）
if __name__ == "__main__":
    # 初始化服务，监听8888端口
    communicator = TestedMachineCommunicator(
        bind_port=8888,
        test_server_host="192.168.44.1",  # 配置测试服务器地址
        test_server_port=8889,
        machine_id="test_machine_001"  # 配置机器ID
    )
    
    try:
        # 启动服务，指定要监控的应用
        communicator.start(app_names=["calculator", "gedit"])  # 监控计算器和文本编辑器
        # communicator.start()  # 监控所有应用
    except KeyboardInterrupt:
        # 按Ctrl+C停止服务
        communicator.stop()