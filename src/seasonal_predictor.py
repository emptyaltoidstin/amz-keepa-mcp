"""
季节性预测模型
基于历史数据预测产品的季节性趋势和未来销量
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from scipy.fft import fft


@dataclass
class SeasonalPattern:
    """季节性模式"""
    seasonality_strength: float  # 0-1，季节性强度
    peak_months: List[int]  # 销售高峰月份
    low_months: List[int]  # 销售低谷月份
    trend_direction: str  # 'up', 'down', 'stable'
    confidence: float  # 预测置信度


@dataclass
class SalesForecast:
    """销量预测"""
    date: datetime
    predicted_rank: int
    confidence_interval: Tuple[int, int]
    probability: float


class SeasonalPredictor:
    """
    季节性预测器
    
    功能:
    1. 检测季节性模式
    2. 预测未来销量趋势
    3. 识别最佳备货时机
    4. 风险评估
    """
    
    def __init__(self):
        self.seasonal_categories = {
            'high': ['Clothing', 'Sports', 'Toys', 'Home Decor'],
            'medium': ['Electronics', 'Kitchen', 'Beauty'],
            'low': ['Books', 'Office', 'Industrial']
        }
    
    def analyze(self, product_data: Dict, days: int = 365) -> Dict[str, Any]:
        """
        执行季节性分析
        
        Args:
            product_data: 产品数据
            days: 分析天数
        
        Returns:
            季节性分析报告
        """
        data = product_data.get('data', {})
        category = product_data.get('category', '')
        
        # 提取时间序列
        times, ranks = self._extract_series(data.get('SALES', []), days)
        times_price, prices = self._extract_series(data.get('NEW', []), days)
        
        if len(times) < 30:
            return {
                'error': 'Insufficient data for seasonal analysis (need >30 days)',
                'data_points': len(times)
            }
        
        # 创建 DataFrame
        df = pd.DataFrame({'date': times, 'rank': ranks})
        df['month'] = df['date'].dt.month
        df['dayofyear'] = df['date'].dt.dayofyear
        df['week'] = df['date'].dt.isocalendar().week
        
        # 执行各项分析
        seasonal_pattern = self._detect_seasonality(df, category)
        trend_analysis = self._analyze_trend(df)
        forecast = self._generate_forecast(df, days=90)
        inventory_plan = self._generate_inventory_plan(df, seasonal_pattern, forecast)
        
        return {
            'seasonal_pattern': seasonal_pattern,
            'trend_analysis': trend_analysis,
            'forecast': forecast,
            'inventory_plan': inventory_plan,
            'key_insights': self._generate_insights(seasonal_pattern, trend_analysis, category),
            'recommendations': self._generate_recommendations(seasonal_pattern, inventory_plan)
        }
    
    def _extract_series(self, data: np.ndarray, days: int) -> Tuple[List[datetime], List[int]]:
        """提取时间序列"""
        if data is None or len(data) == 0:
            return [], []
        
        if hasattr(data, 'tolist'):
            data = data.tolist()
        
        cutoff = datetime.now() - timedelta(days=days)
        keepa_epoch = datetime(2011, 1, 1)
        
        times = []
        values = []
        
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                keepa_time = data[i]
                value = data[i + 1]
                
                dt = keepa_epoch + timedelta(minutes=int(keepa_time))
                if dt >= cutoff and value is not None and value != -1:
                    times.append(dt)
                    values.append(int(value))
        
        return times, values
    
    def _detect_seasonality(self, df: pd.DataFrame, category: str) -> SeasonalPattern:
        """检测季节性模式"""
        
        if len(df) < 60:
            return SeasonalPattern(
                seasonality_strength=0.0,
                peak_months=[],
                low_months=[],
                trend_direction='unknown',
                confidence=0.0
            )
        
        # 按月聚合
        monthly_avg = df.groupby('month')['rank'].mean()
        
        # 计算季节性强度（变异系数）
        cv = monthly_avg.std() / monthly_avg.mean() if monthly_avg.mean() > 0 else 0
        seasonality_strength = min(cv * 2, 1.0)  # 归一化到 0-1
        
        # 识别高低峰月份
        # 注意：BSR 越小销量越高，所以排名低的月份是高峰
        sorted_months = monthly_avg.sort_values()
        peak_months = sorted_months.head(3).index.tolist()
        low_months = sorted_months.tail(3).index.tolist()
        
        # 基于类目的季节性调整
        category_lower = category.lower()
        expected_seasonality = 'low'
        for level, cats in self.seasonal_categories.items():
            if any(cat.lower() in category_lower for cat in cats):
                expected_seasonality = level
                break
        
        # 趋势方向
        if len(df) > 60:
            first_half = df.head(len(df)//2)['rank'].mean()
            second_half = df.tail(len(df)//2)['rank'].mean()
            
            if second_half < first_half * 0.9:
                trend_direction = 'up'  # 排名上升 = 销量上升
            elif second_half > first_half * 1.1:
                trend_direction = 'down'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'unknown'
        
        return SeasonalPattern(
            seasonality_strength=seasonality_strength,
            peak_months=peak_months,
            low_months=low_months,
            trend_direction=trend_direction,
            confidence=min(len(df) / 365, 1.0)  # 数据越多置信度越高
        )
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """分析趋势"""
        if len(df) < 30:
            return {'error': 'Insufficient data'}
        
        # 线性回归
        x = np.arange(len(df))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, df['rank'])
        
        # 计算移动平均
        df['ma7'] = df['rank'].rolling(window=7, min_periods=1).mean()
        df['ma30'] = df['rank'].rolling(window=30, min_periods=1).mean()
        
        # 波动性
        volatility = df['rank'].std() / df['rank'].mean() if df['rank'].mean() > 0 else 0
        
        return {
            'slope': slope,
            'trend_direction': 'improving' if slope < 0 else 'declining' if slope > 0 else 'stable',
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'volatility': volatility,
            'ma7_current': df['ma7'].iloc[-1] if len(df) > 0 else None,
            'ma30_current': df['ma30'].iloc[-1] if len(df) > 0 else None,
            'trend_strength': 'strong' if abs(r_value) > 0.7 else 'moderate' if abs(r_value) > 0.4 else 'weak'
        }
    
    def _generate_forecast(self, df: pd.DataFrame, days: int = 90) -> List[SalesForecast]:
        """生成销量预测"""
        
        if len(df) < 30:
            return []
        
        forecasts = []
        last_date = df['date'].max()
        last_rank = df['rank'].iloc[-1]
        
        # 简单线性外推 + 季节性调整
        x = np.arange(len(df))
        slope, intercept, _, _, _ = stats.linregress(x, df['rank'])
        
        # 计算标准差用于置信区间
        residuals = df['rank'] - (slope * x + intercept)
        std_residuals = residuals.std()
        
        for i in range(1, days + 1):
            future_date = last_date + timedelta(days=i)
            
            # 线性预测
            predicted = last_rank + slope * i
            
            # 季节性调整
            month = future_date.month
            monthly_effect = self._get_monthly_effect(df, month)
            predicted *= (1 + monthly_effect)
            
            # 确保合理范围
            predicted = max(1, int(predicted))
            
            # 置信区间 (95%)
            margin = 1.96 * std_residuals * np.sqrt(1 + i/len(df))  # 随时间扩大
            lower = max(1, int(predicted - margin))
            upper = int(predicted + margin)
            
            forecasts.append(SalesForecast(
                date=future_date,
                predicted_rank=predicted,
                confidence_interval=(lower, upper),
                probability=self._calculate_probability(predicted, lower, upper)
            ))
        
        return forecasts
    
    def _get_monthly_effect(self, df: pd.DataFrame, month: int) -> float:
        """获取月份效应"""
        if len(df) < 60:
            return 0.0
        
        monthly_avg = df.groupby('month')['rank'].mean()
        overall_avg = df['rank'].mean()
        
        if month in monthly_avg.index and overall_avg > 0:
            effect = (monthly_avg[month] - overall_avg) / overall_avg
            return -effect  # BSR 越小销量越高，所以取反
        return 0.0
    
    def _calculate_probability(self, predicted: int, lower: int, upper: int) -> float:
        """计算预测概率"""
        interval_width = upper - lower
        if interval_width == 0:
            return 1.0
        return max(0.3, 1 - (interval_width / predicted) * 0.5)
    
    def _generate_inventory_plan(self, df: pd.DataFrame, 
                                  seasonal: SeasonalPattern, 
                                  forecast: List[SalesForecast]) -> Dict:
        """生成备货计划"""
        
        if not forecast:
            return {'error': 'No forecast available'}
        
        current_month = datetime.now().month
        
        # 识别即将到来的高峰/低谷
        upcoming_peak = None
        upcoming_low = None
        
        for f in forecast:
            if f.date.month in seasonal.peak_months and upcoming_peak is None:
                upcoming_peak = f
            if f.date.month in seasonal.low_months and upcoming_low is None:
                upcoming_low = f
        
        # 备货建议
        recommendations = []
        
        if upcoming_peak:
            days_to_peak = (upcoming_peak.date - datetime.now()).days
            recommendations.append({
                'action': 'Stock up for peak season',
                'timing': f'{days_to_peak} days before peak',
                'quantity_suggestion': 'Increase inventory by 50-100%',
                'reason': f'Peak season in month {upcoming_peak.date.month}'
            })
        
        if upcoming_low:
            days_to_low = (upcoming_low.date - datetime.now()).days
            recommendations.append({
                'action': 'Reduce inventory',
                'timing': f'{days_to_low} days before low season',
                'quantity_suggestion': 'Reduce inventory by 30%',
                'reason': f'Low season in month {upcoming_low.date.month}'
            })
        
        # 计算推荐库存量
        if forecast:
            avg_predicted_rank = np.mean([f.predicted_rank for f in forecast[:30]])
            
            # 根据排名估算日销量
            if avg_predicted_rank < 1000:
                daily_sales = 50
            elif avg_predicted_rank < 5000:
                daily_sales = 20
            elif avg_predicted_rank < 10000:
                daily_sales = 10
            elif avg_predicted_rank < 50000:
                daily_sales = 5
            else:
                daily_sales = 2
            
            recommended_stock = daily_sales * 30  # 30天库存
            
            if seasonal.seasonality_strength > 0.3 and upcoming_peak:
                recommended_stock = int(recommended_stock * 1.5)  # 季节性高峰增加50%
        else:
            recommended_stock = 300  # 默认值
        
        return {
            'recommended_stock_level': recommended_stock,
            'reorder_point': int(recommended_stock * 0.3),
            'max_stock': int(recommended_stock * 1.5),
            'seasonal_adjustments': recommendations,
            'lead_time_consideration': 'Place orders 4-6 weeks before predicted peaks'
        }
    
    def _generate_insights(self, seasonal: SeasonalPattern, trend: Dict, category: str) -> List[str]:
        """生成洞察"""
        insights = []
        
        # 季节性洞察
        if seasonal.seasonality_strength > 0.4:
            peak_names = self._month_names(seasonal.peak_months)
            low_names = self._month_names(seasonal.low_months)
            insights.append(f"📈 **强季节性产品** - 销售高峰: {peak_names}, 低谷: {low_names}")
        elif seasonal.seasonality_strength > 0.2:
            insights.append(f"📊 **中等季节性** - 存在一定的季节波动")
        else:
            insights.append(f"📉 **低季节性** - 全年销售相对稳定")
        
        # 趋势洞察
        trend_dir = trend.get('trend_direction', 'stable')
        if trend_dir == 'improving':
            insights.append(f"🚀 **上升趋势** - 产品销量正在增长，市场热度提升")
        elif trend_dir == 'declining':
            insights.append(f"⚠️ **下降趋势** - 产品销量下滑，可能面临竞争或市场饱和")
        
        # 类目洞察
        category_lower = category.lower()
        for level, cats in self.seasonal_categories.items():
            if any(cat.lower() in category_lower for cat in cats):
                if level == 'high':
                    insights.append(f"🎯 **高季节性类目** - 需要精细的季节性库存管理")
                break
        
        return insights
    
    def _generate_recommendations(self, seasonal: SeasonalPattern, inventory: Dict) -> List[Dict]:
        """生成建议"""
        recommendations = []
        
        if seasonal.seasonality_strength > 0.3:
            recommendations.append({
                'priority': 'High',
                'action': 'Implement seasonal pricing strategy',
                'details': f'Increase prices {self._month_names(seasonal.peak_months)}, decrease during {self._month_names(seasonal.low_months)}'
            })
        
        if inventory.get('seasonal_adjustments'):
            for adj in inventory['seasonal_adjustments']:
                recommendations.append({
                    'priority': 'High',
                    'action': adj['action'],
                    'details': f"{adj['reason']}. {adj['quantity_suggestion']}"
                })
        
        recommendations.append({
            'priority': 'Medium',
            'action': 'Maintain safety stock',
            'details': f"Recommended level: {inventory.get('recommended_stock_level', 300)} units. Reorder at {inventory.get('reorder_point', 100)} units."
        })
        
        return recommendations
    
    def _month_names(self, months: List[int]) -> str:
        """月份数字转名称"""
        names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return ', '.join([names[m-1] for m in months])
    
    def generate_seasonal_report(self, analysis: Dict, asin: str) -> str:
        """生成季节性分析报告"""
        
        seasonal = analysis.get('seasonal_pattern')
        trend = analysis.get('trend_analysis', {})
        forecast = analysis.get('forecast', [])
        inventory = analysis.get('inventory_plan', {})
        insights = analysis.get('key_insights', [])
        recommendations = analysis.get('recommendations', [])
        
        if 'error' in analysis:
            return f"❌ 季节性分析失败: {analysis['error']}"
        
        report = f"""# 📅 季节性分析与预测报告

