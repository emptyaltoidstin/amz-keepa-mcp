#!/bin/bash
# Amz-Keepa-MCP 启动脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "✅ 激活虚拟环境..."
    source venv/bin/activate
else
    echo "⚠️ 虚拟环境不存在，使用系统 Python"
fi

# 检查环境变量
if [ -z "$KEEPA_KEY" ]; then
    if [ -f ".env" ]; then
        echo "✅ 加载 .env 文件..."
        export $(grep -v '^#' .env | xargs)
    else
        echo "❌ 错误: KEEPA_KEY 未设置"
        echo "请设置环境变量或创建 .env 文件"
        exit 1
    fi
fi

# 检查依赖
echo "✅ 检查依赖..."
python -c "import mcp, keepa, pandas, numpy, matplotlib" 2>/dev/null || {
    echo "⚠️ 依赖未安装，正在安装..."
    pip install -r requirements.txt
}

# 启动服务器
echo "🚀 启动 Amz-Keepa-MCP Server..."
echo "配置文件: claude_desktop_config.json"
echo ""
python server.py
