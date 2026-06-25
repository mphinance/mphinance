#!/usr/bin/env python3
"""
🔄 200-Day SMA Reclaim Screener — Comeback Kids

Finds stocks that recently crossed back above their 200-day SMA after
spending time below it — the "trend rehabilitation" signal.

The 200-day SMA is the most-watched long-term trend line in markets.
Institutions use it as the dividing line between bull and bear territory.
When a stock reclaims it within the last 15 trading days with confirming
volume, it often marks the start of a fresh accumulation phase.

Different from every other screener in the dossier:
  - TAO Pullback: stocks already in intact EMA uptrends pulling back
  - High52: stocks quietly pressing toward 52-week highs
  - RVol Breakout: stocks with yesterday's unusual volume surge
  - THIS: stocks just crossing from "broken" to "recovering" right now

Funnel architecture (same 3-stage pattern as high52 / tao / rvol):
    Stage 1 → TradingView bulk API: price > SMA200, within 18%, RSI 38-70
    Stage 2 → Progressive funnel: liquidity, proximity, 1M-return floor
    Stage 3 → yfinance deep scan: detect exact crossover date (≤15 days),
               volume confirmation, RSI position, SMA50 relationship

Scoring (0-100):
    Crossover recency     (40 pts) — more recent = fresher signal
    Volume confirmation   (25 pts) — institutional buying at the level?
    RSI recovery          (20 pts) — building momentum, not overbought
    SMA50 alignment       (15 pts) — above SMA50 = trend fully healing

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.sma200_reclaim_screener                       # whole market
    python -m dossier.sma200_reclaim_screener --tickers NVDA,AAPL  # specific tickers
    python -m dossier.sma200_reclaim_screener --watchlist           # core watchlist only
    python -m dossier.sma200_reclaim_screener --top 20             # limit output
    python -m dossier.sma200_reclaim_screener --json               # machine output
    python -m dossier.sma200_reclaim_screener --quiet              # A+/A only

Output: docs/api/sma200-reclaim.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"The 200-day doesn't lie. Cross back above it with volume and you're back in the game." — Sam
"""

import argparse
import json
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
        "XOM", "OXY",
    ]

# ─── Config ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"

_TV_COLUMNS = [
    "name",                     # 0  ticker
    "description",              # 1  company name
    "close",                    # 2  last price
    "change",                   # 3  % change today
    "volume",                   # 4  today's volume
    "average_volume_30d_calc",  # 5  30d avg volume
    "market_cap_basic",         # 6  market cap
    "SMA200",                   # 7  SMA 200
    "SMA50",                    # 8  SMA 50
    "EMA20",                    # 9  EMA 20
    "RSI",                      # 10 RSI(14)
    "ADX",                      # 11 ADX(14)
    "ATR",                      # 12 ATR(14)
    "Perf.W",                   # 13 weekly performance %
    "Perf.1M",                  # 14 monthly performance %
    "Recommend.All",            # 15 TV signal
    "Perf.3M",                  # 16 3-month performance %
    "High.1Y",                  # 17 52-week high
]


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_reclaim_candidates() -> list[dict]:
    """
    One POST to TradingView → pre-filtered 200-day reclaim candidates.

    Server-side: price above SMA200 but within 18% (fresh crossing zone),
    RSI in recovery range, decent liquidity.
    """
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 200_000},
            {"left": "close", "operation": "greater", "right": 5},
            # Currently above SMA200 (reclaimed it)
            {"left": "close", "operation": "greater", "right": "SMA200"},
            # Not too extended — within 18% of SMA200 (fresh reclaim territory)
            {"left": "close", "operation": "less", "right": "SMA200*1.18"},
            # Recovery RSI — not crashed, not overbought
            {"left": "RSI", "operation": "in_range", "right": [38, 70]},
            # Some trend emerging
            {"left": "ADX", "operation": "greater", "right": 12},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView SMA200 reclaim scan") or {}
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
            "perf_3m": d[16],
            "high_1y": d[17],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """
    Narrow the TV universe to likely 200d reclaim candidates
    before paying the cost of yfinance API calls.
    """
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ RECLAIM FUNNEL: {total} stocks from TradingView")

    # 2A: Liquidity floor — avoid micro-cap noise
    survivors = [s for s in stocks if (
        (s["market_cap"] or 0) >= 500_000_000
        and s["avg_vol_30d"] >= 300_000
    )]
    if verbose:
        print(f"  ├─ Cap ≥$500M + Vol ≥300K ──────────→ {len(survivors)} ({total - len(survivors)} cut)")

    # 2B: Proximity — within 15% above SMA200 (fresh reclaim, not extended for months)
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["sma_200"] is not None and s["sma_200"] > 0
        and s["price"] <= s["sma_200"] * 1.15
    )]
    if verbose:
        print(f"  ├─ Within 15% above SMA200 ─────────→ {len(survivors)} ({prev - len(survivors)} cut)")

    # 2C: RSI in recovery range — not still in freefall, not overbought
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["rsi"] is not None
        and 38 <= s["rsi"] <= 68
    )]
    if verbose:
        print(f"  ├─ RSI 38-68 (recovery zone) ───────→ {len(survivors)} ({prev - len(survivors)} cut)")

    # 2D: Not still in freefall — 1-month return must have some floor
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["perf_1m"] is None or s["perf_1m"] >= -18
    )]
    if verbose:
        print(f"  ├─ 1M return ≥ -18% (not crashing) ─→ {len(survivors)} ({prev - len(survivors)} cut)")

    if verbose:
        pct = (1 - len(survivors) / total) * 100 if total > 0 else 0
        print(f"  └─ FUNNEL DONE: {len(survivors)} survivors ({pct:.0f}% eliminated)\n")

    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  SCORING HELPERS (public — importable for tests)  ████
