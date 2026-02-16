#!/usr/bin/env python3
"""
Amz-Keepa-MCP Server
====================
MCP server for Amazon FBA actuary analysis

Usage with Claude Code:
1. Configure MCP server in Claude Code settings
2. Use: @amz-keepa 分析 ASIN B0F6B5R47Q
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from mcp.server.models import InitializationOptions


class AmzKeepaServer:
    """Amz-Keepa MCP Server"""
    
    def __init__(self):
        self.server = Server("amz-keepa")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup MCP handlers"""
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="docs://readme",
                    name="使用文档",
                    description="Amz-Keepa-MCP 使用说明",
                    mimeType="text/markdown"
                ),
                Resource(
                    uri="docs://commission-rates",
                    name="佣金比例表",
                    description="Amazon各类目佣金比例",
                    mimeType="text/markdown"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "docs://readme":
                return self._get_readme()
            elif uri == "docs://commission-rates":
                return self._get_commission_rates()
            raise ValueError(f"Unknown resource: {uri}")
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="analyze_asin",
                    description="分析Amazon ASIN，生成完整精算师报告",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "asin": {
                                "type": "string",
                                "description": "Amazon产品ASIN (如: B0F6B5R47Q)"
                            },
                            "target_moq": {
                                "type": "integer",
                                "description": "目标采购量 (可选，默认100)",
                                "default": 100
                            }
                        },
                        "required": ["asin"]
                    }
                ),
                Tool(
                    name="get_product_info",
                    description="获取产品基本信息 (快速查询)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "asin": {
                                "type": "string",
                                "description": "Amazon产品ASIN"
                            }
                        },
                        "required": ["asin"]
                    }
                ),
                Tool(
                    name="calculate_cogs",
                    description="计算COGS成本",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procurement_price_rmb": {
                                "type": "number",
                                "description": "1688采购价 (RMB)"
                            },
                            "weight_kg": {
                                "type": "number",
                                "description": "产品重量 (kg)"
                            },
                            "shipping_rate": {
                                "type": "number",
                                "description": "船运价格 RMB/kg (可选，默认12)",
                                "default": 12
                            },
                            "tariff_rate": {
                                "type": "number",
                                "description": "关税率 (可选，默认0.15)",
                                "default": 0.15
                            },
                            "exchange_rate": {
                                "type": "number",
                                "description": "汇率 (可选，默认7.2)",
                                "default": 7.2
                            }
                        },
                        "required": ["procurement_price_rmb", "weight_kg"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool calls"""
            
            if name == "analyze_asin":
                return await self._handle_analyze_asin(arguments)
            elif name == "get_product_info":
                return await self._handle_get_product_info(arguments)
            elif name == "calculate_cogs":
                return await self._handle_calculate_cogs(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_analyze_asin(self, arguments: Dict) -> list[TextContent]:
        """Handle analyze_asin tool"""
        asin = arguments.get("asin", "").strip().upper()
        target_moq = arguments.get("target_moq", 100)
        
        if not asin:
            return [TextContent(type="text", text="❌ 错误: 请提供有效的ASIN")]
        
        # Validate ASIN format
        if not asin.startswith("B") or len(asin) != 10:
            return [TextContent(type="text", text=f"⚠️ 警告: ASIN '{asin}' 格式可能不正确，标准ASIN为10位字符")]
        
        # Check API key
        keepa_key = os.getenv("KEEPA_KEY")
        if not keepa_key:
            return [TextContent(type="text", text="❌ 错误: 未设置 KEEPA_KEY 环境变量")]
        
        # Generate report
        try:
            from generate_report import generate_complete_report
            
            result = generate_complete_report(asin, target_moq)
            
            if result is None:
                return [TextContent(type="text", text=f"❌ 生成报告失败，请检查ASIN '{asin}' 是否有效")]
            
            report_path = result['unified_report']
            variants_count = result['variants_count']
            
            # Generate response
            response = f"""✅ 统一精算师报告生成完成!

📦 ASIN: {result['parent_asin']}
📊 变体数量: {variants_count}

📁 报告路径:
   {report_path}

📋 报告内容:
   ✓ 产品信息 (品牌/类目/总销量/评论/评分)
   ✓ 交互式成本计算器 (填入1688采购价即计算)
   ✓ 完整变体分析表 (BSR/销量/评分/评论/退货率/FBA费/佣金)
   ✓ 帕累托分析 (80/20核心变体)
   ✓ 风险评估
   ✓ 投资建议与行动计划

📝 使用方法:
   1. 打开报告查看完整分析
   2. 在"采购成本"输入框填入1688采购价
   3. 系统自动计算完整利润分析

💡 提示:
   所有FBA费用基于Keepa真实尺寸重量计算
   佣金比例基于类目自动确定 (Electronics 8%, Clothing 17%, 等)
"""
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ 生成报告时出错: {str(e)}")]
    
    async def _handle_get_product_info(self, arguments: Dict) -> list[TextContent]:
        """Handle get_product_info tool"""
        asin = arguments.get("asin", "").strip().upper()
        
        if not asin:
            return [TextContent(type="text", text="❌ 请提供ASIN")]
        
        try:
            from variant_auto_collector import VariantAutoCollector
            
            api_key = os.getenv("KEEPA_KEY")
            if not api_key:
                return [TextContent(type="text", text="❌ 未设置 KEEPA_KEY")]
            
            collector = VariantAutoCollector(api_key)
            products, parent_info = collector.collect_variants(asin)
            
            if not products:
                return [TextContent(type="text", text=f"❌ 未找到ASIN '{asin}' 的数据")]
            
            # Format product info
            info = f"""📦 产品信息: {asin}

基本信息:
   父ASIN: {parent_info.get('parent_asin', 'N/A')}
   品牌: {parent_info.get('brand', 'N/A')}
   类目: {parent_info.get('category', 'N/A')}
   变体数量: {len(products)}

变体列表:
"""
            for i, p in enumerate(products[:5], 1):
                attrs = p.get('attributes', [])
                color = next((a.get('value', '') for a in attrs if a.get('name') == 'Color'), 'N/A')
                size = next((a.get('value', '') for a in attrs if a.get('name') == 'Size'), 'N/A')
                info += f"   {i}. {p.get('asin', '')} - {color}/{size}\n"
            
            if len(products) > 5:
                info += f"   ... 还有 {len(products)-5} 个变体\n"
            
            return [TextContent(type="text", text=info)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ 查询失败: {str(e)}")]
    
    async def _handle_calculate_cogs(self, arguments: Dict) -> list[TextContent]:
        """Handle calculate_cogs tool"""
        procurement = arguments.get("procurement_price_rmb", 0)
        weight = arguments.get("weight_kg", 0)
        shipping_rate = arguments.get("shipping_rate", 12)
        tariff_rate = arguments.get("tariff_rate", 0.15)
        exchange_rate = arguments.get("exchange_rate", 7.2)
        
        if procurement <= 0 or weight <= 0:
            return [TextContent(type="text", text="❌ 请提供有效的采购价和重量")]
        
        # Calculate
        shipping = weight * shipping_rate
        subtotal = procurement + shipping
        tariff = subtotal * tariff_rate
        total_rmb = subtotal + tariff
        cogs_usd = total_rmb / exchange_rate
        
        result = f"""💰 COGS成本计算

输入:
   采购价: ¥{procurement:.2f}
   重量: {weight:.2f} kg
   船运: ¥{shipping_rate}/kg
   关税: {tariff_rate*100:.0f}%
   汇率: {exchange_rate}

计算:
   头程运费 = {weight:.2f} × {shipping_rate} = ¥{shipping:.2f}
   小计 = {procurement:.2f} + {shipping:.2f} = ¥{subtotal:.2f}
   关税 = {subtotal:.2f} × {tariff_rate} = ¥{tariff:.2f}
   总计(RMB) = ¥{total_rmb:.2f}
   
   COGS(USD) = {total_rmb:.2f} ÷ {exchange_rate} = ${cogs_usd:.2f}

✅ 总COGS: ${cogs_usd:.2f} USD
"""
        return [TextContent(type="text", text=result)]
    
    def _get_readme(self) -> str:
        """Get readme content"""
        return """# Amz-Keepa-MCP 使用指南

## 标准流程

使用 `analyze_asin` 工具生成完整报告：

```
@amz-keepa 分析 ASIN B0F6B5R47Q
```

或带参数：

```
@amz-keepa 分析 ASIN B0F6B5R47Q，目标采购量 200
```

## 工具列表

### 1. analyze_asin
生成完整的统一精算师报告

**参数:**
- `asin`: Amazon产品ASIN (必需)
- `target_moq`: 目标采购量 (可选，默认100)

### 2. get_product_info
快速查询产品基本信息

**参数:**
- `asin`: Amazon产品ASIN (必需)

### 3. calculate_cogs
计算COGS成本

**参数:**
- `procurement_price_rmb`: 1688采购价 (必需)
- `weight_kg`: 产品重量kg (必需)
- `shipping_rate`: 船运价格 (可选，默认12)
- `tariff_rate`: 关税率 (可选，默认0.15)
- `exchange_rate`: 汇率 (可选，默认7.2)

## 佣金比例参考

| 类目 | 佣金 |
|------|------|
| Electronics | 8% |
| Clothing | 17% |
| Jewelry | 20% |
| Home | 15% |
| 其他 | 15% |
"""
    
    def _get_commission_rates(self) -> str:
        """Get commission rates"""
        return """# Amazon佣金比例表

| 类目 | 佣金比例 |
|------|----------|
| Amazon Device Accessories | 45% |
| Electronics | 8% |
| Electronics Accessories | 15% |
| Camera | 8% |
| Cell Phone Devices | 8% |
| Clothing | 17% |
| Shoes | 17% |
| Handbags | 15% |
| Jewelry | 20% |
| Kitchen | 15% |
| Home | 15% |
| Home Improvement | 15% |
| Beauty | 15% |
| Health & Personal Care | 15% |
| Toys | 15% |
| Sports | 15% |
| Automotive | 15% |
| Books | 15% |
| Music | 15% |
| Video Games | 15% |
| Grocery | 15% |
| Pet Supplies | 15% |
| Office Products | 15% |
| Industrial | 15% |
| Tools | 15% |
| 其他 | 15% |
"""
    
    async def run(self):
        """Run the server"""
        async with stdio_server(self.server) as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="amz-keepa",
                    server_version="3.0",
                    capabilities=self.server.get_capabilities()
                )
            )


def main():
    """Main entry point"""
    server = AmzKeepaServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
