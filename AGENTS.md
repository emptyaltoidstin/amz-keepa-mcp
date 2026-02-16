# Amz-Keepa-MCP Agent 指南

## 项目定位

**Amz-Keepa-MCP** 是一个专业的亚马逊产品分析 MCP 服务，核心能力：

```
ASIN → 采集163个Keepa指标 → 精算师深度分析 → 生成HTML报告
```

**典型使用场景**:
- 快速评估一个ASIN的市场潜力和风险
- 获取产品的完整数据画像(价格、排名、竞争、评价等)
- 基于数据生成专业的分析报告

## 技术栈

- **Python 3.11+**
- **MCP SDK** - Model Context Protocol 服务端
- **Keepa API** - 亚马逊历史数据
- **Pandas/NumPy** - 数据处理

## 项目结构

```
amz-keepa-mcp/
├── server.py                    # MCP Server 主文件
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
├── run.sh                       # 启动脚本
├── test_installation.py         # 安装测试
├── README.md                    # 用户文档
├── AGENTS.md                    # 本文件
├── docs/                        # 文档
│   └── Keepa_API_Guide.md       # Keepa API完全指南
├── src/                         # 核心模块
│   ├── __init__.py
│   ├── keepa_metrics_collector.py   # 163指标采集器
│   ├── keepa_advanced_analyzer.py   # 高级数据分析 ⭐ NEW
│   ├── visualizer_advanced.py       # 高级可视化 ⭐ NEW
│   ├── deep_factor_miner.py         # 深度因子挖掘
│   ├── market_actuary_v2.py         # 市场可行性分析
│   ├── report_generator.py          # 简化HTML报告生成器
│   └── cache_manager.py             # Token缓存
└── cache/                       # 缓存目录
    ├── keepa_cache.db           # SQLite缓存
    ├── charts/                  # 生成的图表
    └── reports/                 # 分析报告输出
```

## 核心模块

### server.py

MCP Server 入口，提供以下工具:

| 工具名 | 用途 |
|--------|------|
| `generate_html_analysis_report` | **核心工作流**：采集163指标 → 深度分析 → HTML报告 |
| `analyze_asin_deep` | **深度分析**：价格趋势/销售排名/竞争格局/风险检测 |
| `analyze_asin_actuarial` | 精算师级分析（盈利模型/蒙特卡洛模拟） |
| `analyze_cosmo_intent` | COSMO五点意图分析 |
| `get_token_status` | 查看Keepa Token状态 |

**推荐使用流程**:
```
1. analyze_asin_deep(...)           # 获取深度分析+图表
2. generate_html_analysis_report(...)  # 生成完整HTML报告
```

### src/keepa_metrics_collector.py

163指标采集器 - 从Keepa API提取完整数据:

```python
from src.keepa_metrics_collector import KeepaMetricsCollector

collector = KeepaMetricsCollector()
metrics = collector.collect_all_metrics(product)
collector.to_csv(f"cache/reports/{asin}_163_metrics.csv")
```

**指标分类**:
- 价格数据 (Buy Box/New/Used/Amazon Current + 历史平均)
- 销售排名 (Current/Avg/Drops/Percentage)
- 卖家竞争 (Offer Count/FBA/FBM/Winner)
- 评价反馈 (Reviews/Ratings/Return Rate)
- 产品属性 (Brand/Category/Variation)
- 包装规格 (Length/Width/Height/Weight)
- 内容资产 (Videos/A+ Content)
- 促销数据 (Deals/Coupons)

### src/deep_factor_miner.py

深度因子挖掘引擎 - 6维度分析:

```python
from src.deep_factor_miner import DeepFactorMiner

miner = DeepFactorMiner()
factors = miner.mine_all_factors(product_data)
# 返回: 运营健康度/选品质量/竞争态势/风险预警/增长潜力/运营效率
```

**输出示例**:
```python
{
    'operational_health': FactorScore(score=65, weight=0.20, ...),
    'selection_quality': FactorScore(score=72, weight=0.15, ...),
    'competition_landscape': FactorScore(score=58, weight=0.20, ...),
    'risk_warning': FactorScore(score=35, weight=0.15, ...),
    'growth_potential': FactorScore(score=45, weight=0.15, ...),
    'operational_efficiency': FactorScore(score=40, weight=0.15, ...)
}
```

### src/market_actuary_v2.py

市场可行性分析 - 替代不可靠的利润预测:

```python
from src.market_actuary_v2 import MarketActuaryV2

actuary = MarketActuaryV2()
report = actuary.generate_comprehensive_report(product_data)
```

**分析维度**:
- 需求评估 (销量趋势、季节性)
- 竞争分析 (卖家数量、Buy Box竞争)
- 价格稳定性 (波动率、趋势)
- 供应链健康度 (库存、断货风险)

**重要原则**: 不提供具体利润数字，而是给出可行性评分和风险提示。

### src/keepa_advanced_analyzer.py ⭐ NEW

