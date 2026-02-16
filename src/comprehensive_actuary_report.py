"""
亚马逊运营精算师 - 终极综合报告
==================================
整合所有变体数据、真实COGS、订单来源分析的完整报表
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
    """变体详细指标"""
    # 基础信息
    asin: str
    parent_asin: str
    title: str
    color: str
    size: str
    image_url: str
    
    # 价格数据
    current_price: float
    avg_30d_price: float
    lowest_price: float
    highest_price: float
    
    # 销量数据
    sales_rank: int
    estimated_monthly_sales: int
    sales_trend: str  # up/down/stable
    bought_in_past_month: int
    
    # 评价数据
    rating: float
    review_count: int
    review_velocity: int  # 月新增评价
    
    # 成本结构 (用户填入的真实数据)
    cogs: float  # 真实采购成本
    fba_fee: float
    referral_fee_rate: float
    return_rate: float
    storage_fee: float
    
    # 订单来源 (从广告后台获取的真实数据)
    organic_order_pct: float
    ad_order_pct: float
    
    # 竞争数据
    offer_count: int
    amazon_present: bool
    buy_box_seller: str
    
    # 库存数据
    stock_status: str
    inventory_level: int
    
    # 计算字段
    @property
    def referral_fee(self) -> float:
        return self.current_price * self.referral_fee_rate
    
    @property
    def return_cost(self) -> float:
        return self.current_price * self.return_rate * 0.30
    
    def calculate_ad_cost_per_unit(self, tacos_rate: float = 0.15) -> float:
        """计算单位广告成本 (基于TACOS)
        
        TACOS (Total ACOS) = 广告总花费 / 总销售额
        
        正确的计算方式:
        - 变体月广告预算 = 变体月销售额 × TACOS
        - 单位广告成本 = 变体月广告预算 / 月广告订单数
        
        Args:
            tacos_rate: TACOS目标 (默认15%)
        
        Returns:
            每个广告订单的广告成本
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
        """总运营成本 (不含COGS和广告)"""
        return self.fba_fee + self.referral_fee + self.return_cost + self.storage_fee
    
    @property
    def contribution_margin_organic(self) -> float:
        """自然订单贡献毛利"""
        return self.current_price - self.cogs - self.total_operating_cost
    
    @property
    def contribution_margin_ad(self) -> float:
        """广告订单贡献毛利 (扣除TACOS广告费)"""
        return self.contribution_margin_organic - self.calculate_ad_cost_per_unit()
    
    @property
    def blended_margin(self) -> float:
        """混合利润率"""
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
        """利润健康度"""
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
    """链接汇总数据"""
    parent_asin: str
    total_variants: int
    active_variants: int
    
    # 销量汇总
    total_monthly_sales: int
    total_monthly_revenue: float
    total_monthly_profit: float
    
    # 订单来源
    organic_sales_pct: float
    ad_sales_pct: float
    organic_profit: float
    ad_profit: float
    
    # 利润率
    blended_margin: float
    organic_margin: float
    ad_margin: float
    
    # 帕累托分析
    pareto_variants: List[str]  # 贡献80%销量的变体
    top_3_variants: List[str]
    
    # 风险提示
    loss_variants: List[str]
    high_ad_dependency: List[str]  # 广告依赖度>60%的变体
    
    # 机会点
    growth_opportunities: List[str]  # 有增长潜力的变体


