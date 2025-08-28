#!/bin/bash

echo "自动化测试后端服务启动脚本"
echo "======================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "Python版本检查通过"

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "警告: 未在虚拟环境中运行，建议使用虚拟环境"
fi

# 安装依赖
echo "安装依赖包..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

echo "依赖安装完成"

# 启动服务
echo "启动后端服务(uvicorn)..."
echo "服务地址: http://localhost:8080"
echo "API文档: http://localhost:8080/docs"
echo "按 Ctrl+C 停止服务"
echo

python3 -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload