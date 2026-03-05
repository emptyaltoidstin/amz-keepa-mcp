"""
Amazon Operations Analysis Actuary Module
Actuarial-level risk assessment and profit forecast based on Keepa’s comprehensive indicators

Integrated COSMO intent analysis - Multi-Agents collaborative architecture
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json

# Import COSMO intent analyzer
from src.cosmo_intent_analyzer import (
    COSMOIntentAnalyzer, 
    COSMOReportIntegrator,
    COSMOIntentProfile
)


@dataclass
class ActuarialMetrics:
    """Actuarial indicator data class"""
    # Profitability
    gross_margin: float
    net_margin: float
    break_even_units: int
    roi_annual: float
    
    # risk indicators
    volatility_score: float
    risk_adjusted_return: float
    confidence_interval_95: Tuple[float, float]
    
    # demand forecast
    demand_forecast_30d: int
    demand_forecast_90d: int
    seasonality_factor: float
    
    # Competing risks
    market_share_risk: float
    amazon_1p_threat: float
    price_war_probability: float


class AmazonActuary:
    """
    Amazon Operations Actuary
    
    Core functions:
    1. Actuarial-level profit model (considering returns, warehousing, cash flow)
    2. Monte Carlo Risk Simulation
    3. Demand forecasting and inventory optimization
    4. Modeling competitive dynamics
    5. Risk-adjusted return calculation
    """
    
    # Category Benchmark Return Rate
    CATEGORY_RETURN_RATES = {
        'Clothing, Shoes & Jewelry': 0.12,
        'Home & Kitchen': 0.06,
        'Electronics': 0.08,
        'Beauty & Personal Care': 0.05,
        'Sports & Outdoors': 0.07,
        'Toys & Games': 0.05,
        'Baby Products': 0.10,
        'Pet Supplies': 0.04,
        'Office Products': 0.04,
        'Grocery & Gourmet Food': 0.03,
    }
    
    # Category seasonal coefficient
    CATEGORY_SEASONALITY = {
        'Toys & Games': {'Q4': 2.5, 'Q1': 0.6},
        'Clothing, Shoes & Jewelry': {'Q4': 1.8, 'Q1': 0.7},
        'Sports & Outdoors': {'Q2': 1.5, 'Q4': 0.8},
        'Home & Kitchen': {'Q4': 1.4, 'Q1': 0.9},
    }
    
    def __init__(self):
        self.simulation_results = []
    
    def analyze_from_csv(self, csv_path: str, include_cosmo: bool = True) -> Dict:
        """
        Comprehensive actuarial analysis from Keepa CSV files
        
        Multi-Agents collaborative architecture:
        1. DataExtractor: Extract 163 indicators
        2. ActuarialAnalyzer: Actuarial model analysis
        3. COSMOIntentAnalyzer: Five Points of Intention Mining
        4. ReportIntegrator: Integrate output
        
        Args:
            csv_path: CSV file path exported by Keepa Product Viewer
            include_cosmo: Whether to include COSMO intent analysis
            
        Returns:
            Actuarial Analysis Report (Contains COSMO intent analysis)
        """
        df = pd.read_csv(csv_path)
        if len(df) == 0:
            raise ValueError("CSV file is empty")
        
        # Get the first row of product data
        product_data = df.iloc[0].to_dict()
        
        # Perform comprehensive analysis
        analysis = {
            'product_identity': self._extract_identity(product_data),
            'profitability_analysis': self._calculate_profitability(product_data),
            'risk_assessment': self._assess_risks(product_data),
            'demand_forecast': self._forecast_demand(product_data),
            'competition_modeling': self._model_competition(product_data),
            'monte_carlo_simulation': self._run_monte_carlo(product_data),
            'strategic_recommendations': self._generate_recommendations(product_data),
        }
        
        # Agent 3: COSMO intent analysis (Optional)
        if include_cosmo:
            try:
                cosmo_analyzer = COSMOIntentAnalyzer()
                cosmo_profile = cosmo_analyzer.analyze(product_data)
                
                integrator = COSMOReportIntegrator()
                analysis = integrator.integrate_to_actuarial_report(cosmo_profile, analysis)
            except Exception as e:
                # COSMO analysis failure does not affect the main report
                analysis['cosmo_intent_analysis'] = {
                    'error': f'COSMO analysis failed: {str(e)}',
                    'intent_score': 0
                }
        
        return analysis
    
    def _extract_identity(self, data: Dict) -> Dict:
        """Extract product identity information"""
        return {
            'asin': data.get('ASIN', 'N/A'),
            'title': data.get('Title', 'N/A')[:100],
            'brand': data.get('Brand', 'N/A'),
            'category': data.get('Categories: Root', 'N/A'),
            'subcategory': data.get('Categories: Sub', 'N/A'),
            'tracking_since': data.get('Tracking since', 'N/A'),
            'listed_since': data.get('Listed since', 'N/A'),
            'lifecycle_stage': self._determine_lifecycle(data),
        }
    
    def _determine_lifecycle(self, data: Dict) -> str:
        """Determine product life cycle stages"""
        tracking_days = 0
        try:
            if 'Tracking since' in data:
                tracking_date = pd.to_datetime(data['Tracking since'])
                tracking_days = (datetime.now() - tracking_date).days
        except:
            pass
        
        review_count = self._safe_float(data.get('Reviews: Rating Count', 0))
        
        if tracking_days < 90 and review_count < 50:
            return 'Introduction (Introduction period)'
        elif review_count < 500 and tracking_days < 365:
            return 'Growth (growth period)'
        elif review_count > 1000:
            return 'Maturity (mature stage)'
        else:
            return 'Unknown (unknown)'
    
    def _get_effective_price(self, data: Dict) -> float:
        """
        Obtain effective prices and support multiple fallback strategies
        """
        # Try multiple price fields
        price_fields = [
            'Buy Box: Current',
            'Buy Box: Current Price', 
            'New: Current',
            'New: Current Price',
            'Amazon: Current',
            'Buy Box: 90 days avg.',
            'New: 90 days avg.',
        ]
        
        for field in price_fields:
            price = self._safe_float(data.get(field, 0))
            if price > 0:
                return price
        
        # Last alternative: Estimating from the title
        title = str(data.get('Title', '')).lower()
        if 'passport' in title or 'wallet' in title or 'wallet' in title:
            return 20.0
        return 25.0
    
    def _estimate_fba_fee(self, data: Dict, price: float) -> float:
        """Estimating FBA fees based on product attributes"""
        # Get size information
        length = self._safe_float(data.get('Package: Length (cm)'), 15)
        width = self._safe_float(data.get('Package: Width (cm)'), 10)
        height = self._safe_float(data.get('Package: Height (cm)'), 3)
        weight = self._safe_float(data.get('Package: Weight (g)'), 200)
        
        # Volumetric weight
        dimensional_weight = (length * width * height) / 5000 * 1000  # cm³ to g equiv
        billable_weight = max(weight, dimensional_weight)
        
        # FBA fee estimate (Simplified tier system)
        if billable_weight <= 100:
            return 3.22  # Small Standard
        elif billable_weight <= 500:
            return 4.50  # Large Standard (small)
        elif billable_weight <= 1000:
            return 6.10  # Large Standard (large)
        else:
            return 9.00  # Oversize
    
    def _estimate_cogs(self, data: Dict, price: float) -> float:
        """Intelligent estimation of COGS based on categories"""
        # Cost rate based on product type
        category = str(data.get('Categories: Root', '')).lower()
        title = str(data.get('Title', '')).lower()
        
        cost_rates = {
            'electronics': 0.50,
            'clothing': 0.35,
            'home': 0.30,
            'toys': 0.25,
            'sports': 0.35,
            'beauty': 0.20,
            'health': 0.25,
            'office': 0.30,
        }
        
        # Match category
        base_rate = 0.35  # Default 35%
        for cat, rate in cost_rates.items():
            if cat in category or cat in title:
                base_rate = rate
                break
        
        # leather/Genuine leather products cost more
        if 'leather' in title or 'genuine' in title or 'genuine leather' in title:
            base_rate = 0.45
        
        return price * base_rate
    
    def _estimate_storage_cost_v2(self, data: Dict) -> float:
        """
        Single piece warehousing cost estimate
        
        Calculate the monthly warehousing fee allocation for a single product
        Note: Keepa sometimes returns mm units and needs to be converted to cm
        """
        # Get dimensions - Prioritize using Item size(Usually the size of the product itself)
        # Handle possible unit issues: if numeric>50, maybe mm, required/10
        def get_dimension(field, default):
            val = self._safe_float(data.get(field), default)
            # Data verification: Passport holder cannot exceed 30cm
            if val > 50:
                val = val / 10  # Convert to cm (From mm)
            return val
        
        # Prioritize using Item size(product itself), not Package size(Outer packaging)
        length = get_dimension('Item: Length (cm)', 15)
        width = get_dimension('Item: Width (cm)', 10)
        height = get_dimension('Item: Height (cm)', 2)
        
        # Sanity check: if still too large, use default value
        if length * width * height > 5000:  # > 5000 cm³ is unreasonable for a passport holder
            length, width, height = 15, 10, 2  # Standard passport holder size
        
        # Calculate volume (cubic feet)
        volume_cbf = (length * width * height) / 28316.8  # cm³ to cubic feet
        
        # Monthly warehousing rates (Standard size: $0.87/cbf, large items: $0.56/cbf)
        is_oversize = (length > 45.7) or (width > 35.5) or (height > 20.3)  # Amazon large item standards
        storage_rate_per_cbf = 0.56 if is_oversize else 0.87
        
        # Single piece monthly storage fee = Volume × Rate
        storage_per_unit = volume_cbf * storage_rate_per_cbf
        
        # Long-term storage fee estimate (Average storage age is 90 days, extra$6.90/cbf or$0.15/unit)
        aged_inventory_surcharge = 0.15  # Long term storage fee per unit
        
        # Total warehousing cost per unit
        total_storage_per_unit = storage_per_unit + aged_inventory_surcharge
        
        return max(total_storage_per_unit, 0.02)  # lowest$0.02
    
    def _estimate_monthly_fixed_costs(self, data: Dict) -> float:
        """Estimate monthly fixed costs"""
        monthly_sales = self._safe_float(data.get('Bought in past month', 100))
        
        # basic fixed costs + Sales related costs
        base_fixed = 500  # Basic operating expenses
        scaling_cost = monthly_sales * 0.5  # per unit$0.5 floating management cost
        
        return base_fixed + scaling_cost
    
    def _calculate_profitability(self, data: Dict) -> Dict:
        """
        Actuarial Grade Profit Analysis V2
        
        Enhancements:
        - Smart price acquisition (multi-field fallback)
        - Adaptive cost estimating (category-based)
        - Smart FBA fee estimation
        """
        # Basic price data (obtained using smart)
        current_price = self._get_effective_price(data)
        
        # Determine whether it is FBA
        is_fba = str(data.get('Buy Box: Is FBA', '')).lower() in ['yes', 'true', '1']
        
        # cost structure
        fba_fee = self._safe_float(data.get('FBA Pick&Pack Fee', 0))
        
        # If there are no FBA fees, make an estimate
        if fba_fee == 0:
            fba_fee = self._estimate_fba_fee(data, current_price)
        
        referral_rate = self._safe_float(data.get('Referral Fee %', 15)) / 100
        referral_fee = current_price * referral_rate
        
        # Smart COGS Estimation
        estimated_cogs = self._estimate_cogs(data, current_price)
        
        # Return cost calculation (more precise)
        return_rate = self._estimate_return_rate(data)
        return_cost_per_unit = current_price * return_rate * 0.3  # 30%net loss
        
        # Warehousing Cost Estimation
        storage_cost = self._estimate_storage_cost_v2(data)
        
        # Advertising Cost Estimation (ACoS 15%）
        ad_cost = current_price * 0.15
        
        # total cost
        total_cost = estimated_cogs + fba_fee + referral_fee + return_cost_per_unit + storage_cost + ad_cost
        
        # Profit calculation
        gross_profit = current_price - estimated_cogs - fba_fee - referral_fee
        operating_profit = gross_profit - return_cost_per_unit - storage_cost - ad_cost
        
        gross_margin = (gross_profit / current_price * 100) if current_price > 0 else 0
        net_margin = (operating_profit / current_price * 100) if current_price > 0 else 0
        
        # Break-even analysis
        monthly_fixed = self._estimate_monthly_fixed_costs(data)
        break_even_units = int(monthly_fixed / operating_profit) if operating_profit > 0 else float('inf')
        
        # ROI calculation
        monthly_sales = self._safe_float(data.get('Bought in past month', 100))
        annual_profit = operating_profit * monthly_sales * 12
        avg_inventory_value = estimated_cogs * monthly_sales * 1.5
        roi_annual = (annual_profit / avg_inventory_value * 100) if avg_inventory_value > 0 else 0
        
        return {
            'price_analysis': {
                'current_price': current_price,
                'avg_90d_price': self._safe_float(data.get('Buy Box: 90 days avg.', 0)),
                'price_stability': data.get('Buy Box: Standard Deviation 90 days', 'N/A'),
                'flipability': data.get('Buy Box: Flipability 90 days', 'N/A'),
            },
            'cost_structure': {
                'estimated_cogs': round(estimated_cogs, 2),
                'cogs_percentage': round(estimated_cogs / current_price * 100, 1) if current_price > 0 else 0,
                'fba_fee': round(fba_fee, 2),
                'referral_fee': round(referral_fee, 2),
                'return_cost': round(return_cost_per_unit, 2),
                'storage_cost': round(storage_cost, 2),
                'ad_cost': round(ad_cost, 2),
                'total_cost': round(total_cost, 2),
                'cost_to_price_ratio': round(total_cost / current_price * 100, 1) if current_price > 0 else 0,
            },
            'profitability': {
                'gross_profit': round(gross_profit, 2),
                'operating_profit': round(operating_profit, 2),
                'gross_margin': round(gross_margin, 1),
                'net_margin': round(net_margin, 1),
                'break_even_units': break_even_units if break_even_units != float('inf') else 'N/A',
                'roi_annual': round(roi_annual, 1),
                'monthly_profit_estimate': round(operating_profit * monthly_sales, 2),
            },
            'grade': self._grade_profitability(net_margin),
        }
    
    def _assess_risks(self, data: Dict) -> Dict:
        """
        Actuarial Level Risk Assessment
        
        Assessment Dimensions:
        1. Price fluctuation risk
        2. Risk of out of stock
        3. Competition risks
        4. Risk of demand decline
        5. Policy/Compliance risk
        """
        risks = []
        risk_scores = {}
        
        # 1. Price fluctuation risk
        price_std = self._safe_float(data.get('Buy Box: Standard Deviation 90 days', 0))
        current_price = self._safe_float(data.get('Buy Box: Current', 1))
        price_cv = (price_std / current_price) if current_price > 0 else 0
        
        if price_cv > 0.15:
            risks.append({
                'type': 'price fluctuations',
                'level': 'high',
                'score': 8,
                'desc': f'price fluctuation coefficient {price_cv:.1%}, more than 15%threshold'
            })
            risk_scores['price_volatility'] = 8
        elif price_cv > 0.08:
            risks.append({
                'type': 'price fluctuations',
                'level': 'medium',
                'score': 5,
                'desc': f'price fluctuation coefficient {price_cv:.1%}, need to monitor'
            })
            risk_scores['price_volatility'] = 5
        else:
            risk_scores['price_volatility'] = 2
        
        # 2. Risk of out of stock
        oos_90d = self._safe_float(data.get('Amazon: 90 days OOS', 0))
        if oos_90d > 20:
            risks.append({
                'type': 'Out of stock risk',
                'level': 'high',
                'score': 7,
                'desc': f'90-day out-of-stock rate {oos_90d:.1f}%, supply is unstable'
            })
            risk_scores['stockout'] = 7
        elif oos_90d > 5:
            risks.append({
                'type': 'Out of stock risk',
                'level': 'medium',
                'score': 4,
                'desc': f'90-day out-of-stock rate {oos_90d:.1f}%'
            })
            risk_scores['stockout'] = 4
        else:
            risk_scores['stockout'] = 1
        
        # 3. Amazon 1P Competition Risks
        amazon_pct = self._safe_float(data.get('Buy Box: % Amazon 90 days', '0%').replace('%', ''))
        if amazon_pct > 30:
            risks.append({
                'type': 'Amazon self-operated',
                'level': 'high',
                'score': 9,
                'desc': f'Amazon’s self-operated share {amazon_pct:.1f}%, Buy Box competition is fierce'
            })
            risk_scores['amazon_1p'] = 9
        elif amazon_pct > 10:
            risks.append({
                'type': 'Amazon self-operated',
                'level': 'medium',
                'score': 6,
                'desc': f'Amazon’s self-operated share {amazon_pct:.1f}%'
            })
            risk_scores['amazon_1p'] = 6
        else:
            risk_scores['amazon_1p'] = 2
        
        # 4. Risk of demand decline
        rank_drops = self._safe_float(data.get('Sales Rank: Drops last 90 days', 0))
        if rank_drops > 40:
            risks.append({
                'type': 'Falling demand',
                'level': 'high',
                'score': 8,
                'desc': f'90 days ranking drop {rank_drops} times, demand may shrink'
            })
            risk_scores['demand_decline'] = 8
        elif rank_drops > 20:
            risks.append({
                'type': 'Falling demand',
                'level': 'medium',
                'score': 5,
                'desc': f'90 days ranking drop {rank_drops} Second-rate'
            })
            risk_scores['demand_decline'] = 5
        else:
            risk_scores['demand_decline'] = 2
        
        # 5. Return risk
        return_rate = self._estimate_return_rate(data)
        if return_rate > 0.10:
            risks.append({
                'type': 'High return rate',
                'level': 'high',
                'score': 7,
                'desc': f'Estimated return rate {return_rate:.1%}, affecting net profit'
            })
            risk_scores['returns'] = 7
        elif return_rate > 0.06:
            risks.append({
                'type': 'Return risk',
                'level': 'medium',
                'score': 4,
                'desc': f'Estimated return rate {return_rate:.1%}'
            })
            risk_scores['returns'] = 4
        else:
            risk_scores['returns'] = 2
        
        # Calculate comprehensive risk score (0-100)
        total_risk_score = sum(risk_scores.values()) / len(risk_scores) * 10
        
        return {
            'risk_items': risks,
            'risk_scores': risk_scores,
            'total_risk_score': round(total_risk_score, 1),
            'risk_grade': self._grade_risk(total_risk_score),
            'var_95': self._calculate_var(data),  # value at risk
        }
    
    def _forecast_demand(self, data: Dict) -> Dict:
        """
        demand forecasting model
        
        Based on:
        - Historical sales trends
        - seasonal factor
        - Ranking trends
        """
        current_sales = self._safe_float(data.get('Bought in past month', 0))
        sales_change_pct = self._safe_float(data.get('90 days change % monthly sold', '0%').replace('%', ''))
        
        # Get seasonal factor
        category = data.get('Categories: Root', '')
        seasonality = self.CATEGORY_SEASONALITY.get(category, {})
        current_quarter = f"Q{(datetime.now().month - 1) // 3 + 1}"
        season_factor = seasonality.get(current_quarter, 1.0)
        
        # Trend forecast
        trend_factor = 1 + (sales_change_pct / 100)
        
        # 30 day forecast
        forecast_30d = int(current_sales * trend_factor * season_factor)
        
        # 90 day forecast (Consider trend decay)
        forecast_90d = int(forecast_30d * 3 * (1 + (sales_change_pct / 200)))
        
        # confidence interval
        confidence_lower = int(forecast_30d * 0.8)
        confidence_upper = int(forecast_30d * 1.2)
        
        return {
            'current_monthly_sales': int(current_sales),
            'sales_growth_rate': f"{sales_change_pct:.1f}%",
            'seasonality_factor': season_factor,
            'forecast': {
                '30_days': forecast_30d,
                '90_days': forecast_90d,
                'confidence_interval_80': (confidence_lower, confidence_upper),
            },
            'inventory_recommendation': {
                'suggested_inventory': int(forecast_30d * 1.5),  # 1.5 months inventory
                'reorder_point': int(forecast_30d * 0.5),  # 0.5 months inventory
            }
        }
    
    def _model_competition(self, data: Dict) -> Dict:
        """
        Competitive Dynamics Modeling
        """
        # Seller concentration
        total_offers = self._safe_float(data.get('Total Offer Count', 0))
        fba_offers = self._safe_float(data.get('Count of retrieved live offers: New, FBA', 0))
        fbm_offers = self._safe_float(data.get('Count of retrieved live offers: New, FBM', 0))
        
        # Buy Box competition
        buy_box_winners = self._safe_float(data.get('Buy Box: Winner Count 90 days', 0))
        amazon_pct = self._safe_float(data.get('Buy Box: % Amazon 90 days', '0%').replace('%', ''))
        
        # market concentration (HHI approximation)
        if total_offers > 0:
            hhi_approx = 10000 / total_offers  # Simplify calculations
        else:
            hhi_approx = 0
        
        # intensity of price competition
        price_flipability = data.get('Buy Box: Flipability 90 days', 'N/A')
        
        return {
            'seller_concentration': {
                'total_offers': int(total_offers),
                'fba_offers': int(fba_offers),
                'fbm_offers': int(fbm_offers),
                'hhi_approx': int(hhi_approx),
                'concentration_level': 'High' if hhi_approx > 2500 else 'Medium' if hhi_approx > 1500 else 'Low',
            },
            'buy_box_competition': {
                'winner_count_90d': int(buy_box_winners),
                'amazon_share': f"{amazon_pct:.1f}%",
                'flipability': price_flipability,
                'stability': 'Stable' if buy_box_winners <= 3 else 'Volatile',
            },
            'price_war_probability': self._estimate_price_war_risk(data),
        }
    
    def _run_monte_carlo(self, data: Dict, iterations: int = 1000) -> Dict:
        """
        Monte Carlo Simulation V2
        
        Profit distribution simulation based on real cost structure
        """
        np.random.seed(42)
        
        # Get basic parameters (use smart acquisition)
        base_price = self._get_effective_price(data)
        base_sales = self._safe_float(data.get('Bought in past month', 100))
        
        # Calculate base cost structure
        fba_fee = self._safe_float(data.get('FBA Pick&Pack Fee', 0))
        if fba_fee == 0:
            fba_fee = self._estimate_fba_fee(data, base_price)
        
        estimated_cogs = self._estimate_cogs(data, base_price)
        referral_rate = self._safe_float(data.get('Referral Fee %', 15)) / 100
        return_rate = self._estimate_return_rate(data)
        
        # base profit margin
        base_profit_per_unit = base_price - estimated_cogs - fba_fee - (base_price * referral_rate) - (base_price * return_rate * 0.3) - (base_price * 0.15)
        
        simulations = []
        
        for _ in range(iterations):
            # Prices fluctuate randomly (±12%, normal distribution)
            price_factor = np.random.normal(1.0, 0.06)
            
            # Sales volume fluctuates randomly (±25%, normal distribution)
            sales_factor = np.random.normal(1.0, 0.125)
            
            # COGS random fluctuations (±8%)
            cogs_factor = np.random.normal(1.0, 0.04)
            
            # Calculate the scenario
            sim_price = base_price * price_factor
            sim_sales = max(0, base_sales * sales_factor)
            sim_cogs = estimated_cogs * cogs_factor
            sim_referral = sim_price * referral_rate
            sim_return = sim_price * return_rate * 0.3
            
            # monthly profit = Profit per unit × sales volume
            profit_per_unit = sim_price - sim_cogs - fba_fee - sim_referral - sim_return - (sim_price * 0.15)
            monthly_profit = profit_per_unit * sim_sales
            
            simulations.append(monthly_profit)
        
        simulations = np.array(simulations)
        
        return {
            'monthly_profit_distribution': {
                'mean': round(np.mean(simulations), 2),
                'median': round(np.median(simulations), 2),
                'std': round(np.std(simulations), 2),
                'min': round(np.min(simulations), 2),
                'max': round(np.max(simulations), 2),
                'percentile_5': round(np.percentile(simulations, 5), 2),
                'percentile_95': round(np.percentile(simulations, 95), 2),
            },
            'probability_analysis': {
                'p_profit_positive': f"{(simulations > 0).mean():.1%}",
                'p_profit_gt_1000': f"{(simulations > 1000).mean():.1%}",
                'p_loss': f"{(simulations < 0).mean():.1%}",
            },
            'risk_metrics': {
                'var_95': round(np.percentile(simulations, 5), 2),  # 95% VaR
                'cvar_95': round(simulations[simulations <= np.percentile(simulations, 5)].mean(), 2),
            }
        }
    
    def _generate_recommendations(self, data: Dict) -> List[Dict]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Recommendations based on net profit margin
        net_margin = self._calculate_profitability(data)['profitability']['net_margin']
        if net_margin < 10:
            recommendations.append({
                'priority': 'high',
                'category': 'cost optimization',
                'action': ' Negotiate supplier price reduction by 10-15%or find alternative suppliers',
                'impact': f'Can increase net profit margin to {net_margin + 5:.1f}%',
            })
        
        # Competition-based recommendations
        amazon_pct = self._safe_float(data.get('Buy Box: % Amazon 90 days', '0%').replace('%', ''))
        if amazon_pct > 20:
            recommendations.append({
                'priority': 'high',
                'category': 'competitive strategy',
                'action': 'Differentiate positioning or look for brand authorization to avoid direct competition with Amazon’s self-operated products',
                'impact': 'Increase Buy Box win rate to 30%+',
            })
        
        # Recommendations based on return rates
        return_rate = self._estimate_return_rate(data)
        if return_rate > 0.08:
            recommendations.append({
                'priority': 'medium',
                'category': 'Quality control',
                'action': 'Strengthen product quality inspection, optimize product descriptions and reduce expectations gap',
                'impact': f'Reduce return rate from {return_rate:.1%} to 5%',
            })
        
        return recommendations
    
    # Helper method
    def _safe_float(self, value, default=0.0) -> float:
        """safe conversion to float"""
        if pd.isna(value) or value is None:
            return default
        try:
            # Handling currency formats ($ 3.38)
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').replace('%', '').strip()
            return float(value)
        except:
            return default
    
    def _estimate_return_rate(self, data: Dict) -> float:
        """Estimated return rate"""
        # Using the Return Rate field in CSV
        csv_return = data.get('Return Rate', 'Low')
        if isinstance(csv_return, str):
            if 'High' in csv_return:
                return 0.12
            elif 'Medium' in csv_return:
                return 0.08
            elif 'Low' in csv_return:
                return 0.04
        
        # Category-based estimation
        category = data.get('Categories: Root', '')
        return self.CATEGORY_RETURN_RATES.get(category, 0.06)
    
    def _estimate_storage_cost(self, data: Dict) -> float:
        """Estimate monthly warehousing costs"""
        # Simplified calculation: per unit per month$0.50
        monthly_sales = self._safe_float(data.get('Bought in past month', 100))
        avg_inventory = monthly_sales * 1.5  # 1.5 months inventory
        return avg_inventory * 0.50
    
    def _calculate_var(self, data: Dict, confidence: float = 0.95) -> float:
        """Calculate VaR (VaR)"""
        # Simplify calculations
        monthly_sales = self._safe_float(data.get('Bought in past month', 100))
        price = self._safe_float(data.get('Buy Box: Current', 30))
        volatility = 0.15  # Assumption 15%Volatility
        
        z_score = 1.645 if confidence == 0.95 else 2.33  # 95% or 99%
        var = monthly_sales * price * volatility * z_score
        return round(var, 2)
    
    def _estimate_price_war_risk(self, data: Dict) -> Dict:
        """Estimate the risk of price war"""
        total_offers = self._safe_float(data.get('Total Offer Count', 0))
        price_std = self._safe_float(data.get('Buy Box: Standard Deviation 90 days', 0))
        current_price = self._safe_float(data.get('Buy Box: Current', 1))
        
        risk_factors = []
        if total_offers > 10:
            risk_factors.append('Many sellers')
        if price_std / current_price > 0.1 if current_price > 0 else False:
            risk_factors.append('Large price fluctuations')
        
        probability = min(0.8, len(risk_factors) * 0.3)
        
        return {
            'probability': f"{probability:.1%}",
            'risk_factors': risk_factors,
            'mitigation': 'Differentiation or establishing brand barriers' if risk_factors else 'maintain status quo',
        }
    
    def _grade_profitability(self, net_margin: float) -> str:
        """Profitability Rating"""
        if net_margin >= 25:
            return 'A (Excellent)'
        elif net_margin >= 15:
            return 'B (good)'
        elif net_margin >= 8:
            return 'C (pass)'
        elif net_margin >= 0:
            return 'D (danger)'
        else:
            return 'F (Loss)'
    
    def _grade_risk(self, risk_score: float) -> str:
        """risk rating"""
        if risk_score < 30:
            return 'low risk'
        elif risk_score < 50:
            return 'medium risk'
        elif risk_score < 70:
            return 'high risk'
        else:
            return 'extremely high risk'


def format_actuarial_report(analysis: Dict) -> str:
    """Formatting actuarial analysis reports as HTML"""
    # Beautiful HTML reports can be generated here
    return json.dumps(analysis, indent=2, ensure_ascii=False)
