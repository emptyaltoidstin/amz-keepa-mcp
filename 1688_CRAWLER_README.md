# 1688 以图搜图爬虫方案

基于开源项目 [Zhui-CN/1688_image_search_crawler](https://github.com/Zhui-CN/1688_image_search_crawler) 实现的1688采购价格自动采集。

## 方案对比

| 特性 | TMAPI方案 | **开源爬虫方案** (推荐) |
|------|-----------|------------------------|
| **成本** | $0.01-0.05/次 | **免费** |
| **稳定性** | 高 (商业服务) | 中等 (依赖1688接口) |
| **速度** | 快 | 中等 (~2-5秒/次) |
| **API Key** | 需要 | **不需要** |
| **配置复杂度** | 低 | 低 |
| **反爬风险** | 无 | **有** |
| **法律风险** | 无 | 低 (需遵守1688服务条款) |

## 实现原理

```
Amazon产品图片
      ↓
下载图片 → base64编码
      ↓
调用1688 H5 API (h5api.m.1688.com)
      ↓
上传图片获取 imageId
      ↓
使用imageId搜索相似商品
      ↓
解析返回的JSON数据
      ↓
获取价格、MOQ、供应商信息
```

## 使用方法

### 1. 基础使用

```python
from procurement_1688_integration import generate_1688_procurement_report

# 一键生成带1688采购价格的完整报告
report_path, results = generate_1688_procurement_report('B0F6B5R47Q')
```

### 2. 分步使用

```python
from procurement_1688_integration import Smart1688Procurement

# 创建分析器
analyzer = Smart1688Procurement.from_env()

# 分析单个产品
result = analyzer.analyze_product(keepa_product, target_moq=100)

if result.found:
    print(f"采购价格: ¥{result.price_rmb}")
    print(f"供应商: {result.supplier}")
    print(f"总COGS: ${result.total_cogs_usd}")
```

### 3. 直接调用爬虫

```python
from cn_1688_crawler import CN1688Crawler

crawler = CN1688Crawler()

# 通过图片URL搜索
offers = crawler.search_by_image_url(
    'https://example.com/image.jpg',
    max_results=10
)

for offer in offers:
    print(f"{offer.company_name}: ¥{offer.price} (MOQ:{offer.moq})")
```

## 数据结构

### ProcurementResult

```python
{
    "asin": "B0F6B5R47Q",
    "found": True,
    "price_rmb": 35.50,          # 采购价格(人民币)
    "moq": 100,                   # 最小起订量
    "supplier": "XX工厂",         # 供应商名称
    "location": "广东 深圳",      # 供应商位置
    "is_verified": True,          # 是否认证商家
    "product_url": "https://...", # 1688商品链接
    "confidence": "high",         # 置信度
    "weight_kg": 0.45,           # 产品重量
    "shipping_cost_rmb": 5.40,   # 头程运费
    "total_cogs_usd": 6.45       # 总COGS(美元)
}
```

### CNSupplierOffer (详细报价)

```python
{
    "offer_id": "123456789",
    "title": "产品标题",
    "price": 35.50,
    "moq": 100,
    "unit": "件",
    "image_url": "https://...",
    "company_name": "XX工厂",
    "province": "广东",
    "city": "深圳",
    "shop_url": "https://...",
    "is_verified": True,
    "credit_level": "AAA",
    "years": 5,                  # 诚信通年限
    "repurchase_rate": "45%",    # 复购率
    "product_url": "https://...",
    "quantity_prices": [         # 阶梯价格
        {"quantity": "1~99", "price": 35.50},
        {"quantity": ">=100", "price": 32.00}
    ],
    "scores": {                  # 店铺评分
        "composite": 4.5,
        "goods": 4.0,
        "logistics": 4.5
    },
    "position_labels": ["源头工厂", "7×24H响应"]
}
```

## 成本计算公式

```
总COGS (USD) = [采购价 + (重量kg × 船运价格)] × 1.15(关税) ÷ 汇率

默认参数:
- 船运价格: 12 RMB/kg
- 汇率: 7.2 RMB/USD
- 关税: 15%
```

## 注意事项

### ⚠️ 反爬风险

1. **频率限制**: 1688可能有请求频率限制
2. **IP封禁**: 频繁调用可能导致IP被封
3. **服务稳定性**: 1688接口可能随时变更

**建议**:
- 适当添加请求间隔 (已实现 0.5秒延迟)
- 批量分析时控制速度
- 准备备选方案 (TMAPI或手动输入)

### ⚠️ 准确度问题

1. **图片匹配**: 以图搜图不一定100%准确
2. **价格变动**: 1688价格可能实时变动
3. **MOQ差异**: 注意MOQ是否符合需求

**建议**:
- 关键产品人工确认
- 使用置信度评估结果可靠性
- 多个变体取平均价格

## 故障排除

### 无法获取token

```
错误: 无法获取_m_h5_tk cookie
```

**解决**:
- 检查网络连接
- 1688接口可能已变更，需要更新代码
- 切换到TMAPI方案

### 上传图片失败

```
错误: 上传图片失败
```

**解决**:
- 检查图片URL是否可访问
- 图片大小可能过大 (建议 < 5MB)
- 1688服务可能暂时不可用

### 返回空结果

```
1688未找到匹配商品
```

**解决**:
- 产品可能在1688上没有相似款
- 尝试使用不同的产品图片
- 检查图片质量

## 备选方案

如果爬虫方案不可用，可切换到：

1. **TMAPI方案**: 商业API，稳定性高
2. **手动输入**: 使用All-in-One交互式报告手动填入

```python
# 切换到TMAPI方案
from procurement_analyzer import SmartProcurementAnalyzer

analyzer = SmartProcurementAnalyzer(tmapi_token="your_token")
```

## 文件结构

```
src/
├── cn_1688_crawler.py              # 1688爬虫核心
├── procurement_1688_integration.py # 集成模块
└── procurement_analyzer.py         # TMAPI方案(备选)
```

## 更新日志

### v1.0 (2024-02)
- 初始版本
- 实现以图搜图功能
- 支持价格、MOQ、供应商信息采集
- 集成到精算师系统

## 免责声明

本实现基于开源项目，仅供学习研究使用。使用时请遵守1688服务条款，不得用于非法用途。商业使用请考虑TMAPI等官方API方案。
