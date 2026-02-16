"""
竞品分析器
自动发现相似产品并进行多维度对比分析
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CompetitorProfile:
    """竞品画像"""
    asin: str
    title: str
    brand: str
    current_price: float
    avg_price: float
    min_price: float
    max_price: float
    current_rank: int
    avg_rank: int
    rating: float
    review_count: int
    offers: int
    is_amazon: bool
    similarity_score: float  # 与目标产品的相似度


class CompetitorAnalyzer:
    """
    竞品分析器
    
    功能:
    1. 基于类目/价格/关键词发现相似产品
    2. 多维度对比分析
    3. 竞争优势/劣势识别
    4. 市场空白点发现
    """
    
    def __init__(self):
        self.comparison_weights = {
            'price': 0.25,
            'rank': 0.25,
            'rating': 0.20,
            'reviews': 0.15,
            'offers': 0.15
        }
    
    def find_similar_products(self, target_data: Dict, candidate_products: List[Dict]) -> List[CompetitorProfile]:
        """
        发现相似产品
        
        Args:
            target_data: 目标产品数据
            candidate_products: 候选产品列表
        
        Returns:
            按相似度排序的竞品列表
        """
        competitors = []
        
        target_category = target_data.get('category', '')
        target_price = target_data.get('current_price', 0) or 0
        
        for product in candidate_products:
            profile = self._create_profile(product)
            
            # 计算相似度
            similarity = self._calculate_similarity(target_data, product)
            profile.similarity_score = similarity
            
            # 过滤条件：价格相近且相似度足够
            price_diff = abs(profile.current_price - target_price) / max(target_price, 0.01)
            
            if price_diff < 0.5 and similarity > 0.3:  # 价格差异<50% 且 相似度>30%
                competitors.append(profile)
        
        # 按相似度排序
        competitors.sort(key=lambda x: x.similarity_score, reverse=True)
        return competitors[:10]  # 返回前10个
    
    def _create_profile(self, product: Dict) -> CompetitorProfile:
        """创建产品画像"""
        data = product.get('data', {})
        
        # 提取当前价格
        new_prices = data.get('NEW', [])
        current_price = new_prices[-1] if len(new_prices) > 0 else 0
        if hasattr(current_price, 'tolist'):
            current_price = current_price.item() if hasattr(current_price, 'item') else float(current_price)
        
        # 提取排名
        sales_ranks = data.get('SALES', [])
        current_rank = sales_ranks[-1] if len(sales_ranks) > 0 else 999999
        if hasattr(current_rank, 'tolist'):
            current_rank = current_rank.item() if hasattr(current_rank, 'item') else int(current_rank)
        
        # 提取评分
        ratings = data.get('RATING', [])
        rating = ratings[-1] if len(ratings) > 0 else 0
        if hasattr(rating, 'tolist'):
            rating = rating.item() if hasattr(rating, 'item') else float(rating)
        
        # 提取评论数
        reviews = data.get('COUNT_REVIEWS', [])
        review_count = reviews[-1] if len(reviews) > 0 else 0
        if hasattr(review_count, 'tolist'):
            review_count = review_count.item() if hasattr(review_count, 'item') else int(review_count)
        
        # 提取卖家数
        offers_data = data.get('COUNT_NEW', [])
        offers = offers_data[-1] if len(offers_data) > 0 else 0
        if hasattr(offers, 'tolist'):
            offers = offers.item() if hasattr(offers, 'item') else int(offers)
        
        return CompetitorProfile(
            asin=product.get('asin', 'Unknown'),
            title=product.get('title', 'Unknown')[:50],
            brand=product.get('brand', 'Unknown'),
            current_price=current_price,
            avg_price=current_price,  # 简化处理
            min_price=current_price,
            max_price=current_price,
            current_rank=current_rank,
            avg_rank=current_rank,
            rating=rating,
            review_count=review_count,
            offers=offers,
            is_amazon=product.get('is_amazon_selling', False),
            similarity_score=0.0
        )
    
    def _calculate_similarity(self, target: Dict, candidate: Dict) -> float:
        """计算产品相似度"""
        scores = []
        
        target_data = target.get('data', {})
        cand_data = candidate.get('data', {})
        
        # 价格相似度
        target_price = self._get_last_value(target_data.get('NEW', []))
        cand_price = self._get_last_value(cand_data.get('NEW', []))
        if target_price > 0 and cand_price > 0:
            price_sim = 1 - abs(target_price - cand_price) / max(target_price, cand_price)
            scores.append(price_sim * self.comparison_weights['price'])
        
        # BSR 相似度 (同量级)
        target_rank = self._get_last_value(target_data.get('SALES', []))
        cand_rank = self._get_last_value(cand_data.get('SALES', []))
        if target_rank > 0 and cand_rank > 0:
            rank_sim = 1 - abs(np.log10(target_rank) - np.log10(cand_rank)) / 5
            scores.append(max(0, rank_sim) * self.comparison_weights['rank'])
        
        # 评分相似度
        target_rating = self._get_last_value(target_data.get('RATING', []))
        cand_rating = self._get_last_value(cand_data.get('RATING', []))
        if target_rating > 0 and cand_rating > 0:
            rating_sim = 1 - abs(target_rating - cand_rating) / 5
            scores.append(rating_sim * self.comparison_weights['rating'])
        
        # 类目相似度
        if target.get('category') == candidate.get('category'):
            scores.append(0.2)  # 同类目加分
        
        return sum(scores) / sum(self.comparison_weights.values()) if scores else 0.0
    
    def _get_last_value(self, arr):
        """获取数组最后一个有效值"""
        if arr is None or len(arr) == 0:
            return 0
        val = arr[-1]
        if hasattr(val, 'tolist'):
            val = val.item() if hasattr(val, 'item') else val
        return val
    
    def generate_comparison_report(self, target: Dict, competitors: List[CompetitorProfile]) -> str:
        """生成竞品对比报告"""
        
        target_profile = self._create_profile(target)
        
        report = f"""# 🔍 竞品对比分析报告

