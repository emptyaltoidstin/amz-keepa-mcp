"""
智能校准系统 - 将真实数据洞察应用到新ASIN分析

解决核心问题: 新ASIN没有真实运营数据时，如何让Keepa估算更准确？

策略:
1. 偏差学习 - 从真实数据中学习各维度的典型偏差
2. 类目校准 - 根据类目应用历史校准因子
3. 预测区间 - 给出保守/基准/乐观三种估算
4. 置信度评分 - 评估分析可信度
5. 风险预警 - 基于历史偏差模式给出风险警示
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CalibrationPattern:
    """校准模式数据类"""
    category: str  # 类目
    sample_count: int  # 样本数量
    
    # 偏差统计
    cogs_bias_mean: float  # COGS率偏差均值
    cogs_bias_std: float   # COGS率偏差标准差
    
    acos_bias_mean: float  # ACOS偏差均值
    acos_bias_std: float   # ACOS偏差标准差
    
    return_bias_mean: float  # 退货率偏差均值
    return_bias_std: float   # 退货率偏差标准差
    
    margin_bias_mean: float  # 净利率偏差均值
    margin_bias_std: float   # 净利率偏差标准差
    
    # 相关性特征
    price_sensitivity: float  # 价格敏感度
    ad_dependency: float      # 广告依赖度
    quality_sensitivity: float  # 质量敏感度
    
    # 更新时间
    last_updated: str


class IntelligentCalibrationEngine:
    """
    智能校准引擎
    
    从真实数据中学习偏差模式，应用到新ASIN分析
    """
    
    # 类目映射规则
    CATEGORY_MAPPINGS = {
        'Health & Household': ['Health', 'Household', 'Medical', 'Personal Care'],
        'Clothing, Shoes & Jewelry': ['Clothing', 'Shoes', 'Jewelry', 'Fashion'],
        'Electronics': ['Electronics', 'Technology', 'Gadgets', 'Accessories'],
        'Home & Kitchen': ['Home', 'Kitchen', 'Furniture', 'Decor'],
        'Sports & Outdoors': ['Sports', 'Outdoors', 'Fitness', 'Exercise'],
        'Beauty & Personal Care': ['Beauty', 'Cosmetics', 'Skincare', 'Haircare'],
        'Toys & Games': ['Toys', 'Games', 'Baby', 'Kids'],
        'Pet Supplies': ['Pet', 'Animal', 'Dog', 'Cat'],
        'Office Products': ['Office', 'Stationery', 'Supplies'],
        'Automotive': ['Automotive', 'Car', 'Vehicle'],
    }
    
    def __init__(self, calibration_db_path: str = "./cache/calibration_db.json"):
        self.calibration_db_path = calibration_db_path
        self.patterns: Dict[str, CalibrationPattern] = {}
        self.load_calibration_db()
    
    def load_calibration_db(self):
        """加载校准数据库"""
        if os.path.exists(self.calibration_db_path):
            try:
                with open(self.calibration_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for cat, pattern_data in data.items():
                        self.patterns[cat] = CalibrationPattern(**pattern_data)
                print(f"✅ 已加载 {len(self.patterns)} 个类目的校准数据")
            except Exception as e:
                print(f"⚠️ 加载校准数据库失败: {e}")
                self._init_default_patterns()
        else:
            print("📊 校准数据库不存在，初始化默认模式")
            self._init_default_patterns()
    
    def _init_default_patterns(self):
        """初始化默认校准模式（基于B0FDGFQGXN案例）"""
        # 健康家居类目（基于真实数据）
        self.patterns['Health & Household'] = CalibrationPattern(
            category='Health & Household',
            sample_count=1,
            cogs_bias_mean=0.5717,  # +57.17%
            cogs_bias_std=0.0,
            acos_bias_mean=0.1111,  # +11.11%
            acos_bias_std=0.0,
            return_bias_mean=0.1274,  # +12.74%
            return_bias_std=0.0,
            margin_bias_mean=-0.694,  # -69.4%
            margin_bias_std=0.0,
            price_sensitivity=0.3,
            ad_dependency=0.5,
            quality_sensitivity=0.8,
            last_updated=datetime.now().isoformat()
        )
        
        # 其他类目使用通用模式
        for cat in ['Clothing, Shoes & Jewelry', 'Electronics', 'Home & Kitchen']:
            self.patterns[cat] = self._create_generic_pattern(cat)
    
    def _create_generic_pattern(self, category: str) -> CalibrationPattern:
        """创建通用校准模式"""
        return CalibrationPattern(
            category=category,
            sample_count=0,
            cogs_bias_mean=0.20,  # 默认COGS高估20%
            cogs_bias_std=0.10,
            acos_bias_mean=0.05,  # 默认ACOS低估5%
            acos_bias_std=0.03,
            return_bias_mean=0.08,  # 默认退货率低估8%
            return_bias_std=0.05,
            margin_bias_mean=-0.15,  # 默认利润率高估15%
            margin_bias_std=0.10,
            price_sensitivity=0.5,
            ad_dependency=0.4,
            quality_sensitivity=0.5,
            last_updated=datetime.now().isoformat()
        )
    
    def learn_from_real_data(self, 
                            asin: str,
                            category: str,
                            keepa_estimate: Dict,
                            real_metrics: Dict) -> CalibrationPattern:
        """
        从真实数据中学习偏差模式
        
        Args:
            asin: ASIN编号
            category: 产品类目
            keepa_estimate: Keepa估算值
            real_metrics: 真实运营指标
            
        Returns:
            更新的校准模式
        """
        # 计算偏差
        cogs_bias = (1 - real_metrics['gross_margin']) - 0.30
        acos_bias = real_metrics['acos'] - 0.15
        return_bias = real_metrics['return_rate'] - 0.05
        margin_bias = real_metrics['net_margin'] - keepa_estimate.get('net_margin', 0.15)
        
        # 更新或创建模式
        if category in self.patterns:
            pattern = self.patterns[category]
            n = pattern.sample_count
            
            # 增量更新统计量
            pattern.cogs_bias_mean = (pattern.cogs_bias_mean * n + cogs_bias) / (n + 1)
            pattern.acos_bias_mean = (pattern.acos_bias_mean * n + acos_bias) / (n + 1)
            pattern.return_bias_mean = (pattern.return_bias_mean * n + return_bias) / (n + 1)
            pattern.margin_bias_mean = (pattern.margin_bias_mean * n + margin_bias) / (n + 1)
            pattern.sample_count = n + 1
            pattern.last_updated = datetime.now().isoformat()
        else:
            pattern = CalibrationPattern(
                category=category,
                sample_count=1,
                cogs_bias_mean=cogs_bias,
                cogs_bias_std=0.0,
                acos_bias_mean=acos_bias,
                acos_bias_std=0.0,
                return_bias_mean=return_bias,
                return_bias_std=0.0,
                margin_bias_mean=margin_bias,
                margin_bias_std=0.0,
                price_sensitivity=0.5,
                ad_dependency=real_metrics.get('ad_order_ratio', 0.5),
                quality_sensitivity=0.5,
                last_updated=datetime.now().isoformat()
            )
            self.patterns[category] = pattern
        
        # 保存到数据库
        self._save_calibration_db()
        
        return pattern
    
    def calibrate_new_asin(self, 
                          category: str,
                          keepa_analysis: Dict,
                          confidence_level: str = 'medium') -> Dict:
        """
        为新ASIN应用智能校准
        
        Args:
            category: 产品类目
            keepa_analysis: Keepa原始分析结果
            confidence_level: 置信水平 (low/medium/high)
            
        Returns:
            校准后的分析结果
        """
        # 获取校准模式
        pattern = self._get_pattern_for_category(category)
        
        # 原始估算值
        original_net_margin = keepa_analysis['profitability_analysis']['profitability']['net_margin']
        original_roi = keepa_analysis['profitability_analysis']['profitability']['roi_annual']
        original_monthly_profit = keepa_analysis['profitability_analysis']['profitability']['monthly_profit_estimate']
        
        # 应用校准 - margin_bias_mean 是偏差值（如-0.511表示真实比估算低51.1个百分点）
        calibrated_net_margin = original_net_margin + (pattern.margin_bias_mean * 100)  # 转换为百分点
        calibrated_roi = original_roi + (pattern.margin_bias_mean * 100)  # ROI也按百分点调整
        calibrated_monthly_profit = original_monthly_profit * (1 + pattern.margin_bias_mean)  # 利润按比例调整
        
        # 预测区间 - 基于偏差标准差
        prediction_range = self._calculate_prediction_range_v2(
            pattern, original_net_margin, original_roi, original_monthly_profit
        )
        
        # 置信度评分
        confidence_score = self._calculate_confidence_score(pattern, confidence_level)
        
        # 风险调整
        risk_adjustments = self._generate_risk_adjustments(pattern, keepa_analysis)
        
        return {
            'calibration_applied': True,
            'category': category,
            'calibration_pattern': {
                'sample_count': pattern.sample_count,
                'cogs_bias': f"{pattern.cogs_bias_mean:.1%}",
                'acos_bias': f"{pattern.acos_bias_mean:.1%}",
                'return_bias': f"{pattern.return_bias_mean:.1%}",
                'margin_bias': f"{pattern.margin_bias_mean:.1%}",
            },
            'original_estimate': {
                'net_margin': f"{original_net_margin:.1f}%",
                'roi_annual': f"{original_roi:.0f}%",
                'monthly_profit': f"${original_monthly_profit:.0f}",
            },
            'calibrated_estimate': {
                'net_margin': f"{calibrated_net_margin:.1f}%",
                'roi_annual': f"{calibrated_roi:.0f}%",
                'monthly_profit': f"${calibrated_monthly_profit:.0f}",
            },
            'prediction_range': prediction_range,
            'confidence_score': confidence_score,
            'risk_adjustments': risk_adjustments,
            'reliability_assessment': self._assess_reliability(pattern, confidence_score),
        }
    
    def _get_pattern_for_category(self, category: str) -> CalibrationPattern:
        """获取类目的校准模式"""
        # 直接匹配
        if category in self.patterns:
            return self.patterns[category]
        
        # 模糊匹配
        for cat_key, keywords in self.CATEGORY_MAPPINGS.items():
            if any(keyword.lower() in category.lower() for keyword in keywords):
                return self.patterns.get(cat_key, self._create_generic_pattern(category))
        
        # 返回通用模式
        return self._create_generic_pattern(category)
    
    def _get_calibration_factor(self, pattern: CalibrationPattern, level: str) -> float:
        """获取校准因子"""
        factors = {
            'low': 0.5,      # 保守估算
            'medium': 1.0,   # 标准估算
            'high': 1.5,     # 乐观估算
        }
        return factors.get(level, 1.0)
    
    def _calculate_prediction_range_v2(self, 
                                       pattern: CalibrationPattern,
                                       original_margin: float,
                                       original_roi: float,
                                       original_profit: float) -> Dict:
        """计算预测区间 V2 - 修正计算逻辑"""
        # margin_bias_mean 是比例偏差（如-0.511表示真实是估算的48.9%）
        bias = pattern.margin_bias_mean
        
        # 标准差（最小0.10即10%）
        std = max(pattern.margin_bias_std, 0.10)
        
        # 保守估算: 偏差 - 1.96 * 标准差
        conservative_bias = bias - 1.96 * std
        conservative_margin = original_margin + (conservative_bias * 100)
        conservative_roi = original_roi + (conservative_bias * 100)
        conservative_profit = original_profit * (1 + conservative_bias)
        
        # 基准估算: 直接应用平均偏差
        baseline_margin = original_margin + (bias * 100)
        baseline_roi = original_roi + (bias * 100)
        baseline_profit = original_profit * (1 + bias)
        
        # 乐观估算: 偏差 + 1.96 * 标准差
        optimistic_bias = bias + 1.96 * std
        optimistic_margin = original_margin + (optimistic_bias * 100)
        optimistic_roi = original_roi + (optimistic_bias * 100)
        optimistic_profit = original_profit * (1 + optimistic_bias)
        
        return {
            'conservative': {
                'net_margin': f"{conservative_margin:.1f}%",
                'roi_annual': f"{conservative_roi:.0f}%",
                'monthly_profit': f"${conservative_profit:.0f}",
                'description': '最坏情况估算 (95%置信下限)',
            },
            'baseline': {
                'net_margin': f"{baseline_margin:.1f}%",
                'roi_annual': f"{baseline_roi:.0f}%",
                'monthly_profit': f"${baseline_profit:.0f}",
                'description': '基于历史偏差调整的基准估算',
            },
            'optimistic': {
                'net_margin': f"{optimistic_margin:.1f}%",
                'roi_annual': f"{optimistic_roi:.0f}%",
                'monthly_profit': f"${optimistic_profit:.0f}",
                'description': '最好情况估算 (95%置信上限)',
            },
        }
    
    def _calculate_confidence_score(self, pattern: CalibrationPattern, level: str) -> Dict:
        """计算置信度评分"""
        # 基于样本数量计算置信度
        base_confidence = min(0.95, 0.3 + pattern.sample_count * 0.15)
        
        # 调整因子
        level_factors = {'low': 0.9, 'medium': 1.0, 'high': 0.85}
        
        final_confidence = base_confidence * level_factors.get(level, 1.0)
        
        return {
            'score': round(final_confidence, 2),
            'level': 'High' if final_confidence > 0.7 else 'Medium' if final_confidence > 0.4 else 'Low',
            'based_on_samples': pattern.sample_count,
            'reliability': 'Proven' if pattern.sample_count >= 3 else 'Estimated' if pattern.sample_count >= 1 else 'Generic',
        }
    
    def _generate_risk_adjustments(self, pattern: CalibrationPattern, keepa_analysis: Dict) -> List[Dict]:
        """生成风险调整建议"""
        adjustments = []
        
        # COGS风险
        if pattern.cogs_bias_mean > 0.3:
            adjustments.append({
                'risk': '高COGS风险',
                'likelihood': 'High',
                'impact': 'Profit reduction 30%+',
                'mitigation': '保守估算COGS率，预留30%+成本缓冲',
            })
        
        # ACOS风险
        if pattern.acos_bias_mean > 0.08:
            adjustments.append({
                'risk': '高ACOS风险',
                'likelihood': 'Medium',
                'impact': 'Ad cost 50%+ higher than estimated',
                'mitigation': '预算广告成本为估算值的1.5-2倍',
            })
        
        # 退货风险
        if pattern.return_bias_mean > 0.05:
            adjustments.append({
                'risk': '高退货率风险',
                'likelihood': 'High',
                'impact': 'Return rate 2-3x higher than estimated',
                'mitigation': '预留15-20%退货率预算，强化质量控制',
            })
        
        # 利润率风险
        if pattern.margin_bias_mean < -0.2:
            adjustments.append({
                'risk': '严重利润高估风险',
                'likelihood': 'High',
                'impact': 'Actual profit 50%+ lower than estimated',
                'mitigation': '使用保守估算进行决策，准备Plan B',
            })
        
        return adjustments
    
    def _assess_reliability(self, pattern: CalibrationPattern, confidence: Dict) -> str:
        """评估分析可靠性"""
        if pattern.sample_count >= 5 and confidence['score'] > 0.7:
            return "基于大量真实数据验证，分析结果高度可信"
        elif pattern.sample_count >= 2 and confidence['score'] > 0.5:
            return "基于部分真实数据，分析结果中等可信，建议谨慎决策"
        elif pattern.sample_count >= 1:
            return "基于少量真实数据，分析结果存在不确定性，建议保守估算"
        else:
            return "基于通用模式估算，未经验证，分析结果仅供参考"
    
    def _save_calibration_db(self):
        """保存校准数据库"""
        try:
            data = {cat: asdict(pattern) for cat, pattern in self.patterns.items()}
            os.makedirs(os.path.dirname(self.calibration_db_path), exist_ok=True)
            with open(self.calibration_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存校准数据库失败: {e}")
    
    def get_calibration_summary(self) -> Dict:
        """获取校准数据汇总"""
        return {
            'total_categories': len(self.patterns),
            'categories_with_real_data': sum(1 for p in self.patterns.values() if p.sample_count > 0),
            'total_samples': sum(p.sample_count for p in self.patterns.values()),
            'patterns': {
                cat: {
                    'samples': p.sample_count,
                    'margin_bias': f"{p.margin_bias_mean:.1%}",
                    'last_updated': p.last_updated,
                }
                for cat, p in self.patterns.items()
            }
        }


# 便捷函数
def calibrate_analysis_with_intelligence(keepa_analysis: Dict, 
                                         category: str,
                                         calibration_engine: Optional[IntelligentCalibrationEngine] = None) -> Dict:
    """
    便捷函数: 为Keepa分析应用智能校准
    
    Args:
        keepa_analysis: Keepa原始分析结果
        category: 产品类目
        calibration_engine: 校准引擎实例（可选）
        
    Returns:
        校准后的分析结果
    """
    if calibration_engine is None:
        calibration_engine = IntelligentCalibrationEngine()
    
    return calibration_engine.calibrate_new_asin(category, keepa_analysis)


def learn_from_real_data_and_update(asin: str,
                                    category: str,
                                    keepa_csv_path: str,
                                    real_sales_excel_path: str) -> Dict:
    """
    便捷函数: 从真实数据学习并更新校准数据库
    
    Args:
        asin: ASIN编号
        category: 产品类目
        keepa_csv_path: Keepa数据CSV路径
        real_sales_excel_path: 真实销售Excel路径
        
    Returns:
        更新后的校准模式
    """
    from src.actuarial_analyzer import AmazonActuary
    from src.real_sales_optimizer import RealSalesActuarialOptimizer
    
    # 执行Keepa分析
    actuary = AmazonActuary()
    keepa_analysis = actuary.analyze_from_csv(keepa_csv_path, include_cosmo=False)
    
    keepa_estimate = {
        'net_margin': keepa_analysis['profitability_analysis']['profitability']['net_margin'],
        'roi_annual': keepa_analysis['profitability_analysis']['profitability']['roi_annual'],
    }
    
    # 加载真实数据
    optimizer = RealSalesActuarialOptimizer()
    real_df = optimizer.load_real_sales_data(real_sales_excel_path)
    real_metrics = optimizer.calculate_real_metrics(real_df)
    
    # 学习并更新
    engine = IntelligentCalibrationEngine()
    pattern = engine.learn_from_real_data(asin, category, keepa_estimate, {
        'gross_margin': real_metrics.gross_margin,
        'net_margin': real_metrics.net_margin,
        'acos': real_metrics.acos,
        'return_rate': real_metrics.return_rate,
    })
    
    return {
        'message': f'成功从 {asin} 学习并更新 {category} 的校准模式',
        'pattern': asdict(pattern),
        'calibration_summary': engine.get_calibration_summary(),
    }
