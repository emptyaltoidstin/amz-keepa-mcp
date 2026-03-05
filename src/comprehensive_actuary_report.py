"""
Amazon Operations Actuary - Ultimate Integrated Reporting
==================================
A complete report that integrates all variant data, real COGS, and order source analysis
"""

import json
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class VariantDetail:
    """Variant detailed metrics"""
    # Basic information
    asin: str
    parent_asin: str
    title: str
    color: str
    size: str
    image_url: str
    
    # price data
    current_price: float
    avg_30d_price: float
    lowest_price: float
    highest_price: float
    
    # sales data
    sales_rank: int
    estimated_monthly_sales: int
    sales_trend: str  # up/down/stable
    bought_in_past_month: int
    
    # Evaluation data
    rating: float
    review_count: int
    review_velocity: int  # New reviews per month
    
    # cost structure (Real data entered by the user)
    cogs: float  # true purchase cost
    fba_fee: float
    referral_fee_rate: float
    return_rate: float
    storage_fee: float
    
    # Order source (Real data obtained from the advertising backend)
    organic_order_pct: float
    ad_order_pct: float
    
    # Competitive data
    offer_count: int
    amazon_present: bool
    buy_box_seller: str
    
    # Inventory data
    stock_status: str
    inventory_level: int
    
    # Calculated field
    @property
    def referral_fee(self) -> float:
        return self.current_price * self.referral_fee_rate
    
    @property
    def return_cost(self) -> float:
        return self.current_price * self.return_rate * 0.30
    
    def calculate_ad_cost_per_unit(self, tacos_rate: float = 0.15) -> float:
        """Calculate unit advertising costs (Based on TACOS)
        
        TACOS (Total ACOS) = total advertising spend / total sales
        
        Correct way to calculate:
        - Variation Monthly Advertising Budget = Variant Monthly Sales × TACOS
        - unit advertising cost = Variation Monthly Advertising Budget / Monthly advertising orders
        
        Args:
            tacos_rate: TACOS target (Default 15%)
        
        Returns:
            Advertising cost per insertion order
        """
        monthly_revenue = self.monthly_revenue
        monthly_ad_budget = monthly_revenue * tacos_rate
        monthly_ad_orders = self.estimated_monthly_sales * self.ad_order_pct
        
        if monthly_ad_orders > 0:
            return monthly_ad_budget / monthly_ad_orders
        else:
            return 0
    
    @property
    def total_operating_cost(self) -> float:
        """total operating costs (Free of COGS and ads)"""
        return self.fba_fee + self.referral_fee + self.return_cost + self.storage_fee
    
    @property
    def contribution_margin_organic(self) -> float:
        """Natural orders contribute to gross profit"""
        return self.current_price - self.cogs - self.total_operating_cost
    
    @property
    def contribution_margin_ad(self) -> float:
        """Insertion order contribution margin (Deduct TACOS advertising fees)"""
        return self.contribution_margin_organic - self.calculate_ad_cost_per_unit()
    
    @property
    def blended_margin(self) -> float:
        """mixed profit margin"""
        organic_profit = self.contribution_margin_organic * self.organic_order_pct
        ad_profit = self.contribution_margin_ad * self.ad_order_pct
        total_profit = organic_profit + ad_profit
        return (total_profit / self.current_price * 100) if self.current_price > 0 else 0
    
    @property
    def monthly_revenue(self) -> float:
        return self.current_price * self.estimated_monthly_sales
    
    @property
    def monthly_profit_organic(self) -> float:
        sales = self.estimated_monthly_sales * self.organic_order_pct
        return self.contribution_margin_organic * sales
    
    @property
    def monthly_profit_ad(self) -> float:
        sales = self.estimated_monthly_sales * self.ad_order_pct
        return self.contribution_margin_ad * sales
    
    @property
    def monthly_total_profit(self) -> float:
        return self.monthly_profit_organic + self.monthly_profit_ad
    
    @property
    def profit_health(self) -> str:
        """profit health"""
        if self.blended_margin > 20:
            return "excellent"
        elif self.blended_margin > 10:
            return "good"
        elif self.blended_margin > 0:
            return "marginal"
        else:
            return "loss"


