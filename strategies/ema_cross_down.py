"""
Bearish EMA Cross Momentum Strategy
Signals based on EMA(8) crossing BELOW EMA(34) (Death Cross) with momentum and volatility confirmation.
"""
from tradingview_screener import Query, col
from typing import Dict, Any, List
import pandas as pd
from .base import BaseStrategy


class EmaCrossDownStrategy(BaseStrategy):
    """
    Finds stocks where EMA(8) has crossed BELOW EMA(34).
    The "freshness" of the cross is determined by the small distance between EMA8 and EMA34.
    Includes "flipped" Stochastic logic (Overbought) for short entry.
    """
    
    name = "Bearish EMA Cross (Down)"
    description = "EMA(8) crossing BELOW EMA(34) with Bearish Momentum"
    
    select_columns = [
        'name', 'description', 'close', 'change', 'sector', 'volume', 'type',
        'ADX', 'ATR', 'ATR|1W', 'average_volume_10d_calc', 'relative_volume_10d_calc', 'market_cap_basic',
        'Stoch.K', 'Stoch.D', 'RSI',
        'EMA8', 'EMA21', 'EMA34', 'EMA50', 'EMA55', 'EMA89', 'EMA200', 'SMA200',
        'price_52_week_high', 'price_52_week_low'
    ]
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'adx_min': 20.0,
            'vol_min_rel': 1.2,
            'max_spread_pct': 2.0, 
            'stoch_min': 50.0, # Want Stoch to be relatively high (not oversold) for fresh breakdown
            'include_mega_caps': True
        }
    
    def get_param_config(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'adx_min', 'label': 'Min ADX', 'type': 'number', 'min': 10, 'max': 50, 'step': 1},
            {'name': 'vol_min_rel', 'label': 'Min Relative Vol', 'type': 'number', 'min': 0.5, 'max': 5.0, 'step': 0.1},
            {'name': 'stoch_min', 'label': 'Min Stoch % (Not Oversold)', 'type': 'number', 'min': 20, 'max': 80, 'step': 5},
            {'name': 'max_spread_pct', 'label': 'Max Cross Spread %', 'type': 'number', 'min': 0.1, 'max': 5.0, 'step': 0.1,
             'tooltip': 'How close EMA8 must be to EMA34 to count as a "cross"'},
        ]
    
    def build_query(self, params: Dict[str, Any]) -> Query:
        adx_min = params.get('adx_min', 20)
        vol_min = params.get('vol_min_rel', 1.2)
        stoch_min = params.get('stoch_min', 50)
        
        query = (
            Query()
            .select(*self.select_columns)
            .where(
                # General Filters
                col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
                col('close') > 2.0,
                col('volume') >= 300_000,
                col('type') == 'stock',
                
                # The Signal: EMA8 < EMA34 (BEARISH CROSS)
                col('EMA8') < col('EMA34'),
                
                # Momentum & Trend
                col('ADX') >= adx_min,
                col('relative_volume_10d_calc') >= vol_min,
                col('close') < col('EMA34'), # Price confirming downtrend
                
                # Avoid catching falling knives that are already oversold
                col('Stoch.K') > stoch_min, 
                
                # Major Downtrend check (Price below 200)
                col('close') < col('EMA200'), 
            )
            .limit(1000)
        )
        return query
    
    def post_process(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        if df.empty:
            return df
        
        params = params or self.get_default_params()
        max_spread = params.get('max_spread_pct', 2.0)
        
        # Calculate Spread (Inverted for Bearish: EMA34 - EMA8)
        # We want positive spread where 34 is higher than 8
        df['ema_spread_pct'] = ((df['EMA34'] - df['EMA8']) / df['close']) * 100
        
        # Squeeze Ratio
        if 'ATR' in df.columns and 'ATR|1W' in df.columns:
            df['SqueezeRatio'] = df.apply(
                lambda row: round(row['ATR'] / (row['ATR|1W'] / 2.0), 2) if row.get('ATR|1W', 0) > 0 else 1.0, 
                axis=1
            )
        
        # Filter for "Fresh" crosses
        df = df[df['ema_spread_pct'] <= max_spread]
        
        # Sort by spread ascending (tightest spread = freshest cross)
        df = df.sort_values('ema_spread_pct', ascending=True)
        
        # Add Signals
        def get_signals(row):
            signals = []
            
            # Cross Freshness
            spread = row.get('ema_spread_pct', 100)
            if spread < 0.5:
                signals.append("🩸 FRESH BREAKDOWN")
            elif spread < 1.0:
                signals.append("📉 Recent Cross")
                
            # Momentum
            rel_vol = row.get('relative_volume_10d_calc', 0)
            if rel_vol > 2.0:
                signals.append(f"🔊 Vol {rel_vol:.1f}x")
            
            # Volatility
            sq = row.get('SqueezeRatio', 1.0)
            if sq < 0.8:
                signals.append(f"🔋 Squeeze ({sq:.2f})")
            elif sq > 1.2:
                signals.append("💥 Expanding Vol")
            
            # Trend Strength
            adx = row.get('ADX', 0)
            if adx > 40:
                signals.append(f"🐻 Strong Bear ({adx:.0f})")
                
            return " ".join(signals)
            
        df['Signals'] = df.apply(get_signals, axis=1)
        
        df = df.fillna(0.0)
        return df

    def get_fixed_criteria(self, params: Dict[str, Any] = None) -> list:
        params = params or {}
        adx_min = params.get('adx_min', 20)
        stoch_min = params.get('stoch_min', 50)
        
        return [
            "🩸 Signal: EMA(8) crossing BELOW EMA(34)",
            f"📉 Stoch: > {stoch_min} (Not Oversold)",
            f"📊 Buying Pressure: Rel Vol ≥ 1.2x",
            "🛡️ Downtrend: Price < EMA(200)",
            "🎯 Freshness: Sorted by tightness of EMA spread"
        ]