基于Keepa API完整数据的高级分析器:

```python
from src.keepa_advanced_analyzer import KeepaAdvancedAnalyzer

analyzer = KeepaAdvancedAnalyzer()
analysis = analyzer.analyze_product(product)
```

**分析维度**:
- **产品身份**: ASIN/品牌/类目/包装尺寸/图片数量
- **价格分析**: 多维度价格趋势(NEW/Amazon/Used/Buy Box)/波动率
- **销售分析**: 排名趋势/估算销量/销售健康度  
- **竞争分析**: 卖家数/FBA vs FBM/卖家集中度(HHI)/Amazon参与
- **评分分析**: 星级趋势/评论增长/评分健康度
- **Buy Box分析**: Buy Box稳定性/Amazon占比
- **季节性**: 需求周期识别/峰值月份
- **风险信号**: 价格战/排名下滑/断货/差评/卖家激增

### src/visualizer_advanced.py ⭐ NEW

高级可视化模块:

```python
from src.visualizer_advanced import generate_all_charts

charts = generate_all_charts(product, days=90)
# 返回: price_trend/sales_rank/offer_count/rating 图表(Base64)
```

**图表类型**:
- 价格趋势图 (多价格类型对比)
- 销售排名图 (对数刻度+移动平均线)
- 卖家数量趋势图
- 评分与评论增长图

### src/report_generator.py

简化版HTML报告生成器:

```python
from src.report_generator import generate_html_report

generate_html_report(
    asin=asin,
    product_data=product_data,
    factors=factors,
    market_report=market_report,
    output_path="report.html"
)
```

**报告结构**:
1. 产品概览 (ASIN/标题/品牌)
2. 关键指标卡片 (价格/排名/卖家数/评分)
3. 深度因子评分 (6维度进度条)
4. 市场可行性评估
5. 163指标详情表 (可折叠)
6. 决策建议

## 标准使用流程

### 推荐：深度分析 + HTML报告

```python
# Step 1: 执行深度分析 (包含图表生成)
result = await analyze_asin_deep(asin="B0XXXXXX", include_charts=True)
# 返回: 详细分析报告 + 图表路径列表

# Step 2: 生成专业HTML报告
html_result = await generate_html_analysis_report(asin="B0XXXXXX")
# 返回: HTML报告路径
```

### 单独使用分析功能

```python
# 仅深度分析 (含图表)
analysis = await analyze_asin_deep(asin="B0XXXXXX")

# 仅生成HTML报告 (需要已有CSV数据)
html_path = await generate_html_analysis_report(asin="B0XXXXXX")

# 精算师级分析 (盈利模型/蒙特卡洛)
actuarial = await analyze_asin_actuarial(asin="B0XXXXXX")

# COSMO意图分析
cosmo = await analyze_cosmo_intent(asin="B0XXXXXX")
```
```

## 输出文件

### CSV文件
路径: `cache/reports/{ASIN}_163_metrics.csv`

包含161-163个字段，涵盖:
- 当前价格和历史平均
- 销售排名和变动
- 卖家数量和竞争度
- 评价数量和评分
- 产品属性和规格

### HTML报告
路径: `cache/reports/{ASIN}_analysis_report.html`

包含:
- 可视化指标卡片
- 6维度因子评分图
- 完整指标表格(可折叠)
- 风险警告
- 决策建议

## 配置

### 环境变量
```bash
KEEPA_KEY=your_api_key          # 必需
KEEPA_DOMAIN=US                 # 默认US
CACHE_ENABLED=true              # 默认true
CACHE_TTL_HOURS=24              # 默认24
```

### Claude Desktop 配置
```json
{
  "mcpServers": {
    "amz-keepa-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "KEEPA_KEY": "your_key"
      }
    }
  }
}
```

## 调试

### 本地测试
```bash
# 1. 设置环境变量
export KEEPA_KEY="your_key"

# 2. 运行测试
python test_installation.py

# 3. 启动Server
python server.py
```

### 测试指标采集
```python
python -c "
from src.keepa_metrics_collector import KeepaMetricsCollector
import keepa
api = keepa.Keepa('your_key')
products = api.query(['B0F6B5R47Q'])
collector = KeepaMetricsCollector()
metrics = collector.collect_all_metrics(products[0])
print(f'采集了 {len(metrics)} 个指标')
"
```

## 核心原则

1. **数据驱动**: 所有结论基于Keepa API的163个指标
2. **诚实分析**: 不预测无法验证的利润，只分析可观测的信号
3. **风险提示**: 重点识别风险信号(需求下滑、竞争加剧等)
4. **简洁报告**: HTML报告清晰展示关键指标和分析结论

## 参考资源

- [Keepa API 文档](https://keepa.com/#!discuss/t/request-products)
- [MCP 文档](https://modelcontextprotocol.io/)
- [Keepa Python 客户端](https://github.com/akaszynski/keepa)
