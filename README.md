# Amz-Keepa-MCP v3.0 🚀

DO NOT USE NOT PRODUCTION READY THIS FORK IS FOR TRANSLATION AND ANALYSIS PURPOSES
>
> 163 Keepa indicators + Real COGS + TACOS model = Professional-grade FBA profit analysis

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![MCP](https://img.shields.io/badge/MCP-1.26+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎯 Standard process (recommend)

**Generate a complete report in one sentence:**

```bash
python generate_report.py B0F6B5R47Q
```

this is**standard process**! The system will automatically:

```
┌─────────────────────────────────────────────────────────────────────┐
│ Standard process: Enter ASIN → Uniform Actuary Report (interactive+full analysis)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Step 1: Collect product data from Keepa API │
│ ✓ Automatically discover all variants │
│ ✓ Get 163 complete indicators │
│ ✓ Extract true dimensional weight │
│                                                                      │
│ Step 2: Withdraw real FBA fees and commissions │
│ ✓ Calculate FBA fees based on product size (2026 rates)                           │
│ ✓ Determine commission ratio based on category (8%-20%)                                  │
│ ✓ Automatically calculate volumetric weight vs actual weight │
│                                                                      │
│ Step 3: Generate unified actuarial report │
│ ✓ Interactive cost calculator (Fill in the 1688 purchase price and it will be calculated.)                        │
│ ✓ Pareto analysis (80/20 core variant identification)                                 │
│ ✓ Variation Profit Analysis Table │
│ ✓ Risk Assessment │
│ ✓ Investment advice and action plan │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Output file:**
- `cache/reports/{ASIN}_UNIFIED_ACTUARY.html` - Uniform Actuary Report (interactive + full analysis) ⭐

Report structure:
```
├─ Product information column
│ └─ Brand/Category/total sales/Total comments/average rating/Packaging specifications
│
├─ Interactive cost calculator
│ └─ Fill in the 1688 purchase price → automatically calculate COGS
│
├─ Summary indicator panel
│ └─ Total monthly profit/total sales/average profit margin/ROI
│
├─ Investment advice
│  └─ GO/cautious/avoid + confidence score
│
├─ Variant detailed analysis table (12 columns of complete indicators)
│  └─ ASIN/weight/price/monthly sales/BSR/score/Comment/return rate/FBA fee/Commission/COGS/profit
│
├─ Pareto analysis
│  └─ 80/20 core variant identification
│
├─ Risk Assessment
│ └─ Risk item list + Level
│
├─ Action Plan
│  └─ 30-60-90-day optimization suggestions
│
└─ Calculation formula reference
   └─ Complete financial model description
```

---

## ✨ Core Features

### 🧮 Operational Actuary Analysis (v3.0 final version)

The new actuary-level analysis system says goodbye to estimates and embraces real data:

| characteristic                         | Description                                     |
| ---------------------------- | ---------------------------------------- |
| **📊 Complete collection of 163 indicators** | Collect all fields in Keepa Product Viewer CSV format |
| **💰 Real COGS input**    | No cost estimate, user enters actual purchase+first leg+tariff   |
| **🎯 TACOS advertising model**   | Total ACOS = total advertising spend/Total sales, more accurate |
| **📈 Pareto analysis**      | 80/The Rule of 20 to identify core variants                    |
| **🤖 Data-driven decision-making**    | Based on multiple dimensions such as profit margin, rating, competition, return rate, etc. |
| **⚠️Risk quantification**      | confidence score(0-100%), VaR value at risk calculation      |

### 🆕 Based on Keepa real costs (2026-02 update)

```
✅ FBA fees - Calculated based on true dimensional weight (2026 rates)
✅ Commission ratio - Determine based on category (Electronics 8%, Clothing 17%Wait)
✅ Volume weight - Automatic calculation of actual weight vs volumetric weight
✅ Dimensional data - Get packageLength from Keepa API/Width/Height/Weight
```

### 🔍 Other analysis capabilities

- 🚀 **MCP native support** - Use directly in Claude Code `@amz-keepa` analysis
- 💬 **natural language interaction** - Use natural language to describe requirements and automatically generate reports
- 📄 **Professional HTML reporting** - Generate reports that can be displayed directly with one click
- 🧠 **Intelligent calibration system** - Learning bias from real sales data
- 🎯 **opportunity score** - Multidimensional scoring system (0-100)
- ⚠️ **Risk detection** - Automatically identify price wars, ranking decline, etc.
- 🌐 **Multisite support** - US, CN, JP, DE, UK et al20+site

---

## 🚀 Quick start

### Way 1: Claude Code + MCP (Recommended ⭐⭐⭐)

Use it directly in Claude Code:

```bash
# Enter the project directory
cd /Users/blobeats/Downloads/amz-keepa-mcp

# Start Claude Code
claude
```

Then in Claude's conversation use:

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

### Way 2: command line

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables
export KEEPA_KEY="your_keepa_api_key"

# Generate full report
python generate_report.py B0F6B5R47Q
```

Output:
```
✅ The unified actuary report is generated!

📊 Analysis summary:
   • Parent ASIN: B0F6B5R47Q
   • Number of variants: 9

📁 Generated reports:
   cache/reports/B0F6B5R47Q_UNIFIED_ACTUARY.html

📋 Report contains:
   ✅Interactive cost calculator (Fill in the 1688 purchase price and it will be calculated.)
   ✅ Pareto analysis (80/20 core variant identification)
   ✅ Variation profit analysis table
   ✅Risk assessment
   ✅ Investment advice and action plan
   ✅ Complete calculation formula reference

📝 Instructions for use:
   1. Open the report: open cache/reports/B0F6B5R47Q_UNIFIED_ACTUARY.html
   2. in'Procurement cost'Fill in the input box with the purchase price found from 1688
   3. The system automatically calculates complete profit analysis
   4. Scroll down for Pareto analysis, risk assessment, and more

💡 Tips:
   • You can adjust purchase prices in real time and view profits under different costs
   • All FBA fees are calculated based on Keepa true dimensional weight
   • Commission ratio is automatically determined based on category
```

### Way 2: MCP conversation method

After the configuration is completed, enter it directly in Claude:

```
Analysis ASIN B0F6B5R47Q
```

Claude will do it automatically**standard process**, generate a complete report.

### Way 3: Python code method

```python
from generate_report import generate_complete_report

results = generate_complete_report('B0F6B5R47Q', target_moq=100)

print(f"Report path: {results['unified_report']}")
print(f"Parent ASIN: {results['parent_asin']}")
print(f"Number of variants: {results['variants_count']}")
```

---

## 📖 User Guide

### Detailed explanation of standard procedures

#### Step 1: Collect Keepa data

The system automatically obtains from Keepa API:
- Basic product information (Title, brand, category)
- All variant ASINs
- Full size weight (packageLength/Width/Height/Weight)
- Price history, sales ranking
- Review data, return rate

#### Step 2: Calculate true costs

Automatic calculation based on Keepa data:

```python
# FBA fee calculation (2026 rates)
Billing weight = max(actual weight, Volume weight)
Volume weight = (Length×width×height) / 166  (inch³)

# Commission ratio (Based on category)
Electronics: 8%
Clothing: 17%
Jewelry: 20%
Others: 15%
```

#### Step 3: Generate unified actuary report

Generate a unified report (`{ASIN}_UNIFIED_ACTUARY.html`)：

**Report structure:**
```
├─ Interactive cost calculator
│ └─ Fill in the 1688 purchase price → automatically calculate the complete COGS
│
├─ Summary indicator panel
│ └─ Total monthly profit / total sales / average profit margin / ROI
│
├─ Investment advice
│  └─ GO / cautious / avoid + Confidence
│
├─ Pareto analysis
│  └─ 80/20 core variant identification
│
├─ Variation profit analysis table
│ └─ Detailed profit data for each variant
│
├─ Risk Assessment
│ └─ Risk item list + Level
│
├─ Action Plan
│  └─ 30-60-90-day optimization suggestions
│
└─ Calculation formula reference
   └─ Complete financial model description
```

#### Step 4: Enter purchase price (The only manual step required)

```
1. Open 1688.com
2. Use"Search for goods by picture"find product
3. Record the purchase price (Such as ¥35.50)
4. Fill in the interactive report
5. The system automatically calculates complete COGS and profit
```

### Complete financial model

```
selling price (Amazon)
  - COGS (Procurement+first leg+tariff)
  - FBA fees (Based on dimensional weight)
  - Commission (Based on category)
  - return cost
  - Storage fee
  - TACOS advertising fee (15%)
  ─────────────────
  = net profit
```

---

## 📊 Report Example

### Interactive reporting interface

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔧 Cost Calculator │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│ │ Procurement Cost │ │
│  │                                                             │   │
│ │ ¥35.50 ← Fill in the purchase price found from 1688 │ │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│ Cost structure:                                                          │
│ Procurement cost: ¥35.50 + First leg freight: ¥5.40 × Tariff 1.15 ÷ Exchange rate 7.2 │
│  = Total COGS: $6.54 USD                                               │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ 📊 Fee details (Based on Keepa real data)                                     │
├─────────────────────────────────────────────────────────────────────┤
│ FBA fees:    $3.86  (Calculated based on 450g weight)                             │
│ Commission:       $3.68  (Electronics Category 8%)                           │
│ Return costs:   $0.69  (5%return rate)                                     │
│ Storage fee:     $0.06                                                 │
│  TACOS:      $6.90  (Advertising fee 15%)                                    │
│  ─────────────────                                                 │
│ Total cost:     $15.19                                                │
├─────────────────────────────────────────────────────────────────────┤
│ 📈 Profit Analysis │
├─────────────────────────────────────────────────────────────────────┤
│ Selling price:        $45.99                                               │
│ Less COGS:     $6.54                                                │
│ Less fees:     $15.19                                               │
│  ─────────────────                                                 │
│Profit per unit:    $24.26  (Profit margin 52.8%)                               │
│Monthly Sales:      800 pieces │
│Monthly profit:      $19,408                                              │
│                                                                     │
│ 🎯 Investment Advice: Recommended investment (Confidence 85%)                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ❓ FAQ

### Q: Why you only need to enter the ASIN to generate a full report?

**A:** The system will automatically:
1. Get product data from Keepa API (Size, weight, price, etc.)
2. Automatically discover all variants
3. Calculate FBA fees based on real dimensions
4. Determine commission ratio based on category
5. Generate a complete report containing 163 indicators

**The only thing that requires manual**: Fill in the purchase price found from 1688 (Because manual confirmation of suppliers is required)

### Q: Are FBA fees accurate??

**A:** Yes, based on:
- Product dimensions and weight provided by Keepa API
- The latest FBA rate schedule in 2026
- Automatic calculation of dimensional weight vs actual weight

### Q: How is the commission ratio determined??

**A:** Based on category information provided by Keepa API:

| Category | Commission |
|------|------|
| Electronics | 8% |
| Clothing | 17% |
| Jewelry | 20% |
| Others | 15% |

### Q: How to get the 1688 purchase price?

**A:** 
1. Open https://www.1688.com
2. Click on the right side of the search box"camera"icon (Search for goods by picture)
3. Paste Amazon product pictures
4. Find similar products and record the price

### Q: What is TACOS?

**A:** TACOS (Total ACOS) = total advertising spend / total sales

- Better than ACOS to reflect the impact of advertising on the overall business
- Default assumption 15%, can be adjusted according to actual

---

## 🏗️ System architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Amazon Operations Actuary System v3.0 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐  │
│ │ User Input │───▶│ Standard Process Engine │───▶│ Keepa API │ │
│  │  ASIN          │    │  (generate_)     │    │  (True size weight)      │  │
│  └─────────────────┘    └──────────────────┘    └─────────────────────┘  │
│                                │                                        │
│                                ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│ │ Cost Calculation Engine │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│ │ │ FBA fees │ │ Commission calculation │ │ Volumetric weight │ │ │
│  │  │ (2026 rates)  │  │ (Based on category)  │  │ (vs actual)    │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│                                ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│ │ Report generation layer │ │
│  │  ┌─────────────────┐    ┌─────────────────┐                     │   │
│ │ │ Actuary Report │ │ Interactive Report │ │ │
│  │  │ (163 indicators)       │    │ (Fill in COGS)      │                     │   │
│  │  └─────────────────┘    └─────────────────┘                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd amz-keepa-mcp
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# .env file
KEEPA_KEY=your_keepa_api_key_here
TMAPI_TOKEN=your_tmapi_token_here  # Optional, for automatic 1688 purchase price
```

---

## 🔧 MCP configuration

### Claude Desktop Configuration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "amz-keepa": {
      "command": "/path/to/amz-keepa-mcp/venv/bin/python",
      "args": [
        "/path/to/amz-keepa-mcp/server.py"
      ],
      "env": {
        "KEEPA_KEY": "your_api_key"
      }
    }
  }
}
```

---

## 📁 Project structure

```
amz-keepa-mcp/
├── generate_report.py ⭐ Standard process entry (recommend)
├── src/
│   ├── amazon_actuary_final.py      # actuary system
│   ├── keepa_metrics_collector.py   # 163 indicator collection
│   ├── keepa_fee_extractor.py       # True fee withdrawal (NEW)
│   ├── allinone_interactive_report.py # Interactive reporting
│   └── ...
├── cache/
│   └── reports/                     # generated report
├── README.md                        # this document
└── requirements.txt
```

---

## ⚠️ Disclaimer

This system analyzes based on Keepa API historical data. All predictions and recommendations are for reference only:

- 📈 Market fluctuations may cause actual results to differ from forecasts
- 💰 Profit calculation is based on COGS data provided by users, please ensure the data is accurate
- ⚡ Amazon algorithm changes may affect rankings and sales
- 📊 It is recommended to conduct multi-channel verification before making major investment decisions

---

## 📄 License

MIT License - See LICENSE file for details

---

**last updated**: 2026-02-16 | **version**: v3.0 | **standard process**: `python generate_report.py <ASIN>`
