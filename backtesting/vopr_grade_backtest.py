import glob
import re
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import Counter

import yfinance as yf
import pandas as pd
from tqdm import tqdm

# Journal-cache so a mid-run failure doesn't nuke already-fetched OHLC.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_cache import FetchCache, cached_fetch_map

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Prefer the VPS layout, but fall back to a path relative to this file so the
# backtest (and its tests) run anywhere — CI, a fresh clone, another machine.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
_VPS_BASE = "/home/mph/Antigravity/mphinance/backtesting"

BASE_DIR = os.environ.get("MPH_BACKTEST_DIR") or (
    _VPS_BASE if os.path.isdir(os.path.dirname(_VPS_BASE)) else _SCRIPT_DIR
)
REPORTS_DIR = os.environ.get("MPH_REPORTS_DIR") or os.path.join(
    os.path.dirname(BASE_DIR), "docs", "reports"
)
RESULTS_DIR = f"{BASE_DIR}/results"
CACHE_DIR = f"{RESULTS_DIR}/cache"
os.makedirs(RESULTS_DIR, exist_ok=True)

PER_SIGNAL_OUT = f"{RESULTS_DIR}/vopr_per_signal.csv"
SUMMARY_OUT = f"{RESULTS_DIR}/vopr_summary.json"

# Set MPH_FETCH_CACHE=0 to bypass the cache; TTL keeps day-old bars from being
# silently reused by a fresh run while still giving full intra-run resume.
FETCH_CACHE_ENABLED = os.environ.get("MPH_FETCH_CACHE", "1") != "0"
FETCH_CACHE_TTL_SECONDS = float(os.environ.get("MPH_FETCH_CACHE_TTL", 12 * 3600))

# Days to hold the simulated Cash Secured Put (CSP)
HOLD_TIME_DAYS = 15

def parse_dossiers() -> List[Dict[str, Any]]:
    """Parse markdown files to extract VoPR setups."""
    signals = []
    files = glob.glob(f"{REPORTS_DIR}/*_alpha_dossier.md")
    
    ticker_pattern = re.compile(r"### \[(.*?)\]")
    price_grade_pattern = re.compile(r"\*\*\$([\d\.]+)\*\* \| Grade: ([A-F]) \|")
    s1_pattern = re.compile(r"S1: \$([\d\.]+)")
    
    for f_path in files:
        basename = os.path.basename(f_path)
        date_str = basename.split("_")[0]
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
            
        with open(f_path, "r") as f:
            lines = f.readlines()
            
        current_ticker = None
        current_price = None
        current_grade = None
        
        for line in lines:
            if line.startswith("### ["):
                m = ticker_pattern.search(line)
                if m:
                    current_ticker = m.group(1)
            elif current_ticker and "**$" in line and "Grade:" in line:
                m = price_grade_pattern.search(line)
                if m:
                    current_price = float(m.group(1))
                    current_grade = m.group(2)
            elif current_ticker and "S1: $" in line:
                m = s1_pattern.search(line)
                if m and current_price and current_grade:
                    s1 = float(m.group(1))
                    signals.append({
                        "trade_date": date_str,
                        "signal_time": date_obj,
                        "ticker": current_ticker,
                        "price": current_price,
                        "grade": current_grade,
                        "s1_support": s1
                    })
                    # Reset for next block
                    current_ticker = None
                    current_price = None
                    current_grade = None

    return signals

def _download_data(tickers: List[str], start_date: datetime) -> Dict[str, pd.DataFrame]:
    """Raw network fetch of daily OHLC for the relevant period (no caching)."""
    start_str = (start_date - timedelta(days=5)).strftime("%Y-%m-%d")
    logging.info(f"Fetching data for {len(tickers)} tickers from {start_str}...")

    data = yf.download(
        " ".join(tickers),
        start=start_str,
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=True
    )

    ticker_dfs = {}
    if len(tickers) == 1:
        ticker_dfs[tickers[0]] = data
    else:
        for ticker in tickers:
            if ticker in data.columns.levels[0]:
                df = data[ticker].dropna(subset=["Close"])
                if not df.empty:
                    ticker_dfs[ticker] = df

    return ticker_dfs


def fetch_data(
    tickers: List[str],
    start_date: datetime,
    cache: "FetchCache | None" = None,
) -> Dict[str, pd.DataFrame]:
    """Fetch daily OHLC, reusing any bars already persisted to the cache.

    With a cache, each ticker's frame is stored the moment it's fetched and
    only cache misses hit the network. A crash later in the run (or on a
    re-run) reuses everything already downloaded instead of re-paying for it.
    Without a cache, this is just the raw download.
    """
    if cache is None:
        return _download_data(tickers, start_date)

    # Namespace pins the cache to this fetch window + interval so a different
    # backtest window can't reuse another window's bars.
    start_str = (start_date - timedelta(days=5)).strftime("%Y-%m-%d")
    namespace = f"ohlc:1d:{start_str}"
    return cached_fetch_map(
        tickers,
        lambda missing: _download_data(missing, start_date),
        cache,
        namespace,
    )

