# SIF Keyword Tool RPA Automation Guide

> Organizing the official page structure based on Chrome DevTools crawling
> last updated: 2026-02-15
> Applicable version: SIF web version + Plug-in version

---

## Table of contents

1. [System overview](#System overview)
2. [Authentication and login](#Authentication and login)
3. [Core function page URL](#Core function page-url)
4. [RPA operations guide](#rpa-Operation guide)
5. [Data extraction specifications](#Data extraction specifications)
6. [Anti-crawling strategies and restrictions](#Anti-crawling strategies and restrictions)
7. [Automation script example](#Automation script example)
8. [FAQ](#FAQ)

---

## System overview

### Product positioning

SIF is a keyword operation tool focused on Amazon site traffic analysis. It provides:
- Sales query (accurate to variant/attribute level)
- Traffic structure analysis
- Keyword reverse search
- Advertising Architecture Perspective
- Bid inquiry
- Time machine (historical data tracking)
- Word expansion and correlation screening

### support site

| site | code | Data start time |
|------|------|-------------|
| United States | US | 2021-11 |
| germany | DE | 2021-11 |
| United Kingdom | UK | 2021-11 |
| Japan | JP | 2021-11 |
| Canada | CA | 2021-11 |
| france | FR | 2021-11 |
| spain | ES | 2021-11 |
| Italy | IT | 2021-11 |
| Australia | AU | 2025-03-23 |
| mexico | MX | 2025-03-23 |
| Brazil | BR | 2025-03-23 |
| United Arab Emirates | AE | 2025-03-23 |

### Version function differences

| Function | Basic version | Ultimate version |
|------|--------|--------|
| Check sales | ✅ | ✅ |
| Check traffic structure | ✅ | ✅ |
| Check traffic words | ✅ | ✅ |
| Check bidding | 2 times/day | unlimited |
| Advertising perspective | ❌ | ✅ |
| time machine | ❌ | ✅ |
| Extension of keywords for multiple competing products | 50 ASIN/Second-rate | 100 ASIN/Second-rate |
| Expanding the history of words with words | only 1 month | All history |
| Daily pit monitoring | 50 words | 200 words |
| Hourly ranking monitoring | 1 yuan/week | 1 yuan/week |

---

## Authentication and login

### Login page

```
URL: https://www.sif.com/Login
Method: POST
Content-Type: application/json
```

### Login process

**Step 1: Visit login page**
```python
# Selenium example
driver.get("https://www.sif.com/Login")

# Wait for the login form to load
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.ID, "username")))
```

**Step 2: Enter credentials**
```python
# Position input box
username_input = driver.find_element(By.ID, "username")
password_input = driver.find_element(By.ID, "password")

# Enter credentials
username_input.send_keys("your_username")
password_input.send_keys("your_password")
```

**Step 3: Click to log in**
```python
# Way 1: Click the login button
login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
login_button.click()

# Way 2: Press enter key
password_input.send_keys(Keys.RETURN)
```

**Step 4: Verify successful login**
```python
# Check whether it jumps to the function page or the user avatar appears
try:
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "user-avatar")))
    print("Login successful")
except:
    # Check error messages
    error_msg = driver.find_elements(By.CLASS_NAME, "error-message")
    if error_msg:
        print(f"Login failed: {error_msg[0].text}")
```

### Token/Session management

```python
# Get Cookie
cookies = driver.get_cookies()

# Save cookie for later use
import json
with open('sif_cookies.json', 'w') as f:
    json.dump(cookies, f)

# Load cookies for subsequent sessions
driver.get("https://www.sif.com")
with open('sif_cookies.json', 'r') as f:
    cookies = json.load(f)
for cookie in cookies:
    driver.add_cookie(cookie)
driver.refresh()
```

### Login status check

```python
def check_login_status(driver):
    """Check if you are currently logged in"""
    driver.get("https://www.sif.com")
    time.sleep(2)
    
    # Check if login button exists
    login_buttons = driver.find_elements(By.LINK_TEXT, "Login")
    
    if login_buttons:
        return False
    
    # Check if user related elements exist
    user_elements = driver.find_elements(By.CLASS_NAME, "user-menu")
    return len(user_elements) > 0
```

---

## Core function page URL

### 1. Check sales (Sales)

```
URL Pattern: https://www.sif.com/Sales?country={country}
Parameters:
  - country: US, UK, DE, JP, CA, FR, ES, IT, AU, MX, BR, AE
```

**Page operations:**

| Operation | element positioning | Description |
|------|----------|------|
| ASIN lookup | `input[placeholder*="ASIN"]` | Enter the ASIN, separate multiple ASINs with commas(Up to 10) |
| Keyword query | `input[placeholder*="keywords"]` | Enter a keyword to query the sales volume of products under this keyword |
| Site switching | `select[name="country"]` | Switch between different Amazon sites |
| Query button | `button:contains("Query")` | Execute query |
| download button | `button:contains("Download")` | Download Excel/CSV data |

**data fields:**
- ASIN
- Variant properties (Color/Size)
- monthly sales (Format: 50+ Represents 50-99)
- Monthly sales trends
- Number of comments
- Rating stars
- price

---

### 2. Check the traffic structure (Traffic Structure)

```
URL Pattern: https://www.sif.com/TrafficStructure?country={country}&asin={asin}
```

**Page operations:**

| Operation | element positioning | Description |
|------|----------|------|
| ASIN input | `input[name="asin"]` | Enter the ASIN you want to query |
| time range | `select[name="timeRange"]` | 7 days/30 days/All history |
| Variant screening | `.variant-selector` | Select a specific variant |
| Attribute filter | `.attribute-selector` | Press Color/Size filter |
| Traffic type filtering | `.traffic-type-filter` | nature/advertise/recommend/association |

**Traffic type description:**
| Type | Description |
|------|------|
| organic search | Organic Search |
| PPC advertising | Sponsored Products |
| Deal activities | Deals |
| Search recommendations | Search Recommendation |
| associated traffic | Related Products |

---

### 3. Check traffic words (Reverse Search)

```
URL Pattern: https://www.sif.com/ReverseSearch?country={country}&asin={asin}
```

**Page operations:**

| Operation | element positioning | Description |
|------|----------|------|
| ASIN input | `input[name="asin"]` | Enter ASIN |
| contrast mode | `button[data-mode="compare"]` | Multiple ASIN comparison |
| Time selection | `select[name="dateRange"]` | 7 days/30 days/history |
| Parent query | `checkbox[name="parentAsin"]` | Query all traffic words of the parent body |
| Filter sort | `.filter-panel select` | According to traffic proportion/Rank filter |

**data fields:**
- keywords
- Traffic proportion (%)
- search ranking
- exposure position
- nature/Ad traffic distribution
- Weekly search volume (ABA data)

---

### 4. Advertising perspective (Ad Intelligence) ⭐ Ultimate version

```
URL Pattern: https://www.sif.com/AdIntelligence?country={country}&asin={asin}
```

**Page operations:**

| Operation | element positioning | Description |
|------|----------|------|
| ASIN input | `input[name="asin"]` | Enter the competing ASIN |
| Campaign filters | `select[name="campaignId"]` | Filter specific campaigns |
| Serving variant filtering | `select[name="targetAsin"]` | View specific variation ads |
| Ad word search | `input[name="keyword"]` | Search for specific ad terms |
| time range | `select[name="timeRange"]` | Select analysis time period |

**core data:**
- Campaign ID
- Delivery team (Ad Group)
- Delivery terms and matching patterns
- Traffic proportion
- ASIN Targeted Advertising Data

---

### 5. Check the bidding (Bid Query)

```
URL Pattern: https://www.sif.com/BidQuery?country={country}&keyword={keyword}
```

**Page operations:**

| Operation | element positioning | Description |
|------|----------|------|
| Keyword input | `input[name="keyword"]` | single/Enter keywords in batches |
| Advertising type switch | `.ad-type-tabs` | SP / SB switch |
| Match mode selection | `select[name="matchType"]` | Exact/Phrase/Broad |
| Time selection | `select[name="dateRange"]` | week/Monthly data |
| Expand query | `button[data-action="expand"]` | Expand related word bidding |
| download button | `button:contains("Download")` | Export bidding data |

**data fields:**
- keywords
- Suggested bid (SP/SB)
- ABA Top3 Concentration
- Top3 product main picture
- Search volume trends

---

### 6. Time machine (Time Machine) ⭐ Ultimate version

```
URL Pattern: https://www.sif.com/TimeMachine?country={country}&asin={asin}
```

**sub function:**

#### 6.1 Traffic time machine
```
URL: https://www.sif.com/TimeMachine/Traffic?asin={asin}
```
- Competitive product operation tactics reappear
- Flow change diagnosis

#### 6.2 Product time machine
```
URL: https://www.sif.com/TimeMachine/Product?asin={asin}
```
- Seasonal product tracking
- Holiday Product Trends

**Page operations:**

| Operation | element positioning | Description |
|------|----------|------|
| ASIN input | `input[name="asin"]` | Enter ASIN |
| Timeline drag | `.timeline-slider` | Select historical time point |
| contrast mode | `button[data-mode="compare"]` | Compare different time points |
| Change filter | `.change-filter` | Filter for specific types of changes |

**Track change types:**
- Coupon price changes
- Prime price changes
- Main image change
- Title changes
- Campaign changes

---

### 7. Extension of words & screening (Keyword Expansion)

```
URL Pattern: https://www.sif.com/KeywordExpansion
```

**Subfunction URL:**

| Function | URL |
|------|-----|
| Extension of keywords for multiple competing products | `/KeywordExpansion/Competitor` |
| Expand words from words | `/KeywordExpansion/Keyword` |
| Subcategory extensions | `/KeywordExpansion/Category` |
| Batch import screening | `/KeywordExpansion/Import` |

**Page operations:**

| Operation | element positioning | Description |
|------|----------|------|
| ASIN input | `textarea[name="asins"]` | Enter ASINs in bulk(50-100) |
| Relevance threshold | `input[name="relevanceThreshold"]` | Set relevance criteria |
| Start expanding words | `button:contains("Start expanding words")` | Execute extension |
| automatic screening | `button:contains("automatic screening")` | AI automatically determines relevance |
| Manual marking | `.relevance-toggle` | Manual tagging related/Not relevant |
| Save thesaurus | `button:contains("Save to vocabulary")` | Save filter results |
| Advanced filtering | `.advanced-filter-panel` | Multiple condition combination filtering |

**screening index:**
- Relevance score
- The top 4 occupancy rates of natural bits
- Traffic proportion
- search volume

---

### 8. Word choice (Keyword Selection)

```
URL Pattern: https://www.sif.com/KeywordSelection
```

**sub function:**

| Function | URL |
|------|-----|
| click conversion rate | `/KeywordSelection/ConversionRate` |
| Number of competing products | `/KeywordSelection/CompetitorCount` |
| Traffic position competition landscape | `/KeywordSelection/CompetitionLandscape` |

**Page operations:**

| Operation | element positioning | Description |
|------|----------|------|
| Keyword input | `textarea[name="keywords"]` | Enter keywords in batches |
| time range | `select[name="timeRange"]` | Select data time range |
| Conversion rate sorting | `.sort-by-conversion` | Sort by conversion rate |
| ACOS filter | `input[name="acosRange"]` | Filter ACOS ranges |
| Download report | `button:contains("Download")` | Export analysis data |

**data fields:**
- keyword conversion rate
- ACOS
- CPA (Insertion order average promotion cost)
- Suggested bid
- Number of competing products
- Traffic position competition landscape

---

### 9. Check the pit location/Push ranking (Rank Tracking)

```
URL Pattern: https://www.sif.com/RankTracking
```

**sub function:**

| Function | URL | Description |
|------|-----|------|
| Pit snapshot | `/RankTracking/Snapshot` | Quickly check keyword rankings |
| Daily ranking | `/RankTracking/Daily` | Daily ranking monitoring |
| Hourly ranking | `/RankTracking/Hourly` | Hourly ranking monitoring(Pay) |

**Page operations:**

| Operation | element positioning | Description |
|------|----------|------|
| ASIN input | `input[name="asin"]` | Enter monitoring ASIN |
| Keyword input | `input[name="keyword"]` | Enter monitoring keywords |
| Add monitoring | `button:contains("Add monitoring")` | Add monitoring words |
| Monitoring list | `.tracking-list` | View all monitoring words |
| Ranking trends | `.rank-chart` | View ranking trends |
| Delete monitoring | `.remove-tracking-btn` | Delete monitoring words |

**Restrictions:**
- Basic version: 50 words/day
- Ultimate version: 200 words/day
- Hourly ranking: 1 yuan/week/word

---

### 10. Product library/vocabulary (Library)

```
URL Pattern: https://www.sif.com/Library
```

**Subfunction URL:**

| Function | URL |
|------|-----|
| Product library | `/Library/Products` |
| vocabulary | `/Library/Keywords` |

**Page operations:**

| Operation | element positioning | Description |
|------|----------|------|
| Add product | `button:contains("Add product")` | Add products to follow |
| Add vocabulary | `button:contains("Create new vocabulary")` | Create new vocabulary |
| Word frequency statistics | `.word-frequency-btn` | View word frequency statistics |
| Batch operations | `.batch-action-dropdown` | Batch import/Export |

---

## RPA operations guide

### universal waiting strategy

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class SIFAutomation:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
    
    def wait_for_loading(self):
        """Wait for loading to complete"""
        try:
            # Wait for loading animation to disappear
            self.wait.until(EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, ".loading-spinner, .ant-spin")
            ))
        except TimeoutException:
            pass
    
    def wait_for_data_table(self):
        """Wait for the data table to load"""
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".data-table, .ant-table")
        ))
```

### Automated sales check

```python
def query_sales_by_asin(driver, asins, country="US"):
    """
    Check sales by ASIN
    
    Args:
        driver: Selenium WebDriver
        asins: ASIN list (Up to 10)
        country: site code
    """
    # Build URL
    asin_str = ",".join(asins[:10])  # Up to 10
    url = f"https://www.sif.com/Sales?country={country}&asin={asin_str}"
    driver.get(url)
    
    # waiting to load
    time.sleep(3)
    
    # Check if you need to click the query button
    query_buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'Query')]")
    if query_buttons:
        query_buttons[0].click()
        time.sleep(5)  # Wait for data to load
    
    # Extract data
    data = extract_sales_data(driver)
    return data

def extract_sales_data(driver):
    """Extract sales data"""
    data = []
    
    # Locate table row
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
            print(f"Error parsing row data: {e}")
    
    return data
```

### Automatically check traffic words

```python
def reverse_search_keywords(driver, asin, country="US", date_range="30"):
    """
    Check ASIN traffic words
    
    Args:
        driver: Selenium WebDriver
        asin: Target ASIN
        country: site
        date_range: time range (7/30/all)
    """
    url = f"https://www.sif.com/ReverseSearch?country={country}&asin={asin}&range={date_range}"
    driver.get(url)
    
    # Wait for data to load
    time.sleep(5)
    
    # Extract keyword data
    keywords = extract_keyword_data(driver)
    return keywords

def extract_keyword_data(driver):
    """Extract keyword data"""
    keywords = []
    
    # Scroll to load all data
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    # Extract table data
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

### Advertising perspective machine automation (Ultimate version)

```python
def analyze_ad_intelligence(driver, asin, country="US"):
    """
    Analyze advertising architecture
    
    Args:
        driver: Selenium WebDriver
        asin: Competitor ASIN
        country: site
    """
    url = f"https://www.sif.com/AdIntelligence?country={country}&asin={asin}"
    driver.get(url)
    
    time.sleep(5)  # Waiting for ad data to load
    
    # Check if you have permission
    if "upgrade" in driver.page_source.lower() or "Ultimate version" in driver.page_source:
        print("Requires Ultimate Edition permissions")
        return None
    
    ad_data = extract_ad_data(driver)
    return ad_data

def extract_ad_data(driver):
    """Extract advertising data"""
    campaigns = []
    
    # Get a list of advertising campaigns
    campaign_elements = driver.find_elements(By.CSS_SELECTOR, ".campaign-item")
    
    for campaign in campaign_elements:
        try:
            campaign_id = campaign.find_element(By.CSS_SELECTOR, ".campaign-id").text
            keywords = []
            
            # Get the keywords under this activity
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

### Check bidding automation

```python
def query_keyword_bids(driver, keywords, country="US", ad_type="SP"):
    """
    Query keyword bidding in batches
    
    Args:
        driver: Selenium WebDriver
        keywords: keyword list
        country: site
        ad_type: SP or SB
    """
    url = f"https://www.sif.com/BidQuery?country={country}"
    driver.get(url)
    
    # Enter keywords
    keyword_input = driver.find_element(By.CSS_SELECTOR, "textarea[name='keywords']")
    keyword_input.clear()
    keyword_input.send_keys("\n".join(keywords))
    
    # Select ad type
    ad_type_tab = driver.find_element(By.CSS_SELECTOR, f".ad-type-tab[data-type='{ad_type}']")
    ad_type_tab.click()
    
    # Click to query
    query_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Query')]")
    query_btn.click()
    
    time.sleep(5)  # Waiting for results
    
    # Extract bidding data
    bid_data = extract_bid_data(driver)
    return bid_data

def extract_bid_data(driver):
    """Extract bidding data"""
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

### Download data in batches

```python
def download_data(driver, file_name=None):
    """
    Trigger data download
    
    Args:
        driver: Selenium WebDriver
        file_name: Custom file name (Optional)
    """
    # Find the download button
    download_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Download') or contains(@class, 'download')]")
    download_btn.click()
    
    # If there is a file name input box
    try:
        filename_input = driver.find_element(By.CSS_SELECTOR, "input[name='filename']")
        if file_name:
            filename_input.clear()
            filename_input.send_keys(file_name)
        
        # Confirm download
        confirm_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Confirm') or contains(text(),'Download')]")
        confirm_btn.click()
    except:
        pass
    
    # Wait for download to complete
    time.sleep(3)
```

---

## Data extraction specifications

### Data field mapping table

| Function | Field name | data type | Example |
|------|--------|----------|------|
| Check sales | asin | string | B08N5WRWNW |
| Check sales | monthly_sales | string | 200+ |
| Check sales | variant_color | string | Black |
| Check sales | variant_size | string | Large |
| Check traffic words | keyword | string | wireless mouse |
| Check traffic words | traffic_share | string | 15.2% |
| Check traffic words | search_rank | int | 3 |
| Check traffic words | organic_share | string | 80% |
| Check traffic words | ad_share | string | 20% |
| Advertising perspective | campaign_id | string | 123456789 |
| Advertising perspective | ad_group | string | Group-A |
| Advertising perspective | match_type | string | EXACT |
| Check bidding | suggested_bid | float | 2.5 |
| Check bidding | bid_range | string | $1.5-$3.0 |
| Check bidding | acos | float | 15.2 |

### Data cleaning rules

```python
def clean_sales_number(sales_str):
    """
    Clean sales data
    50+ -> 50-99 range
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
    """Clean percentage data"""
    if not pct_str:
        return None
    
    pct_str = pct_str.replace("%", "").strip()
    try:
        return float(pct_str)
    except:
        return None
```

---

## Anti-crawling strategies and restrictions

### Known limitations

| Restriction type | limit value | Description |
|----------|--------|------|
| Login session | need to stay active | It will automatically exit if it is not used for a long time. |
| Query frequency | Undisclosed | It is recommended that a single IP should not query more than 1 time per second |
| Multiple ASIN lookup | 10/Second-rate | Sales query can query up to 10 ASINs at the same time |
| Extension word ASIN number | Basic 50/Flagship 100 | Limitations on word expansion for multiple competing products |
| Pit location monitoring | Basic 50/Flagship 200 | Daily monitoring word limit |
| Bid inquiry | Basic 2 times/flagship unlimited | Check bidding function restrictions |

### Anti-climbing suggestions

```python
import random
import time

class AntiDetection:
    @staticmethod
    def random_delay(min_sec=2, max_sec=5):
        """random delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    @staticmethod
    def human_like_scroll(driver):
        """Simulate human scrolling"""
        for i in range(3):
            driver.execute_script(
                f"window.scrollTo(0, {random.randint(300, 700) * (i+1)});"
            )
            time.sleep(random.uniform(0.5, 1.5))
    
    @staticmethod
    def add_human_behavior(driver):
        """Add human behavior characteristics"""
        # Random mouse movement
        actions = ActionChains(driver)
        actions.move_by_offset(random.randint(-50, 50), random.randint(-50, 50))
        actions.perform()
```

### Security advice

1. **Use an enterprise account**: Enterprise Edition has higher concurrency and looser limits
2. **Control query frequency**: Avoid large number of queries in a short period of time
3. **Use proxy IP**: Multiple accounts/Multiple IP distributed requests
4. **Monitor account status**: Check regularly to see if you are restricted

---

## Automation script example

### Complete workflow: Competitive product analysis

```python
#!/usr/bin/env python3
"""
SIF competitive product analysis automation script
Function: Check sales of competing products -> Check traffic words -> Analyze advertising architecture -> Export report
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
        """Login to SIF"""
        self.driver.get("https://www.sif.com/Login")
        
        # Enter credentials
        self.driver.find_element(By.ID, "username").send_keys(self.username)
        self.driver.find_element(By.ID, "password").send_keys(self.password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for successful login
        time.sleep(3)
        print("Login successful")
    
    def analyze_competitor(self, asin, country="US"):
        """
        Complete competitive product analysis process
        
        Args:
            asin: Competitor ASIN
            country: site
        """
        print(f"Start analyzing ASINs: {asin}")
        
        # Step 1: Check sales
        print("  Check sales...")
        sales_data = self._query_sales(asin, country)
        
        # Step 2: Check traffic structure
        print("  Query traffic structure...")
        traffic_data = self._query_traffic_structure(asin, country)
        
        # Step 3: Check traffic words
        print("  Check traffic words...")
        keywords_data = self._reverse_search_keywords(asin, country)
        
        # Step 4: Advertising perspective (if available)
        print("  Analyze advertising architecture...")
        ad_data = self._analyze_ad_intelligence(asin, country)
        
        # Summary results
        self.results[asin] = {
            "timestamp": datetime.now().isoformat(),
            "country": country,
            "sales": sales_data,
            "traffic_structure": traffic_data,
            "keywords": keywords_data,
            "ads": ad_data
        }
        
        print(f"Analysis completed: {asin}")
        return self.results[asin]
    
    def _query_sales(self, asin, country):
        """Check sales"""
        url = f"https://www.sif.com/Sales?country={country}&asin={asin}"
        self.driver.get(url)
        time.sleep(4)
        
        # Extract data
        data = []
        rows = self.driver.find_elements(By.CSS_SELECTOR, ".data-table tbody tr")
        for row in rows[:5]:  # Take the top 5 variations
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
        """Query traffic structure"""
        url = f"https://www.sif.com/TrafficStructure?country={country}&asin={asin}"
        self.driver.get(url)
        time.sleep(4)
        
        # Extract traffic distribution
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
        """Check traffic words"""
        url = f"https://www.sif.com/ReverseSearch?country={country}&asin={asin}"
        self.driver.get(url)
        time.sleep(5)
        
        # Extract the first 20 keywords
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
        """Analyze advertising architecture (Ultimate version)"""
        url = f"https://www.sif.com/AdIntelligence?country={country}&asin={asin}"
        self.driver.get(url)
        time.sleep(5)
        
        # Check if it is Ultimate version
        if "upgrade" in self.driver.page_source.lower():
            return {"error": "Requires Ultimate Edition permissions"}
        
        # Extract advertising campaigns
        campaigns = []
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".campaign-item")
        for elem in elements[:5]:  # Take the top 5 activities
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
        """Export analysis report"""
        if not filename:
            filename = f"sif_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"Report saved: {filename}")
        return filename
    
    def close(self):
        """Close browser"""
        self.driver.quit()


# Usage example
if __name__ == "__main__":
    analyzer = SIFCompetitorAnalyzer("your_username", "your_password")
    
    try:
        # Login
        analyzer.login()
        
        # Analyze competing products
        competitors = ["B08N5WRWNW", "B08N5M7S6K"]
        for asin in competitors:
            analyzer.analyze_competitor(asin, country="US")
            time.sleep(5)  # Avoid frequent intervals
        
        # Export report
        analyzer.export_report("competitor_analysis.json")
        
    finally:
        analyzer.close()
```

---

## FAQ

### Q1: The page jumps abnormally after logging in?

```python
# Handling post-login redirects
def handle_redirect(driver, target_url):
    max_wait = 10
    waited = 0
    while waited < max_wait:
        if target_url in driver.current_url:
            return True
        time.sleep(1)
        waited += 1
    
    # Manually navigate to target page
    driver.get(target_url)
    return True
```

### Q2: Data loading slowly or timing out?

```python
# Add retry mechanism
def query_with_retry(driver, url, max_retries=3):
    for i in range(max_retries):
        try:
            driver.get(url)
            # wait for specific element
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

### Q3: How to deal with verification codes?

Currently, SIF rarely displays verification codes when logging in. If you encounter any suggestions:
1. Use coding platform API
2. Manual intervention processing
3. Use logged in cookie session

### Q4: How to deal with pop-ups/Tips?

```python
def close_popup(driver):
    """Close possible pop-ups"""
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

## Related links

| link | Description |
|------|------|
| https://www.sif.com | SIF official website |
| https://www.sif.com/Login | Login page |
| https://www.idcspy.com/sif.html | Function introduction and pricing |
| https://www.sif.com/extension | Browser plug-in download |

---

## Change log

| Date | version | Update content |
|------|------|----------|
| 2026-02-15 | v1.0 | Initial version, covering 12 main site functions |

---

*This document is organized based on the structure of the SIF web version. Please adjust the selector according to page updates during actual use.*
