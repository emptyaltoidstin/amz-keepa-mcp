# 亚马逊运营精算师系统 - 使用指南

> **v3.0 Final Edition | 数据驱动的FBA选品决策**

---

## 📋 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [单变体分析](#单变体分析)
4. [多变体链接分析](#多变体链接分析)
5. [数据输入指南](#数据输入指南)
6. [报告解读](#报告解读)
7. [常见问题](#常见问题)

---

## 快速开始

### 3分钟入门

```bash
# 1. 激活环境
source venv/bin/activate

# 2. 准备数据 (示例)
python3 << 'EOF'
from src.amazon_actuary_final import generate_final_report

# 产品数据 (从Keepa API获取)
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

# 真实财务数据
financials = {
    'B0F6B5R47Q': {
        'cogs': 9.50,          # 从供应商获取
        'organic_pct': 0.70,   # 从广告后台获取
        'ad_pct': 0.30,
    }
}

# 生成报告
report_path, analysis = generate_final_report(
    parent_asin='B0F6B5R47Q',
    products=products,
    financials_map=financials,
    tacos_rate=0.15
)

print(f"报告已生成: {report_path}")
print(f"决策: {analysis.overall_decision.decision}")
print(f"预期月利润: ${analysis.total_monthly_profit:,.2f}")
EOF
```

---

## 核心概念

### 1. 163个Keepa指标

系统采集Keepa Product Viewer CSV格式的全部字段，包括：

| 类别 | 关键指标 | 用途 |
|------|----------|------|
| **销售表现** | Sales Rank, 90d avg, Drops | 估算销量、判断趋势 |
| **价格** | Current, 30d avg, Lowest/Highest | 价格稳定性分析 |
| **Buy Box** | Seller, Amazon %, Flipability | 竞争格局分析 |
| **评论** | Rating, Count, Velocity | 产品质量评估 |
| **费用** | FBA Fee, Referral Fee | 成本结构计算 |
| **竞争** | Offer Count, New/Used | 竞争激烈程度 |

### 2. TACOS vs ACOS

```
ACOS  = 广告花费 / 广告销售额  (只看广告订单)
TACOS = 广告花费 / 总销售额    (看整体业务)

示例:
- 广告花费: $1000
- 广告销售额: $3000
- 总销售额: $10000

ACOS  = $1000 / $3000 = 33.3%
TACOS = $1000 / $10000 = 10%

系统使用TACOS因为它更能反映广告对整体盈利的影响。
```

### 3. 真实COGS原则

**永远不要估算COGS！** 即使是$0.50的差异也会导致错误决策。

```
COGS = 产品采购价 + 头程运费 + 关税 + 质检费 + 其他

示例:
- 产品采购价 (1688): $6.00
- 头程运费 (海运): $1.20
- 关税 (15%): $0.90
- 质检费: $0.20
- 其他: $0.20
- COGS总计: $8.50
```

### 4. 订单来源数据

从亚马逊广告后台获取：

**路径**: Seller Central → 广告 → 广告活动管理 → 测量和分析

```
广告销售额占比 = 广告销售额 / 总销售额

示例:
- 广告销售额: $3000
- 总销售额: $10000
- 广告订单占比: 30%
- 自然订单占比: 70%
```

---

## 单变体分析

适用于单一ASIN、无变体的产品。

### 使用场景
- 私模产品 (只有1个ASIN)
- 测试市场反应的新品
- 分析竞品单个ASIN

### 代码示例

```python
from src.amazon_actuary_final import generate_final_report

# 单一产品数据
products = [{
    'asin': 'B0XXX12345',
    'title': 'Single Product',
    'stars': 4.3,
    'reviews': 500,
    # ... Keepa数据
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

### 报告输出
- 单变体利润分析
- 自然vs广告订单对比
- 基于163指标的投资建议

---

## 多变体链接分析

**这是系统最强大的功能！** 对于有多个颜色/尺寸变体的产品，必须分析所有变体。

### 为什么必须分析所有变体?

1. **帕累托效应**: 通常2-3个变体贡献80%销量
2. **成本差异**: 不同颜色/尺寸的COGS可能不同
3. **广告依赖**: 热门颜色可能自然流量高，冷门颜色依赖广告
4. **风险分散**: 避免只看到一个变体而误判整个链接

### 如何获取所有变体ASIN?

#### 方法1: 亚马逊前台手动获取 (推荐)

```
1. 打开产品详情页
2. 找到"Color"或"Size"下拉菜单
3. 切换不同选项，观察URL变化:
   
   黑色: amazon.com/dp/B0F6B5R47Q
   棕色: amazon.com/dp/B0F6B5R47R  ← 记录这个ASIN
   红色: amazon.com/dp/B0F6B5R47W  ← 记录这个ASIN

4. 记录所有变体的ASIN
```

#### 方法2: 使用Keepa Product Viewer

```
1. 打开Keepa网站
2. 搜索父ASIN
3. 查看"Variations"标签页
4. 导出所有变体ASIN列表
```

### 完整代码示例

```python
from src.amazon_actuary_final import generate_final_report
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================
# 步骤1: 准备所有变体的Keepa数据
# ============================================

# 变体ASIN列表
variants = [
    {'asin': 'B0F6B5R47Q', 'color': 'Black', 'size': 'Standard'},
    {'asin': 'B0F6B5R47R', 'color': 'Brown', 'size': 'Standard'},
    {'asin': 'B0F6B5R47W', 'color': 'Wine Red', 'size': 'Standard'},
    {'asin': 'B0F6B5R47L', 'color': 'Black', 'size': 'Large'},
    {'asin': 'B0F6B5R47S', 'color': 'Brown', 'size': 'Small'},
]

# 从Keepa API获取的数据 (简化示例)
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
            # 这里应该是真实的Keepa时间序列数据
            'df_SALES': create_mock_bsr_data(rank=15000),
            'df_NEW': create_mock_price_data(price=27.99),
        }
    })

# ============================================
# 步骤2: 准备真实COGS和订单来源数据
# ============================================

financials_map = {
    # 黑色标准款 - 畅销，自然流量高
    'B0F6B5R47Q': {
        'cogs': 9.50,          # 从供应商报价单
        'organic_pct': 0.70,   # 从广告后台
        'ad_pct': 0.30,
    },
    # 棕色标准款 - 中等销量
    'B0F6B5R47R': {
        'cogs': 9.50,
        'organic_pct': 0.55,
        'ad_pct': 0.45,
    },
    # 酒红色 - 小众，需广告
    'B0F6B5R47W': {
        'cogs': 10.20,         # 红色皮革更贵
        'organic_pct': 0.35,
        'ad_pct': 0.65,
    },
    # 大尺寸 - 销量低但利润好
    'B0F6B5R47L': {
        'cogs': 11.80,
        'organic_pct': 0.60,
        'ad_pct': 0.40,
    },
    # 小尺寸 - 测试市场
    'B0F6B5R47S': {
        'cogs': 8.20,
        'organic_pct': 0.75,
        'ad_pct': 0.25,
    },
}

# ============================================
# 步骤3: 生成精算师报告
# ============================================

report_path, analysis = generate_final_report(
    parent_asin='B0F6B5R47Q',
    products=products,
    financials_map=financials_map,
    output_path='cache/reports/my_product_ACTUARY_FINAL.html',
    tacos_rate=0.15
)

# ============================================
# 步骤4: 查看分析结果
# ============================================

print(f"\n📊 分析完成!")
print(f"报告路径: {report_path}")
print(f"\n整体决策: {analysis.overall_decision.decision}")
print(f"置信度: {analysis.overall_decision.confidence}%")
print(f"总月利润: ${analysis.total_monthly_profit:,.2f}")
print(f"混合利润率: {analysis.blended_portfolio_margin_pct:.1f}%")

print(f"\n📈 变体表现:")
for i, v in enumerate(analysis.variants, 1):
    print(f"  #{i} {v.asin} [{v.metrics.color}]")
    print(f"      月销量: {v.estimated_monthly_sales}")
    print(f"      利润率: {v.blended_margin_pct:.1f}%")
    print(f"      决策: {v.decision.decision}")
```

---

## 数据输入指南

### COGS数据来源

| 成本项 | 来源 | 获取方式 |
|--------|------|----------|
| 产品采购价 | 供应商 | 1688/Alibaba报价单 |
| 头程运费 | 货代 | 海运/空运报价 |
| 关税 | 海关 | 产品HS编码查询 |
| 质检费 | 第三方 | 质检公司报价 |
| 其他 | 内部 | 包装、贴标等 |

### 订单来源数据来源

**亚马逊广告后台**:
1. 登录 Seller Central
2. 广告 → 广告活动管理
3. 点击"测量和分析"
4. 查看"广告销售额"和"总销售额"
5. 计算: 广告订单% = 广告销售额 / 总销售额

**业务报告**:
1. 数据报告 → 业务报告
2. 查看"子商品详情页上的销售量与访问量"
3. 对比"已订购商品数量"和广告报告

### Keepa API数据

系统自动从Keepa API获取163个指标，包括：
- 销售排名历史
- 价格历史
- Buy Box数据
- 评论数据
- 库存数据
- 卖家竞争数据

---

## 报告解读

### 执行摘要部分

```
🟢 建议进行 (置信度: 75%)

关键指标:
- 总月销量: 1,486
- 总月销售额: $42,516
- 总月利润: $10,048
- 混合利润率: 23.6%
- 自然订单占比: 58%
```

**解读**: 
- ✅ 利润率>20%，健康
- ⚠️ 自然订单58%，可提升至70%
- 整体建议进行，但需优化广告效率

### 帕累托分析部分

```
核心发现: 前3个变体贡献80%销量
核心变体: B0F6B5R47Q, B0F6B5R47R, B0F6B5R47W
长尾变体: B0F6B5R47L, B0F6B5R47S
```

**行动建议**:
1. 优先保证核心变体库存
2. 长尾变体可考虑减少SKU

### 风险评估部分

```
⚠️ 高广告依赖 (1个)
ASIN: B0F6B5R47W (酒红色)
广告订单占比: 65%
```

**行动建议**:
- 开展站外推广提升自然流量
- 优化Listing提升转化率

---

## 常见问题

### Q: 为什么置信度不是100%?

**A:** 置信度基于以下因素：
- 数据完整度 (163指标中有多少可用)
- 历史数据长度 (90天 vs 365天)
- 数据一致性 (价格/排名是否稳定)
- 风险因素数量

一般75%以上即可认为是可靠决策。

### Q: 混合利润率多少算好?

| 利润率 | 评价 | 建议 |
|--------|------|------|
| >25% | 优秀 | 可以加大投入 |
| 15-25% | 良好 | 正常运营 |
| 5-15% | 一般 | 需要优化 |
| <5% | 危险 | 考虑退出 |
| <0% | 亏损 | 立即停止 |

### Q: 如何处理亏损变体?

**步骤**:
1. 确认COGS数据准确
2. 尝试提价10-20%测试
3. 优化以降低退货率
4. 如果仍亏损，考虑停售

### Q: 为什么我的实际利润和报告不同?

**可能原因**:
1. COGS输入不准确
2. 销量估算有偏差 (BSR模型限制)
3. 广告费用波动
4. 退货率变化

**建议**: 运行一个月后对比，用真实数据校准。

### Q: 可以分析竞品吗?

**A:** 可以！但注意：
- 无法获取竞品COGS (只能估算)
- 无法获取竞品订单来源
- 主要用于竞争格局分析

---

## 最佳实践

### 1. 月度复盘

每月初运行一次分析，对比：
- 实际销售额 vs 预测
- 实际利润 vs 预测
- COGS是否有变化
- 广告费用是否优化

### 2. A/B测试

对于高广告依赖变体：
1. 保持原样运行2周
2. 优化Listing后运行2周
3. 对比自然订单占比变化
4. 计算ROI提升

### 3. 季节性调整

某些产品有明显季节性：
- 提前2个月备货
- 旺季前加大广告投入
- 淡季优化自然排名

---

## 技术支持

遇到问题？

1. 检查Keepa API Key是否有效
2. 确认COGS数据格式正确 (float)
3. 确认订单占比总和为1.0 (organic_pct + ad_pct = 1.0)
4. 查看 `cache/reports/` 目录是否有生成文件

---

**文档版本**: v3.0 | **最后更新**: 2026-02-15
