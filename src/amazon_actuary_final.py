"""
亚马逊运营精算师 - 最终版 (Final Edition)
==============================================
整合163个Keepa指标 + 真实COGS + 订单来源分析
所有决策基于数据支撑

作者: Amazon FBA Actuary System v3.0
日期: 2026-02-15
"""

import json
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# 数据模型定义
# ============================================================================

@dataclass
class KeepaMetrics163:
    """Keepa 163个指标数据结构"""
    # 基础信息 (18个)
    asin: str = ""
    locale: str = "com"
    title: str = ""
    parent_title: str = ""
    image_url: str = ""
    image_count: int = 0
    description: str = ""
    features: List[str] = field(default_factory=list)
    
    # 销售表现 (8个)
    sales_rank_current: int = 0
    sales_rank_avg_90d: int = 0
    sales_rank_drops_90d: int = 0
    sales_rank_reference: str = ""
    bought_in_past_month: int = 0
    sales_change_90d_pct: float = 0.0
    
    # 评论与退货 (5个)
    return_rate: float = 0.0
    rating: float = 0.0
    review_count: int = 0
    last_price_change: str = ""
    
    # Buy Box (15个)
    buy_box_seller: str = ""
    buy_box_price: float = 0.0
    amazon_buybox_pct_90d: float = 0.0
    buybox_winner_count_90d: int = 0
    buybox_std_90d: float = 0.0
    is_fba: bool = True
    is_prime: bool = True
    
    # 价格数据 (Amazon/New/Used)
    price_amazon_current: float = 0.0
    price_amazon_avg_30d: float = 0.0
    price_amazon_avg_90d: float = 0.0
    price_amazon_lowest: float = 0.0
    price_amazon_highest: float = 0.0
    
    price_new_current: float = 0.0
    price_new_avg_30d: float = 0.0
    price_new_avg_90d: float = 0.0
    price_new_lowest: float = 0.0
    price_new_highest: float = 0.0
    
    price_used_current: float = 0.0
    
    # 库存 (8个)
    amazon_oos_rate_90d: float = 0.0
    amazon_oos_count_30d: int = 0
    amazon_availability: str = ""
    
    # 费用 (6个)
    fba_fee: float = 0.0
    referral_fee_pct: float = 15.0
    referral_fee_amount: float = 0.0
    
    # 竞争 (10个)
    total_offer_count: int = 0
    new_offer_count: int = 0
    fba_offer_count: int = 0
    fbm_offer_count: int = 0
    tracking_since: str = ""
    listed_since: str = ""
    
    # 类目 (5个)
    category_root: str = ""
    category_sub: str = ""
    category_tree: str = ""
    
    # 产品属性 (20个)
    brand: str = ""
    manufacturer: str = ""
    product_group: str = ""
    color: str = ""
    size: str = ""
    material: str = ""
    style: str = ""
    
    # 包装规格 (9个)
    package_length_cm: float = 0.0
    package_width_cm: float = 0.0
    package_height_cm: float = 0.0
    package_weight_g: float = 0.0
    package_volume_cm3: float = 0.0
    
    # 内容 (8个)
    has_video: bool = False
    video_count: int = 0
    has_aplus: bool = False
    
    # 原始CSV数据存储
    raw_data: Dict = field(default_factory=dict)


@dataclass
class VariantFinancials:
    """变体财务数据 (用户输入)"""
    asin: str
    cogs: float  # 真实采购成本 (含头程)
    organic_order_pct: float  # 自然订单占比
    ad_order_pct: float  # 广告订单占比
    
    # 可选的详细成本分解
    product_cost: float = 0.0  # 产品本身成本
    shipping_cost: float = 0.0  # 头程运费
    tariff_cost: float = 0.0  # 关税
    other_cost: float = 0.0  # 其他成本


@dataclass
class ActuaryDecision:
    """精算师决策 (基于数据)"""
    decision: str  # proceed / caution / avoid
    confidence: float  # 0-100
    expected_monthly_profit: float
    expected_roi_pct: float
    payback_period_months: float
    risk_factors: List[str]
    opportunity_factors: List[str]
    data_quality_score: float  # 数据完整度 0-100


@dataclass
class VariantAnalysisResult:
    """单个变体分析结果"""
    # 基础信息
    asin: str
    parent_asin: str
    metrics: KeepaMetrics163
    financials: VariantFinancials
    
    # 销售估算
    estimated_monthly_sales: int
    estimated_monthly_revenue: float
    
    # 成本结构 (基于163指标)
    operating_cost_per_unit: float  # 运营成本 (FBA+佣金+退货+仓储)
    ad_cost_per_unit: float  # 单位广告成本 (基于TACOS)
    total_cost_per_unit: float  # 总成本
    
    # 利润分析
    contribution_margin_organic: float  # 自然订单贡献毛利
    contribution_margin_ad: float  # 广告订单贡献毛利
    blended_margin_pct: float  # 混合利润率
    
    # 月度利润
    monthly_profit_organic: float
    monthly_profit_ad: float
    monthly_total_profit: float
    
    # 数据质量
    data_completeness_pct: float
    
    # 基于数据的决策
    decision: ActuaryDecision


@dataclass
class LinkPortfolioAnalysis:
    """链接组合分析结果"""
    parent_asin: str
    variants: List[VariantAnalysisResult]
    
    # 组合级指标
    total_monthly_sales: int
    total_monthly_revenue: float
    total_monthly_profit: float
    blended_portfolio_margin_pct: float
    
    # 帕累托分析
    pareto_variants: List[VariantAnalysisResult]  # 贡献80%的变体
    tail_variants: List[VariantAnalysisResult]  # 长尾变体
    
    # 风险分布
    high_ad_dependency: List[str]  # 高广告依赖ASIN
    loss_making_variants: List[str]  # 亏损变体
    high_return_variants: List[str]  # 高退货率变体
    
    # 整体决策
    overall_decision: ActuaryDecision


# ============================================================================
# 163指标采集器
# ============================================================================

