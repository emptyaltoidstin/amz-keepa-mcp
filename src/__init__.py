"""
亚马逊运营精算师系统 v3.0
==========================

核心模块:
- amazon_actuary_final: 最终版精算师报告 (推荐)
- variant_auto_collector: 自动变体采集器
- keepa_metrics_collector: 163指标采集器
- market_actuary_v2: 市场可行性分析

快速开始:
    from src import auto_analyze
    report, analysis, info = auto_analyze("B0XXXYYYY")
"""

# 核心功能
from .amazon_actuary_final import (
    generate_final_report,
    generate_actuary_report_auto,
    auto_analyze,  # 便捷别名
    KeepaMetrics163,
    VariantFinancials,
    LinkPortfolioAnalyzer,
    VariantAnalysisResult,
    LinkPortfolioAnalysis,
)

from .variant_auto_collector import (
    VariantAutoCollector,
    collect_variants_for_analysis,
)

from .keepa_metrics_collector import KeepaMetricsCollector

__version__ = "3.0.0"
__all__ = [
    # 主要函数
    'generate_final_report',
    'generate_actuary_report_auto',
    'auto_analyze',
    'collect_variants_for_analysis',
    
    # 核心类
    'KeepaMetrics163',
    'VariantFinancials',
    'LinkPortfolioAnalyzer',
    'VariantAutoCollector',
    'VariantAnalysisResult',
    'LinkPortfolioAnalysis',
    'KeepaMetricsCollector',
]
