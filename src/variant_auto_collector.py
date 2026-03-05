"""
Keepa variant automatic collector
==================
Use the variations field of the Keepa API to automatically obtain and collect all variant data
"""

import os
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import keepa
import pandas as pd


class VariantAutoCollector:
    """
    Automatic collection of variant data
    
    Usage process:
    1. Query a single ASIN to obtain product data
    2. Extract all variant ASINs from the variations field
    3. Query all variants in batches to obtain complete data
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize collector
        
        Args:
            api_key: Keepa API Key, if not provided, it will be obtained from environment variables
        """
        self.api_key = api_key or os.getenv("KEEPA_KEY", "")
        if not self.api_key:
            raise ValueError("Need to provide Keepa API Key or set KEEPA_KEY environment variable")
        
        self.api = keepa.Keepa(self.api_key)
        self.domain = "US"  # Default US site
    
    def collect_variants(self, asin: str, max_variants: Optional[int] = None) -> Tuple[List[Dict], Dict]:
        """
        Capture data for a single ASIN and all its variations
        
        Args:
            asin: Any variant ASIN or parent ASIN
            max_variants: The maximum number of collected variants, the default None means collecting all
            
        Returns:
            (List of all variant product data, Parent product information)
            
        Example:
            >>> collector = VariantAutoCollector()
            >>> variants, parent_info = collector.collect_variants("B0F6B5R47Q", max_variants=8)
            >>> print(f"found {len(variants)} variants")
            >>> for v in variants:
            ...     print(f"  - {v['asin']}: {v.get('color', 'N/A')} {v.get('size', 'N/A')}")
        """
        # Step 1: Query the entered ASIN
        print(f"🔍 Check ASIN: {asin}")
        products = self.api.query(
            asin, 
            domain=self.domain, 
            history=1,  # Get historical data
            stats=90,   # 90 days statistics
            rating=1,   # Get comment data
            buybox=1    # Get Buy Box data
        )
        
        if not products:
            raise ValueError(f"ASIN not found {asin} data")
        
        main_product = products[0]
        
        # Step 2: Get a list of variants
        variation_asins = self._extract_variation_asins(main_product)
        
        if not variation_asins:
            print(f"⚠️ ASIN {asin} No variant data, single product returned")
            return [main_product], {'parent_asin': main_product.get('parentAsin', asin), 'total_variations': 1}
        
        print(f"📦 Discover {len(variation_asins)} variants: {', '.join(variation_asins[:5])}{'...' if len(variation_asins) > 5 else ''}")
        
        # Limit the number of variants (if max is specified_variants）
        if max_variants and len(variation_asins) > max_variants:
            print(f"⚡ Limit the number of collections: from {len(variation_asins)} Before selecting among variations {max_variants} a")
            variation_asins = variation_asins[:max_variants]
        
        # Step 3: Query all variants in batches
        all_variants = self._batch_query_variants(variation_asins)
        
        # Make sure the main product is in the list
        main_asin = main_product.get('asin', '')
        existing_asins = {v.get('asin', '') for v in all_variants}
        
        if main_asin and main_asin not in existing_asins:
            all_variants.insert(0, main_product)
        
        # Step 4: Intelligent processing of boughtInPastMonth data
        # Detect whether it is shared parent ASIN level data
        all_variants = self._process_sales_data(all_variants)
        
        # Build parent product information
        parent_info = {
            'parent_asin': main_product.get('parentAsin', asin),
            'main_title': main_product.get('title', ''),
            'brand': main_product.get('brand', ''),
            'category': main_product.get('categoryTree', [{}])[0].get('name', '') if main_product.get('categoryTree') else '',
            'total_variations': len(all_variants),
            'variation_asins': [v.get('asin', '') for v in all_variants],
        }
        
        print(f"✅ Successfully collected {len(all_variants)} variant data")
        
        return all_variants, parent_info
    
    def _extract_variation_asins(self, product: Dict) -> List[str]:
        """
        Extract all variant ASINs from product data
        
        Variations field format of Keepa API:
        {
            'asin': 'B0XXX',
            'title': 'Product Title - Black',
            'variations': [
                {'asin': 'B0XXX', 'color': 'Black'},
                {'asin': 'B0YYY', 'color': 'Brown'},
                ...
            ]
        }
        """
        variations = product.get('variations', [])
        
        if not variations:
            # If there is no variations field, check if there is parentAsin
            # Some products only have a full list of variations under the parent ASIN
            parent_asin = product.get('parentAsin', '')
            if parent_asin and parent_asin != product.get('asin', ''):
                print(f"  Query parent ASIN {parent_asin} Get a list of variants...")
                try:
                    parent_products = self.api.query(parent_asin, domain=self.domain)
                    if parent_products:
                        variations = parent_products[0].get('variations', [])
                except Exception as e:
                    print(f"  Failed to query parent ASIN: {e}")
        
        # Extract ASIN list
        asin_list = []
        for v in variations:
            if isinstance(v, dict):
                asin = v.get('asin', '')
                if asin:
                    asin_list.append(asin)
            elif isinstance(v, str):
                asin_list.append(v)
        
        # Remove duplicates
        asin_list = list(dict.fromkeys(asin_list))
        
        return asin_list
    
    def _batch_query_variants(self, asins: List[str], batch_size: int = 10) -> List[Dict]:
        """
        Query variation data in batches
        
        Keepa API has rate limit, query in batches to avoid triggering the limit
        
        Args:
            asins: ASIN list
            batch_size: Quantity per batch of queries
            
        Returns:
            Complete data for all variants
        """
        all_products = []
        total_batches = (len(asins) + batch_size - 1) // batch_size
        
        for i in range(0, len(asins), batch_size):
            batch = asins[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"  Query batch {batch_num}/{total_batches}: {', '.join(batch)}")
            
            try:
                # Batch query
                batch_products = self.api.query(
                    batch,
                    domain=self.domain,
                    history=1,
                    stats=90,
                    rating=1,
                    buybox=1
                )
                
                all_products.extend(batch_products)
                
                # Add delay to avoid rate limiting
                if batch_num < total_batches:
                    import time
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"  ⚠️ Batch {batch_num} Query failed: {e}")
                continue
        
        return all_products
    
    def _process_sales_data(self, variants: List[Dict]) -> List[Dict]:
        """
        Intelligent processing of sales data
        
        Detect whether boughtInPastMonth is shared parent ASIN data,
        If so, allocate to each variant in proportion to BSR
        
        Args:
            variants: Raw data for all variants
            
        Returns:
            Processed variant data
        """
        if not variants:
            return variants
        
        # Extract boughtInPastMonth of all variants
        sales_values = []
        for v in variants:
            bought = v.get('boughtInPastMonth', 0)
            if isinstance(bought, (int, float)) and bought > 0:
                sales_values.append(bought)
        
        # If there is no sales data, return directly
        if not sales_values:
            return variants
        
        # Check whether the data is shared (all variants have the same value or are very close)
        # If boughtInPastMonth is the same for all variants, it means the parent ASIN total
        unique_sales = set(sales_values)
        is_shared_data = len(unique_sales) == 1 and len(variants) > 1
        
        if not is_shared_data:
            # Each variant has independent sales data, which can be used directly
            return variants
        
        # It is shared data and needs to be allocated proportionally
        total_sales = sales_values[0]
        print(f"  ℹ️ Shared sales data detected: {total_sales} (Total parent ASINs)")
        print(f"  📊 Distributed to each variant according to BSR ratio...")
        
        # Collect BSR for all variants
        def get_bsr(variant):
            data = variant.get('data', {})
            df_sales = data.get('df_SALES')
            if df_sales is not None and not df_sales.empty:
                try:
                    return int(df_sales['value'].iloc[-1])
                except:
                    pass
            return 999999  # Default value
        
        all_bsr = [get_bsr(v) for v in variants]
        
        # Allocate sales volume according to BSR ratio
        for i, v in enumerate(variants):
            current_bsr = all_bsr[i]
            
            # Calculate weight (The lower the BSR, the higher the weight, and square root smoothing is used.)
            weights = [1 / (bsr ** 0.5) if bsr > 0 else 0 for bsr in all_bsr]
            total_weight = sum(weights)
            
            if total_weight > 0:
                current_weight = 1 / (current_bsr ** 0.5) if current_bsr > 0 else 0
                ratio = current_weight / total_weight
                allocated_sales = int(total_sales * ratio)
                
                # Update variant data
                v['_original_boughtInPastMonth'] = total_sales  # Keep original value
                v['_sales_allocation_ratio'] = ratio  # Reserve allocation ratio
                v['boughtInPastMonth'] = max(allocated_sales, 1)
        
        # Print allocation results
        for v in variants:
            attrs = self.get_variation_attributes(v)
            color = attrs.get('color', 'N/A')
            allocated = v.get('boughtInPastMonth', 0)
            ratio = v.get('_sales_allocation_ratio', 0)
            print(f"    - {color}: {allocated}Single/month ({ratio*100:.1f}%)")
        
        return variants
    
    def get_variation_attributes(self, product: Dict) -> Dict[str, str]:
        """
        Get attribute information of a variant (Color, size, etc.)
        
        Args:
            product: Keepa product data
            
        Returns:
            attribute dictionary, such as {'color': 'Black', 'size': 'Large'}
        """
        attributes = {}
        
        # Get it directly from the product field
        if product.get('color'):
            attributes['color'] = product['color']
        if product.get('size'):
            attributes['size'] = product['size']
        if product.get('style'):
            attributes['style'] = product['style']
        if product.get('flavor'):
            attributes['flavor'] = product['flavor']
        
        # Find the attributes of the current ASIN from the variations list
        current_asin = product.get('asin', '')
        variations = product.get('variations', [])
        
        for v in variations:
            if isinstance(v, dict) and v.get('asin') == current_asin:
                # Extract all possible attributes
                for key in ['color', 'size', 'style', 'flavor', 'pattern', 'material']:
                    if v.get(key):
                        attributes[key] = v[key]
                break
        
        return attributes
    
    def format_variants_summary(self, variants: List[Dict]) -> str:
        """
        Format variant summary information
        
        Args:
            variants: Variant product list
            
        Returns:
            Formatted summary string
        """
        lines = ["\n📊 variant summary:"]
        lines.append("-" * 90)
        lines.append(f"{'ASIN':<15} {'color':<10} {'Size':<10} {'price':<8} {'monthly sales':<8} {'BSR':<10} {'score':<6}")
        lines.append("-" * 90)
        
        total_sales = 0
        for v in variants:
            asin = v.get('asin', 'N/A')
            attrs = self.get_variation_attributes(v)
            color = attrs.get('color', 'N/A')[:8]
            size = attrs.get('size', 'N/A')[:8]
            
            # get price
            price = 0
            data = v.get('data', {})
            if 'df_NEW' in data and data['df_NEW'] is not None:
                try:
                    price = data['df_NEW']['value'].iloc[-1]
                except:
                    pass
            
            # Get sales volume (possibly after distribution)
            sales = v.get('boughtInPastMonth', 0)
            if isinstance(sales, (int, float)):
                total_sales += int(sales)
            
            # Get BSR
            bsr = 0
            if 'df_SALES' in data and data['df_SALES'] is not None:
                try:
                    bsr = int(data['df_SALES']['value'].iloc[-1])
                except:
                    pass
            
            # Get rating
            rating = v.get('stars', 0)
            
            lines.append(f"{asin:<15} {color:<10} {size:<10} ${price:<7.2f} {int(sales):<8} {bsr:<10,} {rating:<6.1f}")
        
        lines.append("-" * 90)
        lines.append(f"{'total':<15} {'':10} {'':10} {'':8} {total_sales:<8}")
        return "\n".join(lines)


