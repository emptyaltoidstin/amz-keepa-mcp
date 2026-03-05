#!/usr/bin/env python3
"""
1688 Example of purchasing price by searching pictures
==========================
Demonstrate how to use 1688 API to automatically obtain purchase prices

Preconditions:
1. Install dependencies: pip install -r requirements.txt
2. Set environment variables: export TMAPI_TOKEN=your_token
3. Or configure in .env file

Get TMAPI Token:
- access https://tmapi.top
- Register an account
- Create an application to obtain API Token
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from procurement_analyzer import (
    SmartProcurementAnalyzer, 
    generate_auto_procurement_report
)


def example_1_basic_search():
    """Example 1: Basic purchase price search"""
    print("\n" + "="*80)
    print("Example 1: Basic purchase price search")
    print("="*80)
    
    # Check environment variables
    tmapi_token = os.getenv("TMAPI_TOKEN")
    if not tmapi_token:
        print("\n⚠️ Please set up TMAPI first_TOKEN environment variable")
        print("   export TMAPI_TOKEN=your_token_here")
        print("\n Get Token: https://tmapi.top")
        return
    
    # Create analyzer
    analyzer = SmartProcurementAnalyzer.from_env()
    
    # Simulate Keepa product data
    test_product = {
        "asin": "B0EXAMPLE1",
        "title": "Wireless Bluetooth Headphones",
        "packageWeight": 450,  # 450g
        "packageLength": 20,
        "packageWidth": 15,
        "packageHeight": 8,
        "imagesCSV": "41ZulE5Q6OL,51Q3+gP8+WL",  # Simulate picture ID
        "data": {
            "images": [
                "https://m.media-amazon.com/images/I/41ZulE5Q6OL._AC_SL1000_.jpg"
            ]
        }
    }
    
    print("\n📦 Test product:")
    print(f"   ASIN: {test_product['asin']}")
    print(f"   weight: {test_product['packageWeight']}g")
    print(f"   pictures: {test_product['data']['images'][0]}")
    
    print("\n🔍 Search 1688 purchase price...")
    result = analyzer.analyze_product(test_product, target_moq=50)
    
    print("\n📊 search results:")
    print(f"   find price: {'✅ Yes' if result.found else '❌ No'}")
    
    if result.found:
        print(f"   purchase price: ¥{result.price_rmb:.2f}")
        print(f"   MOQ: {result.moq}")
        print(f"   supplier: {result.supplier}")
        print(f"   Matching degree: {result.match_score:.2%}")
        print(f"   Confidence: {result.confidence}")
        print(f"   First leg freight: ¥{result.shipping_cost_rmb:.2f}")
        print(f"   Total COGS: ${result.total_cogs_usd:.2f}")
        print(f"   1688 link: {result.source_url}")
    else:
        print(f"   Remarks: {result.note}")


def example_2_full_report():
    """Example 2: Generate complete automated purchase price reports"""
    print("\n" + "="*80)
    print("Example 2: Generate complete automated purchase price reports")
    print("="*80)
    
    # Check environment variables
    tmapi_token = os.getenv("TMAPI_TOKEN")
    keepa_key = os.getenv("KEEPA_KEY")
    
    if not tmapi_token or not keepa_key:
        print("\n⚠️ Please set environment variables:")
        if not keepa_key:
            print("   export KEEPA_KEY=your_keepa_key")
        if not tmapi_token:
            print("   export TMAPI_TOKEN=your_tmapi_token")
        return
    
    # Test ASIN
    test_asin = "B0F6B5R47Q"  # Please replace with actual ASIN
    
    print(f"\n🚀 is ASIN {test_asin} Generate automatic purchase price reports...")
    print("\nThis will automatically:")
    print("   1. Get product data from Keepa")
    print("   2. Search purchase price from 1688")
    print("   3. Calculate the full cost")
    print("   4. Generate actuary report")
    
    try:
        report_path, analyses = generate_auto_procurement_report(
            asin=test_asin,
            target_moq=100
        )
        
        print(f"\n✅ Report generated: {report_path}")
        
        # Print Procurement Analysis Summary
        print("\n💰 Purchase Price Summary:")
        for asin, analysis in analyses.items():
            if analysis.found:
                print(f"   {asin}: ¥{analysis.price_rmb:.2f} (MOQ:{analysis.moq})")
            else:
                print(f"   {asin}: not found - {analysis.note}")
        
    except Exception as e:
        print(f"\n❌ error: {e}")


def example_3_manual_input():
    """Example 3: Manually enter purchase price (without API)"""
    print("\n" + "="*80)
    print("Example 3: Manually enter purchase price")
    print("="*80)
    
    print("\n📝 When there is no 1688 API, you can manually enter the purchase price:")
    
    # Create analyzer without API
    analyzer = SmartProcurementAnalyzer(tmapi_token=None)
    
    test_product = {
        "asin": "B0MANUAL01",
        "title": "Manual Input Example",
        "packageWeight": 350,
    }
    
    result = analyzer.analyze_product(test_product)
    
    print(f"\n products: {test_product['asin']}")
    print(f"   weight: {test_product['packageWeight']}g")
    print(f"   First leg freight(Automatic calculation): ¥{result.shipping_cost_rmb:.2f}")
    print(f"\n   {result.note}")
    
    print("\n💡 Fill in the purchase cost in the interactive report and it will be automatically calculated:")
    print("   1. open *_ALLINONE_INTERACTIVE.html report")
    print("   2. in'Procurement cost'Fill in the price in the input box")
    print("   3. The system automatically calculates complete profit analysis")


def example_4_api_usage_guide():
    """Example 4: API usage guide"""
    print("\n" + "="*80)
    print("1688 API Usage Guide")
    print("="*80)
    
    guide = """
