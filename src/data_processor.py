"""
Keepa 数据处理器
将 Keepa API 返回的原始数据转换为结构化分析数据
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple


class KeepaDataProcessor:
    """
    处理 Keepa API 返回的原始数据
    
    Keepa 数据格式说明:
    - 时间戳: 从 2011-01-01 开始的分钟数
    - 价格单位: 分 (需要除以 100 转换为美元)
    - -1 表示无数据/断货
    """
    
    # Keepa 时间起点
    KEEPA_EPOCH = datetime(2011, 1, 1)
    
    # 数据字段映射
    PRICE_FIELDS = {
        'AMAZON': 'amazon_price',
        'NEW': 'new_price',
        'USED': 'used_price',
        'SALES': 'sales_rank',
        'RATING': 'rating',
        'COUNT_REVIEWS': 'review_count',
        'BUYBOX_SHIPPING': 'buybox_price',
        'NEW_FBA': 'fba_price',
        'NEW_FBM_SHIPPING': 'fbm_price',
        'LIGHTNING_DEAL': 'deal_price',
        'COUNT_NEW': 'new_offers',
        'COUNT_USED': 'used_offers',
        'COUNT_REFURBISHED': 'refurbished_offers',
        'REFERRAL_FEE': 'referral_fee',
        'FULFILLMENT_FEE': 'fulfillment_fee',
    }
    
    def __init__(self):
        self.stats = {}
    
    def keepa_time_to_datetime(self, keepa_minutes: int) -> datetime:
        """将 Keepa 时间转换为 datetime"""
        return self.KEEPA_EPOCH + timedelta(minutes=int(keepa_minutes))
    
    def datetime_to_keepa_time(self, dt: datetime) -> int:
        """将 datetime 转换为 Keepa 时间"""
        return int((dt - self.KEEPA_EPOCH).total_seconds() / 60)
    
    def process_product(self, product: Dict, days: int = 90) -> Dict[str, Any]:
        """
        处理单个产品数据
        
        Args:
            product: Keepa API 返回的产品数据
            days: 分析天数
        
        Returns:
            结构化分析数据
        """
        result = {
            'asin': product.get('asin', 'N/A'),
            'title': product.get('title', 'N/A'),
            'brand': product.get('brand', 'N/A'),
            'category': product.get('categoryTree', [{}])[0].get('name', 'N/A') if product.get('categoryTree') else 'N/A',
            'manufacturer': product.get('manufacturer', 'N/A'),
            'product_group': product.get('productGroup', 'N/A'),
            'package_dimensions': self._extract_dimensions(product),
            'images': product.get('imagesCSV', ''),
            'last_update': datetime.now().isoformat(),
            # 新增: 品牌和专业度指标
            'has_aplus_content': product.get('hasAPlusContent', False),
            'video_count': len(product.get('videos', [])) if product.get('videos') else 0,
            'has_main_video': product.get('hasMainVideo', False),
            'parent_asin': product.get('parentAsin', None),
            'variation_count': len(product.get('variations', [])) if product.get('variations') else 0,
            'model': product.get('model', 'N/A'),
            'color': product.get('color', 'N/A'),
            'size': product.get('size', 'N/A'),
            'material': product.get('material', 'N/A'),
            'style': product.get('style', 'N/A'),
        }
        
        # 处理价格数据
        price_data = self._process_price_data(product, days)
        result.update(price_data)
        
        # 处理排名数据
        rank_data = self._process_rank_data(product, days)
        result.update(rank_data)
        
        # 处理卖家数据
        seller_data = self._process_seller_data(product, days)
        result.update(seller_data)
        
        # 处理评论数据
        review_data = self._process_review_data(product, days)
        result.update(review_data)
        
        # 处理库存/断货数据
        stock_data = self._process_stock_data(product, days)
        result.update(stock_data)
        
        # 处理费用数据 (FBA费、推荐费等)
        fee_data = self._process_fee_data(product)
        result.update(fee_data)
        
        # 计算衍生指标
        derived_data = self._calculate_derived_metrics(result, days)
        result.update(derived_data)
        
        return result
    
    def _process_price_data(self, product: Dict, days: int) -> Dict:
        """Process price data - using DataFrames for better data quality"""
        data = product.get('data', {})
        
        result = {}
        
        # Use DataFrames if available (Keepa provides processed DataFrames)
        # NEW price (third-party new)
        df_new = data.get('df_NEW')
        if df_new is not None and not df_new.empty:
            new_prices = self._extract_from_dataframe(df_new)
        else:
            new_data = data.get('NEW', [])
            new_prices = self._extract_time_series(new_data, 0)
        
        result['new_price_history'] = new_prices
        result['current_new_price'] = new_prices[-1] if new_prices else None
        
        # Amazon 1P price
        df_amazon = data.get('df_AMAZON')
        if df_amazon is not None and not df_amazon.empty:
            amazon_prices = self._extract_from_dataframe(df_amazon)
        else:
            amazon_data = data.get('AMAZON', [])
            amazon_prices = self._extract_time_series(amazon_data, 0)
        
        result['amazon_price_history'] = amazon_prices
        result['current_amazon_price'] = amazon_prices[-1] if amazon_prices else None
        result['min_amazon_price'] = min(amazon_prices) if amazon_prices else None
        result['max_amazon_price'] = max(amazon_prices) if amazon_prices else None
        result['avg_amazon_price'] = round(np.mean(amazon_prices), 2) if amazon_prices else None
        
        # Buy Box price - try DataFrame first
        df_buybox = data.get('df_BUY_BOX_SHIPPING') or data.get('df_BUYBOX_SHIPPING')
        if df_buybox is not None and not df_buybox.empty:
            buybox_prices = self._extract_from_dataframe(df_buybox)
        else:
            buybox_data = data.get('BUY_BOX_SHIPPING', [])
            if not buybox_data:
                buybox_data = data.get('BUYBOX_SHIPPING', [])
            buybox_prices = self._extract_time_series(buybox_data, 0)
        
        result['buybox_price_history'] = buybox_prices
        result['current_buybox_price'] = buybox_prices[-1] if buybox_prices else None
        
        # FBA price
        df_fba = data.get('df_NEW_FBA')
        if df_fba is not None and not df_fba.empty:
            fba_prices = self._extract_from_dataframe(df_fba)
        else:
            fba_data = data.get('NEW_FBA', [])
            fba_prices = self._extract_time_series(fba_data, 0)
        
        result['fba_price_history'] = fba_prices
        result['current_fba_price'] = fba_prices[-1] if fba_prices else None
        
        # Determine current price (priority: Buy Box > FBA > New > Amazon)
        result['current_price'] = (
            result.get('current_buybox_price') or 
            result.get('current_fba_price') or 
            result.get('current_new_price') or 
            result.get('current_amazon_price')
        )
        
        # Use available price data for analysis
        primary_prices = buybox_prices or fba_prices or new_prices or amazon_prices
        
        if primary_prices:
            result['min_price'] = min(primary_prices)
            result['max_price'] = max(primary_prices)
            result['avg_price'] = round(np.mean(primary_prices), 2)
            result['price_std'] = round(np.std(primary_prices), 2)
            result['price_stability'] = self._calculate_price_stability(primary_prices)
            result['price_drops_count'] = self._count_price_drops(primary_prices)
            
            # Multi-timeframe price stats
            result['price_30d_avg'] = self._calculate_window_average(primary_prices, 30)
            result['price_90d_avg'] = self._calculate_window_average(primary_prices, 90)
            result['price_180d_avg'] = self._calculate_window_average(primary_prices, 180)
            result['price_365d_avg'] = self._calculate_window_average(primary_prices, 365)
            result['price_lowest_365d'] = self._calculate_window_min(primary_prices, 365)
            result['price_highest_365d'] = self._calculate_window_max(primary_prices, 365)
        else:
            result['min_price'] = None
            result['max_price'] = None
            result['avg_price'] = None
            result['price_std'] = None
            result['price_stability'] = 'No Data'
            result['price_drops_count'] = 0
        
        return result
    
    def _process_rank_data(self, product: Dict, days: int) -> Dict:
        """Process sales rank data - using DataFrames for better data quality"""
        data = product.get('data', {})
        
        result = {}
        
        # Sales rank - use DataFrame if available
        df_sales = data.get('df_SALES')
        if df_sales is not None and not df_sales.empty:
            sales_ranks = self._extract_from_dataframe(df_sales)
        else:
            sales_data = data.get('SALES', [])
            sales_ranks = self._extract_time_series(sales_data, 0)
        
        result['sales_rank_history'] = sales_ranks
        
        if sales_ranks:
            result['current_rank'] = int(sales_ranks[-1])
            result['best_rank'] = int(min(sales_ranks))
            result['worst_rank'] = int(max(sales_ranks))
            result['avg_rank'] = int(np.mean(sales_ranks))
            result['rank_std'] = round(np.std(sales_ranks), 2)
            result['rank_trend'] = self._calculate_trend(sales_ranks)
            
            # Multi-timeframe rank stats
            result['rank_30d_avg'] = self._calculate_window_average(sales_ranks, 30)
            result['rank_90d_avg'] = self._calculate_window_average(sales_ranks, 90)
            result['rank_180d_avg'] = self._calculate_window_average(sales_ranks, 180)
            result['rank_365d_avg'] = self._calculate_window_average(sales_ranks, 365)
            result['rank_lowest_365d'] = self._calculate_window_min(sales_ranks, 365)
            result['rank_highest_365d'] = self._calculate_window_max(sales_ranks, 365)
            
            # Rank drop counts
            result['rank_drops_30d'] = self._count_rank_drops(sales_ranks, 30)
            result['rank_drops_90d'] = self._count_rank_drops(sales_ranks, 90)
            result['rank_drops_180d'] = self._count_rank_drops(sales_ranks, 180)
            result['rank_drops_365d'] = self._count_rank_drops(sales_ranks, 365)
            
            # Estimate monthly sales
            result['estimated_monthly_sales'] = self._estimate_monthly_sales(result['avg_rank'])
        else:
            result['current_rank'] = None
            result['best_rank'] = None
            result['worst_rank'] = None
            result['avg_rank'] = None
            result['rank_trend'] = 'No Data'
            result['estimated_monthly_sales'] = None
        
        # Category ranks
        result['category_ranks'] = product.get('categoryTree', [])
        
        return result
    
    def _process_seller_data(self, product: Dict, days: int) -> Dict:
        """处理卖家数据 - 包含品牌垄断度分析"""
        data = product.get('data', {})
        
        result = {}
        
        # 新货卖家数
        count_new_data = data.get('COUNT_NEW', [])
        new_offers = self._extract_time_series(count_new_data, 0)
        result['new_offers_history'] = new_offers
        result['current_offers'] = int(new_offers[-1]) if new_offers else None
        result['avg_offers'] = round(np.mean(new_offers), 1) if new_offers else None
        result['max_offers'] = int(max(new_offers)) if new_offers else None
        
        # FBA 卖家数
        fba_data = data.get('COUNT_FBA', [])
        fba_offers = self._extract_time_series(fba_data, 0)
        result['fba_offers'] = int(fba_offers[-1]) if fba_offers else None
        result['fba_offers_avg'] = round(np.mean(fba_offers), 1) if fba_offers else None
        
        # FBM 卖家数
        fbm_data = data.get('COUNT_FBM_SHIPPING', [])
        fbm_offers = self._extract_time_series(fbm_data, 0)
        result['fbm_offers'] = int(fbm_offers[-1]) if fbm_offers else None
        
        # Buy Box 信息
        buybox_data = product.get('buyBoxSellerIdHistory', [])
        if buybox_data:
            result['buybox_winner'] = buybox_data[-1] if isinstance(buybox_data, list) else buybox_data
        else:
            result['buybox_winner'] = 'Unknown'
        
        # 判断是否有亚马逊自营
        result['is_amazon_selling'] = data.get('AMAZON', []) and len(data.get('AMAZON', [])) > 0
        
        # 新增: Buy Box卖家历史分析
        buybox_history = data.get('BUY_BOX_SELLER', [])
        if buybox_history:
            result['buybox_seller_changes'] = self._count_seller_changes(buybox_history)
        else:
            result['buybox_seller_changes'] = 0
        
        return result
    
    def _process_review_data(self, product: Dict, days: int) -> Dict:
        """处理评论数据 - 包含退货率指标"""
        data = product.get('data', {})
        
        result = {}
        
        # 评分
        rating_data = data.get('RATING', [])
        ratings = self._extract_time_series(rating_data, 0)
        result['rating_history'] = ratings
        result['current_rating'] = round(ratings[-1], 1) if ratings else None
        result['avg_rating'] = round(np.mean(ratings), 2) if ratings else None
        
        # 评论数
        reviews_data = data.get('COUNT_REVIEWS', [])
        review_counts = self._extract_time_series(reviews_data, 0)
        result['review_count_history'] = review_counts
        result['total_reviews'] = int(review_counts[-1]) if review_counts else None
        result['reviews_30d'] = self._calculate_review_growth(review_counts, 30)
        result['reviews_90d'] = self._calculate_review_growth(review_counts, 90)
        result['review_trend'] = self._calculate_trend(review_counts) if review_counts else 'No Data'
        
        # 新增: 评论数多时间窗口平均
        result['reviews_90d_avg'] = self._calculate_window_average(review_counts, 90)
        result['reviews_180d_avg'] = self._calculate_window_average(review_counts, 180)
        result['reviews_365d_avg'] = self._calculate_window_average(review_counts, 365)
        
        # 新增: 退货率 (如果Keepa提供)
        return_rate_data = data.get('RETURN_RATE', [])
        if return_rate_data:
            return_rates = self._extract_time_series(return_rate_data, 0)
            result['return_rate'] = return_rates[-1] if return_rates else None
            result['return_rate_avg'] = round(np.mean(return_rates), 2) if return_rates else None
        else:
            # 基于评论情感等估算退货风险
            result['return_rate'] = None
            result['return_risk_level'] = self._estimate_return_risk(product, result)
        
        return result
    
    def _process_stock_data(self, product: Dict, days: int) -> Dict:
        """处理库存/断货数据 - 包含库存紧张信号"""
        data = product.get('data', {})
        
        result = {
            'out_of_stock_days': 0,
            'stockouts_count': 0,
            'last_in_stock': None,
            'inventory_tension': False,  # 新增: 库存紧张信号
            'buybox_stock_level': None,  # 新增: Buy Box库存水平
        }
        
        # 通过价格数据判断断货情况 (-1 表示无货)
        # Amazon 自营价格
        amazon_prices = data.get('AMAZON', [])
        if amazon_prices:
            stockout_periods = self._detect_stockouts(amazon_prices, days)
            result['out_of_stock_days'] = stockout_periods['total_days']
            result['stockouts_count'] = stockout_periods['count']
        
        # 新增: Buy Box库存水平检测 (通过Buy Box价格变化频率)
        buybox_data = data.get('BUY_BOX_SHIPPING', [])
        if buybox_data:
            result['buybox_stock_level'] = self._estimate_buybox_inventory(buybox_data)
            # 如果Buy Box库存水平低且OOS天数>0，标记为库存紧张
            if result['buybox_stock_level'] == 'low' or result['out_of_stock_days'] > 0:
                result['inventory_tension'] = True
        
        # 新增: 90天OOS百分比
        result['oos_rate_90d'] = self._calculate_oos_rate(data, 90)
        
        return result
    
    def _process_fee_data(self, product: Dict) -> Dict:
        """处理费用数据 - FBA费、推荐费等"""
        data = product.get('data', {})
        
        result = {}
        
        # 推荐费比例
        referral_fee_data = data.get('REFERRAL_FEE_PERCENT', [])
        if referral_fee_data:
            referral_fees = self._extract_time_series(referral_fee_data, 0)
            result['referral_fee_percent'] = round(referral_fees[-1], 2) if referral_fees else 15.0
        else:
            # 默认推荐费15%
            result['referral_fee_percent'] = 15.0
        
        # FBA费用 (如果有)
        fba_fee_data = data.get('FULFILLMENT_FEE', [])
        if fba_fee_data:
            fba_fees = self._extract_time_series(fba_fee_data, 0)
            result['fba_fee'] = round(fba_fees[-1], 2) if fba_fees else None
        else:
            # 估算FBA费用基于重量
            weight = product.get('packageWeight', 0) or product.get('itemWeight', 0)
            result['fba_fee'] = self._estimate_fba_fee(weight)
        
        # 计算基于当前Buy Box价格的推荐费金额
        if result.get('referral_fee_percent') and data.get('BUY_BOX_SHIPPING', []):
            buybox_prices = self._extract_time_series(data.get('BUY_BOX_SHIPPING', []), 0)
            if buybox_prices:
                current_price = buybox_prices[-1]
                result['referral_fee_amount'] = round(current_price * result['referral_fee_percent'] / 100, 2)
        
        return result
    
    def _calculate_derived_metrics(self, data: Dict, days: int) -> Dict:
        """计算衍生指标 - 包含PDF启发的新指标"""
        result = {}
        
        # 价格变化率
        if data.get('min_price') and data.get('max_price') and data.get('max_price') > 0:
            result['price_volatility'] = round(
                (data['max_price'] - data['min_price']) / data['max_price'] * 100, 1
            )
        else:
            result['price_volatility'] = 0
        
        # 新增: 定价权指数 (当前价格 vs 历史均价)
        if data.get('current_price') and data.get('price_365d_avg') and data['price_365d_avg'] > 0:
            result['pricing_power_index'] = round(
                (data['current_price'] - data['price_365d_avg']) / data['price_365d_avg'] * 100, 1
            )
        else:
            result['pricing_power_index'] = 0
        
        # 新增: 排名恶化率 (当前排名 vs 365天平均，正值表示排名变差)
        if data.get('current_rank') and data.get('rank_365d_avg') and data['rank_365d_avg'] > 0:
            result['rank_deterioration_rate'] = round(
                (data['current_rank'] - data['rank_365d_avg']) / data['rank_365d_avg'] * 100, 1
            )
        else:
            result['rank_deterioration_rate'] = 0
        
        # 利润率估算 (基于 Buy Box 价格)
        if data.get('avg_price'):
            # 使用实际费用数据
            referral_fee = data.get('referral_fee_percent', 15) / 100
            fba_fee = data.get('fba_fee', 5.0)
            
            # 粗略估算: 假设成本为价格的 35%
            estimated_cost = data['avg_price'] * 0.35
            referral_amount = data['avg_price'] * referral_fee
            
            profit = data['avg_price'] - estimated_cost - referral_amount - fba_fee
            result['estimated_profit'] = round(profit, 2)
            result['estimated_margin'] = round(profit / data['avg_price'] * 100, 1) if data['avg_price'] > 0 else 0
        else:
            result['estimated_profit'] = None
            result['estimated_margin'] = None
        
        # 竞争强度
        if data.get('current_offers'):
            if data['current_offers'] < 5:
                result['competition_level'] = 'Low'
            elif data['current_offers'] < 15:
                result['competition_level'] = 'Medium'
            else:
                result['competition_level'] = 'High'
        else:
            result['competition_level'] = 'Unknown'
        
        # 新增: 品牌垄断度评估
        result['brand_dominance'] = self._assess_brand_dominance(data)
        
        # 新增: 卖家集中度
        result['seller_concentration'] = self._calculate_seller_concentration(data)
        
        # 产品生命周期判断
        result['lifecycle_stage'] = self._determine_lifecycle_stage(data)
        
        return result
    
    def _assess_brand_dominance(self, data: Dict) -> Dict:
        """评估品牌垄断度 - 基于PDF学习"""
        offers = data.get('current_offers', 0) or 0
        fba_offers = data.get('fba_offers', 0) or 0
        buybox_winner = data.get('buybox_winner', '')
        brand = data.get('brand', '')
        
        # 判断是否为品牌方自营
        is_brand_seller = brand.lower() in buybox_winner.lower() if brand and buybox_winner else False
        
        if offers == 1 and fba_offers == 1:
            level = 'monopoly'
            description = 'Brand Monopoly - Single seller controls market'
        elif offers <= 3 and is_brand_seller:
            level = 'dominant'
            description = 'Brand Dominant - Brand controls Buy Box'
        elif offers <= 5:
            level = 'concentrated'
            description = 'Concentrated Market - Few sellers competing'
        elif offers <= 15:
            level = 'competitive'
            description = 'Competitive Market - Multiple active sellers'
        else:
            level = 'fragmented'
            description = 'Fragmented Market - Intense price competition'
        
        return {
            'level': level,
            'description': description,
            'is_brand_seller': is_brand_seller,
            'offers_count': offers,
            'fba_offers_count': fba_offers
        }
    
    def _calculate_seller_concentration(self, data: Dict) -> str:
        """计算卖家集中度"""
        offers = data.get('current_offers', 0) or 0
        
        if offers == 1:
            return '100% (Monopoly)'
        elif offers <= 3:
            return 'High (Oligopoly)'
        elif offers <= 8:
            return 'Medium'
        elif offers <= 20:
            return 'Low'
        else:
            return 'Very Low (Perfect Competition)'
    
    def _estimate_return_risk(self, product: Dict, review_data: Dict) -> str:
        """估算退货风险等级"""
        rating = review_data.get('current_rating', 0) or 0
        category = product.get('categoryTree', [{}])[0].get('name', '') if product.get('categoryTree') else ''
        
        # 高风险类目
        high_return_categories = ['Apparel', 'Shoes', 'Clothing', 'Fashion']
        
        if rating < 4.0:
            return 'High'
        elif rating < 4.2 or any(cat in category for cat in high_return_categories):
            return 'Medium'
        else:
            return 'Low'
    
    def _estimate_buybox_inventory(self, buybox_data: List) -> str:
        """估算Buy Box库存水平"""
        # 简化估算: 基于价格变化频率
        if len(buybox_data) < 10:
            return 'unknown'
        
        # 如果价格频繁变化，可能库存波动大
        recent_changes = sum(1 for i in range(1, min(20, len(buybox_data))) 
                            if abs(buybox_data[i] - buybox_data[i-1]) > 0.01)
        
        if recent_changes > 10:
            return 'low'  # 价格波动大，可能库存紧张
        elif recent_changes > 5:
            return 'medium'
        else:
            return 'normal'
    
    def _calculate_oos_rate(self, data: Dict, days: int) -> float:
        """计算OOS率 (Out of Stock Rate)"""
        amazon_data = data.get('AMAZON', [])
        if not amazon_data or len(amazon_data) < 2:
            return 0.0
        
        # 计算断货天数占比
        cutoff_time = self.datetime_to_keepa_time(datetime.now() - timedelta(days=days))
        oos_count = 0
        total_count = 0
        
        for i in range(0, len(amazon_data) - 1, 2):
            time_val = amazon_data[i]
            if time_val < cutoff_time:
                continue
            
            total_count += 1
            price_val = amazon_data[i + 1]
            if price_val == -1:
                oos_count += 1
        
        return round(oos_count / total_count * 100, 1) if total_count > 0 else 0.0
    
    def _estimate_fba_fee(self, weight: float) -> float:
        """基于重量估算FBA费用"""
        if weight <= 0:
            return 5.0
        
        # 简化估算模型
        if weight <= 0.25:  # 4 oz
            return 3.22
        elif weight <= 0.5:  # 8 oz
            return 3.86
        elif weight <= 1.0:  # 1 lb
            return 5.77
        elif weight <= 2.0:  # 2 lb
            return 7.25
        elif weight <= 3.0:  # 3 lb
            return 8.50
        else:
            return 8.50 + (weight - 3) * 0.50
    
    # Helper methods
    def _extract_from_dataframe(self, df) -> List[float]:
        """Extract values from Keepa DataFrame, filtering out NaN and invalid values"""
        if df is None or df.empty:
            return []
        
        # Get values column and drop NaN
        values = df['value'].dropna()
        
        # Filter out invalid values (-1 indicates out of stock/no data)
        valid_values = values[values != -1].tolist()
        
        return valid_values
    
    def _extract_time_series(self, data, cutoff_time: int) -> List[float]:
        """Extract time series data, filtering out invalid values"""
        if hasattr(data, 'tolist'):
            data = data.tolist()
        
        if not data or len(data) == 0:
            return []
        
        values = []
        for val in data:
            if val is not None and val != -1 and not (isinstance(val, float) and np.isnan(val)):
                values.append(val)
        
        return values
    
    def _calculate_window_average(self, values: List[float], days: int) -> Optional[float]:
        """计算指定时间窗口的平均值"""
        if not values:
            return None
        # 假设数据均匀分布，取最近 N 天的数据
        points = max(1, int(len(values) * days / 365))
        window_values = values[-points:] if points < len(values) else values
        return round(np.mean(window_values), 2) if window_values else None
    
    def _calculate_window_min(self, values: List[float], days: int) -> Optional[float]:
        """计算指定时间窗口的最小值"""
        if not values:
            return None
        points = max(1, int(len(values) * days / 365))
        window_values = values[-points:] if points < len(values) else values
        return round(min(window_values), 2) if window_values else None
    
    def _calculate_window_max(self, values: List[float], days: int) -> Optional[float]:
        """计算指定时间窗口的最大值"""
        if not values:
            return None
        points = max(1, int(len(values) * days / 365))
        window_values = values[-points:] if points < len(values) else values
        return round(max(window_values), 2) if window_values else None
    
    def _count_rank_drops(self, ranks: List[float], days: int) -> int:
        """统计排名下降次数 (排名数字变大表示下降)"""
        if not ranks or len(ranks) < 2:
            return 0
        
        points = max(1, int(len(ranks) * days / 365))
        window_ranks = ranks[-points:] if points < len(ranks) else ranks
        
        drops = 0
        for i in range(1, len(window_ranks)):
            if window_ranks[i] > window_ranks[i-1] * 1.05:  # 排名恶化超过5%
                drops += 1
        
        return drops
    
    def _count_seller_changes(self, seller_history: List) -> int:
        """统计Buy Box卖家变化次数"""
        if not seller_history or len(seller_history) < 2:
            return 0
        
        changes = 0
        for i in range(1, len(seller_history)):
            if seller_history[i] != seller_history[i-1]:
                changes += 1
        
        return changes
    
    def _calculate_price_stability(self, prices: List[float]) -> str:
        """计算价格稳定性"""
        if len(prices) < 2:
            return 'No Data'
        
        cv = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
        
        if cv < 0.05:
            return 'Very Stable'
        elif cv < 0.1:
            return 'Stable'
        elif cv < 0.2:
            return 'Moderate Volatility'
        else:
            return 'High Volatility'
    
    def _count_price_drops(self, prices: List[float], threshold: float = 0.1) -> int:
        """统计价格大幅下降次数"""
        if len(prices) < 2:
            return 0
        
        drops = 0
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                change = (prices[i] - prices[i-1]) / prices[i-1]
                if change < -threshold:
                    drops += 1
        
        return drops
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势"""
        if len(values) < 10:
            return 'Insufficient Data'
        
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        normalized_slope = slope / np.mean(values) if np.mean(values) > 0 else 0
        
        if normalized_slope < -0.001:
            return 'Declining ↘️'
        elif normalized_slope > 0.001:
            return 'Rising ↗️'
        else:
            return 'Stable ➡️'
    
    def _calculate_review_growth(self, review_counts: List[float], days: int) -> int:
        """计算评论增长数"""
        if len(review_counts) < 2:
            return 0
        
        points_per_day = len(review_counts) / 90
        points_to_take = int(points_per_day * days)
        
        if points_to_take >= len(review_counts):
            recent = review_counts[-1]
            past = review_counts[0]
        else:
            recent = review_counts[-1]
            past = review_counts[-points_to_take]
        
        return max(0, int(recent - past))
    
    def _detect_stockouts(self, prices: List, days: int) -> Dict:
        """检测断货情况"""
        if not prices or len(prices) < 2:
            return {'total_days': 0, 'count': 0}
        
        cutoff_time = self.datetime_to_keepa_time(datetime.now() - timedelta(days=days))
        total_days = 0
        stockout_count = 0
        in_stockout = False
        
        for i in range(0, len(prices) - 2, 2):
            time_val = prices[i]
            price_val = prices[i + 1]
            next_time = prices[i + 2]
            
            if time_val < cutoff_time:
                continue
            
            if price_val == -1:
                if not in_stockout:
                    stockout_count += 1
                    in_stockout = True
                days_out = (next_time - time_val) / (24 * 60)
                total_days += max(0, days_out)
            else:
                in_stockout = False
        
        return {
            'total_days': int(total_days),
            'count': stockout_count
        }
    
    def _estimate_monthly_sales(self, avg_rank: int) -> str:
        """根据 BSR 估算月销量"""
        if not avg_rank:
            return 'Unknown'
        
        if avg_rank < 1000:
            return '1000+'
        elif avg_rank < 5000:
            return '500-1000'
        elif avg_rank < 10000:
            return '300-500'
        elif avg_rank < 50000:
            return '100-300'
        elif avg_rank < 100000:
            return '50-100'
        elif avg_rank < 500000:
            return '10-50'
        else:
            return '<10'
    
    def _determine_lifecycle_stage(self, data: Dict) -> str:
        """判断产品生命周期阶段"""
        reviews = data.get('total_reviews', 0) or 0
        rating = data.get('current_rating', 0) or 0
        rank_trend = data.get('rank_trend', '')
        rank_deterioration = data.get('rank_deterioration_rate', 0)
        
        if reviews < 50 and 'Rising' in rank_trend:
            return 'Growth Phase 🌱'
        elif reviews > 500 and rating > 4.0 and 'Stable' in rank_trend:
            return 'Maturity Phase 🌳'
        elif 'Declining' in rank_trend or rank_deterioration > 20:
            return 'Decline Phase 🍂'
        elif reviews < 10:
            return 'New/Test Phase 🌰'
        else:
            return 'Stable Phase ➡️'
    
    def _extract_dimensions(self, product: Dict) -> Dict:
        """提取包装尺寸信息"""
        return {
            'length': product.get('packageLength', 0),
            'width': product.get('packageWidth', 0),
            'height': product.get('packageHeight', 0),
            'weight': product.get('packageWeight', 0),
            'item_length': product.get('itemLength', 0),
            'item_width': product.get('itemWidth', 0),
            'item_height': product.get('itemHeight', 0),
            'item_weight': product.get('itemWeight', 0),
            'dimension_unit': 'cm',
            'weight_unit': 'kg',
        }