# ═══════════════════════════════════════════════════════════════════

def _recency_score(days_since: int) -> int:
    """How recently the SMA200 was reclaimed — fresher = higher score (40 pts max)."""
    if days_since <= 3:
        return 40
    if days_since <= 5:
        return 34
    if days_since <= 7:
        return 26
    if days_since <= 10:
        return 18
    if days_since <= 15:
        return 10
    return 4


def _volume_conf_score(crossover_rvol: float) -> int:
    """
    Volume on the crossover day relative to the 30-day average (25 pts max).

    High relative volume on the reclaim day = institutional participation.
    """
    if crossover_rvol >= 2.5:
        return 25
    if crossover_rvol >= 2.0:
        return 20
    if crossover_rvol >= 1.5:
        return 15
    if crossover_rvol >= 1.2:
        return 9
    return 4


def _rsi_score(rsi: float) -> int:
    """RSI position in the recovery range (20 pts max)."""
    if 50 <= rsi <= 60:
        return 20   # Goldilocks: momentum building, not overbought
    if 45 <= rsi < 50 or 60 < rsi <= 65:
        return 15
    if 40 <= rsi < 45 or 65 < rsi <= 70:
        return 8
    return 3


def _sma50_score(price: float, sma50: float | None) -> int:
    """
    SMA50 relationship (15 pts max).

    Above SMA50 = both trend levels reclaimed = higher conviction.
    """
    if sma50 is None or sma50 <= 0:
        return 0
    if price > sma50:
        pct_above = (price - sma50) / sma50 * 100
        if pct_above <= 5:
            return 15   # Just above SMA50 — clean double reclaim
        if pct_above <= 10:
            return 10
        return 6        # Well above SMA50 — extended but still positive
    return 0            # Below SMA50 — weaker signal


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — DEEP SCAN (yfinance)  ████
# ═══════════════════════════════════════════════════════════════════

