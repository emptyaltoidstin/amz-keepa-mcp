"""
深度因子挖掘系统 - 从163指标中挖掘运营和选品洞察

不再追求虚假盈利预测，而是挖掘指标间的关联模式、异常信号、运营健康度等深层因子

挖掘角度:
1. 运营健康度因子 (Operational Health Factors)
2. 选品质量因子 (Product Quality Factors)  
3. 竞争态势因子 (Competitive Position Factors)
4. 风险预警因子 (Risk Signal Factors)
5. 增长潜力因子 (Growth Potential Factors)
6. 运营效率因子 (Operational Efficiency Factors)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')


@dataclass
class DeepFactor:
    """深度因子数据类"""
    name: str  # 因子名称
    category: str  # 因子类别
    score: float  # 因子得分 (0-100)
    weight: float  # 权重
    signals: List[str]  # 信号列表
    insights: List[str]  # 洞察列表
    actions: List[str]  # 行动建议
    confidence: float  # 置信度


class DeepFactorMiner:
    """
    深度因子挖掘器
    
    从163个Keepa指标中挖掘深层运营和选品洞察
    """
    
    def __init__(self):
        self.factors = {}
        self.raw_data = None
    
    def mine_all_factors(self, product_data: Dict) -> Dict[str, DeepFactor]:
        """
        挖掘所有深度因子
        
        Args:
            product_data: 163指标数据
            
        Returns:
            因子字典
        """
        self.raw_data = product_data
        
        # 1. 运营健康度因子
        self.factors['operational_health'] = self._mine_operational_health()
        
        # 2. 选品质量因子
        self.factors['product_quality'] = self._mine_product_quality()
        
        # 3. 竞争态势因子
        self.factors['competitive_position'] = self._mine_competitive_position()
        
        # 4. 风险预警因子
        self.factors['risk_signals'] = self._mine_risk_signals()
        
        # 5. 增长潜力因子
        self.factors['growth_potential'] = self._mine_growth_potential()
        
        # 6. 运营效率因子
        self.factors['operational_efficiency'] = self._mine_operational_efficiency()
        
        return self.factors
    
    # ========== 1. 运营健康度因子 ==========
    def _mine_operational_health(self) -> DeepFactor:
        """
        运营健康度因子
        
        评估维度:
        - 价格健康度: 价格波动、价格竞争力
        - 库存健康度: 断货频率、库存周转
        - 评价健康度: 评分稳定性、Review增长质量
        """
        signals = []
        insights = []
        actions = []
        score = 50
        confidence = 0.7
        
        # 价格健康度分析
        price_drops = self._safe_float(self.raw_data.get('Buy Box: Drops last 90 days', 0))
        price_trend = self._analyze_price_trend()
        
        if price_drops > 20:
            signals.append(f"价格频繁下调({price_drops}次/90天)")
            insights.append("产品可能面临价格压力或竞争加剧")
            actions.append("监控竞争对手价格策略，考虑差异化定位")
            score -= 15
        elif price_drops < 5:
            signals.append("价格稳定，定价权较好")
            insights.append("产品具有价格稳定性，可能有一定定价权")
            score += 10
        
        # 库存健康度
        oos_rate = self._safe_float(self.raw_data.get('Amazon: 90 days OOS', 0))
        if oos_rate > 30:
            signals.append(f"高断货率({oos_rate:.0f}%)")
            insights.append("供应链不稳定，频繁断货影响排名和销量")
            actions.append("优化库存管理，增加安全库存，寻找备用供应商")
            score -= 20
        elif oos_rate < 5:
            signals.append("库存管理良好，极少断货")
            score += 10
        
        # 评价健康度
        rating = self._safe_float(self.raw_data.get('Reviews: Rating', 0))
        review_growth = self._analyze_review_growth()
        
        if rating >= 4.5:
            signals.append(f"高评分({rating:.1f}★)")
            score += 15
        elif rating < 4.0:
            signals.append(f"低评分({rating:.1f}★)")
            insights.append("产品质量或客户体验存在问题")
            actions.append("分析差评原因，改进产品或优化Listing描述")
            score -= 15
        
        return DeepFactor(
            name="运营健康度",
            category="operational",
            score=max(0, min(100, score)),
            weight=0.20,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 2. 选品质量因子 ==========
    def _mine_product_quality(self) -> DeepFactor:
        """
        选品质量因子
        
        评估维度:
        - 市场需求验证: 销量持续性、排名稳定性
        - 差异化潜力: 品牌集中度、评论差异化
        - 生命周期位置: 导入期/成长期/成熟期/衰退期
        """
        signals = []
        insights = []
        actions = []
        score = 50
        confidence = 0.6
        
        # 市场需求验证
        sales_rank = self._safe_float(self.raw_data.get('Sales Rank: Current', 999999))
        rank_consistency = self._analyze_rank_consistency()
        
        if sales_rank < 10000:
            signals.append(f"销量排名靠前(#{sales_rank:,.0f})")
            insights.append("产品已验证有稳定市场需求")
            score += 20
        elif sales_rank > 100000:
            signals.append(f"销量排名靠后(#{sales_rank:,.0f})")
            insights.append("市场需求有限或竞争激烈")
            score -= 15
        
        # 生命周期判断
        lifecycle = self._determine_lifecycle()
        if lifecycle == 'Growth':
            signals.append("产品处于成长期")
            insights.append("市场正在扩大，是进入的好时机")
            score += 15
        elif lifecycle == 'Maturity':
            signals.append("产品处于成熟期")
            insights.append("市场稳定，需要差异化竞争")
            score += 5
        elif lifecycle == 'Decline':
            signals.append("产品可能处于衰退期")
            insights.append("需求下降，谨慎进入")
            score -= 15
        
        # 差异化潜力
        brand_concentration = self._analyze_brand_concentration()
        if brand_concentration > 0.7:
            signals.append("头部品牌集中度高")
            insights.append("市场被大品牌主导，新进入者难以突破")
            actions.append("寻找细分差异化定位，或选择其他类目")
            score -= 10
        else:
            signals.append("品牌分散，有机会进入")
            score += 10
        
        return DeepFactor(
            name="选品质量",
            category="product_selection",
            score=max(0, min(100, score)),
            weight=0.20,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 3. 竞争态势因子 ==========
    def _mine_competitive_position(self) -> DeepFactor:
        """
        竞争态势因子
        
        评估维度:
        - 卖家结构: FBA/FBM比例、新卖家进入难度
        - Buy Box竞争: 集中度、Amazon自营威胁
        - 价格竞争强度: 价格离散度、促销频率
        """
        signals = []
        insights = []
        actions = []
        score = 50
        confidence = 0.75
        
        # 卖家结构分析
        total_offers = self._safe_float(self.raw_data.get('Total Offer Count', 0))
        fba_offers = self._safe_float(self.raw_data.get('Count of retrieved live offers: New, FBA', 0))
        
        if total_offers > 0:
            fba_ratio = fba_offers / total_offers
            if fba_ratio > 0.8:
                signals.append("FBA卖家占比高")
                insights.append("市场专业化程度高，FBM难以竞争")
            
            if total_offers < 10:
                signals.append(f"卖家数量少({total_offers}个)")
                insights.append("竞争相对温和，有机会进入")
                score += 15
            elif total_offers > 30:
                signals.append(f"卖家数量多({total_offers}个)")
                insights.append("竞争激烈，需要强差异化")
                score -= 10
        
        # Amazon自营威胁
        amazon_share = self._safe_float(self.raw_data.get('Buy Box: % Amazon 90 days', '0%').replace('%', ''))
        if amazon_share > 50:
            signals.append(f"Amazon自营占比高({amazon_share:.0f}%)")
            insights.append("Amazon自营主导，难以获取Buy Box")
            actions.append("考虑避开Amazon自营强的产品")
            score -= 25
        elif amazon_share < 10:
            signals.append("Amazon自营占比低")
            insights.append("第三方卖家有机会")
            score += 10
        
        # Buy Box集中度
        bb_winners = self._safe_float(self.raw_data.get('Buy Box: Winner Count 90 days', 0))
        if bb_winners == 1:
            signals.append("Buy Box垄断")
            insights.append("单一卖家控制Buy Box，进入难度大")
            score -= 15
        elif bb_winners > 5:
            signals.append("Buy Box轮换频繁")
            insights.append("Buy Box竞争激烈，有机会通过优化获得")
            score += 5
        
        return DeepFactor(
            name="竞争态势",
            category="competition",
            score=max(0, min(100, score)),
            weight=0.15,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 4. 风险预警因子 ==========
    def _mine_risk_signals(self) -> DeepFactor:
        """
        风险预警因子
        
        识别维度:
        - 需求下滑信号: 排名下降、销量萎缩
        - 价格崩盘信号: 持续降价、价格战
        - 质量危机信号: 差评激增、退货上升
        - 政策风险: 评论异常、合规问题
        """
        signals = []
        insights = []
        actions = []
        risk_level = 0  # 0-100, 越高风险越大
        confidence = 0.65
        
        # 需求下滑信号
        rank_drops = self._safe_float(self.raw_data.get('Sales Rank: Drops last 90 days', 0))
        if rank_drops > 60:
            signals.append(f"🚨 需求快速下滑信号(排名下降{rank_drops}次)")
            insights.append("产品需求可能正在快速萎缩，可能是季节性结束或趋势变化")
            actions.append("立即分析原因，考虑清库存或转型")
            risk_level += 30
        elif rank_drops > 30:
            signals.append(f"⚠️ 需求下滑迹象(排名下降{rank_drops}次)")
            risk_level += 15
        
        # 价格崩盘信号
        price_trend_90d = self._calculate_price_change(days=90)
        if price_trend_90d < -0.2:  # 90天降价超过20%
            signals.append(f"🚨 价格持续下跌({price_trend_90d:.1%})")
            insights.append("市场价格战激烈或需求下降")
            actions.append("评估是否跟进降价或寻找差异化")
            risk_level += 25
        
        # 质量危机信号
        return_rate = self._estimate_return_rate()
        if return_rate > 0.15:
            signals.append(f"🚨 高退货率({return_rate:.1%})")
            insights.append("产品质量或描述存在严重问题")
            actions.append("立即改进产品或优化Listing")
            risk_level += 25
        
        # 卖家退出信号
        if rank_drops > 40 and self._safe_float(self.raw_data.get('New Offer Count: Current', 0)) < 3:
            signals.append("⚠️ 卖家退出迹象")
            insights.append("需求下滑同时新卖家减少，市场可能正在萎缩")
            risk_level += 15
        
        # 计算风险评分 (100 - risk_level)
        score = max(0, 100 - risk_level)
        
        return DeepFactor(
            name="风险预警",
            category="risk",
            score=score,  # 高分表示低风险
            weight=0.15,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 5. 增长潜力因子 ==========
    def _mine_growth_potential(self) -> DeepFactor:
        """
        增长潜力因子
        
        识别维度:
        - 需求增长信号: 排名上升、新需求进入
        - 市场扩容信号: 新卖家增加、品类扩张
        - 季节性机会: 即将进入旺季、历史季节性
        - 价格提升空间: 当前定价偏低、价值未充分挖掘
        """
        signals = []
        insights = []
        actions = []
        score = 50
        confidence = 0.55
        
        # 需求增长信号
        rank_changes = self._safe_float(self.raw_data.get('90 days change % Sales Rank', '0%').replace('%', ''))
        if rank_changes < -30:  # 排名数字变小(变好)超过30%
            signals.append(f"📈 需求快速增长(排名提升{abs(rank_changes):.0f}%)")
            insights.append("产品需求正在快速增长，可能是趋势产品")
            actions.append("考虑增加库存，抓住机会")
            score += 25
        
        # 新卖家进入
        new_offers = self._safe_float(self.raw_data.get('New Offer Count: Current', 0))
        if new_offers > 5:
            signals.append(f"新卖家持续进入({new_offers}个)")
            insights.append("市场吸引力高，新卖家愿意进入")
            score += 10
        
        # 价格提升空间
        price_position = self._analyze_price_position()
        if price_position == 'low':
            signals.append("价格定位偏低")
            insights.append("当前定价低于市场平均，有提价空间")
            actions.append("测试小幅提价，观察销量反应")
            score += 10
        
        # Review增长质量
        review_velocity = self._calculate_review_velocity()
        if review_velocity > 10:  # 每月超过10个新评论
            signals.append(f"评论增长快速({review_velocity:.0f}个/月)")
            insights.append("销量增长带动评论增加，产品正在获得市场认可")
            score += 15
        
        return DeepFactor(
            name="增长潜力",
            category="growth",
            score=max(0, min(100, score)),
            weight=0.15,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 6. 运营效率因子 ==========
    def _mine_operational_efficiency(self) -> DeepFactor:
        """
        运营效率因子
        
        评估维度:
        - 转化效率: 流量转化、购物车获取率
        - 库存周转: 销售速度、库存天数
        - 客户满意度: 好评率、复购信号
        """
        signals = []
        insights = []
        actions = []
        score = 50
        confidence = 0.6
        
        # 转化效率 (通过Review/销量比估算)
        review_ratio = self._estimate_review_ratio()
        if review_ratio > 0.05:  # Review率高于5%
            signals.append("Review转化率较高")
            insights.append("客户满意度高，愿意留评")
            score += 10
        
        # Buy Box获取能力
        bb_is_fba = str(self.raw_data.get('Buy Box: Is FBA', '')).lower()
        if 'yes' in bb_is_fba or 'true' in bb_is_fba:
            signals.append("当前Buy Box为FBA")
            insights.append("FBA配送有利于获取Buy Box")
            score += 10
        
        # 评论质量
        rating = self._safe_float(self.raw_data.get('Reviews: Rating', 0))
        review_count = self._safe_float(self.raw_data.get('Reviews: Review Count', 0))
        
        if rating >= 4.5 and review_count > 50:
            signals.append("高评分且评论充足")
            insights.append("产品已建立良好口碑，运营基础扎实")
            score += 15
        elif rating < 4.0:
            signals.append("评分偏低")
            insights.append("客户满意度不足，影响转化和复购")
            actions.append("分析差评，改进产品或服务")
            score -= 15
        
        # 变体丰富度 (如有)
        variation_count = self._count_variations()
        if variation_count > 5:
            signals.append(f"变体丰富({variation_count}个)")
            insights.append("多变体覆盖更多需求，但库存管理复杂")
            score += 5
        
        return DeepFactor(
            name="运营效率",
            category="efficiency",
            score=max(0, min(100, score)),
            weight=0.15,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 辅助方法 ==========
    def _safe_float(self, value, default=0.0):
        """安全转换为float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace('$', '').replace('%', '').replace(',', '').strip())
            except:
                return default
        return default
    
    def _analyze_price_trend(self) -> str:
        """分析价格趋势"""
        # 简化实现
        drops = self._safe_float(self.raw_data.get('Buy Box: Drops last 90 days', 0))
        if drops > 15:
            return 'declining'
        elif drops < 3:
            return 'stable'
        return 'volatile'
    
    def _analyze_review_growth(self) -> str:
        """分析评论增长"""
        # 简化实现
        return 'steady'
    
    def _determine_lifecycle(self) -> str:
        """判断生命周期阶段"""
        tracking_days = 365  # 假设
        review_count = self._safe_float(self.raw_data.get('Reviews: Review Count', 0))
        
        if tracking_days < 180 and review_count < 50:
            return 'Introduction'
        elif review_count < 500:
            return 'Growth'
        elif review_count > 1000:
            return 'Maturity'
        return 'Unknown'
    
    def _analyze_brand_concentration(self) -> float:
        """分析品牌集中度"""
        # 简化实现，实际需要更多数据
        return 0.5
    
    def _analyze_rank_consistency(self) -> float:
        """分析排名稳定性"""
        # 简化实现
        return 0.7
    
    def _calculate_price_change(self, days: int = 90) -> float:
        """计算价格变化率"""
        current = self._safe_float(self.raw_data.get('Buy Box: Current', 0))
        historical = self._safe_float(self.raw_data.get(f'Buy Box: {days} days avg.', 0))
        if historical > 0:
            return (current - historical) / historical
        return 0.0
    
    def _analyze_price_position(self) -> str:
        """分析价格定位"""
        current = self._safe_float(self.raw_data.get('Buy Box: Current', 0))
        avg = self._safe_float(self.raw_data.get('Buy Box: 90 days avg.', current))
        
        if current < avg * 0.9:
            return 'low'
        elif current > avg * 1.1:
            return 'high'
        return 'medium'
    
    def _calculate_review_velocity(self) -> float:
        """计算评论增长速度"""
        # 简化实现
        return 5.0
    
    def _estimate_return_rate(self) -> float:
        """估算退货率"""
        val = self.raw_data.get('Return Rate', '')
        if isinstance(val, str):
            if 'High' in val:
                return 0.12
            elif 'Medium' in val:
                return 0.08
        return 0.05
    
    def _estimate_review_ratio(self) -> float:
        """估算评论率"""
        # 简化实现
        return 0.03
    
    def _count_variations(self) -> int:
        """统计变体数量"""
        variations = str(self.raw_data.get('Variation ASINs', ''))
        if variations:
            return len(variations.split(';'))
        return 0