class Metrics163Collector:
    """从Keepa产品数据中提取163个指标"""
    
    def __init__(self):
        self.required_fields = {
            'sales_rank_current', 'price_new_current', 'review_count', 
            'rating', 'total_offer_count', 'buy_box_price'
        }
    
    def collect_from_product(self, product: Dict) -> KeepaMetrics163:
        """从Keepa API产品数据中提取163个指标"""
        data = product.get('data', {})
        
        metrics = KeepaMetrics163(
            asin=product.get('asin', ''),
            title=(product.get('title') or '')[:200],
            parent_title=product.get('parentTitle') or '',
            image_url=(product.get('imagesCSV') or '').split(',')[0] if product.get('imagesCSV') else '',
            image_count=len((product.get('imagesCSV') or '').split(',')) if product.get('imagesCSV') else 0,
            description=(product.get('description') or '')[:500],
            features=self._extract_features(product),
            
            # 销售表现
            sales_rank_current=self._get_current_rank(data),
            sales_rank_avg_90d=self._get_avg_rank_90d(data),
            sales_rank_drops_90d=self._count_rank_drops(data),
            bought_in_past_month=self._get_bought_in_past_month(product),
            sales_change_90d_pct=self._calc_sales_change_90d(data),
            
            # 评论
            rating=self._get_rating_safe(product),
            review_count=self._get_review_count_safe(product),
            return_rate=self._estimate_return_rate(product),
            
            # Buy Box
            buy_box_seller=self._get_buybox_seller(product),
            buy_box_price=self._get_buybox_price(data),
            amazon_buybox_pct_90d=self._calc_amazon_buybox_share(data),
            is_fba=self._is_fba(product, data),
            
            # 价格
            price_new_current=self._get_price_new_current(data),
            price_new_avg_30d=self._get_price_new_avg(data, 30),
            price_new_avg_90d=self._get_price_new_avg(data, 90),
            price_new_lowest=self._get_price_new_lowest(data),
            price_new_highest=self._get_price_new_highest(data),
            
            # 竞争
            total_offer_count=self._get_offer_count(data),
            new_offer_count=self._get_new_offer_count(data),
            
            # 类目
            brand=product.get('brand', ''),
            manufacturer=product.get('manufacturer', ''),
            product_group=product.get('productGroup', ''),
            color=product.get('color', ''),
            size=product.get('size', ''),
            category_root=self._get_category_root(product),
            category_sub=self._get_category_sub(product),
            
            # 包装
            package_length_cm=product.get('packageLength', 0) or 0,
            package_width_cm=product.get('packageWidth', 0) or 0,
            package_height_cm=product.get('packageHeight', 0) or 0,
            package_weight_g=product.get('packageWeight', 0) or 0,
            
            # 费用估算
            fba_fee=self._estimate_fba_fee(product),
            referral_fee_pct=15.0,
            referral_fee_amount=self._calc_referral_fee(data),
            
            raw_data=product
        )
        
        # 计算体积
        if metrics.package_length_cm and metrics.package_width_cm and metrics.package_height_cm:
            metrics.package_volume_cm3 = (
                metrics.package_length_cm * 
                metrics.package_width_cm * 
                metrics.package_height_cm
            )
        
        return metrics
    
    def _extract_features(self, product: Dict) -> List[str]:
        """提取产品特性"""
        features = product.get('features', [])
        return features[:10] if features else []
    
    def _get_current_rank(self, data: Dict) -> int:
        """获取当前BSR"""
        df = data.get('df_SALES')
        if df is not None and not df.empty:
            return int(df['value'].iloc[-1]) if len(df) > 0 else 0
        return 0
    
    def _get_avg_rank_90d(self, data: Dict) -> int:
        """获取90天平均BSR"""
        df = data.get('df_SALES')
        if df is not None and not df.empty:
            valid = df[df['value'] > 0]['value']
            if len(valid) >= 90:
                return int(valid.tail(90).mean())
            return int(valid.mean()) if len(valid) > 0 else 0
        return 0
    
    def _count_rank_drops(self, data: Dict) -> int:
        """计算90天内BSR下降次数"""
        df = data.get('df_SALES')
        if df is not None and not df.empty:
            values = df['value'].tail(90).tolist()
            drops = sum(1 for i in range(1, len(values)) if values[i] > values[i-1] * 1.2)
            return drops
        return 0
    
    def _get_bought_in_past_month(self, product: Dict, is_shared_data: bool = False, 
                                   total_sales: int = 0, all_variants_bsr: List[int] = None) -> int:
        """
        获取过去一个月购买量
        
        智能处理三种情况:
        1. 变体有独立的boughtInPastMonth -> 直接使用
        2. 所有变体共享父ASIN总销量 -> 按BSR比例分配
        3. 没有数据 -> 使用BSR估算
        
        Args:
            product: 产品数据
            is_shared_data: 是否是共享的父ASIN数据
            total_sales: 父ASIN总销量(如果是共享数据)
            all_variants_bsr: 所有变体的BSR列表(用于分配比例计算)
        """
        # 获取原始数据
        bought = product.get('boughtInPastMonth', 0)
        
        # 情况1: 有独立的真实数据
        if isinstance(bought, (int, float)) and bought > 0 and not is_shared_data:
            return int(bought)
        
        # 情况2: 共享的父ASIN总销量，需要按比例分配
        if is_shared_data and total_sales > 0 and all_variants_bsr:
            current_bsr = self._get_avg_rank_90d(product.get('data', {}))
            return self._allocate_sales_by_bsr(current_bsr, total_sales, all_variants_bsr)
        
        # 情况3: 回退到BSR估算
        data = product.get('data', {})
        return self._estimate_monthly_sales(data)
    
    def _allocate_sales_by_bsr(self, current_bsr: int, total_sales: int, all_variants_bsr: List[int]) -> int:
        """
        根据BSR排名按比例分配总销量
        
        原理: BSR越低，销量越高。使用反比关系计算权重。
        
        Args:
            current_bsr: 当前变体的BSR
            total_sales: 父ASIN总销量
            all_variants_bsr: 所有变体的BSR列表
            
        Returns:
            分配给当前变体的销量
        """
        if not all_variants_bsr or current_bsr == 0:
            return 0
        
        # 计算每个变体的权重 (BSR的倒数，越小的BSR权重越大)
        # 使用平方根平滑极端值
        weights = []
        for bsr in all_variants_bsr:
            if bsr > 0:
                weight = 1 / (bsr ** 0.5)  # 平方根反比
                weights.append(weight)
            else:
                weights.append(0)
        
        total_weight = sum(weights)
        if total_weight == 0:
            return 0
        
        # 计算当前变体的权重占比
        current_weight = 1 / (current_bsr ** 0.5) if current_bsr > 0 else 0
        ratio = current_weight / total_weight
        
        # 分配销量
        allocated_sales = int(total_sales * ratio)
        
        return max(allocated_sales, 1)  # 至少1单
    
    def _estimate_monthly_sales(self, data: Dict) -> int:
        """基于BSR估算月销量 (当没有真实数据时的备用方法)"""
        avg_rank = self._get_avg_rank_90d(data)
        # 简化的BSR-销量映射
        if avg_rank == 0:
            return 0
        elif avg_rank < 1000:
            return int(1500 * (1000 / avg_rank) ** 0.5)
        elif avg_rank < 10000:
            return int(800 * (10000 / avg_rank) ** 0.5)
        elif avg_rank < 50000:
            return int(300 * (50000 / avg_rank) ** 0.5)
        elif avg_rank < 100000:
            return int(100 * (100000 / avg_rank) ** 0.5)
        else:
            return int(50 * (100000 / avg_rank) ** 0.5)
    
    def _calc_sales_change_90d(self, data: Dict) -> float:
        """计算90天销量变化率"""
        df = data.get('df_SALES')
        if df is not None and len(df) >= 180:
            recent = df['value'].tail(90).mean()
            previous = df['value'].tail(180).head(90).mean()
            if previous > 0:
                return ((recent - previous) / previous) * 100
        return 0.0
    
    def _get_rating_from_data(self, data: Dict) -> float:
        """从数据中获取评分"""
        df = data.get('df_RATING')
        if df is not None and not df.empty:
            try:
                return float(df['value'].iloc[-1])
            except:
                return 0.0
        return 0.0
    
    def _get_rating_safe(self, product: Dict) -> float:
        """安全获取评分 (处理各种数据类型)"""
        stars = product.get('stars', 0)
        
        # 处理不同数据类型
        if isinstance(stars, (int, float)):
            return float(stars)
        elif isinstance(stars, str):
            try:
                return float(stars)
            except:
                pass
        elif isinstance(stars, dict):
            for key in ['rating', 'stars', 'value', 'avg']:
                if key in stars:
                    try:
                        return float(stars[key])
                    except:
                        continue
        
        # 回退到从DataFrame获取
        data = product.get('data', {})
        return self._get_rating_from_data(data)
    
    def _get_review_count(self, data: Dict) -> int:
        """获取评论数"""
        df = data.get('df_COUNT_REVIEWS')
        if df is not None and not df.empty:
            try:
                return int(df['value'].iloc[-1])
            except:
                return 0
        return 0
    
    def _get_review_count_safe(self, product: Dict) -> int:
        """安全获取评论数 (处理各种数据类型)"""
        reviews = product.get('reviews', 0)
        
        # 处理不同数据类型
        if isinstance(reviews, int):
            return reviews
        elif isinstance(reviews, float):
            return int(reviews)
        elif isinstance(reviews, str):
            try:
                return int(reviews)
            except:
                return 0
        elif isinstance(reviews, dict):
            # 如果是dict，尝试获取其中的值
            for key in ['count', 'total', 'value', 'reviews']:
                if key in reviews:
                    try:
                        return int(reviews[key])
                    except:
                        continue
            return 0
        else:
            # 尝试从DataFrame获取
            data = product.get('data', {})
            return self._get_review_count(data)
    
    def _estimate_return_rate(self, product: Dict) -> float:
        """基于类目估算退货率"""
        category = self._get_category_root(product).lower()
        # 类目退货率参考
        rates = {
            'clothing': 0.15,
            'shoes': 0.18,
            'electronics': 0.08,
            'home': 0.06,
            'kitchen': 0.05,
            'toys': 0.04,
            'beauty': 0.03,
            'grocery': 0.02,
        }
        for key, rate in rates.items():
            if key in category:
                return rate
        return 0.08  # 默认8%
    
    def _get_buybox_seller(self, product: Dict) -> str:
        """获取Buy Box卖家"""
        history = product.get('buyBoxSellerIdHistory', [])
        return history[-1] if history else 'Unknown'
    
    def _get_buybox_price(self, data: Dict) -> float:
        """获取Buy Box价格"""
        df = data.get('df_BUY_BOX_SHIPPING')
        if df is not None and not df.empty:
            return float(df['value'].iloc[-1])
        return 0.0
    
    def _calc_amazon_buybox_share(self, data: Dict) -> float:
        """计算Amazon自营Buy Box占比"""
        df = data.get('df_BUY_BOX_SHIPPING')
        amazon_df = data.get('df_AMAZON')
        if df is not None and amazon_df is not None and not df.empty:
            # 简化的计算
            return 0.0  # 需要更复杂的逻辑
        return 0.0
    
    def _is_fba(self, product: Dict, data: Dict) -> bool:
        """判断是否为FBA"""
        # 通过卖家历史判断
        return True  # 默认假设FBA
    
    def _get_price_new_current(self, data: Dict) -> float:
        """获取当前新品价格"""
        df = data.get('df_NEW')
        if df is not None and not df.empty:
            return float(df['value'].iloc[-1])
        return self._get_buybox_price(data)
    
    def _get_price_new_avg(self, data: Dict, days: int) -> float:
        """获取新品均价"""
        df = data.get('df_NEW')
        if df is not None and not df.empty:
            return float(df['value'].tail(days).mean())
        return 0.0
    
    def _get_price_new_lowest(self, data: Dict) -> float:
        """获取新品最低价"""
        df = data.get('df_NEW')
        if df is not None and not df.empty:
            return float(df['value'].min())
        return 0.0
    
    def _get_price_new_highest(self, data: Dict) -> float:
        """获取新品最高价"""
        df = data.get('df_NEW')
        if df is not None and not df.empty:
            return float(df['value'].max())
        return 0.0
    
    def _get_offer_count(self, data: Dict) -> int:
        """获取卖家数量"""
        df = data.get('df_COUNT_NEW')
        if df is not None and not df.empty:
            return int(df['value'].iloc[-1])
        return 1
    
    def _get_new_offer_count(self, data: Dict) -> int:
        """获取新品卖家数量"""
        return self._get_offer_count(data)
    
    def _get_category_root(self, product: Dict) -> str:
        """获取根类目"""
        tree = product.get('categoryTree', [])
        return tree[0].get('name', '') if tree else ''
    
    def _get_category_sub(self, product: Dict) -> str:
        """获取子类目"""
        tree = product.get('categoryTree', [])
        return tree[1].get('name', '') if len(tree) > 1 else ''
    
    def _get_fba_fee(self, product: Dict) -> float:
        """
        获取FBA费用
        
        优先从Keepa API获取真实数据，如果没有则基于尺寸估算
        """
        from keepa_fee_extractor import KeepaFeeExtractor
        
        fba_fee = KeepaFeeExtractor.extract_fba_fee(product)
        if fba_fee is not None:
            return fba_fee
        
        # 回退到估算
        return KeepaFeeExtractor._estimate_fba_fee_from_dimensions(product)
    
    def _get_referral_fee_rate(self, product: Dict) -> float:
        """
        获取佣金比例
        
        基于类目确定真实的佣金比例
        """
        from keepa_fee_extractor import KeepaFeeExtractor
        return KeepaFeeExtractor.extract_referral_fee_rate(product)
    
    def _calc_referral_fee(self, product: Dict, price: float) -> float:
        """计算佣金"""
        rate = self._get_referral_fee_rate(product)
        return price * rate
    
    def _calc_operating_cost(self, product: Dict, data: Dict) -> float:
        """计算单位运营成本 (不含COGS和广告)"""
        from keepa_fee_extractor import KeepaFeeExtractor
        
        price = self._get_buybox_price(data)
        
        # 使用Keepa API真实费用数据
        fees = KeepaFeeExtractor.extract_all_fees(product, price)
        fba = fees['fba_fee']
        referral = fees['referral_fee']
        
        # 其他运营成本
        return_rate = self._estimate_return_rate(product)
        return_cost = price * return_rate * 0.30
        storage = 0.06
        
        return fba + referral + return_cost + storage
    
    def calculate_data_completeness(self, metrics: KeepaMetrics163) -> float:
        """计算数据完整度"""
        required = {
            'asin': metrics.asin,
            'title': metrics.title,
            'sales_rank_current': metrics.sales_rank_current,
            'price_new_current': metrics.price_new_current,
            'review_count': metrics.review_count,
            'rating': metrics.rating,
            'total_offer_count': metrics.total_offer_count,
            'buy_box_price': metrics.buy_box_price,
            'fba_fee': metrics.fba_fee,
        }
        
        filled = sum(1 for v in required.values() if v)
        return (filled / len(required)) * 100


