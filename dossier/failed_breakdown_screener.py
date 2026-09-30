#!/usr/bin/env python3
"""
🪤 Failed-Breakdown Screener — The Spring: Stops Got Run, Buyers Took It Back

A stock slices below a well-defined support low, trips the stops parked under
it, then closes back ABOVE that level in the same session. The breakdown
"failed": sellers showed their hand and had nothing left. Wyckoff called it a
spring; traders call it a bear trap. The best ones reverse on heavy volume and
close near the high of the day.

Different from the other screeners in the dossier:
  - Capitulation / Williams %R: oversold readings, no support level involved
  - AVWAP / SMA200 reclaim: reclaims of a moving average, not a swing low
  - THIS: an undercut of the prior N-day low that was rejected within a session

Detection (pure yfinance history):
    Support   → lowest low of the _SUPPORT_WINDOW sessions BEFORE the trap day
                (ending _SUPPORT_GAP sessions before it, so support is a real
                prior low and not yesterday's dip)
    Trap day  → within the last _LOOKBACK_DAYS sessions: Low undercuts support
                by >= _MIN_UNDERCUT_PCT, Close back above support
    Holding   → every close since the trap day stays above support

Scoring (0-100):
    Reclaim strength  (30 pts) — where the trap day closed in its range
    Reversal volume   (25 pts) — multiple of the 20-day average
    Undercut depth    (15 pts) — a real stop run, not a 1-tick poke
    Support maturity  (10 pts) — how long the level had stood before the trap
    Follow-through    (20 pts) — % above the trap-day close now

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.failed_breakdown_screener --tickers NVDA,AAPL
    python -m dossier.failed_breakdown_screener --watchlist
    python -m dossier.failed_breakdown_screener --json --no-save

Output: docs/api/failed-breakdown-screener.json (served via GitHub Pages)

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

_SUPPORT_WINDOW = 30      # sessions that define the support low
_SUPPORT_GAP = 3          # support must end this many sessions before the trap
_LOOKBACK_DAYS = 5        # trap must be recent
_MIN_UNDERCUT_PCT = 0.5   # low must pierce support by at least this much
_REQUIRED_COLS = ("High", "Low", "Close", "Volume")


def find_failed_breakdown(hist: "pd.DataFrame", lookback: int = _LOOKBACK_DAYS) -> dict | None:
    """
    Locate the most recent trap day in the last `lookback` sessions: a low that
    undercut the prior swing low but a close back above it, with every close
    since staying above. Returns None if there isn't one.
    """
    if any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    if len(hist) < _SUPPORT_WINDOW + _SUPPORT_GAP + 5:
        return None
    highs, lows, closes, vols = hist["High"], hist["Low"], hist["Close"], hist["Volume"]
    avg_vol = vols.rolling(20).mean().shift(1)
    n = len(hist)

    for i in range(n - 1, max(n - lookback - 1, _SUPPORT_WINDOW + _SUPPORT_GAP), -1):
        window = lows.iloc[i - _SUPPORT_GAP - _SUPPORT_WINDOW: i - _SUPPORT_GAP]
        support = float(window.min())
        if support <= 0 or pd.isna(support):
            continue
        low, close = float(lows.iloc[i]), float(closes.iloc[i])
        undercut_pct = (support - low) / support * 100
        if undercut_pct < _MIN_UNDERCUT_PCT or close <= support:
            continue
        if float(closes.iloc[i:].min()) <= support:
            continue  # lost the level again — the trap didn't hold
        rng = float(highs.iloc[i]) - low
        close_pos = (close - low) / rng if rng > 0 else 0.5
        avg = avg_vol.iloc[i]
        vol_mult = float(vols.iloc[i]) / float(avg) if pd.notna(avg) and avg > 0 else 0.0
        support_age = _SUPPORT_GAP + int(len(window) - 1 - window.values.argmin())
        return {
            "support": support,
            "undercut_pct": undercut_pct,
            "close_pos": close_pos,
            "vol_mult": vol_mult,
            "support_age": support_age,
            "trap_close": close,
            "days_since_trap": n - 1 - i,
            "last": float(closes.iloc[-1]),
        }
    return None


def _reclaim_score(close_pos: float) -> int:
    if close_pos >= 0.8:
        return 30
    if close_pos >= 0.6:
        return 22
    if close_pos >= 0.4:
        return 14
    return 6


def _volume_score(vol_mult: float) -> int:
    if vol_mult >= 3:
        return 25
    if vol_mult >= 2:
        return 20
    if vol_mult >= 1.5:
        return 14
    if vol_mult >= 1:
        return 8
    return 2


def _undercut_score(undercut_pct: float) -> int:
    if undercut_pct >= 3:
        return 15
    if undercut_pct >= 1.5:
        return 11
    if undercut_pct >= _MIN_UNDERCUT_PCT:
        return 6
    return 0


def _maturity_score(support_age: int) -> int:
    if support_age >= 20:
        return 10
    if support_age >= 10:
        return 7
    return 4


def _follow_through_score(pct_since_trap_close: float) -> int:
    if pct_since_trap_close >= 5:
        return 20
    if pct_since_trap_close >= 2:
        return 15
    if pct_since_trap_close >= 0:
        return 10
    return 4


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


def score_failed_breakdown(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None when there's no failed breakdown.
    `hist` may be injected (tests); otherwise fetched from yfinance."""
    if hist is None:
        try:
            hist = yf.Ticker(ticker).history(period="6mo", interval="1d")
        except Exception:
            return None
    ok, _ = check_yfinance_history(hist, ticker, min_rows=25)
    if not ok:
        return None

    trap = find_failed_breakdown(hist)
    if trap is None:
        return None

    since_pct = (trap["last"] - trap["trap_close"]) / trap["trap_close"] * 100
    s_reclaim = _reclaim_score(trap["close_pos"])
    s_vol = _volume_score(trap["vol_mult"])
    s_under = _undercut_score(trap["undercut_pct"])
    s_mature = _maturity_score(trap["support_age"])
    s_follow = _follow_through_score(since_pct)
    total = s_reclaim + s_vol + s_under + s_mature + s_follow

    return {
        "ticker": ticker,
        "price": round(trap["last"], 2),
        "support": round(trap["support"], 2),
        "undercut_pct": round(trap["undercut_pct"], 1),
        "reversal_volume_mult": round(trap["vol_mult"], 1),
        "close_position": round(trap["close_pos"], 2),
        "support_age_days": trap["support_age"],
        "days_since_trap": trap["days_since_trap"],
        "pct_since_trap_close": round(since_pct, 1),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "reclaim_strength": s_reclaim,
            "reversal_volume": s_vol,
            "undercut_depth": s_under,
            "support_maturity": s_mature,
            "follow_through": s_follow,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/failed-breakdown-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "failed-breakdown-screener.json"
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
    parser = argparse.ArgumentParser(description="Failed-Breakdown Screener")
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
        r = score_failed_breakdown(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🪤  Failed-Breakdown — {len(results)} bear traps of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"undercut {r['undercut_pct']:.1f}% below ${r['support']:.2f} on "
            f"{r['reversal_volume_mult']:.1f}× vol, {r['days_since_trap']}d ago, "
            f"{r['pct_since_trap_close']:+.1f}% since  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
