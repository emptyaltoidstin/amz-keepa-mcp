"""
Competitive Product Analyzer
Automatically discover similar products and conduct multi-dimensional comparative analysis
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CompetitorProfile:
    """Competitor portraits"""
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
    similarity_score: float  # Similarity to target product


class CompetitorAnalyzer:
    """
    Competitive Product Analyzer
    
    Function:
    1. Based on categories/price/Keywords to find similar products
    2. Multi-dimensional comparative analysis
    3. Competitive advantage/Weakness identification
    4. Discovery of blank spots in the market
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
        Discover similar products
        
        Args:
            target_data: target product data
            candidate_products: Candidate product list
        
        Returns:
            List of competing products sorted by similarity
        """
        competitors = []
        
        target_category = target_data.get('category', '')
        target_price = target_data.get('current_price', 0) or 0
        
        for product in candidate_products:
            profile = self._create_profile(product)
            
            # Calculate similarity
            similarity = self._calculate_similarity(target_data, product)
            profile.similarity_score = similarity
            
            # Filter conditions: similar price and sufficient similarity
            price_diff = abs(profile.current_price - target_price) / max(target_price, 0.01)
            
            if price_diff < 0.5 and similarity > 0.3:  # price difference<50% and similarity>30%
                competitors.append(profile)
        
        # Sort by similarity
        competitors.sort(key=lambda x: x.similarity_score, reverse=True)
        return competitors[:10]  # Return the first 10
    
    def _create_profile(self, product: Dict) -> CompetitorProfile:
        """Create product images"""
        data = product.get('data', {})
        
        # Extract current price
        new_prices = data.get('NEW', [])
        current_price = new_prices[-1] if len(new_prices) > 0 else 0
        if hasattr(current_price, 'tolist'):
            current_price = current_price.item() if hasattr(current_price, 'item') else float(current_price)
        
        # Extract ranking
        sales_ranks = data.get('SALES', [])
        current_rank = sales_ranks[-1] if len(sales_ranks) > 0 else 999999
        if hasattr(current_rank, 'tolist'):
            current_rank = current_rank.item() if hasattr(current_rank, 'item') else int(current_rank)
        
        # Extract ratings
        ratings = data.get('RATING', [])
        rating = ratings[-1] if len(ratings) > 0 else 0
        if hasattr(rating, 'tolist'):
            rating = rating.item() if hasattr(rating, 'item') else float(rating)
        
        # Extract the number of comments
        reviews = data.get('COUNT_REVIEWS', [])
        review_count = reviews[-1] if len(reviews) > 0 else 0
        if hasattr(review_count, 'tolist'):
            review_count = review_count.item() if hasattr(review_count, 'item') else int(review_count)
        
        # Extract the number of sellers
        offers_data = data.get('COUNT_NEW', [])
        offers = offers_data[-1] if len(offers_data) > 0 else 0
        if hasattr(offers, 'tolist'):
            offers = offers.item() if hasattr(offers, 'item') else int(offers)
        
        return CompetitorProfile(
            asin=product.get('asin', 'Unknown'),
            title=product.get('title', 'Unknown')[:50],
            brand=product.get('brand', 'Unknown'),
            current_price=current_price,
            avg_price=current_price,  # Simplified processing
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
        """Calculate product similarity"""
        scores = []
        
        target_data = target.get('data', {})
        cand_data = candidate.get('data', {})
        
        # price similarity
        target_price = self._get_last_value(target_data.get('NEW', []))
        cand_price = self._get_last_value(cand_data.get('NEW', []))
        if target_price > 0 and cand_price > 0:
            price_sim = 1 - abs(target_price - cand_price) / max(target_price, cand_price)
            scores.append(price_sim * self.comparison_weights['price'])
        
        # BSR similarity (Same magnitude)
        target_rank = self._get_last_value(target_data.get('SALES', []))
        cand_rank = self._get_last_value(cand_data.get('SALES', []))
        if target_rank > 0 and cand_rank > 0:
            rank_sim = 1 - abs(np.log10(target_rank) - np.log10(cand_rank)) / 5
            scores.append(max(0, rank_sim) * self.comparison_weights['rank'])
        
        # Rating similarity
        target_rating = self._get_last_value(target_data.get('RATING', []))
        cand_rating = self._get_last_value(cand_data.get('RATING', []))
        if target_rating > 0 and cand_rating > 0:
            rating_sim = 1 - abs(target_rating - cand_rating) / 5
            scores.append(rating_sim * self.comparison_weights['rating'])
        
        # Category similarity
        if target.get('category') == candidate.get('category'):
            scores.append(0.2)  # Bonus points for similar categories
        
        return sum(scores) / sum(self.comparison_weights.values()) if scores else 0.0
    
    def _get_last_value(self, arr):
        """Get the last valid value of the array"""
        if arr is None or len(arr) == 0:
            return 0
        val = arr[-1]
        if hasattr(val, 'tolist'):
            val = val.item() if hasattr(val, 'item') else val
        return val
    
    def generate_comparison_report(self, target: Dict, competitors: List[CompetitorProfile]) -> str:
        """Generate competitive product comparison report"""
        
        target_profile = self._create_profile(target)
        
        report = f"""# 🔍 Competitive product comparison analysis report

