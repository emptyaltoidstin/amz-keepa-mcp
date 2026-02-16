"""
1688采购价格自动集成模块
=========================
基于开源爬虫实现以图搜图采购价格采集

功能：
1. 从Keepa获取Amazon产品图片
2. 使用1688以图搜图找到相似商品
3. 自动计算COGS和利润分析
4. 生成完整报告

实现方式：基于 https://github.com/Zhui-CN/1688_image_search_crawler
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ProcurementResult:
    """采购分析结果"""
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
    
    # 成本计算
    weight_kg: float
    shipping_cost_rmb: float
    total_cogs_usd: float


class Smart1688Procurement:
    """
    智能1688采购分析器
    
    无需API Key，直接使用爬虫获取数据
    """
    
    def __init__(self,
                 shipping_rate: float = 12.0,  # RMB/kg
                 exchange_rate: float = 7.2,
                 tariff_rate: float = 0.15,
                 timeout: int = 30):
        """
        初始化
        
        Args:
            shipping_rate: 船运价格 RMB/kg
            exchange_rate: 汇率
            tariff_rate: 关税率
            timeout: 请求超时
        """
        self.shipping_rate = shipping_rate
        self.exchange_rate = exchange_rate
        self.tariff_rate = tariff_rate
        self.timeout = timeout
        
        # 初始化1688爬虫
        from cn_1688_crawler import CN1688Crawler
        self.crawler = CN1688Crawler(timeout=timeout)
    
    @classmethod
    def from_env(cls) -> "Smart1688Procurement":
        """从环境变量创建"""
        return cls(
            shipping_rate=float(os.getenv("SHIPPING_RATE", "12")),
            exchange_rate=float(os.getenv("EXCHANGE_RATE", "7.2")),
            tariff_rate=float(os.getenv("TARIFF_RATE", "0.15"))
        )
    
    def _get_weight(self, product: Dict) -> float:
        """获取产品重量(kg)"""
        package_weight_g = product.get("packageWeight", 0) or 0
        item_weight_g = product.get("itemWeight", 0) or 0
        
        weight_g = package_weight_g or item_weight_g
        if weight_g:
            return weight_g / 1000
        
        # 默认重量300g
        return 0.3
    
    def _convert_image_id_to_url(self, image_id: str) -> Optional[str]:
        """将Keepa图片ID转换为完整URL"""
        if not image_id:
            return None
        # 清理图片ID（移除可能的特殊字符）
        image_id = image_id.strip()
        if image_id:
            return f"https://m.media-amazon.com/images/I/{image_id}.jpg"
        return None
    
    def _get_image_url(self, product: Dict) -> Optional[str]:
        """从Keepa产品数据中获取主图URL"""
        # 方法1: 从Keepa CSV导出的"Image"列获取 (分号分隔的完整URL列表)
        image_field = product.get("Image", "")
        if image_field and "https://" in image_field:
            # Keepa CSV格式: "https://...;https://...;..."
            urls = image_field.split(";")
            if urls and urls[0].startswith("http"):
                return urls[0].strip()
        
        # 方法2: 从imagesCSV获取 (Keepa API格式: 逗号分隔的图片ID)
        images = product.get("imagesCSV", "")
        if images:
            image_ids = images.split(",")
            if image_ids and image_ids[0]:
                return self._convert_image_id_to_url(image_ids[0])
        
        # 方法3: 从data.images获取
        data = product.get("data", {})
        image_list = data.get("images", [])
        if image_list:
            return image_list[0]
        
        # 方法4: 从imageUrl获取
        if product.get("imageUrl"):
            return product["imageUrl"]
        
        # 方法5: 从metrics_163字典中的'Image'字段获取
        metrics = product.get('metrics_163', {})
        if metrics and 'Image' in metrics:
            image_value = metrics['Image']
            if 'https://' in image_value:
                urls = image_value.split(';')
                if urls:
                    return urls[0].strip()
            else:
                # 逗号分隔的图片ID
                ids = image_value.split(',')
                if ids:
                    return self._convert_image_id_to_url(ids[0])
        
        return None
    
    def analyze_product(self, keepa_product: Dict, 
                        target_moq: int = 100) -> ProcurementResult:
        """
        分析单个产品的采购价格
        
        Args:
            keepa_product: Keepa产品数据
            target_moq: 目标采购量
            
        Returns:
            采购分析结果
        """
        asin = keepa_product.get("asin", "")
        weight_kg = self._get_weight(keepa_product)
        
        # 获取图片URL
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
                note="无法获取产品图片",
                weight_kg=weight_kg,
                shipping_cost_rmb=weight_kg * self.shipping_rate,
                total_cogs_usd=0
            )
        
        try:
            # 搜索1688
            offer = self.crawler.find_best_price(image_url, target_moq)
            
            if offer:
                # 计算成本
                shipping_cost = weight_kg * self.shipping_rate
                subtotal_rmb = offer.price + shipping_cost
                total_rmb = subtotal_rmb * (1 + self.tariff_rate)
                cogs_usd = total_rmb / self.exchange_rate
                
                # 评估置信度
                if offer.price > 0 and offer.price < 500:  # 价格合理范围
                    confidence = "high"
                elif offer.price > 0:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                # 生成备注
                notes = []
                if offer.moq > target_moq:
                    notes.append(f"MOQ({offer.moq})高于目标({target_moq})")
                if offer.is_verified:
                    notes.append("认证商家")
                if offer.years >= 3:
                    notes.append(f"{offer.years}年老店")
                
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
                    note="1688未找到匹配商品",
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
                note=f"搜索失败: {str(e)}",
                weight_kg=weight_kg,
                shipping_cost_rmb=weight_kg * self.shipping_rate,
                total_cogs_usd=0
            )
    
    def analyze_portfolio(self, products: List[Dict], 
                          target_moq: int = 100) -> Dict[str, ProcurementResult]:
        """
        批量分析产品组合的采购价格
        
        Args:
            products: Keepa产品列表
            target_moq: 目标采购量
            
        Returns:
            ASIN到采购结果的映射
        """
        results = {}
        
        print(f"\n🔍 开始分析 {len(products)} 个产品的1688采购价格...")
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
        
        # 汇总
        found_count = sum(1 for r in results.values() if r.found)
        print("-" * 80)
        print(f"📊 完成: {found_count}/{len(products)} 个产品找到采购价格")
        
        return results
    
    def to_financials_map(self, results: Dict[str, ProcurementResult],
                          organic_pct: float = 0.6,
                          ad_pct: float = 0.4) -> Dict[str, Dict]:
        """
        转换为精算师系统所需的financials_map格式
        
        Args:
            results: 采购分析结果字典
            organic_pct: 自然订单比例
            ad_pct: 广告订单比例
            
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
                    'note': f'未找到采购价格: {result.note}'
                }
        
        return financials


