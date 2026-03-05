"""
Market Actuary V2 - Redefine the value proposition

admit reality: Keepa data cannot accurately predict profitability because core cost data is missing

new value proposition:
1. Market side analysis (Keepa's strengths) - Competition landscape, demand trends, price elasticity
2. Earning potential assessment (Estimate+Risk warning) - Give a range of possibilities rather than a definite number
3. Real data fusion (Key!) - Recalculate after user enters real COGS
4. Feasibility screening - Quickly eliminate obviously inappropriate categories

no more exaggeration: "Actuarial-level profit forecasts" → Change to "Market feasibility analysis + Earning potential assessment"
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketFeasibilityScore:
    """Market feasibility score"""
    demand_score: float  # Demand intensity (0-100)
    competition_score: float  # competitive accessibility (0-100)
    price_stability_score: float  # price stability (0-100)
    supply_chain_score: float  # Supply chain feasibility (0-100)
    
    overall_score: float  # Overall rating
    recommendation: str  # suggestion: Go / Caution / No-Go
    key_risks: List[str]  # Main risk points


class MarketActuaryV2:
    """
    Market Actuary V2 - Honest value proposition
    
    Core functions:
    1. Market feasibility analysis based on Keepa data (reliable)
    2. Estimation of profit potential range (With clear risk warning)
    3. Accurate calculation after input of real COGS (User data required)
    4. Category comparison and screening (relative assessment)
    """
    
    def __init__(self):
        self.disclaimer = """
        ⚠️ IMPORTANT NOTE: 
        This analysis is based on Keepa public market data and cannot obtain your real COGS, operating cost and other data.
        Profit estimates are for reference only, actual profits and losses depend on your supply chain capabilities and operational efficiency.
        It is recommended to use real financial data to make final decisions.
        """
    
    def analyze_market_feasibility(self, product_data: Dict) -> MarketFeasibilityScore:
        """
        1. Market feasibility analysis (Based on Keepa data, relatively reliable)
        
        Assessment Dimensions:
        - Demand intensity: Ranking trends, sales stability
        - competitive accessibility: Seller concentration, new seller opportunities
        - price stability: Price fluctuations and price war risks
        - Supply chain feasibility: Dimensional weight, inventory turnover
        """
        # Need intensity score
        demand_score = self._calculate_demand_score(product_data)
        
        # Competitive Accessibility Rating
        competition_score = self._calculate_competition_score(product_data)
        
        # price stability score
        price_stability_score = self._calculate_price_stability(product_data)
        
        # Supply chain feasibility score
        supply_chain_score = self._calculate_supply_chain_feasibility(product_data)
        
        # Overall rating
        overall_score = (
            demand_score * 0.30 +
            competition_score * 0.25 +
            price_stability_score * 0.25 +
            supply_chain_score * 0.20
        )
        
        # Generate suggestions
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
        2. Earning potential assessment (Interval estimation + Clear risk warning)
        
        If the user provides real COGS, give an accurate calculation
        If you only have Keepa data, give a probability interval and clearly label the uncertainty
        """
        current_price = self._extract_price(product_data)
        
        if user_cogs:
            # User provides real COGS - Can give a relatively accurate estimate
            return self._calculate_with_real_cogs(current_price, user_cogs, product_data)
        else:
            # No real COGS - Give a probability interval
            return self._estimate_profit_range(current_price, product_data)
    
    def _estimate_profit_range(self, price: float, product_data: Dict) -> Dict:
        """
        Estimated profit potential range without true COGS
        
        Provide a reasonable range of COGS rates based on categories rather than fixed values
        """
        category = product_data.get('Categories: Root', '')
        
        # Give COGS rate interval based on category (This is an estimate, not a definite value!)
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
        
        # other costs (relatively certain)
        fba_fee = self._estimate_fba_fee(product_data, price)
        referral_rate = 0.15
        referral_fee = price * referral_rate
        estimated_acos = 0.15  # Estimate ACOS 15%, it may actually be higher
        ad_cost = price * estimated_acos
        return_cost = price * 0.08 * 0.3  # 8%Return rate, 30%net loss
        storage_cost = 0.20
        
        # Calculate profit margins under different COGS scenarios
        def calc_margin(cogs_rate):
            cogs = price * cogs_rate
            total_cost = cogs + fba_fee + referral_fee + ad_cost + return_cost + storage_cost
            net_profit = price - total_cost
            return (net_profit / price * 100) if price > 0 else 0
        
        margin_best = calc_margin(cogs_low)  # best case scenario (Supply chain is extremely strong)
        margin_typical = calc_margin(cogs_typical)  # Typical situation
        margin_worst = calc_margin(cogs_high)  # worst case scenario (Weak supply chain)
        
        return {
            'disclaimer': 'The following estimates are based on assumed COGS rate ranges, actual profit margins depend on your supply chain capabilities',
            'cogs_assumption': {
                'category': category,
                'estimated_range': f"{cogs_low:.0%} - {cogs_high:.0%}",
                'typical': f"{cogs_typical:.0%}",
                'note': 'This is a common range in the market. Your actual COGS may be higher or lower than this range.'
            },
            'profit_scenarios': {
                'best_case': {
                    'cogs_rate': f"{cogs_low:.0%}",
                    'net_margin': f"{margin_best:.1f}%",
                    'description': 'If you have strong supply chain advantages, you can achieve the lowest COGS in the industry'
                },
                'typical_case': {
                    'cogs_rate': f"{cogs_typical:.0%}",
                    'net_margin': f"{margin_typical:.1f}%",
                    'description': 'Industry average, the COGS level of most sellers'
                },
                'worst_case': {
                    'cogs_rate': f"{cogs_high:.0%}",
                    'net_margin': f"{margin_worst:.1f}%",
                    'description': 'If your supply chain is weak and COGS is high'
                }
            },
            'key_uncertainties': [
                'COGS rate: It may actually be higher than/±20 below estimated interval%',
                'ACOS: Estimate 15%, actual health products 18-25%, highly competitive products 30%+',
                'return rate: Estimate 8%, the actual difference in product quality may reach 15-25%',
                'price war: The risk of future price declines has not been taken into account'
            ],
            'reliability_assessment': 'medium low - It is strongly recommended to enter real COGS for accurate calculations',
            'call_to_action': 'If you have real COGS data, please provide it for accurate analysis'
        }
    
    def _calculate_with_real_cogs(self, price: float, cogs: float, product_data: Dict) -> Dict:
        """
        User provides real COGS - gives relatively reliable calculations
        """
        cogs_rate = cogs / price if price > 0 else 0
        
        # Use real data or reasonable estimates
        fba_fee = self._estimate_fba_fee(product_data, price)
        referral_fee = price * 0.15
        
        # Obtain or estimate return rates from data
        return_rate = self._extract_return_rate(product_data)
        return_cost = price * return_rate * 0.3
        
        storage_cost = 0.20
        ad_cost = price * 0.18  # Assuming ACOS 18%, slightly higher than the ideal value
        
        total_cost = cogs + fba_fee + referral_fee + return_cost + storage_cost + ad_cost
        net_profit = price - total_cost
        net_margin = (net_profit / price * 100) if price > 0 else 0
        
        # Break-even analysis
        monthly_fixed = 500  # Assuming monthly fixed costs
        break_even = monthly_fixed / net_profit if net_profit > 0 else float('inf')
        
        return {
            'disclaimer': 'Based on the real COGS calculation you provided, other cost items are estimates.',
            'real_cogs': {
                'value': f"${cogs:.2f}",
                'rate': f"{cogs_rate:.1%}",
                'assessment': 'Excellent' if cogs_rate < 0.35 else 'good' if cogs_rate < 0.50 else 'Average' if cogs_rate < 0.65 else 'On the high side'
            },
            'cost_breakdown': {
                'cogs': f"${cogs:.2f} ({cogs_rate:.1%})",
                'fba_fee': f"${fba_fee:.2f}",
                'referral': f"${referral_fee:.2f} (15%)",
                'ad_cost': f"${ad_cost:.2f} (Estimate 18% ACOS)",
                'return_cost': f"${return_cost:.2f} ({return_rate:.1%}return rate)",
                'storage': f"${storage_cost:.2f}",
                'total': f"${total_cost:.2f}"
            },
            'profit_calculation': {
                'net_margin': f"{net_margin:.1f}%",
                'net_profit_per_unit': f"${net_profit:.2f}",
                'break_even_units': f"{break_even:.0f}pieces/month" if break_even != float('inf') else 'Unable to break even',
                'assessment': 'profit' if net_margin > 15 else 'small profit' if net_margin > 5 else 'risk of loss'
            },
            'sensitivities': {
                'if_acos_25': f"Net interest rate dropped to {net_margin - 7:.1f}%",
                'if_return_15': f"Net interest rate dropped to {net_margin - 2:.1f}%",
                'if_price_drop_10': f"Net interest rate dropped to {net_margin - 8:.1f}%"
            },
            'reliability_assessment': 'Middle to high - Based on real COGS, it is recommended to verify advertising and return data'
        }
    
    def generate_comprehensive_report(self, 
                                     product_data: Dict,
                                     user_cogs: Optional[float] = None) -> Dict:
        """
        Generate comprehensive analysis reports
        """
        # 1. Market feasibility analysis (reliable)
        feasibility = self.analyze_market_feasibility(product_data)
        
        # 2. Earning potential assessment (interval or exact)
        profit_analysis = self.estimate_profit_potential(product_data, user_cogs)
        
        # 3. Final recommendations
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
                'profit_reliability': 'high' if user_cogs else 'medium low (Interval estimation)',
                'market_reliability': 'high (Based on Keepa data)'
            }
        }
    
    # Helper methods
    def _calculate_demand_score(self, data: Dict) -> float:
        """Need intensity score (0-100)"""
        score = 50  # Basic points
        
        # The lower the ranking (the smaller the number) the stronger the demand
        rank = self._extract_sales_rank(data)
        if rank < 1000:
            score += 30
        elif rank < 10000:
            score += 20
        elif rank < 50000:
            score += 10
        elif rank > 100000:
            score -= 20
        
        # Ranking trends
        rank_drops = data.get('Sales Rank: Drops last 90 days', 0)
        if isinstance(rank_drops, str):
            try:
                rank_drops = float(rank_drops)
            except:
                rank_drops = 0
        if isinstance(rank_drops, (int, float)):
            if rank_drops > 50:
                score -= 15  # Decline in demand
            elif rank_drops < 20:
                score += 10  # Demand is stable or rising
        
        return max(0, min(100, score))
    
    def _calculate_competition_score(self, data: Dict) -> float:
        """Competitive Accessibility Rating (0-100)"""
        score = 50
        
        # Number of sellers
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
        
        # Amazon’s self-operated share
        amazon_pct = self._extract_amazon_share(data)
        if amazon_pct > 50:
            score -= 30
        elif amazon_pct > 30:
            score -= 15
        
        # Buy Box stability
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
        """price stability score (0-100)"""
        score = 50
        
        # price fluctuations
        price_cv = data.get('Buy Box: Standard Deviation 90 days', 0)
        # Handling string types(Such as'$ 3.38')
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
        
        # price war indicator
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
        """Supply chain feasibility score (0-100)"""
        score = 60
        
        # Helper function: safe conversion to float
        def safe_float(val, default=0):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val.replace(',', ''))
                except:
                    return default
            return default
        
        # Dimensions and weight
        weight = safe_float(data.get('Package: Weight (g)', 0))
        if weight > 0:
            if weight < 500:  # Light and small items
                score += 15
            elif weight > 2000:  # Heavy cargo
                score -= 10
        
        # Volume
        length = safe_float(data.get('Package: Length (cm)', 0))
        width = safe_float(data.get('Package: Width (cm)', 0))
        height = safe_float(data.get('Package: Height (cm)', 0))
        if length > 0 and width > 0 and height > 0:
            volume = length * width * height
            if volume < 1000:  # Small size
                score += 10
            elif volume > 10000:  # Large size
                score -= 10
        
        # Is there a history of out of stock?
        oos = data.get('Amazon: 90 days OOS', 0)
        if isinstance(oos, str):
            try:
                oos = float(oos.replace('%', ''))
            except:
                oos = 0
        if isinstance(oos, (int, float)) and oos > 20:
            score -= 15  # Supply chain instability
        
        return max(0, min(100, score))
    
    def _generate_recommendation(self, overall_score: float, dimension_scores: Dict) -> str:
        """Generate actionable suggestions"""
        if overall_score >= 70:
            return "Go - High market feasibility and worthy of in-depth investigation"
        elif overall_score >= 50:
            if dimension_scores['competition'] < 40:
                return "Caution - Competition is fierce and differentiation is needed"
            elif dimension_scores['demand'] < 40:
                return "Caution - Insufficient demand, enter with caution"
            else:
                return "Caution - Moderately feasible, needs further analysis"
        else:
            return "No-Go - Market feasibility is low, it is recommended to give up"
    
    def _identify_key_risks(self, data: Dict, scores: Dict) -> List[str]:
        """Identify key risks"""
        risks = []
        
        if scores['demand'] < 40:
            risks.append("demand risk: Sales ranking is low or on a downward trend")
        
        if scores['competition'] < 40:
            amazon_pct = self._extract_amazon_share(data)
            if amazon_pct > 30:
                risks.append(f"Competing risks: Amazon’s self-operated share{amazon_pct:.0%}, it is difficult to obtain the Buy Box")
            else:
                risks.append("Competing risks: Too many sellers and high risk of price war")
        
        if scores['price'] < 40:
            risks.append("price risk: Large price fluctuations or continued downward trend")
        
        if scores['supply'] < 40:
            risks.append("supply chain risk: The product is large or has a history of frequent out-of-stocks")
        
        if not risks:
            risks.append("Main risks: The market seems feasible, but the true profitability still needs to be verified")
        
        return risks
    
    def _generate_final_recommendation(self, feasibility: MarketFeasibilityScore, profit: Dict) -> Dict:
        """Generate final comprehensive recommendations"""
        
        # High market feasibility + Good profit potential = Highly recommended
        # High market feasibility + Uncertain profits = Investigate carefully
        # Low market viability = It is recommended to give up
        
        if feasibility.recommendation.startswith('Go'):
            if 'real_cogs' in profit:
                margin = float(profit['profit_calculation']['net_margin'].rstrip('%'))
                if margin > 20:
                    return {
                        'decision': 'Recommend in-depth',
                        'confidence': 'high',
                        'rationale': 'Good market feasibility and good profitability based on real COGS forecasts',
                        'next_steps': ['Verify advertising costs', 'Confirm return rate', 'Small batch trial marketing']
                    }
                elif margin > 10:
                    return {
                        'decision': 'Consider carefully',
                        'confidence': 'middle',
                        'rationale': 'Good market viability, but medium profit margins',
                        'next_steps': ['Optimize COGS', 'Control advertising costs', 'small-scale testing']
                    }
                else:
                    return {
                        'decision': 'Wait and see for now',
                        'confidence': 'middle',
                        'rationale': 'Good market feasibility, but limited profit potential',
                        'next_steps': ['Significantly optimize cost structure', 'Find differentiated positioning', 'bide your time']
                    }
            else:
                return {
                    'decision': 'Worth investigating',
                    'confidence': 'middle',
                    'rationale': 'High market feasibility, but real COGS data is needed to confirm profitability',
                    'next_steps': ['Calculate real COGS', 'Get samples to test', 'Research suppliers']
                }
        
        elif feasibility.recommendation.startswith('Caution'):
            return {
                'decision': 'Enter with caution',
                'confidence': 'Low-middle',
                'rationale': feasibility.key_risks[0] if feasibility.key_risks else 'There are specific risks',
                'next_steps': ['Address risk points in a targeted manner', 'Assess your own competitiveness', 'small-scale testing']
            }
        
        else:
            return {
                'decision': 'It is recommended to give up',
                'confidence': 'high',
                'rationale': 'Market feasibility is low and entry risks outweigh opportunities',
                'next_steps': ['Find other categories', 'Pay attention to market changes', 'bide your time']
            }
    
    # Data extraction helpers
    def _extract_price(self, data: Dict) -> float:
        """Extract price"""
        for field in ['Buy Box: Current', 'New: Current', 'Amazon: Current']:
            val = data.get(field, 0)
            if val and str(val).replace('.', '').replace('-', '').isdigit():
                return float(val)
        return 0.0
    
    def _extract_sales_rank(self, data: Dict) -> int:
        """Extract sales ranking"""
        val = data.get('Sales Rank: Current', 0)
        try:
            return int(val)
        except:
            return 999999
    
    def _extract_amazon_share(self, data: Dict) -> float:
        """Extract Amazon’s self-operated proportion"""
        val = data.get('Buy Box: % Amazon 90 days', '0%')
        try:
            return float(val.replace('%', '')) / 100
        except:
            return 0.0
    
    def _extract_return_rate(self, data: Dict) -> float:
        """Extract return rate"""
        val = data.get('Return Rate', '')
        if isinstance(val, str):
            if 'High' in val:
                return 0.12
            elif 'Medium' in val:
                return 0.08
        return 0.08  # Default 8%
    
    def _estimate_fba_fee(self, data: Dict, price: float) -> float:
        """Estimate FBA fees"""
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
    """Format V2 report"""
    lines = []
    
    lines.append("=" * 90)
    lines.append("📊 Market Actuary Analysis V2 - Market feasibility assessment report")
    lines.append("=" * 90)
    
    lines.append(f"\n⚠️  {report['disclaimer']}")
    
    # market feasibility
    mf = report['market_feasibility']
    lines.append(f"\n" + "─" * 90)
    lines.append(f"🎯 1. Market feasibility analysis (Based on Keepa data)")
    lines.append("─" * 90)
    lines.append(f"\n Comprehensive rating: {mf['overall_score']:.0f}/100")
    lines.append(f"  suggestion: {mf['recommendation']}")
    lines.append(f"\n dimension score:")
    lines.append(f"    Demand intensity: {mf['dimension_scores']['demand']:.0f}/100")
    lines.append(f"    Competition is available: {mf['dimension_scores']['competition']:.0f}/100")
    lines.append(f"    price stability: {mf['dimension_scores']['price_stability']:.0f}/100")
    lines.append(f"    Supply chain is feasible: {mf['dimension_scores']['supply_chain']:.0f}/100")
    lines.append(f"\n Main risks:")
    for risk in mf['key_risks']:
        lines.append(f"    • {risk}")
    
    # Profit analysis
    lines.append(f"\n" + "─" * 90)
    lines.append(f"💰 2. Profit potential assessment")
    lines.append("─" * 90)
    
    pa = report['profit_analysis']
    lines.append(f"\n  ⚠️ {pa['disclaimer']}")
    
    if 'real_cogs' in pa:
        lines.append(f"\n Calculated based on real COGS:")
        lines.append(f"    Your COGS: {pa['real_cogs']['value']} ({pa['real_cogs']['rate']}) - {pa['real_cogs']['assessment']}")
        lines.append(f"    net profit margin: {pa['profit_calculation']['net_margin']}")
        lines.append(f"    Profit per unit: {pa['profit_calculation']['net_profit_per_unit']}")
        lines.append(f"    break even: {pa['profit_calculation']['break_even_units']}")
        lines.append(f"\n cost structure:")
        for key, value in pa['cost_breakdown'].items():
            lines.append(f"    {key}: {value}")
        lines.append(f"\n Sensitivity analysis:")
        for key, value in pa['sensitivities'].items():
            lines.append(f"    {key}: {value}")
    else:
        lines.append(f"\n COGS hypothesis: {pa['cogs_assumption']['estimated_range']} (Common ranges of categories)")
        lines.append(f"\n Profit scenario analysis:")
        for scenario, values in pa['profit_scenarios'].items():
            lines.append(f"\n    {scenario}:")
            lines.append(f"      COGS rate: {values['cogs_rate']}")
            lines.append(f"      net profit margin: {values['net_margin']}")
            lines.append(f"      Description: {values['description']}")
        lines.append(f"\n ⚠️ Key uncertainties:")
        for unc in pa['key_uncertainties']:
            lines.append(f"    • {unc}")
    
    # Final recommendations
    lines.append(f"\n" + "─" * 90)
    lines.append(f"📋 3. Comprehensive decision-making suggestions")
    lines.append("─" * 90)
    
    fr = report['final_recommendation']
    lines.append(f"\n decision making: {fr['decision']}")
    lines.append(f"  Confidence: {fr['confidence']}")
    lines.append(f"  reason: {fr['rationale']}")
    lines.append(f"\n next action:")
    for step in fr['next_steps']:
        lines.append(f"    • {step}")
    
    lines.append(f"\n" + "=" * 90)
    
    return "\n".join(lines)