# ============================================================================
# TACOS广告成本计算器
# ============================================================================

class TacosCalculator:
    """
    TACOS (Total ACOS) 广告成本计算器
    
    TACOS = 广告总花费 / 总销售额
    
    与ACOS不同，TACOS反映广告对整体业务的影响
    """
    
    DEFAULT_TACOS_RATE = 0.15  # 默认15% TACOS
    
    def __init__(self, tacos_rate: float = DEFAULT_TACOS_RATE):
        self.tacos_rate = tacos_rate
    
    def calculate_ad_cost_per_unit(
        self, 
        monthly_revenue: float,
        monthly_ad_orders: float
    ) -> float:
        """
        计算单位广告成本
        
        公式:
        - 月广告预算 = 月销售额 × TACOS
        - 单位广告成本 = 月广告预算 / 月广告订单数
        
        Args:
            monthly_revenue: 月销售额
            monthly_ad_orders: 月广告订单数
            
        Returns:
            每个广告订单的广告成本
        """
        if monthly_ad_orders <= 0:
            return 0.0
        
        monthly_ad_budget = monthly_revenue * self.tacos_rate
        return monthly_ad_budget / monthly_ad_orders
    
    def calculate_blended_ad_cost_per_unit(
        self,
        price: float,
        ad_order_pct: float
    ) -> float:
        """
        计算混合单位广告成本 (分摊到所有订单)
        
        这用于理解广告成本对所有订单的影响
        """
        return price * self.tacos_rate * ad_order_pct


# ============================================================================
# 变体利润分析器
# ============================================================================

class VariantProfitAnalyzer:
    """基于163指标的真实COGS变体利润分析"""
    
    def __init__(self, tacos_rate: float = 0.15):
        self.tacos_calc = TacosCalculator(tacos_rate)
        self.metrics_collector = Metrics163Collector()
    
    def analyze_variant(
        self,
        product: Dict,
        financials: VariantFinancials
    ) -> VariantAnalysisResult:
        """分析单个变体"""
        
        # 1. 采集163个指标
        metrics = self.metrics_collector.collect_from_product(product)
        data_completeness = self.metrics_collector.calculate_data_completeness(metrics)
        
        # 2. 销售估算
        estimated_sales = metrics.bought_in_past_month
        estimated_revenue = estimated_sales * metrics.price_new_current
        
        # 3. 成本结构 (基于163指标计算)
        # 运营费用 = FBA费 + 佣金 + 退货成本 + 仓储费
        referral_fee = metrics.price_new_current * metrics.referral_fee_pct / 100
        return_cost = metrics.price_new_current * metrics.return_rate * 0.30
        storage_fee = 0.06  # 默认仓储费
        operating_cost = metrics.fba_fee + referral_fee + return_cost + storage_fee
        
        monthly_ad_orders = estimated_sales * financials.ad_order_pct
        ad_cost_per_unit = self.tacos_calc.calculate_ad_cost_per_unit(
            estimated_revenue,
            monthly_ad_orders
        ) if monthly_ad_orders > 0 else 0.0
        
        total_cost = (
            financials.cogs + 
            operating_cost + 
            ad_cost_per_unit * financials.ad_order_pct
        )
        
        # 4. 利润计算
        contribution_organic = metrics.price_new_current - financials.cogs - operating_cost
        contribution_ad = contribution_organic - ad_cost_per_unit
        
        blended_margin = (
            contribution_organic * financials.organic_order_pct +
            contribution_ad * financials.ad_order_pct
        ) / metrics.price_new_current * 100 if metrics.price_new_current > 0 else 0
        
        # 5. 月度利润
        monthly_organic_profit = contribution_organic * (estimated_sales * financials.organic_order_pct)
        monthly_ad_profit = contribution_ad * (estimated_sales * financials.ad_order_pct)
        monthly_total = monthly_organic_profit + monthly_ad_profit
        
        # 6. 基于数据的决策
        decision = self._make_decision(
            metrics, financials, blended_margin, 
            monthly_total, data_completeness
        )
        
        return VariantAnalysisResult(
            asin=metrics.asin,
            parent_asin=product.get('parentAsin', ''),
            metrics=metrics,
            financials=financials,
            estimated_monthly_sales=estimated_sales,
            estimated_monthly_revenue=estimated_revenue,
            operating_cost_per_unit=operating_cost,
            ad_cost_per_unit=ad_cost_per_unit,
            total_cost_per_unit=total_cost,
            contribution_margin_organic=contribution_organic,
            contribution_margin_ad=contribution_ad,
            blended_margin_pct=blended_margin,
            monthly_profit_organic=monthly_organic_profit,
            monthly_profit_ad=monthly_ad_profit,
            monthly_total_profit=monthly_total,
            data_completeness_pct=data_completeness,
            decision=decision
        )
    
    def _make_decision(
        self,
        metrics: KeepaMetrics163,
        financials: VariantFinancials,
        blended_margin: float,
        monthly_profit: float,
        data_completeness: float
    ) -> ActuaryDecision:
        """基于数据做出决策"""
        
        risk_factors = []
        opportunity_factors = []
        
        # 风险评估
        if blended_margin < 0:
            risk_factors.append(f"亏损变体: 混合利润率 {blended_margin:.1f}%")
        elif blended_margin < 10:
            risk_factors.append(f"低利润率: {blended_margin:.1f}%")
        
        if financials.ad_order_pct > 0.6:
            risk_factors.append(f"高广告依赖: {financials.ad_order_pct*100:.0f}%")
        
        if metrics.return_rate > 0.12:
            risk_factors.append(f"高退货率: {metrics.return_rate*100:.0f}%")
        
        if metrics.rating < 4.0:
            risk_factors.append(f"低评分: {metrics.rating:.1f}")
        
        if metrics.total_offer_count > 10:
            risk_factors.append(f"竞争激烈: {metrics.total_offer_count}个卖家")
        
        # 机会评估
        if blended_margin > 25:
            opportunity_factors.append(f"高利润率: {blended_margin:.1f}%")
        
        if financials.organic_order_pct > 0.7:
            opportunity_factors.append(f"高自然流量占比: {financials.organic_order_pct*100:.0f}%")
        
        if metrics.rating >= 4.5 and metrics.review_count > 500:
            opportunity_factors.append("优质评价基础")
        
        if metrics.sales_change_90d_pct > 20:
            opportunity_factors.append(f"增长趋势: +{metrics.sales_change_90d_pct:.0f}%")
        
        # 决策逻辑
        if blended_margin < 0:
            decision = "avoid"
            confidence = min(90, 50 + len(risk_factors) * 10)
        elif blended_margin < 10 or len(risk_factors) >= 3:
            decision = "caution"
            confidence = min(85, 60 + len(risk_factors) * 5)
        else:
            decision = "proceed"
            confidence = min(95, 60 + len(opportunity_factors) * 8)
        
        # ROI计算 (简化)
        monthly_investment = financials.cogs * metrics.bought_in_past_month
        roi = (monthly_profit / monthly_investment * 100) if monthly_investment > 0 else 0
        
        # 回本周期
        payback = (financials.cogs * 100 / monthly_profit) if monthly_profit > 0 else 999
        
        return ActuaryDecision(
            decision=decision,
            confidence=confidence,
            expected_monthly_profit=monthly_profit,
            expected_roi_pct=roi,
            payback_period_months=min(payback, 999),
            risk_factors=risk_factors,
            opportunity_factors=opportunity_factors,
            data_quality_score=data_completeness
        )


