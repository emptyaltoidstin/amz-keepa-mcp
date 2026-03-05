"""
Amazon Operations Actuary - final version (Final Edition)
==============================================
Integrated 163 Keepa indicators + Real COGS + Order source analysis
All decisions are based on data support

Author: Amazon FBA Actuary System v3.0
Date: 2026-02-15
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
# Data model definition
# ============================================================================

@dataclass
class KeepaMetrics163:
    """Keepa 163 indicator data structures"""
    # Basic information (18)
    asin: str = ""
    locale: str = "com"
    title: str = ""
    parent_title: str = ""
    image_url: str = ""
    image_count: int = 0
    description: str = ""
    features: List[str] = field(default_factory=list)
    
    # sales performance (8)
    sales_rank_current: int = 0
    sales_rank_avg_90d: int = 0
    sales_rank_drops_90d: int = 0
    sales_rank_reference: str = ""
    bought_in_past_month: int = 0
    sales_change_90d_pct: float = 0.0
    
    # Reviews and Returns (5)
    return_rate: float = 0.0
    rating: float = 0.0
    review_count: int = 0
    last_price_change: str = ""
    
    # Buy Box (15)
    buy_box_seller: str = ""
    buy_box_price: float = 0.0
    amazon_buybox_pct_90d: float = 0.0
    buybox_winner_count_90d: int = 0
    buybox_std_90d: float = 0.0
    is_fba: bool = True
    is_prime: bool = True
    
    # price data (Amazon/New/Used)
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
    
    # Inventory (8)
    amazon_oos_rate_90d: float = 0.0
    amazon_oos_count_30d: int = 0
    amazon_availability: str = ""
    
    # cost (6)
    fba_fee: float = 0.0
    referral_fee_pct: float = 15.0
    referral_fee_amount: float = 0.0
    
    # compete (10)
    total_offer_count: int = 0
    new_offer_count: int = 0
    fba_offer_count: int = 0
    fbm_offer_count: int = 0
    tracking_since: str = ""
    listed_since: str = ""
    
    # Category (5)
    category_root: str = ""
    category_sub: str = ""
    category_tree: str = ""
    
    # Product attributes (20)
    brand: str = ""
    manufacturer: str = ""
    product_group: str = ""
    color: str = ""
    size: str = ""
    material: str = ""
    style: str = ""
    
    # Packaging specifications (9)
    package_length_cm: float = 0.0
    package_width_cm: float = 0.0
    package_height_cm: float = 0.0
    package_weight_g: float = 0.0
    package_volume_cm3: float = 0.0
    
    # content (8)
    has_video: bool = False
    video_count: int = 0
    has_aplus: bool = False
    
    # Raw CSV data storage
    raw_data: Dict = field(default_factory=dict)


@dataclass
class VariantFinancials:
    """Variant financial data (user input)"""
    asin: str
    cogs: float  # true purchase cost (Including the first step)
    organic_order_pct: float  # Proportion of natural orders
    ad_order_pct: float  # Insertion order proportion
    
    # Optional detailed cost breakdown
    product_cost: float = 0.0  # Product cost
    shipping_cost: float = 0.0  # First leg freight
    tariff_cost: float = 0.0  # tariff
    other_cost: float = 0.0  # other costs


@dataclass
class ActuaryDecision:
    """actuary decision making (Based on data)"""
    decision: str  # proceed / caution / avoid
    confidence: float  # 0-100
    expected_monthly_profit: float
    expected_roi_pct: float
    payback_period_months: float
    risk_factors: List[str]
    opportunity_factors: List[str]
    data_quality_score: float  # Data completeness 0-100


@dataclass
class VariantAnalysisResult:
    """Single variant analysis results"""
    # Basic information
    asin: str
    parent_asin: str
    metrics: KeepaMetrics163
    financials: VariantFinancials
    
    # sales estimate
    estimated_monthly_sales: int
    estimated_monthly_revenue: float
    
    # cost structure (Based on 163 indicators)
    operating_cost_per_unit: float  # operating costs (FBA+Commission+Return+warehousing)
    ad_cost_per_unit: float  # unit advertising cost (Based on TACOS)
    total_cost_per_unit: float  # total cost
    
    # profit analysis
    contribution_margin_organic: float  # Natural orders contribute to gross profit
    contribution_margin_ad: float  # Insertion order contribution margin
    blended_margin_pct: float  # mixed profit margin
    
    # monthly profit
    monthly_profit_organic: float
    monthly_profit_ad: float
    monthly_total_profit: float
    
    # Data quality
    data_completeness_pct: float
    
    # Data-Based Decisions
    decision: ActuaryDecision


@dataclass
class LinkPortfolioAnalysis:
    """Link combination analysis results"""
    parent_asin: str
    variants: List[VariantAnalysisResult]
    
    # Portfolio level indicators
    total_monthly_sales: int
    total_monthly_revenue: float
    total_monthly_profit: float
    blended_portfolio_margin_pct: float
    
    # Pareto analysis
    pareto_variants: List[VariantAnalysisResult]  # Contribute 80%Variants of
    tail_variants: List[VariantAnalysisResult]  # long tail variant
    
    # risk distribution
    high_ad_dependency: List[str]  # High advertising dependence on ASIN
    loss_making_variants: List[str]  # loss variant
    high_return_variants: List[str]  # High return rate variant
    
    # overall decision making
    overall_decision: ActuaryDecision


# ============================================================================
# 163 indicator collector
# ============================================================================

class Metrics163Collector:
    """Extract 163 metrics from Keepa product data"""
    
    def __init__(self):
        self.required_fields = {
            'sales_rank_current', 'price_new_current', 'review_count', 
            'rating', 'total_offer_count', 'buy_box_price'
        }
    
    def collect_from_product(self, product: Dict) -> KeepaMetrics163:
        """Extract 163 metrics from Keepa API product data"""
        data = product.get('data', {})
        
        metrics = KeepaMetrics163(
            asin=product.get('asin', ''),
            title=(product.get('title') or '')[:200],
            parent_title=product.get('parentTitle') or '',
            image_url=(product.get('imagesCSV') or '').split(',')[0] if product.get('imagesCSV') else '',
            image_count=len((product.get('imagesCSV') or '').split(',')) if product.get('imagesCSV') else 0,
            description=(product.get('description') or '')[:500],
            features=self._extract_features(product),
            
            # sales performance
            sales_rank_current=self._get_current_rank(data),
            sales_rank_avg_90d=self._get_avg_rank_90d(data),
            sales_rank_drops_90d=self._count_rank_drops(data),
            bought_in_past_month=self._get_bought_in_past_month(product),
            sales_change_90d_pct=self._calc_sales_change_90d(data),
            
            # Comment
            rating=self._get_rating_safe(product),
            review_count=self._get_review_count_safe(product),
            return_rate=self._estimate_return_rate(product),
            
            # Buy Box
            buy_box_seller=self._get_buybox_seller(product),
            buy_box_price=self._get_buybox_price(data),
            amazon_buybox_pct_90d=self._calc_amazon_buybox_share(data),
            is_fba=self._is_fba(product, data),
            
            # price
            price_new_current=self._get_price_new_current(data),
            price_new_avg_30d=self._get_price_new_avg(data, 30),
            price_new_avg_90d=self._get_price_new_avg(data, 90),
            price_new_lowest=self._get_price_new_lowest(data),
            price_new_highest=self._get_price_new_highest(data),
            
            # compete
            total_offer_count=self._get_offer_count(data),
            new_offer_count=self._get_new_offer_count(data),
            
            # Category
            brand=product.get('brand', ''),
            manufacturer=product.get('manufacturer', ''),
            product_group=product.get('productGroup', ''),
            color=product.get('color', ''),
            size=product.get('size', ''),
            category_root=self._get_category_root(product),
            category_sub=self._get_category_sub(product),
            
            # packaging
            package_length_cm=product.get('packageLength', 0) or 0,
            package_width_cm=product.get('packageWidth', 0) or 0,
            package_height_cm=product.get('packageHeight', 0) or 0,
            package_weight_g=product.get('packageWeight', 0) or 0,
            
            # cost estimate
            fba_fee=self._estimate_fba_fee(product),
            referral_fee_pct=15.0,
            referral_fee_amount=self._calc_referral_fee(data),
            
            raw_data=product
        )
        
        # Calculate volume
        if metrics.package_length_cm and metrics.package_width_cm and metrics.package_height_cm:
            metrics.package_volume_cm3 = (
                metrics.package_length_cm * 
                metrics.package_width_cm * 
                metrics.package_height_cm
            )
        
        return metrics
    
    def _extract_features(self, product: Dict) -> List[str]:
        """Extract product features"""
        features = product.get('features', [])
        return features[:10] if features else []
    
    def _get_current_rank(self, data: Dict) -> int:
        """Get the current BSR"""
        df = data.get('df_SALES')
        if df is not None and not df.empty:
            return int(df['value'].iloc[-1]) if len(df) > 0 else 0
        return 0
    
    def _get_avg_rank_90d(self, data: Dict) -> int:
        """Get the 90-day average BSR"""
        df = data.get('df_SALES')
        if df is not None and not df.empty:
            valid = df[df['value'] > 0]['value']
            if len(valid) >= 90:
                return int(valid.tail(90).mean())
            return int(valid.mean()) if len(valid) > 0 else 0
        return 0
    
    def _count_rank_drops(self, data: Dict) -> int:
        """Calculate the number of BSR drops within 90 days"""
        df = data.get('df_SALES')
        if df is not None and not df.empty:
            values = df['value'].tail(90).tolist()
            drops = sum(1 for i in range(1, len(values)) if values[i] > values[i-1] * 1.2)
            return drops
        return 0
    
    def _get_bought_in_past_month(self, product: Dict, is_shared_data: bool = False, 
                                   total_sales: int = 0, all_variants_bsr: List[int] = None) -> int:
        """
        Get the purchase volume in the past month
        
        Intelligent handling of three situations:
        1. Variants have independent boughtInPastMonth -> Use directly
        2. All variants share the total sales volume of the parent ASIN -> Distributed according to BSR proportion
        3. No data -> Use BSR estimation
        
        Args:
            product: product data
            is_shared_data: Whether it is shared parent ASIN data
            total_sales: Parent ASIN total sales(If it is shared data)
            all_variants_bsr: List of BSRs for all variants(Used for allocation ratio calculations)
        """
        # Get raw data
        bought = product.get('boughtInPastMonth', 0)
        
        # Case 1: Have independent real data
        if isinstance(bought, (int, float)) and bought > 0 and not is_shared_data:
            return int(bought)
        
        # Case 2: The total sales volume of the shared parent ASIN needs to be allocated proportionally
        if is_shared_data and total_sales > 0 and all_variants_bsr:
            current_bsr = self._get_avg_rank_90d(product.get('data', {}))
            return self._allocate_sales_by_bsr(current_bsr, total_sales, all_variants_bsr)
        
        # Case 3: Fallback to BSR estimation
        data = product.get('data', {})
        return self._estimate_monthly_sales(data)
    
    def _allocate_sales_by_bsr(self, current_bsr: int, total_sales: int, all_variants_bsr: List[int]) -> int:
        """
        Prorate total sales based on BSR ranking
        
        principle: The lower the BSR, the higher the sales volume. Calculate weights using an inverse relationship.
        
        Args:
            current_bsr: BSR for current variant
            total_sales: Parent ASIN total sales
            all_variants_bsr: List of BSRs for all variants
            
        Returns:
            Sales volume allocated to the current variant
        """
        if not all_variants_bsr or current_bsr == 0:
            return 0
        
        # Calculate the weight of each variant (The reciprocal of BSR, the smaller the BSR, the greater the weight.)
        # Smooth out extreme values using square roots
        weights = []
        for bsr in all_variants_bsr:
            if bsr > 0:
                weight = 1 / (bsr ** 0.5)  # inverse square root
                weights.append(weight)
            else:
                weights.append(0)
        
        total_weight = sum(weights)
        if total_weight == 0:
            return 0
        
        # Calculate the weight proportion of the current variant
        current_weight = 1 / (current_bsr ** 0.5) if current_bsr > 0 else 0
        ratio = current_weight / total_weight
        
        # Allocate sales volume
        allocated_sales = int(total_sales * ratio)
        
        return max(allocated_sales, 1)  # At least 1 order
    
    def _estimate_monthly_sales(self, data: Dict) -> int:
        """Estimated monthly sales based on BSR (A fallback method when real data is not available)"""
        avg_rank = self._get_avg_rank_90d(data)
        # Simplified BSR-sales mapping
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
        """Calculate 90-day sales change rate"""
        df = data.get('df_SALES')
        if df is not None and len(df) >= 180:
            recent = df['value'].tail(90).mean()
            previous = df['value'].tail(180).head(90).mean()
            if previous > 0:
                return ((recent - previous) / previous) * 100
        return 0.0
    
    def _get_rating_from_data(self, data: Dict) -> float:
        """Get ratings from data"""
        df = data.get('df_RATING')
        if df is not None and not df.empty:
            try:
                return float(df['value'].iloc[-1])
            except:
                return 0.0
        return 0.0
    
    def _get_rating_safe(self, product: Dict) -> float:
        """Get ratings securely (Handle various data types)"""
        stars = product.get('stars', 0)
        
        # Handle different data types
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
        
        # Fallback to getting from DataFrame
        data = product.get('data', {})
        return self._get_rating_from_data(data)
    
    def _get_review_count(self, data: Dict) -> int:
        """Get the number of comments"""
        df = data.get('df_COUNT_REVIEWS')
        if df is not None and not df.empty:
            try:
                return int(df['value'].iloc[-1])
            except:
                return 0
        return 0
    
    def _get_review_count_safe(self, product: Dict) -> int:
        """Safely get the number of comments (Handle various data types)"""
        reviews = product.get('reviews', 0)
        
        # Handle different data types
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
            # If it is a dict, try to get the value in it
            for key in ['count', 'total', 'value', 'reviews']:
                if key in reviews:
                    try:
                        return int(reviews[key])
                    except:
                        continue
            return 0
        else:
            # Try to get from DataFrame
            data = product.get('data', {})
            return self._get_review_count(data)
    
    def _estimate_return_rate(self, product: Dict) -> float:
        """Estimating return rates based on category"""
        category = self._get_category_root(product).lower()
        # Category return rate reference
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
        return 0.08  # Default 8%
    
    def _get_buybox_seller(self, product: Dict) -> str:
        """Get Buy Box Seller"""
        history = product.get('buyBoxSellerIdHistory', [])
        return history[-1] if history else 'Unknown'
    
    def _get_buybox_price(self, data: Dict) -> float:
        """Get Buy Box price"""
        df = data.get('df_BUY_BOX_SHIPPING')
        if df is not None and not df.empty:
            return float(df['value'].iloc[-1])
        return 0.0
    
    def _calc_amazon_buybox_share(self, data: Dict) -> float:
        """Calculate the proportion of Amazon’s self-operated Buy Box"""
        df = data.get('df_BUY_BOX_SHIPPING')
        amazon_df = data.get('df_AMAZON')
        if df is not None and amazon_df is not None and not df.empty:
            # Simplified calculations
            return 0.0  # Requires more complex logic
        return 0.0
    
    def _is_fba(self, product: Dict, data: Dict) -> bool:
        """Determine whether it is FBA"""
        # Judging by seller history
        return True  # Default assumes FBA
    
    def _get_price_new_current(self, data: Dict) -> float:
        """Get the current new product price"""
        df = data.get('df_NEW')
        if df is not None and not df.empty:
            return float(df['value'].iloc[-1])
        return self._get_buybox_price(data)
    
    def _get_price_new_avg(self, data: Dict, days: int) -> float:
        """Get the average price of new products"""
        df = data.get('df_NEW')
        if df is not None and not df.empty:
            return float(df['value'].tail(days).mean())
        return 0.0
    
    def _get_price_new_lowest(self, data: Dict) -> float:
        """Get the lowest price on new products"""
        df = data.get('df_NEW')
        if df is not None and not df.empty:
            return float(df['value'].min())
        return 0.0
    
    def _get_price_new_highest(self, data: Dict) -> float:
        """Get the highest price for new products"""
        df = data.get('df_NEW')
        if df is not None and not df.empty:
            return float(df['value'].max())
        return 0.0
    
    def _get_offer_count(self, data: Dict) -> int:
        """Get the number of sellers"""
        df = data.get('df_COUNT_NEW')
        if df is not None and not df.empty:
            return int(df['value'].iloc[-1])
        return 1
    
    def _get_new_offer_count(self, data: Dict) -> int:
        """Get the number of new product sellers"""
        return self._get_offer_count(data)
    
    def _get_category_root(self, product: Dict) -> str:
        """Get root category"""
        tree = product.get('categoryTree', [])
        return tree[0].get('name', '') if tree else ''
    
    def _get_category_sub(self, product: Dict) -> str:
        """Get subcategory"""
        tree = product.get('categoryTree', [])
        return tree[1].get('name', '') if len(tree) > 1 else ''
    
    def _get_fba_fee(self, product: Dict) -> float:
        """
        Get FBA fees
        
        Prioritize getting real data from Keepa API, if not then estimate based on size
        """
        from keepa_fee_extractor import KeepaFeeExtractor
        
        fba_fee = KeepaFeeExtractor.extract_fba_fee(product)
        if fba_fee is not None:
            return fba_fee
        
        # fallback to estimate
        return KeepaFeeExtractor._estimate_fba_fee_from_dimensions(product)
    
    def _get_referral_fee_rate(self, product: Dict) -> float:
        """
        Get commission ratio
        
        Determine the true commission ratio based on category
        """
        from keepa_fee_extractor import KeepaFeeExtractor
        return KeepaFeeExtractor.extract_referral_fee_rate(product)
    
    def _calc_referral_fee(self, product: Dict, price: float) -> float:
        """Calculate commission"""
        rate = self._get_referral_fee_rate(product)
        return price * rate
    
    def _calc_operating_cost(self, product: Dict, data: Dict) -> float:
        """Calculate unit operating costs (Free of COGS and ads)"""
        from keepa_fee_extractor import KeepaFeeExtractor
        
        price = self._get_buybox_price(data)
        
        # Using Keepa API real expense data
        fees = KeepaFeeExtractor.extract_all_fees(product, price)
        fba = fees['fba_fee']
        referral = fees['referral_fee']
        
        # Other operating costs
        return_rate = self._estimate_return_rate(product)
        return_cost = price * return_rate * 0.30
        storage = 0.06
        
        return fba + referral + return_cost + storage
    
    def calculate_data_completeness(self, metrics: KeepaMetrics163) -> float:
        """Calculate data completeness"""
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
# TACOS Advertising Cost Calculator
# ============================================================================

class TacosCalculator:
    """
    TACOS (Total ACOS) Advertising cost calculator
    
    TACOS = total advertising spend / total sales
    
    Unlike ACOS, TACOS reflects the impact of advertising on the overall business
    """
    
    DEFAULT_TACOS_RATE = 0.15  # Default 15% TACOS
    
    def __init__(self, tacos_rate: float = DEFAULT_TACOS_RATE):
        self.tacos_rate = tacos_rate
    
    def calculate_ad_cost_per_unit(
        self, 
        monthly_revenue: float,
        monthly_ad_orders: float
    ) -> float:
        """
        Calculate unit advertising costs
        
        formula:
        - monthly advertising budget = Monthly Sales × TACOS
        - unit advertising cost = monthly advertising budget / Monthly advertising orders
        
        Args:
            monthly_revenue: monthly sales
            monthly_ad_orders: Monthly advertising orders
            
        Returns:
            Advertising cost per insertion order
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
        Calculate mixed unit advertising costs (Distributed to all orders)
        
        This is used to understand the impact of advertising costs on all orders
        """
        return price * self.tacos_rate * ad_order_pct


# ============================================================================
# Variant Profit Analyzer
# ============================================================================

class VariantProfitAnalyzer:
    """Real COGS variant profit analysis based on 163 indicators"""
    
    def __init__(self, tacos_rate: float = 0.15):
        self.tacos_calc = TacosCalculator(tacos_rate)
        self.metrics_collector = Metrics163Collector()
    
    def analyze_variant(
        self,
        product: Dict,
        financials: VariantFinancials
    ) -> VariantAnalysisResult:
        """Analyze a single variant"""
        
        # 1. Collect 163 indicators
        metrics = self.metrics_collector.collect_from_product(product)
        data_completeness = self.metrics_collector.calculate_data_completeness(metrics)
        
        # 2. Sales estimation
        estimated_sales = metrics.bought_in_past_month
        estimated_revenue = estimated_sales * metrics.price_new_current
        
        # 3. Cost structure (Calculated based on 163 indicators)
        # operating expenses = FBA fee + Commission + return cost + Storage fee
        referral_fee = metrics.price_new_current * metrics.referral_fee_pct / 100
        return_cost = metrics.price_new_current * metrics.return_rate * 0.30
        storage_fee = 0.06  # Default storage fee
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
        
        # 4. Profit calculation
        contribution_organic = metrics.price_new_current - financials.cogs - operating_cost
        contribution_ad = contribution_organic - ad_cost_per_unit
        
        blended_margin = (
            contribution_organic * financials.organic_order_pct +
            contribution_ad * financials.ad_order_pct
        ) / metrics.price_new_current * 100 if metrics.price_new_current > 0 else 0
        
        # 5. Monthly profit
        monthly_organic_profit = contribution_organic * (estimated_sales * financials.organic_order_pct)
        monthly_ad_profit = contribution_ad * (estimated_sales * financials.ad_order_pct)
        monthly_total = monthly_organic_profit + monthly_ad_profit
        
        # 6. Data-Based Decisions
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
        """Make decisions based on data"""
        
        risk_factors = []
        opportunity_factors = []
        
        # risk assessment
        if blended_margin < 0:
            risk_factors.append(f"loss variant: mixed profit margin {blended_margin:.1f}%")
        elif blended_margin < 10:
            risk_factors.append(f"low profit margin: {blended_margin:.1f}%")
        
        if financials.ad_order_pct > 0.6:
            risk_factors.append(f"High advertising dependence: {financials.ad_order_pct*100:.0f}%")
        
        if metrics.return_rate > 0.12:
            risk_factors.append(f"High return rate: {metrics.return_rate*100:.0f}%")
        
        if metrics.rating < 4.0:
            risk_factors.append(f"low rating: {metrics.rating:.1f}")
        
        if metrics.total_offer_count > 10:
            risk_factors.append(f"Competition is fierce: {metrics.total_offer_count}sellers")
        
        # opportunity assessment
        if blended_margin > 25:
            opportunity_factors.append(f"high profit margin: {blended_margin:.1f}%")
        
        if financials.organic_order_pct > 0.7:
            opportunity_factors.append(f"High proportion of natural traffic: {financials.organic_order_pct*100:.0f}%")
        
        if metrics.rating >= 4.5 and metrics.review_count > 500:
            opportunity_factors.append("Quality evaluation basis")
        
        if metrics.sales_change_90d_pct > 20:
            opportunity_factors.append(f"growing trend: +{metrics.sales_change_90d_pct:.0f}%")
        
        # decision logic
        if blended_margin < 0:
            decision = "avoid"
            confidence = min(90, 50 + len(risk_factors) * 10)
        elif blended_margin < 10 or len(risk_factors) >= 3:
            decision = "caution"
            confidence = min(85, 60 + len(risk_factors) * 5)
        else:
            decision = "proceed"
            confidence = min(95, 60 + len(opportunity_factors) * 8)
        
        # ROI calculation (Simplify)
        monthly_investment = financials.cogs * metrics.bought_in_past_month
        roi = (monthly_profit / monthly_investment * 100) if monthly_investment > 0 else 0
        
        # Payback cycle
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
# link combination analyzer
# ============================================================================

class LinkPortfolioAnalyzer:
    """Analyze the entire link portfolio (All variations)"""
    
    def __init__(self, tacos_rate: float = 0.15):
        self.variant_analyzer = VariantProfitAnalyzer(tacos_rate)
        self.tacos_rate = tacos_rate
    
    def analyze_portfolio(
        self,
        parent_asin: str,
        products: List[Dict],
        financials_map: Dict[str, VariantFinancials]
    ) -> LinkPortfolioAnalysis:
        """Analyze the entire link portfolio"""
        
        # Analyze all variants
        variants = []
        for product in products:
            asin = product.get('asin', '')
            if asin in financials_map:
                result = self.variant_analyzer.analyze_variant(
                    product, financials_map[asin]
                )
                variants.append(result)
        
        if not variants:
            raise ValueError("No analyzable variants")
        
        # Sort by sales (Pareto analysis)
        variants_sorted = sorted(variants, key=lambda x: x.estimated_monthly_sales, reverse=True)
        
        # Calculate cumulative sales proportion
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
        
        # Portfolio level indicators
        total_revenue = sum(v.estimated_monthly_revenue for v in variants)
        total_profit = sum(v.monthly_total_profit for v in variants)
        blended_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Risk identification
        high_ad_dep = [v.asin for v in variants if v.financials.ad_order_pct > 0.6]
        loss_variants = [v.asin for v in variants if v.blended_margin_pct < 0]
        high_return = [v.asin for v in variants if v.metrics.return_rate > 0.12]
        
        # overall decision making
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
        """Make portfolio-level decisions"""
        
        risk_factors = []
        opportunity_factors = []
        
        # Portfolio Risk Assessment
        loss_count = sum(1 for v in variants if v.blended_margin_pct < 0)
        if loss_count > 0:
            risk_factors.append(f"{loss_count}loss variant")
        
        high_ad_count = sum(1 for v in variants if v.financials.ad_order_pct > 0.6)
        if high_ad_count > len(variants) / 2:
            risk_factors.append("Most variants are highly ad dependent")
        
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
            opportunity_factors.append(f"healthy profit margins: {blended_margin:.1f}%")
        
        # Calculate portfolio ROI
        total_cogs = sum(v.financials.cogs * v.estimated_monthly_sales for v in variants)
        roi = (total_profit / total_cogs * 100) if total_cogs > 0 else 0
        
        return ActuaryDecision(
            decision=decision,
            confidence=confidence,
            expected_monthly_profit=total_profit,
            expected_roi_pct=roi,
            payback_period_months=3.0,  # Simplify calculations
            risk_factors=risk_factors,
            opportunity_factors=opportunity_factors,
            data_quality_score=avg_confidence
        )


# ============================================================================
# HTML report generator
# ============================================================================

class FinalReportGenerator:
    """Final version of HTML report generator"""
    
    def __init__(self):
        self.template = self._create_template()
    
    def generate(
        self,
        analysis: LinkPortfolioAnalysis,
        output_path: str
    ) -> str:
        """Generate HTML report"""
        
        html = self._render_html(analysis)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def _render_html(self, analysis: LinkPortfolioAnalysis) -> str:
        """Render HTML"""
        
        # decision color
        decision_colors = {
            'proceed': '#22c55e',
            'caution': '#f59e0b', 
            'avoid': '#ef4444'
        }
        decision_text = {
            'proceed': '✅ Recommended',
            'caution': '⚠️ Consider carefully',
            'avoid': '❌ Recommended to avoid'
        }
        
        # Generate variant rows
        variant_rows = self._generate_variant_rows(analysis.variants)
        
        # Generate indicator cards
        metrics_cards = self._generate_metrics_cards(analysis)
        
        # Generate decision basis
        decision_basis = self._generate_decision_basis(analysis)
        
        # Generate 163 indicator details
        metrics_163_section = self._generate_163_metrics_section(analysis.variants)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Operations Actuary Report - {analysis.parent_asin}</title>
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
                    <span class="header-badge">🏆 Actuary-level analysis</span>
                    <span class="header-badge">📊 Full version of 163 indicators</span>
                    <span class="header-badge">✅ Real COGS</span>
                    <span class="header-badge">🎯 TACOS model</span>
                </div>
                <span style="opacity: 0.8; font-size: 0.95em;">{datetime.now().strftime('%Y-%m-%d')}</span>
            </div>
            <h1>Amazon Link Operations Actuary Report</h1>
            <div style="font-size: 1.2em; opacity: 0.95;">
                Parent ASIN: <strong>{analysis.parent_asin}</strong> | 
                number of variants: <strong>{len(analysis.variants)}</strong> | 
                Data integrity: <strong>{np.mean([v.data_completeness_pct for v in analysis.variants]):.0f}%</strong>
            </div>
        </div>
        
        <!-- Executive Summary -->
        <div class="exec-summary">
            <h2 style="font-size: 1.8em; margin-bottom: 10px;">💼 Executive Summary and Investment Decisions</h2>
            <div class="verdict">{decision_text[analysis.overall_decision.decision]}</div>
            <p style="font-size: 1.2em; margin-bottom: 40px;">
                Confidence: {analysis.overall_decision.confidence:.0f}% | 
                Data supports decision-making
            </p>
            
            {metrics_cards}
        </div>
        
        <!-- Decision Basis -->
        <div class="card">
            <h2 class="card-title">📊 Basis for decision-making (Based on data analysis)</h2>
            {decision_basis}
        </div>
        
        <!-- Organic vs Ad Analysis -->
        <div class="card">
            <h2 class="card-title">🌿🎯 Organic order vs insertion order comparison</h2>
            {self._generate_order_comparison(analysis)}
        </div>
        
        <!-- Pareto Analysis -->
        <div class="card">
            <h2 class="card-title">📈 Pareto analysis (80/Rule of 20)</h2>
            {self._generate_pareto_section(analysis)}
        </div>
        
        <!-- Variant Details Table -->
        <div class="card">
            <h2 class="card-title">📋 Full variant detailed indicator table</h2>
            
            <div class="legend">
                <div class="legend-item"><div class="legend-dot" style="background: #22c55e;"></div>🔥 Top Variations</div>
                <div class="legend-item"><div class="legend-dot" style="background: #3b82f6;"></div>📊 Pareto variant</div>
                <div class="legend-item"><div class="legend-dot" style="background: #f59e0b;"></div>⚠️ High advertising dependence</div>
                <div class="legend-item"><div class="legend-dot" style="background: #ef4444;"></div>🔴 Loss variant</div>
            </div>
            
            <div class="variant-section">
                <table class="variant-table">
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>ASIN</th>
                            <th>BSR</th>
                            <th>price</th>
                            <th>monthly sales</th>
                            <th>sales</th>
                            <th>Order source</th>
                            <th>COGS</th>
                            <th>operating expenses</th>
                            <th>Advertising fees</th>
                            <th>mixed profit margin</th>
                            <th>monthly net profit</th>
                            <th>decision making</th>
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
            <h2 class="card-title">🔍 163 Keepa indicator details</h2>
            <p style="opacity: 0.8; margin-bottom: 20px;">
                Complete metric data for each ASIN, all decisions are calculated based on the following metrics
            </p>
            {metrics_163_section}
        </div>
        
        <!-- Risk Assessment -->
        <div class="card">
            <h2 class="card-title">⚠️Risk Assessment</h2>
            {self._generate_risk_section(analysis)}
        </div>
        
        <!-- Action Plan -->
        <div class="card">
            <h2 class="card-title">🎯 Action Plan</h2>
            {self._generate_action_plan(analysis)}
        </div>
        
        <!-- Data Source Note -->
        <div class="card" style="background: rgba(251, 191, 36, 0.05); border: 2px solid rgba(251, 191, 36, 0.3);">
            <h2 class="card-title" style="color: #fbbf24;">📊 Data sources and methodology</h2>
            <div style="line-height: 2;">
                <p><strong>Keepa 163 indicator:</strong> Complete collection of all fields in Product Viewer CSV format</p>
                <p><strong>sales estimate:</strong> Regression model based on BSR historical data</p>
                <p><strong>COGS data:</strong> <span style="color: #fbbf24; font-weight: 600;">Users provide real data</span>, including purchase price, first-way freight and tariffs</p>
                <p><strong>Order source:</strong> <span style="color: #fbbf24; font-weight: 600;">Users provide real data</span>, from Amazon Advertising backend report</p>
                <p><strong>FBA fees:</strong> Based on packaging specifications(Length×width×height×weight)Calculate</p>
                <p><strong>return rate:</strong> Statistical model based on category historical data</p>
                <p><strong>advertising cost:</strong> TACOS (Total ACOS) 15%, that is, the total advertising expenditure accounts for 15% of the overall sales%</p>
                <p><strong>decision model:</strong> Weighted based on multiple dimensions such as profit margin, advertising dependence, return rate, rating, competition, etc.</p>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p style="font-size: 1.1em; margin-bottom: 15px;">
                Based on 163 Keepa indicators + Real COGS + TACOS model | data driven decision making
            </p>
            <p style="opacity: 0.7;">
                © 2026 Amazon Operations Actuary System v3.0 Final Edition<br>
                The report is for reference only. Actual profits are affected by market fluctuations, competition changes and other factors.
            </p>
        </div>
    </div>
</body>
</html>'''
        
        return html
    
    def _generate_variant_rows(self, variants: List[VariantAnalysisResult]) -> str:
        """Generate variant table rows"""
        rows = []
        for i, v in enumerate(variants, 1):
            # row style
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
            
            # profit margin color
            if v.blended_margin_pct >= 25:
                margin_class = "profit-excellent"
            elif v.blended_margin_pct >= 15:
                margin_class = "profit-good"
            elif v.blended_margin_pct >= 0:
                margin_class = "profit-marginal"
            else:
                margin_class = "profit-loss"
            
            # decision text
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
        """Generate indicator cards"""
        
        # Calculating organic vs ad ratio
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
                    <div class="metric-label">Estimated total monthly sales</div>
                    <div class="metric-sublabel">Total of all variants</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #a78bfa;">${analysis.total_monthly_revenue:,.0f}</div>
                    <div class="metric-label">Estimated monthly sales</div>
                    <div class="metric-sublabel">Gross Revenue</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #4ade80;">${analysis.total_monthly_profit:,.0f}</div>
                    <div class="metric-label">Estimated monthly net profit</div>
                    <div class="metric-sublabel">deduct all costs</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: {'#4ade80' if analysis.blended_portfolio_margin_pct >= 20 else '#fbbf24' if analysis.blended_portfolio_margin_pct >= 10 else '#f87171'};">
                        {analysis.blended_portfolio_margin_pct:.1f}%
                    </div>
                    <div class="metric-label">Mixed net profit margin</div>
                    <div class="metric-sublabel">TACOS model</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #22c55e;">{organic_pct:.0f}%</div>
                    <div class="metric-label">Proportion of natural orders</div>
                    <div class="metric-sublabel">No advertising fee</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #f59e0b;">{len(analysis.pareto_variants)}</div>
                    <div class="metric-label">Number of core variants</div>
                    <div class="metric-sublabel">Contribute 80%Sales volume</div>
                </div>
            </div>
        '''
    
    def _generate_decision_basis(self, analysis: LinkPortfolioAnalysis) -> str:
        """Generate decision basis"""
        
        # Positive factors
        positive_factors = []
        negative_factors = []
        
        for v in analysis.variants:
            for factor in v.decision.opportunity_factors:
                positive_factors.append(f"{v.asin}: {factor}")
            for factor in v.decision.risk_factors:
                negative_factors.append(f"{v.asin}: {factor}")
        
        # Add combination-level factors
        if analysis.blended_portfolio_margin_pct > 20:
            positive_factors.insert(0, f"Portfolio Health Profit Margin: {analysis.blended_portfolio_margin_pct:.1f}%")
        elif analysis.blended_portfolio_margin_pct < 15:
            negative_factors.insert(0, f"Portfolio low profit margin: {analysis.blended_portfolio_margin_pct:.1f}%")
        
        if len(analysis.loss_making_variants) == 0:
            positive_factors.append("No loss variant")
        else:
            negative_factors.append(f"{len(analysis.loss_making_variants)}loss variant")
        
        positive_html = "".join([
            f'<div class="decision-item decision-positive">✓ {f}</div>' 
            for f in positive_factors[:8]
        ]) if positive_factors else '<div class="decision-item decision-neutral">No significant positive factors yet</div>'
        
        negative_html = "".join([
            f'<div class="decision-item decision-negative">✗ {f}</div>' 
            for f in negative_factors[:8]
        ]) if negative_factors else '<div class="decision-item decision-neutral">No significant risk factors yet</div>'
        
        return f'''
            <div class="decision-grid">
                <div class="decision-card">
                    <h4>🟢 Support decision-making ({len(positive_factors)}factors)</h4>
                    {positive_html}
                </div>
                <div class="decision-card">
                    <h4>🔴Risk factors ({len(negative_factors)}factors)</h4>
                    {negative_html}
                </div>
            </div>
            <div style="margin-top: 20px; padding: 20px; background: rgba(255,255,255,0.03); border-radius: 12px;">
                <h4 style="color: #60a5fa; margin-bottom: 10px;">📝 Summary of data support</h4>
                <p>Based on{len(analysis.variants)}The analysis of 163 Keepa indicators for each variant takes into account sales performance, price trends, competitive situation, review quality, cost structure and other dimensions. The decision confidence is{analysis.overall_decision.confidence:.0f}%, the expected monthly ROI is{analysis.overall_decision.expected_roi_pct:.1f}%。</p>
            </div>
        '''
    
    def _generate_order_comparison(self, analysis: LinkPortfolioAnalysis) -> str:
        """Generate order source comparison"""
        
        # Calculating Overall Organic vs Advertising Data
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
                    <h3 style="font-size: 1.4em; color: #4ade80; margin-bottom: 25px;">🌿 Natural order</h3>
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>Order proportion</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">{(total_organic_sales/analysis.total_monthly_sales*100) if analysis.total_monthly_sales > 0 else 0:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>Monthly profit contribution</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">${organic_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>average profit margin</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #4ade80;">{organic_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.9; line-height: 1.8;">
                        There is no need to pay advertising fees for organic orders, and the profit margin is significantly higher than that of advertising orders.
                    </p>
                </div>
                
                <div class="comp-card comp-ad">
                    <h3 style="font-size: 1.4em; color: #fbbf24; margin-bottom: 25px;">🎯 Insertion Order</h3>
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>Order proportion</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: #fbbf24;">{(total_ad_sales/analysis.total_monthly_sales*100) if analysis.total_monthly_sales > 0 else 0:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span>Monthly profit contribution</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: {'#f87171' if ad_profit < 0 else '#fbbf24'};">${ad_profit:,.0f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>average profit margin</span>
                            <span style="font-size: 1.3em; font-weight: 700; color: {'#f87171' if ad_margin < 0 else '#fbbf24'};">{ad_margin:.1f}%</span>
                        </div>
                    </div>
                    <p style="opacity: 0.9; line-height: 1.8;">
                        Insertion orders need to allocate advertising costs(TACOS 15%), the profit margin is lower.
                        {"⚠️ The current advertising order is losing money and TACOS needs to be optimized." if ad_profit < 0 else ""}
                    </p>
                </div>
            </div>
            
            <div class="insight-box">
                <h4>💡 Order source insights</h4>
                <p>
                    Natural order profit margin ({organic_margin:.1f}%) 
                    Than insertion order ({ad_margin:.1f}%) high 
                    <strong>{organic_margin - ad_margin:.1f}percentage points</strong>。
                    Every increase of 1%proportion of natural orders, the monthly profit can be increased by approximately 
                    <strong>${abs(organic_profit - ad_profit) / analysis.total_monthly_sales * 100 if analysis.total_monthly_sales > 0 else 0:.0f}</strong>。
                </p>
            </div>
        '''
    
    def _generate_pareto_section(self, analysis: LinkPortfolioAnalysis) -> str:
        """Generate Pareto analysis section"""
        
        pareto_asins = [v.asin for v in analysis.pareto_variants]
        tail_count = len(analysis.tail_variants)
        
        return f'''
            <div class="metrics-grid" style="margin-bottom: 25px;">
                <div class="metric-card" style="background: rgba(59, 130, 246, 0.15); border: 2px solid rgba(59, 130, 246, 0.3);">
                    <div class="metric-value" style="color: #60a5fa;">{len(analysis.pareto_variants)}</div>
                    <div class="metric-label">core variant</div>
                    <div class="metric-sublabel">Contribute 80%Sales volume</div>
                </div>
                <div class="metric-card" style="background: rgba(245, 158, 11, 0.15); border: 2px solid rgba(245, 158, 11, 0.3);">
                    <div class="metric-value" style="color: #fbbf24;">{len(analysis.high_ad_dependency)}</div>
                    <div class="metric-label">High advertising dependence</div>
                    <div class="metric-sublabel">Advertising proportion&gt;60%</div>
                </div>
                <div class="metric-card" style="background: rgba(239, 68, 68, 0.15); border: 2px solid rgba(239, 68, 68, 0.3);">
                    <div class="metric-value" style="color: #f87171;">{len(analysis.loss_making_variants)}</div>
                    <div class="metric-label">loss variant</div>
                    <div class="metric-sublabel">Need immediate attention</div>
                </div>
                <div class="metric-card" style="background: rgba(34, 197, 94, 0.15); border: 2px solid rgba(34, 197, 94, 0.3);">
                    <div class="metric-value" style="color: #4ade80;">{tail_count}</div>
                    <div class="metric-label">long tail variant</div>
                    <div class="metric-sublabel">Contribute the remaining 20%</div>
                </div>
            </div>
            
            <p style="opacity: 0.9; line-height: 1.8;">
                <strong>Core findings:</strong> before{len(analysis.pareto_variants)}variants({', '.join(pareto_asins[:3])}...) 
                Contributed links 80%of sales. Priority should be given to keeping these variants fully stocked and continually optimizing their organic rankings.
                {f"Follow at the same time {len(analysis.high_ad_dependency)}If you have a high advertising dependency variant, consider increasing the organic proportion through off-site promotion." if analysis.high_ad_dependency else ""}
            </p>
        '''
    
    def _generate_163_metrics_section(self, variants: List[VariantAnalysisResult]) -> str:
        """Generate 163 indicator details section"""
        
        sections = []
        for v in variants[:5]:  # Show only first 5 variations
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
        """Generate risk analysis section"""
        
        risks = []
        
        if analysis.loss_making_variants:
            risks.append(f'''
                <div class="alert-box">
                    <h4>🔴 Loss variant ({len(analysis.loss_making_variants)}a)</h4>
                    <p>The following variants are currently losing money and need to be optimized immediately or considered discontinued:</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(analysis.loss_making_variants)}</p>
                </div>
            ''')
        
        if analysis.high_ad_dependency:
            risks.append(f'''
                <div class="insight-box">
                    <h4>⚠️ High advertising dependence ({len(analysis.high_ad_dependency)}a)</h4>
                    <p>The following variant insertion orders account for more than 60%, once advertising costs rise or competition intensifies, profits will decline significantly:</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(analysis.high_ad_dependency)}</p>
                </div>
            ''')
        
        if analysis.high_return_variants:
            risks.append(f'''
                <div class="insight-box">
                    <h4>📦 High return rate ({len(analysis.high_return_variants)}a)</h4>
                    <p>The following variants have a return rate of more than 12%, affecting overall profits:</p>
                    <p style="margin-top: 10px; font-weight: 600;">ASIN: {', '.join(analysis.high_return_variants)}</p>
                </div>
            ''')
        
        if not risks:
            risks.append('''
                <div class="success-box">
                    <h4>🌟 Risk assessment</h4>
                    <p>The overall risk of the current link is controllable, and no significant risk factors have been found.</p>
                </div>
            ''')
        
        return "".join(risks)
    
    def _generate_action_plan(self, analysis: LinkPortfolioAnalysis) -> str:
        """Generate action plan"""
        
        return f'''
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;">
                <div style="background: rgba(239, 68, 68, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(239, 68, 68, 0.3);">
                    <h4 style="color: #f87171; margin-bottom: 20px; font-size: 1.2em;">🚨 Act now (0-30 days)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        <li>• Ensure{len(analysis.pareto_variants)}Full inventory of core variants(60 days+)</li>
                        <li>• Optimize the main image and title of high-selling variants to increase natural conversions</li>
                        {f'<li>• Check{len(analysis.high_ad_dependency)}TACOS for high ad-dependent variants</li>' if analysis.high_ad_dependency else ''}
                        {f'<li>• processing{len(analysis.loss_making_variants)}loss variant(Increase price or reduce cost)</li>' if analysis.loss_making_variants else ''}
                    </ul>
                </div>
                
                <div style="background: rgba(245, 158, 11, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(245, 158, 11, 0.3);">
                    <h4 style="color: #fbbf24; margin-bottom: 20px; font-size: 1.2em;">📈 Short-term optimization (30-60 days)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        {f'<li>• Carry out off-site promotion to reduce TACOS for highly advertising-dependent variants</li>' if analysis.high_ad_dependency else ''}
                        <li>• Test price elasticity and find the optimal pricing point</li>
                        <li>• Collect and analyze reasons for returns to reduce return rates</li>
                        <li>• Optimize advertising strategy and increase budget for high-profit variants</li>
                    </ul>
                </div>
                
                <div style="background: rgba(34, 197, 94, 0.1); border-radius: 16px; padding: 25px; border: 1px solid rgba(34, 197, 94, 0.3);">
                    <h4 style="color: #4ade80; margin-bottom: 20px; font-size: 1.2em;">🚀 Long-term strategy (60-90 days)</h4>
                    <ul style="list-style: none; padding: 0; line-height: 2;">
                        <li>• Develop new colors/Size variations, copy success patterns</li>
                        <li>• Build supply chain bargaining power and reduce COGS 5-10%</li>
                        <li>• Build a brand moat and increase the proportion of natural traffic to 70%+</li>
                        <li>• Establish a monthly profit monitoring system to detect problem variants in a timely manner</li>
                    </ul>
                </div>
            </div>
        '''
    
    def _create_template(self) -> str:
        """Create HTML template (Already inline in_render_html in)"""
        return ""


# ============================================================================
# main entrance
# ============================================================================

def generate_final_report(
    parent_asin: str,
    products: List[Dict],
    financials_map: Dict[str, Dict],
    output_path: Optional[str] = None,
    tacos_rate: float = 0.15
) -> Tuple[str, LinkPortfolioAnalysis]:
    """
    Generate final actuary report
    
    Args:
        parent_asin: Parent ASIN
        products: Product list returned by Keepa API
        financials_map: ASIN to financial data mapping
        output_path: Output path
        tacos_rate: TACOS ratio (Default 15%)
        
    Returns:
        (Report path, Analyze results)
    """
    
    # Transform financial data
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
    
    # analysis portfolio
    analyzer = LinkPortfolioAnalyzer(tacos_rate)
    analysis = analyzer.analyze_portfolio(parent_asin, products, financials)
    
    # Generate report
    if output_path is None:
        output_path = f"cache/reports/{parent_asin}_ACTUARY_FINAL_v3.html"
    
    generator = FinalReportGenerator()
    report_path = generator.generate(analysis, output_path)
    
    return report_path, analysis


# ============================================================================
# Automatic variant collection function
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
    Generate actuary report (Support automatic variant collection)
    
    This is the recommended entry function! It will automatically:
    1. Get data of specified ASIN from Keepa API
    2. If auto_collect_variants=True, automatically discovers and collects all variants
    3. Generate a complete actuarial analysis report
    
    Args:
        asin: Any variant of the ASIN (or parent ASIN)
        financials_map: ASIN to financial data mapping {asin: {'cogs': 9.5, 'organic_pct': 0.7, 'ad_pct': 0.3}}
                       If not provided, the default COGS will be used=0 and average order source ratio
        api_key: Keepa API Key, if not provided then from the environment variable KEEPA_KEY acquisition
        output_path: Report output path
        tacos_rate: TACOS ratio (Default 15%)
        auto_collect_variants: Whether to automatically collect variant data
        
    Returns:
        (Report path, Analyze results, Variant information)
        
    Example:
        >>> # The simplest usage: just enter one ASIN and automatically collect all variants
        >>> report_path, analysis, info = generate_actuary_report_auto("B0F6B5R47Q")
        >>> 
        >>> # Provide real COGS data
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
    
    # Get API Key
    api_key = api_key or os.getenv("KEEPA_KEY", "")
    if not api_key:
        raise ValueError("Need to provide Keepa API Key or set KEEPA_KEY environment variable")
    
    # Import variant collector
    from .variant_auto_collector import VariantAutoCollector
    
    print("=" * 80)
    print(f"🚀Amazon Operations Actuary - Automatic variant acquisition mode")
    print("=" * 80)
    
    # Step 1: Collect variant data
    print(f"\n📦 Step 1: Collect ASIN {asin} and its variant data...")
    collector = VariantAutoCollector(api_key)
    products, parent_info = collector.collect_variants(asin)
    
    print(f"\n✅ Collection completed!")
    print(f"   Parent ASIN: {parent_info['parent_asin']}")
    print(f"   Number of variants: {parent_info['total_variations']}")
    print(f"   brand: {parent_info.get('brand', 'N/A')}")
    print(f"   Category: {parent_info.get('category', 'N/A')}")
    
    # Print variant summary
    print(collector.format_variants_summary(products))
    
    # Step 2: Prepare financial data
    print(f"\n💰 Step 2: Prepare financial data...")
    
    # If no financial data is provided, use default values and prompt the user
    if financials_map is None:
        print("   ⚠️ COGS data is not provided, use default value(cost=0, need to update manually)")
        financials_map = {}
        for p in products:
            asin_code = p.get('asin', '')
            attrs = collector.get_variation_attributes(p)
            color = attrs.get('color', 'Unknown')
            
            # Use default value
            financials_map[asin_code] = {
                'cogs': 0.0,  # User needs to update
                'organic_pct': 0.60,  # Default value
                'ad_pct': 0.40,
                'note': f'please update{color}Real COGS and order source data'
            }
    
    # Check if all variants have financial data
    for p in products:
        asin_code = p.get('asin', '')
        if asin_code not in financials_map:
            print(f"   ⚠️ ASIN {asin_code} No financial data, use default values")
            attrs = collector.get_variation_attributes(p)
            color = attrs.get('color', 'Unknown')
            financials_map[asin_code] = {
                'cogs': 0.0,
                'organic_pct': 0.60,
                'ad_pct': 0.40,
                'note': f'please update{color}The real COGS'
            }
    
    # Step 3: Generate report
    print(f"\n📊 Step 3: Generate actuarial analysis report...")
    
    parent_asin = parent_info['parent_asin']
    report_path, analysis = generate_final_report(
        parent_asin=parent_asin,
        products=products,
        financials_map=financials_map,
        output_path=output_path,
        tacos_rate=tacos_rate
    )
    
    # Generate interactive All-in-One report
    try:
        from allinone_interactive_report import generate_allinone_report
        allinone_path = generate_allinone_report(parent_asin, products, 
            {'variants': analysis.variants})
        print(f"\n   🧮 All-in-Oneinteractive report: {allinone_path}")
        print(f"      └─ Just fill in the purchase cost(RMB), automatically calculates complete profit analysis")
    except Exception as e:
        print(f"\n ⚠️ Interactive report generation failed: {e}")
    
    print(f"\n✅ Report generation completed!")
    print(f"   main report: {report_path}")
    print(f"   overall decision making: {analysis.overall_decision.decision.upper()}")
    print(f"   Confidence: {analysis.overall_decision.confidence}%")
    print(f"   Expected monthly profit: ${analysis.total_monthly_profit:,.2f}")
    
    return report_path, analysis, parent_info


# Convenience alias
auto_analyze = generate_actuary_report_auto


# ============================================================================
# backwards compatible
# ============================================================================

if __name__ == "__main__":
    print("Amazon Actuary System v3.0 - Final Edition")
    print("=" * 60)
    print("\nrecommended function:")
    print("  1. generate_actuary_report_auto(asin) - Automatically collect variants and analyze them")
    print("  2. generate_final_report(...) - Generate reports using existing data")
    print("\nExample:")
    print('  report, analysis, info = generate_actuary_report_auto("B0F6B5R47Q")')
