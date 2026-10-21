#!/usr/bin/env python3
"""
🔥 ADX Trend Ignition Screener — ranging stocks that just started trending up

ADX (Wilder, 14) measures trend STRENGTH, not direction. A reading under 20 means
the stock has been drifting sideways; the cross up through 20 with +DI above -DI
is the moment a range turns into an up-trend. Catching that cross is the opposite
of chasing: the move is days old, and the stock spent weeks building the base.

Different from the other trend screens in the dossier:
  - Golden Cross / SMA200 reclaim / Ichimoku: price vs a level
  - Rs leadership / High52: already-extended leaders
  - THIS: trend-strength regime change (ADX through 20) with direction confirmed

Detection:
    Ignition → ADX now >= 20, ADX was below 20 within the last _IGNITE_WINDOW
               bars, +DI > -DI, and ADX is rising.

Scoring (0-100):
    Freshness (30 pts) — fewer bars since ADX crossed 20
    Slope     (20 pts) — ADX gain over the last 3 bars
    Direction (20 pts) — +DI minus -DI spread
    Alignment (20 pts) — close above a rising 50-day average
    Room      (10 pts) — ADX still in the 20-30 band (not yet exhausted)

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.adx_ignition_screener --tickers NVDA,AAPL
    python -m dossier.adx_ignition_screener --watchlist
    python -m dossier.adx_ignition_screener --json --no-save

Output: docs/api/adx-ignition-screener.json (served via GitHub Pages)

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

_PERIOD = 14
_TREND_LEVEL = 20.0        # ADX at/above this = trending
_IGNITE_WINDOW = 8         # ADX must have been below the level this recently
_SMA = 50
_MIN_ROWS = _SMA + 2 * _PERIOD + _IGNITE_WINDOW
_REQUIRED_COLS = ("High", "Low", "Close")


def compute_adx(hist: "pd.DataFrame", period: int = _PERIOD) -> "pd.DataFrame | None":
    """Wilder ADX with +DI / -DI. Returns columns adx, plus_di, minus_di."""
    if any(c not in hist.columns for c in _REQUIRED_COLS):
        return None
    high, low, close = hist["High"], hist["Low"], hist["Close"]
    up, down = high.diff(), -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()],
                   axis=1).max(axis=1)

    def wilder(s):
        return s.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    atr = wilder(tr)
    plus_di = 100 * wilder(plus_dm) / atr
    minus_di = 100 * wilder(minus_dm) / atr
    denom = (plus_di + minus_di).replace(0, float("nan"))
    dx = 100 * (plus_di - minus_di).abs() / denom
    adx = dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return pd.DataFrame({"adx": adx, "plus_di": plus_di, "minus_di": minus_di})


def find_ignition(ind: "pd.DataFrame") -> dict | None:
    """Return ignition facts if ADX recently crossed up through the trend level."""
    adx = ind["adx"]
    if len(adx) < _IGNITE_WINDOW + 4 or pd.isna(adx.iloc[-1]):
        return None
    now = float(adx.iloc[-1])
    plus_di, minus_di = float(ind["plus_di"].iloc[-1]), float(ind["minus_di"].iloc[-1])
    if now < _TREND_LEVEL or plus_di <= minus_di or now <= float(adx.iloc[-2]):
        return None
    # bars since the last reading below the level (1 == crossed on the latest bar)
    bars_since = None
    for i in range(1, _IGNITE_WINDOW + 1):
        v = adx.iloc[-1 - i]
        if pd.isna(v):
            return None
        if v < _TREND_LEVEL:
            bars_since = i
            break
    if bars_since is None:
        return None
    return {
        "adx": now,
        "plus_di": plus_di,
        "minus_di": minus_di,
        "bars_since_cross": bars_since,
        "adx_gain_3d": now - float(adx.iloc[-4]),
    }


def _fresh_score(bars: int) -> int:
    if bars <= 1:
        return 30
    if bars <= 3:
        return 24
    if bars <= 5:
        return 16
    return 8


def _slope_score(gain: float) -> int:
    if gain >= 6:
        return 20
    if gain >= 3:
        return 14
    if gain >= 1:
        return 8
    return 3


def _direction_score(spread: float) -> int:
    if spread >= 15:
        return 20
    if spread >= 10:
        return 15
    if spread >= 5:
        return 9
    return 4


def _alignment_score(last: float, sma: float, sma_prev: float) -> int:
    pts = 10 if last > sma else 0
    if sma > sma_prev:
        pts += 10
    return pts


def _room_score(adx: float) -> int:
    if adx <= 30:
        return 10
    if adx <= 35:
        return 5
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


def score_adx_ignition(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None when ADX hasn't just ignited.
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

    ind = compute_adx(hist)
    ign = find_ignition(ind) if ind is not None else None
    if ign is None:
        return None

    close = hist["Close"]
    sma = close.rolling(_SMA).mean()
    if pd.isna(sma.iloc[-1]) or pd.isna(sma.iloc[-6]):
        return None
    last = float(close.iloc[-1])
    spread = ign["plus_di"] - ign["minus_di"]

    s_fresh = _fresh_score(ign["bars_since_cross"])
    s_slope = _slope_score(ign["adx_gain_3d"])
    s_dir = _direction_score(spread)
    s_align = _alignment_score(last, float(sma.iloc[-1]), float(sma.iloc[-6]))
    s_room = _room_score(ign["adx"])
    total = s_fresh + s_slope + s_dir + s_align + s_room

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "adx": round(ign["adx"], 1),
        "bars_since_cross": ign["bars_since_cross"],
        "adx_gain_3d": round(ign["adx_gain_3d"], 1),
        "plus_di": round(ign["plus_di"], 1),
        "minus_di": round(ign["minus_di"], 1),
        "above_sma50": bool(last > float(sma.iloc[-1])),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "freshness": s_fresh,
            "slope": s_slope,
            "direction": s_dir,
            "alignment": s_align,
            "room": s_room,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/adx-ignition-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "adx-ignition-screener.json"
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
    parser = argparse.ArgumentParser(description="ADX Trend Ignition Screener")
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
        r = score_adx_ignition(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🔥  ADX Ignition — {len(results)} new trends of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"ADX {r['adx']:.1f} (+{r['adx_gain_3d']:.1f}/3d, crossed {r['bars_since_cross']}d ago), "
            f"+DI {r['plus_di']:.0f}/-DI {r['minus_di']:.0f}  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
