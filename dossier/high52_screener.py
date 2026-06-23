#!/usr/bin/env python3
"""
🏔️ 52-Week High Momentum Screener

Finds stocks quietly building toward new 52-week highs — the "quiet
strength" signal before the breakout. Unlike RVol (which catches the
volume explosion day), this screener finds stocks steadily pressing
toward annual highs on constructive price action.

The 52-week high effect is one of the most documented momentum anomalies
in finance (George & Hwang 2004): anchoring to the 52-week high creates
resistance that, when overcome, unleashes deferred buying pressure. This
screen catches stocks 0–10% below that level — prime pre-breakout
candidates.

Funnel architecture (3-stage, same as rvol / tao):
    Stage 1 → TradingView bulk API: filter universe by 3-month momentum
               + trend alignment (close > SMA50 AND SMA200, RSI 45-78)
    Stage 2 → Progressive funnel: 52-week high proximity (via TV's
               High.1Y), EMA stack, ADX trend confirmation
    Stage 3 → yfinance deep scan: exact 52w proximity, ROC-20, volume
               trend score

Scoring (0–100):
    52w high proximity  (35 pts) — closer to the high = more breakout pressure
    Momentum ROC-20     (30 pts) — 20-day rate of change (price momentum)
    Trend structure     (25 pts) — EMA/SMA alignment quality
    Volume quality      (10 pts) — volume expanding into the run

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)

Usage:
    python -m dossier.high52_screener                       # whole market
    python -m dossier.high52_screener --tickers NVDA,AAPL  # specific tickers
    python -m dossier.high52_screener --watchlist           # core watchlist only
    python -m dossier.high52_screener --top 20             # limit output
    python -m dossier.high52_screener --json               # machine output
    python -m dossier.high52_screener --quiet              # A+/A only

Output: docs/api/high52-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"The stocks near 52-week highs aren't tired. They're loaded." — Sam
"""

import argparse
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

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

# ─── Config ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from dossier.config import CORE_WATCHLIST
except ImportError:
    CORE_WATCHLIST = [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
        "AMD", "AVGO", "TSM", "MRVL", "QCOM",
        "JPM", "GS", "V", "MA",
        "PLTR", "COIN", "HOOD", "SOFI",
    ]

TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"

_TV_COLUMNS = [
    "name",                     # 0  ticker
    "description",              # 1  company name
    "close",                    # 2  last price
    "change",                   # 3  % change today
    "volume",                   # 4  session volume
    "average_volume_30d_calc",  # 5  30d avg volume
    "market_cap_basic",         # 6  market cap
    "SMA200",                   # 7  SMA 200
    "SMA50",                    # 8  SMA 50
    "EMA20",                    # 9  EMA 20
    "RSI",                      # 10 RSI(14)
    "ADX",                      # 11 ADX(14)
    "ATR",                      # 12 ATR(14)
    "Perf.W",                   # 13 weekly perf %
    "Perf.1M",                  # 14 monthly perf %
    "Recommend.All",            # 15 TV signal
    "High.1Y",                  # 16 1-year high (52-week high)
    "Perf.3M",                  # 17 3-month perf %
    "Perf.6M",                  # 18 6-month perf %
    "Low.1Y",                   # 19 1-year low
]