## 目标产品
- **ASIN**: {target_profile.asin}
- **产品**: {target_profile.title}
- **品牌**: {target_profile.brand}
- **价格**: ${target_profile.current_price:.2f}
- **BSR**: #{target_profile.current_rank:,}
- **评分**: {target_profile.rating:.1f}⭐ ({target_profile.review_count} 评论)

## 竞品概览

发现 **{len(competitors)}** 个相似竞品

| 排名 | ASIN | 相似度 | 价格 | BSR | 评分 | 卖家数 | Amazon |
|------|------|--------|------|-----|------|--------|--------|
"""
        
        for i, comp in enumerate(competitors[:5], 1):
            report += f"| {i} | {comp.asin} | {comp.similarity_score:.0%} | ${comp.current_price:.2f} | #{comp.current_rank:,} | {comp.rating:.1f}⭐ | {comp.offers} | {'是' if comp.is_amazon else '否'} |\n"
        
        report += """
## 详细对比分析

### 1. 价格竞争格局

```
价格分布 (USD)
"""
        
        # 价格区间分析
        all_prices = [target_profile.current_price] + [c.current_price for c in competitors]
        min_p, max_p = min(all_prices), max(all_prices)
        avg_p = np.mean(all_prices)
        
        report += f"""
最低: ${min_p:.2f}  {'← 目标产品' if target_profile.current_price == min_p else ''}
平均: ${avg_p:.2f}
最高: ${max_p:.2f}  {'← 目标产品' if target_profile.current_price == max_p else ''}
目标: ${target_profile.current_price:.2f}
```

**价格定位**: {'低于市场' if target_profile.current_price < avg_p else '高于市场'} {'%.1f' % abs((target_profile.current_price - avg_p) / avg_p * 100)}%

"""
        
        # BSR 对比
        report += """
### 2. 销量排名对比

