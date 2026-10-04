#!/usr/bin/env python3
"""
🪜 Higher Lows Screener — Weekly "Staircase" Uptrends

A staircase trend is one where every weekly low is higher than the one before.
Buyers step in at a higher price each week and never let a dip reach the prior
low. It's the cleanest picture of persistent accumulation, and it's measured
on the LOW, not the close, so a single spike week can't fake it.

Different from the other trend screens in the dossier:
  - Golden Cross / SMA reclaim: moving-average events
  - High52: proximity to the annual high
  - Tight Closes: weekly closes bunched together (a pause)
  - THIS: an unbroken run of rising weekly lows (a climb), plus how shallow
    the dips are and how far the run has carried price

Detection (pure yfinance history):
    Staircase → last N weekly lows (N >= _MIN_STEPS) each strictly above the
                previous week's low; the current partial week is dropped
                so a Monday print can't break the streak
    Uptrend   → latest close above the 21-day EMA and SMA50

Scoring (0-100):
    Streak     (40 pts) — consecutive rising weekly lows
    Shallow    (25 pts) — smaller worst weekly dip (close-to-low) inside the run
    Trend      (20 pts) — above EMA21/SMA50, SMA50 > SMA200
    Cushion    (15 pts) — distance of price above the most recent weekly low
                          (closer = a tighter, lower-risk stop)

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.higher_lows_screener --tickers NVDA,AAPL
    python -m dossier.higher_lows_screener --watchlist
    python -m dossier.higher_lows_screener --json --no-save

Output: docs/api/higher-lows-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("❌  pip install yfinance")
    sys.exit(1)

try:
    from dossier.utils.validate_api import check_yfinance_history
except ImportError:
    def check_yfinance_history(df, ticker, min_rows=2):
        if df is None or df.empty:
            return False, f"{ticker}: empty history"
        if len(df) < min_rows:
            return False, f"{ticker}: only {len(df)} rows"
        return True, ""

PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from dossier.config import CORE_WATCHLIST
except ImportError:
    CORE_WATCHLIST = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD"]

_MIN_STEPS = 4             # rising weekly lows needed to call it a staircase
_REQUIRED_COLS = ("Low", "Close")


def _weekly_lows(hist: "pd.DataFrame") -> "pd.Series":
    """Completed weekly lows. Drops the in-progress week (its low is partial)."""
    weekly = hist["Low"].dropna().resample("W-FRI").min().dropna()
    if len(weekly) and hist.index[-1] < weekly.index[-1]:
        weekly = weekly.iloc[:-1]
    return weekly


def find_staircase(hist: "pd.DataFrame") -> dict | None:
    """
    Count consecutive most-recent weeks whose low beat the prior week's low.
    Returns None if fewer than _MIN_STEPS qualify.
    """
    if any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    lows = _weekly_lows(hist)
    if len(lows) < _MIN_STEPS + 1:
        return None

    steps = 0
    for i in range(len(lows) - 1, 0, -1):
        if float(lows.iloc[i]) > float(lows.iloc[i - 1]):
            steps += 1
        else:
            break
    if steps < _MIN_STEPS:
        return None

    run_start = lows.index[-steps - 1] - pd.Timedelta(days=6)
    run = hist.loc[hist.index >= run_start]
    weekly_close = run["Close"].resample("W-FRI").last().dropna()
    weekly_low = run["Low"].resample("W-FRI").min().dropna()
    dips = ((weekly_close - weekly_low) / weekly_close * 100).clip(lower=0)
    return {
        "steps": steps,
        "worst_dip_pct": float(dips.max()) if len(dips) else 0.0,
        "last_low": float(lows.iloc[-1]),
        "start_low": float(lows.iloc[-steps - 1]),
    }


def _streak_score(steps: int) -> int:
    if steps >= 10:
        return 40
    if steps >= 8:
        return 33
    if steps >= 6:
        return 26
    if steps >= _MIN_STEPS:
        return 18
    return 0


def _shallow_score(worst_dip_pct: float) -> int:
    if worst_dip_pct <= 3:
        return 25
    if worst_dip_pct <= 5:
        return 19
    if worst_dip_pct <= 8:
        return 12
    if worst_dip_pct <= 12:
        return 6
    return 0


def _trend_score(last: float, ema21: float, sma50: float, sma200: float | None) -> int:
    pts = 0
    if last > ema21:
        pts += 8
    if last > sma50:
        pts += 6
    if sma200 is not None and sma50 > sma200:
        pts += 6
    return pts


def _cushion_score(cushion_pct: float) -> int:
    if cushion_pct <= 3:
        return 15
    if cushion_pct <= 6:
        return 11
    if cushion_pct <= 10:
        return 6
    return 0


def _grade(total: int) -> str:
    if total >= 80:
        return "A+"
    if total >= 65:
        return "A"
    if total >= 50:
        return "B"
    if total >= 35:
        return "C"
    return "D"


def score_higher_lows(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None when there's no staircase in an uptrend.
    `hist` may be injected (tests); otherwise fetched from yfinance."""
    if hist is None:
        try:
            hist = yf.Ticker(ticker).history(period="1y", interval="1d")
        except Exception:
            return None
    ok, _ = check_yfinance_history(hist, ticker, min_rows=80)
    if not ok or any(c not in hist.columns for c in _REQUIRED_COLS):
        return None

    stair = find_staircase(hist)
    if stair is None:
        return None

    closes = hist["Close"].dropna()
    last = float(closes.iloc[-1])
    ema21 = float(closes.ewm(span=21, adjust=False).mean().iloc[-1])
    sma50_v = closes.rolling(50).mean().iloc[-1]
    if pd.isna(sma50_v) or last <= ema21 or last <= float(sma50_v):
        return None
    sma50 = float(sma50_v)
    sma200_v = closes.rolling(200).mean().iloc[-1]
    sma200 = None if pd.isna(sma200_v) else float(sma200_v)

    cushion = (last - stair["last_low"]) / last * 100
    s_streak = _streak_score(stair["steps"])
    s_shallow = _shallow_score(stair["worst_dip_pct"])
    s_trend = _trend_score(last, ema21, sma50, sma200)
    s_cushion = _cushion_score(cushion)
    total = s_streak + s_shallow + s_trend + s_cushion

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "rising_weeks": stair["steps"],
        "worst_dip_pct": round(stair["worst_dip_pct"], 1),
        "last_weekly_low": round(stair["last_low"], 2),
        "run_gain_pct": round((last - stair["start_low"]) / stair["start_low"] * 100, 1),
        "cushion_pct": round(cushion, 1),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "streak": s_streak,
            "shallow": s_shallow,
            "trend": s_trend,
            "cushion": s_cushion,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/higher-lows-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "higher-lows-screener.json"
    grade_counts: dict[str, int] = {}
    for r in results:
        grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(results),
        "grade_counts": grade_counts,
        "results": results,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\n  💾  Saved {len(results)} results → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Higher Lows Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    else:
        tickers = list(CORE_WATCHLIST)

    results = []
    for t in tickers:
        r = score_higher_lows(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🪜  Higher Lows — {len(results)} staircases of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"{r['rising_weeks']}w of higher lows (+{r['run_gain_pct']:.1f}%), "
            f"worst dip {r['worst_dip_pct']:.1f}%, stop ref ${r['last_weekly_low']:.2f}  "
            f"Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
