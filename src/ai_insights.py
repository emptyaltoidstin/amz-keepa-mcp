"""
AI 深度洞察生成器
基于数据模式生成商业洞察和战略建议
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Insight:
    """洞察项"""
    category: str  # 'opportunity', 'risk', 'strategy', 'tactical'
    title: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    confidence: int  # 0-100
    actionable: bool
    action_items: List[str]


class AIInsightsGenerator:
    """
    AI 深度洞察生成器
    
    功能:
    1. 商业模式分析
    2. 竞争优势识别
    3. 风险预警
    4. 战略建议
    5. 执行方案
    """
    
    def __init__(self):
        self.frameworks = self._load_frameworks()
    
    def _load_frameworks(self) -> Dict:
        """加载分析框架"""
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
        生成完整的 AI 洞察报告
        
        Args:
            data: 处理后的产品数据
            clear_analysis: CLEAR 分析结果（可选）
        
        Returns:
            AI 洞察报告
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
        """分析商业模式"""
        price = data.get('current_price', 0) or 0
        margin = data.get('estimated_margin', 0) or 0
        offers = data.get('current_offers', 0) or 0
        rank = data.get('current_rank', 999999) or 999999
        
        # 判断商业模式
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
        """分析竞争定位"""
        
        # 构建定位地图坐标
        price_score = self._normalize_price(data.get('current_price', 0))
        quality_score = (data.get('current_rating', 0) or 0) / 5.0
        
        # 确定象限
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
        """分析时机"""
        
        rank_trend = data.get('rank_trend', '')
        price_drops = data.get('price_drops_count', 0)
        lifecycle = data.get('lifecycle_stage', '')
        offers = data.get('current_offers', 0) or 0
        
        # 时机评分
        timing_score = 50
        
        if '上升' in rank_trend:
            timing_score += 20
        elif '下降' in rank_trend:
            timing_score -= 20
        
        if price_drops > 20:
            timing_score -= 15
        elif price_drops < 5:
            timing_score += 10
        
        if '成长' in lifecycle:
            timing_score += 15
        elif '衰退' in lifecycle:
            timing_score -= 25
        
        if offers <= 3:
            timing_score += 10
        elif offers > 20:
            timing_score -= 10
        
        # 窗口期判断
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
        """分析利润优化空间"""
        
        current_margin = data.get('estimated_margin', 0) or 0
        current_price = data.get('current_price', 0) or 0
        avg_price = data.get('avg_price', 0) or 0
        
        optimizations = []
        
        # 定价优化
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
        
        # 成本优化
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
        
        # 运营优化
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
        """构建风险矩阵"""
        
        risks = []
        
        # 市场风险
        if data.get('price_volatility', 0) > 30:
            risks.append({
                'category': 'Market',
                'risk': 'Price War',
                'probability': 'High',
                'impact': 'High',
                'mitigation': 'Differentiate on service, bundle products',
                'early_warning': 'Competitor drops price >15%'
            })
        
        # 运营风险
        if data.get('out_of_stock_days', 0) > 5:
            risks.append({
                'category': 'Operational',
                'risk': 'Supply Disruption',
                'probability': 'Medium',
                'impact': 'High',
                'mitigation': 'Dual-source strategy, safety stock',
                'early_warning': 'Supplier delivery delays >1 week'
            })
        
        # 竞争风险
        if data.get('is_amazon_selling', False):
            risks.append({
                'category': 'Competitive',
                'risk': 'Amazon 1P Competition',
                'probability': 'Certain',
                'impact': 'Medium',
                'mitigation': 'Focus on long-tail keywords, bundles',
                'early_warning': 'Amazon consistently wins Buy Box >70%'
            })
        
        # 财务风险
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
        """生成战略选项"""
        
        options = []
        
        margin = data.get('estimated_margin', 0) or 0
        offers = data.get('current_offers', 0) or 0
        rank = data.get('current_rank', 999999) or 999999
        
        # 选项 1: 快速进入
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
        
        # 选项 2: 差异化进入
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
        
        # 选项 3: 等待观察
        if data.get('price_volatility', 0) > 35 or '下降' in data.get('rank_trend', ''):
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
        
        # 选项 4: 放弃
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
        """构建执行路线图"""
        
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
        """识别关键成功因素"""
        
        factors = []
        
        # 产品质量
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
        
        # 价格竞争力
        if (data.get('current_price', 0) or 0) <= (data.get('avg_price', 0) or 999):
            factors.append({
                'factor': 'Price Positioning',
                'status': 'Competitive',
                'importance': 'High',
                'maintenance': 'Monitor competitor pricing, maintain value perception'
            })
        
        # 市场时机
        if '上升' in data.get('rank_trend', ''):
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
        """识别失败模式"""
        
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
        """生成洞察列表"""
        
        insights = []
        
        # 机会洞察
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
        
        # 风险洞察
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
        
        # 战略洞察
        if '上升' in data.get('rank_trend', ''):
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
        """归一化价格"""
        # 假设 $50 为参考点
        return min(price / 50, 2.0) / 2.0
    
    def _calculate_model_fit(self, data: Dict, model: str) -> int:
        """计算模式匹配度"""
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
        """评估模式转换可能性"""
        transitions = []
        
        if current_model == 'Commodity' and (data.get('current_rating', 0) or 0) > 4.5:
            transitions.append('Premium - through brand building')
        
        if current_model == 'Niche' and (data.get('current_rank', 999999) or 999999) < 5000:
            transitions.append('Volume - if supply can scale')
        
        return transitions
    
    def _calculate_competitive_distance(self, data: Dict) -> float:
        """计算竞争距离"""
        offers = data.get('current_offers', 0) or 0
        return max(0, 1 - (offers / 30))
    
    def _identify_white_space(self, data: Dict) -> List[str]:
        """识别空白机会"""
        spaces = []
        
        if (data.get('current_offers', 0) or 0) < 5:
            spaces.append('Low competition segment')
        
        if (data.get('estimated_margin', 0) or 0) > 30:
            spaces.append('High margin opportunity')
        
        return spaces
    
    def _suggest_entry_months(self, data: Dict) -> List[int]:
        """建议进入月份"""
        # 简化逻辑：避开 Q4（竞争激烈）
        return [1, 2, 3, 4, 5]
    
    def _suggest_avoid_months(self, data: Dict) -> List[int]:
        """建议避开月份"""
        return [11, 12]  # Q4 竞争激烈
    
    def _calculate_break_even(self, data: Dict) -> Dict:
        """计算盈亏平衡"""
        price = data.get('current_price', 0) or 0
        margin = data.get('estimated_margin', 0) or 0
        
        if margin > 0:
            daily_profit_per_unit = price * (margin / 100) / 30
            fixed_costs = 500  # 假设固定成本
            be_units = fixed_costs / (price * margin / 100) if margin > 0 else 9999
            
            return {
                'units_to_break_even': int(be_units),
                'estimated_days': int(be_units / max(5, self._estimate_daily_sales(data))),
                'monthly_fixed_costs': fixed_costs
            }
        
        return {'error': 'Cannot calculate with zero/negative margin'}
    
    def _estimate_daily_sales(self, data: Dict) -> int:
        """估算日销量"""
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
        """风险优先级排序"""
        priority_map = {'High': 3, 'Medium': 2, 'Low': 1}
        return sorted(risks, key=lambda x: priority_map.get(x.get('impact'), 0), reverse=True)
    
    def _assess_data_completeness(self, data: Dict) -> int:
        """评估数据完整度"""
        required = ['current_price', 'current_rank', 'current_rating', 'current_offers']
        present = sum(1 for field in required if data.get(field) is not None)
        return int(present / len(required) * 100)
    
    def generate_ai_report(self, ai_analysis: Dict, asin: str) -> str:
        """生成 AI 洞察报告"""
        
        business = ai_analysis.get('business_model_analysis', {})
        positioning = ai_analysis.get('competitive_positioning', {})
        timing = ai_analysis.get('market_timing', {})
        profit = ai_analysis.get('profit_optimization', {})
        risks = ai_analysis.get('risk_matrix', {})
        options = ai_analysis.get('strategic_options', [])
        roadmap = ai_analysis.get('execution_roadmap', {})
        
        report = f"""# 🤖 AI 深度洞察报告

