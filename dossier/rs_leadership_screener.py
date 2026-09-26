#!/usr/bin/env python3
"""
📶 RS Leadership Screener — Relative-Strength Line Making New Highs vs SPY

Every other screener in the dossier measures a stock against ITSELF (its own
52-week high, its own moving averages, its own volume history). This one
measures it against the MARKET: the classic IBD/O'Neil "RS line" is the
ratio of a stock's price to a benchmark's price (here, SPY). When that ratio
makes a new high, the stock is outperforming the market on a relative basis
— often BEFORE its own price confirms with a new high of its own. That lead
time is the signal: institutions rotating into a name show up in relative
strength before the breakout is obvious on the price chart alone.

Different from every other screener in the dossier:
  - High52: absolute price near its own annual high (ignores the market)
  - Sector Rotation: sector-level RS (ETF vs ETF), not single-stock vs SPY
  - THIS: single-stock RS LINE (price / SPY price) at a ~6-month high,
    with a bonus for the "leading divergence" case — RS confirms new
    leadership while price itself hasn't broken out yet

Funnel architecture (3-stage, same as nr7 / high52 / rvol):
    Stage 1 → TradingView bulk API: uptrend universe (above SMA50,
               positive 6-month performance, liquid)
    Stage 2 → Progressive funnel: liquidity, market cap, RSI sanity band
    Stage 3 → yfinance deep scan: build the RS line (stock/SPY) over a
               ~126-session (6-month) lookback, score its proximity to a
               new high, its momentum, price trend, and leadership timing

Scoring (0-100):
    RS proximity to high  (35 pts) — how close the RS ratio is to its own
                                       126-session high (lower gap = better)
    RS momentum           (25 pts) — 20-day rate of change of the RS ratio
    Trend structure        (25 pts) — price EMA/SMA stack quality
    Leadership timing      (15 pts) — RS at a new high while price is NOT
                                       yet at its own 6-month high scores
                                       full marks (early divergence); RS and
                                       price confirming together scores half

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.rs_leadership_screener                       # whole market
    python -m dossier.rs_leadership_screener --tickers NVDA,AAPL  # specific tickers
    python -m dossier.rs_leadership_screener --watchlist          # core watchlist only
    python -m dossier.rs_leadership_screener --top 20             # limit output
    python -m dossier.rs_leadership_screener --json               # machine output
    python -m dossier.rs_leadership_screener --quiet              # A+/A only

Output: docs/api/rs-leadership-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"Price confirms last. The ratio to the index tells you first." — Sam
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

try:
    from dossier.config import CORE_WATCHLIST
except ImportError:
    CORE_WATCHLIST = [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
        "AMD", "AVGO", "TSM", "MRVL", "QCOM",
        "JPM", "GS", "V", "MA",
        "PLTR", "COIN", "HOOD", "SOFI",
    ]

# ─── Config ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"
BENCHMARK = "SPY"
RS_LOOKBACK = 126  # ~6 trading months — the RS line's "recent high" window

_TV_COLUMNS = [
    "name", "description", "close", "change", "volume",
    "average_volume_30d_calc", "market_cap_basic", "SMA200", "SMA50",
    "EMA20", "RSI", "ADX", "Perf.1M", "Perf.3M", "Perf.6M",
]

_MIN_CAP = 300_000_000
_MIN_VOL = 300_000


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_rs_candidates() -> list[dict]:
    """Uptrend universe: above SMA50, positive 6-month performance, liquid."""
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": _MIN_VOL},
            {"left": "close", "operation": "greater", "right": 8},
            {"left": "market_cap_basic", "operation": "greater", "right": _MIN_CAP},
            {"left": "close", "operation": "greater", "right": "SMA50"},
            {"left": "Perf.6M", "operation": "greater", "right": 0},
            {"left": "RSI", "operation": "greater", "right": 35},
            {"left": "RSI", "operation": "less", "right": 85},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "Perf.6M", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView RS Leadership scan") or {}
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
            "ticker": ticker, "name": d[1] or ticker, "price": d[2],
            "change_pct": d[3] or 0, "volume": d[4] or 0,
            "avg_vol_30d": d[5] or 0, "market_cap": d[6] or 0,
            "sma_200": d[7], "sma_50": d[8], "ema_20": d[9],
            "rsi": d[10], "adx": d[11], "perf_1m": d[12],
            "perf_3m": d[13], "perf_6m": d[14],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ RS LEADERSHIP FUNNEL: {total} stocks from TradingView")

    def _cut(remaining, label, predicate):
        after = [s for s in remaining if predicate(s)]
        if verbose:
            print(f"  │  {label:<48} {len(remaining):>5} → {len(after)}")
        return after

    survivors = _cut(
        stocks, f"Market cap ≥ ${_MIN_CAP / 1e6:.0f}M",
        lambda s: (s.get("market_cap") or 0) >= _MIN_CAP,
    )
    survivors = _cut(
        survivors, f"Avg volume ≥ {_MIN_VOL // 1000}k (liquid)",
        lambda s: (s.get("avg_vol_30d") or 0) >= _MIN_VOL,
    )
    survivors = _cut(
        survivors, "Close above EMA20 (short-term trend intact)",
        lambda s: s.get("ema_20") is not None and (s.get("price") or 0) > s["ema_20"],
    )

    if verbose:
        print(f"  └─ {len(survivors)} candidates pass to Stage 3\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — RS LINE + SCORING  ████
# ═══════════════════════════════════════════════════════════════════

def _rs_series(stock_close: pd.Series, spy_close: pd.Series) -> "pd.Series | None":
    """Aligned stock/SPY ratio series over their shared trading dates."""
    common = stock_close.index.intersection(spy_close.index)
    if len(common) < 60:
        return None
    return stock_close.reindex(common) / spy_close.reindex(common)


def _rs_proximity_score(dist_pct: float) -> int:
    """35-pt scale: lower % below the RS line's lookback high = higher score."""
    if dist_pct <= 0.5:
        return 35
    if dist_pct <= 1.5:
        return 29
    if dist_pct <= 3.0:
        return 22
    if dist_pct <= 5.0:
        return 14
    if dist_pct <= 8.0:
        return 6
    return 0


