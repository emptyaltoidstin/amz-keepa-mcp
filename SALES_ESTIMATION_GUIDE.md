# Description of Sales Estimation Method

## 📊 Data source priority

The system uses the following priorities to obtain sales data:

### 1. 🥇 Keepa real data (boughtInPastMonth) - most accurate
```python
# Purchase volume for the past 30 days provided directly by the Keepa API
boughtInPastMonth = product.get('boughtInPastMonth', 0)
```

**advantage**:
- ✅ Real purchase data officially tracked by Amazon
- ✅ Highest accuracy
- ✅Includes the number of actual completed orders

**limitations**:
- ❌ Some products may not have this data (new products, products with very low sales)
- ❌ The data has 1-3 days delay

---

### 2. 🥈 BSR ranking estimation - Alternate method

When there is no `boughtInPastMonth` When, use BSR (Sales Rank) estimation:

```python
def _estimate_monthly_sales(avg_rank: int) -> int:
    if avg_rank < 1000:
        return int(1500 * (1000 / avg_rank) ** 0.5)
    elif avg_rank < 10000:
        return int(800 * (10000 / avg_rank) ** 0.5)
    elif avg_rank < 50000:
        return int(300 * (50000 / avg_rank) ** 0.5)
    elif avg_rank < 100000:
        return int(100 * (100000 / avg_rank) ** 0.5)
    else:
        return int(50 * (100000 / avg_rank) ** 0.5)
```

**Estimate example**:

| BSR | Estimated monthly sales | Description |
|-----|-----------|------|
| 100 | 4,743 | Top sellers |
| 1,000 | 1,500 | Very popular |
| 5,000 | 1,131 | best seller |
| 10,000 | 800 | medium sales |
| 50,000 | 300 | Ordinary sales |
| 100,000 | 100 | lower sales volume |

---

## 🧮 B0BW93MP74 example comparison

### BSR estimation method
```
BSR: ~9,800
Calculation formula: 800 × (10000 / 9800)^0.5 ≈ 808 orders/month/Variants
9 variants total: ~7,272 orders/month
```

### boughtInPastMonth real data
```
If Keepa provides boughtInPastMonth = 616
Then the total of 9 variants: 616 × 9 = 5,544 orders/month
```

### Difference analysis
- BSR estimate: ~7,272 orders
- real data: ~5,544 orders
- difference: ~31% (BSR estimate is too high)

**Reason**: 
- BSR is ranking, which reflects relative sales volume.
- Different categories of BSR-Sales volume relationship is different
- Estimation models use averages and may be biased for specific products

---

## 📈 Accuracy comparison

| method | Accuracy | Applicable scenarios |
|------|--------|----------|
| `boughtInPastMonth` | ⭐⭐⭐⭐⭐ 90%+ | First choice when you have data |
| BSR estimate | ⭐⭐⭐ 60-80% | Backup when no real data is available |

---

## 💡 Best Practice Advice

### 1. Calibrate the estimation model
```python
# Use your own products to compare actual sales with estimates
def calibrate_model(actual_sales: int, estimated_sales: int) -> float:
    calibration_factor = actual_sales / estimated_sales
    return calibration_factor

# Example: Actual 500 orders, estimated 625 orders
calibration_factor = 500 / 625 = 0.8

# Multiply the calibration factor for subsequent estimates
adjusted_estimate = raw_estimate * 0.8
```

### 2. Multi-dimensional verification
```python
# Combine multiple indicators for cross-validation
def validate_sales_estimate(asin: str):
    # Method 1: boughtInPastMonth
    real_sales = get_bought_in_past_month(asin)
    
    # Method 2: BSR estimate
    bsr_estimate = estimate_from_bsr(asin)
    
    # Method 3: Comment growth
    review_growth = estimate_from_reviews(asin)
    
    # Method 4: Inventory changes
    inventory_change = estimate_from_inventory(asin)
    
    # comprehensive analysis
    return weighted_average([real_sales, bsr_estimate, review_growth, inventory_change])
```

### 3. Adjustment by category
Different categories of BSR-Sales volume relationships vary widely:

| Category | Features | Adjustment factor |
|------|------|---------|
| Electronics | Competition is fierce and BSR changes rapidly | 0.7-0.8 |
| Home & Kitchen | Moderate competition | 0.9-1.0 |
| Clothing | Strong seasonality | 0.8-0.9 |
| Toys | Holidays fluctuate greatly | 0.7-0.9 |

---

## 🔍 Code implementation

### Current implementation (Prioritize real data)
```python
def _get_bought_in_past_month(self, product: Dict) -> int:
    """
    Get the purchase volume in the past month
    Prioritize using Keepa real data, if not, use BSR estimation
    """
    # 1. Try to obtain Keepa real data
    bought = product.get('boughtInPastMonth', 0)
    if isinstance(bought, (int, float)) and bought > 0:
        return int(bought)
    
    # 2. Fall back to BSR estimation
    data = product.get('data', {})
    return self._estimate_monthly_sales(data)
```

---

## ⚠️ IMPORTANT NOTE

1. **data delay**: `boughtInPastMonth` Usually there is 1-3 days delay
2. **New product no data**: Products that have been on the shelf for less than 30 days may not have this data
3. **Very low sales**: monthly sales<10 products may not have accurate data
4. **Variant merging**: Some variants may share sales data

---

## 📊 Summary

| scene | Recommended method |
|------|---------|
| have `boughtInPastMonth` | Use real data |
| No real data | BSR estimate + Calibration coefficient |
| Competitive product analysis | BSR estimate |
| Own product optimization | Use Amazon backend real data |

**core principles**: 
> If you can use real data, there is no need to estimate.
> When estimates must be made, the error range must be known.
> Important decisions need to be verified in multiple dimensions.
