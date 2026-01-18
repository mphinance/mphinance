import pandas as pd
from strategies.meme_scanner import MemeScannerStrategy

def test_meme_strategy():
    print("Initializing MEME Strategy...")
    strategy = MemeScannerStrategy()
    
    print("Building query...")
    query = strategy.build_query({})
    
    print("Fetching data from TradingView...")
    count, df = query.get_scanner_data()
    print(f"Initial candidates: {count}")
    
    if count > 0:
        print("\nTop 5 by Volume (Pre-filter):")
        print(df[['name', 'volume', 'close']].head())
        
        print("\nRunning post-processing (IV Fetching)...")
        result = strategy.post_process(df)
        
        print(f"\nFinal Result Count: {len(result)}")
        print("\nTop 10 High IV Stocks:")
        print(result[['name', 'IV', 'volume', 'close', 'sector']].head(10))
    else:
        print("No candidates found.")

if __name__ == "__main__":
    test_meme_strategy()
