"""
COSMO Intent Analyzer - Amazon COSMO Algorithmic Intent Mining Analyzer

Based on Amazon COSMO (Common Sense Knowledge Generation)algorithm framework,
Mining users’ five-point intent details from Keepa data:
1. Crowd attributes (User Persona) - who is buying
2. Shopping mission (Shopping Mission) - Why buy
3. Usage scenarios (Usage Context) - When and where to use
4. Demand pain points (Needs & Pain Points) - what problem to solve
5. Preference characteristics (Preferences) - What features do you prefer?

Multi-Agents collaborative architecture:
- DataExtractor Agent: Extract raw data from 163 indicators
- IntentMiner Agent: Discover the five intentions of COSMO
- SemanticAnalyzer Agent: Semantic association analysis
- ReportIntegrator Agent: Integrate into actuarial reporting
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import Counter
import pandas as pd
import numpy as np


@dataclass
class COSMOIntentProfile:
    """COSMO five-point intention portrait"""
    # 1. Crowd attributes
    persona: Dict[str, Any]
    # 2. Shopping mission
    mission: Dict[str, Any]
    # 3. Usage scenarios
    context: Dict[str, Any]
    # 4. Demand pain points
    needs: Dict[str, Any]
    # 5. Preference characteristics
    preferences: Dict[str, Any]
    # Overall rating
    intent_score: float
    # key insights
    key_insights: List[str]


class COSMOIntentAnalyzer:
    """
    COSMO Intent Analyzer - Agent 1: DataExtractor + IntentMiner
    
    Mining user intentions from Keepa data and building knowledge graph connections
    """
    
    # Crowd keyword mapping
    PERSONA_KEYWORDS = {
        'home user': ['family', 'household', 'home', 'parents', 'kids', 'children', 'baby'],
        'professionals': ['professional', 'office', 'work', 'business', 'executive'],
        'outdoor enthusiast': ['outdoor', 'camping', 'hiking', 'travel', 'adventure', 'sports'],
        'student group': ['student', 'school', 'college', 'university', 'study'],
        'Elderly users': ['elderly', 'senior', 'old', 'aging', 'retired'],
        'Female users': ['women', 'female', 'lady', 'mom', 'mother', 'her'],
        'Male users': ['men', 'male', 'man', 'father', 'dad', 'his'],
        'pet owner': ['pet', 'dog', 'cat', 'animal', 'puppy', 'kitten'],
    }
    
    # Shopping mission keywords
    MISSION_KEYWORDS = {
        'gift purchase': ['gift', 'present', 'birthday', 'anniversary', 'holiday', 'christmas'],
        'Replacement and upgrade': ['replacement', 'upgrade', 'new', 'update', 'renew'],
        'first time purchase': ['first', 'starter', 'beginner', 'entry', 'basic'],
        'Stock up and restock': ['bulk', 'stock', 'refill', 'supply', 'pack'],
        'Emergency needs': ['emergency', 'urgent', 'backup', 'spare', 'temporary'],
    }
    
    # scene keywords
    CONTEXT_KEYWORDS = {
        'Daily household use': ['daily', 'everyday', 'home', 'household', 'routine'],
        'office space': ['office', 'work', 'desk', 'professional', 'business'],
        'outdoor travel': ['travel', 'trip', 'vacation', 'outdoor', 'camping'],
        'Sports and fitness': ['gym', 'workout', 'fitness', 'exercise', 'sports', 'running'],
        'Festive occasions': ['party', 'celebration', 'wedding', 'holiday', 'event'],
        'special environment': ['waterproof', 'outdoor', 'extreme', 'weather', 'condition'],
    }
    
    # Demand pain point keywords
    NEEDS_KEYWORDS = {
        'Convenience': ['convenient', 'easy', 'quick', 'simple', 'fast', 'effortless'],
        'security': ['safe', 'secure', 'protection', 'durable', 'reliable', 'quality'],
        'comfort': ['comfortable', 'soft', 'ergonomic', 'cozy', 'smooth'],
        'Aesthetics': ['beautiful', 'stylish', 'elegant', 'fashion', 'design', 'aesthetic'],
        'Cost-effectiveness': ['value', 'affordable', 'cheap', 'budget', 'economic', 'saving'],
        'Functional': ['functional', 'practical', 'useful', 'effective', 'efficient'],
    }
    
    # Preference feature keywords
    PREFERENCE_KEYWORDS = {
        'brand loyalty': ['brand', 'premium', 'authentic', 'genuine', 'original'],
        'environmental awareness': ['eco', 'organic', 'natural', 'sustainable', 'green', 'recycle'],
        'Science and technology pursuit': ['smart', 'digital', 'tech', 'innovation', 'advanced', 'modern'],
        'Customized personality': ['custom', 'personalized', 'unique', 'special', 'diy'],
        'social display': ['instagram', 'social', 'share', 'trendy', 'popular', 'viral'],
    }
    
    def __init__(self):
        self.intent_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, Dict[str, List[re.Pattern]]]:
        """Compile regular expression patterns"""
        patterns = {}
        for category, keywords in [
            ('persona', self.PERSONA_KEYWORDS),
            ('mission', self.MISSION_KEYWORDS),
            ('context', self.CONTEXT_KEYWORDS),
            ('needs', self.NEEDS_KEYWORDS),
            ('preferences', self.PREFERENCE_KEYWORDS),
        ]:
            patterns[category] = {}
            for label, words in keywords.items():
                patterns[category][label] = [
                    re.compile(r'\b' + word + r'\b', re.IGNORECASE) 
                    for word in words
                ]
        return patterns
    
    def analyze(self, product_data: Dict[str, Any]) -> COSMOIntentProfile:
        """
        Main analysis entrance - Execute COSMO five-point intention mining
        
        Args:
            product_data: Keepa product data(163 indicators)
            
        Returns:
            COSMOIntentProfile: five point intention portrait
        """
        # Extract text data sources
        text_sources = self._extract_text_sources(product_data)
        
        # Five Points of Intention Mining
        persona = self._analyze_persona(text_sources, product_data)
        mission = self._analyze_mission(text_sources, product_data)
        context = self._analyze_context(text_sources, product_data)
        needs = self._analyze_needs(text_sources, product_data)
        preferences = self._analyze_preferences(text_sources, product_data)
        
        # Calculate intent match score
        intent_score = self._calculate_intent_score(
            persona, mission, context, needs, preferences
        )
        
        # Generate key insights
        key_insights = self._generate_insights(
            persona, mission, context, needs, preferences, product_data
        )
        
        return COSMOIntentProfile(
            persona=persona,
            mission=mission,
            context=context,
            needs=needs,
            preferences=preferences,
            intent_score=intent_score,
            key_insights=key_insights
        )
    
    def _extract_text_sources(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract all text data sources"""
        sources = {
            'title': str(data.get('Title', '')).lower(),
            'description': str(data.get('Description', '')).lower(),
            'features': str(data.get('Features', '')).lower(),
            'category': str(data.get('Categories: Root', '')).lower(),
            'subcategory': str(data.get('Category: Subcategory', '')).lower(),
            'brand': str(data.get('Brand', '')).lower(),
            'style': str(data.get('Style', '')).lower(),
            'material': str(data.get('Material', '')).lower(),
        }
        # Merge all texts for overall analysis
        sources['combined'] = ' '.join(sources.values())
        return sources
    
    def _analyze_persona(self, sources: Dict[str, str], data: Dict) -> Dict:
        """Analyze crowd attributes (Agent 1.1: PersonaMiner)"""
        scores = {}
        combined = sources['combined']
        
        for label, patterns in self.intent_patterns['persona'].items():
            score = sum(1 for p in patterns if p.search(combined))
            if score > 0:
                scores[label] = score
        
        # Inference based on product attributes
        indicators = []
        
        # price inference
        price = self._extract_price(data)
        if price > 100:
            indicators.append(('High-end users', 0.7))
        elif price < 20:
            indicators.append(('price sensitive users', 0.6))
        
        # Brand inference
        if data.get('Brand') and data.get('Brand') not in ['Generic', '']:
            indicators.append(('Brand aware users', 0.5))
        
        # Review count inference
        review_count = self._extract_review_count(data)
        if review_count > 1000:
            indicators.append(('Mainstream mass users', 0.6))
        elif review_count < 50:
            indicators.append(('Early adopters', 0.4))
        
        # Integrate results
        primary_persona = max(scores.items(), key=lambda x: x[1])[0] if scores else 'general consumer'
        confidence = min(0.95, 0.5 + len(scores) * 0.1)
        
        return {
            'primary': primary_persona,
            'all_scores': scores,
            'indicators': indicators,
            'confidence': confidence,
            'persona_description': self._describe_persona(primary_persona, data)
        }
    
    def _analyze_mission(self, sources: Dict[str, str], data: Dict) -> Dict:
        """Analyze shopping mission (Agent 1.2: MissionMiner)"""
        scores = {}
        combined = sources['combined']
        
        for label, patterns in self.intent_patterns['mission'].items():
            score = sum(1 for p in patterns if p.search(combined))
            if score > 0:
                scores[label] = score
        
        indicators = []
        
        # Price change inference
        price_drops = self._extract_price_drops(data)
        if price_drops > 5:
            indicators.append(('promotion sensitive-Waiting for discount', 0.6))
        
        # Comment sentiment inference
        rating = self._extract_rating(data)
        if rating > 4.5 and self._extract_review_count(data) > 500:
            indicators.append(('Quality Oriented-Carefully selected', 0.7))
        
        # Product feature inference
        if 'gift' in combined or 'present' in combined:
            indicators.append(('Gift Buying Mission', 0.8))
        
        # seasonal inference
        if self._is_seasonal_product(data):
            indicators.append(('Seasonal purchases', 0.5))
        
        primary_mission = max(scores.items(), key=lambda x: x[1])[0] if scores else 'Daily purchases'
        
        return {
            'primary': primary_mission,
            'all_scores': scores,
            'indicators': indicators,
            'urgency_level': self._assess_urgency(data),
            'mission_description': self._describe_mission(primary_mission, data)
        }
    
    def _analyze_context(self, sources: Dict[str, str], data: Dict) -> Dict:
        """Analyze usage scenarios (Agent 1.3: ContextMiner)"""
        scores = {}
        combined = sources['combined']
        
        for label, patterns in self.intent_patterns['context'].items():
            score = sum(1 for p in patterns if p.search(combined))
            if score > 0:
                scores[label] = score
        
        indicators = []
        
        # Portability inference scenarios
        weight = self._extract_weight(data)
        if weight and weight < 200:  # Less than 200g
            indicators.append(('Portable scene', 0.7))
        
        # Waterproof properties extrapolated outdoors
        if 'waterproof' in combined or 'water-resistant' in combined:
            indicators.append(('outdoor/sports scene', 0.6))
        
        # Size inference usage scenarios
        if data.get('Package: Length (cm)') and float(data.get('Package: Length (cm)', 0)) < 10:
            indicators.append(('Compact space use', 0.5))
        
        primary_context = max(scores.items(), key=lambda x: x[1])[0] if scores else 'Common scenarios'
        
        # scene frequency
        frequency = self._assess_usage_frequency(data)
        
        return {
            'primary': primary_context,
            'all_scores': scores,
            'indicators': indicators,
            'usage_frequency': frequency,
            'context_description': self._describe_context(primary_context, data)
        }
    
    def _analyze_needs(self, sources: Dict[str, str], data: Dict) -> Dict:
        """Analyze demand pain points (Agent 1.4: NeedsMiner)"""
        scores = {}
        combined = sources['combined']
        
        for label, patterns in self.intent_patterns['needs'].items():
            score = sum(1 for p in patterns if p.search(combined))
            if score > 0:
                scores[label] = score
        
        indicators = []
        
        # Return rate inference pain points
        return_rate = self._estimate_return_rate(data)
        if return_rate > 0.08:
            indicators.append(('Quality expectations gap-high risk', 0.8))
        
        # Negative review keyword mining
        negative_signals = self._extract_negative_signals(data)
        
        # price-Evaluation relationship inference
        price = self._extract_price(data)
        rating = self._extract_rating(data)
        if price > 50 and rating < 4.0:
            indicators.append(('High price, low satisfaction-Cost-effectiveness pain points', 0.7))
        
        primary_need = max(scores.items(), key=lambda x: x[1])[0] if scores else 'Basic functional requirements'
        
        # Pain point intensity
        pain_intensity = self._assess_pain_intensity(data, negative_signals)
        
        return {
            'primary': primary_need,
            'all_scores': scores,
            'indicators': indicators,
            'negative_signals': negative_signals,
            'pain_intensity': pain_intensity,
            'needs_description': self._describe_needs(primary_need, data)
        }
    
    def _analyze_preferences(self, sources: Dict[str, str], data: Dict) -> Dict:
        """Analyze preference characteristics (Agent 1.5: PreferenceMiner)"""
        scores = {}
        combined = sources['combined']
        
        for label, patterns in self.intent_patterns['preferences'].items():
            score = sum(1 for p in patterns if p.search(combined))
            if score > 0:
                scores[label] = score
        
        indicators = []
        
        # Brand premium acceptance
        brand = data.get('Brand', '')
        if brand and brand not in ['Generic', '']:
            indicators.append(('brand preference', 0.6))
        
        # Material preference
        material = str(data.get('Material', '')).lower()
        if 'leather' in material or 'genuine' in combined:
            indicators.append(('Natural material preference', 0.7))
        if 'organic' in combined or 'eco' in combined:
            indicators.append(('Environmental awareness preferences', 0.6))
        
        # Functional complexity preference
        features = combined.count(',') + combined.count('·') + combined.count('•')
        if features > 10:
            indicators.append(('Feature-rich preferences', 0.5))
        else:
            indicators.append(('Simple and practical preference', 0.4))
        
        primary_preference = max(scores.items(), key=lambda x: x[1])[0] if scores else 'pragmatism'
        
        # price sensitivity
        price_sensitivity = self._assess_price_sensitivity(data)
        
        return {
            'primary': primary_preference,
            'all_scores': scores,
            'indicators': indicators,
            'price_sensitivity': price_sensitivity,
            'preference_description': self._describe_preferences(primary_preference, data)
        }
    
    def _calculate_intent_score(self, *components) -> float:
        """Calculate overall intent match score"""
        # Calculate weighted scores based on the confidence of each dimension
        weights = {
            'persona': 0.20,
            'mission': 0.25,
            'context': 0.20,
            'needs': 0.20,
            'preferences': 0.15
        }
        
        total_score = 0
        for comp, weight in zip(components, weights.values()):
            confidence = comp.get('confidence', 0.5)
            total_score += confidence * weight * 100
        
        return round(total_score, 1)
    
    def _generate_insights(self, persona, mission, context, needs, preferences, data) -> List[str]:
        """Generate key insights (Agent 2: SemanticAnalyzer)"""
        insights = []
        
        # Insight 1: crowd-mission match
        persona_primary = persona.get('primary', '')
        mission_primary = mission.get('primary', '')
        if persona_primary and mission_primary:
            insights.append(
                f"【Crowd-mission】{persona_primary}Main execution{mission_primary}，"
                f"Recommended marketing highlights{'Gift attributes' if 'gift' in mission_primary else 'Practical value'}"
            )
        
        # Insight 2: scene-demand matching
        context_primary = context.get('primary', '')
        needs_primary = needs.get('primary', '')
        if 'outdoor' in context_primary and 'safe' in needs_primary:
            insights.append("【Scene-Requirements] Outdoor scenes+Security requirements are strong, it is recommended to strengthen the durability description")
        
        # Insight 3: Pain point opportunity
        pain_intensity = needs.get('pain_intensity', 'low')
        if pain_intensity == 'high':
            insights.append("[Pain Point Opportunities] For high pain point products, optimizing quality descriptions can reduce return rates")
        
        # Insight 4: price sensitivity
        price_sens = preferences.get('price_sensitivity', 'medium')
        if price_sens == 'high':
            insights.append("[Pricing Strategy] For price-sensitive user groups, it is recommended to set promotional discounts")
        
        # Insight 5: competitive positioning
        if persona.get('indicators') and preferences.get('indicators'):
            insights.append(
                "[Differentiated Suggestions] Based on user portraits and preferences, the recommendations are highlighted"
                f"{preferences['primary']}characteristics to attract{persona['primary']}"
            )
        
        return insights
    
    # Helper methods
    def _extract_price(self, data: Dict) -> float:
        """Extract price"""
        for field in ['Buy Box: Current', 'New: Current', 'Amazon: Current']:
            val = data.get(field, 0)
            if val and str(val).replace('.', '').isdigit():
                return float(val)
        return 0.0
    
    def _extract_review_count(self, data: Dict) -> int:
        """Extract the number of reviews"""
        val = data.get('Reviews: Review Count', 0)
        try:
            return int(val)
        except:
            return 0
    
    def _extract_rating(self, data: Dict) -> float:
        """Extract ratings"""
        val = data.get('Reviews: Rating', 0)
        try:
            return float(val)
        except:
            return 0.0
    
    def _extract_price_drops(self, data: Dict) -> int:
        """Extract the number of price reductions"""
        val = data.get('Buy Box: Drops last 90 days', 0)
        try:
            return int(val)
        except:
            return 0
    
    def _extract_weight(self, data: Dict) -> Optional[float]:
        """Extract weight"""
        val = data.get('Item: Weight (g)', 0) or data.get('Package: Weight (g)', 0)
        try:
            return float(val)
        except:
            return None
    
    def _estimate_return_rate(self, data: Dict) -> float:
        """Estimated return rate"""
        val = data.get('Return Rate', '')
        if isinstance(val, str):
            if 'High' in val:
                return 0.12
            elif 'Medium' in val:
                return 0.08
        return 0.05
    
    def _is_seasonal_product(self, data: Dict) -> bool:
        """Determine whether it is a seasonal product"""
        category = str(data.get('Categories: Root', '')).lower()
        return any(x in category for x in ['holiday', 'christmas', 'summer', 'winter'])
    
    def _assess_urgency(self, data: Dict) -> str:
        """Assess purchase urgency"""
        if self._is_seasonal_product(data):
            return 'seasonal'
        if self._extract_price_drops(data) > 10:
            return 'price_waiting'
        return 'normal'
    
    def _assess_usage_frequency(self, data: Dict) -> str:
        """Evaluate frequency of use"""
        category = str(data.get('Categories: Root', '')).lower()
        if any(x in category for x in ['consumable', 'grocery', 'beauty']):
            return 'daily'
        elif any(x in category for x in ['electronics', 'clothing']):
            return 'weekly'
        return 'occasional'
    
    def _extract_negative_signals(self, data: Dict) -> List[str]:
        """extract negative signals"""
        signals = []
        if self._estimate_return_rate(data) > 0.10:
            signals.append('high_return_rate')
        if self._extract_rating(data) < 3.5:
            signals.append('low_rating')
        return signals
    
    def _assess_pain_intensity(self, data: Dict, signals: List[str]) -> str:
        """Assess pain point intensity"""
        if 'high_return_rate' in signals and 'low_rating' in signals:
            return 'high'
        elif len(signals) > 0:
            return 'medium'
        return 'low'
    
    def _assess_price_sensitivity(self, data: Dict) -> str:
        """Assess price sensitivity"""
        drops = self._extract_price_drops(data)
        if drops > 15:
            return 'high'
        elif drops > 5:
            return 'medium'
        return 'low'
    
    # Description generators
    def _describe_persona(self, persona: str, data: Dict) -> str:
        """Generate crowd descriptions"""
        descriptions = {
            'home user': 'Families with children, focus on practicality and safety',
            'professionals': 'Professionals, focusing on quality and efficiency',
            'outdoor enthusiast': 'Love the outdoors and value durability and portability',
            'student group': 'Limited budget, pursuing cost-effectiveness',
            'Female users': 'Pay attention to appearance design and user experience',
            'Male users': 'Focus on functionality and technical parameters',
        }
        return descriptions.get(persona, 'General consumer, no specific image')
    
    def _describe_mission(self, mission: str, data: Dict) -> str:
        """Generate shopping mission description"""
        descriptions = {
            'gift purchase': 'When choosing gifts for others, pay attention to packaging and thoughtfulness',
            'Replacement and upgrade': 'Replace older products or upgrade existing equipment',
            'first time purchase': 'This is my first time trying a product in this category and I need guidance.',
            'Stock up and restock': 'Regular replenishment, pay attention to price and quantity',
            'Emergency needs': 'Urgent need, low price sensitivity',
        }
        return descriptions.get(mission, 'Daily purchases to meet basic needs')
    
    def _describe_context(self, context: str, data: Dict) -> str:
        """Generate scene description"""
        descriptions = {
            'Daily household use': 'Daily use at home, high frequency',
            'office space': 'Work scene, focusing on professional image',
            'outdoor travel': 'For travel or outdoor activities, portability is important',
            'Sports and fitness': 'Sports scenes, emphasizing functionality',
            'Festive occasions': 'special holiday or celebration',
        }
        return descriptions.get(context, 'General scenarios, no specific restrictions')
    
    def _describe_needs(self, need: str, data: Dict) -> str:
        """Generate requirement description"""
        descriptions = {
            'Convenience': 'Pursuing simplicity of use, saving time and effort',
            'security': 'Pay attention to product safety and reliability',
            'comfort': 'Focus on user experience and comfort',
            'Aesthetics': 'Appearance design is an important consideration',
            'Cost-effectiveness': 'Get the best value within your budget',
            'Functional': 'Complete functions and reliable performance',
        }
        return descriptions.get(need, 'Meet basic functional needs')
    
    def _describe_preferences(self, pref: str, data: Dict) -> str:
        """Generate preference description"""
        descriptions = {
            'brand loyalty': 'Preference for well-known brands and high trust',
            'environmental awareness': 'Focus on sustainability and environmentally friendly attributes',
            'Science and technology pursuit': 'Love new technology and smart features',
            'Customized personality': 'Pursue uniqueness and personalization',
            'social display': 'Suitable for sharing, has social attributes',
        }
        return descriptions.get(pref, 'Pragmatism, no particular preference')


