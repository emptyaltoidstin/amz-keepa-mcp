"""
1688 purchase price automatic integration module
=========================
Implementing image search and purchase price collection based on open source crawler

Function:
1. Get Amazon product images from Keepa
2. Use 1688 to search images to find similar products
3. Automatically calculate COGS and profit analysis
4. Generate full report

Implementation method: Based on https://github.com/Zhui-CN/1688_image_search_crawler
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ProcurementResult:
    """Procurement analysis results"""
    asin: str
    found: bool
    price_rmb: float
    moq: int
    supplier: str
    location: str
    is_verified: bool
    product_url: str
    confidence: str  # high/medium/low
    note: str
    
    # cost calculation
    weight_kg: float
    shipping_cost_rmb: float
    total_cogs_usd: float


class Smart1688Procurement:
    """
    Intelligent 1688 Procurement Analyzer
    
    No need for API Key, directly use crawler to obtain data
    """
    
    def __init__(self,
                 shipping_rate: float = 12.0,  # RMB/kg
                 exchange_rate: float = 7.2,
                 tariff_rate: float = 0.15,
                 timeout: int = 30):
        """
        initialization
        
        Args:
            shipping_rate: Shipping price RMB/kg
            exchange_rate: exchange rate
            tariff_rate: tariff rate
            timeout: Request timeout
        """
        self.shipping_rate = shipping_rate
        self.exchange_rate = exchange_rate
        self.tariff_rate = tariff_rate
        self.timeout = timeout
        
        # Initialize 1688 crawler
        from cn_1688_crawler import CN1688Crawler
        self.crawler = CN1688Crawler(timeout=timeout)
    
    @classmethod
    def from_env(cls) -> "Smart1688Procurement":
        """Create from environment variables"""
        return cls(
            shipping_rate=float(os.getenv("SHIPPING_RATE", "12")),
            exchange_rate=float(os.getenv("EXCHANGE_RATE", "7.2")),
            tariff_rate=float(os.getenv("TARIFF_RATE", "0.15"))
        )
    
    def _get_weight(self, product: Dict) -> float:
        """Get product weight(kg)"""
        package_weight_g = product.get("packageWeight", 0) or 0
        item_weight_g = product.get("itemWeight", 0) or 0
        
        weight_g = package_weight_g or item_weight_g
        if weight_g:
            return weight_g / 1000
        
        # Default weight 300g
        return 0.3
    
    def _convert_image_id_to_url(self, image_id: str) -> Optional[str]:
        """Convert Keepa image ID to full URL"""
        if not image_id:
            return None
        # Clean image ID (remove possible special characters)
        image_id = image_id.strip()
        if image_id:
            return f"https://m.media-amazon.com/images/I/{image_id}.jpg"
        return None
    
    def _get_image_url(self, product: Dict) -> Optional[str]:
        """Get main image URL from Keepa product data"""
        # Method 1: Exported from Keepa CSV"Image"column get (Semicolon separated complete list of URLs)
        image_field = product.get("Image", "")
        if image_field and "https://" in image_field:
            # Keepa CSV format: "https://...;https://...;..."
            urls = image_field.split(";")
            if urls and urls[0].startswith("http"):
                return urls[0].strip()
        
        # Method 2: Get from imagesCSV (Keepa API format: Comma separated image IDs)
        images = product.get("imagesCSV", "")
        if images:
            image_ids = images.split(",")
            if image_ids and image_ids[0]:
                return self._convert_image_id_to_url(image_ids[0])
        
        # Method 3: Get from data.images
        data = product.get("data", {})
        image_list = data.get("images", [])
        if image_list:
            return image_list[0]
        
        # Method 4: Get from imageUrl
        if product.get("imageUrl"):
            return product["imageUrl"]
        
        # Method 5: from metrics_163 in the dictionary'Image'Field acquisition
        metrics = product.get('metrics_163', {})
        if metrics and 'Image' in metrics:
            image_value = metrics['Image']
            if 'https://' in image_value:
                urls = image_value.split(';')
                if urls:
                    return urls[0].strip()
            else:
                # Comma separated image IDs
                ids = image_value.split(',')
                if ids:
                    return self._convert_image_id_to_url(ids[0])
        
        return None
    
    def analyze_product(self, keepa_product: Dict, 
                        target_moq: int = 100) -> ProcurementResult:
        """
        Analyze the purchase price of individual products
        
        Args:
            keepa_product: Keepa product data
            target_moq: Target purchase quantity
            
        Returns:
            Procurement analysis results
        """
        asin = keepa_product.get("asin", "")
        weight_kg = self._get_weight(keepa_product)
        
        # Get image URL
        image_url = self._get_image_url(keepa_product)
        
        if not image_url:
            return ProcurementResult(
                asin=asin,
                found=False,
                price_rmb=0,
                moq=0,
                supplier="",
                location="",
                is_verified=False,
                product_url="",
                confidence="low",
                note="Unable to get product image",
                weight_kg=weight_kg,
                shipping_cost_rmb=weight_kg * self.shipping_rate,
                total_cogs_usd=0
            )
        
        try:
            # Search 1688
            offer = self.crawler.find_best_price(image_url, target_moq)
            
            if offer:
                # Calculate cost
                shipping_cost = weight_kg * self.shipping_rate
                subtotal_rmb = offer.price + shipping_cost
                total_rmb = subtotal_rmb * (1 + self.tariff_rate)
                cogs_usd = total_rmb / self.exchange_rate
                
                # Evaluate confidence
                if offer.price > 0 and offer.price < 500:  # Reasonable price range
                    confidence = "high"
                elif offer.price > 0:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                # Generate notes
                notes = []
                if offer.moq > target_moq:
                    notes.append(f"MOQ({offer.moq})above target({target_moq})")
                if offer.is_verified:
                    notes.append("Certified Merchant")
                if offer.years >= 3:
                    notes.append(f"{offer.years}nianlaodian")
                
                return ProcurementResult(
                    asin=asin,
                    found=True,
                    price_rmb=offer.price,
                    moq=offer.moq,
                    supplier=offer.company_name,
                    location=f"{offer.province} {offer.city}".strip(),
                    is_verified=offer.is_verified,
                    product_url=offer.product_url,
                    confidence=confidence,
                    note="; ".join(notes) if notes else "OK",
                    weight_kg=weight_kg,
                    shipping_cost_rmb=shipping_cost,
                    total_cogs_usd=cogs_usd
                )
            else:
                return ProcurementResult(
                    asin=asin,
                    found=False,
                    price_rmb=0,
                    moq=0,
                    supplier="",
                    location="",
                    is_verified=False,
                    product_url="",
                    confidence="low",
                    note="1688No matching product found",
                    weight_kg=weight_kg,
                    shipping_cost_rmb=weight_kg * self.shipping_rate,
                    total_cogs_usd=0
                )
                
        except Exception as e:
            return ProcurementResult(
                asin=asin,
                found=False,
                price_rmb=0,
                moq=0,
                supplier="",
                location="",
                is_verified=False,
                product_url="",
                confidence="low",
                note=f"Search failed: {str(e)}",
                weight_kg=weight_kg,
                shipping_cost_rmb=weight_kg * self.shipping_rate,
                total_cogs_usd=0
            )
    
    def analyze_portfolio(self, products: List[Dict], 
                          target_moq: int = 100) -> Dict[str, ProcurementResult]:
        """
        Bulk analysis of purchase prices for product portfolios
        
        Args:
            products: Keepa product list
            target_moq: Target purchase quantity
            
        Returns:
            ASIN to purchase result mapping
        """
        results = {}
        
        print(f"\n🔍 Start analysis {len(products)} The purchase price of 1688 products...")
        print("-" * 80)
        
        for i, product in enumerate(products, 1):
            asin = product.get("asin", "")
            print(f"  [{i}/{len(products)}] {asin}...", end=" ")
            
            result = self.analyze_product(product, target_moq)
            results[asin] = result
            
            if result.found:
                print(f"✅ ¥{result.price_rmb:.2f} (MOQ:{result.moq}, {result.confidence})")
            else:
                print(f"❌ {result.note[:30]}...")
        
        # Summary
        found_count = sum(1 for r in results.values() if r.found)
        print("-" * 80)
        print(f"📊 Complete: {found_count}/{len(products)} Find purchase price for products")
        
        return results
    
    def to_financials_map(self, results: Dict[str, ProcurementResult],
                          organic_pct: float = 0.6,
                          ad_pct: float = 0.4) -> Dict[str, Dict]:
        """
        Financials required to convert to actuarial systems_map format
        
        Args:
            results: Procurement Analysis Result Dictionary
            organic_pct: Natural order ratio
            ad_pct: Insertion order ratio
            
        Returns:
            financials_map
        """
        financials = {}
        
        for asin, result in results.items():
            if result.found:
                financials[asin] = {
                    'cogs': result.total_cogs_usd,
                    'organic_pct': organic_pct,
                    'ad_pct': ad_pct,
                    'product_cost': result.price_rmb / self.exchange_rate,
                    'shipping_cost': result.shipping_cost_rmb / self.exchange_rate,
                    'tariff_cost': (result.price_rmb + result.shipping_cost_rmb) * self.tariff_rate / self.exchange_rate,
                    'procurement_price_rmb': result.price_rmb,
                    'moq': result.moq,
                    'supplier': result.supplier,
                    'location': result.location,
                    'source_url': result.product_url,
                    'is_verified': result.is_verified,
                    'confidence': result.confidence,
                    'note': result.note
                }
            else:
                financials[asin] = {
                    'cogs': 0,
                    'organic_pct': organic_pct,
                    'ad_pct': ad_pct,
                    'note': f'Purchase price not found: {result.note}'
                }
        
        return financials


def generate_1688_procurement_report(
    asin: str,
    api_key: Optional[str] = None,
    target_moq: int = 100,
    output_path: Optional[str] = None
) -> Tuple[str, Dict[str, ProcurementResult]]:
    """
    Generate actuary report with 1688 purchase price
    
    Complete with one click:
    1. Get product data from Keepa
    2. Get the purchase price from 1688 crawler
    3. Generate a complete actuary report
    
    Args:
        asin: Product ASIN
        api_key: Keepa API Key
        target_moq: Target purchase quantity
        output_path: Report output path
        
    Returns:
        (Report path, Procurement analysis results)
    """
    import os
    from variant_auto_collector import VariantAutoCollector
    from amazon_actuary_final import generate_final_report
    
    # Get API Key
    api_key = api_key or os.getenv("KEEPA_KEY", "")
    if not api_key:
        raise ValueError("Keepa API Key is required")
    
    print("=" * 80)
    print("🚀 Intelligent 1688 Procurement Actuary - Automatically search images to obtain purchase prices")
    print("=" * 80)
    
    # Step 1: Collect variant data
    print(f"\n📦 Step 1: Collect product data...")
    collector = VariantAutoCollector(api_key)
    products, parent_info = collector.collect_variants(asin)
    parent_asin = parent_info['parent_asin']
    
    print(f"   Parent ASIN: {parent_asin}")
    print(f"   Number of variants: {len(products)}")
    print(f"   brand: {parent_info.get('brand', 'N/A')}")
    
    # Step 2: Analyze 1688 purchase price
    print(f"\n💰 Step 2: Search pictures to get the purchase price from 1688...")
    print("   (Based on open source implementation: https://github.com/Zhui-CN/1688_image_search_crawler)")
    
    analyzer = Smart1688Procurement.from_env()
    procurement_results = analyzer.analyze_portfolio(products, target_moq)
    
    # Step 3: Convert to financial data
    print(f"\n📊 Step 3: Generate actuary report...")
    financials_map = analyzer.to_financials_map(procurement_results)
    
    # Step 4: Generate report
    report_path, analysis = generate_final_report(
        parent_asin=parent_asin,
        products=products,
        financials_map=financials_map,
        output_path=output_path
    )
    
    # Print summary
    print(f"\n✅ Report generation completed!")
    print(f"   main report: {report_path}")
    print(f"   Expected monthly profit: ${analysis.total_monthly_profit:,.2f}")
    
    # Print purchase price summary
    print(f"\n💰 1688 purchase price summary:")
    for asin, result in procurement_results.items():
        if result.found:
            print(f"   {asin}: ¥{result.price_rmb:.2f} ({result.supplier[:20]}...)")
        else:
            print(f"   {asin}: not found - {result.note[:30]}")
    
    # Generate interactive reports
    try:
        from allinone_interactive_report import generate_allinone_report
        allinone_path = generate_allinone_report(parent_asin, products, 
            {'variants': analysis.variants})
        print(f"\n🧮 All-in-Oneinteractive report: {allinone_path}")
    except Exception as e:
        pass
    
    return report_path, procurement_results


# Convenience alias
auto_1688_analyze = generate_1688_procurement_report


if __name__ == "__main__":
    print("1688 purchase price automatic integration module")
    print("=" * 60)
    print("\nHow to use:")
    print("1. Make sure the dependencies are installed:")
    print("   pip install requests")
    print("\n2. Set Keepa API Key:")
    print("   export KEEPA_KEY=your_key")
    print("\n3. Run analysis:")
    print("   from procurement_1688_integration import generate_1688_procurement_report")
    print("   report, results = generate_1688_procurement_report('B0F6B5R47Q')")
    print("\nFeatures:")
    print("   ✅ No 1688 API Key required")
    print("   ✅ Search pictures directly by pictures")
    print("   ✅ Automatically calculate complete COGS")
    print("   ⚠️ NOTE: Frequent calls may trigger anti-crawling")
