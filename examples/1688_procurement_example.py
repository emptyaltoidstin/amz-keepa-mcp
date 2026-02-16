#!/usr/bin/env python3
"""
1688 以图搜图采购价格示例
==========================
演示如何使用1688 API自动获取采购价格

前置条件:
1. 安装依赖: pip install -r requirements.txt
2. 设置环境变量: export TMAPI_TOKEN=your_token
3. 或在 .env 文件中配置

获取TMAPI Token:
- 访问 https://tmapi.top
- 注册账号
- 创建应用获取 API Token
"""

import os
import sys

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from procurement_analyzer import (
    SmartProcurementAnalyzer, 
    generate_auto_procurement_report
)


def example_1_basic_search():
    """示例1: 基本采购价格搜索"""
    print("\n" + "="*80)
    print("示例1: 基本采购价格搜索")
    print("="*80)
    
    # 检查环境变量
    tmapi_token = os.getenv("TMAPI_TOKEN")
    if not tmapi_token:
        print("\n⚠️  请先设置 TMAPI_TOKEN 环境变量")
        print("   export TMAPI_TOKEN=your_token_here")
        print("\n   获取Token: https://tmapi.top")
        return
    
    # 创建分析器
    analyzer = SmartProcurementAnalyzer.from_env()
    
    # 模拟Keepa产品数据
    test_product = {
        "asin": "B0EXAMPLE1",
        "title": "Wireless Bluetooth Headphones",
        "packageWeight": 450,  # 450g
        "packageLength": 20,
        "packageWidth": 15,
        "packageHeight": 8,
        "imagesCSV": "41ZulE5Q6OL,51Q3+gP8+WL",  # 模拟图片ID
        "data": {
            "images": [
                "https://m.media-amazon.com/images/I/41ZulE5Q6OL._AC_SL1000_.jpg"
            ]
        }
    }
    
    print("\n📦 测试产品:")
    print(f"   ASIN: {test_product['asin']}")
    print(f"   重量: {test_product['packageWeight']}g")
    print(f"   图片: {test_product['data']['images'][0]}")
    
    print("\n🔍 搜索1688采购价格...")
    result = analyzer.analyze_product(test_product, target_moq=50)
    
    print("\n📊 搜索结果:")
    print(f"   找到价格: {'✅ 是' if result.found else '❌ 否'}")
    
    if result.found:
        print(f"   采购价格: ¥{result.price_rmb:.2f}")
        print(f"   MOQ: {result.moq}")
        print(f"   供应商: {result.supplier}")
        print(f"   匹配度: {result.match_score:.2%}")
        print(f"   置信度: {result.confidence}")
        print(f"   头程运费: ¥{result.shipping_cost_rmb:.2f}")
        print(f"   总COGS: ${result.total_cogs_usd:.2f}")
        print(f"   1688链接: {result.source_url}")
    else:
        print(f"   备注: {result.note}")


def example_2_full_report():
    """示例2: 生成完整的自动采购价格报告"""
    print("\n" + "="*80)
    print("示例2: 生成完整自动采购价格报告")
    print("="*80)
    
    # 检查环境变量
    tmapi_token = os.getenv("TMAPI_TOKEN")
    keepa_key = os.getenv("KEEPA_KEY")
    
    if not tmapi_token or not keepa_key:
        print("\n⚠️  请设置环境变量:")
        if not keepa_key:
            print("   export KEEPA_KEY=your_keepa_key")
        if not tmapi_token:
            print("   export TMAPI_TOKEN=your_tmapi_token")
        return
    
    # 测试ASIN
    test_asin = "B0F6B5R47Q"  # 请替换为实际的ASIN
    
    print(f"\n🚀 为 ASIN {test_asin} 生成自动采购价格报告...")
    print("\n这将自动:")
    print("   1. 从Keepa获取产品数据")
    print("   2. 从1688搜索采购价格")
    print("   3. 计算完整成本")
    print("   4. 生成精算师报告")
    
    try:
        report_path, analyses = generate_auto_procurement_report(
            asin=test_asin,
            target_moq=100
        )
        
        print(f"\n✅ 报告已生成: {report_path}")
        
        # 打印采购分析摘要
        print("\n💰 采购价格摘要:")
        for asin, analysis in analyses.items():
            if analysis.found:
                print(f"   {asin}: ¥{analysis.price_rmb:.2f} (MOQ:{analysis.moq})")
            else:
                print(f"   {asin}: 未找到 - {analysis.note}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")