class ComprehensiveActuaryReport:
    """综合精算师报告生成器"""
    
    def __init__(self):
        self.storage_rate = 0.87  # $/cu.ft/month
        
    def generate_report(self,
                       parent_asin: str,
                       variants: List[VariantDetail],
                       output_path: str):
        """生成综合报告"""
        
        # 计算链接汇总
        summary = self._calculate_summary(parent_asin, variants)
        
        # 生成HTML
        html = self._render_html(parent_asin, variants, summary)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path, summary
    
    def _calculate_summary(self, parent_asin: str, variants: List[VariantDetail]) -> LinkSummary:
        """计算链接汇总数据"""
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
        
        # 按销量排序
        sorted_variants = sorted(variants, key=lambda x: x.estimated_monthly_sales, reverse=True)
        
        total_sales = sum(v.estimated_monthly_sales for v in variants)
        total_revenue = sum(v.monthly_revenue for v in variants)
        
        # 帕累托分析
        sales_accumulated = 0
        pareto_threshold = total_sales * 0.80
        pareto_variants = []
        for v in sorted_variants:
            sales_accumulated += v.estimated_monthly_sales
            pareto_variants.append(v.asin)
            if sales_accumulated >= pareto_threshold:
                break
        
        top_3 = [v.asin for v in sorted_variants[:3]]
        
        # 汇总自然/广告
        total_organic_profit = sum(v.monthly_profit_organic for v in variants)
        total_ad_profit = sum(v.monthly_profit_ad for v in variants)
        total_profit = total_organic_profit + total_ad_profit
        
        organic_revenue = sum(v.monthly_revenue * v.organic_order_pct for v in variants)
        ad_revenue = sum(v.monthly_revenue * v.ad_order_pct for v in variants)
        
        # 利润率
        organic_margin = (total_organic_profit / organic_revenue * 100) if organic_revenue > 0 else 0
        ad_margin = (total_ad_profit / ad_revenue * 100) if ad_revenue > 0 else 0
        blended_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # 风险识别
        loss_variants = [v.asin for v in variants if v.blended_margin <= 0]
        high_ad_dependency = [v.asin for v in variants if v.ad_order_pct > 0.60]
        
        # 增长机会 (销量中等但评价好)
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
        """渲染HTML报告"""
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 决策建议
        if summary.blended_margin > 20 and summary.organic_sales_pct > 60:
            verdict = "🟢 强烈推荐"
            verdict_color = "#4ade80"
            verdict_detail = "利润率高且自然流量占比健康"
        elif summary.blended_margin > 10:
            verdict = "🟡 谨慎考虑"
            verdict_color = "#fbbf24"
            verdict_detail = "利润率尚可，需关注广告依赖度"
        else:
            verdict = "🔴 建议放弃"
            verdict_color = "#f87171"
            verdict_detail = "利润率过低或亏损风险高"
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>亚马逊链接精算师分析报告 - {parent_asin}</title>
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
                    <span class="header-badge">🏆 精算师级分析</span>
                    <span class="header-badge">📊 全变体覆盖</span>
                    <span class="header-badge">✅ 真实COGS</span>
                </div>
                <span style="opacity: 0.8; font-size: 0.95em;">{current_date}</span>
            </div>
            <h1>亚马逊链接运营精算师报告</h1>
            <div style="font-size: 1.2em; opacity: 0.95;">
                父ASIN: <strong>{parent_asin}</strong> | 
                变体数: <strong>{summary.total_variants}</strong> | 
                分析日期: {current_date}
            </div>
        </div>
        
        <!-- Executive Summary -->
        <div class="exec-summary">
            <h2 style="font-size: 1.8em; margin-bottom: 10px;">💼 执行摘要与投资决策</h2>
            <div class="verdict">{verdict}</div>
            <p style="font-size: 1.2em; margin-bottom: 40px;">{verdict_detail}</p>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value" style="color: #60a5fa;">{summary.total_monthly_sales:,}</div>
                    <div class="metric-label">预估月总销量</div>
                    <div class="metric-sublabel">全变体合计</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #a78bfa;">${summary.total_monthly_revenue:,.0f}</div>
                    <div class="metric-label">预估月销售额</div>
                    <div class="metric-sublabel">Gross Revenue</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #4ade80;">${summary.total_monthly_profit:,.0f}</div>
                    <div class="metric-label">预估月净利润</div>
                    <div class="metric-sublabel">扣除所有成本</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: {'#4ade80' if summary.blended_margin > 20 else '#fbbf24' if summary.blended_margin > 10 else '#f87171'};">
                        {summary.blended_margin:.1f}%
                    </div>
                    <div class="metric-label">混合净利率</div>
                    <div class="metric-sublabel">自然+广告加权</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #22c55e;">{summary.organic_sales_pct:.0f}%</div>
                    <div class="metric-label">自然订单占比</div>
                    <div class="metric-sublabel">无需广告费</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #f59e0b;">{len(summary.pareto_variants)}</div>
                    <div class="metric-label">核心变体数</div>
                    <div class="metric-sublabel">贡献80%销量</div>
                </div>
            </div>
        </div>
        
        <!-- Organic vs Ad Analysis -->
        <div class="card">
            <h2 class="card-title">🌿🎯 自然订单 vs 广告订单深度对比</h2>
            
            <div class="comparison-grid">
                <div class="comp-card comp-organic">
                    <h3 style="font-size: 1.4em; color: #4ade80; margin-bottom: 25px;">🌿 自然订单分析</h3>
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>收入占比</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">{summary.organic_sales_pct:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>月利润贡献</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">${summary.organic_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>平均利润率</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">{summary.organic_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.9; line-height: 1.8;">
                        自然订单无需支付广告费，利润率显著高于广告订单。
                        当前自然占比{summary.organic_sales_pct:.0f}%属于{"优秀" if summary.organic_sales_pct > 60 else "良好" if summary.organic_sales_pct > 50 else "需提升"}水平。
                    </p>
                </div>
                
                <div class="comp-card comp-ad">
                    <h3 style="font-size: 1.4em; color: #fbbf24; margin-bottom: 25px;">🎯 广告订单分析</h3>
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>收入占比</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #fbbf24;">{summary.ad_sales_pct:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>月利润贡献</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #fbbf24;">${summary.ad_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>平均利润率</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #fbbf24;">{summary.ad_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.9; line-height: 1.8;">
                        广告订单需要分摊广告费(TACOS 15%)，利润率较低。
                        {"广告依赖度适中" if summary.ad_sales_pct < 40 else "⚠️ 广告依赖度较高，需关注TACOS优化" if summary.ad_sales_pct < 60 else "🔴 广告依赖度过高，存在风险"}。
                    </p>
                </div>
            </div>
            
            <div class="insight-box">
                <h4>💡 订单来源洞察</h4>
                <p>
                    自然订单利润率 ({summary.organic_margin:.1f}%) 
                    比广告订单 ({summary.ad_margin:.1f}%) 高 
                    <strong>{summary.organic_margin - summary.ad_margin:.1f}个百分点</strong>。
                    每提升1%的自然订单占比，月利润可增加约 
                    <strong>${(summary.organic_profit/summary.organic_sales_pct - summary.ad_profit/summary.ad_sales_pct) * summary.total_monthly_sales / 100:.0f}</strong>。
                </p>
            </div>
        </div>
        
        <!-- Pareto Analysis -->
        <div class="card">
            <h2 class="card-title">📈 帕累托分析 (80/20法则)</h2>
            
            <div class="metrics-grid" style="margin-bottom: 25px;">
                <div class="metric-card" style="background: rgba(59, 130, 246, 0.15); border: 2px solid rgba(59, 130, 246, 0.3);">
                    <div class="metric-value" style="color: #60a5fa;">{len(summary.pareto_variants)}</div>
                    <div class="metric-label">核心变体</div>
                    <div class="metric-sublabel">贡献80%销量</div>
                </div>
                <div class="metric-card" style="background: rgba(245, 158, 11, 0.15); border: 2px solid rgba(245, 158, 11, 0.3);">
                    <div class="metric-value" style="color: #fbbf24;">{len(summary.high_ad_dependency)}</div>
                    <div class="metric-label">高广告依赖</div>
                    <div class="metric-sublabel">广告占比&gt;60%</div>
                </div>
                <div class="metric-card" style="background: rgba(239, 68, 68, 0.15); border: 2px solid rgba(239, 68, 68, 0.3);">
                    <div class="metric-value" style="color: #f87171;">{len(summary.loss_variants)}</div>
                    <div class="metric-label">亏损变体</div>
                    <div class="metric-sublabel">需立即处理</div>
                </div>
                <div class="metric-card" style="background: rgba(34, 197, 94, 0.15); border: 2px solid rgba(34, 197, 94, 0.3);">
                    <div class="metric-value" style="color: #4ade80;">{len(summary.growth_opportunities)}</div>
                    <div class="metric-label">增长机会</div>
                    <div class="metric-sublabel">有潜力变体</div>
                </div>
            </div>
            
            <p style="opacity: 0.9; line-height: 1.8;">
                <strong>核心发现:</strong> 前{len(summary.pareto_variants)}个变体贡献了链接80%的销量。
                应优先保证这些变体的库存充足，并持续优化其自然排名。
                {"同时关注" if len(summary.high_ad_dependency) > 0 else ""} 
                {len(summary.high_ad_dependency)}个高广告依赖变体，考虑通过站外或优化listing提升自然占比。
            </p>
        </div>
        
        <!-- Variant Details Table -->
        <div class="card">
            <h2 class="card-title">📋 全变体详细指标表</h2>
            
            <div class="legend">
                <div class="legend-item"><div class="legend-dot" style="background: #22c55e;"></div>🔥 Top 3 变体</div>
                <div class="legend-item"><div class="legend-dot" style="background: #3b82f6;"></div>📊 帕累托变体(贡献80%)</div>
                <div class="legend-item"><div class="legend-dot" style="background: #f59e0b;"></div>⚠️ 高广告依赖(&gt;60%)</div>
                <div class="legend-item"><div class="legend-dot" style="background: #ef4444;"></div>🔴 亏损变体</div>
            </div>
            
            <div class="variant-section">
                <table class="variant-table">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>ASIN</th>
                            <th>颜色/尺寸</th>
                            <th>价格</th>
                            <th>月销量</th>
                            <th>销售额</th>
                            <th>订单来源</th>
                            <th>COGS</th>
                            <th>贡献毛利</th>
                            <th>自然利润</th>
                            <th>广告利润</th>
                            <th>利润率</th>
                            <th>月净利润</th>
                            <th>健康度</th>
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
            <h2 class="card-title">⚠️ 风险评估与缓解措施</h2>
            
            {self._render_risk_assessment(summary, variants)}
        </div>
        
        <!-- Action Plan -->
        <div class="card">
            <h2 class="card-title">🎯 30-60-90天行动计划</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;">
                <div style="background: rgba(239, 68, 68, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(239, 68, 68, 0.3);">
                    <h4 style="color: #f87171; margin-bottom: 20px; font-size: 1.2em;">🚨 立即行动 (0-30天)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        {f'<li>• 核查{len(summary.loss_variants)}个亏损变体的COGS是否准确</li>' if len(summary.loss_variants) > 0 else ''}
                        <li>• 确保{len(summary.pareto_variants)}个核心变体库存充足(60天+)</li>
                        <li>• 优化高销量变体的主图和标题，提升自然转化</li>
                        <li>• 检查{len(summary.high_ad_dependency)}个高广告依赖变体的TACOS</li>
                    </ul>
                </div>
                
                <div style="background: rgba(245, 158, 11, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(245, 158, 11, 0.3);">
                    <h4 style="color: #fbbf24; margin-bottom: 20px; font-size: 1.2em;">📈 短期优化 (30-60天)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        <li>• 针对高广告依赖变体，开展站外推广降低TACOS</li>
                        <li>• 测试{len(summary.growth_opportunities)}个潜力变体的价格弹性</li>
                        <li>• 收集并分析退货原因，降低退货率</li>
                        <li>• 优化广告投放策略，加大高利润变体预算</li>
                    </ul>
                </div>
                
                <div style="background: rgba(34, 197, 94, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(34, 197, 94, 0.3);">
                    <h4 style="color: #4ade80; margin-bottom: 20px; font-size: 1.2em;">🚀 长期策略 (60-90天)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        <li>• 开发新颜色/尺寸变体，复制成功模式</li>
                        <li>• 建立供应链议价能力，降低COGS 5-10%</li>
                        <li>• 构建品牌护城河，提升自然流量占比至70%+</li>
                        <li>• 建立月度利润监控体系，及时发现问题变体</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- Data Source Note -->
        <div class="card" style="background: rgba(251, 191, 36, 0.05); border: 2px solid rgba(251, 191, 36, 0.3);">
            <h2 class="card-title" style="color: #fbbf24;">📊 数据来源说明</h2>
            <div style="line-height: 2;">
                <p><strong>销量数据:</strong> 基于Keepa销售排名估算，参考过去30天平均排名</p>
                <p><strong>价格数据:</strong> 当前Buy Box价格或New价格，取平均值</p>
                <p><strong>COGS数据:</strong> <span style="color: #fbbf24; font-weight: 600;">用户提供真实数据</span>，包含采购价、头程运费、关税</p>
                <p><strong>订单来源:</strong> <span style="color: #fbbf24; font-weight: 600;">用户提供真实数据</span>，来自亚马逊广告后台报表</p>
                <p><strong>FBA费用:</strong> 从Keepa API获取或基于重量/尺寸计算</p>
                <p><strong>退货率:</strong> 从Keepa API获取该产品历史退货率</p>
                <p><strong>广告费率:</strong> 假设TACOS (Total ACOS) 15%，即广告总花费占整体销售额的15%。实际费用请根据后台广告报表调整。</p>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p style="font-size: 1.1em; margin-bottom: 15px;">本报告基于真实COGS和订单来源数据生成 | 数据驱动决策</p>
            <p style="opacity: 0.7;">
                © 2026 亚马逊运营精算师系统 | 所有成本数据需用户核实确认<br>
                报告仅供参考，实际盈利受市场波动、竞争变化等因素影响
            </p>
        </div>
    </div>
</body>
</html>'''
        
        return html
    
    def _render_variant_rows(self, variants: List[VariantDetail], summary: LinkSummary) -> str:
        """渲染变体表格行"""
        html = ''
        sorted_variants = sorted(variants, key=lambda x: x.estimated_monthly_sales, reverse=True)
        
        for i, v in enumerate(sorted_variants, 1):
            # 确定行样式
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
            
            # 利润健康度样式
            profit_class = f'profit-{v.profit_health}'
            
            # 健康度标签
            health_label = {
                'excellent': '✅ 优秀',
                'good': '🟢 良好',
                'marginal': '🟡 一般',
                'loss': '🔴 亏损'
            }.get(v.profit_health, '❓ 未知')
            
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
        """渲染风险评估"""
        html = ''
        
        # 风险1: 亏损变体
        if len(summary.loss_variants) > 0:
            html += f'''
                <div class="alert-box">
                    <h4>🔴 亏损变体风险 ({len(summary.loss_variants)}个)</h4>
                    <p>以下变体在当前成本结构下可能亏损，请立即核查COGS是否准确，或考虑提价/下架：</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(summary.loss_variants)}</p>
                </div>
            '''
        
        # 风险2: 高广告依赖
        if len(summary.high_ad_dependency) > 0:
            html += f'''
                <div class="insight-box">
                    <h4>⚠️ 高广告依赖风险 ({len(summary.high_ad_dependency)}个)</h4>
                    <p>以下变体广告订单占比超过60%，一旦广告成本上升或竞争加剧，利润将显著下滑：</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(summary.high_ad_dependency)}</p>
                    <p style="margin-top: 10px;"><strong>缓解措施:</strong> 通过站外推广、社交媒体种草等方式提升自然流量占比。</p>
                </div>
            '''
        
        # 风险3: 销量集中
        if len(summary.pareto_variants) <= 2 and summary.total_variants >= 5:
            html += f'''
                <div class="insight-box">
                    <h4>⚠️ 销量过度集中风险</h4>
                    <p>仅{len(summary.pareto_variants)}个变体贡献了80%的销量，链接抗风险能力较弱。一旦核心变体出现问题(断货、差评、跟卖)，整体销售将受到严重冲击。</p>
                    <p style="margin-top: 10px;"><strong>缓解措施:</strong> 平衡推广资源，培育第二梯队变体；确保核心变体库存充足且多仓分布。</p>
                </div>
            '''
        
        # 机会点
        if len(summary.growth_opportunities) > 0:
            html += f'''
                <div class="success-box">
                    <h4>🌟 增长机会 ({len(summary.growth_opportunities)}个)</h4>
                    <p>以下变体评价较好但销量中等，有潜力成为新的增长点：</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(summary.growth_opportunities)}</p>
                    <p style="margin-top: 10px;"><strong>建议:</strong> 增加广告投放测试、优化listing图片和关键词、考虑参加Deal活动。</p>
                </div>
            '''
        
        if not html:
            html = '<p style="color: #4ade80; font-size: 1.1em;">✅ 未发现明显风险，当前运营状态良好</p>'
        
        return html


def generate_comprehensive_report(parent_asin: str,
                                 variants: List[VariantDetail],
                                 output_path: str) -> Tuple[str, LinkSummary]:
    """便捷函数：生成综合报告"""
    generator = ComprehensiveActuaryReport()
    return generator.generate_report(parent_asin, variants, output_path)
