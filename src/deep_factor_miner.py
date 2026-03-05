"""
Deep factor mining system - Mining operational and product selection insights from 163 indicators

No longer pursue false profit forecasts, but explore deep factors such as correlation patterns between indicators, abnormal signals, and operational health.

Digging angle:
1. Operational health factor (Operational Health Factors)
2. Product selection quality factor (Product Quality Factors)  
3. Competitive situation factors (Competitive Position Factors)
4. Risk warning factors (Risk Signal Factors)
5. Growth potential factor (Growth Potential Factors)
6. Operational efficiency factors (Operational Efficiency Factors)
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
    """Depth factor data class"""
    name: str  # factor name
    category: str  # factor category
    score: float  # factor score (0-100)
    weight: float  # weight
    signals: List[str]  # Signal list
    insights: List[str]  # Insight list
    actions: List[str]  # Suggestions for action
    confidence: float  # Confidence


class DeepFactorMiner:
    """
    Deep factor miner
    
    Mining deep operational and product selection insights from 163 Keepa indicators
    """
    
    def __init__(self):
        self.factors = {}
        self.raw_data = None
    
    def mine_all_factors(self, product_data: Dict) -> Dict[str, DeepFactor]:
        """
        Explore all depth factors
        
        Args:
            product_data: 163 indicator data
            
        Returns:
            factor dictionary
        """
        self.raw_data = product_data
        
        # 1. Operational health factor
        self.factors['operational_health'] = self._mine_operational_health()
        
        # 2. Product selection quality factor
        self.factors['product_quality'] = self._mine_product_quality()
        
        # 3. Competitive situation factors
        self.factors['competitive_position'] = self._mine_competitive_position()
        
        # 4. Risk warning factors
        self.factors['risk_signals'] = self._mine_risk_signals()
        
        # 5. Growth potential factor
        self.factors['growth_potential'] = self._mine_growth_potential()
        
        # 6. Operational efficiency factors
        self.factors['operational_efficiency'] = self._mine_operational_efficiency()
        
        return self.factors
    
    # ========== 1. Operational health factor ==========
    def _mine_operational_health(self) -> DeepFactor:
        """
        operational health factors
        
        Assessment Dimensions:
        - price health: Price fluctuations, price competitiveness
        - Inventory health: Out-of-stock frequency, inventory turnover
        - Evaluate health: Rating stability, Review growth quality
        """
        signals = []
        insights = []
        actions = []
        score = 50
        confidence = 0.7
        
        # Price health analysis
        price_drops = self._safe_float(self.raw_data.get('Buy Box: Drops last 90 days', 0))
        price_trend = self._analyze_price_trend()
        
        if price_drops > 20:
            signals.append(f"Frequent price cuts({price_drops}Second-rate/90 days)")
            insights.append("Products may face pricing pressure or increased competition")
            actions.append("Monitor competitor pricing strategies and consider differentiated positioning")
            score -= 15
        elif price_drops < 5:
            signals.append("Stable prices and good pricing power")
            insights.append("The product has price stability and may have certain pricing power")
            score += 10
        
        # Inventory health
        oos_rate = self._safe_float(self.raw_data.get('Amazon: 90 days OOS', 0))
        if oos_rate > 30:
            signals.append(f"High stockout rate({oos_rate:.0f}%)")
            insights.append("The supply chain is unstable and frequent out-of-stocks affect rankings and sales.")
            actions.append("Optimize inventory management, increase safety stock, and find backup suppliers")
            score -= 20
        elif oos_rate < 5:
            signals.append("Inventory is well managed and few out of stock items")
            score += 10
        
        # Evaluate health
        rating = self._safe_float(self.raw_data.get('Reviews: Rating', 0))
        review_growth = self._analyze_review_growth()
        
        if rating >= 4.5:
            signals.append(f"high rating({rating:.1f}★)")
            score += 15
        elif rating < 4.0:
            signals.append(f"low rating({rating:.1f}★)")
            insights.append("There are issues with product quality or customer experience")
            actions.append("Analyze the reasons for negative reviews, improve products or optimize listing descriptions")
            score -= 15
        
        return DeepFactor(
            name="operational health",
            category="operational",
            score=max(0, min(100, score)),
            weight=0.20,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 2. Product selection quality factor ==========
    def _mine_product_quality(self) -> DeepFactor:
        """
        Selection quality factor
        
        Assessment Dimensions:
        - Market demand verification: Sales continuity and ranking stability
        - Differentiation potential: Brand concentration and review differentiation
        - life cycle position: Introduction period/growth period/mature stage/recession period
        """
        signals = []
        insights = []
        actions = []
        score = 50
        confidence = 0.6
        
        # Market demand verification
        sales_rank = self._safe_float(self.raw_data.get('Sales Rank: Current', 999999))
        rank_consistency = self._analyze_rank_consistency()
        
        if sales_rank < 10000:
            signals.append(f"Top sales ranking(#{sales_rank:,.0f})")
            insights.append("The product has been proven to have stable market demand")
            score += 20
        elif sales_rank > 100000:
            signals.append(f"Sales volume ranks low(#{sales_rank:,.0f})")
            insights.append("Market demand is limited or competition is fierce")
            score -= 15
        
        # life cycle judgment
        lifecycle = self._determine_lifecycle()
        if lifecycle == 'Growth':
            signals.append("The product is in the growth stage")
            insights.append("The market is expanding and it’s a good time to enter")
            score += 15
        elif lifecycle == 'Maturity':
            signals.append("The product is in the mature stage")
            insights.append("The market is stable and requires differentiated competition")
            score += 5
        elif lifecycle == 'Decline':
            signals.append("Product may be in decline")
            insights.append("Demand drops, enter with caution")
            score -= 15
        
        # Differentiation potential
        brand_concentration = self._analyze_brand_concentration()
        if brand_concentration > 0.7:
            signals.append("High concentration of top brands")
            insights.append("The market is dominated by big brands, making it difficult for new entrants to break through")
            actions.append("Find segmented and differentiated positioning, or choose other categories")
            score -= 10
        else:
            signals.append("Brands are dispersed and there is an opportunity to enter")
            score += 10
        
        return DeepFactor(
            name="Selection quality",
            category="product_selection",
            score=max(0, min(100, score)),
            weight=0.20,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 3. Competitive situation factors ==========
    def _mine_competitive_position(self) -> DeepFactor:
        """
        competitive situation factors
        
        Assessment Dimensions:
        - Seller structure: FBA/FBM ratio, difficulty for new sellers to enter
        - Buy Box competition: Concentration, Amazon’s self-operated threats
        - intensity of price competition: Price dispersion, promotion frequency
        """
        signals = []
        insights = []
        actions = []
        score = 50
        confidence = 0.75
        
        # Seller structure analysis
        total_offers = self._safe_float(self.raw_data.get('Total Offer Count', 0))
        fba_offers = self._safe_float(self.raw_data.get('Count of retrieved live offers: New, FBA', 0))
        
        if total_offers > 0:
            fba_ratio = fba_offers / total_offers
            if fba_ratio > 0.8:
                signals.append("FBA sellers account for a high proportion")
                insights.append("The market is highly specialized and it is difficult for FBM to compete")
            
            if total_offers < 10:
                signals.append(f"Few sellers({total_offers}a)")
                insights.append("Competition is relatively mild and there is a chance to enter")
                score += 15
            elif total_offers > 30:
                signals.append(f"Many sellers({total_offers}a)")
                insights.append("Competition is fierce and differentiation is needed")
                score -= 10
        
        # Amazon self-operated threats
        amazon_share = self._safe_float(self.raw_data.get('Buy Box: % Amazon 90 days', '0%').replace('%', ''))
        if amazon_share > 50:
            signals.append(f"Amazon has a high proportion of self-operated products({amazon_share:.0f}%)")
            insights.append("Amazon is self-operated and it is difficult to obtain the Buy Box")
            actions.append("Consider avoiding Amazon’s self-operated products")
            score -= 25
        elif amazon_share < 10:
            signals.append("Amazon’s self-operated share is low")
            insights.append("Opportunities for third-party sellers")
            score += 10
        
        # Buy Box Concentration
        bb_winners = self._safe_float(self.raw_data.get('Buy Box: Winner Count 90 days', 0))
        if bb_winners == 1:
            signals.append("Buy BoxMonopoly")
            insights.append("A single seller controls the Buy Box, making it difficult to enter")
            score -= 15
        elif bb_winners > 5:
            signals.append("Buy Box rotates frequently")
            insights.append("Buy Box competition is fierce, there are opportunities to obtain through optimization")
            score += 5
        
        return DeepFactor(
            name="competitive situation",
            category="competition",
            score=max(0, min(100, score)),
            weight=0.15,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 4. Risk warning factors ==========
    def _mine_risk_signals(self) -> DeepFactor:
        """
        risk warning factors
        
        Identify dimensions:
        - Signal of declining demand: Ranking decline, sales shrinking
        - Price crash signal: Continuous price cuts and price wars
        - quality crisis signal: Negative reviews surge, returns rise
        - policy risk: Comment anomalies and compliance issues
        """
        signals = []
        insights = []
        actions = []
        risk_level = 0  # 0-100, The higher the risk, the greater the risk
        confidence = 0.65
        
        # Signal of declining demand
        rank_drops = self._safe_float(self.raw_data.get('Sales Rank: Drops last 90 days', 0))
        if rank_drops > 60:
            signals.append(f"🚨 Signal of rapid decline in demand(Ranking dropped{rank_drops}Second-rate)")
            insights.append("Product demand may be shrinking rapidly, possibly due to the end of seasonality or a change in trends")
            actions.append("Immediately analyze the reasons and consider inventory clearance or transformation")
            risk_level += 30
        elif rank_drops > 30:
            signals.append(f"⚠️ Signs of declining demand(Ranking dropped{rank_drops}Second-rate)")
            risk_level += 15
        
        # Price crash signal
        price_trend_90d = self._calculate_price_change(days=90)
        if price_trend_90d < -0.2:  # More than 20 price reductions in 90 days%
            signals.append(f"🚨 Prices continue to fall({price_trend_90d:.1%})")
            insights.append("Intense price war or declining demand in the market")
            actions.append("Evaluate whether to follow up with price cuts or look for differentiation")
            risk_level += 25
        
        # quality crisis signal
        return_rate = self._estimate_return_rate()
        if return_rate > 0.15:
            signals.append(f"🚨High return rate({return_rate:.1%})")
            insights.append("There are serious problems with product quality or description")
            actions.append("Improve products or optimize listings immediately")
            risk_level += 25
        
        # Seller exit signal
        if rank_drops > 40 and self._safe_float(self.raw_data.get('New Offer Count: Current', 0)) < 3:
            signals.append("⚠️ Signs of seller exit")
            insights.append("With falling demand and fewer new sellers, the market may be shrinking")
            risk_level += 15
        
        # Calculate risk score (100 - risk_level)
        score = max(0, 100 - risk_level)
        
        return DeepFactor(
            name="Risk warning",
            category="risk",
            score=score,  # High scores indicate low risk
            weight=0.15,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 5. Growth potential factor ==========
    def _mine_growth_potential(self) -> DeepFactor:
        """
        growth potential factor
        
        Identify dimensions:
        - Demand growth signals: Ranking rises and new demands enter
        - market expansion signal: New sellers increase and categories expand
        - seasonal opportunities: About to enter peak season, historical seasonality
        - Room for price improvement: The current pricing is low and the value is not fully exploited.
        """
        signals = []
        insights = []
        actions = []
        score = 50
        confidence = 0.55
        
        # Demand growth signals
        rank_changes = self._safe_float(self.raw_data.get('90 days change % Sales Rank', '0%').replace('%', ''))
        if rank_changes < -30:  # Ranking numbers become smaller(get better)more than 30%
            signals.append(f"📈 Demand is growing rapidly(Ranking improvement{abs(rank_changes):.0f}%)")
            insights.append("Product demand is growing rapidly and may be a trending product")
            actions.append("Consider increasing inventory and seize opportunities")
            score += 25
        
        # New seller enters
        new_offers = self._safe_float(self.raw_data.get('New Offer Count: Current', 0))
        if new_offers > 5:
            signals.append(f"New sellers continue to enter({new_offers}a)")
            insights.append("The market is highly attractive and new sellers are willing to enter")
            score += 10
        
        # Room for price improvement
        price_position = self._analyze_price_position()
        if price_position == 'low':
            signals.append("Price positioning is low")
            insights.append("The current pricing is lower than the market average, and there is room for price increase")
            actions.append("Test a small price increase and observe the sales response")
            score += 10
        
        # ReviewGrowthQuality
        review_velocity = self._calculate_review_velocity()
        if review_velocity > 10:  # More than 10 new comments per month
            signals.append(f"Comments are growing rapidly({review_velocity:.0f}a/month)")
            insights.append("Sales growth has led to an increase in reviews, and the product is gaining market recognition.")
            score += 15
        
        return DeepFactor(
            name="growth potential",
            category="growth",
            score=max(0, min(100, score)),
            weight=0.15,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== 6. Operational efficiency factors ==========
    def _mine_operational_efficiency(self) -> DeepFactor:
        """
        operational efficiency factor
        
        Assessment Dimensions:
        - conversion efficiency: Traffic conversion, shopping cart acquisition rate
        - Inventory turns: Sales speed, inventory days
        - customer satisfaction: Positive rating, repurchase signal
        """
        signals = []
        insights = []
        actions = []
        score = 50
        confidence = 0.6
        
        # conversion efficiency (byReview/sales ratio estimate)
        review_ratio = self._estimate_review_ratio()
        if review_ratio > 0.05:  # Review rate is higher than 5%
            signals.append("Review conversion rate is higher")
            insights.append("Customer satisfaction is high and willing to leave reviews")
            score += 10
        
        # Buy Box acquisition ability
        bb_is_fba = str(self.raw_data.get('Buy Box: Is FBA', '')).lower()
        if 'yes' in bb_is_fba or 'true' in bb_is_fba:
            signals.append("The current Buy Box is FBA")
            insights.append("FBA delivery is conducive to obtaining the Buy Box")
            score += 10
        
        # Review quality
        rating = self._safe_float(self.raw_data.get('Reviews: Rating', 0))
        review_count = self._safe_float(self.raw_data.get('Reviews: Review Count', 0))
        
        if rating >= 4.5 and review_count > 50:
            signals.append("Highly rated and well reviewed")
            insights.append("The product has established a good reputation and has a solid operating foundation.")
            score += 15
        elif rating < 4.0:
            signals.append("Low rating")
            insights.append("Insufficient customer satisfaction affects conversion and repurchase")
            actions.append("Analyze negative reviews and improve products or services")
            score -= 15
        
        # variant richness (If any)
        variation_count = self._count_variations()
        if variation_count > 5:
            signals.append(f"Rich variants({variation_count}a)")
            insights.append("Multiple variants cover more needs, but inventory management is complex")
            score += 5
        
        return DeepFactor(
            name="operational efficiency",
            category="efficiency",
            score=max(0, min(100, score)),
            weight=0.15,
            signals=signals,
            insights=insights,
            actions=actions,
            confidence=confidence
        )
    
    # ========== Helper method ==========
    def _safe_float(self, value, default=0.0):
        """safe conversion to float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace('$', '').replace('%', '').replace(',', '').strip())
            except:
                return default
        return default
    
    def _analyze_price_trend(self) -> str:
        """Analyze price trends"""
        # Simplify implementation
        drops = self._safe_float(self.raw_data.get('Buy Box: Drops last 90 days', 0))
        if drops > 15:
            return 'declining'
        elif drops < 3:
            return 'stable'
        return 'volatile'
    
    def _analyze_review_growth(self) -> str:
        """Analyze review growth"""
        # Simplify implementation
        return 'steady'
    
    def _determine_lifecycle(self) -> str:
        """Determine life cycle stage"""
        tracking_days = 365  # hypothesis
        review_count = self._safe_float(self.raw_data.get('Reviews: Review Count', 0))
        
        if tracking_days < 180 and review_count < 50:
            return 'Introduction'
        elif review_count < 500:
            return 'Growth'
        elif review_count > 1000:
            return 'Maturity'
        return 'Unknown'
    
    def _analyze_brand_concentration(self) -> float:
        """Analyze brand concentration"""
        # Simplified implementation, actually requires more data
        return 0.5
    
    def _analyze_rank_consistency(self) -> float:
        """Analyze ranking stability"""
        # Simplify implementation
        return 0.7
    
    def _calculate_price_change(self, days: int = 90) -> float:
        """Calculate price change rate"""
        current = self._safe_float(self.raw_data.get('Buy Box: Current', 0))
        historical = self._safe_float(self.raw_data.get(f'Buy Box: {days} days avg.', 0))
        if historical > 0:
            return (current - historical) / historical
        return 0.0
    
    def _analyze_price_position(self) -> str:
        """Analyze price positioning"""
        current = self._safe_float(self.raw_data.get('Buy Box: Current', 0))
        avg = self._safe_float(self.raw_data.get('Buy Box: 90 days avg.', current))
        
        if current < avg * 0.9:
            return 'low'
        elif current > avg * 1.1:
            return 'high'
        return 'medium'
    
    def _calculate_review_velocity(self) -> float:
        """Calculate review growth rate"""
        # Simplify implementation
        return 5.0
    
    def _estimate_return_rate(self) -> float:
        """Estimated return rate"""
        val = self.raw_data.get('Return Rate', '')
        if isinstance(val, str):
            if 'High' in val:
                return 0.12
            elif 'Medium' in val:
                return 0.08
        return 0.05
    
    def _estimate_review_ratio(self) -> float:
        """Estimated review rate"""
        # Simplify implementation
        return 0.03
    
    def _count_variations(self) -> int:
        """Number of statistical variants"""
        variations = str(self.raw_data.get('Variation ASINs', ''))
        if variations:
            return len(variations.split(';'))
        return 0


