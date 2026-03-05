# Amz-Keepa-MCP architecture diagram

## System architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ User Layer │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│ │ MCP Tools │ │ Python API │ │ Command Line CLI │ │
│ │ Claude integration │ │ Programmatic call │ │ Script execution │ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                           │
└─────────┼───────────────────┼───────────────────┼───────────────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Data collection layer │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────┐    ┌──────────────────────┐                      │
│ │ Variant automatic collector │ │ 163 indicator collector │ │
│  │  VariantAutoCollector│    │   Metrics163Collector│                      │
│  │                      │    │                      │                      │
│ │ • Utilizing variations │ │ • Basic information(18 items)    │                      │
│ │ Field Discovery Variants │ │ • Sales Performance(8 items)     │                      │
│ │ • Batch API query │ │ • Price data(33 items)    │                      │
│ │ • Smart data merging │ │ • Review returns(5 items)     │                      │
│ │ │ │ • ...163 items in total │ │
│  └──────────┬───────────┘    └──────────┬───────────┘                      │
│             │                           │                                   │
│             └─────────────┬─────────────┘                                   │
│                           │                                                 │
│                           ▼                                                 │
│  ┌─────────────────────────────────────────────────────────┐               │
│ │Smart sales allocator │ │
│  │              SalesAllocationEngine                       │               │
│  │                                                          │               │
│ │ Enter: boughtInPastMonth (May be shared data)               │               │
│  │       ↓                                                  │               │
│ │ Detection: Are all variants numerically the same??                            │               │
│  │       ↓                                                  │               │
│ │ Yes → Distributed according to BSR ratio │ │
│  │       weight = 1 / BSR^0.5                               │               │
│  │       ratio = weight / total_weights                     │               │
│  │       allocated = total_sales × ratio                    │               │
│  │       ↓                                                  │               │
│ │ Output: Independent Sales of Each Variant │ │
│  └─────────────────────────────────────────────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Analysis engine layer │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│ │ TACOS Calculator │ │
│  │                  TacosCalculator                            │           │
│  │                                                              │           │
│ │ Enter: monthly sales, Monthly advertising orders, TACOS ratio(Default 15%)           │           │
│  │       ↓                                                      │           │
│ │ Calculate: unit advertising cost = (Monthly Sales × TACOS) / Number of advertising orders per month │ │
│  │       ↓                                                      │           │
│ │ Output: Advertising cost per insertion order │ │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│ │ Profit Analyzer │ │
│  │                 ProfitAnalyzer                              │           │
│  │                                                              │           │
│ │ Enter: price, COGS, operating expenses, advertising cost, Order source ratio │ │
│  │       ↓                                                      │           │
│ │ Calculate:                                                      │           │
│ │ Natural profit = price - COGS - Operating expenses │ │
│ │ Advertising profit = price - COGS - operating expenses - Advertising Cost │ │
│ │ Mixed Profit = Natural profit × natural proportion + Advertising profit × advertising proportion │ │
│  │       ↓                                                      │           │
│ │ Output: Profit structure of each variant │ │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│ │ Pareto Analyzer │ │
│  │                  ParetoAnalyzer                             │           │
│  │                                                              │           │
│ │ Enter: Sales data of each variant │ │
│  │       ↓                                                      │           │
│ │ Calculate: Sort by sales, Total 80%sales volume variations = Core variant │ │
│  │       ↓                                                      │           │
│ │ Output: Core variant list, Long tail variant list │ │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│ │ Decision Engine │ │
│  │                   DecisionEngine                            │           │
│  │                                                              │           │
│ │ Enter: profit margin, advertising dependence, return rate, score, Competition, Trend │ │
│  │       ↓                                                      │           │
│ │ Assessment:                                                      │           │
│ │ Profit rate > 15% AND risk factors < 3 → PROCEED (Recommended investment)       │           │
│ │ Profit margin 5-15% OR risk factor ≥ 3 → CAUTION (Consider carefully)        │           │
│ │ Profit rate < 5% OR loss → AVOID (Recommended to avoid)                   │           │
│  │       ↓                                                      │           │
│ │ Output: decision making + Confidence + risk/Chance factors │ │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Report generation layer │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐          │
│ │ Chinese Report Generator │ │ Premium Report Generator │ │
│  │    ChineseActuaryReport    │  │   PremiumActuaryReport      │          │
│  │                            │  │                             │          │
│ │ • Dark minimalist style │ │ • Luxury aesthetic design │ │
│ │ • Complete Chinese version of 163 indicators │ │ • Micro-precision details │ │
│ │ • Complete data transparency │ │ • Elegant animation │ │
│ │ • Visualization of computing logic │ │ • Responsive layout │ │
│  │                            │  │                             │          │
│ │ Output: HTML Report │ │ Output: HTML report │ │
│  └─────────────────────────────┘  └─────────────────────────────┘          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│ │ CSV data export │
│  │                   CSVExporter                               │
│  │                                                             │           │
│ │ Output: 163 indicator raw data CSV file │ │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│External dependencies │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                      Keepa API                              │           │
│  │                                                             │           │
│ │ • 163 indicator data sources │ │
│ │ • Price/Ranking history data │ │
│ │ • boughtInPastMonth real sales │ │
│ │ • variations variation relationship │ │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘


