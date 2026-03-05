# SIF Playwright MCP Server

> Use Playwright instead of Selenium for better anti-detection capabilities and stability

## 🚀 Why use Playwright?

| characteristic | Selenium | Playwright |
|------|----------|------------|
| Anti-detection capabilities | Average | **Excellent** |
| automatically wait | Need manual | **Built-in** |
| Asynchronous support | weak | **Native** |
| Browser support | Many but complex | Chromium/Firefox/WebKit |
| stability | Average | **better** |
| Execution speed | slower | **faster** |

## 📦 Installation

### 1. Install Playwright

```bash
# Install Python packages
pip install playwright

# Install browser (Required for first run)
playwright install

# If you only install Chromium (faster)
playwright install chromium
```

### 2. Configure Claude Desktop

Edit `claude_desktop_config.json`：

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

## 🎯 Usage examples

### Test login

```
Test SIF Playwright Login
```

### Analyze ASINs

```
Use Playwright to analyze the traffic words of B08N5WRWNW
```

### One-click full-dimensional analysis

```
Analyze the full-dimensional data of B08N5WRWNW
```

---

## 🔧 Available tools

| Tool | Function |
|------|------|
| `test_sif_login_playwright` | Test login status |
| `analyze_asin_sif_playwright` | Full-dimensional analysis (including download) |

---

## 🆚 Playwright vs Selenium

### Selenium problem
1. Easily detectable (`navigator.webdriver` logo)
2. Need to wait for elements manually
3. Downloading files is complicated
4. Page redirection is difficult to handle

### Playwright improvements
1. **Stealth mode**: Automatically hide automation features
2. **automatically wait**: Smart waiting for elements to appear
3. **Download monitoring**: Native support for download event monitoring
4. **more stable**: Better error handling and retry mechanism

---

## 🧪 Test

```bash
cd /Users/blobeats/Downloads/amz-keepa-mcp
python test_playwright.py
```

---

## 📝 Technical details

### Stealth injection

```python
# Hide webdriver flag
await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
""")
```

### Download monitoring

```python
# Native download event
page.on("download", lambda download: print(f"Download: {download.suggested_filename}"))
```

### Smart waiting

```python
# Automatically wait for element to be visible
await page.click('button:has-text("Download")')
```

---

## 🐛 Troubleshooting

### Question 1: `playwright install` failed

**solve:**
```bash
# Use domestic mirroring
PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium

# Or download manually
# access https://playwright.dev/docs/browsers
```

### Question 2: Browser startup failed

**solve:**
```bash
# Check system dependencies
playwright install-deps chromium
```

### Question 3: Cookie still invalid

**Reason:**
- SIF may have detected stricter validation
- Additional request headers may be required
- May require specific browser fingerprinting

**solve:**
1. Try using it in Playwright `--disable-features=IsolateOrigins` and other parameters
2. Use a more realistic User-Agent
3. Add more browser feature simulations

---

## 🎉 Summary of advantages

Playwright version compared to Selenium:
- ✅ Better anti-detection capabilities
- ✅ Faster execution speed
- ✅ Simpler asynchronous code
- ✅ More stable download processing
- ✅ Better error recovery

If the Selenium version fails to log in, it is highly recommended to try the Playwright version!