**ASIN**: {asin}  
**分析周期**: 过去365天  
**预测周期**: 未来90天

---

## 🌊 季节性模式

### 季节性强度
```
{'█' * int(seasonal.seasonality_strength * 20)}{'░' * (20 - int(seasonal.seasonality_strength * 20))} {seasonal.seasonality_strength:.0%}
```

**评估**: {'强季节性 - 需要精细的季节性管理' if seasonal.seasonality_strength > 0.4 else '中等季节性 - 存在一定的波动' if seasonal.seasonality_strength > 0.2 else '低季节性 - 全年相对稳定'}

### 销售日历

| 季度 | 月份 | 销售预期 | 建议动作 |
|------|------|----------|----------|
| **高峰** | {self._month_names(seasonal.peak_months)} | 🔥 销量增长 30-50% | 提前备货，适度提价 |
| **平季** | 其他月份 | ➡️ 正常销量 | 维持标准库存 |
| **低谷** | {self._month_names(seasonal.low_months)} | 📉 销量下降 20-30% | 减少库存，促销活动 |

---

## 📈 趋势分析

| 指标 | 数值 | 解读 |
|------|------|------|
| 趋势方向 | {trend.get('trend_direction', 'Unknown')} | {'销量上升' if trend.get('trend_direction') == 'improving' else '销量下降' if trend.get('trend_direction') == 'declining' else '相对稳定'} |
| 趋势强度 | {trend.get('trend_strength', 'Unknown')} | R² = {trend.get('r_squared', 0):.2f} |
| 波动性 | {trend.get('volatility', 0):.1%} | {'高波动' if trend.get('volatility', 0) > 0.3 else '中等波动' if trend.get('volatility', 0) > 0.15 else '低波动'} |