class COSMOReportIntegrator:
    """
    COSMO reporting aggregator - Agent 3: ReportIntegrator
    
    Integrate COSMO five-point intent analysis into actuarial reports
    """
    
    def integrate_to_actuarial_report(self, cosmo_profile: COSMOIntentProfile, 
                                       actuarial_report: Dict) -> Dict:
        """
        Integrate COSMO analysis into actuarial reports
        
        Args:
            cosmo_profile: COSMO five-point intention portrait
            actuarial_report: Original Actuarial Report
            
        Returns:
            Enhanced Actuarial Reporting
        """
        # Add COSMO intent analysis chapter
        actuarial_report['cosmo_intent_analysis'] = {
            'intent_score': cosmo_profile.intent_score,
            'five_points': {
                'persona': cosmo_profile.persona,
                'mission': cosmo_profile.mission,
                'context': cosmo_profile.context,
                'needs': cosmo_profile.needs,
                'preferences': cosmo_profile.preferences,
            },
            'key_insights': cosmo_profile.key_insights,
            'strategic_implications': self._derive_strategic_implications(cosmo_profile)
        }
        
        # Enhance strategic advice
        if 'strategic_recommendations' in actuarial_report:
            actuarial_report['strategic_recommendations'].extend(
                self._convert_insights_to_recommendations(cosmo_profile)
            )
        
        # Update product identity description
        if 'product_identity' in actuarial_report:
            actuarial_report['product_identity']['target_persona'] = \
                cosmo_profile.persona.get('primary', 'general consumer')
            actuarial_report['product_identity']['shopping_mission'] = \
                cosmo_profile.mission.get('primary', 'Daily purchases')
        
        return actuarial_report
    
    def _derive_strategic_implications(self, profile: COSMOIntentProfile) -> Dict:
        """Deriving strategic implications"""
        implications = {
            'product_positioning': self._suggest_positioning(profile),
            'pricing_strategy': self._suggest_pricing(profile),
            'marketing_angle': self._suggest_marketing(profile),
            'inventory_planning': self._suggest_inventory(profile),
        }
        return implications
    
    def _suggest_positioning(self, profile: COSMOIntentProfile) -> str:
        """Suggested product positioning"""
        persona = profile.persona.get('primary', '')
        needs = profile.needs.get('primary', '')
        return f"Target{persona}of{needs}Positioning"
    
    def _suggest_pricing(self, profile: COSMOIntentProfile) -> str:
        """Recommended pricing strategy"""
        sensitivity = profile.preferences.get('price_sensitivity', 'medium')
        strategies = {
            'high': 'Promotion-oriented pricing, set up tiered discounts',
            'medium': 'Value-oriented pricing, highlighting cost-effectiveness',
            'low': ' Premium pricing, emphasis on quality'
        }
        return strategies.get(sensitivity, ' competitive pricing')
    
    def _suggest_marketing(self, profile: COSMOIntentProfile) -> str:
        """Suggest marketing strategies"""
        mission = profile.mission.get('primary', '')
        context = profile.context.get('primary', '')
        return f"exist{context}Emphasis on the scene{mission}value"
    
    def _suggest_inventory(self, profile: COSMOIntentProfile) -> str:
        """Recommended inventory strategy"""
        frequency = profile.context.get('usage_frequency', 'occasional')
        strategies = {
            'daily': 'High-frequency turnover to maintain sufficient inventory',
            'weekly': 'Regular replenishment, pay attention to trends',
            'occasional': 'Stock up on demand to avoid backlogs'
        }
        return strategies.get(frequency, 'Robust inventory strategy')
    
    def _convert_insights_to_recommendations(self, profile: COSMOIntentProfile) -> List[Dict]:
        """Turn insights into recommendations"""
        recommendations = []
        
        for insight in profile.key_insights[:3]:  # Take the top 3 insights
            recommendations.append({
                'priority': 'medium',
                'category': 'COSMO intent optimization',
                'action': insight,
                'impact': 'Improve the match between products and user intentions and increase conversion rate'
            })
        
        return recommendations