**ASIN**: {asin}  
**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**AI 版本**: v1.0 | **数据完整度**: {ai_analysis.get('metadata', {}).get('data_completeness', 0)}%

---

## 🎯 商业模式分析

### 识别模式: {business.get('identified_model', 'Unknown')}

**模式特征**:
"""
        
        for char in business.get('characteristics', []):
            report += f"- {char}\n"
        
        report += f"""
**关键成功因素**: {business.get('key_success_factor', 'Unknown')}

**模式匹配度**: {business.get('suitability_score', 0)}/100

"""
        
        if business.get('model_transition_potential'):
            report += "**模式演进可能**: " + ", ".join(business['model_transition_potential']) + "\n\n"
        
        report += f"""---

## 🗺️ 竞争定位

### 定位象限: {positioning.get('positioning_quadrant', 'Unknown')}

{positioning.get('description', '')}

**价格位置**: {positioning.get('price_position', 0):.0%}  
**质量位置**: {positioning.get('quality_position', 0):.0%}

### 市场空白机会
"""
        
        for space in positioning.get('white_space_opportunities', []):
            report += f"- 💡 {space}\n"
        
        report += f"""

---

## ⏰ 时机分析

### 时机评分: {timing.get('timing_score', 0)}/100

**市场窗口**: {timing.get('market_window', 'Unknown')}  
{timing.get('window_description', '')}

