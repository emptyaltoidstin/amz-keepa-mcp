# Keepa Product Viewer CSV Metric Analysis

## Overview

Keepa Product Viewer export includes**163 fields**The complete product indicators can be divided into the following core dimensions:

---

## 📊 Indicator Classification (MECE)

### 1. Basic information (Basic Info) - 18 fields

| Field | Description | importance |
|------|------|--------|
| Locale | market code | ⭐ |
| ASIN | Product ID | ⭐⭐⭐ |
| Title | title | ⭐⭐ |
| Parent Title | parent title | ⭐ |
| Brand | brand | ⭐⭐ |
| Manufacturer | manufacturer | ⭐ |
| Product Group | product group | ⭐ |
| Category Tree | Category path | ⭐⭐ |
| Model | Model | ⭐ |
| Binding | binding type | ⭐ |
| Tracking since | Tracking start | ⭐ |
| Listed since | Release date | ⭐⭐ |

### 2. Sales performance (Sales Performance) - 8 fields

| Field | Description | importance |
|------|------|--------|
| Sales Rank: Current | Current BSR | ⭐⭐⭐ |
| Sales Rank: 90 days avg. | 90-day average BSR | ⭐⭐⭐ |
| Sales Rank: Drops last 90 days | Number of ranking drops in 90 days | ⭐⭐⭐ |
| Bought in past month | Sales volume in the past 30 days | ⭐⭐⭐ |
| 90 days change % monthly sold | Sales volume change rate | ⭐⭐⭐ |
| Return Rate | return rate | ⭐⭐⭐ |
| Sales Rank: Reference | Reference category | ⭐ |
| Sales Rank: Subcategory Sales Ranks | Subcategory ranking | ⭐⭐ |

### 3. Price data (Pricing) - 35+fields

#### Buy Box price
- Buy Box: Current
- Buy Box: 90 days avg.
- Buy Box: Strikethrough Price
- Buy Box: Standard Deviation 90 days
- Buy Box: Flipability 90 days

#### Amazon self-operated price
- Amazon: Current
- Amazon: 30/90/180/365 days avg.
- Amazon: Lowest/Highest
- Amazon: Stock
- Amazon: 90 days OOS

#### New product price
- New: Current
- New: 30/90/180/365 days avg.
- New: Lowest/Highest

#### other prices
- List Price: Current/avg.
- Lightning Deals: Current
- Warehouse Deals: Current/avg.
- Used: Current/avg.

### 4. Competitive Analysis (Competition) - 15 fields

| Field | Description | importance |
|------|------|--------|
| Buy Box: Buy Box Seller | Buy Box seller | ⭐⭐⭐ |
| Buy Box: Is FBA | Whether FBA | ⭐⭐ |
| Buy Box: % Amazon 90 days | Amazon’s share | ⭐⭐⭐ |
| Buy Box: % Top Seller 90 days | Proportion of top sellers | ⭐⭐ |
| Buy Box: Winner Count 90 days | Buy Box switching times | ⭐⭐ |
| Total Offer Count | Total number of offers | ⭐⭐⭐ |
| Count of retrieved live offers: New, FBA | Number of FBA sellers | ⭐⭐⭐ |
| Count of retrieved live offers: New, FBM | Number of FBM sellers | ⭐⭐⭐ |
| New Offer Count: Current | Number of new product sellers | ⭐⭐ |
| Used Offer Count: Current | Number of second-hand sellers | ⭐ |

### 5. Review quality (Reviews) - 5 fields

| Field | Description | importance |
|------|------|--------|
| Reviews: Rating | score | ⭐⭐⭐ |
| Reviews: Rating Count | Number of comments | ⭐⭐⭐ |
| Reviews: Review Count - Format Specific | Format specific comments | ⭐ |
| Reviews: Rating - 30 days avg. | 30-day average rating | ⭐⭐ |
| Reviews: Rating Count - 90 days avg. | 90-day average reviews | ⭐⭐ |

### 6. Fee structure (Fees) - 5 fields

| Field | Description | importance |
|------|------|--------|
| FBA Pick&Pack Fee | FBA processing fee | ⭐⭐⭐ |
| Referral Fee % | Commission ratio | ⭐⭐⭐ |
| Referral Fee based on current Buy Box price | Commission amount | ⭐⭐ |
| Suggested Lower Price | Recommended price reduction | ⭐ |
| Business Discount: Percentage | corporate discount | ⭐ |

### 7. Inventory health (Inventory) - 8 fields

| Field | Description | importance |
|------|------|--------|
| Amazon: Stock | Amazon inventory | ⭐⭐ |
| Amazon: 90 days OOS | 90-day out-of-stock rate | ⭐⭐⭐ |
| Amazon: OOS Count 30 days | Number of out-of-stocks in 30 days | ⭐⭐ |
| Amazon: OOS Count 90 days | Number of out-of-stocks within 90 days | ⭐⭐ |
| Amazon: Availability | Availability | ⭐⭐ |
| Buy Box: Prime Eligible | Prime Eligibility | ⭐⭐ |
| Buy Box: Subscribe & Save | Subscribe to save | ⭐ |

