#!/usr/bin/env python3
"""
简化版启动脚本 - 同时启动前后端服务
"""
import subprocess
import sys
import time
from pathlib import Path

def main():
    print("🚀 启动自动化测试系统...")
    
    # 启动后端
    print("启动后端服务...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
    backend_process = subprocess.Popen(backend_cmd, cwd="backend")
    
    # 等待后端启动
    time.sleep(3)
    
    # 启动前端
    print("启动前端服务...")
    frontend_cmd = ["npm", "run", "dev"]
    frontend_process = subprocess.Popen(frontend_cmd, cwd="frontend")
    
    print("✅ 服务启动完成！")
    print("📍 后端: http://localhost:8080")
    print("📍 前端: http://localhost:3000")
    print("💡 按 Ctrl+C 停止服务")
    
    try:
        # 等待任一进程结束
        while backend_process.poll() is None and frontend_process.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 停止服务...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ 服务已停止")

if __name__ == "__main__":
    main()
