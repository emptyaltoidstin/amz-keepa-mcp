"""
Smart Purchase Price Analyzer
==================
Integrate 1688 API to automatically obtain purchase price
Deep integration with actuarial systems
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcurementAnalysis:
    """Procurement analysis results"""
    asin: str
    found: bool
    price_rmb: float
    moq: int
    supplier: str
    source_url: str
    match_score: float
    confidence: str  # high/medium/low
    note: str
    
    # Calculated cost
    shipping_cost_rmb: float  # First leg freight
    total_cogs_usd: float  # Total COGS(USD)


class SmartProcurementAnalyzer:
    """
    Smart Procurement Analyzer
    
    Function:
    1. Search purchase price through 1688 API
    2. Automatically calculate first-trip freight
    3. Calculate full COGS
    4. Generate purchasing proposals
    """
    
    def __init__(self, 
                 tmapi_token: Optional[str] = None,
                 shipping_rate: float = 12.0,  # RMB/kg
                 exchange_rate: float = 7.2,
                 tariff_rate: float = 0.15):
        """
        initialization
        
        Args:
            tmapi_token: TMAPI API Token
            shipping_rate: Shipping price RMB/kg
            exchange_rate: exchange rate
            tariff_rate: tariff rate
        """
        self.shipping_rate = shipping_rate
        self.exchange_rate = exchange_rate
        self.tariff_rate = tariff_rate
        
        # Initialize 1688 client
        self.finder = None
        if tmapi_token:
            from cn_1688_api import CNProcurementFinder
            self.finder = CNProcurementFinder(tmapi_token=tmapi_token)
        
        # cache results
        self._cache: Dict[str, Dict] = {}
    
    @classmethod
    def from_env(cls) -> "SmartProcurementAnalyzer":
        """Create from environment variables"""
        return cls(
            tmapi_token=os.getenv("TMAPI_TOKEN"),
            shipping_rate=float(os.getenv("SHIPPING_RATE", "12")),
            exchange_rate=float(os.getenv("EXCHANGE_RATE", "7.2")),
            tariff_rate=float(os.getenv("TARIFF_RATE", "0.15"))
        )
    
    def analyze_product(self, keepa_product: Dict, 
                        target_moq: int = 100) -> ProcurementAnalysis:
        """
        Analyze the purchase price of individual products
        
        Args:
            keepa_product: Keepa product data
            target_moq: Target purchase quantity (used to evaluate MOQ suitability)
            
        Returns:
            Procurement analysis results
        """
        asin = keepa_product.get("asin", "")
        
        # Get product weight
        weight_kg = self._get_weight(keepa_product)
        
        # If there is no 1688 finder, return to manual input prompt
        if not self.finder:
            return ProcurementAnalysis(
                asin=asin,
                found=False,
                price_rmb=0,
                moq=0,
                supplier="",
                source_url="",
                match_score=0,
                confidence="low",
                note="1688 API is not configured, please enter the purchase price manually",
                shipping_cost_rmb=weight_kg * self.shipping_rate,
                total_cogs_usd=0
            )
        
        # Get product pictures
        from cn_1688_api import get_product_main_image
        image_url = get_product_main_image(keepa_product)
        
        if not image_url:
            return ProcurementAnalysis(
                asin=asin,
                found=False,
                price_rmb=0,
                moq=0,
                supplier="",
                source_url="",
                match_score=0,
                confidence="low",
                note="Unable to get product image",
                shipping_cost_rmb=weight_kg * self.shipping_rate,
                total_cogs_usd=0
            )
        
        try:
            # Search for the best price
            best_offer = self.finder.search_best_price(
                image_url=image_url,
                target_moq=target_moq
            )
            
            if best_offer:
                # Calculate cost
                shipping_cost = weight_kg * self.shipping_rate
                subtotal_rmb = best_offer.price + shipping_cost
                total_rmb = subtotal_rmb * (1 + self.tariff_rate)
                cogs_usd = total_rmb / self.exchange_rate
                
                # Evaluate confidence
                confidence = self._assess_confidence(best_offer)
                
                # Generate notes
                note = self._generate_note(best_offer, target_moq)
                
                return ProcurementAnalysis(
                    asin=asin,
                    found=True,
                    price_rmb=best_offer.price,
                    moq=best_offer.moq,
                    supplier=best_offer.supplier_name,
                    source_url=best_offer.product_url,
                    match_score=best_offer.match_score,
                    confidence=confidence,
                    note=note,
                    shipping_cost_rmb=shipping_cost,
                    total_cogs_usd=cogs_usd
                )
            else:
                return ProcurementAnalysis(
                    asin=asin,
                    found=False,
                    price_rmb=0,
                    moq=0,
                    supplier="",
                    source_url="",
                    match_score=0,
                    confidence="low",
                    note="1688No matching product found",
                    shipping_cost_rmb=weight_kg * self.shipping_rate,
                    total_cogs_usd=0
                )
                
        except Exception as e:
            return ProcurementAnalysis(
                asin=asin,
                found=False,
                price_rmb=0,
                moq=0,
                supplier="",
                source_url="",
                match_score=0,
                confidence="low",
                note=f"Search failed: {str(e)}",
                shipping_cost_rmb=weight_kg * self.shipping_rate,
                total_cogs_usd=0
            )
    
    def analyze_portfolio(self, products: List[Dict], 
                          target_moq: int = 100) -> Dict[str, ProcurementAnalysis]:
        """
        Analyze purchase prices across your entire product portfolio
        
        Args:
            products: Keepa product list
            target_moq: Target purchase quantity
            
        Returns:
            ASIN to Procurement Analytics Mapping
        """
        results = {}
        
        print(f"\n🔍 Start analysis {len(products)} The purchase price of a product...")
        
        for i, product in enumerate(products, 1):
            asin = product.get("asin", "")
            print(f"  [{i}/{len(products)}] analysis {asin}...", end=" ")
            
            analysis = self.analyze_product(product, target_moq)
            results[asin] = analysis
            
            if analysis.found:
                print(f"✅ ¥{analysis.price_rmb:.2f} (MOQ:{analysis.moq})")
            else:
                print(f"❌ {analysis.note}")
        
        # Print summary
        found_count = sum(1 for a in results.values() if a.found)
        print(f"\n📊 Procurement analysis completed: {found_count}/{len(products)} Product found price")
        
        return results
    
    def _get_weight(self, product: Dict) -> float:
        """Get product weight(kg)"""
        package_weight_g = product.get("packageWeight", 0) or 0
        item_weight_g = product.get("itemWeight", 0) or 0
        
        weight_g = package_weight_g or item_weight_g
        if weight_g:
            return weight_g / 1000
        
        # Default weight
        return 0.3  # 300g
    
    def _assess_confidence(self, offer) -> str:
        """Evaluate confidence"""
        if offer.match_score > 0.8 and offer.is_verified:
            return "high"
        elif offer.match_score > 0.5:
            return "medium"
        else:
            return "low"
    
    def _generate_note(self, offer, target_moq: int) -> str:
        """Generate notes"""
        notes = []
        
        if offer.moq > target_moq:
            notes.append(f"MOQ({offer.moq})above target({target_moq})")
        
        if offer.is_verified:
            notes.append("Certified Merchant")
        
        if offer.sales_count > 1000:
            notes.append("Good sales")
        
        if offer.match_score < 0.6:
            notes.append("The matching degree is low, please confirm manually.")
        
        return "; ".join(notes) if notes else "OK"
    
    def to_financials_map(self, analyses: Dict[str, ProcurementAnalysis],
                          organic_pct: float = 0.6,
                          ad_pct: float = 0.4) -> Dict[str, Dict]:
        """
        Financials required to convert to actuarial systems_map format
        
        Args:
            analyses: Procurement Analysis Result Dictionary
            organic_pct: Natural order ratio
            ad_pct: Insertion order ratio
            
        Returns:
            financials_map
        """
        financials = {}
        
        for asin, analysis in analyses.items():
            if analysis.found:
                financials[asin] = {
                    'cogs': analysis.total_cogs_usd,
                    'organic_pct': organic_pct,
                    'ad_pct': ad_pct,
                    'product_cost': analysis.price_rmb / self.exchange_rate,  # USD
                    'shipping_cost': analysis.shipping_cost_rmb / self.exchange_rate,
                    'tariff_cost': (analysis.price_rmb + analysis.shipping_cost_rmb) * self.tariff_rate / self.exchange_rate,
                    'procurement_price_rmb': analysis.price_rmb,
                    'moq': analysis.moq,
                    'supplier': analysis.supplier,
                    'source_url': analysis.source_url,
                    'confidence': analysis.confidence,
                    'note': analysis.note
                }
            else:
                financials[asin] = {
                    'cogs': 0,
                    'organic_pct': organic_pct,
                    'ad_pct': ad_pct,
                    'note': f'Purchase price not found: {analysis.note}'
                }
        
        return financials


def generate_auto_procurement_report(asin: str, 
                                     api_key: Optional[str] = None,
                                     tmapi_token: Optional[str] = None,
                                     target_moq: int = 100) -> Tuple[str, Dict]:
    """
    Automatically generate actuarial reports with purchase prices
    
    This is the most advanced integration function, completed with one click:
    1. Get product data from Keepa
    2. Get the purchase price from 1688
    3. Generate a complete actuary report
    
    Args:
        asin: Product ASIN
        api_key: Keepa API Key
        tmapi_token: TMAPI Token
        target_moq: Target purchase quantity
        
    Returns:
        (Report path, Procurement analysis results)
    """
    import os
    from variant_auto_collector import VariantAutoCollector
    from amazon_actuary_final import generate_final_report
    
    # Get API Key
    api_key = api_key or os.getenv("KEEPA_KEY", "")
    tmapi_token = tmapi_token or os.getenv("TMAPI_TOKEN", "")
    
    if not api_key:
        raise ValueError("Keepa API Key is required")
    
    print("=" * 80)
    print("🚀 Intelligent Procurement Actuary - Automatically obtain 1688 purchase price")
    print("=" * 80)
    
    # Step 1: Collect variant data
    print(f"\n📦 Step 1: Collect product data...")
    collector = VariantAutoCollector(api_key)
    products, parent_info = collector.collect_variants(asin)
    parent_asin = parent_info['parent_asin']
    
    print(f"   Parent ASIN: {parent_asin}")
    print(f"   Number of variants: {len(products)}")
    
    # Step 2: Analyze purchase price
    print(f"\n💰 Step 2: Get purchase price from 1688...")
    analyzer = SmartProcurementAnalyzer(
        tmapi_token=tmapi_token,
        shipping_rate=12.0,
        exchange_rate=7.2,
        tariff_rate=0.15
    )
    
    if not tmapi_token:
        print("   ⚠️ TMAPI is not configured_TOKEN, skip 1688 price search")
        print("   Please add it manually in the .env file: TMAPI_TOKEN=your_token")
    
    procurement_analyses = analyzer.analyze_portfolio(products, target_moq)
    
    # Step 3: Convert to financial data
    print(f"\n📊 Step 3: Generate actuary report...")
    financials_map = analyzer.to_financials_map(procurement_analyses)
    
    # Step 4: Generate report
    report_path, analysis = generate_final_report(
        parent_asin=parent_asin,
        products=products,
        financials_map=financials_map
    )
    
    print(f"\n✅ Report generation completed!")
    print(f"   path: {report_path}")
    print(f"   Expected monthly profit: ${analysis.total_monthly_profit:,.2f}")
    
    # Print purchase price summary
    print(f"\n💡 Purchase price summary:")
    for asin, proc in procurement_analyses.items():
        if proc.found:
            print(f"   {asin}: ¥{proc.price_rmb:.2f} (MOQ:{proc.moq}, {proc.confidence})")
        else:
            print(f"   {asin}: not found ({proc.note})")
    
    return report_path, procurement_analyses


if __name__ == "__main__":
    print("Smart Purchase Price Analyzer")
    print("=" * 60)
    print("\nHow to use:")
    print("1. Set environment variables:")
    print("   export TMAPI_TOKEN=your_tmapi_token")
    print("   export KEEPA_KEY=your_keepa_key")
    print("\n2. Call function:")
    print("   report, analyses = generate_auto_procurement_report('B0F6B5R47Q')")
    print("\nGet TMAPI Token:")
    print("   access https://tmapi.top registration and acquisition")
