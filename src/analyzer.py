"""
产品分析器
基于 Keepa 数据框架进行深度分析
"""

import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Risk:
    """风险项"""
    type: str
    level: RiskLevel
    description: str
    recommendation: str


class ProductAnalyzer:
    """
    Amazon FBA 产品分析器
    
    基于 Keepa 数据进行多维度分析:
    1. 盈利能力分析
    2. 竞争分析
    3. 销售趋势分析
    4. 风险评估
    5. 机会评分
    """
    
    def __init__(self):
        # 权重配置
        self.weights = {
            'profitability': 0.25,
            'competition': 0.20,
            'sales': 0.20,
            'reviews': 0.15,
            'sustainability': 0.20,
        }
    
    def calculate_opportunity_score(self, data: Dict) -> int:
        """
        计算综合机会评分 (0-100)
        
        评分维度:
        - 盈利能力 (25%)
        - 竞争程度 (20%)
        - 销售潜力 (20%)
        - 评论质量 (15%)
        - 可持续性 (20%)
        """
        scores = {
            'profitability': self._score_profitability(data),
            'competition': self._score_competition(data),
            'sales': self._score_sales(data),
            'reviews': self._score_reviews(data),
            'sustainability': self._score_sustainability(data),
        }
        
        # 加权计算
        total_score = sum(
            scores[key] * self.weights[key]
            for key in scores
        )
        
        return min(100, max(0, int(total_score)))
    
    def _score_profitability(self, data: Dict) -> float:
        """盈利能力评分"""
        margin = data.get('estimated_margin', 0) or 0
        
        if margin >= 40:
            return 100
        elif margin >= 30:
            return 80 + (margin - 30) * 2
        elif margin >= 20:
            return 60 + (margin - 20) * 2
        elif margin >= 10:
            return 40 + (margin - 10) * 2
        else:
            return max(0, margin * 4)
    
    def _score_competition(self, data: Dict) -> float:
        """竞争程度评分"""
        offers = data.get('current_offers', 100) or 100
        
        if offers <= 3:
            return 95  # 低竞争
        elif offers <= 8:
            return 85 - (offers - 3) * 2
        elif offers <= 15:
            return 70 - (offers - 8) * 1.5
        elif offers <= 25:
            return 50 - (offers - 15) * 1.5
        else:
            return max(10, 30 - (offers - 25))
    
    def _score_sales(self, data: Dict) -> float:
        """销售潜力评分"""
        rank = data.get('avg_rank', 500000) or 500000
        
        if rank < 1000:
            return 100
        elif rank < 5000:
            return 90
        elif rank < 10000:
            return 80
        elif rank < 50000:
            return 70
        elif rank < 100000:
            return 60
        elif rank < 200000:
            return 45
        elif rank < 500000:
            return 30
        else:
            return 15
    
    def _score_reviews(self, data: Dict) -> float:
        """评论质量评分"""
        rating = data.get('current_rating', 0) or 0
        review_count = data.get('total_reviews', 0) or 0
        
        # 评分基础分
        if rating >= 4.5:
            base_score = 100
        elif rating >= 4.0:
            base_score = 85
        elif rating >= 3.5:
            base_score = 70
        elif rating >= 3.0:
            base_score = 50
        else:
            base_score = 30
        
        # 评论数调整
        if review_count < 10:
            return base_score * 0.7  # 评论太少
        elif review_count < 50:
            return base_score * 0.85
        elif review_count > 1000:
            return base_score * 0.95  # 评论太多，竞争激烈
        
        return base_score
    
    def _score_sustainability(self, data: Dict) -> float:
        """可持续性评分"""
        score = 70  # 基础分
        
        # 价格稳定性
        stability = data.get('price_stability', '')
        if '非常稳定' in stability:
            score += 10
        elif '波动较大' in stability:
            score -= 15
        
        # 断货情况
        stockout_days = data.get('out_of_stock_days', 0) or 0
        if stockout_days > 10:
            score -= 20
        elif stockout_days > 5:
            score -= 10
        
        # 排名趋势
        rank_trend = data.get('rank_trend', '')
        if '上升' in rank_trend:
            score += 10
        elif '下降' in rank_trend:
            score -= 15
        
        # 亚马逊自营
        if data.get('is_amazon_selling'):
            score -= 10
        
        return min(100, max(0, score))
    
    def detect_risks(self, data: Dict) -> List[Risk]:
        """
        检测潜在风险
        
        检测以下风险模式:
        1. 高利润 + 低竞争 + 无品牌 = 陷阱
        2. 高评分 + 销量暴跌 = 异常
        3. 频繁断货 = 供应链问题
        4. 价格频繁大幅波动 = 价格战
        5. 亚马逊自营占比高 = 难竞争
        """
        risks = []
        
        # 风险 1: 高利润 + 低竞争 + 无品牌
        margin = data.get('estimated_margin', 0) or 0
        offers = data.get('current_offers', 100) or 100
        brand = data.get('brand', '').lower()
        
        if margin > 35 and offers < 5 and (not brand or brand in ['generic', 'unknown', 'n/a']):
            risks.append(Risk(
                type="利润陷阱",
                level=RiskLevel.HIGH,
                description="高利润率但低竞争且无品牌，可能存在隐藏缺陷或合规问题",
                recommendation="仔细检查产品评论，搜索相关法规，验证供应商资质"
            ))
        
        # 风险 2: 高评分 + 销量下降
        rating = data.get('current_rating', 0) or 0
        rank_trend = data.get('rank_trend', '')
        
        if rating >= 4.5 and '下降' in rank_trend:
            risks.append(Risk(
                type="销量异常",
                level=RiskLevel.MEDIUM,
                description="评分高但销量下降，可能遇到新竞争或季节性影响",
                recommendation="分析评论情感，检查是否有新竞品进入市场"
            ))
        
        # 风险 3: 频繁断货
        stockout_days = data.get('out_of_stock_days', 0) or 0
        stockouts_count = data.get('stockouts_count', 0) or 0
        
        if stockout_days > 7 or stockouts_count > 3:
            risks.append(Risk(
                type="供应链风险",
                level=RiskLevel.HIGH,
                description=f"过去90天断货 {stockout_days} 天，断货 {stockouts_count} 次",
                recommendation="确保有可靠的备用供应商，评估供应链稳定性"
            ))
        
        # 风险 4: 价格战
        price_drops = data.get('price_drops_count', 0) or 0
        price_volatility = data.get('price_volatility', 0) or 0
        
        if price_drops > 5 or price_volatility > 30:
            risks.append(Risk(
                type="价格战风险",
                level=RiskLevel.MEDIUM,
                description=f"价格频繁波动 ({price_drops} 次大幅下降，波动率 {price_volatility}%)",
                recommendation="谨慎定价，准备应对价格竞争，考虑差异化策略"
            ))
        
        # 风险 5: 亚马逊自营竞争
        if data.get('is_amazon_selling'):
            amazon_prices = data.get('amazon_price_history', [])
            if len(amazon_prices) > 10:
                risks.append(Risk(
                    type="亚马逊自营竞争",
                    level=RiskLevel.MEDIUM,
                    description="亚马逊正在销售该产品，Buy Box 难以获取",
                    recommendation="评估是否能提供比亚马逊更好的服务或价格"
                ))
        
        # 风险 6: 评论增长异常
        reviews_30d = data.get('reviews_30d', 0) or 0
        total_reviews = data.get('total_reviews', 0) or 0
        
        if total_reviews > 100 and reviews_30d == 0:
            risks.append(Risk(
                type="评论增长停滞",
                level=RiskLevel.LOW,
                description="产品评论数多但近期无新增，可能销量停滞",
                recommendation="验证产品是否还在正常销售"
            ))
        
        # 风险 7: 低评分
        if rating < 3.5:
            risks.append(Risk(
                type="产品质量问题",
                level=RiskLevel.CRITICAL,
                description=f"产品评分仅 {rating}，存在质量问题",
                recommendation="不建议进入，或寻找改进版本"
            ))
        
        # 风险 8: 竞争过度
        if offers > 25:
            risks.append(Risk(
                type="竞争过度",
                level=RiskLevel.HIGH,
                description=f"有 {offers} 个卖家，竞争非常激烈",
                recommendation="考虑差异化或寻找细分市场"
            ))
        
        return risks
    
    def generate_recommendations(self, data: Dict, risks: List[Risk]) -> List[str]:
        """生成投资建议"""
        recommendations = []
        
        score = self.calculate_opportunity_score(data)
        
        # 基于评分的总体建议
        if score >= 80:
            recommendations.append("✅ 强烈推荐: 这是一个优质机会，建议尽快行动")
        elif score >= 60:
            recommendations.append("⚠️ 可以考虑: 有一定潜力，但需谨慎评估风险")
        elif score >= 40:
            recommendations.append("❓ 观望: 条件一般，建议等待更好机会或进一步研究")
        else:
            recommendations.append("❌ 不推荐: 风险较高，建议放弃")
        
        # 基于数据的专项建议
        margin = data.get('estimated_margin', 0) or 0
        if margin > 30:
            recommendations.append(f"💰 利润空间充足 ({margin}%)，有足够的降价空间")
        elif margin < 20:
            recommendations.append(f"⚠️ 利润空间有限 ({margin}%)，需要精确控制成本")
        
        offers = data.get('current_offers', 100) or 100
        if offers < 5:
            recommendations.append("🎯 竞争较少，有机会获取 Buy Box")
        elif offers > 20:
            recommendations.append("🔥 竞争激烈，需要强力差异化策略")
        
        rank_trend = data.get('rank_trend', '')
        if '上升' in rank_trend:
            recommendations.append("📈 销量上升趋势，市场需求增长")
        elif '下降' in rank_trend:
            recommendations.append("📉 销量下降，需要分析原因")
        
        stockout_days = data.get('out_of_stock_days', 0) or 0
        if stockout_days > 5:
            recommendations.append("📦 供应链不稳定，务必准备备用供应商")
        
        # 针对风险的特殊建议
        if risks:
            high_risks = [r for r in risks if r.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
            if high_risks:
                recommendations.append("🚨 存在高风险因素，决策前务必验证")
        
        return recommendations
    
    def analyze_market_position(self, data: Dict) -> Dict[str, Any]:
        """分析市场定位"""
        return {
            'price_position': self._analyze_price_position(data),
            'competitive_position': self._analyze_competitive_position(data),
            'quality_position': self._analyze_quality_position(data),
        }
    
    def _analyze_price_position(self, data: Dict) -> str:
        """分析价格定位"""
        avg_price = data.get('avg_price', 0) or 0
        
        if avg_price < 10:
            return "低价区间"
        elif avg_price < 25:
            return "中低价位"
        elif avg_price < 50:
            return "中价位 (推荐)"
        elif avg_price < 100:
            return "中高价位"
        else:
            return "高价位"
    
    def _analyze_competitive_position(self, data: Dict) -> str:
        """分析竞争定位"""
        offers = data.get('current_offers', 0) or 0
        
        if offers <= 3:
            return "蓝海市场"
        elif offers <= 8:
            return "低竞争"
        elif offers <= 15:
            return "中等竞争"
        elif offers <= 25:
            return "高竞争"
        else:
            return "红海市场"
    
    def _analyze_quality_position(self, data: Dict) -> str:
        """分析质量定位"""
        rating = data.get('current_rating', 0) or 0
        
        if rating >= 4.5:
            return "优质产品"
        elif rating >= 4.0:
            return "良好"
        elif rating >= 3.5:
            return "一般"
        else:
            return "质量堪忧"
    
    def generate_quick_screening_report(self, data: Dict) -> Dict[str, Any]:
        """
        生成快速筛选报告 (30秒快速评估)
        
        Returns:
            包含关键决策信息的字典
        """
        margin = data.get('estimated_margin', 0) or 0
        offers = data.get('current_offers', 100) or 100
        rank_trend = data.get('rank_trend', '')
        
        checks = {
            'margin_ok': margin >= 20,
            'competition_ok': offers < 20,
            'trend_ok': '下降' not in rank_trend,
        }
        
        # 快速决策
        if all(checks.values()):
            decision = "PASS - 进入深度分析"
        elif checks['margin_ok'] and checks['competition_ok']:
            decision = "MAYBE - 需要进一步分析趋势"
        else:
            decision = "REJECT - 不满足基本条件"
        
        return {
            'decision': decision,
            'checks': checks,
            'margin': margin,
            'offers': offers,
            'rank_trend': rank_trend,
            'quick_score': self.calculate_opportunity_score(data),
        }
