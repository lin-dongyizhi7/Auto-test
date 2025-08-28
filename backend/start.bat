@echo off
echo 自动化测试后端服务启动脚本
echo ======================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo Python版本检查通过

REM 检查是否在虚拟环境中
if "%VIRTUAL_ENV%"=="" (
    echo 警告: 未在虚拟环境中运行，建议使用虚拟环境
)

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo 依赖安装完成

REM 启动服务
echo 启动后端服务(uvicorn)...
echo 服务地址: http://localhost:8080
echo API文档: http://localhost:8080/docs
echo 按 Ctrl+C 停止服务
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload