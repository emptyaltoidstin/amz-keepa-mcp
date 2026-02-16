"""
亚马逊链接变体利润分析器
===========================
采集父ASIN下所有变体，基于真实销量分布和订单来源推演链接整体盈利
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class VariantMetrics:
    """变体指标"""
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
    
    # 订单来源分布 (从真实数据或估算)
    organic_order_pct: float = 0.60  # 自然订单占比
    ad_order_pct: float = 0.40       # 广告订单占比
    
    # 成本结构
    cogs: float = 0.0
    fba_fee: float = 0.0
    
    @property
    def monthly_revenue(self) -> float:
        return self.price * self.estimated_sales
    
    @property
    def contribution_margin(self) -> float:
        """贡献毛利 (不含广告费)"""
        referral_fee = self.price * 0.15
        return_cost = self.price * self.return_rate * 0.30
        storage = 0.05  # 估算
        return self.price - self.cogs - self.fba_fee - referral_fee - return_cost - storage


@dataclass
class LinkProfitability:
    """链接整体盈利性"""
    parent_asin: str
    total_variants: int
    active_variants: int
    
    # 销量分布
    total_monthly_sales: int
    top_3_variants_sales_pct: float
    
    # 收入结构
    total_monthly_revenue: float
    
    # 利润分析
    blended_organic_margin: float  # 混合自然订单利润率
    blended_ad_margin: float       # 混合广告订单利润率
    blended_overall_margin: float  # 整体混合利润率
    
    # 自然 vs 广告对比
    organic_revenue_pct: float
    ad_revenue_pct: float
    organic_profit: float
    ad_profit: float
    
    # 关键发现
    pareto_variants: List[str]  # 贡献80%销量的变体
    loss_variants: List[str]    # 亏损的变体


class VariantProfitAnalyzer:
    """变体利润分析器"""
    
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
        分析整个链接的盈利性
        
        Args:
            parent_asin: 父ASIN
            variants_data: 所有变体的Keepa数据
            cogs_map: 各变体的COGS {asin: cogs}
            order_source_map: 各变体的订单来源比例 {asin: (organic_pct, ad_pct)}
        
        Returns:
            LinkProfitability 链接整体盈利分析
        """
        # 解析每个变体的指标
        variants = []
        for data in variants_data:
            variant = self._parse_variant_metrics(data)
            
            # 应用自定义COGS
            if cogs_map and variant.asin in cogs_map:
                variant.cogs = cogs_map[variant.asin]
            else:
                # 基于价格的默认估算
                variant.cogs = variant.price * 0.35
            
            # 应用订单来源比例
            if order_source_map and variant.asin in order_source_map:
                variant.organic_order_pct, variant.ad_order_pct = order_source_map[variant.asin]
            
            variants.append(variant)
        
        # 按销量排序
        variants.sort(key=lambda x: x.estimated_sales, reverse=True)
        
        # 计算链接整体指标
        return self._calculate_link_metrics(parent_asin, variants)
    
    def _parse_variant_metrics(self, data: Dict) -> VariantMetrics:
        """解析变体指标"""
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
        """计算链接整体指标"""
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
        
        # 帕累托分析 (80/20法则)
        sales_accumulated = 0
        pareto_threshold = total_sales * 0.80
        pareto_variants = []
        loss_variants = []
        
        for v in variants:
            sales_accumulated += v.estimated_sales
            if sales_accumulated <= pareto_threshold:
                pareto_variants.append(v.asin)
            
            # 检查是否亏损
            if v.contribution_margin <= 0:
                loss_variants.append(v.asin)
        
        top_3_sales = sum(v.estimated_sales for v in variants[:3])
        
        # 计算加权平均利润率
        total_organic_profit = 0
        total_ad_profit = 0
        total_organic_revenue = 0
        total_ad_revenue = 0
        
        for v in variants:
            organic_sales = v.estimated_sales * v.organic_order_pct
            ad_sales = v.estimated_sales * v.ad_order_pct
            
            # 自然订单利润 (无广告费)
            organic_profit_per_unit = v.contribution_margin
            total_organic_profit += organic_profit_per_unit * organic_sales
            total_organic_revenue += v.price * organic_sales
            
            # 广告订单利润 (减去广告费)
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
        """生成变体利润分析报告"""
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>链接变体利润分析 - {parent_asin}</title>
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
            <h1>🔗 链接变体利润分析报告</h1>
            <div style="opacity: 0.9;">父ASIN: {parent_asin}</div>
            <div style="margin-top: 15px; display: flex; gap: 20px; flex-wrap: wrap;">
                <span>总变体数: {link_metrics.total_variants}</span>
                <span>活跃变体: {link_metrics.active_variants}</span>
                <span>帕累托变体: {len(link_metrics.pareto_variants)}个(贡献80%销量)</span>
            </div>
        </div>
        
        <!-- Executive Summary -->
        <div class="card">
            <h2 class="card-title">💼 链接整体盈利概览</h2>
            
            <div class="metrics-grid">
                <div class="metric-box">
                    <div class="metric-value" style="color: #60a5fa;">{link_metrics.total_monthly_sales:,}</div>
                    <div class="metric-label">预估月总销量</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: #a78bfa;">${link_metrics.total_monthly_revenue:,.0f}</div>
                    <div class="metric-label">预估月销售额</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: {'#4ade80' if link_metrics.blended_overall_margin > 15 else '#fbbf24' if link_metrics.blended_overall_margin > 5 else '#f87171'};">
                        {link_metrics.blended_overall_margin:.1f}%
                    </div>
                    <div class="metric-label">整体混合利润率</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: #22c55e;">{link_metrics.organic_revenue_pct:.0f}%</div>
                    <div class="metric-label">自然订单收入占比</div>
                </div>
            </div>
            
            <div class="insight-box">
                <strong>💡 关键发现:</strong> 前{len(link_metrics.pareto_variants)}个变体贡献了80%的销量，
                其中{len(link_metrics.loss_variants)}个变体可能亏损。建议重点关注高销量变体的利润率优化。
            </div>
        </div>
        
        <!-- Organic vs Ad Comparison -->
        <div class="card">
            <h2 class="card-title">📊 自然订单 vs 广告订单对比</h2>
            
            <div class="comparison-grid">
                <div style="background: rgba(34, 197, 94, 0.1); padding: 25px; border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.3);">
                    <h3 style="color: #4ade80; margin-bottom: 20px;">🌿 自然订单 ({link_metrics.organic_revenue_pct:.0f}%)</h3>
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>自然订单月利润</span>
                            <span style="font-weight: 600; color: #4ade80;">${link_metrics.organic_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>自然订单利润率</span>
                            <span style="font-weight: 600; color: #4ade80;">{link_metrics.blended_organic_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.8; font-size: 0.9em;">自然订单无广告成本，利润率更高，应重点优化自然排名。</p>
                </div>
                
                <div style="background: rgba(245, 158, 11, 0.1); padding: 25px; border-radius: 12px; border: 1px solid rgba(245, 158, 11, 0.3);">
                    <h3 style="color: #fbbf24; margin-bottom: 20px;">🎯 广告订单 ({link_metrics.ad_revenue_pct:.0f}%)</h3>
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>广告订单月利润</span>
                            <span style="font-weight: 600; color: #fbbf24;">${link_metrics.ad_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>广告订单利润率</span>
                            <span style="font-weight: 600; color: #fbbf24;">{link_metrics.blended_ad_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.8; font-size: 0.9em;">广告订单利润率较低，需监控ACoS，避免广告亏损。</p>
                </div>
            </div>
        </div>
        
        <!-- Variant Details -->
        <div class="card">
            <h2 class="card-title">📋 变体详细分析</h2>
            <p style="color: #94a3b8; margin-bottom: 20px;">
                共{len(variants)}个变体，按销量排序显示
            </p>
            
            <div style="overflow-x: auto;">
                <table class="variant-table">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>ASIN</th>
                            <th>颜色/尺寸</th>
                            <th>价格</th>
                            <th>月销量</th>
                            <th>订单来源</th>
                            <th>贡献毛利</th>
                            <th>自然利润</th>
                            <th>广告利润</th>
                            <th>状态</th>
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
            <h2 class="card-title">💡 运营建议</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                    <h4 style="color: #4ade80; margin-bottom: 15px;">✅ 立即行动</h4>
                    <ul style="list-style: none; padding: 0;">
                        <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            1. 核查{len(link_metrics.loss_variants)}个亏损变体的COGS
                        </li>
                        <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            2. 优化前{len(link_metrics.pareto_variants)}个变体的自然排名
                        </li>
                        <li style="padding: 8px 0;">
                            3. 监控广告订单ACoS，控制在15%以内
                        </li>
                    </ul>
                </div>
                
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                    <h4 style="color: #fbbf24; margin-bottom: 15px;">⚠️ 风险提示</h4>
                    <ul style="list-style: none; padding: 0;">
                        <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            • 自然订单占比{link_metrics.organic_revenue_pct:.0f}%，{'良好' if link_metrics.organic_revenue_pct > 60 else '需提升'}
                        </li>
                        <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            • 头部{link_metrics.top_3_variants_sales_pct:.0f}%销量集中，{'风险集中' if link_metrics.top_3_variants_sales_pct > 80 else '分布合理'}
                        </li>
                        <li style="padding: 8px 0;">
                            • 实际盈利取决于真实COGS和订单来源比例
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
        """渲染变体行"""
        html = ''
        for i, v in enumerate(variants, 1):
            # 计算各种利润
            referral = v.price * 0.15
            returns = v.price * v.return_rate * 0.30
            storage = 0.05
            
            contribution = v.price - v.cogs - v.fba_fee - referral - returns - storage
            organic_profit = contribution
            ad_profit = contribution - v.price * 0.15  # 减去广告费
            
            # 行样式
            row_class = ''
            status = ''
            if i <= 3:
                row_class = 'top-variant'
                status = '🔥 Top'
            elif contribution <= 0:
                row_class = 'loss-variant'
                status = '⚠️ 亏损'
            elif v.estimated_sales > 0:
                status = '✅ 正常'
            
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
        """根据排名估算月销量"""
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
