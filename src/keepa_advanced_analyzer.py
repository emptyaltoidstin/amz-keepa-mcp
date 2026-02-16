"""
Keepa 深度分析器
================
基于Keepa API完整数据的高级分析
"""

import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PriceTrend:
    """价格趋势分析"""
    current: float
    avg_30d: float
    avg_90d: float
    avg_180d: float
    trend: str  # 'up', 'down', 'stable'
    volatility: float  # 波动率
    change_percent: float  # 变化百分比


@dataclass
class CompetitionMetrics:
    """竞争指标"""
    total_offers: int
    fba_offers: int
    fbm_offers: int
    amazon_present: bool
    buy_box_seller: str
    seller_concentration: float  # 卖家集中度 HHI
    price_spread: float  # 价格离散度


@dataclass
class Seasonality:
    """季节性分析"""
    has_seasonality: bool
    peak_months: List[int]
    low_months: List[int]
    seasonality_score: float  # 0-100


class KeepaAdvancedAnalyzer:
    """Keepa高级分析器 - 深度数据挖掘"""
    
    def __init__(self):
        self.domain_names = {
            1: 'US', 2: 'UK', 3: 'DE', 4: 'FR', 5: 'JP',
            6: 'CA', 7: 'CN', 8: 'IT', 9: 'ES', 10: 'IN',
            11: 'MX', 12: 'BR', 13: 'AU', 14: 'NL', 15: 'SA',
            16: 'AE', 17: 'SE', 18: 'PL', 19: 'TR', 20: 'BE'
        }
    
    def analyze_product(self, product: dict) -> Dict:
        """
        执行完整的产品深度分析
        
        Returns:
            包含所有分析结果的字典
        """
        results = {
            'product_identity': self._analyze_identity(product),
            'price_analysis': self._analyze_price_trends(product),
            'sales_analysis': self._analyze_sales_rank(product),
            'competition_analysis': self._analyze_competition(product),
            'rating_analysis': self._analyze_ratings(product),
            'seasonality': self._analyze_seasonality(product),
            'buybox_analysis': self._analyze_buybox(product),
            'risk_signals': self._detect_risk_signals(product),
        }
        
        # 计算综合健康度评分
        results['health_score'] = self._calculate_health_score(results)
        
        return results
    
    def _analyze_identity(self, product: dict) -> Dict:
        """分析产品身份信息"""
        domain_id = product.get('domainId', 1)
        
        # 转换包装尺寸
        package_dims = {}
        for key in ['packageHeight', 'packageLength', 'packageWidth', 'packageWeight']:
            if key in product and product[key]:
                # Keepa使用百分之一单位
                if 'Weight' in key:
                    package_dims[key] = product[key] / 100  # 转换为磅
                else:
                    package_dims[key] = product[key] / 100  # 转换为英寸
        
        return {
            'asin': product.get('asin', 'N/A'),
            'title': product.get('title', 'N/A'),
            'brand': product.get('brand', 'N/A'),
            'manufacturer': product.get('manufacturer', 'N/A'),
            'model': product.get('model', 'N/A'),
            'category': product.get('rootCategory', 'N/A'),
            'product_group': product.get('productGroup', 'N/A'),
            'domain': self.domain_names.get(domain_id, 'US'),
            'last_update': self._keepa_time_to_datetime(product.get('lastUpdate', 0)),
            'is_adult': product.get('isAdult', False),
            'is_sns': product.get('isSNS', False),
            'amazon_offer': product.get('amazonOffer', False),
            'package_dimensions': package_dims,
            'image_count': product.get('imageCount', 0),
            'variation_count': len(product.get('variations', [])),
        }
    
    def _analyze_price_trends(self, product: dict) -> Dict:
        """分析价格趋势"""
        data = product.get('data', {})
        
        # 分析不同价格类型
        price_types = ['NEW', 'AMAZON', 'USED', 'BUY_BOX_SHIPPING']
        analysis = {}
        
        for ptype in price_types:
            if ptype not in data or len(data[ptype]) == 0:
                continue
            
            prices = np.array(data[ptype])
            times = np.array(data.get(f'{ptype}_time', []))
            
            if len(prices) == 0:
                continue
            
            # 过滤无效值(-1)
            valid_mask = prices > 0
            valid_prices = prices[valid_mask] / 100  # 转换为美元
            valid_times = times[valid_mask] if len(times) == len(prices) else []
            
            if len(valid_prices) == 0:
                continue
            
            current = valid_prices[-1]
            
            # 计算不同时间段的平均价格
            if len(valid_times) > 0:
                now = datetime.utcnow()
                days_30 = self._datetime_to_keepa_minutes(now - timedelta(days=30))
                days_90 = self._datetime_to_keepa_minutes(now - timedelta(days=90))
                days_180 = self._datetime_to_keepa_minutes(now - timedelta(days=180))
                
                mask_30 = valid_times >= days_30
                mask_90 = valid_times >= days_90
                mask_180 = valid_times >= days_180
                
                avg_30d = np.mean(valid_prices[mask_30]) if np.any(mask_30) else current
                avg_90d = np.mean(valid_prices[mask_90]) if np.any(mask_90) else current
                avg_180d = np.mean(valid_prices[mask_180]) if np.any(mask_180) else current
            else:
                avg_30d = avg_90d = avg_180d = current
            
            # 趋势判断
            if current > avg_90d * 1.05:
                trend = 'up'
            elif current < avg_90d * 0.95:
                trend = 'down'
            else:
                trend = 'stable'
            
            # 波动率
            volatility = np.std(valid_prices) / np.mean(valid_prices) * 100 if np.mean(valid_prices) > 0 else 0
            
            # 变化百分比
            change_percent = ((current - avg_90d) / avg_90d * 100) if avg_90d > 0 else 0
            
            analysis[ptype] = {
                'current': round(current, 2),
                'avg_30d': round(avg_30d, 2),
                'avg_90d': round(avg_90d, 2),
                'avg_180d': round(avg_180d, 2),
                'trend': trend,
                'volatility': round(volatility, 2),
                'change_percent': round(change_percent, 2),
                'min': round(np.min(valid_prices), 2),
                'max': round(np.max(valid_prices), 2),
            }
        
        return analysis
    
    def _analyze_sales_rank(self, product: dict) -> Dict:
        """分析销售排名趋势"""
        data = product.get('data', {})
        
        if 'SALES' not in data or len(data['SALES']) == 0:
            return {'error': 'No sales rank data'}
        
        ranks = np.array(data['SALES'])
        times = np.array(data.get('SALES_time', []))
        
        # 过滤无效值(0或-1)
        valid_mask = ranks > 0
        valid_ranks = ranks[valid_mask]
        valid_times = times[valid_mask] if len(times) == len(ranks) else []
        
        if len(valid_ranks) == 0:
            return {'error': 'No valid sales rank data'}
        
        current = int(valid_ranks[-1])
        
        # 计算趋势
        if len(valid_ranks) >= 30:
            recent_avg = np.mean(valid_ranks[-30:])
            older_avg = np.mean(valid_ranks[:-30]) if len(valid_ranks) > 30 else recent_avg
            
            if recent_avg < older_avg * 0.9:
                trend = 'improving'  # 排名变好(数字变小)
            elif recent_avg > older_avg * 1.1:
                trend = 'declining'  # 排名变差
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        # 排名分类
        if current < 1000:
            rank_level = 'best_seller'
        elif current < 10000:
            rank_level = 'good'
        elif current < 50000:
            rank_level = 'average'
        elif current < 100000:
            rank_level = 'poor'
        else:
            rank_level = 'very_poor'
        
        # 估算销量
        estimated_sales = self._estimate_sales_from_rank(current, product.get('rootCategory'))
        
        return {
            'current': current,
            'avg_30d': int(np.mean(valid_ranks[-30:])) if len(valid_ranks) >= 30 else current,
            'avg_90d': int(np.mean(valid_ranks[-90:])) if len(valid_ranks) >= 90 else current,
            'trend': trend,
            'rank_level': rank_level,
            'estimated_monthly_sales': estimated_sales,
            'volatility': round(np.std(valid_ranks) / np.mean(valid_ranks) * 100, 2),
        }
    
    def _analyze_competition(self, product: dict) -> Dict:
        """分析竞争格局"""
        data = product.get('data', {})
        
        # 获取卖家数量历史
        offer_counts = {}
        for key in ['COUNT_NEW', 'COUNT_USED', 'COUNT_FBA']:
            if key in data and len(data[key]) > 0:
                values = np.array(data[key])
                valid = values[values > 0]
                if len(valid) > 0:
                    offer_counts[key] = int(valid[-1])
        
        # 获取offers详情
        offers = product.get('offers', [])
        live_offers_indices = product.get('liveOffersOrder', [])
        
        fba_count = 0
        fbm_count = 0
        seller_ids = []
        prices = []
        
        for idx in live_offers_indices:
            if idx < len(offers):
                offer = offers[idx]
                seller_ids.append(offer.get('sellerId', 'Unknown'))
                
                if offer.get('isFBA', False):
                    fba_count += 1
                else:
                    fbm_count += 1
                
                # 获取当前价格
                csv_data = offer.get('offerCSV', [])
                if len(csv_data) > 0:
                    prices.append(csv_data[-1] / 100)
        
        # 计算HHI集中度指数
        if len(seller_ids) > 0:
            unique, counts = np.unique(seller_ids, return_counts=True)
            shares = counts / len(seller_ids)
            hhi = np.sum(shares ** 2) * 10000
        else:
            hhi = 0
        
        # 价格离散度
        if len(prices) > 1:
            price_spread = (max(prices) - min(prices)) / np.mean(prices) * 100
        else:
            price_spread = 0
        
        return {
            'total_live_offers': len(live_offers_indices),
            'fba_offers': fba_count,
            'fbm_offers': fbm_count,
            'amazon_present': product.get('amazonOffer', False),
            'seller_concentration_hhi': round(hhi, 2),
            'price_spread_percent': round(price_spread, 2),
            'offer_history': offer_counts,
            'competition_level': 'high' if len(live_offers_indices) > 15 else 'medium' if len(live_offers_indices) > 5 else 'low',
        }
    
    def _analyze_ratings(self, product: dict) -> Dict:
        """分析评分和评价"""
        data = product.get('data', {})
        
        ratings = {}
        
        # 评分历史
        if 'RATING' in data and len(data['RATING']) > 0:
            rating_values = np.array(data['RATING'])
            valid_ratings = rating_values[rating_values > 0] / 10  # Keepa存储为0-50
            
            if len(valid_ratings) > 0:
                ratings['current'] = round(valid_ratings[-1], 1)
                ratings['avg'] = round(np.mean(valid_ratings), 1)
                ratings['trend'] = 'up' if valid_ratings[-1] > np.mean(valid_ratings[:-10]) else 'stable'
        
        # 评论数量
        if 'COUNT_REVIEWS' in data and len(data['COUNT_REVIEWS']) > 0:
            reviews = np.array(data['COUNT_REVIEWS'])
            valid_reviews = reviews[reviews > 0]
            
            if len(valid_reviews) > 0:
                ratings['review_count'] = int(valid_reviews[-1])
                
                # 计算近期增长速度
                if len(valid_reviews) >= 30:
                    recent_growth = valid_reviews[-1] - valid_reviews[-30]
                    ratings['monthly_review_growth'] = recent_growth
        
        # 评分健康度
        if 'current' in ratings:
            if ratings['current'] >= 4.5:
                ratings['health'] = 'excellent'
            elif ratings['current'] >= 4.0:
                ratings['health'] = 'good'
            elif ratings['current'] >= 3.5:
                ratings['health'] = 'average'
            else:
                ratings['health'] = 'poor'
        
        return ratings
    
    def _analyze_seasonality(self, product: dict) -> Seasonality:
        """分析季节性"""
        data = product.get('data', {})
        
        if 'SALES' not in data or len(data['SALES']) < 180:
            return Seasonality(has_seasonality=False, peak_months=[], low_months=[], seasonality_score=0)
        
        ranks = np.array(data['SALES'])
        times = np.array(data.get('SALES_time', []))
        
        # 转换为DataFrame进行分析
        df_data = []
        for i, (rank, time) in enumerate(zip(ranks, times)):
            if rank > 0 and time > 0:
                dt = self._keepa_time_to_datetime(time)
                df_data.append({'date': dt, 'rank': rank, 'month': dt.month})
        
        if len(df_data) < 180:
            return Seasonality(has_seasonality=False, peak_months=[], low_months=[], seasonality_score=0)
        
        df = pd.DataFrame(df_data)
        
        # 按月聚合
        monthly_avg = df.groupby('month')['rank'].mean()
        
        # 找出峰值月份(排名较低=销量较高)
        sorted_months = monthly_avg.sort_values()
        peak_months = sorted_months.head(3).index.tolist()
        low_months = sorted_months.tail(3).index.tolist()
        
        # 计算季节性强度
        seasonality_score = (monthly_avg.max() - monthly_avg.min()) / monthly_avg.mean() * 100
        
        has_seasonality = seasonality_score > 20
        
        return Seasonality(
            has_seasonality=has_seasonality,
            peak_months=peak_months,
            low_months=low_months,
            seasonality_score=round(seasonality_score, 2)
        )
    
    def _analyze_buybox(self, product: dict) -> Dict:
        """分析Buy Box"""
        data = product.get('data', {})
        
        buybox_history = product.get('buyBoxSellerIdHistory', [])
        
        if len(buybox_history) == 0:
            return {'has_buybox_data': False}
        
        # 统计Buy Box轮换情况
        seller_changes = 0
        current_seller = None
        sellers = []
        
        for entry in buybox_history:
            if isinstance(entry, dict):
                seller = entry.get('sellerId', 'Unknown')
            else:
                seller = str(entry)
            
            sellers.append(seller)
            
            if current_seller is None:
                current_seller = seller
            elif seller != current_seller:
                seller_changes += 1
                current_seller = seller
        
        # 计算Amazon获得Buy Box的比例
        amazon_wins = sum(1 for s in sellers if s == 'ATVPDKIKX0DER')  # Amazon US seller ID
        amazon_share = amazon_wins / len(sellers) * 100 if sellers else 0
        
        # Buy Box稳定性
        stability = 'stable' if seller_changes < len(sellers) * 0.1 else 'volatile'
        
        # Buy Box价格分析
        if 'BUY_BOX_SHIPPING' in data and len(data['BUY_BOX_SHIPPING']) > 0:
            bb_prices = np.array(data['BUY_BOX_SHIPPING'])
            valid_bb = bb_prices[bb_prices > 0] / 100
            
            if len(valid_bb) > 0:
                avg_buybox_price = round(np.mean(valid_bb), 2)
                current_buybox_price = round(valid_bb[-1], 2)
            else:
                avg_buybox_price = current_buybox_price = 0
        else:
            avg_buybox_price = current_buybox_price = 0
        
        return {
            'has_buybox_data': True,
            'seller_changes_90d': seller_changes,
            'stability': stability,
            'amazon_share_percent': round(amazon_share, 2),
            'current_buybox_price': current_buybox_price,
            'avg_buybox_price': avg_buybox_price,
            'unique_sellers_count': len(set(sellers)),
        }
    
    def _detect_risk_signals(self, product: dict) -> List[Dict]:
        """检测风险信号"""
        risks = []
        
        data = product.get('data', {})
        
        # 1. 价格大幅下降风险
        if 'NEW' in data and len(data['NEW']) > 30:
            prices = np.array(data['NEW'])
            valid = prices[prices > 0]
            
            if len(valid) > 30:
                recent_avg = np.mean(valid[-30:])
                previous_avg = np.mean(valid[-60:-30]) if len(valid) >= 60 else recent_avg
                
                if previous_avg > 0 and recent_avg < previous_avg * 0.8:
                    risks.append({
                        'type': 'price_drop',
                        'level': 'high',
                        'desc': f'价格近30天下降 {(1-recent_avg/previous_avg)*100:.0f}%，可能触发价格战',
                    })
        
        # 2. 排名持续下滑风险
        if 'SALES' in data and len(data['SALES']) > 60:
            ranks = np.array(data['SALES'])
            valid = ranks[ranks > 0]
            
            if len(valid) > 60:
                recent_avg = np.mean(valid[-30:])
                previous_avg = np.mean(valid[-60:-30])
                
                if recent_avg > previous_avg * 1.5:  # 排名数字变大=销量变差
                    risks.append({
                        'type': 'rank_decline',
                        'level': 'medium',
                        'desc': '销售排名持续下滑，需求可能正在萎缩',
                    })
        
        # 3. 断货风险
        if 'OUT_OF_STOCK' in data:
            oos_events = len(data['OUT_OF_STOCK'])
            if oos_events > 5:
                risks.append({
                    'type': 'stock_out',
                    'level': 'high',
                    'desc': f'历史断货次数较多 ({oos_events}次)，供应链不稳定',
                })
        
        # 4. 评价差评风险
        if 'RATING' in data and len(data['RATING']) > 0:
            ratings = np.array(data['RATING'])
            valid = ratings[ratings > 0]
            
            if len(valid) > 0 and valid[-1] < 35:  # 低于3.5星
                risks.append({
                    'type': 'low_rating',
                    'level': 'high',
                    'desc': f'评分较低 ({valid[-1]/10:.1f}/5)，可能影响转化',
                })
        
        # 5. 卖家数量激增风险
        if 'COUNT_NEW' in data and len(data['COUNT_NEW']) > 30:
            counts = np.array(data['COUNT_NEW'])
            valid = counts[counts > 0]
            
            if len(valid) > 30:
                recent = np.mean(valid[-30:])
                previous = np.mean(valid[:-30]) if len(valid) > 30 else recent
                
                if previous > 0 and recent > previous * 2:
                    risks.append({
                        'type': 'seller_surge',
                        'level': 'medium',
                        'desc': '新卖家数量激增，竞争正在加剧',
                    })
        
        return risks
    
    def _calculate_health_score(self, analysis: Dict) -> Dict:
        """计算综合健康度评分"""
        scores = []
        
        # 价格健康度 (25%)
        price_score = 70
        if 'price_analysis' in analysis:
            prices = analysis['price_analysis']
            if 'NEW' in prices:
                new_price = prices['NEW']
                if new_price['trend'] == 'stable':
                    price_score = 85
                elif new_price['trend'] == 'up':
                    price_score = 75
                else:
                    price_score = 60
                
                if new_price['volatility'] > 30:
                    price_score -= 15
        scores.append(('price', price_score, 0.25))
        
        # 销售健康度 (25%)
        sales_score = 70
        if 'sales_analysis' in analysis and 'error' not in analysis['sales_analysis']:
            sales = analysis['sales_analysis']
            rank = sales.get('current', 100000)
            if rank < 10000:
                sales_score = 90
            elif rank < 50000:
                sales_score = 75
            elif rank < 100000:
                sales_score = 60
            else:
                sales_score = 40
            
            if sales.get('trend') == 'improving':
                sales_score += 5
            elif sales.get('trend') == 'declining':
                sales_score -= 15
        scores.append(('sales', sales_score, 0.25))
        
        # 竞争健康度 (20%)
        comp_score = 70
        if 'competition_analysis' in analysis:
            comp = analysis['competition_analysis']
            if comp.get('competition_level') == 'low':
                comp_score = 85
            elif comp.get('competition_level') == 'medium':
                comp_score = 70
            else:
                comp_score = 50
            
            if comp.get('amazon_present'):
                comp_score -= 10
        scores.append(('competition', comp_score, 0.20))
        
        # 评价健康度 (20%)
        rating_score = 70
        if 'rating_analysis' in analysis:
            ratings = analysis['rating_analysis']
            if 'current' in ratings:
                current = ratings['current']
                if current >= 4.5:
                    rating_score = 95
                elif current >= 4.0:
                    rating_score = 80
                elif current >= 3.5:
                    rating_score = 60
                else:
                    rating_score = 40
        scores.append(('rating', rating_score, 0.20))
        
        # Buy Box健康度 (10%)
        buybox_score = 70
        if 'buybox_analysis' in analysis and analysis['buybox_analysis'].get('has_buybox_data'):
            bb = analysis['buybox_analysis']
            if bb.get('stability') == 'stable':
                buybox_score = 85
            else:
                buybox_score = 60
        scores.append(('buybox', buybox_score, 0.10))
        
        # 计算加权总分
        total_score = sum(score * weight for _, score, weight in scores)
        
        # 风险扣分
        risks = analysis.get('risk_signals', [])
        risk_penalty = sum(10 if r['level'] == 'high' else 5 for r in risks)
        total_score = max(0, total_score - risk_penalty)
        
        return {
            'overall': round(total_score, 1),
            'breakdown': {name: score for name, score, _ in scores},
            'risk_penalty': risk_penalty,
            'grade': 'A' if total_score >= 80 else 'B' if total_score >= 70 else 'C' if total_score >= 60 else 'D',
        }
    
    def _estimate_sales_from_rank(self, rank: int, category: Optional[int]) -> int:
        """根据排名估算月销量"""
        # 简化的估算模型
        if rank < 1000:
            return 1000 + int((1000 - rank) * 5)
        elif rank < 10000:
            return 500 + int((10000 - rank) * 0.05)
        elif rank < 50000:
            return 100 + int((50000 - rank) * 0.01)
        elif rank < 100000:
            return 20 + int((100000 - rank) * 0.002)
        else:
            return max(5, int(500000 / rank))
    
    def _keepa_time_to_datetime(self, keepa_minutes: int) -> datetime:
        """将Keepa分钟时间转换为datetime"""
        # Keepa时间起点: 2011-01-01 00:00:00 UTC
        base = datetime(2011, 1, 1)
        return base + timedelta(minutes=keepa_minutes)
    
    def _datetime_to_keepa_minutes(self, dt: datetime) -> int:
        """将datetime转换为Keepa分钟时间"""
        base = datetime(2011, 1, 1)
        return int((dt - base).total_seconds() / 60)