## target product
- **ASIN**: {target_profile.asin}
- **Products**: {target_profile.title}
- **brand**: {target_profile.brand}
- **price**: ${target_profile.current_price:.2f}
- **BSR**: #{target_profile.current_rank:,}
- **score**: {target_profile.rating:.1f}⭐ ({target_profile.review_count} Comment)

## Competitive product overview

discover **{len(competitors)}** similar competing products

| Ranking | ASIN | Similarity | price | BSR | score | Number of sellers | Amazon |
|------|------|--------|------|-----|------|--------|--------|
"""
        
        for i, comp in enumerate(competitors[:5], 1):
            report += f"| {i} | {comp.asin} | {comp.similarity_score:.0%} | ${comp.current_price:.2f} | #{comp.current_rank:,} | {comp.rating:.1f}⭐ | {comp.offers} | {'Yes' if comp.is_amazon else 'No'} |\n"
        
        report += """
## Detailed comparative analysis

### 1. Price competition landscape

```
price distribution (USD)
"""
        
        # price range analysis
        all_prices = [target_profile.current_price] + [c.current_price for c in competitors]
        min_p, max_p = min(all_prices), max(all_prices)
        avg_p = np.mean(all_prices)
        
        report += f"""
lowest: ${min_p:.2f}  {'← Target Products' if target_profile.current_price == min_p else ''}
average: ${avg_p:.2f}
highest: ${max_p:.2f}  {'← Target Products' if target_profile.current_price == max_p else ''}
target: ${target_profile.current_price:.2f}
```

**price positioning**: {'below market' if target_profile.current_price < avg_p else 'above market'} {'%.1f' % abs((target_profile.current_price - avg_p) / avg_p * 100)}%

"""
        
        # BSR comparison
        report += """
### 2. Sales ranking comparison

```
BSR level (The lower the better)
"""
        
        all_ranks = [target_profile.current_rank] + [c.current_rank for c in competitors]
        best_rank = min(all_ranks)
        
        sorted_by_rank = sorted([(target_profile.asin[:10], target_profile.current_rank, 'target')] + 
                               [(c.asin[:10], c.current_rank, 'Competing products') for c in competitors], 
                               key=lambda x: x[1])
        
        for asin, rank, ptype in sorted_by_rank[:5]:
            bar = '█' * int(20 - np.log10(max(rank, 1)))
            marker = ' ← ' + ptype if ptype == 'target' else ''
            report += f"#{rank:>6,} {bar}{marker}\n"
        
        report += f"""```

**sales position**: {'leading' if target_profile.current_rank == best_rank else 'medium' if target_profile.current_rank < np.median(all_ranks) else 'backward'}

"""
        
        # Competitive advantage analysis
        report += """
### 3. Competitive advantage matrix

| Dimensions | target product | Best on the market | gap | suggestion |
|------|----------|----------|------|------|
"""
        
        # Price advantage
        best_price = min(all_prices)
        price_diff = ((target_profile.current_price - best_price) / best_price * 100) if best_price > 0 else 0
        price_status = '✅ Lowest' if target_profile.current_price == best_price else f'⚠️ +{price_diff:.0f}%'
        report += f"| price | ${target_profile.current_price:.2f} | ${best_price:.2f} | {price_status} | {'keep' if target_profile.current_price == best_price else 'Consider price reduction'} |\n"
        
        # BSR Advantages
        bsr_diff = ((target_profile.current_rank - best_rank) / best_rank * 100) if best_rank > 0 else 0
        bsr_status = '✅ Best' if target_profile.current_rank == best_rank else f'⚠️ +{bsr_diff:.0f}%'
        report += f"| BSR | #{target_profile.current_rank:,} | #{best_rank:,} | {bsr_status} | {'keep' if target_profile.current_rank == best_rank else 'Improve ranking'} |\n"
        
        # score
        all_ratings = [target_profile.rating] + [c.rating for c in competitors if c.rating > 0]
        best_rating = max(all_ratings) if all_ratings else 0
        rating_status = '✅ Highest' if target_profile.rating >= best_rating else '⚠️ Behind'
        report += f"| score | {target_profile.rating:.1f}⭐ | {best_rating:.1f}⭐ | {rating_status} | {'keep' if target_profile.rating >= best_rating else 'improve quality'} |\n"
        
        # Number of comments
        all_reviews = [target_profile.review_count] + [c.review_count for c in competitors]
        best_reviews = max(all_reviews)
        review_status = '✅ Most' if target_profile.review_count >= best_reviews else '⚠️ Behind'
        report += f"| Comment | {target_profile.review_count:,} | {best_reviews:,} | {review_status} | {'keep' if target_profile.review_count >= best_reviews else 'Accumulate comments'} |\n"
        
        # Number of sellers
        all_offers = [target_profile.offers] + [c.offers for c in competitors]
        min_offers = min(all_offers)
        offers_status = '✅ Minimum' if target_profile.offers <= min_offers else '⚠️ More'
        report += f"| seller | {target_profile.offers} | {min_offers} | {offers_status} | {'seize the opportunity' if target_profile.offers <= min_offers else 'Differentiation'} |\n"
        
        report += """