## data flow diagram

```
User enters ASIN
    │
    ▼
┌─────────────────┐
│ Variant automatic collector │ ──→ Discover all variant ASINs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Batch API query │ ──→ Get Keepa data for each variant
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 163 indicator collector │ ──→ Extract 163 indicators
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Intelligent sales allocator │ ──→ Process shared data/Allocate sales volume
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Profit Analyzer │ ──→ Calculate the profit of each variant
│ (TACOS model)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Decision engine │ ──→ Generate investment recommendations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Report Generator │ ──→ Generate HTML report
└─────────────────┘
```


## Core algorithm

### 1. Intelligent sales volume allocation algorithm

```python
def allocate_sales(variants, total_sales):
    """
    Allocate parent ASIN total sales in proportion to BSR
    """
    # Calculate weight (The lower the BSR, the higher the weight)
    weights = [1 / (v.bsr ** 0.5) for v in variants]
    total_weight = sum(weights)
    
    for v in variants:
        # Calculate proportion
        ratio = (1 / v.bsr ** 0.5) / total_weight
        # Allocate sales volume
        v.allocated_sales = total_sales * ratio
    
    return variants
```

### 2. TACOS advertising cost calculation

```python
def calculate_ad_cost(price, monthly_sales, ad_order_pct, tacos_rate=0.15):
    """
    Calculate unit advertising costs
    """
    monthly_revenue = price * monthly_sales
    monthly_ad_budget = monthly_revenue * tacos_rate
    monthly_ad_orders = monthly_sales * ad_order_pct
    
    ad_cost_per_unit = monthly_ad_budget / monthly_ad_orders
    
    return ad_cost_per_unit
```

### 3. Decision Algorithm

```python
def make_decision(margin, ad_dependency, return_rate, rating, competition):
    """
    generate investment decisions
    """
    risk_factors = []
    
    if margin < 0:
        risk_factors.append("Loss")
    if ad_dependency > 0.6:
        risk_factors.append("High advertising dependence")
    if return_rate > 0.12:
        risk_factors.append("High return rate")
    if rating < 4.0:
        risk_factors.append("low rating")
    if competition > 10:
        risk_factors.append("Competition is fierce")
    
    if margin < 0:
        return "AVOID", 90, risk_factors
    elif margin < 10 or len(risk_factors) >= 3:
        return "CAUTION", 70, risk_factors
    else:
        return "PROCEED", 80, risk_factors
```


## file dependencies

```
server.py
    ├── src/__init__.py
    │ └── Export: auto_analyze, generate_final_report, ...
    │
    ├── src/amazon_actuary_final.py (core analysis engine)
    │       ├── KeepaMetrics163 (data model)
    │       ├── VariantFinancials (financial model)
    │       ├── Metrics163Collector (Indicator collection)
    │       ├── TacosCalculator (TACOS calculation)
    │       ├── VariantProfitAnalyzer (profit analysis)
    │       ├── LinkPortfolioAnalyzer (Portfolio analysis)
    │       └── generate_final_report (main entrance)
    │
    ├── src/variant_auto_collector.py
    │       └── VariantAutoCollector (variant collection)
    │
    ├── src/keepa_metrics_collector.py
    │       └── KeepaMetricsCollector (163 indicators)
    │
    ├── src/chinese_actuary_report.py
    │       └── ChineseActuaryReport (Chinese report)
    │
    └── src/premium_actuary_report.py
            └── PremiumReportGenerator (Premium reporting)
```


## Performance optimization

### API call optimization
- Batch query: Maximum of 10 ASINs at a time
- automatic delay: 0.5 second delay between batches
- caching mechanism: Avoid duplicate queries

### Computational optimization
- vectorized computation: Use numpy to process large amounts of data
- parallel processing: Multi-threading independent variant
- Memory optimization: Timely release of big data objects


## Extensible design

### Add new data source
```python
class NewDataSource:
    def fetch_data(self, asin):
        # Implement new data acquisition logic
        pass
```

### Add new analysis dimension
```python
class NewAnalyzer:
    def analyze(self, data):
        # Implement new analysis logic
        pass
```

### New report format
```python
class NewReportGenerator:
    def generate(self, analysis):
        # Implement new report generation logic
        pass
```
