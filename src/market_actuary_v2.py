"""
市场精算师 V2 - 重新定义价值主张

承认现实: Keepa数据无法准确预测盈利，因为核心成本数据缺失

新价值主张:
1. 市场侧分析 (Keepa强项) - 竞争格局、需求趋势、价格弹性
2. 盈利潜力评估 (估算+风险提示) - 给出可能性区间而非确定数字
3. 真实数据融合 (关键!) - 用户输入真实COGS后重新计算
4. 可行性筛选 - 快速排除明显不合适的品类

不再夸大: "精算级盈利预测" → 改为 "市场可行性分析 + 盈利潜力评估"
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketFeasibilityScore:
    """市场可行性评分"""
    demand_score: float  # 需求强度 (0-100)
    competition_score: float  # 竞争可进入性 (0-100)
    price_stability_score: float  # 价格稳定性 (0-100)
    supply_chain_score: float  # 供应链可行性 (0-100)
    
    overall_score: float  # 综合评分
    recommendation: str  # 建议: Go / Caution / No-Go
    key_risks: List[str]  # 主要风险点


class MarketActuaryV2:
    """
    市场精算师 V2 - 诚实的价值主张
    
    核心功能:
    1. 基于Keepa数据的市场可行性分析 (可靠)
    2. 盈利潜力区间估算 (带明确风险提示)
    3. 真实COGS输入后的精确计算 (需要用户数据)
    4. 类目对比筛选 (相对评估)
    """
    
    def __init__(self):
        self.disclaimer = """
        ⚠️ 重要提示: 
        本分析基于Keepa公开市场数据，无法获取您的真实COGS、运营成本等数据。
        盈利估算仅供参考，实际盈亏取决于您的供应链能力和运营效率。
        建议结合真实财务数据进行最终决策。
        """
    
    def analyze_market_feasibility(self, product_data: Dict) -> MarketFeasibilityScore:
        """
        1. 市场可行性分析 (基于Keepa数据，相对可靠)
        
        评估维度:
        - 需求强度: 排名趋势、销量稳定性
        - 竞争可进入性: 卖家集中度、新卖家机会
        - 价格稳定性: 价格波动、价格战风险
        - 供应链可行性: 尺寸重量、库存周转
        """
        # 需求强度评分
        demand_score = self._calculate_demand_score(product_data)
        
        # 竞争可进入性评分
        competition_score = self._calculate_competition_score(product_data)
        
        # 价格稳定性评分
        price_stability_score = self._calculate_price_stability(product_data)
        
        # 供应链可行性评分
        supply_chain_score = self._calculate_supply_chain_feasibility(product_data)
        
        # 综合评分
        overall_score = (
            demand_score * 0.30 +
            competition_score * 0.25 +
            price_stability_score * 0.25 +
            supply_chain_score * 0.20
        )
        
        # 生成建议
        recommendation = self._generate_recommendation(overall_score, {
            'demand': demand_score,
            'competition': competition_score,
            'price': price_stability_score,
            'supply': supply_chain_score
        })
        
        key_risks = self._identify_key_risks(product_data, {
            'demand': demand_score,
            'competition': competition_score,
            'price': price_stability_score,
            'supply': supply_chain_score
        })
        
        return MarketFeasibilityScore(
            demand_score=demand_score,
            competition_score=competition_score,
            price_stability_score=price_stability_score,
            supply_chain_score=supply_chain_score,
            overall_score=overall_score,
            recommendation=recommendation,
            key_risks=key_risks
        )
    
    def estimate_profit_potential(self, 
                                 product_data: Dict,
                                 user_cogs: Optional[float] = None) -> Dict:
        """
        2. 盈利潜力评估 (区间估算 + 明确风险提示)
        
        如果用户提供了真实COGS，给出精确计算
        如果只有Keepa数据，给出可能性区间并明确标注不确定性
        """
        current_price = self._extract_price(product_data)
        
        if user_cogs:
            # 用户提供了真实COGS - 可以给出相对准确的估算
            return self._calculate_with_real_cogs(current_price, user_cogs, product_data)
        else:
            # 没有真实COGS - 给出可能性区间
            return self._estimate_profit_range(current_price, product_data)
    
    def _estimate_profit_range(self, price: float, product_data: Dict) -> Dict:
        """
        没有真实COGS时的盈利潜力区间估算
        
        基于类目给出COGS率的合理区间，而非固定值
        """
        category = product_data.get('Categories: Root', '')
        
        # 基于类目给出COGS率区间 (这是估算，不是确定值!)
        cogs_ranges = {
            'Clothing, Shoes & Jewelry': (0.40, 0.70),
            'Health & Household': (0.30, 0.60),
            'Electronics': (0.50, 0.80),
            'Home & Kitchen': (0.35, 0.65),
            'Sports & Outdoors': (0.40, 0.70),
            'Beauty & Personal Care': (0.25, 0.55),
            'Toys & Games': (0.35, 0.65),
        }
        
        cogs_low, cogs_high = cogs_ranges.get(category, (0.35, 0.65))
        cogs_typical = (cogs_low + cogs_high) / 2
        
        # 其他成本 (相对确定的)
        fba_fee = self._estimate_fba_fee(product_data, price)
        referral_rate = 0.15
        referral_fee = price * referral_rate
        estimated_acos = 0.15  # 估算ACOS 15%，实际可能更高
        ad_cost = price * estimated_acos
        return_cost = price * 0.08 * 0.3  # 8%退货率，30%净损失
        storage_cost = 0.20
        
        # 计算不同COGS场景下的利润率
        def calc_margin(cogs_rate):
            cogs = price * cogs_rate
            total_cost = cogs + fba_fee + referral_fee + ad_cost + return_cost + storage_cost
            net_profit = price - total_cost
            return (net_profit / price * 100) if price > 0 else 0
        
        margin_best = calc_margin(cogs_low)  # 最佳情况 (供应链极强)
        margin_typical = calc_margin(cogs_typical)  # 典型情况
        margin_worst = calc_margin(cogs_high)  # 最差情况 (供应链弱)
        
        return {
            'disclaimer': '以下估算基于假设的COGS率区间，实际利润率取决于您的供应链能力',
            'cogs_assumption': {
                'category': category,
                'estimated_range': f"{cogs_low:.0%} - {cogs_high:.0%}",
                'typical': f"{cogs_typical:.0%}",
                'note': '此为市场常见区间，您的实际COGS可能高于或低于此范围'
            },
            'profit_scenarios': {
                'best_case': {
                    'cogs_rate': f"{cogs_low:.0%}",
                    'net_margin': f"{margin_best:.1f}%",
                    'description': '如果您有极强的供应链优势，能达到行业最低COGS'
                },
                'typical_case': {
                    'cogs_rate': f"{cogs_typical:.0%}",
                    'net_margin': f"{margin_typical:.1f}%",
                    'description': '行业平均水平，大多数卖家的COGS水平'
                },
                'worst_case': {
                    'cogs_rate': f"{cogs_high:.0%}",
                    'net_margin': f"{margin_worst:.1f}%",
                    'description': '如果您供应链较弱，COGS较高的情况'
                }
            },
            'key_uncertainties': [
                'COGS率: 实际可能高于/低于估算区间 ±20%',
                'ACOS: 估算15%，实际健康产品18-25%，竞争激烈产品30%+',
                '退货率: 估算8%，实际因产品质量差异可能达15-25%',
                '价格战: 未来价格下降风险未计入'
            ],
            'reliability_assessment': '中低 - 强烈建议输入真实COGS进行精确计算',
            'call_to_action': '如果您有真实COGS数据，请提供以获得精确分析'
        }
    
    def _calculate_with_real_cogs(self, price: float, cogs: float, product_data: Dict) -> Dict:
        """
        用户提供了真实COGS - 给出相对可靠的计算
        """
        cogs_rate = cogs / price if price > 0 else 0
        
        # 使用真实数据或合理估算
        fba_fee = self._estimate_fba_fee(product_data, price)
        referral_fee = price * 0.15
        
        # 从数据中获取或估算退货率
        return_rate = self._extract_return_rate(product_data)
        return_cost = price * return_rate * 0.3
        
        storage_cost = 0.20
        ad_cost = price * 0.18  # 假设ACOS 18%，略高于理想值
        
        total_cost = cogs + fba_fee + referral_fee + return_cost + storage_cost + ad_cost
        net_profit = price - total_cost
        net_margin = (net_profit / price * 100) if price > 0 else 0
        
        # 盈亏平衡分析
        monthly_fixed = 500  # 假设月固定成本
        break_even = monthly_fixed / net_profit if net_profit > 0 else float('inf')
        
        return {
            'disclaimer': '基于您提供的真实COGS计算，其他成本项为估算值',
            'real_cogs': {
                'value': f"${cogs:.2f}",
                'rate': f"{cogs_rate:.1%}",
                'assessment': '优秀' if cogs_rate < 0.35 else '良好' if cogs_rate < 0.50 else '一般' if cogs_rate < 0.65 else '偏高'
            },
            'cost_breakdown': {
                'cogs': f"${cogs:.2f} ({cogs_rate:.1%})",
                'fba_fee': f"${fba_fee:.2f}",
                'referral': f"${referral_fee:.2f} (15%)",
                'ad_cost': f"${ad_cost:.2f} (估算18% ACOS)",
                'return_cost': f"${return_cost:.2f} ({return_rate:.1%}退货率)",
                'storage': f"${storage_cost:.2f}",
                'total': f"${total_cost:.2f}"
            },
            'profit_calculation': {
                'net_margin': f"{net_margin:.1f}%",
                'net_profit_per_unit': f"${net_profit:.2f}",
                'break_even_units': f"{break_even:.0f}件/月" if break_even != float('inf') else '无法盈亏平衡',
                'assessment': '盈利' if net_margin > 15 else '微利' if net_margin > 5 else '亏损风险'
            },
            'sensitivities': {
                'if_acos_25': f"净利率降至 {net_margin - 7:.1f}%",
                'if_return_15': f"净利率降至 {net_margin - 2:.1f}%",
                'if_price_drop_10': f"净利率降至 {net_margin - 8:.1f}%"
            },
            'reliability_assessment': '中高 - 基于真实COGS，建议再核实广告和退货数据'
        }
    
    def generate_comprehensive_report(self, 
                                     product_data: Dict,
                                     user_cogs: Optional[float] = None) -> Dict:
        """
        生成综合分析报告
        """
        # 1. 市场可行性分析 (可靠)
        feasibility = self.analyze_market_feasibility(product_data)
        
        # 2. 盈利潜力评估 (区间或精确)
        profit_analysis = self.estimate_profit_potential(product_data, user_cogs)
        
        # 3. 最终建议
        final_recommendation = self._generate_final_recommendation(feasibility, profit_analysis)
        
        return {
            'disclaimer': self.disclaimer,
            'market_feasibility': {
                'overall_score': feasibility.overall_score,
                'recommendation': feasibility.recommendation,
                'dimension_scores': {
                    'demand': feasibility.demand_score,
                    'competition': feasibility.competition_score,
                    'price_stability': feasibility.price_stability_score,
                    'supply_chain': feasibility.supply_chain_score
                },
                'key_risks': feasibility.key_risks
            },
            'profit_analysis': profit_analysis,
            'final_recommendation': final_recommendation,
            'data_quality': {
                'has_real_cogs': user_cogs is not None,
                'profit_reliability': '高' if user_cogs else '中低 (区间估算)',
                'market_reliability': '高 (基于Keepa数据)'
            }
        }
    
    # Helper methods
    def _calculate_demand_score(self, data: Dict) -> float:
        """需求强度评分 (0-100)"""
        score = 50  # 基础分
        
        # 排名越低（数字越小）需求越强
        rank = self._extract_sales_rank(data)
        if rank < 1000:
            score += 30
        elif rank < 10000:
            score += 20
        elif rank < 50000:
            score += 10
        elif rank > 100000:
            score -= 20
        
        # 排名趋势
        rank_drops = data.get('Sales Rank: Drops last 90 days', 0)
        if isinstance(rank_drops, str):
            try:
                rank_drops = float(rank_drops)
            except:
                rank_drops = 0
        if isinstance(rank_drops, (int, float)):
            if rank_drops > 50:
                score -= 15  # 需求下降
            elif rank_drops < 20:
                score += 10  # 需求稳定或上升
        
        return max(0, min(100, score))
    
    def _calculate_competition_score(self, data: Dict) -> float:
        """竞争可进入性评分 (0-100)"""
        score = 50
        
        # 卖家数量
        offers = data.get('Total Offer Count', 0)
        if isinstance(offers, str):
            try:
                offers = int(offers)
            except:
                offers = 0
        if isinstance(offers, (int, float)):
            if offers < 5:
                score += 25
            elif offers < 15:
                score += 15
            elif offers > 30:
                score -= 20
        
        # Amazon自营占比
        amazon_pct = self._extract_amazon_share(data)
        if amazon_pct > 50:
            score -= 30
        elif amazon_pct > 30:
            score -= 15
        
        # Buy Box稳定性
        winners = data.get('Buy Box: Winner Count 90 days', 0)
        if isinstance(winners, str):
            try:
                winners = int(winners)
            except:
                winners = 0
        if isinstance(winners, (int, float)):
            if winners <= 3:
                score += 10
            elif winners > 10:
                score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_price_stability(self, data: Dict) -> float:
        """价格稳定性评分 (0-100)"""
        score = 50
        
        # 价格波动
        price_cv = data.get('Buy Box: Standard Deviation 90 days', 0)
        # 处理字符串类型(如'$ 3.38')
        if isinstance(price_cv, str):
            price_cv = price_cv.replace('$', '').replace(',', '').strip()
            try:
                price_cv = float(price_cv)
            except:
                price_cv = 0
        
        current_price = self._extract_price(data)
        if current_price > 0 and isinstance(price_cv, (int, float)):
            cv_ratio = price_cv / current_price
            if cv_ratio < 0.05:
                score += 25
            elif cv_ratio > 0.15:
                score -= 20
        
        # 价格战指标
        price_drops = data.get('Buy Box: Drops last 90 days', 0)
        if isinstance(price_drops, str):
            try:
                price_drops = int(price_drops)
            except:
                price_drops = 0
        if price_drops > 20:
            score -= 15
        
        return max(0, min(100, score))
    
    def _calculate_supply_chain_feasibility(self, data: Dict) -> float:
        """供应链可行性评分 (0-100)"""
        score = 60
        
        # 辅助函数: 安全转换为float
        def safe_float(val, default=0):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val.replace(',', ''))
                except:
                    return default
            return default
        
        # 尺寸重量
        weight = safe_float(data.get('Package: Weight (g)', 0))
        if weight > 0:
            if weight < 500:  # 轻小件
                score += 15
            elif weight > 2000:  # 重货
                score -= 10
        
        # 体积
        length = safe_float(data.get('Package: Length (cm)', 0))
        width = safe_float(data.get('Package: Width (cm)', 0))
        height = safe_float(data.get('Package: Height (cm)', 0))
        if length > 0 and width > 0 and height > 0:
            volume = length * width * height
            if volume < 1000:  # 小体积
                score += 10
            elif volume > 10000:  # 大体积
                score -= 10
        
        # 是否有断货历史
        oos = data.get('Amazon: 90 days OOS', 0)
        if isinstance(oos, str):
            try:
                oos = float(oos.replace('%', ''))
            except:
                oos = 0
        if isinstance(oos, (int, float)) and oos > 20:
            score -= 15  # 供应链不稳定
        
        return max(0, min(100, score))
    
    def _generate_recommendation(self, overall_score: float, dimension_scores: Dict) -> str:
        """生成可行性建议"""
        if overall_score >= 70:
            return "Go - 市场可行性高，值得深入调研"
        elif overall_score >= 50:
            if dimension_scores['competition'] < 40:
                return "Caution - 竞争激烈，需有差异化优势"
            elif dimension_scores['demand'] < 40:
                return "Caution - 需求不足，谨慎进入"
            else:
                return "Caution - 中等可行性，需进一步分析"
        else:
            return "No-Go - 市场可行性低，建议放弃"
    
    def _identify_key_risks(self, data: Dict, scores: Dict) -> List[str]:
        """识别主要风险"""
        risks = []
        
        if scores['demand'] < 40:
            risks.append("需求风险: 销量排名低或呈下降趋势")
        
        if scores['competition'] < 40:
            amazon_pct = self._extract_amazon_share(data)
            if amazon_pct > 30:
                risks.append(f"竞争风险: Amazon自营占比{amazon_pct:.0%}，难以获取Buy Box")
            else:
                risks.append("竞争风险: 卖家数量过多，价格战风险高")
        
        if scores['price'] < 40:
            risks.append("价格风险: 价格波动大或持续下降趋势")
        
        if scores['supply'] < 40:
            risks.append("供应链风险: 产品体积大或历史断货频繁")
        
        if not risks:
            risks.append("主要风险: 市场看似可行，但仍需验证真实盈利能力")
        
        return risks
    
    def _generate_final_recommendation(self, feasibility: MarketFeasibilityScore, profit: Dict) -> Dict:
        """生成最终综合建议"""
        
        # 市场可行性高 + 盈利潜力好 = 强烈推荐
        # 市场可行性高 + 盈利不确定 = 谨慎调研
        # 市场可行性低 = 建议放弃
        
        if feasibility.recommendation.startswith('Go'):
            if 'real_cogs' in profit:
                margin = float(profit['profit_calculation']['net_margin'].rstrip('%'))
                if margin > 20:
                    return {
                        'decision': '推荐深入',
                        'confidence': '高',
                        'rationale': '市场可行性好，且基于真实COGS预测盈利良好',
                        'next_steps': ['验证广告成本', '确认退货率', '小批量试销']
                    }
                elif margin > 10:
                    return {
                        'decision': '谨慎考虑',
                        'confidence': '中',
                        'rationale': '市场可行性好，但利润空间中等',
                        'next_steps': ['优化COGS', '控制广告成本', '小规模测试']
                    }
                else:
                    return {
                        'decision': '暂时观望',
                        'confidence': '中',
                        'rationale': '市场可行性好，但盈利空间有限',
                        'next_steps': ['大幅优化成本结构', '寻找差异化定位', '等待时机']
                    }
            else:
                return {
                    'decision': '值得调研',
                    'confidence': '中',
                    'rationale': '市场可行性高，但需要真实COGS数据确认盈利',
                    'next_steps': ['核算真实COGS', '获取样品测试', '调研供应商']
                }
        
        elif feasibility.recommendation.startswith('Caution'):
            return {
                'decision': '谨慎进入',
                'confidence': '低-中',
                'rationale': feasibility.key_risks[0] if feasibility.key_risks else '存在特定风险',
                'next_steps': ['针对性解决风险点', '评估自身竞争力', '小规模测试']
            }
        
        else:
            return {
                'decision': '建议放弃',
                'confidence': '高',
                'rationale': '市场可行性低，进入风险大于机会',
                'next_steps': ['寻找其他品类', '关注市场变化', '等待时机']
            }
    
    # Data extraction helpers
    def _extract_price(self, data: Dict) -> float:
        """提取价格"""
        for field in ['Buy Box: Current', 'New: Current', 'Amazon: Current']:
            val = data.get(field, 0)
            if val and str(val).replace('.', '').replace('-', '').isdigit():
                return float(val)
        return 0.0
    
    def _extract_sales_rank(self, data: Dict) -> int:
        """提取销售排名"""
        val = data.get('Sales Rank: Current', 0)
        try:
            return int(val)
        except:
            return 999999
    
    def _extract_amazon_share(self, data: Dict) -> float:
        """提取Amazon自营占比"""
        val = data.get('Buy Box: % Amazon 90 days', '0%')
        try:
            return float(val.replace('%', '')) / 100
        except:
            return 0.0
    
    def _extract_return_rate(self, data: Dict) -> float:
        """提取退货率"""
        val = data.get('Return Rate', '')
        if isinstance(val, str):
            if 'High' in val:
                return 0.12
            elif 'Medium' in val:
                return 0.08
        return 0.08  # 默认8%
    
    def _estimate_fba_fee(self, data: Dict, price: float) -> float:
        """估算FBA费用"""
        weight = data.get('Package: Weight (g)', 0) or 200
        if weight < 100:
            return 3.22
        elif weight < 500:
            return 4.50
        elif weight < 1000:
            return 6.10
        else:
            return 9.00


def format_v2_report(report: Dict) -> str:
    """格式化V2报告"""
    lines = []
    
    lines.append("=" * 90)
    lines.append("📊 市场精算师分析 V2 - 市场可行性评估报告")
    lines.append("=" * 90)
    
    lines.append(f"\n⚠️  {report['disclaimer']}")
    
    # 市场可行性
    mf = report['market_feasibility']
    lines.append(f"\n" + "─" * 90)
    lines.append(f"🎯 1. 市场可行性分析 (基于Keepa数据)")
    lines.append("─" * 90)
    lines.append(f"\n  综合评分: {mf['overall_score']:.0f}/100")
    lines.append(f"  建议: {mf['recommendation']}")
    lines.append(f"\n  维度评分:")
    lines.append(f"    需求强度: {mf['dimension_scores']['demand']:.0f}/100")
    lines.append(f"    竞争可进入: {mf['dimension_scores']['competition']:.0f}/100")
    lines.append(f"    价格稳定性: {mf['dimension_scores']['price_stability']:.0f}/100")
    lines.append(f"    供应链可行: {mf['dimension_scores']['supply_chain']:.0f}/100")
    lines.append(f"\n  主要风险:")
    for risk in mf['key_risks']:
        lines.append(f"    • {risk}")
    
    # 盈利分析
    lines.append(f"\n" + "─" * 90)
    lines.append(f"💰 2. 盈利潜力评估")
    lines.append("─" * 90)
    
    pa = report['profit_analysis']
    lines.append(f"\n  ⚠️ {pa['disclaimer']}")
    
    if 'real_cogs' in pa:
        lines.append(f"\n  基于真实COGS计算:")
        lines.append(f"    您的COGS: {pa['real_cogs']['value']} ({pa['real_cogs']['rate']}) - {pa['real_cogs']['assessment']}")
        lines.append(f"    净利率: {pa['profit_calculation']['net_margin']}")
        lines.append(f"    单件利润: {pa['profit_calculation']['net_profit_per_unit']}")
        lines.append(f"    盈亏平衡: {pa['profit_calculation']['break_even_units']}")
        lines.append(f"\n  成本结构:")
        for key, value in pa['cost_breakdown'].items():
            lines.append(f"    {key}: {value}")
        lines.append(f"\n  敏感性分析:")
        for key, value in pa['sensitivities'].items():
            lines.append(f"    {key}: {value}")
    else:
        lines.append(f"\n  COGS假设: {pa['cogs_assumption']['estimated_range']} (类目常见区间)")
        lines.append(f"\n  盈利情景分析:")
        for scenario, values in pa['profit_scenarios'].items():
            lines.append(f"\n    {scenario}:")
            lines.append(f"      COGS率: {values['cogs_rate']}")
            lines.append(f"      净利率: {values['net_margin']}")
            lines.append(f"      说明: {values['description']}")
        lines.append(f"\n  ⚠️ 关键不确定性:")
        for unc in pa['key_uncertainties']:
            lines.append(f"    • {unc}")
    
    # 最终建议
    lines.append(f"\n" + "─" * 90)
    lines.append(f"📋 3. 综合决策建议")
    lines.append("─" * 90)
    
    fr = report['final_recommendation']
    lines.append(f"\n  决策: {fr['decision']}")
    lines.append(f"  置信度: {fr['confidence']}")
    lines.append(f"  理由: {fr['rationale']}")
    lines.append(f"\n  下一步行动:")
    for step in fr['next_steps']:
        lines.append(f"    • {step}")
    
    lines.append(f"\n" + "=" * 90)
    
    return "\n".join(lines)
