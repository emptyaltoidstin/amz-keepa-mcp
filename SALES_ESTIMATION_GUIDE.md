# 销量估算方法说明

## 📊 数据来源优先级

系统使用以下优先级获取销量数据：

### 1. 🥇 Keepa真实数据 (boughtInPastMonth) - 最准确
```python
# Keepa API直接提供的过去30天购买量
boughtInPastMonth = product.get('boughtInPastMonth', 0)
```

**优点**:
- ✅ 亚马逊官方追踪的真实购买数据
- ✅ 准确度最高
- ✅ 包含实际成交的订单数

**局限性**:
- ❌ 部分产品可能没有此数据（新品、销量极低的产品）
- ❌ 数据有1-3天延迟

---

### 2. 🥈 BSR排名估算 - 备用方法

当没有 `boughtInPastMonth` 时，使用BSR（销售排名）估算：

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

**估算示例**:

| BSR | 估算月销量 | 说明 |
|-----|-----------|------|
| 100 | 4,743 | 顶级畅销品 |
| 1,000 | 1,500 | 非常畅销 |
| 5,000 | 1,131 | 畅销 |
| 10,000 | 800 | 中等销量 |
| 50,000 | 300 | 普通销量 |
| 100,000 | 100 | 较低销量 |

---

## 🧮 B0BW93MP74 实例对比

### BSR估算方法
```
BSR: ~9,800
计算公式: 800 × (10000 / 9800)^0.5 ≈ 808单/月/变体
9个变体总计: ~7,272单/月
```

### boughtInPastMonth 真实数据
```
如果Keepa提供的boughtInPastMonth = 616
则9个变体总计: 616 × 9 = 5,544单/月
```

### 差异分析
- BSR估算: ~7,272单
- 真实数据: ~5,544单
- 差异: ~31% (BSR估算偏高)

**原因**: 
- BSR是排名，反映的是相对销量
- 不同类目BSR-销量关系不同
- 估算模型使用平均值，特定产品可能有偏差

---

## 📈 准确性对比

| 方法 | 准确度 | 适用场景 |
|------|--------|----------|
| `boughtInPastMonth` | ⭐⭐⭐⭐⭐ 90%+ | 有数据时的首选 |
| BSR估算 | ⭐⭐⭐ 60-80% | 无真实数据时的备用 |

---

## 💡 最佳实践建议

### 1. 校准估算模型
```python
# 用自己的产品对比实际销量和估算值
def calibrate_model(actual_sales: int, estimated_sales: int) -> float:
    calibration_factor = actual_sales / estimated_sales
    return calibration_factor

# 例：实际500单，估算625单
calibration_factor = 500 / 625 = 0.8

# 后续估算时乘以校准系数
adjusted_estimate = raw_estimate * 0.8
```

### 2. 多维度验证
```python
# 结合多个指标交叉验证
def validate_sales_estimate(asin: str):
    # 方法1: boughtInPastMonth
    real_sales = get_bought_in_past_month(asin)
    
    # 方法2: BSR估算
    bsr_estimate = estimate_from_bsr(asin)
    
    # 方法3: 评论增长
    review_growth = estimate_from_reviews(asin)
    
    # 方法4: 库存变化
    inventory_change = estimate_from_inventory(asin)
    
    # 综合分析
    return weighted_average([real_sales, bsr_estimate, review_growth, inventory_change])
```

### 3. 分品类调整
不同品类的BSR-销量关系差异很大：

| 品类 | 特点 | 调整系数 |
|------|------|---------|
| Electronics | 竞争激烈，BSR变化快 | 0.7-0.8 |
| Home & Kitchen | 中等竞争 | 0.9-1.0 |
| Clothing | 季节性强 | 0.8-0.9 |
| Toys | 节日波动大 | 0.7-0.9 |

---

## 🔍 代码实现

### 当前实现 (优先真实数据)
```python
def _get_bought_in_past_month(self, product: Dict) -> int:
    """
    获取过去一个月购买量
    优先使用Keepa真实数据，如果没有则用BSR估算
    """
    # 1. 尝试获取Keepa真实数据
    bought = product.get('boughtInPastMonth', 0)
    if isinstance(bought, (int, float)) and bought > 0:
        return int(bought)
    
    # 2. 回退到BSR估算
    data = product.get('data', {})
    return self._estimate_monthly_sales(data)
```

---

## ⚠️ 重要提示

1. **数据延迟**: `boughtInPastMonth` 通常有1-3天延迟
2. **新品无数据**: 上架少于30天的产品可能没有此数据
3. **极低销量**: 月销量<10的产品可能没有准确数据
4. **变体合并**: 某些变体可能共享销量数据

---

## 📊 总结

| 场景 | 推荐方法 |
|------|---------|
| 有 `boughtInPastMonth` | 使用真实数据 |
| 无真实数据 | BSR估算 + 校准系数 |
| 竞品分析 | BSR估算 |
| 自身产品优化 | 使用亚马逊后台真实数据 |

**核心原则**: 
> 能用真实数据就不用估算，
> 必须估算时要知晓误差范围，
> 重要决策要结合多个维度验证。
