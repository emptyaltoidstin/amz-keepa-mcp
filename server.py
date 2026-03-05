#!/usr/bin/env python3
"""
Amz-Keepa-MCP Server
====================
MCP server for Amazon FBA actuary analysis

Usage with Claude Code:
1. Configure MCP server in Claude Code settings
2. Use: @amz-keepa analysis ASIN B0F6B5R47Q
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
                    name="Use documentation",
                    description="Amz-Keepa-MCP Instructions for Use",
                    mimeType="text/markdown"
                ),
                Resource(
                    uri="docs://commission-rates",
                    name="Commission scale table",
                    description="Amazon commission ratio for various categories",
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
                    description="Analyze Amazon ASIN and generate a complete actuary report",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "asin": {
                                "type": "string",
                                "description": "Amazon product ASIN (Such as: B0F6B5R47Q)"
                            },
                            "target_moq": {
                                "type": "integer",
                                "description": "Target purchase quantity (Optional, default 100)",
                                "default": 100
                            }
                        },
                        "required": ["asin"]
                    }
                ),
                Tool(
                    name="get_product_info",
                    description="Get basic product information (Quick query)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "asin": {
                                "type": "string",
                                "description": "Amazon product ASIN"
                            }
                        },
                        "required": ["asin"]
                    }
                ),
                Tool(
                    name="calculate_cogs",
                    description="Calculate COGS cost",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procurement_price_rmb": {
                                "type": "number",
                                "description": "1688 purchase price (RMB)"
                            },
                            "weight_kg": {
                                "type": "number",
                                "description": "Product weight (kg)"
                            },
                            "shipping_rate": {
                                "type": "number",
                                "description": "Shipping price RMB/kg (Optional, default 12)",
                                "default": 12
                            },
                            "tariff_rate": {
                                "type": "number",
                                "description": "tariff rate (Optional, default 0.15)",
                                "default": 0.15
                            },
                            "exchange_rate": {
                                "type": "number",
                                "description": "exchange rate (Optional, default 7.2)",
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
            return [TextContent(type="text", text="❌ Error: Please provide a valid ASIN")]
        
        # Validate ASIN format
        if not asin.startswith("B") or len(asin) != 10:
            return [TextContent(type="text", text=f"⚠️ WARNING: ASIN '{asin}' The format may be incorrect, standard ASIN is 10 characters")]
        
        # Check API key
        keepa_key = os.getenv("KEEPA_KEY")
        if not keepa_key:
            return [TextContent(type="text", text="❌ Error: KEEPA not set_KEY environment variable")]
        
        # Generate report
        try:
            from generate_report import generate_complete_report
            
            result = generate_complete_report(asin, target_moq)
            
            if result is None:
                return [TextContent(type="text", text=f"❌ Failed to generate report, please check ASIN '{asin}' Is it valid?")]
            
            report_path = result['unified_report']
            variants_count = result['variants_count']
            
            # Generate response
            response = f"""✅ The unified actuary report is generated!

📦 ASIN: {result['parent_asin']}
📊Number of variants: {variants_count}

📁 Report path:
   {report_path}

📋 Report content:
   ✓ Product information (brand/Category/total sales/Comment/score)
   ✓ Interactive cost calculator (Fill in the 1688 purchase price and it will be calculated.)
   ✓ Complete variant analysis table (BSR/Sales volume/score/Comment/return rate/FBA fee/Commission)
   ✓ Pareto analysis (80/20 core variants)
   ✓ Risk assessment
   ✓ Investment advice and action plan

📝 How to use:
   1. Open the report to view the complete analysis
   2. in"Procurement cost"Fill in the input box with the purchase price of 1688
   3. The system automatically calculates complete profit analysis

💡 Tips:
   All FBA fees are calculated based on Keepa true dimensional weight
   The commission ratio is automatically determined based on the category (Electronics 8%, Clothing 17%, Wait)
"""
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error while generating report: {str(e)}")]
    
    async def _handle_get_product_info(self, arguments: Dict) -> list[TextContent]:
        """Handle get_product_info tool"""
        asin = arguments.get("asin", "").strip().upper()
        
        if not asin:
            return [TextContent(type="text", text="❌ Please provide ASIN")]
        
        try:
            from variant_auto_collector import VariantAutoCollector
            
            api_key = os.getenv("KEEPA_KEY")
            if not api_key:
                return [TextContent(type="text", text="❌ KEEPA not set_KEY")]
            
            collector = VariantAutoCollector(api_key)
            products, parent_info = collector.collect_variants(asin)
            
            if not products:
                return [TextContent(type="text", text=f"❌ ASIN not found '{asin}' data")]
            
            # Format product info
            info = f"""📦 Product information: {asin}

