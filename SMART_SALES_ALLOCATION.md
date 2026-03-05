# Intelligent sales distribution system

## Problem background

Provided by Keepa API `boughtInPastMonth` There are two possibilities for fields:

### Case 1: Each variant has independent data
```
Black: 800 orders
Grey: 600 orders
Brown: 400 orders
...
```
**ideal situation**, use directly

### Case 2: All variants share parent ASIN total sales
```
All variations boughtInPastMonth = 5544 (total)
```
**question**: If used directly, all variants will have the same sales volume, which is obviously unreasonable!

---

## solution: Intelligent sales distribution algorithm

### core logic

When all variants are detected `boughtInPastMonth` numerical value**exactly the same**, the system determines that the data is shared and automatically presses **BSR ranking ratio** assigned to each variant.

### Distribution formula

```python
# 1. Calculate the weight of each variant
weight = 1 / (BSR ^ 0.5)  # The lower the BSR, the higher the weight

# 2. Calculate the proportion
ratio = current_weight / total_weights

# 3. Allocate sales volume
allocated_sales = total_sales * ratio
```

**Why use BSR^-0.5？**
- BSR is a ranking, not a linear relationship
- The difference between ranking 1 and ranking 10 > The difference between ranking 1000 and 1010
- Square root smoothes extreme values to avoid an overrepresentation of head variants

---

## Case analysis (B0BW93MP74)

### raw data
```
All variations boughtInPastMonth = 5544 (Detected as shared data)
```

### Variants BSR
```
Black: BSR 9,804
Grey: BSR 9,770
Brown: BSR 9,803
Green: BSR 9,804
White: BSR 9,803
...
```

### Allocation calculation
```
total sales: 5544 orders/month

Black (BSR 9804):
  weight = 1 / sqrt(9804) = 0.0101
  Proportion = 0.0101 / total weight = 11.1%
  Allocate sales volume = 5544 * 11.1% = 615 orders

Grey (BSR 9770):
  weight = 1 / sqrt(9770) = 0.0101
  Proportion = 11.2%
  Allocate sales volume = 621 orders

Brown (BSR 9803):
  weight = 0.0101
  Proportion = 11.1%
  Allocate sales volume = 615 orders
```

### Assignment results
```
📊 Distributed to each variant according to BSR ratio...
    - Black: 615 orders/month (11.1%)
    - Grey: 621 orders/month (11.2%)
    - Brown: 615 orders/month (11.1%)
    - Green: 615 orders/month (11.1%)
    - White: 615 orders/month (11.1%)
    - ...
```

**Key improvements**: 
- before: All variations = 5544 orders (obvious error)
- now: every variant = Around 615 orders (sum = 5544, logical)

---

## Code implementation

### variant_auto_collector.py

```python
def _process_sales_data(self, variants: List[Dict]) -> List[Dict]:
    # 1. Check whether it is shared data
    sales_values = [v.get('boughtInPastMonth', 0) for v in variants]
    is_shared_data = len(set(sales_values)) == 1 and len(variants) > 1
    
    if not is_shared_data:
        return variants  # Independent data, used directly
    
    # 2. Allocation according to BSR ratio
    total_sales = sales_values[0]
    all_bsr = [get_bsr(v) for v in variants]
    
    for i, v in enumerate(variants):
        current_bsr = all_bsr[i]
        weights = [1 / (bsr ** 0.5) for bsr in all_bsr]
        ratio = weights[i] / sum(weights)
        v['boughtInPastMonth'] = int(total_sales * ratio)
    
    return variants
```

### amazon_actuary_final.py

```python
def _get_bought_in_past_month(self, product: Dict, is_shared_data: bool = False, 
                               total_sales: int = 0, all_variants_bsr: List[int] = None) -> int:
    """Intelligent acquisition of sales volume: give priority to real data and allocate proportionally if necessary"""
    
    bought = product.get('boughtInPastMonth', 0)
    
    # Case 1: Have independent real data
    if bought > 0 and not is_shared_data:
        return int(bought)
    
    # Case 2: Shared data requires allocation
    if is_shared_data and total_sales > 0:
        return self._allocate_sales_by_bsr(
            current_bsr=self._get_avg_rank_90d(product.get('data', {})),
            total_sales=total_sales,
            all_variants_bsr=all_variants_bsr
        )
    
    # Case 3: BSR estimate
    return self._estimate_monthly_sales(product.get('data', {}))
```

---

## Advantages

| Features | Description |
|------|------|
| **Automatic detection** | Automatically identify shared data vs independent data |
| **Smart allocation** | Scientific allocation based on BSR ranking and in line with market rules |
| **keep traces** | Record original data and distribution ratio for easy traceability |
| **Seamless rollback** | Automatically use BSR estimation when there is no real data |

---

## Things to note

1. **Allocation precision**: When the BSRs of all variants are very close, the distribution results are not very different, which is consistent with the actual situation (the sales volume of the hot-selling variants is similar)

2. **extreme case**: If a variant BSR is much higher than others (e.g. 100,000 vs 10,000), the allocated sales volume will be very small, which may be a true tail variant

3. **Calibration recommendations**: Use your own products to compare actual sales and distribution results, and adjust the weight calculation formula

---

## Summary

**Intelligent sales distribution system**Fixed issues with Keepa data sharing:

> not simple"Use real data or estimates"，
> Rather"Identify data types → Intelligent processing → Reasonable allocation"

Make sure every variant has**Independent sales data that conforms to market rules**。
