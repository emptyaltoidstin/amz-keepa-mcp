"""
Intelligent calibration system - Apply real data insights to new ASIN analysis

Solve the core problem: How to make Keepa estimates more accurate when the new ASIN does not have real operating data?

Strategy:
1. Bias learning - Learn typical deviations in each dimension from real data
2. Category calibration - Apply historical calibration factors based on category
3. Prediction interval - give conservative/benchmark/Three optimistic estimates
4. Confidence score - Evaluate the credibility of your analysis
5. Risk warning - Provide risk warnings based on historical deviation patterns
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
    """Calibration mode data class"""
    category: str  # Category
    sample_count: int  # sample size
    
    # Deviation Statistics
    cogs_bias_mean: float  # COGS rate deviation mean
    cogs_bias_std: float   # COGS rate deviation standard deviation
    
    acos_bias_mean: float  # ACOS deviation mean
    acos_bias_std: float   # ACOS deviation standard deviation
    
    return_bias_mean: float  # Return rate deviation mean
    return_bias_std: float   # return rate deviation standard deviation
    
    margin_bias_mean: float  # Net interest rate deviation mean
    margin_bias_std: float   # Net interest rate deviation standard deviation
    
    # Relevant features
    price_sensitivity: float  # price sensitivity
    ad_dependency: float      # advertising dependence
    quality_sensitivity: float  # mass sensitivity
    
    # Update time
    last_updated: str


class IntelligentCalibrationEngine:
    """
    Smart calibration engine
    
    Learn bias patterns from real data and apply them to new ASIN analysis
    """
    
    # Category mapping rules
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
        """Load calibration database"""
        if os.path.exists(self.calibration_db_path):
            try:
                with open(self.calibration_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for cat, pattern_data in data.items():
                        self.patterns[cat] = CalibrationPattern(**pattern_data)
                print(f"✅ Loaded {len(self.patterns)} Calibration data for categories")
            except Exception as e:
                print(f"⚠️ Failed to load calibration database: {e}")
                self._init_default_patterns()
        else:
            print("📊 Calibration database does not exist, initialize default mode")
            self._init_default_patterns()
    
    def _init_default_patterns(self):
        """Initialize the default calibration mode (based on B0FDGFQGXN case)"""
        # Healthy home category (based on real data)
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
        
        # Other categories use common patterns
        for cat in ['Clothing, Shoes & Jewelry', 'Electronics', 'Home & Kitchen']:
            self.patterns[cat] = self._create_generic_pattern(cat)
    
    def _create_generic_pattern(self, category: str) -> CalibrationPattern:
        """Create a universal calibration pattern"""
        return CalibrationPattern(
            category=category,
            sample_count=0,
            cogs_bias_mean=0.20,  # Default COGS overestimation 20%
            cogs_bias_std=0.10,
            acos_bias_mean=0.05,  # Default ACOS underestimates 5%
            acos_bias_std=0.03,
            return_bias_mean=0.08,  # The default return rate is underestimated by 8%
            return_bias_std=0.05,
            margin_bias_mean=-0.15,  # Default profit margin is overestimated by 15%
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
        Learning bias patterns from real data
        
        Args:
            asin: ASIN number
            category: Product category
            keepa_estimate: Keepa estimates
            real_metrics: real operating indicators
            
        Returns:
            Updated calibration mode
        """
        # Calculate deviation
        cogs_bias = (1 - real_metrics['gross_margin']) - 0.30
        acos_bias = real_metrics['acos'] - 0.15
        return_bias = real_metrics['return_rate'] - 0.05
        margin_bias = real_metrics['net_margin'] - keepa_estimate.get('net_margin', 0.15)
        
        # Update or create schema
        if category in self.patterns:
            pattern = self.patterns[category]
            n = pattern.sample_count
            
            # Incrementally update statistics
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
        
        # Save to database
        self._save_calibration_db()
        
        return pattern
    
    def calibrate_new_asin(self, 
                          category: str,
                          keepa_analysis: Dict,
                          confidence_level: str = 'medium') -> Dict:
        """
        Apply smart calibration for new ASINs
        
        Args:
            category: Product category
            keepa_analysis: Keepa original analysis results
            confidence_level: confidence level (low/medium/high)
            
        Returns:
            Analysis results after calibration
        """
        # Get calibration mode
        pattern = self._get_pattern_for_category(category)
        
        # Original estimate
        original_net_margin = keepa_analysis['profitability_analysis']['profitability']['net_margin']
        original_roi = keepa_analysis['profitability_analysis']['profitability']['roi_annual']
        original_monthly_profit = keepa_analysis['profitability_analysis']['profitability']['monthly_profit_estimate']
        
        # Apply calibration - margin_bias_mean is the deviation value (e.g.-0.511 means the true value is 51.1 percentage points lower than the estimate)
        calibrated_net_margin = original_net_margin + (pattern.margin_bias_mean * 100)  # Convert to percentage points
        calibrated_roi = original_roi + (pattern.margin_bias_mean * 100)  # ROI is also adjusted by percentage points
        calibrated_monthly_profit = original_monthly_profit * (1 + pattern.margin_bias_mean)  # Profits are adjusted proportionally
        
        # prediction interval - Based on deviation standard deviation
        prediction_range = self._calculate_prediction_range_v2(
            pattern, original_net_margin, original_roi, original_monthly_profit
        )
        
        # confidence score
        confidence_score = self._calculate_confidence_score(pattern, confidence_level)
        
        # risk adjustment
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
        """Get the calibration mode of a category"""
        # direct match
        if category in self.patterns:
            return self.patterns[category]
        
        # fuzzy matching
        for cat_key, keywords in self.CATEGORY_MAPPINGS.items():
            if any(keyword.lower() in category.lower() for keyword in keywords):
                return self.patterns.get(cat_key, self._create_generic_pattern(category))
        
        # Return to common mode
        return self._create_generic_pattern(category)
    
    def _get_calibration_factor(self, pattern: CalibrationPattern, level: str) -> float:
        """Get calibration factor"""
        factors = {
            'low': 0.5,      # Conservative estimate
            'medium': 1.0,   # standard estimate
            'high': 1.5,     # Optimistic estimate
        }
        return factors.get(level, 1.0)
    
    def _calculate_prediction_range_v2(self, 
                                       pattern: CalibrationPattern,
                                       original_margin: float,
                                       original_roi: float,
                                       original_profit: float) -> Dict:
        """Calculate prediction interval V2 - Correct calculation logic"""
        # margin_bias_mean is the proportional deviation (e.g.-0.511 means the true is estimated 48.9%）
        bias = pattern.margin_bias_mean
        
        # Standard deviation (minimum 0.10 is 10%）
        std = max(pattern.margin_bias_std, 0.10)
        
        # Conservative estimate: Deviation - 1.96 * standard deviation
        conservative_bias = bias - 1.96 * std
        conservative_margin = original_margin + (conservative_bias * 100)
        conservative_roi = original_roi + (conservative_bias * 100)
        conservative_profit = original_profit * (1 + conservative_bias)
        
        # baseline estimate: Apply mean deviation directly
        baseline_margin = original_margin + (bias * 100)
        baseline_roi = original_roi + (bias * 100)
        baseline_profit = original_profit * (1 + bias)
        
        # Optimistic estimate: Deviation + 1.96 * standard deviation
        optimistic_bias = bias + 1.96 * std
        optimistic_margin = original_margin + (optimistic_bias * 100)
        optimistic_roi = original_roi + (optimistic_bias * 100)
        optimistic_profit = original_profit * (1 + optimistic_bias)
        
        return {
            'conservative': {
                'net_margin': f"{conservative_margin:.1f}%",
                'roi_annual': f"{conservative_roi:.0f}%",
                'monthly_profit': f"${conservative_profit:.0f}",
                'description': 'worst case estimate (95%lower confidence limit)',
            },
            'baseline': {
                'net_margin': f"{baseline_margin:.1f}%",
                'roi_annual': f"{baseline_roi:.0f}%",
                'monthly_profit': f"${baseline_profit:.0f}",
                'description': 'Baseline estimates adjusted for historical deviations',
            },
            'optimistic': {
                'net_margin': f"{optimistic_margin:.1f}%",
                'roi_annual': f"{optimistic_roi:.0f}%",
                'monthly_profit': f"${optimistic_profit:.0f}",
                'description': 'best case estimate (95%upper confidence limit)',
            },
        }
    
    def _calculate_confidence_score(self, pattern: CalibrationPattern, level: str) -> Dict:
        """Calculate confidence score"""
        # Calculate confidence based on sample size
        base_confidence = min(0.95, 0.3 + pattern.sample_count * 0.15)
        
        # adjustment factor
        level_factors = {'low': 0.9, 'medium': 1.0, 'high': 0.85}
        
        final_confidence = base_confidence * level_factors.get(level, 1.0)
        
        return {
            'score': round(final_confidence, 2),
            'level': 'High' if final_confidence > 0.7 else 'Medium' if final_confidence > 0.4 else 'Low',
            'based_on_samples': pattern.sample_count,
            'reliability': 'Proven' if pattern.sample_count >= 3 else 'Estimated' if pattern.sample_count >= 1 else 'Generic',
        }
    
    def _generate_risk_adjustments(self, pattern: CalibrationPattern, keepa_analysis: Dict) -> List[Dict]:
        """Generate risk adjustment recommendations"""
        adjustments = []
        
        # COGS risk
        if pattern.cogs_bias_mean > 0.3:
            adjustments.append({
                'risk': 'High COGS risk',
                'likelihood': 'High',
                'impact': 'Profit reduction 30%+',
                'mitigation': 'Conservatively estimate the COGS rate and reserve 30%+cost buffer',
            })
        
        # ACOS risks
        if pattern.acos_bias_mean > 0.08:
            adjustments.append({
                'risk': 'High ACOS risk',
                'likelihood': 'Medium',
                'impact': 'Ad cost 50%+ higher than estimated',
                'mitigation': 'The budgeted advertising cost is 1.5 of the estimate-2 times',
            })
        
        # Return risk
        if pattern.return_bias_mean > 0.05:
            adjustments.append({
                'risk': 'High return rate risk',
                'likelihood': 'High',
                'impact': 'Return rate 2-3x higher than estimated',
                'mitigation': 'Reserve 15-20%Return rate budget and strengthen quality control',
            })
        
        # Margin risk
        if pattern.margin_bias_mean < -0.2:
            adjustments.append({
                'risk': 'Serious profit overestimation risk',
                'likelihood': 'High',
                'impact': 'Actual profit 50%+ lower than estimated',
                'mitigation': 'Use conservative estimates to make decisions and prepare Plan B',
            })
        
        return adjustments
    
    def _assess_reliability(self, pattern: CalibrationPattern, confidence: Dict) -> str:
        """Evaluate analytical reliability"""
        if pattern.sample_count >= 5 and confidence['score'] > 0.7:
            return "Based on a large amount of real data verification, the analysis results are highly credible"
        elif pattern.sample_count >= 2 and confidence['score'] > 0.5:
            return "Based on some real data, the analysis results are moderately credible. It is recommended to make cautious decisions."
        elif pattern.sample_count >= 1:
            return "Based on a small amount of real data, the analysis results are uncertain, and conservative estimates are recommended."
        else:
            return "Estimated based on general model, without verification, analysis results are for reference only"
    
    def _save_calibration_db(self):
        """Save calibration database"""
        try:
            data = {cat: asdict(pattern) for cat, pattern in self.patterns.items()}
            os.makedirs(os.path.dirname(self.calibration_db_path), exist_ok=True)
            with open(self.calibration_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save calibration database: {e}")
    
    def get_calibration_summary(self) -> Dict:
        """Get a summary of calibration data"""
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


# Convenience function
def calibrate_analysis_with_intelligence(keepa_analysis: Dict, 
                                         category: str,
                                         calibration_engine: Optional[IntelligentCalibrationEngine] = None) -> Dict:
    """
    Convenience function: Apply smart calibration for Keepa analysis
    
    Args:
        keepa_analysis: Keepa original analysis results
        category: Product category
        calibration_engine: Calibration engine instance (optional)
        
    Returns:
        Analysis results after calibration
    """
    if calibration_engine is None:
        calibration_engine = IntelligentCalibrationEngine()
    
    return calibration_engine.calibrate_new_asin(category, keepa_analysis)


def learn_from_real_data_and_update(asin: str,
                                    category: str,
                                    keepa_csv_path: str,
                                    real_sales_excel_path: str) -> Dict:
    """
    Convenience function: Learn from real data and update the calibration database
    
    Args:
        asin: ASIN number
        category: Product category
        keepa_csv_path: Keepa data CSV path
        real_sales_excel_path: Real Sales Excel Path
        
    Returns:
        Updated calibration mode
    """
    from src.actuarial_analyzer import AmazonActuary
    from src.real_sales_optimizer import RealSalesActuarialOptimizer
    
    # Perform Keepa analysis
    actuary = AmazonActuary()
    keepa_analysis = actuary.analyze_from_csv(keepa_csv_path, include_cosmo=False)
    
    keepa_estimate = {
        'net_margin': keepa_analysis['profitability_analysis']['profitability']['net_margin'],
        'roi_annual': keepa_analysis['profitability_analysis']['profitability']['roi_annual'],
    }
    
    # Load real data
    optimizer = RealSalesActuarialOptimizer()
    real_df = optimizer.load_real_sales_data(real_sales_excel_path)
    real_metrics = optimizer.calculate_real_metrics(real_df)
    
    # Learn and update
    engine = IntelligentCalibrationEngine()
    pattern = engine.learn_from_real_data(asin, category, keepa_estimate, {
        'gross_margin': real_metrics.gross_margin,
        'net_margin': real_metrics.net_margin,
        'acos': real_metrics.acos,
        'return_rate': real_metrics.return_rate,
    })
    
    return {
        'message': f'successfully from {asin} Learn and update {category} calibration mode',
        'pattern': asdict(pattern),
        'calibration_summary': engine.get_calibration_summary(),
    }