```
BSR 层级 (越低越好)
"""
        
        all_ranks = [target_profile.current_rank] + [c.current_rank for c in competitors]
        best_rank = min(all_ranks)
        
        sorted_by_rank = sorted([(target_profile.asin[:10], target_profile.current_rank, '目标')] + 
                               [(c.asin[:10], c.current_rank, '竞品') for c in competitors], 
                               key=lambda x: x[1])
        
        for asin, rank, ptype in sorted_by_rank[:5]:
            bar = '█' * int(20 - np.log10(max(rank, 1)))
            marker = ' ← ' + ptype if ptype == '目标' else ''
            report += f"#{rank:>6,} {bar}{marker}\n"
        
        report += f"""```

**销量地位**: {'领先' if target_profile.current_rank == best_rank else '中等' if target_profile.current_rank < np.median(all_ranks) else '落后'}

"""
        
        # 竞争优势分析
        report += """
### 3. 竞争优势矩阵

| 维度 | 目标产品 | 市场最佳 | 差距 | 建议 |
|------|----------|----------|------|------|
"""
        
        # 价格优势
        best_price = min(all_prices)
        price_diff = ((target_profile.current_price - best_price) / best_price * 100) if best_price > 0 else 0
        price_status = '✅ 最低' if target_profile.current_price == best_price else f'⚠️ +{price_diff:.0f}%'
        report += f"| 价格 | ${target_profile.current_price:.2f} | ${best_price:.2f} | {price_status} | {'保持' if target_profile.current_price == best_price else '考虑降价'} |\n"
        
        # BSR 优势
        bsr_diff = ((target_profile.current_rank - best_rank) / best_rank * 100) if best_rank > 0 else 0
        bsr_status = '✅ 最佳' if target_profile.current_rank == best_rank else f'⚠️ +{bsr_diff:.0f}%'
        report += f"| BSR | #{target_profile.current_rank:,} | #{best_rank:,} | {bsr_status} | {'保持' if target_profile.current_rank == best_rank else '提升排名'} |\n"
        
        # 评分
        all_ratings = [target_profile.rating] + [c.rating for c in competitors if c.rating > 0]
        best_rating = max(all_ratings) if all_ratings else 0
        rating_status = '✅ 最高' if target_profile.rating >= best_rating else '⚠️ 落后'
        report += f"| 评分 | {target_profile.rating:.1f}⭐ | {best_rating:.1f}⭐ | {rating_status} | {'保持' if target_profile.rating >= best_rating else '改进质量'} |\n"
        
        # 评论数
        all_reviews = [target_profile.review_count] + [c.review_count for c in competitors]
        best_reviews = max(all_reviews)
        review_status = '✅ 最多' if target_profile.review_count >= best_reviews else '⚠️ 落后'
        report += f"| 评论 | {target_profile.review_count:,} | {best_reviews:,} | {review_status} | {'保持' if target_profile.review_count >= best_reviews else '积累评论'} |\n"
        
        # 卖家数
        all_offers = [target_profile.offers] + [c.offers for c in competitors]
        min_offers = min(all_offers)
        offers_status = '✅ 最少' if target_profile.offers <= min_offers else '⚠️ 较多'
        report += f"| 卖家 | {target_profile.offers} | {min_offers} | {offers_status} | {'抓住机会' if target_profile.offers <= min_offers else '差异化'} |\n"
        
        report += """
### 4. 竞争策略建议

#### 我们的优势
"""
        
        advantages = []
        if target_profile.current_price <= min(all_prices) * 1.05:
            advantages.append("✅ **价格优势** - 有竞争力的定价空间")
        if target_profile.current_rank <= np.median(all_ranks):
            advantages.append("✅ **销量优势** - 良好的市场地位")
        if target_profile.rating >= 4.5:
            advantages.append("✅ **质量优势** - 高评分带来信任")
        if target_profile.offers <= 5:
            advantages.append("✅ **竞争稀少** - 低竞争环境")
        
        if advantages:
            report += '\n'.join(advantages)
        else:
            report += "⚠️ 未发现有明显优势，需要寻找差异化定位"
        
        report += """

