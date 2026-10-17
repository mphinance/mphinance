#!/usr/bin/env python3
"""
🧭 Aroon Trend Birth Screener — fresh highs arriving, fresh lows gone

Aroon measures *time since* the extreme, not distance from it. Aroon Up(25) of 100
means today is the highest high of the last 25 sessions; Aroon Down(25) near 0 means
the lows are ancient history. A "trend birth" is the moment Up crosses above Down and
pushes through 70 while Down collapses under 30: the tape stopped printing new lows
and started printing new highs. It catches turns earlier than the SMA crosses and
is a different lens from the 52-week-high and donchian screens (which need a breakout).

Qualifies when:
    Aroon Up(25) crossed above _UP_MIN within the last _CROSS_WINDOW sessions,
    Aroon Up now >= _UP_MIN and Aroon Down now <= _DOWN_MAX,
    and close is above the 50-day SMA.

Scoring (0-100):
    Aroon Up   (30 pts) — how fresh the high is (100 = today)
    Aroon Down (20 pts) — lower = the last low is further in the past
    Freshness  (20 pts) — how recently the cross happened
    Trend      (20 pts) — price vs 50/200-day SMAs
    Oscillator (10 pts) — Aroon Up minus Down spread

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.aroon_screener --tickers NVDA,AAPL
    python -m dossier.aroon_screener --json --no-save

Output: docs/api/aroon-screener.json (served via GitHub Pages)

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

_PERIOD = 25
_UP_MIN = 70.0
_DOWN_MAX = 30.0
_CROSS_WINDOW = 10
_MIN_ROWS = 210
_REQUIRED_COLS = ("High", "Low", "Close")


def _sessions_since_extreme(values: "pd.Series", pick) -> "pd.Series":
    """Rolling count of sessions since the window's max/min (ties -> most recent)."""
    def since(w: np.ndarray) -> float:
        # reverse so index 0 = today; argmax/argmin return the first (most recent) tie
        return float(pick(w[::-1]))
    return values.rolling(_PERIOD + 1).apply(since, raw=True)


def aroon(high: "pd.Series", low: "pd.Series") -> "pd.DataFrame":
    """Aroon Up/Down (0-100) over a _PERIOD-session lookback (window of _PERIOD+1 bars)."""
    since_high = _sessions_since_extreme(high, np.argmax)
    since_low = _sessions_since_extreme(low, np.argmin)
    up = (_PERIOD - since_high) / _PERIOD * 100
    down = (_PERIOD - since_low) / _PERIOD * 100
    return pd.DataFrame({"up": up, "down": down})


def sessions_since_cross(up: "pd.Series") -> int | None:
    """Sessions since Aroon Up last crossed from below _UP_MIN to at/above it,
    searching the last _CROSS_WINDOW bars. 0 = crossed today. None = no cross."""
    vals = up.iloc[-(_CROSS_WINDOW + 1):].to_numpy()
    for back in range(len(vals) - 1):
        i = len(vals) - 1 - back
        if vals[i] >= _UP_MIN and vals[i - 1] < _UP_MIN:
            return back
    return None


def _up_score(up: float) -> int:
    if up >= 100:
        return 30
    if up >= 90:
        return 24
    if up >= 80:
        return 18
    return 12


def _down_score(down: float) -> int:
    if down <= 0:
        return 20
    if down <= 12:
        return 15
    if down <= 20:
        return 10
    return 5


def _fresh_score(since: int) -> int:
    if since <= 2:
        return 20
    if since <= 5:
        return 14
    return 8


def _trend_score(close: float, sma50: float, sma200: float) -> int:
    if close > sma50 > sma200:
        return 20
    if close > sma50:
        return 10
    return 0


def _spread_score(spread: float) -> int:
    if spread >= 90:
        return 10
    if spread >= 70:
        return 7
    return 3


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


def score_aroon(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None unless a trend birth qualifies.
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

    ar = aroon(hist["High"], hist["Low"])
    up, down = float(ar["up"].iloc[-1]), float(ar["down"].iloc[-1])
    if np.isnan(up) or np.isnan(down) or up < _UP_MIN or down > _DOWN_MAX:
        return None
    since = sessions_since_cross(ar["up"])
    if since is None:
        return None

    close = hist["Close"]
    last = float(close.iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1])
    if last <= sma50:
        return None

    s_up, s_down = _up_score(up), _down_score(down)
    s_fresh, s_trend = _fresh_score(since), _trend_score(last, sma50, sma200)
    s_spread = _spread_score(up - down)
    total = s_up + s_down + s_fresh + s_trend + s_spread

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "aroon_up": round(up, 1),
        "aroon_down": round(down, 1),
        "aroon_osc": round(up - down, 1),
        "sessions_since_cross": since,
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "aroon_up": s_up,
            "aroon_down": s_down,
            "freshness": s_fresh,
            "trend": s_trend,
            "spread": s_spread,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/aroon-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "aroon-screener.json"
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
    parser = argparse.ArgumentParser(description="Aroon Trend Birth Screener")
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
        r = score_aroon(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🧭  Aroon — {len(results)} trend births of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"Up {r['aroon_up']:.0f} / Down {r['aroon_down']:.0f}, "
            f"crossed {r['sessions_since_cross']}d ago  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
