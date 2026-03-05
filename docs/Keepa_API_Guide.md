# Complete Guide to Keepa API

> Organizing official documents based on Chrome DevTools
> last updated: 2026-02-15

---

## Table of contents

1. [Overview](#Overview)
2. [Pricing plans](#Pricing plans)
3. [Core API endpoints](#core-api-endpoint)
4. [Detailed explanation of product objects](#Detailed explanation of product objects)
5. [Price history data type](#Price history data type)
6. [Detailed explanation of request parameters](#Detailed explanation of request parameters)
7. [Python client usage](#python-Client use)
8. [Asynchronous API usage](#asynchronous-api-use)
9. [Error handling](#Error handling)
10. [Related links](#Related links)

---

## Overview

The Keepa API provides support for more than **4 billion** Access to price history data for Amazon products.

### Core functions

| Function | Description |
|------|------|
| Product coverage | 4 billion+ Track products |
| data type | Live pricing, availability, historical prices |
| price type | Amazon、Marketplace New/Used、Warehouse、FBA、FBM、Collectible、Refurbished、eBay |
| Ranking data | Sales Rank, Offers Count, Rating, Review Count History |
| Buy Box | Complete Buy Box information including price and seller history |
| Category data | Category details, search, browse |
| Product lookup | Search the entire database based on any criteria |
| bestseller list | Best Sellers list with up to 500,000 ASINs |
| Seller Indicators | Seller ratings, rating count history, top seller lists, store visits(Up to 100,000 ASINs) |
| Promotional data | Full access to millions of Deals with support for searching, filtering and sorting |
| Data format | JSON format via RESTful API, TLS encryption |
| client support | PHP and Java frameworks |

### support site

| domain name | code |
|------|------|
| Amazon.com | US |
| Amazon.co.uk | UK |
| Amazon.de | DE |
| Amazon.fr | FR |
| Amazon.it | IT |
| Amazon.es | ES |
| Amazon.co.jp | JP |
| Amazon.ca | CA |
| Amazon.cn | CN |
| Amazon.in | IN |
| Amazon.mx | MX |
| Amazon.br | BR |
| Amazon.au | AU |
| Amazon.nl | NL |
| Amazon.sa | SA |
| Amazon.ae | AE |
| Amazon.se | SE |
| Amazon.pl | PL |
| Amazon.tr | TR |
| Amazon.be | BE |

---

## Pricing plans

Keepa API Adoption **Token** Billing model, all plans are prepaid monthly subscription model.

### Token mechanism

- Most requests: 1 Token to get complete data for a product
- Advanced/Detailed inquiry: Additional Token may be required
- Unused Token: Expires in 1 hour
- Supports upgrades at any time and can be downgraded once a month

### Plan list

| plan | Token/minutes | Approximately/month | price/month | save |
|------|-----------|---------|---------|------|
| Plan 20 | 20 | 892,800 | €49 | - |
| Plan 60 | 60 | 2,678,400 | €129 | 12% |
| Plan 250 | 250 | 11,160,000 | €459 | 25% |
| Plan 500 | 500 | 22,320,000 | €879 | 28% |
| Plan 1000 | 1000 | 44,640,000 | €1,499 | 39% |
| Plan 2000 | 2000 | 89,280,000 | €2,499 | 49% |
| Plan 3000 | 3000 | 133,920,000 | €3,499 | 52% |
| Plan 5000 | 5000 | 223,200,000 | €5,350 | 56% |
| Plan 10000 | 10000 | 446,400,000 | €11,099 | 55% |
| Plan 20000 | 20000 | 892,800,000 | €22,000 | 55% |

> You need to register a Keepa account to use the API.

---

## Core API endpoints

### 1. Product inquiry (Product Query)

Get complete product data for one or more ASINs.

**Endpoint:** `https://api.keepa.com/product`

**Request method:** GET

**Required parameters:**

| parameters | Type | Description |
|------|------|------|
| `key` | string | 64 character access key |
| `domain` | int | Amazon domain ID (1=US, 2=UK, etc.) |
| `asin` | string | List of ASINs, comma separated |

**Optional parameters:**

| parameters | Type | Default value | Description |
|------|------|--------|------|
| `stats` | int | 0 | Statistics time range(day) |
| `buybox` | bool | false | Contains Buy Box history |
| `history` | bool | true | Contains price history |
| `offers` | int | 0 | Number of offers obtained(Consume additional tokens) |
| `update` | int | 0 | Maximum product data age(hours) |
| `stock` | bool | false | Contains inventory data |
| `rating` | bool | true | Contains rating data |

**Sample request:**

```http
GET https://api.keepa.com/product?key=YOUR_KEY&domain=1&asin=B0088PUEPK,B00ZVJAF3G&stats=90&buybox=1
```

**Python example:**

```python
import keepa

api = keepa.Keepa('YOUR_ACCESS_KEY')

# Single ASIN
products = api.query('B0088PUEPK')
product = products[0]

# Multiple ASINs
asins = ['B0088PUEPK', 'B00ZVJAF3G', 'B00H93NJLS']
products = api.query(asins)

# Query with parameters
products = api.query('B0088PUEPK', 
                     stats=90,           # 90 days statistics
                     buybox=True,        # Includes Buy Box
                     offers=20,          # Get 20 offers
                     history=True)       # Contains historical data
```

---

### 2. Product search (Product Finder)

Search the Keepa database for products matching specific criteria.

**Endpoint:** `https://api.keepa.com/query`

**Python example:**

```python
# Search criteria
product_parms = {
    'author': 'jim butcher',
    'sort': ['current_SALES', 'asc'],  # Sort by sales volume in ascending order
    'perPage': 50
}

asins = api.product_finder(product_parms)
print(f"found {len(asins)} products")
```

---

### 3. Bestseller list (Best Sellers)

Get a list of best-selling products in a specific category.

**Endpoint:** `https://api.keepa.com/bestsellers`

**parameters:**

| parameters | Description |
|------|------|
| `category` | Category node ID |
| `rank_avg_range` | Rank average range (0, 30, 90, 180) |
| `variations` | Whether to include variations |
| `sublist` | Whether to use subcategory ranking |

**Python example:**

```python
# Search category first
categories = api.search_for_categories("movies")
category_id = list(categories.keys())[0]

# Get bestseller list
asins = api.best_sellers_query(category_id)
print(f"Bestsellers: {asins[:10]}")

# Use average position
asins = api.best_sellers_query(category_id, rank_avg_range=30)
```

---

### 4. Category query (Category)

Get category information and hierarchical structure.

**Python example:**

```python
# Search category
categories = api.search_for_categories("electronics")
for cat_id, cat_info in categories.items():
    print(f"{cat_id}: {cat_info['name']}")

# Get root category
root_categories = api.category_lookup(0)

# Get details about a specific category
category_details = api.category_lookup(172282)  # Electronics
```

---

### 5. Deals query

Find promotional products that match specific criteria.

**Endpoint:** `https://api.keepa.com/deals`

**A maximum of 150 Deals can be returned in a single request**

**Python example:**

```python
deal_parms = {
    'page': 0,
    'domainId': 1,
    'excludeCategories': [],
    'includeCategories': [172282],  # Electronics
    'priceTypes': [0],  # Amazon price
    'deltaRange': [0, 100],
    'deltaPercentRange': [-90, -10],  # Price reduced by 10%-90%
    'deltaLastRange': [0, 7],  # Last 7 days
    'salesRankRange': [0, 50000],
    'currentRange': [1000, 50000],  # price range
    'minRating': 4,
    'isLowest': True,
    'sortType': 0,
    'dateRange': 0
}

deals = api.deals(deal_parms)
```

---

## Detailed explanation of product objects

The product object returned by the product query contains the following main fields:

### Basic information fields

| Field | Type | Description |
|------|------|------|
| `asin` | string | ASIN code |
| `title` | string | product title |
| `brand` | string | brand |
| `manufacturer` | string | manufacturer |
| `productGroup` | string | product group |
| `model` | string | Model |
| `partNumber` | string | Part number |
| `color` | string | color |
| `size` | string | Size |
| `format` | string | Format |
| `packageHeight` | int | Packing height(hundredth of an inch) |
| `packageLength` | int | Packing length(hundredth of an inch) |
| `packageWidth` | int | Packing width(hundredth of an inch) |
| `packageWeight` | int | Packing weight(one hundredth of a pound) |
| `itemHeight` | int | Product height |
| `itemLength` | int | Product length |
| `itemWidth` | int | Product width |
| `itemWeight` | int | Product weight |

### Category and ranking fields

| Field | Type | Description |
|------|------|------|
| `rootCategory` | int | Root category ID |
| `categoryTree` | list | Category tree |
| `pickupInStore` | bool | Does it support in-store pickup? |
| `shipsInOriginalPackaging` | bool | Whether shipped in original packaging |
| `lastUpdate` | int | Last updated(Keepa minutes) |
| `lastPriceChange` | int | Last price change time |
| `lastRatingChange` | int | Last rating change time |

### Amazon data fields

| Field | Type | Description |
|------|------|------|
| `amazonOffer` | bool | Is it on sale on Amazon? |
| `isSNS` | bool | Whether to support Subscribe & Save |
| `isRedirectASIN` | bool | Whether to redirect ASIN |
| `isAdult` | bool | Is it an adult product? |
| `isB2B` | bool | Is it a B2B product? |

### variant field

| Field | Type | Description |
|------|------|------|
| `variations` | list | Variant ASIN list |
| `parentAsin` | string | Parent ASIN |
| `variationCSV` | string | Variations CSV data |
| `hasParent` | bool | Is there a parent product? |

### Picture field

| Field | Type | Description |
|------|------|------|
| `imagesCSV` | string | Image URL CSV |
| `imageCount` | int | Number of pictures |
| `imageURLs` | list | Image URL list |

### EAN/UPC field

| Field | Type | Description |
|------|------|------|
| `eanList` | list | EAN list |
| `upcList` | list | UPC list |
| `gtin` | string | GTIN |
| `mpn` | string | MPN |

---

## Price history data type

product object `data` Fields contain the following price history types:

### price type

| key | Description |
|-----|------|
| `AMAZON` | Amazon Official Price History |
| `NEW` | Marketplace new price history(Contains Amazon) |
| `USED` | Second hand price history |
| `SALES` | Sales ranking history |
| `LISTPRICE` | Price history |
| `COLLECTIBLE` | Collectible Price History |
| `REFURBISHED` | Refurbishment Price History |
| `NEW_FBA` | FBA new lowest price(Does not include Amazon/Warehouse) |
| `NEW_FBM_SHIPPING` | FBM new price including shipping fee |
| `LIGHTNING_DEAL` | Flash sale price history |
| `WAREHOUSE` | Amazon Warehouse Price |

### status price type

| key | Description |
|-----|------|
| `USED_NEW_SHIPPING` | "Used - Like New" shipping included |
| `USED_VERY_GOOD_SHIPPING` | "Used - Very Good" shipping included |
| `USED_GOOD_SHIPPING` | "Used - Good" shipping included |
| `USED_ACCEPTABLE_SHIPPING` | "Used - Acceptable" shipping included |
| `COLLECTIBLE_NEW_SHIPPING` | "Collectible - Like New" shipping included |
| `COLLECTIBLE_VERY_GOOD_SHIPPING` | "Collectible - Very Good" shipping included |
| `COLLECTIBLE_GOOD_SHIPPING` | "Collectible - Good" shipping included |
| `COLLECTIBLE_ACCEPTABLE_SHIPPING` | "Collectible - Acceptable" shipping included |
| `REFURBISHED_SHIPPING` | Refurbishment price including freight |

### Count type

| key | Description |
|-----|------|
| `COUNT_NEW` | New quote quantity history |
| `COUNT_USED` | Second-hand quotation quantity history |
| `COUNT_REFURBISHED` | Refurbishment quote quantity history |
| `COUNT_COLLECTIBLE` | Collection quote quantity history |

### Rating type

| key | Description |
|-----|------|
| `RATING` | Rating history(0-50, like 45=4.5 stars) |
| `COUNT_REVIEWS` | Comment count history |

### Buy Box Type

| key | Description |
|-----|------|
| `BUY_BOX_SHIPPING` | Buy Box Price History(shipping included) |
| `BUY_BOX_USED` | Second hand Buy Box prices |
| `TRADE_IN` | Trade-in price history |

### Each data type has a corresponding time field

For example:`NEW` Correspond `NEW_time`，`USED` Correspond `USED_time`

**Python example:**

```python
product = products[0]
data = product['data']

# Get NEW price history
new_prices = data['NEW']
new_times = data['NEW_time']

# Get sales ranking history
sales_ranks = data['SALES']
sales_times = data['SALES_time']

# Get rating history
ratings = data['RATING']
rating_times = data['RATING_time']

# Print the last 10 prices
for i in range(min(10, len(new_prices))):
    print(f"{new_times[i]}: ${new_prices[i]/100:.2f}")
```

---

## Detailed explanation of request parameters

### Statistical parameters (stats)

`stats` Parameters are used to request statistics for a specific time range.

```python
# Request 30 days of statistics
products = api.query('B0088PUEPK', stats=30)

# access statistics
stats = product['stats']
print(f"current price: ${stats['current']/100:.2f}")
print(f"average price: ${stats['avg']/100:.2f}")
print(f"lowest price: ${stats['min']/100:.2f}")
print(f"highest price: ${stats['max']/100:.2f}")
```

### Offers Parameters

`offers` Parameter used to obtain detailed seller quote history.

```python
# Get 20 offers (expends additional tokens)
products = api.query('B0088PUEPK', offers=20)
product = products[0]

# All offers
offers = product['offers']

# Active offers index
active_indices = product['liveOffersOrder']

# Loop through active offers
for idx in active_indices:
    offer = offers[idx]
    seller_id = offer['sellerId']
    condition = offer['condition']
    is_fba = offer['isFBA']
    
    # Get offer price history
    csv = offer['offerCSV']
    times, prices = keepa.convert_offer_history(csv)
    
    print(f"seller: {seller_id}, Conditions: {condition}, FBA: {is_fba}")
    print(f"current price: ${prices[-1]/100:.2f}")
```

### Update parameters (update)

```python
# Only get products whose data age is less than 1 hour
products = api.query('B0088PUEPK', update=1)

# If the data expires, the API will automatically refresh
```

---

## Python client usage

### Installation

```bash
pip install keepa
```

### rely

- Python >= 3.10
- numpy
- aiohttp
- matplotlib (Optional, for plotting)
- tqdm

### Basic usage

```python
import keepa

# Initialize API
accesskey = 'YOUR_64_CHAR_ACCESS_KEY'
api = keepa.Keepa(accesskey)

# Inquire about products
products = api.query('B0088PUEPK')
product = products[0]

# Print basic information
print(f"ASIN: {product['asin']}")
print(f"title: {product['title']}")
print(f"brand: {product['brand']}")

# Get current price
data = product['data']
if len(data['NEW']) > 0:
    current_price = data['NEW'][-1]
    print(f"current price: ${current_price/100:.2f}")

# Get current sales ranking
if len(data['SALES']) > 0:
    current_rank = data['SALES'][-1]
    print(f"Current ranking: {current_rank}")

# Get rating
if 'RATING' in data and len(data['RATING']) > 0:
    rating = data['RATING'][-1]
    print(f"score: {rating/10:.1f}")
```

### Use UPC/EAN/ISBN-13 Query

```python
# Use UPC lookup
products = api.query('883904227319', product_code_is_asin=False)

# Use ISBN-13 Query
products = api.query('978-0786222728', product_code_is_asin=False)
```

### Batch query

```python
import numpy as np

# use list
asins = ['B0088PUEPK', 'B00ZVJAF3G', 'B00H93NJLS']
products = api.query(asins)

# Using numpy arrays
asins = np.asarray(['B0088PUEPK', 'B00ZVJAF3G'])
products = api.query(asins)
```

### Drawing

```python
import matplotlib.pyplot as plt

# Drawing using keepa's built-in
keepa.plot_product(product)

# Or use matplotlib to customize
data = product['data']
plt.step(data['NEW_time'], data['NEW'], where='pre', label='New Price')
plt.step(data['AMAZON_time'], data['AMAZON'], where='pre', label='Amazon Price')
plt.step(data['USED_time'], data['USED'], where='pre', label='Used Price')
plt.xlabel('Date')
plt.ylabel('Price ($)')
plt.legend()
plt.show()
```

---

## Asynchronous API usage

For large numbers of concurrent queries, it is more efficient to use the asynchronous API.

```python
import asyncio
import keepa

async def main():
    # Create an asynchronous client
    api = await keepa.AsyncKeepa().create('YOUR_ACCESS_KEY')
    
    # Asynchronous query
    products = await api.query('B0088PUEPK')
    
    # Batch asynchronous query
    asins = ['B0088PUEPK', 'B00ZVJAF3G', 'B00H93NJLS']
    
    # Create multiple concurrent tasks
    tasks = [api.query(asin) for asin in asins]
    results = await asyncio.gather(*tasks)
    
    for asin, products in zip(asins, results):
        print(f"{asin}: {products[0]['title']}")
    
    # Asynchronous product lookup
    product_parms = {'author': 'brandon sanderson'}
    asins = await api.product_finder(product_parms)
    
    # Asynchronous bestseller list
    categories = await api.search_for_categories("books")
    category_id = list(categories.keys())[0]
    bestsellers = await api.best_sellers_query(category_id)
    
    return results

# run
results = asyncio.run(main())
```

### Not waiting for Token refill

```python
# If the token is insufficient, an error will be returned directly without waiting.
products = await api.query('B0088PUEPK', wait=False)
```

---

## Buy Box Data Analysis

### Get Buy Box History

```python
products = api.query('B0088PUEPK', buybox=True)
product = products[0]

# Buy Box History
buybox_history = product['buyBoxSellerIdHistory']
buybox_prices = product['data']['BUY_BOX_SHIPPING']
```

### Dealing with second-hand Buy Box

```python
import pandas as pd

# Need to enable offers parameter
products = api.query('B0088PUEPK', offers=20)
product = products[0]

# Processing Secondary Buy Box Data
buybox_info = product.get('buyBoxUsedHistory', [])
if buybox_info:
    df = keepa.process_used_buybox(buybox_info)
    print(df.head())
    # output: datetime, user_id, condition, isFBA
```

---

## Token management

### Check token status

```python
# Get the current number of tokens
tokens_left = api.tokens_left
print(f"Remaining Tokens: {tokens_left}")

# Get token replenishment time
time_to_refill = api.time_to_refill
print(f"replenishment time: {time_to_refill} seconds")
```

### Waiting for Token

```python
# Default behavior: Automatically wait for token
products = api.query('B0088PUEPK', wait=True)

# Don't wait, execute immediately
products = api.query('B0088PUEPK', wait=False)
```

---

## Error handling

```python
import keepa

try:
    api = keepa.Keepa('INVALID_KEY')
    products = api.query('B0088PUEPK')
except Exception as e:
    print(f"mistake: {e}")

# Common mistakes:
# - Invalid access key
# - Insufficient Token (when wait=False)
# - Product not found
# - network error
```

---

## Time format description

Keepa uses a special minute time format:

- Keepa time = Since 2011-01-01 00:00:Minutes since 00 UTC
- The Python library automatically converts to datetime objects

```python
# Manual conversion
import keepa
keepa_minutes = 5000000
datetime_obj = keepa.keepa_minutes_to_time(keepa_minutes)
print(datetime_obj)  # 2020-06-18 09:20:00
```

---

## Related links

### Official documentation

| link | Description |
|------|------|
| https://keepa.com/#!api | API homepage |
| https://keepa.com/#!discuss/t/request-products/110 | Product Request Document |
| https://keepa.com/#!discuss/t/product-object/116 | Product Object Document |
| https://keepa.com/#!discuss/t/browsing-deals/338 | Deals Query Document |
| https://keepa.com/#!discuss/t/request-seller-information/790 | Seller information document |
| https://keepa.com/#!discuss/t/request-best-sellers/340 | Bestseller list document |
| https://keepa.com/#!discuss/t/searching-categories/232 | Category search documents |

### Developer resources

| link | Description |
|------|------|
| https://keepaapi.readthedocs.io | Python client documentation |
| https://github.com/akaszynski/keepa | Python client source code |
| https://github.com/keepacom/api_backend | Java backend source code |

### Get API Key

https://keepa.com/#!api (Requires a Keepa account registration)

---

## best practices

### 1. Batch query

```python
# good practice: Batch query
asins = ['A', 'B', 'C', 'D', 'E']
products = api.query(asins)  # Use fewer tokens

# avoid: Loop over a single query
for asin in asins:
    product = api.query(asin)  # Consume more tokens
```

### 2. Caching data

```python
# Use the stats parameter to get statistics instead of the full history
products = api.query(asins, stats=30, history=False)
```

### 3. Process large numbers of queries asynchronously

```python
async def batch_query(asins):
    api = await keepa.AsyncKeepa().create(KEY)
    tasks = [api.query(asin) for asin in asins]
    return await asyncio.gather(*tasks)
```

### 4. Error retry

```python
import time

def query_with_retry(asin, max_retries=3):
    for i in range(max_retries):
        try:
            return api.query(asin)
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # exponential backoff
```

---

## Summary

Keepa API is a powerful tool for Amazon product data analysis, providing:

1. **Comprehensive data coverage**: 4 billion+ Products, various price types
2. **Rich historical data**: Price, ranking, ratings, review history
3. **Various query methods**: ASIN, Category, Seller, Deals
4. **Flexible Python client**: sync/Asynchronous support
5. **Transparent pricing**: Token-based billing model

Amazon market data can be obtained and analyzed efficiently through the proper use of batch queries, asynchronous processing, and caching strategies.

---

*This document is based on Keepa’s official API documentation. If there are any updates, please refer to the official documentation.*
