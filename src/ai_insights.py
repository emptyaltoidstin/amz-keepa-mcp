"""
AI Deep Insight Generator
Generate business insights and strategic recommendations based on data patterns
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Insight:
    """Insight items"""
    category: str  # 'opportunity', 'risk', 'strategy', 'tactical'
    title: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    confidence: int  # 0-100
    actionable: bool
    action_items: List[str]


class AIInsightsGenerator:
    """
    AI Deep Insight Generator
    
    Function:
    1. Business model analysis
    2. Identification of competitive advantages
    3. Risk warning
    4. Strategic advice
    5. Execution plan
    """
    
    def __init__(self):
        self.frameworks = self._load_frameworks()
    
    def _load_frameworks(self) -> Dict:
        """Load analysis framework"""
        return {
            'porter_forces': {
                'threat_of_new_entrants': 'High' if 'low_barrier' else 'Medium',
                'bargaining_power_of_suppliers': 'Medium',
                'bargaining_power_of_buyers': 'High',
                'threat_of_substitutes': 'Medium',
                'competitive_rivalry': 'High'
            },
            'swot_elements': ['strengths', 'weaknesses', 'opportunities', 'threats'],
            'business_models': ['premium', 'value', 'volume', 'niche']
        }
    
    def generate(self, data: Dict, clear_analysis: Dict = None) -> Dict[str, Any]:
        """
        Generate a complete AI insights report
        
        Args:
            data: Processed product data
            clear_analysis: CLEAR analysis results (optional)
        
        Returns:
            AI Insights Report
        """
        return {
            'business_model_analysis': self._analyze_business_model(data),
            'competitive_positioning': self._analyze_positioning(data),
            'market_timing': self._analyze_timing(data),
            'profit_optimization': self._analyze_profit_optimization(data),
            'risk_matrix': self._build_risk_matrix(data),
            'strategic_options': self._generate_strategic_options(data),
            'execution_roadmap': self._build_execution_roadmap(data),
            'success_factors': self._identify_success_factors(data),
            'failure_modes': self._identify_failure_modes(data),
            'insights': self._generate_insights_list(data),
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'ai_version': '1.0',
                'data_completeness': self._assess_data_completeness(data)
            }
        }
    
    def _analyze_business_model(self, data: Dict) -> Dict:
        """Analyze business model"""
        price = data.get('current_price', 0) or 0
        margin = data.get('estimated_margin', 0) or 0
        offers = data.get('current_offers', 0) or 0
        rank = data.get('current_rank', 999999) or 999999
        
        # Determine business model
        if margin > 40 and price > 50:
            model = 'Premium'
            characteristics = ['High margin', 'Low volume', 'Brand focus']
            key_success_factor = 'Differentiation and brand building'
        elif margin < 20 and rank < 10000:
            model = 'Volume'
            characteristics = ['Low margin', 'High volume', 'Operational efficiency']
            key_success_factor = 'Supply chain and cost control'
        elif offers < 5 and rank < 50000:
            model = 'Niche'
            characteristics = ['Specialized', 'Low competition', 'Targeted audience']
            key_success_factor = 'Product-market fit and customer loyalty'
        else:
            model = 'Value'
            characteristics = ['Balanced margin', 'Competitive pricing', 'Service differentiation']
            key_success_factor = 'Value proposition clarity'
        
        return {
            'identified_model': model,
            'characteristics': characteristics,
            'key_success_factor': key_success_factor,
            'suitability_score': self._calculate_model_fit(data, model),
            'model_transition_potential': self._assess_model_transition(data, model)
        }
    
    def _analyze_positioning(self, data: Dict) -> Dict:
        """Analyze competitive positioning"""
        
        # Build positioning map coordinates
        price_score = self._normalize_price(data.get('current_price', 0))
        quality_score = (data.get('current_rating', 0) or 0) / 5.0
        
        # Identify the quadrants
        if price_score > 0.5 and quality_score > 0.8:
            quadrant = 'Premium Leader'
            description = 'High price, high quality - commanding market respect'
        elif price_score < 0.5 and quality_score > 0.8:
            quadrant = 'Value Champion'
            description = 'Affordable quality - best value proposition'
        elif price_score > 0.5 and quality_score < 0.8:
            quadrant = 'Premium Risk'
            description = 'High price, mediocre quality - vulnerable position'
        else:
            quadrant = 'Commodity Player'
            description = 'Low price, average quality - competing on cost'
        
        return {
            'positioning_quadrant': quadrant,
            'description': description,
            'price_position': price_score,
            'quality_position': quality_score,
            'competitive_distance': self._calculate_competitive_distance(data),
            'white_space_opportunities': self._identify_white_space(data)
        }
    
    def _analyze_timing(self, data: Dict) -> Dict:
        """Analysis time"""
        
        rank_trend = data.get('rank_trend', '')
        price_drops = data.get('price_drops_count', 0)
        lifecycle = data.get('lifecycle_stage', '')
        offers = data.get('current_offers', 0) or 0
        
        # timing score
        timing_score = 50
        
        if 'rise' in rank_trend:
            timing_score += 20
        elif 'decline' in rank_trend:
            timing_score -= 20
        
        if price_drops > 20:
            timing_score -= 15
        elif price_drops < 5:
            timing_score += 10
        
        if 'grow' in lifecycle:
            timing_score += 15
        elif 'recession' in lifecycle:
            timing_score -= 25
        
        if offers <= 3:
            timing_score += 10
        elif offers > 20:
            timing_score -= 10
        
        # Window period judgment
        if timing_score >= 70:
            window = 'Optimal'
            window_desc = 'Market conditions favorable - act quickly'
            urgency = 'High - Window may close in 4-6 weeks'
        elif timing_score >= 50:
            window = 'Acceptable'
            window_desc = 'Conditions workable but not ideal'
            urgency = 'Medium - Complete due diligence within 30 days'
        elif timing_score >= 30:
            window = 'Marginal'
            window_desc = 'Challenging conditions - require strong differentiation'
            urgency = 'Low - No rush, perfect your offering'
        else:
            window = 'Unfavorable'
            window_desc = 'Poor timing - recommend waiting or passing'
            urgency = 'Not recommended at this time'
        
        return {
            'timing_score': timing_score,
            'market_window': window,
            'window_description': window_desc,
            'urgency_assessment': urgency,
            'optimal_entry_months': self._suggest_entry_months(data),
            'months_to_avoid': self._suggest_avoid_months(data)
        }
    
    def _analyze_profit_optimization(self, data: Dict) -> Dict:
        """Analyze profit optimization space"""
        
        current_margin = data.get('estimated_margin', 0) or 0
        current_price = data.get('current_price', 0) or 0
        avg_price = data.get('avg_price', 0) or 0
        
        optimizations = []
        
        # Pricing optimization
        if current_price < avg_price * 0.95:
            price_upside = avg_price * 1.05 - current_price
            new_margin = current_margin + (price_upside / current_price * 100) if current_price > 0 else current_margin
            optimizations.append({
                'lever': 'Pricing',
                'action': 'Gradual price increase to market average',
                'potential_impact': f'+{price_upside:.2f} USD per unit',
                'new_margin_estimate': f'{new_margin:.1f}%',
                'confidence': 'Medium',
                'implementation': 'Increase by 3-5% every 2 weeks, monitor BSR'
            })
        
        # cost optimization
        if current_margin < 25:
            cost_reduction_needed = 25 - current_margin
            optimizations.append({
                'lever': 'Cost Structure',
                'action': f'Reduce sourcing cost by {cost_reduction_needed:.0f}%',
                'potential_impact': f'+{cost_reduction_needed:.1f}% margin',
                'new_margin_estimate': '25%',
                'confidence': 'Low-Medium',
                'implementation': 'Negotiate with suppliers, explore alternative manufacturers'
            })
        
        # Operation optimization
        optimizations.append({
            'lever': 'Operational Efficiency',
            'action': 'Optimize inventory turnover and reduce storage fees',
            'potential_impact': '+2-5% effective margin',
            'new_margin_estimate': f'{current_margin + 3:.1f}%',
            'confidence': 'High',
            'implementation': 'Use FBA inventory planning tools, avoid long-term storage'
        })
        
        return {
            'current_margin': current_margin,
            'margin_gap_to_target': max(0, 25 - current_margin),
            'optimization_opportunities': optimizations,
            'realistic_margin_ceiling': min(45, current_margin + 15),
            'break_even_analysis': self._calculate_break_even(data)
        }
    
    def _build_risk_matrix(self, data: Dict) -> Dict:
        """Build a risk matrix"""
        
        risks = []
        
        # market risk
        if data.get('price_volatility', 0) > 30:
            risks.append({
                'category': 'Market',
                'risk': 'Price War',
                'probability': 'High',
                'impact': 'High',
                'mitigation': 'Differentiate on service, bundle products',
                'early_warning': 'Competitor drops price >15%'
            })
        
        # operational risk
        if data.get('out_of_stock_days', 0) > 5:
            risks.append({
                'category': 'Operational',
                'risk': 'Supply Disruption',
                'probability': 'Medium',
                'impact': 'High',
                'mitigation': 'Dual-source strategy, safety stock',
                'early_warning': 'Supplier delivery delays >1 week'
            })
        
        # Competing risks
        if data.get('is_amazon_selling', False):
            risks.append({
                'category': 'Competitive',
                'risk': 'Amazon 1P Competition',
                'probability': 'Certain',
                'impact': 'Medium',
                'mitigation': 'Focus on long-tail keywords, bundles',
                'early_warning': 'Amazon consistently wins Buy Box >70%'
            })
        
        # financial risk
        if (data.get('estimated_margin', 0) or 0) < 20:
            risks.append({
                'category': 'Financial',
                'risk': 'Low Margin Buffer',
                'probability': 'Certain',
                'impact': 'Medium',
                'mitigation': 'Strict cost control, volume focus',
                'early_warning': 'Actual margin <15% after launch'
            })
        
        return {
            'risk_count': len(risks),
            'high_impact_risks': [r for r in risks if r['impact'] == 'High'],
            'risk_matrix': risks,
            'overall_risk_level': 'High' if len([r for r in risks if r['impact'] == 'High']) >= 2 else 'Medium' if risks else 'Low',
            'risk_mitigation_priority': self._prioritize_risks(risks)
        }
    
    def _generate_strategic_options(self, data: Dict) -> List[Dict]:
        """Generate strategic options"""
        
        options = []
        
        margin = data.get('estimated_margin', 0) or 0
        offers = data.get('current_offers', 0) or 0
        rank = data.get('current_rank', 999999) or 999999
        
        # Option 1: Quick entry
        if margin > 20 and offers <= 10:
            options.append({
                'strategy': 'Fast Market Entry',
                'description': 'Capitalize on favorable conditions quickly',
                'investment_level': 'Medium',
                'timeline': '2-4 weeks to launch',
                'probability_of_success': '70%',
                'expected_roi': '100-150% first year',
                'key_actions': [
                    'Source inventory immediately',
                    'Set competitive opening price',
                    'Aggressive PPC launch campaign'
                ],
                'when_to_choose': 'When timing score >70 and margin >25%'
            })
        
        # Option 2: Differentiated entry
        if offers > 10 or data.get('is_amazon_selling', False):
            options.append({
                'strategy': 'Differentiated Entry',
                'description': 'Enter with unique value proposition',
                'investment_level': 'High',
                'timeline': '6-8 weeks to launch',
                'probability_of_success': '60%',
                'expected_roi': '150-200% first year',
                'key_actions': [
                    'Improve product features/packaging',
                    'Build brand story and A+ content',
                    'Target specific customer segments'
                ],
                'when_to_choose': 'When facing strong competition'
            })
        
        # Option 3: Wait and see
        if data.get('price_volatility', 0) > 35 or 'decline' in data.get('rank_trend', ''):
            options.append({
                'strategy': 'Wait and Monitor',
                'description': 'Observe market stabilization before entering',
                'investment_level': 'Low',
                'timeline': '3-6 months',
                'probability_of_success': '50%',
                'expected_roi': '80-120% first year',
                'key_actions': [
                    'Set up price alerts',
                    'Monitor competitor actions',
                    'Prepare contingency plans'
                ],
                'when_to_choose': 'When market conditions are unstable'
            })
        
        # Option 4: give up
        if margin < 15 and offers > 20:
            options.append({
                'strategy': 'Pass and Pivot',
                'description': 'Look for better opportunities elsewhere',
                'investment_level': 'None',
                'timeline': 'Immediate',
                'probability_of_success': 'N/A',
                'expected_roi': 'Save capital for better opportunity',
                'key_actions': [
                    'Document learnings',
                    'Search adjacent products',
                    'Maintain monitoring alerts'
                ],
                'when_to_choose': 'When risk-adjusted return is negative'
            })
        
        return options
    
    def _build_execution_roadmap(self, data: Dict) -> Dict:
        """Build an execution roadmap"""
        
        return {
            'phase_1_preparation': {
                'duration': 'Week 1-2',
                'key_milestones': [
                    'Finalize supplier selection',
                    'Confirm product specifications',
                    'Calculate precise costs and margins',
                    'Develop brand identity and packaging'
                ],
                'decision_gate': 'Go/No-Go decision on supplier'
            },
            'phase_2_launch': {
                'duration': 'Week 3-4',
                'key_milestones': [
                    'Place initial inventory order',
                    'Create optimized listing',
                    'Set up PPC campaigns',
                    'Prepare review generation strategy'
                ],
                'decision_gate': 'Inventory received and inspected'
            },
            'phase_3_optimization': {
                'duration': 'Month 2-3',
                'key_milestones': [
                    'Monitor and optimize PPC',
                    'Adjust pricing based on response',
                    'Gather and analyze customer feedback',
                    'Plan replenishment order'
                ],
                'decision_gate': 'Achieve target metrics or pivot'
            },
            'phase_4_scale': {
                'duration': 'Month 4-6',
                'key_milestones': [
                    'Scale winning campaigns',
                    'Expand to variations/bundles',
                    'Optimize supply chain',
                    'Evaluate product line extension'
                ],
                'decision_gate': 'ROI validation and expansion approval'
            }
        }
    
    def _identify_success_factors(self, data: Dict) -> List[Dict]:
        """Identify critical success factors"""
        
        factors = []
        
        # product quality
        if (data.get('current_rating', 0) or 0) >= 4.5:
            factors.append({
                'factor': 'Product Quality',
                'status': 'Strong',
                'importance': 'Critical',
                'maintenance': 'Continue QC processes, monitor reviews'
            })
        else:
            factors.append({
                'factor': 'Product Quality',
                'status': 'Needs Improvement',
                'importance': 'Critical',
                'maintenance': 'Address review pain points, upgrade materials'
            })
        
        # price competitiveness
        if (data.get('current_price', 0) or 0) <= (data.get('avg_price', 0) or 999):
            factors.append({
                'factor': 'Price Positioning',
                'status': 'Competitive',
                'importance': 'High',
                'maintenance': 'Monitor competitor pricing, maintain value perception'
            })
        
        # market timing
        if 'rise' in data.get('rank_trend', ''):
            factors.append({
                'factor': 'Market Timing',
                'status': 'Favorable',
                'importance': 'High',
                'maintenance': 'Act quickly to capture growth wave'
            })
        
        factors.append({
            'factor': 'Supply Chain Reliability',
            'status': 'Good' if data.get('out_of_stock_days', 0) == 0 else 'At Risk',
            'importance': 'Critical',
            'maintenance': 'Maintain backup suppliers, safety stock'
        })
        
        return factors
    
    def _identify_failure_modes(self, data: Dict) -> List[Dict]:
        """Identify failure patterns"""
        
        failures = []
        
        if data.get('is_amazon_selling', False):
            failures.append({
                'failure_mode': 'Cannot Win Buy Box',
                'probability': '40%',
                'impact': 'Revenue limited to 20-30% of potential',
                'warning_signs': ['Amazon price consistently lower', 'Buy Box win rate <15%'],
                'prevention': 'Focus on long-tail keywords, bundle strategy'
            })
        
        if (data.get('estimated_margin', 0) or 0) < 20:
            failures.append({
                'failure_mode': 'Margin Erosion',
                'probability': '50%',
                'impact': 'Unsustainable business, forced exit',
                'warning_signs': ['Actual costs higher than estimate', 'Price competition intensifies'],
                'prevention': 'Strict cost control, premium positioning'
            })
        
        if data.get('price_drops_count', 0) > 25:
            failures.append({
                'failure_mode': 'Price War Entry',
                'probability': '35%',
                'impact': 'Compressed margins, inventory stuck',
                'warning_signs': ['Multiple competitors dropping prices', 'Race to bottom'],
                'prevention': 'Differentiate early, avoid commodity positioning'
            })
        
        return failures
    
    def _generate_insights_list(self, data: Dict) -> List[Insight]:
        """Generate a list of insights"""
        
        insights = []
        
        # Opportunity insights
        if (data.get('current_offers', 100) or 100) <= 5 and (data.get('estimated_margin', 0) or 0) > 25:
            insights.append(Insight(
                category='opportunity',
                title='Blue Ocean Opportunity',
                description='Low competition with healthy margins - rare combination',
                impact='high',
                confidence=85,
                actionable=True,
                action_items=['Secure reliable supplier quickly', 'Enter market before competition', 'Build early review advantage']
            ))
        
        # Risk Insights
        if data.get('price_volatility', 0) > 30:
            insights.append(Insight(
                category='risk',
                title='Price Instability Warning',
                description='Frequent price changes indicate market uncertainty',
                impact='medium',
                confidence=75,
                actionable=True,
                action_items=['Monitor price daily', 'Set automated repricing rules', 'Maintain price flexibility']
            ))
        
        # strategic insights
        if 'rise' in data.get('rank_trend', ''):
            insights.append(Insight(
                category='strategy',
                title='Rising Demand Wave',
                description='Product is gaining traction - window of opportunity',
                impact='high',
                confidence=70,
                actionable=True,
                action_items=['Accelerate launch timeline', 'Prepare larger initial inventory', 'Plan for sustained PPC']
            ))
        
        return insights
    
    # Helper methods
    def _normalize_price(self, price: float) -> float:
        """normalized price"""
        # hypothesis $50 is the reference point
        return min(price / 50, 2.0) / 2.0
    
    def _calculate_model_fit(self, data: Dict, model: str) -> int:
        """Calculate pattern matching"""
        score = 50
        
        if model == 'Premium':
            if (data.get('estimated_margin', 0) or 0) > 35:
                score += 30
            if (data.get('current_rating', 0) or 0) > 4.5:
                score += 20
        elif model == 'Volume':
            if (data.get('current_rank', 999999) or 999999) < 10000:
                score += 30
            if (data.get('estimated_margin', 0) or 0) < 20:
                score += 20
        
        return min(100, score)
    
    def _assess_model_transition(self, data: Dict, current_model: str) -> List[str]:
        """Evaluate mode switching possibilities"""
        transitions = []
        
        if current_model == 'Commodity' and (data.get('current_rating', 0) or 0) > 4.5:
            transitions.append('Premium - through brand building')
        
        if current_model == 'Niche' and (data.get('current_rank', 999999) or 999999) < 5000:
            transitions.append('Volume - if supply can scale')
        
        return transitions
    
    def _calculate_competitive_distance(self, data: Dict) -> float:
        """Calculate competitive distance"""
        offers = data.get('current_offers', 0) or 0
        return max(0, 1 - (offers / 30))
    
    def _identify_white_space(self, data: Dict) -> List[str]:
        """Identify white space opportunities"""
        spaces = []
        
        if (data.get('current_offers', 0) or 0) < 5:
            spaces.append('Low competition segment')
        
        if (data.get('estimated_margin', 0) or 0) > 30:
            spaces.append('High margin opportunity')
        
        return spaces
    
    def _suggest_entry_months(self, data: Dict) -> List[int]:
        """It is recommended to enter the month"""
        # Simplified logic: avoid Q4 (high competition)
        return [1, 2, 3, 4, 5]
    
    def _suggest_avoid_months(self, data: Dict) -> List[int]:
        """It is recommended to avoid months"""
        return [11, 12]  # Q4 Competition is fierce
    
    def _calculate_break_even(self, data: Dict) -> Dict:
        """Calculate break-even"""
        price = data.get('current_price', 0) or 0
        margin = data.get('estimated_margin', 0) or 0
        
        if margin > 0:
            daily_profit_per_unit = price * (margin / 100) / 30
            fixed_costs = 500  # Assuming fixed costs
            be_units = fixed_costs / (price * margin / 100) if margin > 0 else 9999
            
            return {
                'units_to_break_even': int(be_units),
                'estimated_days': int(be_units / max(5, self._estimate_daily_sales(data))),
                'monthly_fixed_costs': fixed_costs
            }
        
        return {'error': 'Cannot calculate with zero/negative margin'}
    
    def _estimate_daily_sales(self, data: Dict) -> int:
        """Estimated daily sales"""
        rank = data.get('current_rank', 999999) or 999999
        if rank < 1000:
            return 50
        elif rank < 5000:
            return 20
        elif rank < 10000:
            return 10
        elif rank < 50000:
            return 5
        return 2
    
    def _prioritize_risks(self, risks: List[Dict]) -> List[Dict]:
        """Risk prioritization"""
        priority_map = {'High': 3, 'Medium': 2, 'Low': 1}
        return sorted(risks, key=lambda x: priority_map.get(x.get('impact'), 0), reverse=True)
    
    def _assess_data_completeness(self, data: Dict) -> int:
        """Assess data completeness"""
        required = ['current_price', 'current_rank', 'current_rating', 'current_offers']
        present = sum(1 for field in required if data.get(field) is not None)
        return int(present / len(required) * 100)
    
    def generate_ai_report(self, ai_analysis: Dict, asin: str) -> str:
        """Generate AI insights report"""
        
        business = ai_analysis.get('business_model_analysis', {})
        positioning = ai_analysis.get('competitive_positioning', {})
        timing = ai_analysis.get('market_timing', {})
        profit = ai_analysis.get('profit_optimization', {})
        risks = ai_analysis.get('risk_matrix', {})
        options = ai_analysis.get('strategic_options', [])
        roadmap = ai_analysis.get('execution_roadmap', {})
        
        report = f"""# 🤖 AI in-depth insight report