---

## 🔮 未来90天预测

### 销量预测

"""
        
        # 添加预测表格
        if forecast:
            report += "| 时间段 | 预测 BSR | 置信区间 | 概率 |\n"
            report += "|--------|----------|----------|------|\n"
            
            # 按周汇总
            weeks = {}
            for f in forecast:
                week_key = f.date.strftime('%Y-W%W')
                if week_key not in weeks:
                    weeks[week_key] = []
                weeks[week_key].append(f)
            
            for week, forecasts in list(weeks.items())[:12]:  # 显示前12周
                avg_rank = int(np.mean([f.predicted_rank for f in forecasts]))
                avg_lower = int(np.mean([f.confidence_interval[0] for f in forecasts]))
                avg_upper = int(np.mean([f.confidence_interval[1] for f in forecasts]))
                avg_prob = np.mean([f.probability for f in forecasts])
                
                trend_icon = '📈' if forecasts[-1].predicted_rank < forecasts[0].predicted_rank else '📉' if forecasts[-1].predicted_rank > forecasts[0].predicted_rank else '➡️'
                report += f"| {week} | #{avg_rank:,} | #{avg_lower:,} - #{avg_upper:,} | {avg_prob:.0%} {trend_icon} |\n"
        
        report += f"""

---

## 📦 备货计划

