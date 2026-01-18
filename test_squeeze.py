import pandas as pd
from strategies.volatility_squeeze import VolatilitySqueezeStrategy

def test_squeeze_strategy():
    print("Initializing Volatility Squeeze Strategy...")
    strategy = VolatilitySqueezeStrategy()
    
    print("Building query...")
    query = strategy.build_query({})
    
    print("Fetching data from TradingView...")
    count, df = query.get_scanner_data()
    print(f"Initial candidates (Filtered by Stacked EMA): {count}")
    
    if count > 0:
        print("\nTop 5 Candidates:")
        print(df[['name', 'close', 'EMA8', 'EMA21', 'EMA34', 'EMA55', 'EMA89']].head())
        
        # Verify stack
        for i, row in df.head().iterrows():
            stack_ok = (row['EMA8'] > row['EMA21'] > row['EMA34'] > row['EMA55'] > row['EMA89'])
            print(f"{row['name']}: Stack OK? {stack_ok}")
    else:
        print("No candidates found.")

if __name__ == "__main__":
    test_squeeze_strategy()
