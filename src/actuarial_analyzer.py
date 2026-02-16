"""
亚马逊运营分析精算师模块
基于Keepa全面指标进行精算级风险评估和盈利预测

集成COSMO意图分析 - 多Agents协同架构
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json

# 导入COSMO意图分析器
from src.cosmo_intent_analyzer import (
    COSMOIntentAnalyzer, 
    COSMOReportIntegrator,
    COSMOIntentProfile
)


@dataclass
class ActuarialMetrics:
    """精算指标数据类"""
    # 盈利能力
    gross_margin: float
    net_margin: float
    break_even_units: int
    roi_annual: float
    
    # 风险指标
    volatility_score: float
    risk_adjusted_return: float
    confidence_interval_95: Tuple[float, float]
    
    # 需求预测
    demand_forecast_30d: int
    demand_forecast_90d: int
    seasonality_factor: float
    
    # 竞争风险
    market_share_risk: float
    amazon_1p_threat: float
    price_war_probability: float


class AmazonActuary:
    """
    亚马逊运营精算师
    
    核心功能：
    1. 精算级盈利模型（考虑退货、仓储、现金流）
    2. 蒙特卡洛风险模拟
    3. 需求预测与库存优化
    4. 竞争动态建模
    5. 风险调整收益计算
    """
    
    # 类目基准退货率
    CATEGORY_RETURN_RATES = {
        'Clothing, Shoes & Jewelry': 0.12,
        'Home & Kitchen': 0.06,
        'Electronics': 0.08,
        'Beauty & Personal Care': 0.05,
        'Sports & Outdoors': 0.07,
        'Toys & Games': 0.05,
        'Baby Products': 0.10,
        'Pet Supplies': 0.04,
        'Office Products': 0.04,
        'Grocery & Gourmet Food': 0.03,
    }
    
    # 类目季节性系数
    CATEGORY_SEASONALITY = {
        'Toys & Games': {'Q4': 2.5, 'Q1': 0.6},
        'Clothing, Shoes & Jewelry': {'Q4': 1.8, 'Q1': 0.7},
        'Sports & Outdoors': {'Q2': 1.5, 'Q4': 0.8},
        'Home & Kitchen': {'Q4': 1.4, 'Q1': 0.9},
    }
    
    def __init__(self):
        self.simulation_results = []
    
    def analyze_from_csv(self, csv_path: str, include_cosmo: bool = True) -> Dict:
        """
        从Keepa CSV文件进行全面精算分析
        
        多Agents协同架构:
        1. DataExtractor: 提取163指标
        2. ActuarialAnalyzer: 精算模型分析
        3. COSMOIntentAnalyzer: 五点意图挖掘
        4. ReportIntegrator: 整合输出
        
        Args:
            csv_path: Keepa Product Viewer导出的CSV文件路径
            include_cosmo: 是否包含COSMO意图分析
            
        Returns:
            精算分析报告 (含COSMO意图分析)
        """
        df = pd.read_csv(csv_path)
        if len(df) == 0:
            raise ValueError("CSV文件为空")
        
        # 取第一行产品数据
        product_data = df.iloc[0].to_dict()
        
        # 执行全面分析
        analysis = {
            'product_identity': self._extract_identity(product_data),
            'profitability_analysis': self._calculate_profitability(product_data),
            'risk_assessment': self._assess_risks(product_data),
            'demand_forecast': self._forecast_demand(product_data),
            'competition_modeling': self._model_competition(product_data),
            'monte_carlo_simulation': self._run_monte_carlo(product_data),
            'strategic_recommendations': self._generate_recommendations(product_data),
        }
        
        # Agent 3: COSMO意图分析 (可选)
        if include_cosmo:
            try:
                cosmo_analyzer = COSMOIntentAnalyzer()
                cosmo_profile = cosmo_analyzer.analyze(product_data)
                
                integrator = COSMOReportIntegrator()
                analysis = integrator.integrate_to_actuarial_report(cosmo_profile, analysis)
            except Exception as e:
                # COSMO分析失败不影响主报告
                analysis['cosmo_intent_analysis'] = {
                    'error': f'COSMO分析失败: {str(e)}',
                    'intent_score': 0
                }
        
        return analysis
    
    def _extract_identity(self, data: Dict) -> Dict:
        """提取产品身份信息"""
        return {
            'asin': data.get('ASIN', 'N/A'),
            'title': data.get('Title', 'N/A')[:100],
            'brand': data.get('Brand', 'N/A'),
            'category': data.get('Categories: Root', 'N/A'),
            'subcategory': data.get('Categories: Sub', 'N/A'),
            'tracking_since': data.get('Tracking since', 'N/A'),
            'listed_since': data.get('Listed since', 'N/A'),
            'lifecycle_stage': self._determine_lifecycle(data),
        }
    
    def _determine_lifecycle(self, data: Dict) -> str:
        """确定产品生命周期阶段"""
        tracking_days = 0
        try:
            if 'Tracking since' in data:
                tracking_date = pd.to_datetime(data['Tracking since'])
                tracking_days = (datetime.now() - tracking_date).days
        except:
            pass
        
        review_count = self._safe_float(data.get('Reviews: Rating Count', 0))
        
        if tracking_days < 90 and review_count < 50:
            return 'Introduction (导入期)'
        elif review_count < 500 and tracking_days < 365:
            return 'Growth (成长期)'
        elif review_count > 1000:
            return 'Maturity (成熟期)'
        else:
            return 'Unknown (未知)'
    
    def _get_effective_price(self, data: Dict) -> float:
        """
        获取有效价格，支持多种回退策略
        """
        # 尝试多种价格字段
        price_fields = [
            'Buy Box: Current',
            'Buy Box: Current Price', 
            'New: Current',
            'New: Current Price',
            'Amazon: Current',
            'Buy Box: 90 days avg.',
            'New: 90 days avg.',
        ]
        
        for field in price_fields:
            price = self._safe_float(data.get(field, 0))
            if price > 0:
                return price
        
        # 最后的备选：从标题估算
        title = str(data.get('Title', '')).lower()
        if 'passport' in title or '钱包' in title or 'wallet' in title:
            return 20.0
        return 25.0
    
    def _estimate_fba_fee(self, data: Dict, price: float) -> float:
        """基于产品属性估算FBA费用"""
        # 获取尺寸信息
        length = self._safe_float(data.get('Package: Length (cm)'), 15)
        width = self._safe_float(data.get('Package: Width (cm)'), 10)
        height = self._safe_float(data.get('Package: Height (cm)'), 3)
        weight = self._safe_float(data.get('Package: Weight (g)'), 200)
        
        # 体积重
        dimensional_weight = (length * width * height) / 5000 * 1000  # cm³ to g equiv
        billable_weight = max(weight, dimensional_weight)
        
        # FBA费用估算 (简化的tier系统)
        if billable_weight <= 100:
            return 3.22  # Small Standard
        elif billable_weight <= 500:
            return 4.50  # Large Standard (small)
        elif billable_weight <= 1000:
            return 6.10  # Large Standard (large)
        else:
            return 9.00  # Oversize
    
    def _estimate_cogs(self, data: Dict, price: float) -> float:
        """基于类目智能估算COGS"""
        # 基于产品类型的成本率
        category = str(data.get('Categories: Root', '')).lower()
        title = str(data.get('Title', '')).lower()
        
        cost_rates = {
            'electronics': 0.50,
            'clothing': 0.35,
            'home': 0.30,
            'toys': 0.25,
            'sports': 0.35,
            'beauty': 0.20,
            'health': 0.25,
            'office': 0.30,
        }
        
        # 匹配类目
        base_rate = 0.35  # 默认35%
        for cat, rate in cost_rates.items():
            if cat in category or cat in title:
                base_rate = rate
                break
        
        # 皮革/真皮产品成本更高
        if 'leather' in title or 'genuine' in title or '真皮' in title:
            base_rate = 0.45
        
        return price * base_rate
    
    def _estimate_storage_cost_v2(self, data: Dict) -> float:
        """
        单件仓储成本估算
        
        计算单件产品每月的仓储费分摊
        注意：Keepa有时返回mm单位，需要转换为cm
        """
        # 获取尺寸 - 优先使用Item尺寸(通常是产品本身尺寸)
        # 处理可能的单位问题：如果数值>50，可能是mm，需要/10
        def get_dimension(field, default):
            val = self._safe_float(data.get(field), default)
            # 数据验证：护照夹类不可能超过30cm
            if val > 50:
                val = val / 10  # 转换为cm (从mm)
            return val
        
        # 优先使用Item尺寸(产品本身)，而非Package尺寸(外包装)
        length = get_dimension('Item: Length (cm)', 15)
        width = get_dimension('Item: Width (cm)', 10)
        height = get_dimension('Item: Height (cm)', 2)
        
        # 合理性检查：如果还是太大，使用默认值
        if length * width * height > 5000:  # > 5000 cm³ 对护照夹不合理
            length, width, height = 15, 10, 2  # 标准护照夹尺寸
        
        # 计算体积 (立方英尺)
        volume_cbf = (length * width * height) / 28316.8  # cm³ to cubic feet
        
        # 月度仓储费率 (标准尺寸: $0.87/cbf，大件: $0.56/cbf)
        is_oversize = (length > 45.7) or (width > 35.5) or (height > 20.3)  # 亚马逊大件标准
        storage_rate_per_cbf = 0.56 if is_oversize else 0.87
        
        # 单件月度仓储费 = 体积 × 费率
        storage_per_unit = volume_cbf * storage_rate_per_cbf
        
        # 长期仓储费估算 (平均库龄90天，额外$6.90/cbf或$0.15/单位)
        aged_inventory_surcharge = 0.15  # 每单位长期仓储费
        
        # 单件总仓储成本
        total_storage_per_unit = storage_per_unit + aged_inventory_surcharge
        
        return max(total_storage_per_unit, 0.02)  # 最低$0.02
    
    def _estimate_monthly_fixed_costs(self, data: Dict) -> float:
        """估算月度固定成本"""
        monthly_sales = self._safe_float(data.get('Bought in past month', 100))
        
        # 基础固定成本 + 销量相关成本
        base_fixed = 500  # 基础运营费用
        scaling_cost = monthly_sales * 0.5  # 每单位$0.5的浮动管理成本
        
        return base_fixed + scaling_cost
    
    def _calculate_profitability(self, data: Dict) -> Dict:
        """
        精算级盈利分析 V2
        
        增强功能：
        - 智能价格获取（多字段回退）
        - 自适应成本估算（基于类目）
        - 智能FBA费用估算
        """
        # 基础价格数据（使用智能获取）
        current_price = self._get_effective_price(data)
        
        # 判断是否为FBA
        is_fba = str(data.get('Buy Box: Is FBA', '')).lower() in ['yes', 'true', '1']
        
        # 成本结构
        fba_fee = self._safe_float(data.get('FBA Pick&Pack Fee', 0))
        
        # 如果没有FBA费用，进行估算
        if fba_fee == 0:
            fba_fee = self._estimate_fba_fee(data, current_price)
        
        referral_rate = self._safe_float(data.get('Referral Fee %', 15)) / 100
        referral_fee = current_price * referral_rate
        
        # 智能COGS估算
        estimated_cogs = self._estimate_cogs(data, current_price)
        
        # 退货成本计算（更精确）
        return_rate = self._estimate_return_rate(data)
        return_cost_per_unit = current_price * return_rate * 0.3  # 30%净损失
        
        # 仓储成本估算
        storage_cost = self._estimate_storage_cost_v2(data)
        
        # 广告成本估算（ACoS 15%）
        ad_cost = current_price * 0.15
        
        # 总成本
        total_cost = estimated_cogs + fba_fee + referral_fee + return_cost_per_unit + storage_cost + ad_cost
        
        # 利润计算
        gross_profit = current_price - estimated_cogs - fba_fee - referral_fee
        operating_profit = gross_profit - return_cost_per_unit - storage_cost - ad_cost
        
        gross_margin = (gross_profit / current_price * 100) if current_price > 0 else 0
        net_margin = (operating_profit / current_price * 100) if current_price > 0 else 0
        
        # 盈亏平衡分析
        monthly_fixed = self._estimate_monthly_fixed_costs(data)
        break_even_units = int(monthly_fixed / operating_profit) if operating_profit > 0 else float('inf')
        
        # ROI计算
        monthly_sales = self._safe_float(data.get('Bought in past month', 100))
        annual_profit = operating_profit * monthly_sales * 12
        avg_inventory_value = estimated_cogs * monthly_sales * 1.5
        roi_annual = (annual_profit / avg_inventory_value * 100) if avg_inventory_value > 0 else 0
        
        return {
            'price_analysis': {
                'current_price': current_price,
                'avg_90d_price': self._safe_float(data.get('Buy Box: 90 days avg.', 0)),
                'price_stability': data.get('Buy Box: Standard Deviation 90 days', 'N/A'),
                'flipability': data.get('Buy Box: Flipability 90 days', 'N/A'),
            },
            'cost_structure': {
                'estimated_cogs': round(estimated_cogs, 2),
                'cogs_percentage': round(estimated_cogs / current_price * 100, 1) if current_price > 0 else 0,
                'fba_fee': round(fba_fee, 2),
                'referral_fee': round(referral_fee, 2),
                'return_cost': round(return_cost_per_unit, 2),
                'storage_cost': round(storage_cost, 2),
                'ad_cost': round(ad_cost, 2),
                'total_cost': round(total_cost, 2),
                'cost_to_price_ratio': round(total_cost / current_price * 100, 1) if current_price > 0 else 0,
            },
            'profitability': {
                'gross_profit': round(gross_profit, 2),
                'operating_profit': round(operating_profit, 2),
                'gross_margin': round(gross_margin, 1),
                'net_margin': round(net_margin, 1),
                'break_even_units': break_even_units if break_even_units != float('inf') else 'N/A',
                'roi_annual': round(roi_annual, 1),
                'monthly_profit_estimate': round(operating_profit * monthly_sales, 2),
            },
            'grade': self._grade_profitability(net_margin),
        }
    
    def _assess_risks(self, data: Dict) -> Dict:
        """
        精算级风险评估
        
        评估维度：
        1. 价格波动风险
        2. 断货风险
        3. 竞争风险
        4. 需求下滑风险
        5. 政策/合规风险
        """
        risks = []
        risk_scores = {}
        
        # 1. 价格波动风险
        price_std = self._safe_float(data.get('Buy Box: Standard Deviation 90 days', 0))
        current_price = self._safe_float(data.get('Buy Box: Current', 1))
        price_cv = (price_std / current_price) if current_price > 0 else 0
        
        if price_cv > 0.15:
            risks.append({
                'type': '价格波动',
                'level': 'high',
                'score': 8,
                'desc': f'价格波动系数 {price_cv:.1%}，超过15%阈值'
            })
            risk_scores['price_volatility'] = 8
        elif price_cv > 0.08:
            risks.append({
                'type': '价格波动',
                'level': 'medium',
                'score': 5,
                'desc': f'价格波动系数 {price_cv:.1%}，需监控'
            })
            risk_scores['price_volatility'] = 5
        else:
            risk_scores['price_volatility'] = 2
        
        # 2. 断货风险
        oos_90d = self._safe_float(data.get('Amazon: 90 days OOS', 0))
        if oos_90d > 20:
            risks.append({
                'type': '断货风险',
                'level': 'high',
                'score': 7,
                'desc': f'90天断货率 {oos_90d:.1f}%，供应不稳定'
            })
            risk_scores['stockout'] = 7
        elif oos_90d > 5:
            risks.append({
                'type': '断货风险',
                'level': 'medium',
                'score': 4,
                'desc': f'90天断货率 {oos_90d:.1f}%'
            })
            risk_scores['stockout'] = 4
        else:
            risk_scores['stockout'] = 1
        
        # 3. Amazon 1P 竞争风险
        amazon_pct = self._safe_float(data.get('Buy Box: % Amazon 90 days', '0%').replace('%', ''))
        if amazon_pct > 30:
            risks.append({
                'type': 'Amazon自营',
                'level': 'high',
                'score': 9,
                'desc': f'Amazon自营占比 {amazon_pct:.1f}%，Buy Box竞争激烈'
            })
            risk_scores['amazon_1p'] = 9
        elif amazon_pct > 10:
            risks.append({
                'type': 'Amazon自营',
                'level': 'medium',
                'score': 6,
                'desc': f'Amazon自营占比 {amazon_pct:.1f}%'
            })
            risk_scores['amazon_1p'] = 6
        else:
            risk_scores['amazon_1p'] = 2
        
        # 4. 需求下滑风险
        rank_drops = self._safe_float(data.get('Sales Rank: Drops last 90 days', 0))
        if rank_drops > 40:
            risks.append({
                'type': '需求下滑',
                'level': 'high',
                'score': 8,
                'desc': f'90天排名下降 {rank_drops} 次，需求可能萎缩'
            })
            risk_scores['demand_decline'] = 8
        elif rank_drops > 20:
            risks.append({
                'type': '需求下滑',
                'level': 'medium',
                'score': 5,
                'desc': f'90天排名下降 {rank_drops} 次'
            })
            risk_scores['demand_decline'] = 5
        else:
            risk_scores['demand_decline'] = 2
        
        # 5. 退货风险
        return_rate = self._estimate_return_rate(data)
        if return_rate > 0.10:
            risks.append({
                'type': '高退货率',
                'level': 'high',
                'score': 7,
                'desc': f'预估退货率 {return_rate:.1%}，影响净利润'
            })
            risk_scores['returns'] = 7
        elif return_rate > 0.06:
            risks.append({
                'type': '退货风险',
                'level': 'medium',
                'score': 4,
                'desc': f'预估退货率 {return_rate:.1%}'
            })
            risk_scores['returns'] = 4
        else:
            risk_scores['returns'] = 2
        
        # 计算综合风险评分 (0-100)
        total_risk_score = sum(risk_scores.values()) / len(risk_scores) * 10
        
        return {
            'risk_items': risks,
            'risk_scores': risk_scores,
            'total_risk_score': round(total_risk_score, 1),
            'risk_grade': self._grade_risk(total_risk_score),
            'var_95': self._calculate_var(data),  # 风险价值
        }
    
    def _forecast_demand(self, data: Dict) -> Dict:
        """
        需求预测模型
        
        基于：
        - 历史销量趋势
        - 季节性因子
        - 排名变化趋势
        """
        current_sales = self._safe_float(data.get('Bought in past month', 0))
        sales_change_pct = self._safe_float(data.get('90 days change % monthly sold', '0%').replace('%', ''))
        
        # 获取季节性因子
        category = data.get('Categories: Root', '')
        seasonality = self.CATEGORY_SEASONALITY.get(category, {})
        current_quarter = f"Q{(datetime.now().month - 1) // 3 + 1}"
        season_factor = seasonality.get(current_quarter, 1.0)
        
        # 趋势预测
        trend_factor = 1 + (sales_change_pct / 100)
        
        # 30天预测
        forecast_30d = int(current_sales * trend_factor * season_factor)
        
        # 90天预测 (考虑趋势衰减)
        forecast_90d = int(forecast_30d * 3 * (1 + (sales_change_pct / 200)))
        
        # 置信区间
        confidence_lower = int(forecast_30d * 0.8)
        confidence_upper = int(forecast_30d * 1.2)
        
        return {
            'current_monthly_sales': int(current_sales),
            'sales_growth_rate': f"{sales_change_pct:.1f}%",
            'seasonality_factor': season_factor,
            'forecast': {
                '30_days': forecast_30d,
                '90_days': forecast_90d,
                'confidence_interval_80': (confidence_lower, confidence_upper),
            },
            'inventory_recommendation': {
                'suggested_inventory': int(forecast_30d * 1.5),  # 1.5个月库存
                'reorder_point': int(forecast_30d * 0.5),  # 0.5个月库存
            }
        }
    
    def _model_competition(self, data: Dict) -> Dict:
        """
        竞争动态建模
        """
        # 卖家集中度
        total_offers = self._safe_float(data.get('Total Offer Count', 0))
        fba_offers = self._safe_float(data.get('Count of retrieved live offers: New, FBA', 0))
        fbm_offers = self._safe_float(data.get('Count of retrieved live offers: New, FBM', 0))
        
        # Buy Box竞争
        buy_box_winners = self._safe_float(data.get('Buy Box: Winner Count 90 days', 0))
        amazon_pct = self._safe_float(data.get('Buy Box: % Amazon 90 days', '0%').replace('%', ''))
        
        # 市场集中度 (HHI近似)
        if total_offers > 0:
            hhi_approx = 10000 / total_offers  # 简化计算
        else:
            hhi_approx = 0
        
        # 价格竞争强度
        price_flipability = data.get('Buy Box: Flipability 90 days', 'N/A')
        
        return {
            'seller_concentration': {
                'total_offers': int(total_offers),
                'fba_offers': int(fba_offers),
                'fbm_offers': int(fbm_offers),
                'hhi_approx': int(hhi_approx),
                'concentration_level': 'High' if hhi_approx > 2500 else 'Medium' if hhi_approx > 1500 else 'Low',
            },
            'buy_box_competition': {
                'winner_count_90d': int(buy_box_winners),
                'amazon_share': f"{amazon_pct:.1f}%",
                'flipability': price_flipability,
                'stability': 'Stable' if buy_box_winners <= 3 else 'Volatile',
            },
            'price_war_probability': self._estimate_price_war_risk(data),
        }
    
    def _run_monte_carlo(self, data: Dict, iterations: int = 1000) -> Dict:
        """
        蒙特卡洛模拟 V2
        
        基于真实成本结构的盈利分布模拟
        """
        np.random.seed(42)
        
        # 获取基础参数（使用智能获取）
        base_price = self._get_effective_price(data)
        base_sales = self._safe_float(data.get('Bought in past month', 100))
        
        # 计算基础成本结构
        fba_fee = self._safe_float(data.get('FBA Pick&Pack Fee', 0))
        if fba_fee == 0:
            fba_fee = self._estimate_fba_fee(data, base_price)
        
        estimated_cogs = self._estimate_cogs(data, base_price)
        referral_rate = self._safe_float(data.get('Referral Fee %', 15)) / 100
        return_rate = self._estimate_return_rate(data)
        
        # 基础利润率
        base_profit_per_unit = base_price - estimated_cogs - fba_fee - (base_price * referral_rate) - (base_price * return_rate * 0.3) - (base_price * 0.15)
        
        simulations = []
        
        for _ in range(iterations):
            # 价格随机波动 (±12%，正态分布)
            price_factor = np.random.normal(1.0, 0.06)
            
            # 销量随机波动 (±25%，正态分布)
            sales_factor = np.random.normal(1.0, 0.125)
            
            # COGS随机波动 (±8%)
            cogs_factor = np.random.normal(1.0, 0.04)
            
            # 计算该情景
            sim_price = base_price * price_factor
            sim_sales = max(0, base_sales * sales_factor)
            sim_cogs = estimated_cogs * cogs_factor
            sim_referral = sim_price * referral_rate
            sim_return = sim_price * return_rate * 0.3
            
            # 月利润 = 单件利润 × 销量
            profit_per_unit = sim_price - sim_cogs - fba_fee - sim_referral - sim_return - (sim_price * 0.15)
            monthly_profit = profit_per_unit * sim_sales
            
            simulations.append(monthly_profit)
        
        simulations = np.array(simulations)
        
        return {
            'monthly_profit_distribution': {
                'mean': round(np.mean(simulations), 2),
                'median': round(np.median(simulations), 2),
                'std': round(np.std(simulations), 2),
                'min': round(np.min(simulations), 2),
                'max': round(np.max(simulations), 2),
                'percentile_5': round(np.percentile(simulations, 5), 2),
                'percentile_95': round(np.percentile(simulations, 95), 2),
            },
            'probability_analysis': {
                'p_profit_positive': f"{(simulations > 0).mean():.1%}",
                'p_profit_gt_1000': f"{(simulations > 1000).mean():.1%}",
                'p_loss': f"{(simulations < 0).mean():.1%}",
            },
            'risk_metrics': {
                'var_95': round(np.percentile(simulations, 5), 2),  # 95% VaR
                'cvar_95': round(simulations[simulations <= np.percentile(simulations, 5)].mean(), 2),
            }
        }
    
    def _generate_recommendations(self, data: Dict) -> List[Dict]:
        """生成战略建议"""
        recommendations = []
        
        # 基于净利率的建议
        net_margin = self._calculate_profitability(data)['profitability']['net_margin']
        if net_margin < 10:
            recommendations.append({
                'priority': 'high',
                'category': '成本优化',
                'action': ' negotiate供应商降价10-15%或寻找替代供应商',
                'impact': f'可提升净利率至 {net_margin + 5:.1f}%',
            })
        
        # 基于竞争的建议
        amazon_pct = self._safe_float(data.get('Buy Box: % Amazon 90 days', '0%').replace('%', ''))
        if amazon_pct > 20:
            recommendations.append({
                'priority': 'high',
                'category': '竞争策略',
                'action': '差异化定位或寻找品牌授权，避免与Amazon自营直接竞争',
                'impact': '提升Buy Box胜率至30%+',
            })
        
        # 基于退货率的建议
        return_rate = self._estimate_return_rate(data)
        if return_rate > 0.08:
            recommendations.append({
                'priority': 'medium',
                'category': '质量控制',
                'action': '加强产品质检，优化产品描述减少期望落差',
                'impact': f'降低退货率从 {return_rate:.1%} 至 5%',
            })
        
        return recommendations
    
    # 辅助方法
    def _safe_float(self, value, default=0.0) -> float:
        """安全转换为float"""
        if pd.isna(value) or value is None:
            return default
        try:
            # 处理货币格式 ($ 3.38)
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').replace('%', '').strip()
            return float(value)
        except:
            return default
    
    def _estimate_return_rate(self, data: Dict) -> float:
        """估算退货率"""
        # 使用CSV中的Return Rate字段
        csv_return = data.get('Return Rate', 'Low')
        if isinstance(csv_return, str):
            if 'High' in csv_return:
                return 0.12
            elif 'Medium' in csv_return:
                return 0.08
            elif 'Low' in csv_return:
                return 0.04
        
        # 基于类目估算
        category = data.get('Categories: Root', '')
        return self.CATEGORY_RETURN_RATES.get(category, 0.06)
    
    def _estimate_storage_cost(self, data: Dict) -> float:
        """估算月度仓储成本"""
        # 简化计算：每单位每月$0.50
        monthly_sales = self._safe_float(data.get('Bought in past month', 100))
        avg_inventory = monthly_sales * 1.5  # 1.5个月库存
        return avg_inventory * 0.50
    
    def _calculate_var(self, data: Dict, confidence: float = 0.95) -> float:
        """计算风险价值 (VaR)"""
        # 简化计算
        monthly_sales = self._safe_float(data.get('Bought in past month', 100))
        price = self._safe_float(data.get('Buy Box: Current', 30))
        volatility = 0.15  # 假设15%波动率
        
        z_score = 1.645 if confidence == 0.95 else 2.33  # 95% or 99%
        var = monthly_sales * price * volatility * z_score
        return round(var, 2)
    
    def _estimate_price_war_risk(self, data: Dict) -> Dict:
        """估算价格战风险"""
        total_offers = self._safe_float(data.get('Total Offer Count', 0))
        price_std = self._safe_float(data.get('Buy Box: Standard Deviation 90 days', 0))
        current_price = self._safe_float(data.get('Buy Box: Current', 1))
        
        risk_factors = []
        if total_offers > 10:
            risk_factors.append('卖家数量多')
        if price_std / current_price > 0.1 if current_price > 0 else False:
            risk_factors.append('价格波动大')
        
        probability = min(0.8, len(risk_factors) * 0.3)
        
        return {
            'probability': f"{probability:.1%}",
            'risk_factors': risk_factors,
            'mitigation': '差异化或建立品牌壁垒' if risk_factors else '维持现状',
        }
    
    def _grade_profitability(self, net_margin: float) -> str:
        """盈利能力评级"""
        if net_margin >= 25:
            return 'A (优秀)'
        elif net_margin >= 15:
            return 'B (良好)'
        elif net_margin >= 8:
            return 'C (及格)'
        elif net_margin >= 0:
            return 'D (危险)'
        else:
            return 'F (亏损)'
    
    def _grade_risk(self, risk_score: float) -> str:
        """风险评级"""
        if risk_score < 30:
            return '低风险'
        elif risk_score < 50:
            return '中等风险'
        elif risk_score < 70:
            return '高风险'
        else:
            return '极高风险'


def format_actuarial_report(analysis: Dict) -> str:
    """格式化精算分析报告为HTML"""
    # 这里可以生成精美的HTML报告
    return json.dumps(analysis, indent=2, ensure_ascii=False)