def format_advanced_analysis(analysis: Dict) -> str:
    """格式化高级分析结果为可读文本"""
    lines = []
    
    lines.append("=" * 80)
    lines.append("🔍 Keepa 深度分析报告")
    lines.append("=" * 80)
    
    # 产品身份
    identity = analysis['product_identity']
    lines.append(f"\n📦 产品信息")
    lines.append(f"  ASIN: {identity['asin']}")
    lines.append(f"  标题: {identity['title'][:60]}...")
    lines.append(f"  品牌: {identity['brand']}")
    lines.append(f"  站点: {identity['domain']}")
    
    # 健康度评分
    health = analysis['health_score']
    lines.append(f"\n💯 综合健康度评分: {health['overall']:.0f}/100 (等级: {health['grade']})")
    lines.append(f"  分项评分:")
    for name, score in health['breakdown'].items():
        lines.append(f"    - {name}: {score}分")
    
    # 价格分析
    lines.append(f"\n💰 价格分析")
    for ptype, pdata in analysis['price_analysis'].items():
        lines.append(f"  {ptype}:")
        lines.append(f"    当前: ${pdata['current']}, 趋势: {pdata['trend']}, 波动: {pdata['volatility']}%")
    
    # 销售分析
    if 'error' not in analysis['sales_analysis']:
        sales = analysis['sales_analysis']
        lines.append(f"\n📈 销售分析")
        lines.append(f"  当前排名: {sales['current']:,}")
        lines.append(f"  趋势: {sales['trend']}")
        lines.append(f"  估算月销量: {sales['estimated_monthly_sales']} 件")
    
    # 竞争分析
    comp = analysis['competition_analysis']
    lines.append(f"\n🏪 竞争分析")
    lines.append(f"  活跃卖家: {comp['total_live_offers']} (FBA: {comp['fba_offers']}, FBM: {comp['fbm_offers']})")
    lines.append(f"  竞争程度: {comp['competition_level']}")
    lines.append(f"  卖家集中度(HHI): {comp['seller_concentration_hhi']:.0f}")
    
    # 风险信号
    risks = analysis['risk_signals']
    if risks:
        lines.append(f"\n⚠️ 风险信号 ({len(risks)}个)")
        for risk in risks:
            emoji = "🔴" if risk['level'] == 'high' else "🟡"
            lines.append(f"  {emoji} [{risk['type']}] {risk['desc']}")
    else:
        lines.append(f"\n✅ 未发现明显风险信号")
    
    lines.append("\n" + "=" * 80)
    
    return "\n".join(lines)
