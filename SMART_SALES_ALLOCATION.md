# 智能销量分配系统

## 问题背景

Keepa API提供的 `boughtInPastMonth` 字段有两种可能：

### 情况1: 每个变体有独立数据
```
Black: 800单
Grey: 600单
Brown: 400单
...
```
**理想情况**，直接使用

### 情况2: 所有变体共享父ASIN总销量
```
所有变体 boughtInPastMonth = 5544 (总计)
```
**问题**: 如果直接使用，会导致所有变体销量相同，明显不合理！

---

## 解决方案: 智能销量分配算法

### 核心逻辑

当检测到所有变体的 `boughtInPastMonth` 数值**完全相同**时，系统判定为共享数据，自动按 **BSR排名比例** 分配到各变体。

### 分配公式

```python
# 1. 计算每个变体的权重
weight = 1 / (BSR ^ 0.5)  # BSR越低，权重越高

# 2. 计算占比
ratio = current_weight / total_weights

# 3. 分配销量
allocated_sales = total_sales * ratio
```

**为什么用 BSR^-0.5？**
- BSR是排名，不是线性关系
- 排名1和排名10的差距 > 排名1000和1010的差距
- 平方根平滑极端值，避免头部变体占有过高比例

---

## 实例分析 (B0BW93MP74)

### 原始数据
```
所有变体 boughtInPastMonth = 5544 (检测为共享数据)
```

### 各变体BSR
```
Black: BSR 9,804
Grey: BSR 9,770
Brown: BSR 9,803
Green: BSR 9,804
White: BSR 9,803
...
```

### 分配计算
```
总销量: 5544单/月

Black (BSR 9804):
  权重 = 1 / sqrt(9804) = 0.0101
  占比 = 0.0101 / 总权重 = 11.1%
  分配销量 = 5544 * 11.1% = 615单

Grey (BSR 9770):
  权重 = 1 / sqrt(9770) = 0.0101
  占比 = 11.2%
  分配销量 = 621单

Brown (BSR 9803):
  权重 = 0.0101
  占比 = 11.1%
  分配销量 = 615单
```

### 分配结果
```
📊 按BSR比例分配到各变体...
    - Black: 615单/月 (11.1%)
    - Grey: 621单/月 (11.2%)
    - Brown: 615单/月 (11.1%)
    - Green: 615单/月 (11.1%)
    - White: 615单/月 (11.1%)
    - ...
```

**关键改进**: 
- 之前: 所有变体 = 5544单 (明显错误)
- 现在: 每个变体 = 615单左右 (总和 = 5544，符合逻辑)

---

## 代码实现

### variant_auto_collector.py

```python
def _process_sales_data(self, variants: List[Dict]) -> List[Dict]:
    # 1. 检测是否是共享数据
    sales_values = [v.get('boughtInPastMonth', 0) for v in variants]
    is_shared_data = len(set(sales_values)) == 1 and len(variants) > 1
    
    if not is_shared_data:
        return variants  # 独立数据，直接使用
    
    # 2. 按BSR比例分配
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
    """智能获取销量：优先真实数据，必要时按比例分配"""
    
    bought = product.get('boughtInPastMonth', 0)
    
    # 情况1: 有独立的真实数据
    if bought > 0 and not is_shared_data:
        return int(bought)
    
    # 情况2: 共享数据，需要分配
    if is_shared_data and total_sales > 0:
        return self._allocate_sales_by_bsr(
            current_bsr=self._get_avg_rank_90d(product.get('data', {})),
            total_sales=total_sales,
            all_variants_bsr=all_variants_bsr
        )
    
    # 情况3: BSR估算
    return self._estimate_monthly_sales(product.get('data', {}))
```

---

## 优势

| 特点 | 说明 |
|------|------|
| **自动检测** | 自动识别共享数据 vs 独立数据 |
| **智能分配** | 基于BSR排名科学分配，符合市场规律 |
| **保留痕迹** | 记录原始数据和分配比例，便于追溯 |
| **无缝回退** | 没有真实数据时自动使用BSR估算 |

---

## 注意事项

1. **分配精度**: 当所有变体BSR非常接近时，分配结果差异不大，这符合实际情况（热销变体销量相近）

2. **极端情况**: 如果某个变体BSR远高于其他（如100,000 vs 10,000），分配到的销量会很少，这可能是真实的尾部变体

3. **校准建议**: 用自己的产品对比实际销量和分配结果，调整权重计算公式

---

## 总结

**智能销量分配系统**解决了Keepa数据共享的问题：

> 不是简单的"用真实数据或估算"，
> 而是"识别数据类型 → 智能处理 → 合理分配"

确保每个变体都有**符合市场规律的独立销量数据**。
