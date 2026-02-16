# CLEAR Architecture Prompts

This directory contains professional prompts for Amazon FBA product analysis using the CLEAR Architecture framework.

## Files

### 1. `clear_analyst_prompt.md`
**Purpose:** System prompt for LLM-based product analysis

**Content:**
- Role definition (Senior Amazon FBA Business Analyst)
- CLEAR Architecture framework (Context, Logic, Evidence, Analysis, Recommendation)
- MECE principle implementation
- Five logic chains (Profitability, Demand, Competition, Timing, Sustainability)
- Scoring weights and decision matrix
- Output format requirements
- Quality standards

**Usage:**
```python
# Load as system prompt for LLM
with open('prompts/clear_analyst_prompt.md', 'r') as f:
    system_prompt = f.read()

# Combine with product data
full_prompt = system_prompt + "\n\n" + product_data_prompt
```

## Integration with MCP Server

### Python Usage

```python
from src.clear_prompt_formatter import format_product_for_analysis
from src.data_processor import KeepaDataProcessor
import keepa

# Fetch product data
api = keepa.Keepa('your_api_key')
products = api.query(['B0XXXXXXX'], history=True)

# Process data
processor = KeepaDataProcessor()
data = processor.process_product(products[0], days=90)

# Generate analysis prompt
prompt = format_product_for_analysis(data)

# Send to LLM for analysis
response = llm.analyze(prompt)
```

### Output Files

The formatter generates:
1. **Markdown Prompt** (`*_analysis_prompt_*.md`) - Human-readable analysis request
2. **JSON Data** (`*_analysis_data_*.json`) - Structured data for programmatic use

## CLEAR Architecture Overview

```
C - Context (Background & Environment)
    └── Product Identity, Market Structure, Stakeholder Mapping

L - Logic (Framework & Reasoning)
    ├── Profitability Logic Chain
    ├── Demand Logic Chain
    ├── Competition Logic Chain
    ├── Timing Logic Chain
    └── Sustainability Logic Chain

E - Evidence (Data Support) [MECE Organized]
    ├── E1: Financial Metrics
    ├── E2: Demand Metrics
    ├── E3: Competition Metrics
    ├── E4: Operational Metrics
    └── E5: Brand Metrics

A - Analysis (Insights & Patterns)
    ├── Pattern Recognition
    ├── Risk-Opportunity Matrix
    └── Contradiction Detection

R - Recommendation (Action Plan)
    ├── Verdict (PROCEED/EVALUATE/MONITOR/PASS)
    ├── Scoring (0-100)
    ├── Action Items
    └── Success Metrics
```

## Scoring Framework

| Category | Weight | Criteria |
|----------|--------|----------|
| Profitability | 25% | Margin thresholds, pricing power |
| Market Demand | 20% | BSR, trend direction, velocity |
| Competition | 20% | Seller count, Amazon 1P, barriers |
| Brand Dominance | 15% | Brand control, monopoly status |
| Quality & Risk | 10% | Rating, return risk |
| Timing | 10% | Market cycle, seasonality |

### Decision Matrix

| Score | Verdict | Action |
|-------|---------|--------|
| 75-100 | **PROCEED** | Act within 2 weeks |
| 60-74 | **EVALUATE** | 30-day due diligence |
| 45-59 | **MONITOR** | Watch quarterly |
| 0-44 | **PASS** | Look for alternatives |

## Quality Standards

### MECE Verification
- ✅ No overlapping categories
- ✅ All metrics covered
- ✅ Each conclusion has ≥2 data points
- ✅ Alternative explanations considered
- ✅ Confidence levels justified

### Analysis Depth
- Quantitative over qualitative
- Contradictory signals acknowledged
- Data gaps explicitly stated
- Professional, analytical tone
