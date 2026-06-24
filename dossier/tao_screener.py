#!/usr/bin/env python3
"""
🌊 TAO Pullback Screener — Multi-Timeframe EMA Stack + Pullback Finder

Finds stocks in confirmed uptrends (TAO EMA stack) that are currently
pulling back to EMA 21 support — the ideal swing-trade entry zone.

TAO Stack definition (from STRATEGY_SPECS.md):
    EMA 8 > EMA 21 > EMA 34 > EMA 55 > EMA 89 on the daily

Entry condition (the "Bounce 2.0" zone):
    Price is above EMA 21 but within 1.5× ATR(14) of it —
    close enough to support to give a tight stop, far enough to confirm
    the trend hasn't broken.

Funnel architecture (same 3-stage pattern as ghost_alpha_screener):
    Stage 1 → TradingView bulk API: pre-filter ~8000 US stocks in one request
    Stage 2 → Progressive funnel cuts using pre-computed TV technicals
    Stage 3 → yfinance deep scan: compute full EMA stack + pullback score

Scoring (0–100):
    EMA alignment  (40 pts) — how many of the 5 EMA pairs are stacked
    Pullback quality (30 pts) — distance from EMA 21 in ATR units
    Trend strength   (20 pts) — ADX reading
    Weekly bonus     (10 pts) — weekly EMAs also stacked

Grades: A+ (85+) · A (70–84) · B (55–69) · C (40–54) · D (<40)

Usage:
    python -m dossier.tao_screener                        # whole market
    python -m dossier.tao_screener --tickers NVDA,AAPL   # specific tickers
    python -m dossier.tao_screener --watchlist            # core watchlist only
    python -m dossier.tao_screener --top 20              # limit output
    python -m dossier.tao_screener --json                 # machine output
    python -m dossier.tao_screener --quiet                # A+/A only

Output: docs/api/tao-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"The trend is your friend — catch it on the dip." — Sam
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

# Reuse same columns as ghost_alpha_screener to keep TV calls consistent
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
    "EMA20",                    # 9  EMA 20 (proxy for EMA 21 in pre-filter)
    "RSI",                      # 10 RSI(14)
    "ADX",                      # 11 ADX(14)
    "ATR",                      # 12 ATR(14)
    "Perf.W",                   # 13 weekly performance %
    "Perf.1M",                  # 14 monthly performance %
    "Recommend.All",            # 15 TV signal
    "Stoch.K",                  # 16 Stochastic K
    "BB.upper",                 # 17 Bollinger upper
    "BB.lower",                 # 18 Bollinger lower
    "Perf.3M",                  # 19 3-month performance %
]


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_tao_candidates() -> list[dict]:
    """
    One POST to TradingView → pre-filtered TAO candidates.

    Server-side: price > $5, avg vol > 200K, price > SMA200 (macro uptrend),
    SMA50 > SMA200 (golden cross confirmed), ADX > 15 (some trend exists).
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
            # Macro uptrend: price above SMA 200
            {"left": "close", "operation": "greater", "right": "SMA200"},
            # Golden cross: SMA 50 above SMA 200
            {"left": "SMA50", "operation": "greater", "right": "SMA200"},
            # Some trend strength — cuts trendless choppers
            {"left": "ADX", "operation": "greater", "right": 15},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView TAO scan") or {}
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
            "stoch_k": d[16],
            "bb_upper": d[17],
            "bb_lower": d[18],
            "perf_3m": d[19],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """
    Narrow the TV universe to likely TAO pullback candidates
    before paying the cost of yfinance API calls.
    """
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ TAO FUNNEL: {total} stocks from TradingView")

    # 2A: Liquidity floor
    survivors = [s for s in stocks if (
        (s["market_cap"] or 0) >= 500_000_000  # $500M+ — avoid micro-cap noise
        and s["avg_vol_30d"] >= 300_000
    )]
    if verbose:
        print(f"  ├─ Cap ≥$500M + Vol ≥300K ──────────→ {len(survivors)} ({total - len(survivors)} cut)")

    # 2B: Pullback zone — price within ±5% of EMA 20 (proxy for EMA 21)
    # Too far above = extended, not a pullback. Below = breakdown.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["ema_20"] is not None and s["ema_20"] > 0
        and s["price"] > s["ema_20"] * 0.97      # must be above (not broken)
        and s["price"] < s["ema_20"] * 1.06      # within 6% (near, not extended)
    )]
    if verbose:
        print(f"  ├─ Price within 6% above EMA 20 ────→ {len(survivors)} ({prev - len(survivors)} cut)")

    # 2C: Pullback confirmed — RSI between 35 and 65 (healthy dip, not crashed)
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["rsi"] is not None
        and 35 <= s["rsi"] <= 65
    )]
    if verbose:
        print(f"  ├─ RSI 35-65 (pullback zone) ───────→ {len(survivors)} ({prev - len(survivors)} cut)")

    # 2D: No extreme weekly moves (blow-offs or crashes)
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["perf_1w"] is None or -15 <= s["perf_1w"] <= 15
    )]
    if verbose:
        print(f"  ├─ Weekly ±15% (no extremes) ───────→ {len(survivors)} ({prev - len(survivors)} cut)")

    if verbose:
        pct = (1 - len(survivors) / total) * 100 if total > 0 else 0
        print(f"  └─ FUNNEL DONE: {len(survivors)} survivors ({pct:.0f}% eliminated)\n")

    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — TAO DEEP SCAN (yfinance)  ████
