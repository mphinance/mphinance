#!/usr/bin/env python3
"""
🎯 RSI(2) Pullback Screener — Washed-Out Dips Inside Long-Term Uptrends

The Connors-style mean-reversion setup: a stock in a durable uptrend (above its
200-day average) gets sold hard for a few days, pushing the 2-period RSI into
single digits. In an uptrend, that kind of short-term capitulation tends to
snap back within days, which is the opposite trade from the breakout screens.

Different from the other dossier screens:
  - Capitulation / Failed Breakdown: stocks in or below a damaged trend
  - Pocket Pivot / VCP / NR7: continuation and breakout setups
  - THIS: a trend that is intact, with a short, violent pullback to buy into

Detection (pure yfinance history):
    Trend      → close above SMA200 and SMA50 above SMA200
    Washed out → RSI(2) <= _MAX_RSI2 (Wilder smoothing)

Scoring (0-100):
    Oversold   (40 pts) — lower RSI(2) is a deeper flush
    Trend      (25 pts) — SMA50 slope, distance above SMA200
    Streak     (15 pts) — consecutive down closes into today
    Pullback   (20 pts) — drop from the 10-day high (sweet spot 4-12%)

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.rsi2_pullback_screener --tickers NVDA,AAPL
    python -m dossier.rsi2_pullback_screener --json --no-save

Output: docs/api/rsi2-pullback-screener.json (served via GitHub Pages)

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

_MAX_RSI2 = 10.0           # washed-out threshold
_REQUIRED_COLS = ("Close",)


def rsi(close: "pd.Series", period: int = 2) -> "pd.Series":
    """Wilder RSI. Flat stretches (no gains, no losses) read 50, not NaN."""
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    out = 100 - 100 / (1 + gain / loss)
    out = out.where(loss != 0, 100.0)
    return out.where(~((gain == 0) & (loss == 0)), 50.0)


def _down_streak(close: "pd.Series") -> int:
    """Consecutive down closes ending at the latest bar."""
    diffs = close.diff().dropna().tolist()
    n = 0
    for d in reversed(diffs):
        if d < 0:
            n += 1
        else:
            break
    return n


def _oversold_score(rsi2: float) -> int:
    if rsi2 <= 2:
        return 40
    if rsi2 <= 4:
        return 33
    if rsi2 <= 7:
        return 25
    if rsi2 <= _MAX_RSI2:
        return 16
    return 0


def _trend_score(sma50_slope_pct: float, above_200_pct: float) -> int:
    pts = 0
    if sma50_slope_pct > 0:
        pts += 10
    if sma50_slope_pct > 2:
        pts += 5
    if above_200_pct >= 5:
        pts += 5
    if above_200_pct >= 15:
        pts += 5
    return pts


def _streak_score(streak: int) -> int:
    if streak >= 4:
        return 15
    if streak == 3:
        return 11
    if streak == 2:
        return 6
    return 0


def _pullback_score(drop_pct: float) -> int:
    if 4 <= drop_pct <= 12:
        return 20
    if 2 <= drop_pct < 4 or 12 < drop_pct <= 18:
        return 11
    return 3 if drop_pct > 0 else 0


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


def score_rsi2_pullback(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; None unless a washed-out RSI(2) sits inside an uptrend.
    `hist` may be injected (tests); otherwise fetched from yfinance."""
    if hist is None:
        try:
            hist = yf.Ticker(ticker).history(period="1y", interval="1d")
        except Exception:
            return None
    ok, _ = check_yfinance_history(hist, ticker, min_rows=210)
    if not ok or any(c not in hist.columns for c in _REQUIRED_COLS):
        return None

    close = hist["Close"].dropna()
    if len(close) < 210:
        return None
    last = float(close.iloc[-1])
    sma50 = close.rolling(50).mean()
    sma200_v = close.rolling(200).mean().iloc[-1]
    if pd.isna(sma200_v) or pd.isna(sma50.iloc[-1]) or pd.isna(sma50.iloc[-11]):
        return None
    sma200 = float(sma200_v)
    if last <= sma200 or float(sma50.iloc[-1]) <= sma200:
        return None

    rsi2 = float(rsi(close, 2).iloc[-1])
    if pd.isna(rsi2) or rsi2 > _MAX_RSI2:
        return None

    high10 = float(close.iloc[-10:].max())
    drop = (high10 - last) / high10 * 100
    slope = (float(sma50.iloc[-1]) / float(sma50.iloc[-11]) - 1) * 100
    above_200 = (last / sma200 - 1) * 100
    streak = _down_streak(close)

    s_over = _oversold_score(rsi2)
    s_trend = _trend_score(slope, above_200)
    s_streak = _streak_score(streak)
    s_pull = _pullback_score(drop)
    total = s_over + s_trend + s_streak + s_pull

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "rsi2": round(rsi2, 1),
        "down_days": streak,
        "drop_from_10d_high_pct": round(drop, 1),
        "above_sma200_pct": round(above_200, 1),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "oversold": s_over,
            "trend": s_trend,
            "streak": s_streak,
            "pullback": s_pull,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/rsi2-pullback-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "rsi2-pullback-screener.json"
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
    parser = argparse.ArgumentParser(description="RSI(2) Pullback Screener")
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
        r = score_rsi2_pullback(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🎯  RSI(2) Pullbacks — {len(results)} of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"RSI2 {r['rsi2']:.1f}, {r['down_days']} down days, "
            f"-{r['drop_from_10d_high_pct']:.1f}% off 10d high  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
