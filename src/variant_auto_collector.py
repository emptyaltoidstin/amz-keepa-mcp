"""
Keepa变体自动采集器
==================
利用Keepa API的variations字段自动获取并采集所有变体数据
"""

import os
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import keepa
import pandas as pd


class VariantAutoCollector:
    """
    自动采集变体数据
    
    使用流程:
    1. 查询单个ASIN获取产品数据
    2. 从variations字段提取所有变体ASIN
    3. 批量查询所有变体获取完整数据
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化采集器
        
        Args:
            api_key: Keepa API Key，如果不提供则从环境变量获取
        """
        self.api_key = api_key or os.getenv("KEEPA_KEY", "")
        if not self.api_key:
            raise ValueError("需要提供Keepa API Key或设置KEEPA_KEY环境变量")
        
        self.api = keepa.Keepa(self.api_key)
        self.domain = "US"  # 默认美国站
    
    def collect_variants(self, asin: str, max_variants: Optional[int] = None) -> Tuple[List[Dict], Dict]:
        """
        采集单个ASIN及其所有变体的数据
        
        Args:
            asin: 任意一个变体的ASIN或父ASIN
            max_variants: 最大采集变体数量，默认None表示采集全部
            
        Returns:
            (所有变体产品数据列表, 父产品信息)
            
        Example:
            >>> collector = VariantAutoCollector()
            >>> variants, parent_info = collector.collect_variants("B0F6B5R47Q", max_variants=8)
            >>> print(f"找到 {len(variants)} 个变体")
            >>> for v in variants:
            ...     print(f"  - {v['asin']}: {v.get('color', 'N/A')} {v.get('size', 'N/A')}")
        """
        # 第1步: 查询输入的ASIN
        print(f"🔍 查询ASIN: {asin}")
        products = self.api.query(
            asin, 
            domain=self.domain, 
            history=1,  # 获取历史数据
            stats=90,   # 90天统计
            rating=1,   # 获取评论数据
            buybox=1    # 获取Buy Box数据
        )
        
        if not products:
            raise ValueError(f"未找到ASIN {asin} 的数据")
        
        main_product = products[0]
        
        # 第2步: 获取变体列表
        variation_asins = self._extract_variation_asins(main_product)
        
        if not variation_asins:
            print(f"⚠️ ASIN {asin} 没有变体数据，返回单一产品")
            return [main_product], {'parent_asin': main_product.get('parentAsin', asin), 'total_variations': 1}
        
        print(f"📦 发现 {len(variation_asins)} 个变体: {', '.join(variation_asins[:5])}{'...' if len(variation_asins) > 5 else ''}")
        
        # 限制变体数量（如果指定了max_variants）
        if max_variants and len(variation_asins) > max_variants:
            print(f"⚡ 限制采集数量: 从 {len(variation_asins)} 个变体中选择前 {max_variants} 个")
            variation_asins = variation_asins[:max_variants]
        
        # 第3步: 批量查询所有变体
        all_variants = self._batch_query_variants(variation_asins)
        
        # 确保主产品在列表中
        main_asin = main_product.get('asin', '')
        existing_asins = {v.get('asin', '') for v in all_variants}
        
        if main_asin and main_asin not in existing_asins:
            all_variants.insert(0, main_product)
        
        # 第4步: 智能处理boughtInPastMonth数据
        # 检测是否是共享的父ASIN级别数据
        all_variants = self._process_sales_data(all_variants)
        
        # 构建父产品信息
        parent_info = {
            'parent_asin': main_product.get('parentAsin', asin),
            'main_title': main_product.get('title', ''),
            'brand': main_product.get('brand', ''),
            'category': main_product.get('categoryTree', [{}])[0].get('name', '') if main_product.get('categoryTree') else '',
            'total_variations': len(all_variants),
            'variation_asins': [v.get('asin', '') for v in all_variants],
        }
        
        print(f"✅ 成功采集 {len(all_variants)} 个变体数据")
        
        return all_variants, parent_info
    
    def _extract_variation_asins(self, product: Dict) -> List[str]:
        """
        从产品数据中提取所有变体ASIN
        
        Keepa API的variations字段格式:
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
            # 如果没有variations字段，检查是否有parentAsin
            # 有些产品只在父ASIN下有完整的variations列表
            parent_asin = product.get('parentAsin', '')
            if parent_asin and parent_asin != product.get('asin', ''):
                print(f"  查询父ASIN {parent_asin} 获取变体列表...")
                try:
                    parent_products = self.api.query(parent_asin, domain=self.domain)
                    if parent_products:
                        variations = parent_products[0].get('variations', [])
                except Exception as e:
                    print(f"  查询父ASIN失败: {e}")
        
        # 提取ASIN列表
        asin_list = []
        for v in variations:
            if isinstance(v, dict):
                asin = v.get('asin', '')
                if asin:
                    asin_list.append(asin)
            elif isinstance(v, str):
                asin_list.append(v)
        
        # 去重
        asin_list = list(dict.fromkeys(asin_list))
        
        return asin_list
    
    def _batch_query_variants(self, asins: List[str], batch_size: int = 10) -> List[Dict]:
        """
        批量查询变体数据
        
        Keepa API有速率限制，分批查询避免触发限制
        
        Args:
            asins: ASIN列表
            batch_size: 每批查询的数量
            
        Returns:
            所有变体的完整数据
        """
        all_products = []
        total_batches = (len(asins) + batch_size - 1) // batch_size
        
        for i in range(0, len(asins), batch_size):
            batch = asins[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"  查询批次 {batch_num}/{total_batches}: {', '.join(batch)}")
            
            try:
                # 批量查询
                batch_products = self.api.query(
                    batch,
                    domain=self.domain,
                    history=1,
                    stats=90,
                    rating=1,
                    buybox=1
                )
                
                all_products.extend(batch_products)
                
                # 添加延迟避免速率限制
                if batch_num < total_batches:
                    import time
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"  ⚠️ 批次 {batch_num} 查询失败: {e}")
                continue
        
        return all_products
    
    def _process_sales_data(self, variants: List[Dict]) -> List[Dict]:
        """
        智能处理销量数据
        
        检测boughtInPastMonth是否是共享的父ASIN数据，
        如果是，则按BSR比例分配到各变体
        
        Args:
            variants: 所有变体的原始数据
            
        Returns:
            处理后的变体数据
        """
        if not variants:
            return variants
        
        # 提取所有变体的boughtInPastMonth
        sales_values = []
        for v in variants:
            bought = v.get('boughtInPastMonth', 0)
            if isinstance(bought, (int, float)) and bought > 0:
                sales_values.append(bought)
        
        # 如果没有销量数据，直接返回
        if not sales_values:
            return variants
        
        # 检测是否是共享数据（所有变体数值相同或非常接近）
        # 如果所有变体的boughtInPastMonth都相同，说明是父ASIN总计
        unique_sales = set(sales_values)
        is_shared_data = len(unique_sales) == 1 and len(variants) > 1
        
        if not is_shared_data:
            # 每个变体有独立的销量数据，直接使用
            return variants
        
        # 是共享数据，需要按比例分配
        total_sales = sales_values[0]
        print(f"  ℹ️ 检测到共享销量数据: {total_sales} (父ASIN总计)")
        print(f"  📊 按BSR比例分配到各变体...")
        
        # 收集所有变体的BSR
        def get_bsr(variant):
            data = variant.get('data', {})
            df_sales = data.get('df_SALES')
            if df_sales is not None and not df_sales.empty:
                try:
                    return int(df_sales['value'].iloc[-1])
                except:
                    pass
            return 999999  # 默认值
        
        all_bsr = [get_bsr(v) for v in variants]
        
        # 按BSR比例分配销量
        for i, v in enumerate(variants):
            current_bsr = all_bsr[i]
            
            # 计算权重 (BSR越低权重越高，使用平方根平滑)
            weights = [1 / (bsr ** 0.5) if bsr > 0 else 0 for bsr in all_bsr]
            total_weight = sum(weights)
            
            if total_weight > 0:
                current_weight = 1 / (current_bsr ** 0.5) if current_bsr > 0 else 0
                ratio = current_weight / total_weight
                allocated_sales = int(total_sales * ratio)
                
                # 更新变体数据
                v['_original_boughtInPastMonth'] = total_sales  # 保留原始值
                v['_sales_allocation_ratio'] = ratio  # 保留分配比例
                v['boughtInPastMonth'] = max(allocated_sales, 1)
        
        # 打印分配结果
        for v in variants:
            attrs = self.get_variation_attributes(v)
            color = attrs.get('color', 'N/A')
            allocated = v.get('boughtInPastMonth', 0)
            ratio = v.get('_sales_allocation_ratio', 0)
            print(f"    - {color}: {allocated}单/月 ({ratio*100:.1f}%)")
        
        return variants
    
    def get_variation_attributes(self, product: Dict) -> Dict[str, str]:
        """
        获取变体的属性信息 (颜色、尺寸等)
        
        Args:
            product: Keepa产品数据
            
        Returns:
            属性字典，如 {'color': 'Black', 'size': 'Large'}
        """
        attributes = {}
        
        # 直接从产品字段获取
        if product.get('color'):
            attributes['color'] = product['color']
        if product.get('size'):
            attributes['size'] = product['size']
        if product.get('style'):
            attributes['style'] = product['style']
        if product.get('flavor'):
            attributes['flavor'] = product['flavor']
        
        # 从variations列表中查找当前ASIN的属性
        current_asin = product.get('asin', '')
        variations = product.get('variations', [])
        
        for v in variations:
            if isinstance(v, dict) and v.get('asin') == current_asin:
                # 提取所有可能的属性
                for key in ['color', 'size', 'style', 'flavor', 'pattern', 'material']:
                    if v.get(key):
                        attributes[key] = v[key]
                break
        
        return attributes
    
    def format_variants_summary(self, variants: List[Dict]) -> str:
        """
        格式化变体摘要信息
        
        Args:
            variants: 变体产品列表
            
        Returns:
            格式化的摘要字符串
        """
        lines = ["\n📊 变体摘要:"]
        lines.append("-" * 90)
        lines.append(f"{'ASIN':<15} {'颜色':<10} {'尺寸':<10} {'价格':<8} {'月销量':<8} {'BSR':<10} {'评分':<6}")
        lines.append("-" * 90)
        
        total_sales = 0
        for v in variants:
            asin = v.get('asin', 'N/A')
            attrs = self.get_variation_attributes(v)
            color = attrs.get('color', 'N/A')[:8]
            size = attrs.get('size', 'N/A')[:8]
            
            # 获取价格
            price = 0
            data = v.get('data', {})
            if 'df_NEW' in data and data['df_NEW'] is not None:
                try:
                    price = data['df_NEW']['value'].iloc[-1]
                except:
                    pass
            
            # 获取销量（可能是分配后的）
            sales = v.get('boughtInPastMonth', 0)
            if isinstance(sales, (int, float)):
                total_sales += int(sales)
            
            # 获取BSR
            bsr = 0
            if 'df_SALES' in data and data['df_SALES'] is not None:
                try:
                    bsr = int(data['df_SALES']['value'].iloc[-1])
                except:
                    pass
            
            # 获取评分
            rating = v.get('stars', 0)
            
            lines.append(f"{asin:<15} {color:<10} {size:<10} ${price:<7.2f} {int(sales):<8} {bsr:<10,} {rating:<6.1f}")
        
        lines.append("-" * 90)
        lines.append(f"{'总计':<15} {'':10} {'':10} {'':8} {total_sales:<8}")
        return "\n".join(lines)


# 便捷函数
def collect_variants_for_analysis(asin: str, api_key: Optional[str] = None) -> Tuple[List[Dict], Dict]:
    """
    便捷函数：采集变体数据用于分析
    
    Args:
        asin: ASIN
        api_key: Keepa API Key
        
    Returns:
        (变体列表, 父产品信息)
        
    Example:
        >>> variants, parent = collect_variants_for_analysis("B0F6B5R47Q")
        >>> for v in variants:
        ...     print(v['asin'], v.get('color'))
    """
    collector = VariantAutoCollector(api_key)
    return collector.collect_variants(asin)


# 测试代码
if __name__ == "__main__":
    import os
    
    # 需要设置API Key
    api_key = os.getenv("KEEPA_KEY", "")
    if not api_key:
        print("请设置KEEEPA_KEY环境变量")
        exit(1)
    
    # 测试采集
    test_asin = "B0F6B5R47Q"  # 示例ASIN
    
    print("=" * 80)
    print(f"🧪 测试变体自动采集: {test_asin}")
    print("=" * 80)
    
    try:
        collector = VariantAutoCollector(api_key)
        variants, parent_info = collector.collect_variants(test_asin)
        
        print(f"\n📦 父产品信息:")
        for key, value in parent_info.items():
            if isinstance(value, list) and len(value) > 5:
                print(f"  {key}: {value[:5]}... (共{len(value)}个)")
            else:
                print(f"  {key}: {value}")
        
        # 打印变体摘要
        print(collector.format_variants_summary(variants))
        
        # 打印详细属性
        print("\n📋 变体详细属性:")
        for v in variants:
            asin = v.get('asin', '')
            attrs = collector.get_variation_attributes(v)
            attr_str = ', '.join([f"{k}={v}" for k, v in attrs.items()])
            print(f"  {asin}: {attr_str}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