Basic information:
   Parent ASIN: {parent_info.get('parent_asin', 'N/A')}
   brand: {parent_info.get('brand', 'N/A')}
   Category: {parent_info.get('category', 'N/A')}
   Number of variants: {len(products)}

Variation list:
"""
            for i, p in enumerate(products[:5], 1):
                attrs = p.get('attributes', [])
                color = next((a.get('value', '') for a in attrs if a.get('name') == 'Color'), 'N/A')
                size = next((a.get('value', '') for a in attrs if a.get('name') == 'Size'), 'N/A')
                info += f"   {i}. {p.get('asin', '')} - {color}/{size}\n"
            
            if len(products) > 5:
                info += f"   ...and {len(products)-5} variants\n"
            
            return [TextContent(type="text", text=info)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Query failed: {str(e)}")]
    
    async def _handle_calculate_cogs(self, arguments: Dict) -> list[TextContent]:
        """Handle calculate_cogs tool"""
        procurement = arguments.get("procurement_price_rmb", 0)
        weight = arguments.get("weight_kg", 0)
        shipping_rate = arguments.get("shipping_rate", 12)
        tariff_rate = arguments.get("tariff_rate", 0.15)
        exchange_rate = arguments.get("exchange_rate", 7.2)
        
        if procurement <= 0 or weight <= 0:
            return [TextContent(type="text", text="❌ Please provide valid purchase price and weight")]
        
        # Calculate
        shipping = weight * shipping_rate
        subtotal = procurement + shipping
        tariff = subtotal * tariff_rate
        total_rmb = subtotal + tariff
        cogs_usd = total_rmb / exchange_rate
        
        result = f"""💰 COGS cost calculation

input:
   purchase price: ¥{procurement:.2f}
   weight: {weight:.2f} kg
   Shipping: ¥{shipping_rate}/kg
   tariff: {tariff_rate*100:.0f}%
   exchange rate: {exchange_rate}

Calculate:
   First leg freight = {weight:.2f} × {shipping_rate} = ¥{shipping:.2f}
   Subtotal = {procurement:.2f} + {shipping:.2f} = ¥{subtotal:.2f}
   tariff = {subtotal:.2f} × {tariff_rate} = ¥{tariff:.2f}
   total(RMB) = ¥{total_rmb:.2f}
   
   COGS(USD) = {total_rmb:.2f} ÷ {exchange_rate} = ${cogs_usd:.2f}

✅ Total COGS: ${cogs_usd:.2f} USD
"""
        return [TextContent(type="text", text=result)]
    
    def _get_readme(self) -> str:
        """Get readme content"""
        return """# Amz-Keepa-MCP User Guide

## standard process

use `analyze_asin` The tool generates a full report:

```
@amz-keepa analysis ASIN B0F6B5R47Q
```

Or with parameters:

```
@amz-keepa analyzes ASIN B0F6B5R47Q, target purchase quantity 200
```

## Tool list

### 1. analyze_asin
Generate complete unified actuarial report

**parameters:**
- `asin`: Amazon product ASIN (required)
- `target_moq`: Target purchase quantity (Optional, default 100)

### 2. get_product_info
Quickly query basic product information

**parameters:**
- `asin`: Amazon product ASIN (required)

### 3. calculate_cogs
Calculate COGS cost

**parameters:**
- `procurement_price_rmb`: 1688 purchase price (required)
- `weight_kg`: Product weightkg (required)
- `shipping_rate`: shipping price (Optional, default 12)
- `tariff_rate`: tariff rate (Optional, default 0.15)
- `exchange_rate`: exchange rate (Optional, default 7.2)

## Commission ratio reference

| Category | Commission |
|------|------|
| Electronics | 8% |
| Clothing | 17% |
| Jewelry | 20% |
| Home | 15% |
| Others | 15% |
"""
    
    def _get_commission_rates(self) -> str:
        """Get commission rates"""
        return """# Amazon commission ratio table

| Category | Commission ratio |
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
| Others | 15% |
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