# ═══════════════════════════════════════════════════════════════════

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["High"], df["Low"], df["Close"]
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def _adx(df: pd.DataFrame, period: int = 14) -> float:
    """Return last ADX value."""
    high, low, close = df["High"], df["Low"], df["Close"]
    up = high.diff()
    dn = -low.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    atr14 = _atr(df, period)
    # Avoid divide-by-zero
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(span=period, adjust=False).mean() / atr14.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(span=period, adjust=False).mean() / atr14.replace(0, np.nan)
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)).fillna(0)
    return float(dx.ewm(span=period, adjust=False).mean().iloc[-1])


def _weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily OHLCV to weekly (Friday-close bars)."""
    return df.resample("W-FRI").agg({
        "Open": "first", "High": "max", "Low": "min",
        "Close": "last", "Volume": "sum",
    }).dropna()


def score_tao(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep scan a single ticker for TAO pullback score.

    Returns a result dict on success, None if data is insufficient
    or the TAO conditions aren't met at all.
    """
    try:
        df = yf.Ticker(ticker).history(period="3y")
        ok, reason = check_yfinance_history(df, ticker, min_rows=150)
        if not ok:
            return None

        price = float(df["Close"].iloc[-1])
        atr14 = float(_atr(df).iloc[-1])

        # ── Daily EMA stack ──────────────────────────────────────
        e8  = float(_ema(df["Close"], 8).iloc[-1])
        e21 = float(_ema(df["Close"], 21).iloc[-1])
        e34 = float(_ema(df["Close"], 34).iloc[-1])
        e55 = float(_ema(df["Close"], 55).iloc[-1])
        e89 = float(_ema(df["Close"], 89).iloc[-1])

        # Count how many consecutive EMA pairs are stacked
        pairs = [(e8, e21), (e21, e34), (e34, e55), (e55, e89)]
        aligned_pairs = sum(1 for a, b in pairs if a > b)

        # Require at least 3/4 pairs aligned — strict but allows near-full stacks
        if aligned_pairs < 3:
            return None

        full_stack = aligned_pairs == 4

        # ── Pullback check ───────────────────────────────────────
        # Price must be above EMA 21 (trend unbroken)
        if price <= e21:
            return None
        distance_atr = (price - e21) / atr14 if atr14 > 0 else 99.0
        # Skip if too far extended (>2.5 ATR above EMA21 = not a pullback)
        if distance_atr > 2.5:
            return None

        # ── ADX ──────────────────────────────────────────────────
        adx = _adx(df)
        if adx < 18:  # Trendless — skip
            return None

        # ── Weekly EMA alignment ─────────────────────────────────
        weekly_aligned = 0
        try:
            wdf = _weekly(df)
            if len(wdf) >= 60:
                we8  = float(_ema(wdf["Close"], 8).iloc[-1])
                we21 = float(_ema(wdf["Close"], 21).iloc[-1])
                we34 = float(_ema(wdf["Close"], 34).iloc[-1])
                we55 = float(_ema(wdf["Close"], 55).iloc[-1])
                we89 = float(_ema(wdf["Close"], 89).iloc[-1])
                weekly_pairs = [(we8, we21), (we21, we34), (we34, we55), (we55, we89)]
                weekly_aligned = sum(1 for a, b in weekly_pairs if a > b)
        except Exception:
            weekly_aligned = 0

        # ── Scoring (0–100) ──────────────────────────────────────
        # EMA alignment (40 pts)
        ema_score = {4: 40, 3: 25}.get(aligned_pairs, 0)

        # Pullback quality (30 pts): closer to EMA 21 = better entry
        if distance_atr <= 0.25:
            pb_score = 30   # At the EMA — perfect
        elif distance_atr <= 0.5:
            pb_score = 25
        elif distance_atr <= 0.75:
            pb_score = 20
        elif distance_atr <= 1.0:
            pb_score = 15
        elif distance_atr <= 1.5:
            pb_score = 8
        else:
            pb_score = 3   # Still valid but far

        # ADX trend strength (20 pts)
        if adx >= 35:
            adx_score = 20
        elif adx >= 28:
            adx_score = 16
        elif adx >= 22:
            adx_score = 12
        else:
            adx_score = 6

        # Weekly bonus (10 pts)
        weekly_score = {4: 10, 3: 7, 2: 3}.get(weekly_aligned, 0)

        total_score = ema_score + pb_score + adx_score + weekly_score

        # Grade
        if total_score >= 85:
            grade = "A+"
        elif total_score >= 70:
            grade = "A"
        elif total_score >= 55:
            grade = "B"
        elif total_score >= 40:
            grade = "C"
        else:
            grade = "D"

        sma50 = float(df["Close"].rolling(50).mean().iloc[-1])
        sma200 = float(df["Close"].rolling(200).mean().iloc[-1])

        result = {
            "ticker": ticker,
            "name": (tv_data or {}).get("name", ticker),
            "price": round(price, 2),
            "score": total_score,
            "grade": grade,
            "ema_stack": aligned_pairs,      # out of 4
            "full_stack": full_stack,
            "distance_atr": round(distance_atr, 2),
            "adx": round(adx, 1),
            "atr": round(atr14, 2),
            "ema_21": round(e21, 2),
            "ema_8":  round(e8, 2),
            "ema_89": round(e89, 2),
            "sma50_gt_sma200": sma50 > sma200,
            "weekly_stack": weekly_aligned,  # out of 4
            "market_cap": (tv_data or {}).get("market_cap"),
            "change_pct": (tv_data or {}).get("change_pct", 0),
        }
        return result

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
        stack_bar = "█" * r["ema_stack"] + "░" * (4 - r["ema_stack"])
        weekly = "✓W" if r["weekly_stack"] >= 3 else ("~W" if r["weekly_stack"] == 2 else "  ")
        dist = r["distance_atr"]
        dist_str = f"{dist:.2f}× ATR"
        change = r.get("change_pct", 0) or 0
        chg_str = f"+{change:.1f}%" if change >= 0 else f"{change:.1f}%"
        cap_str = _fmt_cap(r["market_cap"])

        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Score:{r['score']:>3}  Stack:[{stack_bar}] {weekly}  "
            f"Dist:{dist_str:<10}  ADX:{r['adx']:<5.1f}  "
            f"{chg_str:>6}  {cap_str}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/tao-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "tao-screener.json"
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
    parser = argparse.ArgumentParser(description="TAO Pullback Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🌊  TAO Pullback Screener — {len(tickers)} tickers\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🌊  TAO Pullback Screener — core watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🌊  TAO Pullback Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_tao_candidates()
        print(f"     → {len(raw)} pre-filtered candidates from TradingView\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        # Sort by market cap (bigger first, faster yf scans + more liquid)
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_tao(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} TAO setups found so far")
        time.sleep(0.05)  # gentle rate-limit

    # Sort by score descending
    results.sort(key=lambda r: r["score"], reverse=True)

    if args.top:
        results = results[:args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    grade_counts = {}
    for r in results:
        grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1

    print(f"\n{'═' * 100}")
    print(f"  🌊  TAO PULLBACK SCREENER RESULTS — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: Stack [████] = 4/4 EMA pairs aligned (8>21>34>55>89)")
    print(f"          Dist = price distance above EMA 21 in ATR units (lower = better entry)")
    print(f"          W = weekly EMA stack also aligned\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
