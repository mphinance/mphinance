#!/usr/bin/env python3
"""
🔄 Supertrend Flip Screener — ATR trailing stop just turned bullish

Supertrend(10, 3) is an ATR-based trailing stop that sits under price in an uptrend
and above it in a downtrend. A "flip" is the session close pushes through the upper
band and the stop jumps from overhead to underneath: a volatility-adjusted trend
change signal. Unlike the SMA crosses or Aroon it adapts to each name's own ATR, and
the stop doubles as a ready-made invalidation level (the new support line).

Qualifies when:
    Supertrend flipped from bearish to bullish within the last _FLIP_WINDOW sessions,
    and it is still bullish today.

Scoring (0-100):
    Freshness  (30 pts) — flipped today scores highest
    Risk       (25 pts) — distance from close to the stop (tighter = better R:R)
    Trend      (25 pts) — price vs 50/200-day SMAs
    Volume     (20 pts) — flip-day volume vs 20-day average

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.supertrend_screener --tickers NVDA,AAPL
    python -m dossier.supertrend_screener --json --no-save

Output: docs/api/supertrend-screener.json (served via GitHub Pages)

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

_ATR_PERIOD = 10
_MULT = 3.0
_FLIP_WINDOW = 5
_MIN_ROWS = 210
_REQUIRED_COLS = ("High", "Low", "Close", "Volume")


def supertrend(df: "pd.DataFrame") -> "pd.DataFrame":
    """Supertrend line and direction (+1 bullish / -1 bearish) per bar.
    ATR is Wilder-smoothed; bands ratchet and direction flips on a close through them."""
    high, low, close = df["High"].to_numpy(float), df["Low"].to_numpy(float), df["Close"].to_numpy(float)
    n = len(close)
    prev_close = np.concatenate([[close[0]], close[:-1]])
    tr = np.maximum(high - low, np.maximum(abs(high - prev_close), abs(low - prev_close)))
    atr = pd.Series(tr).ewm(alpha=1 / _ATR_PERIOD, adjust=False, min_periods=_ATR_PERIOD).mean().to_numpy()
    mid = (high + low) / 2
    upper_basic, lower_basic = mid + _MULT * atr, mid - _MULT * atr

    upper, lower = upper_basic.copy(), lower_basic.copy()
    direction = np.ones(n, dtype=int)
    line = np.full(n, np.nan)
    for i in range(1, n):
        if np.isnan(atr[i]):
            continue
        if np.isnan(upper[i - 1]):  # first bar with a usable ATR: seed
            line[i] = lower[i]
            continue
        # ratchet: bands only tighten unless the prior close escaped them
        if not (upper_basic[i] < upper[i - 1] or close[i - 1] > upper[i - 1]):
            upper[i] = upper[i - 1]
        if not (lower_basic[i] > lower[i - 1] or close[i - 1] < lower[i - 1]):
            lower[i] = lower[i - 1]
        if direction[i - 1] == 1:
            direction[i] = -1 if close[i] < lower[i] else 1
        else:
            direction[i] = 1 if close[i] > upper[i] else -1
        line[i] = lower[i] if direction[i] == 1 else upper[i]
    return pd.DataFrame({"line": line, "direction": direction}, index=df.index)


def sessions_since_flip(direction: "pd.Series") -> int | None:
    """Sessions since direction last went -1 -> +1 within _FLIP_WINDOW bars
    (0 = flipped today). None if no bullish flip or direction isn't bullish now."""
    vals = direction.iloc[-(_FLIP_WINDOW + 1):].to_numpy()
    if len(vals) < 2 or vals[-1] != 1:
        return None
    for back in range(len(vals) - 1):
        i = len(vals) - 1 - back
        if vals[i] == 1 and vals[i - 1] == -1:
            return back
    return None


def _fresh_score(since: int) -> int:
    return {0: 30, 1: 26, 2: 22}.get(since, 16 if since <= 3 else 10)


def _risk_score(risk_pct: float) -> int:
    if risk_pct <= 4:
        return 25
    if risk_pct <= 7:
        return 18
    if risk_pct <= 10:
        return 10
    return 4


def _trend_score(close: float, sma50: float, sma200: float) -> int:
    if close > sma50 > sma200:
        return 25
    if close > sma200:
        return 15
    if close > sma50:
        return 8
    return 0


def _volume_score(ratio: float) -> int:
    if ratio >= 1.5:
        return 20
    if ratio >= 1.0:
        return 12
    return 5


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


def score_supertrend(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None unless a fresh bullish flip qualifies.
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

    st = supertrend(hist)
    since = sessions_since_flip(st["direction"])
    stop = float(st["line"].iloc[-1])
    if since is None or np.isnan(stop):
        return None

    close = hist["Close"]
    last = float(close.iloc[-1])
    if last <= 0 or stop >= last:
        return None
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1])
    avg_vol = float(hist["Volume"].rolling(20).mean().iloc[-1 - since]) if since < len(hist) - 20 else 0.0
    flip_vol = float(hist["Volume"].iloc[-1 - since])
    vol_ratio = flip_vol / avg_vol if avg_vol > 0 else 0.0
    risk_pct = (last - stop) / last * 100

    s_fresh, s_risk = _fresh_score(since), _risk_score(risk_pct)
    s_trend, s_vol = _trend_score(last, sma50, sma200), _volume_score(vol_ratio)
    total = s_fresh + s_risk + s_trend + s_vol

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "stop": round(stop, 2),
        "risk_pct": round(risk_pct, 1),
        "sessions_since_flip": since,
        "flip_volume_ratio": round(vol_ratio, 2),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "freshness": s_fresh,
            "risk": s_risk,
            "trend": s_trend,
            "volume": s_vol,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/supertrend-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "supertrend-screener.json"
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
    parser = argparse.ArgumentParser(description="Supertrend Flip Screener")
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
        r = score_supertrend(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🔄  Supertrend — {len(results)} bullish flips of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"stop ${r['stop']:.2f} ({r['risk_pct']:.1f}% risk), "
            f"flipped {r['sessions_since_flip']}d ago  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
