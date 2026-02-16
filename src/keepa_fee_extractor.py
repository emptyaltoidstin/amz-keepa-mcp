"""
Keepa API 费用提取器
==================
从Keepa API提取真实的FBA费用和佣金数据
"""

from typing import Dict, Optional, Tuple


class KeepaFeeExtractor:
    """
    从Keepa API产品数据中提取真实的FBA费用和佣金
    
    Keepa API可以返回:
    - FBA费用 (fbaFees)
    - 佣金比例 (referralFeePercentage)
    - 产品尺寸 (package dimensions)
    - 产品重量 (package weight)
    """
    
    # 亚马逊佣金比例表 (按类目)
    REFERRAL_FEE_RATES = {
        'Amazon Device Accessories': 0.45,  # 45%
        'Electronics': 0.08,  # 8%
        'Electronics Accessories': 0.15,  # 15%
        'Camera': 0.08,  # 8%
        'Cell Phone Devices': 0.08,  # 8%
        'Clothing': 0.17,  # 17%
        'Shoes': 0.17,  # 17%
        'Handbags': 0.15,  # 15%
        'Jewelry': 0.20,  # 20%
        'Kitchen': 0.15,  # 15%
        'Home': 0.15,  # 15%
        'Home Improvement': 0.15,  # 15%
        'Beauty': 0.15,  # 15%
        'Health & Personal Care': 0.15,  # 15%
        'Toys': 0.15,  # 15%
        'Sports': 0.15,  # 15%
        'Automotive': 0.15,  # 15%
        'Books': 0.15,  # 15%
        'Music': 0.15,  # 15%
        'Video Games': 0.15,  # 15%
        'Grocery': 0.15,  # 15%
        'Pet Supplies': 0.15,  # 15%
        'Office Products': 0.15,  # 15%
        'Industrial': 0.15,  # 15%
        'Tools': 0.15,  # 15%
    }
    
    @classmethod
    def extract_fba_fee(cls, product: Dict) -> Optional[float]:
        """
        提取FBA费用
        
        Keepa API可能在以下字段返回FBA费用:
        - fbaFees (直接费用)
        - data.fbaFees
        - 或需要从尺寸/重量计算
        """
        # 尝试直接获取FBA费用
        fba_fee = product.get('fbaFees')
        if fba_fee and isinstance(fba_fee, (int, float)) and fba_fee > 0:
            return float(fba_fee) / 100  # Keepa可能以 cents 存储
        
        # 从data字段获取
        data = product.get('data', {})
        if data:
            fba_fee = data.get('fbaFees')
            if fba_fee and isinstance(fba_fee, (int, float)) and fba_fee > 0:
                return float(fba_fee) / 100
            
            # 从CSV数据获取
            csv = data.get('csv', [])
            # FBA费用通常在特定的CSV索引中
            # 根据Keepa文档，FBA费用可能在特定的csv字段
            if len(csv) > 70:  # 假设FBA费用在某个索引
                # 这里需要根据实际Keepa数据结构确定
                pass
        
        # 如果没有直接数据，返回None让调用者估算
        return None
    
    @classmethod
    def extract_referral_fee_rate(cls, product: Dict) -> float:
        """
        提取佣金比例
        
        优先顺序:
        1. Keepa API直接返回的referralFeePercentage
        2. 根据类目推断
        3. 默认15%
        """
        # 尝试直接获取
        referral_pct = product.get('referralFeePercentage')
        if referral_pct and isinstance(referral_pct, (int, float)) and referral_pct > 0:
            return referral_pct / 100 if referral_pct > 1 else referral_pct
        
        # 从data字段获取
        data = product.get('data', {})
        if data:
            referral_pct = data.get('referralFeePercentage')
            if referral_pct and isinstance(referral_pct, (int, float)) and referral_pct > 0:
                return referral_pct / 100 if referral_pct > 1 else referral_pct
        
        # 根据类目推断
        category = cls._get_main_category(product)
        if category:
            for cat_pattern, rate in cls.REFERRAL_FEE_RATES.items():
                if cat_pattern.lower() in category.lower():
                    return rate
        
        # 默认15%
        return 0.15
    
    @classmethod
    def extract_referral_fee(cls, product: Dict, price: float) -> float:
        """
        计算佣金金额
        
        Args:
            product: Keepa产品数据
            price: 售价(USD)
        """
        rate = cls.extract_referral_fee_rate(product)
        return price * rate
    
    @classmethod
    def extract_dimensions(cls, product: Dict) -> Dict[str, float]:
        """
        提取产品尺寸 (cm)
        """
        return {
            'length': product.get('packageLength', 0) or 0,
            'width': product.get('packageWidth', 0) or 0,
            'height': product.get('packageHeight', 0) or 0,
            'weight': product.get('packageWeight', 0) or 0,
        }
    
    @classmethod
    def extract_all_fees(cls, product: Dict, price: float) -> Dict:
        """
        提取所有费用
        
        Returns:
            {
                'fba_fee': FBA费用,
                'referral_rate': 佣金比例,
                'referral_fee': 佣金金额,
                'total_fees': 总费用,
                'is_fba_estimated': FBA费用是否估算,
            }
        """
        # FBA费用
        fba_fee = cls.extract_fba_fee(product)
        is_fba_estimated = fba_fee is None
        if fba_fee is None:
            fba_fee = cls._estimate_fba_fee_from_dimensions(product)
        
        # 佣金
        referral_rate = cls.extract_referral_fee_rate(product)
        referral_fee = price * referral_rate
        
        return {
            'fba_fee': fba_fee,
            'referral_rate': referral_rate,
            'referral_fee': referral_fee,
            'total_fees': fba_fee + referral_fee,
            'is_fba_estimated': is_fba_estimated,
            'dimensions': cls.extract_dimensions(product),
        }
    
    @classmethod
    def _get_main_category(cls, product: Dict) -> str:
        """获取主类目"""
        category_tree = product.get('categoryTree', [])
        if category_tree:
            return category_tree[0].get('name', '')
        return product.get('rootCategory', '')
    
    @classmethod
    def _estimate_fba_fee_from_dimensions(cls, product: Dict) -> float:
        """
        基于尺寸估算FBA费用
        
        当Keepa API没有直接返回FBA费用时使用
        """
        dims = cls.extract_dimensions(product)
        weight_g = dims['weight']
        
        if weight_g == 0:
            return 3.22  # 默认
        
        # 转换为英制
        weight_lb = weight_g / 453.592
        length_in = dims['length'] / 2.54
        width_in = dims['width'] / 2.54
        height_in = dims['height'] / 2.54
        
        # 计算体积重量
        volume_weight = (length_in * width_in * height_in) / 166
        billable_weight = max(weight_lb, volume_weight)
        
        # 2026年FBA费率 (简化版)
        # 标准尺寸 - 小号
        if billable_weight <= 0.75:
            return 3.22
        # 标准尺寸 - 大号
        elif billable_weight <= 1.0:
            return 3.86
        elif billable_weight <= 1.5:
            return 4.75
        elif billable_weight <= 2.0:
            return 5.77
        elif billable_weight <= 3.0:
            return 6.47
        else:
            return 7.25 + (billable_weight - 3.0) * 0.32


