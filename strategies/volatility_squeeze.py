"""
Fibonacci Volatility Squeeze Strategy - "The Snap"
Uses NATR with EMA crossover to detect volatility expansion after compression.
"""
from tradingview_screener import Query, col
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from .base import BaseStrategy


def calc_natr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    """Calculate Normalized Average True Range (NATR) as percentage of close."""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=length, adjust=False).mean()
    natr = (atr / close) * 100
    return natr


def calc_ema(series: pd.Series, length: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=length, adjust=False).mean()


class VolatilitySqueezeStrategy(BaseStrategy):
    """
    Finds stocks exiting a volatility squeeze using Fibonacci-based volatility lines.
    
    The Core Concept:
    - Fast Line: EMA(8) of NATR(14) - responsive to volatility changes
    - Slow Line: EMA(34) of NATR(14) - baseline volatility level
    - "The Snap": Fast crossing above Slow, or curling up from recent low
    - Trend Filter: Price > EMA(34) to avoid catching falling knives
    """
    
    name = "Volatility Squeeze"
    description = "Fibonacci volatility lines detecting 'The Snap' after a squeeze"
    
    select_columns = [
        'name', 'description', 'close', 'change', 'sector', 'volume', 'type',
        'high', 'low', 'open',  # Needed for NATR calculation
        'ADX', 'ATR', 'ATR|1W', 'average_volume_10d_calc', 'relative_volume_10d_calc', 'market_cap_basic',
        'Stoch.K', 'Stoch.D', 'SMA50', 'EMA200', 'RSI',
        'EMA8', 'EMA21', 'EMA34', 'EMA55', 'EMA89',
        'EMA8|1W', 'EMA21|1W', 'EMA34|1W', 'EMA55|1W', 'EMA89|1W',
        'SMA50|1W', 'EMA200|1W', 'SMA50|1M', 'EMA200|1M',
        'price_52_week_high'  # For flatline filter
    ]
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'lookback_squeeze': 10,   # Days to check for recent squeeze
            'min_squeeze_days': 5,    # Minimum days Fast < Slow in lookback
            'require_trend': True,    # Require price > EMA34
            'adx_min': 20.0,          # Min ADX (want directional trending)
            'mcap_min_b': 0.0,
            'mcap_max_b': 1000.0,
            'include_mega_caps': True,
            'require_volume_spark': False  # Optional volume confirmation
        }
    
    def get_param_config(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'lookback_squeeze', 'label': 'Squeeze Lookback (Days)', 'type': 'number', 'min': 5, 'max': 20, 'step': 1},
            {'name': 'min_squeeze_days', 'label': 'Min Squeeze Days', 'type': 'number', 'min': 2, 'max': 10, 'step': 1},
            {'name': 'adx_min', 'label': 'Min ADX', 'type': 'number', 'min': 10, 'max': 40, 'step': 1},
            {'name': 'require_trend', 'label': 'Require Uptrend', 'type': 'checkbox'},
            {'name': 'require_volume_spark', 'label': 'Require Volume Spark (1.3x)', 'type': 'checkbox'},
            {'name': 'mcap_range', 'label': 'Market Cap ($B)', 'type': 'range',
             'fields': [('mcap_min_b', 'Min'), ('mcap_max_b', 'Max')],
             'mega_cap_switch': True}
        ]
    
    def build_query(self, params: Dict[str, Any]) -> Query:
        """
        Pre-filter using TradingView screener to reduce API calls.
        Actual volatility logic is computed in post_process with historical data.
        """
        adx_min = params.get('adx_min', 20)
        mcap_min = params.get('mcap_min_b', 0) * 1_000_000_000
        mcap_max = params.get('mcap_max_b', 1000) * 1_000_000_000
        if params.get('include_mega_caps'):
            mcap_max = 5_000_000_000_000
        
        query = (
            Query()
            .select(*self.select_columns)
            .where(
                # General Filters
                col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
                col('close') > 2.0,
                col('volume') >= 300_000,
                col('average_volume_10d_calc') > 300_000,
                
                # Instrument Type Filter - Common Stock Only
                # Excludes: Preferreds, Funds, CEFs, ETFs, ADRs etc.
                col('type') == 'stock',
                
                # ADX filter for trend strength (not too weak)
                col('ADX') >= adx_min,
                
                # Relative Volume filter (avoid dead stocks)
                col('relative_volume_10d_calc') >= 1.3,
                
                # Market Cap
                col('market_cap_basic').between(mcap_min, mcap_max),

                # Daily EMA Stack (Quality Trend Filter)
                col('EMA8') > col('EMA21'), 
                col('EMA21') > col('EMA34'), 
                col('EMA34') > col('EMA55'), 
                col('EMA55') > col('EMA89')
            )
            .limit(1500)
        )
        return query
    
    def calculate_volatility_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Calculate the Fibonacci volatility lines and signals.
        This is applied per-ticker using historical data.
        
        Returns DataFrame with signal columns added.
        """
        lookback = params.get('lookback_squeeze', 10)
        min_squeeze_days = params.get('min_squeeze_days', 5)
        
        if len(df) < 35:  # Need enough data for EMA(34)
            df['buy_signal'] = False
            return df
        
        # 1. Calculate NATR (Normalized ATR - as percentage of close)
        df['natr'] = calc_natr(df['high'], df['low'], df['close'], length=14)
        
        # 2. Calculate Fibonacci Volatility Lines
        # Fast Line: EMA(8) of NATR - responsive to volatility changes
        df['vol_fast_8'] = calc_ema(df['natr'], length=8)
        
        # Slow Line: EMA(34) of NATR - baseline volatility
        df['vol_slow_34'] = calc_ema(df['natr'], length=34)
        
        # 3. Trend Filter
        df['trend_ema_34'] = calc_ema(df['close'], length=34)
        
        # --- LOGIC GATES ---
        
        # Gate 1: Recent Squeeze Check
        # Fast was below Slow recently (volatility was compressed)
        was_below = (df['vol_fast_8'] < df['vol_slow_34']).astype(int)
        df['recent_squeeze'] = was_below.rolling(lookback).sum() >= min_squeeze_days
        
        # Gate 2: "The Snap" Detection
        # Option A: Classic Crossover (Fast crosses above Slow)
        df['crossover'] = (df['vol_fast_8'] > df['vol_slow_34']) & \
                          (df['vol_fast_8'].shift(1) <= df['vol_slow_34'].shift(1))
        
        # Option B: The Curl (volatility expanding from recent low point)
        df['is_rising'] = df['vol_fast_8'] > df['vol_fast_8'].shift(1)
        
        # Find position of minimum in the lookback window
        # argmin returns index within window. Window [0..9] where 9 is oldest, 0 is newest.
        # If low was in position 0, 1, or 2 (most recent 3 bars), it's a "recent low"
        def find_min_position(x):
            if len(x) < lookback:
                return np.nan
            # np.argmin returns index of minimum. 
            # For a window of size N, 0 = most recent, N-1 = oldest
            return (len(x) - 1) - np.argmin(x[::-1])  # Convert to "bars ago" perspective
        
        df['min_position'] = df['vol_fast_8'].rolling(lookback).apply(
            lambda x: np.argmin(x), raw=True
        )
        # argmin returns 0-9 where 9 = most recent bar in the window
        # So we want min_position >= (lookback - 3) to indicate "low was recent"
        df['low_was_recent'] = df['min_position'] >= (lookback - 3)
        
        # Combined Curl Signal: Rising from a recent bottom
        df['curl_signal'] = df['is_rising'] & df['low_was_recent'] & (df['vol_fast_8'] < df['vol_slow_34'])
        
        # The Snap: Either crossover OR curl
        df['snap_signal'] = df['crossover'] | df['curl_signal']
        
        # Gate 3: Trend Filter
        df['uptrend'] = df['close'] > df['trend_ema_34']
        
        # FINAL SIGNAL
        df['buy_signal'] = df['recent_squeeze'] & df['snap_signal']
        
        if params.get('require_trend', True):
            df['buy_signal'] = df['buy_signal'] & df['uptrend']
        
        return df
    
    def post_process(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Post-process the screener results.
        Note: The full volatility calculation requires historical data which
        isn't available from the screener. We use screener data for initial 
        filtering and add useful metadata.
        """
        if df.empty:
            return df
        
        params = params or self.get_default_params()
        
        # Rename cols for consistency
        df = df.rename(columns={'Stoch.K': 'Stoch_K', 'Stoch.D': 'Stoch_D', 'ATR|1W': 'ATR_1W'})
        
        # Squeeze Ratio as a proxy indicator (ATR / normalized weekly ATR)
        # This is a heuristic since we don't have true NATR lines from screener
        df['SqueezeRatio'] = df.apply(
            lambda row: round(row['ATR'] / (row['ATR_1W'] / 2.0), 2) if row.get('ATR_1W', 0) > 0 else 1.0, 
            axis=1
        )
        
        # Prioritize stocks showing squeeze characteristics (ratio < 1.0)
        df = df[df['SqueezeRatio'] < 1.0]
        
        # 52-Week High Flatline Filter
        # Exclude stocks within 1% of 52-week high (buyout targets pinned to deal price)
        if 'price_52_week_high' in df.columns:
            df['pct_from_high'] = ((df['price_52_week_high'] - df['close']) / df['price_52_week_high']) * 100
            # Keep only stocks > 1% below their 52-week high
            df = df[df['pct_from_high'] > 1.0]
        
        # Spark Indicators
        def check_signals(row):
            signals = []
            
            # Volume Spark
            rel_vol = row.get('relative_volume_10d_calc', 0)
            if rel_vol and rel_vol > 1.5:
                signals.append(f"🔥 Vol {rel_vol:.1f}x")
            elif rel_vol and rel_vol > 1.3:
                signals.append(f"📊 Vol {rel_vol:.1f}x")
                
            # Deep Coil (very low ADX)
            adx = row.get('ADX', 0)
            if adx and adx < 15:
                signals.append("🌀 Deep Coil")
            elif adx and adx < 20:
                signals.append("💤 Coiling")
                
            # Squeeze intensity
            sr = row.get('SqueezeRatio', 1.0)
            if sr < 0.7:
                signals.append(f"🔋 Tight ({sr:.2f})")
            elif sr < 0.85:
                signals.append(f"⚡ Squeeze ({sr:.2f})")
                
            return " ".join(signals) if signals else "—"
        
        df['Signals'] = df.apply(check_signals, axis=1)
        
        # Volume filter if required
        if params.get('require_volume_spark', False):
            df = df[df['relative_volume_10d_calc'] >= 1.3]
        
        # Sort by squeeze tightness (lower ratio = tighter squeeze)
        df = df.sort_values('SqueezeRatio', ascending=True)
        
        df = df.fillna(0.0)
        return df
    
    def get_fixed_criteria(self, params: Dict[str, Any] = None) -> list:
        params = params or {}
        adx_min = params.get('adx_min', 20)
        lookback = params.get('lookback_squeeze', 10)
        min_days = params.get('min_squeeze_days', 5)
        
        return [
            "🏷️ Common Stock Only (excludes Preferreds, Funds, CEFs)",
            "📉 Not Flatlined: > 1% below 52-week high (filters buyout targets)",
            f"🔋 Squeeze: ATR(14) < ATR(1W)/2 (SqueezeRatio < 1.0)",
            f"💪 Trend Strength: ADX ≥ {adx_min}",
            "📊 Relative Volume: ≥ 1.3x avg",
            "📈 Trend: EMA Stack 8 > 21 > 34 > 55 > 89",
            "📊 Volume: ≥ 300K Daily",
            "🔥 Signals: Vol spikes, Deep Coil, Squeeze intensity"
        ]