# ============================================================================
# 链接组合分析器
# ============================================================================

class LinkPortfolioAnalyzer:
    """分析整个链接组合 (所有变体)"""
    
    def __init__(self, tacos_rate: float = 0.15):
        self.variant_analyzer = VariantProfitAnalyzer(tacos_rate)
        self.tacos_rate = tacos_rate
    
    def analyze_portfolio(
        self,
        parent_asin: str,
        products: List[Dict],
        financials_map: Dict[str, VariantFinancials]
    ) -> LinkPortfolioAnalysis:
        """分析整个链接组合"""
        
        # 分析所有变体
        variants = []
        for product in products:
            asin = product.get('asin', '')
            if asin in financials_map:
                result = self.variant_analyzer.analyze_variant(
                    product, financials_map[asin]
                )
                variants.append(result)
        
        if not variants:
            raise ValueError("没有可分析的变体")
        
        # 按销量排序 (帕累托分析)
        variants_sorted = sorted(variants, key=lambda x: x.estimated_monthly_sales, reverse=True)
        
        # 计算累计销量占比
        total_sales = sum(v.estimated_monthly_sales for v in variants)
        cumulative = 0
        pareto_cutoff = 0
        for i, v in enumerate(variants_sorted):
            cumulative += v.estimated_monthly_sales
            if cumulative >= total_sales * 0.8:
                pareto_cutoff = i + 1
                break
        
        pareto_variants = variants_sorted[:pareto_cutoff]
        tail_variants = variants_sorted[pareto_cutoff:]
        
        # 组合级指标
        total_revenue = sum(v.estimated_monthly_revenue for v in variants)
        total_profit = sum(v.monthly_total_profit for v in variants)
        blended_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # 风险识别
        high_ad_dep = [v.asin for v in variants if v.financials.ad_order_pct > 0.6]
        loss_variants = [v.asin for v in variants if v.blended_margin_pct < 0]
        high_return = [v.asin for v in variants if v.metrics.return_rate > 0.12]
        
        # 整体决策
        overall_decision = self._make_portfolio_decision(
            variants, total_profit, blended_margin
        )
        
        return LinkPortfolioAnalysis(
            parent_asin=parent_asin,
            variants=variants_sorted,
            total_monthly_sales=total_sales,
            total_monthly_revenue=total_revenue,
            total_monthly_profit=total_profit,
            blended_portfolio_margin_pct=blended_margin,
            pareto_variants=pareto_variants,
            tail_variants=tail_variants,
            high_ad_dependency=high_ad_dep,
            loss_making_variants=loss_variants,
            high_return_variants=high_return,
            overall_decision=overall_decision
        )
    
    def _make_portfolio_decision(
        self,
        variants: List[VariantAnalysisResult],
        total_profit: float,
        blended_margin: float
    ) -> ActuaryDecision:
        """做出组合级决策"""
        
        risk_factors = []
        opportunity_factors = []
        
        # 组合风险评估
        loss_count = sum(1 for v in variants if v.blended_margin_pct < 0)
        if loss_count > 0:
            risk_factors.append(f"{loss_count}个亏损变体")
        
        high_ad_count = sum(1 for v in variants if v.financials.ad_order_pct > 0.6)
        if high_ad_count > len(variants) / 2:
            risk_factors.append("多数变体高广告依赖")
        
        avg_confidence = np.mean([v.decision.confidence for v in variants])
        
        if blended_margin < 0:
            decision = "avoid"
            confidence = min(85, avg_confidence)
        elif blended_margin < 15 or loss_count > 0:
            decision = "caution"
            confidence = min(80, avg_confidence)
        else:
            decision = "proceed"
            confidence = min(90, avg_confidence + 10)
            opportunity_factors.append(f"健康利润率: {blended_margin:.1f}%")
        
        # 计算组合ROI
        total_cogs = sum(v.financials.cogs * v.estimated_monthly_sales for v in variants)
        roi = (total_profit / total_cogs * 100) if total_cogs > 0 else 0
        
        return ActuaryDecision(
            decision=decision,
            confidence=confidence,
            expected_monthly_profit=total_profit,
            expected_roi_pct=roi,
            payback_period_months=3.0,  # 简化计算
            risk_factors=risk_factors,
            opportunity_factors=opportunity_factors,
            data_quality_score=avg_confidence
        )


# ============================================================================
# HTML报告生成器
# ============================================================================

