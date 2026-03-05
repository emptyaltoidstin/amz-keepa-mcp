"""
Amazon Link Variant Profit Analyzer
===========================
Collect all variants under the parent ASIN, and deduce the overall profitability of the link based on real sales distribution and order sources.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class VariantMetrics:
    """Variation indicator"""
    asin: str
    title: str
    color: str
    size: str
    price: float
    sales_rank: int
    estimated_sales: int
    review_count: int
    rating: float
    return_rate: float
    
    # Order source distribution (from real data or estimates)
    organic_order_pct: float = 0.60  # Proportion of natural orders
    ad_order_pct: float = 0.40       # Insertion order proportion
    
    # cost structure
    cogs: float = 0.0
    fba_fee: float = 0.0
    
    @property
    def monthly_revenue(self) -> float:
        return self.price * self.estimated_sales
    
    @property
    def contribution_margin(self) -> float:
        """Contribute gross profit (Does not include advertising fees)"""
        referral_fee = self.price * 0.15
        return_cost = self.price * self.return_rate * 0.30
        storage = 0.05  # Estimate
        return self.price - self.cogs - self.fba_fee - referral_fee - return_cost - storage


@dataclass
class LinkProfitability:
    """Overall link profitability"""
    parent_asin: str
    total_variants: int
    active_variants: int
    
    # Sales volume distribution
    total_monthly_sales: int
    top_3_variants_sales_pct: float
    
    # income structure
    total_monthly_revenue: float
    
    # profit analysis
    blended_organic_margin: float  # Mixed organic order margin
    blended_ad_margin: float       # Mixed insertion order margin
    blended_overall_margin: float  # Overall blended profit margin
    
    # Organic vs Advertising Comparison
    organic_revenue_pct: float
    ad_revenue_pct: float
    organic_profit: float
    ad_profit: float
    
    # Key findings
    pareto_variants: List[str]  # Contribute 80%sales volume variations
    loss_variants: List[str]    # Losing variant


class VariantProfitAnalyzer:
    """Variant Profit Analyzer"""
    
    def __init__(self):
        self.referral_rate = 0.15
        self.return_loss_rate = 0.30
        self.storage_per_unit = 0.05
        
    def analyze_link_profitability(self, 
                                   parent_asin: str,
                                   variants_data: List[Dict],
                                   cogs_map: Optional[Dict[str, float]] = None,
                                   order_source_map: Optional[Dict[str, Tuple[float, float]]] = None
                                   ) -> LinkProfitability:
        """
        Analyze the profitability of the entire link
        
        Args:
            parent_asin: Parent ASIN
            variants_data: Keepa data for all variants
            cogs_map: COGS of each variant {asin: cogs}
            order_source_map: Proportion of order sources for each variant {asin: (organic_pct, ad_pct)}
        
        Returns:
            LinkProfitability Link overall profitability analysis
        """
        # Parse metrics for each variant
        variants = []
        for data in variants_data:
            variant = self._parse_variant_metrics(data)
            
            # Apply custom COGS
            if cogs_map and variant.asin in cogs_map:
                variant.cogs = cogs_map[variant.asin]
            else:
                # Price-based default estimate
                variant.cogs = variant.price * 0.35
            
            # Apply order source ratio
            if order_source_map and variant.asin in order_source_map:
                variant.organic_order_pct, variant.ad_order_pct = order_source_map[variant.asin]
            
            variants.append(variant)
        
        # Sort by sales
        variants.sort(key=lambda x: x.estimated_sales, reverse=True)
        
        # Calculate overall link metrics
        return self._calculate_link_metrics(parent_asin, variants)
    
    def _parse_variant_metrics(self, data: Dict) -> VariantMetrics:
        """Parse variant metrics"""
        return VariantMetrics(
            asin=data.get('asin', ''),
            title=data.get('title', ''),
            color=data.get('color', 'N/A'),
            size=data.get('size', 'N/A'),
            price=self._safe_float(data.get('price', 0)),
            sales_rank=self._safe_int(data.get('sales_rank', 999999)),
            estimated_sales=self._estimate_sales_from_rank(self._safe_int(data.get('sales_rank', 999999))),
            review_count=self._safe_int(data.get('review_count', 0)),
            rating=self._safe_float(data.get('rating', 0)) / 10,
            return_rate=self._parse_return_rate(data.get('return_rate', '5%')),
            fba_fee=self._safe_float(data.get('fba_fee', 3.50))
        )
    
    def _calculate_link_metrics(self, parent_asin: str, variants: List[VariantMetrics]) -> LinkProfitability:
        """Calculate overall link metrics"""
        if not variants:
            return LinkProfitability(
                parent_asin=parent_asin,
                total_variants=0,
                active_variants=0,
                total_monthly_sales=0,
                top_3_variants_sales_pct=0,
                total_monthly_revenue=0,
                blended_organic_margin=0,
                blended_ad_margin=0,
                blended_overall_margin=0,
                organic_revenue_pct=0,
                ad_revenue_pct=0,
                organic_profit=0,
                ad_profit=0,
                pareto_variants=[],
                loss_variants=[]
            )
        
        total_sales = sum(v.estimated_sales for v in variants)
        total_revenue = sum(v.monthly_revenue for v in variants)
        
        # Pareto analysis (80/Rule of 20)
        sales_accumulated = 0
        pareto_threshold = total_sales * 0.80
        pareto_variants = []
        loss_variants = []
        
        for v in variants:
            sales_accumulated += v.estimated_sales
            if sales_accumulated <= pareto_threshold:
                pareto_variants.append(v.asin)
            
            # Check if there is a loss
            if v.contribution_margin <= 0:
                loss_variants.append(v.asin)
        
        top_3_sales = sum(v.estimated_sales for v in variants[:3])
        
        # Calculate weighted average profit margin
        total_organic_profit = 0
        total_ad_profit = 0
        total_organic_revenue = 0
        total_ad_revenue = 0
        
        for v in variants:
            organic_sales = v.estimated_sales * v.organic_order_pct
            ad_sales = v.estimated_sales * v.ad_order_pct
            
            # Natural order profit (No advertising fees)
            organic_profit_per_unit = v.contribution_margin
            total_organic_profit += organic_profit_per_unit * organic_sales
            total_organic_revenue += v.price * organic_sales
            
            # Insertion Order Profit (minus advertising costs)
            ad_cost_per_unit = v.price * 0.15  # ACoS 15%
            ad_profit_per_unit = v.contribution_margin - ad_cost_per_unit
            total_ad_profit += ad_profit_per_unit * ad_sales
            total_ad_revenue += v.price * ad_sales
        
        organic_revenue_pct = (total_organic_revenue / total_revenue * 100) if total_revenue > 0 else 0
        ad_revenue_pct = (total_ad_revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        blended_organic_margin = (total_organic_profit / total_organic_revenue * 100) if total_organic_revenue > 0 else 0
        blended_ad_margin = (total_ad_profit / total_ad_revenue * 100) if total_ad_revenue > 0 else 0
        blended_overall_margin = ((total_organic_profit + total_ad_profit) / total_revenue * 100) if total_revenue > 0 else 0
        
        return LinkProfitability(
            parent_asin=parent_asin,
            total_variants=len(variants),
            active_variants=len([v for v in variants if v.estimated_sales > 0]),
            total_monthly_sales=total_sales,
            top_3_variants_sales_pct=(top_3_sales / total_sales * 100) if total_sales > 0 else 0,
            total_monthly_revenue=total_revenue,
            blended_organic_margin=blended_organic_margin,
            blended_ad_margin=blended_ad_margin,
            blended_overall_margin=blended_overall_margin,
            organic_revenue_pct=organic_revenue_pct,
            ad_revenue_pct=ad_revenue_pct,
            organic_profit=total_organic_profit,
            ad_profit=total_ad_profit,
            pareto_variants=pareto_variants,
            loss_variants=loss_variants
        )
    
    def generate_variant_profit_report(self, 
                                     parent_asin: str,
                                     link_metrics: LinkProfitability,
                                     variants: List[VariantMetrics],
                                     output_path: str):
        """Generate variant profit analysis report"""
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Link variant profit analysis - {parent_asin}</title>
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
        }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        
        .card {{
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 25px;
        }}
        .card-title {{
            font-size: 1.4em;
            margin-bottom: 20px;
            color: #60a5fa;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
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
        .metric-label {{ opacity: 0.7; font-size: 0.9em; }}
        
        .variant-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}
        .variant-table th {{
            background: rgba(255,255,255,0.1);
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        .variant-table td {{
            padding: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .variant-table tr:hover {{ background: rgba(255,255,255,0.05); }}
        
        .profit-positive {{ color: #4ade80; }}
        .profit-negative {{ color: #f87171; }}
        .top-variant {{ background: rgba(34, 197, 94, 0.1); }}
        .loss-variant {{ background: rgba(239, 68, 68, 0.1); }}
        
        .order-source-bar {{
            height: 24px;
            border-radius: 12px;
            overflow: hidden;
            display: flex;
        }}
        .organic-part {{
            background: #22c55e;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .ad-part {{
            background: #f59e0b;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            font-weight: 600;
        }}
        
        .insight-box {{
            background: rgba(251, 191, 36, 0.1);
            border-left: 4px solid #f59e0b;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 10px 10px 0;
        }}
        
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 768px) {{ .comparison-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🔗 Link variant profit analysis report</h1>
            <div style="opacity: 0.9;">Parent ASIN: {parent_asin}</div>
            <div style="margin-top: 15px; display: flex; gap: 20px; flex-wrap: wrap;">
                <span>Total number of variants: {link_metrics.total_variants}</span>
                <span>active variant: {link_metrics.active_variants}</span>
                <span>Pareto variant: {len(link_metrics.pareto_variants)}a(Contribute 80%Sales volume)</span>
            </div>
        </div>
        
        <!-- Executive Summary -->
        <div class="card">
            <h2 class="card-title">💼 Link overall profit overview</h2>
            
            <div class="metrics-grid">
                <div class="metric-box">
                    <div class="metric-value" style="color: #60a5fa;">{link_metrics.total_monthly_sales:,}</div>
                    <div class="metric-label">Estimated total monthly sales</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: #a78bfa;">${link_metrics.total_monthly_revenue:,.0f}</div>
                    <div class="metric-label">Estimated monthly sales</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: {'#4ade80' if link_metrics.blended_overall_margin > 15 else '#fbbf24' if link_metrics.blended_overall_margin > 5 else '#f87171'};">
                        {link_metrics.blended_overall_margin:.1f}%
                    </div>
                    <div class="metric-label">Overall blended profit margin</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: #22c55e;">{link_metrics.organic_revenue_pct:.0f}%</div>
                    <div class="metric-label">Proportion of natural order revenue</div>
                </div>
            </div>
            
            <div class="insight-box">
                <strong>💡 Key findings:</strong> before{len(link_metrics.pareto_variants)}variants contributed 80%sales volume,
                in{len(link_metrics.loss_variants)}Variants may lose money. It is recommended to focus on margin optimization for high-volume variants.
            </div>
        </div>
        
        <!-- Organic vs Ad Comparison -->
        <div class="card">
            <h2 class="card-title">📊 Organic order vs insertion order comparison</h2>
            
            <div class="comparison-grid">
                <div style="background: rgba(34, 197, 94, 0.1); padding: 25px; border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.3);">
                    <h3 style="color: #4ade80; margin-bottom: 20px;">🌿 Natural order ({link_metrics.organic_revenue_pct:.0f}%)</h3>
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>Natural order monthly profit</span>
                            <span style="font-weight: 600; color: #4ade80;">${link_metrics.organic_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Natural order profit margin</span>
                            <span style="font-weight: 600; color: #4ade80;">{link_metrics.blended_organic_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.8; font-size: 0.9em;">Natural orders have no advertising costs and higher profit margins, so focus should be placed on optimizing natural rankings.</p>
                </div>
                
                <div style="background: rgba(245, 158, 11, 0.1); padding: 25px; border-radius: 12px; border: 1px solid rgba(245, 158, 11, 0.3);">
                    <h3 style="color: #fbbf24; margin-bottom: 20px;">🎯 Insertion Order ({link_metrics.ad_revenue_pct:.0f}%)</h3>
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>Insertion order monthly profit</span>
                            <span style="font-weight: 600; color: #fbbf24;">${link_metrics.ad_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Insertion order profit margin</span>
                            <span style="font-weight: 600; color: #fbbf24;">{link_metrics.blended_ad_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.8; font-size: 0.9em;">The profit margin of advertising orders is low, and ACoS needs to be monitored to avoid advertising losses.</p>
                </div>
            </div>
        </div>
        
        <!-- Variant Details -->
        <div class="card">
            <h2 class="card-title">📋 Detailed analysis of variants</h2>
            <p style="color: #94a3b8; margin-bottom: 20px;">
                total{len(variants)}variations, displayed sorted by sales volume
            </p>
            
            <div style="overflow-x: auto;">
                <table class="variant-table">
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>ASIN</th>
                            <th>color/Size</th>
                            <th>price</th>
                            <th>monthly sales</th>
                            <th>Order source</th>
                            <th>Contribute gross profit</th>
                            <th>natural profit</th>
                            <th>advertising profit</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._render_variant_rows(variants)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Recommendations -->
        <div class="card">
            <h2 class="card-title">💡Operation suggestions</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                    <h4 style="color: #4ade80; margin-bottom: 15px;">✅ Act now</h4>
                    <ul style="list-style: none; padding: 0;">
                        <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            1. Verification{len(link_metrics.loss_variants)}COGS of loss-making variants
                        </li>
                        <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            2. Before optimization{len(link_metrics.pareto_variants)}natural ranking of variants
                        </li>
                        <li style="padding: 8px 0;">
                            3. Monitor the ACoS of the insertion order and control it at 15%within
                        </li>
                    </ul>
                </div>
                
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                    <h4 style="color: #fbbf24; margin-bottom: 15px;">⚠️Risk warning</h4>
                    <ul style="list-style: none; padding: 0;">
                        <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            • Proportion of natural orders{link_metrics.organic_revenue_pct:.0f}%，{'good' if link_metrics.organic_revenue_pct > 60 else 'Need to improve'}
                        </li>
                        <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            • Head{link_metrics.top_3_variants_sales_pct:.0f}%Sales volume is concentrated,{'risk concentration' if link_metrics.top_3_variants_sales_pct > 80 else 'Reasonable distribution'}
                        </li>
                        <li style="padding: 8px 0;">
                            • Actual profit depends on real COGS and order source ratio
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def _render_variant_rows(self, variants: List[VariantMetrics]) -> str:
        """Render variant row"""
        html = ''
        for i, v in enumerate(variants, 1):
            # Calculate various profits
            referral = v.price * 0.15
            returns = v.price * v.return_rate * 0.30
            storage = 0.05
            
            contribution = v.price - v.cogs - v.fba_fee - referral - returns - storage
            organic_profit = contribution
            ad_profit = contribution - v.price * 0.15  # minus advertising costs
            
            # row style
            row_class = ''
            status = ''
            if i <= 3:
                row_class = 'top-variant'
                status = '🔥 Top'
            elif contribution <= 0:
                row_class = 'loss-variant'
                status = '⚠️ Loss'
            elif v.estimated_sales > 0:
                status = '✅Normal'
            
            profit_class = 'profit-positive' if contribution > 0 else 'profit-negative'
            
            html += f'''
                <tr class="{row_class}">
                    <td>#{i}</td>
                    <td>{v.asin}</td>
                    <td>{v.color} / {v.size}</td>
                    <td>${v.price:.2f}</td>
                    <td>{v.estimated_sales}</td>
                    <td>
                        <div class="order-source-bar" style="width: 100px;">
                            <div class="organic-part" style="width: {v.organic_order_pct*100}%;">
                                {v.organic_order_pct*100:.0f}%
                            </div>
                            <div class="ad-part" style="width: {v.ad_order_pct*100}%;">
                                {v.ad_order_pct*100:.0f}%
                            </div>
                        </div>
                    </td>
                    <td class="{profit_class}">${contribution:.2f}</td>
                    <td class="profit-positive">${organic_profit:.2f}</td>
                    <td class="{'profit-positive' if ad_profit > 0 else 'profit-negative'}">${ad_profit:.2f}</td>
                    <td>{status}</td>
                </tr>
            '''
        return html
    
    def _estimate_sales_from_rank(self, rank: int) -> int:
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
    
    def _safe_float(self, val) -> float:
        try:
            if val is None:
                return 0.0
            if isinstance(val, str):
                val = val.replace('$', '').replace(',', '').strip()
            return float(val)
        except:
            return 0.0
    
    def _safe_int(self, val) -> int:
        try:
            if val is None:
                return 0
            return int(float(val))
        except:
            return 0
    
    def _parse_return_rate(self, val) -> float:
        try:
            if isinstance(val, str):
                val = val.replace('%', '').strip()
            return float(val) / 100
        except:
            return 0.05
