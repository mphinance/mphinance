
import asyncio
import pandas as pd
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from strategies.trend_exhaustion import TrendExhaustionStrategy
# Mocking query object since we don't have the full app context
class MockQuery:
    def __init__(self, strategy):
        self.strategy = strategy
        
    def get_scanner_data(self):
        # Return a dummy dataframe that mimics what TradingView would return
        # We need tickers that definitely exist
        data = {
            'name': ['AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX', 'SPY'],
            'description': ['Apple', 'Tesla', 'Nvidia', 'AMD', 'Microsoft', 'Google', 'Amazon', 'Meta', 'Netflix', 'SPY'],
            'close': [200.0] * 10,
            'change': [1.0] * 10,
            'volume': [1000000] * 10,
            'relative_volume_10d_calc': [2.0] * 10,
            'market_cap_basic': [1000000000] * 10,
            'sector': ['Tech'] * 10,
            'ADX': [25.0] * 10,
            'ATR': [5.0] * 10,
            'exchange': ['NASDAQ'] * 10
        }
        return 10, pd.DataFrame(data)

async def test_scanner():
    print("Initializing Strategy...")
    strategy = TrendExhaustionStrategy()
    
    # Test Params for "Potential Setups"
    params = {
        'threshold': 20,
        'signal_mode': 'Potential Setups',
        'signal_type': 'All', 
        'require_hull_trend': True,
        'min_rel_vol': 0.5,
        'timeframe': '1d',
        'hull_source': 'hlc3'
    }
    
    print(f"Building Query with params: {params}")
    # Initialize params in strategy (imitating build_query)
    strategy.build_query(params)
    
    print("Running Post-Process (Fetching History & calculating indicators)...")
    try:
        # Create a mock dataframe directly since we can't easily run the TV query without auth/lib
        mock_query = MockQuery(strategy)
        _, df = mock_query.get_scanner_data()
        
        results = strategy.post_process(df)
        
        print(f"Final Matches: {len(results)}")
        if not results.empty:
            print(results[['name', 'Signal', 'SignalDate', 'WR21', 'WR112', 'HMA55', 'PriceVsHMA']].head())
        else:
            print("No matches found in test set (expected if no signals in these 10 stocks).")
            
    except Exception as e:
        print(f"Exception caught during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scanner())
