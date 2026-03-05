"""
Keepa API Fee Extractor
==================
Extract real FBA fee and commission data from Keepa API
"""

from typing import Dict, Optional, Tuple


class KeepaFeeExtractor:
    """
    Extract real FBA fees and commissions from Keepa API product data
    
    Keepa API can return:
    - FBA fees (fbaFees)
    - Commission ratio (referralFeePercentage)
    - Product size (package dimensions)
    - Product weight (package weight)
    """
    
    # Amazon commission ratio table (by category)
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
        Withdraw FBA fees
        
        Keepa API may return FBA fees in the following fields:
        - fbaFees (direct costs)
        - data.fbaFees
        - or need to size from/Weight calculation
        """
        # Try to get FBA fees directly
        fba_fee = product.get('fbaFees')
        if fba_fee and isinstance(fba_fee, (int, float)) and fba_fee > 0:
            return float(fba_fee) / 100  # Keepa may be stored in cents
        
        # Get from data field
        data = product.get('data', {})
        if data:
            fba_fee = data.get('fbaFees')
            if fba_fee and isinstance(fba_fee, (int, float)) and fba_fee > 0:
                return float(fba_fee) / 100
            
            # Get from CSV data
            csv = data.get('csv', [])
            # FBA fees are usually in a specific CSV index
            # According to Keepa documentation, FBA fees may be in specific csv fields
            if len(csv) > 70:  # Assume that the FBA fee is on a certain index
                # This needs to be determined based on the actual Keepa data structure
                pass
        
        # If there is no direct data, return None to let the caller estimate
        return None
    
    @classmethod
    def extract_referral_fee_rate(cls, product: Dict) -> float:
        """
        Withdraw commission ratio
        
        Priority:
        1. ReferralFeePercentage returned directly by Keepa API
        2. Inference based on category
        3. Default 15%
        """
        # Try to get it directly
        referral_pct = product.get('referralFeePercentage')
        if referral_pct and isinstance(referral_pct, (int, float)) and referral_pct > 0:
            return referral_pct / 100 if referral_pct > 1 else referral_pct
        
        # Get from data field
        data = product.get('data', {})
        if data:
            referral_pct = data.get('referralFeePercentage')
            if referral_pct and isinstance(referral_pct, (int, float)) and referral_pct > 0:
                return referral_pct / 100 if referral_pct > 1 else referral_pct
        
        # Inference based on category
        category = cls._get_main_category(product)
        if category:
            for cat_pattern, rate in cls.REFERRAL_FEE_RATES.items():
                if cat_pattern.lower() in category.lower():
                    return rate
        
        # Default 15%
        return 0.15
    
    @classmethod
    def extract_referral_fee(cls, product: Dict, price: float) -> float:
        """
        Calculate commission amount
        
        Args:
            product: Keepa product data
            price: selling price(USD)
        """
        rate = cls.extract_referral_fee_rate(product)
        return price * rate
    
    @classmethod
    def extract_dimensions(cls, product: Dict) -> Dict[str, float]:
        """
        Extract product dimensions (cm)
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
        Withdraw all fees
        
        Returns:
            {
                'fba_fee': FBA fees,
                'referral_rate': Commission ratio,
                'referral_fee': Commission amount,
                'total_fees': total cost,
                'is_fba_estimated': Are FBA fees estimated?,
            }
        """
        # FBA fees
        fba_fee = cls.extract_fba_fee(product)
        is_fba_estimated = fba_fee is None
        if fba_fee is None:
            fba_fee = cls._estimate_fba_fee_from_dimensions(product)
        
        # Commission
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
        """Get main category"""
        category_tree = product.get('categoryTree', [])
        if category_tree:
            return category_tree[0].get('name', '')
        return product.get('rootCategory', '')
    
    @classmethod
    def _estimate_fba_fee_from_dimensions(cls, product: Dict) -> float:
        """
        Estimate FBA fees based on size
        
        Used when Keepa API does not directly return FBA fees
        """
        dims = cls.extract_dimensions(product)
        weight_g = dims['weight']
        
        if weight_g == 0:
            return 3.22  # Default
        
        # Convert to imperial
        weight_lb = weight_g / 453.592
        length_in = dims['length'] / 2.54
        width_in = dims['width'] / 2.54
        height_in = dims['height'] / 2.54
        
        # Calculate volumetric weight
        volume_weight = (length_in * width_in * height_in) / 166
        billable_weight = max(weight_lb, volume_weight)
        
        # FBA rates in 2026 (Simplified version)
        # Standard size - trumpet
        if billable_weight <= 0.75:
            return 3.22
        # Standard size - Large size
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
    Get product fee summary (for display)
    """
    extractor = KeepaFeeExtractor()
    fees = extractor.extract_all_fees(product, price)
    
    lines = [
        f"FBA fees: ${fees['fba_fee']:.2f}" + 
        (" (Estimate)" if fees['is_fba_estimated'] else " (from Keepa)"),
        f"Commission ratio: {fees['referral_rate']*100:.1f}%",
        f"Commission amount: ${fees['referral_fee']:.2f}",
        f"total cost: ${fees['total_fees']:.2f}",
        f"",
        f"Product size:",
        f"  Length×width×height: {fees['dimensions']['length']:.1f}×{fees['dimensions']['width']:.1f}×{fees['dimensions']['height']:.1f} cm",
        f"  weight: {fees['dimensions']['weight']:.0f}g",
    ]
    
    return "\n".join(lines)


if __name__ == "__main__":
    # test
    print("Keepa fee extractor")
    print("=" * 60)
    
    # Simulated product data
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
    
    print(f"\ntest products: {test_product['asin']}")
    print(f"selling price: ${price}")
    print()
    
    summary = get_product_fees_summary(test_product, price)
    print(summary)
