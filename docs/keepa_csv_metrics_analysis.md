# Keepa Product Viewer CSV 指标分析

## 概述

Keepa Product Viewer导出包含**163个字段**的完整产品指标，可分为以下核心维度：

---

## 📊 指标分类（MECE）

### 1. 基础信息 (Basic Info) - 18个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| Locale | 市场代码 | ⭐ |
| ASIN | 产品ID | ⭐⭐⭐ |
| Title | 标题 | ⭐⭐ |
| Parent Title | 父标题 | ⭐ |
| Brand | 品牌 | ⭐⭐ |
| Manufacturer | 制造商 | ⭐ |
| Product Group | 产品组 | ⭐ |
| Category Tree | 类目路径 | ⭐⭐ |
| Model | 型号 | ⭐ |
| Binding | 绑定类型 | ⭐ |
| Tracking since | 追踪起始 | ⭐ |
| Listed since | 上架日期 | ⭐⭐ |

### 2. 销售表现 (Sales Performance) - 8个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| Sales Rank: Current | 当前BSR | ⭐⭐⭐ |
| Sales Rank: 90 days avg. | 90天平均BSR | ⭐⭐⭐ |
| Sales Rank: Drops last 90 days | 90天排名下降次数 | ⭐⭐⭐ |
| Bought in past month | 过去30天销量 | ⭐⭐⭐ |
| 90 days change % monthly sold | 销量变化率 | ⭐⭐⭐ |
| Return Rate | 退货率 | ⭐⭐⭐ |
| Sales Rank: Reference | 参考类目 | ⭐ |
| Sales Rank: Subcategory Sales Ranks | 子类目排名 | ⭐⭐ |

### 3. 价格数据 (Pricing) - 35+个字段

#### Buy Box价格
- Buy Box: Current
- Buy Box: 90 days avg.
- Buy Box: Strikethrough Price
- Buy Box: Standard Deviation 90 days
- Buy Box: Flipability 90 days

#### Amazon自营价格
- Amazon: Current
- Amazon: 30/90/180/365 days avg.
- Amazon: Lowest/Highest
- Amazon: Stock
- Amazon: 90 days OOS

#### 新品价格
- New: Current
- New: 30/90/180/365 days avg.
- New: Lowest/Highest

#### 其他价格
- List Price: Current/avg.
- Lightning Deals: Current
- Warehouse Deals: Current/avg.
- Used: Current/avg.

### 4. 竞争分析 (Competition) - 15个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| Buy Box: Buy Box Seller | Buy Box卖家 | ⭐⭐⭐ |
| Buy Box: Is FBA | 是否FBA | ⭐⭐ |
| Buy Box: % Amazon 90 days | Amazon占比 | ⭐⭐⭐ |
| Buy Box: % Top Seller 90 days | 头部卖家占比 | ⭐⭐ |
| Buy Box: Winner Count 90 days | Buy Box切换次数 | ⭐⭐ |
| Total Offer Count | 总offer数 | ⭐⭐⭐ |
| Count of retrieved live offers: New, FBA | FBA卖家数 | ⭐⭐⭐ |
| Count of retrieved live offers: New, FBM | FBM卖家数 | ⭐⭐⭐ |
| New Offer Count: Current | 新品卖家数 | ⭐⭐ |
| Used Offer Count: Current | 二手卖家数 | ⭐ |

### 5. 评论质量 (Reviews) - 5个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| Reviews: Rating | 评分 | ⭐⭐⭐ |
| Reviews: Rating Count | 评论数 | ⭐⭐⭐ |
| Reviews: Review Count - Format Specific | 格式特定评论 | ⭐ |
| Reviews: Rating - 30 days avg. | 30天平均评分 | ⭐⭐ |
| Reviews: Rating Count - 90 days avg. | 90天平均评论 | ⭐⭐ |

### 6. 费用结构 (Fees) - 5个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| FBA Pick&Pack Fee | FBA处理费 | ⭐⭐⭐ |
| Referral Fee % | 佣金比例 | ⭐⭐⭐ |
| Referral Fee based on current Buy Box price | 佣金金额 | ⭐⭐ |
| Suggested Lower Price | 建议降价 | ⭐ |
| Business Discount: Percentage | 企业折扣 | ⭐ |

### 7. 库存健康 (Inventory) - 8个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| Amazon: Stock | Amazon库存 | ⭐⭐ |
| Amazon: 90 days OOS | 90天断货率 | ⭐⭐⭐ |
| Amazon: OOS Count 30 days | 30天断货次数 | ⭐⭐ |
| Amazon: OOS Count 90 days | 90天断货次数 | ⭐⭐ |
| Amazon: Availability | 可用性 | ⭐⭐ |
| Buy Box: Prime Eligible | Prime资格 | ⭐⭐ |
| Buy Box: Subscribe & Save | 订阅节省 | ⭐ |

