@echo off
echo 自动化测试系统 - 前后端同时启动脚本
echo ======================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查Node.js是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

REM 检查npm是否安装
npm --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到npm，请先安装npm
    pause
    exit /b 1
)

echo 环境检查通过
echo.

REM 启动后端服务
echo 启动后端服务...
start "后端服务" cmd /k "cd backend && python -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload"

REM 等待后端服务启动
echo 等待后端服务启动...
timeout /t 3 /nobreak >nul

REM 启动前端服务
echo 启动前端服务...
start "前端服务" cmd /k "cd frontend && npm run dev"

echo.
echo 服务启动完成！
echo ======================================
echo 后端服务: http://localhost:8080
echo API文档: http://localhost:8080/docs
echo 前端服务: http://localhost:3000
echo ======================================
echo 两个服务窗口已打开，按任意键关闭此窗口
pause >nul