@dataclass
class LinkSummary:
    """Linked summary data"""
    parent_asin: str
    total_variants: int
    active_variants: int
    
    # Sales summary
    total_monthly_sales: int
    total_monthly_revenue: float
    total_monthly_profit: float
    
    # Order source
    organic_sales_pct: float
    ad_sales_pct: float
    organic_profit: float
    ad_profit: float
    
    # profit margin
    blended_margin: float
    organic_margin: float
    ad_margin: float
    
    # Pareto analysis
    pareto_variants: List[str]  # Contribute 80%sales volume variations
    top_3_variants: List[str]
    
    # Risk warning
    loss_variants: List[str]
    high_ad_dependency: List[str]  # advertising dependence>60%Variants of
    
    # opportunity
    growth_opportunities: List[str]  # Variants with growth potential


class ComprehensiveActuaryReport:
    """Comprehensive Actuarial Report Generator"""
    
    def __init__(self):
        self.storage_rate = 0.87  # $/cu.ft/month
        
    def generate_report(self,
                       parent_asin: str,
                       variants: List[VariantDetail],
                       output_path: str):
        """Generate comprehensive reports"""
        
        # Calculate link summary
        summary = self._calculate_summary(parent_asin, variants)
        
        # Generate HTML
        html = self._render_html(parent_asin, variants, summary)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path, summary
    
    def _calculate_summary(self, parent_asin: str, variants: List[VariantDetail]) -> LinkSummary:
        """Calculate linked summary data"""
        if not variants:
            return LinkSummary(
                parent_asin=parent_asin,
                total_variants=0, active_variants=0,
                total_monthly_sales=0, total_monthly_revenue=0, total_monthly_profit=0,
                organic_sales_pct=0, ad_sales_pct=0,
                organic_profit=0, ad_profit=0,
                blended_margin=0, organic_margin=0, ad_margin=0,
                pareto_variants=[], top_3_variants=[],
                loss_variants=[], high_ad_dependency=[], growth_opportunities=[]
            )
        
        # Sort by sales
        sorted_variants = sorted(variants, key=lambda x: x.estimated_monthly_sales, reverse=True)
        
        total_sales = sum(v.estimated_monthly_sales for v in variants)
        total_revenue = sum(v.monthly_revenue for v in variants)
        
        # Pareto analysis
        sales_accumulated = 0
        pareto_threshold = total_sales * 0.80
        pareto_variants = []
        for v in sorted_variants:
            sales_accumulated += v.estimated_monthly_sales
            pareto_variants.append(v.asin)
            if sales_accumulated >= pareto_threshold:
                break
        
        top_3 = [v.asin for v in sorted_variants[:3]]
        
        # summary natural/advertise
        total_organic_profit = sum(v.monthly_profit_organic for v in variants)
        total_ad_profit = sum(v.monthly_profit_ad for v in variants)
        total_profit = total_organic_profit + total_ad_profit
        
        organic_revenue = sum(v.monthly_revenue * v.organic_order_pct for v in variants)
        ad_revenue = sum(v.monthly_revenue * v.ad_order_pct for v in variants)
        
        # profit margin
        organic_margin = (total_organic_profit / organic_revenue * 100) if organic_revenue > 0 else 0
        ad_margin = (total_ad_profit / ad_revenue * 100) if ad_revenue > 0 else 0
        blended_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Risk identification
        loss_variants = [v.asin for v in variants if v.blended_margin <= 0]
        high_ad_dependency = [v.asin for v in variants if v.ad_order_pct > 0.60]
        
        # growth opportunities (Average sales but good reviews)
        growth_opportunities = [
            v.asin for v in variants 
            if 50 < v.estimated_monthly_sales < 500 and v.rating >= 4.3
        ]
        
        return LinkSummary(
            parent_asin=parent_asin,
            total_variants=len(variants),
            active_variants=len([v for v in variants if v.estimated_monthly_sales > 0]),
            total_monthly_sales=total_sales,
            total_monthly_revenue=total_revenue,
            total_monthly_profit=total_profit,
            organic_sales_pct=(organic_revenue/total_revenue*100) if total_revenue > 0 else 0,
            ad_sales_pct=(ad_revenue/total_revenue*100) if total_revenue > 0 else 0,
            organic_profit=total_organic_profit,
            ad_profit=total_ad_profit,
            blended_margin=blended_margin,
            organic_margin=organic_margin,
            ad_margin=ad_margin,
            pareto_variants=pareto_variants,
            top_3_variants=top_3,
            loss_variants=loss_variants,
            high_ad_dependency=high_ad_dependency,
            growth_opportunities=growth_opportunities
        )
    
    def _render_html(self, parent_asin: str, variants: List[VariantDetail], summary: LinkSummary) -> str:
        """Render HTML report"""
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Decision suggestions
        if summary.blended_margin > 20 and summary.organic_sales_pct > 60:
            verdict = "🟢 Highly recommended"
            verdict_color = "#4ade80"
            verdict_detail = "High profit margins and a healthy proportion of organic traffic"
        elif summary.blended_margin > 10:
            verdict = "🟡 Consider carefully"
            verdict_color = "#fbbf24"
            verdict_detail = "The profit margin is acceptable, but we need to pay attention to advertising dependence"
        else:
            verdict = "🔴 It is recommended to give up"
            verdict_color = "#f87171"
            verdict_detail = "Profit rate is too low or risk of loss is high"
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Link Actuary Analysis Report - {parent_asin}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border-radius: 24px;
            padding: 50px;
            margin-bottom: 30px;
            box-shadow: 0 25px 80px rgba(0,0,0,0.4);
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 20px; font-weight: 800; }}
        .header-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 0.9em;
            margin-right: 15px;
            backdrop-filter: blur(10px);
        }}
        
        /* Executive Summary */
        .exec-summary {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.1));
            border: 2px solid rgba(59, 130, 246, 0.3);
            border-radius: 24px;
            padding: 50px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .verdict {{
            font-size: 4em;
            font-weight: 800;
            color: {verdict_color};
            margin: 30px 0;
            text-shadow: 0 0 60px {verdict_color}40;
        }}
        
        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s;
        }}
        .metric-card:hover {{ transform: translateY(-5px); }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .metric-label {{ opacity: 0.7; font-size: 0.95em; }}
        .metric-sublabel {{ opacity: 0.5; font-size: 0.8em; margin-top: 5px; }}
        
        /* Cards */
        .card {{
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 35px;
            margin-bottom: 25px;
            backdrop-filter: blur(10px);
        }}
        .card-title {{
            font-size: 1.6em;
            font-weight: 600;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: #60a5fa;
        }}
        
        /* Comparison Cards */
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }}
        @media (max-width: 900px) {{ .comparison-grid {{ grid-template-columns: 1fr; }} }}
        
        .comp-card {{
            border-radius: 16px;
            padding: 30px;
        }}
        .comp-organic {{
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05));
            border: 2px solid rgba(34, 197, 94, 0.3);
        }}
        .comp-ad {{
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05));
            border: 2px solid rgba(245, 158, 11, 0.3);
        }}
        
        /* Variant Table */
        .variant-section {{
            overflow-x: auto;
            border-radius: 16px;
            background: rgba(0,0,0,0.2);
        }}
        .variant-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.85em;
            min-width: 1400px;
        }}
        .variant-table th {{
            background: rgba(255,255,255,0.1);
            padding: 16px 12px;
            text-align: center;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        .variant-table td {{
            padding: 16px 12px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .variant-table tr:hover {{ background: rgba(255,255,255,0.05); }}
        
        /* Variant Row Styles */
        .row-top {{ background: rgba(34, 197, 94, 0.1); }}
        .row-pareto {{ background: rgba(59, 130, 246, 0.1); }}
        .row-loss {{ background: rgba(239, 68, 68, 0.1); }}
        .row-high-ad {{ background: rgba(245, 158, 11, 0.1); }}
        
        /* Profit Colors */
        .profit-excellent {{ color: #4ade80; font-weight: 700; }}
        .profit-good {{ color: #22d3ee; }}
        .profit-marginal {{ color: #fbbf24; }}
        .profit-loss {{ color: #f87171; font-weight: 700; }}
        
        /* Order Source Bar */
        .order-bar {{
            width: 100px;
            height: 28px;
            border-radius: 14px;
            overflow: hidden;
            display: flex;
            margin: 0 auto;
        }}
        .organic-segment {{
            background: linear-gradient(90deg, #22c55e, #4ade80);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75em;
            font-weight: 700;
            color: #000;
            min-width: 30px;
        }}
        .ad-segment {{
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75em;
            font-weight: 700;
            color: #000;
            min-width: 30px;
        }}
        
        /* Insight Boxes */
        .insight-box {{
            background: rgba(251, 191, 36, 0.1);
            border-left: 4px solid #fbbf24;
            padding: 25px;
            margin: 25px 0;
            border-radius: 0 12px 12px 0;
        }}
        .insight-box h4 {{ color: #fbbf24; margin-bottom: 12px; }}
        
        .alert-box {{
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid #ef4444;
            padding: 25px;
            margin: 25px 0;
            border-radius: 0 12px 12px 0;
        }}
        .alert-box h4 {{ color: #f87171; margin-bottom: 12px; }}
        
        .success-box {{
            background: rgba(34, 197, 94, 0.1);
            border-left: 4px solid #22c55e;
            padding: 25px;
            margin: 25px 0;
            border-radius: 0 12px 12px 0;
        }}
        .success-box h4 {{ color: #4ade80; margin-bottom: 12px; }}
        
        /* Legend */
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
            font-size: 0.9em;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        /* Section Headers */
        .section-header {{
            font-size: 1.3em;
            font-weight: 600;
            margin: 35px 0 20px 0;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(255,255,255,0.1);
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 50px;
            opacity: 0.6;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: 50px;
        }}
        
        /* Tooltip */
        .tooltip {{
            position: relative;
            cursor: help;
            border-bottom: 1px dashed rgba(255,255,255,0.3);
        }}
        
        /* Print Styles */
        @media print {{
            body {{ background: white; color: black; }}
            .header {{ background: #f0f0f0; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                <div>
                    <span class="header-badge">🏆 Actuary-level analysis</span>
                    <span class="header-badge">📊 Full variant coverage</span>
                    <span class="header-badge">✅ Real COGS</span>
                </div>
                <span style="opacity: 0.8; font-size: 0.95em;">{current_date}</span>
            </div>
            <h1>Amazon Link Operations Actuary Report</h1>
            <div style="font-size: 1.2em; opacity: 0.95;">
                Parent ASIN: <strong>{parent_asin}</strong> | 
                number of variants: <strong>{summary.total_variants}</strong> | 
                Analysis date: {current_date}
            </div>
        </div>
        
        <!-- Executive Summary -->
        <div class="exec-summary">
            <h2 style="font-size: 1.8em; margin-bottom: 10px;">💼 Executive Summary and Investment Decisions</h2>
            <div class="verdict">{verdict}</div>
            <p style="font-size: 1.2em; margin-bottom: 40px;">{verdict_detail}</p>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value" style="color: #60a5fa;">{summary.total_monthly_sales:,}</div>
                    <div class="metric-label">Estimated total monthly sales</div>
                    <div class="metric-sublabel">Total of all variants</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #a78bfa;">${summary.total_monthly_revenue:,.0f}</div>
                    <div class="metric-label">Estimated monthly sales</div>
                    <div class="metric-sublabel">Gross Revenue</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #4ade80;">${summary.total_monthly_profit:,.0f}</div>
                    <div class="metric-label">Estimated monthly net profit</div>
                    <div class="metric-sublabel">deduct all costs</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: {'#4ade80' if summary.blended_margin > 20 else '#fbbf24' if summary.blended_margin > 10 else '#f87171'};">
                        {summary.blended_margin:.1f}%
                    </div>
                    <div class="metric-label">Mixed net profit margin</div>
                    <div class="metric-sublabel">nature+ad weighting</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #22c55e;">{summary.organic_sales_pct:.0f}%</div>
                    <div class="metric-label">Proportion of natural orders</div>
                    <div class="metric-sublabel">No advertising fee</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #f59e0b;">{len(summary.pareto_variants)}</div>
                    <div class="metric-label">Number of core variants</div>
                    <div class="metric-sublabel">Contribute 80%Sales volume</div>
                </div>
            </div>
        </div>
        
        <!-- Organic vs Ad Analysis -->
        <div class="card">
            <h2 class="card-title">🌿🎯 In-depth comparison of natural orders vs advertising orders</h2>
            
            <div class="comparison-grid">
                <div class="comp-card comp-organic">
                    <h3 style="font-size: 1.4em; color: #4ade80; margin-bottom: 25px;">🌿 Natural order analysis</h3>
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>Revenue proportion</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">{summary.organic_sales_pct:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>Monthly profit contribution</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">${summary.organic_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>average profit margin</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">{summary.organic_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.9; line-height: 1.8;">
                        There is no need to pay advertising fees for organic orders, and the profit margin is significantly higher than that of advertising orders.
                        Current natural proportion{summary.organic_sales_pct:.0f}%Belong to{"Excellent" if summary.organic_sales_pct > 60 else "good" if summary.organic_sales_pct > 50 else "Need to improve"}level.
                    </p>
                </div>
                
                <div class="comp-card comp-ad">
                    <h3 style="font-size: 1.4em; color: #fbbf24; margin-bottom: 25px;">🎯 Insertion order analysis</h3>
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>Revenue proportion</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #fbbf24;">{summary.ad_sales_pct:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>Monthly profit contribution</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #fbbf24;">${summary.ad_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>average profit margin</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #fbbf24;">{summary.ad_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.9; line-height: 1.8;">
                        Insertion orders need to allocate advertising costs(TACOS 15%), the profit margin is lower.
                        {"Moderate reliance on advertising" if summary.ad_sales_pct < 40 else "⚠️ High reliance on advertising, need to pay attention to TACOS optimization" if summary.ad_sales_pct < 60 else "🔴 Reliance on advertising is too high and there are risks"}。
                    </p>
                </div>
            </div>
            
            <div class="insight-box">
                <h4>💡 Order source insights</h4>
                <p>
                    Natural order profit margin ({summary.organic_margin:.1f}%) 
                    Than insertion order ({summary.ad_margin:.1f}%) high 
                    <strong>{summary.organic_margin - summary.ad_margin:.1f}percentage points</strong>。
                    Every increase of 1%proportion of natural orders, the monthly profit can be increased by approximately 
                    <strong>${(summary.organic_profit/summary.organic_sales_pct - summary.ad_profit/summary.ad_sales_pct) * summary.total_monthly_sales / 100:.0f}</strong>。
                </p>
            </div>
        </div>
        
        <!-- Pareto Analysis -->
        <div class="card">
            <h2 class="card-title">📈 Pareto analysis (80/Rule of 20)</h2>
            
            <div class="metrics-grid" style="margin-bottom: 25px;">
                <div class="metric-card" style="background: rgba(59, 130, 246, 0.15); border: 2px solid rgba(59, 130, 246, 0.3);">
                    <div class="metric-value" style="color: #60a5fa;">{len(summary.pareto_variants)}</div>
                    <div class="metric-label">core variant</div>
                    <div class="metric-sublabel">Contribute 80%Sales volume</div>
                </div>
                <div class="metric-card" style="background: rgba(245, 158, 11, 0.15); border: 2px solid rgba(245, 158, 11, 0.3);">
                    <div class="metric-value" style="color: #fbbf24;">{len(summary.high_ad_dependency)}</div>
                    <div class="metric-label">High advertising dependence</div>
                    <div class="metric-sublabel">Advertising proportion&gt;60%</div>
                </div>
                <div class="metric-card" style="background: rgba(239, 68, 68, 0.15); border: 2px solid rgba(239, 68, 68, 0.3);">
                    <div class="metric-value" style="color: #f87171;">{len(summary.loss_variants)}</div>
                    <div class="metric-label">loss variant</div>
                    <div class="metric-sublabel">Need immediate attention</div>
                </div>
                <div class="metric-card" style="background: rgba(34, 197, 94, 0.15); border: 2px solid rgba(34, 197, 94, 0.3);">
                    <div class="metric-value" style="color: #4ade80;">{len(summary.growth_opportunities)}</div>
                    <div class="metric-label">growth opportunities</div>
                    <div class="metric-sublabel">Potential variants</div>
                </div>
            </div>
            
            <p style="opacity: 0.9; line-height: 1.8;">
                <strong>Core findings:</strong> before{len(summary.pareto_variants)}variants contributed links 80%of sales.
                Priority should be given to keeping these variants fully stocked and continually optimizing their organic rankings.
                {"Follow at the same time" if len(summary.high_ad_dependency) > 0 else ""} 
                {len(summary.high_ad_dependency)}If you have a high advertising dependency variation, consider increasing the organic proportion through off-site or optimized listings.
            </p>
        </div>
        
        <!-- Variant Details Table -->
        <div class="card">
            <h2 class="card-title">📋 Full variant detailed indicator table</h2>
            
            <div class="legend">
                <div class="legend-item"><div class="legend-dot" style="background: #22c55e;"></div>🔥Top 3 Variations</div>
                <div class="legend-item"><div class="legend-dot" style="background: #3b82f6;"></div>📊 Pareto variant(Contribute 80%)</div>
                <div class="legend-item"><div class="legend-dot" style="background: #f59e0b;"></div>⚠️ High advertising dependence(&gt;60%)</div>
                <div class="legend-item"><div class="legend-dot" style="background: #ef4444;"></div>🔴 Loss variant</div>
            </div>
            
            <div class="variant-section">
                <table class="variant-table">
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>ASIN</th>
                            <th>color/Size</th>
                            <th>price</th>
                            <th>monthly sales</th>
                            <th>sales</th>
                            <th>Order source</th>
                            <th>COGS</th>
                            <th>Contribute gross profit</th>
                            <th>natural profit</th>
                            <th>advertising profit</th>
                            <th>profit margin</th>
                            <th>monthly net profit</th>
                            <th>health</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._render_variant_rows(variants, summary)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Risk Assessment -->
        <div class="card">
            <h2 class="card-title">⚠️Risk assessment and mitigation measures</h2>
            
            {self._render_risk_assessment(summary, variants)}
        </div>
        
        <!-- Action Plan -->
        <div class="card">
            <h2 class="card-title">🎯 30-60-90 day action plan</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;">
                <div style="background: rgba(239, 68, 68, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(239, 68, 68, 0.3);">
                    <h4 style="color: #f87171; margin-bottom: 20px; font-size: 1.2em;">🚨 Act now (0-30 days)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        {f'<li>• Verification{len(summary.loss_variants)}Are the COGS of loss-making variants accurate?</li>' if len(summary.loss_variants) > 0 else ''}
                        <li>• Ensure{len(summary.pareto_variants)}Full inventory of core variants(60 days+)</li>
                        <li>• Optimize the main image and title of high-selling variants to increase natural conversions</li>
                        <li>• Check{len(summary.high_ad_dependency)}TACOS for high ad-dependent variants</li>
                    </ul>
                </div>
                
                <div style="background: rgba(245, 158, 11, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(245, 158, 11, 0.3);">
                    <h4 style="color: #fbbf24; margin-bottom: 20px; font-size: 1.2em;">📈 Short-term optimization (30-60 days)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        <li>• Carry out off-site promotion to reduce TACOS for highly advertising-dependent variants</li>
                        <li>• Test{len(summary.growth_opportunities)}price elasticity of potential variants</li>
                        <li>• Collect and analyze reasons for returns to reduce return rates</li>
                        <li>• Optimize advertising strategy and increase budget for high-profit variants</li>
                    </ul>
                </div>
                
                <div style="background: rgba(34, 197, 94, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(34, 197, 94, 0.3);">
                    <h4 style="color: #4ade80; margin-bottom: 20px; font-size: 1.2em;">🚀 Long-term strategy (60-90 days)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        <li>• Develop new colors/Size variations, copy success patterns</li>
                        <li>• Build supply chain bargaining power and reduce COGS 5-10%</li>
                        <li>• Build a brand moat and increase the proportion of natural traffic to 70%+</li>
                        <li>• Establish a monthly profit monitoring system to detect problem variants in a timely manner</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- Data Source Note -->
        <div class="card" style="background: rgba(251, 191, 36, 0.05); border: 2px solid rgba(251, 191, 36, 0.3);">
            <h2 class="card-title" style="color: #fbbf24;">📊 Data source description</h2>
            <div style="line-height: 2;">
                <p><strong>sales data:</strong> Based on Keepa sales ranking estimation, refer to the average ranking in the past 30 days</p>
                <p><strong>price data:</strong> Current Buy Box price or New price, average</p>
                <p><strong>COGS data:</strong> <span style="color: #fbbf24; font-weight: 600;">Users provide real data</span>, including purchase price, first-way freight and tariffs</p>
                <p><strong>Order source:</strong> <span style="color: #fbbf24; font-weight: 600;">Users provide real data</span>, from Amazon Advertising backend report</p>
                <p><strong>FBA fees:</strong> Get from Keepa API or based on weight/Size calculation</p>
                <p><strong>return rate:</strong> Get the historical return rate of this product from Keepa API</p>
                <p><strong>advertising rate:</strong> Assuming TACOS (Total ACOS) 15%, that is, the total advertising expenditure accounts for 15% of the overall sales%. Please adjust the actual cost according to the background advertising report.</p>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p style="font-size: 1.1em; margin-bottom: 15px;">This report is generated based on real COGS and order source data | data driven decision making</p>
            <p style="opacity: 0.7;">
                © 2026 Amazon Operations Actuary System | All cost data needs to be verified and confirmed by the user<br>
                The report is for reference only. Actual profits are affected by market fluctuations, competition changes and other factors.
            </p>
        </div>
    </div>
</body>
</html>'''
        
        return html
    
    def _render_variant_rows(self, variants: List[VariantDetail], summary: LinkSummary) -> str:
        """Render variant table rows"""
        html = ''
        sorted_variants = sorted(variants, key=lambda x: x.estimated_monthly_sales, reverse=True)
        
        for i, v in enumerate(sorted_variants, 1):
            # Determine row style
            row_classes = []
            if i <= 3:
                row_classes.append('row-top')
            if v.asin in summary.pareto_variants:
                row_classes.append('row-pareto')
            if v.asin in summary.high_ad_dependency:
                row_classes.append('row-high-ad')
            if v.asin in summary.loss_variants:
                row_classes.append('row-loss')
            
            row_class = ' '.join(row_classes)
            
            # Profit Health Style
            profit_class = f'profit-{v.profit_health}'
            
            # health label
            health_label = {
                'excellent': '✅ Excellent',
                'good': '🟢 Good',
                'marginal': '🟡 Average',
                'loss': '🔴 Loss'
            }.get(v.profit_health, '❓ unknown')
            
            html += f'''
                <tr class="{row_class}">
                    <td><strong>#{i}</strong></td>
                    <td>{v.asin}</td>
                    <td>{v.color}<br><small style="opacity:0.7">{v.size}</small></td>
                    <td>${v.current_price:.2f}</td>
                    <td>{v.estimated_monthly_sales:,}</td>
                    <td>${v.monthly_revenue:,.0f}</td>
                    <td>
                        <div class="order-bar">
                            <div class="organic-segment" style="width: {v.organic_order_pct*100}%;">
                                {v.organic_order_pct*100:.0f}%
                            </div>
                            <div class="ad-segment" style="width: {v.ad_order_pct*100}%;">
                                {v.ad_order_pct*100:.0f}%
                            </div>
                        </div>
                    </td>
                    <td>${v.cogs:.2f}</td>
                    <td>${v.contribution_margin_organic:.2f}</td>
                    <td class="profit-positive">${v.contribution_margin_organic:.2f}</td>
                    <td class="{'profit-positive' if v.contribution_margin_ad > 0 else 'profit-loss'}">${v.contribution_margin_ad:.2f}</td>
                    <td class="{profit_class}">{v.blended_margin:.1f}%</td>
                    <td class="{profit_class}">${v.monthly_total_profit:,.0f}</td>
                    <td>{health_label}</td>
                </tr>
            '''
        
        return html
    
    def _render_risk_assessment(self, summary: LinkSummary, variants: List[VariantDetail]) -> str:
        """Rendering risk assessment"""
        html = ''
        
        # Risk 1: loss variant
        if len(summary.loss_variants) > 0:
            html += f'''
                <div class="alert-box">
                    <h4>🔴 Loss variant risk ({len(summary.loss_variants)}a)</h4>
                    <p>The following variants may be loss-making under the current cost structure, please immediately check whether the COGS is accurate, or consider raising the price/Removal:</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(summary.loss_variants)}</p>
                </div>
            '''
        
        # Risk 2: High advertising dependence
        if len(summary.high_ad_dependency) > 0:
            html += f'''
                <div class="insight-box">
                    <h4>⚠️ High risk of advertising dependence ({len(summary.high_ad_dependency)}a)</h4>
                    <p>The following variant insertion orders account for more than 60%, once advertising costs rise or competition intensifies, profits will decline significantly:</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(summary.high_ad_dependency)}</p>
                    <p style="margin-top: 10px;"><strong>Mitigation measures:</strong> Increase the proportion of natural traffic through off-site promotion, social media planting, etc.</p>
                </div>
            '''
        
        # Risk 3: Concentrated sales
        if len(summary.pareto_variants) <= 2 and summary.total_variants >= 5:
            html += f'''
                <div class="insight-box">
                    <h4>⚠️Risk of excessive sales concentration</h4>
                    <p>only{len(summary.pareto_variants)}variants contributed 80%sales volume, the link's ability to resist risks is weak. Once something goes wrong with the core variant(Out of stock, bad reviews, follow-up sales), overall sales will be severely impacted.</p>
                    <p style="margin-top: 10px;"><strong>Mitigation measures:</strong> Balance promotion resources and cultivate second-tier variants; ensure sufficient inventory of core variants and distribution in multiple warehouses.</p>
                </div>
            '''
        
        # opportunity
        if len(summary.growth_opportunities) > 0:
            html += f'''
                <div class="success-box">
                    <h4>🌟 Growth opportunities ({len(summary.growth_opportunities)}a)</h4>
                    <p>The following variants have good reviews but moderate sales, and have the potential to become new growth points:</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(summary.growth_opportunities)}</p>
                    <p style="margin-top: 10px;"><strong>suggestion:</strong> Increase advertising testing, optimize listing images and keywords, and consider participating in deal activities.</p>
                </div>
            '''
        
        if not html:
            html = '<p style="color: #4ade80; font-size: 1.1em;">✅ No obvious risks have been found, and the current operating status is good</p>'
        
        return html


def generate_comprehensive_report(parent_asin: str,
                                 variants: List[VariantDetail],
                                 output_path: str) -> Tuple[str, LinkSummary]:
    """Convenience functions: Generate comprehensive reports"""
    generator = ComprehensiveActuaryReport()
    return generator.generate_report(parent_asin, variants, output_path)
