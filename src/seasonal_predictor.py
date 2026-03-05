"""
Seasonal Forecasting Model
Predict seasonal trends and future sales of products based on historical data
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
    """seasonal pattern"""
    seasonality_strength: float  # 0-1. Seasonal intensity
    peak_months: List[int]  # Peak sales months
    low_months: List[int]  # Low sales months
    trend_direction: str  # 'up', 'down', 'stable'
    confidence: float  # Prediction confidence


@dataclass
class SalesForecast:
    """sales forecast"""
    date: datetime
    predicted_rank: int
    confidence_interval: Tuple[int, int]
    probability: float


class SeasonalPredictor:
    """
    seasonal predictor
    
    Function:
    1. Detect seasonal patterns
    2. Predict future sales trends
    3. Identify the best time to stock up
    4. Risk assessment
    """
    
    def __init__(self):
        self.seasonal_categories = {
            'high': ['Clothing', 'Sports', 'Toys', 'Home Decor'],
            'medium': ['Electronics', 'Kitchen', 'Beauty'],
            'low': ['Books', 'Office', 'Industrial']
        }
    
    def analyze(self, product_data: Dict, days: int = 365) -> Dict[str, Any]:
        """
        Perform seasonal analysis
        
        Args:
            product_data: product data
            days: Analysis days
        
        Returns:
            Seasonal Analysis Report
        """
        data = product_data.get('data', {})
        category = product_data.get('category', '')
        
        # Extract time series
        times, ranks = self._extract_series(data.get('SALES', []), days)
        times_price, prices = self._extract_series(data.get('NEW', []), days)
        
        if len(times) < 30:
            return {
                'error': 'Insufficient data for seasonal analysis (need >30 days)',
                'data_points': len(times)
            }
        
        # Create DataFrame
        df = pd.DataFrame({'date': times, 'rank': ranks})
        df['month'] = df['date'].dt.month
        df['dayofyear'] = df['date'].dt.dayofyear
        df['week'] = df['date'].dt.isocalendar().week
        
        # Perform analyzes
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
        """Extract time series"""
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
        """Detect seasonal patterns"""
        
        if len(df) < 60:
            return SeasonalPattern(
                seasonality_strength=0.0,
                peak_months=[],
                low_months=[],
                trend_direction='unknown',
                confidence=0.0
            )
        
        # Aggregate by month
        monthly_avg = df.groupby('month')['rank'].mean()
        
        # Calculate seasonal intensity (coefficient of variation)
        cv = monthly_avg.std() / monthly_avg.mean() if monthly_avg.mean() > 0 else 0
        seasonality_strength = min(cv * 2, 1.0)  # normalized to 0-1
        
        # Identify high and low peak months
        # Note: The smaller the BSR, the higher the sales volume, so the month with the lowest ranking is the peak
        sorted_months = monthly_avg.sort_values()
        peak_months = sorted_months.head(3).index.tolist()
        low_months = sorted_months.tail(3).index.tolist()
        
        # Category-based seasonal adjustment
        category_lower = category.lower()
        expected_seasonality = 'low'
        for level, cats in self.seasonal_categories.items():
            if any(cat.lower() in category_lower for cat in cats):
                expected_seasonality = level
                break
        
        # trend direction
        if len(df) > 60:
            first_half = df.head(len(df)//2)['rank'].mean()
            second_half = df.tail(len(df)//2)['rank'].mean()
            
            if second_half < first_half * 0.9:
                trend_direction = 'up'  # Ranking up = sales increase
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
            confidence=min(len(df) / 365, 1.0)  # The more data, the higher the confidence
        )
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze trends"""
        if len(df) < 30:
            return {'error': 'Insufficient data'}
        
        # linear regression
        x = np.arange(len(df))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, df['rank'])
        
        # Calculate moving average
        df['ma7'] = df['rank'].rolling(window=7, min_periods=1).mean()
        df['ma30'] = df['rank'].rolling(window=30, min_periods=1).mean()
        
        # Volatility
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
        """Generate sales forecast"""
        
        if len(df) < 30:
            return []
        
        forecasts = []
        last_date = df['date'].max()
        last_rank = df['rank'].iloc[-1]
        
        # simple linear extrapolation + Seasonal adjustment
        x = np.arange(len(df))
        slope, intercept, _, _, _ = stats.linregress(x, df['rank'])
        
        # Calculate standard deviation for confidence interval
        residuals = df['rank'] - (slope * x + intercept)
        std_residuals = residuals.std()
        
        for i in range(1, days + 1):
            future_date = last_date + timedelta(days=i)
            
            # linear prediction
            predicted = last_rank + slope * i
            
            # Seasonal adjustment
            month = future_date.month
            monthly_effect = self._get_monthly_effect(df, month)
            predicted *= (1 + monthly_effect)
            
            # Ensure reasonable range
            predicted = max(1, int(predicted))
            
            # confidence interval (95%)
            margin = 1.96 * std_residuals * np.sqrt(1 + i/len(df))  # Expand over time
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
        """Get month effect"""
        if len(df) < 60:
            return 0.0
        
        monthly_avg = df.groupby('month')['rank'].mean()
        overall_avg = df['rank'].mean()
        
        if month in monthly_avg.index and overall_avg > 0:
            effect = (monthly_avg[month] - overall_avg) / overall_avg
            return -effect  # The smaller the BSR, the higher the sales volume, so the inverse
        return 0.0
    
    def _calculate_probability(self, predicted: int, lower: int, upper: int) -> float:
        """Calculate predicted probability"""
        interval_width = upper - lower
        if interval_width == 0:
            return 1.0
        return max(0.3, 1 - (interval_width / predicted) * 0.5)
    
    def _generate_inventory_plan(self, df: pd.DataFrame, 
                                  seasonal: SeasonalPattern, 
                                  forecast: List[SalesForecast]) -> Dict:
        """Generate stocking plan"""
        
        if not forecast:
            return {'error': 'No forecast available'}
        
        current_month = datetime.now().month
        
        # Identify upcoming peaks/low point
        upcoming_peak = None
        upcoming_low = None
        
        for f in forecast:
            if f.date.month in seasonal.peak_months and upcoming_peak is None:
                upcoming_peak = f
            if f.date.month in seasonal.low_months and upcoming_low is None:
                upcoming_low = f
        
        # Stocking suggestions
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
        
        # Calculate recommended inventory levels
        if forecast:
            avg_predicted_rank = np.mean([f.predicted_rank for f in forecast[:30]])
            
            # Estimate daily sales based on ranking
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
            
            recommended_stock = daily_sales * 30  # 30 days in stock
            
            if seasonal.seasonality_strength > 0.3 and upcoming_peak:
                recommended_stock = int(recommended_stock * 1.5)  # Seasonal peak increases by 50%
        else:
            recommended_stock = 300  # Default value
        
        return {
            'recommended_stock_level': recommended_stock,
            'reorder_point': int(recommended_stock * 0.3),
            'max_stock': int(recommended_stock * 1.5),
            'seasonal_adjustments': recommendations,
            'lead_time_consideration': 'Place orders 4-6 weeks before predicted peaks'
        }
    
    def _generate_insights(self, seasonal: SeasonalPattern, trend: Dict, category: str) -> List[str]:
        """generate insights"""
        insights = []
        
        # Seasonal insights
        if seasonal.seasonality_strength > 0.4:
            peak_names = self._month_names(seasonal.peak_months)
            low_names = self._month_names(seasonal.low_months)
            insights.append(f"📈 **Strong seasonal products** - sales peak: {peak_names}, low point: {low_names}")
        elif seasonal.seasonality_strength > 0.2:
            insights.append(f"📊 **Moderately seasonal** - There are certain seasonal fluctuations")
        else:
            insights.append(f"📉 **low seasonality** - Sales are relatively stable throughout the year")
        
        # Trend Insights
        trend_dir = trend.get('trend_direction', 'stable')
        if trend_dir == 'improving':
            insights.append(f"🚀 **uptrend** - Product sales are growing and market popularity is increasing")
        elif trend_dir == 'declining':
            insights.append(f"⚠️ **downtrend** - Product sales decline and may face competition or market saturation")
        
        # Category Insights
        category_lower = category.lower()
        for level, cats in self.seasonal_categories.items():
            if any(cat.lower() in category_lower for cat in cats):
                if level == 'high':
                    insights.append(f"🎯 **Highly seasonal categories** - Requires sophisticated seasonal inventory management")
                break
        
        return insights
    
    def _generate_recommendations(self, seasonal: SeasonalPattern, inventory: Dict) -> List[Dict]:
        """Generate suggestions"""
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
        """Month number to name"""
        names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return ', '.join([names[m-1] for m in months])
    
    def generate_seasonal_report(self, analysis: Dict, asin: str) -> str:
        """Generate seasonal analysis report"""
        
        seasonal = analysis.get('seasonal_pattern')
        trend = analysis.get('trend_analysis', {})
        forecast = analysis.get('forecast', [])
        inventory = analysis.get('inventory_plan', {})
        insights = analysis.get('key_insights', [])
        recommendations = analysis.get('recommendations', [])
        
        if 'error' in analysis:
            return f"❌ Seasonal analysis failed: {analysis['error']}"
        
        report = f"""# 📅 Seasonal analysis and forecast report

**ASIN**: {asin}  
**Analysis cycle**: past 365 days  
**Forecast period**: next 90 days

---

## 🌊 Seasonal mode

### seasonal intensity
```
{'█' * int(seasonal.seasonality_strength * 20)}{'░' * (20 - int(seasonal.seasonality_strength * 20))} {seasonal.seasonality_strength:.0%}
```

**Assessment**: {'strong seasonality - Requires careful seasonal management' if seasonal.seasonality_strength > 0.4 else 'Moderately seasonal - There is some fluctuation' if seasonal.seasonality_strength > 0.2 else 'low seasonality - Relatively stable throughout the year'}

### sales calendar

| quarter | month | sales expectations | Recommended action |
|------|------|----------|----------|
| **peak** | {self._month_names(seasonal.peak_months)} | 🔥 Sales increased by 30-50% | Stock up in advance and raise prices appropriately |
| **shoulder season** | other months | ➡️Normal sales | Maintain standard inventory |
| **low point** | {self._month_names(seasonal.low_months)} | 📉 Sales dropped by 20-30% | Inventory reduction, promotions |

---

## 📈 Trend analysis

| indicator | numerical value | Interpretation |
|------|------|------|
| trend direction | {trend.get('trend_direction', 'Unknown')} | {'sales increase' if trend.get('trend_direction') == 'improving' else 'sales drop' if trend.get('trend_direction') == 'declining' else 'relatively stable'} |
| trend strength | {trend.get('trend_strength', 'Unknown')} | R² = {trend.get('r_squared', 0):.2f} |
| Volatility | {trend.get('volatility', 0):.1%} | {'High volatility' if trend.get('volatility', 0) > 0.3 else 'medium volatility' if trend.get('volatility', 0) > 0.15 else 'low volatility'} |

---

## 🔮 Forecast for the next 90 days

### sales forecast

"""
        
        # Add forecast table
        if forecast:
            report += "| time period | Predict BSR | confidence interval | Probability |\n"
            report += "|--------|----------|----------|------|\n"
            
            # Summary by week
            weeks = {}
            for f in forecast:
                week_key = f.date.strftime('%Y-W%W')
                if week_key not in weeks:
                    weeks[week_key] = []
                weeks[week_key].append(f)
            
            for week, forecasts in list(weeks.items())[:12]:  # Showing the previous 12 weeks
                avg_rank = int(np.mean([f.predicted_rank for f in forecasts]))
                avg_lower = int(np.mean([f.confidence_interval[0] for f in forecasts]))
                avg_upper = int(np.mean([f.confidence_interval[1] for f in forecasts]))
                avg_prob = np.mean([f.probability for f in forecasts])
                
                trend_icon = '📈' if forecasts[-1].predicted_rank < forecasts[0].predicted_rank else '📉' if forecasts[-1].predicted_rank > forecasts[0].predicted_rank else '➡️'
                report += f"| {week} | #{avg_rank:,} | #{avg_lower:,} - #{avg_upper:,} | {avg_prob:.0%} {trend_icon} |\n"
        
        report += f"""

---

## 📦 Stocking plan

### Inventory recommendations

| indicator | Recommended value | Description |
|------|--------|------|
| Standard stock | {inventory.get('recommended_stock_level', 300)} pieces | Based on forecasted average daily sales |
| replenishment point | {inventory.get('reorder_point', 100)} pieces | Inventory warning line |
| Maximum inventory | {inventory.get('max_stock', 450)} pieces | Prevent backlog |

### Seasonal adjustment

"""
        
        if inventory.get('seasonal_adjustments'):
            for adj in inventory['seasonal_adjustments']:
                report += f"""
**{adj['action']}**
- timing: {adj['timing']}
- adjust: {adj['quantity_suggestion']}
- Reason: {adj['reason']}
"""
        else:
            report += "No special seasonal adjustment recommendations are currently available\n"
        
        report += f"""

---

## 💡 Key Insights

"""
        
        for insight in insights:
            report += f"- {insight}\n"
        
        report += f"""

---

## 🎯 Action suggestions

"""
        
        for rec in recommendations:
            priority_emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(rec.get('priority', ''), '⚪')
            report += f"""
{priority_emoji} **{rec.get('priority', 'Medium')} priority**

**action**: {rec.get('action')}

**Details**: {rec.get('details')}

"""
        
        report += """
---

**Disclaimer**: Forecasts are based on historical data analysis and actual results may vary due to market changes. It is recommended to make flexible adjustments based on the actual situation.
"""
        
        return report
