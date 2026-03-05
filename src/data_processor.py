"""
Keepa data processor
Convert raw data returned by the Keepa API into structured analytics data
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple


class KeepaDataProcessor:
    """
    Processing raw data returned by the Keepa API
    
    Keepa data format description:
    - Timestamp: from 2011-01-01 starting minutes
    - price unit: points (Need to divide by 100 to convert to USD)
    - -1 means no data/Out of stock
    """
    
    # Keepa time starting point
    KEEPA_EPOCH = datetime(2011, 1, 1)
    
    # Data field mapping
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
        """Convert Keepa time to datetime"""
        return self.KEEPA_EPOCH + timedelta(minutes=int(keepa_minutes))
    
    def datetime_to_keepa_time(self, dt: datetime) -> int:
        """Convert datetime to Keepa time"""
        return int((dt - self.KEEPA_EPOCH).total_seconds() / 60)
    
    def process_product(self, product: Dict, days: int = 90) -> Dict[str, Any]:
        """
        Process individual product data
        
        Args:
            product: Product data returned by Keepa API
            days: Analysis days
        
        Returns:
            Structured analytics data
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
            # New: Brand and professionalism indicators
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
        
        # Process price data
        price_data = self._process_price_data(product, days)
        result.update(price_data)
        
        # Process ranking data
        rank_data = self._process_rank_data(product, days)
        result.update(rank_data)
        
        # Process seller data
        seller_data = self._process_seller_data(product, days)
        result.update(seller_data)
        
        # Process comment data
        review_data = self._process_review_data(product, days)
        result.update(review_data)
        
        # Process inventory/Out of stock data
        stock_data = self._process_stock_data(product, days)
        result.update(stock_data)
        
        # Process expense data (FBA fees, recommendation fees, etc.)
        fee_data = self._process_fee_data(product)
        result.update(fee_data)
        
        # Calculate derived indicators
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
        """Process seller data - Contains brand monopoly analysis"""
        data = product.get('data', {})
        
        result = {}
        
        # Number of new goods sellers
        count_new_data = data.get('COUNT_NEW', [])
        new_offers = self._extract_time_series(count_new_data, 0)
        result['new_offers_history'] = new_offers
        result['current_offers'] = int(new_offers[-1]) if new_offers else None
        result['avg_offers'] = round(np.mean(new_offers), 1) if new_offers else None
        result['max_offers'] = int(max(new_offers)) if new_offers else None
        
        # Number of FBA sellers
        fba_data = data.get('COUNT_FBA', [])
        fba_offers = self._extract_time_series(fba_data, 0)
        result['fba_offers'] = int(fba_offers[-1]) if fba_offers else None
        result['fba_offers_avg'] = round(np.mean(fba_offers), 1) if fba_offers else None
        
        # Number of FBM sellers
        fbm_data = data.get('COUNT_FBM_SHIPPING', [])
        fbm_offers = self._extract_time_series(fbm_data, 0)
        result['fbm_offers'] = int(fbm_offers[-1]) if fbm_offers else None
        
        # Buy Box Information
        buybox_data = product.get('buyBoxSellerIdHistory', [])
        if buybox_data:
            result['buybox_winner'] = buybox_data[-1] if isinstance(buybox_data, list) else buybox_data
        else:
            result['buybox_winner'] = 'Unknown'
        
        # Determine whether it is self-operated by Amazon
        result['is_amazon_selling'] = data.get('AMAZON', []) and len(data.get('AMAZON', [])) > 0
        
        # New: Buy Box seller history analysis
        buybox_history = data.get('BUY_BOX_SELLER', [])
        if buybox_history:
            result['buybox_seller_changes'] = self._count_seller_changes(buybox_history)
        else:
            result['buybox_seller_changes'] = 0
        
        return result
    
    def _process_review_data(self, product: Dict, days: int) -> Dict:
        """Process comment data - Includes return rate metrics"""
        data = product.get('data', {})
        
        result = {}
        
        # score
        rating_data = data.get('RATING', [])
        ratings = self._extract_time_series(rating_data, 0)
        result['rating_history'] = ratings
        result['current_rating'] = round(ratings[-1], 1) if ratings else None
        result['avg_rating'] = round(np.mean(ratings), 2) if ratings else None
        
        # Number of comments
        reviews_data = data.get('COUNT_REVIEWS', [])
        review_counts = self._extract_time_series(reviews_data, 0)
        result['review_count_history'] = review_counts
        result['total_reviews'] = int(review_counts[-1]) if review_counts else None
        result['reviews_30d'] = self._calculate_review_growth(review_counts, 30)
        result['reviews_90d'] = self._calculate_review_growth(review_counts, 90)
        result['review_trend'] = self._calculate_trend(review_counts) if review_counts else 'No Data'
        
        # New: Average number of comments over multiple time windows
        result['reviews_90d_avg'] = self._calculate_window_average(review_counts, 90)
        result['reviews_180d_avg'] = self._calculate_window_average(review_counts, 180)
        result['reviews_365d_avg'] = self._calculate_window_average(review_counts, 365)
        
        # New: return rate (If Keepa provides)
        return_rate_data = data.get('RETURN_RATE', [])
        if return_rate_data:
            return_rates = self._extract_time_series(return_rate_data, 0)
            result['return_rate'] = return_rates[-1] if return_rates else None
            result['return_rate_avg'] = round(np.mean(return_rates), 2) if return_rates else None
        else:
            # Estimating return risk based on review sentiment, etc.
            result['return_rate'] = None
            result['return_risk_level'] = self._estimate_return_risk(product, result)
        
        return result
    
    def _process_stock_data(self, product: Dict, days: int) -> Dict:
        """Process inventory/Out of stock data - Contains tight inventory signals"""
        data = product.get('data', {})
        
        result = {
            'out_of_stock_days': 0,
            'stockouts_count': 0,
            'last_in_stock': None,
            'inventory_tension': False,  # New: tight inventory signal
            'buybox_stock_level': None,  # New: Buy Box inventory levels
        }
        
        # Use price data to determine out-of-stock status (-1 means out of stock)
        # Amazon self-operated price
        amazon_prices = data.get('AMAZON', [])
        if amazon_prices:
            stockout_periods = self._detect_stockouts(amazon_prices, days)
            result['out_of_stock_days'] = stockout_periods['total_days']
            result['stockouts_count'] = stockout_periods['count']
        
        # New: Buy Box inventory level detection (Frequency of price changes via Buy Box)
        buybox_data = data.get('BUY_BOX_SHIPPING', [])
        if buybox_data:
            result['buybox_stock_level'] = self._estimate_buybox_inventory(buybox_data)
            # If Buy Box inventory level is low and OOS days>0, marked as tight inventory
            if result['buybox_stock_level'] == 'low' or result['out_of_stock_days'] > 0:
                result['inventory_tension'] = True
        
        # New: 90-day OOS percentage
        result['oos_rate_90d'] = self._calculate_oos_rate(data, 90)
        
        return result
    
    def _process_fee_data(self, product: Dict) -> Dict:
        """Process expense data - FBA fees, recommendation fees, etc."""
        data = product.get('data', {})
        
        result = {}
        
        # Recommendation fee ratio
        referral_fee_data = data.get('REFERRAL_FEE_PERCENT', [])
        if referral_fee_data:
            referral_fees = self._extract_time_series(referral_fee_data, 0)
            result['referral_fee_percent'] = round(referral_fees[-1], 2) if referral_fees else 15.0
        else:
            # Default referral fee 15%
            result['referral_fee_percent'] = 15.0
        
        # FBA fees (if there is)
        fba_fee_data = data.get('FULFILLMENT_FEE', [])
        if fba_fee_data:
            fba_fees = self._extract_time_series(fba_fee_data, 0)
            result['fba_fee'] = round(fba_fees[-1], 2) if fba_fees else None
        else:
            # Estimated FBA fees based on weight
            weight = product.get('packageWeight', 0) or product.get('itemWeight', 0)
            result['fba_fee'] = self._estimate_fba_fee(weight)
        
        # Calculate the referral fee amount based on the current Buy Box price
        if result.get('referral_fee_percent') and data.get('BUY_BOX_SHIPPING', []):
            buybox_prices = self._extract_time_series(data.get('BUY_BOX_SHIPPING', []), 0)
            if buybox_prices:
                current_price = buybox_prices[-1]
                result['referral_fee_amount'] = round(current_price * result['referral_fee_percent'] / 100, 2)
        
        return result
    
    def _calculate_derived_metrics(self, data: Dict, days: int) -> Dict:
        """Calculate derived indicators - Contains new indicators inspired by PDF"""
        result = {}
        
        # price change rate
        if data.get('min_price') and data.get('max_price') and data.get('max_price') > 0:
            result['price_volatility'] = round(
                (data['max_price'] - data['min_price']) / data['max_price'] * 100, 1
            )
        else:
            result['price_volatility'] = 0
        
        # New: pricing power index (Current price vs historical average price)
        if data.get('current_price') and data.get('price_365d_avg') and data['price_365d_avg'] > 0:
            result['pricing_power_index'] = round(
                (data['current_price'] - data['price_365d_avg']) / data['price_365d_avg'] * 100, 1
            )
        else:
            result['pricing_power_index'] = 0
        
        # New: Ranking deterioration rate (Current ranking vs 365-day average, positive value indicates ranking deterioration)
        if data.get('current_rank') and data.get('rank_365d_avg') and data['rank_365d_avg'] > 0:
            result['rank_deterioration_rate'] = round(
                (data['current_rank'] - data['rank_365d_avg']) / data['rank_365d_avg'] * 100, 1
            )
        else:
            result['rank_deterioration_rate'] = 0
        
        # profit margin estimate (Based on Buy Box price)
        if data.get('avg_price'):
            # Use actual cost data
            referral_fee = data.get('referral_fee_percent', 15) / 100
            fba_fee = data.get('fba_fee', 5.0)
            
            # Rough estimate: Assume cost is 35 of price%
            estimated_cost = data['avg_price'] * 0.35
            referral_amount = data['avg_price'] * referral_fee
            
            profit = data['avg_price'] - estimated_cost - referral_amount - fba_fee
            result['estimated_profit'] = round(profit, 2)
            result['estimated_margin'] = round(profit / data['avg_price'] * 100, 1) if data['avg_price'] > 0 else 0
        else:
            result['estimated_profit'] = None
            result['estimated_margin'] = None
        
        # competitive intensity
        if data.get('current_offers'):
            if data['current_offers'] < 5:
                result['competition_level'] = 'Low'
            elif data['current_offers'] < 15:
                result['competition_level'] = 'Medium'
            else:
                result['competition_level'] = 'High'
        else:
            result['competition_level'] = 'Unknown'
        
        # New: Brand monopoly assessment
        result['brand_dominance'] = self._assess_brand_dominance(data)
        
        # New: Seller concentration
        result['seller_concentration'] = self._calculate_seller_concentration(data)
        
        # Product life cycle judgment
        result['lifecycle_stage'] = self._determine_lifecycle_stage(data)
        
        return result
    
    def _assess_brand_dominance(self, data: Dict) -> Dict:
        """Assess brand monopoly - Learning based on PDF"""
        offers = data.get('current_offers', 0) or 0
        fba_offers = data.get('fba_offers', 0) or 0
        buybox_winner = data.get('buybox_winner', '')
        brand = data.get('brand', '')
        
        # Determine whether it is self-operated by the brand
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
        """Calculate seller concentration"""
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
        """Estimate return risk level"""
        rating = review_data.get('current_rating', 0) or 0
        category = product.get('categoryTree', [{}])[0].get('name', '') if product.get('categoryTree') else ''
        
        # high risk category
        high_return_categories = ['Apparel', 'Shoes', 'Clothing', 'Fashion']
        
        if rating < 4.0:
            return 'High'
        elif rating < 4.2 or any(cat in category for cat in high_return_categories):
            return 'Medium'
        else:
            return 'Low'
    
    def _estimate_buybox_inventory(self, buybox_data: List) -> str:
        """Estimate Buy Box inventory levels"""
        # Simplify estimating: Based on price change frequency
        if len(buybox_data) < 10:
            return 'unknown'
        
        # If prices change frequently, inventory may fluctuate greatly
        recent_changes = sum(1 for i in range(1, min(20, len(buybox_data))) 
                            if abs(buybox_data[i] - buybox_data[i-1]) > 0.01)
        
        if recent_changes > 10:
            return 'low'  # Prices fluctuate greatly and inventory may be tight
        elif recent_changes > 5:
            return 'medium'
        else:
            return 'normal'
    
    def _calculate_oos_rate(self, data: Dict, days: int) -> float:
        """Calculate OOS rate (Out of Stock Rate)"""
        amazon_data = data.get('AMAZON', [])
        if not amazon_data or len(amazon_data) < 2:
            return 0.0
        
        # Calculate the proportion of days out of stock
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
        """Estimate FBA fees based on weight"""
        if weight <= 0:
            return 5.0
        
        # Simplified estimation model
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
        """Calculate the average of a specified time window"""
        if not values:
            return None
        # Assuming that the data is uniformly distributed, take the data of the last N days
        points = max(1, int(len(values) * days / 365))
        window_values = values[-points:] if points < len(values) else values
        return round(np.mean(window_values), 2) if window_values else None
    
    def _calculate_window_min(self, values: List[float], days: int) -> Optional[float]:
        """Calculate the minimum value of a specified time window"""
        if not values:
            return None
        points = max(1, int(len(values) * days / 365))
        window_values = values[-points:] if points < len(values) else values
        return round(min(window_values), 2) if window_values else None
    
    def _calculate_window_max(self, values: List[float], days: int) -> Optional[float]:
        """Calculate the maximum value of a specified time window"""
        if not values:
            return None
        points = max(1, int(len(values) * days / 365))
        window_values = values[-points:] if points < len(values) else values
        return round(max(window_values), 2) if window_values else None
    
    def _count_rank_drops(self, ranks: List[float], days: int) -> int:
        """Statistical ranking drops (A larger ranking number indicates a decline)"""
        if not ranks or len(ranks) < 2:
            return 0
        
        points = max(1, int(len(ranks) * days / 365))
        window_ranks = ranks[-points:] if points < len(ranks) else ranks
        
        drops = 0
        for i in range(1, len(window_ranks)):
            if window_ranks[i] > window_ranks[i-1] * 1.05:  # Ranking deteriorated by more than 5%
                drops += 1
        
        return drops
    
    def _count_seller_changes(self, seller_history: List) -> int:
        """Count the number of changes in Buy Box sellers"""
        if not seller_history or len(seller_history) < 2:
            return 0
        
        changes = 0
        for i in range(1, len(seller_history)):
            if seller_history[i] != seller_history[i-1]:
                changes += 1
        
        return changes
    
    def _calculate_price_stability(self, prices: List[float]) -> str:
        """Calculate price stability"""
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
        """Count the number of significant price drops"""
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
        """Calculate trends"""
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
        """Calculate comment growth"""
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
        """Detect out-of-stock situations"""
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
        """Estimated monthly sales based on BSR"""
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
        """Determine product life cycle stage"""
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
        """Extract package size information"""
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
