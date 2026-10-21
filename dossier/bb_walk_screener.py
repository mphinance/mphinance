#!/usr/bin/env python3
"""
🚶 Bollinger Band Walk Screener — strong trends that ride the upper band

A "band walk" is the opposite of a mean-reversion tell: in a powerful trend, price
keeps closing in the top of the 20-day Bollinger envelope instead of snapping back
to the mean. Overbought stays overbought. The other volatility screens in the
dossier look for compression (TTM squeeze, NR7, tight closes); this one finds the
names where the expansion is already underway and still being bought.

Qualifies when:
    >= _MIN_WALK_DAYS of the last _WALK_WINDOW closes have %B >= _WALK_PCTB,
    close above the 20-day SMA (the middle band never got tested), the
    20-day SMA is rising, and bandwidth is expanding vs 10 sessions ago.

Scoring (0-100):
    Walk days  (40 pts) — closes in the upper band, last 10 sessions
    Bandwidth  (20 pts) — expansion of band width vs 10 sessions ago
    Trend      (20 pts) — price vs 50/200-day SMAs
    Mid-band   (10 pts) — cushion above the 20-day SMA (not too stretched, not too thin)
    Streak     (10 pts) — consecutive closes holding above the middle band

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.bb_walk_screener --tickers NVDA,AAPL
    python -m dossier.bb_walk_screener --json --no-save

Output: docs/api/bb-walk-screener.json (served via GitHub Pages)

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

_BB_PERIOD = 20
_BB_STD = 2.0
_WALK_WINDOW = 10
_WALK_PCTB = 0.8           # "upper band zone": top 20% of the envelope
_MIN_WALK_DAYS = 6
_LOOKBACK = 10
_MIN_ROWS = 210
_REQUIRED_COLS = ("Close",)


def bollinger(close: "pd.Series") -> "pd.DataFrame":
    """Middle band, %B (0 = lower band, 1 = upper band) and bandwidth (% of middle)."""
    mid = close.rolling(_BB_PERIOD).mean()
    sd = close.rolling(_BB_PERIOD).std(ddof=0)
    upper, lower = mid + _BB_STD * sd, mid - _BB_STD * sd
    width = (upper - lower).where(lambda w: w > 0)   # flat price -> NaN, not div-by-zero
    return pd.DataFrame({
        "mid": mid,
        "pctb": (close - lower) / width,
        "bandwidth": width / mid * 100,
    })


def walk_days(pctb: "pd.Series") -> int:
    """Closes in the upper-band zone over the last _WALK_WINDOW sessions."""
    return int((pctb.iloc[-_WALK_WINDOW:] >= _WALK_PCTB).sum())


def mid_streak(close: "pd.Series", mid: "pd.Series") -> int:
    """Consecutive most-recent closes above the middle band."""
    above = (close > mid).to_numpy()
    n = 0
    for flag in above[::-1]:
        if not flag:
            break
        n += 1
    return n


def _walk_score(days: int) -> int:
    if days >= 9:
        return 40
    if days >= 8:
        return 32
    if days >= 7:
        return 24
    return 16


def _bandwidth_score(expansion: float) -> int:
    if expansion >= 1.5:
        return 20
    if expansion >= 1.25:
        return 14
    return 8


def _trend_score(close: float, sma50: float, sma200: float) -> int:
    if close > sma50 > sma200:
        return 20
    if close > sma50:
        return 10
    return 0


def _cushion_score(pct_above_mid: float) -> int:
    if 3 <= pct_above_mid <= 10:
        return 10
    if 1 <= pct_above_mid < 3 or 10 < pct_above_mid <= 15:
        return 6
    return 2


def _streak_score(streak: int) -> int:
    if streak >= 20:
        return 10
    if streak >= 10:
        return 6
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


def score_bb_walk(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None unless a band walk qualifies.
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

    close = hist["Close"]
    bb = bollinger(close)
    if bb["pctb"].iloc[-_WALK_WINDOW:].isna().any():
        return None
    days = walk_days(bb["pctb"])
    if days < _MIN_WALK_DAYS:
        return None

    last = float(close.iloc[-1])
    mid_now = float(bb["mid"].iloc[-1])
    mid_prev = float(bb["mid"].iloc[-1 - _LOOKBACK])
    bw_now = float(bb["bandwidth"].iloc[-1])
    bw_prev = float(bb["bandwidth"].iloc[-1 - _LOOKBACK])
    if last <= mid_now or mid_now <= mid_prev:
        return None
    if pd.isna(bw_prev) or pd.isna(bw_now) or bw_prev <= 0 or bw_now <= bw_prev:
        return None

    expansion = bw_now / bw_prev
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1])
    pct_above_mid = (last / mid_now - 1) * 100
    streak = mid_streak(close, bb["mid"])

    s_walk = _walk_score(days)
    s_bw = _bandwidth_score(expansion)
    s_trend = _trend_score(last, sma50, sma200)
    s_cush = _cushion_score(pct_above_mid)
    s_streak = _streak_score(streak)
    total = s_walk + s_bw + s_trend + s_cush + s_streak

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "walk_days_10d": days,
        "pct_b": round(float(bb["pctb"].iloc[-1]), 2),
        "bandwidth_pct": round(bw_now, 1),
        "bandwidth_expansion": round(expansion, 2),
        "pct_above_mid_band": round(pct_above_mid, 1),
        "days_above_mid_band": streak,
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "walk_days": s_walk,
            "bandwidth": s_bw,
            "trend": s_trend,
            "mid_band_cushion": s_cush,
            "streak": s_streak,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/bb-walk-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "bb-walk-screener.json"
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
    parser = argparse.ArgumentParser(description="Bollinger Band Walk Screener")
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
        r = score_bb_walk(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🚶  BB Walk — {len(results)} band walkers of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"{r['walk_days_10d']}/10 upper-band closes, BW x{r['bandwidth_expansion']:.2f}, "
            f"{r['days_above_mid_band']}d above mid  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
