"""
亚马逊产品分析报告生成器
============================
基于Keepa 163指标生成专业HTML分析报告
"""

import json
import math
from typing import Dict
from datetime import datetime


class ReportGenerator:
    """生成基于Keepa数据的HTML分析报告"""
    
    def generate_report(self, 
                       asin: str,
                       product_data: dict,
                       factors: dict,
                       market_report: dict) -> str:
        """
        生成完整HTML报告
        
        Args:
            asin: 产品ASIN
            product_data: 163指标数据
            factors: 6维度因子分析结果
            market_report: 市场可行性报告
            
        Returns:
            HTML字符串
        """
        # 提取关键指标
        title = product_data.get('Title', 'Unknown Product')
        brand = product_data.get('Brand', 'N/A')
        current_rank = self._safe_int(product_data.get('Sales Rank: Current', 0))
        monthly_sales = self._safe_int(product_data.get('Bought in past month', 0))
        review_rating = self._safe_float(product_data.get('Reviews: Rating', 0))
        review_count = self._safe_int(product_data.get('Reviews: Rating Count', 0))
        new_price = self._safe_float(product_data.get('New: Current', 0))
        offer_count = self._safe_int(product_data.get('New Offer Count: Current', 0))
        return_rate = product_data.get('Return Rate', 'N/A')
        
        # 计算综合评分
        factor_score = sum(f.score * f.weight for f in factors.values())
        market_score = market_report['market_feasibility']['overall_score']
        overall_score = (factor_score + market_score) / 2
        
        # 决策建议
        if overall_score >= 70:
            decision = "🟢 推荐考虑"
            decision_color = "#4ade80"
        elif overall_score >= 50:
            decision = "🟡 谨慎评估"
            decision_color = "#fbbf24"
        else:
            decision = "🔴 建议放弃"
            decision_color = "#f87171"
        
        # 生成因子卡片
        factor_cards = self._generate_factor_cards(factors)
        
        # 生成指标表格
        metrics_table = self._generate_metrics_table(product_data)
        
        # 生成维度评分HTML
        dimension_scores_html = self._generate_dimension_scores(market_report)
        
        # 当前日期
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 市场可行性颜色
        market_score_val = market_report['market_feasibility']['overall_score']
        market_color = '#4ade80' if market_score_val >= 70 else '#fbbf24' if market_score_val >= 50 else '#f87171'
        
        # 战略建议
        recommendations = market_report.get('strategic_recommendations', ['建议结合具体运营数据进行进一步评估。'])
        first_recommendation = recommendations[0] if recommendations else '建议结合具体运营数据进行进一步评估。'
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>亚马逊产品分析报告 - {asin}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        
        .header {{
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 25px 80px rgba(0,0,0,0.4);
        }}
        
        .header h1 {{
            font-size: 2.2em;
            margin-bottom: 15px;
            font-weight: 700;
        }}
        
        .meta {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 0.95em;
            opacity: 0.9;
        }}
        
        .product-title {{
            margin-top: 20px;
            font-size: 1.1em;
            line-height: 1.5;
            opacity: 0.95;
        }}
        
        .card {{
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 25px;
            backdrop-filter: blur(10px);
        }}
        
        .card-title {{
            font-size: 1.4em;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }}
        
        .metric-box {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.7;
            margin-bottom: 5px;
        }}
        
        .metric-sub {{
            font-size: 0.8em;
            opacity: 0.5;
        }}
        
        .factor-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .factor-card {{
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid;
        }}
        
        .factor-card.good {{ border-color: #22c55e; }}
        .factor-card.warning {{ border-color: #f59e0b; }}
        .factor-card.danger {{ border-color: #ef4444; }}
        
        .factor-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .factor-name {{ font-weight: 600; }}
        
        .factor-score {{
            font-size: 1.5em;
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 8px;
        }}
        
        .factor-score.good {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; }}
        .factor-score.warning {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; }}
        .factor-score.danger {{ background: rgba(239, 68, 68, 0.2); color: #f87171; }}
        
        .progress-container {{
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 10px;
        }}
        
        .progress-bar {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.6s ease;
        }}
        
        .progress-bar.good {{ background: linear-gradient(90deg, #22c55e, #4ade80); }}
        .progress-bar.warning {{ background: linear-gradient(90deg, #f59e0b, #fbbf24); }}
        .progress-bar.danger {{ background: linear-gradient(90deg, #ef4444, #f87171); }}
        
        .factor-meta {{
            display: flex;
            justify-content: space-between;
            font-size: 0.85em;
            opacity: 0.7;
        }}
        
        .metrics-section {{
            max-height: 600px;
            overflow-y: auto;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}
        
        .category-header {{
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            font-weight: 600;
            padding: 12px 15px;
            text-align: left;
        }}
        
        .metrics-table td {{
            padding: 8px 15px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }}
        
        .metrics-table td:first-child {{
            color: #94a3b8;
            width: 45%;
        }}
        
        .metrics-table td:last-child {{
            color: #e2e8f0;
            font-family: monospace;
        }}
        
        .na-value {{
            color: #64748b;
            font-style: italic;
        }}
        
        .highlight-price {{
            color: #4ade80;
            font-weight: 600;
        }}
        
        .highlight-rank {{
            color: #fbbf24;
            font-weight: 600;
        }}
        
        .decision-box {{
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(30, 41, 59, 0.8));
            border: 2px solid {decision_color};
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            margin-top: 30px;
        }}
        
        .decision-label {{
            font-size: 1.1em;
            opacity: 0.8;
            margin-bottom: 15px;
        }}
        
        .decision-value {{
            font-size: 2.5em;
            font-weight: 700;
            color: {decision_color};
            margin-bottom: 20px;
        }}
        
        .decision-reason {{
            opacity: 0.9;
            line-height: 1.8;
        }}
        
        .footer {{
            text-align: center;
            padding: 40px 20px;
            opacity: 0.6;
            font-size: 0.9em;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .card {{ animation: fadeIn 0.6s ease forwards; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 亚马逊产品分析报告</h1>
            <div class="meta">
                <span>ASIN: {asin}</span>
                <span>分析日期: {current_date}</span>
                <span>数据源: Keepa API (163指标)</span>
            </div>
            <div class="product-title">{title}</div>
        </div>
        
        <div class="card">
            <h2 class="card-title">📈 关键指标概览</h2>
            <div class="metrics-grid">
                <div class="metric-box">
                    <div class="metric-value highlight-price">${new_price:.2f}</div>
                    <div class="metric-label">当前价格</div>
                    <div class="metric-sub">New: Current</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value highlight-rank">{current_rank:,}</div>
                    <div class="metric-label">销售排名</div>
                    <div class="metric-sub">Sales Rank</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{monthly_sales}</div>
                    <div class="metric-label">月销量</div>
                    <div class="metric-sub">Bought in past month</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{review_rating:.1f}</div>
                    <div class="metric-label">评分</div>
                    <div class="metric-sub">{review_count:,} 评价</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{offer_count}</div>
                    <div class="metric-label">卖家数</div>
                    <div class="metric-sub">New Offer Count</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{return_rate}</div>
                    <div class="metric-label">退货率</div>
                    <div class="metric-sub">Return Rate</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2 class="card-title">🔍 六维深度因子分析</h2>
            <div class="factor-grid">
                {factor_cards}
            </div>
        </div>
        
        <div class="card">
            <h2 class="card-title">📊 市场可行性评估</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                {dimension_scores_html}
            </div>
            <div style="margin-top: 25px; padding: 20px; background: rgba(255,255,255,0.03); border-radius: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.1em;">综合可行性评分</span>
                    <span style="font-size: 2em; font-weight: 700; color: {market_color};">{market_score_val:.0f}/100</span>
                </div>
                <div style="margin-top: 15px; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 8px; font-size: 0.95em; line-height: 1.6;">
                    <strong>分析结论:</strong> {market_report['market_feasibility']['recommendation']}
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2 class="card-title" style="cursor: pointer;" onclick="document.getElementById('metrics-detail').style.display = document.getElementById('metrics-detail').style.display === 'none' ? 'block' : 'none';">
                📋 163指标详情 (点击展开/折叠)
            </h2>
            <div id="metrics-detail" style="display: none;">
                <p style="color: #94a3b8; margin-bottom: 20px; font-size: 0.9em;">
                    以下数据来自Keepa Product Viewer API。
                </p>
                <div class="metrics-section">
                    <table class="metrics-table">
                        {metrics_table}
                    </table>
                </div>
            </div>
        </div>
        
        <div class="decision-box">
            <div class="decision-label">基于数据分析的最终建议</div>
            <div class="decision-value">{decision}</div>
            <div class="decision-reason">
                综合评分: <strong>{overall_score:.0f}/100</strong><br>
                六维因子得分: <strong>{factor_score:.0f}/100</strong> | 
                市场可行性: <strong>{market_score:.0f}/100</strong><br><br>
                {first_recommendation}
            </div>
        </div>
        
        <div class="footer">
            <p>本报告基于 Keepa API 163个指标自动生成</p>
            <p>分析引擎: 深度因子挖掘 + 市场可行性评估</p>
            <p style="margin-top: 15px; opacity: 0.7;">© 亚马逊产品分析系统 | 数据驱动决策</p>
        </div>
    </div>
</body>
</html>'''
        
        return html
    
    def _generate_factor_cards(self, factors: dict) -> str:
        """生成因子评分卡片"""
        factor_names = {
            'operational_health': '运营健康度',
            'selection_quality': '选品质量',
            'competition_landscape': '竞争态势',
            'risk_warning': '风险预警',
            'growth_potential': '增长潜力',
            'operational_efficiency': '运营效率',
        }
        
        cards = []
        for key, name in factor_names.items():
            if key not in factors:
                continue
            f = factors[key]
            score_class = 'good' if f.score >= 70 else 'warning' if f.score >= 50 else 'danger'
            
            card = f'''
                <div class="factor-card {score_class}">
                    <div class="factor-header">
                        <span class="factor-name">{name}</span>
                        <span class="factor-score {score_class}">{f.score:.0f}</span>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar {score_class}" style="width: {f.score}%"></div>
                    </div>
                    <div class="factor-meta">
                        <span>权重 {f.weight:.0%}</span>
                        <span>置信度 {f.confidence:.0%}</span>
                    </div>
                </div>
            '''
            cards.append(card)
        
        return '\n'.join(cards)
    
    def _generate_metrics_table(self, data: dict) -> str:
        """生成指标详情表格"""
        # 分类
        categories = {
            '基本信息': [],
            '销售排名': [],
            '价格数据': [],
            '卖家竞争': [],
            '评价数据': [],
            '库存物流': [],
            '产品属性': [],
            '包装尺寸': [],
            '内容资产': [],
            '其他': [],
        }
        
        for field in data.keys():
            if field in ['ASIN', 'Locale', 'Image Count', 'Title', 'Parent Title', 'Last Update'] or field == 'Image':
                categories['基本信息'].append(field)
            elif 'Sales Rank' in field or 'Bought' in field or 'monthly sold' in field:
                categories['销售排名'].append(field)
            elif any(kw in field for kw in ['Current', 'avg.', '90 days', '180 days']) and 'Offer' not in field:
                categories['价格数据'].append(field)
            elif 'Offer' in field or 'Buy Box' in field or 'Winner' in field:
                categories['卖家竞争'].append(field)
            elif 'Review' in field or 'Rating' in field or 'Return Rate' in field:
                categories['评价数据'].append(field)
            elif 'Stock' in field or 'OOS' in field:
                categories['库存物流'].append(field)
            elif any(kw in field for kw in ['Brand', 'Manufacturer', 'Color', 'Size', 'Style']):
                categories['产品属性'].append(field)
            elif field.startswith('Package:') or field.startswith('Item:'):
                categories['包装尺寸'].append(field)
            elif 'Video' in field or 'A+' in field:
                categories['内容资产'].append(field)
            else:
                categories['其他'].append(field)
        
        rows = []
        for category, fields in categories.items():
            if not fields:
                continue
            
            rows.append(f'<tr><td colspan="2" class="category-header">📁 {category} ({len(fields)}个字段)</td></tr>')
            
            for field in sorted(fields):
                value = data.get(field)
                
                # 格式化值
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    display = '<span class="na-value">N/A</span>'
                elif isinstance(value, float):
                    display = f"{value:.2f}"
                else:
                    str_val = str(value)
                    if len(str_val) > 100:
                        str_val = str_val[:97] + '...'
                    display = str_val
                
                # 高亮
                if field in ['New: Current'] and display != 'N/A':
                    display = f'<span class="highlight-price">{display}</span>'
                elif field in ['Sales Rank: Current'] and display != 'N/A':
                    display = f'<span class="highlight-rank">{display}</span>'
                
                rows.append(f'<tr><td>{field}</td><td>{display}</td></tr>')
        
        return '\n'.join(rows)
    
    def _generate_dimension_scores(self, market_report: dict) -> str:
        """生成维度评分HTML"""
        dimension_scores = market_report['market_feasibility'].get('dimension_scores', {})
        
        if not dimension_scores:
            return '<div style="color: #94a3b8;">暂无详细维度评分</div>'
        
        # 维度名称映射
        dimension_names = {
            'demand': '需求评估',
            'competition': '竞争强度',
            'price_stability': '价格稳定性',
            'supply_chain': '供应链健康度',
        }
        
        colors = {
            'demand': '#60a5fa',
            'competition': '#f472b6',
            'price_stability': '#a78bfa',
            'supply_chain': '#34d399',
        }
        
        html_parts = []
        for key, name in dimension_names.items():
            score = dimension_scores.get(key, 0)
            color = colors.get(key, '#e2e8f0')
            
            html_parts.append(f'''
                <div style="background: rgba(255,255,255,0.03); padding: 20px; border-radius: 12px;">
                    <div style="font-size: 0.9em; opacity: 0.7; margin-bottom: 10px;">{name}</div>
                    <div style="font-size: 1.5em; font-weight: 600; color: {color};">{score:.0f}/100</div>
                </div>
            ''')
        
        return '\n'.join(html_parts)
    
    def _safe_float(self, val) -> float:
        """安全转float"""
        try:
            if val is None or (isinstance(val, float) and val != val):
                return 0.0
            return float(val)
        except:
            return 0.0
    
    def _safe_int(self, val) -> int:
        """安全转int"""
        try:
            if val is None:
                return 0
            return int(float(val))
        except:
            return 0


def generate_html_report(asin: str,
                        product_data: dict,
                        factors: dict,
                        market_report: dict,
                        output_path: str):
    """便捷函数：生成HTML报告并保存"""
    generator = ReportGenerator()
    html = generator.generate_report(asin, product_data, factors, market_report)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path