def format_factor_report(factors: Dict[str, DeepFactor]) -> str:
    """Format Factor Report"""
    lines = []
    
    lines.append("=" * 90)
    lines.append("🔍 Deep factor mining report - Operation and product selection insights")
    lines.append("=" * 90)
    
    # Calculate overall score
    total_score = 0
    total_weight = 0
    for factor in factors.values():
        total_score += factor.score * factor.weight
        total_weight += factor.weight
    overall_score = total_score / total_weight if total_weight > 0 else 0
    
    lines.append(f"\n📊 Comprehensive health score: {overall_score:.0f}/100")
    
    # Group by category
    categories = {
        'operational': '📈 Operational dimension',
        'product_selection': '🎯 Product selection dimensions',
        'competition': '⚔️Competition Dimension',
        'risk': '⚠️Risk Dimensions',
        'growth': '🚀 Growth dimension',
        'efficiency': '⚡ Efficiency Dimension',
    }
    
    for factor in factors.values():
        cat_name = categories.get(factor.category, factor.category)
        status = "🟢" if factor.score >= 70 else "🟡" if factor.score >= 50 else "🔴"
        
        lines.append(f"\n{'─' * 90}")
        lines.append(f"{status} {factor.name} (weight{factor.weight:.0%}) - {factor.score:.0f}/100 [Confidence: {factor.confidence:.0%}]")
        lines.append(f"{'─' * 90}")
        
        if factor.signals:
            lines.append(f"\n 📡 Key Signals:")
            for signal in factor.signals:
                lines.append(f"    • {signal}")
        
        if factor.insights:
            lines.append(f"\n 💡 Deep Insight:")
            for insight in factor.insights:
                lines.append(f"    • {insight}")
        
        if factor.actions:
            lines.append(f"\n 🎯 Action suggestions:")
            for action in factor.actions:
                lines.append(f"    • {action}")
    
    lines.append("\n" + "=" * 90)
    
    return "\n".join(lines)
