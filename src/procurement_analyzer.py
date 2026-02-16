"""
智能采购价格分析器
==================
整合1688 API自动获取采购价格
与精算师系统深度集成
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcurementAnalysis:
    """采购分析结果"""
    asin: str
    found: bool
    price_rmb: float
    moq: int
    supplier: str
    source_url: str
    match_score: float
    confidence: str  # high/medium/low
    note: str
    
    # 计算后的成本
    shipping_cost_rmb: float  # 头程运费
    total_cogs_usd: float  # 总COGS(USD)


class SmartProcurementAnalyzer:
    """
    智能采购分析器
    
    功能：
    1. 通过1688 API搜索采购价格
    2. 自动计算头程运费
    3. 计算完整COGS
    4. 生成采购建议
    """
    
    def __init__(self, 
                 tmapi_token: Optional[str] = None,
                 shipping_rate: float = 12.0,  # RMB/kg
                 exchange_rate: float = 7.2,
                 tariff_rate: float = 0.15):
        """
        初始化
        
        Args:
            tmapi_token: TMAPI API Token
            shipping_rate: 船运价格 RMB/kg
            exchange_rate: 汇率
            tariff_rate: 关税率
        """
        self.shipping_rate = shipping_rate
        self.exchange_rate = exchange_rate
        self.tariff_rate = tariff_rate
        
        # 初始化1688客户端
        self.finder = None
        if tmapi_token:
            from cn_1688_api import CNProcurementFinder
            self.finder = CNProcurementFinder(tmapi_token=tmapi_token)
        
        # 缓存结果
        self._cache: Dict[str, Dict] = {}
    
    @classmethod
    def from_env(cls) -> "SmartProcurementAnalyzer":
        """从环境变量创建"""
        return cls(
            tmapi_token=os.getenv("TMAPI_TOKEN"),
            shipping_rate=float(os.getenv("SHIPPING_RATE", "12")),
            exchange_rate=float(os.getenv("EXCHANGE_RATE", "7.2")),
            tariff_rate=float(os.getenv("TARIFF_RATE", "0.15"))
        )
    
    def analyze_product(self, keepa_product: Dict, 
                        target_moq: int = 100) -> ProcurementAnalysis:
        """
        分析单个产品的采购价格
        
        Args:
            keepa_product: Keepa产品数据
            target_moq: 目标采购量（用于评估MOQ适合度）
            
        Returns:
            采购分析结果
        """
        asin = keepa_product.get("asin", "")
        
        # 获取产品重量
        weight_kg = self._get_weight(keepa_product)
        
        # 如果没有1688 finder，返回手动输入提示
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
                note="未配置1688 API，请手动输入采购价格",
                shipping_cost_rmb=weight_kg * self.shipping_rate,
                total_cogs_usd=0
            )
        
        # 获取产品图片
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
                note="无法获取产品图片",
                shipping_cost_rmb=weight_kg * self.shipping_rate,
                total_cogs_usd=0
            )
        
        try:
            # 搜索最优价格
            best_offer = self.finder.search_best_price(
                image_url=image_url,
                target_moq=target_moq
            )
            
            if best_offer:
                # 计算成本
                shipping_cost = weight_kg * self.shipping_rate
                subtotal_rmb = best_offer.price + shipping_cost
                total_rmb = subtotal_rmb * (1 + self.tariff_rate)
                cogs_usd = total_rmb / self.exchange_rate
                
                # 评估置信度
                confidence = self._assess_confidence(best_offer)
                
                # 生成备注
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
                    note="1688未找到匹配商品",
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
                note=f"搜索失败: {str(e)}",
                shipping_cost_rmb=weight_kg * self.shipping_rate,
                total_cogs_usd=0
            )
    
    def analyze_portfolio(self, products: List[Dict], 
                          target_moq: int = 100) -> Dict[str, ProcurementAnalysis]:
        """
        分析整个产品组合的采购价格
        
        Args:
            products: Keepa产品列表
            target_moq: 目标采购量
            
        Returns:
            ASIN到采购分析的映射
        """
        results = {}
        
        print(f"\n🔍 开始分析 {len(products)} 个产品的采购价格...")
        
        for i, product in enumerate(products, 1):
            asin = product.get("asin", "")
            print(f"  [{i}/{len(products)}] 分析 {asin}...", end=" ")
            
            analysis = self.analyze_product(product, target_moq)
            results[asin] = analysis
            
            if analysis.found:
                print(f"✅ ¥{analysis.price_rmb:.2f} (MOQ:{analysis.moq})")
            else:
                print(f"❌ {analysis.note}")
        
        # 打印汇总
        found_count = sum(1 for a in results.values() if a.found)
        print(f"\n📊 采购分析完成: {found_count}/{len(products)} 个产品找到价格")
        
        return results
    
    def _get_weight(self, product: Dict) -> float:
        """获取产品重量(kg)"""
        package_weight_g = product.get("packageWeight", 0) or 0
        item_weight_g = product.get("itemWeight", 0) or 0
        
        weight_g = package_weight_g or item_weight_g
        if weight_g:
            return weight_g / 1000
        
        # 默认重量
        return 0.3  # 300g
    
    def _assess_confidence(self, offer) -> str:
        """评估置信度"""
        if offer.match_score > 0.8 and offer.is_verified:
            return "high"
        elif offer.match_score > 0.5:
            return "medium"
        else:
            return "low"
    
    def _generate_note(self, offer, target_moq: int) -> str:
        """生成备注"""
        notes = []
        
        if offer.moq > target_moq:
            notes.append(f"MOQ({offer.moq})高于目标({target_moq})")
        
        if offer.is_verified:
            notes.append("认证商家")
        
        if offer.sales_count > 1000:
            notes.append("销量好")
        
        if offer.match_score < 0.6:
            notes.append("匹配度较低，请人工确认")
        
        return "; ".join(notes) if notes else "OK"
    
    def to_financials_map(self, analyses: Dict[str, ProcurementAnalysis],
                          organic_pct: float = 0.6,
                          ad_pct: float = 0.4) -> Dict[str, Dict]:
        """
        转换为精算师系统所需的financials_map格式
        
        Args:
            analyses: 采购分析结果字典
            organic_pct: 自然订单比例
            ad_pct: 广告订单比例
            
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
                    'note': f'未找到采购价格: {analysis.note}'
                }
        
        return financials


