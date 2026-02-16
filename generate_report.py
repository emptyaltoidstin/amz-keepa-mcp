#!/usr/bin/env python3
"""
标准流程: 基于ASIN生成完整All-in-One HTML报告
================================================
使用方法: python generate_report.py <ASIN>

示例: python generate_report.py B0F6B5R47Q
"""

import sys
import os
import argparse
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()


def print_banner():
    """打印欢迎横幅"""
    print("=" * 80)
    print("🚀 Amz-Keepa-MCP v3.0 - All-in-One 报告生成器")
    print("=" * 80)
    print()


def validate_environment():
    """验证环境配置"""
    keepa_key = os.getenv("KEEPA_KEY")
    if not keepa_key:
        print("❌ 错误: 未设置 KEEPA_KEY 环境变量")
        print("   请在 .env 文件中添加: KEEPA_KEY=your_api_key")
        print("   或在命令行设置: export KEEPA_KEY=your_api_key")
        return False
    return True


def generate_complete_report(asin: str, target_moq: int = 100):
    """
    生成完整的All-in-One HTML报告
    
    标准流程:
    1. 从Keepa API获取产品数据
    2. 自动发现所有变体
    3. 提取真实FBA费用和佣金
    4. 生成交互式HTML报告
    
    Args:
        asin: 产品ASIN
        target_moq: 目标采购量(用于1688采购参考)
    """
    
    print(f"📦 ASIN: {asin}")
    print(f"🎯 目标MOQ: {target_moq}")
    print()
    
    # 步骤1: 采集产品数据
    print("步骤 1/4: 从Keepa API采集产品数据...")
    print("-" * 80)
    
    try:
        from variant_auto_collector import VariantAutoCollector
        
        api_key = os.getenv("KEEPA_KEY")
        collector = VariantAutoCollector(api_key)
        
        products, parent_info = collector.collect_variants(asin)
        parent_asin = parent_info['parent_asin']
        
        print(f"   ✅ 采集完成")
        print(f"   • 父ASIN: {parent_asin}")
        print(f"   • 变体数量: {len(products)}")
        print(f"   • 品牌: {parent_info.get('brand', 'N/A')}")
        print(f"   • 类目: {parent_info.get('category', 'N/A')}")
        
    except Exception as e:
        print(f"   ❌ 采集失败: {e}")
        return None
    
    # 步骤2: 提取费用数据
    print()
    print("步骤 2/4: 提取真实FBA费用和佣金...")
    print("-" * 80)
    
    try:
        from keepa_fee_extractor import KeepaFeeExtractor
        
        total_fees = 0
        for product in products[:3]:  # 显示前3个变体
            data = product.get('data', {})
            price = product.get('stats', {}).get('buyBoxPrice', 2999) / 100
            
            fees = KeepaFeeExtractor.extract_all_fees(product, price)
            total_fees += fees['total_fees']
            
            asin_code = product.get('asin', '')
            print(f"   {asin_code}: FBA ${fees['fba_fee']:.2f} + 佣金 {fees['referral_rate']*100:.0f}%")
        
        if len(products) > 3:
            print(f"   ... 还有 {len(products)-3} 个变体")
        
        print(f"   ✅ 费用提取完成")
        
    except Exception as e:
        print(f"   ⚠️  费用提取警告: {e}")
    
    # 步骤3: 生成统一精算师报告 v2 (包含完整Keepa指标)
    print()
    print("步骤 3/3: 生成统一精算师报告 v2 (完整Keepa指标 + 精算师分析)...")
    print("-" * 80)
    
    try:
        from unified_report_v2 import generate_unified_report_v2
        
        # 准备分析数据
        analysis_data = {
            'parent_info': parent_info,
            'variants': products
        }
        
        unified_path = generate_unified_report_v2(
            asin=parent_asin,
            products=products,
            analysis_data=analysis_data
        )
        
        print(f"   ✅ 统一报告生成完成")
        print(f"   • 路径: {unified_path}")
        print(f"   • 包含:")
        print(f"     - 产品信息 (总销量/评论/评分等)")
        print(f"     - 交互式成本计算器")
        print(f"     - 完整变体分析表 (BSR/销量/评分/评论/退货率/FBA费/佣金)")
        print(f"     - 帕累托分析 (80/20)")
        print(f"     - 风险评估")
        print(f"     - 行动计划")
        
    except Exception as e:
        print(f"   ❌ 报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return {
        'parent_asin': parent_asin,
        'unified_report': unified_path,
        'variants_count': len(products),
    }


def print_results(results):
    """打印结果摘要"""
    if not results:
        return
    
    print()
    print("=" * 80)
    print("✅ 统一精算师报告 v2 生成完成!")
    print("=" * 80)
    print()
    print(f"📊 分析摘要:")
    print(f"   • 父ASIN: {results['parent_asin']}")
    print(f"   • 变体数量: {results['variants_count']}")
    print()
    print("📁 生成的报告:")
    print(f"   {results['unified_report']}")
    print()
    print("📋 报告包含:")
    print("   ✅ 产品信息 (品牌/类目/总销量/评论数/评分)")
    print("   ✅ 交互式成本计算器 (填入1688采购价即计算)")
    print("   ✅ 完整变体分析表 (BSR/销量/评分/评论/退货率/FBA费/佣金)")
    print("   ✅ 帕累托分析 (80/20核心变体识别)")
    print("   ✅ 风险评估")
    print("   ✅ 投资建议与行动计划")
    print()
    print("📝 使用说明:")
    print("   1. 打开报告: open " + results['unified_report'])
    print("   2. 在'采购成本'输入框填入从1688找到的采购价")
    print("   3. 查看完整变体分析表 (包含所有Keepa指标)")
    print("   4. 向下滚动查看帕累托分析、风险评估、行动计划")
    print()
    print("💡 提示:")
    print("   • 变体分析表包含: 销量、BSR、评分、评论数、退货率、FBA费、佣金")
    print("   • 可以实时调整采购价，查看不同成本下的利润")
    print("   • 所有数据基于Keepa API真实数据")
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='基于ASIN生成完整All-in-One HTML报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python generate_report.py B0F6B5R47Q
  python generate_report.py B0F6B5R47Q --moq 200
        """
    )
    
    parser.add_argument('asin', help='Amazon产品ASIN')
    parser.add_argument('--moq', type=int, default=100, 
                        help='目标采购量 (默认: 100)')
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    # 验证环境
    if not validate_environment():
        sys.exit(1)
    
    # 生成报告
    results = generate_complete_report(args.asin, args.moq)
    
    # 打印结果
    if results:
        print_results(results)
        print("✨ 标准流程执行完毕!")
    else:
        print("\n❌ 报告生成失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
