# GitHub 推送指南

## 方法一: 使用 Git 命令 (最简单)

```bash
cd /Users/blobeats/Downloads/amz-keepa-mcp
git push -u origin main
```

按提示输入:
- Username: `itnewlife`
- Password: `你的 Personal Access Token`

> 注意: 密码处输入的是 Token，不是 GitHub 登录密码

## 方法二: 使用 GitHub CLI

```bash
# 1. 登录 (浏览器方式)
gh auth login

# 按提示选择:
# - GitHub.com
# - HTTPS
# - Yes
# - Login with a web browser

# 2. 推送
git push -u origin main
```

## 生成 Personal Access Token

1. 访问: https://github.com/settings/tokens/new
2. 输入名称: `amz-keepa-mcp`
3. 勾选: `repo` 权限
4. 点击 Generate token
5. 复制生成的 token

## 当前状态

- ✅ 本地提交: 2 commits
- ✅ 远程仓库: `https://github.com/itnewlife/amz-keepa-mcp.git`
- ✅ GitHub CLI: 已安装 v2.86.0
