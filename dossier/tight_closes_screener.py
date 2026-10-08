#!/usr/bin/env python3
"""
🧷 Tight Closes Screener — "3 Weeks Tight" Bases Near Highs

O'Neil's "3 weeks tight" pattern: a stock in an uptrend closes the week at
nearly the same price three or more weeks running. Weekly closes within ~1.5%
of each other means sellers have run out and holders won't let go; the stock
is being held in a vise, and the resolution is usually a move out of it.

Different from the other base screeners in the dossier:
  - NR7: one narrow DAY
  - VCP: contracting pullback depth over weeks
  - Volume Dry-Up: volume only
  - THIS: the WEEKLY CLOSE spread itself, inside an uptrend, near highs

Detection (pure yfinance history):
    Tight    → last N weekly closes (N >= _MIN_WEEKS) all sit within
               _MAX_SPREAD_PCT of each other (max-min over mean)
    Uptrend  → latest close above SMA50, and within _MAX_OFF_HIGH_PCT of the
               52-week high (a tight base far below the high is just a dead stock)

Scoring (0-100):
    Tightness      (35 pts) — smaller weekly-close spread
    Duration       (20 pts) — more consecutive tight weeks
    Trend          (25 pts) — above SMA50, SMA50 rising, SMA50 > SMA200
    Near high      (20 pts) — distance below the 52-week high

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.tight_closes_screener --tickers NVDA,AAPL
    python -m dossier.tight_closes_screener --watchlist
    python -m dossier.tight_closes_screener --json --no-save

Output: docs/api/tight-closes-screener.json (served via GitHub Pages)

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

_MIN_WEEKS = 3             # classic "3 weeks tight"
_MAX_WEEKS = 8             # stop counting past two months
_MAX_SPREAD_PCT = 1.5      # weekly-close range as % of mean close
_MAX_OFF_HIGH_PCT = 10.0   # must sit within this of the 52-week high
_REQUIRED_COLS = ("High", "Close")


def find_tight_weeks(hist: "pd.DataFrame") -> dict | None:
    """
    Count the consecutive most-recent weekly closes that sit inside the
    _MAX_SPREAD_PCT band. Returns None if fewer than _MIN_WEEKS qualify.
    """
    if any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    weekly = hist["Close"].dropna().resample("W-FRI").last().dropna()
    if len(weekly) < _MIN_WEEKS:
        return None

    best = None
    for k in range(_MIN_WEEKS, min(_MAX_WEEKS, len(weekly)) + 1):
        window = weekly.iloc[-k:]
        mean = float(window.mean())
        if mean <= 0:
            return None
        spread = (float(window.max()) - float(window.min())) / mean * 100
        if spread > _MAX_SPREAD_PCT:
            break  # widening the window only ever widens the spread
        best = {"weeks": k, "spread_pct": spread}
    if best is None:
        return None

    cutoff = weekly.index[-best["weeks"]] - pd.Timedelta(days=6)
    base = hist.loc[hist.index >= cutoff]
    best["pivot"] = float(base["High"].max())
    return best


def _tightness_score(spread_pct: float) -> int:
    if spread_pct <= 0.5:
        return 35
    if spread_pct <= 0.8:
        return 29
    if spread_pct <= 1.1:
        return 23
    if spread_pct <= _MAX_SPREAD_PCT:
        return 16
    return 0


def _duration_score(weeks: int) -> int:
    if weeks >= 6:
        return 20
    if weeks >= 5:
        return 16
    if weeks >= 4:
        return 12
    if weeks >= _MIN_WEEKS:
        return 8
    return 0


def _trend_score(last: float, sma50: float, sma50_prior: float, sma200: float | None) -> int:
    pts = 0
    if last > sma50:
        pts += 10
    if sma50 > sma50_prior:
        pts += 7
    if sma200 is not None and sma50 > sma200:
        pts += 8
    return pts


def _near_high_score(off_high_pct: float) -> int:
    if off_high_pct <= 3:
        return 20
    if off_high_pct <= 6:
        return 14
    if off_high_pct <= _MAX_OFF_HIGH_PCT:
        return 8
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


def score_tight_closes(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None when there's no tight base in an uptrend.
    `hist` may be injected (tests); otherwise fetched from yfinance."""
    if hist is None:
        try:
            hist = yf.Ticker(ticker).history(period="1y", interval="1d")
        except Exception:
            return None
    ok, _ = check_yfinance_history(hist, ticker, min_rows=80)
    if not ok or any(c not in hist.columns for c in _REQUIRED_COLS):
        return None

    tight = find_tight_weeks(hist)
    if tight is None:
        return None

    closes = hist["Close"].dropna()
    last = float(closes.iloc[-1])
    sma50_s = closes.rolling(50).mean()
    sma50, sma50_prior = sma50_s.iloc[-1], sma50_s.iloc[-11]
    if pd.isna(sma50) or pd.isna(sma50_prior) or last <= float(sma50):
        return None
    sma200_v = closes.rolling(200).mean().iloc[-1]
    sma200 = None if pd.isna(sma200_v) else float(sma200_v)

    high52 = float(hist["High"].max())
    off_high = (high52 - last) / high52 * 100 if high52 > 0 else 100.0
    if off_high > _MAX_OFF_HIGH_PCT:
        return None

    s_tight = _tightness_score(tight["spread_pct"])
    s_dur = _duration_score(tight["weeks"])
    s_trend = _trend_score(last, float(sma50), float(sma50_prior), sma200)
    s_high = _near_high_score(off_high)
    total = s_tight + s_dur + s_trend + s_high

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "tight_weeks": tight["weeks"],
        "weekly_spread_pct": round(tight["spread_pct"], 2),
        "pivot": round(tight["pivot"], 2),
        "pct_to_pivot": round((tight["pivot"] - last) / last * 100, 1),
        "off_52w_high_pct": round(off_high, 1),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "tightness": s_tight,
            "duration": s_dur,
            "trend": s_trend,
            "near_high": s_high,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/tight-closes-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "tight-closes-screener.json"
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
    parser = argparse.ArgumentParser(description="Tight Closes Screener")
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
        r = score_tight_closes(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🧷  Tight Closes — {len(results)} tight bases of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"{r['tight_weeks']}w tight ({r['weekly_spread_pct']:.2f}% spread), "
            f"{r['off_52w_high_pct']:.1f}% off high, pivot ${r['pivot']:.2f}  "
            f"Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