### 4. Competitive strategy suggestions

#### Our advantages
"""
        
        advantages = []
        if target_profile.current_price <= min(all_prices) * 1.05:
            advantages.append("✅ **Price advantage** - Competitive pricing space")
        if target_profile.current_rank <= np.median(all_ranks):
            advantages.append("✅ **Sales advantage** - good market position")
        if target_profile.rating >= 4.5:
            advantages.append("✅ **Quality advantage** - High ratings bring trust")
        if target_profile.offers <= 5:
            advantages.append("✅ **Little competition** - low competitive environment")
        
        if advantages:
            report += '\n'.join(advantages)
        else:
            report += "⚠️ No obvious advantages found, need to find differentiated positioning"
        
        report += """

#### Areas for improvement
"""
        
        disadvantages = []
        if target_profile.current_price > avg_p * 1.1:
            disadvantages.append(f"❌ **Price is on the high side** - Higher than average price {(target_profile.current_price/avg_p-1)*100:.0f}%")
        if target_profile.current_rank > np.median(all_ranks):
            disadvantages.append("❌ **Sales lag** - BSR is in the second half")
        if target_profile.rating < 4.3:
            disadvantages.append("❌ **Low rating** - Need to improve product quality")
        if target_profile.review_count < 500:
            disadvantages.append("❌ **Not enough comments** - lack of social proof")
        
        if disadvantages:
            report += '\n'.join(disadvantages)
        else:
            report += "✅ Balanced performance in all aspects"
        
        report += """

### 5. Market opportunities

"""
        
        # Analyze market gaps
        opportunities = []
        
        # price blank
        price_gaps = []
        sorted_prices = sorted(all_prices)
        for i in range(len(sorted_prices) - 1):
            gap = sorted_prices[i+1] - sorted_prices[i]
            if gap > sorted_prices[i] * 0.3:  # 30% The price above is blank
                price_gaps.append((sorted_prices[i], sorted_prices[i+1]))
        
        if price_gaps:
            opportunities.append(f"💡 **price blank**: exist ${price_gaps[0][0]:.2f} - ${price_gaps[0][1]:.2f} There is a price gap between")
        
        # Rating blank
        low_rating_competitors = [c for c in competitors if c.rating < 4.0]
        if low_rating_competitors:
            opportunities.append(f"💡 **quality opportunity**: {len(low_rating_competitors)} Competitors have a rating below 4.0 and can be differentiated through quality products")
        
        # Out of stock opportunity
        if target_profile.current_rank < 10000 and target_profile.offers <= 3:
            opportunities.append("💡 **supply opportunities**: Hot-selling products but few sellers, leaving a supply gap")
        
        if opportunities:
            report += '\n\n'.join(opportunities)
        else:
            report += "⚠️ The market is relatively saturated and it is necessary to find niche areas or differentiated positioning"
        
        report += """

---

## in conclusion

"""
        
        # Overall conclusion
        advantages_count = len(advantages)
        disadvantages_count = len(disadvantages)
        
        if advantages_count > disadvantages_count:
            report += f"✅ **Good competitive position** - own {advantages_count} Advantages vs. {disadvantages_count} Disadvantages\n\n"
            report += "**suggestion**: Maintain existing strengths while developing improvement plans for weaknesses"
        elif advantages_count == disadvantages_count:
            report += f"⚠️ **Competitive position is medium** - The advantages and disadvantages are equal ({advantages_count} vs {disadvantages_count})\n\n"
            report += "**suggestion**: Find breakthrough points for differentiation and avoid head-on competition"
        else:
            report += f"❌ **Weaker competitive position** - only {advantages_count} Advantages vs. {disadvantages_count} Disadvantages\n\n"
            report += "**suggestion**: Re-evaluate entry strategy, or find niche markets"
        
        return report
    
    def identify_market_gaps(self, competitors: List[CompetitorProfile]) -> List[Dict]:
        """Identify gaps in the market"""
        gaps = []
        
        if not competitors:
            return gaps
        
        # price blank
        prices = sorted([c.current_price for c in competitors])
        for i in range(len(prices) - 1):
            if prices[i+1] / prices[i] > 1.5:  # 50% The above gap
                gaps.append({
                    'type': 'price_gap',
                    'description': f'Price gap between ${prices[i]:.2f} and ${prices[i+1]:.2f}',
                    'opportunity': f'Target ${(prices[i] + prices[i+1]) / 2:.2f} price point'
                })
        
        # Rating blank
        low_quality = [c for c in competitors if c.rating < 4.0]
        if len(low_quality) >= len(competitors) * 0.3:
            gaps.append({
                'type': 'quality_gap',
                'description': f'{len(low_quality)} competitors have rating < 4.0',
                'opportunity': 'Enter with premium quality product'
            })
        
        # Function blank (Need title analysis)
        keywords = defaultdict(int)
        for c in competitors:
            # Simplified processing: assuming there are functional keywords in the title
            pass
        
        return gaps
