#!/bin/bash
# =============================================================================
# 电梯调度算法启动脚本 - Linux 版本
# =============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印标题
print_header() {
    echo -e "${GREEN}"
    echo "=============================================="
    echo "    电梯调度算法启动器 (Linux)"
    echo "=============================================="
    echo -e "${NC}"
}

# 检查 Python 是否安装
check_python() {
    print_info "检查 Python 环境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version)
        print_success "找到 Python: $PYTHON_VERSION"
        return 0
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(python --version)
        print_success "找到 Python: $PYTHON_VERSION"
        return 0
    else
        print_error "未找到 Python！请先安装 Python 3.7+"
        return 1
    fi
}

# 检查虚拟环境
check_venv() {
    print_info "检查虚拟环境..."
    
    # 常见的虚拟环境路径
    VENV_PATHS=("venv" "env" ".venv" "../venv")
    
    for venv_path in "${VENV_PATHS[@]}"; do
        if [ -d "$venv_path" ]; then
            print_info "找到虚拟环境: $venv_path"
            source "$venv_path/bin/activate"
            print_success "虚拟环境已激活"
            return 0
        fi
    done
    
    print_warning "未找到虚拟环境，使用系统 Python"
    return 0
}

# 检查依赖包
check_dependencies() {
    print_info "检查依赖包..."
    
    $PYTHON_CMD -c "import elevator_saga" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_success "elevator_saga 包已安装"
        return 0
    else
        print_error "elevator_saga 包未安装！"
        print_info "尝试安装依赖..."
        
        if [ -f "requirements.txt" ]; then
            $PYTHON_CMD -m pip install -r requirements.txt
        else
            print_error "未找到 requirements.txt"
            return 1
        fi
    fi
}

# 查找算法文件
find_algorithm_file() {
    print_info "查找算法文件..."
    
    # 可能的文件路径
    POSSIBLE_PATHS=(
        "bus_example.py"
        "bus_example_optimized.py"
        "elevator_saga/client_examples/bus_example.py"
        "client_examples/bus_example.py"
        "./bus_example.py"
    )
    
    for path in "${POSSIBLE_PATHS[@]}"; do
        if [ -f "$path" ]; then
            ALGORITHM_FILE="$path"
            print_success "找到算法文件: $ALGORITHM_FILE"
            return 0
        fi
    done
    
    print_error "未找到算法文件！"
    print_info "请确保以下文件之一存在："
    for path in "${POSSIBLE_PATHS[@]}"; do
        echo "  - $path"
    done
    return 1
}

# 运行算法
run_algorithm() {
    print_info "启动电梯调度算法..."
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    $PYTHON_CMD "$ALGORITHM_FILE"
}

# 主函数
main() {
    print_header
    
    # 检查环境
    check_python || exit 1
    check_venv
    check_dependencies || exit 1
    
    
    echo ""
    
    # 查找并运行算法
    find_algorithm_file || exit 1
    
    echo ""
    
    echo ""
    
    run_algorithm
    
    echo ""
    
}

# 运行主函数
main
