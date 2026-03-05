# Amz-Keepa-MCP Setup Guide

## Used in Claude Code

### Way 1: Used directly within the project (recommend)

Go to the project directory in Claude Code, then:

```bash
# Start Claude Code in the project directory
claude

# and then use
@amz-keepa analysis ASIN B0F6B5R47Q
```

### Way 2: Configure to Claude Code settings

Edit the Claude Code configuration file:

```bash
# Edit configuration file
claude config set mcpServers.amz-keepa.command "python3"
claude config set mcpServers.amz-keepa.args '["server.py"]'
claude config set mcpServers.amz-keepa.cwd "/Users/blobeats/Downloads/amz-keepa-mcp"
```

or edit manually `~/.claude/settings.json`：

```json
{
  "mcpServers": {
    "amz-keepa": {
      "command": "python3",
      "args": ["server.py"],
      "cwd": "/Users/blobeats/Downloads/amz-keepa-mcp",
      "env": {
        "KEEPA_KEY": "your_keepa_api_key_here"
      }
    }
  }
}
```

### Way 3: Using MCP profiles

```bash
# Specify configuration file at startup
claude --mcp-config .claude-mcp.json
```

## Usage example

### 1. Analyze ASINs (standard process)

```
@amz-keepa analysis ASIN B0F6B5R47Q
```

Output:
```
✅ The unified actuary report is generated!

📦 ASIN: B0F6B5R47Q
📊Number of variants: 9

📁 Report path:
   cache/reports/B0F6B5R47Q_UNIFIED_ACTUARY.html

📋 Report content:
   ✓ Product information (brand/Category/total sales/Comment/score)
   ✓ Interactive cost calculator
   ✓ Complete variant analysis table (BSR/Sales volume/score/Comment/return rate/FBA fee/Commission)
   ✓ Pareto analysis
   ✓ Risk assessment
   ✓ Investment advice and action plan

📝 How to use:
   1. Open the report to view the complete analysis
   2. in"Procurement cost"Fill in the input box with the purchase price of 1688
   3. The system automatically calculates complete profit analysis
```

### 2. Analysis with parameters

```
@amz-keepa analyzes ASIN B0F6B5R47Q, target purchase quantity 200
```

### 3. Quickly query product information

```
@amz-keepa Get basic information about product B0F6B5R47Q
```

### 4. Calculate COGS

```
@amz-keepa calculates COGS, purchase price is 35.5 yuan, weight is 0.45kg
```

## Environment variable settings

Make sure the Keepa API Key is set:

```bash
# Create an .env file in the project directory
echo "KEEPA_KEY=your_api_key_here" > .env

# Or set before starting claude
export KEEPA_KEY=your_api_key_here
claude
```

## Tool description

| Tools | Function | Example |
|------|------|------|
| `analyze_asin` | Generate full actuarial report | `@amz-keepa analysis ASIN B0F6B5R47Q` |
| `get_product_info` | Quickly query product information | `@amz-keepa Get product B0F6B5R47Q information` |
| `calculate_cogs` | Calculate COGS cost | `@amz-keepa calculates COGS, purchase price 35.5, weight 0.45` |

## troubleshooting

### 1. MCP tool not displayed

Check server.py for errors:

```bash
cd /Users/blobeats/Downloads/amz-keepa-mcp
python3 server.py
```

### 2. Keepa API Key error

Confirm KEEPA in .env file_KEY is set:

```bash
cat .env
```

### 3. Missing dependencies

Install required dependencies:

```bash
pip install -r requirements.txt
```

## File structure

```
amz-keepa-mcp/
├── server.py              # MCP server main file
├── .claude-mcp.json       # Claude Code MCP configuration
├── mcp-config.json        # Generic MCP configuration
├── MCP_SETUP.md           # this document
└── src/
    ├── unified_report_v2.py   # report generator
    └── ...
```

## Change log

### v3.0 (2026-02-16)
- ✅ Added MCP server support
- ✅Support Claude Code direct call
- ✅ Provides 3 MCP tools
- ✅ Unified reporting includes complete Keepa indicators