# Convenience function
def collect_variants_for_analysis(asin: str, api_key: Optional[str] = None) -> Tuple[List[Dict], Dict]:
    """
    Convenience function: collecting variant data for analysis
    
    Args:
        asin: ASIN
        api_key: Keepa API Key
        
    Returns:
        (Variation list, Parent product information)
        
    Example:
        >>> variants, parent = collect_variants_for_analysis("B0F6B5R47Q")
        >>> for v in variants:
        ...     print(v['asin'], v.get('color'))
    """
    collector = VariantAutoCollector(api_key)
    return collector.collect_variants(asin)


# test code
if __name__ == "__main__":
    import os
    
    # Need to set API Key
    api_key = os.getenv("KEEPA_KEY", "")
    if not api_key:
        print("Please set KEEEPA_KEY environment variable")
        exit(1)
    
    # Test collection
    test_asin = "B0F6B5R47Q"  # Example ASIN
    
    print("=" * 80)
    print(f"🧪 Automatic collection of test variants: {test_asin}")
    print("=" * 80)
    
    try:
        collector = VariantAutoCollector(api_key)
        variants, parent_info = collector.collect_variants(test_asin)
        
        print(f"\n📦 Parent product information:")
        for key, value in parent_info.items():
            if isinstance(value, list) and len(value) > 5:
                print(f"  {key}: {value[:5]}... (total{len(value)}a)")
            else:
                print(f"  {key}: {value}")
        
        # Print variant summary
        print(collector.format_variants_summary(variants))
        
        # Print detailed properties
        print("\n📋 variant detailed attributes:")
        for v in variants:
            asin = v.get('asin', '')
            attrs = collector.get_variation_attributes(v)
            attr_str = ', '.join([f"{k}={v}" for k, v in attrs.items()])
            print(f"  {asin}: {attr_str}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
