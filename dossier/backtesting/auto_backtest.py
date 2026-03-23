"""
Auto-Backtest — Track forward returns for daily momentum picks.

Reads today's picks from docs/api/daily-picks.json, appends to the
rolling track record, then validates older picks by fetching actual
prices from Yahoo Finance.

Called by generate.py during the pipeline (Stage 15d).
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

# Use relative path from file location — works in CI and locally
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DAILY_PICKS_PATH = PROJECT_ROOT / "docs" / "api" / "daily-picks.json"
TRACK_RECORD_PATH = PROJECT_ROOT / "docs" / "backtesting" / "track_record.json"


def load_track_record():
    if TRACK_RECORD_PATH.exists():
        with open(TRACK_RECORD_PATH, 'r') as f:
            return json.load(f)
    return {"entries": [], "stats": {}}


def save_track_record(data):
    TRACK_RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACK_RECORD_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def update_entry_returns(entry):
    """Fetch forward returns for a single pick entry."""
    ticker = entry['ticker']
    scan_date_str = entry['date']

    try:
        import yfinance as yf
        import pandas as pd

        scan_date = pd.to_datetime(scan_date_str)
        end_date = scan_date + timedelta(days=45)

        hist = yf.download(ticker, start=scan_date, end=end_date, interval='1d', progress=False)
        if hist.empty:
            return entry

        prices = hist['Close']
        if prices.empty:
            return entry

        # Use entry_price if available, otherwise first close
        entry_price = entry.get('entry_price', 0)
        if entry_price <= 0:
            entry_price = float(prices.iloc[0])
            entry['entry_price'] = round(entry_price, 2)

        # Calculate returns for 1d, 5d, 10d, 21d
        days_to_check = {1: 'fwd_1d', 5: 'fwd_5d', 10: 'fwd_10d', 21: 'fwd_21d'}
        for d, key in days_to_check.items():
            if len(prices) > d:
                exit_price = float(prices.iloc[d])
                ret = (exit_price - entry_price) / entry_price * 100
                entry[key] = round(ret, 2)

    except Exception as e:
        print(f"  [WARN] Forward return fetch failed for {ticker} on {scan_date_str}: {e}")

    return entry


def recalculate_stats(track_record):
    """Recompute aggregate stats from validated entries."""
    entries = track_record['entries']
    validated = [e for e in entries if 'fwd_5d' in e]

    if not validated:
        track_record['stats'] = {
            "total_picks_tracked": len(entries),
            "total_validated": 0,
            "win_rate_5d": 0,
            "avg_5d_return": 0,
            "avg_1d_return": 0,
            "sharpe_5d": 0,
            "best_pick": None,
            "worst_pick": None,
        }
        return track_record

    import math

    fwd_5d_returns = [e['fwd_5d'] for e in validated]
    fwd_1d_returns = [e['fwd_1d'] for e in validated if 'fwd_1d' in e]

    avg_5d = sum(fwd_5d_returns) / len(fwd_5d_returns)
    avg_1d = sum(fwd_1d_returns) / len(fwd_1d_returns) if fwd_1d_returns else 0
    win_rate = len([r for r in fwd_5d_returns if r > 0]) / len(fwd_5d_returns) * 100

    best_pick = max(validated, key=lambda x: x['fwd_5d'])
    worst_pick = min(validated, key=lambda x: x['fwd_5d'])

    # Sharpe-like ratio (annualized from 5-day returns)
    if len(fwd_5d_returns) > 1:
        variance = sum((r - avg_5d) ** 2 for r in fwd_5d_returns) / (len(fwd_5d_returns) - 1)
        std_5d = math.sqrt(variance) if variance > 0 else 1
        sharpe = round((avg_5d / std_5d) * math.sqrt(252 / 5), 2)
    else:
        sharpe = 0

    track_record['stats'] = {
        "total_picks_tracked": len(entries),
        "total_validated": len(validated),
        "win_rate_5d": round(win_rate, 1),
        "avg_5d_return": round(avg_5d, 2),
        "avg_1d_return": round(avg_1d, 2),
        "sharpe_5d": sharpe,
        "best_pick": {"ticker": best_pick['ticker'], "date": best_pick['date'], "return": best_pick['fwd_5d']},
        "worst_pick": {"ticker": worst_pick['ticker'], "date": worst_pick['date'], "return": worst_pick['fwd_5d']},
    }

    return track_record


def main():
    print("  Loading track record...")
    track_record = load_track_record()

    # 1. Append today's picks (with actual prices!)
    if DAILY_PICKS_PATH.exists():
        with open(DAILY_PICKS_PATH, 'r') as f:
            daily_data = json.load(f)
            today_date = daily_data.get('date', '')

            existing_pairs = {(e['ticker'], e['date']) for e in track_record['entries']}

            for pick in daily_data.get('picks', [])[:10]:
                pair = (pick['ticker'], today_date)
                if pair not in existing_pairs:
                    track_record['entries'].append({
                        "date": today_date,
                        "ticker": pick['ticker'],
                        "score": pick.get('score', 0),
                        "grade": pick.get('grade', ''),
                        "medal": pick.get('medal', ''),
                        "entry_price": pick.get('price', 0),  # <-- ACTUAL PRICE
                        "ema_stack": pick.get('ema_stack', ''),
                        "is_pullback": pick.get('is_pullback_setup', False),
                    })

    # 2. Update returns for older entries that haven't been validated yet
    today = datetime.now()
    to_update = []
    for i, entry in enumerate(track_record['entries']):
        if 'fwd_5d' not in entry:
            try:
                scan_date = datetime.strptime(entry['date'], "%Y-%m-%d")
                if (today - scan_date).days >= 7:
                    to_update.append(i)
            except ValueError:
                continue

    if to_update:
        print(f"  Updating returns for {len(to_update)} entries...")
        for i in to_update:
            track_record['entries'][i] = update_entry_returns(track_record['entries'][i])
            time.sleep(0.5)  # Rate limit

    # 3. Recalculate stats
    print("  Recalculating stats...")
    track_record = recalculate_stats(track_record)

    # 4. Save
    save_track_record(track_record)
    print(f"  ✓ Track record saved: {len(track_record['entries'])} entries")
    stats = track_record.get('stats', {})
    if stats.get('total_validated', 0) > 0:
        print(f"    Win rate: {stats['win_rate_5d']}% | Avg 5d: {stats['avg_5d_return']}%")
        print(f"    Sharpe (5d): {stats['sharpe_5d']}")
    else:
        print(f"    No validated entries yet ({stats.get('total_picks_tracked', 0)} tracked, awaiting 7+ days)")


if __name__ == "__main__":
    main()