### 8. 内容质量 (Content) - 15个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| Image Count | 图片数 | ⭐⭐ |
| Videos: Video Count | 视频数 | ⭐⭐ |
| Videos: Has Main Video | 主视频 | ⭐⭐ |
| A+ Content: Has A+ Content | A+内容 | ⭐⭐ |
| A+ Content: A+ From Manufacturer | 制造商A+ | ⭐ |
| Description & Features: Feature 1-10 | 产品卖点 | ⭐⭐ |

### 9. 物流规格 (Dimensions) - 10个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| Package: Length/Width/Height (cm) | 包装尺寸 | ⭐⭐⭐ |
| Package: Weight (g) | 包装重量 | ⭐⭐⭐ |
| Package: Dimension (cm³) | 包装体积 | ⭐⭐ |
| Item: Length/Width/Height (cm) | 产品尺寸 | ⭐⭐ |
| Item: Weight (g) | 产品重量 | ⭐⭐ |

### 10. 营销促销 (Marketing) - 8个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| Lightning Deals: Current | 秒杀 | ⭐⭐ |
| Deals: Deal Type | 促销类型 | ⭐⭐ |
| Deals: Badge | 徽章 | ⭐ |
| One Time Coupon: Absolute/Percentage | 优惠券 | ⭐⭐ |
| Warehouse Deals: Current/avg. | 仓库 deals | ⭐ |

### 11. 产品变体 (Variations) - 5个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| Parent ASIN | 父ASIN | ⭐⭐ |
| Variation ASINs | 变体列表 | ⭐⭐ |
| Variation Attributes | 变体属性 | ⭐ |
| Color | 颜色 | ⭐ |
| Size | 尺寸 | ⭐ |

### 12. 供应链 (Supply Chain) - 10个字段

| 字段 | 说明 | 重要性 |
|------|------|--------|
| Buy Box: Shipping Country | 发货国 | ⭐⭐ |
| Amazon: Amazon offer shipping delay | 发货延迟 | ⭐⭐ |
| Is HazMat | 危险品 | ⭐⭐⭐ |
| Is heat sensitive | 热敏感 | ⭐ |
| Batteries Required/Included | 电池 | ⭐ |

---

## 🎯 精算师关注的核心指标

### A. 盈利能力指标 (Profitability)
```
利润 = 售价 - COGS - FBA费 - 佣金 - 其他费用

关键输入：
- Buy Box价格 (当前/历史)
- FBA Pick&Pack Fee
- Referral Fee %
- Package Weight (影响FBA费)
- Return Rate (影响退货成本)
```

### B. 需求强度指标 (Demand)
```
需求评分 = f(销量, 排名趋势, 季节性)

关键输入：
- Bought in past month
- 90 days change % monthly sold
- Sales Rank: Current vs avg
- Sales Rank: Drops count
```

### C. 竞争强度指标 (Competition)
```
竞争评分 = f(卖家数, Amazon占比, Buy Box稳定性)

关键输入：
- Total Offer Count
- Buy Box: % Amazon 90 days
- Buy Box: Winner Count 90 days
- Buy Box: Is FBA (是否FBA竞争)
```

### D. 风险评估指标 (Risk)
```
风险评分 = f(退货率, 断货率, 价格 volatility)

关键输入：
- Return Rate
- Amazon: 90 days OOS
- Price Standard Deviation
- Buy Box: Flipability
```

---

## 🔧 MCP扩展方案

### 方案1: CSV导入器 (CSV Importer Tool)
```python
@mcp.tool()
async def import_keepa_csv(csv_path: str, ctx: Context) -> str:
    """导入Keepa Product Viewer CSV文件进行全面分析"""
    pass
```

### 方案2: 扩展数据采集 (Extended Data Collection)
```python
# 在现有process_product基础上增加CSV字段映射
csv_field_mapping = {
    'salesRank': ['Sales Rank: Current', 'Sales Rank: 90 days avg.'],
    'buyBox': ['Buy Box: Current', 'Buy Box: % Amazon 90 days'],
    'fees': ['FBA Pick&Pack Fee', 'Referral Fee %'],
    # ...更多映射
}
```

### 方案3: 精算师分析模块 (Actuarial Analysis)
```python
class ActuarialAnalyzer:
    def calculate_profit_score(self, data):
        # 精算级盈利评分
        pass
    
    def calculate_risk_adjusted_return(self, data):
        # 风险调整收益
        pass
    
    def monte_carlo_simulation(self, data, iterations=1000):
        # 蒙特卡洛模拟
        pass
```
