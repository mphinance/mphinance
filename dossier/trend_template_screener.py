#!/usr/bin/env python3
"""
📐 Trend Template Screener — Minervini's Stage 2 checklist, every box ticked

A strict, all-or-nothing trend filter: a name only shows up when ALL of these hold.

    1. Close above the 150-day and 200-day SMA
    2. 150-day SMA above the 200-day SMA
    3. 200-day SMA rising for at least 21 bars (a month)
    4. 50-day SMA above both the 150 and 200
    5. Close above the 50-day SMA
    6. Close at least 30% above the 52-week low
    7. Close within 25% of the 52-week high

Most of the other trend screens key off one signal (a cross, a breakout). This one is
the "is the whole structure healthy" gate, so the survivors are the leadership list.

Scoring (0-100):
    Near high   (30) — distance below the 52-week high (closer is better)
    Off lows    (20) — advance off the 52-week low
    200 slope   (20) — 200-day SMA rise over the last 21 bars
    6-mo return (20) — 126-bar return (rough relative-strength proxy)
    50 slope    (10) — 50-day SMA rising over 10 bars

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.trend_template_screener --tickers NVDA,AAPL
    python -m dossier.trend_template_screener --json --no-save

Output: docs/api/trend-template-screener.json (served via GitHub Pages)

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

_MIN_ROWS = 252            # needs a full year for the 52-week range and 200-SMA slope
_MIN_OFF_LOW = 0.30        # close >= 30% above the 52-week low
_MAX_BELOW_HIGH = 0.25     # close within 25% of the 52-week high
_SLOPE_BARS = 21
_REQUIRED_COLS = ("High", "Low", "Close")


def evaluate_template(hist: "pd.DataFrame") -> dict | None:
    """Return the template metrics if every rule passes, else None."""
    close = hist["Close"]
    sma50 = close.rolling(50).mean()
    sma150 = close.rolling(150).mean()
    sma200 = close.rolling(200).mean()
    last = float(close.iloc[-1])
    s50, s150, s200 = (float(s.iloc[-1]) for s in (sma50, sma150, sma200))
    s200_prior = float(sma200.iloc[-1 - _SLOPE_BARS])
    if any(pd.isna(v) for v in (s50, s150, s200, s200_prior)):
        return None
    window = hist.iloc[-252:]
    hi52, lo52 = float(window["High"].max()), float(window["Low"].min())
    if lo52 <= 0 or hi52 <= 0:
        return None

    off_low = last / lo52 - 1
    below_high = 1 - last / hi52
    passed = (
        last > s150 and last > s200
        and s150 > s200
        and s200 > s200_prior
        and s50 > s150 and s50 > s200
        and last > s50
        and off_low >= _MIN_OFF_LOW
        and below_high <= _MAX_BELOW_HIGH
    )
    if not passed:
        return None
    return {
        "last": last, "sma50": s50, "sma150": s150, "sma200": s200,
        "off_low": off_low, "below_high": below_high,
        "slope200": s200 / s200_prior - 1,
        "slope50": s50 / float(sma50.iloc[-11]) - 1 if not pd.isna(sma50.iloc[-11]) else 0.0,
        "ret_6m": last / float(close.iloc[-127]) - 1,
        "hi52": hi52, "lo52": lo52,
    }


def _near_high_score(below_high: float) -> int:
    if below_high <= 0.03:
        return 30
    if below_high <= 0.08:
        return 22
    if below_high <= 0.15:
        return 14
    return 6


def _off_low_score(off_low: float) -> int:
    if off_low >= 1.0:
        return 20
    if off_low >= 0.6:
        return 15
    return 9


def _slope200_score(slope: float) -> int:
    if slope >= 0.06:
        return 20
    if slope >= 0.03:
        return 14
    return 7


def _return_score(ret: float) -> int:
    if ret >= 0.40:
        return 20
    if ret >= 0.20:
        return 14
    if ret >= 0.05:
        return 8
    return 3


def _slope50_score(slope: float) -> int:
    return 10 if slope > 0.02 else 5 if slope > 0 else 0


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


def score_trend_template(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; None unless it passes the full template.
    `hist` may be injected (tests); otherwise fetched from yfinance."""
    if hist is None:
        try:
            hist = yf.Ticker(ticker).history(period="2y", interval="1d")
        except Exception:
            return None
    ok, _ = check_yfinance_history(hist, ticker, min_rows=_MIN_ROWS)
    if not ok or any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    hist = hist.dropna(subset=list(_REQUIRED_COLS))
    if len(hist) < _MIN_ROWS:
        return None

    m = evaluate_template(hist)
    if m is None:
        return None
    s_high = _near_high_score(m["below_high"])
    s_low = _off_low_score(m["off_low"])
    s_s200 = _slope200_score(m["slope200"])
    s_ret = _return_score(m["ret_6m"])
    s_s50 = _slope50_score(m["slope50"])
    total = s_high + s_low + s_s200 + s_ret + s_s50

    return {
        "ticker": ticker,
        "price": round(m["last"], 2),
        "sma50": round(m["sma50"], 2),
        "sma200": round(m["sma200"], 2),
        "pct_below_52w_high": round(m["below_high"] * 100, 1),
        "pct_above_52w_low": round(m["off_low"] * 100, 1),
        "sma200_slope_pct": round(m["slope200"] * 100, 2),
        "return_6m_pct": round(m["ret_6m"] * 100, 1),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "near_high": s_high,
            "off_lows": s_low,
            "sma200_slope": s_s200,
            "return_6m": s_ret,
            "sma50_slope": s_s50,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/trend-template-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "trend-template-screener.json"
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
    parser = argparse.ArgumentParser(description="Trend Template Screener")
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
        r = score_trend_template(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n📐  Trend Template — {len(results)} pass of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"{r['pct_below_52w_high']:.1f}% off high, +{r['pct_above_52w_low']:.0f}% off low, "
            f"6m {r['return_6m_pct']:+.0f}%  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