**ASIN**: {asin}  
**Analysis time**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**AI version**: v1.0 | **Data integrity**: {ai_analysis.get('metadata', {}).get('data_completeness', 0)}%

---

## 🎯 Business model analysis

### Identify patterns: {business.get('identified_model', 'Unknown')}

**pattern characteristics**:
"""
        
        for char in business.get('characteristics', []):
            report += f"- {char}\n"
        
        report += f"""
**critical success factors**: {business.get('key_success_factor', 'Unknown')}

**pattern matching**: {business.get('suitability_score', 0)}/100

"""
        
        if business.get('model_transition_potential'):
            report += "**Model evolution is possible**: " + ", ".join(business['model_transition_potential']) + "\n\n"
        
        report += f"""---

## 🗺️ Competitive positioning

### positioning quadrant: {positioning.get('positioning_quadrant', 'Unknown')}

{positioning.get('description', '')}

**price position**: {positioning.get('price_position', 0):.0%}  
**mass position**: {positioning.get('quality_position', 0):.0%}

### Market gap opportunity
"""
        
        for space in positioning.get('white_space_opportunities', []):
            report += f"- 💡 {space}\n"
        
        report += f"""

---

## ⏰ Timing analysis

### timing score: {timing.get('timing_score', 0)}/100

**market window**: {timing.get('market_window', 'Unknown')}  
{timing.get('window_description', '')}

