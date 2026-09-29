#!/usr/bin/env python3
"""
🪟 Gap-and-Hold Screener — Gaps That Institutions Refuse to Fill

A gap up on heavy volume is a statement; a gap that is still UNFILLED days
later is the market agreeing with it. Most gap-ups get faded within a week.
The ones that hold (price stays above the pre-gap close, and ideally above
the gap-day low) are where the buyers are defending their cost basis.

Different from the other screeners in the dossier:
  - RVol: big volume today, no memory of what price did after
  - PEAD / Earnings Momentum: gap tied to an earnings event only
  - THIS: any gap (news, upgrade, earnings), judged by what happened AFTER

Detection (pure yfinance history, no TradingView dependency):
    Gap day   → open >= prior close by _MIN_GAP_PCT, on volume >= _MIN_VOL_MULT
                × the 20-day average, within the last _LOOKBACK_DAYS sessions
    Held      → every close since the gap day is above the pre-gap close
                (gap not filled), and the latest close is above the gap-day low

Scoring (0-100):
    Gap size          (25 pts) — bigger gap = bigger statement
    Gap-day volume    (25 pts) — multiple of 20-day average
    Hold quality      (30 pts) — how far price sits above the gap floor
    Follow-through    (20 pts) — % gain since the gap-day close

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.gap_hold_screener --tickers NVDA,AAPL
    python -m dossier.gap_hold_screener --watchlist
    python -m dossier.gap_hold_screener --json --no-save

Output: docs/api/gap-hold-screener.json (served via GitHub Pages)

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

_MIN_GAP_PCT = 4.0        # open vs prior close
_MIN_VOL_MULT = 1.5       # gap-day volume vs 20d average
_LOOKBACK_DAYS = 10       # gap must be recent
_MIN_DAYS_HELD = 1        # at least one session after the gap day
_REQUIRED_COLS = ("Open", "Low", "Close", "Volume")


def find_gap_day(hist: "pd.DataFrame", lookback: int = _LOOKBACK_DAYS) -> dict | None:
    """
    Locate the most recent qualifying gap-up in the last `lookback` sessions
    that has held (no close back below the pre-gap close, latest close above
    the gap-day low). Returns None if there isn't one.
    """
    if any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    if len(hist) < 25:
        return None
    opens, lows, closes, vols = hist["Open"], hist["Low"], hist["Close"], hist["Volume"]
    avg_vol = vols.rolling(20).mean().shift(1)  # average BEFORE the gap day
    n = len(hist)

    # Most recent first, so the freshest held gap wins.
    for i in range(n - _MIN_DAYS_HELD - 1, max(n - lookback - 1, 0), -1):
        prev_close = float(closes.iloc[i - 1])
        avg = avg_vol.iloc[i]
        if prev_close <= 0 or pd.isna(avg) or avg <= 0:
            continue
        gap_pct = (float(opens.iloc[i]) - prev_close) / prev_close * 100
        vol_mult = float(vols.iloc[i]) / float(avg)
        if gap_pct < _MIN_GAP_PCT or vol_mult < _MIN_VOL_MULT:
            continue
        gap_low = float(lows.iloc[i])
        since = closes.iloc[i:]
        if float(since.min()) <= prev_close:
            continue  # gap filled — not a hold
        last = float(closes.iloc[-1])
        if last <= gap_low:
            continue
        return {
            "gap_pct": gap_pct,
            "vol_mult": vol_mult,
            "prev_close": prev_close,
            "gap_low": gap_low,
            "gap_close": float(closes.iloc[i]),
            "days_since_gap": n - 1 - i,
            "last": last,
        }
    return None


def _gap_size_score(gap_pct: float) -> int:
    if gap_pct >= 15:
        return 25
    if gap_pct >= 10:
        return 20
    if gap_pct >= 7:
        return 14
    if gap_pct >= _MIN_GAP_PCT:
        return 8
    return 0


def _gap_volume_score(vol_mult: float) -> int:
    if vol_mult >= 5:
        return 25
    if vol_mult >= 3:
        return 20
    if vol_mult >= 2:
        return 14
    if vol_mult >= _MIN_VOL_MULT:
        return 8
    return 0


def _hold_quality_score(last: float, prev_close: float, gap_low: float) -> int:
    """30 pts: price above the gap-day low = buyers defending the whole gap;
    between the pre-gap close and the gap-day low = only partly held."""
    if prev_close <= 0 or last <= prev_close:
        return 0
    cushion = (last - gap_low) / gap_low * 100 if gap_low > 0 else 0
    if cushion >= 5:
        return 30
    if cushion >= 2:
        return 24
    if cushion >= 0:
        return 16
    return 6


def _follow_through_score(pct_since_gap_close: float) -> int:
    if pct_since_gap_close >= 8:
        return 20
    if pct_since_gap_close >= 3:
        return 15
    if pct_since_gap_close >= 0:
        return 10
    if pct_since_gap_close >= -3:
        return 4
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


def score_gap_hold(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None when there's no held gap-up.
    `hist` may be injected (tests); otherwise fetched from yfinance."""
    if hist is None:
        try:
            hist = yf.Ticker(ticker).history(period="6mo", interval="1d")
        except Exception:
            return None
    ok, _ = check_yfinance_history(hist, ticker, min_rows=25)
    if not ok:
        return None

    gap = find_gap_day(hist)
    if gap is None:
        return None

    since_pct = (gap["last"] - gap["gap_close"]) / gap["gap_close"] * 100
    s_gap = _gap_size_score(gap["gap_pct"])
    s_vol = _gap_volume_score(gap["vol_mult"])
    s_hold = _hold_quality_score(gap["last"], gap["prev_close"], gap["gap_low"])
    s_follow = _follow_through_score(since_pct)
    total = s_gap + s_vol + s_hold + s_follow

    return {
        "ticker": ticker,
        "price": round(gap["last"], 2),
        "gap_pct": round(gap["gap_pct"], 1),
        "gap_volume_mult": round(gap["vol_mult"], 1),
        "days_since_gap": gap["days_since_gap"],
        "gap_floor": round(gap["prev_close"], 2),
        "gap_day_low": round(gap["gap_low"], 2),
        "pct_since_gap_close": round(since_pct, 1),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "gap_size": s_gap,
            "gap_volume": s_vol,
            "hold_quality": s_hold,
            "follow_through": s_follow,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/gap-hold-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "gap-hold-screener.json"
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
    parser = argparse.ArgumentParser(description="Gap-and-Hold Screener")
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
        r = score_gap_hold(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🪟  Gap-and-Hold — {len(results)} unfilled gaps of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"gap +{r['gap_pct']:.1f}% on {r['gap_volume_mult']:.1f}× vol, "
            f"{r['days_since_gap']}d ago, {r['pct_since_gap_close']:+.1f}% since  "
            f"Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
