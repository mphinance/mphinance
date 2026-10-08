#!/usr/bin/env python3
"""
🗜️ TTM Squeeze Screener — Bollinger Bands Compressed Inside Keltner Channels

The squeeze is on when the Bollinger Bands (20, 2 std) sit entirely inside the
Keltner Channels (20, 1.5 ATR): realized volatility has dropped below the
range-based "normal", the market is coiled, and a directional expansion is
usually close. The screen reports two states:

  squeezing → squeeze is on right now (how long, how tight, which way momentum leans)
  fired     → squeeze released within the last _FIRE_WINDOW bars after a real build-up

Different from the other dossier screens:
  - NR7 / Tight Closes / VCP: price-range contraction patterns
  - THIS: volatility-regime contraction (bands vs channels), with a duration
    clock and a momentum lean, so "coiled for 18 bars, leaning up" is a data point

Detection (pure yfinance history):
    Squeeze on → BB upper < KC upper AND BB lower > KC lower
    Duration   → consecutive squeeze-on bars ending at the latest bar
                 (for "fired": the run that ended just before release)
    Momentum   → close minus the average of the 20-bar Donchian midline and SMA20

Scoring (0-100):
    Duration   (30 pts) — longer coil, more stored energy
    Tightness  (25 pts) — BB width / KC width, lower is tighter
    Momentum   (25 pts) — positive and rising lean
    Trend      (20 pts) — close above SMA50 and SMA200

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.ttm_squeeze_screener --tickers NVDA,AAPL
    python -m dossier.ttm_squeeze_screener --json --no-save

Output: docs/api/ttm-squeeze-screener.json (served via GitHub Pages)

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

_LEN = 20
_KC_MULT = 1.5
_FIRE_WINDOW = 3           # bars since release still counted as "fired"
_MIN_FIRED_DURATION = 5    # a release only matters after a real build-up
_MIN_SQUEEZE_BARS = 3      # ignore one-bar blips
_MIN_ROWS = 210
_REQUIRED_COLS = ("High", "Low", "Close")


def squeeze_series(hist: "pd.DataFrame") -> tuple["pd.Series", "pd.Series"]:
    """Return (squeeze_on bool series, BB width / KC width ratio series)."""
    close, high, low = hist["Close"], hist["High"], hist["Low"]
    sma = close.rolling(_LEN).mean()
    std = close.rolling(_LEN).std(ddof=0)
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.rolling(_LEN).mean()
    bb_half, kc_half = 2 * std, _KC_MULT * atr
    on = (bb_half < kc_half) & kc_half.notna()
    ratio = bb_half / kc_half.where(kc_half > 0)
    return on, ratio


def _run_length(flags: list[bool]) -> int:
    """Consecutive True values ending at the last element."""
    n = 0
    for f in reversed(flags):
        if not f:
            break
        n += 1
    return n


def _momentum(hist: "pd.DataFrame") -> "pd.Series":
    mid = (hist["High"].rolling(_LEN).max() + hist["Low"].rolling(_LEN).min()) / 2
    return hist["Close"] - (mid + hist["Close"].rolling(_LEN).mean()) / 2


def _duration_score(bars: int) -> int:
    if bars >= 20:
        return 30
    if bars >= 12:
        return 24
    if bars >= 6:
        return 16
    return 8 if bars >= _MIN_SQUEEZE_BARS else 0


def _tightness_score(ratio: float) -> int:
    if ratio <= 0.55:
        return 25
    if ratio <= 0.7:
        return 19
    if ratio <= 0.85:
        return 12
    return 5


def _momentum_score(mom: float, mom_prev: float) -> int:
    pts = 0
    if mom > 0:
        pts += 15
    if mom > mom_prev:
        pts += 10
    return pts


def _trend_score(above_50: bool, above_200: bool) -> int:
    return (10 if above_50 else 0) + (10 if above_200 else 0)


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


def score_ttm_squeeze(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; None unless a squeeze is on or just fired.
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

    on, ratio = squeeze_series(hist)
    flags = [bool(x) for x in on.tolist()]

    if flags[-1]:
        state, bars, since = "squeezing", _run_length(flags), 0
    else:
        since = _run_length([not f for f in flags])
        if since > _FIRE_WINDOW:
            return None
        state, bars = "fired", _run_length(flags[: len(flags) - since])
        if bars < _MIN_FIRED_DURATION:
            return None
    if state == "squeezing" and bars < _MIN_SQUEEZE_BARS:
        return None

    close = hist["Close"]
    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1]
    mom = _momentum(hist)
    m_now, m_prev = float(mom.iloc[-1]), float(mom.iloc[-2])
    r = ratio.iloc[-1 - since]
    if pd.isna(sma50) or pd.isna(sma200) or pd.isna(m_now) or pd.isna(m_prev) or pd.isna(r):
        return None
    last = float(close.iloc[-1])

    s_dur = _duration_score(bars)
    s_tight = _tightness_score(float(r))
    s_mom = _momentum_score(m_now, m_prev)
    s_trend = _trend_score(last > float(sma50), last > float(sma200))
    total = s_dur + s_tight + s_mom + s_trend

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "state": state,
        "squeeze_bars": bars,
        "bars_since_fire": since,
        "bb_kc_ratio": round(float(r), 2),
        "momentum_lean": "up" if m_now > 0 else "down",
        "momentum_rising": m_now > m_prev,
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "duration": s_dur,
            "tightness": s_tight,
            "momentum": s_mom,
            "trend": s_trend,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/ttm-squeeze-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ttm-squeeze-screener.json"
    grade_counts: dict[str, int] = {}
    for r in results:
        grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(results),
        "squeezing": sum(1 for r in results if r["state"] == "squeezing"),
        "fired": sum(1 for r in results if r["state"] == "fired"),
        "grade_counts": grade_counts,
        "results": results,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\n  💾  Saved {len(results)} results → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="TTM Squeeze Screener")
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
        r = score_ttm_squeeze(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🗜️  TTM Squeeze — {len(results)} of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"{r['state']} {r['squeeze_bars']} bars, BB/KC {r['bb_kc_ratio']:.2f}, "
            f"leaning {r['momentum_lean']}  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
