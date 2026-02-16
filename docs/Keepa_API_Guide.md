# Keepa API 完全指南

> 基于 Chrome DevTools 抓取的官方文档整理
> 最后更新: 2026-02-15

---

## 目录

1. [概述](#概述)
2. [定价计划](#定价计划)
3. [核心 API 端点](#核心-api-端点)
4. [产品对象详解](#产品对象详解)
5. [价格历史数据类型](#价格历史数据类型)
6. [请求参数详解](#请求参数详解)
7. [Python 客户端使用](#python-客户端使用)
8. [异步 API 使用](#异步-api-使用)
9. [错误处理](#错误处理)
10. [相关链接](#相关链接)

---

## 概述

Keepa API 提供对超过 **40 亿** 亚马逊产品的价格历史数据访问。

### 核心功能

| 功能 | 说明 |
|------|------|
| 产品覆盖 | 40亿+ 追踪产品 |
| 数据类型 | 实时定价、可用性、历史价格 |
| 价格类型 | Amazon、Marketplace New/Used、Warehouse、FBA、FBM、Collectible、Refurbished、eBay |
| 排名数据 | Sales Rank、Offers Count、Rating、Review Count 历史 |
| Buy Box | 完整的 Buy Box 信息，包括价格和卖家历史 |
| 类目数据 | 类目详情、搜索、浏览 |
| 产品查找 | 基于任意条件搜索整个数据库 |
| 畅销榜单 | 包含多达 50万 ASIN 的 Best Sellers 列表 |
| 卖家指标 | 卖家评分、评分数量历史、顶级卖家列表、店铺访问(多达10万ASIN) |
| 促销数据 | 数百万 Deals 的完整访问，支持搜索、筛选和排序 |
| 数据格式 | JSON 格式 via RESTful API，TLS 加密 |
| 客户端支持 | PHP 和 Java 框架 |

### 支持站点

| 域名 | 代码 |
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

## 定价计划

Keepa API 采用 **Token** 计费模式，所有计划均为预付月费订阅模式。

### Token 机制

- 大多数请求：1 个 Token 可获取一个产品的完整数据
- 高级/详细查询：可能需要额外 Token
- 未使用 Token：1 小时后过期
- 支持随时升级，每月可降级一次

### 计划列表

| 计划 | Token/分钟 | 约计/月 | 价格/月 | 节省 |
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

> 需要注册 Keepa 账户才能使用 API。

---

## 核心 API 端点

### 1. 产品查询 (Product Query)

获取一个或多个 ASIN 的完整产品数据。

**Endpoint:** `https://api.keepa.com/product`

**请求方法:** GET

**必需参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `key` | string | 64字符访问密钥 |
| `domain` | int | Amazon 域名 ID (1=US, 2=UK, etc.) |
| `asin` | string | ASIN 列表，逗号分隔 |

**可选参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `stats` | int | 0 | 统计时间范围(天) |
| `buybox` | bool | false | 包含 Buy Box 历史 |
| `history` | bool | true | 包含价格历史 |
| `offers` | int | 0 | 获取的 offers 数量(消耗额外token) |
| `update` | int | 0 | 最大产品数据年龄(小时) |
| `stock` | bool | false | 包含库存数据 |
| `rating` | bool | true | 包含评分数据 |

**示例请求:**

```http
GET https://api.keepa.com/product?key=YOUR_KEY&domain=1&asin=B0088PUEPK,B00ZVJAF3G&stats=90&buybox=1
```

**Python 示例:**

```python
import keepa

api = keepa.Keepa('YOUR_ACCESS_KEY')

# 单个 ASIN
products = api.query('B0088PUEPK')
product = products[0]

# 多个 ASIN
asins = ['B0088PUEPK', 'B00ZVJAF3G', 'B00H93NJLS']
products = api.query(asins)

# 带参数查询
products = api.query('B0088PUEPK', 
                     stats=90,           # 90天统计
                     buybox=True,        # 包含Buy Box
                     offers=20,          # 获取20个offers
                     history=True)       # 包含历史数据
```

---

### 2. 产品查找 (Product Finder)

在 Keepa 数据库中搜索匹配特定条件的产品。

**Endpoint:** `https://api.keepa.com/query`

**Python 示例:**

```python
# 查找条件
product_parms = {
    'author': 'jim butcher',
    'sort': ['current_SALES', 'asc'],  # 按销量升序
    'perPage': 50
}

asins = api.product_finder(product_parms)
print(f"找到 {len(asins)} 个产品")
```

---

### 3. 畅销榜单 (Best Sellers)

获取特定类目的畅销产品列表。

**Endpoint:** `https://api.keepa.com/bestsellers`

**参数:**

| 参数 | 说明 |
|------|------|
| `category` | 类目节点 ID |
| `rank_avg_range` | 排名平均范围 (0, 30, 90, 180) |
| `variations` | 是否包含变体 |
| `sublist` | 是否使用子类目排名 |

**Python 示例:**

```python
# 先搜索类目
categories = api.search_for_categories("movies")
category_id = list(categories.keys())[0]

# 获取畅销榜
asins = api.best_sellers_query(category_id)
print(f"畅销产品: {asins[:10]}")

# 使用平均排名
asins = api.best_sellers_query(category_id, rank_avg_range=30)
```

---

### 4. 类目查询 (Category)

获取类目信息和层级结构。

**Python 示例:**

```python
# 搜索类目
categories = api.search_for_categories("electronics")
for cat_id, cat_info in categories.items():
    print(f"{cat_id}: {cat_info['name']}")

# 获取根类目
root_categories = api.category_lookup(0)

# 获取特定类目详情
category_details = api.category_lookup(172282)  # Electronics
```

---

### 5. Deals 查询

查找符合特定条件的促销产品。

**Endpoint:** `https://api.keepa.com/deals`

**单次请求最多返回 150 个 Deals**

**Python 示例:**

```python
deal_parms = {
    'page': 0,
    'domainId': 1,
    'excludeCategories': [],
    'includeCategories': [172282],  # Electronics
    'priceTypes': [0],  # Amazon price
    'deltaRange': [0, 100],
    'deltaPercentRange': [-90, -10],  # 降价10%-90%
    'deltaLastRange': [0, 7],  # 最近7天
    'salesRankRange': [0, 50000],
    'currentRange': [1000, 50000],  # 价格范围
    'minRating': 4,
    'isLowest': True,
    'sortType': 0,
    'dateRange': 0
}

deals = api.deals(deal_parms)
```

---

## 产品对象详解

产品查询返回的产品对象包含以下主要字段：

### 基础信息字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `asin` | string | ASIN 码 |
| `title` | string | 产品标题 |
| `brand` | string | 品牌 |
| `manufacturer` | string | 制造商 |
| `productGroup` | string | 产品组 |
| `model` | string | 型号 |
| `partNumber` | string | 零件号 |
| `color` | string | 颜色 |
| `size` | string | 尺寸 |
| `format` | string | 格式 |
| `packageHeight` | int | 包装高度(百分之一英寸) |
| `packageLength` | int | 包装长度(百分之一英寸) |
| `packageWidth` | int | 包装宽度(百分之一英寸) |
| `packageWeight` | int | 包装重量(百分之一磅) |
| `itemHeight` | int | 产品高度 |
| `itemLength` | int | 产品长度 |
| `itemWidth` | int | 产品宽度 |
| `itemWeight` | int | 产品重量 |

### 类目和排名字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `rootCategory` | int | 根类目 ID |
| `categoryTree` | list | 类目树 |
| `pickupInStore` | bool | 是否支持到店取货 |
| `shipsInOriginalPackaging` | bool | 是否原包装发货 |
| `lastUpdate` | int | 最后更新时间(Keepa分钟时间) |
| `lastPriceChange` | int | 最后价格变更时间 |
| `lastRatingChange` | int | 最后评分变更时间 |

### 亚马逊数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `amazonOffer` | bool | 亚马逊是否在售 |
| `isSNS` | bool | 是否支持 Subscribe & Save |
| `isRedirectASIN` | bool | 是否重定向 ASIN |
| `isAdult` | bool | 是否成人产品 |
| `isB2B` | bool | 是否 B2B 产品 |

### 变体字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `variations` | list | 变体 ASIN 列表 |
| `parentAsin` | string | 父 ASIN |
| `variationCSV` | string | 变体 CSV 数据 |
| `hasParent` | bool | 是否有父产品 |

### 图片字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `imagesCSV` | string | 图片 URL CSV |
| `imageCount` | int | 图片数量 |
| `imageURLs` | list | 图片 URL 列表 |

### EAN/UPC 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `eanList` | list | EAN 列表 |
| `upcList` | list | UPC 列表 |
| `gtin` | string | GTIN |
| `mpn` | string | MPN |

---

## 价格历史数据类型

产品对象的 `data` 字段包含以下价格历史类型：

### 价格类型

| 键 | 说明 |
|-----|------|
| `AMAZON` | Amazon 官方价格历史 |
| `NEW` | Marketplace 全新价格历史(包含Amazon) |
| `USED` | 二手价格历史 |
| `SALES` | 销售排名历史 |
| `LISTPRICE` | 标价历史 |
| `COLLECTIBLE` | 收藏品价格历史 |
| `REFURBISHED` | 翻新价格历史 |
| `NEW_FBA` | FBA 全新最低价格(不含Amazon/Warehouse) |
| `NEW_FBM_SHIPPING` | FBM 全新含运费价格 |
| `LIGHTNING_DEAL` | 秒杀价格历史 |
| `WAREHOUSE` | Amazon Warehouse 价格 |

### 状态价格类型

| 键 | 说明 |
|-----|------|
| `USED_NEW_SHIPPING` | "Used - Like New" 含运费 |
| `USED_VERY_GOOD_SHIPPING` | "Used - Very Good" 含运费 |
| `USED_GOOD_SHIPPING` | "Used - Good" 含运费 |
| `USED_ACCEPTABLE_SHIPPING` | "Used - Acceptable" 含运费 |
| `COLLECTIBLE_NEW_SHIPPING` | "Collectible - Like New" 含运费 |
| `COLLECTIBLE_VERY_GOOD_SHIPPING` | "Collectible - Very Good" 含运费 |
| `COLLECTIBLE_GOOD_SHIPPING` | "Collectible - Good" 含运费 |
| `COLLECTIBLE_ACCEPTABLE_SHIPPING` | "Collectible - Acceptable" 含运费 |
| `REFURBISHED_SHIPPING` | 翻新含运费价格 |

### 计数类型

| 键 | 说明 |
|-----|------|
| `COUNT_NEW` | 全新报价数量历史 |
| `COUNT_USED` | 二手报价数量历史 |
| `COUNT_REFURBISHED` | 翻新报价数量历史 |
| `COUNT_COLLECTIBLE` | 收藏品报价数量历史 |

### 评分类型

| 键 | 说明 |
|-----|------|
| `RATING` | 评分历史(0-50，如45=4.5星) |
| `COUNT_REVIEWS` | 评论数量历史 |

### Buy Box 类型

| 键 | 说明 |
|-----|------|
| `BUY_BOX_SHIPPING` | Buy Box 价格历史(含运费) |
| `BUY_BOX_USED` | 二手 Buy Box 价格 |
| `TRADE_IN` | 以旧换新价格历史 |

### 每个数据类型都有对应的时间字段

例如：`NEW` 对应 `NEW_time`，`USED` 对应 `USED_time`

**Python 示例:**

```python
product = products[0]
data = product['data']

# 获取 NEW 价格历史
new_prices = data['NEW']
new_times = data['NEW_time']

# 获取销售排名历史
sales_ranks = data['SALES']
sales_times = data['SALES_time']

# 获取评分历史
ratings = data['RATING']
rating_times = data['RATING_time']

# 打印最近10条价格
for i in range(min(10, len(new_prices))):
    print(f"{new_times[i]}: ${new_prices[i]/100:.2f}")
```

---

## 请求参数详解

### 统计参数 (stats)

`stats` 参数用于请求特定时间范围内的统计数据。

```python
# 请求 30 天统计
products = api.query('B0088PUEPK', stats=30)

# 访问统计数据
stats = product['stats']
print(f"当前价格: ${stats['current']/100:.2f}")
print(f"平均价格: ${stats['avg']/100:.2f}")
print(f"最低价格: ${stats['min']/100:.2f}")
print(f"最高价格: ${stats['max']/100:.2f}")
```

### Offers 参数

`offers` 参数用于获取详细的卖家报价历史。

```python
# 获取 20 个 offers（消耗额外 token）
products = api.query('B0088PUEPK', offers=20)
product = products[0]

# 所有 offers
offers = product['offers']

# 活跃 offers 索引
active_indices = product['liveOffersOrder']

# 遍历活跃 offers
for idx in active_indices:
    offer = offers[idx]
    seller_id = offer['sellerId']
    condition = offer['condition']
    is_fba = offer['isFBA']
    
    # 获取 offer 价格历史
    csv = offer['offerCSV']
    times, prices = keepa.convert_offer_history(csv)
    
    print(f"卖家: {seller_id}, 条件: {condition}, FBA: {is_fba}")
    print(f"当前价格: ${prices[-1]/100:.2f}")
```

### 更新参数 (update)

```python
# 只获取数据年龄小于 1 小时的产品
products = api.query('B0088PUEPK', update=1)

# 如果数据过期，API 会自动刷新
```

---

## Python 客户端使用

### 安装

```bash
pip install keepa
```

### 依赖

- Python >= 3.10
- numpy
- aiohttp
- matplotlib (可选，用于绘图)
- tqdm

### 基础使用

```python
import keepa

# 初始化 API
accesskey = 'YOUR_64_CHAR_ACCESS_KEY'
api = keepa.Keepa(accesskey)

# 查询产品
products = api.query('B0088PUEPK')
product = products[0]

# 打印基本信息
print(f"ASIN: {product['asin']}")
print(f"标题: {product['title']}")
print(f"品牌: {product['brand']}")

# 获取当前价格
data = product['data']
if len(data['NEW']) > 0:
    current_price = data['NEW'][-1]
    print(f"当前价格: ${current_price/100:.2f}")

# 获取当前销售排名
if len(data['SALES']) > 0:
    current_rank = data['SALES'][-1]
    print(f"当前排名: {current_rank}")

# 获取评分
if 'RATING' in data and len(data['RATING']) > 0:
    rating = data['RATING'][-1]
    print(f"评分: {rating/10:.1f}")
```

### 使用 UPC/EAN/ISBN-13 查询

```python
# 使用 UPC 查询
products = api.query('883904227319', product_code_is_asin=False)

# 使用 ISBN-13 查询
products = api.query('978-0786222728', product_code_is_asin=False)
```

### 批量查询

```python
import numpy as np

# 使用列表
asins = ['B0088PUEPK', 'B00ZVJAF3G', 'B00H93NJLS']
products = api.query(asins)

# 使用 numpy 数组
asins = np.asarray(['B0088PUEPK', 'B00ZVJAF3G'])
products = api.query(asins)
```

### 绘图

```python
import matplotlib.pyplot as plt

# 使用 keepa 内置绘图
keepa.plot_product(product)

# 或使用 matplotlib 自定义
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

## 异步 API 使用

对于大量并发查询，使用异步 API 更高效。

```python
import asyncio
import keepa

async def main():
    # 创建异步客户端
    api = await keepa.AsyncKeepa().create('YOUR_ACCESS_KEY')
    
    # 异步查询
    products = await api.query('B0088PUEPK')
    
    # 批量异步查询
    asins = ['B0088PUEPK', 'B00ZVJAF3G', 'B00H93NJLS']
    
    # 创建多个并发任务
    tasks = [api.query(asin) for asin in asins]
    results = await asyncio.gather(*tasks)
    
    for asin, products in zip(asins, results):
        print(f"{asin}: {products[0]['title']}")
    
    # 异步产品查找
    product_parms = {'author': 'brandon sanderson'}
    asins = await api.product_finder(product_parms)
    
    # 异步畅销榜
    categories = await api.search_for_categories("books")
    category_id = list(categories.keys())[0]
    bestsellers = await api.best_sellers_query(category_id)
    
    return results

# 运行
results = asyncio.run(main())
```

### 不等待 Token  refill

```python
# 如果 token 不足，不等待直接返回错误
products = await api.query('B0088PUEPK', wait=False)
```

---

## Buy Box 数据分析

### 获取 Buy Box 历史

```python
products = api.query('B0088PUEPK', buybox=True)
product = products[0]

# Buy Box 历史
buybox_history = product['buyBoxSellerIdHistory']
buybox_prices = product['data']['BUY_BOX_SHIPPING']
```

### 处理二手 Buy Box

```python
import pandas as pd

# 需要启用 offers 参数
products = api.query('B0088PUEPK', offers=20)
product = products[0]

# 处理二手 Buy Box 数据
buybox_info = product.get('buyBoxUsedHistory', [])
if buybox_info:
    df = keepa.process_used_buybox(buybox_info)
    print(df.head())
    # 输出: datetime, user_id, condition, isFBA
```

---

## Token 管理

### 检查 Token 状态

```python
# 获取当前 token 数量
tokens_left = api.tokens_left
print(f"剩余 Token: {tokens_left}")

# 获取 token 补充时间
time_to_refill = api.time_to_refill
print(f"补充时间: {time_to_refill} 秒")
```

### 等待 Token

```python
# 默认行为: 自动等待 token
products = api.query('B0088PUEPK', wait=True)

# 不等待，立即执行
products = api.query('B0088PUEPK', wait=False)
```

---

## 错误处理

```python
import keepa

try:
    api = keepa.Keepa('INVALID_KEY')
    products = api.query('B0088PUEPK')
except Exception as e:
    print(f"错误: {e}")

# 常见错误:
# - 无效访问密钥
# - Token 不足 (当 wait=False)
# - 产品未找到
# - 网络错误
```

---

## 时间格式说明

Keepa 使用特殊的分钟时间格式：

- Keepa 时间 = 自 2011-01-01 00:00:00 UTC 以来的分钟数
- Python 库会自动转换为 datetime 对象

```python
# 手动转换
import keepa
keepa_minutes = 5000000
datetime_obj = keepa.keepa_minutes_to_time(keepa_minutes)
print(datetime_obj)  # 2020-06-18 09:20:00
```

---

## 相关链接

### 官方文档

| 链接 | 说明 |
|------|------|
| https://keepa.com/#!api | API 主页 |
| https://keepa.com/#!discuss/t/request-products/110 | 产品请求文档 |
| https://keepa.com/#!discuss/t/product-object/116 | 产品对象文档 |
| https://keepa.com/#!discuss/t/browsing-deals/338 | Deals 查询文档 |
| https://keepa.com/#!discuss/t/request-seller-information/790 | 卖家信息文档 |
| https://keepa.com/#!discuss/t/request-best-sellers/340 | 畅销榜文档 |
| https://keepa.com/#!discuss/t/searching-categories/232 | 类目搜索文档 |

### 开发者资源

| 链接 | 说明 |
|------|------|
| https://keepaapi.readthedocs.io | Python 客户端文档 |
| https://github.com/akaszynski/keepa | Python 客户端源码 |
| https://github.com/keepacom/api_backend | Java 后端源码 |

### 获取 API Key

https://keepa.com/#!api (需注册 Keepa 账户)

---

## 最佳实践

### 1. 批量查询

```python
# 好的做法: 批量查询
asins = ['A', 'B', 'C', 'D', 'E']
products = api.query(asins)  # 使用更少 token

# 避免: 循环单个查询
for asin in asins:
    product = api.query(asin)  # 消耗更多 token
```

### 2. 缓存数据

```python
# 使用 stats 参数获取统计数据，而不是完整历史
products = api.query(asins, stats=30, history=False)
```

### 3. 异步处理大量查询

```python
async def batch_query(asins):
    api = await keepa.AsyncKeepa().create(KEY)
    tasks = [api.query(asin) for asin in asins]
    return await asyncio.gather(*tasks)
```

### 4. 错误重试

```python
import time

def query_with_retry(asin, max_retries=3):
    for i in range(max_retries):
        try:
            return api.query(asin)
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # 指数退避
```

---

## 总结

Keepa API 是亚马逊产品数据分析的强大工具，提供：

1. **全面的数据覆盖**: 40亿+ 产品，多种价格类型
2. **丰富的历史数据**: 价格、排名、评分、评论历史
3. **多样的查询方式**: ASIN、类目、卖家、Deals
4. **灵活的 Python 客户端**: 同步/异步支持
5. **透明的定价**: 基于 Token 的计费模式

通过合理使用批量查询、异步处理和缓存策略，可以高效地获取和分析亚马逊市场数据。

---

*本文档基于 Keepa 官方 API 文档整理，如有更新请以官方文档为准。*