def generate_1688_procurement_report(
    asin: str,
    api_key: Optional[str] = None,
    target_moq: int = 100,
    output_path: Optional[str] = None
) -> Tuple[str, Dict[str, ProcurementResult]]:
    """
    生成带1688采购价格的精算师报告
    
    一键完成：
    1. 从Keepa获取产品数据
    2. 从1688爬虫获取采购价格
    3. 生成完整精算师报告
    
    Args:
        asin: 产品ASIN
        api_key: Keepa API Key
        target_moq: 目标采购量
        output_path: 报告输出路径
        
    Returns:
        (报告路径, 采购分析结果)
    """
    import os
    from variant_auto_collector import VariantAutoCollector
    from amazon_actuary_final import generate_final_report
    
    # 获取API Key
    api_key = api_key or os.getenv("KEEPA_KEY", "")
    if not api_key:
        raise ValueError("需要提供Keepa API Key")
    
    print("=" * 80)
    print("🚀 智能1688采购精算师 - 自动以图搜图获取采购价格")
    print("=" * 80)
    
    # 步骤1: 采集变体数据
    print(f"\n📦 步骤1: 采集产品数据...")
    collector = VariantAutoCollector(api_key)
    products, parent_info = collector.collect_variants(asin)
    parent_asin = parent_info['parent_asin']
    
    print(f"   父ASIN: {parent_asin}")
    print(f"   变体数量: {len(products)}")
    print(f"   品牌: {parent_info.get('brand', 'N/A')}")
    
    # 步骤2: 分析1688采购价格
    print(f"\n💰 步骤2: 从1688以图搜图获取采购价格...")
    print("   (基于开源实现: https://github.com/Zhui-CN/1688_image_search_crawler)")
    
    analyzer = Smart1688Procurement.from_env()
    procurement_results = analyzer.analyze_portfolio(products, target_moq)
    
    # 步骤3: 转换为财务数据
    print(f"\n📊 步骤3: 生成精算师报告...")
    financials_map = analyzer.to_financials_map(procurement_results)
    
    # 步骤4: 生成报告
    report_path, analysis = generate_final_report(
        parent_asin=parent_asin,
        products=products,
        financials_map=financials_map,
        output_path=output_path
    )
    
    # 打印汇总
    print(f"\n✅ 报告生成完成!")
    print(f"   主报告: {report_path}")
    print(f"   预期月利润: ${analysis.total_monthly_profit:,.2f}")
    
    # 打印采购价格汇总
    print(f"\n💰 1688采购价格汇总:")
    for asin, result in procurement_results.items():
        if result.found:
            print(f"   {asin}: ¥{result.price_rmb:.2f} ({result.supplier[:20]}...)")
        else:
            print(f"   {asin}: 未找到 - {result.note[:30]}")
    
    # 生成交互式报告
    try:
        from allinone_interactive_report import generate_allinone_report
        allinone_path = generate_allinone_report(parent_asin, products, 
            {'variants': analysis.variants})
        print(f"\n🧮 All-in-One交互式报告: {allinone_path}")
    except Exception as e:
        pass
    
    return report_path, procurement_results


# 便捷别名
auto_1688_analyze = generate_1688_procurement_report


if __name__ == "__main__":
    print("1688采购价格自动集成模块")
    print("=" * 60)
    print("\n使用方法:")
    print("1. 确保已安装依赖:")
    print("   pip install requests")
    print("\n2. 设置Keepa API Key:")
    print("   export KEEPA_KEY=your_key")
    print("\n3. 运行分析:")
    print("   from procurement_1688_integration import generate_1688_procurement_report")
    print("   report, results = generate_1688_procurement_report('B0F6B5R47Q')")
    print("\n特点:")
    print("   ✅ 无需1688 API Key")
    print("   ✅ 直接以图搜图")
    print("   ✅ 自动计算完整COGS")
    print("   ⚠️  注意: 频繁调用可能触发反爬")
