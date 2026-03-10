"""
Momentum with Pullback Strategy - TAO Multi-Timeframe EMA Stack
"""
from tradingview_screener import Query, col
from typing import Dict, Any, List
import pandas as pd
from .base import BaseStrategy


class MomentumStrategy(BaseStrategy):
    """TAO Multi-Timeframe EMA Stack with Pullback focus."""
    
    name = "Momentum with Pullback"
    description = "EMA stack alignment with ADX pullback (default <40)"
    
    select_columns = [
        'name', 'description', 'close', 'change', 'sector',
        'ADX', 'ATR', 'ATR|1W', 'average_volume_10d_calc', 'relative_volume_10d_calc', 'market_cap_basic',
        'Stoch.K', 'Stoch.D', 'SMA50', 'EMA200', 'RSI',
        'EMA8', 'EMA21', 'EMA34', 'EMA55', 'EMA89',
        'EMA8|1W', 'EMA21|1W', 'EMA34|1W', 'EMA55|1W', 'EMA89|1W',
        'EMA8|1M', 'EMA21|1M', 'EMA34|1M', 'EMA55|1M', 'EMA89|1M',
        'SMA50|1W', 'EMA200|1W', 'SMA50|1M', 'EMA200|1M'
    ]
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'adx_min': 20.0,
            'adx_max': 100.0,
            'mcap_min_b': 0.0,
            'mcap_max_b': 2.0,
            'stoch_min': 0.0,
            'stoch_max': 40.0,  # Default to 40 as requested
            'include_mega_caps': False,
            'require_within_1_atr': True  # Toggle for price within 1 ATR of EMA21
        }
    
    def get_param_config(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'adx_range', 'label': 'ADX Range', 'type': 'range', 
             'fields': [('adx_min', 'Min'), ('adx_max', 'Max')]},
            {'name': 'mcap_range', 'label': 'Market Cap ($B)', 'type': 'range',
             'fields': [('mcap_min_b', 'Min'), ('mcap_max_b', 'Max')],
             'mega_cap_switch': True},
            {'name': 'stoch_range', 'label': 'Stochastic (8,3,3)', 'type': 'range',
             'fields': [('stoch_min', 'Min'), ('stoch_max', 'Max')]},
            {'name': 'require_within_1_atr', 'label': 'Require Within 1 ATR', 'type': 'switch',
             'tooltip': 'When ON, only shows stocks within 1 ATR of EMA21. Turn OFF to include overextended stocks.'}
        ]
    
    def build_query(self, params: Dict[str, Any]) -> Query:
        adx_range = (params.get('adx_min', 20), params.get('adx_max', 100))
        mcap_min = params.get('mcap_min_b', 0) * 1_000_000_000
        mcap_max = params.get('mcap_max_b', 2) * 1_000_000_000
        if params.get('include_mega_caps'):
            mcap_max = 5_000_000_000_000
        mcap_range = (mcap_min, mcap_max)
        stoch_range = (params.get('stoch_min', 0), params.get('stoch_max', 40))

        
        # Build base filters
        base_filters = [
            # General Filters
            col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
            col('close') > 0.01,
            col('volume') >= 500_000,
            col('average_volume_10d_calc') > 500_000,
            
            # User Dynamic Range Filters
            col('ADX').between(adx_range[0], adx_range[1]),
            col('market_cap_basic').between(mcap_range[0], mcap_range[1]),
            col('Stoch.K').between(stoch_range[0], stoch_range[1]),

            # Trend filters (always required)
            col('SMA50') > col('EMA200'),
            col('SMA50|1W') > col('EMA200|1W'),
            col('SMA50|1M') > col('EMA200|1M'),

            # EMA Stack (always required)
            col('EMA8') > col('EMA21'), col('EMA21') > col('EMA34'), 
            col('EMA34') > col('EMA55'), col('EMA55') > col('EMA89'),

            col('EMA8|1W') > col('EMA21|1W'), col('EMA21|1W') > col('EMA34|1W'), 
            col('EMA34|1W') > col('EMA55|1W'), col('EMA55|1W') > col('EMA89|1W'),

            col('EMA8|1M') > col('EMA21|1M'), col('EMA21|1M') > col('EMA34|1M'), 
            col('EMA34|1M') > col('EMA55|1M'), col('EMA55|1M') > col('EMA89|1M')
        ]
        

        
        query = (
            Query()
            .select(*self.select_columns)
            .where(*base_filters)
            .limit(1000)
        )
        return query
    
    def post_process(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        if df.empty:
            return df
        
        params = params or {}
        require_within_1_atr = params.get('require_within_1_atr', True)
        
        # Rename columns first for consistency
        df = df.rename(columns={'Stoch.K': 'Stoch_K', 'Stoch.D': 'Stoch_D', 'ATR|1W': 'ATR_1W'})
        
        # Calculate squeeze ratio (ATR / (ATR_1W/2)) - normalizing for Daily vs Week approx
        df['SqueezeRatio'] = df.apply(
            lambda row: round(row['ATR'] / (row['ATR_1W'] / 2.0), 2) if row['ATR_1W'] > 0 else 1.0, 
            axis=1
        )
        
        # Conditionally filter for stocks within 1 ATR of EMA21
        if require_within_1_atr:
            df['dist_to_21'] = (df['close'] - df['EMA21']).abs()
            df = df[df['dist_to_21'] <= df['ATR']]
        
        df = df.fillna(0.0)
        return df
    
    def get_fixed_criteria(self, params: Dict[str, Any] = None) -> list:
        """Return list of fixed/locked strategy criteria for display."""
        params = params or {}
        require_within_1_atr = params.get('require_within_1_atr', True)
        
        criteria = [
            "📊 US Exchanges Only (NYSE, NASDAQ, AMEX)",
            "💰 Volume ≥ 500K daily",
            "📈 EMA Stack Aligned (D/W/M): 8 > 21 > 34 > 55 > 89",
            "✅ Uptrend: SMA50 > EMA200 (D/W/M)",
        ]
            
        if require_within_1_atr:
            criteria.append("🎯 Not Overextended: Price within 1 ATR of EMA21")
        else:
            criteria.append("🚀 Within 1 ATR: OFF (includes extended stocks)")
            
        return criteria
