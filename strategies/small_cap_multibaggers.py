"""
Small Cap Multibaggers Strategy - Quality small caps with growth potential

Filter Criteria:
- Market Cap between 10M - 1,000M
- Total Revenues, CAGR (YoY TTM) greater than 15%  
- Gross Profit Margin % (LTM) between 30% - 100%
- Net Debt / EBITDA (calculated) between 0x - 2x
- FCF (LTM) greater than 0
"""
from tradingview_screener import Query, col
from typing import Dict, Any, List
import pandas as pd
from .base import BaseStrategy


class SmallCapMultibaggersStrategy(BaseStrategy):
    """Small Cap Multibaggers - Quality small caps with growth potential."""
    
    name = "Small Cap Multibaggers"
    description = "Small caps ($10M-$1B) with strong fundamentals and growth"
    
    select_columns = [
        'name', 'description', 'close', 'change', 
        'market_cap_basic', 'average_volume_10d_calc',
        'gross_margin', 'free_cash_flow', 'net_debt', 'ebitda',
        'total_revenue_yoy_growth_ttm',
        'EMA8', 'EMA21', 'EMA34', 'EMA55', 'EMA89'
    ]
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'mcap_min_m': 10.0,
            'mcap_max_m': 1000.0,
            'gross_margin_min': 30.0,
            'gross_margin_max': 100.0,
            'revenue_growth_min': 15.0
        }
    
    def get_param_config(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'mcap_range', 'label': 'Market Cap ($M)', 'type': 'range',
             'fields': [('mcap_min_m', 'Min'), ('mcap_max_m', 'Max')]},
            {'name': 'gross_margin', 'label': 'Gross Margin (%)', 'type': 'range',
             'fields': [('gross_margin_min', 'Min'), ('gross_margin_max', 'Max')]},
            {'name': 'revenue_growth', 'label': 'Revenue Growth YoY (%)', 'type': 'min',
             'fields': [('revenue_growth_min', 'Min')]}
        ]
    
    def build_query(self, params: Dict[str, Any]) -> Query:
        mcap_min = params.get('mcap_min_m', 10) * 1_000_000
        mcap_max = params.get('mcap_max_m', 1000) * 1_000_000
        gross_margin_min = params.get('gross_margin_min', 30)
        gross_margin_max = params.get('gross_margin_max', 100)
        revenue_growth_min = params.get('revenue_growth_min', 15)
        
        query = (
            Query()
            .select(*self.select_columns)
            .where(
                # General Filters
                col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
                col('close') > 1.0,  # Avoid penny stocks
                col('average_volume_10d_calc') > 100_000,
                
                # Small Cap Universe: $10M - $1B
                col('market_cap_basic').between(mcap_min, mcap_max),
                
                # Quality Filters
                col('gross_margin').between(gross_margin_min, gross_margin_max),
                col('free_cash_flow') > 0,  # Positive FCF
                col('ebitda') > 0,  # Positive EBITDA for leverage calc
                
                # Growth Filter - Revenue YoY Growth
                col('total_revenue_yoy_growth_ttm') >= revenue_growth_min,
            )
            .limit(500)
        )
        return query
    
    def post_process(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        if df.empty:
            return df
        
        # Calculate Net Debt / EBITDA ratio and filter
        if 'net_debt' in df.columns and 'ebitda' in df.columns:
            df['net_debt_ebitda'] = df['net_debt'] / df['ebitda'].replace(0, float('nan'))
            # Filter: Net Debt / EBITDA between 0 and 2
            df = df[(df['net_debt_ebitda'] >= 0) & (df['net_debt_ebitda'] <= 2)]
        
        df = df.rename(columns={'total_revenue_yoy_growth_ttm': 'revenue_growth'})
        df = df.fillna(0.0)
        return df
    
    def get_fixed_criteria(self) -> list:
        """Return list of fixed/locked strategy criteria for display."""
        return [
            "📊 US Exchanges Only (NYSE, NASDAQ, AMEX)",
            "💰 Volume ≥ 100K daily",
            "🚫 No Penny Stocks: Price > $1",
            "💵 Positive Free Cash Flow",
            "📈 Positive EBITDA",
            "🏦 Net Debt/EBITDA: 0x - 2x (low leverage)"
        ]
