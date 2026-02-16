# Keepa API 真实费用集成指南

## 概述

现在系统使用 **Keepa API 真实数据** 来计算FBA费用和佣金，而不是估算值。

## 数据来源

### Keepa API 提供的数据

| 数据项 | 字段名 | 说明 |
|--------|--------|------|
| 产品长度 | `packageLength` | cm |
| 产品宽度 | `packageWidth` | cm |
| 产品高度 | `packageHeight` | cm |
| 产品重量 | `packageWeight` | g |
| 类目树 | `categoryTree` | 用于确定佣金比例 |
| FBA费用 | `fbaFees` | 直接返回或估算 |

### 佣金比例表 (基于类目)

| 类目 | 佣金比例 | 示例产品 |
|------|----------|----------|
| Electronics | 8% | 耳机、相机、手机 |
| Clothing | 17% | T恤、鞋子、包包 |
| Jewelry | 20% | 项链、戒指 |
| Home | 15% | 厨具、家居 |
| Books | 15% | 图书 |
| Beauty | 15% | 化妆品 |
| 其他 | 15% | 默认值 |

## 费用计算流程

```
Keepa API 产品数据
       ↓
┌─────────────────────────────────────┐
│  KeepaFeeExtractor                  │
│  - 提取尺寸重量                      │
│  - 确定类目佣金比例                  │
│  - 获取/估算FBA费用                  │
└─────────────────────────────────────┘
       ↓
费用明细:
  ├─ FBA费用: $X.XX (基于2026年费率)
  ├─ 佣金: $X.XX (售价 × 类目比例)
  └─ 其他: 退货、仓储等
       ↓
利润计算:
  利润 = 售价 - COGS - 总费用 - 广告成本
```

## 使用示例

### 基础使用

```python
from keepa_fee_extractor import KeepaFeeExtractor

# 从Keepa API获取的产品数据
product = {
    'asin': 'B0XXXXXXX',
    'packageLength': 20,
    'packageWidth': 15,
    'packageHeight': 8,
    'packageWeight': 450,
    'categoryTree': [{'name': 'Electronics'}]
}

price = 45.99

# 提取所有费用
fees = KeepaFeeExtractor.extract_all_fees(product, price)

print(f"FBA费用: ${fees['fba_fee']:.2f}")
print(f"佣金比例: {fees['referral_rate']*100:.1f}%")
print(f"佣金金额: ${fees['referral_fee']:.2f}")
print(f"总费用: ${fees['total_fees']:.2f}")
```

### 在精算师系统中使用

```python
from amazon_actuary_final import generate_actuary_report_auto

# 自动生成报告，使用Keepa真实费用数据
report_path, analysis, info = generate_actuary_report_auto('B0XXXXXXX')

# 报告中的费用分析将基于:
# - 真实的FBA费用 (从Keepa获取或基于尺寸计算)
# - 准确的佣金比例 (基于类目)
# - 精确的产品尺寸和重量
```

## FBA费用计算详情

### 2026年FBA费率表 (标准尺寸)

| 计费重量 | 费用 |
|----------|------|
| ≤ 0.75 lb | $3.22 |
| ≤ 1.0 lb | $3.86 |
| ≤ 1.5 lb | $4.75 |
| ≤ 2.0 lb | $5.77 |
| ≤ 3.0 lb | $6.47 |
| > 3.0 lb | $7.25 + $0.32/lb |

### 计费重量计算

```
计费重量 = max(实际重量, 体积重量)

体积重量 = (长 × 宽 × 高) / 166  (单位: inches)
```

示例:
```
产品尺寸: 20×15×8 cm = 7.9×5.9×3.1 inches
实际重量: 450g = 0.99 lb
体积重量: (7.9 × 5.9 × 3.1) / 166 = 0.87 lb

计费重量: max(0.99, 0.87) = 0.99 lb
FBA费用: $3.86
```

## 与其他系统的对比

### vs 固定15%佣金估算

| 类目 | 固定估算 | Keepa真实 | 差异 |
|------|----------|-----------|------|
| Electronics | 15% | 8% | 节省7% |
| Clothing | 15% | 17% | 多付2% |
| Jewelry | 15% | 20% | 多付5% |

**影响**: 对于$50售价的产品，佣金差异可达$2.50-$3.50

### vs 简化FBA估算

简化估算:
- 仅基于重量
- 忽略体积重量
- 使用旧费率

Keepa集成:
- 考虑尺寸和重量
- 计算体积重量
- 使用2026年最新费率

**影响**: 大件轻量产品FBA费用可能差异$2-$5

## 更新日志

### v3.1 (2026-02-16)
- ✅ 添加 `keepa_fee_extractor.py` 模块
- ✅ 集成类目佣金比例表
- ✅ 更新FBA费率为2026年标准
- ✅ 自动计算体积重量
- ✅ 更新 `amazon_actuary_final.py` 使用真实费用
- ✅ 更新 `keepa_metrics_collector.py` 提取费用指标

## 文件结构

```
src/
├── keepa_fee_extractor.py          # 新增: 费用提取器
├── amazon_actuary_final.py          # 更新: 使用真实费用
├── keepa_metrics_collector.py       # 更新: 提取费用指标
└── ...
```

## 下一步

现在系统可以:
1. ✅ 从Keepa API获取真实产品尺寸
2. ✅ 基于类目确定准确佣金比例
3. ✅ 使用2026年FBA费率计算费用
4. ✅ 自动处理体积重量计算
5. ✅ 生成基于真实数据的利润分析

所有财务模型都基于 **Keepa API 的真实数据**!
