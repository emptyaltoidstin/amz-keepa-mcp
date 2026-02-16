"""
亚马逊运营精算师报告生成器
=============================
基于Keepa数据的专业财务分析和风险评估
"""

import json
import math
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class FinancialModel:
    """财务模型"""
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
    """情景分析"""
    name: str
    price: float
    volume: int
    revenue: float
    cost: float
    profit: float
    margin: float
    roi: float


class ActuaryReportGenerator:
    """精算师报告生成器"""
    
    def __init__(self):
        self.referral_rate = 0.15  # 默认15%
        self.return_loss_rate = 0.30  # 退货损失率
        self.storage_rate_per_cuft = 0.87  # 仓储费率 $/cu.ft/month
        self.acos_default = 0.15  # 默认ACOS 15%
        
    def generate_actuary_report(self,
                               asin: str,
                               product_data: dict,
                               factors: dict,
                               market_report: dict) -> str:
        """生成精算师级HTML报告"""
        
        # 提取基础数据
        title = product_data.get('Title', 'Unknown Product')
        brand = product_data.get('Brand', 'N/A')
        current_price = self._safe_float(product_data.get('New: Current', 0))
        rank = self._safe_int(product_data.get('Sales Rank: Current', 0))
        monthly_sales = self._estimate_monthly_sales(rank)
        return_rate = self._parse_percentage(product_data.get('Return Rate', '5%'))
        
        # 构建已知成本结构
        cost_structure = self._build_financial_model(current_price, monthly_sales, return_rate, product_data)
        
        # 基于不同COGS比例计算情景
        cogs_scenarios = self._build_cogs_scenarios(current_price, monthly_sales, cost_structure)
        
        # 盈亏平衡分析 (不同COGS下的最低售价)
        breakeven = self._calculate_breakeven_by_cogs(current_price, cost_structure)
        
        # 敏感性分析 (对COGS敏感)
        sensitivity = self._calculate_cogs_sensitivity(current_price, cost_structure)
        
        # 风险评估 (基于已知成本)
        risks = self._assess_risks_without_cogs(product_data, cost_structure, market_report)
        
        # 生成HTML
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
        """构建已知成本结构模型 (COGS由用户填写)"""
        
        # FBA费用 (从数据中获取或估算)
        fba_fee = self._safe_float(data.get('FBA Pick&Pack Fee', 0))
        if fba_fee == 0:
            weight_g = self._safe_float(data.get('Package: Weight (g)', 0))
            if weight_g > 0:
                fba_fee = self._estimate_fba_fee(weight_g)
            else:
                fba_fee = 3.50  # 默认估计
        
        # 佣金
        referral_rate = self._safe_float(data.get('Referral Fee %', 15)) / 100
        referral_fee = price * referral_rate
        
        # 退货成本
        return_cost = price * return_rate * self.return_loss_rate
        
        # 仓储费
        storage_cost = self._calculate_storage_cost(data)
        
        # 广告费 (按ACOS)
        ad_cost = price * self.acos_default
        
        # 已知运营成本 (不含COGS)
        known_operating_cost = fba_fee + referral_fee + return_cost + storage_cost + ad_cost
        
        # 假设COGS占位 (用户需要填入实际值)
        placeholder_cogs = price * 0.35  # 仅作为参考占位，不用于最终计算
        
        # 总成本 (含占位COGS)
        total_cost_with_placeholder = placeholder_cogs + known_operating_cost
        
        return {
            'selling_price': price,
            'cogs_placeholder': placeholder_cogs,  # 仅参考
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
        """基于不同COGS比例计算利润情景"""
        scenarios = []
        
        known_cost = cost_structure['known_operating_cost']
        
        # 不同COGS比例情景
        cogs_rates = [
            (0.20, "低COGS (20%)", "优质供应链"),
            (0.30, "中低COGS (30%)", "良好供应链"),
            (0.40, "中等COGS (40%)", "普通供应链"),
            (0.50, "中高COGS (50%)", "较差供应链"),
            (0.60, "高COGS (60%)", "需优化供应链"),
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
                'is_viable': margin > 10,  # 10%以上利润率视为可行
            })
        
        return scenarios
    
    def _calculate_breakeven_by_cogs(self, price: float, cost_structure: Dict) -> Dict:
        """计算不同COGS下的盈亏平衡"""
        known_cost = cost_structure['known_operating_cost']
        
        # 不同COGS下的最低售价
        breakeven_prices = {}
        for cogs_rate in [0.20, 0.30, 0.40, 0.50]:
            cogs = price * cogs_rate
            breakeven_price = cogs + known_cost
            breakeven_prices[cogs_rate] = breakeven_price
        
        return {
            'known_operating_cost': known_cost,
            'breakeven_by_cogs': breakeven_prices,
            'current_price': price,
            'safety_margin': {},  # 将在渲染时计算
        }
    
    def _calculate_cogs_sensitivity(self, price: float, cost_structure: Dict) -> Dict:
        """COGS敏感性分析"""
        known_cost = cost_structure['known_operating_cost']
        base_cogs_rate = 0.35
        base_cogs = price * base_cogs_rate
        base_profit = price - base_cogs - known_cost
        
        sensitivities = []
        
        # COGS从20%到60%变化
        for cogs_rate in [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
            cogs = price * cogs_rate
            total_cost = cogs + known_cost
            profit = price - total_cost
            margin = (profit / price * 100) if price > 0 else 0
            
            profit_change = ((profit - base_profit) / base_profit * 100) if base_profit != 0 else 0
            
            status = "🟢 健康" if margin > 15 else "🟡 一般" if margin > 5 else "🔴 危险"
            
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
        """计算盈亏平衡"""
        # 单位盈亏平衡 (售价已定，看最低需要多少销量)
        fixed_costs_per_month = 0  # 假设无固定成本
        contribution_margin = financial.gross_profit
        
        breakeven_units = 0
        if contribution_margin > 0:
            breakeven_units = int(fixed_costs_per_month / contribution_margin) + 1
        
        # 价格盈亏平衡 (给定销量，看最低售价)
        target_volume = 100  # 假设月销100件
        min_price = financial.total_cost
        
        return {
            'breakeven_units': breakeven_units,
            'contribution_margin': contribution_margin,
            'min_viable_price': min_price,
            'target_volume': target_volume,
        }
    
    def _calculate_sensitivity(self, financial: FinancialModel) -> Dict:
        """敏感性分析"""
        base_profit = financial.gross_profit
        base_margin = financial.net_margin
        
        sensitivities = []
        
        # 价格变动 ±10%
        for delta in [-0.10, -0.05, 0, 0.05, 0.10]:
            new_price = financial.selling_price * (1 + delta)
            new_profit = new_price - financial.total_cost + (financial.selling_price - new_price) * 0.15  # 佣金变化
            new_margin = (new_profit / new_price * 100) if new_price > 0 else 0
            profit_change = ((new_profit - base_profit) / base_profit * 100) if base_profit != 0 else 0
            
            sensitivities.append({
                'variable': f'价格 {delta*100:+.0f}%',
                'value': new_price,
                'profit': new_profit,
                'margin': new_margin,
                'change': profit_change
            })
        
        # COGS变动 ±10%
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
        """风险评估 (不含COGS估算)"""
        risks = []
        price = cost_structure['selling_price']
        known_cost = cost_structure['known_operating_cost']
        
        # 已知成本占比风险
        known_cost_ratio = known_cost / price if price > 0 else 0
        if known_cost_ratio > 0.50:
            risks.append({
                'type': 'cost_structure',
                'level': 'high',
                'desc': f'已知运营成本占比过高 ({known_cost_ratio*100:.1f}%)，留给COGS的空间很小',
                'mitigation': '降低FBA费用(轻小计划)或优化广告ACOS'
            })
        
        # 退货率风险
        return_rate = cost_structure['return_rate']
        if return_rate > 0.15:
            risks.append({
                'type': 'returns',
                'level': 'high',
                'desc': f'退货率过高 ({return_rate*100:.0f}%)，严重侵蚀利润',
                'mitigation': '改善产品质量或描述'
            })
        elif return_rate > 0.10:
            risks.append({
                'type': 'returns',
                'level': 'medium',
                'desc': f'退货率偏高 ({return_rate*100:.0f}%)',
                'mitigation': '关注退货原因'
            })
        
        # 竞争风险
        offer_count = self._safe_int(data.get('New Offer Count: Current', 0))
        if offer_count > 15:
            risks.append({
                'type': 'competition',
                'level': 'high',
                'desc': f'竞争激烈 ({offer_count}个卖家)，价格战风险高',
                'mitigation': '差异化或寻找蓝海'
            })
        
        # 排名下滑风险
        rank_drops = self._safe_int(data.get('Sales Rank: Drops last 90 days', 0))
        if rank_drops > 40:
            risks.append({
                'type': 'demand',
                'level': 'high',
                'desc': f'需求下滑迹象 (90天排名下降{rank_drops}次)',
                'mitigation': '关注市场趋势'
            })
        
        # FBA费用风险
        fba_fee = cost_structure['fba_fee']
        if fba_fee > price * 0.20:
            risks.append({
                'type': 'fba_cost',
                'level': 'medium',
                'desc': f'FBA费用占比过高 (${fba_fee:.2f})',
                'mitigation': '考虑轻小计划或自发货'
            })
        
        return risks
    
    def _render_html(self, **kwargs) -> str:
        """渲染HTML报告"""
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
        
        # 计算综合评分
        factor_score = sum(f.score * f.weight for f in kwargs['factors'].values())
        market_score = kwargs['market_report']['market_feasibility']['overall_score']
        overall = (factor_score + market_score) / 2  # 不含财务评分，因为COGS未知
        
        # 决策建议 (基于已知信息)
        if overall >= 70 and known_cost / price < 0.40 if price > 0 else False:
            decision = "🟢 推荐考虑"
            decision_color = "#4ade80"
            decision_detail = "市场可行性好，运营成本结构合理，待确认COGS后即可决策"
        elif overall >= 55:
            decision = "🟡 谨慎评估"
            decision_color = "#fbbf24"
            decision_detail = "有一定可行性，需确认实际COGS后评估"
        else:
            decision = "🔴 建议放弃"
            decision_color = "#f87171"
            decision_detail = "市场可行性不足或运营成本过高"
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>亚马逊运营精算师分析报告 - {asin}</title>
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
                <span class="badge badge-professional">🏆 精算师级分析</span>
                <span style="opacity: 0.8;">{current_date}</span>
            </div>
            <h1>亚马逊运营精算师分析报告</h1>
            <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 15px;">
                <span>ASIN: {asin}</span>
                <span>品牌: {kwargs.get('brand', 'N/A')}</span>
            </div>
            <div style="font-size: 1.1em; opacity: 0.9; line-height: 1.5;">{title}</div>
        </div>
        
        <!-- COGS Notice -->
        <div class="cogs-notice">
            <h2>⚠️ COGS (采购成本) 待填写</h2>
            <p style="font-size: 1.1em; margin-bottom: 15px;">
                本报告仅基于<strong>已知运营成本</strong>进行分析，不包含COGS估算。
            </p>
            <p style="opacity: 0.9;">
                请在下方表格填入您的实际COGS，查看对应利润率。
                <br>COGS = 产品采购价 + 头程运费 + 关税 + 其他到仓成本
            </p>
        </div>
        
        <!-- Executive Summary -->
        <div class="card">
            <h2 class="card-title">💼 执行摘要</h2>
            <div class="verdict">{decision}</div>
            <p style="text-align: center; font-size: 1.1em; margin-bottom: 30px;">{decision_detail}</p>
            
            <div class="metrics-grid">
                <div class="metric-box">
                    <div class="metric-value" style="color: #60a5fa;">{overall:.0f}</div>
                    <div class="metric-label">综合评分</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: #fbbf24;">{factor_score:.0f}</div>
                    <div class="metric-label">六维因子</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: #a78bfa;">{market_score:.0f}</div>
                    <div class="metric-label">市场可行性</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: #fbbf24;">{known_cost/price*100:.1f}%</div>
                    <div class="metric-label">已知成本占比</div>
                </div>
            </div>
        </div>
        
        <!-- Known Cost Structure -->
        <div class="card">
            <h2 class="card-title">💰 已知成本结构 (不含COGS)</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                <div>
                    <h3 style="margin-bottom: 20px; color: #94a3b8;">单位运营成本 (每件)</h3>
                    <div class="cost-breakdown">
                        <div class="cost-item known">
                            <span>售价 (Selling Price)</span>
                            <span style="font-weight: 600;">${price:.2f}</span>
                        </div>
                        <div class="cost-item tbd">
                            <span>➖ COGS (待填写)</span>
                            <span style="font-weight: 600;">?</span>
                        </div>
                        <div class="cost-item known">
                            <span>➖ FBA费用</span>
                            <span>-${cost_structure.get('fba_fee', 0):.2f}</span>
                        </div>
                        <div class="cost-item known">
                            <span>➖ 平台佣金 ({cost_structure.get('referral_rate', 0.15)*100:.0f}%)</span>
                            <span>-${cost_structure.get('referral_fee', 0):.2f}</span>
                        </div>
                        <div class="cost-item known">
                            <span>➖ 退货成本 ({cost_structure.get('return_rate', 0.05)*100:.0f}%退货率)</span>
                            <span>-${cost_structure.get('return_cost', 0):.2f}</span>
                        </div>
                        <div class="cost-item known">
                            <span>➖ 仓储费</span>
                            <span>-${cost_structure.get('storage_cost', 0):.3f}</span>
                        </div>
                        <div class="cost-item known">
                            <span>➖ 广告费 (ACoS 15%)</span>
                            <span>-${cost_structure.get('ad_cost', 0):.2f}</span>
                        </div>
                        <div class="cost-item total">
                            <span>已知运营成本合计</span>
                            <span style="color: #f87171;">${known_cost:.2f}</span>
                        </div>
                        <div class="cost-item" style="background: rgba(251, 191, 36, 0.1); border-radius: 8px; padding: 15px; margin-top: 10px;">
                            <span style="color: #fbbf24; font-weight: 600;">COGS上限空间</span>
                            <span style="color: #fbbf24; font-weight: 600;">${price - known_cost:.2f} (最高{(price-known_cost)/price*100:.0f}%)</span>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h3 style="margin-bottom: 20px; color: #94a3b8;">月度运营数据</h3>
                    <div class="cost-breakdown">
                        <div class="cost-item">
                            <span>估算月销量</span>
                            <span style="font-weight: 600;">{monthly_sales} 件</span>
                        </div>
                        <div class="cost-item">
                            <span>月销售额 (Gross Revenue)</span>
                            <span>${price * monthly_sales:,.2f}</span>
                        </div>
                        <div class="cost-item">
                            <span>月已知运营成本</span>
                            <span style="color: #f87171;">${known_cost * monthly_sales:,.2f}</span>
                        </div>
                        <div class="cost-item" style="background: rgba(251, 191, 36, 0.1); border-radius: 8px; padding: 15px; margin-top: 10px;">
                            <span style="color: #fbbf24; font-weight: 600;">月COGS上限</span>
                            <span style="color: #fbbf24; font-weight: 600;">${(price - known_cost) * monthly_sales:,.2f}</span>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <h4 style="margin-bottom: 10px; color: #94a3b8;">关键指标</h4>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>已知成本占比</span>
                            <span style="font-weight: 600;">{known_cost/price*100:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>留给COGS的空间</span>
                            <span style="font-weight: 600; color: #fbbf24;">{((price-known_cost)/price*100) if price > 0 else 0:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>要达到15%净利率</span>
                            <span style="font-weight: 600; color: #4ade80;">
                                COGS需≤${price*0.70-known_cost:.2f} (≤{(price*0.70-known_cost)/price*100:.0f}%)
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- COGS Scenarios -->
        <div class="card">
            <h2 class="card-title">📊 不同COGS比例下的利润分析</h2>
            <p style="color: #94a3b8; margin-bottom: 20px;">填入您的实际COGS比例，查看对应的财务表现</p>
            
            <div style="overflow-x: auto;">
                <table class="cogs-table">
                    <thead>
                        <tr>
                            <th>COGS比例</th>
                            <th>COGS金额</th>
                            <th>总成本</th>
                            <th>单位利润</th>
                            <th>净利率</th>
                            <th>月利润</th>
                            <th>可行性</th>
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
            <h2 class="card-title">📈 盈亏平衡分析</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                    <h4 style="margin-bottom: 15px; color: #94a3b8;">不同COGS下的最低售价</h4>
                    {self._render_breakeven_prices(breakeven)}
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                    <h4 style="margin-bottom: 15px; color: #94a3b8;">当前定价安全边际</h4>
                    <div style="line-height: 2;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>当前售价</span>
                            <span style="font-weight: 600;">${price:.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>已知运营成本</span>
                            <span style="color: #f87171;">${known_cost:.2f}</span>
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.2); margin: 10px 0; padding-top: 10px; display: flex; justify-content: space-between;">
                            <span>COGS上限空间</span>
                            <span style="color: #fbbf24; font-weight: 600;">${price - known_cost:.2f}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Risk Assessment -->
        <div class="card">
            <h2 class="card-title">⚠️ 已知成本结构风险评估</h2>
            {self._render_risks(risks)}
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>本报告基于Keepa API已知数据生成 | 不包含COGS估算</p>
            <p style="margin-top: 10px; opacity: 0.7; font-size: 0.9em;">
                © 2026 Amz-Keepa-MCP | 请填入实际COGS后进行投资决策
            </p>
        </div>
    </div>
</body>
</html>'''
        
        return html
    
    def _render_cogs_scenarios(self, scenarios: List[Dict], monthly_sales: int) -> str:
        """渲染COGS情景表格"""
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
                    <td>{'✅ 可行' if s['is_viable'] else '⚠️ 风险'}</td>
                </tr>
            '''
        return html
    
    def _render_breakeven_prices(self, breakeven: Dict) -> str:
        """渲染盈亏平衡价格"""
        html = '<div style="line-height: 2;">'
        for cogs_rate, price in breakeven.get('breakeven_by_cogs', {}).items():
            html += f'''
                <div style="display: flex; justify-content: space-between;">
                    <span>COGS {cogs_rate*100:.0f}%时</span>
                    <span style="font-weight: 600;">最低售价 ${price:.2f}</span>
                </div>
            '''
        html += '</div>'
        return html
    
    def _render_risks(self, risks: List[Dict]) -> str:
        """渲染风险项"""
        if not risks:
            return '<p style="color: #4ade80;">✅ 未发现基于已知成本的风险</p>'
        
        html = ''
        for risk in risks:
            level_class = '' if risk['level'] == 'high' else 'medium'
            html += f'''
                <div class="risk-item {level_class}">
                    <div style="font-weight: 600; color: #fca5a5; margin-bottom: 8px;">
                        {risk['type'].upper()} - {risk['level'].upper()}
                    </div>
                    <p style="margin-bottom: 10px;">{risk['desc']}</p>
                    <p style="opacity: 0.8; font-size: 0.9em;"><strong>缓解措施:</strong> {risk.get('mitigation', '')}</p>
                </div>
            '''
        return html
    
    def _estimate_monthly_sales(self, rank: int) -> int:
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
    
    def _estimate_fba_fee(self, weight_g: float) -> float:
        """估算FBA费用"""
        weight_lb = weight_g / 453.592
        if weight_lb < 1:
            return 3.22
        elif weight_lb < 2:
            return 4.71
        else:
            return 4.71 + (weight_lb - 1) * 0.50
    
    def _calculate_storage_cost(self, data: dict) -> float:
        """计算仓储费"""
        length = self._safe_float(data.get('Package: Length (cm)', 0)) / 2.54  # 转英寸
        width = self._safe_float(data.get('Package: Width (cm)', 0)) / 2.54
        height = self._safe_float(data.get('Package: Height (cm)', 0)) / 2.54
        
        if length > 0 and width > 0 and height > 0:
            volume_cuft = (length * width * height) / 1728
            return volume_cuft * self.storage_rate_per_cuft
        return 0.05
    
    def _parse_percentage(self, val) -> float:
        """解析百分比"""
        if isinstance(val, str):
            val = val.replace('%', '').strip()
        try:
            return float(val) / 100
        except:
            return 0.05
    
    def _safe_float(self, val) -> float:
        """安全转float"""
        try:
            if val is None:
                return 0.0
            if isinstance(val, str):
                val = val.replace('$', '').replace(',', '').strip()
            return float(val)
        except:
            return 0.0
    
    def _safe_int(self, val) -> int:
        """安全转int"""
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
    """便捷函数：生成精算师报告"""
    generator = ActuaryReportGenerator()
    html = generator.generate_actuary_report(asin, product_data, factors, market_report)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path
