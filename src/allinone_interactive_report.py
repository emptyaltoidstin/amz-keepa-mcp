"""
All-in-One 交互式精算师报告
=============================
包含内置计算器的完整HTML报告
- 使用Keepa API真实重量数据
- 只需填入采购成本（RMB）
- 自动计算头程运费（12RMB/kg）
- 实时更新利润分析
"""

import json
from datetime import datetime
from typing import Dict, List


class AllInOneInteractiveReport:
    """
    All-in-One交互式报告生成器
    
    特点：
    - 使用Keepa API真实重量数据 (packageWeight)
    - 头程运费 = 重量(kg) × 12 RMB/kg
    - 只需填入采购成本（RMB）
    - 关税 15%
    - 自动转换为USD COGS
    """
    
    def __init__(self):
        self.shipping_rate = 12  # RMB/kg
        self.tariff_rate = 0.15
        self.exchange_rate = 7.2
        
    def generate(self, asin: str, products: List[Dict], analysis_data: Dict, 
                 output_path: str = None) -> str:
        """生成交互式报告"""
        
        if output_path is None:
            output_path = f'cache/reports/{asin}_ALLINONE_INTERACTIVE.html'
        
        # 准备变体数据（包含真实重量）
        variants_with_weight = self._prepare_variants_data(products, analysis_data)
        
        html = self._build_html(asin, variants_with_weight, analysis_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def _prepare_variants_data(self, products: List[Dict], analysis_data: Dict) -> List[Dict]:
        """准备变体数据，包含真实重量"""
        variants = []
        
        for product in products:
            asin = product.get('asin', '')
            
            # 获取重量数据（克转千克）
            package_weight_g = product.get('packageWeight', 0) or 0
            item_weight_g = product.get('itemWeight', 0) or 0
            
            # 优先使用packageWeight，如果没有则使用itemWeight
            weight_kg = (package_weight_g or item_weight_g) / 1000 if (package_weight_g or item_weight_g) else 0.3
            
            # 如果没有重量数据，使用估算值
            if weight_kg == 0:
                weight_kg = 0.3  # 默认300g
            
            # 获取其他属性
            attrs = product.get('attributes', [])
            color = self._get_attr(attrs, 'Color')
            size = self._get_attr(attrs, 'Size')
            
            # 获取价格
            data = product.get('data', {})
            buybox_price = 0
            if data.get('buyBoxSellerIdHistory'):
                csv = data.get('csv', [])
                if len(csv) > 18 and csv[18]:
                    buybox_price = self._get_current_price(csv[18])
            
            if buybox_price == 0:
                buybox_price = product.get('stats', {}).get('buyBoxPrice', 2999) / 100
            
            # 获取销量
            bought_month = product.get('boughtInPastMonth', 0)
            if isinstance(bought_month, dict):
                bought_month = 0
            
            # 获取BSR
            bsr = self._get_bsr(data)
            
            variants.append({
                'asin': asin,
                'color': color,
                'size': size,
                'weight_kg': round(weight_kg, 3),
                'weight_g': round(weight_kg * 1000, 1),
                'price': round(buybox_price, 2),
                'sales': bought_month,
                'bsr': bsr
            })
        
        return variants
    
    def _get_attr(self, attrs: List, name: str) -> str:
        """获取属性值"""
        for attr in attrs:
            if isinstance(attr, dict):
                if attr.get('name') == name:
                    return attr.get('value', 'N/A')
        return 'N/A'
    
    def _get_current_price(self, csv_data) -> float:
        """获取当前价格"""
        if not csv_data:
            return 0
        if isinstance(csv_data, list) and len(csv_data) >= 2:
            return csv_data[-1] / 100 if csv_data[-1] else 0
        return 0
    
    def _get_bsr(self, data: Dict) -> int:
        """获取BSR"""
        csv = data.get('csv', [])
        if len(csv) > 3 and csv[3]:
            bsr_data = csv[3]
            if isinstance(bsr_data, list) and len(bsr_data) >= 2:
                return int(bsr_data[-1]) if bsr_data[-1] else 999999
        return 999999
    
    def _build_html(self, asin: str, variants: List[Dict], analysis_data: Dict) -> str:
        """构建完整的交互式HTML"""
        
        variants_json = json.dumps(variants, ensure_ascii=False)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 计算平均重量
        avg_weight = sum(v['weight_kg'] for v in variants) / len(variants) if variants else 0.3
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>All-in-One 交互式精算师报告 | {asin}</title>
    <style>
        :root {{
            --bg: #0a0a0a;
            --surface: #141414;
            --elevated: #1a1a1a;
            --text: #ffffff;
            --text-secondary: rgba(255,255,255,0.7);
            --text-muted: rgba(255,255,255,0.5);
            --green: #22c55e;
            --green-glow: rgba(34,197,94,0.2);
            --red: #ef4444;
            --red-glow: rgba(239,68,68,0.2);
            --yellow: #f59e0b;
            --blue: #3b82f6;
            --purple: #8b5cf6;
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
        .header .subtitle {{
            color: var(--text-muted);
            font-size: 0.95em;
            letter-spacing: 2px;
        }}
        .header .asin {{
            margin-top: 15px;
            font-family: 'Monaco', monospace;
            color: var(--blue);
            font-size: 0.9em;
            letter-spacing: 1px;
        }}
        
        /* Calculator Section */
        .calculator-section {{
            background: linear-gradient(135deg, var(--surface) 0%, var(--elevated) 100%);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 50px;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 35px;
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
        
        /* Main Input */
        .main-input {{
            background: var(--bg);
            border: 2px solid var(--border);
            border-radius: 16px;
            padding: 35px;
            text-align: center;
            margin-bottom: 30px;
            transition: all 0.3s;
        }}
        .main-input:focus-within {{
            border-color: var(--blue);
            box-shadow: 0 0 0 4px rgba(59,130,246,0.1);
        }}
        
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
        
        .input-unit {{
            font-size: 1.2em;
            color: var(--text-muted);
            margin-top: 10px;
        }}
        
        /* Settings Grid */
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
        
        .setting-box .value-static {{
            font-size: 1.4em;
            color: var(--text-secondary);
            font-family: 'Monaco', monospace;
        }}
        
        /* Cost Breakdown */
        .cost-breakdown {{
            background: var(--bg);
            border-radius: 16px;
            padding: 30px;
        }}
        
        .breakdown-title {{
            font-size: 0.9em;
            color: var(--text-muted);
            margin-bottom: 25px;
            letter-spacing: 1px;
        }}
        
        .breakdown-flow {{
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
        
        .flow-item label {{
            display: block;
            font-size: 0.7em;
            color: var(--text-muted);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .flow-item .value {{
            font-size: 1.5em;
            font-family: 'Monaco', monospace;
            color: var(--text-secondary);
        }}
        
        .flow-item.highlight {{
            background: linear-gradient(135deg, rgba(34,197,94,0.15), rgba(34,197,94,0.05));
            border: 1px solid rgba(34,197,94,0.3);
        }}
        .flow-item.highlight .value {{ color: var(--green); }}
        
        .flow-arrow {{
            font-size: 1.5em;
            color: var(--text-muted);
        }}
        
        .flow-op {{
            background: var(--elevated);
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1em;
            color: var(--text-muted);
        }}
        
        /* Variants Table */
        .variants-section {{
            margin-bottom: 50px;
        }}
        
        .variants-table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--surface);
            border-radius: 16px;
            overflow: hidden;
        }}
        
        .variants-table th {{
            background: var(--elevated);
            padding: 18px 15px;
            text-align: left;
            font-size: 0.75em;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }}
        
        .variants-table td {{
            padding: 18px 15px;
            border-bottom: 1px solid var(--border);
        }}
        
        .variants-table tr:last-child td {{ border-bottom: none; }}
        .variants-table tr:hover {{ background: rgba(255,255,255,0.02); }}
        
        .variant-info {{ display: flex; flex-direction: column; gap: 5px; }}
        .variant-info .name {{ font-weight: 500; }}
        .variant-info .asin {{ font-size: 0.75em; color: var(--text-muted); font-family: monospace; }}
        
        .weight-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: rgba(139,92,246,0.15);
            color: var(--purple);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-family: monospace;
        }}
        
        .price-tag {{
            font-size: 1.2em;
            font-weight: 500;
            color: var(--blue);
            font-family: monospace;
        }}
        
        .metric-value {{
            font-family: monospace;
            font-size: 1.1em;
        }}
        .metric-value.positive {{ color: var(--green); }}
        .metric-value.negative {{ color: var(--red); }}
        .metric-value.neutral {{ color: var(--text-secondary); }}
        
        /* Summary Cards */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 50px;
        }}
        
        .summary-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 30px;
            text-align: center;
        }}
        
        .summary-card.highlight {{
            background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(34,197,94,0.02));
            border-color: rgba(34,197,94,0.3);
        }}
        
        .summary-card label {{
            display: block;
            font-size: 0.8em;
            color: var(--text-muted);
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .summary-card .value {{
            font-size: 2.5em;
            font-weight: 300;
            font-family: 'Monaco', monospace;
        }}
        
        .summary-card.highlight .value {{ color: var(--green); }}
        
        /* Verdict */
        .verdict-section {{
            text-align: center;
            padding: 60px 0;
            background: var(--surface);
            border-radius: 20px;
            border: 1px solid var(--border);
        }}
        
        .verdict-label {{
            font-size: 0.9em;
            color: var(--text-muted);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 20px;
        }}
        
        .verdict-value {{
            font-size: 3.5em;
            font-weight: 200;
            letter-spacing: 8px;
            margin-bottom: 15px;
        }}
        
        .verdict-value.proceed {{ color: var(--green); }}
        .verdict-value.caution {{ color: var(--yellow); }}
        .verdict-value.avoid {{ color: var(--red); }}
        
        .verdict-confidence {{
            font-size: 1em;
            color: var(--text-muted);
        }}
        
        /* Formula Section */
        .formula-section {{
            background: var(--surface);
            border-radius: 16px;
            padding: 30px;
            margin-top: 40px;
        }}
        
        .formula-title {{
            font-size: 0.8em;
            color: var(--text-muted);
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .formula-code {{
            background: var(--bg);
            border-radius: 12px;
            padding: 25px;
            font-family: 'Monaco', 'Fira Code', monospace;
            font-size: 0.9em;
            line-height: 2;
            color: var(--text-secondary);
            overflow-x: auto;
        }}
        
        .formula-code .comment {{ color: var(--text-muted); }}
        .formula-code .variable {{ color: var(--blue); }}
        .formula-code .number {{ color: var(--purple); }}
        .formula-code .result {{ color: var(--green); }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .header h1 {{ font-size: 1.6em; }}
            .input-large {{ font-size: 2.5em; }}
            .breakdown-flow {{ flex-direction: column; }}
            .flow-arrow {{ transform: rotate(90deg); }}
            .variants-table {{ font-size: 0.85em; }}
            .variants-table th, .variants-table td {{ padding: 12px 8px; }}
            .verdict-value {{ font-size: 2.5em; letter-spacing: 4px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>All-in-One 交互式精算师报告</h1>
            <div class="subtitle">填入采购成本，即刻获取完整利润分析</div>
            <div class="asin">ASIN: {asin}</div>
        </header>
        
        <!-- Calculator Section -->
        <div class="calculator-section">
            <div class="section-header">
                <span class="icon">🔧</span>
                <h2>成本计算器</h2>
            </div>
            
            <!-- Main Input -->
            <div class="main-input">
                <label>采购成本</label>
                <input type="number" class="input-large" id="procurementCost" 
                       placeholder="0" oninput="calculateAll()">
                <div class="input-unit">人民币 (RMB)</div>
            </div>
            
            <!-- Settings -->
            <div class="settings-grid">
                <div class="setting-box">
                    <label>船运价格</label>
                    <input type="number" id="shippingRate" value="{self.shipping_rate}" 
                           oninput="calculateAll()">
                </div>
                <div class="setting-box">
                    <label>关税率</label>
                    <div class="value-static">15%</div>
                </div>
                <div class="setting-box">
                    <label>汇率</label>
                    <input type="number" id="exchangeRate" value="{self.exchange_rate}" 
                           step="0.1" oninput="calculateAll()">
                </div>
                <div class="setting-box">
                    <label>TACOS</label>
                    <div class="value-static">15%</div>
                </div>
            </div>
            
            <!-- Cost Breakdown -->
            <div class="cost-breakdown">
                <div class="breakdown-title">成本构成计算流程</div>
                <div class="breakdown-flow">
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
                        <label>关税 15%</label>
                        <div class="value">1.15</div>
                    </div>
                    <div class="flow-op">÷</div>
                    <div class="flow-item">
                        <label>汇率</label>
                        <div class="value" id="costExchange">-</div>
                    </div>
                    <div class="flow-arrow">→</div>
                    <div class="flow-item highlight">
                        <label>总COGS (USD)</label>
                        <div class="value" id="costTotal">-</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Variants Section -->
        <div class="variants-section">
            <div class="section-header">
                <span class="icon">📦</span>
                <h2>变体分析</h2>
            </div>
            
            <table class="variants-table">
                <thead>
                    <tr>
                        <th>变体</th>
                        <th>重量</th>
                        <th>价格</th>
                        <th>头程运费</th>
                        <th>COGS</th>
                        <th>月销</th>
                        <th>利润</th>
                        <th>利润率</th>
                    </tr>
                </thead>
                <tbody id="variantsTableBody">
                    <!-- 动态生成 -->
                </tbody>
            </table>
        </div>
        
        <!-- Summary -->
        <div class="summary-grid" id="summarySection" style="display: none;">
            <div class="summary-card">
                <label>预计月度总利润</label>
                <div class="value" id="totalProfit">$0</div>
            </div>
            <div class="summary-card">
                <label>预计月度总销量</label>
                <div class="value" id="totalSales">0</div>
            </div>
            <div class="summary-card">
                <label>平均利润率</label>
                <div class="value" id="avgMargin">0%</div>
            </div>
            <div class="summary-card highlight">
                <label>ROI估算</label>
                <div class="value" id="roiEstimate">0%</div>
            </div>
        </div>
        
        <!-- Verdict -->
        <div class="verdict-section" id="verdictSection" style="display: none;">
            <div class="verdict-label">投资建议</div>
            <div class="verdict-value" id="verdictValue">-</div>
            <div class="verdict-confidence" id="verdictConfidence">-</div>
        </div>
        
        <!-- Formula -->
        <div class="formula-section">
            <div class="formula-title">计算公式详解</div>
            <div class="formula-code">
<span class="comment">// 头程运费计算 (基于Keepa API真实重量)</span>
<span class="variable">头程运费</span> = 重量(kg) × 船运价格(RMB/kg)

<span class="comment">// COGS计算流程</span>
<span class="variable">COGS(USD)</span> = [采购成本(RMB) + 头程运费(RMB)] × <span class="number">1.15</span>(关税) ÷ 汇率

<span class="comment">// 单件利润计算 (TACOS模型)</span>
<span class="variable">利润</span> = 售价 - COGS - FBA费用 - 佣金 - 广告成本 - 退货成本

<span class="comment">// 月度利润</span>
<span class="variable">月利润</span> = 单件利润 × 月销量
            </div>
        </div>
    </div>
    
    <script>
        // 变体数据（包含Keepa真实重量）
        const variantsData = {variants_json};
        const avgWeight = {avg_weight:.3f};
        
        // 初始化表格
        function initTable() {{
            const tbody = document.getElementById('variantsTableBody');
            tbody.innerHTML = '';
            
            variantsData.forEach(v => {{
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>
                        <div class="variant-info">
                            <div class="name">${{v.color}} - ${{v.size}}</div>
                            <div class="asin">${{v.asin}}</div>
                        </div>
                    </td>
                    <td><span class="weight-badge">⚖️ ${{v.weight_g}}g</span></td>
                    <td><span class="price-tag">$${{v.price.toFixed(2)}}</span></td>
                    <td class="metric-value neutral shipping-cost" data-weight="${{v.weight_kg}}">-</td>
                    <td class="metric-value neutral cogs-value" data-weight="${{v.weight_kg}}">-</td>
                    <td class="metric-value neutral">${{v.sales || '-'}}</td>
                    <td class="metric-value neutral profit-value">-</td>
                    <td class="metric-value neutral margin-value">-</td>
                `;
                tbody.appendChild(row);
            }});
        }}
        
        // 计算所有
        function calculateAll() {{
            const procurementRMB = parseFloat(document.getElementById('procurementCost').value) || 0;
            const shippingRate = parseFloat(document.getElementById('shippingRate').value) || {self.shipping_rate};
            const exchangeRate = parseFloat(document.getElementById('exchangeRate').value) || {self.exchange_rate};
            
            // 更新流程显示
            document.getElementById('costProcurement').textContent = procurementRMB > 0 ? procurementRMB.toFixed(2) + ' RMB' : '-';
            document.getElementById('costExchange').textContent = exchangeRate.toFixed(1);
            
            // 计算每个变体
            const rows = document.querySelectorAll('#variantsTableBody tr');
            let totalProfit = 0;
            let totalSales = 0;
            let totalRevenue = 0;
            let validVariants = 0;
            
            rows.forEach((row, index) => {{
                const v = variantsData[index];
                const weightKg = v.weight_kg;
                const price = v.price;
                const sales = v.sales || 0;
                
                // 计算头程运费
                const shippingRMB = procurementRMB > 0 ? weightKg * shippingRate : 0;
                
                // 计算COGS
                let cogsUSD = 0;
                if (procurementRMB > 0) {{
                    const subtotalRMB = procurementRMB + shippingRMB;
                    const totalRMB = subtotalRMB * 1.15; // 关税
                    cogsUSD = totalRMB / exchangeRate;
                }}
                
                // 估算FBA费用
                const fbaFee = estimateFBAFee(weightKg);
                
                // 计算费用
                const referralFee = price * 0.15;
                const returnCost = price * 0.05 * 0.3;
                const storageFee = 0.06;
                const tacosCost = price * 0.15;
                
                const totalCost = cogsUSD + fbaFee + referralFee + returnCost + storageFee + tacosCost;
                const profit = price - totalCost;
                const margin = price > 0 ? (profit / price) * 100 : 0;
                const monthlyProfit = profit * sales;
                
                // 更新行
                const shippingCell = row.querySelector('.shipping-cost');
                const cogsCell = row.querySelector('.cogs-value');
                const profitCell = row.querySelector('.profit-value');
                const marginCell = row.querySelector('.margin-value');
                
                if (procurementRMB > 0) {{
                    shippingCell.textContent = shippingRMB.toFixed(0) + ' RMB';
                    cogsCell.textContent = '$' + cogsUSD.toFixed(2);
                    profitCell.textContent = '$' + profit.toFixed(2);
                    marginCell.textContent = margin.toFixed(1) + '%';
                    
                    profitCell.className = 'metric-value profit-value ' + (profit > 0 ? 'positive' : 'negative');
                    marginCell.className = 'metric-value margin-value ' + (margin > 0 ? 'positive' : 'negative');
                    
                    totalProfit += monthlyProfit;
                    totalSales += sales;
                    totalRevenue += price * sales;
                    validVariants++;
                }} else {{
                    shippingCell.textContent = weightKg + 'kg × ' + shippingRate;
                    cogsCell.textContent = '-';
                    profitCell.textContent = '-';
                    marginCell.textContent = '-';
                    profitCell.className = 'metric-value profit-value neutral';
                    marginCell.className = 'metric-value margin-value neutral';
                }}
            }});
            
            // 更新汇总
            if (procurementRMB > 0) {{
                document.getElementById('summarySection').style.display = 'grid';
                document.getElementById('verdictSection').style.display = 'block';
                
                document.getElementById('totalProfit').textContent = '$' + totalProfit.toFixed(0);
                document.getElementById('totalSales').textContent = totalSales.toLocaleString();
                
                const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
                document.getElementById('avgMargin').textContent = avgMargin.toFixed(1) + '%';
                
                // ROI估算
                const monthlyCogs = procurementRMB * totalSales / exchangeRate;
                const roi = monthlyCogs > 0 ? (totalProfit / monthlyCogs) * 100 : 0;
                document.getElementById('roiEstimate').textContent = roi.toFixed(0) + '%';
                
                // 决策
                updateVerdict(avgMargin, roi);
            }} else {{
                document.getElementById('summarySection').style.display = 'none';
                document.getElementById('verdictSection').style.display = 'none';
            }}
        }}
        
        // 估算FBA费用
        function estimateFBAFee(weightKg) {{
            const weightLb = weightKg * 2.20462;
            if (weightLb <= 0.5) return 3.22;
            if (weightLb <= 1.0) return 4.50;
            if (weightLb <= 2.0) return 5.77;
            return 5.77 + (weightLb - 2.0) * 0.50;
        }}
        
        // 更新决策
        function updateVerdict(margin, roi) {{
            const verdictEl = document.getElementById('verdictValue');
            const confidenceEl = document.getElementById('verdictConfidence');
            
            let verdict = 'avoid';
            let text = '建议避免';
            let confidence = 60;
            
            if (margin > 20 && roi > 50) {{
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
            confidenceEl.textContent = '置信度 ' + confidence + '%';
        }}
        
        // 初始化
        initTable();
        calculateAll();
    </script>
</body>
</html>'''
        
        return html


def generate_allinone_report(asin: str, products: List[Dict], 
                              analysis_data: Dict = None,
                              output_path: str = None) -> str:
    """
    生成All-in-One交互式报告
    
    Args:
        asin: 父ASIN
        products: Keepa API产品数据列表
        analysis_data: 分析数据（可选）
        output_path: 输出路径
    
    Returns:
        报告路径
    """
    generator = AllInOneInteractiveReport()
    return generator.generate(asin, products, analysis_data or {}, output_path)


# 测试代码
if __name__ == "__main__":
    # 模拟数据
    test_products = [
        {
            'asin': 'B0TEST001',
            'packageWeight': 450,  # 450克
            'itemWeight': 380,
            'attributes': [{'name': 'Color', 'value': '黑色'}, {'name': 'Size', 'value': 'L'}],
            'data': {'csv': [[], [], [], [100, 5000, 8000], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [2999]]},
            'stats': {'buyBoxPrice': 2999},
            'boughtInPastMonth': 600
        },
        {
            'asin': 'B0TEST002',
            'packageWeight': 380,  # 380克
            'itemWeight': 320,
            'attributes': [{'name': 'Color', 'value': '白色'}, {'name': 'Size', 'value': 'M'}],
            'data': {'csv': [[], [], [], [100, 4500, 7500], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [2799]]},
            'stats': {'buyBoxPrice': 2799},
            'boughtInPastMonth': 450
        }
    ]
    
    output = generate_allinone_report('B0TEST001', test_products)
    print(f"报告已生成: {output}")