# Convenience function for direct usage
def analyze_cosmo_intent(product_data: Dict[str, Any]) -> Dict:
    """
    Convenience function: Analyze product COSMO intent
    
    Args:
        product_data: Keepa product data
        
    Returns:
        COSMO intent analysis results(Dictionary format)
    """
    analyzer = COSMOIntentAnalyzer()
    profile = analyzer.analyze(product_data)
    
    return {
        'intent_score': profile.intent_score,
        'five_points': {
            'persona': profile.persona,
            'mission': profile.mission,
            'context': profile.context,
            'needs': profile.needs,
            'preferences': profile.preferences,
        },
        'key_insights': profile.key_insights,
    }


def integrate_cosmo_to_actuarial(cosmo_result: Dict, actuarial_report: Dict) -> Dict:
    """
    Convenience function: Integrate COSMO analysis into actuarial reports
    
    Args:
        cosmo_result: COSMO analysis results
        actuarial_report: Actuarial report
        
    Returns:
        Integrated report
    """
    integrator = COSMOReportIntegrator()
    
    # Refactor the COSMOProfile object
    profile = COSMOIntentProfile(
        persona=cosmo_result['five_points']['persona'],
        mission=cosmo_result['five_points']['mission'],
        context=cosmo_result['five_points']['context'],
        needs=cosmo_result['five_points']['needs'],
        preferences=cosmo_result['five_points']['preferences'],
        intent_score=cosmo_result['intent_score'],
        key_insights=cosmo_result['key_insights']
    )
    
    return integrator.integrate_to_actuarial_report(profile, actuarial_report)