def example_3_manual_input():
    """示例3: 手动输入采购价格（无API时）"""
    print("\n" + "="*80)
    print("示例3: 手动输入采购价格")
    print("="*80)
    
    print("\n📝 在没有1688 API时，您可以手动输入采购价格:")
    
    # 创建不带API的分析器
    analyzer = SmartProcurementAnalyzer(tmapi_token=None)
    
    test_product = {
        "asin": "B0MANUAL01",
        "title": "Manual Input Example",
        "packageWeight": 350,
    }
    
    result = analyzer.analyze_product(test_product)
    
    print(f"\n   产品: {test_product['asin']}")
    print(f"   重量: {test_product['packageWeight']}g")
    print(f"   头程运费(自动计算): ¥{result.shipping_cost_rmb:.2f}")
    print(f"\n   {result.note}")
    
    print("\n💡 在交互式报告中填入采购成本即可自动计算:")
    print("   1. 打开 *_ALLINONE_INTERACTIVE.html 报告")
    print("   2. 在'采购成本'输入框填入价格")
    print("   3. 系统自动计算完整利润分析")


def example_4_api_usage_guide():
    """示例4: API使用指南"""
    print("\n" + "="*80)
    print("1688 API 使用指南")
    print("="*80)
    
    guide = """
【方案对比】

1️⃣ TMAPI (推荐)
   优点: 简单快速，无需企业资质
   缺点: 收费服务
   价格: 约 $0.01-0.05/次调用
   获取: https://tmapi.top
   
2️⃣ 1688官方开放平台
   优点: 免费
   缺点: 需要企业资质申请
   获取: https://open.1688.com
   
3️⃣ 手动输入
   优点: 免费，准确
   缺点: 耗时
   使用: 打开交互式报告，填入成本

【使用流程】

1. 注册TMAPI (https://tmapi.top)
   - 注册账号
   - 创建应用
   - 获取 API Token

2. 配置环境变量
   export TMAPI_TOKEN=your_token_here
   export KEEPA_KEY=your_keepa_key

3. 运行分析
   from procurement_analyzer import generate_auto_procurement_report
   report, analyses = generate_auto_procurement_report('B0XXXXXX')

【注意事项】

⚠️ 图片限制:
   - 1688以图搜图主要支持阿里系平台图片
   - Amazon图片可能需要先转换到阿里图床
   
⚠️ 匹配准确度:
   - 以图搜图的准确度取决于图片质量和数据库覆盖
   - 建议人工确认关键产品的采购价格
   
⚠️ MOQ考量:
   - 注意MOQ是否适合您的采购量
   - 系统会标注MOQ高于目标值的情况

【成本计算公式】

总COGS (USD) = [采购价(RMB) + 头程运费(RMB)] × 1.15(关税) ÷ 汇率

其中:
- 头程运费 = 重量(kg) × 12 RMB/kg
- 汇率 = 7.2 RMB/USD (可配置)
- 关税 = 15% (可配置)
"""
    
    print(guide)


if __name__ == "__main__":
    print("1688 以图搜图采购价格示例")
    print("=" * 80)
    
    # 显示菜单
    print("\n选择示例:")
    print("   1. 基本采购价格搜索")
    print("   2. 生成完整自动报告")
    print("   3. 手动输入示例")
    print("   4. API使用指南")
    print("   0. 全部运行")
    
    choice = input("\n输入选项 (0-4): ").strip()
    
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
        print("示例2需要实际的API Key，请配置后再运行")
    else:
        print("无效选项")
