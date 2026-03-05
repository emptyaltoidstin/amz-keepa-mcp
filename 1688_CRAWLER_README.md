# 1688 Image search crawler solution

Based on open source projects [Zhui-CN/1688_image_search_crawler](https://github.com/Zhui-CN/1688_image_search_crawler) Realized automatic collection of 1688 purchase prices.

## Plan comparison

| characteristic | TMAPI scheme | **Open source crawler solution** (recommend) |
|------|-----------|------------------------|
| **cost** | $0.01-0.05/Second-rate | **free** |
| **stability** | high (business services) | medium (Depends on 1688 interface) |
| **speed** | quick | medium (~2-5 seconds/Second-rate) |
| **API Key** | need | **unnecessary** |
| **Configuration complexity** | Low | Low |
| **Anti-climbing risk** | none | **have** |
| **legal risks** | none | Low (Subject to 1688 Terms of Service) |

## Implementation principle

```
Amazon product images
      ↓
Download image → base64 encoding
      ↓
Call 1688 H5 API (h5api.m.1688.com)
      ↓
Upload image to get imageId
      ↓
Use imageId to search for similar products
      ↓
Parse the returned JSON data
      ↓
Get price, MOQ, supplier information
```

## How to use

### 1. Basic usage

```python
from procurement_1688_integration import generate_1688_procurement_report

# Generate a complete report with 1688 purchase price in one click
report_path, results = generate_1688_procurement_report('B0F6B5R47Q')
```

### 2. Use step by step

```python
from procurement_1688_integration import Smart1688Procurement

# Create analyzer
analyzer = Smart1688Procurement.from_env()

# Analyze individual products
result = analyzer.analyze_product(keepa_product, target_moq=100)

if result.found:
    print(f"purchase price: ¥{result.price_rmb}")
    print(f"supplier: {result.supplier}")
    print(f"Total COGS: ${result.total_cogs_usd}")
```

### 3. Call the crawler directly

```python
from cn_1688_crawler import CN1688Crawler

crawler = CN1688Crawler()

# Search by image URL
offers = crawler.search_by_image_url(
    'https://example.com/image.jpg',
    max_results=10
)

for offer in offers:
    print(f"{offer.company_name}: ¥{offer.price} (MOQ:{offer.moq})")
```

## data structure

### ProcurementResult

```python
{
    "asin": "B0F6B5R47Q",
    "found": True,
    "price_rmb": 35.50,          # purchase price(RMB)
    "moq": 100,                   # MOQ
    "supplier": "XX factory",         # Supplier name
    "location": "Guangdong Shenzhen",      # supplier location
    "is_verified": True,          # Whether to certify merchants
    "product_url": "https://...", # 1688 product link
    "confidence": "high",         # Confidence
    "weight_kg": 0.45,           # Product weight
    "shipping_cost_rmb": 5.40,   # First leg freight
    "total_cogs_usd": 6.45       # Total COGS(Dollar)
}
```

### CNSupplierOffer (Detailed quotation)

```python
{
    "offer_id": "123456789",
    "title": "product title",
    "price": 35.50,
    "moq": 100,
    "unit": "pieces",
    "image_url": "https://...",
    "company_name": "XX factory",
    "province": "Guangdong",
    "city": "Shenzhen",
    "shop_url": "https://...",
    "is_verified": True,
    "credit_level": "AAA",
    "years": 5,                  # Credit Pass Period
    "repurchase_rate": "45%",    # Repurchase rate
    "product_url": "https://...",
    "quantity_prices": [         # Ladder price
        {"quantity": "1~99", "price": 35.50},
        {"quantity": ">=100", "price": 32.00}
    ],
    "scores": {                  # Store rating
        "composite": 4.5,
        "goods": 4.0,
        "logistics": 4.5
    },
    "position_labels": ["Source factory", "7×24H response"]
}
```

## cost calculation formula

```
Total COGS (USD) = [purchase price + (Weight kg × shipping price)] × 1.15(tariff) ÷ exchange rate

Default parameters:
- shipping price: 12 RMB/kg
- exchange rate: 7.2 RMB/USD
- tariff: 15%
```

## Things to note

### ⚠️ Anti-climbing risk

1. **frequency limit**: 1688 There may be a request frequency limit
2. **IP ban**: Frequent calls may result in the IP being blocked
3. **Service stability**: 1688 interface may change at any time

**suggestion**:
- Add request interval appropriately (Implemented 0.5 second delay)
- Controlling speed during batch analysis
- Prepare alternatives (TMAPI or manual entry)

### ⚠️ Accuracy issue

1. **Picture matching**: Searching pictures by pictures may not necessarily result in 100%precise
2. **Price changes**: 1688 prices may change in real time
3. **MOQ difference**: Pay attention to whether the MOQ meets the requirements

**suggestion**:
- Manual confirmation of key products
- Use confidence levels to assess the reliability of results
- Average price across multiple variants

## troubleshooting

### Unable to obtain token

```
mistake: Unable to obtain_m_h5_tk cookie
```

**solve**:
- Check network connection
- 1688 The interface may have changed and the code needs to be updated.
- Switch to TMAPI scheme

### Failed to upload image

```
mistake: Failed to upload image
```

**solve**:
- Check if the image URL is accessible
- Image size may be too large (suggestion < 5MB)
- 1688 service may be temporarily unavailable

### Return empty result

```
1688No matching product found
```

**solve**:
- The product may not be similar on 1688
- Try using different product images
- Check picture quality

## Alternatives

If the crawler solution is not available, you can switch to:

1. **TMAPI scheme**: Commercial API, high stability
2. **Manual entry**: Use All-in-One interactive report manual filling

```python
# Switch to TMAPI scheme
from procurement_analyzer import SmartProcurementAnalyzer

analyzer = SmartProcurementAnalyzer(tmapi_token="your_token")
```

## File structure

```
src/
├── cn_1688_crawler.py              # 1688 crawler core
├── procurement_1688_integration.py # Integrated module
└── procurement_analyzer.py         # TMAPI scheme(alternative)
```

## Change log

### v1.0 (2024-02)
- initial version
- Implement image search function
- Support price, MOQ, supplier information collection
- Integrated into actuary system

## Disclaimer

This implementation is based on an open source project and is for learning and research purposes only. Please comply with the 1688 Terms of Service when using it and may not be used for illegal purposes. For commercial use, please consider official API solutions such as TMAPI.
