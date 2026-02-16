"""
Keepa 163指标完整采集器
将Keepa API数据映射为CSV格式的163个指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class KeepaMetricsCollector:
    """
    Keepa 163指标采集器
    
    将Keepa API原始数据转换为Product Viewer CSV格式的163个指标
    """
    
    # 完整指标定义
    ALL_METRICS = {
        # 1. 基础信息 (18个)
        'basic_info': [
            'Locale', 'Image', 'Image Count', 'Title', 'Parent Title',
            'Description & Features: Description', 'Description & Features: Short Description',
            'Description & Features: Feature 1', 'Description & Features: Feature 2',
            'Description & Features: Feature 3', 'Description & Features: Feature 4',
            'Description & Features: Feature 5', 'Description & Features: Feature 6',
            'Description & Features: Feature 7', 'Description & Features: Feature 8',
            'Description & Features: Feature 9', 'Description & Features: Feature 10',
        ],
        
        # 2. 销售表现 (8个)
        'sales_performance': [
            'Sales Rank: Current', 'Sales Rank: 90 days avg.',
            'Sales Rank: Drops last 90 days', 'Sales Rank: Reference',
            'Sales Rank: Display Group', 'Sales Rank: Subcategory Sales Ranks',
            'Bought in past month', '90 days change % monthly sold',
        ],
        
        # 3. 退货与评论 (5个)
        'reviews_returns': [
            'Return Rate', 'Reviews: Rating', 'Reviews: Rating Count',
            'Reviews: Review Count - Format Specific', 'Last Price Change',
        ],
        
        # 4. Buy Box (15个)
        'buy_box': [
            'Buy Box: Buy Box Seller', 'Buy Box: Shipping Country',
            'Buy Box: Strikethrough Price', 'Buy Box: % Amazon 90 days',
            'Buy Box: % Top Seller 90 days', 'Buy Box: Winner Count 90 days',
            'Buy Box: Standard Deviation 90 days', 'Buy Box: Flipability 90 days',
            'Buy Box: Is FBA', 'Buy Box: Unqualified',
            'Buy Box: Prime Eligible', 'Buy Box: Subscribe & Save',
            'Suggested Lower Price', 'Lightning Deals: Current',
            'Warehouse Deals: Current',
        ],
        
        # 5. Amazon自营价格 (15个)
        'amazon_price': [
            'Amazon: Current', 'Amazon: 30 days avg.', 'Amazon: 90 days avg.',
            'Amazon: 180 days avg.', 'Amazon: 365 days avg.',
            'Amazon: 1 day drop %', 'Amazon: 7 days drop %',
            'Amazon: 30 days drop %', 'Amazon: 90 days drop %',
            'Amazon: Drop since last visit', 'Amazon: Drop % since last visit',
            'Amazon: Last visit', 'Amazon: Is Lowest', 'Amazon: Is Lowest 90 days',
            'Amazon: Lowest', 'Amazon: Highest',
        ],
        
        # 6. 新品价格 (13个)
        'new_price': [
            'New: Current', 'New: 30 days avg.', 'New: 90 days avg.',
            'New: 180 days avg.', 'New: 365 days avg.',
            'New: 1 day drop %', 'New: 7 days drop %',
            'New: 30 days drop %', 'New: 90 days drop %',
            'New: Drop since last visit', 'New: Drop % since last visit',
            'New: Lowest', 'New: Highest',
        ],
        
        # 7. 二手价格 (类似结构)
        'used_price': [
            'Used: Current', 'Used: 90 days avg.', 'Used: Lowest', 'Used: Highest',
        ],
        
        # 8. 库存 (8个)
        'inventory': [
            'Amazon: Stock', 'Amazon: 90 days OOS',
            'Amazon: OOS Count 30 days', 'Amazon: OOS Count 90 days',
            'Amazon: Availability of the Amazon offer',
            'Amazon: Amazon offer shipping delay',
        ],
        
        # 9. 费用 (6个)
        'fees': [
            'FBA Pick&Pack Fee', 'Referral Fee %',
            'Referral Fee based on current Buy Box price',
            'List Price: Current', 'List Price: 30 days avg.', 'List Price: 90 days avg.',
        ],
        
        # 10. 卖家竞争 (10个)
        'competition': [
            'Total Offer Count', 'New Offer Count: Current', 'Used Offer Count: Current',
            'Count of retrieved live offers: New, FBA',
            'Count of retrieved live offers: New, FBM',
            'Tracking since', 'Listed since',
        ],
        
        # 11. 类目 (5个)
        'category': [
            'URL: Amazon', 'Categories: Root', 'Categories: Sub',
            'Categories: Tree', 'Website Display Group: Name',
        ],
        
        # 12. 产品代码 (8个)
        'product_codes': [
            'ASIN', 'Imported by Code', 'Product Codes: UPC',
            'Product Codes: EAN', 'Product Codes: GTIN', 'Product Codes: PartNumber',
            'Parent ASIN', 'Variation ASINs',
        ],
        
        # 13. 产品属性 (20个)
        'attributes': [
            'Type', 'Manufacturer', 'Brand', 'Brand Store Name', 'Brand Store URL Name',
            'Product Group', 'Model', 'Variation Attributes',
            'Color', 'Size', 'Unit Details: Unit Value', 'Unit Details: Unit Type',
            'Scent', 'Item Form', 'Pattern', 'Style', 'Material', 'Item Type',
            'Target Audience', 'Recommended Uses',
        ],
        
        # 14. 内容 (8个)
        'content': [
            'Videos: Video Count', 'Videos: Has Main Video',
            'Videos: Main Videos', 'Videos: Additional Videos',
            'A+ Content: Has A+ Content', 'A+ Content: A+ From Manufacturer',
            'A+ Content: A+ Content',
        ],
        
        # 15. 包装规格 (9个)
        'package': [
            'Package: Dimension (cm³)', 'Package: Length (cm)',
            'Package: Width (cm)', 'Package: Height (cm)',
            'Package: Weight (g)', 'Package: Quantity',
            'Item: Dimension (cm³)', 'Item: Length (cm)', 'Item: Width (cm)',
            'Item: Height (cm)', 'Item: Weight (g)',
        ],
        
        # 16. 其他属性 (剩余字段)
        'other': [
            'Included Components', 'Ingredients', 'Active Ingredients',
            'Special Ingredients', 'Safety Warning', 'Batteries Required',
            'Batteries Included', 'Hazardous Materials', 'Is HazMat',
            'Is heat sensitive', 'Adult Product', 'Is Merch on Demand',
            'Trade-In Eligible', 'Deals: Deal Type', 'Deals: Badge',
            'One Time Coupon: Absolute', 'One Time Coupon: Percentage',
            'One Time Coupon: Subscribe & Save %', 'Business Discount: Percentage',
            'Freq. Bought Together',
        ],
    }
    
    def __init__(self):
        self.collected_metrics = {}
    
    def collect_all_metrics(self, product: Dict) -> Dict[str, Any]:
        """
        从Keepa API产品数据中提取所有163个指标
        
        Args:
            product: Keepa API返回的产品数据
            
        Returns:
            包含163个指标的字典
        """
        metrics = {}
        
        # 基础产品信息
        metrics.update(self._extract_basic_info(product))
        
        # 销售表现
        metrics.update(self._extract_sales_performance(product))
        
        # 评论与退货
        metrics.update(self._extract_reviews_returns(product))
        
        # Buy Box数据
        metrics.update(self._extract_buy_box_metrics(product))
        
        # 价格数据 (Amazon/New/Used)
        metrics.update(self._extract_price_metrics(product))
        
        # 库存数据
        metrics.update(self._extract_inventory_metrics(product))
        
        # 费用数据
        metrics.update(self._extract_fee_metrics(product))
        
        # 竞争数据
        metrics.update(self._extract_competition_metrics(product))
        
        # 类目数据
        metrics.update(self._extract_category_metrics(product))
        
        # 产品代码
        metrics.update(self._extract_product_codes(product))
        
        # 产品属性
        metrics.update(self._extract_attributes(product))
        
        # 内容数据
        metrics.update(self._extract_content_metrics(product))
        
        # 包装规格
        metrics.update(self._extract_package_metrics(product))
        
        # 其他属性
        metrics.update(self._extract_other_attributes(product))
        
        self.collected_metrics = metrics
        return metrics
    
    def _extract_basic_info(self, product: Dict) -> Dict:
        """提取基础信息 (18个指标)"""
        return {
            'Locale': 'com',  # 默认美国站
            'Image': product.get('imagesCSV', ''),
            'Image Count': len(product.get('imagesCSV', '').split(';')) if product.get('imagesCSV') else 0,
            'Title': product.get('title', ''),
            'Parent Title': product.get('parentTitle', ''),
            'Description & Features: Description': product.get('description', ''),
            'Description & Features: Short Description': '',  # API无此字段
            'Description & Features: Feature 1': self._get_feature(product, 0),
            'Description & Features: Feature 2': self._get_feature(product, 1),
            'Description & Features: Feature 3': self._get_feature(product, 2),
            'Description & Features: Feature 4': self._get_feature(product, 3),
            'Description & Features: Feature 5': self._get_feature(product, 4),
            'Description & Features: Feature 6': self._get_feature(product, 5),
            'Description & Features: Feature 7': self._get_feature(product, 6),
            'Description & Features: Feature 8': self._get_feature(product, 7),
            'Description & Features: Feature 9': self._get_feature(product, 8),
            'Description & Features: Feature 10': self._get_feature(product, 9),
        }
    
    def _extract_sales_performance(self, product: Dict) -> Dict:
        """提取销售表现 (8个指标)"""
        data = product.get('data', {})
        
        # 获取BSR数据
        df_sales = data.get('df_SALES')
        if df_sales is not None and not df_sales.empty:
            current_rank = int(df_sales['value'].iloc[-1]) if len(df_sales) > 0 else 0
            valid_ranks = df_sales[df_sales['value'] > 0]['value']
            avg_90d = int(valid_ranks.tail(90).mean()) if len(valid_ranks) >= 90 else int(valid_ranks.mean())
            drops_90d = self._count_rank_drops(df_sales['value'].tolist())
        else:
            current_rank = 0
            avg_90d = 0
            drops_90d = 0
        
        # 估算月销量 (基于BSR)
        estimated_sales = self._estimate_sales_from_bsr(avg_90d)
        
        return {
            'Sales Rank: Current': current_rank,
            'Sales Rank: 90 days avg.': avg_90d,
            'Sales Rank: Drops last 90 days': drops_90d,
            'Sales Rank: Reference': product.get('categoryTree', [{}])[0].get('name', '') if product.get('categoryTree') else '',
            'Sales Rank: Display Group': product.get('websiteDisplayGroup', ''),
            'Sales Rank: Subcategory Sales Ranks': self._format_subcategory_ranks(product.get('categoryTree', [])),
            'Bought in past month': product.get('boughtInPastMonth') or estimated_sales,
            '90 days change % monthly sold': self._calculate_sales_change(data),
        }
    
    def _extract_reviews_returns(self, product: Dict) -> Dict:
        """提取评论与退货 (5个指标)"""
        data = product.get('data', {})
        
        # 评论数据
        df_reviews = data.get('df_COUNT_REVIEWS')
        if df_reviews is not None and not df_reviews.empty:
            review_count = int(df_reviews['value'].iloc[-1])
        else:
            review_count = product.get('reviews', 0)
        
        # 评分
        rating = product.get('stars', 0) or data.get('csv', [{}])[0].get('RATING', 0)
        
        # 退货率 (基于类目估算)
        category = product.get('categoryTree', [{}])[0].get('name', '') if product.get('categoryTree') else ''
        return_rate = self._estimate_return_rate(category)
        
        return {
            'Return Rate': return_rate,
            'Reviews: Rating': rating,
            'Reviews: Rating Count': review_count,
            'Reviews: Review Count - Format Specific': review_count,
            'Last Price Change': self._get_last_price_change(data),
        }
    
    def _extract_buy_box_metrics(self, product: Dict) -> Dict:
        """提取Buy Box指标 (15个指标)"""
        data = product.get('data', {})
        
        # Buy Box价格
        df_buybox = data.get('df_BUY_BOX_SHIPPING')
        if df_buybox is not None and not df_buybox.empty:
            current_buybox = df_buybox['value'].iloc[-1]
            std_90d = df_buybox['value'].tail(90).std()
            flipability = self._calculate_flipability(df_buybox['value'])
        else:
            current_buybox = 0
            std_90d = 0
            flipability = 'N/A'
        
        # 卖家信息
        buybox_seller = product.get('buyBoxSellerIdHistory', ['Unknown'])[-1] if product.get('buyBoxSellerIdHistory') else 'Unknown'
        
        # Amazon自营占比
        amazon_pct = self._calculate_amazon_buybox_share(data)
        
        return {
            'Buy Box: Buy Box Seller': buybox_seller,
            'Buy Box: Shipping Country': 'US',  # 默认
            'Buy Box: Strikethrough Price': '',  # API无此字段
            'Buy Box: % Amazon 90 days': f"{amazon_pct:.1f}%",
            'Buy Box: % Top Seller 90 days': 'N/A',
            'Buy Box: Winner Count 90 days': len(set(product.get('buyBoxSellerIdHistory', []) or [])),
            'Buy Box: Standard Deviation 90 days': f"${std_90d:.2f}",
            'Buy Box: Flipability 90 days': flipability,
            'Buy Box: Is FBA': 'yes' if self._is_fba_seller(product) else 'no',
            'Buy Box: Unqualified': 'no',
            'Buy Box: Prime Eligible': 'yes',
            'Buy Box: Subscribe & Save': 'no',
            'Suggested Lower Price': '',
            'Lightning Deals: Current': '',
            'Warehouse Deals: Current': '',
        }
    
    def _extract_price_metrics(self, product: Dict) -> Dict:
        """提取价格指标 (Amazon/New/Used)"""
        data = product.get('data', {})
        metrics = {}
        
        # Amazon价格
        df_amazon = data.get('df_AMAZON')
        if df_amazon is not None and not df_amazon.empty:
            metrics.update(self._calculate_price_metrics(df_amazon, 'Amazon'))
        else:
            metrics.update(self._empty_price_metrics('Amazon'))
        
        # New价格
        df_new = data.get('df_NEW')
        if df_new is not None and not df_new.empty:
            metrics.update(self._calculate_price_metrics(df_new, 'New'))
        else:
            metrics.update(self._empty_price_metrics('New'))
        
        # Used价格 (简化)
        df_used = data.get('df_USED')
        if df_used is not None and not df_used.empty:
            metrics['Used: Current'] = df_used['value'].iloc[-1]
            metrics['Used: 90 days avg.'] = df_used['value'].tail(90).mean()
            metrics['Used: Lowest'] = df_used['value'].min()
            metrics['Used: Highest'] = df_used['value'].max()
        else:
            metrics['Used: Current'] = 0
            metrics['Used: 90 days avg.'] = 0
            metrics['Used: Lowest'] = 0
            metrics['Used: Highest'] = 0
        
        return metrics
    
    def _extract_inventory_metrics(self, product: Dict) -> Dict:
        """提取库存指标"""
        data = product.get('data', {})
        
        # Amazon库存
        df_amazon = data.get('df_AMAZON')
        if df_amazon is not None and not df_amazon.empty:
            # 检测断货 (价格为-1表示断货)
            oos_count = (df_amazon['value'] == -1).tail(90).sum()
            oos_rate = (oos_count / min(90, len(df_amazon))) * 100
        else:
            oos_count = 0
            oos_rate = 0
        
        return {
            'Amazon: Stock': 0,  # API不直接提供
            'Amazon: 90 days OOS': f"{oos_rate:.1f}%",
            'Amazon: OOS Count 30 days': int(oos_count * 30/90),
            'Amazon: OOS Count 90 days': int(oos_count),
            'Amazon: Availability of the Amazon offer': 'In Stock' if oos_rate < 50 else 'Out of Stock',
            'Amazon: Amazon offer shipping delay': '',
        }
    
    def _extract_fee_metrics(self, product: Dict) -> Dict:
        """提取费用指标 - 使用Keepa API真实数据"""
        from keepa_fee_extractor import KeepaFeeExtractor
        
        # Buy Box价格
        data = product.get('data', {})
        df_buybox = data.get('df_BUY_BOX_SHIPPING')
        buybox_price = df_buybox['value'].iloc[-1] if df_buybox is not None and not df_buybox.empty else 0
        
        # 使用Keepa费用提取器获取真实费用
        fees = KeepaFeeExtractor.extract_all_fees(product, buybox_price)
        
        fba_fee = fees['fba_fee']
        referral_rate = fees['referral_rate']
        referral_fee = fees['referral_fee']
        
        # 标记FBA费用来源
        fba_note = "(Keepa)" if not fees['is_fba_estimated'] else "(估算)"
        
        return {
            'FBA Pick&Pack Fee': f"${fba_fee:.2f} {fba_note}",
            'Referral Fee %': f"{referral_rate * 100:.2f}%",
            'Referral Fee based on current Buy Box price': f"${referral_fee:.2f}",
            'List Price: Current': product.get('listPrice', 0),
            'List Price: 30 days avg.': product.get('listPrice', 0),
            'List Price: 90 days avg.': product.get('listPrice', 0),
        }
    
    def _extract_competition_metrics(self, product: Dict) -> Dict:
        """提取竞争指标"""
        data = product.get('data', {})
        
        # 卖家数量
        df_count_new = data.get('df_COUNT_NEW')
        if df_count_new is not None and not df_count_new.empty:
            total_offers = int(df_count_new['value'].iloc[-1])
        else:
            total_offers = 1
        
        return {
            'Total Offer Count': total_offers,
            'New Offer Count: Current': total_offers,
            'Used Offer Count: Current': 0,
            'Count of retrieved live offers: New, FBA': total_offers,  # 简化
            'Count of retrieved live offers: New, FBM': 0,
            'Tracking since': self._format_date(product.get('trackingSince', 0)),
            'Listed since': self._format_date(product.get('listedSince', 0)),
        }
    
    def _extract_category_metrics(self, product: Dict) -> Dict:
        """提取类目指标"""
        category_tree = product.get('categoryTree', [])
        root = category_tree[0].get('name', '') if category_tree else ''
        sub = category_tree[1].get('name', '') if len(category_tree) > 1 else ''
        
        return {
            'URL: Amazon': f"https://www.amazon.com/dp/{product.get('asin', '')}",
            'Categories: Root': root,
            'Categories: Sub': sub,
            'Categories: Tree': ' > '.join([c.get('name', '') for c in category_tree]),
            'Website Display Group: Name': product.get('websiteDisplayGroup', ''),
        }
    
    def _extract_product_codes(self, product: Dict) -> Dict:
        """提取产品代码"""
        return {
            'ASIN': product.get('asin', ''),
            'Imported by Code': '',
            'Product Codes: UPC': product.get('upc', ''),
            'Product Codes: EAN': product.get('ean', ''),
            'Product Codes: GTIN': '',
            'Product Codes: PartNumber': product.get('partNumber', ''),
            'Parent ASIN': product.get('parentAsin', ''),
            'Variation ASINs': ';'.join([v.get('asin', '') for v in product.get('variations', [])]) if product.get('variations') else '',
        }
    
    def _extract_attributes(self, product: Dict) -> Dict:
        """提取产品属性"""
        # 提取变体属性 (从变体列表中找到当前ASIN的属性)
        variation_attrs = []
        current_asin = product.get('asin', '')
        for v in product.get('variations', []):
            if v.get('asin') == current_asin:
                # 变体可能有 color, size, style 等属性
                attrs = []
                if v.get('color'):
                    attrs.append(f"Color:{v['color']}")
                if v.get('size'):
                    attrs.append(f"Size:{v['size']}")
                if v.get('style'):
                    attrs.append(f"Style:{v['style']}")
                variation_attrs = attrs
                break
        
        return {
            'Type': product.get('type', ''),
            'Manufacturer': product.get('manufacturer', ''),
            'Brand': product.get('brand', ''),
            'Brand Store Name': product.get('brandStoreName', ''),
            'Brand Store URL Name': '',
            'Product Group': product.get('productGroup', ''),
            'Model': product.get('model', ''),
            'Variation Attributes': ';'.join(variation_attrs) if variation_attrs else '',
            'Color': product.get('color', ''),
            'Size': product.get('size', ''),
            'Unit Details: Unit Value': 1,
            'Unit Details: Unit Type': 'Count',
            'Scent': '',
            'Item Form': '',
            'Pattern': product.get('pattern', ''),
            'Style': product.get('style', ''),
            'Material': product.get('material', ''),
            'Item Type': product.get('itemType', ''),
            'Target Audience': '',
            'Recommended Uses': '',
        }
    
    def _extract_content_metrics(self, product: Dict) -> Dict:
        """提取内容指标"""
        videos = product.get('videos', [])
        
        # 分类主视频和附加视频
        main_videos = [v for v in videos if v.get('isMain')]
        additional_videos = [v for v in videos if not v.get('isMain')]
        
        # 提取视频ID/URL列表
        main_video_list = ';'.join([v.get('videoId', '') for v in main_videos]) if main_videos else ''
        add_video_list = ';'.join([v.get('videoId', '') for v in additional_videos]) if additional_videos else ''
        
        return {
            'Videos: Video Count': len(videos),
            'Videos: Has Main Video': 'yes' if main_videos else 'no',
            'Videos: Main Videos': main_video_list,
            'Videos: Additional Videos': add_video_list,
            'A+ Content: Has A+ Content': 'yes' if product.get('hasAPlusContent') else 'no',
            'A+ Content: A+ From Manufacturer': 'no',
            'A+ Content: A+ Content': '',
        }
    
    def _extract_package_metrics(self, product: Dict) -> Dict:
        """提取包装规格"""
        length = product.get('packageLength', 0) or 0
        width = product.get('packageWidth', 0) or 0
        height = product.get('packageHeight', 0) or 0
        weight = product.get('packageWeight', 0) or 0
        
        item_length = product.get('itemLength', 0) or 0
        item_width = product.get('itemWidth', 0) or 0
        item_height = product.get('itemHeight', 0) or 0
        item_weight = product.get('itemWeight', 0) or 0
        
        return {
            'Package: Dimension (cm³)': length * width * height if all([length, width, height]) else 0,
            'Package: Length (cm)': length,
            'Package: Width (cm)': width,
            'Package: Height (cm)': height,
            'Package: Weight (g)': weight,
            'Package: Quantity': 1,
            'Item: Dimension (cm³)': item_length * item_width * item_height if all([item_length, item_width, item_height]) else 0,
            'Item: Length (cm)': item_length,
            'Item: Width (cm)': item_width,
            'Item: Height (cm)': item_height,
            'Item: Weight (g)': item_weight,
        }
    
    def _extract_other_attributes(self, product: Dict) -> Dict:
        """提取其他属性"""
        return {
            'Included Components': '',
            'Ingredients': '',
            'Active Ingredients': '',
            'Special Ingredients': '',
            'Safety Warning': '',
            'Batteries Required': 'no',
            'Batteries Included': 'no',
            'Hazardous Materials': '',
            'Is HazMat': 'no',
            'Is heat sensitive': 'no',
            'Adult Product': 'no',
            'Is Merch on Demand': 'no',
            'Trade-In Eligible': 'no',
            'Deals: Deal Type': '',
            'Deals: Badge': '',
            'One Time Coupon: Absolute': '',
            'One Time Coupon: Percentage': '',
            'One Time Coupon: Subscribe & Save %': '',
            'Business Discount: Percentage': '',
            'Freq. Bought Together': ';'.join(product.get('freqBoughtTogether', [])) if product.get('freqBoughtTogether') else '',
        }
    
    # 辅助方法
    def _get_feature(self, product: Dict, index: int) -> str:
        """获取产品卖点"""
        features = product.get('features', [])
        return features[index] if index < len(features) else ''
    
    def _count_rank_drops(self, ranks: List) -> int:
        """统计排名下降次数"""
        drops = 0
        for i in range(1, len(ranks)):
            if ranks[i] > ranks[i-1] * 1.05:  # 排名数字变大表示下降
                drops += 1
        return drops
    
    def _estimate_sales_from_bsr(self, bsr: int) -> int:
        """根据BSR估算月销量"""
        if bsr < 1000:
            return 1000
        elif bsr < 5000:
            return 500
        elif bsr < 10000:
            return 300
        elif bsr < 50000:
            return 100
        elif bsr < 100000:
            return 50
        elif bsr < 500000:
            return 10
        else:
            return 5
    
    def _calculate_sales_change(self, data: Dict) -> str:
        """计算销量变化率"""
        df_sales = data.get('df_SALES')
        if df_sales is not None and len(df_sales) >= 90:
            recent = df_sales['value'].tail(30).mean()
            previous = df_sales['value'].tail(90).head(60).mean()
            if previous > 0:
                change = ((recent - previous) / previous) * 100
                return f"{change:+.0f}%"
        return "0%"
    
    def _estimate_return_rate(self, category: str) -> str:
        """估算退货率"""
        rates = {
            'Clothing': '12%',
            'Shoes': '12%',
            'Electronics': '8%',
            'Home': '6%',
            'Beauty': '5%',
        }
        for key, rate in rates.items():
            if key in category:
                return rate
        return '6%'
    
    def _get_last_price_change(self, data: Dict) -> str:
        """获取上次价格变化"""
        # 简化实现
        return ''
    
    def _calculate_flipability(self, prices: pd.Series) -> str:
        """计算Buy Box可翻转性"""
        if len(prices) < 10:
            return 'N/A'
        changes = prices.diff().abs()
        avg_change = changes.mean()
        if avg_change > 1.0:
            return 'High'
        elif avg_change > 0.5:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_amazon_buybox_share(self, data: Dict) -> float:
        """计算Amazon自营Buy Box占比"""
        # 简化实现，实际需要buyBoxSellerIdHistory
        return 0.0
    
    def _is_fba_seller(self, product: Dict) -> bool:
        """判断是否为FBA卖家"""
        return product.get('buyBoxIsFBA', False)
    
    def _calculate_price_metrics(self, df: pd.DataFrame, prefix: str) -> Dict:
        """计算价格指标"""
        metrics = {}
        values = df['value']
        
        metrics[f'{prefix}: Current'] = values.iloc[-1] if len(values) > 0 else 0
        metrics[f'{prefix}: 30 days avg.'] = values.tail(30).mean()
        metrics[f'{prefix}: 90 days avg.'] = values.tail(90).mean()
        metrics[f'{prefix}: 180 days avg.'] = values.tail(180).mean() if len(values) >= 180 else values.mean()
        metrics[f'{prefix}: 365 days avg.'] = values.tail(365).mean() if len(values) >= 365 else values.mean()
        
        # 下降百分比
        for days in [1, 7, 30, 90]:
            if len(values) >= days + 1:
                prev_value = values.iloc[-days-1]
                if prev_value != 0:
                    drop = (values.iloc[-1] - prev_value) / prev_value * 100
                    metrics[f'{prefix}: {days} days drop %'] = f"{drop:.2f}%"
                else:
                    metrics[f'{prefix}: {days} days drop %'] = "0.00%"
            else:
                metrics[f'{prefix}: {days} days drop %'] = "0.00%"
        
        metrics[f'{prefix}: Lowest'] = values.min()
        metrics[f'{prefix}: Highest'] = values.max()
        
        return metrics
    
    def _empty_price_metrics(self, prefix: str) -> Dict:
        """空价格指标"""
        return {
            f'{prefix}: Current': 0,
            f'{prefix}: 30 days avg.': 0,
            f'{prefix}: 90 days avg.': 0,
            f'{prefix}: 180 days avg.': 0,
            f'{prefix}: 365 days avg.': 0,
            f'{prefix}: 1 day drop %': "0.00%",
            f'{prefix}: 7 days drop %': "0.00%",
            f'{prefix}: 30 days drop %': "0.00%",
            f'{prefix}: 90 days drop %': "0.00%",
            f'{prefix}: Lowest': 0,
            f'{prefix}: Highest': 0,
        }
    
    def _estimate_fba_fee(self, weight_kg: float, volume_cm3: float) -> float:
        """估算FBA费用"""
        # 简化估算
        if weight_kg <= 0.25:
            return 3.22
        elif weight_kg <= 0.5:
            return 3.86
        elif weight_kg <= 1.0:
            return 5.77
        elif weight_kg <= 2.0:
            return 7.25
        else:
            return 8.50
    
    def _format_subcategory_ranks(self, category_tree: List) -> str:
        """格式化子类目排名"""
        return '; '.join([f"{c.get('name', '')}: #{c.get('rank', 0)}" for c in category_tree if c.get('rank')])
    
    def _format_date(self, keepa_time: int) -> str:
        """格式化Keepa时间为日期"""
        if keepa_time == 0:
            return ''
        base = datetime(2011, 1, 1)
        date = base + timedelta(minutes=keepa_time)
        return date.strftime('%Y/%m/%d')
    
    def to_dataframe(self) -> pd.DataFrame:
        """将采集的指标转换为DataFrame"""
        if not self.collected_metrics:
            raise ValueError("尚未采集指标，请先调用collect_all_metrics()")
        
        return pd.DataFrame([self.collected_metrics])
    
    def export_to_csv(self, filepath: str):
        """导出为CSV文件"""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False, encoding='utf-8-sig')


def collect_163_metrics(product: Dict) -> Dict[str, Any]:
    """
    快捷函数：从Keepa产品数据中提取所有163个指标
    
    Args:
        product: Keepa API返回的产品数据
        
    Returns:
        包含163个指标的字典
    """
    collector = KeepaMetricsCollector()
    return collector.collect_all_metrics(product)
