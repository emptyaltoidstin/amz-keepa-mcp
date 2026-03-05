# 1688 Integration of searching pictures and purchasing prices

This system supports automatic acquisition of purchase prices through the 1688 API, allowing direct search for 1688 supplier quotes from Amazon product images.

## Features

✅ **Search pictures by pictures**: Use Amazon product images to search for similar products on 1688  
✅ **Automatic calculation**: Automatically calculate first-way freight based on weight  
✅ **cost estimate**: Automatic calculation of complete COGS(Including tariffs and exchange rate conversion)  
✅ **Smart sorting**: Comprehensive consideration of price, matching degree, and supplier level  
✅ **One-click reporting**: Automatically generate actuarial reports including purchase prices  

## quick start

### 1. Obtain TMAPI Token

access [TMAPI official website](https://tmapi.top) Register and get API Token.

### 2. Configure environment variables

```bash
# .env file
TMAPI_TOKEN=your_tmapi_token_here
KEEPA_KEY=your_keepa_key_here
```

### 3. Run the analysis

```python
from src.procurement_analyzer import generate_auto_procurement_report

# Generate a complete report with purchase prices in one click
report_path, analyses = generate_auto_procurement_report('B0F6B5R47Q')
```

## Detailed usage

### Basic purchase price search

```python
from src.procurement_analyzer import SmartProcurementAnalyzer

# Create analyzer
analyzer = SmartProcurementAnalyzer.from_env()

# Analyze individual products
result = analyzer.analyze_product(keepa_product, target_moq=100)

if result.found:
    print(f"purchase price: ¥{result.price_rmb}")
    print(f"Total COGS: ${result.total_cogs_usd}")
```

### Batch analysis

```python
# Analyze the entire variant portfolio
analyses = analyzer.analyze_portfolio(products, target_moq=100)

# Convert to financial data
financials_map = analyzer.to_financials_map(analyses)
```

### When not using API

If there is no 1688 API, you can fill it in manually using interactive reporting:

```python
# An interactive version is automatically created when a report is generated
# Open *_ALLINONE_INTERACTIVE.html
# exist"Procurement cost"Fill in the price in the input box and it will be automatically calculated.
```

## Comparison of API solutions

| plan | advantage | shortcoming | Applicable scenarios |
|------|------|------|----------|
| **TMAPI** | Simple and fast | TOLL (~$0.01-0.05/Second-rate) | Recommended plan |
| **1688 official** | free | Requires enterprise qualifications | Qualified enterprises |
| **Manual entry** | precise | time consuming | small scale use |

## cost calculation formula

```
Total COGS (USD) = [purchase price(RMB) + First leg freight(RMB)] × 1.15(tariff) ÷ exchange rate

in:
- First leg freight = weight(kg) × 12 RMB/kg
- exchange rate = 7.2 RMB/USD (Configurable)
- tariff = 15% (Configurable)
```

## data structure

### ProcurementAnalysis

```python
{
    "asin": "B0F6B5R47Q",
    "found": True,
    "price_rmb": 35.50,          # purchase price(RMB)
    "moq": 100,                   # MOQ
    "supplier": "XX factory",         # Supplier name
    "source_url": "https://...",  # 1688 link
    "match_score": 0.85,          # Image matching
    "confidence": "high",         # Confidence
    "shipping_cost_rmb": 4.80,    # First leg freight
    "total_cogs_usd": 6.45        # Total COGS(Dollar)
}
```

## Things to note

⚠️ **Image restrictions**: 
- 1688’s image search mainly supports Alibaba platform images
- Amazon images may need to be converted

⚠️ **Accuracy**: 
- It is recommended to manually confirm the price of key products
- Searching for images may return similar but not identical products

⚠️ **MOQ considerations**: 
- Pay attention to whether the MOQ is suitable for your purchasing volume
- The system will mark the case where the MOQ is too high.

## Configuration file

```env
# required
KEEPA_KEY=your_keepa_api_key

# 1688 API (Recommend TMAPI)
TMAPI_TOKEN=your_tmapi_token

# Optional - Costing parameters
SHIPPING_RATE=12          # RMB/kg
EXCHANGE_RATE=7.2         # RMB/USD
TARIFF_RATE=0.15          # 15%
```

## Sample code

See `examples/1688_procurement_example.py`

```bash
cd examples
python 1688_procurement_example.py
```

## troubleshooting

### Purchase price not found

- Check TMAPI_Is TOKEN set correctly?
- Confirm if product images are accessible
- Try adjusting the target_moq parameters

### Price is not accurate

- Manually confirm 1688 search results
- Consider MOQ and supplier level
- Check if the weight data is correct

### API call failed

- Check network connection
- Confirm API Token balance
- Check TMAPI service status

## Related documents

- `src/cn_1688_api.py` - 1688 API client
- `src/procurement_analyzer.py` - Smart Procurement Analyzer
- `src/allinone_interactive_report.py` - Interactive reporting

## Update plan

- [ ] Support 1688 official API
- [ ] Pictures are automatically converted to Alibaba Pictures
- [ ] Historical price trend analysis
- [ ] Multi-supplier price comparison function
