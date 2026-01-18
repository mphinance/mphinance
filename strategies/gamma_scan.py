"""
Gamma Scan Strategy - Find stocks nearing high Open Interest strikes
Combines TAO EMA stack with options gamma proximity detection
"""
from tradingview_screener import Query, col
from typing import Dict, Any, List
import pandas as pd
import yfinance as yf
from .base import BaseStrategy


class GammaScanStrategy(BaseStrategy):
    """
    Scans for momentum stocks approaching high OI option strikes.
    
    These "gamma walls" can act as magnets or resistance levels as
    market makers delta-hedge their positions.
    """
    
    name = "Gamma Scan"
    description = "TAO EMA Stack + High OI Strike Proximity"
    
    select_columns = [
        'name', 'description', 'close', 'change', 'sector',
        'volume', 'market_cap_basic', 'ADX', 'ATR'
    ]
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'proximity_pct': 2.0,      # How close to strike (%)
            'min_oi': 1000,            # Minimum open interest
            'min_volume': 1_000_000,   # Minimum daily volume
            'min_adx': 15,             # ADX filter
            'signal_type': 'All',      # All, Calls Only, Puts Only
        }
    
    def get_param_config(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'proximity_pct', 'label': 'Proximity %', 'type': 'number', 'step': 0.5, 'min': 0.5, 'max': 10},
            {'name': 'min_oi', 'label': 'Min Open Interest', 'type': 'number', 'step': 500, 'min': 100},
            {'name': 'min_volume', 'label': 'Min Volume', 'type': 'number', 'step': 100000},
            {'name': 'min_adx', 'label': 'Min ADX', 'type': 'number', 'step': 5, 'min': 0, 'max': 50},
            {'name': 'signal_type', 'label': 'Wall Type', 'type': 'select', 
             'options': ['All', 'Calls Only', 'Puts Only']},
        ]
    
    def build_query(self, params: Dict[str, Any]) -> Query:
        """Build TAO stacked EMA query to get momentum candidates."""
        self.params = params
        
        min_volume = params.get('min_volume', 1_000_000)
        min_adx = params.get('min_adx', 15)
        
        query = (
            Query()
            .select(*self.select_columns)
            .where(
                col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
                col('is_primary') == True,
                col('type') == 'stock',
                col('volume') >= min_volume,
                col('ADX') >= min_adx,
                # SMA/EMA trend alignment
                col('SMA50') > col('EMA200'),
                col('SMA50|1W') > col('EMA200|1W'),
                col('SMA50|1M') > col('EMA200|1M'),
                # Daily EMA Stack: 8 > 21 > 34 > 55 > 89
                col('EMA8') > col('EMA21'), col('EMA21') > col('EMA34'), 
                col('EMA34') > col('EMA55'), col('EMA55') > col('EMA89'),
                # Weekly EMA Stack
                col('EMA8|1W') > col('EMA21|1W'), col('EMA21|1W') > col('EMA34|1W'), 
                col('EMA34|1W') > col('EMA55|1W'), col('EMA55|1W') > col('EMA89|1W'),
                # Monthly EMA Stack
                col('EMA8|1M') > col('EMA21|1M'), col('EMA21|1M') > col('EMA34|1M'), 
                col('EMA34|1M') > col('EMA55|1M'), col('EMA55|1M') > col('EMA89|1M'),
            )
            .limit(500)
        )
        return query
    
    def _check_gamma_proximity(self, ticker: str, price: float, 
                                proximity_pct: float, min_oi: int, 
                                signal_type: str) -> dict | None:
        """Check if price is near a high-OI strike."""
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options
            
            if not expirations:
                return None
            
            # Get next expiration
            next_exp = expirations[0]
            chain = stock.option_chain(next_exp)
            
            walls = []
            
            # Check calls
            if signal_type in ['All', 'Calls Only']:
                high_oi_calls = chain.calls[chain.calls['openInterest'] >= min_oi]
                for _, row in high_oi_calls.iterrows():
                    strike = row['strike']
                    oi = row['openInterest']
                    pct_away = abs(price - strike) / price * 100
                    
                    if pct_away <= proximity_pct:
                        walls.append({
                            'type': 'CALL',
                            'strike': strike,
                            'oi': int(oi),
                            'pct_away': round(pct_away, 2),
                            'position': 'ABOVE' if strike > price else 'BELOW'
                        })
            
            # Check puts
            if signal_type in ['All', 'Puts Only']:
                high_oi_puts = chain.puts[chain.puts['openInterest'] >= min_oi]
                for _, row in high_oi_puts.iterrows():
                    strike = row['strike']
                    oi = row['openInterest']
                    pct_away = abs(price - strike) / price * 100
                    
                    if pct_away <= proximity_pct:
                        walls.append({
                            'type': 'PUT',
                            'strike': strike,
                            'oi': int(oi),
                            'pct_away': round(pct_away, 2),
                            'position': 'ABOVE' if strike > price else 'BELOW'
                        })
            
            if walls:
                max_wall = max(walls, key=lambda x: x['oi'])
                return {
                    'expiration': next_exp,
                    'walls': walls,
                    'max_wall': max_wall,
                    'total_nearby_oi': sum(w['oi'] for w in walls)
                }
            
            return None
            
        except Exception as e:
            print(f"  [{ticker}] Error: {e}")
            return None
    
    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter candidates by gamma proximity."""
        if df.empty:
            return df
        
        params = getattr(self, 'params', self.get_default_params())
        proximity_pct = params.get('proximity_pct', 2.0)
        min_oi = params.get('min_oi', 1000)
        signal_type = params.get('signal_type', 'All')
        
        results = []
        total = len(df)
        
        for i, row in df.iterrows():
            ticker = row['name'].replace('.', '-')
            price = row['close']
            
            print(f"[{len(results)+1}/{total}] Checking {ticker} @ ${price:.2f}...", end='')
            
            gamma_info = self._check_gamma_proximity(
                ticker, price, proximity_pct, min_oi, signal_type
            )
            
            if gamma_info:
                print(f" ✓ {len(gamma_info['walls'])} walls")
                
                # Add gamma info to row
                max_wall = gamma_info['max_wall']
                row = row.copy()
                row['Expiration'] = gamma_info['expiration']
                row['TotalNearbyOI'] = gamma_info['total_nearby_oi']
                row['TopWallType'] = max_wall['type']
                row['TopWallStrike'] = max_wall['strike']
                row['TopWallOI'] = max_wall['oi']
                row['PctAway'] = max_wall['pct_away']
                row['WallPosition'] = max_wall['position']
                
                # Build wall summary string
                wall_strs = []
                for w in sorted(gamma_info['walls'], key=lambda x: -x['oi'])[:3]:
                    arrow = "↑" if w['position'] == 'ABOVE' else "↓"
                    wall_strs.append(f"{arrow}{w['type'][0]}${w['strike']}({w['oi']:,})")
                row['WallSummary'] = " | ".join(wall_strs)
                
                results.append(row)
            else:
                print(" -")
        
        if results:
            result_df = pd.DataFrame(results)
            # Sort by total nearby OI
            result_df = result_df.sort_values('TotalNearbyOI', ascending=False)
            return result_df
        
        return pd.DataFrame()
    
    def get_fixed_criteria(self) -> list:
        return [
            "📈 TAO EMA Stack Aligned (D/W/M): 8 > 21 > 34 > 55 > 89",
            "✅ Uptrend: SMA50 > EMA200 (D/W/M)",
            "🎯 Near High OI Strikes (Gamma Walls)",
            "📊 Next Expiration Options Only"
        ]