**Urgency**: {timing.get('urgency_assessment', 'Unknown')}

**It is recommended to enter the month**: {timing.get('optimal_entry_months', [])}  
**It is recommended to avoid months**: {timing.get('months_to_avoid', [])}

---

## 💰 Profit Optimization

### current profit margin: {profit.get('current_margin', 0):.1f}%

**gap with target**: {profit.get('margin_gap_to_target', 0):.1f}%

### Optimization opportunities

"""
        
        for opt in profit.get('optimization_opportunities', []):
            report += f"""
**{opt.get('lever')}**
- action: {opt.get('action')}
- potential impact: {opt.get('potential_impact')}
- Estimated new profit margin: {opt.get('new_margin_estimate')}
- Confidence: {opt.get('confidence')}
- Implementation plan: {opt.get('implementation')}

"""
        
        report += f"""---

## ⚠️Risk Matrix

### overall risk level: {risks.get('overall_risk_level', 'Unknown')}

| risk | Category | Probability | influence | Mitigation measures |
|------|------|------|------|----------|
"""
        
        for risk in risks.get('risk_matrix', []):
            report += f"| {risk.get('risk')} | {risk.get('category')} | {risk.get('probability')} | {risk.get('impact')} | {risk.get('mitigation', '')[:30]}... |\n"
        
        report += f"""

