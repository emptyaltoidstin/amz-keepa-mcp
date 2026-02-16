#!/bin/bash
# Amz-Keepa-MCP 快速启动脚本
# 用法: ./quickstart.sh <ASIN>

set -e

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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查参数
if [ $# -eq 0 ]; then
    echo "Usage: ./quickstart.sh <ASIN>"
    echo "Example: ./quickstart.sh B0F6B5R47Q"
    exit 1
fi

ASIN=$1

# 打印欢迎信息
echo "========================================"
echo "  Amz-Keepa-MCP v3.0 - 快速启动"
echo "========================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 not found. Please install Python 3.11+"
    exit 1
fi

print_info "Python version: $(python3 --version)"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
print_info "Activating virtual environment..."
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.deps_installed" ]; then
    print_info "Installing dependencies..."
    pip install -q -r requirements.txt
    touch venv/.deps_installed
    print_success "Dependencies installed"
fi

# 检查环境变量
if [ -z "$KEEPA_KEY" ]; then
    if [ -f ".env" ]; then
        export $(cat .env | xargs)
    fi
fi

if [ -z "$KEEPA_KEY" ]; then
    print_error "KEEPA_KEY not set!"
    print_info "Please set it in .env file or environment variable"
    exit 1
fi

print_success "Environment check passed"
echo ""

# 执行标准流程
print_info "Starting standard workflow for ASIN: $ASIN"
echo "========================================"
python3 generate_report.py "$ASIN"

# 检查报告是否生成
REPORT_PATH="cache/reports/${ASIN}_ALLINONE_INTERACTIVE.html"
if [ -f "$REPORT_PATH" ]; then
    echo ""
    print_success "Report generated successfully!"
    echo ""
    echo "📁 Report location:"
    echo "   $REPORT_PATH"
    echo ""
    echo "🚀 To open the report:"
    echo "   open $REPORT_PATH"
    echo ""
    echo "💡 Next steps:"
    echo "   1. Open the interactive report in your browser"
    echo "   2. Enter your 1688 procurement price"
    echo "   3. View complete profit analysis"
else
    print_error "Report generation may have failed"
    exit 1
fi
