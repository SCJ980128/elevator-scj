#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 清屏
clear

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  电梯调度算法测试与对比系统${NC}"
echo -e "${BLUE}  Elevator Scheduling Algorithm Test System${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 检查Python是否安装
echo -e "${YELLOW}[1/3] 检查Python环境...${NC}"

if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ 错误: 未检测到Python安装${NC}"
        echo ""
        echo "请先安装Python 3.7或更高版本"
        echo ""
        echo "Ubuntu/Debian: sudo apt-get install python3"
        echo "CentOS/RHEL:   sudo yum install python3"
        echo "macOS:         brew install python3"
        echo ""
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 显示Python版本
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}✅ 检测到 $PYTHON_VERSION${NC}"
echo ""

# 检查Python版本是否满足要求 (>= 3.7)
VERSION_CHECK=$($PYTHON_CMD -c "import sys; print(sys.version_info >= (3, 7))")
if [ "$VERSION_CHECK" != "True" ]; then
    echo -e "${RED}❌ 错误: Python版本过低，需要3.7或更高版本${NC}"
    echo ""
    exit 1
fi

# 检查tkinter是否可用
echo -e "${YELLOW}[2/3] 检查GUI库...${NC}"
if ! $PYTHON_CMD -c "import tkinter" &> /dev/null; then
    echo -e "${RED}❌ 错误: tkinter未安装${NC}"
    echo ""
    echo "请安装tkinter:"
    echo "Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "CentOS/RHEL:   sudo yum install python3-tkinter"
    echo "macOS:         通常已随Python安装"
    echo ""
    exit 1
fi
echo -e "${GREEN}✅ GUI库已就绪${NC}"
echo ""

# 检查elevator_GUI.py是否存在
if [ ! -f "elevator_GUI.py" ]; then
    echo -e "${RED}❌ 错误: 找不到 elevator_GUI.py 文件${NC}"
    echo ""
    echo "请确保启动脚本与elevator_GUI.py在同一目录下"
    echo "当前目录: $(pwd)"
    echo ""
    exit 1
fi

# 运行程序
echo -e "${YELLOW}[3/3] 启动程序...${NC}"
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  程序正在启动，请稍候...${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

$PYTHON_CMD elevator_GUI.py

# 检查退出状态
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}❌ 程序异常退出 (错误码: $EXIT_CODE)${NC}"
    echo -e "${RED}============================================${NC}"
    echo ""
    exit $EXIT_CODE
fi

exit 0
