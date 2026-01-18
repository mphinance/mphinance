from tradingview_screener import Query, col
import pandas as pd

def test_atr_query():
    print("Testing ATR variations...")
    # List of candidates to try
    candidates = [
        'ATR', 'ATR[55]', 'ATR|55', 'ATR.55', 'average_true_range', 
        'AverageTrueRange', 'Volatility.D', 'Volatility', 'std_dev', 
        'daily_volatility'
    ]
    
    try:
        q = Query().select('name', 'close', *candidates).limit(5)
        # Note: If any single column is invalid, the whole query might fail or return error. 
        # But library often just ignores invalid ones or returns error.
        # Let's try one by one if batch fails.
        
        try:
            count, df = q.get_scanner_data()
            print(f"Batch fetch success. Columns: {df.columns.tolist()}")
            print(df.head())
        except Exception as e:
            print(f"Batch fetch failed: {e}")
            print("Trying individual columns...")
            for c in candidates:
                try:
                    q = Query().select('name', c).limit(1)
                    count, df = q.get_scanner_data()
                    if df is not None and not df.empty and df[c].iloc[0] is not None:
                        print(f"SUCCESS: {c} returned data: {df[c].iloc[0]}")
                    else:
                        print(f"FAIL: {c} returned None or no data")
                except Exception as ex:
                    print(f"ERROR: {c} caused exception: {ex}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_atr_query()
