"""
真实销售数据精算优化器 (Real Sales Actuarial Optimizer)

基于真实亚马逊运营数据优化精算模型，解决Keepa估算与真实数据的偏差问题。

核心功能:
1. 真实数据校准 - 用实际运营数据修正估算参数
2. 多数据源融合 - 整合Keepa数据 + 真实销售数据
3. 动态参数调整 - 基于历史数据趋势优化预测
4. 真实盈利模型 - 考虑所有真实成本项

优化维度:
- COGS率: 从估算30% → 真实87% (关键修正!)
- ACOS: 从估算15% → 真实26%
- 退货率: 从估算5% → 真实18%
- 促销成本: 新增Coupon/Deal花费
- 自然vs广告订单: 区分流量来源利润
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RealSalesMetrics:
    """真实销售指标数据类"""
    # 销售基础
    total_sales: float
    total_units: int
    avg_price: float
    avg_daily_sales: float
    
    # 退货退款 (关键!)
    refund_rate: float
    return_rate: float
    
    # 广告表现
    acos: float
    roas: float
    ad_spend_ratio: float
    ad_order_ratio: float
    
    # 真实利润 (最重要!)
    gross_margin: float
    net_margin: float
    
    # 促销成本
    coupon_cost_ratio: float
    deal_cost_ratio: float
    
    # 数据质量
    data_days: int
    confidence_score: float


class RealSalesActuarialOptimizer:
    """
    真实销售数据精算优化器
    
    多Agents协同架构:
    - DataLoader Agent: 加载真实销售Excel
    - Calibrator Agent: 计算校准参数
    - Fusion Agent: 融合Keepa+真实数据
    - Optimizer Agent: 生成优化建议
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
        Agent 1: DataLoader - 加载真实销售数据
        
        Args:
            excel_path: 销售数据Excel文件路径
            
        Returns:
            清洗后的DataFrame
        """
        df = pd.read_excel(excel_path)
        
        # 数据清洗
        # 移除汇总行
        df = df[df['日期'] != '汇总'].copy()
        
        # 转换数值列
        numeric_cols = ['销量', '销售额', '退款量', '退货量', '广告花费', 
                       '广告销售额', '销售毛利', '销售毛利率', '销售净毛利率',
                       'ACOS', 'ROAS', 'Coupon花费', 'Deal花费']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def calculate_real_metrics(self, df: pd.DataFrame) -> RealSalesMetrics:
        """
        Agent 2: Calibrator - 计算真实运营指标
        
        Args:
            df: 清洗后的销售数据
            
        Returns:
            RealSalesMetrics真实指标对象
        """
        # 基础销售数据
        total_sales = df['销售额'].sum()
        total_units = df['销量'].sum()
        avg_price = df['平均销售价格'].mean()
        data_days = len(df)
        avg_daily_sales = total_units / data_days if data_days > 0 else 0
        
        # 退货退款率 (关键!)
        refund_rate = df['退款量'].sum() / total_units if total_units > 0 else 0
        return_rate = df['退货量'].sum() / total_units if total_units > 0 else 0
        
        # 广告指标
        total_ad_spend = abs(df['广告花费'].sum())  # 花费是负数
        total_ad_sales = df['广告销售额'].sum()
        acos = total_ad_spend / total_ad_sales if total_ad_sales > 0 else 0
        roas = total_ad_sales / total_ad_spend if total_ad_spend > 0 else 0
        ad_spend_ratio = total_ad_spend / total_sales if total_sales > 0 else 0
        
        total_ad_orders = df['广告订单量'].sum()
        total_orders = df['订单量'].sum()
        ad_order_ratio = total_ad_orders / total_orders if total_orders > 0 else 0
        
        # 真实利润率 (最重要!)
        avg_gross_margin = df['销售毛利率'].mean()
        avg_net_margin = df['销售净毛利率'].mean()
        
        # 促销成本
        total_coupon = df['Coupon花费'].sum()
        total_deal = df['Deal花费'].sum()
        coupon_cost_ratio = total_coupon / total_sales if total_sales > 0 else 0
        deal_cost_ratio = total_deal / total_sales if total_sales > 0 else 0
        
        # 数据质量评分
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
        Agent 3: Calibrator - 生成校准参数
        
        对比Keepa估算 vs 真实数据，生成校准因子
        
        Args:
            real_metrics: 真实运营指标
            
        Returns:
            校准参数字典
        """
        calibrations = {}
        
        # 1. COGS率校准 (最关键!)
        estimated_cogs = self.baseline_params['estimated_cogs_rate']
        real_cogs = 1 - real_metrics.gross_margin  # 从毛利率反推COGS
        calibrations['cogs_rate'] = {
            'estimated': estimated_cogs,
            'real': real_cogs,
            'calibration_factor': real_cogs / estimated_cogs if estimated_cogs > 0 else 1,
            'impact': 'Critical' if abs(real_cogs - estimated_cogs) > 0.2 else 'Medium'
        }
        
        # 2. ACOS校准
        estimated_acos = self.baseline_params['estimated_acos']
        real_acos = real_metrics.acos
        calibrations['acos'] = {
            'estimated': estimated_acos,
            'real': real_acos,
            'calibration_factor': real_acos / estimated_acos if estimated_acos > 0 else 1,
            'impact': 'High' if real_acos > estimated_acos * 1.5 else 'Medium'
        }
        
        # 3. 退货率校准
        estimated_return = self.baseline_params['estimated_return_rate']
        real_return = real_metrics.return_rate
        calibrations['return_rate'] = {
            'estimated': estimated_return,
            'real': real_return,
            'calibration_factor': real_return / estimated_return if estimated_return > 0 else 1,
            'impact': 'High' if real_return > estimated_return * 2 else 'Medium'
        }
        
        # 4. 退款率校准
        estimated_refund = self.baseline_params['estimated_refund_rate']
        real_refund = real_metrics.refund_rate
        calibrations['refund_rate'] = {
            'estimated': estimated_refund,
            'real': real_refund,
            'calibration_factor': real_refund / estimated_refund if estimated_refund > 0 else 1,
            'impact': 'Medium'
        }
        
        # 5. 广告订单占比
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
        Agent 4: Optimizer - 生成优化的盈利计算
        
        融合Keepa数据 + 真实数据，生成更准确的盈利预测
        
        Args:
            keepa_analysis: 基于Keepa的精算分析结果
            real_metrics: 真实运营指标
            
        Returns:
            优化后的分析结果
        """
        # 获取当前价格
        current_price = keepa_analysis['profitability_analysis']['price_analysis']['current_price']
        
        # 使用真实参数重新计算成本
        # 注意: 真实数据是人民币，需要转换为美元(假设汇率7.2)
        exchange_rate = 7.2
        price_rmb = current_price * exchange_rate
        
        # 真实COGS (基于真实毛利率)
        real_cogs_rate = 1 - real_metrics.gross_margin
        cogs_per_unit = price_rmb * real_cogs_rate
        
        # 真实FBA费用 (估算)
        fba_fee_rmb = 60  # 约$8.5
        
        # 真实佣金 (15%)
        referral_fee = price_rmb * 0.15
        
        # 真实退货成本
        return_cost = price_rmb * real_metrics.return_rate * 0.3  # 30%净损失
        
        # 真实仓储费
        storage_cost = 1.0  # 约$0.15
        
        # 真实广告费 (基于真实ACOS)
        ad_cost = price_rmb * real_metrics.acos
        
        # 促销成本
        coupon_cost = price_rmb * real_metrics.coupon_cost_ratio
        deal_cost = price_rmb * real_metrics.deal_cost_ratio
        
        # 总成本
        total_cost = (cogs_per_unit + fba_fee_rmb + referral_fee + 
                     return_cost + storage_cost + ad_cost + coupon_cost + deal_cost)
        
        # 利润计算
        gross_profit = price_rmb - cogs_per_unit - fba_fee_rmb - referral_fee
        net_profit = price_rmb - total_cost
        
        gross_margin = (gross_profit / price_rmb * 100) if price_rmb > 0 else 0
        net_margin = (net_profit / price_rmb * 100) if price_rmb > 0 else 0
        
        # 转换为美元
        net_profit_usd = net_profit / exchange_rate
        
        # 月均销量预测 (基于真实数据)
        monthly_units = real_metrics.avg_daily_sales * 30
        monthly_profit = net_profit_usd * monthly_units
        
        # ROI计算
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
        生成完整的优化报告
        
        Returns:
            优化报告字典
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
        """计算数据质量评分"""
        score = 1.0
        
        # 检查数据完整性
        missing_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
        score -= missing_ratio * 0.3
        
        # 检查数据天数
        if len(df) < 7:
            score -= 0.3
        elif len(df) < 30:
            score -= 0.1
        
        # 检查关键字段
        critical_fields = ['销售额', '销量', '广告花费', '销售毛利率']
        for field in critical_fields:
            if field not in df.columns or df[field].isnull().all():
                score -= 0.1
        
        return max(0, min(1, score))
    
    def _generate_findings(self, 
                          real_metrics: RealSalesMetrics,
                          calibrations: Dict,
                          optimized: Dict) -> List[str]:
        """生成关键发现"""
        findings = []
        
        # 盈利能力发现
        if real_metrics.net_margin < 0:
            findings.append(f"🔴 严重警告: 产品正在亏损! 净利率{real_metrics.net_margin:.1%}，需立即优化成本结构")
        elif real_metrics.net_margin < 0.05:
            findings.append(f"🟡 警告: 净利率仅{real_metrics.net_margin:.1%}，利润空间极薄")
        
        # 退货率发现
        if real_metrics.return_rate > 0.15:
            findings.append(f"🔴 高退货率警告: {real_metrics.return_rate:.1%}，远超行业平均，质量或描述需改进")
        
        # ACOS发现
        if real_metrics.acos > 0.30:
            findings.append(f"🟡 高ACOS警告: {real_metrics.acos:.1%}，广告效率低下，需优化广告策略")
        
        # 估算偏差发现
        variance = optimized['variance_analysis']
        if variance['net_margin_variance'] < -10:
            findings.append(f"🔴 Keepa模型高估净利率{abs(variance['net_margin_variance']):.1f}%，真实盈利远低于预期")
        
        # 广告依赖发现
        if real_metrics.ad_order_ratio > 0.6:
            findings.append(f"🟡 广告依赖度过高: {real_metrics.ad_order_ratio:.1%}订单来自广告，自然流量不足")
        
        return findings
    
    def _generate_recommendations(self, 
                                 real_metrics: RealSalesMetrics,
                                 optimized: Dict) -> List[Dict]:
        """生成优化建议"""
        recommendations = []
        
        # 成本优化建议
        if real_metrics.net_margin < 0.05:
            recommendations.append({
                'priority': 'Critical',
                'category': '成本控制',
                'action': '紧急降低COGS，当前毛利率过低',
                'expected_impact': f'目标毛利率从{real_metrics.gross_margin:.1%}提升至25%',
            })
        
        # 退货优化建议
        if real_metrics.return_rate > 0.10:
            recommendations.append({
                'priority': 'High',
                'category': '质量控制',
                'action': '降低退货率，优化产品描述和质量',
                'expected_impact': f'目标退货率从{real_metrics.return_rate:.1%}降至8%',
            })
        
        # 广告优化建议
        if real_metrics.acos > 0.25:
            recommendations.append({
                'priority': 'High',
                'category': '广告优化',
                'action': '优化广告结构和关键词，降低ACOS',
                'expected_impact': f'目标ACOS从{real_metrics.acos:.1%}降至20%',
            })
        
        # 自然流量建议
        if real_metrics.ad_order_ratio > 0.5:
            recommendations.append({
                'priority': 'Medium',
                'category': '流量结构',
                'action': '提升自然排名，降低对广告依赖',
                'expected_impact': '自然订单占比提升至60%',
            })
        
        return recommendations


# 便捷使用函数
def optimize_with_real_sales(keepa_csv_path: str, 
                             real_sales_excel_path: str) -> Dict:
    """
    便捷函数: 用真实销售数据优化Keepa精算分析
    
    Args:
        keepa_csv_path: Keepa数据CSV路径
        real_sales_excel_path: 真实销售Excel路径
        
    Returns:
        优化后的完整报告
    """
    from src.actuarial_analyzer import AmazonActuary
    
    # 1. 执行标准精算分析
    actuary = AmazonActuary()
    keepa_analysis = actuary.analyze_from_csv(keepa_csv_path, include_cosmo=False)
    
    # 2. 加载真实数据并优化
    optimizer = RealSalesActuarialOptimizer()
    real_df = optimizer.load_real_sales_data(real_sales_excel_path)
    real_metrics = optimizer.calculate_real_metrics(real_df)
    
    # 3. 校准模型
    calibrations = optimizer.calibrate_actuarial_model(real_metrics)
    
    # 4. 优化盈利计算
    optimized = optimizer.optimize_profit_calculation(keepa_analysis, real_metrics)
    
    # 5. 生成报告
    report = optimizer.generate_optimization_report(real_metrics, calibrations, optimized)
    
    return report


def format_optimization_report(report: Dict) -> str:
    """
    格式化优化报告为可读文本
    
    Args:
        report: 优化报告字典
        
    Returns:
        格式化字符串
    """
    lines = []
    lines.append("=" * 90)
    lines.append("📊 真实销售数据精算优化报告")
    lines.append("=" * 90)
    
    # 数据质量
    ds = report['data_source']
    lines.append(f"\n📈 数据质量: {ds['confidence_score']:.0%} | 分析天数: {ds['data_days']}天")
    
    # 真实指标
    rm = report['real_metrics']
    lines.append(f"\n💰 真实运营表现:")
    lines.append(f"  总销售额: ¥{rm['sales_performance']['total_sales_rmb']:,.2f}")
    lines.append(f"  总销量: {rm['sales_performance']['total_units']} 件")
    lines.append(f"  平均售价: ¥{rm['sales_performance']['avg_price_rmb']:.2f}")
    lines.append(f"  日均销量: {rm['sales_performance']['avg_daily_sales']:.1f} 件")
    
    lines.append(f"\n  退货退款:")
    lines.append(f"    退款率: {rm['return_refund']['refund_rate']}")
    lines.append(f"    退货率: {rm['return_refund']['return_rate']} ({rm['return_refund']['risk_level']}风险)")
    
    lines.append(f"\n  广告表现:")
    lines.append(f"    ACOS: {rm['advertising']['acos']}")
    lines.append(f"    ROAS: {rm['advertising']['roas']}")
    lines.append(f"    广告订单占比: {rm['advertising']['ad_order_ratio']}")
    
    lines.append(f"\n  利润率 (关键!):")
    lines.append(f"    毛利率: {rm['profitability']['gross_margin']}")
    lines.append(f"    净利率: {rm['profitability']['net_margin']}")
    lines.append(f"    状态: {rm['profitability']['profit_status']}")
    
    # 校准因子
    lines.append(f"\n" + "─" * 90)
    lines.append("⚠️ 模型校准: Keepa估算 vs 真实数据")
    lines.append("─" * 90)
    
    for param, values in report['calibration_factors'].items():
        if 'estimated' in values:
            lines.append(f"\n  {param}:")
            lines.append(f"    估算值: {values['estimated']:.2%} | 真实值: {values['real']:.2%}")
            lines.append(f"    校准因子: {values['calibration_factor']:.2f}x | 影响: {values['impact']}")
    
    # 优化结果对比
    lines.append(f"\n" + "─" * 90)
    lines.append("📊 盈利预测对比")
    lines.append("─" * 90)
    
    orig = report['optimized_results']['original_keepa_estimate']
    real = report['optimized_results']['real_data_calibrated']
    var = report['optimized_results']['variance_analysis']
    
    lines.append(f"\n  {'指标':<20} {'Keepa估算':<15} {'真实校准':<15} {'差异':<15}")
    lines.append(f"  {'─' * 65}")
    lines.append(f"  {'净利率':<20} {orig['net_margin']:.1f}%{' '*10} {real['net_margin']:.1f}%{' '*10} {var['net_margin_variance']:+.1f}%")
    lines.append(f"  {'年化ROI':<20} {orig['roi_annual']:.0f}%{' '*10} {real['roi_annual']:.0f}%{' '*10} {var['roi_variance']:+.0f}%")
    lines.append(f"  {'月利润':<20} ${orig['monthly_profit']:.0f}{' '*10} ${real['monthly_profit']:.0f}{' '*10} ${var['profit_variance']:+.0f}")
    
    # 关键发现
    lines.append(f"\n" + "─" * 90)
    lines.append("💡 关键发现")
    lines.append("─" * 90)
    for finding in report['key_findings']:
        lines.append(f"  {finding}")
    
    # 建议
    lines.append(f"\n" + "─" * 90)
    lines.append("🎯 优化建议")
    lines.append("─" * 90)
    for rec in report['action_recommendations']:
        priority_emoji = "🔴" if rec['priority'] == 'Critical' else "🟡" if rec['priority'] == 'High' else "🟢"
        lines.append(f"\n  {priority_emoji} [{rec['category']}] {rec['action']}")
        lines.append(f"     预期影响: {rec['expected_impact']}")
    
    lines.append("\n" + "=" * 90)
    
    return "\n".join(lines)