def score_sma200_reclaim(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep scan a single ticker for a 200-day SMA reclaim setup.

    Returns a result dict on success, None if data is insufficient
    or no crossover is detected within the last 15 trading days.
    """
    try:
        df = yf.Ticker(ticker).history(period="2y")
        ok, _ = check_yfinance_history(df, ticker, min_rows=210)
        if not ok:
            return None

        close = df["Close"]
        volume = df["Volume"]
        sma200 = close.rolling(200).mean()
        sma50 = close.rolling(50).mean()

        if pd.isna(sma200.iloc[-1]):
            return None

        current_price = float(close.iloc[-1])
        current_sma200 = float(sma200.iloc[-1])
        current_sma50 = float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else None
        avg_vol_30 = float(volume.rolling(30).mean().iloc[-1])

        # Must be currently above SMA200
        if current_price <= current_sma200:
            return None

        # Must be within 15% above SMA200 (fresh reclaim, not extended for months)
        proximity_pct = (current_price - current_sma200) / current_sma200 * 100
        if proximity_pct > 15.0:
            return None

        # ── Detect most recent upward crossover (within last 15 trading days) ──
        # i=1: crossover at the most recent bar
        # i=15: crossover 15 days ago (our cutoff)
        days_since = None
        crossover_rvol = 1.0

        for i in range(1, min(16, len(close) - 1)):
            price_now = float(close.iloc[-i])
            sma_now = float(sma200.iloc[-i])
            price_prev = float(close.iloc[-(i + 1)])
            sma_prev = float(sma200.iloc[-(i + 1)])

            if pd.isna(sma_now) or pd.isna(sma_prev):
                continue

            # Found where price crossed from below to above
            if price_prev <= sma_prev and price_now > sma_now:
                days_since = i
                day_vol = float(volume.iloc[-i])
                if avg_vol_30 > 0:
                    crossover_rvol = day_vol / avg_vol_30
                break

        # No recent crossover — stock has been above SMA200 for more than 15 days
        if days_since is None:
            return None

        # ── RSI (Wilder's smoothing) ──────────────────────────────────
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, float("nan"))
        rsi_val = float((100 - 100 / (1 + rs)).iloc[-1])

        if pd.isna(rsi_val) or not (35 <= rsi_val <= 75):
            return None

        # ── Scoring ───────────────────────────────────────────────────
        rec_pts = _recency_score(days_since)
        vol_pts = _volume_conf_score(crossover_rvol)
        rsi_pts = _rsi_score(rsi_val)
        sma50_pts = _sma50_score(current_price, current_sma50)

        total_score = rec_pts + vol_pts + rsi_pts + sma50_pts

        if total_score >= 80:
            grade = "A+"
        elif total_score >= 65:
            grade = "A"
        elif total_score >= 50:
            grade = "B"
        elif total_score >= 35:
            grade = "C"
        else:
            grade = "D"

        above_sma50 = current_sma50 is not None and current_price > current_sma50

        return {
            "ticker": ticker,
            "name": (tv_data or {}).get("name", ticker),
            "price": round(current_price, 2),
            "score": total_score,
            "grade": grade,
            "days_since_reclaim": days_since,
            "proximity_pct": round(proximity_pct, 2),
            "crossover_rvol": round(crossover_rvol, 2),
            "rsi": round(rsi_val, 1),
            "sma200": round(current_sma200, 2),
            "sma50": round(current_sma50, 2) if current_sma50 else None,
            "above_sma50": above_sma50,
            "market_cap": (tv_data or {}).get("market_cap"),
            "change_pct": (tv_data or {}).get("change_pct", 0),
            "score_breakdown": {
                "recency": rec_pts,
                "volume_conf": vol_pts,
                "rsi": rsi_pts,
                "sma50": sma50_pts,
            },
        }

    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT & FORMATTING  ████
# ═══════════════════════════════════════════════════════════════════

_GRADE_COLOR = {
    "A+": "\033[96m", "A": "\033[92m", "B": "\033[94m",
    "C": "\033[93m", "D": "\033[91m",
}
_RESET = "\033[0m"


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
        grade = r["grade"]
        if quiet and grade not in ("A+", "A"):
            continue
        days = r["days_since_reclaim"]
        rvol = r["crossover_rvol"]
        prox = r["proximity_pct"]
        above50 = "✓50" if r["above_sma50"] else "  "
        change = r.get("change_pct", 0) or 0
        chg_str = f"+{change:.1f}%" if change >= 0 else f"{change:.1f}%"
        cap_str = _fmt_cap(r["market_cap"])

        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Score:{r['score']:>3}  Day+{days:<2}  RVol:{rvol:<4.1f}  "
            f"RSI:{r['rsi']:<5.1f}  +{prox:.1f}%>200d  {above50}  "
            f"{chg_str:>6}  {cap_str}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/sma200-reclaim.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sma200-reclaim.json"
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(results),
        "results": results,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\n  💾  Saved {len(results)} results → {out_path}")


# ═══════════════════════════════════════════════════════════════════
# ████  MAIN  ████
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="200-Day SMA Reclaim Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🔄  SMA200 Reclaim Screener — {len(tickers)} tickers\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🔄  SMA200 Reclaim Screener — core watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🔄  SMA200 Reclaim Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_reclaim_candidates()
        print(f"     → {len(raw)} pre-filtered candidates from TradingView\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_sma200_reclaim(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} reclaims found so far")
        time.sleep(0.05)

    results.sort(key=lambda r: r["score"], reverse=True)

    if args.top:
        results = results[:args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    grade_counts: dict[str, int] = {}
    for r in results:
        grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1

    print(f"\n{'═' * 100}")
    print(f"  🔄  SMA200 RECLAIM SCREENER RESULTS — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: Day+N = N trading days since SMA200 reclaim  |  RVol = vol/avg on crossover day")
    print(f"          +X%>200d = how far above SMA200 now  |  ✓50 = also above SMA50\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
