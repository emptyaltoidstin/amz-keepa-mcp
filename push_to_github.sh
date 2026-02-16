#!/bin/bash
# GitHub 推送脚本

REPO_URL="https://github.com/itnewlife/amz-keepa-mcp.git"

echo "═══════════════════════════════════════════════════════════"
echo "  🚀 推送到 GitHub"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "仓库: $REPO_URL"
echo ""

# 检查 gh 是否可用
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI 已安装"
    
    # 检查是否已登录
    if gh auth status &> /dev/null; then
        echo "✅ 已登录 GitHub"
        echo ""
        echo "正在推送..."
        git push -u origin main
    else
        echo "⚠️  未登录 GitHub"
        echo ""
        echo "请选择认证方式:"
        echo ""
        echo "方式 1: 浏览器登录 (推荐)"
        echo "  gh auth login"
        echo ""
        echo "方式 2: 使用 Token"
        echo "  export GITHUB_TOKEN=your_token"
        echo "  gh auth login --with-token"
        echo ""
        echo "方式 3: 直接使用 git + Personal Access Token"
        echo "  git push -u origin main"
        echo "  # 输入用户名: itnewlife"
        echo "  # 输入密码: your_personal_access_token"
        echo ""
    fi
else
    echo "❌ GitHub CLI 未安装"
    echo ""
    echo "使用 git 直接推送:"
    echo "  git push -u origin main"
    echo ""
    echo "提示: 密码处输入 Personal Access Token，不是登录密码"
fi
