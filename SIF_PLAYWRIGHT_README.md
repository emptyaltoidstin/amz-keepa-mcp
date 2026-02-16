# SIF Playwright MCP Server

> 使用 Playwright 替代 Selenium，更好的反检测能力和稳定性

## 🚀 为什么使用 Playwright?

| 特性 | Selenium | Playwright |
|------|----------|------------|
| 反检测能力 | 一般 | **优秀** |
| 自动等待 | 需手动 | **内置** |
| 异步支持 | 弱 | **原生** |
| 浏览器支持 | 多但复杂 | Chromium/Firefox/WebKit |
| 稳定性 | 一般 | **更好** |
| 执行速度 | 较慢 | **更快** |

## 📦 安装

### 1. 安装 Playwright

```bash
# 安装 Python 包
pip install playwright

# 安装浏览器 (首次运行必需)
playwright install

# 如果只安装 Chromium (更快)
playwright install chromium
```

### 2. 配置 Claude Desktop

编辑 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "sif-playwright-mcp": {
      "command": "python",
      "args": ["/Users/blobeats/Downloads/amz-keepa-mcp/sif_playwright_mcp.py"],
      "env": {
        "SIF_COOKIE_FILE": "/Users/blobeats/Downloads/amz-keepa-mcp/www.sif.com_json_1771165148823.json",
        "SIF_OUTPUT_DIR": "/Users/blobeats/Downloads/amz-keepa-mcp/cache/sif_reports",
        "SIF_DOWNLOAD_DIR": "/Users/blobeats/Downloads/amz-keepa-mcp/cache/sif_downloads",
        "SIF_HEADLESS": "false"
      }
    }
  }
}
```

## 🎯 使用示例

### 测试登录

```
测试 SIF Playwright 登录
```

### 分析 ASIN

```
用 Playwright 分析 B08N5WRWNW 的流量词
```

### 一键全维度分析

```
分析 B08N5WRWNW 的全维度数据
```

---

## 🔧 可用工具

| Tool | 功能 |
|------|------|
| `test_sif_login_playwright` | 测试登录状态 |
| `analyze_asin_sif_playwright` | 全维度分析（含下载） |

---

## 🆚 Playwright vs Selenium

### Selenium 的问题
1. 容易被检测（`navigator.webdriver` 标志）
2. 需要手动等待元素
3. 下载文件处理复杂
4. 页面重定向难处理

### Playwright 的改进
1. **Stealth 模式**: 自动隐藏自动化特征
2. **自动等待**: 智能等待元素出现
3. **下载监听**: 原生支持下载事件监听
4. **更稳定**: 更好的错误处理和重试机制

---

## 🧪 测试

```bash
cd /Users/blobeats/Downloads/amz-keepa-mcp
python test_playwright.py
```

---

## 📝 技术细节

### Stealth 注入

```python
# 隐藏 webdriver 标志
await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
""")
```

### 下载监听

```python
# 原生下载事件
page.on("download", lambda download: print(f"下载: {download.suggested_filename}"))
```

### 智能等待

```python
# 自动等待元素可见
await page.click('button:has-text("下载")')
```

---

## 🐛 故障排查

### 问题 1: `playwright install` 失败

**解决:**
```bash
# 使用国内镜像
PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium

# 或手动下载
# 访问 https://playwright.dev/docs/browsers
```

### 问题 2: 浏览器启动失败

**解决:**
```bash
# 检查系统依赖
playwright install-deps chromium
```

### 问题 3: Cookie 仍然无效

**原因:**
- SIF 可能检测到了更严格的验证
- 可能需要额外的请求头
- 可能需要特定的浏览器指纹

**解决:**
1. 尝试在 Playwright 中使用 `--disable-features=IsolateOrigins` 等参数
2. 使用更真实的 User-Agent
3. 添加更多的浏览器特征模拟

---

## 🎉 优势总结

Playwright 版本相比 Selenium：
- ✅ 更好的反检测能力
- ✅ 更快的执行速度
- ✅ 更简单的异步代码
- ✅ 更稳定的下载处理
- ✅ 更好的错误恢复

如果 Selenium 版本无法登录，强烈推荐尝试 Playwright 版本！
