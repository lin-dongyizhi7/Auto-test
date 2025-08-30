from ..operation_multi_machine import MultiMachineOperation
import time
import logging

if __name__ == "__main__":
    # 作为脚本运行：启动服务器并常驻监听
    op = MultiMachineOperation()
    try:
        while True:
            time.sleep(5)
            # 定期打印状态（不强制要求连接，始终常驻）
            machines = op.get_available_machines()
            apps = op.get_available_apps()
            logging.info(f"运行中：已连接机器 {len(machines)}，已注册应用 {len(apps)}")
    except KeyboardInterrupt:
        op.close()
        logging.info("已退出")