**紧急程度**: {timing.get('urgency_assessment', 'Unknown')}

**建议进入月份**: {timing.get('optimal_entry_months', [])}  
**建议避开月份**: {timing.get('months_to_avoid', [])}

---

## 💰 利润优化

### 当前利润率: {profit.get('current_margin', 0):.1f}%

**与目标差距**: {profit.get('margin_gap_to_target', 0):.1f}%

### 优化机会

"""
        
        for opt in profit.get('optimization_opportunities', []):
            report += f"""
**{opt.get('lever')}**
- 行动: {opt.get('action')}
- 潜在影响: {opt.get('potential_impact')}
- 预计新利润率: {opt.get('new_margin_estimate')}
- 置信度: {opt.get('confidence')}
- 实施方案: {opt.get('implementation')}

"""
        
        report += f"""---

## ⚠️ 风险矩阵

### 整体风险等级: {risks.get('overall_risk_level', 'Unknown')}

| 风险 | 类别 | 概率 | 影响 | 缓解措施 |
|------|------|------|------|----------|
"""
        
        for risk in risks.get('risk_matrix', []):
            report += f"| {risk.get('risk')} | {risk.get('category')} | {risk.get('probability')} | {risk.get('impact')} | {risk.get('mitigation', '')[:30]}... |\n"
        
        report += f"""

---

## 🎲 战略选项

"""
        
        for i, option in enumerate(options, 1):
            report += f"""
### 选项 {i}: {option.get('strategy')}

{option.get('description')}

- **投资水平**: {option.get('investment_level')}
- **时间线**: {option.get('timeline')}
- **成功概率**: {option.get('probability_of_success')}
- **预期 ROI**: {option.get('expected_roi')}

**关键行动**:
"""
            for action in option.get('key_actions', []):
                report += f"- {action}\n"
            
            report += f"\n**何时选择**: {option.get('when_to_choose')}\n"
        
        report += f"""

---

## 🗓️ 执行路线图

"""
        
        for phase, details in roadmap.items():
            phase_name = phase.replace('_', ' ').title()
            report += f"""
### {phase_name}
**周期**: {details.get('duration')}

**关键里程碑**:
"""
            for milestone in details.get('key_milestones', []):
                report += f"- [ ] {milestone}\n"
            
            report += f"\n**决策门**: {details.get('decision_gate')}\n"
        
        report += """

---

## 🎯 总结建议

基于 AI 综合分析，建议：

"""
        
        if timing.get('timing_score', 0) >= 70 and risks.get('overall_risk_level') != 'High':
            report += "✅ **建议进入** - 市场条件 favorable，风险可控\n\n"
            report += "采取 **" + options[0]['strategy'] + "** 策略\n"
        elif timing.get('timing_score', 0) >= 50:
            report += "⚠️ **谨慎进入** - 需要更充分的准备和差异化\n\n"
            report += "采取 **" + (options[1]['strategy'] if len(options) > 1 else options[0]['strategy']) + "** 策略\n"
        else:
            report += "❌ **建议观望** - 当前时机不佳，等待更好的窗口\n"
        
        report += """

---

*本报告由 AI 深度分析引擎生成，结合 CLEAR 架构数据*  
*建议结合人工判断做出最终决策*
"""
        
        return report
