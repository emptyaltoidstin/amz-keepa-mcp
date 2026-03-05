# Amazon Operations Actuary System - User Guide

> **v3.0 Final Edition | Data-driven FBA product selection decision-making**

---

## 📋 Table of Contents

1. [quick start](#quick start)
2. [core concepts](#core concepts)
3. [Single variant analysis](#Single variant analysis)
4. [Multi-variant linkage analysis](#Multi-variant linkage analysis)
5. [Data Entry Guide](#Data Entry Guide)
6. [Report interpretation](#Report interpretation)
7. [FAQ](#FAQ)

---

## quick start

### Get started in 3 minutes

```bash
# 1. Activate the environment
source venv/bin/activate

# 2. Prepare data (Example)
python3 << 'EOF'
from src.amazon_actuary_final import generate_final_report

# product data (Get from Keepa API)
products = [{
    'asin': 'B0F6B5R47Q',
    'title': 'Your Product Title',
    'stars': 4.5,
    'reviews': 1000,
    'brand': 'Brand',
    'color': 'Black',
    'size': 'Standard',
    'packageLength': 15, 'packageWidth': 12, 'packageHeight': 2,
    'packageWeight': 150,
    'categoryTree': [{'name': 'Luggage'}],
    'data': {'df_SALES': None, 'df_NEW': None, 'df_BUY_BOX_SHIPPING': None}
}]

# real financial data
financials = {
    'B0F6B5R47Q': {
        'cogs': 9.50,          # Obtain from supplier
        'organic_pct': 0.70,   # Obtained from the advertising backend
        'ad_pct': 0.30,
    }
}

# Generate report
report_path, analysis = generate_final_report(
    parent_asin='B0F6B5R47Q',
    products=products,
    financials_map=financials,
    tacos_rate=0.15
)

print(f"Report generated: {report_path}")
print(f"decision making: {analysis.overall_decision.decision}")
print(f"Expected monthly profit: ${analysis.total_monthly_profit:,.2f}")
EOF
```

---

## core concepts

### 1. 163 Keepa indicators

The system collects all fields in Keepa Product Viewer CSV format, including:

| Category | key indicators | use |
|------|----------|------|
| **sales performance** | Sales Rank, 90d avg, Drops | Estimate sales and determine trends |
| **price** | Current, 30d avg, Lowest/Highest | price stability analysis |
| **Buy Box** | Seller, Amazon %, Flipability | Competitive Landscape Analysis |
| **Comment** | Rating, Count, Velocity | Product quality assessment |
| **cost** | FBA Fee, Referral Fee | cost structure calculation |
| **compete** | Offer Count, New/Used | intensity of competition |

### 2. TACOS vs ACOS

```
ACOS  = advertising spend / advertising sales  (View insertion orders only)
TACOS = advertising spend / total sales    (Look at the overall business)

Example:
- advertising spend: $1000
- advertising sales: $3000
- total sales: $10000

ACOS  = $1000 / $3000 = 33.3%
TACOS = $1000 / $10000 = 10%

The system uses TACOS because it better reflects the impact of advertising on overall profitability.
```

### 3. True COGS principles

**Never estimate COGS!** Even if it is$A difference of 0.50 can also lead to wrong decisions.

```
COGS = Product purchase price + First leg freight + tariff + Quality inspection fee + Others

Example:
- Product purchase price (1688): $6.00
- First leg freight (Shipping): $1.20
- tariff (15%): $0.90
- Quality inspection fee: $0.20
- Others: $0.20
- Total COGS: $8.50
```

### 4. Order source data

Obtained from Amazon Advertising Backend:

**path**: Seller Central → Advertising → Campaign Management → Measurement and Analytics

```
Advertising sales ratio = advertising sales / total sales

Example:
- advertising sales: $3000
- total sales: $10000
- Insertion order proportion: 30%
- Proportion of natural orders: 70%
```

---

## Single variant analysis

Applicable to products with a single ASIN and no variations.

### Usage scenarios
- Private model products (Only 1 ASIN)
- Test new products for market response
- Analyze individual ASINs of competing products

### code example

```python
from src.amazon_actuary_final import generate_final_report

# single product data
products = [{
    'asin': 'B0XXX12345',
    'title': 'Single Product',
    'stars': 4.3,
    'reviews': 500,
    # ...Keepa data
}]

financials = {
    'B0XXX12345': {
        'cogs': 8.00,
        'organic_pct': 0.65,
        'ad_pct': 0.35,
    }
}

report_path, analysis = generate_final_report(
    parent_asin='B0XXX12345',
    products=products,
    financials_map=financials,
    tacos_rate=0.15
)
```

### Report output
- Single variant profit analysis
- Organic vs Insertion Order Comparison
- Investment advice based on 163 indicators

---

## Multi-variant linkage analysis

**This is the most powerful feature of the system!** For multiple colors/For products with size variants, all variants must be analyzed.

### Why all variants must be analyzed?

1. **Pareto effect**: Usually 2-3 variants contribute 80%Sales volume
2. **cost difference**: different colors/Dimensions of COGS may vary
3. **advertising dependence**: Popular colors may have high natural traffic, while unpopular colors rely on advertising.
4. **Risk diversification**: Avoid seeing only one variation and misjudging the entire link

### How to get all variant ASINs?

#### Method 1: Amazon front desk manual acquisition (recommend)

```
1. Open the product details page
2. find"Color"or"Size"drop down menu
3. Switch between different options and observe the URL changes:
   
   black: amazon.com/dp/B0F6B5R47Q
   brown: amazon.com/dp/B0F6B5R47R ← Record this ASIN
   red: amazon.com/dp/B0F6B5R47W ← Record this ASIN

4. Record ASINs for all variants
```

#### Method 2: Using Keepa Product Viewer

```
1. Open the Keepa website
2. Search for parent ASIN
3. View"Variations"tab page
4. Export all variant ASIN lists
```

### Complete code example

```python
from src.amazon_actuary_final import generate_final_report
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================
# Step 1: Prepare Keepa data for all variants
# ============================================

# Variant ASIN list
variants = [
    {'asin': 'B0F6B5R47Q', 'color': 'Black', 'size': 'Standard'},
    {'asin': 'B0F6B5R47R', 'color': 'Brown', 'size': 'Standard'},
    {'asin': 'B0F6B5R47W', 'color': 'Wine Red', 'size': 'Standard'},
    {'asin': 'B0F6B5R47L', 'color': 'Black', 'size': 'Large'},
    {'asin': 'B0F6B5R47S', 'color': 'Brown', 'size': 'Small'},
]

# Data obtained from Keepa API (Simplified example)
products = []
for v in variants:
    products.append({
        'asin': v['asin'],
        'title': f'Passport Holder - {v["color"]} {v["size"]}',
        'color': v['color'],
        'size': v['size'],
        'stars': 4.5,
        'reviews': 1000,
        'brand': 'BrandName',
        'packageLength': 15, 'packageWidth': 12, 'packageHeight': 2,
        'packageWeight': 150,
        'categoryTree': [{'name': 'Luggage'}],
        'data': {
            # This should be the real Keepa time series data
            'df_SALES': create_mock_bsr_data(rank=15000),
            'df_NEW': create_mock_price_data(price=27.99),
        }
    })

# ============================================
# Step 2: Prepare real COGS and order source data
# ============================================

financials_map = {
    # black standard - Best-selling, high organic traffic
    'B0F6B5R47Q': {
        'cogs': 9.50,          # Quote from supplier
        'organic_pct': 0.70,   # From the advertising backend
        'ad_pct': 0.30,
    },
    # Brown standard - medium sales
    'B0F6B5R47R': {
        'cogs': 9.50,
        'organic_pct': 0.55,
        'ad_pct': 0.45,
    },
    # Claret - Niche, needs advertising
    'B0F6B5R47W': {
        'cogs': 10.20,         # Red leather is more expensive
        'organic_pct': 0.35,
        'ad_pct': 0.65,
    },
    # large size - Low sales but good profits
    'B0F6B5R47L': {
        'cogs': 11.80,
        'organic_pct': 0.60,
        'ad_pct': 0.40,
    },
    # small size - test market
    'B0F6B5R47S': {
        'cogs': 8.20,
        'organic_pct': 0.75,
        'ad_pct': 0.25,
    },
}

# ============================================
# Step 3: Generate actuary report
# ============================================

report_path, analysis = generate_final_report(
    parent_asin='B0F6B5R47Q',
    products=products,
    financials_map=financials_map,
    output_path='cache/reports/my_product_ACTUARY_FINAL.html',
    tacos_rate=0.15
)

# ============================================
# Step 4: View analysis results
# ============================================

print(f"\n📊 Analysis completed!")
print(f"Report path: {report_path}")
print(f"\nOverall decision-making: {analysis.overall_decision.decision}")
print(f"Confidence: {analysis.overall_decision.confidence}%")
print(f"Total monthly profit: ${analysis.total_monthly_profit:,.2f}")
print(f"mixed profit margin: {analysis.blended_portfolio_margin_pct:.1f}%")

print(f"\n📈 variant performance:")
for i, v in enumerate(analysis.variants, 1):
    print(f"  #{i} {v.asin} [{v.metrics.color}]")
    print(f"      monthly sales: {v.estimated_monthly_sales}")
    print(f"      profit margin: {v.blended_margin_pct:.1f}%")
    print(f"      decision making: {v.decision.decision}")
```

---

## Data Entry Guide

### COGS data source

| Cost item | Source | How to get it |
|--------|------|----------|
| Product purchase price | supplier | 1688/Alibaba quotation |
| First leg freight | freight forwarding | Shipping/Air freight quotation |
| tariff | customs | Product HS code query |
| Quality inspection fee | third party | Quality inspection company quotation |
| Others | internal | Packaging, labeling, etc. |

### Order source data source

**Amazon Advertising Backend**:
1. Log in to Seller Central
2. Advertising → Advertising campaign management
3. Click"Measurement and Analysis"
4. View"advertising sales"and"total sales"
5. Calculation: insertion order% = advertising sales / total sales

**business report**:
1. Data Report → Business Report
2. View"Sales volume and visits on sub-product detail pages"
3. Comparison"Quantity of items ordered"and advertising reports

### Keepa API data

The system automatically obtains 163 indicators from the Keepa API, including:
- Sales ranking history
- price history
- Buy Box data
- Comment data
- Inventory data
- Seller competition data

---

## Report interpretation

### executive summary section

```
🟢 Recommended (Confidence: 75%)

key indicators:
- Total monthly sales: 1,486
- total monthly sales: $42,516
- Total monthly profit: $10,048
- mixed profit margin: 23.6%
- Proportion of natural orders: 58%
```

**Interpretation**: 
- ✅ Profit margin>20%, healthy
- ⚠️ Natural Order 58%, can be increased to 70%
- Overall recommendations are made, but advertising efficiency needs to be optimized.

### Pareto analysis part

```
Core findings: The first 3 variants contribute 80%Sales volume
core variant: B0F6B5R47Q, B0F6B5R47R, B0F6B5R47W
long tail variant: B0F6B5R47L, B0F6B5R47S
```

**Suggestions for action**:
1. Prioritize keeping core variants in stock
2. Consider reducing SKUs for long-tail variants

### risk assessment section

```
⚠️ High advertising dependence (1)
ASIN: B0F6B5R47W (Claret)
Insertion order proportion: 65%
```

**Suggestions for action**:
- Carry out off-site promotion to increase natural traffic
- Optimize Listing to Improve Conversion Rate

---

## FAQ

### Q: Why the confidence level is not 100%?

**A:** Confidence is based on the following factors:
- Data integrity (How many of 163 indicators are available)
- Historical data length (90 days vs 365 days)
- data consistency (price/Is the ranking stable?)
- Number of risk factors

Normally 75%The above can be considered a reliable decision.

### Q: What is a good blended profit margin??

| profit margin | Evaluation | suggestion |
|--------|------|------|
| >25% | Excellent | Can increase investment |
| 15-25% | good | Normal operations |
| 5-15% | Average | Need optimization |
| <5% | danger | Consider quitting |
| <0% | Loss | Stop now |

### Q: How to deal with loss-making variants?

**steps**:
1. Confirm that COGS data is accurate
2. Try to raise the price by 10-20%test
3. Optimize to reduce return rates
4. If you are still losing money, consider stopping sales.

### Q: Why are my actual profits different from those reported??

**Possible reasons**:
1. COGS input is inaccurate
2. Sales volume estimates are biased (BSR model limitations)
3. Fluctuation in advertising costs
4. Changes in return rate

**suggestion**: Compare after running for one month and calibrate with real data.

### Q: Can you analyze competing products??

**A:** Yes! But note:
- Unable to obtain competitive product COGS (Can only estimate)
- Unable to obtain competitive product order source
- Mainly used for competitive landscape analysis

---

## best practices

### 1. Monthly review

Run an analysis at the beginning of each month to compare:
- Actual Sales vs Forecast
- Actual profit vs forecast
- Is there any change in COGS?
- Are advertising costs optimized?

### 2. A/B test

For high ad dependency variants:
1. Leave it running as is for 2 weeks
2. Run for 2 weeks after optimizing Listing
3. Compare the changes in the proportion of natural orders
4. Calculate ROI improvement

### 3. Seasonal adjustment

Some products have significant seasonality:
- Stock up 2 months in advance
- Increase advertising investment before peak season
- Optimize natural ranking in off-season

---

## Technical support

Having a problem?

1. Check whether the Keepa API Key is valid
2. Confirm that the COGS data format is correct (float)
3. The total proportion of confirmed orders is 1.0 (organic_pct + ad_pct = 1.0)
4. View `cache/reports/` Does the directory have generated files?

---

**Document version**: v3.0 | **last updated**: 2026-02-15
