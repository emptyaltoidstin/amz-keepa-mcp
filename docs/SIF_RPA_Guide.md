# SIF 关键词工具 RPA 自动化指南

> 基于 Chrome DevTools 抓取的官方页面结构整理
> 最后更新: 2026-02-15
> 适用版本: SIF 网页版 + 插件版

---

## 目录

1. [系统概述](#系统概述)
2. [认证与登录](#认证与登录)
3. [核心功能页面 URL](#核心功能页面-url)
4. [RPA 操作指南](#rpa-操作指南)
5. [数据提取规范](#数据提取规范)
6. [反爬策略与限制](#反爬策略与限制)
7. [自动化脚本示例](#自动化脚本示例)
8. [常见问题](#常见问题)

---

## 系统概述

### 产品定位

SIF 是专注于亚马逊站内流量分析的关键词运营工具，提供：
- 销量查询（精确到变体/属性级别）
- 流量结构分析
- 关键词反查
- 广告架构透视
- 竞价查询
- 时光机（历史数据追踪）
- 拓词与相关性筛查

### 支持站点

| 站点 | 代码 | 数据开始时间 |
|------|------|-------------|
| 美国 | US | 2021-11 |
| 德国 | DE | 2021-11 |
| 英国 | UK | 2021-11 |
| 日本 | JP | 2021-11 |
| 加拿大 | CA | 2021-11 |
| 法国 | FR | 2021-11 |
| 西班牙 | ES | 2021-11 |
| 意大利 | IT | 2021-11 |
| 澳大利亚 | AU | 2025-03-23 |
| 墨西哥 | MX | 2025-03-23 |
| 巴西 | BR | 2025-03-23 |
| 阿联酋 | AE | 2025-03-23 |

### 版本功能差异

| 功能 | 基础版 | 旗舰版 |
|------|--------|--------|
| 查销量 | ✅ | ✅ |
| 查流量结构 | ✅ | ✅ |
| 反查流量词 | ✅ | ✅ |
| 查竞价 | 2次/天 | 无限 |
| 广告透视仪 | ❌ | ✅ |
| 时光机 | ❌ | ✅ |
| 多竞品拓词 | 50 ASIN/次 | 100 ASIN/次 |
| 以词拓词历史 | 仅1个月 | 所有历史 |
| 每日坑位监控 | 50词 | 200词 |
| 小时排名监控 | 1元/周 | 1元/周 |

---

## 认证与登录

### 登录页面

```
URL: https://www.sif.com/Login
Method: POST
Content-Type: application/json
```

### 登录流程

**Step 1: 访问登录页**
```python
# Selenium 示例
driver.get("https://www.sif.com/Login")

# 等待登录表单加载
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.ID, "username")))
```

**Step 2: 输入凭证**
```python
# 定位输入框
username_input = driver.find_element(By.ID, "username")
password_input = driver.find_element(By.ID, "password")

# 输入凭证
username_input.send_keys("your_username")
password_input.send_keys("your_password")
```

**Step 3: 点击登录**
```python
# 方式1: 点击登录按钮
login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
login_button.click()

# 方式2: 按回车键
password_input.send_keys(Keys.RETURN)
```

**Step 4: 验证登录成功**
```python
# 检查是否跳转到功能页面或出现用户头像
try:
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "user-avatar")))
    print("登录成功")
except:
    # 检查错误信息
    error_msg = driver.find_elements(By.CLASS_NAME, "error-message")
    if error_msg:
        print(f"登录失败: {error_msg[0].text}")
```

### Token/Session 管理

```python
# 获取 Cookie
cookies = driver.get_cookies()

# 保存 Cookie 供后续使用
import json
with open('sif_cookies.json', 'w') as f:
    json.dump(cookies, f)

# 后续会话加载 Cookie
driver.get("https://www.sif.com")
with open('sif_cookies.json', 'r') as f:
    cookies = json.load(f)
for cookie in cookies:
    driver.add_cookie(cookie)
driver.refresh()
```

### 登录状态检查

```python
def check_login_status(driver):
    """检查当前是否已登录"""
    driver.get("https://www.sif.com")
    time.sleep(2)
    
    # 检查是否存在登录按钮
    login_buttons = driver.find_elements(By.LINK_TEXT, "登录")
    
    if login_buttons:
        return False
    
    # 检查是否存在用户相关元素
    user_elements = driver.find_elements(By.CLASS_NAME, "user-menu")
    return len(user_elements) > 0
```

---

## 核心功能页面 URL

### 1. 查销量 (Sales)

```
URL Pattern: https://www.sif.com/Sales?country={country}
Parameters:
  - country: US, UK, DE, JP, CA, FR, ES, IT, AU, MX, BR, AE
```

**页面操作:**

| 操作 | 元素定位 | 说明 |
|------|----------|------|
| ASIN 查询 | `input[placeholder*="ASIN"]` | 输入 ASIN，多 ASIN 用逗号分隔(最多10个) |
| 关键词查询 | `input[placeholder*="关键词"]` | 输入关键词查询该词下产品销量 |
| 站点切换 | `select[name="country"]` | 切换不同亚马逊站点 |
| 查询按钮 | `button:contains("查询")` | 执行查询 |
| 下载按钮 | `button:contains("下载")` | 下载 Excel/CSV 数据 |

**数据字段:**
- ASIN
- 变体属性 (Color/Size)
- 月销量 (格式: 50+ 代表 50-99)
- 月销量趋势
- 评论数
- 评分星级
- 价格

---

### 2. 查流量结构 (Traffic Structure)

```
URL Pattern: https://www.sif.com/TrafficStructure?country={country}&asin={asin}
```

**页面操作:**

| 操作 | 元素定位 | 说明 |
|------|----------|------|
| ASIN 输入 | `input[name="asin"]` | 输入要查询的 ASIN |
| 时间范围 | `select[name="timeRange"]` | 7天/30天/历史所有 |
| 变体筛选 | `.variant-selector` | 选择特定变体 |
| 属性筛选 | `.attribute-selector` | 按 Color/Size 筛选 |
| 流量类型筛选 | `.traffic-type-filter` | 自然/广告/推荐/关联 |

**流量类型说明:**
| 类型 | 说明 |
|------|------|
| 自然搜索 | Organic Search |
| PPC广告 | Sponsored Products |
| Deal活动 | Deals |
| 搜索推荐 | Search Recommendation |
| 关联流量 | Related Products |

---

### 3. 反查流量词 (Reverse Search)

```
URL Pattern: https://www.sif.com/ReverseSearch?country={country}&asin={asin}
```

**页面操作:**

| 操作 | 元素定位 | 说明 |
|------|----------|------|
| ASIN 输入 | `input[name="asin"]` | 输入 ASIN |
| 对比模式 | `button[data-mode="compare"]` | 多 ASIN 对比 |
| 时间选择 | `select[name="dateRange"]` | 7天/30天/历史 |
| 父体查询 | `checkbox[name="parentAsin"]` | 查询父体所有流量词 |
| 筛选排序 | `.filter-panel select` | 按流量占比/排名筛选 |

**数据字段:**
- 关键词
- 流量占比 (%)
- 搜索排名
- 曝光位置
- 自然/广告流量分布
- 周搜索量 (ABA数据)

---

### 4. 广告透视仪 (Ad Intelligence) ⭐ 旗舰版

```
URL Pattern: https://www.sif.com/AdIntelligence?country={country}&asin={asin}
```

**页面操作:**

| 操作 | 元素定位 | 说明 |
|------|----------|------|
| ASIN 输入 | `input[name="asin"]` | 输入竞品 ASIN |
| 广告活动筛选 | `select[name="campaignId"]` | 筛选特定广告活动 |
| 投放变体筛选 | `select[name="targetAsin"]` | 查看特定变体广告 |
| 广告词搜索 | `input[name="keyword"]` | 搜索特定广告词 |
| 时间范围 | `select[name="timeRange"]` | 选择分析时间段 |

**核心数据:**
- 广告活动 ID
- 投放小组 (Ad Group)
- 投放词和匹配模式
- 流量占比
- ASIN 定位广告数据

---

### 5. 查竞价 (Bid Query)

```
URL Pattern: https://www.sif.com/BidQuery?country={country}&keyword={keyword}
```

**页面操作:**

| 操作 | 元素定位 | 说明 |
|------|----------|------|
| 关键词输入 | `input[name="keyword"]` | 单个/批量输入关键词 |
| 广告类型切换 | `.ad-type-tabs` | SP / SB 切换 |
| 匹配模式选择 | `select[name="matchType"]` | Exact/Phrase/Broad |
| 时间选择 | `select[name="dateRange"]` | 周/月数据 |
| 拓展查询 | `button[data-action="expand"]` | 拓展相关词竞价 |
| 下载按钮 | `button:contains("下载")` | 导出竞价数据 |

**数据字段:**
- 关键词
- 建议竞价 (SP/SB)
- ABA Top3 集中度
- Top3 产品主图
- 搜索量趋势

---

### 6. 时光机 (Time Machine) ⭐ 旗舰版

```
URL Pattern: https://www.sif.com/TimeMachine?country={country}&asin={asin}
```

**子功能:**

#### 6.1 流量时光机
```
URL: https://www.sif.com/TimeMachine/Traffic?asin={asin}
```
- 竞品运营打法复现
- 流量变化诊断

#### 6.2 产品时光机
```
URL: https://www.sif.com/TimeMachine/Product?asin={asin}
```
- 季节性产品追踪
- 节日产品趋势

**页面操作:**

| 操作 | 元素定位 | 说明 |
|------|----------|------|
| ASIN 输入 | `input[name="asin"]` | 输入 ASIN |
| 时间轴拖动 | `.timeline-slider` | 选择历史时间点 |
| 对比模式 | `button[data-mode="compare"]` | 对比不同时间点 |
| 变更筛选 | `.change-filter` | 筛选特定类型变更 |

**追踪变更类型:**
- Coupon 价格变化
- Prime 价格变化
- 主图变更
- 标题变更
- 广告活动变更

---

### 7. 拓词 & 筛查 (Keyword Expansion)

```
URL Pattern: https://www.sif.com/KeywordExpansion
```

**子功能 URL:**

| 功能 | URL |
|------|-----|
| 多竞品拓词 | `/KeywordExpansion/Competitor` |
| 以词拓词 | `/KeywordExpansion/Keyword` |
| 细分品类拓词 | `/KeywordExpansion/Category` |
| 批量导入筛查 | `/KeywordExpansion/Import` |

**页面操作:**

| 操作 | 元素定位 | 说明 |
|------|----------|------|
| ASIN 输入 | `textarea[name="asins"]` | 批量输入 ASIN(50-100个) |
| 相关性阈值 | `input[name="relevanceThreshold"]` | 设置相关性判定标准 |
| 开始拓词 | `button:contains("开始拓词")` | 执行拓词 |
| 自动筛查 | `button:contains("自动筛查")` | AI 自动判断相关性 |
| 手动标记 | `.relevance-toggle` | 手动标记相关/不相关 |
| 保存词库 | `button:contains("保存到词库")` | 保存筛选结果 |
| 高级筛选 | `.advanced-filter-panel` | 多条件组合筛选 |

**筛查指标:**
- 相关性评分
- 自然位前4占位率
- 流量占比
- 搜索量

---

### 8. 选词 (Keyword Selection)

```
URL Pattern: https://www.sif.com/KeywordSelection
```

**子功能:**

| 功能 | URL |
|------|-----|
| 点击转化率 | `/KeywordSelection/ConversionRate` |
| 竞品数量 | `/KeywordSelection/CompetitorCount` |
| 流量位竞争格局 | `/KeywordSelection/CompetitionLandscape` |

**页面操作:**

| 操作 | 元素定位 | 说明 |
|------|----------|------|
| 关键词输入 | `textarea[name="keywords"]` | 批量输入关键词 |
| 时间范围 | `select[name="timeRange"]` | 选择数据时间范围 |
| 转化率排序 | `.sort-by-conversion` | 按转化率排序 |
| ACOS 筛选 | `input[name="acosRange"]` | 筛选 ACOS 范围 |
| 下载报告 | `button:contains("下载")` | 导出分析数据 |

**数据字段:**
- 关键词转化率
- ACOS
- CPA (广告订单平均推广成本)
- 建议竞价
- 竞品数量
- 流量位竞争格局

---

### 9. 查坑位/推排名 (Rank Tracking)

```
URL Pattern: https://www.sif.com/RankTracking
```

**子功能:**

| 功能 | URL | 说明 |
|------|-----|------|
| 坑位快照 | `/RankTracking/Snapshot` | 快速查看关键词排名 |
| 每日排名 | `/RankTracking/Daily` | 每日排名监控 |
| 小时排名 | `/RankTracking/Hourly` | 小时级排名监控(付费) |

**页面操作:**

| 操作 | 元素定位 | 说明 |
|------|----------|------|
| ASIN 输入 | `input[name="asin"]` | 输入监控 ASIN |
| 关键词输入 | `input[name="keyword"]` | 输入监控关键词 |
| 添加监控 | `button:contains("添加监控")` | 添加监控词 |
| 监控列表 | `.tracking-list` | 查看所有监控词 |
| 排名趋势 | `.rank-chart` | 查看排名变化趋势 |
| 删除监控 | `.remove-tracking-btn` | 删除监控词 |

**限制说明:**
- 基础版: 50词/日
- 旗舰版: 200词/日
- 小时排名: 1元/周/词

---

### 10. 产品库/词库 (Library)

```
URL Pattern: https://www.sif.com/Library
```

**子功能 URL:**

| 功能 | URL |
|------|-----|
| 产品库 | `/Library/Products` |
| 词库 | `/Library/Keywords` |

**页面操作:**

| 操作 | 元素定位 | 说明 |
|------|----------|------|
| 添加产品 | `button:contains("添加产品")` | 添加关注产品 |
| 添加词库 | `button:contains("新建词库")` | 创建新词库 |
| 词频统计 | `.word-frequency-btn` | 查看词频统计 |
| 批量操作 | `.batch-action-dropdown` | 批量导入/导出 |

---

## RPA 操作指南

### 通用等待策略

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class SIFAutomation:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
    
    def wait_for_loading(self):
        """等待加载完成"""
        try:
            # 等待加载动画消失
            self.wait.until(EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, ".loading-spinner, .ant-spin")
            ))
        except TimeoutException:
            pass
    
    def wait_for_data_table(self):
        """等待数据表格加载"""
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".data-table, .ant-table")
        ))
```

### 查销量自动化

```python
def query_sales_by_asin(driver, asins, country="US"):
    """
    通过 ASIN 查询销量
    
    Args:
        driver: Selenium WebDriver
        asins: ASIN 列表 (最多10个)
        country: 站点代码
    """
    # 构建 URL
    asin_str = ",".join(asins[:10])  # 最多10个
    url = f"https://www.sif.com/Sales?country={country}&asin={asin_str}"
    driver.get(url)
    
    # 等待加载
    time.sleep(3)
    
    # 检查是否需要点击查询按钮
    query_buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'查询')]")
    if query_buttons:
        query_buttons[0].click()
        time.sleep(5)  # 等待数据加载
    
    # 提取数据
    data = extract_sales_data(driver)
    return data

def extract_sales_data(driver):
    """提取销量数据"""
    data = []
    
    # 定位表格行
    rows = driver.find_elements(By.CSS_SELECTOR, ".data-table tbody tr")
    
    for row in rows:
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 5:
                record = {
                    "asin": cells[0].text,
                    "variant": cells[1].text,
                    "monthly_sales": cells[2].text,
                    "reviews": cells[3].text,
                    "rating": cells[4].text,
                    "price": cells[5].text if len(cells) > 5 else None
                }
                data.append(record)
        except Exception as e:
            print(f"解析行数据出错: {e}")
    
    return data
```

### 反查流量词自动化

```python
def reverse_search_keywords(driver, asin, country="US", date_range="30"):
    """
    反查 ASIN 流量词
    
    Args:
        driver: Selenium WebDriver
        asin: 目标 ASIN
        country: 站点
        date_range: 时间范围 (7/30/all)
    """
    url = f"https://www.sif.com/ReverseSearch?country={country}&asin={asin}&range={date_range}"
    driver.get(url)
    
    # 等待数据加载
    time.sleep(5)
    
    # 提取关键词数据
    keywords = extract_keyword_data(driver)
    return keywords

def extract_keyword_data(driver):
    """提取关键词数据"""
    keywords = []
    
    # 滚动加载所有数据
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    # 提取表格数据
    rows = driver.find_elements(By.CSS_SELECTOR, ".keyword-table tbody tr")
    
    for row in rows:
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:
                keyword_data = {
                    "keyword": cells[0].text,
                    "traffic_share": cells[1].text,
                    "search_rank": cells[2].text,
                    "position": cells[3].text,
                    "organic_traffic": cells[4].text if len(cells) > 4 else None,
                    "ad_traffic": cells[5].text if len(cells) > 5 else None,
                    "search_volume": cells[6].text if len(cells) > 6 else None
                }
                keywords.append(keyword_data)
        except Exception as e:
            continue
    
    return keywords
```

### 广告透视仪自动化 (旗舰版)

```python
def analyze_ad_intelligence(driver, asin, country="US"):
    """
    分析广告架构
    
    Args:
        driver: Selenium WebDriver
        asin: 竞品 ASIN
        country: 站点
    """
    url = f"https://www.sif.com/AdIntelligence?country={country}&asin={asin}"
    driver.get(url)
    
    time.sleep(5)  # 等待广告数据加载
    
    # 检查是否有权限
    if "upgrade" in driver.page_source.lower() or "旗舰版" in driver.page_source:
        print("需要旗舰版权限")
        return None
    
    ad_data = extract_ad_data(driver)
    return ad_data

def extract_ad_data(driver):
    """提取广告数据"""
    campaigns = []
    
    # 获取广告活动列表
    campaign_elements = driver.find_elements(By.CSS_SELECTOR, ".campaign-item")
    
    for campaign in campaign_elements:
        try:
            campaign_id = campaign.find_element(By.CSS_SELECTOR, ".campaign-id").text
            keywords = []
            
            # 获取该活动下的关键词
            keyword_rows = campaign.find_elements(By.CSS_SELECTOR, ".keyword-row")
            for row in keyword_rows:
                keyword_data = {
                    "keyword": row.find_element(By.CSS_SELECTOR, ".keyword-text").text,
                    "match_type": row.find_element(By.CSS_SELECTOR, ".match-type").text,
                    "traffic_share": row.find_element(By.CSS_SELECTOR, ".traffic-share").text,
                    "ad_group": row.find_element(By.CSS_SELECTOR, ".ad-group").text
                }
                keywords.append(keyword_data)
            
            campaigns.append({
                "campaign_id": campaign_id,
                "keywords": keywords
            })
        except Exception as e:
            continue
    
    return campaigns
```

### 查竞价自动化

```python
def query_keyword_bids(driver, keywords, country="US", ad_type="SP"):
    """
    批量查询关键词竞价
    
    Args:
        driver: Selenium WebDriver
        keywords: 关键词列表
        country: 站点
        ad_type: SP 或 SB
    """
    url = f"https://www.sif.com/BidQuery?country={country}"
    driver.get(url)
    
    # 输入关键词
    keyword_input = driver.find_element(By.CSS_SELECTOR, "textarea[name='keywords']")
    keyword_input.clear()
    keyword_input.send_keys("\n".join(keywords))
    
    # 选择广告类型
    ad_type_tab = driver.find_element(By.CSS_SELECTOR, f".ad-type-tab[data-type='{ad_type}']")
    ad_type_tab.click()
    
    # 点击查询
    query_btn = driver.find_element(By.XPATH, "//button[contains(text(),'查询')]")
    query_btn.click()
    
    time.sleep(5)  # 等待结果
    
    # 提取竞价数据
    bid_data = extract_bid_data(driver)
    return bid_data

def extract_bid_data(driver):
    """提取竞价数据"""
    bids = []
    
    rows = driver.find_elements(By.CSS_SELECTOR, ".bid-table tbody tr")
    for row in rows:
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            bid_info = {
                "keyword": cells[0].text,
                "suggested_bid": cells[1].text,
                "bid_range": cells[2].text,
                "top3_concentration": cells[3].text,
                "search_volume": cells[4].text,
                "trend": cells[5].text if len(cells) > 5 else None
            }
            bids.append(bid_info)
        except Exception as e:
            continue
    
    return bids
```

### 批量下载数据

```python
def download_data(driver, file_name=None):
    """
    触发数据下载
    
    Args:
        driver: Selenium WebDriver
        file_name: 自定义文件名 (可选)
    """
    # 找到下载按钮
    download_btn = driver.find_element(By.XPATH, "//button[contains(text(),'下载') or contains(@class, 'download')]")
    download_btn.click()
    
    # 如果有文件名输入框
    try:
        filename_input = driver.find_element(By.CSS_SELECTOR, "input[name='filename']")
        if file_name:
            filename_input.clear()
            filename_input.send_keys(file_name)
        
        # 确认下载
        confirm_btn = driver.find_element(By.XPATH, "//button[contains(text(),'确认') or contains(text(),'下载')]")
        confirm_btn.click()
    except:
        pass
    
    # 等待下载完成
    time.sleep(3)
```

---

## 数据提取规范

### 数据字段映射表

| 功能 | 字段名 | 数据类型 | 示例 |
|------|--------|----------|------|
| 查销量 | asin | string | B08N5WRWNW |
| 查销量 | monthly_sales | string | 200+ |
| 查销量 | variant_color | string | Black |
| 查销量 | variant_size | string | Large |
| 反查流量词 | keyword | string | wireless mouse |
| 反查流量词 | traffic_share | string | 15.2% |
| 反查流量词 | search_rank | int | 3 |
| 反查流量词 | organic_share | string | 80% |
| 反查流量词 | ad_share | string | 20% |
| 广告透视仪 | campaign_id | string | 123456789 |
| 广告透视仪 | ad_group | string | Group-A |
| 广告透视仪 | match_type | string | EXACT |
| 查竞价 | suggested_bid | float | 2.5 |
| 查竞价 | bid_range | string | $1.5-$3.0 |
| 查竞价 | acos | float | 15.2 |

### 数据清洗规则

```python
def clean_sales_number(sales_str):
    """
    清洗销量数据
    50+ -> 50-99 范围
    """
    if not sales_str or sales_str == "-":
        return None
    
    sales_str = sales_str.strip()
    
    if "+" in sales_str:
        base = int(sales_str.replace("+", ""))
        return {
            "min": base,
            "max": base * 2 - 1,
            "display": sales_str
        }
    elif "-" in sales_str:
        parts = sales_str.split("-")
        return {
            "min": int(parts[0]),
            "max": int(parts[1]),
            "display": sales_str
        }
    else:
        try:
            val = int(sales_str)
            return {"min": val, "max": val, "display": sales_str}
        except:
            return None

def clean_percentage(pct_str):
    """清洗百分比数据"""
    if not pct_str:
        return None
    
    pct_str = pct_str.replace("%", "").strip()
    try:
        return float(pct_str)
    except:
        return None
```

---

## 反爬策略与限制

### 已知限制

| 限制类型 | 限制值 | 说明 |
|----------|--------|------|
| 登录会话 | 需保持活跃 | 长时间不操作会自动退出 |
| 查询频率 | 未公开 | 建议单 IP 每秒不超过 1 次查询 |
| 多 ASIN 查询 | 10个/次 | 销量查询最多同时查 10 个 ASIN |
| 拓词 ASIN 数 | 基础50/旗舰100 | 多竞品拓词限制 |
| 坑位监控 | 基础50/旗舰200 | 每日监控词数限制 |
| 竞价查询 | 基础2次/旗舰无限 | 查竞价功能限制 |

### 反爬建议

```python
import random
import time

class AntiDetection:
    @staticmethod
    def random_delay(min_sec=2, max_sec=5):
        """随机延迟"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    @staticmethod
    def human_like_scroll(driver):
        """模拟人类滚动"""
        for i in range(3):
            driver.execute_script(
                f"window.scrollTo(0, {random.randint(300, 700) * (i+1)});"
            )
            time.sleep(random.uniform(0.5, 1.5))
    
    @staticmethod
    def add_human_behavior(driver):
        """添加人类行为特征"""
        # 随机鼠标移动
        actions = ActionChains(driver)
        actions.move_by_offset(random.randint(-50, 50), random.randint(-50, 50))
        actions.perform()
```

### 安全建议

1. **使用企业版账号**: 企业版有更高并发和更宽松限制
2. **控制查询频率**: 避免短时间内大量查询
3. **使用代理 IP**: 多账号/多 IP 分散请求
4. **监控账号状态**: 定期检查是否被限制

---

## 自动化脚本示例

### 完整工作流: 竞品分析

```python
#!/usr/bin/env python3
"""
SIF 竞品分析自动化脚本
功能: 查询竞品销量 -> 反查流量词 -> 分析广告架构 -> 导出报告
"""

import json
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SIFCompetitorAnalyzer:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 30)
        self.results = {}
    
    def login(self):
        """登录 SIF"""
        self.driver.get("https://www.sif.com/Login")
        
        # 输入凭证
        self.driver.find_element(By.ID, "username").send_keys(self.username)
        self.driver.find_element(By.ID, "password").send_keys(self.password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # 等待登录成功
        time.sleep(3)
        print("登录成功")
    
    def analyze_competitor(self, asin, country="US"):
        """
        完整竞品分析流程
        
        Args:
            asin: 竞品 ASIN
            country: 站点
        """
        print(f"开始分析 ASIN: {asin}")
        
        # Step 1: 查销量
        print("  查询销量...")
        sales_data = self._query_sales(asin, country)
        
        # Step 2: 查流量结构
        print("  查询流量结构...")
        traffic_data = self._query_traffic_structure(asin, country)
        
        # Step 3: 反查流量词
        print("  反查流量词...")
        keywords_data = self._reverse_search_keywords(asin, country)
        
        # Step 4: 广告透视 (如果可用)
        print("  分析广告架构...")
        ad_data = self._analyze_ad_intelligence(asin, country)
        
        # 汇总结果
        self.results[asin] = {
            "timestamp": datetime.now().isoformat(),
            "country": country,
            "sales": sales_data,
            "traffic_structure": traffic_data,
            "keywords": keywords_data,
            "ads": ad_data
        }
        
        print(f"分析完成: {asin}")
        return self.results[asin]
    
    def _query_sales(self, asin, country):
        """查询销量"""
        url = f"https://www.sif.com/Sales?country={country}&asin={asin}"
        self.driver.get(url)
        time.sleep(4)
        
        # 提取数据
        data = []
        rows = self.driver.find_elements(By.CSS_SELECTOR, ".data-table tbody tr")
        for row in rows[:5]:  # 取前5个变体
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:
                data.append({
                    "variant": cells[1].text,
                    "monthly_sales": cells[2].text,
                    "reviews": cells[3].text,
                    "rating": cells[4].text if len(cells) > 4 else None
                })
        return data
    
    def _query_traffic_structure(self, asin, country):
        """查询流量结构"""
        url = f"https://www.sif.com/TrafficStructure?country={country}&asin={asin}"
        self.driver.get(url)
        time.sleep(4)
        
        # 提取流量分布
        traffic_types = {}
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".traffic-type-card")
        for elem in elements:
            try:
                type_name = elem.find_element(By.CSS_SELECTOR, ".type-name").text
                percentage = elem.find_element(By.CSS_SELECTOR, ".percentage").text
                traffic_types[type_name] = percentage
            except:
                continue
        
        return traffic_types
    
    def _reverse_search_keywords(self, asin, country):
        """反查流量词"""
        url = f"https://www.sif.com/ReverseSearch?country={country}&asin={asin}"
        self.driver.get(url)
        time.sleep(5)
        
        # 提取前20个关键词
        keywords = []
        rows = self.driver.find_elements(By.CSS_SELECTOR, ".keyword-table tbody tr")
        for row in rows[:20]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:
                keywords.append({
                    "keyword": cells[0].text,
                    "traffic_share": cells[1].text,
                    "search_rank": cells[2].text,
                    "position": cells[3].text
                })
        return keywords
    
    def _analyze_ad_intelligence(self, asin, country):
        """分析广告架构 (旗舰版)"""
        url = f"https://www.sif.com/AdIntelligence?country={country}&asin={asin}"
        self.driver.get(url)
        time.sleep(5)
        
        # 检查是否旗舰版
        if "upgrade" in self.driver.page_source.lower():
            return {"error": "需要旗舰版权限"}
        
        # 提取广告活动
        campaigns = []
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".campaign-item")
        for elem in elements[:5]:  # 取前5个活动
            try:
                campaign_id = elem.find_element(By.CSS_SELECTOR, ".campaign-id").text
                keywords_count = len(elem.find_elements(By.CSS_SELECTOR, ".keyword-row"))
                campaigns.append({
                    "campaign_id": campaign_id,
                    "keywords_count": keywords_count
                })
            except:
                continue
        
        return campaigns
    
    def export_report(self, filename=None):
        """导出分析报告"""
        if not filename:
            filename = f"sif_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"报告已保存: {filename}")
        return filename
    
    def close(self):
        """关闭浏览器"""
        self.driver.quit()


# 使用示例
if __name__ == "__main__":
    analyzer = SIFCompetitorAnalyzer("your_username", "your_password")
    
    try:
        # 登录
        analyzer.login()
        
        # 分析竞品
        competitors = ["B08N5WRWNW", "B08N5M7S6K"]
        for asin in competitors:
            analyzer.analyze_competitor(asin, country="US")
            time.sleep(5)  # 间隔避免频繁
        
        # 导出报告
        analyzer.export_report("competitor_analysis.json")
        
    finally:
        analyzer.close()
```

---

## 常见问题

### Q1: 登录后页面跳转异常？

```python
# 处理登录后的重定向
def handle_redirect(driver, target_url):
    max_wait = 10
    waited = 0
    while waited < max_wait:
        if target_url in driver.current_url:
            return True
        time.sleep(1)
        waited += 1
    
    # 手动导航到目标页面
    driver.get(target_url)
    return True
```

### Q2: 数据加载慢或超时？

```python
# 增加重试机制
def query_with_retry(driver, url, max_retries=3):
    for i in range(max_retries):
        try:
            driver.get(url)
            # 等待特定元素
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".data-loaded"))
            )
            return True
        except:
            if i == max_retries - 1:
                raise
            time.sleep(5)
    return False
```

### Q3: 如何处理验证码？

目前 SIF 在登录时较少出现验证码，如遇到建议：
1. 使用打码平台 API
2. 人工介入处理
3. 使用已登录的 Cookie 会话

### Q4: 如何处理弹窗/提示？

```python
def close_popup(driver):
    """关闭可能的弹窗"""
    popup_selectors = [
        ".modal-close",
        ".ant-modal-close",
        ".popup-close",
        "button[aria-label='close']"
    ]
    
    for selector in popup_selectors:
        try:
            popup = driver.find_element(By.CSS_SELECTOR, selector)
            popup.click()
            time.sleep(0.5)
        except:
            continue
```

---

## 相关链接

| 链接 | 说明 |
|------|------|
| https://www.sif.com | SIF 官网 |
| https://www.sif.com/Login | 登录页 |
| https://www.idcspy.com/sif.html | 功能介绍与定价 |
| https://www.sif.com/extension | 浏览器插件下载 |

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-02-15 | v1.0 | 初始版本，覆盖12个站点主要功能 |

---

*本文档基于 SIF 网页版结构整理，实际使用时请根据页面更新调整选择器。*
