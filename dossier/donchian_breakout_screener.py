#!/usr/bin/env python3
"""
🐢 Donchian Turtle Breakout Screener — fresh closes above the 55-day channel high

The Turtle System 2 entry: buy the close that clears the highest high of the prior
55 sessions. It is a pure price-structure signal (no indicator smoothing), so it
fires on names the MA-based screens only reach days later. Each hit carries the
Turtle risk math: N = 20-day ATR, initial stop = breakout level - 2N, and the
percent of price that stop risks.

Different from the other breakout screens in the dossier:
  - High52 / RS leadership: proximity to the 52-week high (a level, not a clear)
  - Ichimoku / SMA200 reclaim: price vs a derived line
  - THIS: a close that cleared 55 sessions of highs, within the last few bars,
    with volume and risk-in-ATRs attached

Detection:
    Breakout → within the last _FRESH_WINDOW bars a close exceeded the prior
               55-day high (excluding that bar), and the latest close still
               holds at/above that breakout level.

Scoring (0-100):
    Freshness (30 pts) — fewer bars since the breakout close
    Volume    (25 pts) — breakout-bar volume vs the 50-day average
    Thrust    (20 pts) — breakout close above the channel, measured in ATRs
    Trend     (15 pts) — close above a rising 200-day average
    Close     (10 pts) — latest close in the top of its day range

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.donchian_breakout_screener --tickers NVDA,AAPL
    python -m dossier.donchian_breakout_screener --json --no-save

Output: docs/api/donchian-breakout-screener.json (served via GitHub Pages)

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

_CHANNEL = 55              # Turtle System 2 entry lookback
_ATR_PERIOD = 20           # Turtle "N"
_FRESH_WINDOW = 3          # breakout must be this recent (bars, 0 == today)
_STOP_N = 2.0              # initial stop distance in N
_SMA_LONG = 200
_VOL_AVG = 50
_MIN_ROWS = _SMA_LONG + 10
_REQUIRED_COLS = ("High", "Low", "Close", "Volume")


def compute_channel(hist: "pd.DataFrame") -> "pd.DataFrame | None":
    """Prior-55-bar high (shifted so a bar never compares to itself) and 20-bar ATR."""
    if any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    high, low, close = hist["High"], hist["Low"], hist["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()],
                   axis=1).max(axis=1)
    return pd.DataFrame({
        "channel_high": high.rolling(_CHANNEL).max().shift(1),
        "atr": tr.rolling(_ATR_PERIOD).mean(),
    })


def find_breakout(hist: "pd.DataFrame", ch: "pd.DataFrame") -> dict | None:
    """Most recent in-window close above the prior channel high that still holds."""
    close = hist["Close"]
    last = float(close.iloc[-1])
    for back in range(_FRESH_WINDOW + 1):
        i = len(close) - 1 - back
        level, atr = ch["channel_high"].iloc[i], ch["atr"].iloc[i]
        if pd.isna(level) or pd.isna(atr) or atr <= 0:
            continue
        if float(close.iloc[i]) > float(level):
            if last < float(level):
                return None  # failed back into the channel
            return {"bars_since": back, "level": float(level), "atr": float(atr), "idx": i}
    return None


def _fresh_score(bars: int) -> int:
    return {0: 30, 1: 22, 2: 14}.get(bars, 8)


def _volume_score(ratio: float) -> int:
    if ratio >= 2.0:
        return 25
    if ratio >= 1.5:
        return 19
    if ratio >= 1.0:
        return 11
    return 4


def _thrust_score(atrs: float) -> int:
    if atrs >= 1.0:
        return 20
    if atrs >= 0.5:
        return 14
    if atrs >= 0.2:
        return 8
    return 3


def _trend_score(last: float, sma: float, sma_prev: float) -> int:
    pts = 8 if last > sma else 0
    if sma > sma_prev:
        pts += 7
    return pts


def _close_score(pos: float) -> int:
    if pos >= 0.8:
        return 10
    if pos >= 0.5:
        return 6
    return 2


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


def score_donchian_breakout(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None without a fresh, holding 55-day breakout.
    `hist` may be injected (tests); otherwise fetched from yfinance."""
    if hist is None:
        try:
            hist = yf.Ticker(ticker).history(period="2y", interval="1d")
        except Exception:
            return None
    ok, _ = check_yfinance_history(hist, ticker, min_rows=_MIN_ROWS)
    if not ok or any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    hist = hist.dropna(subset=list(_REQUIRED_COLS))
    if len(hist) < _MIN_ROWS:
        return None

    ch = compute_channel(hist)
    bo = find_breakout(hist, ch) if ch is not None else None
    if bo is None:
        return None

    close, volume = hist["Close"], hist["Volume"]
    sma = close.rolling(_SMA_LONG).mean()
    vol_avg = volume.rolling(_VOL_AVG).mean().shift(1)
    if pd.isna(sma.iloc[-1]) or pd.isna(sma.iloc[-11]) or pd.isna(vol_avg.iloc[bo["idx"]]) \
            or vol_avg.iloc[bo["idx"]] <= 0:
        return None

    last = float(close.iloc[-1])
    vol_ratio = float(volume.iloc[bo["idx"]]) / float(vol_avg.iloc[bo["idx"]])
    thrust = (float(close.iloc[bo["idx"]]) - bo["level"]) / bo["atr"]
    rng = float(hist["High"].iloc[-1]) - float(hist["Low"].iloc[-1])
    pos = (last - float(hist["Low"].iloc[-1])) / rng if rng > 0 else 0.5
    stop = bo["level"] - _STOP_N * bo["atr"]

    s_fresh = _fresh_score(bo["bars_since"])
    s_vol = _volume_score(vol_ratio)
    s_thrust = _thrust_score(thrust)
    s_trend = _trend_score(last, float(sma.iloc[-1]), float(sma.iloc[-11]))
    s_close = _close_score(pos)
    total = s_fresh + s_vol + s_thrust + s_trend + s_close

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "channel_high": round(bo["level"], 2),
        "bars_since_breakout": bo["bars_since"],
        "volume_ratio": round(vol_ratio, 2),
        "thrust_atr": round(thrust, 2),
        "atr20": round(bo["atr"], 2),
        "stop_2n": round(stop, 2),
        "risk_pct": round((last - stop) / last * 100, 1),
        "above_sma200": bool(last > float(sma.iloc[-1])),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "freshness": s_fresh,
            "volume": s_vol,
            "thrust": s_thrust,
            "trend": s_trend,
            "close": s_close,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/donchian-breakout-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "donchian-breakout-screener.json"
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
    parser = argparse.ArgumentParser(description="Donchian Turtle Breakout Screener")
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
        r = score_donchian_breakout(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🐢  Donchian 55 — {len(results)} breakouts of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"cleared ${r['channel_high']:.2f} {r['bars_since_breakout']}d ago, "
            f"vol {r['volume_ratio']:.1f}x, stop ${r['stop_2n']:.2f} ({r['risk_pct']:.1f}% risk)  "
            f"Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
