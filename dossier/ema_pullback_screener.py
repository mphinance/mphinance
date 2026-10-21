#!/usr/bin/env python3
"""
🧲 EMA Pullback Screener — strong uptrends tagging the rising 21-EMA on light volume

The buy-the-dip entry for names that are already working: 8 > 21 > 50 EMA stacked
and rising, price has pulled back into the 21-EMA zone, and selling volume is thin.
Pairs with the breakout screens (Donchian, Ichimoku): those find the first leg,
this finds the second entry after it.

Detection:
    Trend  → close > 50-EMA, EMA21 > EMA50, EMA21 rising over 5 bars, and the
             50-EMA rising over 10 bars
    Tag    → latest low within _TAG_ATR of the 21-EMA (or below it) while the close
             still holds at/above EMA21 - _TAG_ATR (no break of the line)
    Dip    → price is off its 20-day closing high by at least 1 ATR (a real pullback)

Scoring (0-100):
    Tag quality (30) — closeness of the low to EMA21 and close back above it
    Pullback    (20) — depth off the 20-day high, in ATRs (sweet spot 1-3)
    Dry volume  (20) — last-3-day volume vs 50-day average
    Trend       (20) — EMA stack spacing (EMA21 vs EMA50, in ATRs)
    Reversal    (10) — latest close above the prior close

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.ema_pullback_screener --tickers NVDA,AAPL
    python -m dossier.ema_pullback_screener --json --no-save

Output: docs/api/ema-pullback-screener.json (served via GitHub Pages)

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

_TAG_ATR = 0.5             # how close (in ATRs) the low must get to EMA21
_MIN_DIP_ATR = 1.0         # minimum pullback off the 20-day closing high
_ATR_PERIOD = 14
_VOL_AVG = 50
_MIN_ROWS = 120
_REQUIRED_COLS = ("High", "Low", "Close", "Volume")


def compute_indicators(hist: "pd.DataFrame") -> "pd.DataFrame | None":
    if any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    high, low, close = hist["High"], hist["Low"], hist["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()],
                   axis=1).max(axis=1)
    return pd.DataFrame({
        "ema8": close.ewm(span=8, adjust=False).mean(),
        "ema21": close.ewm(span=21, adjust=False).mean(),
        "ema50": close.ewm(span=50, adjust=False).mean(),
        "atr": tr.rolling(_ATR_PERIOD).mean(),
        "high20": close.rolling(20).max(),
    })


def is_stacked_uptrend(ind: "pd.DataFrame", close: "pd.Series") -> bool:
    e8, e21, e50 = ind["ema8"], ind["ema21"], ind["ema50"]
    return bool(
        close.iloc[-1] > e50.iloc[-1]
        and e21.iloc[-1] > e50.iloc[-1]
        and e21.iloc[-1] > e21.iloc[-6]
        and e50.iloc[-1] > e50.iloc[-11]
    )


def _tag_score(low_gap_atr: float, close_above: bool) -> int:
    """low_gap_atr = (low - EMA21) / ATR; negative means the low pierced the line."""
    gap = abs(low_gap_atr)
    pts = 22 if gap <= 0.15 else 16 if gap <= 0.3 else 10
    return pts + (8 if close_above else 0)


def _pullback_score(dip_atr: float) -> int:
    if 1.0 <= dip_atr <= 3.0:
        return 20
    if 3.0 < dip_atr <= 4.5:
        return 12
    return 6


def _dryup_score(ratio: float) -> int:
    if ratio <= 0.6:
        return 20
    if ratio <= 0.85:
        return 14
    if ratio <= 1.1:
        return 8
    return 2


def _trend_score(spread_atr: float) -> int:
    if spread_atr >= 3.0:
        return 20
    if spread_atr >= 1.5:
        return 14
    return 7


def _reversal_score(last: float, prev: float) -> int:
    return 10 if last > prev else 3


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


def score_ema_pullback(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; None unless a stacked uptrend is tagging EMA21.
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

    ind = compute_indicators(hist)
    close = hist["Close"]
    if ind is None or not is_stacked_uptrend(ind, close):
        return None
    atr = float(ind["atr"].iloc[-1])
    vol_avg = float(hist["Volume"].rolling(_VOL_AVG).mean().iloc[-1])
    if pd.isna(atr) or atr <= 0 or pd.isna(vol_avg) or vol_avg <= 0:
        return None

    last, prev = float(close.iloc[-1]), float(close.iloc[-2])
    ema21, ema50 = float(ind["ema21"].iloc[-1]), float(ind["ema50"].iloc[-1])
    low = float(hist["Low"].iloc[-1])
    low_gap = (low - ema21) / atr
    if low_gap > _TAG_ATR or last < ema21 - _TAG_ATR * atr:
        return None
    dip = (float(ind["high20"].iloc[-1]) - last) / atr
    if dip < _MIN_DIP_ATR:
        return None

    vol_ratio = float(hist["Volume"].iloc[-3:].mean()) / vol_avg
    spread = (ema21 - ema50) / atr
    s_tag = _tag_score(low_gap, last >= ema21)
    s_dip = _pullback_score(dip)
    s_vol = _dryup_score(vol_ratio)
    s_trend = _trend_score(spread)
    s_rev = _reversal_score(last, prev)
    total = s_tag + s_dip + s_vol + s_trend + s_rev

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "ema21": round(ema21, 2),
        "ema50": round(ema50, 2),
        "dist_to_ema21_pct": round((last - ema21) / ema21 * 100, 2),
        "pullback_atr": round(dip, 2),
        "volume_ratio_3d": round(vol_ratio, 2),
        "atr14": round(atr, 2),
        "stop_below_ema50": round(ema50, 2),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "tag": s_tag,
            "pullback": s_dip,
            "dry_volume": s_vol,
            "trend": s_trend,
            "reversal": s_rev,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/ema-pullback-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ema-pullback-screener.json"
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
    parser = argparse.ArgumentParser(description="EMA Pullback Screener")
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
        r = score_ema_pullback(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🧲  EMA Pullback — {len(results)} tags of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"EMA21 ${r['ema21']:.2f} ({r['dist_to_ema21_pct']:+.1f}%), "
            f"dip {r['pullback_atr']:.1f}N, vol {r['volume_ratio_3d']:.1f}x  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
