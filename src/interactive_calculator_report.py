"""
Interactive Actuarial Report Generator
========================
Built-in calculator, just fill in the purchase cost (RMB) and automatically calculate the complete report
"""

import json
from datetime import datetime
from typing import Dict, List


class InteractiveCalculatorReport:
    """
    Interactive report generator
    
    Features:
    - Built-in calculator, just fill in the purchase cost (RMB)
    - Automatically calculate first-way freight (12RMB/kg）
    - Live exchange rate conversion
    - Instantly updated profit analysis
    """
    
    def __init__(self):
        # Default parameters
        self.shipping_rate_rmb_per_kg = 12  # Shipping price: 12RMB/kg
        self.default_weight_kg = 0.5  # Default product weight 0.5kg
        self.exchange_rate = 7.2  # Exchange rate: 1 USD = 7.2 RMB
        self.tariff_rate = 0.15  # Tariff rate: 15%
        
    def generate(self, asin: str, products: List[Dict], analysis_data: Dict, 
                 output_path: str) -> str:
        """Generate interactive reports"""
        
        html = self._build_interactive_html(asin, products, analysis_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def _build_interactive_html(self, asin: str, products: List[Dict], 
                                analysis_data: Dict) -> str:
        """Build interactive HTML"""
        
        # Prepare variant data JSON
        variants_json = json.dumps(analysis_data.get('variants', []), 
                                   ensure_ascii=False, default=str)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Actuary Analysis Report | {asin}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        :root {{
            --bg: #0a0a0a;
            --surface: #141414;
            --elevated: #1a1a1a;
            --text: #ffffff;
            --text-secondary: rgba(255,255,255,0.6);
            --text-muted: rgba(255,255,255,0.4);
            --green: #22c55e;
            --red: #ef4444;
            --yellow: #f59e0b;
            --blue: #3b82f6;
            --purple: #8b5cf6;
            --border: rgba(255,255,255,0.08);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 40px; }}
        
        /* Header */
        .header {{
            text-align: center;
            padding: 60px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 60px;
        }}
        .header h1 {{
            font-size: 2.5em;
            font-weight: 300;
            letter-spacing: 8px;
            margin-bottom: 20px;
        }}
        .header .subtitle {{
            color: var(--text-secondary);
            font-size: 1em;
            letter-spacing: 2px;
        }}
        
        /* Calculator Panel */
        .calculator-panel {{
            background: linear-gradient(135deg, var(--surface) 0%, var(--elevated) 100%);
            border: 2px solid var(--blue);
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 60px;
            position: relative;
            overflow: hidden;
        }}
        
        .calculator-panel::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--blue), var(--purple));
        }}
        
        .panel-title {{
            font-size: 1.3em;
            font-weight: 500;
            margin-bottom: 30px;
            color: var(--blue);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .panel-title::before {{
            content: '🔧';
            font-size: 1.2em;
        }}
        
        /* Input Grid */
        .input-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .input-group {{
            background: var(--bg);
            padding: 25px;
            border-radius: 12px;
            border: 1px solid var(--border);
        }}
        
        .input-group label {{
            display: block;
            font-size: 0.85em;
            color: var(--text-muted);
            margin-bottom: 12px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        
        .input-wrapper {{
            position: relative;
            display: flex;
            align-items: center;
        }}
        
        .input-wrapper input {{
            width: 100%;
            background: transparent;
            border: 2px solid var(--border);
            border-radius: 8px;
            padding: 15px 20px;
            font-size: 1.5em;
            font-weight: 300;
            color: var(--text);
            transition: all 0.3s;
        }}
        
        .input-wrapper input:focus {{
            outline: none;
            border-color: var(--blue);
            box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
        }}
        
        .input-wrapper .unit {{
            position: absolute;
            right: 20px;
            font-size: 0.9em;
            color: var(--text-muted);
        }}
        
        .input-hint {{
            font-size: 0.75em;
            color: var(--text-muted);
            margin-top: 10px;
        }}
        
        /* Calculation Breakdown */
        .calc-breakdown {{
            background: var(--bg);
            border-radius: 12px;
            padding: 30px;
            margin-top: 30px;
        }}
        
        .breakdown-title {{
            font-size: 1em;
            color: var(--text-secondary);
            margin-bottom: 20px;
            letter-spacing: 1px;
        }}
        
        .breakdown-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        
        .breakdown-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: var(--surface);
            border-radius: 8px;
            border-left: 3px solid var(--border);
        }}
        
        .breakdown-item.highlight {{
            border-left-color: var(--green);
            background: linear-gradient(90deg, rgba(34,197,94,0.1), transparent);
        }}
        
        .breakdown-label {{
            font-size: 0.85em;
            color: var(--text-muted);
        }}
        
        .breakdown-value {{
            font-size: 1.1em;
            font-weight: 500;
            font-family: 'Monaco', monospace;
        }}
        
        /* Results Section */
        .results-section {{
            margin-top: 60px;
        }}
        
        .section-title {{
            font-size: 1.2em;
            font-weight: 400;
            letter-spacing: 3px;
            padding: 20px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 40px;
            color: var(--text-secondary);
        }}
        
        /* Variant Cards */
        .variant-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
        }}
        
        .variant-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 30px;
            transition: all 0.3s;
        }}
        
        .variant-card:hover {{
            border-color: var(--blue);
            transform: translateY(-5px);
        }}
        
        .variant-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }}
        
        .variant-info h3 {{
            font-size: 1.1em;
            font-weight: 500;
            margin-bottom: 5px;
        }}
        
        .variant-asin {{
            font-size: 0.75em;
            color: var(--text-muted);
            font-family: 'Monaco', monospace;
        }}
        
        .variant-price {{
            font-size: 1.5em;
            font-weight: 300;
            color: var(--blue);
        }}
        
        .variant-metrics {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }}
        
        .metric-box {{
            background: var(--bg);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .metric-box label {{
            display: block;
            font-size: 0.7em;
            color: var(--text-muted);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .metric-box .value {{
            font-size: 1.3em;
            font-weight: 500;
            font-family: 'Monaco', monospace;
        }}
        
        .metric-box .value.positive {{ color: var(--green); }}
        .metric-box .value.negative {{ color: var(--red); }}
        
        /* Summary Card */
        .summary-card {{
            background: linear-gradient(135deg, var(--surface), var(--elevated));
            border: 2px solid var(--green);
            border-radius: 16px;
            padding: 40px;
            margin-top: 40px;
            text-align: center;
        }}
        
        .summary-label {{
            font-size: 0.9em;
            color: var(--text-secondary);
            letter-spacing: 2px;
            margin-bottom: 15px;
        }}
        
        .summary-value {{
            font-size: 3.5em;
            font-weight: 200;
            color: var(--green);
            margin-bottom: 10px;
        }}
        
        .summary-hint {{
            font-size: 0.85em;
            color: var(--text-muted);
        }}
        
        /* Verdict Section */
        .verdict-section {{
            text-align: center;
            padding: 80px 0;
            margin-top: 60px;
        }}
        
        .verdict-text {{
            font-size: 4em;
            font-weight: 200;
            letter-spacing: 12px;
            margin-bottom: 20px;
            transition: all 0.3s;
        }}
        
        .verdict-text.proceed {{ color: var(--green); }}
        .verdict-text.caution {{ color: var(--yellow); }}
        .verdict-text.avoid {{ color: var(--red); }}
        
        .verdict-confidence {{
            font-size: 1.2em;
            color: var(--text-secondary);
            letter-spacing: 2px;
        }}
        
        /* Formula Display */
        .formula-display {{
            background: var(--bg);
            border-radius: 12px;
            padding: 25px;
            margin-top: 30px;
            font-family: 'Monaco', monospace;
            font-size: 0.9em;
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }}
        
        .formula-title {{
            font-size: 0.8em;
            color: var(--text-muted);
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .formula {{
            line-height: 2;
        }}
        
        .formula .highlight {{
            color: var(--blue);
            font-weight: 500;
        }}
        
        /* Settings Panel */
        .settings-panel {{
            background: var(--surface);
            border-radius: 12px;
            padding: 25px;
            margin-top: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        
        .setting-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .setting-label {{
            font-size: 0.85em;
            color: var(--text-muted);
        }}
        
        .setting-value {{
            font-family: 'Monaco', monospace;
            color: var(--blue);
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 20px; }}
            .header h1 {{ font-size: 1.8em; }}
            .input-grid {{ grid-template-columns: 1fr; }}
            .variant-grid {{ grid-template-columns: 1fr; }}
            .verdict-text {{ font-size: 2.5em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>Interactive Actuary Analysis Report</h1>
            <div class="subtitle">Fill in the purchase cost and calculate the complete profit analysis instantly</div>
            <div class="subtitle" style="margin-top: 10px;">ASIN: {asin}</div>
        </header>
        
        <!-- Calculator Panel -->
        <div class="calculator-panel">
            <div class="panel-title">cost calculator</div>
            
            <div class="input-grid">
                <div class="input-group">
                    <label>Procurement cost (Required)</label>
                    <div class="input-wrapper">
                        <input type="number" id="procurementCost" 
                               placeholder="For example: 35" 
                               oninput="calculateAll()">
                        <span class="unit">RMB</span>
                    </div>
                    <div class="input-hint">Supplier's quotation (RMB)</div>
                </div>
                
                <div class="input-group">
                    <label>Product weight</label>
                    <div class="input-wrapper">
                        <input type="number" id="productWeight" 
                               value="{self.default_weight_kg}" 
                               step="0.1"
                               oninput="calculateAll()">
                        <span class="unit">kg</span>
                    </div>
                    <div class="input-hint">Used to calculate first-way freight</div>
                </div>
                
                <div class="input-group">
                    <label>shipping price</label>
                    <div class="input-wrapper">
                        <input type="number" id="shippingRate" 
                               value="{self.shipping_rate_rmb_per_kg}" 
                               oninput="calculateAll()">
                        <span class="unit">RMB/kg</span>
                    </div>
                    <div class="input-hint">Default 12 RMB/kg</div>
                </div>
                
                <div class="input-group">
                    <label>exchange rate</label>
                    <div class="input-wrapper">
                        <input type="number" id="exchangeRate" 
                               value="{self.exchange_rate}" 
                               step="0.1"
                               oninput="calculateAll()">
                        <span class="unit">RMB/USD</span>
                    </div>
                    <div class="input-hint">Default 7.2</div>
                </div>
            </div>
            
            <!-- Calculation Breakdown -->
            <div class="calc-breakdown">
                <div class="breakdown-title">Cost composition details</div>
                <div class="breakdown-grid">
                    <div class="breakdown-item">
                        <span class="breakdown-label">Procurement cost</span>
                        <span class="breakdown-value" id="displayProcurement">-</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">First leg freight</span>
                        <span class="breakdown-value" id="displayShipping">-</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">tariff (15%)</span>
                        <span class="breakdown-value" id="displayTariff">-</span>
                    </div>
                    <div class="breakdown-item highlight">
                        <span class="breakdown-label">Total COGS</span>
                        <span class="breakdown-value" id="displayTotalCOGS">-</span>
                    </div>
                </div>
            </div>
            
            <!-- Formula Display -->
            <div class="formula-display">
                <div class="formula-title">Calculation formula</div>
                <div class="formula">
                    <span class="highlight">COGS (USD)</span> = [Procurement cost(RMB) + (weight(kg) × Shipping price(RMB/kg))] × 1.15(tariff) ÷ exchange rate<br>
                    <span id="formulaExample" style="color: var(--text-muted);">Waiting for input...</span>
                </div>
            </div>
            
            <!-- Settings Summary -->
            <div class="settings-panel">
                <div class="setting-item">
                    <span class="setting-label">First leg freight estimate</span>
                    <span class="setting-value" id="settingShipping">{self.default_weight_kg}kg × {self.shipping_rate_rmb_per_kg}RMB = {self.default_weight_kg * self.shipping_rate_rmb_per_kg}RMB</span>
                </div>
                <div class="setting-item">
                    <span class="setting-label">tariff rate</span>
                    <span class="setting-value">15%</span>
                </div>
                <div class="setting-item">
                    <span class="setting-label">TACOS</span>
                    <span class="setting-value">15%</span>
                </div>
                <div class="setting-item">
                    <span class="setting-label">Amazon commission</span>
                    <span class="setting-value">15%</span>
                </div>
            </div>
        </div>
        
        <!-- Results Section -->
        <div class="results-section" id="resultsSection" style="display: none;">
            <div class="section-title">Variant Profit Analysis</div>
            
            <div class="variant-grid" id="variantGrid">
                <!-- Variation cards will be dynamically generated via JavaScript -->
            </div>
            
            <!-- Summary -->
            <div class="summary-card">
                <div class="summary-label">Estimated monthly total profit</div>
                <div class="summary-value" id="totalProfit">$0</div>
                <div class="summary-hint">Calculated based on current COGS</div>
            </div>
            
            <!-- Verdict -->
            <div class="verdict-section">
                <div class="verdict-text" id="verdictText">-</div>
                <div class="verdict-confidence" id="verdictConfidence">-</div>
            </div>
        </div>
    </div>
    
    <script>
        // variant data
        const variantsData = {variants_json};
        
        // Count all
        function calculateAll() {{
            const procurementRMB = parseFloat(document.getElementById('procurementCost').value) || 0;
            const weightKg = parseFloat(document.getElementById('productWeight').value) || {self.default_weight_kg};
            const shippingRate = parseFloat(document.getElementById('shippingRate').value) || {self.shipping_rate_rmb_per_kg};
            const exchangeRate = parseFloat(document.getElementById('exchangeRate').value) || {self.exchange_rate};
            
            if (procurementRMB <= 0) {{
                document.getElementById('resultsSection').style.display = 'none';
                return;
            }}
            
            // Calculate cost
            const shippingRMB = weightKg * shippingRate;
            const subtotalRMB = procurementRMB + shippingRMB;
            const tariffRMB = subtotalRMB * 0.15;
            const totalRMB = subtotalRMB + tariffRMB;
            const cogsUSD = totalRMB / exchangeRate;
            
            // Update display
            document.getElementById('displayProcurement').textContent = procurementRMB.toFixed(2) + ' RMB';
            document.getElementById('displayShipping').textContent = shippingRMB.toFixed(2) + ' RMB (' + weightKg + 'kg × ' + shippingRate + 'RMB/kg)';
            document.getElementById('displayTariff').textContent = tariffRMB.toFixed(2) + ' RMB';
            document.getElementById('displayTotalCOGS').textContent = '$' + cogsUSD.toFixed(2) + ' USD';
            
            // Update formula example
            const formulaText = `COGS = [${{procurementRMB}} + (${{weightKg}} × ${{shippingRate}})] × 1.15 ÷ ${{exchangeRate}} = $${{cogsUSD.toFixed(2)}}`;
            document.getElementById('formulaExample').textContent = formulaText;
            
            // Update settings display
            document.getElementById('settingShipping').textContent = `${{weightKg}}kg × ${{shippingRate}}RMB = ${{shippingRMB.toFixed(0)}}RMB`;
            
            // Calculate and display variant analysis
            calculateVariants(cogsUSD);
            
            // Show results area
            document.getElementById('resultsSection').style.display = 'block';
        }}
        
        // Calculate variant profit
        function calculateVariants(cogsUSD) {{
            const variantGrid = document.getElementById('variantGrid');
            variantGrid.innerHTML = '';
            
            let totalProfit = 0;
            let totalSales = 0;
            
            variantsData.forEach((variant, index) => {{
                const price = variant.price || 30.99;
                const sales = variant.sales || 600;
                const organicPct = variant.organic_pct || 0.65;
                const adPct = variant.ad_pct || 0.35;
                
                // Calculate cost
                const fbaFee = 3.22;
                const referralFee = price * 0.15;
                const returnCost = price * 0.05 * 0.3;
                const storageFee = 0.06;
                const operatingCost = fbaFee + referralFee + returnCost + storageFee;
                
                // TACOS Advertising Cost
                const monthlyRevenue = price * sales;
                const monthlyAdBudget = monthlyRevenue * 0.15;
                const monthlyAdOrders = sales * adPct;
                const adCostPerUnit = monthlyAdOrders > 0 ? monthlyAdBudget / monthlyAdOrders : 0;
                
                // Profit calculation
                const organicProfit = price - cogsUSD - operatingCost;
                const adProfit = organicProfit - adCostPerUnit;
                const blendedProfit = organicProfit * organicPct + adProfit * adPct;
                const monthlyProfit = blendedProfit * sales;
                const margin = (blendedProfit / price) * 100;
                
                totalProfit += monthlyProfit;
                totalSales += sales;
                
                // Create variant cards
                const card = document.createElement('div');
                card.className = 'variant-card';
                card.innerHTML = `
                    <div class="variant-header">
                        <div class="variant-info">
                            <h3>${{variant.color || 'color'}} - ${{variant.size || 'Size'}}</h3>
                            <div class="variant-asin">${{variant.asin}}</div>
                        </div>
                        <div class="variant-price">$${{price.toFixed(2)}}</div>
                    </div>
                    <div class="variant-metrics">
                        <div class="metric-box">
                            <label>monthly sales</label>
                            <div class="value">${{sales}}</div>
                        </div>
                        <div class="metric-box">
                            <label>monthly profit</label>
                            <div class="value ${{monthlyProfit > 0 ? 'positive' : 'negative'}}">$${{monthlyProfit.toFixed(0)}}</div>
                        </div>
                        <div class="metric-box">
                            <label>profit margin</label>
                            <div class="value ${{margin > 0 ? 'positive' : 'negative'}}">${{margin.toFixed(1)}}%</div>
                        </div>
                        <div class="metric-box">
                            <label>COGS proportion</label>
                            <div class="value">${{((cogsUSD/price)*100).toFixed(1)}}%</div>
                        </div>
                    </div>
                `;
                variantGrid.appendChild(card);
            }});
            
            // Update total profit
            document.getElementById('totalProfit').textContent = '$' + totalProfit.toFixed(0);
            
            // update decision
            updateVerdict(totalProfit, totalSales);
        }}
        
        // update decision
        function updateVerdict(totalProfit, totalSales) {{
            const avgMargin = (totalProfit / (totalSales * 30)) * 100; // Assuming average price$30
            
            let verdict = 'avoid';
            let confidence = 60;
            let text = 'Recommended to avoid';
            
            if (avgMargin > 15) {{
                verdict = 'proceed';
                confidence = 78;
                text = 'Recommended investment';
            }} else if (avgMargin > 5) {{
                verdict = 'caution';
                confidence = 65;
                text = 'Consider carefully';
            }}
            
            const verdictText = document.getElementById('verdictText');
            verdictText.textContent = text;
            verdictText.className = 'verdict-text ' + verdict;
            
            document.getElementById('verdictConfidence').textContent = 'Confidence ' + confidence + '%';
        }}
    </script>
</body>
</html>'''
        
        return html


# Convenience function
def generate_interactive_report(asin: str, products: List[Dict], 
                                analysis_data: Dict, output_path: str = None) -> str:
    """Generate interactive reports"""
    if output_path is None:
        output_path = f'cache/reports/{asin}_INTERACTIVE_CALCULATOR.html'
    
    generator = InteractiveCalculatorReport()
    return generator.generate(asin, products, analysis_data, output_path)
