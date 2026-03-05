"""
Premium Actuary Report Generator
=================================
Based on premium-senior actuary report of design skill
Dark minimalist style, luxurious details, and data transparency
"""

import json
from datetime import datetime
from typing import Dict, List
from src.amazon_actuary_final import LinkPortfolioAnalysis, VariantAnalysisResult


class PremiumReportGenerator:
    """
    Senior Actuary Report Generator
    
    Features:
    - Dark minimalist style (Dark Minimalist)
    - Complete data transparency (Show raw Keepa data)
    - Sales calculation logic is clearly displayed
    - Interactive charts
    """
    
    def __init__(self):
        self.colors = {
            'bg_deep': '#0a0a0a',
            'bg_surface': '#141414',
            'bg_elevated': '#1a1a1a',
            'text_primary': '#ffffff',
            'text_secondary': 'rgba(255,255,255,0.5)',
            'text_tertiary': 'rgba(255,255,255,0.3)',
            'accent_green': '#a9dfbf',
            'accent_red': '#f5b7b7',
            'accent_yellow': '#f9e79f',
            'accent_blue': '#a9cce3',
            'border_subtle': 'rgba(255,255,255,0.03)',
            'border_medium': 'rgba(255,255,255,0.05)',
        }
    
    def generate(self, analysis: LinkPortfolioAnalysis, raw_products: List[Dict], 
                 output_path: str) -> str:
        """Generate advanced reports"""
        html = self._build_html(analysis, raw_products)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path
    
    def _build_html(self, analysis: LinkPortfolioAnalysis, raw_products: List[Dict]) -> str:
        """Build HTML"""
        
        # Calculate real vs estimated sales
        sales_calculation = self._analyze_sales_calculation(raw_products)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Actuary analysis report | {analysis.parent_asin}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        :root {{
            --bg-deep: {self.colors['bg_deep']};
            --bg-surface: {self.colors['bg_surface']};
            --bg-elevated: {self.colors['bg_elevated']};
            --text-primary: {self.colors['text_primary']};
            --text-secondary: {self.colors['text_secondary']};
            --text-tertiary: {self.colors['text_tertiary']};
            --accent-green: {self.colors['accent_green']};
            --accent-red: {self.colors['accent_red']};
            --accent-yellow: {self.colors['accent_yellow']};
            --accent-blue: {self.colors['accent_blue']};
            --border-subtle: {self.colors['border_subtle']};
            --border-medium: {self.colors['border_medium']};
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
            background: var(--bg-deep);
            color: var(--text-primary);
            font-weight: 300;
            line-height: 1.8;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 60px 40px;
        }}
        
        /* Header */
        .header {{
            text-align: center;
            padding: 80px 0;
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 80px;
        }}
        
        .header-label {{
            font-size: 0.7em;
            letter-spacing: 4px;
            text-transform: uppercase;
            color: var(--text-tertiary);
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 3em;
            font-weight: 200;
            letter-spacing: 8px;
            text-transform: uppercase;
            margin-bottom: 20px;
        }}
        
        .header-meta {{
            font-size: 0.9em;
            color: var(--text-secondary);
            letter-spacing: 2px;
        }}
        
        /* Verdict Section */
        .verdict-section {{
            text-align: center;
            padding: 100px 0;
            margin-bottom: 80px;
        }}
        
        .verdict-label {{
            font-size: 0.7em;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: var(--text-tertiary);
            margin-bottom: 40px;
        }}
        
        .verdict {{
            font-size: 4em;
            font-weight: 200;
            letter-spacing: 12px;
            text-transform: uppercase;
            margin-bottom: 30px;
        }}
        
        .verdict.proceed {{ color: var(--accent-green); }}
        .verdict.caution {{ color: var(--accent-yellow); }}
        .verdict.avoid {{ color: var(--accent-red); }}
        
        .verdict-confidence {{
            font-size: 1.2em;
            color: var(--text-secondary);
            letter-spacing: 2px;
        }}
        
        /* Cards */
        .card {{
            background: var(--bg-surface);
            padding: 50px;
            margin-bottom: 40px;
            border: 1px solid var(--border-subtle);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .card:hover {{
            border-color: var(--border-medium);
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 1px solid var(--border-subtle);
        }}
        
        .card-title {{
            font-size: 1.2em;
            font-weight: 200;
            letter-spacing: 3px;
            text-transform: uppercase;
        }}
        
        .card-subtitle {{
            font-size: 0.75em;
            color: var(--text-tertiary);
            letter-spacing: 1px;
        }}
        
        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 30px;
            margin-bottom: 60px;
        }}
        
        .metric-item {{
            text-align: center;
            padding: 40px 20px;
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
        }}
        
        .metric-value {{
            font-size: 2.5em;
            font-weight: 200;
            margin-bottom: 15px;
            letter-spacing: 2px;
        }}
        
        .metric-value.positive {{ color: var(--accent-green); }}
        .metric-value.negative {{ color: var(--accent-red); }}
        .metric-value.warning {{ color: var(--accent-yellow); }}
        
        .metric-label {{
            font-size: 0.7em;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--text-tertiary);
        }}
        
        /* Data Transparency Section */
        .data-source-section {{
            background: var(--bg-surface);
            padding: 50px;
            margin-bottom: 40px;
            border-left: 3px solid var(--accent-blue);
        }}
        
        .data-source-title {{
            font-size: 1em;
            font-weight: 200;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 30px;
            color: var(--accent-blue);
        }}
        
        .calculation-flow {{
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
            margin: 30px 0;
            padding: 30px;
            background: var(--bg-deep);
        }}
        
        .calc-step {{
            padding: 20px 30px;
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
        }}
        
        .calc-step-value {{
            font-size: 1.5em;
            font-weight: 300;
            margin-bottom: 5px;
        }}
        
        .calc-step-label {{
            font-size: 0.65em;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: var(--text-tertiary);
        }}
        
        .calc-arrow {{
            font-size: 1.5em;
            color: var(--text-tertiary);
        }}
        
        /* Variant Table */
        .variant-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 30px;
        }}
        
        .variant-table th {{
            text-align: left;
            padding: 20px;
            font-size: 0.7em;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--text-tertiary);
            font-weight: 400;
            border-bottom: 1px solid var(--border-medium);
        }}
        
        .variant-table td {{
            padding: 25px 20px;
            border-bottom: 1px solid var(--border-subtle);
            font-size: 0.9em;
        }}
        
        .variant-table tr:hover {{
            background: var(--bg-elevated);
        }}
        
        .variant-asin {{
            font-family: 'Monaco', monospace;
            font-size: 0.85em;
            color: var(--text-secondary);
        }}
        
        .variant-attributes {{
            font-size: 0.8em;
            color: var(--text-tertiary);
        }}
        
        .sales-breakdown {{
            font-size: 0.75em;
            color: var(--text-tertiary);
            margin-top: 5px;
        }}
        
        .data-source-tag {{
            display: inline-block;
            padding: 4px 10px;
            font-size: 0.65em;
            letter-spacing: 1px;
            text-transform: uppercase;
            background: var(--bg-deep);
            border: 1px solid var(--border-subtle);
            margin-right: 5px;
        }}
        
        .data-source-tag.real {{ color: var(--accent-green); border-color: var(--accent-green); }}
        .data-source-tag.estimated {{ color: var(--accent-yellow); border-color: var(--accent-yellow); }}
        .data-source-tag.allocated {{ color: var(--accent-blue); border-color: var(--accent-blue); }}
        
        /* Original Data Panel */
        .original-data-panel {{
            background: var(--bg-deep);
            padding: 30px;
            margin-top: 20px;
            border: 1px solid var(--border-subtle);
        }}
        
        .original-data-title {{
            font-size: 0.75em;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--text-tertiary);
            margin-bottom: 20px;
        }}
        
        .data-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }}
        
        .data-item {{
            padding: 15px;
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
        }}
        
        .data-item-label {{
            font-size: 0.65em;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: var(--text-tertiary);
            margin-bottom: 8px;
        }}
        
        .data-item-value {{
            font-size: 1.1em;
            font-weight: 300;
            font-family: 'Monaco', monospace;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 80px 0;
            border-top: 1px solid var(--border-subtle);
            margin-top: 80px;
        }}
        
        .footer-text {{
            font-size: 0.8em;
            color: var(--text-tertiary);
            letter-spacing: 1px;
        }}
        
        @media (max-width: 1200px) {{
            .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .data-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 30px 20px; }}
            .header h1 {{ font-size: 2em; }}
            .metrics-grid {{ grid-template-columns: 1fr; }}
            .data-grid {{ grid-template-columns: 1fr; }}
            .calculation-flow {{ flex-direction: column; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="header-label">Amazon FBA Actuary Report</div>
            <h1>Actuary analysis report</h1>
            <div class="header-meta">{analysis.parent_asin} · {datetime.now().strftime('%Y.%m.%d')}</div>
        </header>
        
        <!-- Verdict -->
        <section class="verdict-section">
            <div class="verdict-label">Investment Decision</div>
            <div class="verdict {analysis.overall_decision.decision}">
                {analysis.overall_decision.decision.upper()}
            </div>
            <div class="verdict-confidence">Confidence {analysis.overall_decision.confidence:.0f}%</div>
        </section>
        
        <!-- Key Metrics -->
        <div class="metrics-grid">
            <div class="metric-item">
                <div class="metric-value {"positive" if analysis.total_monthly_profit > 0 else "negative"}">${analysis.total_monthly_profit:,.0f}</div>
                <div class="metric-label">Monthly Profit</div>
            </div>
            <div class="metric-item">
                <div class="metric-value {"positive" if analysis.blended_portfolio_margin_pct > 15 else "warning"}">{analysis.blended_portfolio_margin_pct:.1f}%</div>
                <div class="metric-label">Margin</div>
            </div>
            <div class="metric-item">
                <div class="metric-value positive">{analysis.total_monthly_sales:,}</div>
                <div class="metric-label">Monthly Sales</div>
            </div>
            <div class="metric-item">
                <div class="metric-value {"positive" if analysis.overall_decision.expected_roi_pct > 50 else "warning"}">{analysis.overall_decision.expected_roi_pct:.1f}%</div>
                <div class="metric-label">ROI</div>
            </div>
        </div>
        
        <!-- Data Source Transparency -->
        <section class="data-source-section">
            <div class="data-source-title">Data Source & Calculation Logic</div>
            {self._render_sales_calculation(sales_calculation)}
        </section>
        
        <!-- Variants Detail -->
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="card-title">Variant Analysis</div>
                    <div class="card-subtitle">{len(analysis.variants)} variants with raw Keepa data</div>
                </div>
            </div>
            {self._render_variant_table(analysis, raw_products)}
        </div>
        
        <!-- Footer -->
        <footer class="footer">
            <div class="footer-text">
                Based on 163 Keepa metrics · Data-driven decision making<br>
                Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </footer>
    </div>
</body>
</html>'''
        return html
    
    def _analyze_sales_calculation(self, raw_products: List[Dict]) -> Dict:
        """Analyze sales calculation logic"""
        variants_data = []
        total_real_sales = 0
        total_estimated_sales = 0
        real_data_count = 0
        
        for p in raw_products:
            asin = p.get('asin', '')
            bought = p.get('boughtInPastMonth', 0)
            bsr = self._get_current_bsr(p)
            
            # Determine data source
            if isinstance(bought, (int, float)) and bought > 0:
                data_source = 'real'
                sales = int(bought)
                total_real_sales += sales
                real_data_count += 1
            else:
                data_source = 'estimated'
                sales = self._estimate_from_bsr(bsr)
                total_estimated_sales += sales
            
            variants_data.append({
                'asin': asin,
                'sales': sales,
                'data_source': data_source,
                'bsr': bsr,
                'raw_bought': bought,
            })
        
        # Check whether it is shared data
        is_shared = False
        if real_data_count == len(raw_products) and len(raw_products) > 1:
            sales_values = [v['sales'] for v in variants_data if v['data_source'] == 'real']
            if len(set(sales_values)) == 1:
                is_shared = True
                # Recalculate sales volume after distribution
                total_sales = sales_values[0]
                variants_data = self._allocate_sales(variants_data, total_sales)
        
        return {
            'variants': variants_data,
            'total_real_sales': total_real_sales,
            'total_estimated_sales': total_estimated_sales,
            'real_data_count': real_data_count,
            'is_shared_data': is_shared,
            'total_variants': len(raw_products),
        }
    
    def _allocate_sales(self, variants_data: List[Dict], total_sales: int) -> List[Dict]:
        """Prorate sales volume"""
        all_bsr = [v['bsr'] for v in variants_data]
        
        for v in variants_data:
            current_bsr = v['bsr']
            if current_bsr > 0 and sum(all_bsr) > 0:
                weights = [1 / (bsr ** 0.5) if bsr > 0 else 0 for bsr in all_bsr]
                current_weight = 1 / (current_bsr ** 0.5) if current_bsr > 0 else 0
                ratio = current_weight / sum(weights) if sum(weights) > 0 else 0
                v['allocated_sales'] = int(total_sales * ratio)
                v['allocation_ratio'] = ratio
                v['original_total'] = total_sales
            else:
                v['allocated_sales'] = 0
                v['allocation_ratio'] = 0
        
        return variants_data
    
    def _render_sales_calculation(self, calc: Dict) -> str:
        """Render sales calculation process"""
        if calc['is_shared_data']:
            return f'''
            <div class="calculation-flow">
                <div class="calc-step">
                    <div class="calc-step-value">{calc['variants'][0]['original_total']:,}</div>
                    <div class="calc-step-label">Keepa Raw Data (Parent ASIN)</div>
                </div>
                <div class="calc-arrow">→</div>
                <div class="calc-step">
                    <div class="calc-step-value">BSR Ratio</div>
                    <div class="calc-step-label">Weight = 1/√BSR</div>
                </div>
                <div class="calc-arrow">→</div>
                <div class="calc-step">
                    <div class="calc-step-value">{sum(v.get('allocated_sales', 0) for v in calc['variants']):,}</div>
                    <div class="calc-step-label">Allocated to {calc['total_variants']} variants</div>
                </div>
            </div>
            <p style="color: var(--text-tertiary); font-size: 0.85em; margin-top: 20px;">
                <span class="data-source-tag allocated">Allocated</span>
                Keepa provides parent ASIN total only. Sales distributed by BSR ranking.
            </p>
            '''
        else:
            return f'''
            <div class="calculation-flow">
                <div class="calc-step">
                    <div class="calc-step-value">{calc['real_data_count']}</div>
                    <div class="calc-step-label">Variants with Real Data</div>
                </div>
                <div class="calc-arrow">+</div>
                <div class="calc-step">
                    <div class="calc-step-value">{calc['total_variants'] - calc['real_data_count']}</div>
                    <div class="calc-step-label">Variants Estimated</div>
                </div>
                <div class="calc-arrow">=</div>
                <div class="calc-step">
                    <div class="calc-step-value">{calc['total_real_sales'] + calc['total_estimated_sales']:,}</div>
                    <div class="calc-step-label">Total Monthly Sales</div>
                </div>
            </div>
            <p style="color: var(--text-tertiary); font-size: 0.85em; margin-top: 20px;">
                <span class="data-source-tag real">Real</span> {calc['real_data_count']} variants with Keepa boughtInPastMonth
                <span class="data-source-tag estimated" style="margin-left: 10px;">Estimated</span> {calc['total_variants'] - calc['real_data_count']} variants from BSR
            </p>
            '''
    
    def _render_variant_table(self, analysis: LinkPortfolioAnalysis, raw_products: List[Dict]) -> str:
        """Render variant table"""
        rows = []
        
        for i, variant in enumerate(analysis.variants, 1):
            # Find the corresponding raw product
            raw = next((p for p in raw_products if p.get('asin') == variant.asin), {})
            bought_raw = raw.get('boughtInPastMonth', 'N/A')
            bsr = variant.metrics.sales_rank_current
            
            # Identify data source tags
            if bought_raw != 'N/A' and bought_raw > 0:
                if hasattr(variant, '_allocated') and variant._allocated:
                    source_tag = '<span class="data-source-tag allocated">Allocated</span>'
                else:
                    source_tag = '<span class="data-source-tag real">Real</span>'
            else:
                source_tag = '<span class="data-source-tag estimated">Estimated</span>'
            
            # Sales details
            sales_detail = f"BSR: {bsr:,}" if bought_raw == 'N/A' or bought_raw == 0 else f"Raw: {bought_raw}"
            
            rows.append(f'''
            <tr>
                <td>
                    <div class="variant-asin">{variant.asin}</div>
                    <div class="variant-attributes">{variant.metrics.color} · {variant.metrics.size}</div>
                </td>
                <td>${variant.metrics.price_new_current:.2f}</td>
                <td>
                    <strong>{variant.estimated_monthly_sales}</strong>
                    <div class="sales-breakdown">{sales_detail}</div>
                </td>
                <td>${variant.estimated_monthly_revenue:,.0f}</td>
                <td>${variant.monthly_total_profit:,.0f}</td>
                <td>{variant.blended_margin_pct:.1f}%</td>
                <td>{source_tag}</td>
            </tr>
            ''')
        
        return f'''
        <table class="variant-table">
            <thead>
                <tr>
                    <th>Variant</th>
                    <th>Price</th>
                    <th>Monthly Sales</th>
                    <th>Revenue</th>
                    <th>Profit</th>
                    <th>Margin</th>
                    <th>Data Source</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        
        <div class="original-data-panel">
            <div class="original-data-title">Raw Keepa Data Sample</div>
            <div class="data-grid">
                <div class="data-item">
                    <div class="data-item-label">Parent ASIN</div>
                    <div class="data-item-value">{analysis.parent_asin}</div>
                </div>
                <div class="data-item">
                    <div class="data-item-label">Total Variants</div>
                    <div class="data-item-value">{len(analysis.variants)}</div>
                </div>
                <div class="data-item">
                    <div class="data-item-label">Data Source</div>
                    <div class="data-item-value">Keepa API</div>
                </div>
            </div>
        </div>
        '''
    
    def _get_current_bsr(self, product: Dict) -> int:
        """Get the current BSR"""
        data = product.get('data', {})
        df = data.get('df_SALES')
        if df is not None and not df.empty:
            try:
                return int(df['value'].iloc[-1])
            except:
                pass
        return 999999
    
    def _estimate_from_bsr(self, bsr: int) -> int:
        """Estimating sales volume from BSR"""
        if bsr < 1000:
            return int(1500 * (1000 / bsr) ** 0.5)
        elif bsr < 10000:
            return int(800 * (10000 / bsr) ** 0.5)
        elif bsr < 50000:
            return int(300 * (50000 / bsr) ** 0.5)
        else:
            return int(100 * (100000 / bsr) ** 0.5)
