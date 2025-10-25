@echo off
chcp 65001 >nul
title 电梯调度算法测试系统 - 启动器

echo ============================================
echo   电梯调度算法测试与对比系统
echo   Elevator Scheduling Algorithm Test System
echo ============================================
echo.

:: 检查Python是否安装
echo [1/3] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未检测到Python安装
    echo.
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 显示Python版本
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ 检测到 %PYTHON_VERSION%
echo.

:: 检查tkinter是否可用（通常Python自带）
echo [2/3] 检查GUI库...
python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: tkinter未安装
    echo.
    echo tkinter通常随Python一起安装
    echo 如果您使用的是Linux，请运行: sudo apt-get install python3-tk
    echo.
    pause
    exit /b 1
)
echo ✅ GUI库已就绪
echo.

:: 运行程序
echo [3/3] 启动程序...
echo.
echo ============================================
echo   程序正在启动，请稍候...
echo ============================================
echo.

python elevator_GUI.py

:: 如果程序异常退出
if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo ❌ 程序异常退出 (错误码: %errorlevel%)
    echo ============================================
    echo.
    pause
)

exit /b %errorlevel%
