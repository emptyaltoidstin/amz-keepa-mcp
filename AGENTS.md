# Amz-Keepa-MCP Agent Guide

## Project positioning

**Amz-Keepa-MCP** It is a professional Amazon product analysis MCP service with core capabilities:

```
ASIN → Collect 163 Keepa indicators → In-depth analysis by actuaries → Generate HTML report
```

**Typical usage scenarios**:
- Quickly assess an ASIN’s market potential and risks
- Get a complete picture of the product(Price, ranking, competition, reviews, etc.)
- Generate professional analysis reports based on data

## technology stack

- **Python 3.11+**
- **MCP SDK** - Model Context Protocol server
- **Keepa API** - Amazon historical data
- **Pandas/NumPy** - Data processing

## Project structure

```
amz-keepa-mcp/
├── server.py                    # MCP Server Master File
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── run.sh                       # startup script
├── test_installation.py         # Installation test
├── README.md                    # User documentation
├── AGENTS.md                    # this document
├── docs/                        # document
│   └── Keepa_API_Guide.md       # Complete Guide to Keepa API
├── src/                         # core module
│   ├── __init__.py
│   ├── keepa_metrics_collector.py   # 163 indicator collector
│   ├── keepa_advanced_analyzer.py   # Advanced Data Analysis ⭐ NEW
│   ├── visualizer_advanced.py       # Advanced Visualization ⭐ NEW
│   ├── deep_factor_miner.py         # Deep factor mining
│   ├── market_actuary_v2.py         # Market feasibility analysis
│   ├── report_generator.py          # Simplified HTML report generator
│   └── cache_manager.py             # Token cache
└── cache/                       # cache directory
    ├── keepa_cache.db           # SQLite cache
    ├── charts/                  # generated chart
    └── reports/                 # Analysis report output
```

## core module

### server.py

MCP Server entrance, providing the following tools:

| Tool name | use |
|--------|------|
| `generate_html_analysis_report` | **core workflow**: Collect 163 indicators → In-depth analysis → HTML report |
| `analyze_asin_deep` | **In-depth analysis**: Price trend/sales ranking/competitive landscape/Risk detection |
| `analyze_asin_actuarial` | Actuarial level analysis (profit modeling/Monte Carlo simulation) |
| `analyze_cosmo_intent` | COSMO five-point intention analysis |
| `get_token_status` | Check Keepa Token status |

**Recommended usage process**:
```
1. analyze_asin_deep(...)           # Get in-depth analysis+chart
2. generate_html_analysis_report(...)  # Generate full HTML report
```

### src/keepa_metrics_collector.py

163 indicator collector - Extract complete data from Keepa API:

```python
from src.keepa_metrics_collector import KeepaMetricsCollector

collector = KeepaMetricsCollector()
metrics = collector.collect_all_metrics(product)
collector.to_csv(f"cache/reports/{asin}_163_metrics.csv")
```

**Indicator classification**:
- price data (Buy Box/New/Used/Amazon Current + historical average)
- sales ranking (Current/Avg/Drops/Percentage)
- Seller competition (Offer Count/FBA/FBM/Winner)
- Evaluation feedback (Reviews/Ratings/Return Rate)
- Product attributes (Brand/Category/Variation)
- Packaging specifications (Length/Width/Height/Weight)
- content assets (Videos/A+ Content)
- Promotional data (Deals/Coupons)

### src/deep_factor_miner.py

Deep factor mining engine - 6 dimensions analysis:

```python
from src.deep_factor_miner import DeepFactorMiner

miner = DeepFactorMiner()
factors = miner.mine_all_factors(product_data)
# return: operational health/Selection quality/competitive situation/Risk warning/growth potential/operational efficiency
```

**Output example**:
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

Market feasibility analysis - Replace unreliable profit forecasts:

```python
from src.market_actuary_v2 import MarketActuaryV2

actuary = MarketActuaryV2()
report = actuary.generate_comprehensive_report(product_data)
```

**Analysis Dimensions**:
- needs assessment (Sales trends, seasonality)
- competitive analysis (Number of sellers, Buy Box competition)
- price stability (volatility, trend)
- Supply chain health (Inventory and out-of-stock risk)

**important principles**: No specific profit figures are provided, but feasibility scores and risk tips are given.

### src/keepa_advanced_analyzer.py ⭐ NEW

Advanced analyzer based on Keepa API complete data:

