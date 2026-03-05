"""
Product Analyzer
In-depth analysis based on Keepa data framework
"""

import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """risk level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Risk:
    """Risk items"""
    type: str
    level: RiskLevel
    description: str
    recommendation: str


class ProductAnalyzer:
    """
    Amazon FBA Product Analyzer
    
    Multi-dimensional analysis based on Keepa data:
    1. Profitability analysis
    2. Competitive Analysis
    3. Sales trend analysis
    4. Risk assessment
    5. Opportunity Scoring
    """
    
    def __init__(self):
        # Weight configuration
        self.weights = {
            'profitability': 0.25,
            'competition': 0.20,
            'sales': 0.20,
            'reviews': 0.15,
            'sustainability': 0.20,
        }
    
    def calculate_opportunity_score(self, data: Dict) -> int:
        """
        Calculate overall opportunity score (0-100)
        
        Rating dimensions:
        - Profitability (25%)
        - level of competition (20%)
        - sales potential (20%)
        - Review quality (15%)
        - sustainability (20%)
        """
        scores = {
            'profitability': self._score_profitability(data),
            'competition': self._score_competition(data),
            'sales': self._score_sales(data),
            'reviews': self._score_reviews(data),
            'sustainability': self._score_sustainability(data),
        }
        
        # Weighted calculation
        total_score = sum(
            scores[key] * self.weights[key]
            for key in scores
        )
        
        return min(100, max(0, int(total_score)))
    
    def _score_profitability(self, data: Dict) -> float:
        """Profitability score"""
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
        """Competition Rating"""
        offers = data.get('current_offers', 100) or 100
        
        if offers <= 3:
            return 95  # low competition
        elif offers <= 8:
            return 85 - (offers - 3) * 2
        elif offers <= 15:
            return 70 - (offers - 8) * 1.5
        elif offers <= 25:
            return 50 - (offers - 15) * 1.5
        else:
            return max(10, 30 - (offers - 25))
    
    def _score_sales(self, data: Dict) -> float:
        """sales potential score"""
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
        """Review quality rating"""
        rating = data.get('current_rating', 0) or 0
        review_count = data.get('total_reviews', 0) or 0
        
        # Rating base points
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
        
        # Adjustment of number of comments
        if review_count < 10:
            return base_score * 0.7  # Too few comments
        elif review_count < 50:
            return base_score * 0.85
        elif review_count > 1000:
            return base_score * 0.95  # Too many comments and fierce competition
        
        return base_score
    
    def _score_sustainability(self, data: Dict) -> float:
        """sustainability score"""
        score = 70  # Basic points
        
        # price stability
        stability = data.get('price_stability', '')
        if 'very stable' in stability:
            score += 10
        elif 'Larger fluctuations' in stability:
            score -= 15
        
        # Out of stock situation
        stockout_days = data.get('out_of_stock_days', 0) or 0
        if stockout_days > 10:
            score -= 20
        elif stockout_days > 5:
            score -= 10
        
        # Ranking trends
        rank_trend = data.get('rank_trend', '')
        if 'rise' in rank_trend:
            score += 10
        elif 'decline' in rank_trend:
            score -= 15
        
        # Amazon self-operated
        if data.get('is_amazon_selling'):
            score -= 10
        
        return min(100, max(0, score))
    
    def detect_risks(self, data: Dict) -> List[Risk]:
        """
        Detect potential risks
        
        Detect the following risk patterns:
        1. High profits + low competition + No brand = Trap
        2. High rating + Sales plummet = Abnormal
        3. Frequent stock outs = supply chain issues
        4. Frequent and large price fluctuations = price war
        5. Amazon has a high proportion of self-operated products = Difficult to compete
        """
        risks = []
        
        # Risk 1: high profit + low competition + No brand
        margin = data.get('estimated_margin', 0) or 0
        offers = data.get('current_offers', 100) or 100
        brand = data.get('brand', '').lower()
        
        if margin > 35 and offers < 5 and (not brand or brand in ['generic', 'unknown', 'n/a']):
            risks.append(Risk(
                type="profit trap",
                level=RiskLevel.HIGH,
                description="High profit margins but low competition and no brand, may have hidden flaws or compliance issues",
                recommendation="Carefully check product reviews, search for relevant regulations, and verify supplier qualifications"
            ))
        
        # Risk 2: high rating + sales drop
        rating = data.get('current_rating', 0) or 0
        rank_trend = data.get('rank_trend', '')
        
        if rating >= 4.5 and 'decline' in rank_trend:
            risks.append(Risk(
                type="Abnormal sales volume",
                level=RiskLevel.MEDIUM,
                description="High ratings but declining sales, possibly new competition or seasonal effects",
                recommendation="Analyze review sentiment and check whether new competing products have entered the market"
            ))
        
        # Risk 3: Frequently out of stock
        stockout_days = data.get('out_of_stock_days', 0) or 0
        stockouts_count = data.get('stockouts_count', 0) or 0
        
        if stockout_days > 7 or stockouts_count > 3:
            risks.append(Risk(
                type="supply chain risk",
                level=RiskLevel.HIGH,
                description=f"Out of stock in the past 90 days {stockout_days} God, out of stock {stockouts_count} Second-rate",
                recommendation="Ensure reliable backup suppliers and assess supply chain stability"
            ))
        
        # Risk 4: price war
        price_drops = data.get('price_drops_count', 0) or 0
        price_volatility = data.get('price_volatility', 0) or 0
        
        if price_drops > 5 or price_volatility > 30:
            risks.append(Risk(
                type="Price war risk",
                level=RiskLevel.MEDIUM,
                description=f"Frequent price fluctuations ({price_drops} times fell sharply, volatility {price_volatility}%)",
                recommendation="Price prudently, prepare for price competition, and consider differentiation strategies"
            ))
        
        # Risk 5: Amazon self-operated competition
        if data.get('is_amazon_selling'):
            amazon_prices = data.get('amazon_price_history', [])
            if len(amazon_prices) > 10:
                risks.append(Risk(
                    type="Amazon self-operated competition",
                    level=RiskLevel.MEDIUM,
                    description="Amazon is selling this product, the Buy Box is hard to get",
                    recommendation="Evaluate whether you can offer better service or prices than Amazon"
                ))
        
        # Risk 6: Comments grow abnormally
        reviews_30d = data.get('reviews_30d', 0) or 0
        total_reviews = data.get('total_reviews', 0) or 0
        
        if total_reviews > 100 and reviews_30d == 0:
            risks.append(Risk(
                type="Comment growth stalls",
                level=RiskLevel.LOW,
                description="The product has many reviews but no new ones recently, so sales may have stagnated.",
                recommendation="Verify that the product is still on sale"
            ))
        
        # Risk 7: low rating
        if rating < 3.5:
            risks.append(Risk(
                type="Product quality issues",
                level=RiskLevel.CRITICAL,
                description=f"Product ratings only {rating}, there are quality problems",
                recommendation="It is not recommended to enter or look for an improved version"
            ))
        
        # Risk 8: excessive competition
        if offers > 25:
            risks.append(Risk(
                type="excessive competition",
                level=RiskLevel.HIGH,
                description=f"have {offers} Sellers, competition is very fierce",
                recommendation="Consider differentiation or find niche markets"
            ))
        
        return risks
    
    def generate_recommendations(self, data: Dict, risks: List[Risk]) -> List[str]:
        """Generate investment recommendations"""
        recommendations = []
        
        score = self.calculate_opportunity_score(data)
        
        # Overall recommendations based on ratings
        if score >= 80:
            recommendations.append("✅ Highly recommended: This is a great opportunity, we recommend you act as soon as possible")
        elif score >= 60:
            recommendations.append("⚠️Can be considered: There is some potential, but the risks need to be carefully assessed")
        elif score >= 40:
            recommendations.append("❓ Wait and see: Conditions are average, it is recommended to wait for better opportunities or further research")
        else:
            recommendations.append("❌ Not recommended: The risk is high, it is recommended to give up")
        
        # Data-based recommendations
        margin = data.get('estimated_margin', 0) or 0
        if margin > 30:
            recommendations.append(f"💰 Sufficient profit margins ({margin}%), there is enough room for price reduction")
        elif margin < 20:
            recommendations.append(f"⚠️ Limited profit margins ({margin}%), need to accurately control costs")
        
        offers = data.get('current_offers', 100) or 100
        if offers < 5:
            recommendations.append("🎯 Less competition, chance to get Buy Box")
        elif offers > 20:
            recommendations.append("🔥 Competition is fierce and strong differentiation strategies are needed")
        
        rank_trend = data.get('rank_trend', '')
        if 'rise' in rank_trend:
            recommendations.append("📈 Sales volume is rising and market demand is growing")
        elif 'decline' in rank_trend:
            recommendations.append("📉 Sales volume has dropped and the reasons need to be analyzed")
        
        stockout_days = data.get('out_of_stock_days', 0) or 0
        if stockout_days > 5:
            recommendations.append("📦 The supply chain is unstable, be sure to prepare backup suppliers")
        
        # Special advice on risks
        if risks:
            high_risks = [r for r in risks if r.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
            if high_risks:
                recommendations.append("🚨 There are high risk factors, be sure to verify before making a decision")
        
        return recommendations
    
    def analyze_market_position(self, data: Dict) -> Dict[str, Any]:
        """Analyze market positioning"""
        return {
            'price_position': self._analyze_price_position(data),
            'competitive_position': self._analyze_competitive_position(data),
            'quality_position': self._analyze_quality_position(data),
        }
    
    def _analyze_price_position(self, data: Dict) -> str:
        """Analyze price positioning"""
        avg_price = data.get('avg_price', 0) or 0
        
        if avg_price < 10:
            return "low price range"
        elif avg_price < 25:
            return "Low to medium price"
        elif avg_price < 50:
            return "Medium price (recommend)"
        elif avg_price < 100:
            return "mid to high price"
        else:
            return "high price"
    
    def _analyze_competitive_position(self, data: Dict) -> str:
        """Analyze competitive positioning"""
        offers = data.get('current_offers', 0) or 0
        
        if offers <= 3:
            return "blue ocean market"
        elif offers <= 8:
            return "low competition"
        elif offers <= 15:
            return "Moderate competition"
        elif offers <= 25:
            return "high competition"
        else:
            return "red sea market"
    
    def _analyze_quality_position(self, data: Dict) -> str:
        """Analyze quality positioning"""
        rating = data.get('current_rating', 0) or 0
        
        if rating >= 4.5:
            return "quality product"
        elif rating >= 4.0:
            return "good"
        elif rating >= 3.5:
            return "Average"
        else:
            return "Worrying quality"
    
    def generate_quick_screening_report(self, data: Dict) -> Dict[str, Any]:
        """
        Generate quick screening report (30 second quick assessment)
        
        Returns:
            Dictionary containing key decision information
        """
        margin = data.get('estimated_margin', 0) or 0
        offers = data.get('current_offers', 100) or 100
        rank_trend = data.get('rank_trend', '')
        
        checks = {
            'margin_ok': margin >= 20,
            'competition_ok': offers < 20,
            'trend_ok': 'decline' not in rank_trend,
        }
        
        # Quick decision making
        if all(checks.values()):
            decision = "PASS - Go to in-depth analysis"
        elif checks['margin_ok'] and checks['competition_ok']:
            decision = "MAYBE - Need to further analyze trends"
        else:
            decision = "REJECT - Does not meet basic conditions"
        
        return {
            'decision': decision,
            'checks': checks,
            'margin': margin,
            'offers': offers,
            'rank_trend': rank_trend,
            'quick_score': self.calculate_opportunity_score(data),
        }
