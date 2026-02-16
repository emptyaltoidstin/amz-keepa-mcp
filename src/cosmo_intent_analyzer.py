"""
COSMO Intent Analyzer - Amazon COSMO算法意图挖掘分析器

基于Amazon COSMO (Common Sense Knowledge Generation)算法框架，
从Keepa数据中挖掘用户的五点意图详情：
1. 人群属性 (User Persona) - 谁在购买
2. 购物使命 (Shopping Mission) - 为什么购买
3. 使用场景 (Usage Context) - 何时何地使用
4. 需求痛点 (Needs & Pain Points) - 解决什么问题
5. 偏好特征 (Preferences) - 偏好什么特性

多Agents协同架构：
- DataExtractor Agent: 从163指标中提取原始数据
- IntentMiner Agent: 挖掘COSMO五点意图
- SemanticAnalyzer Agent: 语义关联分析
- ReportIntegrator Agent: 整合到精算报告
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
    """COSMO五点意图画像"""
    # 1. 人群属性
    persona: Dict[str, Any]
    # 2. 购物使命
    mission: Dict[str, Any]
    # 3. 使用场景
    context: Dict[str, Any]
    # 4. 需求痛点
    needs: Dict[str, Any]
    # 5. 偏好特征
    preferences: Dict[str, Any]
    # 综合评分
    intent_score: float
    # 关键洞察
    key_insights: List[str]


class COSMOIntentAnalyzer:
    """
    COSMO意图分析器 - Agent 1: DataExtractor + IntentMiner
    
    从Keepa数据中挖掘用户意图，构建知识图谱连接
    """
    
    # 人群关键词映射
    PERSONA_KEYWORDS = {
        '家庭用户': ['family', 'household', 'home', 'parents', 'kids', 'children', 'baby'],
        '专业人士': ['professional', 'office', 'work', 'business', 'executive'],
        '户外爱好者': ['outdoor', 'camping', 'hiking', 'travel', 'adventure', 'sports'],
        '学生群体': ['student', 'school', 'college', 'university', 'study'],
        '老年用户': ['elderly', 'senior', 'old', 'aging', 'retired'],
        '女性用户': ['women', 'female', 'lady', 'mom', 'mother', 'her'],
        '男性用户': ['men', 'male', 'man', 'father', 'dad', 'his'],
        '宠物主人': ['pet', 'dog', 'cat', 'animal', 'puppy', 'kitten'],
    }
    
    # 购物使命关键词
    MISSION_KEYWORDS = {
        '礼品购买': ['gift', 'present', 'birthday', 'anniversary', 'holiday', 'christmas'],
        '替换升级': ['replacement', 'upgrade', 'new', 'update', 'renew'],
        '首次购买': ['first', 'starter', 'beginner', 'entry', 'basic'],
        '囤货补货': ['bulk', 'stock', 'refill', 'supply', 'pack'],
        '应急需求': ['emergency', 'urgent', 'backup', 'spare', 'temporary'],
    }
    
    # 场景关键词
    CONTEXT_KEYWORDS = {
        '日常家用': ['daily', 'everyday', 'home', 'household', 'routine'],
        '办公场所': ['office', 'work', 'desk', 'professional', 'business'],
        '户外旅行': ['travel', 'trip', 'vacation', 'outdoor', 'camping'],
        '运动健身': ['gym', 'workout', 'fitness', 'exercise', 'sports', 'running'],
        '节庆场合': ['party', 'celebration', 'wedding', 'holiday', 'event'],
        '特殊环境': ['waterproof', 'outdoor', 'extreme', 'weather', 'condition'],
    }
    
    # 需求痛点关键词
    NEEDS_KEYWORDS = {
        '便捷性': ['convenient', 'easy', 'quick', 'simple', 'fast', 'effortless'],
        '安全性': ['safe', 'secure', 'protection', 'durable', 'reliable', 'quality'],
        '舒适性': ['comfortable', 'soft', 'ergonomic', 'cozy', 'smooth'],
        '美观性': ['beautiful', 'stylish', 'elegant', 'fashion', 'design', 'aesthetic'],
        '性价比': ['value', 'affordable', 'cheap', 'budget', 'economic', 'saving'],
        '功能性': ['functional', 'practical', 'useful', 'effective', 'efficient'],
    }
    
    # 偏好特征关键词
    PREFERENCE_KEYWORDS = {
        '品牌忠诚': ['brand', 'premium', 'authentic', 'genuine', 'original'],
        '环保意识': ['eco', 'organic', 'natural', 'sustainable', 'green', 'recycle'],
        '科技追求': ['smart', 'digital', 'tech', 'innovation', 'advanced', 'modern'],
        '定制个性': ['custom', 'personalized', 'unique', 'special', 'diy'],
        '社交展示': ['instagram', 'social', 'share', 'trendy', 'popular', 'viral'],
    }
    
    def __init__(self):
        self.intent_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, Dict[str, List[re.Pattern]]]:
        """编译正则表达式模式"""
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
        主分析入口 - 执行COSMO五点意图挖掘
        
        Args:
            product_data: Keepa产品数据(163指标)
            
        Returns:
            COSMOIntentProfile: 五点意图画像
        """
        # 提取文本数据源
        text_sources = self._extract_text_sources(product_data)
        
        # 五点意图挖掘
        persona = self._analyze_persona(text_sources, product_data)
        mission = self._analyze_mission(text_sources, product_data)
        context = self._analyze_context(text_sources, product_data)
        needs = self._analyze_needs(text_sources, product_data)
        preferences = self._analyze_preferences(text_sources, product_data)
        
        # 计算意图匹配度评分
        intent_score = self._calculate_intent_score(
            persona, mission, context, needs, preferences
        )
        
        # 生成关键洞察
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
        """提取所有文本数据源"""
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
        # 合并所有文本用于整体分析
        sources['combined'] = ' '.join(sources.values())
        return sources
    
    def _analyze_persona(self, sources: Dict[str, str], data: Dict) -> Dict:
        """分析人群属性 (Agent 1.1: PersonaMiner)"""
        scores = {}
        combined = sources['combined']
        
        for label, patterns in self.intent_patterns['persona'].items():
            score = sum(1 for p in patterns if p.search(combined))
            if score > 0:
                scores[label] = score
        
        # 基于产品属性推断
        indicators = []
        
        # 价格推断
        price = self._extract_price(data)
        if price > 100:
            indicators.append(('高端用户', 0.7))
        elif price < 20:
            indicators.append(('价格敏感用户', 0.6))
        
        # 品牌推断
        if data.get('Brand') and data.get('Brand') not in ['Generic', '']:
            indicators.append(('品牌意识用户', 0.5))
        
        # 评价数量推断
        review_count = self._extract_review_count(data)
        if review_count > 1000:
            indicators.append(('主流大众用户', 0.6))
        elif review_count < 50:
            indicators.append(('早期尝鲜用户', 0.4))
        
        # 整合结果
        primary_persona = max(scores.items(), key=lambda x: x[1])[0] if scores else '一般消费者'
        confidence = min(0.95, 0.5 + len(scores) * 0.1)
        
        return {
            'primary': primary_persona,
            'all_scores': scores,
            'indicators': indicators,
            'confidence': confidence,
            'persona_description': self._describe_persona(primary_persona, data)
        }
    
    def _analyze_mission(self, sources: Dict[str, str], data: Dict) -> Dict:
        """分析购物使命 (Agent 1.2: MissionMiner)"""
        scores = {}
        combined = sources['combined']
        
        for label, patterns in self.intent_patterns['mission'].items():
            score = sum(1 for p in patterns if p.search(combined))
            if score > 0:
                scores[label] = score
        
        indicators = []
        
        # 价格变动推断
        price_drops = self._extract_price_drops(data)
        if price_drops > 5:
            indicators.append(('促销敏感-等待折扣', 0.6))
        
        # 评论情感推断
        rating = self._extract_rating(data)
        if rating > 4.5 and self._extract_review_count(data) > 500:
            indicators.append(('品质导向-精挑细选', 0.7))
        
        # 产品特性推断
        if 'gift' in combined or 'present' in combined:
            indicators.append(('礼品购买使命', 0.8))
        
        # 季节性推断
        if self._is_seasonal_product(data):
            indicators.append(('季节性采购', 0.5))
        
        primary_mission = max(scores.items(), key=lambda x: x[1])[0] if scores else '日常采购'
        
        return {
            'primary': primary_mission,
            'all_scores': scores,
            'indicators': indicators,
            'urgency_level': self._assess_urgency(data),
            'mission_description': self._describe_mission(primary_mission, data)
        }
    
    def _analyze_context(self, sources: Dict[str, str], data: Dict) -> Dict:
        """分析使用场景 (Agent 1.3: ContextMiner)"""
        scores = {}
        combined = sources['combined']
        
        for label, patterns in self.intent_patterns['context'].items():
            score = sum(1 for p in patterns if p.search(combined))
            if score > 0:
                scores[label] = score
        
        indicators = []
        
        # 便携性推断场景
        weight = self._extract_weight(data)
        if weight and weight < 200:  # 小于200g
            indicators.append(('随身便携场景', 0.7))
        
        # 防水特性推断户外
        if 'waterproof' in combined or 'water-resistant' in combined:
            indicators.append(('户外/运动场景', 0.6))
        
        # 尺寸推断使用场景
        if data.get('Package: Length (cm)') and float(data.get('Package: Length (cm)', 0)) < 10:
            indicators.append(('紧凑空间使用', 0.5))
        
        primary_context = max(scores.items(), key=lambda x: x[1])[0] if scores else '通用场景'
        
        # 场景频率
        frequency = self._assess_usage_frequency(data)
        
        return {
            'primary': primary_context,
            'all_scores': scores,
            'indicators': indicators,
            'usage_frequency': frequency,
            'context_description': self._describe_context(primary_context, data)
        }
    
    def _analyze_needs(self, sources: Dict[str, str], data: Dict) -> Dict:
        """分析需求痛点 (Agent 1.4: NeedsMiner)"""
        scores = {}
        combined = sources['combined']
        
        for label, patterns in self.intent_patterns['needs'].items():
            score = sum(1 for p in patterns if p.search(combined))
            if score > 0:
                scores[label] = score
        
        indicators = []
        
        # 退货率推断痛点
        return_rate = self._estimate_return_rate(data)
        if return_rate > 0.08:
            indicators.append(('质量期望落差-高风险', 0.8))
        
        # 差评关键词挖掘
        negative_signals = self._extract_negative_signals(data)
        
        # 价格-评价关系推断
        price = self._extract_price(data)
        rating = self._extract_rating(data)
        if price > 50 and rating < 4.0:
            indicators.append(('高价低满意度-性价比痛点', 0.7))
        
        primary_need = max(scores.items(), key=lambda x: x[1])[0] if scores else '基础功能需求'
        
        # 痛点强度
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
        """分析偏好特征 (Agent 1.5: PreferenceMiner)"""
        scores = {}
        combined = sources['combined']
        
        for label, patterns in self.intent_patterns['preferences'].items():
            score = sum(1 for p in patterns if p.search(combined))
            if score > 0:
                scores[label] = score
        
        indicators = []
        
        # 品牌溢价接受度
        brand = data.get('Brand', '')
        if brand and brand not in ['Generic', '']:
            indicators.append(('品牌偏好', 0.6))
        
        # 材质偏好
        material = str(data.get('Material', '')).lower()
        if 'leather' in material or 'genuine' in combined:
            indicators.append(('天然材质偏好', 0.7))
        if 'organic' in combined or 'eco' in combined:
            indicators.append(('环保意识偏好', 0.6))
        
        # 功能复杂度偏好
        features = combined.count(',') + combined.count('·') + combined.count('•')
        if features > 10:
            indicators.append(('功能丰富偏好', 0.5))
        else:
            indicators.append(('简约实用偏好', 0.4))
        
        primary_preference = max(scores.items(), key=lambda x: x[1])[0] if scores else '实用主义'
        
        # 价格敏感度
        price_sensitivity = self._assess_price_sensitivity(data)
        
        return {
            'primary': primary_preference,
            'all_scores': scores,
            'indicators': indicators,
            'price_sensitivity': price_sensitivity,
            'preference_description': self._describe_preferences(primary_preference, data)
        }
    
    def _calculate_intent_score(self, *components) -> float:
        """计算整体意图匹配度评分"""
        # 基于各维度置信度计算加权分数
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
        """生成关键洞察 (Agent 2: SemanticAnalyzer)"""
        insights = []
        
        # 洞察1: 人群-使命匹配
        persona_primary = persona.get('primary', '')
        mission_primary = mission.get('primary', '')
        if persona_primary and mission_primary:
            insights.append(
                f"【人群-使命】{persona_primary}主要执行{mission_primary}，"
                f"建议营销突出{'礼品属性' if '礼品' in mission_primary else '实用价值'}"
            )
        
        # 洞察2: 场景-需求匹配
        context_primary = context.get('primary', '')
        needs_primary = needs.get('primary', '')
        if '户外' in context_primary and '安全' in needs_primary:
            insights.append("【场景-需求】户外场景+安全需求强烈，建议强化耐用性描述")
        
        # 洞察3: 痛点机会
        pain_intensity = needs.get('pain_intensity', 'low')
        if pain_intensity == 'high':
            insights.append("【痛点机会】高痛点产品，优化质量描述可减少退货率")
        
        # 洞察4: 价格敏感度
        price_sens = preferences.get('price_sensitivity', 'medium')
        if price_sens == 'high':
            insights.append("【定价策略】价格敏感用户群体，建议设置促销折扣")
        
        # 洞察5: 竞争定位
        if persona.get('indicators') and preferences.get('indicators'):
            insights.append(
                "【差异化建议】基于用户画像和偏好，建议突出"
                f"{preferences['primary']}特性以吸引{persona['primary']}"
            )
        
        return insights
    
    # Helper methods
    def _extract_price(self, data: Dict) -> float:
        """提取价格"""
        for field in ['Buy Box: Current', 'New: Current', 'Amazon: Current']:
            val = data.get(field, 0)
            if val and str(val).replace('.', '').isdigit():
                return float(val)
        return 0.0
    
    def _extract_review_count(self, data: Dict) -> int:
        """提取评价数量"""
        val = data.get('Reviews: Review Count', 0)
        try:
            return int(val)
        except:
            return 0
    
    def _extract_rating(self, data: Dict) -> float:
        """提取评分"""
        val = data.get('Reviews: Rating', 0)
        try:
            return float(val)
        except:
            return 0.0
    
    def _extract_price_drops(self, data: Dict) -> int:
        """提取降价次数"""
        val = data.get('Buy Box: Drops last 90 days', 0)
        try:
            return int(val)
        except:
            return 0
    
    def _extract_weight(self, data: Dict) -> Optional[float]:
        """提取重量"""
        val = data.get('Item: Weight (g)', 0) or data.get('Package: Weight (g)', 0)
        try:
            return float(val)
        except:
            return None
    
    def _estimate_return_rate(self, data: Dict) -> float:
        """估算退货率"""
        val = data.get('Return Rate', '')
        if isinstance(val, str):
            if 'High' in val:
                return 0.12
            elif 'Medium' in val:
                return 0.08
        return 0.05
    
    def _is_seasonal_product(self, data: Dict) -> bool:
        """判断是否为季节性产品"""
        category = str(data.get('Categories: Root', '')).lower()
        return any(x in category for x in ['holiday', 'christmas', 'summer', 'winter'])
    
    def _assess_urgency(self, data: Dict) -> str:
        """评估购买紧急程度"""
        if self._is_seasonal_product(data):
            return 'seasonal'
        if self._extract_price_drops(data) > 10:
            return 'price_waiting'
        return 'normal'
    
    def _assess_usage_frequency(self, data: Dict) -> str:
        """评估使用频率"""
        category = str(data.get('Categories: Root', '')).lower()
        if any(x in category for x in ['consumable', 'grocery', 'beauty']):
            return 'daily'
        elif any(x in category for x in ['electronics', 'clothing']):
            return 'weekly'
        return 'occasional'
    
    def _extract_negative_signals(self, data: Dict) -> List[str]:
        """提取负面信号"""
        signals = []
        if self._estimate_return_rate(data) > 0.10:
            signals.append('high_return_rate')
        if self._extract_rating(data) < 3.5:
            signals.append('low_rating')
        return signals
    
    def _assess_pain_intensity(self, data: Dict, signals: List[str]) -> str:
        """评估痛点强度"""
        if 'high_return_rate' in signals and 'low_rating' in signals:
            return 'high'
        elif len(signals) > 0:
            return 'medium'
        return 'low'
    
    def _assess_price_sensitivity(self, data: Dict) -> str:
        """评估价格敏感度"""
        drops = self._extract_price_drops(data)
        if drops > 15:
            return 'high'
        elif drops > 5:
            return 'medium'
        return 'low'
    
    # Description generators
    def _describe_persona(self, persona: str, data: Dict) -> str:
        """生成人群描述"""
        descriptions = {
            '家庭用户': '有孩子的家庭，关注实用性和安全性',
            '专业人士': '职场人士，注重品质和效率',
            '户外爱好者': '热爱户外活动，重视耐用性和便携性',
            '学生群体': '预算有限，追求性价比',
            '女性用户': '关注外观设计和使用体验',
            '男性用户': '注重功能性和技术参数',
        }
        return descriptions.get(persona, '一般消费者，无特定画像')
    
    def _describe_mission(self, mission: str, data: Dict) -> str:
        """生成购物使命描述"""
        descriptions = {
            '礼品购买': '为他人挑选礼物，注重包装和心意',
            '替换升级': '替换旧产品或升级现有设备',
            '首次购买': '首次尝试该品类产品，需要引导',
            '囤货补货': '常规补货，关注价格和数量',
            '应急需求': '紧急需要，对价格敏感度低',
        }
        return descriptions.get(mission, '日常采购，满足基本需求')
    
    def _describe_context(self, context: str, data: Dict) -> str:
        """生成场景描述"""
        descriptions = {
            '日常家用': '家庭日常使用，高频次',
            '办公场所': '工作场景，注重专业形象',
            '户外旅行': '旅行或户外活动，便携性重要',
            '运动健身': '运动场景，强调功能性',
            '节庆场合': '特殊节日或庆祝活动',
        }
        return descriptions.get(context, '通用场景，无特定限制')
    
    def _describe_needs(self, need: str, data: Dict) -> str:
        """生成需求描述"""
        descriptions = {
            '便捷性': '追求使用简单、省时省力',
            '安全性': '重视产品安全和可靠性',
            '舒适性': '注重使用体验和舒适感',
            '美观性': '外观设计是重要考量因素',
            '性价比': '在预算内追求最大价值',
            '功能性': '功能完整、性能可靠',
        }
        return descriptions.get(need, '满足基本功能需求')
    
    def _describe_preferences(self, pref: str, data: Dict) -> str:
        """生成偏好描述"""
        descriptions = {
            '品牌忠诚': '偏好知名品牌，信任度高',
            '环保意识': '关注可持续性和环保属性',
            '科技追求': '喜欢新技术和智能功能',
            '定制个性': '追求独特性和个性化',
            '社交展示': '适合分享，有社交属性',
        }
        return descriptions.get(pref, '实用主义，无特殊偏好')


