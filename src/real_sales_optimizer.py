"""
Actuarial Optimizer for Real Sales Data (Real Sales Actuarial Optimizer)

Optimize the actuarial model based on real Amazon operating data to solve the problem of deviation between Keepa estimation and real data.

Core functions:
1. Real data calibration - Revise estimated parameters using actual operating data
2. Fusion of multiple data sources - Integrate Keepa data + Real sales data
3. Dynamic parameter adjustment - Optimize forecasting based on historical data trends
4. Real profit model - Consider all true cost items

Optimize dimensions:
- COGS rate: From estimate 30% → Real 87% (Critical fix!)
- ACOS: From estimate 15% → Real 26%
- return rate: From estimate 5% → Real 18%
- Promotional costs: Add Coupon/Deal cost
- Organic vs Insertion Order: Distinguish traffic source profit
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RealSalesMetrics:
    """Real sales indicator data class"""
    # Sales Basics
    total_sales: float
    total_units: int
    avg_price: float
    avg_daily_sales: float
    
    # Returns and refunds (Key!)
    refund_rate: float
    return_rate: float
    
    # advertising performance
    acos: float
    roas: float
    ad_spend_ratio: float
    ad_order_ratio: float
    
    # real profit (The most important thing!)
    gross_margin: float
    net_margin: float
    
    # Promotional costs
    coupon_cost_ratio: float
    deal_cost_ratio: float
    
    # Data quality
    data_days: int
    confidence_score: float


class RealSalesActuarialOptimizer:
    """
    Actuarial Optimizer for Real Sales Data
    
    Multi-Agents collaborative architecture:
    - DataLoader Agent: Load real sales Excel
    - Calibrator Agent: Calculate calibration parameters
    - Fusion Agent: Fusion Keepa+real data
    - Optimizer Agent: Generate optimization suggestions
    """
    
    def __init__(self):
        self.baseline_params = {
            'estimated_cogs_rate': 0.30,
            'estimated_acos': 0.15,
            'estimated_return_rate': 0.05,
            'estimated_refund_rate': 0.05,
        }
        self.calibration_factors = {}
    
    def load_real_sales_data(self, excel_path: str) -> pd.DataFrame:
        """
        Agent 1: DataLoader - Load real sales data
        
        Args:
            excel_path: Sales data Excel file path
            
        Returns:
            Cleaned DataFrame
        """
        df = pd.read_excel(excel_path)
        
        # Data cleaning
        # Remove summary row
        df = df[df['Date'] != 'Summary'].copy()
        
        # Convert numeric column
        numeric_cols = ['Sales volume', 'sales', 'Refund amount', 'Return volume', 'advertising spend', 
                       'advertising sales', 'Gross profit on sales', 'gross sales profit margin', 'Sales net gross profit margin',
                       'ACOS', 'ROAS', 'Coupon cost', 'Deal cost']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def calculate_real_metrics(self, df: pd.DataFrame) -> RealSalesMetrics:
        """
        Agent 2: Calibrator - Calculate real operating indicators
        
        Args:
            df: Cleaned sales data
            
        Returns:
            RealSalesMetrics real metric object
        """
        # Basic sales data
        total_sales = df['sales'].sum()
        total_units = df['Sales volume'].sum()
        avg_price = df['average sales price'].mean()
        data_days = len(df)
        avg_daily_sales = total_units / data_days if data_days > 0 else 0
        
        # Return Refund Rate (Key!)
        refund_rate = df['Refund amount'].sum() / total_units if total_units > 0 else 0
        return_rate = df['Return volume'].sum() / total_units if total_units > 0 else 0
        
        # advertising metrics
        total_ad_spend = abs(df['advertising spend'].sum())  # cost is negative
        total_ad_sales = df['advertising sales'].sum()
        acos = total_ad_spend / total_ad_sales if total_ad_sales > 0 else 0
        roas = total_ad_sales / total_ad_spend if total_ad_spend > 0 else 0
        ad_spend_ratio = total_ad_spend / total_sales if total_sales > 0 else 0
        
        total_ad_orders = df['Insertion order volume'].sum()
        total_orders = df['Order quantity'].sum()
        ad_order_ratio = total_ad_orders / total_orders if total_orders > 0 else 0
        
        # real profit rate (The most important thing!)
        avg_gross_margin = df['gross sales profit margin'].mean()
        avg_net_margin = df['Sales net gross profit margin'].mean()
        
        # Promotional costs
        total_coupon = df['Coupon cost'].sum()
        total_deal = df['Deal cost'].sum()
        coupon_cost_ratio = total_coupon / total_sales if total_sales > 0 else 0
        deal_cost_ratio = total_deal / total_sales if total_sales > 0 else 0
        
        # Data quality score
        confidence_score = self._calculate_data_quality(df)
        
        return RealSalesMetrics(
            total_sales=total_sales,
            total_units=total_units,
            avg_price=avg_price,
            avg_daily_sales=avg_daily_sales,
            refund_rate=refund_rate,
            return_rate=return_rate,
            acos=acos,
            roas=roas,
            ad_spend_ratio=ad_spend_ratio,
            ad_order_ratio=ad_order_ratio,
            gross_margin=avg_gross_margin,
            net_margin=avg_net_margin,
            coupon_cost_ratio=coupon_cost_ratio,
            deal_cost_ratio=deal_cost_ratio,
            data_days=data_days,
            confidence_score=confidence_score
        )
    
    def calibrate_actuarial_model(self, real_metrics: RealSalesMetrics) -> Dict:
        """
        Agent 3: Calibrator - Generate calibration parameters
        
        Compare Keepa estimates vs real data and generate calibration factors
        
        Args:
            real_metrics: real operating indicators
            
        Returns:
            Calibration parameter dictionary
        """
        calibrations = {}
        
        # 1. COGS rate calibration (The most important thing!)
        estimated_cogs = self.baseline_params['estimated_cogs_rate']
        real_cogs = 1 - real_metrics.gross_margin  # Deducing COGS from gross profit margin
        calibrations['cogs_rate'] = {
            'estimated': estimated_cogs,
            'real': real_cogs,
            'calibration_factor': real_cogs / estimated_cogs if estimated_cogs > 0 else 1,
            'impact': 'Critical' if abs(real_cogs - estimated_cogs) > 0.2 else 'Medium'
        }
        
        # 2. ACOS calibration
        estimated_acos = self.baseline_params['estimated_acos']
        real_acos = real_metrics.acos
        calibrations['acos'] = {
            'estimated': estimated_acos,
            'real': real_acos,
            'calibration_factor': real_acos / estimated_acos if estimated_acos > 0 else 1,
            'impact': 'High' if real_acos > estimated_acos * 1.5 else 'Medium'
        }
        
        # 3. Return rate calibration
        estimated_return = self.baseline_params['estimated_return_rate']
        real_return = real_metrics.return_rate
        calibrations['return_rate'] = {
            'estimated': estimated_return,
            'real': real_return,
            'calibration_factor': real_return / estimated_return if estimated_return > 0 else 1,
            'impact': 'High' if real_return > estimated_return * 2 else 'Medium'
        }
        
        # 4. Refund rate calibration
        estimated_refund = self.baseline_params['estimated_refund_rate']
        real_refund = real_metrics.refund_rate
        calibrations['refund_rate'] = {
            'estimated': estimated_refund,
            'real': real_refund,
            'calibration_factor': real_refund / estimated_refund if estimated_refund > 0 else 1,
            'impact': 'Medium'
        }
        
        # 5. Proportion of advertising orders
        calibrations['ad_order_ratio'] = {
            'real': real_metrics.ad_order_ratio,
            'natural_order_ratio': 1 - real_metrics.ad_order_ratio,
            'impact': 'Medium'
        }
        
        self.calibration_factors = calibrations
        return calibrations
    
    def optimize_profit_calculation(self, 
                                   keepa_analysis: Dict,
                                   real_metrics: RealSalesMetrics) -> Dict:
        """
        Agent 4: Optimizer - Generate optimized profit calculations
        
        Fusion of Keepa data + Real data to generate more accurate profit forecasts
        
        Args:
            keepa_analysis: Actuarial analysis results based on Keepa
            real_metrics: real operating indicators
            
        Returns:
            Optimized analysis results
        """
        # Get current price
        current_price = keepa_analysis['profitability_analysis']['price_analysis']['current_price']
        
        # Recalculate costs using real parameters
        # Note: The real data is RMB and needs to be converted to US dollars.(Assume an exchange rate of 7.2)
        exchange_rate = 7.2
        price_rmb = current_price * exchange_rate
        
        # Real COGS (Based on real gross profit margin)
        real_cogs_rate = 1 - real_metrics.gross_margin
        cogs_per_unit = price_rmb * real_cogs_rate
        
        # True FBA fees (Estimate)
        fba_fee_rmb = 60  # approx.$8.5
        
        # real commission (15%)
        referral_fee = price_rmb * 0.15
        
        # true return cost
        return_cost = price_rmb * real_metrics.return_rate * 0.3  # 30%net loss
        
        # True storage fees
        storage_cost = 1.0  # approx.$0.15
        
        # real advertising cost (Based on real ACOS)
        ad_cost = price_rmb * real_metrics.acos
        
        # Promotional costs
        coupon_cost = price_rmb * real_metrics.coupon_cost_ratio
        deal_cost = price_rmb * real_metrics.deal_cost_ratio
        
        # total cost
        total_cost = (cogs_per_unit + fba_fee_rmb + referral_fee + 
                     return_cost + storage_cost + ad_cost + coupon_cost + deal_cost)
        
        # Profit calculation
        gross_profit = price_rmb - cogs_per_unit - fba_fee_rmb - referral_fee
        net_profit = price_rmb - total_cost
        
        gross_margin = (gross_profit / price_rmb * 100) if price_rmb > 0 else 0
        net_margin = (net_profit / price_rmb * 100) if price_rmb > 0 else 0
        
        # Convert to USD
        net_profit_usd = net_profit / exchange_rate
        
        # Average monthly sales forecast (Based on real data)
        monthly_units = real_metrics.avg_daily_sales * 30
        monthly_profit = net_profit_usd * monthly_units
        
        # ROI calculation
        inventory_investment = (cogs_per_unit / exchange_rate) * monthly_units * 1.5
        roi_annual = ((monthly_profit * 12) / inventory_investment * 100) if inventory_investment > 0 else 0
        
        optimized_profit = {
            'original_keepa_estimate': {
                'net_margin': keepa_analysis['profitability_analysis']['profitability']['net_margin'],
                'roi_annual': keepa_analysis['profitability_analysis']['profitability']['roi_annual'],
                'monthly_profit': keepa_analysis['profitability_analysis']['profitability']['monthly_profit_estimate'],
            },
            'real_data_calibrated': {
                'net_margin': round(net_margin, 1),
                'gross_margin': round(gross_margin, 1),
                'roi_annual': round(roi_annual, 1),
                'monthly_profit': round(monthly_profit, 2),
                'monthly_units': round(monthly_units, 0),
            },
            'cost_structure_rmb': {
                'price': round(price_rmb, 2),
                'cogs': round(cogs_per_unit, 2),
                'fba_fee': round(fba_fee_rmb, 2),
                'referral_fee': round(referral_fee, 2),
                'return_cost': round(return_cost, 2),
                'storage_cost': round(storage_cost, 2),
                'ad_cost': round(ad_cost, 2),
                'promo_cost': round(coupon_cost + deal_cost, 2),
                'total_cost': round(total_cost, 2),
            },
            'variance_analysis': {
                'net_margin_variance': round(net_margin - keepa_analysis['profitability_analysis']['profitability']['net_margin'], 1),
                'roi_variance': round(roi_annual - keepa_analysis['profitability_analysis']['profitability']['roi_annual'], 1),
                'profit_variance': round(monthly_profit - keepa_analysis['profitability_analysis']['profitability']['monthly_profit_estimate'], 2),
            }
        }
        
        return optimized_profit
    
    def generate_optimization_report(self, 
                                    real_metrics: RealSalesMetrics,
                                    calibrations: Dict,
                                    optimized: Dict) -> Dict:
        """
        Generate a complete optimization report
        
        Returns:
            Optimization report dictionary
        """
        report = {
            'data_source': {
                'type': 'Real Sales Data + Keepa API',
                'data_days': real_metrics.data_days,
                'confidence_score': real_metrics.confidence_score,
                'analysis_date': datetime.now().isoformat(),
            },
            'real_metrics': {
                'sales_performance': {
                    'total_sales_rmb': round(real_metrics.total_sales, 2),
                    'total_units': real_metrics.total_units,
                    'avg_price_rmb': round(real_metrics.avg_price, 2),
                    'avg_daily_sales': round(real_metrics.avg_daily_sales, 1),
                },
                'return_refund': {
                    'refund_rate': f"{real_metrics.refund_rate:.2%}",
                    'return_rate': f"{real_metrics.return_rate:.2%}",
                    'risk_level': 'High' if real_metrics.return_rate > 0.15 else 'Medium' if real_metrics.return_rate > 0.08 else 'Low',
                },
                'advertising': {
                    'acos': f"{real_metrics.acos:.2%}",
                    'roas': round(real_metrics.roas, 2),
                    'ad_spend_ratio': f"{real_metrics.ad_spend_ratio:.2%}",
                    'ad_order_ratio': f"{real_metrics.ad_order_ratio:.2%}",
                },
                'profitability': {
                    'gross_margin': f"{real_metrics.gross_margin:.2%}",
                    'net_margin': f"{real_metrics.net_margin:.2%}",
                    'profit_status': 'Profitable' if real_metrics.net_margin > 0 else 'Loss Making',
                }
            },
            'calibration_factors': calibrations,
            'optimized_results': optimized,
            'key_findings': self._generate_findings(real_metrics, calibrations, optimized),
            'action_recommendations': self._generate_recommendations(real_metrics, optimized),
        }
        
        return report
    
    def _calculate_data_quality(self, df: pd.DataFrame) -> float:
        """Calculate data quality score"""
        score = 1.0
        
        # Check data integrity
        missing_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
        score -= missing_ratio * 0.3
        
        # Check data days
        if len(df) < 7:
            score -= 0.3
        elif len(df) < 30:
            score -= 0.1
        
        # Check key fields
        critical_fields = ['sales', 'Sales volume', 'advertising spend', 'gross sales profit margin']
        for field in critical_fields:
            if field not in df.columns or df[field].isnull().all():
                score -= 0.1
        
        return max(0, min(1, score))
    
    def _generate_findings(self, 
                          real_metrics: RealSalesMetrics,
                          calibrations: Dict,
                          optimized: Dict) -> List[str]:
        """Generate key findings"""
        findings = []
        
        # Profitability discovery
        if real_metrics.net_margin < 0:
            findings.append(f"🔴Serious warning: The product is losing money! Net profit margin{real_metrics.net_margin:.1%}, the cost structure needs to be optimized immediately")
        elif real_metrics.net_margin < 0.05:
            findings.append(f"🟡 WARNING: net profit margin only{real_metrics.net_margin:.1%}, extremely thin profit margins")
        
        # Return rate discovery
        if real_metrics.return_rate > 0.15:
            findings.append(f"🔴High return rate warning: {real_metrics.return_rate:.1%}, far exceeding the industry average, quality or description needs improvement")
        
        # ACOSdiscovery
        if real_metrics.acos > 0.30:
            findings.append(f"🟡 High ACOS warning: {real_metrics.acos:.1%}, advertising efficiency is low and advertising strategies need to be optimized.")
        
        # Estimation bias discovery
        variance = optimized['variance_analysis']
        if variance['net_margin_variance'] < -10:
            findings.append(f"🔴 Keepa model overestimates net profit margin{abs(variance['net_margin_variance']):.1f}%, the actual profit is far lower than expected")
        
        # Advertising dependency discovery
        if real_metrics.ad_order_ratio > 0.6:
            findings.append(f"🟡 Too much reliance on advertising: {real_metrics.ad_order_ratio:.1%}The order comes from advertising, and there is insufficient natural traffic.")
        
        return findings
    
    def _generate_recommendations(self, 
                                 real_metrics: RealSalesMetrics,
                                 optimized: Dict) -> List[Dict]:
        """Generate optimization suggestions"""
        recommendations = []
        
        # Cost optimization suggestions
        if real_metrics.net_margin < 0.05:
            recommendations.append({
                'priority': 'Critical',
                'category': 'cost control',
                'action': 'Urgently reduce COGS, the current gross profit margin is too low',
                'expected_impact': f'The target gross profit margin is from{real_metrics.gross_margin:.1%}Increased to 25%',
            })
        
        # Return optimization suggestions
        if real_metrics.return_rate > 0.10:
            recommendations.append({
                'priority': 'High',
                'category': 'Quality control',
                'action': 'Reduce return rates and optimize product description and quality',
                'expected_impact': f'The target return rate is from{real_metrics.return_rate:.1%}down to 8%',
            })
        
        # Advertising optimization suggestions
        if real_metrics.acos > 0.25:
            recommendations.append({
                'priority': 'High',
                'category': 'Advertising optimization',
                'action': 'Optimize ad structure and keywords to reduce ACOS',
                'expected_impact': f'Target ACOS from{real_metrics.acos:.1%}down to 20%',
            })
        
        # Organic traffic recommendations
        if real_metrics.ad_order_ratio > 0.5:
            recommendations.append({
                'priority': 'Medium',
                'category': 'traffic structure',
                'action': 'Improve natural rankings and reduce reliance on advertising',
                'expected_impact': 'The proportion of natural orders increased to 60%',
            })
        
        return recommendations


# Easy to use functions
def optimize_with_real_sales(keepa_csv_path: str, 
                             real_sales_excel_path: str) -> Dict:
    """
    Convenience function: Optimize Keepa actuarial analysis with real sales data
    
    Args:
        keepa_csv_path: Keepa data CSV path
        real_sales_excel_path: Real Sales Excel Path
        
    Returns:
        Optimized full report
    """
    from src.actuarial_analyzer import AmazonActuary
    
    # 1. Perform standard actuarial analysis
    actuary = AmazonActuary()
    keepa_analysis = actuary.analyze_from_csv(keepa_csv_path, include_cosmo=False)
    
    # 2. Load real data and optimize
    optimizer = RealSalesActuarialOptimizer()
    real_df = optimizer.load_real_sales_data(real_sales_excel_path)
    real_metrics = optimizer.calculate_real_metrics(real_df)
    
    # 3. Calibrate the model
    calibrations = optimizer.calibrate_actuarial_model(real_metrics)
    
    # 4. Optimize profit calculation
    optimized = optimizer.optimize_profit_calculation(keepa_analysis, real_metrics)
    
    # 5. Generate reports
    report = optimizer.generate_optimization_report(real_metrics, calibrations, optimized)
    
    return report


def format_optimization_report(report: Dict) -> str:
    """
    Format optimization reports as readable text
    
    Args:
        report: Optimization report dictionary
        
    Returns:
        Format string
    """
    lines = []
    lines.append("=" * 90)
    lines.append("📊 Actuarial optimization report of real sales data")
    lines.append("=" * 90)
    
    # Data quality
    ds = report['data_source']
    lines.append(f"\n📈 Data quality: {ds['confidence_score']:.0%} | Analysis days: {ds['data_days']}day")
    
    # real indicator
    rm = report['real_metrics']
    lines.append(f"\n💰 Real operational performance:")
    lines.append(f"  total sales: ¥{rm['sales_performance']['total_sales_rmb']:,.2f}")
    lines.append(f"  total sales: {rm['sales_performance']['total_units']} pieces")
    lines.append(f"  average selling price: ¥{rm['sales_performance']['avg_price_rmb']:.2f}")
    lines.append(f"  average daily sales: {rm['sales_performance']['avg_daily_sales']:.1f} pieces")
    
    lines.append(f"\n Return and refund:")
    lines.append(f"    Refund rate: {rm['return_refund']['refund_rate']}")
    lines.append(f"    return rate: {rm['return_refund']['return_rate']} ({rm['return_refund']['risk_level']}risk)")
    
    lines.append(f"\n advertising performance:")
    lines.append(f"    ACOS: {rm['advertising']['acos']}")
    lines.append(f"    ROAS: {rm['advertising']['roas']}")
    lines.append(f"    Insertion order proportion: {rm['advertising']['ad_order_ratio']}")
    
    lines.append(f"\n profit margin (Key!):")
    lines.append(f"    Gross profit margin: {rm['profitability']['gross_margin']}")
    lines.append(f"    net profit margin: {rm['profitability']['net_margin']}")
    lines.append(f"    Status: {rm['profitability']['profit_status']}")
    
    # calibration factor
    lines.append(f"\n" + "─" * 90)
    lines.append("⚠️ Model calibration: Keepa estimates vs real data")
    lines.append("─" * 90)
    
    for param, values in report['calibration_factors'].items():
        if 'estimated' in values:
            lines.append(f"\n  {param}:")
            lines.append(f"    Estimate: {values['estimated']:.2%} | true value: {values['real']:.2%}")
            lines.append(f"    calibration factor: {values['calibration_factor']:.2f}x | influence: {values['impact']}")
    
    # Comparison of optimization results
    lines.append(f"\n" + "─" * 90)
    lines.append("📊 Profit forecast comparison")
    lines.append("─" * 90)
    
    orig = report['optimized_results']['original_keepa_estimate']
    real = report['optimized_results']['real_data_calibrated']
    var = report['optimized_results']['variance_analysis']
    
    lines.append(f"\n  {'indicator':<20} {'Keepa estimate':<15} {'true calibration':<15} {'difference':<15}")
    lines.append(f"  {'─' * 65}")
    lines.append(f"  {'net profit margin':<20} {orig['net_margin']:.1f}%{' '*10} {real['net_margin']:.1f}%{' '*10} {var['net_margin_variance']:+.1f}%")
    lines.append(f"  {'Annualized ROI':<20} {orig['roi_annual']:.0f}%{' '*10} {real['roi_annual']:.0f}%{' '*10} {var['roi_variance']:+.0f}%")
    lines.append(f"  {'monthly profit':<20} ${orig['monthly_profit']:.0f}{' '*10} ${real['monthly_profit']:.0f}{' '*10} ${var['profit_variance']:+.0f}")
    
    # Key findings
    lines.append(f"\n" + "─" * 90)
    lines.append("💡 Key findings")
    lines.append("─" * 90)
    for finding in report['key_findings']:
        lines.append(f"  {finding}")
    
    # suggestion
    lines.append(f"\n" + "─" * 90)
    lines.append("🎯 Optimization suggestions")
    lines.append("─" * 90)
    for rec in report['action_recommendations']:
        priority_emoji = "🔴" if rec['priority'] == 'Critical' else "🟡" if rec['priority'] == 'High' else "🟢"
        lines.append(f"\n  {priority_emoji} [{rec['category']}] {rec['action']}")
        lines.append(f"     expected impact: {rec['expected_impact']}")
    
    lines.append("\n" + "=" * 90)
    
    return "\n".join(lines)
