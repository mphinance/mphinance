#!/usr/bin/env python3
"""
📊 Up/Down Volume Screener — who's actually buying the shares (accumulation tape)

The IBD-style Up/Down Volume Ratio: total volume on up-close days divided by total
volume on down-close days over the last 50 sessions. Above 1.0 means more shares
changed hands on the way up than the way down. Institutions can't hide size, so a
persistent 1.5+ ratio in a name that's holding its trend is accumulation showing in
the tape.

Different from the other volume screens in the dossier:
  - OBV divergence: cumulative-flow slope vs price (reversal tell)
  - Pocket pivot: single-bar volume vs the biggest down-day volume
  - Volume dry-up: volume contracting inside a base
  - THIS: the 50-day ratio of up-volume to down-volume, plus whether the last
    20 days are accelerating and how many heavy-volume accumulation days printed

Qualifies when:
    50-day U/D volume ratio >= _MIN_RATIO, close above the 50-day SMA,
    and close within _MAX_OFF_HIGH of the 52-week high.

Scoring (0-100):
    Ratio        (40 pts) — 50-day up/down volume ratio
    Acceleration (20 pts) — 20-day ratio vs the 50-day ratio
    Trend        (15 pts) — price vs 50/200-day SMAs
    Highs        (15 pts) — distance under the 52-week high
    Heavy days   (10 pts) — net count of heavy-volume up days minus heavy down days (25d)

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.updown_volume_screener --tickers NVDA,AAPL
    python -m dossier.updown_volume_screener --json --no-save

Output: docs/api/updown-volume-screener.json (served via GitHub Pages)

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

_RATIO_WINDOW = 50
_RECENT_WINDOW = 20
_HEAVY_WINDOW = 25
_HEAVY_MULT = 1.5          # a "heavy" day trades 1.5x the 50-day average volume
_MIN_RATIO = 1.3
_MAX_OFF_HIGH = 0.15       # within 15% of the 52-week high
_MIN_ROWS = 210
_REQUIRED_COLS = ("Close", "Volume")
_RATIO_CAP = 99.0          # all-up-volume windows would divide by zero


def updown_ratio(close: "pd.Series", volume: "pd.Series", window: int) -> float | None:
    """Up-day volume / down-day volume over the last `window` bars (flat days ignored).
    None when the window has no down volume at all and no up volume either."""
    delta = close.diff().iloc[-window:]
    vol = volume.iloc[-window:]
    up = float(vol[delta > 0].sum())
    down = float(vol[delta < 0].sum())
    if down <= 0:
        return _RATIO_CAP if up > 0 else None
    return min(up / down, _RATIO_CAP)


def heavy_day_balance(close: "pd.Series", volume: "pd.Series") -> int:
    """Heavy-volume up days minus heavy-volume down days over the last _HEAVY_WINDOW bars."""
    avg_vol = volume.rolling(_RATIO_WINDOW).mean().shift(1)
    heavy = volume > avg_vol * _HEAVY_MULT
    delta = close.diff()
    recent = slice(-_HEAVY_WINDOW, None)
    ups = int((heavy & (delta > 0)).iloc[recent].sum())
    downs = int((heavy & (delta < 0)).iloc[recent].sum())
    return ups - downs


def _ratio_score(r: float) -> int:
    if r >= 2.5:
        return 40
    if r >= 2.0:
        return 32
    if r >= 1.6:
        return 24
    return 16


def _accel_score(recent: float, base: float) -> int:
    if recent >= base and recent >= 1.5:
        return 20
    if recent >= 1.2:
        return 12
    return 4


def _trend_score(close: float, sma50: float, sma200: float) -> int:
    if close > sma50 > sma200:
        return 15
    if close > sma50:
        return 9
    return 0


def _highs_score(off_high: float) -> int:
    if off_high <= 0.03:
        return 15
    if off_high <= 0.08:
        return 10
    return 5


def _heavy_score(balance: int) -> int:
    if balance >= 4:
        return 10
    if balance >= 2:
        return 6
    return 2


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


def score_updown_volume(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None unless accumulation qualifies.
    `hist` may be injected (tests); otherwise fetched from yfinance."""
    if hist is None:
        try:
            hist = yf.Ticker(ticker).history(period="1y", interval="1d")
        except Exception:
            return None
    ok, _ = check_yfinance_history(hist, ticker, min_rows=_MIN_ROWS)
    if not ok or any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    hist = hist.dropna(subset=list(_REQUIRED_COLS))
    if len(hist) < _MIN_ROWS:
        return None

    close, volume = hist["Close"], hist["Volume"]
    ratio50 = updown_ratio(close, volume, _RATIO_WINDOW)
    ratio20 = updown_ratio(close, volume, _RECENT_WINDOW)
    if ratio50 is None or ratio20 is None or ratio50 < _MIN_RATIO:
        return None

    last = float(close.iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1])
    high52 = float(close.iloc[-252:].max())
    if last <= sma50 or high52 <= 0:
        return None
    off_high = max(0.0, (high52 - last) / high52)
    if off_high > _MAX_OFF_HIGH:
        return None

    balance = heavy_day_balance(close, volume)
    s_ratio = _ratio_score(ratio50)
    s_accel = _accel_score(ratio20, ratio50)
    s_trend = _trend_score(last, sma50, sma200)
    s_highs = _highs_score(off_high)
    s_heavy = _heavy_score(balance)
    total = s_ratio + s_accel + s_trend + s_highs + s_heavy

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "updown_ratio_50d": round(ratio50, 2),
        "updown_ratio_20d": round(ratio20, 2),
        "accelerating": ratio20 >= ratio50,
        "heavy_day_balance_25d": balance,
        "off_52w_high_pct": round(off_high * 100, 1),
        "pct_above_sma50": round((last / sma50 - 1) * 100, 1),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "ratio": s_ratio,
            "acceleration": s_accel,
            "trend": s_trend,
            "highs": s_highs,
            "heavy_days": s_heavy,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/updown-volume-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "updown-volume-screener.json"
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
    parser = argparse.ArgumentParser(description="Up/Down Volume Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
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
        r = score_updown_volume(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n📊  Up/Down Volume — {len(results)} accumulation names of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"U/D 50d {r['updown_ratio_50d']:.2f}, 20d {r['updown_ratio_20d']:.2f}, "
            f"{r['off_52w_high_pct']:.1f}% off high  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