class COSMOReportIntegrator:
    """
    COSMO报告整合器 - Agent 3: ReportIntegrator
    
    将COSMO五点意图分析整合到精算师报告中
    """
    
    def integrate_to_actuarial_report(self, cosmo_profile: COSMOIntentProfile, 
                                       actuarial_report: Dict) -> Dict:
        """
        将COSMO分析整合到精算师报告
        
        Args:
            cosmo_profile: COSMO五点意图画像
            actuarial_report: 原有精算报告
            
        Returns:
            增强后的精算报告
        """
        # 添加COSMO意图分析章节
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
        
        # 增强战略建议
        if 'strategic_recommendations' in actuarial_report:
            actuarial_report['strategic_recommendations'].extend(
                self._convert_insights_to_recommendations(cosmo_profile)
            )
        
        # 更新产品身份描述
        if 'product_identity' in actuarial_report:
            actuarial_report['product_identity']['target_persona'] = \
                cosmo_profile.persona.get('primary', '一般消费者')
            actuarial_report['product_identity']['shopping_mission'] = \
                cosmo_profile.mission.get('primary', '日常采购')
        
        return actuarial_report
    
    def _derive_strategic_implications(self, profile: COSMOIntentProfile) -> Dict:
        """推导战略含义"""
        implications = {
            'product_positioning': self._suggest_positioning(profile),
            'pricing_strategy': self._suggest_pricing(profile),
            'marketing_angle': self._suggest_marketing(profile),
            'inventory_planning': self._suggest_inventory(profile),
        }
        return implications
    
    def _suggest_positioning(self, profile: COSMOIntentProfile) -> str:
        """建议产品定位"""
        persona = profile.persona.get('primary', '')
        needs = profile.needs.get('primary', '')
        return f"针对{persona}的{needs}定位"
    
    def _suggest_pricing(self, profile: COSMOIntentProfile) -> str:
        """建议定价策略"""
        sensitivity = profile.preferences.get('price_sensitivity', 'medium')
        strategies = {
            'high': '促销导向定价，设置阶梯折扣',
            'medium': '价值导向定价，突出性价比',
            'low': ' premium定价，强调品质'
        }
        return strategies.get(sensitivity, ' competitive定价')
    
    def _suggest_marketing(self, profile: COSMOIntentProfile) -> str:
        """建议营销策略"""
        mission = profile.mission.get('primary', '')
        context = profile.context.get('primary', '')
        return f"在{context}场景下强调{mission}价值"
    
    def _suggest_inventory(self, profile: COSMOIntentProfile) -> str:
        """建议库存策略"""
        frequency = profile.context.get('usage_frequency', 'occasional')
        strategies = {
            'daily': '高频周转，保持充足库存',
            'weekly': '常规补货，关注趋势',
            'occasional': '按需备货，避免积压'
        }
        return strategies.get(frequency, '稳健库存策略')
    
    def _convert_insights_to_recommendations(self, profile: COSMOIntentProfile) -> List[Dict]:
        """将洞察转换为建议"""
        recommendations = []
        
        for insight in profile.key_insights[:3]:  # 取前3个洞察
            recommendations.append({
                'priority': 'medium',
                'category': 'COSMO意图优化',
                'action': insight,
                'impact': '提升产品与用户意图匹配度，增加转化率'
            })
        
        return recommendations


# Convenience function for direct usage
def analyze_cosmo_intent(product_data: Dict[str, Any]) -> Dict:
    """
    便捷函数: 分析产品COSMO意图
    
    Args:
        product_data: Keepa产品数据
        
    Returns:
        COSMO意图分析结果(字典格式)
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
    便捷函数: 整合COSMO分析到精算报告
    
    Args:
        cosmo_result: COSMO分析结果
        actuarial_report: 精算报告
        
    Returns:
        整合后的报告
    """
    integrator = COSMOReportIntegrator()
    
    # 重构COSMOProfile对象
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