```python
from src.keepa_advanced_analyzer import KeepaAdvancedAnalyzer

analyzer = KeepaAdvancedAnalyzer()
analysis = analyzer.analyze_product(product)
```

**Analysis Dimensions**:
- **product identity**: ASIN/brand/Category/Packing size/Number of pictures
- **price analysis**: Multidimensional price trends(NEW/Amazon/Used/Buy Box)/Volatility
- **sales analysis**: Ranking trends/Estimated sales/sales health  
- **competitive analysis**: Number of sellers/FBA vs FBM/Seller concentration(HHI)/Amazon participates
- **Rating analysis**: star trend/Comment growth/Rating health
- **Buy Box Analysis**: Buy Box stability/Amazon’s share
- **Seasonal**: Demand cycle identification/peak month
- **risk signal**: price war/Ranking decline/Out of stock/Bad review/Seller surge

### src/visualizer_advanced.py ⭐ NEW

Advanced visualization module:

```python
from src.visualizer_advanced import generate_all_charts

charts = generate_all_charts(product, days=90)
# return: price_trend/sales_rank/offer_count/rating chart(Base64)
```

**chart type**:
- price trend chart (Compare multiple price types)
- Sales ranking chart (Logarithmic scale+moving average)
- Seller number trend chart
- Ratings and comments growth chart

### src/report_generator.py

Simplified HTML report generator:

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

**Report structure**:
1. Product Overview (ASIN/title/brand)
2. Key indicator card (price/Ranking/Number of sellers/score)
3. Depth factor scoring (6 dimensions progress bar)
4. Market feasibility assessment
5. 163 indicator details table (Foldable)
6. Decision-making suggestions

## Standard usage process

### Recommended: In-depth analysis + HTML report

```python
# Step 1: Perform in-depth analysis (Contains chart generation)
result = await analyze_asin_deep(asin="B0XXXXXX", include_charts=True)
# return: Detailed analysis report + Chart path list

# Step 2: Generate professional HTML reports
html_result = await generate_html_analysis_report(asin="B0XXXXXX")
# return: HTML report path
```

### Using analysis functions alone

```python
# In-depth analysis only (With charts)
analysis = await analyze_asin_deep(asin="B0XXXXXX")

# Generate HTML report only (Requires existing CSV data)
html_path = await generate_html_analysis_report(asin="B0XXXXXX")

# Actuarial level analysis (Profit model/Monte Carlo)
actuarial = await analyze_asin_actuarial(asin="B0XXXXXX")

# COSMO intent analysis
cosmo = await analyze_cosmo_intent(asin="B0XXXXXX")
```
```

## output file

### CSV file
path: `cache/reports/{ASIN}_163_metrics.csv`

Contains 161-163 fields covering:
- Current price and historical average
- Sales rankings and changes
- Number of sellers and competition
- Number of reviews and ratings
- Product attributes and specifications

### HTML report
path: `cache/reports/{ASIN}_analysis_report.html`

Include:
- Visual indicator card
- 6-dimensional factor score chart
- Complete indicator table(Foldable)
- Risk warning
- Decision suggestions

## Configuration

### environment variables
```bash
KEEPA_KEY=your_api_key          # required
KEEPA_DOMAIN=US                 # DefaultUS
CACHE_ENABLED=true              # Default true
CACHE_TTL_HOURS=24              # Default 24
```

### Claude Desktop Configuration
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

## debug

### local test
```bash
# 1. Set environment variables
export KEEPA_KEY="your_key"

# 2. Run the test
python test_installation.py

# 3. Start the server
python server.py
```

### Test indicator collection
```python
python -c "
from src.keepa_metrics_collector import KeepaMetricsCollector
import keepa
api = keepa.Keepa('your_key')
products = api.query(['B0F6B5R47Q'])
collector = KeepaMetricsCollector()
metrics = collector.collect_all_metrics(products[0])
print(f'Collected {len(metrics)} indicators')
"
```

## core principles

1. **data driven**: All conclusions based on 163 indicators of Keepa API
2. **honest analysis**: Don’t predict unverifiable profits, only analyze observable signals
3. **Risk warning**: Focus on identifying risk signals(Falling demand, intensifying competition, etc.)
4. **Concise reporting**: HTML reports clearly display key indicators and analysis conclusions

## Reference resources

- [Keepa API Documentation](https://keepa.com/#!discuss/t/request-products)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [Keepa Python client](https://github.com/akaszynski/keepa)