[Comparison of plans]

1️⃣ TMAPI (recommend)
   advantage: Simple and fast, no corporate qualifications required
   shortcoming: Charged service
   price: approx. $0.01-0.05/calls
   get: https://tmapi.top
   
2️⃣ 1688 official open platform
   advantage: free
   shortcoming: Requires enterprise qualification application
   get: https://open.1688.com
   
3️⃣ Manual input
   advantage: Free and accurate
   shortcoming: time consuming
   use: Open the interactive report and fill in the costs

【Usage process】

1. Register TMAPI (https://tmapi.top)
   - Register an account
   - Create app
   - Get API Token

2. Configure environment variables
   export TMAPI_TOKEN=your_token_here
   export KEEPA_KEY=your_keepa_key

3. Run the analysis
   from procurement_analyzer import generate_auto_procurement_report
   report, analyses = generate_auto_procurement_report('B0XXXXXX')

【Notes】

⚠️ Image restrictions:
   - 1688’s image search mainly supports Alibaba platform images
   - Amazon images may need to be converted to Alibaba Pictures first
   
⚠️ Matching accuracy:
   - The accuracy of image search depends on image quality and database coverage
   - It is recommended to manually confirm the purchase price of key products
   
⚠️MOQ consideration:
   - Pay attention to whether the MOQ is suitable for your purchasing volume
   - The system will mark the situation when the MOQ is higher than the target value

[Cost calculation formula]

Total COGS (USD) = [purchase price(RMB) + First leg freight(RMB)] × 1.15(tariff) ÷ exchange rate

in:
- First leg freight = weight(kg) × 12 RMB/kg
- exchange rate = 7.2 RMB/USD (Configurable)
- tariff = 15% (Configurable)
"""
    
    print(guide)


if __name__ == "__main__":
    print("1688 Example of purchasing price by searching pictures")
    print("=" * 80)
    
    # Show menu
    print("\nSelect example:")
    print("   1. Basic purchase price search")
    print("   2. Generate complete automated reports")
    print("   3. Manual input example")
    print("   4. API usage guide")
    print("   0. Run all")
    
    choice = input("\nInput options (0-4): ").strip()
    
    if choice == "1":
        example_1_basic_search()
    elif choice == "2":
        example_2_full_report()
    elif choice == "3":
        example_3_manual_input()
    elif choice == "4":
        example_4_api_usage_guide()
    elif choice == "0":
        example_1_basic_search()
        example_3_manual_input()
        example_4_api_usage_guide()
        print("\n" + "="*80)
        print("Example 2 requires the actual API Key, please configure it before running")
    else:
        print("Invalid option")
