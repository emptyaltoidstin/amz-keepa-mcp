# GitHub push guide

## Method one: Using Git commands (The simplest)

```bash
cd /Users/blobeats/Downloads/amz-keepa-mcp
git push -u origin main
```

Enter as prompted:
- Username: `itnewlife`
- Password: `Your Personal Access Token`

> Note: The password entered is Token, not the GitHub login password.

## Method two: Using the GitHub CLI

```bash
# 1. Login (Browser mode)
gh auth login

# Follow the prompts to select:
# - GitHub.com
# - HTTPS
# - Yes
# - Login with a web browser

# 2. Push
git push -u origin main
```

## Generate Personal Access Token

1. Visit: https://github.com/settings/tokens/new
2. Enter the name: `amz-keepa-mcp`
3. Check: `repo` Permissions
4. Click Generate token
5. Copy the generated token

## Current status

- ✅ Submit locally: 2 commits
- ✅Remote warehouse: `https://github.com/itnewlife/amz-keepa-mcp.git`
- ✅ GitHub CLI: v2.86.0 installed
