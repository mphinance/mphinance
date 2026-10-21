#!/usr/bin/env python3
"""
🪃 Bullish RSI Divergence Screener — price makes a lower low, momentum doesn't

Classic reversal tell: price sells off to a new swing low below the previous one,
but RSI(14) prints a HIGHER low at the second bottom. Sellers are pushing price
further for less and less momentum. Detected on confirmed swing lows only (a
low that is the lowest of the 3 bars either side), so nothing repaints.

Different from the other reversal screens in the dossier:
  - OBV divergence: volume-flow slope vs price over a window
  - RSI(2) pullback / capitulation: oversold in an uptrend / a washout bar
  - THIS: two discrete swing lows, price lower and RSI higher, first low
    washed out (RSI < 40), and price has since lifted off the second low

Detection:
    Swing low 1 (older) and swing low 2 (recent, within _FRESH_WINDOW bars):
        low2 < low1 by at least _MIN_PRICE_DROP, RSI2 > RSI1 by at least
        _MIN_RSI_RISE, RSI1 < _RSI1_MAX, pivots _MIN_GAP+ bars apart.
    Still alive → latest close above low2 (the pivot has not been taken out).

Scoring (0-100):
    Divergence (35 pts) — RSI points gained between the two lows
    Washout    (20 pts) — how oversold the first low was
    Turn       (20 pts) — bounce off the second low, in ATRs
    Fresh      (15 pts) — fewer bars since the second low
    Volume     (10 pts) — second-low volume below the first (selling fading)

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.rsi_divergence_screener --tickers NVDA,AAPL
    python -m dossier.rsi_divergence_screener --json --no-save

Output: docs/api/rsi-divergence-screener.json (served via GitHub Pages)

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

_RSI_PERIOD = 14
_ATR_PERIOD = 14
_PIVOT_SIDE = 3            # bars each side that must be higher for a swing low
_SEARCH_WINDOW = 60        # how far back the first low may sit
_FRESH_WINDOW = 10         # second low must be this recent (bars before today)
_MIN_GAP = 5               # min bars between the two lows
_MIN_PRICE_DROP = 0.005    # low2 at least 0.5% under low1
_MIN_RSI_RISE = 3.0        # RSI points higher at low2
_RSI1_MAX = 40.0           # first low must be washed out
_MIN_ROWS = 80
_REQUIRED_COLS = ("High", "Low", "Close", "Volume")


def compute_rsi(close: "pd.Series", period: int = _RSI_PERIOD) -> "pd.Series":
    """Wilder RSI. A flat-loss window yields 100, a flat-gain-less window 0."""
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - 100 / (1 + rs)
    return rsi.where(loss != 0, 100.0).where(~((gain == 0) & (loss == 0)), 50.0)


def find_swing_lows(low: "pd.Series", side: int = _PIVOT_SIDE) -> list[int]:
    """Positions whose low is strictly below the `side` bars either side (confirmed pivots)."""
    vals = low.to_numpy(dtype=float)
    out = []
    for i in range(side, len(vals) - side):
        window_l, window_r = vals[i - side:i], vals[i + 1:i + 1 + side]
        if vals[i] < window_l.min() and vals[i] <= window_r.min():
            out.append(i)
    return out


def find_divergence(hist: "pd.DataFrame", rsi: "pd.Series") -> dict | None:
    """Latest qualifying (older low, recent low) pair, or None."""
    n = len(hist)
    low, close = hist["Low"], hist["Close"]
    pivots = [p for p in find_swing_lows(low) if n - 1 - p <= _SEARCH_WINDOW + _FRESH_WINDOW]
    recent = [p for p in pivots if n - 1 - p <= _FRESH_WINDOW]
    if not recent:
        return None
    p2 = recent[-1]
    if pd.isna(rsi.iloc[p2]):
        return None
    for p1 in reversed([p for p in pivots if p2 - p >= _MIN_GAP]):
        if pd.isna(rsi.iloc[p1]):
            continue
        l1, l2 = float(low.iloc[p1]), float(low.iloc[p2])
        r1, r2 = float(rsi.iloc[p1]), float(rsi.iloc[p2])
        if l2 < l1 * (1 - _MIN_PRICE_DROP) and r2 >= r1 + _MIN_RSI_RISE and r1 < _RSI1_MAX:
            if float(close.iloc[-1]) <= l2:
                return None  # pivot already taken out
            return {"p1": p1, "p2": p2, "low1": l1, "low2": l2, "rsi1": r1, "rsi2": r2}
    return None


def _divergence_score(rise: float) -> int:
    if rise >= 15:
        return 35
    if rise >= 10:
        return 27
    if rise >= 6:
        return 19
    return 11


def _washout_score(rsi1: float) -> int:
    if rsi1 < 20:
        return 20
    if rsi1 < 27:
        return 15
    if rsi1 < 33:
        return 10
    return 5


def _turn_score(atrs: float) -> int:
    if atrs >= 2.0:
        return 20
    if atrs >= 1.0:
        return 14
    if atrs >= 0.5:
        return 8
    return 3


def _fresh_score(bars: int) -> int:
    if bars <= 3:
        return 15
    if bars <= 6:
        return 10
    return 5


def _volume_score(ratio: float) -> int:
    if ratio <= 0.7:
        return 10
    if ratio <= 1.0:
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


def score_rsi_divergence(ticker: str, hist: "pd.DataFrame | None" = None) -> dict | None:
    """Score one ticker; returns None without a live bullish RSI divergence.
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

    close, high, low, volume = hist["Close"], hist["High"], hist["Low"], hist["Volume"]
    rsi = compute_rsi(close)
    div = find_divergence(hist, rsi)
    if div is None:
        return None

    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()],
                   axis=1).max(axis=1)
    atr = float(tr.rolling(_ATR_PERIOD).mean().iloc[-1])
    if pd.isna(atr) or atr <= 0:
        return None

    last = float(close.iloc[-1])
    bars_since = len(hist) - 1 - div["p2"]
    rise = div["rsi2"] - div["rsi1"]
    bounce = (last - div["low2"]) / atr
    v1 = float(volume.iloc[div["p1"]])
    vol_ratio = float(volume.iloc[div["p2"]]) / v1 if v1 > 0 else 1.0

    s_div = _divergence_score(rise)
    s_wash = _washout_score(div["rsi1"])
    s_turn = _turn_score(bounce)
    s_fresh = _fresh_score(bars_since)
    s_vol = _volume_score(vol_ratio)
    total = s_div + s_wash + s_turn + s_fresh + s_vol

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "low1": round(div["low1"], 2),
        "low2": round(div["low2"], 2),
        "rsi_low1": round(div["rsi1"], 1),
        "rsi_low2": round(div["rsi2"], 1),
        "rsi_now": round(float(rsi.iloc[-1]), 1),
        "rsi_rise": round(rise, 1),
        "bars_between_lows": div["p2"] - div["p1"],
        "bars_since_low2": bars_since,
        "bounce_atr": round(bounce, 2),
        "volume_ratio_low2_vs_low1": round(vol_ratio, 2),
        "invalidation": round(div["low2"], 2),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "divergence": s_div,
            "washout": s_wash,
            "turn": s_turn,
            "freshness": s_fresh,
            "volume": s_vol,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/rsi-divergence-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "rsi-divergence-screener.json"
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
    parser = argparse.ArgumentParser(description="Bullish RSI Divergence Screener")
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
        r = score_rsi_divergence(t)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🪃  RSI Divergence — {len(results)} setups of {len(tickers)} scanned\n")
    for r in results:
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"low ${r['low2']:.2f} < ${r['low1']:.2f}, RSI {r['rsi_low1']:.0f} → {r['rsi_low2']:.0f} "
            f"({r['bars_since_low2']}d ago), invalidation ${r['invalidation']:.2f}  "
            f"Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
