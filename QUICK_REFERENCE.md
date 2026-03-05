# Amz-Keepa-MCP Quick Reference Card

## 🚀 Get started in 3 minutes

```python
# 1. Import
from src import auto_analyze

# 2. Provide COGS data
financials = {
    'B0XXXYYYYY': {
        'cogs': 8.50,        # true purchase cost
        'organic_pct': 0.65, # Proportion of natural orders
        'ad_pct': 0.35,      # Insertion order proportion
    },
}

# 3. One-click analysis
report, analysis, info = auto_analyze(
    asin='B0XXXYYYYY',
    financials_map=financials
)

# 4. View results
print(f"decision making: {analysis.overall_decision.decision}")
print(f"monthly profit: ${analysis.total_monthly_profit:,.2f}")
print(f"report: {report}")
```

---

## 📊 Quick overview of core functions

| Function | Description | code |
|------|------|------|
| **Automatic variant collection** | Enter 1 ASIN and automatically discover all variations | `auto_analyze(asin)` |
| **163 indicator collection** | Complete Keepa Product Viewer data | Automatic integration |
| **Intelligent sales volume allocation** | Allocate parent ASIN total sales in proportion to BSR | Automatic processing |
| **TACOS model** | True Advertising Cost Calculation | Built-in calculations |
| **data driven decision making** | Automatically generate investment recommendations | `analysis.overall_decision` |
| **Chinese report** | 163 indicators Chinese version + Advanced UI | Automatically generated |

---

## 💰 Key calculation formulas

### TACOS Advertising Cost
```
unit advertising cost = (Monthly Sales × TACOS) / Monthly advertising orders

Example:
- monthly sales: $13,575
- TACOS: 15%
- monthly insertion order: 146
- unit advertising cost = ($13,575 × 15%) / 146 = $13.95
```

### mixed profit margin
```
mixed profit margin = (Natural profit × natural proportion + Advertising profit × advertising proportion) / price

Example:
- natural profit: $10.00 (Accounting for 70%)
- advertising profit: $-3.99 (Proportion 30%)
- price: $27.99
- mixed profit margin = ($10×0.7 + $-3.99×0.3) / $27.99 = 20.7%
```

### BSR sales estimate
```
BSR < 1,000:   Sales volume = 1500 × (1000/BSR)^0.5
BSR < 10,000:  Sales volume = 800 × (10000/BSR)^0.5
BSR < 50,000:  Sales volume = 300 × (50000/BSR)^0.5
BSR > 100,000: Sales volume = 50 × (100000/BSR)^0.5
```

---

## 📋 Decision Criteria

| decision making | Conditions | Confidence |
|------|------|--------|
| ✅ **Recommended investment** | profit margin>15% & risk factors<3 | 75%+ |
| ⚠️ **Consider carefully** | Profit margin 5-15% or risk factor 3+ | 60-75% |
| ❌ **Recommended to avoid** | profit margin<5% or loss | <60% |

---

## 🔧 Commonly used APIs

### variant collection
```python
from src.variant_auto_collector import VariantAutoCollector

collector = VariantAutoCollector(api_key)
variants, parent_info = collector.collect_variants('B0XXX')

# Print summary
print(collector.format_variants_summary(variants))

# Get properties
for v in variants:
    attrs = collector.get_variation_attributes(v)
    print(f"{v['asin']}: {attrs}")
```

### 163 indicators
```python
from src.keepa_metrics_collector import KeepaMetricsCollector

collector = KeepaMetricsCollector()
metrics = collector.collect_all_metrics(product)

# Check data integrity
completeness = collector.calculate_data_completeness(metrics)
print(f"Data integrity: {completeness:.0f}%")
```

### Custom analysis
```python
from src.amazon_actuary_final import generate_final_report

report_path, analysis = generate_final_report(
    parent_asin='B0PARENT',
    products=products,           # Keepa product data
    financials_map=financials,   # financial data
    tacos_rate=0.15              # TACOS ratio
)
```

---

## 📁 Output file

| File | location | Description |
|------|------|------|
| Chinese report | `cache/reports/{ASIN}_CHINESE_FULL_REPORT.html` | Full analysis report |
| Premium reporting | `cache/reports/{ASIN}_PREMIUM.html` | Advanced UI reporting |
| CSV data | `cache/reports/{ASIN}_163_metrics.csv` | Raw data export |
| chart | `cache/charts/{ASIN}_*.png` | Visual charts |

---

## 🎨 Report content

### Chinese report contains
1. **executive summary** - investment decision + Confidence
2. **key indicators** - profit/profit margin/Sales volume/number of variants
3. **Variant analysis** - Detailed comparison of 9 variants
4. **163 indicators** - Complete display of Chinese indicators
5. **Data source** - Original Keepa data is transparent
6. **Calculation logic** - Visualization of sales distribution process

---

## ⚡ Troubleshooting

### Question 1: API current limit
```
Symptoms: "Waiting XXX seconds for additional tokens"
solve: Normal phenomenon, the system will automatically wait
```

### Question 2: No variant data
```
Symptoms: "Variant data not found"
solve: 
1. Confirm that the ASIN is correct
2. Check if the product has any variants
3. Try to query the parent ASIN
```

### Question 3: Sales estimates have large deviations
```
Symptoms: There is a big gap between estimated sales and actual sales
solve:
1. Calibrate the model with your own product
2. Adjust BSR-Sales volume mapping parameters
3. Prioritize the use of boughtInPastMonth real data
```

---

## 📚 Related documents

| document | content |
|------|------|
| `PROJECT_SUMMARY.md` | Full project summary |
| `METRICS_DICTIONARY.md` | 163 indicators Chinese dictionary |
| `SALES_ESTIMATION_GUIDE.md` | Sales Estimation Guide |
| `USAGE_GUIDE.md` | Detailed user guide |
| `README.md` | Project description |

---

## 💡 Best Practices Quick Check

### ✅ Should do
- [ ] Use real COGS data
- [ ] Get the order source ratio from the advertising backend
- [ ] Calibration model review monthly
- [ ] Prioritize analysis of all variants rather than individual ones

### ❌ Should not do
- [ ] Estimate COGS (Would rather wait for the supplier's quotation)
- [ ] See only single ASIN analysis
- [ ] Risks of Ignoring High Ad-Dependent Variants
- [ ] Long-tail variant of Pareto analysis that ignores

---

## 🎯 Decision Checklist

Before making an investment decision, confirm:

- [ ] Real COGS for all variants entered
- [ ] The order source ratio comes from the advertising backend
- [ ] 163 indicator data integrity>80%
- [ ] Pareto analysis identified core variants
- [ ] There are no major risk items in the risk assessment
- [ ] Expected ROI meets investment objectives

---

## 📞 Quick commands

```bash
# activate environment
cd /Users/blobeats/Downloads/amz-keepa-mcp
source venv/bin/activate

# Set API Key
export KEEPA_KEY="your_key_here"

# Run analysis
python3 -c "from src import auto_analyze; auto_analyze('B0XXX')"

# View report
open cache/reports/*.html
```

---

**Remember the core principles**: 
> If you can use real data, you don’t need to estimate.  
> Know the margin of error when you must estimate  
> All decisions must be based on data

---

**version**: v3.0 | **renew**: 2026-02-16
