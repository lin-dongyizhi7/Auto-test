@echo off
echo 正在启动QGIS自动化测试前端...
echo.

REM 检查Node.js是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js
    echo 下载地址: https://nodejs.org/
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

REM 安装依赖
echo 正在安装依赖...
npm install
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

REM 启动开发服务器
echo.
echo 启动开发服务器...
echo 访问地址: http://localhost:3000
echo 按 Ctrl+C 停止服务器
echo.
npm run dev

pause 