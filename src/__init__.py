"""
Amazon Operations Actuary System v3.0
==========================

core module:
- amazon_actuary_final: Final Actuary’s Report (recommend)
- variant_auto_collector: Automatic variant collector
- keepa_metrics_collector: 163 indicator collector
- market_actuary_v2: Market feasibility analysis

quick start:
    from src import auto_analyze
    report, analysis, info = auto_analyze("B0XXXYYYY")
"""

# Core functions
from .amazon_actuary_final import (
    generate_final_report,
    generate_actuary_report_auto,
    auto_analyze,  # Convenience alias
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
    # main function
    'generate_final_report',
    'generate_actuary_report_auto',
    'auto_analyze',
    'collect_variants_for_analysis',
    
    # core class
    'KeepaMetrics163',
    'VariantFinancials',
    'LinkPortfolioAnalyzer',
    'VariantAutoCollector',
    'VariantAnalysisResult',
    'LinkPortfolioAnalysis',
    'KeepaMetricsCollector',
]
