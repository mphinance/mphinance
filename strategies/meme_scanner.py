"""
MEME Scanner Strategy
Filters for the top 200 most liquid stocks (Volume) and then keeps the top 30 with highest Implied Volatility (IV).
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import yfinance as yf
import concurrent.futures
from tradingview_screener import Query, col
from .base import BaseStrategy

class MemeScannerStrategy(BaseStrategy):
    """
    Mimics the MEME ETF methodology:
    1. Select top 200 US stocks by Volume.
    2. Sort by Implied Volatility (IV) descending.
    3. Keep top 30.
    """
    
    name = "MEME Screen"
    description = "Top 200 Volume -> Top 30 High Implied Volatility (IV)"
    
    select_columns = [
        'name', 'description', 'close', 'change', 'volume', 
        'market_cap_basic', 'sector', 'industry'
    ]
    
    def get_default_params(self) -> Dict[str, Any]:
        return {}
    
    def get_param_config(self) -> List[Dict[str, Any]]:
        return []
        
    def build_query(self, params: Dict[str, Any]) -> Query:
        """Fetch top 200 stocks by volume."""
        return (
            Query()
            .select(*self.select_columns)
            .where(
                col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
                col('type') == 'stock',
                col('is_primary') == True,
                col('close') > 1.0, # Basic penny stock filter
                # Ensure we have decent volume to start with
                col('volume') > 1_000_000 
            )
            .order_by('volume', ascending=False)
            .limit(200)
        )

    def _get_iv(self, ticker: str) -> float:
        """Fetch approx 30-day IV from yfinance options chain."""
        try:
            # Replace dot with hyphen for yfinance (e.g. BRK.B -> BRK-B)
            safe_ticker = ticker.replace('.', '-')
            tk = yf.Ticker(safe_ticker)
            
            # Use 30-day historical volatility as a fallback if option chain is heavy?
            # No, user specifically asked for IV.
            # Getting current IV from yf is a bit tricky without full chain.
            # But yfinance Ticker object might have 'impliedVolatility' in info?
            # Checking 'info' is expensive.
            # Checking options chain is also expensive.
            
            # Efficient way: Get nearest expiration chain
            exps = tk.options
            if not exps:
                return 0.0
                
            # Get first expiration (closest to 30 days would be better, but let's start with front month for speed)
            # Actually, standard IV is usually interpolated 30-day. 
            # Let's try to grab a front-month ATM option IV.
            
            chain = tk.option_chain(exps[0])
            
            # Combine calls and puts
            opts = pd.concat([chain.calls, chain.puts])
            
            # Filter for volume/OI to avoid bad data? 
            # Just take average IV of near-the-money options
            current_price = tk.fast_info.last_price
            
            # Filter for strikes within 5% of price
            atm_opts = opts[
                (opts['strike'] >= current_price * 0.95) & 
                (opts['strike'] <= current_price * 1.05)
            ]
            
            if atm_opts.empty:
                return 0.0
                
            return atm_opts['impliedVolatility'].mean()
            
        except Exception:
            return 0.0

    def post_process(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        """Fetch IV for the 200 candidates and filter to top 30."""
        print(f"  [MEME] Fetching IV for {len(df)} candidates...")
        
        tickers = df['name'].tolist()
        iv_map = {}
        
        # Concurrently fetch IV
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ticker = {executor.submit(self._get_iv, t): t for t in tickers}
            for i, future in enumerate(concurrent.futures.as_completed(future_to_ticker)):
                ticker = future_to_ticker[future]
                try:
                    iv = future.result()
                    iv_map[ticker] = iv
                except Exception as exc:
                    iv_map[ticker] = 0.0
                    
                if (i + 1) % 50 == 0:
                    print(f"  [MEME] Processed {i+1}/{len(tickers)}")

        # Add IV to dataframe
        df['IV'] = df['name'].map(iv_map)
        
        # Sort by IV desc
        df = df.sort_values('IV', ascending=False)
        
        # Keep top 30
        result = df.head(30).copy()
        
        # Formatting
        result['IV'] = result['IV'].apply(lambda x: f"{x:.2%}")
        
        print(f"  [MEME] Filtered to top {len(result)} stocks by IV.")
        return result
