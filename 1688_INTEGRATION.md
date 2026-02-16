# 1688 以图搜图采购价格集成

本系统支持通过1688 API自动获取采购价格，实现从Amazon产品图片直接搜索1688供应商报价。

## 功能特性

✅ **以图搜图**: 使用Amazon产品图片在1688搜索相似商品  
✅ **自动计算**: 根据重量自动计算头程运费  
✅ **成本估算**: 自动计算完整COGS(含关税、汇率转换)  
✅ **智能排序**: 综合考虑价格、匹配度、供应商等级  
✅ **一键报告**: 自动生成包含采购价格的精算师报告  

## 快速开始

### 1. 获取TMAPI Token

访问 [TMAPI官网](https://tmapi.top) 注册并获取API Token。

### 2. 配置环境变量

```bash
# .env 文件
TMAPI_TOKEN=your_tmapi_token_here
KEEPA_KEY=your_keepa_key_here
```

### 3. 运行分析

```python
from src.procurement_analyzer import generate_auto_procurement_report

# 一键生成带采购价格的完整报告
report_path, analyses = generate_auto_procurement_report('B0F6B5R47Q')
```

## 详细用法

### 基础采购价格搜索

```python
from src.procurement_analyzer import SmartProcurementAnalyzer

# 创建分析器
analyzer = SmartProcurementAnalyzer.from_env()

# 分析单个产品
result = analyzer.analyze_product(keepa_product, target_moq=100)

if result.found:
    print(f"采购价格: ¥{result.price_rmb}")
    print(f"总COGS: ${result.total_cogs_usd}")
```

### 批量分析

```python
# 分析整个变体组合
analyses = analyzer.analyze_portfolio(products, target_moq=100)

# 转换为财务数据
financials_map = analyzer.to_financials_map(analyses)
```

### 不使用API时

如果没有1688 API，可以使用交互式报告手动填入：

```python
# 生成报告时会自动创建交互式版本
# 打开 *_ALLINONE_INTERACTIVE.html
# 在"采购成本"输入框填入价格即可自动计算
```

## API方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **TMAPI** | 简单快速 | 收费 (~$0.01-0.05/次) | 推荐方案 |
| **1688官方** | 免费 | 需企业资质 | 有资质企业 |
| **手动输入** | 准确 | 耗时 | 小规模使用 |

## 成本计算公式

```
总COGS (USD) = [采购价(RMB) + 头程运费(RMB)] × 1.15(关税) ÷ 汇率

其中:
- 头程运费 = 重量(kg) × 12 RMB/kg
- 汇率 = 7.2 RMB/USD (可配置)
- 关税 = 15% (可配置)
```

## 数据结构

### ProcurementAnalysis

```python
{
    "asin": "B0F6B5R47Q",
    "found": True,
    "price_rmb": 35.50,          # 采购价格(人民币)
    "moq": 100,                   # 最小起订量
    "supplier": "XX工厂",         # 供应商名称
    "source_url": "https://...",  # 1688链接
    "match_score": 0.85,          # 图片匹配度
    "confidence": "high",         # 置信度
    "shipping_cost_rmb": 4.80,    # 头程运费
    "total_cogs_usd": 6.45        # 总COGS(美元)
}
```

## 注意事项

⚠️ **图片限制**: 
- 1688以图搜图主要支持阿里系平台图片
- Amazon图片可能需要转换

⚠️ **准确度**: 
- 建议人工确认关键产品价格
- 以图搜图可能返回相似但不完全相同的商品

⚠️ **MOQ考量**: 
- 注意MOQ是否适合您的采购量
- 系统会标注MOQ过高的情况

## 配置文件

```env
# 必需
KEEPA_KEY=your_keepa_api_key

# 1688 API (推荐TMAPI)
TMAPI_TOKEN=your_tmapi_token

# 可选 - 成本计算参数
SHIPPING_RATE=12          # RMB/kg
EXCHANGE_RATE=7.2         # RMB/USD
TARIFF_RATE=0.15          # 15%
```

## 示例代码

见 `examples/1688_procurement_example.py`

```bash
cd examples
python 1688_procurement_example.py
```

## 故障排除

### 找不到采购价格

- 检查TMAPI_TOKEN是否正确设置
- 确认产品图片是否可访问
- 尝试调整target_moq参数

### 价格不准确

- 人工确认1688搜索结果
- 考虑MOQ和供应商等级
- 检查重量数据是否正确

### API调用失败

- 检查网络连接
- 确认API Token余额
- 查看TMAPI服务状态

## 相关文件

- `src/cn_1688_api.py` - 1688 API客户端
- `src/procurement_analyzer.py` - 智能采购分析器
- `src/allinone_interactive_report.py` - 交互式报告

## 更新计划

- [ ] 支持1688官方API
- [ ] 图片自动转换到阿里图床
- [ ] 历史价格趋势分析
- [ ] 多供应商比价功能
