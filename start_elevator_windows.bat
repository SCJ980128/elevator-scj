@echo off
REM =============================================================================
REM 电梯调度算法启动脚本 - Windows 版本
REM =============================================================================

chcp 65001 >nul
setlocal enabledelayedexpansion

REM 颜色代码（Windows 10+）
set "COLOR_RESET=[0m"
set "COLOR_INFO=[34m"
set "COLOR_SUCCESS=[32m"
set "COLOR_WARNING=[33m"
set "COLOR_ERROR=[31m"

echo.
echo %COLOR_SUCCESS%==============================================
echo     电梯调度算法启动器 (Windows)
echo ==============================================%COLOR_RESET%
echo.

REM 检查 Python 是否安装
echo %COLOR_INFO%[INFO]%COLOR_RESET% 检查 Python 环境...

set PYTHON_CMD=
set PYTHON_VERSION=

REM 尝试查找 Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% 找到 Python: !PYTHON_VERSION!
    goto :python_found
)

where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    for /f "tokens=*" %%i in ('python3 --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% 找到 Python: !PYTHON_VERSION!
    goto :python_found
)

REM 尝试 Anaconda Python
if exist "C:\APP\Anaconda\python.exe" (
    set PYTHON_CMD=C:\APP\Anaconda\python.exe
    for /f "tokens=*" %%i in ('C:\APP\Anaconda\python.exe --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% 找到 Anaconda Python: !PYTHON_VERSION!
    goto :python_found
)

REM 尝试查找 Anaconda 环境中的 Python
if exist "C:\APP\Anaconda\envs\elevator\python.exe" (
    set PYTHON_CMD=C:\APP\Anaconda\envs\elevator\python.exe
    for /f "tokens=*" %%i in ('C:\APP\Anaconda\envs\elevator\python.exe --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% 找到 Elevator 环境 Python: !PYTHON_VERSION!
    goto :python_found
)

echo %COLOR_ERROR%[ERROR]%COLOR_RESET% 未找到 Python！请先安装 Python 3.7+
pause
exit /b 1

:python_found

REM 检查虚拟环境
echo %COLOR_INFO%[INFO]%COLOR_RESET% 检查虚拟环境...

set VENV_ACTIVATED=0

if exist "venv\Scripts\activate.bat" (
    echo %COLOR_INFO%[INFO]%COLOR_RESET% 找到虚拟环境: venv
    call venv\Scripts\activate.bat
    set VENV_ACTIVATED=1
    echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% 虚拟环境已激活
    goto :venv_checked
)

if exist "env\Scripts\activate.bat" (
    echo %COLOR_INFO%[INFO]%COLOR_RESET% 找到虚拟环境: env
    call env\Scripts\activate.bat
    set VENV_ACTIVATED=1
    echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% 虚拟环境已激活
    goto :venv_checked
)

if exist ".venv\Scripts\activate.bat" (
    echo %COLOR_INFO%[INFO]%COLOR_RESET% 找到虚拟环境: .venv
    call .venv\Scripts\activate.bat
    set VENV_ACTIVATED=1
    echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% 虚拟环境已激活
    goto :venv_checked
)

echo %COLOR_WARNING%[WARNING]%COLOR_RESET% 未找到虚拟环境，使用系统 Python

:venv_checked

REM 检查依赖包
echo %COLOR_INFO%[INFO]%COLOR_RESET% 检查依赖包...

%PYTHON_CMD% -c "import elevator_saga" >nul 2>&1
if %errorlevel% equ 0 (
    echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% elevator_saga 包已安装
) else (
    echo %COLOR_ERROR%[ERROR]%COLOR_RESET% elevator_saga 包未安装！
    echo %COLOR_INFO%[INFO]%COLOR_RESET% 尝试安装依赖...
    
    if exist "requirements.txt" (
        %PYTHON_CMD% -m pip install -r requirements.txt
    ) else (
        echo %COLOR_ERROR%[ERROR]%COLOR_RESET% 未找到 requirements.txt
        pause
        exit /b 1
    )
)

REM 检查服务器状态
echo %COLOR_INFO%[INFO]%COLOR_RESET% 检查服务器状态...

REM 使用 PowerShell 检查端口
powershell -Command "Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -InformationLevel Quiet" >nul 2>&1
if %errorlevel% equ 0 (
    echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% 服务器运行中 (http://127.0.0.1:8000^)
) else (
    echo %COLOR_WARNING%[WARNING]%COLOR_RESET% 服务器未运行！请先启动服务器
)

REM 查找算法文件
echo %COLOR_INFO%[INFO]%COLOR_RESET% 查找算法文件...

set ALGORITHM_FILE=
set FOUND=0

if exist "bus_example.py" (
    set ALGORITHM_FILE=bus_example.py
    set FOUND=1
)

if !FOUND! equ 0 (
    if exist "bus_example_optimized.py" (
        set ALGORITHM_FILE=bus_example_optimized.py
        set FOUND=1
    )
)

if !FOUND! equ 0 (
    if exist "elevator_saga\client_examples\bus_example.py" (
        set ALGORITHM_FILE=elevator_saga\client_examples\bus_example.py
        set FOUND=1
    )
)

if !FOUND! equ 0 (
    if exist "client_examples\bus_example.py" (
        set ALGORITHM_FILE=client_examples\bus_example.py
        set FOUND=1
    )
)

if !FOUND! equ 0 (
    echo %COLOR_ERROR%[ERROR]%COLOR_RESET% 未找到算法文件！
    echo %COLOR_INFO%[INFO]%COLOR_RESET% 请确保以下文件之一存在：
    echo   - bus_example.py
    echo   - bus_example_optimized.py
    echo   - elevator_saga\client_examples\bus_example.py
    echo   - client_examples\bus_example.py
    pause
    exit /b 1
)

echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% 找到算法文件: !ALGORITHM_FILE!

echo.
echo 按任意键开始运行...
pause >nul
echo.

REM 运行算法
echo %COLOR_INFO%[INFO]%COLOR_RESET% 启动电梯调度算法...
echo.
echo %COLOR_SUCCESS%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%COLOR_RESET%
echo.

%PYTHON_CMD% !ALGORITHM_FILE!
set EXIT_CODE=!errorlevel!

echo.
echo %COLOR_SUCCESS%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%COLOR_RESET%
echo.

if !EXIT_CODE! equ 0 (
    echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% 算法执行完成
) else (
    echo %COLOR_ERROR%[ERROR]%COLOR_RESET% 算法执行出错 (退出码: !EXIT_CODE!^)
)

echo.
echo 按任意键退出...
pause >nul

exit /b !EXIT_CODE!