# ─── Funnel thresholds ────────────────────────────────────────────
_MAX_DIST_TO_52H = 10.0  # % below 52-week high — max to survive funnel
_MIN_CAP = 300_000_000   # $300M market-cap floor
_MIN_ADX = 18            # ADX floor — must be in a trend, not coiling


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_high52_candidates() -> list[dict]:
    """
    One POST to TradingView → stocks in strong 3-month uptrends
    above both SMA50 and SMA200 with RSI in a healthy range.
    Sorting by 3-month performance descends so the most momentum-charged
    names surface first; proximity to the 52-week high is refined in
    Stage 2 using the High.1Y column.
    """
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 300_000},
            {"left": "close", "operation": "greater", "right": 10},
            {"left": "market_cap_basic", "operation": "greater", "right": 300_000_000},
            # Must be above both moving averages — no falling knives
            {"left": "close", "operation": "greater", "right": "SMA50"},
            {"left": "close", "operation": "greater", "right": "SMA200"},
            # Strong recent momentum — proxy for proximity to highs
            {"left": "Perf.3M", "operation": "greater", "right": 8},
            # RSI healthy range
            {"left": "RSI", "operation": "greater", "right": 45},
            {"left": "RSI", "operation": "less", "right": 80},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "Perf.3M", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView High52 scan") or {}
    rows = data.get("data") or []

    results = []
    for item in rows:
        d = item.get("d", [])
        if len(d) < len(_TV_COLUMNS):
            continue
        ticker = d[0]
        if not ticker or d[2] is None:
            continue
        results.append({
            "ticker": ticker,
            "name": d[1] or ticker,
            "price": d[2],
            "change_pct": d[3] or 0,
            "volume": d[4] or 0,
            "avg_vol_30d": d[5] or 0,
            "market_cap": d[6] or 0,
            "sma_200": d[7],
            "sma_50": d[8],
            "ema_20": d[9],
            "rsi": d[10],
            "adx": d[11],
            "atr": d[12],
            "perf_1w": d[13],
            "perf_1m": d[14],
            "tv_signal": d[15],
            "high_1y": d[16],   # 52-week high from TradingView (may be None)
            "perf_3m": d[17],
            "perf_6m": d[18],
            "low_1y": d[19],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

def _dist_to_52h_tv(stock: dict) -> float | None:
    """% distance below TV's reported 1-year high. None if data is missing."""
    high = stock.get("high_1y")
    price = stock.get("price")
    if not high or not price or high <= 0:
        return None
    return (high - price) / high * 100


def _passes_proximity(stock: dict) -> bool:
    """True if within _MAX_DIST_TO_52H or if TV has no high_1y data (deferred to Stage 3)."""
    d = _dist_to_52h_tv(stock)
    return d is None or d <= _MAX_DIST_TO_52H


def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """Cut the TV universe to near-52-week-high candidates."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ HIGH-52 FUNNEL: {total} stocks from TradingView")

    def _cut(remaining, label, predicate):
        after = [s for s in remaining if predicate(s)]
        if verbose:
            print(f"  │  {label:<48} {len(remaining):>5} → {len(after)}")
        return after

    # 1. Within 10% of 52-week high (when TV has the data)
    survivors = _cut(
        stocks,
        f"Within {_MAX_DIST_TO_52H:.0f}% of 52-week high (or TV missing)",
        _passes_proximity,
    )

    # 2. Market cap ≥ $300M
    survivors = _cut(
        survivors,
        f"Market cap ≥ ${_MIN_CAP / 1e6:.0f}M",
        lambda s: (s.get("market_cap") or 0) >= _MIN_CAP,
    )

    # 3. ADX ≥ 18 — must be in a directional trend
    survivors = _cut(
        survivors,
        f"ADX ≥ {_MIN_ADX} (trending, not ranging)",
        lambda s: (s.get("adx") or 0) >= _MIN_ADX,
    )

    # 4. Price above EMA20 (short-term trend intact)
    survivors = _cut(
        survivors,
        "Close above EMA20",
        lambda s: s.get("ema_20") is not None and (s.get("price") or 0) > s["ema_20"],
    )

    # 5. Not a vertical blow-off (>25% in one month = too extended)
    survivors = _cut(
        survivors,
        "1-month gain ≤ 25% (not parabolic)",
        lambda s: abs(s.get("perf_1m") or 0) <= 25,
    )

    if verbose:
        print(f"  └─ {len(survivors)} candidates pass to Stage 3\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — YFINANCE DEEP SCAN + SCORING  ████
# ═══════════════════════════════════════════════════════════════════

def _prox_score(dist_pct: float) -> int:
    """35-pt scale: lower % below 52-week high = higher score."""
    if dist_pct <= 1.0:
        return 35   # at or through the high (breakout confirmed)
    if dist_pct <= 2.0:
        return 30
    if dist_pct <= 3.5:
        return 24
    if dist_pct <= 5.0:
        return 16
    if dist_pct <= 7.5:
        return 8
    return 3   # 7.5–10% away — eligible but modest proximity signal


def _roc_score(roc20: float) -> int:
    """30-pt scale: 20-day rate of change measures price momentum."""
    if roc20 >= 20:
        return 30
    if roc20 >= 12:
        return 24
    if roc20 >= 7:
        return 18
    if roc20 >= 3:
        return 10
    if roc20 >= 0:
        return 4
    return 0   # negative ROC while near 52wk high = warning sign


def _trend_score(price: float, ema20, ema50, sma200) -> int:
    """25-pt scale: reward cleaner EMA stacks."""
    score = 0
    if ema20 and price > ema20:
        score += 8
    if ema50 and price > ema50:
        score += 8
    if sma200 and isinstance(sma200, float) and not math.isnan(sma200) and price > sma200:
        score += 5
    if ema20 and ema50 and ema20 > ema50:
        score += 4
    return min(score, 25)


def _volume_score(hist: pd.DataFrame) -> int:
    """10-pt scale: volume expanding into the run is constructive."""
    try:
        vol = hist["Volume"]
        if len(vol) < 25:
            return 0
        recent_avg = float(vol.iloc[-5:].mean())
        prior_avg = float(vol.iloc[-25:-5].mean())
        if prior_avg <= 0:
            return 0
        ratio = recent_avg / prior_avg
        if ratio >= 1.3:
            return 10
        if ratio >= 1.1:
            return 6
        if ratio >= 0.9:
            return 3
        return 0   # volume fading into new highs = distribution risk
    except Exception:
        return 0


def score_high52(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep-scan a single ticker for 52-week-high momentum score.
    Returns None if the ticker doesn't qualify (too far from high, bad history, etc.).
    tv_data: pre-fetched TradingView dict; used for fast EMA/RSI lookups.
    """
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return None

    ok, _ = check_yfinance_history(hist, ticker, min_rows=60)
    if not ok:
        return None

    price = float(hist["Close"].iloc[-1])
    high_52w = float(hist["High"].max())

    if high_52w <= 0 or price <= 0:
        return None

    dist_pct = (high_52w - price) / high_52w * 100

    # Hard cap: more than 10% below 52-week high → skip
    if dist_pct > 10.0:
        return None

    # ROC-20: 20-day price rate of change
    if len(hist) >= 22:
        price_20d_ago = float(hist["Close"].iloc[-21])
        roc20 = (price - price_20d_ago) / price_20d_ago * 100 if price_20d_ago > 0 else 0.0
    else:
        roc20 = 0.0

    # EMA/SMA: prefer TV pre-computed values (more accurate for the prior session)
    ema20 = (tv_data or {}).get("ema_20") or float(
        hist["Close"].ewm(span=20, adjust=False).mean().iloc[-1]
    )
    ema50 = (tv_data or {}).get("sma_50") or float(
        hist["Close"].ewm(span=50, adjust=False).mean().iloc[-1]
    )
    _sma200_raw = (tv_data or {}).get("sma_200") or (
        hist["Close"].rolling(200).mean().iloc[-1]
    )
    sma200 = float(_sma200_raw) if _sma200_raw is not None else None

    # ── Scoring ──────────────────────────────────────────────────
    s_prox  = _prox_score(dist_pct)
    s_roc   = _roc_score(roc20)
    s_trend = _trend_score(price, ema20, ema50, sma200)
    s_vol   = _volume_score(hist)
    total   = s_prox + s_roc + s_trend + s_vol

    if total >= 80:
        grade = "A+"
    elif total >= 65:
        grade = "A"
    elif total >= 50:
        grade = "B"
    elif total >= 35:
        grade = "C"
    else:
        grade = "D"

    cap = (tv_data or {}).get("market_cap")
    at_new_high = dist_pct <= 1.0

    sma200_out = (
        round(sma200, 2)
        if sma200 is not None and not math.isnan(sma200)
        else None
    )

    return {
        "ticker": ticker,
        "name": (tv_data or {}).get("name") or ticker,
        "price": round(price, 2),
        "high_52w": round(high_52w, 2),
        "dist_to_52h_pct": round(dist_pct, 2),
        "at_new_high": at_new_high,
        "roc_20d": round(roc20, 2),
        "ema20": round(ema20, 2) if ema20 else None,
        "ema50": round(ema50, 2) if ema50 else None,
        "sma200": sma200_out,
        "rsi": (tv_data or {}).get("rsi"),
        "adx": (tv_data or {}).get("adx"),
        "perf_3m": (tv_data or {}).get("perf_3m"),
        "market_cap": cap,
        "score": total,
        "grade": grade,
        "score_breakdown": {
            "proximity": s_prox,
            "roc_20d": s_roc,
            "trend": s_trend,
            "volume": s_vol,
        },
    }


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT & FORMATTING  ████
# ═══════════════════════════════════════════════════════════════════

_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_RESET = "\033[0m"
_GRADE_COLOR = {"A+": _GREEN, "A": _GREEN, "B": _YELLOW, "C": _YELLOW, "D": _RED}


def _gc(grade: str) -> str:
    return f"{_GRADE_COLOR.get(grade, '')}{grade}{_RESET}"


def _fmt_cap(cap) -> str:
    if cap is None:
        return "N/A"
    if cap >= 1e12:
        return f"${cap / 1e12:.1f}T"
    if cap >= 1e9:
        return f"${cap / 1e9:.1f}B"
    return f"${cap / 1e6:.0f}M"


def print_results(results: list[dict], quiet: bool = False) -> None:
    for r in results:
        grade = r["grade"]
        if quiet and grade not in ("A+", "A"):
            continue
        dist = r["dist_to_52h_pct"]
        new_hi = " ★NEW HIGH" if r.get("at_new_high") else ""
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Dist:{dist:.1f}%  ROC20:{r['roc_20d']:+.1f}%  Score:{r['score']:>3}  "
            f"{_fmt_cap(r['market_cap'])}{new_hi}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/high52-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "high52-screener.json"
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


# ═══════════════════════════════════════════════════════════════════
# ████  MAIN  ████
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="52-Week High Momentum Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🏔️  52-Week High Screener — {len(tickers)} tickers\n")
        tv_map: dict[str, dict] = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🏔️  52-Week High Screener — watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🏔️  52-Week High Momentum Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_high52_candidates()
        print(f"     → {len(raw)} stocks in strong 3M+ uptrends\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_high52(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} near-high setups found")
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
    print(f"  🏔️   52-WEEK HIGH MOMENTUM SCREENER — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: Dist = % below 52-week high (lower = closer to breakout)")
    print(f"          ROC20 = 20-day price momentum (higher = stronger trend)\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
