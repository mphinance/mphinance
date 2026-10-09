#!/usr/bin/env python3
"""
☁️ Ichimoku Cloud Breakout Screener — fresh closes above the Kumo

The Ichimoku cloud is a support/resistance band built from midpoints of the
highest high and lowest low over several windows. A close ABOVE the cloud after
a stretch spent inside or under it means price has cleared the whole zone of
overhead supply the market has been defending for ~2 months.

Different from the other trend screens in the dossier:
  - Golden Cross / SMA200 reclaim: single moving-average events
  - High52: proximity to the annual high
  - THIS: a multi-window structure break (cloud top), with the lagging span
    and the forward cloud colour as independent confirmations

Standard settings (9 / 26 / 52):
    Tenkan   = midpoint of the 9-day range
    Kijun    = midpoint of the 26-day range
    Span A   = (Tenkan + Kijun) / 2, plotted 26 bars ahead
    Span B   = midpoint of the 52-day range, plotted 26 bars ahead
    Cloud NOW = the spans computed 26 bars ago
    Chikou   = today's close compared with the close 26 bars ago

Detection:
    Breakout → latest close above the current cloud top, and at least one close
               in the prior _FRESH_WINDOW bars at or below it (a fresh break,
               not a stock that has been riding above for months)

Scoring (0-100):
    Freshness (30 pts) — fewer bars since the first close above the cloud
    Cloud     (25 pts) — forward cloud bullish (Span A > Span B) and thickness
    TK        (20 pts) — Tenkan > Kijun and price above Kijun
    Chikou    (15 pts) — close above the close (and high) 26 bars back
    Reach     (10 pts) — not yet stretched far above the cloud top

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.ichimoku_screener --tickers NVDA,AAPL
    python -m dossier.ichimoku_screener --watchlist
    python -m dossier.ichimoku_screener --json --no-save

Output: docs/api/ichimoku-screener.json (served via GitHub Pages)

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

_TENKAN, _KIJUN, _SENKOU_B, _SHIFT = 9, 26, 52, 26
_FRESH_WINDOW = 10         # a break counts as fresh if price was in/below the cloud this recently
_MIN_ROWS = _SENKOU_B + _SHIFT + _FRESH_WINDOW
_REQUIRED_COLS = ("High", "Low", "Close")


def compute_ichimoku(hist: "pd.DataFrame") -> "pd.DataFrame | None":
    """Tenkan/Kijun plus the cloud edges as they sit under each bar today
    (spans shifted forward by _SHIFT) and the unshifted forward spans."""
    if any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    h, l = hist["High"], hist["Low"]

    def mid(n):
        return (h.rolling(n).max() + l.rolling(n).min()) / 2

    tenkan, kijun, span_b = mid(_TENKAN), mid(_KIJUN), mid(_SENKOU_B)
    span_a = (tenkan + kijun) / 2
    return pd.DataFrame({
        "close": hist["Close"],
        "tenkan": tenkan,
        "kijun": kijun,
        "fwd_a": span_a,
        "fwd_b": span_b,
        "cloud_a": span_a.shift(_SHIFT),
        "cloud_b": span_b.shift(_SHIFT),
    })


def find_breakout(ich: "pd.DataFrame") -> dict | None:
    """Return breakout facts if the last close is a fresh close above the cloud."""
    top = ich[["cloud_a", "cloud_b"]].max(axis=1, skipna=False)
    bottom = ich[["cloud_a", "cloud_b"]].min(axis=1, skipna=False)
    valid = top.notna()
    if not valid.iloc[-1] or valid.sum() < _FRESH_WINDOW + 1:
        return None
    above = ich["close"] > top
    if not above.iloc[-1]:
        return None

    # consecutive bars above the cloud, ending now
    bars_above = 0
    for i in range(len(ich) - 1, -1, -1):
        if valid.iloc[i] and above.iloc[i]:
            bars_above += 1
        else:
            break
    prior = valid.iloc[-1 - bars_above] if bars_above < len(ich) else False
    if bars_above > _FRESH_WINDOW or not prior:
        return None

    last = float(ich["close"].iloc[-1])
    cloud_top, cloud_bottom = float(top.iloc[-1]), float(bottom.iloc[-1])
    return {
        "bars_above": bars_above,
        "cloud_top": cloud_top,
        "cloud_bottom": cloud_bottom,
        "thickness_pct": (cloud_top - cloud_bottom) / last * 100,
        "above_cloud_pct": (last - cloud_top) / cloud_top * 100,
    }


def _fresh_score(bars_above: int) -> int:
    if bars_above <= 2:
        return 30
    if bars_above <= 4:
        return 24
    if bars_above <= 7:
        return 16
    return 8


def _cloud_score(bullish_fwd: bool, thickness_pct: float) -> int:
    pts = 15 if bullish_fwd else 0
    if thickness_pct >= 6:
        pts += 10
    elif thickness_pct >= 3:
        pts += 6
    elif thickness_pct >= 1:
        pts += 3
    return pts


def _tk_score(last: float, tenkan: float, kijun: float) -> int:
    pts = 0
    if tenkan > kijun:
        pts += 12
    if last > kijun:
        pts += 8
    return pts


def _chikou_score(last: float, past_close: float, past_high: float) -> int:
    pts = 0
    if last > past_close:
        pts += 8
    if last > past_high:
        pts += 7
    return pts


def _reach_score(above_cloud_pct: float) -> int:
    if above_cloud_pct <= 3:
        return 10
    if above_cloud_pct <= 6:
        return 7
    if above_cloud_pct <= 10:
        return 3
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


def score_ichimoku(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None when there's no fresh cloud breakout.
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

    ich = compute_ichimoku(hist)
    bo = find_breakout(ich) if ich is not None else None
    if bo is None:
        return None

    last = float(ich["close"].iloc[-1])
    tenkan, kijun = ich["tenkan"].iloc[-1], ich["kijun"].iloc[-1]
    fwd_a, fwd_b = ich["fwd_a"].iloc[-1], ich["fwd_b"].iloc[-1]
    if pd.isna(tenkan) or pd.isna(kijun) or pd.isna(fwd_a) or pd.isna(fwd_b):
        return None
    bullish_fwd = bool(fwd_a > fwd_b)
    past_close = float(hist["Close"].iloc[-1 - _SHIFT])
    past_high = float(hist["High"].iloc[-1 - _SHIFT])

    s_fresh = _fresh_score(bo["bars_above"])
    s_cloud = _cloud_score(bullish_fwd, bo["thickness_pct"])
    s_tk = _tk_score(last, float(tenkan), float(kijun))
    s_chikou = _chikou_score(last, past_close, past_high)
    s_reach = _reach_score(bo["above_cloud_pct"])
    total = s_fresh + s_cloud + s_tk + s_chikou + s_reach

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "bars_above_cloud": bo["bars_above"],
        "cloud_top": round(bo["cloud_top"], 2),
        "above_cloud_pct": round(bo["above_cloud_pct"], 1),
        "cloud_thickness_pct": round(bo["thickness_pct"], 1),
        "forward_cloud": "bullish" if bullish_fwd else "bearish",
        "tenkan_above_kijun": bool(tenkan > kijun),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "freshness": s_fresh,
            "cloud": s_cloud,
            "tk": s_tk,
            "chikou": s_chikou,
            "reach": s_reach,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/ichimoku-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ichimoku-screener.json"
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
    parser = argparse.ArgumentParser(description="Ichimoku Cloud Breakout Screener")
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
        r = score_ichimoku(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n☁️  Ichimoku — {len(results)} cloud breakouts of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"{r['bars_above_cloud']}d above cloud (+{r['above_cloud_pct']:.1f}% over ${r['cloud_top']:.2f}), "
            f"fwd cloud {r['forward_cloud']}  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
