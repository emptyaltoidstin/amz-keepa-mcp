"""
统一精算师报告生成器 v2
======================
包含完整的 Keepa 指标和精算师分析维度
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict


class UnifiedActuaryReportV2:
    """
    统一精算师报告 v2 - 包含完整 Keepa 指标
    
    报告结构:
    1. 交互式成本计算器
    2. 执行摘要 (核心指标)
    3. 帕累托分析 (80/20)
    4. 完整变体分析表 (含所有 Keepa 指标)
    5. 风险评估
    6. 投资建议
    7. 行动计划
    """
    
    def __init__(self):
        self.shipping_rate = 12
        self.tariff_rate = 0.15
        self.exchange_rate = 7.2
        
    def generate(self, asin: str, products: List[Dict], 
                 analysis_data: Dict, output_path: str = None) -> str:
        """生成统一报告"""
        
        if output_path is None:
            output_path = f'cache/reports/{asin}_UNIFIED_ACTUARY.html'
        
        # 准备完整数据
        variants = self._prepare_full_variants(products)
        metrics_163 = self._collect_163_metrics(products)
        parent_info = analysis_data.get('parent_info', {})
        
        # 生成HTML
        html = self._build_html(asin, variants, metrics_163, parent_info, analysis_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def _prepare_full_variants(self, products: List[Dict]) -> List[Dict]:
        """准备完整的变体数据，包含所有 Keepa 指标"""
        variants = []
        
        for product in products:
            asin = product.get('asin', '')
            
            # 基础信息
            weight_g = product.get('packageWeight', 0) or product.get('itemWeight', 0) or 300
            
            # 价格
            stats = product.get('stats', {})
            price = stats.get('buyBoxPrice', 2999) / 100 if stats and 'buyBoxPrice' in stats else 29.99
            
            # 销量
            bought = product.get('boughtInPastMonth', 0)
            sales = bought[1] if isinstance(bought, list) and len(bought) > 1 else (bought if isinstance(bought, (int, float)) else 500)
            
            # BSR
            bsr_data = product.get('salesRank', [0, 999999])
            bsr = bsr_data[1] if isinstance(bsr_data, list) and len(bsr_data) > 1 else bsr_data
            
            # 评论
            reviews = product.get('reviews', [])
            review_count = len(reviews) if isinstance(reviews, list) else product.get('reviewCount', 0)
            rating = product.get('stars', 0) or product.get('rating', 0)
            
            # 属性
            attrs = product.get('attributes', [])
            color = self._get_attr(attrs, 'Color') or '默认'
            size = self._get_attr(attrs, 'Size') or '标准'
            
            # 退货率估算
            return_rate = self._estimate_return_rate(product)
            
            # 费用
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
        """收集163指标摘要"""
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
        """获取类目"""
        tree = product.get('categoryTree', [])
        if tree:
            return ' > '.join([c.get('name', '') for c in tree[:3]])
        return product.get('rootCategory', '')
    
    def _get_attr(self, attrs: List, name: str) -> str:
        """获取属性"""
        for attr in attrs:
            if isinstance(attr, dict) and attr.get('name') == name:
                return attr.get('value', '')
        return ''
    
    def _estimate_return_rate(self, product: Dict) -> float:
        """估算退货率"""
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
        """构建完整HTML报告"""
        
        variants_json = json.dumps(variants, ensure_ascii=False)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 汇总数据
        total_sales = sum(v['sales'] for v in variants)
        avg_price = sum(v['price'] for v in variants) / len(variants) if variants else 30
        total_reviews = sum(v['review_count'] for v in variants)
        avg_rating = sum(v['rating'] for v in variants) / len(variants) if variants else 0
        
        # 帕累托分析
        pareto_data = self._calculate_pareto(variants)
        
        # 风险评估
        risks = self._assess_risks(variants, metrics_163)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>统一精算师分析报告 | {asin}</title>
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
            <h1>统一精算师分析报告</h1>
            <div class="subtitle">All-in-One 交互式分析 · 基于Keepa真实数据</div>
            <div class="meta">
                ASIN: {asin} | 
                品牌: {metrics_163.get('brand', 'N/A')} | 
                类目: {metrics_163.get('category', 'N/A')} | 
                生成时间: {timestamp}
            </div>
        </header>
        
        <!-- Section 1: Product Info -->
        <div class="section">
            <div class="section-header">
                <span class="icon">📦</span>
                <h2>产品信息</h2>
            </div>
            <div class="product-info">
                <div style="font-size: 1.1em; margin-bottom: 20px; line-height: 1.8;">
                    {metrics_163.get('title', 'Product Title')}
                </div>
                <div class="info-grid">
                    <div>
                        <div class="info-item">
                            <span class="info-label">总变体数</span>
                            <span class="info-value">{len(variants)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">月均总销量</span>
                            <span class="info-value">{total_sales:,}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">总评论数</span>
                            <span class="info-value">{total_reviews:,}</span>
                        </div>
                    </div>
                    <div>
                        <div class="info-item">
                            <span class="info-label">平均售价</span>
                            <span class="info-value">${avg_price:.2f}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">平均评分</span>
                            <span class="info-value">{avg_rating:.1f} ⭐</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">包装重量</span>
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
                <h2>成本计算器 · 填入1688采购价</h2>
            </div>
            
            <div class="main-input">
                <label>采购成本 (RMB)</label>
                <input type="number" class="input-large" id="procurementCost" 
                       placeholder="0" oninput="calculateAll()">
            </div>
            
            <div class="settings-grid">
                <div class="setting-box">
                    <label>船运价格</label>
                    <input type="number" id="shippingRate" value="{self.shipping_rate}" oninput="calculateAll()">
                </div>
                <div class="setting-box">
                    <label>关税率</label>
                    <div style="font-size: 1.4em; color: var(--text-secondary); font-family: monospace;">15%</div>
                </div>
                <div class="setting-box">
                    <label>汇率</label>
                    <input type="number" id="exchangeRate" value="{self.exchange_rate}" step="0.1" oninput="calculateAll()">
                </div>
                <div class="setting-box">
                    <label>TACOS</label>
                    <div style="font-size: 1.4em; color: var(--text-secondary); font-family: monospace;">15%</div>
                </div>
            </div>
            
            <div class="cost-flow">
                <div class="flow-item">
                    <label>采购成本</label>
                    <div class="value" id="costProcurement">-</div>
                </div>
                <div class="flow-op">+</div>
                <div class="flow-item">
                    <label>头程运费</label>
                    <div class="value" id="costShipping">-</div>
                </div>
                <div class="flow-op">×</div>
                <div class="flow-item">
                    <label>关税15%</label>
                    <div class="value">1.15</div>
                </div>
                <div class="flow-op">÷</div>
                <div class="flow-item">
                    <label>汇率</label>
                    <div class="value" id="costExchange">7.2</div>
                </div>
                <div class="flow-item highlight">
                    <label>总COGS</label>
                    <div class="value" id="costTotal">-</div>
                </div>
            </div>
        </div>
        
        <!-- Section 3: Dashboard -->
        <div class="dashboard-grid" id="dashboardSection" style="display: none;">
            <div class="metric-card highlight">
                <label>月度总利润</label>
                <div class="value" id="totalProfit">$0</div>
            </div>
            <div class="metric-card">
                <label>月度总销量</label>
                <div class="value" id="totalSales">0</div>
            </div>
            <div class="metric-card">
                <label>平均利润率</label>
                <div class="value" id="avgMargin">0%</div>
            </div>
            <div class="metric-card">
                <label>平均ROI</label>
                <div class="value" id="roiEstimate">0%</div>
            </div>
        </div>
        
        <!-- Section 4: Verdict -->
        <div class="verdict-section" id="verdictSection" style="display: none;">
            <div class="verdict-label">投资建议</div>
            <div class="verdict-value" id="verdictValue">-</div>
            <div style="color: var(--text-muted);" id="verdictConfidence">-</div>
        </div>
        
        <!-- Section 5: Variant Analysis -->
        <div class="section">
            <div class="section-header">
                <span class="icon">📊</span>
                <h2>变体详细分析 · 完整Keepa指标</h2>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>变体</th>
                        <th>重量</th>
                        <th>价格</th>
                        <th>月销量</th>
                        <th>BSR</th>
                        <th>评分</th>
                        <th>评论</th>
                        <th>退货率</th>
                        <th>FBA费</th>
                        <th>佣金</th>
                        <th>COGS</th>
                        <th>利润</th>
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
                <h2>帕累托分析 · 80/20核心变体</h2>
            </div>
            <div style="margin-bottom: 20px; color: var(--text-muted);">
                识别贡献80%销量的核心变体 (绿色标记)
            </div>
            {self._generate_pareto_bars(variants)}
        </div>
        
        <!-- Section 7: Risks -->
        <div class="section">
            <div class="section-header">
                <span class="icon">⚠️</span>
                <h2>风险评估</h2>
            </div>
            <div class="item-list">
                {self._generate_risk_items(risks)}
            </div>
        </div>
        
        <!-- Section 8: Actions -->
        <div class="section">
            <div class="section-header">
                <span class="icon">🎯</span>
                <h2>行动计划</h2>
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
            
            let verdict = 'avoid', text = '建议避免', confidence = 60;
            
            if (margin > 15 && roi > 50) {{
                verdict = 'proceed';
                text = '建议投资';
                confidence = 85;
            }} else if (margin > 10 && roi > 20) {{
                verdict = 'caution';
                text = '谨慎考虑';
                confidence = 70;
            }}
            
            verdictEl.textContent = text;
            verdictEl.className = 'verdict-value ' + verdict;
            sectionEl.className = 'verdict-section ' + verdict;
            confidenceEl.textContent = '置信度 ' + confidence + '%';
        }}
        
        calculateAll();
    </script>
</body>
</html>'''
        
        return html
    
    def _generate_variant_rows(self, variants: List[Dict]) -> str:
        """生成变体表格行"""
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
        """计算帕累托数据"""
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
        """生成帕累托图"""
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
        """评估风险"""
        risks = []
        
        # 检查变体数量
        if len(variants) > 10:
            risks.append({
                'level': 'medium',
                'title': '变体数量过多',
                'desc': f'共{len(variants)}个变体，增加库存管理复杂度',
                'icon': '⚠️'
            })
        
        # 检查评分
        avg_rating = sum(v['rating'] for v in variants) / len(variants) if variants else 0
        if avg_rating < 4.0:
            risks.append({
                'level': 'high',
                'title': '评分偏低',
                'desc': f'平均评分{avg_rating:.1f}，可能影响转化率',
                'icon': '📉'
            })
        
        # 检查评论数
        total_reviews = sum(v['review_count'] for v in variants)
        if total_reviews < 100:
            risks.append({
                'level': 'medium',
                'title': '评论数不足',
                'desc': f'总评论数仅{total_reviews}，信任度建设需要加强',
                'icon': '💬'
            })
        
        if not risks:
            risks.append({
                'level': 'low',
                'title': '暂无重大风险',
                'desc': '当前产品组合风险可控',
                'icon': '✅'
            })
        
        return risks
    
    def _generate_risk_items(self, risks: List[Dict]) -> str:
        """生成风险项"""
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
        """生成基于产品数据的动态 30-60-90 天行动计划"""
        
        # 分析产品数据
        sorted_by_sales = sorted(variants, key=lambda x: x.get('sales', 0), reverse=True)
        top_variants = sorted_by_sales[:3] if len(sorted_by_sales) >= 3 else sorted_by_sales
        
        avg_rating = sum(v.get('rating', 0) for v in variants) / len(variants) if variants else 0
        avg_bsr = sum(v.get('bsr', 999999) for v in variants) / len(variants) if variants else 999999
        
        # 识别问题
        low_rating = avg_rating < 4.0
        high_bsr = avg_bsr > 100000
        
        # 生成动态 30-60-90 天计划
        actions = []
        
        # === 30天行动计划 ===
        actions.append({
            'phase': '30天',
            'priority': 'high',
            'title': f'快速启动 - 集中火力推广TOP{len(top_variants)}变体',
            'desc': f"立即启动广告投放: {', '.join([v.get('color', '默认') for v in top_variants])}。"
                   f"预计首月可获得 {sum(v.get('sales', 0) for v in top_variants)//4} 单销量。"
                   f"预算建议: ${sum(v.get('sales', 0) for v in top_variants)*0.5:.0f}/月 (基于TACOS 15%)",
            'kpi': f'单量目标: {sum(v.get("sales", 0) for v in top_variants)//4}单/月 | ACoS < 25%'
        })
        
        # 根据数据添加针对性的30天行动
        if low_rating:
            actions.append({
                'phase': '30天',
                'priority': 'high',
                'title': '紧急优化 - 提升评分至4.0+',
                'desc': f'当前评分 {avg_rating:.1f} 偏低，启动Vine计划和售后邮件跟进。'
                       '联系供应商检查产品质量问题，必要时暂停低评分变体销售。',
                'kpi': '评分提升至4.0+ | 差评率<2%'
            })
        
        # === 60天行动计划 ===
        actions.append({
            'phase': '60天',
            'priority': 'medium',
            'title': '库存优化 - 清理长尾变体',
            'desc': f'根据首月数据，淘汰销量后50%的变体，集中库存到TOP{len(top_variants)}。'
                   f'预计可降低库存成本 {len(variants)//2} 个SKU的管理成本。',
            'kpi': f'库存周转率提升30% | SKU数量优化至{max(3, len(variants)//2)}个'
        })
        
        if high_bsr:
            actions.append({
                'phase': '60天',
                'priority': 'medium',
                'title': '排名冲刺 - BSR进入前5万',
                'desc': f'当前平均BSR {avg_bsr:,.0f} 偏高，通过LD/7DD秒杀提升排名。'
                       '优化关键词投放，针对高转化词提高竞价20%。',
                'kpi': 'BSR进入类目TOP 50,000 | 自然流量占比>40%'
            })
        
        # === 90天行动计划 ===
        total_monthly_sales = sum(v.get('sales', 0) for v in variants)
        actions.append({
            'phase': '90天',
            'priority': 'low',
            'title': '规模扩张 - 复制成功模式',
            'desc': f'基于TOP变体的成功经验，拓展相似产品线。'
                   f'当前月销{total_monthly_sales}单，目标Q2提升至{int(total_monthly_sales*1.5)}单。'
                   '评估品牌旗舰店和A+页面建设。',
            'kpi': f'月销量目标: {int(total_monthly_sales*1.5)}单 | 利润率达到25%+'
        })
        
        # 生成HTML
        items = []
        current_phase = None
        
        for action in actions:
            # 阶段分隔
            if current_phase != action['phase']:
                current_phase = action['phase']
                items.append(f'''
                    <div style="margin: 20px 0 10px 0; padding: 8px 16px; background: rgba(59,130,246,0.1); 
                                border-left: 3px solid var(--blue); border-radius: 0 8px 8px 0;">
                        <span style="font-weight: 600; color: var(--blue);">📅 {action['phase']}行动计划</span>
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
    """生成统一精算师报告 v2"""
    generator = UnifiedActuaryReportV2()
    return generator.generate(asin, products, analysis_data, output_path)


if __name__ == "__main__":
    print("统一精算师报告生成器 v2")
    print("包含完整 Keepa 指标和精算师分析维度")
