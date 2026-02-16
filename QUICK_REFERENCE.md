# Amz-Keepa-MCP 快速参考卡片

## 🚀 3分钟上手

```python
# 1. 导入
from src import auto_analyze

# 2. 提供COGS数据
financials = {
    'B0XXXYYYYY': {
        'cogs': 8.50,        # 真实采购成本
        'organic_pct': 0.65, # 自然订单占比
        'ad_pct': 0.35,      # 广告订单占比
    },
}

# 3. 一键分析
report, analysis, info = auto_analyze(
    asin='B0XXXYYYYY',
    financials_map=financials
)

# 4. 查看结果
print(f"决策: {analysis.overall_decision.decision}")
print(f"月利润: ${analysis.total_monthly_profit:,.2f}")
print(f"报告: {report}")
```

---

## 📊 核心功能速览

| 功能 | 说明 | 代码 |
|------|------|------|
| **自动变体采集** | 输入1个ASIN，自动发现所有变体 | `auto_analyze(asin)` |
| **163指标采集** | 完整Keepa Product Viewer数据 | 自动集成 |
| **智能销量分配** | 按BSR比例分配父ASIN总销量 | 自动处理 |
| **TACOS模型** | 真实广告成本计算 | 内置计算 |
| **数据驱动决策** | 自动生成投资建议 | `analysis.overall_decision` |
| **中文报告** | 163指标汉化 + 高级UI | 自动生成 |

---

## 💰 关键计算公式

### TACOS广告成本
```
单位广告成本 = (月销售额 × TACOS) / 月广告订单数

示例:
- 月销售额: $13,575
- TACOS: 15%
- 月广告订单: 146
- 单位广告成本 = ($13,575 × 15%) / 146 = $13.95
```

### 混合利润率
```
混合利润率 = (自然利润 × 自然占比 + 广告利润 × 广告占比) / 价格

示例:
- 自然利润: $10.00 (占比70%)
- 广告利润: $-3.99 (占比30%)
- 价格: $27.99
- 混合利润率 = ($10×0.7 + $-3.99×0.3) / $27.99 = 20.7%
```

### BSR销量估算
```
BSR < 1,000:   销量 = 1500 × (1000/BSR)^0.5
BSR < 10,000:  销量 = 800 × (10000/BSR)^0.5
BSR < 50,000:  销量 = 300 × (50000/BSR)^0.5
BSR > 100,000: 销量 = 50 × (100000/BSR)^0.5
```

---

## 📋 决策标准

| 决策 | 条件 | 置信度 |
|------|------|--------|
| ✅ **建议投资** | 利润率>15% & 风险因素<3 | 75%+ |
| ⚠️ **谨慎考虑** | 利润率5-15% 或 风险因素3+ | 60-75% |
| ❌ **建议避免** | 利润率<5% 或 亏损 | <60% |

---

## 🔧 常用API

### 变体采集
```python
from src.variant_auto_collector import VariantAutoCollector

collector = VariantAutoCollector(api_key)
variants, parent_info = collector.collect_variants('B0XXX')

# 打印摘要
print(collector.format_variants_summary(variants))

# 获取属性
for v in variants:
    attrs = collector.get_variation_attributes(v)
    print(f"{v['asin']}: {attrs}")
```

### 163指标
```python
from src.keepa_metrics_collector import KeepaMetricsCollector

collector = KeepaMetricsCollector()
metrics = collector.collect_all_metrics(product)

# 检查数据完整度
completeness = collector.calculate_data_completeness(metrics)
print(f"数据完整度: {completeness:.0f}%")
```

### 自定义分析
```python
from src.amazon_actuary_final import generate_final_report

report_path, analysis = generate_final_report(
    parent_asin='B0PARENT',
    products=products,           # Keepa产品数据
    financials_map=financials,   # 财务数据
    tacos_rate=0.15              # TACOS比例
)
```

---

## 📁 输出文件

| 文件 | 位置 | 说明 |
|------|------|------|
| 中文报告 | `cache/reports/{ASIN}_CHINESE_FULL_REPORT.html` | 完整分析报告 |
| Premium报告 | `cache/reports/{ASIN}_PREMIUM.html` | 高级UI报告 |
| CSV数据 | `cache/reports/{ASIN}_163_metrics.csv` | 原始数据导出 |
| 图表 | `cache/charts/{ASIN}_*.png` | 可视化图表 |

---

## 🎨 报告内容

### 中文报告包含
1. **执行摘要** - 投资决策 + 置信度
2. **关键指标** - 利润/利润率/销量/变体数
3. **变体分析** - 9个变体详细对比
4. **163指标** - 完整汉化指标展示
5. **数据来源** - 原始Keepa数据透明
6. **计算逻辑** - 销量分配过程可视化

---

## ⚡ 故障排除

### 问题1: API限流
```
症状: "Waiting XXX seconds for additional tokens"
解决: 正常现象，系统会自动等待
```

### 问题2: 无变体数据
```
症状: "未找到变体数据"
解决: 
1. 确认ASIN正确
2. 检查产品是否有变体
3. 尝试查询父ASIN
```

### 问题3: 销量估算偏差大
```
症状: 估算销量与实际差距大
解决:
1. 用自己的产品校准模型
2. 调整BSR-销量映射参数
3. 优先使用boughtInPastMonth真实数据
```

---

## 📚 相关文档

| 文档 | 内容 |
|------|------|
| `PROJECT_SUMMARY.md` | 完整项目总结 |
| `METRICS_DICTIONARY.md` | 163指标中文词典 |
| `SALES_ESTIMATION_GUIDE.md` | 销量估算指南 |
| `USAGE_GUIDE.md` | 详细使用指南 |
| `README.md` | 项目说明 |

---

## 💡 最佳实践速查

### ✅ 应该做
- [ ] 使用真实COGS数据
- [ ] 从广告后台获取订单来源比例
- [ ] 每月复盘校准模型
- [ ] 优先分析所有变体而非单个

### ❌ 不应该做
- [ ] 估算COGS (宁可等供应商报价)
- [ ] 只看单一ASIN分析
- [ ] 忽视高广告依赖变体的风险
- [ ] 忽略帕累托分析的长尾变体

---

## 🎯 决策检查清单

在做出投资决策前，确认:

- [ ] 所有变体的真实COGS已输入
- [ ] 订单来源比例来自广告后台
- [ ] 163指标数据完整度>80%
- [ ] 帕累托分析已识别核心变体
- [ ] 风险评估无重大风险项
- [ ] 预期ROI符合投资目标

---

## 📞 快速命令

```bash
# 激活环境
cd /Users/blobeats/Downloads/amz-keepa-mcp
source venv/bin/activate

# 设置API Key
export KEEPA_KEY="your_key_here"

# 运行分析
python3 -c "from src import auto_analyze; auto_analyze('B0XXX')"

# 查看报告
open cache/reports/*.html
```

---

**记住核心原则**: 
> 能用真实数据就不用估算  
> 必须估算时要知晓误差范围  
> 所有决策必须基于数据支撑

---

**版本**: v3.0 | **更新**: 2026-02-16
