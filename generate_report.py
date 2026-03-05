#!/usr/bin/env python3
"""
standard process: Generate complete All based on ASIN-in-One HTML report
================================================
How to use: python generate_report.py <ASIN>

Example: python generate_report.py B0F6B5R47Q
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()


def print_banner():
    """Print welcome banner"""
    print("=" * 80)
    print("🚀 Amz-Keepa-MCP v3.0 - All-in-One report generator")
    print("=" * 80)
    print()


def validate_environment():
    """Verify environment configuration"""
    keepa_key = os.getenv("KEEPA_KEY")
    if not keepa_key:
        print("❌ Error: KEEPA not set_KEY environment variable")
        print("   Please add in .env file: KEEPA_KEY=your_api_key")
        print("   Or set it on the command line: export KEEPA_KEY=your_api_key")
        return False
    return True


def generate_complete_report(asin: str, target_moq: int = 100, max_variants: int = 8):
    """
    Generate complete All-in-One HTML report
    
    standard process:
    1. Get product data from Keepa API
    2. Automatically discover all variants
    3. Withdraw real FBA fees and commissions
    4. Generate interactive HTML reports
    
    Args:
        asin: Product ASIN
        target_moq: Target purchase quantity(Used for 1688 purchasing reference)
        max_variants: Maximum number of collected variants(Default is 8, saving API quota)
    """
    
    print(f"📦 ASIN: {asin}")
    print(f"🎯 Target MOQ: {target_moq}")
    print(f"🔢 Maximum number of variations: {max_variants}")
    print()
    
    # Step 1: Collect product data
    print("Step 1/4: Collect product data from Keepa API...")
    print("-" * 80)
    
    try:
        from variant_auto_collector import VariantAutoCollector
        
        api_key = os.getenv("KEEPA_KEY")
        collector = VariantAutoCollector(api_key)
        
        products, parent_info = collector.collect_variants(asin, max_variants=max_variants)
        parent_asin = parent_info['parent_asin']
        
        print(f"   ✅ Collection completed")
        print(f"   • Parent ASIN: {parent_asin}")
        print(f"   • Number of variants: {len(products)}")
        print(f"   • Brand: {parent_info.get('brand', 'N/A')}")
        print(f"   • Category: {parent_info.get('category', 'N/A')}")
        
    except Exception as e:
        print(f"   ❌ Collection failed: {e}")
        return None
    
    # Step 2: Extract cost data
    print()
    print("Step 2/4: Withdraw real FBA fees and commissions...")
    print("-" * 80)
    
    try:
        from keepa_fee_extractor import KeepaFeeExtractor
        
        total_fees = 0
        for product in products[:3]:  # Show first 3 variations
            data = product.get('data', {})
            price = product.get('stats', {}).get('buyBoxPrice', 2999) / 100
            
            fees = KeepaFeeExtractor.extract_all_fees(product, price)
            total_fees += fees['total_fees']
            
            asin_code = product.get('asin', '')
            print(f"   {asin_code}: FBA ${fees['fba_fee']:.2f} + Commission {fees['referral_rate']*100:.0f}%")
        
        if len(products) > 3:
            print(f"   ...and {len(products)-3} variants")
        
        print(f"   ✅ Fee withdrawal completed")
        
    except Exception as e:
        print(f"   ⚠️ Fee withdrawal warning: {e}")
    
    # Step 3: Generate Uniform Actuarial Report v2 (Contains full Keepa indicators)
    print()
    print("Step 3/3: Generate Uniform Actuarial Report v2 (Complete Keepa Indicators + Actuary analysis)...")
    print("-" * 80)
    
    try:
        from unified_report_v2 import generate_unified_report_v2
        
        # Prepare data for analysis
        analysis_data = {
            'parent_info': parent_info,
            'variants': products
        }
        
        unified_path = generate_unified_report_v2(
            asin=parent_asin,
            products=products,
            analysis_data=analysis_data
        )
        
        print(f"   ✅ Unified report generation completed")
        print(f"   • path: {unified_path}")
        print(f"   • Contains:")
        print(f"     - product information (total sales/Comment/Rating etc.)")
        print(f"     - Interactive cost calculator")
        print(f"     - Complete variant analysis table (BSR/Sales volume/score/Comment/return rate/FBA fee/Commission)")
        print(f"     - Pareto analysis (80/20)")
        print(f"     - risk assessment")
        print(f"     - action plan")
        
    except Exception as e:
        print(f"   ❌ Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return {
        'parent_asin': parent_asin,
        'unified_report': unified_path,
        'variants_count': len(products),
    }


def print_results(results):
    """Print result summary"""
    if not results:
        return
    
    print()
    print("=" * 80)
    print("✅ The unified actuary report v2 is generated!")
    print("=" * 80)
    print()
    print(f"📊 Analysis summary:")
    print(f"   • Parent ASIN: {results['parent_asin']}")
    print(f"   • Number of variants: {results['variants_count']}")
    print()
    print("📁 Generated reports:")
    print(f"   {results['unified_report']}")
    print()
    print("📋 Report contains:")
    print("   ✅ Product information (brand/Category/total sales/Number of comments/score)")
    print("   ✅Interactive cost calculator (Fill in the 1688 purchase price and it will be calculated.)")
    print("   ✅ Complete variant analysis table (BSR/Sales volume/score/Comment/return rate/FBA fee/Commission)")
    print("   ✅ Pareto analysis (80/20 core variant identification)")
    print("   ✅Risk assessment")
    print("   ✅ Investment advice and action plan")
    print()
    print("📝 Instructions for use:")
    print("   1. Open the report: open " + results['unified_report'])
    print("   2. in'Procurement cost'Fill in the input box with the purchase price found from 1688")
    print("   3. View the complete variant analysis table (Contains all Keepa metrics)")
    print("   4. Scroll down for Pareto Analysis, Risk Assessment, Action Plan")
    print()
    print("💡 Tips:")
    print("   • Variant analysis table contains: Sales volume, BSR, ratings, number of reviews, return rate, FBA fees, commission")
    print("   • You can adjust purchase prices in real time and view profits under different costs")
    print("   • All data are based on Keepa API real data")
    print()


def main():
    """main function"""
    parser = argparse.ArgumentParser(
        description='Generate complete All based on ASIN-in-One HTML report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python generate_report.py B0F6B5R47Q
  python generate_report.py B0F6B5R47Q --moq 200
  python generate_report.py B0F6B5R47Q --max-variants 8
        """
    )
    
    parser.add_argument('asin', help='Amazon product ASIN')
    parser.add_argument('--moq', type=int, default=100, 
                        help='Target purchase quantity (Default: 100)')
    parser.add_argument('--max-variants', type=int, default=8,
                        help='Maximum number of collected variants (Default: 8, 0 means no limit)')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Verification environment
    if not validate_environment():
        sys.exit(1)
    
    # Generate report
    max_variants = None if args.max_variants == 0 else args.max_variants
    results = generate_complete_report(args.asin, args.moq, max_variants)
    
    # Print results
    if results:
        print_results(results)
        print("✨ The standard process is completed!")
    else:
        print("\n❌ Report generation failed, please check the error message")
        sys.exit(1)


if __name__ == "__main__":
    main()
