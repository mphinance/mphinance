#!/usr/bin/env python3
"""
Batch Scanner Template - Run screening strategies and export to Google Sheets

This is a template/example. Customize STRATEGIES list with your own strategy classes.

Usage:
    python batch_scanner_template.py                    # Run all strategies
    python batch_scanner_template.py --strategies "Strategy A,Strategy B"
    python batch_scanner_template.py --dry-run          # Print results, don't send
    
Cron Example (daily at 4pm):
    0 16 * * 1-5 cd /path/to/project && .venv/bin/python batch_scanner_template.py >> logs/batch.log 2>&1
"""

import os
import sys
import json
import argparse
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
SHEETS_WEBHOOK = os.getenv("GOOGLE_SHEETS_WEBHOOK", "")

# =============================================================================
# STRATEGIES - Add your own or use the MEME Screen example
# =============================================================================
# Each strategy should be a dict with:
#   - name: Display name
#   - query_fn: Function that returns a pandas DataFrame of results
#   - priority_cols: List of columns to show first in Sheets (optional)

def meme_screen():
    """
    MEME Screen - Top 30 stocks by Implied Volatility from top 200 by volume.
    Mimics the MEME ETF methodology.
    """
    from tradingview_screener import Query, col
    import yfinance as yf
    import concurrent.futures
    
    print("  → Fetching top 200 by volume...")
    
    # Step 1: Get top 200 stocks by volume
    query = (
        Query()
        .select('name', 'description', 'close', 'change', 'volume', 'market_cap_basic', 'sector')
        .where(
            col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
            col('type') == 'stock',
            col('is_primary') == True,
            col('close') > 1.0,
            col('volume') > 1_000_000
        )
        .order_by('volume', ascending=False)
        .limit(200)
    )
    count, df = query.get_scanner_data()
    
    if df.empty:
        return df
    
    print(f"  → Got {len(df)} candidates, fetching IV...")
    
    # Step 2: Fetch IV for each ticker
    def get_iv(ticker):
        try:
            tk = yf.Ticker(ticker.replace('.', '-'))
            exps = tk.options
            if not exps:
                return 0.0
            chain = tk.option_chain(exps[0])
            opts = pd.concat([chain.calls, chain.puts])
            price = tk.fast_info.last_price
            atm = opts[(opts['strike'] >= price * 0.95) & (opts['strike'] <= price * 1.05)]
            return atm['impliedVolatility'].mean() if not atm.empty else 0.0
        except:
            return 0.0
    
    tickers = df['name'].tolist()
    iv_map = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(get_iv, t): t for t in tickers}
        for i, f in enumerate(concurrent.futures.as_completed(futures)):
            iv_map[futures[f]] = f.result()
            if (i + 1) % 50 == 0:
                print(f"  → Processed {i+1}/{len(tickers)}")
    
    df['IV'] = df['name'].map(iv_map)
    df = df.sort_values('IV', ascending=False).head(30)
    df['IV'] = df['IV'].apply(lambda x: f"{x:.2%}")
    
    print(f"  → Top 30 by IV selected")
    return df


STRATEGIES = [
    {
        "name": "MEME Screen",
        "query_fn": meme_screen,
        "priority_cols": ["close", "IV", "volume", "sector", "change", "market_cap_basic"],
    },
    # Add more strategies here:
    # {
    #     "name": "My Custom Strategy",
    #     "query_fn": my_custom_function,
    #     "priority_cols": ["close", "volume"],
    # },
]

# Columns to exclude from Sheets output (noise)
EXCLUDE_COLS = ['type', 'is_primary']

# =============================================================================
# Core Functions (no changes needed below)
# =============================================================================

def run_strategy(strategy: dict) -> pd.DataFrame:
    """Run a single strategy and return results DataFrame."""
    name = strategy["name"]
    print(f"\n{'='*60}")
    print(f"📊 Running: {name}")
    print(f"{'='*60}")
    
    try:
        df = strategy["query_fn"]()
        print(f"  → Results: {len(df)}")
        return df
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return pd.DataFrame()


def send_to_sheets(df: pd.DataFrame, strategy: dict) -> bool:
    """Send results to Google Sheets."""
    if not SHEETS_WEBHOOK:
        print("  ⚠️ GOOGLE_SHEETS_WEBHOOK not configured in .env")
        return False
    
    if df.empty:
        print("  → No data to send")
        return True
    
    name = strategy["name"]
    priority_cols = strategy.get("priority_cols", [])
    
    # Calculate week ending
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    week_ending = today + timedelta(days=days_until_sunday) if days_until_sunday > 0 else today
    week_ending_str = week_ending.strftime('%Y-%m-%d')
    
    # Build ordered columns
    ordered_cols = [c for c in priority_cols if c in df.columns]
    for c in df.columns:
        if c not in ordered_cols and c not in ['name', 'description'] and c not in EXCLUDE_COLS:
            ordered_cols.append(c)
    
    # Build payload
    sheets_data = []
    for _, row in df.iterrows():
        record = {
            'Symbol': str(row.get('name', '')),
            'Company': str(row.get('description', ''))[:50],
            'WeekEnding': week_ending_str,
        }
        
        for col in ordered_cols:
            val = row[col]
            if pd.isna(val):
                record[col] = ''
            elif isinstance(val, float):
                record[col] = round(val, 4) if abs(val) < 1000000 else f"{val:.0f}"
            else:
                record[col] = str(val)
        
        sheets_data.append(record)
    
    payload = {
        "data": sheets_data,
        "timestamp": datetime.now().isoformat(),
        "strategy": name
    }
    
    try:
        resp = requests.post(SHEETS_WEBHOOK, json=payload, timeout=30)
        if resp.status_code == 200:
            print(f"  ✅ Sent {len(sheets_data)} rows to Sheets")
            return True
        else:
            print(f"  ❌ Sheets error: {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Sheets exception: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Batch Scanner")
    parser.add_argument("--strategies", type=str, help="Comma-separated strategy names")
    parser.add_argument("--dry-run", action="store_true", help="Don't send to Sheets")
    parser.add_argument("--list", action="store_true", help="List available strategies")
    args = parser.parse_args()
    
    if args.list:
        print("Available strategies:")
        for s in STRATEGIES:
            print(f"  - {s['name']}")
        return
    
    # Filter strategies if specified
    if args.strategies:
        names = [n.strip() for n in args.strategies.split(",")]
        strategies_to_run = [s for s in STRATEGIES if s["name"] in names]
    else:
        strategies_to_run = STRATEGIES
    
    print(f"\n🚀 Batch Scanner Started: {datetime.now().isoformat()}")
    print(f"   Strategies: {len(strategies_to_run)}")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    
    results_summary = {}
    
    for strategy in strategies_to_run:
        df = run_strategy(strategy)
        results_summary[strategy["name"]] = len(df)
        
        if not df.empty:
            if args.dry_run:
                print(f"\n  [DRY RUN] Would send {len(df)} rows")
                print(df.head(5).to_string())
            else:
                send_to_sheets(df, strategy)
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 SUMMARY")
    print(f"{'='*60}")
    for name, count in results_summary.items():
        status = "✅" if count > 0 else "○"
        print(f"  {status} {name}: {count} results")
    
    print(f"\n✓ Completed at {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