### 库存建议

| 指标 | 建议值 | 说明 |
|------|--------|------|
| 标准库存 | {inventory.get('recommended_stock_level', 300)} 件 | 基于预测日均销量 |
| 补货点 | {inventory.get('reorder_point', 100)} 件 | 库存预警线 |
| 最大库存 | {inventory.get('max_stock', 450)} 件 | 防止积压 |

### 季节性调整

"""
        
        if inventory.get('seasonal_adjustments'):
            for adj in inventory['seasonal_adjustments']:
                report += f"""
**{adj['action']}**
- 时机: {adj['timing']}
- 调整: {adj['quantity_suggestion']}
- 原因: {adj['reason']}
"""
        else:
            report += "暂无特殊的季节性调整建议\n"
        
        report += f"""

---

## 💡 关键洞察

"""
        
        for insight in insights:
            report += f"- {insight}\n"
        
        report += f"""

---

## 🎯 行动建议

"""
        
        for rec in recommendations:
            priority_emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(rec.get('priority', ''), '⚪')
            report += f"""
{priority_emoji} **{rec.get('priority', 'Medium')} 优先级**

**行动**: {rec.get('action')}

**详情**: {rec.get('details')}

"""
        
        report += """
---

**免责声明**: 预测基于历史数据分析，实际结果可能因市场变化而有所不同。建议结合实际情况灵活调整。
"""
        
        return report