def evaluate_trade(signal: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """Simulate a short put sold at S1 support."""
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')
        
    signal_time = signal["signal_time"]
    if signal_time.tzinfo is None:
        from datetime import timezone
        signal_time = signal_time.replace(tzinfo=timezone.utc)
        
    post_signal = df[df.index >= signal_time]
    
    if post_signal.empty:
        return {"outcome": "OPEN", "lowest_low": None, "final_close": None, "win": False}
        
    # Get N trading days
    eval_window = post_signal.head(HOLD_TIME_DAYS)
    
    if len(eval_window) < HOLD_TIME_DAYS and (datetime.now(timezone.utc) - signal_time).days < HOLD_TIME_DAYS:
        # Still open, hasn't reached the N days yet
        return {"outcome": "OPEN", "lowest_low": None, "final_close": None, "win": False}
        
    s1 = signal["s1_support"]
    lowest_low = eval_window["Low"].min()
    
    # We use final close of the evaluation window to determine assignment.
    # If final close >= S1, the put expires worthless (WIN).
    # If final close < S1, we take assignment (LOSS).
    final_close = eval_window.iloc[-1]["Close"]
    
    win = bool(final_close >= s1)
    outcome = "WIN" if win else "LOSS"
    
    # For reporting, also calculate the drawdown below S1
    max_drawdown_pct = min(0, (lowest_low - s1) / s1) * 100
    
    return {
        "outcome": outcome,
        "win": win,
        "lowest_low": float(lowest_low),
        "final_close": float(final_close),
        "max_drawdown_pct": float(max_drawdown_pct)
    }

def main():
    signals = parse_dossiers()
    logging.info(f"Extracted {len(signals)} graded setups from dossiers.")
    
    if not signals:
        return
        
    earliest_time = min(s["signal_time"] for s in signals)
    tickers = list(set(s["ticker"] for s in signals))
    
    cache = (
        FetchCache(CACHE_DIR, max_age_seconds=FETCH_CACHE_TTL_SECONDS)
        if FETCH_CACHE_ENABLED
        else None
    )

    results = []
    chunk_size = 50
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]

    for chunk in tqdm(ticker_chunks, desc="Fetching data and evaluating"):
        data_dict = fetch_data(chunk, earliest_time, cache=cache)
        
        chunk_signals = [s for s in signals if s["ticker"] in chunk]
        for sig in chunk_signals:
            ticker = sig["ticker"]
            if ticker not in data_dict:
                sig.update({"outcome": "ERROR_NO_DATA", "win": False, "lowest_low": None, "final_close": None, "max_drawdown_pct": 0.0})
                results.append(sig)
                continue
                
            res = evaluate_trade(sig, data_dict[ticker])
            sig.update(res)
            sig["signal_time"] = sig["signal_time"].isoformat()
            results.append(sig)
            
    completed = [r for r in results if r["outcome"] in ["WIN", "LOSS"]]
    
    grade_stats = {}
    for grade in ["A", "B", "C", "D", "F"]:
        grade_trades = [r for r in completed if r["grade"] == grade]
        if not grade_trades:
            continue
            
        wins = sum(1 for r in grade_trades if r["win"])
        win_rate = wins / len(grade_trades)
        avg_drawdown = sum(r["max_drawdown_pct"] for r in grade_trades) / len(grade_trades)
        
        grade_stats[grade] = {
            "total": len(grade_trades),
            "wins": wins,
            "losses": len(grade_trades) - wins,
            "win_rate_pct": round(win_rate * 100, 2),
            "avg_max_drawdown_pct": round(avg_drawdown, 2)
        }
        
    summary = {
        "total_signals": len(signals),
        "completed_trades": len(completed),
        "hold_time_days": HOLD_TIME_DAYS,
        "grade_performance": grade_stats
    }
    
    with open(SUMMARY_OUT, "w") as f:
        json.dump(summary, f, indent=2)
        
    df_results = pd.DataFrame(results)
    df_results.to_csv(PER_SIGNAL_OUT, index=False)
    
    logging.info("VoPR backtest complete!")
    for g, stats in grade_stats.items():
        logging.info(f"Grade {g}: {stats['win_rate_pct']}% WR (N={stats['total']}) | Avg Drawdown: {stats['avg_max_drawdown_pct']}%")
        
if __name__ == "__main__":
    main()
