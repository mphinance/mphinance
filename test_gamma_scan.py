#!/usr/bin/env python3
"""
Gamma Scan Test - Find stocks nearing high OI strikes
"""
from tradingview_screener import Query, col
import yfinance as yf
import pandas as pd
from datetime import datetime

def get_stacked_ema_candidates():
    """Get stocks passing the full TAO stacked EMA filter."""
    query = (
        Query()
        .select('name', 'close', 'ADX', 'volume')
        .where(
            col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
            col('is_primary') == True,
            col('type') == 'stock',
            col('volume') >= 1_000_000,
            col('ADX') >= 15,
            # SMA/EMA trend
            col('SMA50') > col('EMA200'),
            col('SMA50|1W') > col('EMA200|1W'),
            col('SMA50|1M') > col('EMA200|1M'),
            # Daily EMA Stack
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
    count, df = query.get_scanner_data()
    print(f"[Filter] {count} stocks pass stacked EMA filter")
    return df


def check_gamma_proximity(ticker: str, price: float, proximity_pct: float = 2.0, min_oi: int = 1000):
    """
    Check if price is near a high-OI strike.
    
    Returns dict with gamma info if near a wall, else None.
    """
    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options
        
        if not expirations:
            return None
        
        # Get next expiration
        next_exp = expirations[0]
        
        # Get options chain
        chain = stock.option_chain(next_exp)
        calls = chain.calls
        puts = chain.puts
        
        results = []
        
        # Check calls with high OI near price
        high_oi_calls = calls[calls['openInterest'] >= min_oi].copy()
        for _, row in high_oi_calls.iterrows():
            strike = row['strike']
            oi = row['openInterest']
            pct_away = abs(price - strike) / price * 100
            
            if pct_away <= proximity_pct:
                results.append({
                    'type': 'CALL',
                    'strike': strike,
                    'oi': int(oi),
                    'pct_away': round(pct_away, 2),
                    'position': 'ABOVE' if strike > price else 'BELOW'
                })
        
        # Check puts with high OI near price
        high_oi_puts = puts[puts['openInterest'] >= min_oi].copy()
        for _, row in high_oi_puts.iterrows():
            strike = row['strike']
            oi = row['openInterest']
            pct_away = abs(price - strike) / price * 100
            
            if pct_away <= proximity_pct:
                results.append({
                    'type': 'PUT',
                    'strike': strike,
                    'oi': int(oi),
                    'pct_away': round(pct_away, 2),
                    'position': 'ABOVE' if strike > price else 'BELOW'
                })
        
        if results:
            # Find the highest OI wall
            max_oi_wall = max(results, key=lambda x: x['oi'])
            return {
                'ticker': ticker,
                'price': price,
                'expiration': next_exp,
                'walls': results,
                'max_wall': max_oi_wall,
                'total_nearby_oi': sum(r['oi'] for r in results)
            }
        
        return None
        
    except Exception as e:
        print(f"  [{ticker}] Error: {e}")
        return None


def run_gamma_scan(proximity_pct: float = 2.0, min_oi: int = 1000):
    """Run the full gamma scan."""
    print(f"\n{'='*60}")
    print(f"GAMMA SCAN - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Proximity: {proximity_pct}% | Min OI: {min_oi:,}")
    print(f"{'='*60}\n")
    
    # Step 1: Get candidates
    candidates = get_stacked_ema_candidates()
    
    if candidates.empty:
        print("No candidates found!")
        return
    
    # Step 2: Check each for gamma proximity
    gamma_hits = []
    
    for i, row in candidates.iterrows():
        ticker = row['name'].replace('.', '-')  # Yahoo format
        price = row['close']
        
        print(f"[{i+1}/{len(candidates)}] Checking {ticker} @ ${price:.2f}...", end='')
        
        result = check_gamma_proximity(ticker, price, proximity_pct, min_oi)
        
        if result:
            print(f" ✓ {len(result['walls'])} walls found!")
            gamma_hits.append(result)
        else:
            print(" -")
    
    # Step 3: Display results
    print(f"\n{'='*60}")
    print(f"RESULTS: {len(gamma_hits)} stocks near gamma walls")
    print(f"{'='*60}\n")
    
    if gamma_hits:
        # Sort by total nearby OI
        gamma_hits.sort(key=lambda x: x['total_nearby_oi'], reverse=True)
        
        for hit in gamma_hits:
            print(f"\n{hit['ticker']} @ ${hit['price']:.2f} (Exp: {hit['expiration']})")
            print(f"  Total Nearby OI: {hit['total_nearby_oi']:,}")
            for wall in sorted(hit['walls'], key=lambda x: -x['oi']):
                direction = "↑" if wall['position'] == 'ABOVE' else "↓"
                print(f"    {direction} {wall['type']} ${wall['strike']} - OI: {wall['oi']:,} ({wall['pct_away']}% away)")
    
    return gamma_hits


if __name__ == "__main__":
    results = run_gamma_scan(proximity_pct=2.0, min_oi=1000)