---

## 🎲 Strategic options

"""
        
        for i, option in enumerate(options, 1):
            report += f"""
### Options {i}: {option.get('strategy')}

{option.get('description')}

- **investment level**: {option.get('investment_level')}
- **timeline**: {option.get('timeline')}
- **Probability of success**: {option.get('probability_of_success')}
- **Expected ROI**: {option.get('expected_roi')}

**key actions**:
"""
            for action in option.get('key_actions', []):
                report += f"- {action}\n"
            
            report += f"\n**When to choose**: {option.get('when_to_choose')}\n"
        
        report += f"""

---

## 🗓️ Execution Roadmap

"""
        
        for phase, details in roadmap.items():
            phase_name = phase.replace('_', ' ').title()
            report += f"""
### {phase_name}
**cycle**: {details.get('duration')}

**key milestones**:
"""
            for milestone in details.get('key_milestones', []):
                report += f"- [ ] {milestone}\n"
            
            report += f"\n**decision gate**: {details.get('decision_gate')}\n"
        
        report += """

---

## 🎯 Summary suggestions

Based on AI comprehensive analysis, it is recommended:

"""
        
        if timing.get('timing_score', 0) >= 70 and risks.get('overall_risk_level') != 'High':
            report += "✅ **Recommended to enter** - Market conditions are favorable and risks are controllable\n\n"
            report += "take **" + options[0]['strategy'] + "** Strategy\n"
        elif timing.get('timing_score', 0) >= 50:
            report += "⚠️ **Enter with caution** - Needs greater preparation and differentiation\n\n"
            report += "take **" + (options[1]['strategy'] if len(options) > 1 else options[0]['strategy']) + "** Strategy\n"
        else:
            report += "❌ **It is recommended to wait and see** - Bad timing right now, wait for a better window\n"
        
        report += """

---

*This report is generated by the AI in-depth analysis engine and combined with CLEAR architecture data*  
*It is recommended to use manual judgment to make the final decision*
"""
        
        return report