#### 需要改进的方面
"""
        
        disadvantages = []
        if target_profile.current_price > avg_p * 1.1:
            disadvantages.append(f"❌ **价格偏高** - 比均价高 {(target_profile.current_price/avg_p-1)*100:.0f}%")
        if target_profile.current_rank > np.median(all_ranks):
            disadvantages.append("❌ **销量落后** - BSR 处于后半段")
        if target_profile.rating < 4.3:
            disadvantages.append("❌ **评分偏低** - 需要提升产品质量")
        if target_profile.review_count < 500:
            disadvantages.append("❌ **评论不足** - 缺乏社会证明")
        
        if disadvantages:
            report += '\n'.join(disadvantages)
        else:
            report += "✅ 各方面表现均衡"
        
        report += """

### 5. 市场机会点

"""
        
        # 分析市场空白
        opportunities = []
        
        # 价格空白
        price_gaps = []
        sorted_prices = sorted(all_prices)
        for i in range(len(sorted_prices) - 1):
            gap = sorted_prices[i+1] - sorted_prices[i]
            if gap > sorted_prices[i] * 0.3:  # 30% 以上的价格空白
                price_gaps.append((sorted_prices[i], sorted_prices[i+1]))
        
        if price_gaps:
            opportunities.append(f"💡 **价格空白**: 在 ${price_gaps[0][0]:.2f} - ${price_gaps[0][1]:.2f} 之间存在价格空白")
        
        # 评分空白
        low_rating_competitors = [c for c in competitors if c.rating < 4.0]
        if low_rating_competitors:
            opportunities.append(f"💡 **质量机会**: {len(low_rating_competitors)} 个竞品评分低于 4.0，可通过优质产品差异化")
        
        # 断货机会
        if target_profile.current_rank < 10000 and target_profile.offers <= 3:
            opportunities.append("💡 **供应机会**: 热销产品但卖家少，存在供应缺口")
        
        if opportunities:
            report += '\n\n'.join(opportunities)
        else:
            report += "⚠️ 市场较为饱和，需要寻找细分领域或差异化定位"
        
        report += """

---

## 结论

"""
        
        # 总体结论
        advantages_count = len(advantages)
        disadvantages_count = len(disadvantages)
        
        if advantages_count > disadvantages_count:
            report += f"✅ **竞争地位良好** - 拥有 {advantages_count} 项优势 vs {disadvantages_count} 项劣势\n\n"
            report += "**建议**: 保持现有优势，同时针对劣势制定改进计划"
        elif advantages_count == disadvantages_count:
            report += f"⚠️ **竞争地位中等** - 优势与劣势相当 ({advantages_count} vs {disadvantages_count})\n\n"
            report += "**建议**: 寻找差异化突破口，避免正面竞争"
        else:
            report += f"❌ **竞争地位较弱** - 仅有 {advantages_count} 项优势 vs {disadvantages_count} 项劣势\n\n"
            report += "**建议**: 重新评估进入策略，或寻找细分市场"
        
        return report
    
    def identify_market_gaps(self, competitors: List[CompetitorProfile]) -> List[Dict]:
        """识别市场空白点"""
        gaps = []
        
        if not competitors:
            return gaps
        
        # 价格空白
        prices = sorted([c.current_price for c in competitors])
        for i in range(len(prices) - 1):
            if prices[i+1] / prices[i] > 1.5:  # 50% 以上差距
                gaps.append({
                    'type': 'price_gap',
                    'description': f'Price gap between ${prices[i]:.2f} and ${prices[i+1]:.2f}',
                    'opportunity': f'Target ${(prices[i] + prices[i+1]) / 2:.2f} price point'
                })
        
        # 评分空白
        low_quality = [c for c in competitors if c.rating < 4.0]
        if len(low_quality) >= len(competitors) * 0.3:
            gaps.append({
                'type': 'quality_gap',
                'description': f'{len(low_quality)} competitors have rating < 4.0',
                'opportunity': 'Enter with premium quality product'
            })
        
        # 功能空白 (需要标题分析)
        keywords = defaultdict(int)
        for c in competitors:
            # 简化处理：假设标题中有功能关键词
            pass
        
        return gaps