def get_product_fees_summary(product: Dict, price: float) -> str:
    """
    获取产品费用摘要 (用于显示)
    """
    extractor = KeepaFeeExtractor()
    fees = extractor.extract_all_fees(product, price)
    
    lines = [
        f"FBA费用: ${fees['fba_fee']:.2f}" + 
        (" (估算)" if fees['is_fba_estimated'] else " (来自Keepa)"),
        f"佣金比例: {fees['referral_rate']*100:.1f}%",
        f"佣金金额: ${fees['referral_fee']:.2f}",
        f"总费用: ${fees['total_fees']:.2f}",
        f"",
        f"产品尺寸:",
        f"  长×宽×高: {fees['dimensions']['length']:.1f}×{fees['dimensions']['width']:.1f}×{fees['dimensions']['height']:.1f} cm",
        f"  重量: {fees['dimensions']['weight']:.0f}g",
    ]
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    print("Keepa费用提取器")
    print("=" * 60)
    
    # 模拟产品数据
    test_product = {
        'asin': 'B0TEST001',
        'packageLength': 20,
        'packageWidth': 15,
        'packageHeight': 8,
        'packageWeight': 450,
        'categoryTree': [{'name': 'Electronics'}, {'name': 'Headphones'}],
        'rootCategory': 'Electronics',
    }
    
    price = 45.99
    
    print(f"\n测试产品: {test_product['asin']}")
    print(f"售价: ${price}")
    print()
    
    summary = get_product_fees_summary(test_product, price)
    print(summary)
