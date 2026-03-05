"""
Unified Actuarial Report Generator v2
======================
Contains complete Keepa indicators and actuarial analysis dimensions
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict


class UnifiedActuaryReportV2:
    """
    Unified Actuarial Report v2 - Contains full Keepa indicators
    
    Report structure:
    1. Interactive cost calculator
    2. Executive summary (core indicators)
    3. Pareto analysis (80/20)
    4. Complete variant analysis table (Includes all Keepa indicators)
    5. Risk assessment
    6. Investment advice
    7. Action Plan
    """
    
    def __init__(self):
        self.shipping_rate = 12
        self.tariff_rate = 0.15
        self.exchange_rate = 7.2
        
    def generate(self, asin: str, products: List[Dict], 
                 analysis_data: Dict, output_path: str = None) -> str:
        """Generate unified reports"""
        
        if output_path is None:
            output_path = f'cache/reports/{asin}_UNIFIED_ACTUARY.html'
        
        # Prepare complete data
        variants = self._prepare_full_variants(products)
        metrics_163 = self._collect_163_metrics(products)
        parent_info = analysis_data.get('parent_info', {})
        
        # Generate HTML
        html = self._build_html(asin, variants, metrics_163, parent_info, analysis_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def _prepare_full_variants(self, products: List[Dict]) -> List[Dict]:
        """Prepare complete variant data including all Keepa metrics"""
        variants = []
        
        for product in products:
            asin = product.get('asin', '')
            
            # Basic information
            weight_g = product.get('packageWeight', 0) or product.get('itemWeight', 0) or 300
            
            # price
            stats = product.get('stats', {})
            price = stats.get('buyBoxPrice', 2999) / 100 if stats and 'buyBoxPrice' in stats else 29.99
            
            # Sales volume
            bought = product.get('boughtInPastMonth', 0)
            sales = bought[1] if isinstance(bought, list) and len(bought) > 1 else (bought if isinstance(bought, (int, float)) else 500)
            
            # BSR
            bsr_data = product.get('salesRank', [0, 999999])
            bsr = bsr_data[1] if isinstance(bsr_data, list) and len(bsr_data) > 1 else bsr_data
            
            # Comment
            reviews = product.get('reviews', [])
            review_count = len(reviews) if isinstance(reviews, list) else product.get('reviewCount', 0)
            rating = product.get('stars', 0) or product.get('rating', 0)
            
            # Properties
            attrs = product.get('attributes', [])
            color = self._get_attr(attrs, 'Color') or 'Default'
            size = self._get_attr(attrs, 'Size') or 'standard'
            
            # Return rate estimate
            return_rate = self._estimate_return_rate(product)
            
            # cost
            from keepa_fee_extractor import KeepaFeeExtractor
            fees = KeepaFeeExtractor.extract_all_fees(product, price)
            
            variants.append({
                'asin': asin,
                'color': color,
                'size': size,
                'weight_kg': round(weight_g / 1000, 3),
                'weight_g': weight_g,
                'price': round(price, 2),
                'sales': sales,
                'bsr': bsr,
                'review_count': review_count,
                'rating': round(rating, 1) if rating else 0,
                'return_rate': return_rate,
                'fba_fee': fees['fba_fee'],
                'referral_rate': fees['referral_rate'],
                'referral_fee': fees['referral_fee'],
            })
        
        return variants
    
    def _collect_163_metrics(self, products: List[Dict]) -> Dict:
        """Collect 163 indicator summaries"""
        if not products:
            return {}
        
        product = products[0]
        
        return {
            'title': product.get('title', ''),
            'brand': product.get('brand', ''),
            'category': self._get_category(product),
            'package': {
                'length': product.get('packageLength', 0),
                'width': product.get('packageWidth', 0),
                'height': product.get('packageHeight', 0),
                'weight': product.get('packageWeight', 0),
            },
            'tracking_since': product.get('trackingSince', 0),
            'listed_since': product.get('listedSince', 0),
        }
    
    def _get_category(self, product: Dict) -> str:
        """Get category"""
        tree = product.get('categoryTree', [])
        if tree:
            return ' > '.join([c.get('name', '') for c in tree[:3]])
        return product.get('rootCategory', '')
    
    def _get_attr(self, attrs: List, name: str) -> str:
        """Get properties"""
        for attr in attrs:
            if isinstance(attr, dict) and attr.get('name') == name:
                return attr.get('value', '')
        return ''
    
    def _estimate_return_rate(self, product: Dict) -> float:
        """Estimated return rate"""
        category = self._get_category(product).lower()
        if 'clothing' in category or 'shoes' in category:
            return 0.12
        elif 'electronics' in category:
            return 0.08
        elif 'jewelry' in category:
            return 0.05
        return 0.10
    
    def _build_html(self, asin: str, variants: List[Dict], 
                    metrics_163: Dict, parent_info: Dict, analysis_data: Dict) -> str:
        """Build a full HTML report"""
        
        variants_json = json.dumps(variants, ensure_ascii=False)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Aggregate data
        total_sales = sum(v['sales'] for v in variants)
        avg_price = sum(v['price'] for v in variants) / len(variants) if variants else 30
        total_reviews = sum(v['review_count'] for v in variants)
        avg_rating = sum(v['rating'] for v in variants) / len(variants) if variants else 0
        
        # Pareto analysis
        pareto_data = self._calculate_pareto(variants)
        
        # risk assessment
        risks = self._assess_risks(variants, metrics_163)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Uniform Actuary Analysis Report | {asin}</title>
    <style>
        :root {{
            --bg: #0a0a0a;
            --surface: #141414;
            --elevated: #1a1a1a;
            --text: #ffffff;
            --text-secondary: rgba(255,255,255,0.7);
            --text-muted: rgba(255,255,255,0.5);
            --green: #22c55e;
            --red: #ef4444;
            --yellow: #f59e0b;
            --blue: #3b82f6;
            --purple: #8b5cf6;
            --cyan: #06b6d4;
            --border: rgba(255,255,255,0.08);
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px; }}
        
        /* Header */
        .header {{
            text-align: center;
            padding: 50px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 50px;
        }}
        .header h1 {{
            font-size: 2.2em;
            font-weight: 300;
            letter-spacing: 6px;
            margin-bottom: 15px;
            background: linear-gradient(90deg, #fff, rgba(255,255,255,0.7));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header .subtitle {{ color: var(--text-muted); letter-spacing: 2px; }}
        .header .meta {{ margin-top: 20px; font-family: monospace; color: var(--blue); font-size: 0.85em; }}
        
        /* Sections */
        .section {{
            background: linear-gradient(135deg, var(--surface) 0%, var(--elevated) 100%);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 40px;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }}
        .section-header .icon {{ font-size: 1.5em; }}
        .section-header h2 {{
            font-size: 1.3em;
            font-weight: 500;
            color: var(--blue);
            letter-spacing: 1px;
        }}
        
        /* Calculator */
        .calculator-section {{ border-color: var(--blue); position: relative; overflow: hidden; }}
        .calculator-section::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--blue), var(--purple));
        }}
        
        .main-input {{
            background: var(--bg);
            border: 2px solid var(--border);
            border-radius: 16px;
            padding: 35px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .main-input:focus-within {{ border-color: var(--blue); box-shadow: 0 0 0 4px rgba(59,130,246,0.1); }}
        .main-input label {{
            display: block;
            font-size: 0.85em;
            color: var(--text-muted);
            margin-bottom: 15px;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}
        
        .input-large {{
            width: 100%;
            background: transparent;
            border: none;
            font-size: 4em;
            font-weight: 200;
            color: var(--blue);
            text-align: center;
            font-family: 'Monaco', monospace;
        }}
        .input-large:focus {{ outline: none; }}
        .input-large::placeholder {{ color: rgba(59,130,246,0.3); }}
        
        .settings-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .setting-box {{
            background: var(--bg);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
        }}
        .setting-box label {{
            display: block;
            font-size: 0.75em;
            color: var(--text-muted);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .setting-box input {{
            width: 100%;
            background: transparent;
            border: none;
            font-size: 1.4em;
            color: var(--text);
            font-family: 'Monaco', monospace;
        }}
        .setting-box input:focus {{ outline: none; }}
        
        /* Cost Flow */
        .cost-flow {{
            background: var(--bg);
            border-radius: 16px;
            padding: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .flow-item {{
            background: var(--surface);
            border-radius: 12px;
            padding: 20px 25px;
            text-align: center;
            min-width: 140px;
        }}
        .flow-item.highlight {{
            background: linear-gradient(135deg, rgba(34,197,94,0.15), rgba(34,197,94,0.05));
            border: 1px solid rgba(34,197,94,0.3);
        }}
        .flow-item label {{
            display: block;
            font-size: 0.7em;
            color: var(--text-muted);
            margin-bottom: 8px;
            text-transform: uppercase;
        }}
        .flow-item .value {{
            font-size: 1.5em;
            font-family: 'Monaco', monospace;
            color: var(--text-secondary);
        }}
        .flow-item.highlight .value {{ color: var(--green); }}
        
        .flow-op {{
            background: var(--elevated);
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
        }}
        
        /* Dashboard */
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: var(--bg);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            border: 1px solid var(--border);
        }}
        .metric-card.highlight {{
            background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(34,197,94,0.02));
            border-color: rgba(34,197,94,0.3);
        }}
        .metric-card label {{
            display: block;
            font-size: 0.75em;
            color: var(--text-muted);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-card .value {{
            font-size: 2em;
            font-weight: 300;
            font-family: 'Monaco', monospace;
        }}
        .metric-card.highlight .value {{ color: var(--green); }}
        
        /* Tables */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--bg);
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 30px;
        }}
        .data-table th {{
            background: var(--elevated);
            padding: 15px 12px;
            text-align: left;
            font-size: 0.75em;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }}
        .data-table td {{
            padding: 15px 12px;
            border-bottom: 1px solid var(--border);
            font-size: 0.9em;
        }}
        .data-table tr:last-child td {{ border-bottom: none; }}
        .data-table tr:hover {{ background: rgba(255,255,255,0.02); }}
        
        .cell-value {{ font-family: 'Monaco', monospace; }}
        .cell-value.positive {{ color: var(--green); }}
        .cell-value.negative {{ color: var(--red); }}
        
        /* Product Info */
        .product-info {{
            background: var(--bg);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}
        .info-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
        }}
        .info-item:last-child {{ border-bottom: none; }}
        .info-label {{ color: var(--text-muted); font-size: 0.9em; }}
        .info-value {{ font-family: 'Monaco', monospace; font-weight: 500; }}
        
        /* Verdict */
        .verdict-section {{
            text-align: center;
            padding: 50px;
            border-radius: 20px;
            border: 2px solid var(--border);
            margin-bottom: 40px;
        }}
        .verdict-section.proceed {{ border-color: var(--green); background: linear-gradient(135deg, rgba(34,197,94,0.05), transparent); }}
        .verdict-section.caution {{ border-color: var(--yellow); background: linear-gradient(135deg, rgba(245,158,11,0.05), transparent); }}
        .verdict-section.avoid {{ border-color: var(--red); background: linear-gradient(135deg, rgba(239,68,68,0.05), transparent); }}
        
        .verdict-label {{
            font-size: 0.9em;
            color: var(--text-muted);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 20px;
        }}
        .verdict-value {{
            font-size: 3em;
            font-weight: 200;
            letter-spacing: 8px;
            margin-bottom: 15px;
        }}
        .verdict-value.proceed {{ color: var(--green); }}
        .verdict-value.caution {{ color: var(--yellow); }}
        .verdict-value.avoid {{ color: var(--red); }}
        
        /* Risk & Action */
        .item-list {{ display: grid; gap: 15px; }}
        .item {{
            background: var(--bg);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid var(--border);
            display: flex;
            gap: 15px;
        }}
        .item.high {{ border-left-color: var(--red); }}
        .item.medium {{ border-left-color: var(--yellow); }}
        .item.low {{ border-left-color: var(--blue); }}
        .item-icon {{ font-size: 1.5em; }}
        .item-content {{ flex: 1; }}
        .item-title {{ font-weight: 500; margin-bottom: 5px; }}
        .item-desc {{ font-size: 0.85em; color: var(--text-muted); }}
        
        /* Pareto */
        .pareto-bar {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        .pareto-label {{ width: 100px; font-size: 0.85em; color: var(--text-secondary); }}
        .pareto-track {{
            flex: 1;
            height: 25px;
            background: var(--bg);
            border-radius: 6px;
            overflow: hidden;
            margin: 0 15px;
        }}
        .pareto-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--blue), var(--purple));
            border-radius: 6px;
        }}
        .pareto-fill.core {{ background: linear-gradient(90deg, var(--green), var(--cyan)); }}
        .pareto-value {{ width: 60px; text-align: right; font-family: monospace; }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .input-large {{ font-size: 2.5em; }}
            .data-table {{ font-size: 0.8em; }}
            .data-table th, .data-table td {{ padding: 10px 6px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>Uniform Actuary Analysis Report</h1>
            <div class="subtitle">All-in-One Interactive Analysis · Based on Keepa real data</div>
            <div class="meta">
                ASIN: {asin} | 
                brand: {metrics_163.get('brand', 'N/A')} | 
                Category: {metrics_163.get('category', 'N/A')} | 
                Generation time: {timestamp}
            </div>
        </header>
        
        <!-- Section 1: Product Info -->
        <div class="section">
            <div class="section-header">
                <span class="icon">📦</span>
                <h2>product information</h2>
            </div>
            <div class="product-info">
                <div style="font-size: 1.1em; margin-bottom: 20px; line-height: 1.8;">
                    {metrics_163.get('title', 'Product Title')}
                </div>
                <div class="info-grid">
                    <div>
                        <div class="info-item">
                            <span class="info-label">Total number of variants</span>
                            <span class="info-value">{len(variants)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Average monthly total sales</span>
                            <span class="info-value">{total_sales:,}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Total comments</span>
                            <span class="info-value">{total_reviews:,}</span>
                        </div>
                    </div>
                    <div>
                        <div class="info-item">
                            <span class="info-label">average selling price</span>
                            <span class="info-value">${avg_price:.2f}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">average rating</span>
                            <span class="info-value">{avg_rating:.1f} ⭐</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Packing weight</span>
                            <span class="info-value">{metrics_163.get('package', {}).get('weight', 0)}g</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Section 2: Calculator -->
        <div class="section calculator-section">
            <div class="section-header">
                <span class="icon">🔧</span>
                <h2>Cost Calculator · Fill in the 1688 purchase price</h2>
            </div>
            
            <div class="main-input">
                <label>Procurement cost (RMB)</label>
                <input type="number" class="input-large" id="procurementCost" 
                       placeholder="0" oninput="calculateAll()">
            </div>
            
            <div class="settings-grid">
                <div class="setting-box">
                    <label>shipping price</label>
                    <input type="number" id="shippingRate" value="{self.shipping_rate}" oninput="calculateAll()">
                </div>
                <div class="setting-box">
                    <label>tariff rate</label>
                    <div style="font-size: 1.4em; color: var(--text-secondary); font-family: monospace;">15%</div>
                </div>
                <div class="setting-box">
                    <label>exchange rate</label>
                    <input type="number" id="exchangeRate" value="{self.exchange_rate}" step="0.1" oninput="calculateAll()">
                </div>
                <div class="setting-box">
                    <label>TACOS</label>
                    <div style="font-size: 1.4em; color: var(--text-secondary); font-family: monospace;">15%</div>
                </div>
            </div>
            
            <div class="cost-flow">
                <div class="flow-item">
                    <label>Procurement cost</label>
                    <div class="value" id="costProcurement">-</div>
                </div>
                <div class="flow-op">+</div>
                <div class="flow-item">
                    <label>First leg freight</label>
                    <div class="value" id="costShipping">-</div>
                </div>
                <div class="flow-op">×</div>
                <div class="flow-item">
                    <label>Tariff 15%</label>
                    <div class="value">1.15</div>
                </div>
                <div class="flow-op">÷</div>
                <div class="flow-item">
                    <label>exchange rate</label>
                    <div class="value" id="costExchange">7.2</div>
                </div>
                <div class="flow-item highlight">
                    <label>Total COGS</label>
                    <div class="value" id="costTotal">-</div>
                </div>
            </div>
        </div>
        
        <!-- Section 3: Dashboard -->
        <div class="dashboard-grid" id="dashboardSection" style="display: none;">
            <div class="metric-card highlight">
                <label>Total monthly profit</label>
                <div class="value" id="totalProfit">$0</div>
            </div>
            <div class="metric-card">
                <label>Total monthly sales</label>
                <div class="value" id="totalSales">0</div>
            </div>
            <div class="metric-card">
                <label>average profit margin</label>
                <div class="value" id="avgMargin">0%</div>
            </div>
            <div class="metric-card">
                <label>average ROI</label>
                <div class="value" id="roiEstimate">0%</div>
            </div>
        </div>
        
        <!-- Section 4: Verdict -->
        <div class="verdict-section" id="verdictSection" style="display: none;">
            <div class="verdict-label">investment advice</div>
            <div class="verdict-value" id="verdictValue">-</div>
            <div style="color: var(--text-muted);" id="verdictConfidence">-</div>
        </div>
        
        <!-- Section 5: Variant Analysis -->
        <div class="section">
            <div class="section-header">
                <span class="icon">📊</span>
                <h2>Detailed analysis of variants · Complete Keepa metrics</h2>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Variants</th>
                        <th>weight</th>
                        <th>price</th>
                        <th>monthly sales</th>
                        <th>BSR</th>
                        <th>score</th>
                        <th>Comment</th>
                        <th>return rate</th>
                        <th>FBA fee</th>
                        <th>Commission</th>
                        <th>COGS</th>
                        <th>profit</th>
                    </tr>
                </thead>
                <tbody id="variantsTableBody">
                    {self._generate_variant_rows(variants)}
                </tbody>
            </table>
        </div>
        
        <!-- Section 6: Pareto -->
        <div class="section">
            <div class="section-header">
                <span class="icon">📈</span>
                <h2>Pareto Analysis · 80/20 core variants</h2>
            </div>
            <div style="margin-bottom: 20px; color: var(--text-muted);">
                Recognize contribution 80%core variant of sales volume (green mark)
            </div>
            {self._generate_pareto_bars(variants)}
        </div>
        
        <!-- Section 7: Risks -->
        <div class="section">
            <div class="section-header">
                <span class="icon">⚠️</span>
                <h2>risk assessment</h2>
            </div>
            <div class="item-list">
                {self._generate_risk_items(risks)}
            </div>
        </div>
        
        <!-- Section 8: Actions -->
        <div class="section">
            <div class="section-header">
                <span class="icon">🎯</span>
                <h2>action plan</h2>
            </div>
            <div class="item-list">
                {self._generate_action_items(variants)}
            </div>
        </div>
    </div>
    
    <script>
        const variantsData = {variants_json};
        
        function calculateAll() {{
            const procurementRMB = parseFloat(document.getElementById('procurementCost').value) || 0;
            const shippingRate = parseFloat(document.getElementById('shippingRate').value) || 12;
            const exchangeRate = parseFloat(document.getElementById('exchangeRate').value) || 7.2;
            
            document.getElementById('costProcurement').textContent = procurementRMB > 0 ? '¥' + procurementRMB.toFixed(2) : '-';
            document.getElementById('costExchange').textContent = exchangeRate.toFixed(1);
            
            const rows = document.querySelectorAll('#variantsTableBody tr');
            let totalProfit = 0;
            let totalSales = 0;
            let totalRevenue = 0;
            
            rows.forEach((row, index) => {{
                const v = variantsData[index];
                const weightKg = v.weight_kg;
                const price = v.price;
                const sales = v.sales;
                
                const shippingRMB = procurementRMB > 0 ? weightKg * shippingRate : 0;
                
                let cogsUSD = 0;
                if (procurementRMB > 0) {{
                    const subtotalRMB = procurementRMB + shippingRMB;
                    const totalRMB = subtotalRMB * 1.15;
                    cogsUSD = totalRMB / exchangeRate;
                }}
                
                const fbaFee = v.fba_fee;
                const referralFee = price * v.referral_rate;
                const returnCost = price * v.return_rate * 0.3;
                const storageFee = 0.06;
                const tacosCost = price * 0.15;
                
                const totalCost = cogsUSD + fbaFee + referralFee + returnCost + storageFee + tacosCost;
                const profit = price - totalCost;
                const monthlyProfit = profit * sales;
                
                totalProfit += monthlyProfit;
                totalSales += sales;
                totalRevenue += price * sales;
                
                const cells = row.querySelectorAll('td');
                if (cells.length >= 12) {{
                    if (procurementRMB > 0) {{
                        cells[10].textContent = '$' + cogsUSD.toFixed(2);
                        cells[11].textContent = '$' + profit.toFixed(2);
                        cells[11].className = 'cell-value ' + (profit > 0 ? 'positive' : 'negative');
                    }} else {{
                        cells[10].textContent = '-';
                        cells[11].textContent = '-';
                        cells[11].className = 'cell-value';
                    }}
                }}
            }});
            
            if (procurementRMB > 0) {{
                document.getElementById('dashboardSection').style.display = 'grid';
                document.getElementById('verdictSection').style.display = 'block';
                
                document.getElementById('totalProfit').textContent = '$' + totalProfit.toFixed(0);
                document.getElementById('totalSales').textContent = totalSales.toLocaleString();
                
                const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
                document.getElementById('avgMargin').textContent = avgMargin.toFixed(1) + '%';
                
                const monthlyCogs = procurementRMB * totalSales / exchangeRate;
                const roi = monthlyCogs > 0 ? (totalProfit / monthlyCogs) * 100 : 0;
                document.getElementById('roiEstimate').textContent = roi.toFixed(0) + '%';
                
                const avgWeight = variantsData.reduce((a, v) => a + v.weight_kg, 0) / variantsData.length;
                const shippingRMB = avgWeight * shippingRate;
                const totalRMB = (procurementRMB + shippingRMB) * 1.15;
                const cogsUSD = totalRMB / exchangeRate;
                document.getElementById('costShipping').textContent = '¥' + shippingRMB.toFixed(0);
                document.getElementById('costTotal').textContent = '$' + cogsUSD.toFixed(2);
                
                updateVerdict(avgMargin, roi);
            }} else {{
                document.getElementById('dashboardSection').style.display = 'none';
                document.getElementById('verdictSection').style.display = 'none';
                document.getElementById('costShipping').textContent = '-';
                document.getElementById('costTotal').textContent = '-';
            }}
        }}
        
        function updateVerdict(margin, roi) {{
            const verdictEl = document.getElementById('verdictValue');
            const confidenceEl = document.getElementById('verdictConfidence');
            const sectionEl = document.getElementById('verdictSection');
            
            let verdict = 'avoid', text = 'Recommended to avoid', confidence = 60;
            
            if (margin > 15 && roi > 50) {{
                verdict = 'proceed';
                text = 'Recommended investment';
                confidence = 85;
            }} else if (margin > 10 && roi > 20) {{
                verdict = 'caution';
                text = 'Consider carefully';
                confidence = 70;
            }}
            
            verdictEl.textContent = text;
            verdictEl.className = 'verdict-value ' + verdict;
            sectionEl.className = 'verdict-section ' + verdict;
            confidenceEl.textContent = 'Confidence ' + confidence + '%';
        }}
        
        calculateAll();
    </script>
</body>
</html>'''
        
        return html
    
    def _generate_variant_rows(self, variants: List[Dict]) -> str:
        """Generate variant table rows"""
        rows = []
        for v in variants:
            rows.append(f'''
                <tr>
                    <td>
                        <div style="font-weight: 500;">{v['color']} - {v['size']}</div>
                        <div style="font-size: 0.75em; color: var(--text-muted); font-family: monospace;">{v['asin']}</div>
                    </td>
                    <td><span style="background: rgba(139,92,246,0.15); color: var(--purple); padding: 4px 10px; border-radius: 12px; font-size: 0.8em; font-family: monospace;">{v['weight_g']}g</span></td>
                    <td style="font-weight: 500; color: var(--blue); font-family: monospace;">${v['price']:.2f}</td>
                    <td class="cell-value">{v['sales']:,}</td>
                    <td class="cell-value">{v['bsr']:,}</td>
                    <td class="cell-value">{v['rating']:.1f}⭐</td>
                    <td class="cell-value">{v['review_count']:,}</td>
                    <td class="cell-value">{v['return_rate']*100:.0f}%</td>
                    <td class="cell-value">${v['fba_fee']:.2f}</td>
                    <td class="cell-value">{v['referral_rate']*100:.0f}%</td>
                    <td class="cell-value">-</td>
                    <td class="cell-value">-</td>
                </tr>
            ''')
        return '\n'.join(rows)
    
    def _calculate_pareto(self, variants: List[Dict]) -> List[Dict]:
        """Calculate Pareto data"""
        sorted_variants = sorted(variants, key=lambda x: x['sales'], reverse=True)
        total_sales = sum(v['sales'] for v in variants)
        
        pareto_data = []
        cumulative = 0
        for v in sorted_variants[:5]:
            cumulative += v['sales']
            percentage = (v['sales'] / total_sales * 100) if total_sales > 0 else 0
            cumulative_pct = (cumulative / total_sales * 100) if total_sales > 0 else 0
            
            pareto_data.append({
                'name': f"{v['color']}",
                'percentage': percentage,
                'cumulative': cumulative_pct,
                'is_core': cumulative_pct <= 80
            })
        
        return pareto_data
    
    def _generate_pareto_bars(self, variants: List[Dict]) -> str:
        """Generate Pareto chart"""
        pareto_data = self._calculate_pareto(variants)
        bars = []
        for item in pareto_data:
            width = item['percentage']
            bars.append(f'''
                <div class="pareto-bar">
                    <div class="pareto-label">{item['name']}</div>
                    <div class="pareto-track">
                        <div class="pareto-fill {'core' if item['is_core'] else ''}" style="width: {width}%"></div>
                    </div>
                    <div class="pareto-value">{width:.1f}%</div>
                </div>
            ''')
        return '\n'.join(bars)
    
    def _assess_risks(self, variants: List[Dict], metrics_163: Dict) -> List[Dict]:
        """Assess risks"""
        risks = []
        
        # Check number of variants
        if len(variants) > 10:
            risks.append({
                'level': 'medium',
                'title': 'Too many variants',
                'desc': f'total{len(variants)}variants, increasing the complexity of inventory management',
                'icon': '⚠️'
            })
        
        # Check rating
        avg_rating = sum(v['rating'] for v in variants) / len(variants) if variants else 0
        if avg_rating < 4.0:
            risks.append({
                'level': 'high',
                'title': 'Low rating',
                'desc': f'average rating{avg_rating:.1f}, which may affect the conversion rate',
                'icon': '📉'
            })
        
        # Check number of comments
        total_reviews = sum(v['review_count'] for v in variants)
        if total_reviews < 100:
            risks.append({
                'level': 'medium',
                'title': 'Not enough comments',
                'desc': f'The total number of comments is only{total_reviews}, trust building needs to be strengthened',
                'icon': '💬'
            })
        
        if not risks:
            risks.append({
                'level': 'low',
                'title': 'No major risks yet',
                'desc': 'Current product portfolio risks are controllable',
                'icon': '✅'
            })
        
        return risks
    
    def _generate_risk_items(self, risks: List[Dict]) -> str:
        """Generate risk items"""
        items = []
        for risk in risks:
            items.append(f'''
                <div class="item {risk['level']}">
                    <div class="item-icon">{risk['icon']}</div>
                    <div class="item-content">
                        <div class="item-title">{risk['title']}</div>
                        <div class="item-desc">{risk['desc']}</div>
                    </div>
                </div>
            ''')
        return '\n'.join(items)
    
    def _generate_action_items(self, variants: List[Dict]) -> str:
        """Generate updates based on product data 30-60-90 day action plan"""
        
        # Analyze product data
        sorted_by_sales = sorted(variants, key=lambda x: x.get('sales', 0), reverse=True)
        top_variants = sorted_by_sales[:3] if len(sorted_by_sales) >= 3 else sorted_by_sales
        
        avg_rating = sum(v.get('rating', 0) for v in variants) / len(variants) if variants else 0
        avg_bsr = sum(v.get('bsr', 999999) for v in variants) / len(variants) if variants else 999999
        
        # Identify the problem
        low_rating = avg_rating < 4.0
        high_bsr = avg_bsr > 100000
        
        # Generate dynamics 30-60-90 day plan
        actions = []
        
        # === 30 day action plan ===
        actions.append({
            'phase': '30 days',
            'priority': 'high',
            'title': f'quick start - Concentrate on promoting TOP{len(top_variants)}Variants',
            'desc': f"Start advertising now: {', '.join([v.get('color', 'Default') for v in top_variants])}。"
                   f"Expected to be available in the first month {sum(v.get('sales', 0) for v in top_variants)//4} Single sales volume."
                   f"budget advice: ${sum(v.get('sales', 0) for v in top_variants)*0.5:.0f}/month (Based on TACOS 15%)",
            'kpi': f'Single quantity target: {sum(v.get("sales", 0) for v in top_variants)//4}Single/month | ACoS < 25%'
        })
        
        # Add targeted 30-day actions based on data
        if low_rating:
            actions.append({
                'phase': '30 days',
                'priority': 'high',
                'title': 'Emergency optimization - Improve rating to 4.0+',
                'desc': f'Current rating {avg_rating:.1f} On the low side, start the Vine plan and follow up with after-sales emails.'
                       'Contact suppliers to check for product quality issues and suspend sales of low-scoring variants if necessary.',
                'kpi': 'Rating improved to 4.0+ | Negative review rate<2%'
            })
        
        # === 60 day action plan ===
        actions.append({
            'phase': '60 days',
            'priority': 'medium',
            'title': 'Inventory optimization - Clean up long tail variants',
            'desc': f'According to the first month’s data, after the elimination of sales volume, 50%Variation, centralized inventory to TOP{len(top_variants)}。'
                   f'Expected to reduce inventory costs {len(variants)//2} The management cost of each SKU.',
            'kpi': f'Inventory turnover rate increased by 30% | The number of SKUs is optimized to{max(3, len(variants)//2)}a'
        })
        
        if high_bsr:
            actions.append({
                'phase': '60 days',
                'priority': 'medium',
                'title': 'Ranking Sprint - BSR enters the top 50,000',
                'desc': f'Current average BSR {avg_bsr:,.0f} On the high side, through LD/7DD flash sale improves ranking.'
                       'Optimize keyword placement and increase bids for high-converting words20%。',
                'kpi': 'BSR enters the category TOP 50,000 | Natural traffic proportion>40%'
            })
        
        # === 90 day action plan ===
        total_monthly_sales = sum(v.get('sales', 0) for v in variants)
        actions.append({
            'phase': '90 days',
            'priority': 'low',
            'title': 'scale expansion - Copy success pattern',
            'desc': f'Based on the successful experience of TOP variants, similar product lines will be expanded.'
                   f'Current monthly sales{total_monthly_sales}Single, the target Q2 is increased to{int(total_monthly_sales*1.5)}Single.'
                   'Evaluate brand flagship store and A+Page construction.',
            'kpi': f'monthly sales target: {int(total_monthly_sales*1.5)}Single | The profit margin reaches 25%+'
        })
        
        # Generate HTML
        items = []
        current_phase = None
        
        for action in actions:
            # stage separation
            if current_phase != action['phase']:
                current_phase = action['phase']
                items.append(f'''
                    <div style="margin: 20px 0 10px 0; padding: 8px 16px; background: rgba(59,130,246,0.1); 
                                border-left: 3px solid var(--blue); border-radius: 0 8px 8px 0;">
                        <span style="font-weight: 600; color: var(--blue);">📅 {action['phase']}action plan</span>
                    </div>
                ''')
            
            priority_color = 'red' if action['priority'] == 'high' else ('yellow' if action['priority'] == 'medium' else 'blue')
            
            items.append(f'''
                <div class="item" style="margin-left: 10px;">
                    <div style="background: var(--{priority_color}); color: var(--bg); padding: 5px 12px; 
                                border-radius: 20px; font-size: 0.75em; font-weight: 600; text-transform: uppercase;">
                        {action['priority']}
                    </div>
                    <div class="item-content" style="flex: 1;">
                        <div class="item-title">{action['title']}</div>
                        <div class="item-desc">{action['desc']}</div>
                        <div style="margin-top: 8px; padding: 6px 10px; background: rgba(59,130,246,0.05); 
                                    border-radius: 6px; font-size: 0.8em; color: var(--blue);">
                            🎯 {action['kpi']}
                        </div>
                    </div>
                </div>
            ''')
        
        return '\n'.join(items)


def generate_unified_report_v2(asin: str, products: List[Dict], 
                                analysis_data: Dict, output_path: str = None) -> str:
    """Generate Uniform Actuarial Report v2"""
    generator = UnifiedActuaryReportV2()
    return generator.generate(asin, products, analysis_data, output_path)


if __name__ == "__main__":
    print("Unified Actuarial Report Generator v2")
    print("Contains complete Keepa indicators and actuarial analysis dimensions")