def _rs_momentum_score(rs_roc20: float) -> int:
    """25-pt scale: 20-session rate of change of the RS ratio itself."""
    if rs_roc20 >= 10:
        return 25
    if rs_roc20 >= 5:
        return 19
    if rs_roc20 >= 2:
        return 12
    if rs_roc20 >= 0:
        return 5
    return 0  # RS ratio falling — losing relative ground even if price is up


def _trend_score(price: float, ema20, ema50, sma200) -> int:
    """25-pt scale: reward cleaner EMA/SMA stacks."""
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


def _leadership_bonus(rs_dist_pct: float, price_dist_pct: float) -> int:
    """
    15-pt scale: the timing tell.

    RS at a new (or near-new) high while price is still meaningfully below
    ITS OWN recent high is early leadership — the market hasn't caught up
    to the outperformance yet. Full marks. If both RS and price are
    confirming new highs together, the move is already validated but no
    longer "early" — half marks. Otherwise, no divergence signal.
    """
    rs_at_high = rs_dist_pct <= 1.5
    if not rs_at_high:
        return 0
    if price_dist_pct > 3.0:
        return 15  # RS leads, price hasn't confirmed yet — the early tell
    return 7  # RS and price confirming together


def score_rs_leadership(ticker: str, spy_hist: pd.DataFrame, tv_data: dict | None = None) -> dict | None:
    """
    Deep-scan a single ticker for RS-line leadership score.
    spy_hist: pre-fetched SPY daily history (shared across the whole run).
    Returns None if history is too short or the RS ratio can't be built.
    """
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return None

    ok, _ = check_yfinance_history(hist, ticker, min_rows=130)
    if not ok:
        return None
    ok_spy, _ = check_yfinance_history(spy_hist, BENCHMARK, min_rows=130)
    if not ok_spy:
        return None

    price = float(hist["Close"].iloc[-1])
    if price <= 0:
        return None

    rs = _rs_series(hist["Close"], spy_hist["Close"])
    if rs is None or len(rs) < 60:
        return None

    lookback = min(len(rs), RS_LOOKBACK)
    rs_window = rs.iloc[-lookback:]
    rs_high = float(rs_window.max())
    rs_now = float(rs.iloc[-1])
    if rs_high <= 0:
        return None
    rs_dist_pct = max(0.0, (rs_high - rs_now) / rs_high * 100)

    if len(rs) >= 21:
        rs_20d_ago = float(rs.iloc[-21])
        rs_roc20 = (rs_now - rs_20d_ago) / rs_20d_ago * 100 if rs_20d_ago > 0 else 0.0
    else:
        rs_roc20 = 0.0

    price_window = hist["Close"].iloc[-lookback:]
    price_high = float(price_window.max())
    price_dist_pct = (price_high - price) / price_high * 100 if price_high > 0 else 0.0

    ema20 = (tv_data or {}).get("ema_20") or float(
        hist["Close"].ewm(span=20, adjust=False).mean().iloc[-1]
    )
    ema50 = (tv_data or {}).get("sma_50") or float(
        hist["Close"].ewm(span=50, adjust=False).mean().iloc[-1]
    )
    _sma200_raw = (tv_data or {}).get("sma_200") or hist["Close"].rolling(200).mean().iloc[-1]
    sma200 = float(_sma200_raw) if _sma200_raw is not None else None

    s_prox = _rs_proximity_score(rs_dist_pct)
    s_mom = _rs_momentum_score(rs_roc20)
    s_trend = _trend_score(price, ema20, ema50, sma200)
    s_lead = _leadership_bonus(rs_dist_pct, price_dist_pct)
    total = s_prox + s_mom + s_trend + s_lead

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

    sma200_out = round(sma200, 2) if sma200 is not None and not math.isnan(sma200) else None

    return {
        "ticker": ticker,
        "name": (tv_data or {}).get("name") or ticker,
        "price": round(price, 2),
        "rs_ratio": round(rs_now, 5),
        "dist_to_rs_high_pct": round(rs_dist_pct, 2),
        "rs_new_high": rs_dist_pct <= 1.5,
        "rs_roc_20d": round(rs_roc20, 2),
        "price_dist_to_6m_high_pct": round(price_dist_pct, 2),
        "leading_divergence": s_lead == 15,
        "ema20": round(ema20, 2) if ema20 else None,
        "ema50": round(ema50, 2) if ema50 else None,
        "sma200": sma200_out,
        "rsi": (tv_data or {}).get("rsi"),
        "adx": (tv_data or {}).get("adx"),
        "market_cap": (tv_data or {}).get("market_cap"),
        "score": total,
        "grade": grade,
        "score_breakdown": {
            "rs_proximity": s_prox,
            "rs_momentum": s_mom,
            "trend": s_trend,
            "leadership_timing": s_lead,
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
        tag = " ★LEADING" if r.get("leading_divergence") else ""
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"RSΔ:{r['dist_to_rs_high_pct']:.1f}%  RSmom:{r['rs_roc_20d']:+.1f}%  "
            f"Score:{r['score']:>3}  {_fmt_cap(r['market_cap'])}{tag}"
        )


def _save_api_output(results: list[dict]) -> None:
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "rs-leadership-screener.json"
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
    parser = argparse.ArgumentParser(description="RS Leadership Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    try:
        spy_hist = yf.Ticker(BENCHMARK).history(period="1y", interval="1d")
    except Exception as e:
        print(f"❌  Could not fetch {BENCHMARK} benchmark history: {e}")
        sys.exit(1)
    ok_spy, msg = check_yfinance_history(spy_hist, BENCHMARK, min_rows=130)
    if not ok_spy:
        print(f"❌  {msg}")
        sys.exit(1)

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n📶  RS Leadership Screener — {len(tickers)} tickers\n")
        tv_map: dict[str, dict] = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n📶  RS Leadership Screener — watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n📶  RS Leadership Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_rs_candidates()
        print(f"     → {len(raw)} stocks in uptrends with positive 6M performance\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates vs {BENCHMARK}...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        if ticker == BENCHMARK:
            continue
        r = score_rs_leadership(ticker, spy_hist, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} leadership setups found")
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
    print(f"  📶   RS LEADERSHIP SCREENER — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: RSΔ = % below the {RS_LOOKBACK}-session RS-line high (stock/SPY ratio)")
    print(f"          ★LEADING = RS confirming a new high while price hasn't yet\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