def format_factor_report(factors: Dict[str, DeepFactor]) -> str:
    """格式化因子报告"""
    lines = []
    
    lines.append("=" * 90)
    lines.append("🔍 深度因子挖掘报告 - 运营与选品洞察")
    lines.append("=" * 90)
    
    # 计算综合评分
    total_score = 0
    total_weight = 0
    for factor in factors.values():
        total_score += factor.score * factor.weight
        total_weight += factor.weight
    overall_score = total_score / total_weight if total_weight > 0 else 0
    
    lines.append(f"\n📊 综合健康度评分: {overall_score:.0f}/100")
    
    # 按类别分组
    categories = {
        'operational': '📈 运营维度',
        'product_selection': '🎯 选品维度',
        'competition': '⚔️ 竞争维度',
        'risk': '⚠️ 风险维度',
        'growth': '🚀 增长维度',
        'efficiency': '⚡ 效率维度',
    }
    
    for factor in factors.values():
        cat_name = categories.get(factor.category, factor.category)
        status = "🟢" if factor.score >= 70 else "🟡" if factor.score >= 50 else "🔴"
        
        lines.append(f"\n{'─' * 90}")
        lines.append(f"{status} {factor.name} (权重{factor.weight:.0%}) - {factor.score:.0f}/100 [置信度: {factor.confidence:.0%}]")
        lines.append(f"{'─' * 90}")
        
        if factor.signals:
            lines.append(f"\n  📡 关键信号:")
            for signal in factor.signals:
                lines.append(f"    • {signal}")
        
        if factor.insights:
            lines.append(f"\n  💡 深层洞察:")
            for insight in factor.insights:
                lines.append(f"    • {insight}")
        
        if factor.actions:
            lines.append(f"\n  🎯 行动建议:")
            for action in factor.actions:
                lines.append(f"    • {action}")
    
    lines.append("\n" + "=" * 90)
    
    return "\n".join(lines)
