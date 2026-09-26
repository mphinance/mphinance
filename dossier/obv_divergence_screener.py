#!/usr/bin/env python3
"""
🔊 OBV Divergence Screener — Volume Says What Price Won't

Finds stocks where price action and On-Balance Volume (cumulative volume
flow) have been trending in OPPOSITE directions for the last month —
the "smart money is quietly building/dumping a position while price stays
boring" signal.

Different from every other screener in the dossier:
  - RVOL: flags ONE big volume day — this flags a multi-week volume TREND
  - Capitulation: hunts stocks already bottoming and reversing UP
  - NR7: range compression (volatility), not volume flow
  - Death/Golden Cross: two moving averages crossing, no volume component
  - THIS: cumulative volume flow (OBV) disagreeing with price trend over a
    30-day window — bullish divergence (price flat/down, OBV rising =
    accumulation) or bearish divergence (price flat/up, OBV falling =
    distribution), each scored by strength, consistency, and conviction

Funnel architecture (3-stage, same as death_cross / nr7 / rvol):
    Stage 1 → TradingView bulk API: liquid, non-penny, moderate RSI (avoid
               names already at an exhaustion extreme)
    Stage 2 → Python funnel: liquidity + market-cap floor
    Stage 3 → yfinance deep scan: compute OBV, regress price vs. OBV slope
               over 30 trading days, score the mismatch

Scoring (0–100):
    Divergence strength (40 pts) — how hard OBV disagrees with price (normalized
                                    by average daily volume)
    OBV consistency     (25 pts) — % of days OBV moved in the dominant direction
    Volume conviction    (20 pts) — volume on the "right side" days vs. the other
    Base compression     (15 pts) — tighter ATR% = a cleaner accumulation/
                                    distribution base, not noisy chop

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)

Usage:
    python -m dossier.obv_divergence_screener                  # whole market
    python -m dossier.obv_divergence_screener --tickers NVDA,AAPL
    python -m dossier.obv_divergence_screener --watchlist
    python -m dossier.obv_divergence_screener --direction bullish
    python -m dossier.obv_divergence_screener --top 20
    python -m dossier.obv_divergence_screener --json
    python -m dossier.obv_divergence_screener --quiet          # A+/A only
    python -m dossier.obv_divergence_screener --no-save        # skip JSON write

Output: docs/api/obv-divergence.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"Price is what everyone sees. Volume flow is what they hoped you wouldn't notice." — Sam
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

try:
    import yfinance as yf
except ImportError:
    print("❌  pip install yfinance")
    sys.exit(1)

try:
    from dossier.utils.validate_api import safe_json, check_yfinance_history
except ImportError:
    def safe_json(resp, context=""):
        try:
            return resp.json()
        except Exception as e:
            print(f"    [WARN] [{context}] not valid JSON: {e}", file=sys.stderr)
            return None

    def check_yfinance_history(df, ticker, min_rows=2):
        if df is None or df.empty:
            return False, f"{ticker}: empty history"
        if len(df) < min_rows:
            return False, f"{ticker}: only {len(df)} rows"
        return True, ""

try:
    from dossier.config import CORE_WATCHLIST
except ImportError:
    CORE_WATCHLIST = [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
        "AMD", "AVGO", "TSM", "MRVL", "QCOM",
        "JPM", "GS", "V", "MA",
        "PLTR", "COIN", "HOOD", "SOFI",
        "XOM", "OXY",
    ]

# ─── Config ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"
_LOOKBACK = 30          # trading days — the divergence window
_PRICE_FLAT_PCT = 0.02  # %/day threshold below which price counts as "flat/down" (bullish) or above as "flat/up" (bearish)
_OBV_MIN_NORM = 0.03    # min |OBV slope| in avg-volume-days/day to count as a real trend

_TV_COLUMNS = [
    "name",                     # 0  ticker
    "description",              # 1  company name
    "close",                    # 2  last price
    "change",                   # 3  % change today
    "volume",                   # 4  session volume
    "average_volume_30d_calc",  # 5  30-day avg volume
    "market_cap_basic",         # 6  market cap
    "RSI",                      # 7  RSI(14)
    "ADX",                      # 8  ADX(14)
]


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_candidates() -> list[dict]:
    """One POST to TradingView → liquid stocks, not already at an RSI extreme."""
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 300_000},
            {"left": "close", "operation": "greater", "right": 5},
            {"left": "RSI", "operation": "in_range", "right": [30, 70]},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "average_volume_30d_calc", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    data = safe_json(resp, "obv-divergence TV scan")
    if not data or "data" not in data:
        return []

    results = []
    for row in data["data"]:
        d = row.get("d", [])
        if len(d) < len(_TV_COLUMNS):
            continue
        try:
            results.append({
                "ticker":      d[0],
                "name":        d[1] or d[0],
                "price":       d[2],
                "change_pct":  d[3],
                "volume":      d[4],
                "avg_vol_30d": d[5],
                "market_cap":  d[6],
                "rsi":         d[7],
                "adx":         d[8],
            })
        except (IndexError, TypeError):
            continue
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PYTHON FUNNEL  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """Tighten the TradingView universe before expensive yfinance calls."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ OBV FUNNEL: {total} stocks from TradingView")

    survivors = [s for s in stocks if (
        (s["market_cap"] or 0) >= 300_000_000
        and (s["avg_vol_30d"] or 0) >= 150_000
    )]
    if verbose:
        print(f"  └─ Cap ≥$300M + Vol ≥150K ─────────→ {len(survivors)} ({total - len(survivors)} cut)\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  SCORING HELPERS (public — importable for tests)  ████
# ═══════════════════════════════════════════════════════════════════

def compute_obv(close: "pd.Series", volume: "pd.Series") -> "pd.Series":
    """Classic On-Balance Volume: cumulative +volume on up days, -volume on down days."""
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def detect_obv_divergence(close: "pd.Series", obv: "pd.Series", avg_volume: float,
                          lookback: int = _LOOKBACK) -> "dict | None":
    """
    Regress price and OBV over the trailing `lookback` bars and compare slopes.

    Returns {"direction": "bullish"|"bearish", "price_slope_pct": float,
    "obv_slope_norm": float} when the two trends disagree beyond the noise
    thresholds, else None.
    """
    if len(close) < lookback or len(obv) < lookback or not avg_volume or avg_volume <= 0:
        return None

    price_window = close.iloc[-lookback:].to_numpy(dtype=float)
    obv_window = obv.iloc[-lookback:].to_numpy(dtype=float)
    if np.isnan(price_window).any() or np.isnan(obv_window).any():
        return None

    x = np.arange(lookback, dtype=float)

    price_slope = np.polyfit(x, price_window, 1)[0]
    price_mean = price_window.mean()
    price_slope_pct = (price_slope / price_mean * 100) if price_mean else 0.0

    obv_slope = np.polyfit(x, obv_window, 1)[0]
    obv_slope_norm = obv_slope / avg_volume

    if price_slope_pct <= _PRICE_FLAT_PCT and obv_slope_norm >= _OBV_MIN_NORM:
        return {"direction": "bullish", "price_slope_pct": price_slope_pct,
                "obv_slope_norm": obv_slope_norm}
    if price_slope_pct >= -_PRICE_FLAT_PCT and obv_slope_norm <= -_OBV_MIN_NORM:
        return {"direction": "bearish", "price_slope_pct": price_slope_pct,
                "obv_slope_norm": obv_slope_norm}
    return None


def _divergence_score(obv_slope_norm: float) -> int:
    """Magnitude of the OBV/price disagreement (40 pts max)."""
    mag = abs(obv_slope_norm)
    if mag >= 0.12: return 40
    if mag >= 0.08: return 32
    if mag >= 0.05: return 24
    if mag >= 0.03: return 14
    return 6


def _consistency_score(obv_diffs: "pd.Series", direction: str) -> int:
    """% of days OBV moved in the dominant direction (25 pts max)."""
    if len(obv_diffs) == 0:
        return 0
    if direction == "bullish":
        frac = float((obv_diffs > 0).mean())
    else:
        frac = float((obv_diffs < 0).mean())
    if frac >= 0.65: return 25
    if frac >= 0.55: return 18
    if frac >= 0.45: return 10
    return 4


def _conviction_score(volume: "pd.Series", close: "pd.Series", direction: str) -> int:
    """Volume on the supportive side vs. the other side (20 pts max)."""
    changes = close.diff()
    up_vol = volume[changes > 0]
    down_vol = volume[changes < 0]
    up_mean = float(up_vol.mean()) if len(up_vol) else 0.0
    down_mean = float(down_vol.mean()) if len(down_vol) else 0.0

    if direction == "bullish":
        ratio = (up_mean / down_mean) if down_mean > 0 else (2.0 if up_mean > 0 else 0.0)
    else:
        ratio = (down_mean / up_mean) if up_mean > 0 else (2.0 if down_mean > 0 else 0.0)

    if ratio >= 1.5: return 20
    if ratio >= 1.2: return 14
    if ratio >= 1.0: return 8
    return 3


def _compression_score(atr_pct: float) -> int:
    """Tighter ATR% = a cleaner base, not noisy chop (15 pts max)."""
    if atr_pct <= 2.5: return 15
    if atr_pct <= 4.0: return 10
    if atr_pct <= 6.0: return 5
    return 1


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — DEEP SCAN (yfinance)  ████
# ═══════════════════════════════════════════════════════════════════

def score_obv_divergence(ticker: str, tv_data: "dict | None" = None,
                         direction_filter: "str | None" = None) -> "dict | None":
    """
    Deep scan a single ticker for a price/OBV divergence.

    Returns a result dict on success, None if data is insufficient, no
    divergence is detected, or `direction_filter` ("bullish"/"bearish")
    excludes the detected direction.
    """
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        ok, _ = check_yfinance_history(df, ticker, min_rows=60)
        if not ok:
            return None

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        avg_vol_30 = float(volume.rolling(30).mean().iloc[-1])
        obv = compute_obv(close, volume)

        div = detect_obv_divergence(close, obv, avg_vol_30, lookback=_LOOKBACK)
        if div is None:
            return None
        if direction_filter and div["direction"] != direction_filter:
            return None

        # ATR% — base compression over the same window
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        current_price = float(close.iloc[-1])
        atr_pct = float(atr / current_price * 100) if current_price else 0.0

        obv_diffs = obv.diff().iloc[-_LOOKBACK:]
        price_window = close.iloc[-_LOOKBACK:]
        volume_window = volume.iloc[-_LOOKBACK:]

        div_pts = _divergence_score(div["obv_slope_norm"])
        cons_pts = _consistency_score(obv_diffs, div["direction"])
        conv_pts = _conviction_score(volume_window, price_window, div["direction"])
        comp_pts = _compression_score(atr_pct)

        total = div_pts + cons_pts + conv_pts + comp_pts

        if   total >= 80: grade = "A+"
        elif total >= 65: grade = "A"
        elif total >= 50: grade = "B"
        elif total >= 35: grade = "C"
        else:             grade = "D"

        return {
            "ticker":           ticker,
            "name":             (tv_data or {}).get("name", ticker),
            "price":            round(current_price, 2),
            "score":            total,
            "grade":            grade,
            "direction":        div["direction"],
            "price_slope_pct":  round(div["price_slope_pct"], 3),
            "obv_slope_norm":   round(div["obv_slope_norm"], 3),
            "atr_pct":          round(atr_pct, 2),
            "market_cap":       (tv_data or {}).get("market_cap"),
            "change_pct":       (tv_data or {}).get("change_pct", 0),
            "score_breakdown": {
                "divergence":  div_pts,
                "consistency": cons_pts,
                "conviction":  conv_pts,
                "compression": comp_pts,
            },
        }

    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT & FORMATTING  ████
# ═══════════════════════════════════════════════════════════════════

_GRADE_COLOR = {
    "A+": "\033[95m", "A": "\033[91m", "B": "\033[33m",
    "C": "\033[93m", "D": "\033[90m",
}
_RESET = "\033[0m"
_DIR_ICON = {"bullish": "🟢", "bearish": "🔴"}


def _gc(grade: str) -> str:
    return f"{_GRADE_COLOR.get(grade, '')}{grade}{_RESET}"


def _fmt_cap(cap) -> str:
    if cap is None:
        return "—"
    if cap >= 1e12:
        return f"${cap/1e12:.1f}T"
    if cap >= 1e9:
        return f"${cap/1e9:.1f}B"
    return f"${cap/1e6:.0f}M"


def print_results(results: list[dict], quiet: bool = False) -> None:
    for r in results:
        if quiet and r["grade"] not in ("A+", "A"):
            continue
        icon = _DIR_ICON.get(r["direction"], "")
        print(
            f"  {_gc(r['grade']):>14}  {icon} {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"{r['direction']:<8}  OBV/day:{r['obv_slope_norm']:+.3f}  "
            f"ATR%:{r['atr_pct']:<5}  Score:{r['score']:>3}  {_fmt_cap(r['market_cap'])}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/obv-divergence.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "obv-divergence.json"
    grade_counts: dict[str, int] = {}
    direction_counts: dict[str, int] = {}
    for r in results:
        grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1
        direction_counts[r["direction"]] = direction_counts.get(r["direction"], 0) + 1
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(results),
        "grade_counts": grade_counts,
        "direction_counts": direction_counts,
        "results": results,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\n  💾  Saved {len(results)} results → {out_path}")


# ═══════════════════════════════════════════════════════════════════
# ████  MAIN  ████
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="OBV Divergence Screener")
    parser.add_argument("--tickers",   help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--direction", choices=["bullish", "bearish"],
                        help="Only surface one direction (default: both)")
    parser.add_argument("--top",       type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json",      action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet",     action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save",   action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🔊  OBV Divergence Screener — {len(tickers)} tickers\n")
        tv_map: dict[str, dict] = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🔊  OBV Divergence Screener — watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🔊  OBV Divergence Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_candidates()
        print(f"     → {len(raw)} liquid, non-extreme-RSI stocks\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("avg_vol_30d") or 0, reverse=True)

    print(f"  🧪 Stage 2: Deep scanning {len(candidates)} candidates for OBV divergence...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_obv_divergence(ticker, tv_data=tv_map.get(ticker, c),
                                 direction_filter=args.direction)
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} divergences found")
        time.sleep(0.05)

    results.sort(key=lambda r: r["score"], reverse=True)

    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    grade_counts: dict[str, int] = {}
    for r in results:
        grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1

    print(f"\n{'═' * 100}")
    print(f"  🔊   OBV DIVERGENCE — {len(results)} price/volume-flow disagreements")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: OBV/day = normalized OBV slope (avg-volume-days per day)  |  "
          f"bullish = price flat/down + OBV rising (accumulation)  |  "
          f"bearish = price flat/up + OBV falling (distribution)\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