def generate_auto_procurement_report(asin: str, 
                                     api_key: Optional[str] = None,
                                     tmapi_token: Optional[str] = None,
                                     target_moq: int = 100) -> Tuple[str, Dict]:
    """
    自动生成带采购价格的精算师报告
    
    这是最高级的集成函数，一键完成：
    1. 从Keepa获取产品数据
    2. 从1688获取采购价格
    3. 生成完整精算师报告
    
    Args:
        asin: 产品ASIN
        api_key: Keepa API Key
        tmapi_token: TMAPI Token
        target_moq: 目标采购量
        
    Returns:
        (报告路径, 采购分析结果)
    """
    import os
    from variant_auto_collector import VariantAutoCollector
    from amazon_actuary_final import generate_final_report
    
    # 获取API Key
    api_key = api_key or os.getenv("KEEPA_KEY", "")
    tmapi_token = tmapi_token or os.getenv("TMAPI_TOKEN", "")
    
    if not api_key:
        raise ValueError("需要提供Keepa API Key")
    
    print("=" * 80)
    print("🚀 智能采购精算师 - 自动获取1688采购价格")
    print("=" * 80)
    
    # 步骤1: 采集变体数据
    print(f"\n📦 步骤1: 采集产品数据...")
    collector = VariantAutoCollector(api_key)
    products, parent_info = collector.collect_variants(asin)
    parent_asin = parent_info['parent_asin']
    
    print(f"   父ASIN: {parent_asin}")
    print(f"   变体数量: {len(products)}")
    
    # 步骤2: 分析采购价格
    print(f"\n💰 步骤2: 从1688获取采购价格...")
    analyzer = SmartProcurementAnalyzer(
        tmapi_token=tmapi_token,
        shipping_rate=12.0,
        exchange_rate=7.2,
        tariff_rate=0.15
    )
    
    if not tmapi_token:
        print("   ⚠️ 未配置TMAPI_TOKEN，跳过1688价格搜索")
        print("   请手动在 .env 文件中添加: TMAPI_TOKEN=your_token")
    
    procurement_analyses = analyzer.analyze_portfolio(products, target_moq)
    
    # 步骤3: 转换为财务数据
    print(f"\n📊 步骤3: 生成精算师报告...")
    financials_map = analyzer.to_financials_map(procurement_analyses)
    
    # 步骤4: 生成报告
    report_path, analysis = generate_final_report(
        parent_asin=parent_asin,
        products=products,
        financials_map=financials_map
    )
    
    print(f"\n✅ 报告生成完成!")
    print(f"   路径: {report_path}")
    print(f"   预期月利润: ${analysis.total_monthly_profit:,.2f}")
    
    # 打印采购价格汇总
    print(f"\n💡 采购价格汇总:")
    for asin, proc in procurement_analyses.items():
        if proc.found:
            print(f"   {asin}: ¥{proc.price_rmb:.2f} (MOQ:{proc.moq}, {proc.confidence})")
        else:
            print(f"   {asin}: 未找到 ({proc.note})")
    
    return report_path, procurement_analyses


if __name__ == "__main__":
    print("智能采购价格分析器")
    print("=" * 60)
    print("\n使用方法:")
    print("1. 设置环境变量:")
    print("   export TMAPI_TOKEN=your_tmapi_token")
    print("   export KEEPA_KEY=your_keepa_key")
    print("\n2. 调用函数:")
    print("   report, analyses = generate_auto_procurement_report('B0F6B5R47Q')")
    print("\n获取TMAPI Token:")
    print("   访问 https://tmapi.top 注册获取")
