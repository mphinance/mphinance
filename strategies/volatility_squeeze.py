"""
Volatility Squeeze Strategy - Finding 'Coiling' Stocks with Spark Triggers
"""
from tradingview_screener import Query, col
from typing import Dict, Any, List
import pandas as pd
from .base import BaseStrategy


class VolatilitySqueezeStrategy(BaseStrategy):
    """Finds stocks in a volatility squeeze (ATR < ATR|1W) with potential volume triggers."""
    
    name = "Volatility Squeeze"
    description = "Find coiling stocks (ATR < ATR55) with volume spark potential"
    
    select_columns = [
        'name', 'description', 'close', 'change', 'sector', 'volume',
        'ADX', 'ATR', 'ATR|1W', 'average_volume_10d_calc', 'relative_volume_10d_calc', 'market_cap_basic',
        'Stoch.K', 'Stoch.D', 'SMA50', 'EMA200', 'RSI',
        'EMA8', 'EMA21', 'EMA34', 'EMA55', 'EMA89',
        'EMA8|1W', 'EMA21|1W', 'EMA34|1W', 'EMA55|1W', 'EMA89|1W',
        'SMA50|1W', 'EMA200|1W', 'SMA50|1M', 'EMA200|1M'
    ]
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'adx_max': 30.0,  # Coiling usually means lower ADX
            'mcap_min_b': 0.0,
            'mcap_max_b': 1000.0, # Broad range by default
            'squeeze_required': True,
            'include_mega_caps': True
        }
    
    def get_param_config(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'adx_max', 'label': 'Max ADX (Coil)', 'type': 'number', 'min': 10, 'max': 60, 'step': 1},
            {'name': 'mcap_range', 'label': 'Market Cap ($B)', 'type': 'range',
             'fields': [('mcap_min_b', 'Min'), ('mcap_max_b', 'Max')],
             'mega_cap_switch': True}
        ]
    
    def build_query(self, params: Dict[str, Any]) -> Query:
        adx_max = params.get('adx_max', 30)
        mcap_min = params.get('mcap_min_b', 0) * 1_000_000_000
        mcap_max = params.get('mcap_max_b', 1000) * 1_000_000_000
        if params.get('include_mega_caps'):
            mcap_max = 5_000_000_000_000
        
        # Squeeze logic: ATR(14) < ATR(1W) (approx for ATR55 weekly or long term)
        # Using ATR|1W as proxy for longer term volatility reference
        
        query = (
            Query()
            .select(*self.select_columns)
            .where(
                # General Filters
                col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
                col('close') > 2.0,
                col('volume') >= 300_000,
                col('average_volume_10d_calc') > 300_000,
                
                # Squeeze & Trend
                # col('ATR') < col('ATR|1W'),  # The Squeeze (Filtered in post-process with normalization)
                col('ADX') < adx_max,          # The Coil (Quiet)
                
                # Basic Trend (Don't buy garbage)
                # col('SMA50') > col('EMA200'), # Optional, but good for quality
                
                # Market Cap
                col('market_cap_basic').between(mcap_min, mcap_max),

                # Daily EMA Stack (Trend Alignment)
                col('EMA8') > col('EMA21'), col('EMA21') > col('EMA34'), 
                col('EMA34') > col('EMA55'), col('EMA55') > col('EMA89')
            )
            .limit(1000)
        )
        return query
    
    def post_process(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        if df.empty:
            return df
        
        # Rename cols
        df = df.rename(columns={'Stoch.K': 'Stoch_K', 'Stoch.D': 'Stoch_D', 'ATR|1W': 'ATR_1W'})
        
        # 1. Squeeze Ratio (Heuristic: ATR < WeeklyATR/2)
        # We normalize Weekly ATR by dividing by 2 to approximate "Long Term Daily ATR"
        df['SqueezeRatio'] = df.apply(
            lambda row: round(row['ATR'] / (row['ATR_1W'] / 2.0), 2) if row['ATR_1W'] > 0 else 1.0, 
            axis=1
        )
        
        # Filter: Only keep squeezed stocks (< 1.0 ratio after normalization)
        df = df[df['SqueezeRatio'] < 1.0]
        
        # 2. Volume Trigger (Spark)
        # Calculate Volume Ratio if not available, or use relative_volume_10d_calc
        # Relative Volume is usually Vol / AvgVol
        
        def check_spark(row):
            triggers = []
            
            # Volume Spike (> 1.5x)
            rel_vol = row.get('relative_volume_10d_calc', 0)
            if rel_vol > 1.5:
                triggers.append(f"🔥 Vol {rel_vol:.1f}x")
                
            # ADX Rising? We only have current ADX. 
            # If ADX is very low (< 15), it's a "Deep Coil"
            if row.get('ADX', 0) < 15:
                triggers.append("🌀 Deep Coil")
                
            return " ".join(triggers) if triggers else ""

        df['Spark'] = df.apply(check_spark, axis=1)
        
        df = df.fillna(0.0)
        return df
    
    def get_fixed_criteria(self, params: Dict[str, Any] = None) -> list:
        params = params or {}
        adx_max = params.get('adx_max', 30)
        return [
            "🔋 Squeeze: ATR(14) < (ATR|1W / 2) (Heuristic Daily Proxy)",
            f"🤫 Quiet Coil: ADX < {adx_max}",
            "📊 Volume Filter: ≥ 300K Daily",
            "📈 EMA Stack: 8 > 21 > 34 > 55 > 89",
            "🔥 Spark Triggers: Looking for Vol > 1.5x Avg"
        ]
