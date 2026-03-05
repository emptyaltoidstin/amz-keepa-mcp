"""
Amazon Operations Actuary Report Generator
=============================
Professional financial analysis and risk assessment based on Keepa data
"""

import json
import math
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class FinancialModel:
    """financial model"""
    selling_price: float
    cogs_estimate: float
    fba_fee: float
    referral_fee: float
    return_cost: float
    storage_cost: float
    ad_cost: float
    total_cost: float
    gross_profit: float
    net_margin: float


@dataclass
class Scenario:
    """Scenario analysis"""
    name: str
    price: float
    volume: int
    revenue: float
    cost: float
    profit: float
    margin: float
    roi: float


class ActuaryReportGenerator:
    """Actuary Report Generator"""
    
    def __init__(self):
        self.referral_rate = 0.15  # Default 15%
        self.return_loss_rate = 0.30  # return loss rate
        self.storage_rate_per_cuft = 0.87  # Warehousing rates $/cu.ft/month
        self.acos_default = 0.15  # Default ACOS 15%
        
    def generate_actuary_report(self,
                               asin: str,
                               product_data: dict,
                               factors: dict,
                               market_report: dict) -> str:
        """Generate actuarial grade HTML reports"""
        
        # Extract basic data
        title = product_data.get('Title', 'Unknown Product')
        brand = product_data.get('Brand', 'N/A')
        current_price = self._safe_float(product_data.get('New: Current', 0))
        rank = self._safe_int(product_data.get('Sales Rank: Current', 0))
        monthly_sales = self._estimate_monthly_sales(rank)
        return_rate = self._parse_percentage(product_data.get('Return Rate', '5%'))
        
        # Build a known cost structure
        cost_structure = self._build_financial_model(current_price, monthly_sales, return_rate, product_data)
        
        # Calculation scenarios based on different COGS ratios
        cogs_scenarios = self._build_cogs_scenarios(current_price, monthly_sales, cost_structure)
        
        # Break-even analysis (The lowest selling price under different COGS)
        breakeven = self._calculate_breakeven_by_cogs(current_price, cost_structure)
        
        # sensitivity analysis (Sensitive to COGS)
        sensitivity = self._calculate_cogs_sensitivity(current_price, cost_structure)
        
        # risk assessment (Based on known costs)
        risks = self._assess_risks_without_cogs(product_data, cost_structure, market_report)
        
        # Generate HTML
        return self._render_html(
            asin=asin,
            title=title,
            brand=brand,
            product_data=product_data,
            factors=factors,
            market_report=market_report,
            cost_structure=cost_structure,
            cogs_scenarios=cogs_scenarios,
            breakeven=breakeven,
            sensitivity=sensitivity,
            risks=risks,
            monthly_sales=monthly_sales
        )
    
    def _build_financial_model(self, price: float, volume: int, return_rate: float, data: dict) -> Dict:
        """Build a known cost structure model (COGS is filled in by the user)"""
        
        # FBA fees (Obtain or estimate from data)
        fba_fee = self._safe_float(data.get('FBA Pick&Pack Fee', 0))
        if fba_fee == 0:
            weight_g = self._safe_float(data.get('Package: Weight (g)', 0))
            if weight_g > 0:
                fba_fee = self._estimate_fba_fee(weight_g)
            else:
                fba_fee = 3.50  # Default estimate
        
        # Commission
        referral_rate = self._safe_float(data.get('Referral Fee %', 15)) / 100
        referral_fee = price * referral_rate
        
        # return cost
        return_cost = price * return_rate * self.return_loss_rate
        
        # Storage fee
        storage_cost = self._calculate_storage_cost(data)
        
        # Advertising fees (Press ACOS)
        ad_cost = price * self.acos_default
        
        # Known operating costs (COGS free)
        known_operating_cost = fba_fee + referral_fee + return_cost + storage_cost + ad_cost
        
        # Assume COGS occupancy (User needs to fill in the actual value)
        placeholder_cogs = price * 0.35  # Only as a reference placeholder and not used in final calculations
        
        # total cost (Includes placeholder COGS)
        total_cost_with_placeholder = placeholder_cogs + known_operating_cost
        
        return {
            'selling_price': price,
            'cogs_placeholder': placeholder_cogs,  # Reference only
            'fba_fee': fba_fee,
            'referral_fee': referral_fee,
            'return_cost': return_cost,
            'storage_cost': storage_cost,
            'ad_cost': ad_cost,
            'known_operating_cost': known_operating_cost,
            'total_cost_placeholder': total_cost_with_placeholder,
            'referral_rate': referral_rate,
            'return_rate': return_rate,
        }
    
    def _build_cogs_scenarios(self, price: float, volume: int, cost_structure: Dict) -> List[Dict]:
        """Calculate profit scenarios based on different COGS ratios"""
        scenarios = []
        
        known_cost = cost_structure['known_operating_cost']
        
        # Different COGS ratio scenarios
        cogs_rates = [
            (0.20, "Low COGS (20%)", "Quality supply chain"),
            (0.30, "Medium to low COGS (30%)", "good supply chain"),
            (0.40, "Medium COGS (40%)", "Ordinary supply chain"),
            (0.50, "Medium to high COGS (50%)", "Poor supply chain"),
            (0.60, "High COGS (60%)", "Need to optimize supply chain"),
        ]
        
        for cogs_rate, label, desc in cogs_rates:
            cogs = price * cogs_rate
            total_cost = cogs + known_cost
            profit = price - total_cost
            margin = (profit / price * 100) if price > 0 else 0
            
            monthly_profit = profit * volume
            monthly_revenue = price * volume
            
            scenarios.append({
                'cogs_rate': cogs_rate,
                'cogs_amount': cogs,
                'label': label,
                'description': desc,
                'total_cost': total_cost,
                'unit_profit': profit,
                'net_margin': margin,
                'monthly_profit': monthly_profit,
                'monthly_revenue': monthly_revenue,
                'is_viable': margin > 10,  # 10%The above profit margin is considered feasible
            })
        
        return scenarios
    
    def _calculate_breakeven_by_cogs(self, price: float, cost_structure: Dict) -> Dict:
        """Calculate break-even under different COGS"""
        known_cost = cost_structure['known_operating_cost']
        
        # The lowest selling price under different COGS
        breakeven_prices = {}
        for cogs_rate in [0.20, 0.30, 0.40, 0.50]:
            cogs = price * cogs_rate
            breakeven_price = cogs + known_cost
            breakeven_prices[cogs_rate] = breakeven_price
        
        return {
            'known_operating_cost': known_cost,
            'breakeven_by_cogs': breakeven_prices,
            'current_price': price,
            'safety_margin': {},  # will be calculated at render time
        }
    
    def _calculate_cogs_sensitivity(self, price: float, cost_structure: Dict) -> Dict:
        """COGS sensitivity analysis"""
        known_cost = cost_structure['known_operating_cost']
        base_cogs_rate = 0.35
        base_cogs = price * base_cogs_rate
        base_profit = price - base_cogs - known_cost
        
        sensitivities = []
        
        # COGS from 20%to 60%change
        for cogs_rate in [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
            cogs = price * cogs_rate
            total_cost = cogs + known_cost
            profit = price - total_cost
            margin = (profit / price * 100) if price > 0 else 0
            
            profit_change = ((profit - base_profit) / base_profit * 100) if base_profit != 0 else 0
            
            status = "🟢 Health" if margin > 15 else "🟡 Average" if margin > 5 else "🔴 Danger"
            
            sensitivities.append({
                'cogs_rate': cogs_rate,
                'cogs_amount': cogs,
                'unit_profit': profit,
                'net_margin': margin,
                'change_from_base': profit_change,
                'status': status,
            })
        
        return {
            'base_cogs_rate': base_cogs_rate,
            'base_profit': base_profit,
            'sensitivities': sensitivities,
        }
    
    def _calculate_breakeven(self, financial: FinancialModel) -> Dict:
        """Calculate break-even"""
        # unit breakeven (The selling price has been determined, it depends on the minimum sales volume required)
        fixed_costs_per_month = 0  # Assume no fixed costs
        contribution_margin = financial.gross_profit
        
        breakeven_units = 0
        if contribution_margin > 0:
            breakeven_units = int(fixed_costs_per_month / contribution_margin) + 1
        
        # price breakeven (Given the sales volume, look at the lowest selling price)
        target_volume = 100  # Assume monthly sales of 100 pieces
        min_price = financial.total_cost
        
        return {
            'breakeven_units': breakeven_units,
            'contribution_margin': contribution_margin,
            'min_viable_price': min_price,
            'target_volume': target_volume,
        }
    
    def _calculate_sensitivity(self, financial: FinancialModel) -> Dict:
        """sensitivity analysis"""
        base_profit = financial.gross_profit
        base_margin = financial.net_margin
        
        sensitivities = []
        
        # Price change ±10%
        for delta in [-0.10, -0.05, 0, 0.05, 0.10]:
            new_price = financial.selling_price * (1 + delta)
            new_profit = new_price - financial.total_cost + (financial.selling_price - new_price) * 0.15  # Commission changes
            new_margin = (new_profit / new_price * 100) if new_price > 0 else 0
            profit_change = ((new_profit - base_profit) / base_profit * 100) if base_profit != 0 else 0
            
            sensitivities.append({
                'variable': f'price {delta*100:+.0f}%',
                'value': new_price,
                'profit': new_profit,
                'margin': new_margin,
                'change': profit_change
            })
        
        # COGS variation ±10%
        for delta in [-0.10, 0, 0.10]:
            new_cogs = financial.cogs_estimate * (1 + delta)
            new_total = new_cogs + financial.fba_fee + financial.referral_fee + financial.return_cost + financial.storage_cost + financial.ad_cost
            new_profit = financial.selling_price - new_total
            new_margin = (new_profit / financial.selling_price * 100) if financial.selling_price > 0 else 0
            profit_change = ((new_profit - base_profit) / base_profit * 100) if base_profit != 0 else 0
            
            sensitivities.append({
                'variable': f'COGS {delta*100:+.0f}%',
                'value': new_cogs,
                'profit': new_profit,
                'margin': new_margin,
                'change': profit_change
            })
        
        return {
            'base_profit': base_profit,
            'base_margin': base_margin,
            'sensitivities': sensitivities
        }
    
    def _assess_risks_without_cogs(self, data: dict, cost_structure: Dict, market_report: dict) -> List[Dict]:
        """risk assessment (Without COGS estimate)"""
        risks = []
        price = cost_structure['selling_price']
        known_cost = cost_structure['known_operating_cost']
        
        # Known cost share risk
        known_cost_ratio = known_cost / price if price > 0 else 0
        if known_cost_ratio > 0.50:
            risks.append({
                'type': 'cost_structure',
                'level': 'high',
                'desc': f'It is known that the proportion of operating costs is too high ({known_cost_ratio*100:.1f}%), leaving little space for COGS',
                'mitigation': 'Reduce FBA fees(Small and light plan)Or optimize advertising ACOS'
            })
        
        # Return rate risk
        return_rate = cost_structure['return_rate']
        if return_rate > 0.15:
            risks.append({
                'type': 'returns',
                'level': 'high',
                'desc': f'Return rate is too high ({return_rate*100:.0f}%), seriously eroding profits',
                'mitigation': 'Improve product quality or description'
            })
        elif return_rate > 0.10:
            risks.append({
                'type': 'returns',
                'level': 'medium',
                'desc': f'Return rate is high ({return_rate*100:.0f}%)',
                'mitigation': 'Pay attention to the reason for return'
            })
        
        # Competing risks
        offer_count = self._safe_int(data.get('New Offer Count: Current', 0))
        if offer_count > 15:
            risks.append({
                'type': 'competition',
                'level': 'high',
                'desc': f'Competition is fierce ({offer_count}sellers), the risk of price war is high',
                'mitigation': 'Differentiation or looking for blue ocean'
            })
        
        # Risk of ranking decline
        rank_drops = self._safe_int(data.get('Sales Rank: Drops last 90 days', 0))
        if rank_drops > 40:
            risks.append({
                'type': 'demand',
                'level': 'high',
                'desc': f'Signs of falling demand (90 days ranking drop{rank_drops}Second-rate)',
                'mitigation': 'Pay attention to market trends'
            })
        
        # FBA fee risk
        fba_fee = cost_structure['fba_fee']
        if fba_fee > price * 0.20:
            risks.append({
                'type': 'fba_cost',
                'level': 'medium',
                'desc': f'FBA fees are too high (${fba_fee:.2f})',
                'mitigation': 'Consider small and light plans or self-shipping'
            })
        
        return risks
    
    def _render_html(self, **kwargs) -> str:
        """Render HTML report"""
        asin = kwargs['asin']
        title = kwargs['title']
        cost_structure = kwargs.get('cost_structure', {})
        cogs_scenarios = kwargs.get('cogs_scenarios', [])
        breakeven = kwargs.get('breakeven', {})
        sensitivity = kwargs.get('sensitivity', {})
        risks = kwargs.get('risks', [])
        monthly_sales = kwargs.get('monthly_sales', 0)
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        price = cost_structure.get('selling_price', 0)
        known_cost = cost_structure.get('known_operating_cost', 0)
        
        # Calculate overall score
        factor_score = sum(f.score * f.weight for f in kwargs['factors'].values())
        market_score = kwargs['market_report']['market_feasibility']['overall_score']
        overall = (factor_score + market_score) / 2  # Financial score not included because COGS is unknown
        
        # Decision suggestions (Based on known information)
        if overall >= 70 and known_cost / price < 0.40 if price > 0 else False:
            decision = "🟢 Recommended to consider"
            decision_color = "#4ade80"
            decision_detail = "The market feasibility is good and the operating cost structure is reasonable. The decision can be made after COGS is confirmed."
        elif overall >= 55:
            decision = "🟡 Evaluate carefully"
            decision_color = "#fbbf24"
            decision_detail = "It is feasible to a certain extent and needs to be evaluated after confirming the actual COGS"
        else:
            decision = "🔴 It is recommended to give up"
            decision_color = "#f87171"
            decision_detail = "Insufficient market feasibility or too high operating costs"
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Operations Actuary Analysis Report - {asin}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        
        .header {{
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 25px 80px rgba(0,0,0,0.4);
        }}
        .header h1 {{ font-size: 2.2em; margin-bottom: 15px; font-weight: 700; }}
        .badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 10px;
        }}
        .badge-professional {{ background: rgba(34, 197, 94, 0.3); color: #4ade80; border: 1px solid #4ade80; }}
        
        .card {{
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 25px;
            backdrop-filter: blur(10px);
        }}
        .card-title {{
            font-size: 1.4em;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #60a5fa;
        }}
        
        .cogs-notice {{
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.1));
            border: 2px solid #f59e0b;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .cogs-notice h2 {{ color: #fbbf24; margin-bottom: 15px; }}
        
        .cost-breakdown {{
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            padding: 20px;
        }}
        .cost-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .cost-item:last-child {{ border-bottom: none; }}
        .cost-item.known {{ color: #e2e8f0; }}
        .cost-item.tbd {{ 
            color: #fbbf24; 
            background: rgba(251, 191, 36, 0.1);
            margin: 0 -10px;
            padding: 12px 10px;
            border-radius: 8px;
        }}
        .cost-item.total {{ 
            border-top: 2px solid rgba(255,255,255,0.3); 
            margin-top: 10px; 
            padding-top: 15px;
            font-weight: 600;
        }}
        
        .cogs-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .cogs-table th {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        .cogs-table td {{
            padding: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .cogs-table tr:hover {{ background: rgba(255,255,255,0.05); }}
        .cogs-table .viable {{ color: #4ade80; font-weight: 600; }}
        .cogs-table .risky {{ color: #f87171; }}
        
        .verdict {{
            font-size: 3em;
            font-weight: 700;
            text-align: center;
            margin: 20px 0;
            color: {decision_color};
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }}
        .metric-box {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .risk-item {{
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid #ef4444;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 0 12px 12px 0;
        }}
        .risk-item.medium {{
            background: rgba(245, 158, 11, 0.1);
            border-left-color: #f59e0b;
        }}
        
        .footer {{
            text-align: center;
            padding: 40px;
            opacity: 0.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <span class="badge badge-professional">🏆 Actuary-level analysis</span>
                <span style="opacity: 0.8;">{current_date}</span>
            </div>
            <h1>Amazon Operations Actuary Analysis Report</h1>
            <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 15px;">
                <span>ASIN: {asin}</span>
                <span>brand: {kwargs.get('brand', 'N/A')}</span>
            </div>
            <div style="font-size: 1.1em; opacity: 0.9; line-height: 1.5;">{title}</div>
        </div>
        
        <!-- COGS Notice -->
        <div class="cogs-notice">
            <h2>⚠️ COGS (Procurement cost) To be filled in</h2>
            <p style="font-size: 1.1em; margin-bottom: 15px;">
                This report is based solely on<strong>Known operating costs</strong>The analysis is performed without COGS estimates.
            </p>
            <p style="opacity: 0.9;">
                Please fill in your actual COGS in the form below to see the corresponding profit margin.
                <br>COGS = Product purchase price + First leg freight + tariff + Other arrival costs
            </p>
        </div>
        
        <!-- Executive Summary -->
        <div class="card">
            <h2 class="card-title">💼 Executive Summary</h2>
            <div class="verdict">{decision}</div>
            <p style="text-align: center; font-size: 1.1em; margin-bottom: 30px;">{decision_detail}</p>
            
            <div class="metrics-grid">
                <div class="metric-box">
                    <div class="metric-value" style="color: #60a5fa;">{overall:.0f}</div>
                    <div class="metric-label">Overall rating</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: #fbbf24;">{factor_score:.0f}</div>
                    <div class="metric-label">six-dimensional factor</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: #a78bfa;">{market_score:.0f}</div>
                    <div class="metric-label">market feasibility</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: #fbbf24;">{known_cost/price*100:.1f}%</div>
                    <div class="metric-label">Known cost ratio</div>
                </div>
            </div>
        </div>
        
        <!-- Known Cost Structure -->
        <div class="card">
            <h2 class="card-title">💰 Known cost structure (COGS free)</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                <div>
                    <h3 style="margin-bottom: 20px; color: #94a3b8;">unit operating cost (per piece)</h3>
                    <div class="cost-breakdown">
                        <div class="cost-item known">
                            <span>selling price (Selling Price)</span>
                            <span style="font-weight: 600;">${price:.2f}</span>
                        </div>
                        <div class="cost-item tbd">
                            <span>➖ COGS (To be filled in)</span>
                            <span style="font-weight: 600;">?</span>
                        </div>
                        <div class="cost-item known">
                            <span>➖ FBA fees</span>
                            <span>-${cost_structure.get('fba_fee', 0):.2f}</span>
                        </div>
                        <div class="cost-item known">
                            <span>➖Platform commission ({cost_structure.get('referral_rate', 0.15)*100:.0f}%)</span>
                            <span>-${cost_structure.get('referral_fee', 0):.2f}</span>
                        </div>
                        <div class="cost-item known">
                            <span>➖ Return costs ({cost_structure.get('return_rate', 0.05)*100:.0f}%return rate)</span>
                            <span>-${cost_structure.get('return_cost', 0):.2f}</span>
                        </div>
                        <div class="cost-item known">
                            <span>➖ Storage fee</span>
                            <span>-${cost_structure.get('storage_cost', 0):.3f}</span>
                        </div>
                        <div class="cost-item known">
                            <span>➖ Advertising fees (ACoS 15%)</span>
                            <span>-${cost_structure.get('ad_cost', 0):.2f}</span>
                        </div>
                        <div class="cost-item total">
                            <span>Total known operating costs</span>
                            <span style="color: #f87171;">${known_cost:.2f}</span>
                        </div>
                        <div class="cost-item" style="background: rgba(251, 191, 36, 0.1); border-radius: 8px; padding: 15px; margin-top: 10px;">
                            <span style="color: #fbbf24; font-weight: 600;">COGS cap space</span>
                            <span style="color: #fbbf24; font-weight: 600;">${price - known_cost:.2f} (highest{(price-known_cost)/price*100:.0f}%)</span>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h3 style="margin-bottom: 20px; color: #94a3b8;">Monthly operating data</h3>
                    <div class="cost-breakdown">
                        <div class="cost-item">
                            <span>Estimated monthly sales</span>
                            <span style="font-weight: 600;">{monthly_sales} pieces</span>
                        </div>
                        <div class="cost-item">
                            <span>monthly sales (Gross Revenue)</span>
                            <span>${price * monthly_sales:,.2f}</span>
                        </div>
                        <div class="cost-item">
                            <span>Monthly known operating costs</span>
                            <span style="color: #f87171;">${known_cost * monthly_sales:,.2f}</span>
                        </div>
                        <div class="cost-item" style="background: rgba(251, 191, 36, 0.1); border-radius: 8px; padding: 15px; margin-top: 10px;">
                            <span style="color: #fbbf24; font-weight: 600;">Monthly COGS upper limit</span>
                            <span style="color: #fbbf24; font-weight: 600;">${(price - known_cost) * monthly_sales:,.2f}</span>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <h4 style="margin-bottom: 10px; color: #94a3b8;">key indicators</h4>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Known cost ratio</span>
                            <span style="font-weight: 600;">{known_cost/price*100:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Space left for COGS</span>
                            <span style="font-weight: 600; color: #fbbf24;">{((price-known_cost)/price*100) if price > 0 else 0:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>To reach 15%net profit margin</span>
                            <span style="font-weight: 600; color: #4ade80;">
                                COGS needs to be ≤${price*0.70-known_cost:.2f} (≤{(price*0.70-known_cost)/price*100:.0f}%)
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- COGS Scenarios -->
        <div class="card">
            <h2 class="card-title">📊 Profit analysis under different COGS ratios</h2>
            <p style="color: #94a3b8; margin-bottom: 20px;">Fill in your actual COGS ratio to view the corresponding financial performance</p>
            
            <div style="overflow-x: auto;">
                <table class="cogs-table">
                    <thead>
                        <tr>
                            <th>COGS ratio</th>
                            <th>COGS amount</th>
                            <th>total cost</th>
                            <th>unit profit</th>
                            <th>net profit margin</th>
                            <th>monthly profit</th>
                            <th>Feasibility</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._render_cogs_scenarios(cogs_scenarios, monthly_sales)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Breakeven Analysis -->
        <div class="card">
            <h2 class="card-title">📈 Break-even analysis</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                    <h4 style="margin-bottom: 15px; color: #94a3b8;">The lowest selling price under different COGS</h4>
                    {self._render_breakeven_prices(breakeven)}
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                    <h4 style="margin-bottom: 15px; color: #94a3b8;">Current pricing margin of safety</h4>
                    <div style="line-height: 2;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>Current selling price</span>
                            <span style="font-weight: 600;">${price:.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Known operating costs</span>
                            <span style="color: #f87171;">${known_cost:.2f}</span>
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.2); margin: 10px 0; padding-top: 10px; display: flex; justify-content: space-between;">
                            <span>COGS cap space</span>
                            <span style="color: #fbbf24; font-weight: 600;">${price - known_cost:.2f}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Risk Assessment -->
        <div class="card">
            <h2 class="card-title">⚠️ Known cost structure risk assessment</h2>
            {self._render_risks(risks)}
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>This report is generated based on known data from Keepa API | Does not include COGS estimates</p>
            <p style="margin-top: 10px; opacity: 0.7; font-size: 0.9em;">
                © 2026 Amz-Keepa-MCP | Please fill in the actual COGS before making an investment decision
            </p>
        </div>
    </div>
</body>
</html>'''
        
        return html
    
    def _render_cogs_scenarios(self, scenarios: List[Dict], monthly_sales: int) -> str:
        """Render COGS scenario table"""
        html = ''
        for s in scenarios:
            viable_class = 'viable' if s['is_viable'] else 'risky'
            html += f'''
                <tr class="{viable_class}">
                    <td>{s['label']}</td>
                    <td>${s['cogs_amount']:.2f}</td>
                    <td>${s['total_cost']:.2f}</td>
                    <td>${s['unit_profit']:.2f}</td>
                    <td>{s['net_margin']:.1f}%</td>
                    <td>${s['monthly_profit']:,.0f}</td>
                    <td>{'✅ feasible' if s['is_viable'] else '⚠️ Risk'}</td>
                </tr>
            '''
        return html
    
    def _render_breakeven_prices(self, breakeven: Dict) -> str:
        """Render breakeven price"""
        html = '<div style="line-height: 2;">'
        for cogs_rate, price in breakeven.get('breakeven_by_cogs', {}).items():
            html += f'''
                <div style="display: flex; justify-content: space-between;">
                    <span>COGS {cogs_rate*100:.0f}%time</span>
                    <span style="font-weight: 600;">lowest selling price ${price:.2f}</span>
                </div>
            '''
        html += '</div>'
        return html
    
    def _render_risks(self, risks: List[Dict]) -> str:
        """Render risk items"""
        if not risks:
            return '<p style="color: #4ade80;">✅ No risks based on known costs found</p>'
        
        html = ''
        for risk in risks:
            level_class = '' if risk['level'] == 'high' else 'medium'
            html += f'''
                <div class="risk-item {level_class}">
                    <div style="font-weight: 600; color: #fca5a5; margin-bottom: 8px;">
                        {risk['type'].upper()} - {risk['level'].upper()}
                    </div>
                    <p style="margin-bottom: 10px;">{risk['desc']}</p>
                    <p style="opacity: 0.8; font-size: 0.9em;"><strong>Mitigation measures:</strong> {risk.get('mitigation', '')}</p>
                </div>
            '''
        return html
    
    def _estimate_monthly_sales(self, rank: int) -> int:
        """Estimated monthly sales based on ranking"""
        if rank < 1000:
            return 1000 + int((1000 - rank) * 5)
        elif rank < 10000:
            return 500 + int((10000 - rank) * 0.05)
        elif rank < 50000:
            return 100 + int((50000 - rank) * 0.01)
        elif rank < 100000:
            return 20 + int((100000 - rank) * 0.002)
        else:
            return max(5, int(500000 / rank))
    
    def _estimate_fba_fee(self, weight_g: float) -> float:
        """Estimate FBA fees"""
        weight_lb = weight_g / 453.592
        if weight_lb < 1:
            return 3.22
        elif weight_lb < 2:
            return 4.71
        else:
            return 4.71 + (weight_lb - 1) * 0.50
    
    def _calculate_storage_cost(self, data: dict) -> float:
        """Calculate storage fees"""
        length = self._safe_float(data.get('Package: Length (cm)', 0)) / 2.54  # Turn inches
        width = self._safe_float(data.get('Package: Width (cm)', 0)) / 2.54
        height = self._safe_float(data.get('Package: Height (cm)', 0)) / 2.54
        
        if length > 0 and width > 0 and height > 0:
            volume_cuft = (length * width * height) / 1728
            return volume_cuft * self.storage_rate_per_cuft
        return 0.05
    
    def _parse_percentage(self, val) -> float:
        """parse percentage"""
        if isinstance(val, str):
            val = val.replace('%', '').strip()
        try:
            return float(val) / 100
        except:
            return 0.05
    
    def _safe_float(self, val) -> float:
        """Convert safely to float"""
        try:
            if val is None:
                return 0.0
            if isinstance(val, str):
                val = val.replace('$', '').replace(',', '').strip()
            return float(val)
        except:
            return 0.0
    
    def _safe_int(self, val) -> int:
        """safe transfer to int"""
        try:
            if val is None:
                return 0
            return int(float(val))
        except:
            return 0


def generate_actuary_report(asin: str,
                           product_data: dict,
                           factors: dict,
                           market_report: dict,
                           output_path: str):
    """Convenience function: generate actuary report"""
    generator = ActuaryReportGenerator()
    html = generator.generate_actuary_report(asin, product_data, factors, market_report)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path