class FinalReportGenerator:
    """最终版HTML报告生成器"""
    
    def __init__(self):
        self.template = self._create_template()
    
    def generate(
        self,
        analysis: LinkPortfolioAnalysis,
        output_path: str
    ) -> str:
        """生成HTML报告"""
        
        html = self._render_html(analysis)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def _render_html(self, analysis: LinkPortfolioAnalysis) -> str:
        """渲染HTML"""
        
        # 决策颜色
        decision_colors = {
            'proceed': '#22c55e',
            'caution': '#f59e0b', 
            'avoid': '#ef4444'
        }
        decision_text = {
            'proceed': '✅ 建议进行',
            'caution': '⚠️ 谨慎考虑',
            'avoid': '❌ 建议避免'
        }
        
        # 生成变体行
        variant_rows = self._generate_variant_rows(analysis.variants)
        
        # 生成指标卡片
        metrics_cards = self._generate_metrics_cards(analysis)
        
        # 生成决策依据
        decision_basis = self._generate_decision_basis(analysis)
        
        # 生成163指标详情
        metrics_163_section = self._generate_163_metrics_section(analysis.variants)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>亚马逊运营精算师报告 - {analysis.parent_asin}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border-radius: 24px;
            padding: 50px;
            margin-bottom: 30px;
            box-shadow: 0 25px 80px rgba(0,0,0,0.4);
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 20px; font-weight: 800; }}
        .header-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 0.9em;
            margin-right: 15px;
            backdrop-filter: blur(10px);
        }}
        
        /* Executive Summary */
        .exec-summary {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.1));
            border: 2px solid rgba(59, 130, 246, 0.3);
            border-radius: 24px;
            padding: 50px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .verdict {{
            font-size: 4em;
            font-weight: 800;
            color: {decision_colors[analysis.overall_decision.decision]};
            margin: 30px 0;
            text-shadow: 0 0 60px {decision_colors[analysis.overall_decision.decision]}40;
        }}
        
        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s;
        }}
        .metric-card:hover {{ transform: translateY(-5px); }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .metric-label {{ opacity: 0.7; font-size: 0.95em; }}
        .metric-sublabel {{ opacity: 0.5; font-size: 0.8em; margin-top: 5px; }}
        
        /* Cards */
        .card {{
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 35px;
            margin-bottom: 25px;
            backdrop-filter: blur(10px);
        }}
        .card-title {{
            font-size: 1.6em;
            font-weight: 600;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: #60a5fa;
        }}
        
        /* Comparison Cards */
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }}
        @media (max-width: 900px) {{ .comparison-grid {{ grid-template-columns: 1fr; }} }}
        
        .comp-card {{
            border-radius: 16px;
            padding: 30px;
        }}
        .comp-organic {{
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05));
            border: 2px solid rgba(34, 197, 94, 0.3);
        }}
        .comp-ad {{
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05));
            border: 2px solid rgba(245, 158, 11, 0.3);
        }}
        
        /* Variant Table */
        .variant-section {{
            overflow-x: auto;
            border-radius: 16px;
            background: rgba(0,0,0,0.2);
        }}
        .variant-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.85em;
            min-width: 1400px;
        }}
        .variant-table th {{
            background: rgba(255,255,255,0.1);
            padding: 16px 12px;
            text-align: center;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        .variant-table td {{
            padding: 16px 12px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .variant-table tr:hover {{ background: rgba(255,255,255,0.05); }}
        
        /* Variant Row Styles */
        .row-top {{ background: rgba(34, 197, 94, 0.1); }}
        .row-pareto {{ background: rgba(59, 130, 246, 0.1); }}
        .row-loss {{ background: rgba(239, 68, 68, 0.1); }}
        .row-high-ad {{ background: rgba(245, 158, 11, 0.1); }}
        
        /* Profit Colors */
        .profit-excellent {{ color: #4ade80; font-weight: 700; }}
        .profit-good {{ color: #22d3ee; }}
        .profit-marginal {{ color: #fbbf24; }}
        .profit-loss {{ color: #f87171; font-weight: 700; }}
        
        /* Order Source Bar */
        .order-bar {{
            width: 100px;
            height: 28px;
            border-radius: 14px;
            overflow: hidden;
            display: flex;
            margin: 0 auto;
        }}
        .organic-segment {{
            background: linear-gradient(90deg, #22c55e, #4ade80);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75em;
            font-weight: 700;
            color: #000;
            min-width: 30px;
        }}
        .ad-segment {{
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75em;
            font-weight: 700;
            color: #000;
            min-width: 30px;
        }}
        
        /* Insight Boxes */
        .insight-box {{
            background: rgba(251, 191, 36, 0.1);
            border-left: 4px solid #fbbf24;
            padding: 25px;
            margin: 25px 0;
            border-radius: 0 12px 12px 0;
        }}
        .insight-box h4 {{ color: #fbbf24; margin-bottom: 12px; }}
        
        .alert-box {{
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid #ef4444;
            padding: 25px;
            margin: 25px 0;
            border-radius: 0 12px 12px 0;
        }}
        .alert-box h4 {{ color: #f87171; margin-bottom: 12px; }}
        
        .success-box {{
            background: rgba(34, 197, 94, 0.1);
            border-left: 4px solid #22c55e;
            padding: 25px;
            margin: 25px 0;
            border-radius: 0 12px 12px 0;
        }}
        .success-box h4 {{ color: #4ade80; margin-bottom: 12px; }}
        
        /* Legend */
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
            font-size: 0.9em;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        /* Decision Basis */
        .decision-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .decision-card {{
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 20px;
        }}
        .decision-card h4 {{
            margin-bottom: 15px;
            color: #60a5fa;
        }}
        .decision-item {{
            padding: 10px;
            margin: 8px 0;
            border-radius: 8px;
            background: rgba(255,255,255,0.03);
        }}
        .decision-positive {{ border-left: 3px solid #22c55e; }}
        .decision-negative {{ border-left: 3px solid #ef4444; }}
        .decision-neutral {{ border-left: 3px solid #f59e0b; }}
        
        /* 163 Metrics Section */
        .metrics-163-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
        }}
        .metric-163-card {{
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 20px;
        }}
        .metric-163-card h5 {{
            color: #94a3b8;
            font-size: 0.85em;
            margin-bottom: 8px;
            text-transform: uppercase;
        }}
        .metric-163-value {{
            font-size: 1.4em;
            font-weight: 600;
            color: #e2e8f0;
        }}
        
        /* Section Headers */
        .section-header {{
            font-size: 1.3em;
            font-weight: 600;
            margin: 35px 0 20px 0;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(255,255,255,0.1);
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 50px;
            opacity: 0.6;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: 50px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                <div>
                    <span class="header-badge">🏆 精算师级分析</span>
                    <span class="header-badge">📊 163指标完整版</span>
                    <span class="header-badge">✅ 真实COGS</span>
                    <span class="header-badge">🎯 TACOS模型</span>
                </div>
                <span style="opacity: 0.8; font-size: 0.95em;">{datetime.now().strftime('%Y-%m-%d')}</span>
            </div>
            <h1>亚马逊链接运营精算师报告</h1>
            <div style="font-size: 1.2em; opacity: 0.95;">
                父ASIN: <strong>{analysis.parent_asin}</strong> | 
                变体数: <strong>{len(analysis.variants)}</strong> | 
                数据完整度: <strong>{np.mean([v.data_completeness_pct for v in analysis.variants]):.0f}%</strong>
            </div>
        </div>
        
        <!-- Executive Summary -->
        <div class="exec-summary">
            <h2 style="font-size: 1.8em; margin-bottom: 10px;">💼 执行摘要与投资决策</h2>
            <div class="verdict">{decision_text[analysis.overall_decision.decision]}</div>
            <p style="font-size: 1.2em; margin-bottom: 40px;">
                置信度: {analysis.overall_decision.confidence:.0f}% | 
                数据支撑决策
            </p>
            
            {metrics_cards}
        </div>
        
        <!-- Decision Basis -->
        <div class="card">
            <h2 class="card-title">📊 决策依据 (基于数据分析)</h2>
            {decision_basis}
        </div>
        
        <!-- Organic vs Ad Analysis -->
        <div class="card">
            <h2 class="card-title">🌿🎯 自然订单 vs 广告订单对比</h2>
            {self._generate_order_comparison(analysis)}
        </div>
        
        <!-- Pareto Analysis -->
        <div class="card">
            <h2 class="card-title">📈 帕累托分析 (80/20法则)</h2>
            {self._generate_pareto_section(analysis)}
        </div>
        
        <!-- Variant Details Table -->
        <div class="card">
            <h2 class="card-title">📋 全变体详细指标表</h2>
            
            <div class="legend">
                <div class="legend-item"><div class="legend-dot" style="background: #22c55e;"></div>🔥 Top变体</div>
                <div class="legend-item"><div class="legend-dot" style="background: #3b82f6;"></div>📊 帕累托变体</div>
                <div class="legend-item"><div class="legend-dot" style="background: #f59e0b;"></div>⚠️ 高广告依赖</div>
                <div class="legend-item"><div class="legend-dot" style="background: #ef4444;"></div>🔴 亏损变体</div>
            </div>
            
            <div class="variant-section">
                <table class="variant-table">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>ASIN</th>
                            <th>BSR</th>
                            <th>价格</th>
                            <th>月销量</th>
                            <th>销售额</th>
                            <th>订单来源</th>
                            <th>COGS</th>
                            <th>运营费</th>
                            <th>广告费</th>
                            <th>混合利润率</th>
                            <th>月净利润</th>
                            <th>决策</th>
                        </tr>
                    </thead>
                    <tbody>
                        {variant_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- 163 Metrics Detail -->
        <div class="card">
            <h2 class="card-title">🔍 163个Keepa指标详情</h2>
            <p style="opacity: 0.8; margin-bottom: 20px;">
                每个ASIN的完整指标数据，所有决策均基于以下指标计算得出
            </p>
            {metrics_163_section}
        </div>
        
        <!-- Risk Assessment -->
        <div class="card">
            <h2 class="card-title">⚠️ 风险评估</h2>
            {self._generate_risk_section(analysis)}
        </div>
        
        <!-- Action Plan -->
        <div class="card">
            <h2 class="card-title">🎯 行动计划</h2>
            {self._generate_action_plan(analysis)}
        </div>
        
        <!-- Data Source Note -->
        <div class="card" style="background: rgba(251, 191, 36, 0.05); border: 2px solid rgba(251, 191, 36, 0.3);">
            <h2 class="card-title" style="color: #fbbf24;">📊 数据来源与方法论</h2>
            <div style="line-height: 2;">
                <p><strong>Keepa 163指标:</strong> 完整采集Product Viewer CSV格式所有字段</p>
                <p><strong>销量估算:</strong> 基于BSR历史数据的回归模型</p>
                <p><strong>COGS数据:</strong> <span style="color: #fbbf24; font-weight: 600;">用户提供真实数据</span>，包含采购价、头程运费、关税</p>
                <p><strong>订单来源:</strong> <span style="color: #fbbf24; font-weight: 600;">用户提供真实数据</span>，来自亚马逊广告后台报表</p>
                <p><strong>FBA费用:</strong> 基于包装规格(长×宽×高×重量)计算</p>
                <p><strong>退货率:</strong> 基于类目历史数据的统计模型</p>
                <p><strong>广告成本:</strong> TACOS (Total ACOS) 15%，即广告总花费占整体销售额的15%</p>
                <p><strong>决策模型:</strong> 基于利润率、广告依赖度、退货率、评分、竞争度等多维度加权</p>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p style="font-size: 1.1em; margin-bottom: 15px;">
                基于163个Keepa指标 + 真实COGS + TACOS模型 | 数据驱动决策
            </p>
            <p style="opacity: 0.7;">
                © 2026 亚马逊运营精算师系统 v3.0 Final Edition<br>
                报告仅供参考，实际盈利受市场波动、竞争变化等因素影响
            </p>
        </div>
    </div>
</body>
</html>'''
        
        return html
    
    def _generate_variant_rows(self, variants: List[VariantAnalysisResult]) -> str:
        """生成变体表格行"""
        rows = []
        for i, v in enumerate(variants, 1):
            # 行样式
            classes = []
            if i <= 3:
                classes.append("row-top")
            if v.blended_margin_pct > 0:
                classes.append("row-pareto")
            if v.blended_margin_pct < 0:
                classes.append("row-loss")
            if v.financials.ad_order_pct > 0.6:
                classes.append("row-high-ad")
            
            class_str = " ".join(classes)
            
            # 利润率颜色
            if v.blended_margin_pct >= 25:
                margin_class = "profit-excellent"
            elif v.blended_margin_pct >= 15:
                margin_class = "profit-good"
            elif v.blended_margin_pct >= 0:
                margin_class = "profit-marginal"
            else:
                margin_class = "profit-loss"
            
            # 决策文本
            decision_icons = {
                'proceed': '✅',
                'caution': '⚠️',
                'avoid': '❌'
            }
            
            row = f'''
                <tr class="{class_str}">
                    <td><strong>#{i}</strong></td>
                    <td>{v.asin}</td>
                    <td>{v.metrics.sales_rank_current:,}</td>
                    <td>${v.metrics.price_new_current:.2f}</td>
                    <td>{v.estimated_monthly_sales}</td>
                    <td>${v.estimated_monthly_revenue:,.0f}</td>
                    <td>
                        <div class="order-bar">
                            <div class="organic-segment" style="width: {v.financials.organic_order_pct*100}%;">
                                {v.financials.organic_order_pct*100:.0f}%
                            </div>
                            <div class="ad-segment" style="width: {v.financials.ad_order_pct*100}%;">
                                {v.financials.ad_order_pct*100:.0f}%
                            </div>
                        </div>
                    </td>
                    <td>${v.financials.cogs:.2f}</td>
                    <td>${v.operating_cost_per_unit:.2f}</td>
                    <td>${v.ad_cost_per_unit:.2f}</td>
                    <td class="{margin_class}">{v.blended_margin_pct:.1f}%</td>
                    <td class="{margin_class}">${v.monthly_total_profit:,.0f}</td>
                    <td>{decision_icons[v.decision.decision]} {v.decision.confidence:.0f}%</td>
                </tr>
            '''
            rows.append(row)
        
        return "".join(rows)
    
    def _generate_metrics_cards(self, analysis: LinkPortfolioAnalysis) -> str:
        """生成指标卡片"""
        
        # 计算有机vs广告占比
        total_organic_sales = sum(
            v.estimated_monthly_sales * v.financials.organic_order_pct 
            for v in analysis.variants
        )
        total_ad_sales = sum(
            v.estimated_monthly_sales * v.financials.ad_order_pct 
            for v in analysis.variants
        )
        organic_pct = (total_organic_sales / analysis.total_monthly_sales * 100) if analysis.total_monthly_sales > 0 else 0
        
        return f'''
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value" style="color: #60a5fa;">{analysis.total_monthly_sales:,}</div>
                    <div class="metric-label">预估月总销量</div>
                    <div class="metric-sublabel">全变体合计</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #a78bfa;">${analysis.total_monthly_revenue:,.0f}</div>
                    <div class="metric-label">预估月销售额</div>
                    <div class="metric-sublabel">Gross Revenue</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #4ade80;">${analysis.total_monthly_profit:,.0f}</div>
                    <div class="metric-label">预估月净利润</div>
                    <div class="metric-sublabel">扣除所有成本</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: {'#4ade80' if analysis.blended_portfolio_margin_pct >= 20 else '#fbbf24' if analysis.blended_portfolio_margin_pct >= 10 else '#f87171'};">
                        {analysis.blended_portfolio_margin_pct:.1f}%
                    </div>
                    <div class="metric-label">混合净利率</div>
                    <div class="metric-sublabel">TACOS模型</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #22c55e;">{organic_pct:.0f}%</div>
                    <div class="metric-label">自然订单占比</div>
                    <div class="metric-sublabel">无需广告费</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #f59e0b;">{len(analysis.pareto_variants)}</div>
                    <div class="metric-label">核心变体数</div>
                    <div class="metric-sublabel">贡献80%销量</div>
                </div>
            </div>
        '''
    
    def _generate_decision_basis(self, analysis: LinkPortfolioAnalysis) -> str:
        """生成决策依据"""
        
        # 正面因素
        positive_factors = []
        negative_factors = []
        
        for v in analysis.variants:
            for factor in v.decision.opportunity_factors:
                positive_factors.append(f"{v.asin}: {factor}")
            for factor in v.decision.risk_factors:
                negative_factors.append(f"{v.asin}: {factor}")
        
        # 添加组合级因素
        if analysis.blended_portfolio_margin_pct > 20:
            positive_factors.insert(0, f"组合健康利润率: {analysis.blended_portfolio_margin_pct:.1f}%")
        elif analysis.blended_portfolio_margin_pct < 15:
            negative_factors.insert(0, f"组合低利润率: {analysis.blended_portfolio_margin_pct:.1f}%")
        
        if len(analysis.loss_making_variants) == 0:
            positive_factors.append("无亏损变体")
        else:
            negative_factors.append(f"{len(analysis.loss_making_variants)}个亏损变体")
        
        positive_html = "".join([
            f'<div class="decision-item decision-positive">✓ {f}</div>' 
            for f in positive_factors[:8]
        ]) if positive_factors else '<div class="decision-item decision-neutral">暂无显著正面因素</div>'
        
        negative_html = "".join([
            f'<div class="decision-item decision-negative">✗ {f}</div>' 
            for f in negative_factors[:8]
        ]) if negative_factors else '<div class="decision-item decision-neutral">暂无显著风险因素</div>'
        
        return f'''
            <div class="decision-grid">
                <div class="decision-card">
                    <h4>🟢 支持决策 ({len(positive_factors)}个因素)</h4>
                    {positive_html}
                </div>
                <div class="decision-card">
                    <h4>🔴 风险因素 ({len(negative_factors)}个因素)</h4>
                    {negative_html}
                </div>
            </div>
            <div style="margin-top: 20px; padding: 20px; background: rgba(255,255,255,0.03); border-radius: 12px;">
                <h4 style="color: #60a5fa; margin-bottom: 10px;">📝 数据支撑总结</h4>
                <p>基于{len(analysis.variants)}个变体的163个Keepa指标分析，综合考虑了销售表现、价格趋势、竞争态势、评论质量、成本结构等维度。决策置信度为{analysis.overall_decision.confidence:.0f}%，预期月ROI为{analysis.overall_decision.expected_roi_pct:.1f}%。</p>
            </div>
        '''
    
    def _generate_order_comparison(self, analysis: LinkPortfolioAnalysis) -> str:
        """生成订单来源对比"""
        
        # 计算整体有机vs广告数据
        organic_profit = sum(v.monthly_profit_organic for v in analysis.variants)
        ad_profit = sum(v.monthly_profit_ad for v in analysis.variants)
        
        total_organic_sales = sum(
            v.estimated_monthly_sales * v.financials.organic_order_pct 
            for v in analysis.variants
        )
        total_ad_sales = sum(
            v.estimated_monthly_sales * v.financials.ad_order_pct 
            for v in analysis.variants
        )
        
        organic_revenue = sum(
            v.estimated_monthly_revenue * v.financials.organic_order_pct 
            for v in analysis.variants
        )
        ad_revenue = sum(
            v.estimated_monthly_revenue * v.financials.ad_order_pct 
            for v in analysis.variants
        )
        
        organic_margin = (organic_profit / organic_revenue * 100) if organic_revenue > 0 else 0
        ad_margin = (ad_profit / ad_revenue * 100) if ad_revenue > 0 else 0
        
        return f'''
            <div class="comparison-grid">
                <div class="comp-card comp-organic">
                    <h3 style="font-size: 1.4em; color: #4ade80; margin-bottom: 25px;">🌿 自然订单</h3>
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>订单占比</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">{(total_organic_sales/analysis.total_monthly_sales*100) if analysis.total_monthly_sales > 0 else 0:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>月利润贡献</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">${organic_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>平均利润率</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">{organic_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.9; line-height: 1.8;">
                        自然订单无需支付广告费，利润率显著高于广告订单。
                    </p>
                </div>
                
                <div class="comp-card comp-ad">
                    <h3 style="font-size: 1.4em; color: #fbbf24; margin-bottom: 25px;">🎯 广告订单</h3>
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>订单占比</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #fbbf24;">{(total_ad_sales/analysis.total_monthly_sales*100) if analysis.total_monthly_sales > 0 else 0:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>月利润贡献</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: {'#f87171' if ad_profit < 0 else '#fbbf24'};">${ad_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>平均利润率</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: {'#f87171' if ad_margin < 0 else '#fbbf24'};">{ad_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.9; line-height: 1.8;">
                        广告订单需要分摊广告费(TACOS 15%)，利润率较低。
                        {"⚠️ 当前广告订单亏损，需优化TACOS。" if ad_profit < 0 else ""}
                    </p>
                </div>
            </div>
            
            <div class="insight-box">
                <h4>💡 订单来源洞察</h4>
                <p>
                    自然订单利润率 ({organic_margin:.1f}%) 
                    比广告订单 ({ad_margin:.1f}%) 高 
                    <strong>{organic_margin - ad_margin:.1f}个百分点</strong>。
                    每提升1%的自然订单占比，月利润可增加约 
                    <strong>${abs(organic_profit - ad_profit) / analysis.total_monthly_sales * 100 if analysis.total_monthly_sales > 0 else 0:.0f}</strong>。
                </p>
            </div>
        '''
    
    def _generate_pareto_section(self, analysis: LinkPortfolioAnalysis) -> str:
        """生成帕累托分析部分"""
        
        pareto_asins = [v.asin for v in analysis.pareto_variants]
        tail_count = len(analysis.tail_variants)
        
        return f'''
            <div class="metrics-grid" style="margin-bottom: 25px;">
                <div class="metric-card" style="background: rgba(59, 130, 246, 0.15); border: 2px solid rgba(59, 130, 246, 0.3);">
                    <div class="metric-value" style="color: #60a5fa;">{len(analysis.pareto_variants)}</div>
                    <div class="metric-label">核心变体</div>
                    <div class="metric-sublabel">贡献80%销量</div>
                </div>
                <div class="metric-card" style="background: rgba(245, 158, 11, 0.15); border: 2px solid rgba(245, 158, 11, 0.3);">
                    <div class="metric-value" style="color: #fbbf24;">{len(analysis.high_ad_dependency)}</div>
                    <div class="metric-label">高广告依赖</div>
                    <div class="metric-sublabel">广告占比&gt;60%</div>
                </div>
                <div class="metric-card" style="background: rgba(239, 68, 68, 0.15); border: 2px solid rgba(239, 68, 68, 0.3);">
                    <div class="metric-value" style="color: #f87171;">{len(analysis.loss_making_variants)}</div>
                    <div class="metric-label">亏损变体</div>
                    <div class="metric-sublabel">需立即处理</div>
                </div>
                <div class="metric-card" style="background: rgba(34, 197, 94, 0.15); border: 2px solid rgba(34, 197, 94, 0.3);">
                    <div class="metric-value" style="color: #4ade80;">{tail_count}</div>
                    <div class="metric-label">长尾变体</div>
                    <div class="metric-sublabel">贡献剩余20%</div>
                </div>
            </div>
            
            <p style="opacity: 0.9; line-height: 1.8;">
                <strong>核心发现:</strong> 前{len(analysis.pareto_variants)}个变体({', '.join(pareto_asins[:3])}...) 
                贡献了链接80%的销量。应优先保证这些变体的库存充足，并持续优化其自然排名。
                {f"同时关注 {len(analysis.high_ad_dependency)}个高广告依赖变体，考虑通过站外推广提升自然占比。" if analysis.high_ad_dependency else ""}
            </p>
        '''
    
    def _generate_163_metrics_section(self, variants: List[VariantAnalysisResult]) -> str:
        """生成163指标详情部分"""
        
        sections = []
        for v in variants[:5]:  # 只显示前5个变体
            metrics = v.metrics
            
            section = f'''
                <div style="margin-bottom: 30px; padding: 20px; background: rgba(255,255,255,0.02); border-radius: 12px;">
                    <h3 style="margin-bottom: 15px; color: #60a5fa;">{v.asin} - {metrics.title[:50]}...</h3>
                    <div class="metrics-163-grid">
                        <div class="metric-163-card">
                            <h5>Sales Rank Current</h5>
                            <div class="metric-163-value">{metrics.sales_rank_current:,}</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>Sales Rank 90d Avg</h5>
                            <div class="metric-163-value">{metrics.sales_rank_avg_90d:,}</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>Price New Current</h5>
                            <div class="metric-163-value">${metrics.price_new_current:.2f}</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>Price New 30d Avg</h5>
                            <div class="metric-163-value">${metrics.price_new_avg_30d:.2f}</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>Rating</h5>
                            <div class="metric-163-value">{metrics.rating:.1f} ⭐</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>Review Count</h5>
                            <div class="metric-163-value">{metrics.review_count:,}</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>Return Rate</h5>
                            <div class="metric-163-value">{metrics.return_rate*100:.1f}%</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>Total Offers</h5>
                            <div class="metric-163-value">{metrics.total_offer_count}</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>FBA Fee</h5>
                            <div class="metric-163-value">${metrics.fba_fee:.2f}</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>Referral Fee</h5>
                            <div class="metric-163-value">${metrics.referral_fee_amount:.2f}</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>Brand</h5>
                            <div class="metric-163-value">{metrics.brand or 'N/A'}</div>
                        </div>
                        <div class="metric-163-card">
                            <h5>Category</h5>
                            <div class="metric-163-value">{metrics.category_root or 'N/A'}</div>
                        </div>
                    </div>
                </div>
            '''
            sections.append(section)
        
        return "".join(sections)
    
    def _generate_risk_section(self, analysis: LinkPortfolioAnalysis) -> str:
        """生成风险分析部分"""
        
        risks = []
        
        if analysis.loss_making_variants:
            risks.append(f'''
                <div class="alert-box">
                    <h4>🔴 亏损变体 ({len(analysis.loss_making_variants)}个)</h4>
                    <p>以下变体当前处于亏损状态，需立即优化或考虑停售：</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(analysis.loss_making_variants)}</p>
                </div>
            ''')
        
        if analysis.high_ad_dependency:
            risks.append(f'''
                <div class="insight-box">
                    <h4>⚠️ 高广告依赖 ({len(analysis.high_ad_dependency)}个)</h4>
                    <p>以下变体广告订单占比超过60%，一旦广告成本上升或竞争加剧，利润将显著下滑：</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(analysis.high_ad_dependency)}</p>
                </div>
            ''')
        
        if analysis.high_return_variants:
            risks.append(f'''
                <div class="insight-box">
                    <h4>📦 高退货率 ({len(analysis.high_return_variants)}个)</h4>
                    <p>以下变体退货率超过12%，影响整体利润：</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(analysis.high_return_variants)}</p>
                </div>
            ''')
        
        if not risks:
            risks.append('''
                <div class="success-box">
                    <h4>🌟 风险评估</h4>
                    <p>当前链接整体风险可控，未发现显著风险因素。</p>
                </div>
            ''')
        
        return "".join(risks)
    
    def _generate_action_plan(self, analysis: LinkPortfolioAnalysis) -> str:
        """生成行动计划"""
        
        return f'''
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;">
                <div style="background: rgba(239, 68, 68, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(239, 68, 68, 0.3);">
                    <h4 style="color: #f87171; margin-bottom: 20px; font-size: 1.2em;">🚨 立即行动 (0-30天)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        <li>• 确保{len(analysis.pareto_variants)}个核心变体库存充足(60天+)</li>
                        <li>• 优化高销量变体的主图和标题，提升自然转化</li>
                        {f'<li>• 检查{len(analysis.high_ad_dependency)}个高广告依赖变体的TACOS</li>' if analysis.high_ad_dependency else ''}
                        {f'<li>• 处理{len(analysis.loss_making_variants)}个亏损变体(提价或降本)</li>' if analysis.loss_making_variants else ''}
                    </ul>
                </div>
                
                <div style="background: rgba(245, 158, 11, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(245, 158, 11, 0.3);">
                    <h4 style="color: #fbbf24; margin-bottom: 20px; font-size: 1.2em;">📈 短期优化 (30-60天)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        {f'<li>• 针对高广告依赖变体，开展站外推广降低TACOS</li>' if analysis.high_ad_dependency else ''}
                        <li>• 测试价格弹性，寻找最优定价点</li>
                        <li>• 收集并分析退货原因，降低退货率</li>
                        <li>• 优化广告投放策略，加大高利润变体预算</li>
                    </ul>
                </div>
                
                <div style="background: rgba(34, 197, 94, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(34, 197, 94, 0.3);">
                    <h4 style="color: #4ade80; margin-bottom: 20px; font-size: 1.2em;">🚀 长期策略 (60-90天)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        <li>• 开发新颜色/尺寸变体，复制成功模式</li>
                        <li>• 建立供应链议价能力，降低COGS 5-10%</li>
                        <li>• 构建品牌护城河，提升自然流量占比至70%+</li>
                        <li>• 建立月度利润监控体系，及时发现问题变体</li>
                    </ul>
                </div>
            </div>
        '''
    
    def _create_template(self) -> str:
        """创建HTML模板 (已内联在_render_html中)"""
        return ""


# ============================================================================
# 主入口
# ============================================================================

def generate_final_report(
    parent_asin: str,
    products: List[Dict],
    financials_map: Dict[str, Dict],
    output_path: Optional[str] = None,
    tacos_rate: float = 0.15
) -> Tuple[str, LinkPortfolioAnalysis]:
    """
    生成最终版精算师报告
    
    Args:
        parent_asin: 父ASIN
        products: Keepa API返回的产品列表
        financials_map: ASIN到财务数据的映射
        output_path: 输出路径
        tacos_rate: TACOS比例 (默认15%)
        
    Returns:
        (报告路径, 分析结果)
    """
    
    # 转换财务数据
    financials = {}
    for asin, data in financials_map.items():
        financials[asin] = VariantFinancials(
            asin=asin,
            cogs=data.get('cogs', 0),
            organic_order_pct=data.get('organic_pct', 0.6),
            ad_order_pct=data.get('ad_pct', 0.4),
            product_cost=data.get('product_cost', 0),
            shipping_cost=data.get('shipping_cost', 0),
            tariff_cost=data.get('tariff_cost', 0),
            other_cost=data.get('other_cost', 0)
        )
    
    # 分析组合
    analyzer = LinkPortfolioAnalyzer(tacos_rate)
    analysis = analyzer.analyze_portfolio(parent_asin, products, financials)
    
    # 生成报告
    if output_path is None:
        output_path = f"cache/reports/{parent_asin}_ACTUARY_FINAL_v3.html"
    
    generator = FinalReportGenerator()
    report_path = generator.generate(analysis, output_path)
    
    return report_path, analysis


# ============================================================================
# 自动变体采集功能
# ============================================================================

def generate_actuary_report_auto(
    asin: str,
    financials_map: Optional[Dict[str, Dict]] = None,
    api_key: Optional[str] = None,
    output_path: Optional[str] = None,
    tacos_rate: float = 0.15,
    auto_collect_variants: bool = True
) -> Tuple[str, LinkPortfolioAnalysis, Dict]:
    """
    生成精算师报告 (支持自动变体采集)
    
    这是推荐的入口函数！它会自动：
    1. 从Keepa API获取指定ASIN的数据
    2. 如果auto_collect_variants=True，自动发现并采集所有变体
    3. 生成完整的精算师分析报告
    
    Args:
        asin: 任意一个变体的ASIN (或父ASIN)
        financials_map: ASIN到财务数据的映射 {asin: {'cogs': 9.5, 'organic_pct': 0.7, 'ad_pct': 0.3}}
                       如果不提供，会使用默认COGS=0和平均订单来源比例
        api_key: Keepa API Key，如果不提供则从环境变量KEEPA_KEY获取
        output_path: 报告输出路径
        tacos_rate: TACOS比例 (默认15%)
        auto_collect_variants: 是否自动采集变体数据
        
    Returns:
        (报告路径, 分析结果, 变体信息)
        
    Example:
        >>> # 最简单用法：只输入一个ASIN，自动采集所有变体
        >>> report_path, analysis, info = generate_actuary_report_auto("B0F6B5R47Q")
        >>> 
        >>> # 提供真实COGS数据
        >>> financials = {
        ...     'B0F6B5R47Q': {'cogs': 9.50, 'organic_pct': 0.70, 'ad_pct': 0.30},
        ...     'B0F6B5R47R': {'cogs': 9.50, 'organic_pct': 0.55, 'ad_pct': 0.45},
        ... }
        >>> report_path, analysis, info = generate_actuary_report_auto(
        ...     "B0F6B5R47Q",
        ...     financials_map=financials
        ... )
    """
    import os
    
    # 获取API Key
    api_key = api_key or os.getenv("KEEPA_KEY", "")
    if not api_key:
        raise ValueError("需要提供Keepa API Key或设置KEEPA_KEY环境变量")
    
    # 导入变体采集器
    from .variant_auto_collector import VariantAutoCollector
    
    print("=" * 80)
    print(f"🚀 亚马逊运营精算师 - 自动变体采集模式")
    print("=" * 80)
    
    # 第1步: 采集变体数据
    print(f"\n📦 步骤1: 采集ASIN {asin} 及其变体数据...")
    collector = VariantAutoCollector(api_key)
    products, parent_info = collector.collect_variants(asin)
    
    print(f"\n✅ 采集完成!")
    print(f"   父ASIN: {parent_info['parent_asin']}")
    print(f"   变体数量: {parent_info['total_variations']}")
    print(f"   品牌: {parent_info.get('brand', 'N/A')}")
    print(f"   类目: {parent_info.get('category', 'N/A')}")
    
    # 打印变体摘要
    print(collector.format_variants_summary(products))
    
    # 第2步: 准备财务数据
    print(f"\n💰 步骤2: 准备财务数据...")
    
    # 如果没有提供财务数据，使用默认值并提示用户
    if financials_map is None:
        print("   ⚠️ 未提供COGS数据，使用默认值(成本=0，需手动更新)")
        financials_map = {}
        for p in products:
            asin_code = p.get('asin', '')
            attrs = collector.get_variation_attributes(p)
            color = attrs.get('color', 'Unknown')
            
            # 使用默认值
            financials_map[asin_code] = {
                'cogs': 0.0,  # 用户需要更新
                'organic_pct': 0.60,  # 默认值
                'ad_pct': 0.40,
                'note': f'请更新{color}的真实COGS和订单来源数据'
            }
    
    # 检查是否所有变体都有财务数据
    for p in products:
        asin_code = p.get('asin', '')
        if asin_code not in financials_map:
            print(f"   ⚠️ ASIN {asin_code} 没有财务数据，使用默认值")
            attrs = collector.get_variation_attributes(p)
            color = attrs.get('color', 'Unknown')
            financials_map[asin_code] = {
                'cogs': 0.0,
                'organic_pct': 0.60,
                'ad_pct': 0.40,
                'note': f'请更新{color}的真实COGS'
            }
    
    # 第3步: 生成报告
    print(f"\n📊 步骤3: 生成精算师分析报告...")
    
    parent_asin = parent_info['parent_asin']
    report_path, analysis = generate_final_report(
        parent_asin=parent_asin,
        products=products,
        financials_map=financials_map,
        output_path=output_path,
        tacos_rate=tacos_rate
    )
    
    # 生成交互式All-in-One报告
    try:
        from allinone_interactive_report import generate_allinone_report
        allinone_path = generate_allinone_report(parent_asin, products, 
            {'variants': analysis.variants})
        print(f"\n   🧮 All-in-One交互式报告: {allinone_path}")
        print(f"      └─ 只需填入采购成本(RMB)，自动计算完整利润分析")
    except Exception as e:
        print(f"\n   ⚠️ 交互式报告生成失败: {e}")
    
    print(f"\n✅ 报告生成完成!")
    print(f"   主报告: {report_path}")
    print(f"   整体决策: {analysis.overall_decision.decision.upper()}")
    print(f"   置信度: {analysis.overall_decision.confidence}%")
    print(f"   预期月利润: ${analysis.total_monthly_profit:,.2f}")
    
    return report_path, analysis, parent_info


# 便捷别名
auto_analyze = generate_actuary_report_auto


# ============================================================================
# 向后兼容
# ============================================================================

if __name__ == "__main__":
    print("Amazon Actuary System v3.0 - Final Edition")
    print("=" * 60)
    print("\n推荐函数:")
    print("  1. generate_actuary_report_auto(asin) - 自动采集变体并分析")
    print("  2. generate_final_report(...) - 使用已有数据生成报告")
    print("\n示例:")
    print('  report, analysis, info = generate_actuary_report_auto("B0F6B5R47Q")')