### 8. Content quality (Content) - 15 fields

| Field | Description | importance |
|------|------|--------|
| Image Count | Number of pictures | ⭐⭐ |
| Videos: Video Count | Number of videos | ⭐⭐ |
| Videos: Has Main Video | Main video | ⭐⭐ |
| A+ Content: Has A+ Content | A+content | ⭐⭐ |
| A+ Content: A+ From Manufacturer | Manufacturer A+ | ⭐ |
| Description & Features: Feature 1-10 | Product selling point | ⭐⭐ |

### 9. Logistics specifications (Dimensions) - 10 fields

| Field | Description | importance |
|------|------|--------|
| Package: Length/Width/Height (cm) | Packing size | ⭐⭐⭐ |
| Package: Weight (g) | Packing weight | ⭐⭐⭐ |
| Package: Dimension (cm³) | Packing volume | ⭐⭐ |
| Item: Length/Width/Height (cm) | Product size | ⭐⭐ |
| Item: Weight (g) | Product weight | ⭐⭐ |

### 10. Marketing promotions (Marketing) - 8 fields

| Field | Description | importance |
|------|------|--------|
| Lightning Deals: Current | flash sale | ⭐⭐ |
| Deals: Deal Type | Promotion type | ⭐⭐ |
| Deals: Badge | badge | ⭐ |
| One Time Coupon: Absolute/Percentage | Coupon | ⭐⭐ |
| Warehouse Deals: Current/avg. | Warehouse deals | ⭐ |

### 11. Product Variations (Variations) - 5 fields

| Field | Description | importance |
|------|------|--------|
| Parent ASIN | Parent ASIN | ⭐⭐ |
| Variation ASINs | Variation list | ⭐⭐ |
| Variation Attributes | Variant properties | ⭐ |
| Color | color | ⭐ |
| Size | Size | ⭐ |

### 12. Supply chain (Supply Chain) - 10 fields

| Field | Description | importance |
|------|------|--------|
| Buy Box: Shipping Country | Shipping country | ⭐⭐ |
| Amazon: Amazon offer shipping delay | Shipping delay | ⭐⭐ |
| Is HazMat | Dangerous goods | ⭐⭐⭐ |
| Is heat sensitive | heat sensitive | ⭐ |
| Batteries Required/Included | battery | ⭐ |

---

## 🎯 Core indicators that actuaries pay attention to

### A. Profitability indicators (Profitability)
```
profit = selling price - COGS - FBA fee - Commission - Other expenses

Key input:
- Buy Box price (current/history)
- FBA Pick&Pack Fee
- Referral Fee %
- Package Weight (Impact on FBA fees)
- Return Rate (Impact on return costs)
```

### B. Demand intensity indicator (Demand)
```
Needs scoring = f(Sales volume, Ranking trends, Seasonal)

Key input:
- Bought in past month
- 90 days change % monthly sold
- Sales Rank: Current vs avg
- Sales Rank: Drops count
```

### C. Competitive intensity indicator (Competition)
```
Competition Rating = f(Number of sellers, Amazon’s share, Buy Box stability)

Key input:
- Total Offer Count
- Buy Box: % Amazon 90 days
- Buy Box: Winner Count 90 days
- Buy Box: Is FBA (Does FBA compete?)
```

### D. Risk assessment indicators (Risk)
```
risk score = f(return rate, Out of stock rate, price volatility)

Key input:
- Return Rate
- Amazon: 90 days OOS
- Price Standard Deviation
- Buy Box: Flipability
```

---

## 🔧 MCP expansion plan

### Option 1: CSV importer (CSV Importer Tool)
```python
@mcp.tool()
async def import_keepa_csv(csv_path: str, ctx: Context) -> str:
    """Import Keepa Product Viewer CSV files for comprehensive analysis"""
    pass
```

### Option 2: Extended data collection (Extended Data Collection)
```python
# in existing process_Add CSV field mapping based on product
csv_field_mapping = {
    'salesRank': ['Sales Rank: Current', 'Sales Rank: 90 days avg.'],
    'buyBox': ['Buy Box: Current', 'Buy Box: % Amazon 90 days'],
    'fees': ['FBA Pick&Pack Fee', 'Referral Fee %'],
    # ...more mappings
}
```

### Option 3: Actuary Analysis Module (Actuarial Analysis)
```python
class ActuarialAnalyzer:
    def calculate_profit_score(self, data):
        # Actuarial grade profitability score
        pass
    
    def calculate_risk_adjusted_return(self, data):
        # risk adjusted return
        pass
    
    def monte_carlo_simulation(self, data, iterations=1000):
        # Monte Carlo simulation
        pass
```
