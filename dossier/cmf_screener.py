#!/usr/bin/env python3
"""
💧 CMF Accumulation Screener — Chaikin Money Flow says buyers are loading quietly

Chaikin Money Flow (20) weights each session's volume by where the close landed in
the day's range, then sums over 20 sessions. Sustained readings above +0.10 mean
closes keep landing near the highs on real volume: accumulation. The interesting
case is when that buying has NOT yet shown up as a breakout, so price is still
sitting in a base. Unlike OBV divergence (cumulative, direction only) CMF is bounded
(-1..+1) and comparable across tickers.

Qualifies when:
    CMF(20) >= _MIN_CMF, price above its 200-day SMA, and price within
    _MAX_BELOW_HIGH % of its 20-day high (a base, not a crash).

Scoring (0-100):
    Level      (35 pts) — CMF(20) strength
    Persistence(25 pts) — of the last 10 sessions, how many had CMF > 0
    Rising     (20 pts) — CMF now vs 10 sessions ago
    Base       (20 pts) — tight to the 20-day high but not yet through it

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.cmf_screener --tickers NVDA,AAPL
    python -m dossier.cmf_screener --json --no-save

Output: docs/api/cmf-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
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

_PERIOD = 20
_MIN_CMF = 0.10
_MAX_BELOW_HIGH = 8.0
_MIN_ROWS = 210
_REQUIRED_COLS = ("High", "Low", "Close", "Volume")


def cmf_series(df: "pd.DataFrame", period: int = _PERIOD) -> "pd.Series":
    """Chaikin Money Flow per bar. Zero-range bars contribute no money flow."""
    high, low, close, vol = (df[c].astype(float) for c in _REQUIRED_COLS)
    rng = (high - low).replace(0, np.nan)
    mfm = (((close - low) - (high - close)) / rng).fillna(0.0)
    vol_sum = vol.rolling(period).sum().replace(0, np.nan)
    return (mfm * vol).rolling(period).sum() / vol_sum


def _level_score(cmf: float) -> int:
    if cmf >= 0.30:
        return 35
    if cmf >= 0.20:
        return 28
    if cmf >= 0.15:
        return 21
    return 14


def _persist_score(pos_days: int) -> int:
    return round(25 * pos_days / 10)


def _rising_score(delta: float) -> int:
    if delta >= 0.10:
        return 20
    if delta >= 0.0:
        return 12
    if delta >= -0.05:
        return 6
    return 0


def _base_score(below_high_pct: float) -> int:
    if below_high_pct <= 2:
        return 20
    if below_high_pct <= 4:
        return 15
    return 8


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


def score_cmf(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None unless it qualifies as quiet accumulation.
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

    cmf = cmf_series(hist).dropna()
    if len(cmf) < 11:
        return None
    now = float(cmf.iloc[-1])
    if now < _MIN_CMF:
        return None

    close = hist["Close"].astype(float)
    last = float(close.iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1])
    high20 = float(hist["High"].astype(float).iloc[-20:].max())
    if last <= 0 or last < sma200 or high20 <= 0:
        return None
    below_high = (high20 - last) / high20 * 100
    if below_high > _MAX_BELOW_HIGH:
        return None

    pos_days = int((cmf.iloc[-10:] > 0).sum())
    delta = now - float(cmf.iloc[-11])
    s_level, s_persist = _level_score(now), _persist_score(pos_days)
    s_rise, s_base = _rising_score(delta), _base_score(below_high)
    total = s_level + s_persist + s_rise + s_base

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "cmf": round(now, 3),
        "cmf_change_10d": round(delta, 3),
        "positive_days_10d": pos_days,
        "below_20d_high_pct": round(below_high, 1),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "level": s_level,
            "persistence": s_persist,
            "rising": s_rise,
            "base": s_base,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/cmf-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "cmf-screener.json"
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
    parser = argparse.ArgumentParser(description="CMF Accumulation Screener")
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
        r = score_cmf(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n💧  CMF Accumulation — {len(results)} of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"CMF {r['cmf']:+.2f} ({r['positive_days_10d']}/10 up days), "
            f"{r['below_20d_high_pct']:.1f}% off 20d high  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
