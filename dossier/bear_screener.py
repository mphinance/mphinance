#!/usr/bin/env python3
"""
🐻 Bear Mode Screener — Bearish EMA Stack Scanner

Mirror of ghost_alpha_screener.py with ALL conditions reversed.
Finds stocks in confirmed downtrends pulling back to resistance
(Stoch K > 60) — prime entries for puts or shorts.

Port of the "Stacked EMAs Tao" reversed screener:
  Daily:   EMA 8 < 21 < 34 < 55 < 89  (bearish cascade)
  Weekly:  Same stack reversed
  Monthly: Same stack reversed (multi-TF confirmation)

Funnel architecture (same as bull side):
  Stage 1 → TradingView bulk API: fetch bearish universe
  Stage 2 → Progressive bear filters eliminate noise
  Stage 3 → yfinance deep scan on survivors
  Stage 4 → Multi-timeframe alignment (daily + weekly both bearish)

Usage:
    python -m dossier.bear_screener                       # Whole market
    python -m dossier.bear_screener --tickers NKLA,LCID   # Specific tickers
    python -m dossier.bear_screener --json                 # Machine output
    python -m dossier.bear_screener --quiet                # Only A+/A setups

Output: docs/api/bear-screener.json (bear feed)

© mphinance + Sam the Quant Ghost
"The trend is your friend... unless it's going down." — Sam
"""

import argparse
import json
import math
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
    print("❌ pip install yfinance")
    sys.exit(1)

# ─── Config ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Import grading engine from bull screener (no duplication)
from dossier.ghost_alpha_screener import (
    compute_ghost_grade,
    deep_scan_ticker,
    batch_deep_scan,
    resample_to_weekly,
    TV_COLUMNS,
)

TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCANNER (BEAR MODE)  ████
# ═══════════════════════════════════════════════════════════════════
# Same structure as bull, but every directional filter is flipped.

def _tv_fetch_bear_stocks() -> list[dict]:
    """
    Fetch bearish US equities from TradingView's scanner API.
    Server-side filters do the heavy lifting:
      - EMA stack reversed (8 < 21 < 34 < 55 < 89)
      - MACD < 0
      - ADX ≥ 20 (stronger confirmation for shorts)
      - Stoch K > 60 (pulled back to resistance — the buy zone for puts)
    """
    # TradingView columns — same as bull screener
    # We need EMA 8 for the full Tao stack
    bear_columns = list(TV_COLUMNS) + ["EMA8"]  # index 35

    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            # ── Hard floors ──
            {"left": "close", "operation": "greater", "right": 1},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 1_000_000},
            {"left": "market_cap_basic", "operation": "greater", "right": 300_000_000},
            # ── BEARISH directional filters ──
            # ADX ≥ 20 (demand stronger trend for shorts)
            {"left": "ADX", "operation": "greater", "right": 20},
            # MACD < 0 (bearish momentum)
            {"left": "MACD.macd", "operation": "less", "right": 0},
            # RSI not extreme — 25-80 (avoid deeply oversold bounces)
            {"left": "RSI", "operation": "greater", "right": 25},
            {"left": "RSI", "operation": "less", "right": 80},
            # Stoch K > 60 — pullback to resistance (PUT ENTRY ZONE)
            {"left": "Stoch.K", "operation": "greater", "right": 60},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": bear_columns,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("data", [])

    results = []
    for item in rows:
        d = item.get("d", [])
        if len(d) < len(TV_COLUMNS):
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
            "ema_21": d[9],
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
            "williams_r": d[20],
            "adx_plus_di": d[21],
            "adx_minus_di": d[22],
            "ema_50": d[23],
            "ema_200": d[24],
            "recommend_ma": d[25],
            "rvol_10d": d[26],
            "stoch_rsi_k": d[27],
            "macd": d[28],
            "ema_34": d[29],
            "ema_55": d[30],
            "cci20": d[31],
            "cmf": d[32],
            "hull_ma9": d[33],
            "ema_89": d[34],
            "ema_8": d[35] if len(d) > 35 else None,
        })

    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE BEAR FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════
# Same architecture as bull, every directional check is flipped.

def bear_funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """
    Progressive bear filter funnel. Mirrors the bull funnel
    with every directional condition reversed.
    """
    import time as _t
    _t0 = _t.time()
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ 🐻 BEAR FUNNEL: {total} stocks loaded "
              f"(server pre-filtered: $1+, Vol 1M+, Cap $300M+, ADX≥20, MACD<0, Stoch>60)")

    # ── STAGE 2A: Price & Liquidity Floor ─────────────────────────
    survivors = [s for s in stocks if (
        s["price"] >= 1.0
        and s["avg_vol_30d"] >= 1_000_000
        and (s["market_cap"] or 0) >= 300_000_000
    )]
    cut = total - len(survivors)
    if verbose:
        print(f"  ├─ Price ≥$1 + Vol ≥1M + Cap ≥$300M → {len(survivors)} survive ({cut} cut)")

    # ── STAGE 2B: BEARISH Trend — Price BELOW SMA 200 ──────────
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["sma_200"] is not None
        and s["price"] < s["sma_200"]
    )]
    if verbose:
        print(f"  ├─ Price < SMA 200 (bear) ─────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2C: Death Cross — EMA 50 < EMA 200 ──────────────
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("ema_50") is not None
        and s.get("ema_200") is not None
        and s["ema_50"] < s["ema_200"]
    )]
    if verbose:
        print(f"  ├─ Death Cross (EMA50<200) ────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2D: BEARISH EMA Stack (Tao: 21<34<55<89) ────────
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("ema_21") is not None
        and s.get("ema_34") is not None
        and s.get("ema_55") is not None
        and s.get("ema_89") is not None
        and s["ema_21"] < s["ema_34"] < s["ema_55"] < s["ema_89"]
    )]
    if verbose:
        print(f"  ├─ EMA Stack 21<34<55<89 ─────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2E: MACD Bearish Confirmation ───────────────────
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("macd") is None
        or s["macd"] < 0
    )]
    if verbose:
        print(f"  ├─ MACD < 0 (bear momentum) ──→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2F: Monthly Performance < 0 (still falling) ────
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("perf_1m") is None
        or s["perf_1m"] < 0
    )]
    if verbose:
        print(f"  ├─ Perf.1M < 0% (falling) ────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2G: MA Recommendation < 0.3 (not bullish) ──────
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("recommend_ma") is None
        or s["recommend_ma"] < 0.3
    )]
    if verbose:
        print(f"  ├─ MA Recommend < 0.3 ────────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2H: Keltner / Extension Filter ─────────────────
    # Within ±8% of EMA 21 — nearness is universal
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["ema_21"] is not None
        and s["ema_21"] > 0
        and ((s["price"] - s["ema_21"]) / s["ema_21"] * 100) <= 8.0
        and ((s["price"] - s["ema_21"]) / s["ema_21"] * 100) >= -8.0
    )]
    if verbose:
        print(f"  ├─ Within ±8% EMA 21 (Kelt) ──→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2I: Stoch K > 60 (PULLED BACK TO RESISTANCE) ───
    # This IS the bear entry zone. Stoch bounced up = selling opportunity.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("stoch_k") is None
        or s["stoch_k"] > 60
    )]
    if verbose:
        print(f"  ├─ Stoch.K > 60 (resistance) ─→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2J: Williams %R Zone ───────────────────────────
    # Keep the same range — works for both directions
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("williams_r") is None
        or (-80 <= s["williams_r"] <= -20)
    )]
    if verbose:
        print(f"  ├─ W%R -80 to -20 (no exh) ──→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2K: CCI20 Goldilocks Zone ─────────────────────
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("cci20") is None
        or (-100 <= s["cci20"] <= 100)
    )]
    if verbose:
        print(f"  ├─ CCI20 ±100 (goldilocks) ──→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2L: RSI Range (25-80 for bears) ────────────────
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["rsi"] is not None
        and 25 <= s["rsi"] <= 80
    )]
    if verbose:
        print(f"  ├─ RSI 25-80 (no extremes) ──→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2M: ADX Trend Strength + BEARISH Direction ─────
    # -DI must lead +DI by 5+ (bears in control)
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["adx"] is not None
        and s["adx"] >= 20
        and (s.get("adx_plus_di") is None or s.get("adx_minus_di") is None
             or s["adx_minus_di"] > s["adx_plus_di"] + 5)  # -DI must lead
    )]
    if verbose:
        print(f"  ├─ ADX ≥20 + DI- > DI+ +5 ──→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2N: Volume Life Check ─────────────────────────
    # For bearish pullbacks to resistance, volume often dries up.
    # We will score it later, but won't use it as a hard funnel killer.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["volume"] > 0 and s["avg_vol_30d"] > 0  # Just make sure it trades
    )]
    if verbose:
        print(f"  ├─ Volume > 0 (not dead) ────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2O: Weekly Performance Sanity ─────────────────
    # No blow-off crash (dead cat bounce territory)
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["perf_1w"] is None
        or (-20 <= s["perf_1w"] <= 10)
    )]
    if verbose:
        print(f"  ├─ Weekly -20/+10% (sanity) ─→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    if verbose:
        pct = (1 - len(survivors) / total) * 100 if total > 0 else 0
        elapsed = _t.time() - _t0
        print(f"  └─ 🐻 BEAR FUNNEL COMPLETE: {len(survivors)} survivors "
              f"({pct:.0f}% eliminated) [{elapsed:.1f}s]")
        print()

    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  BEAR-SPECIFIC DEEP SCAN WRAPPER  ████
# ═══════════════════════════════════════════════════════════════════
# Reuses the grading engine but tags results as bearish.

def bear_deep_scan_ticker(ticker: str, df: pd.DataFrame = None,
                          tv_data: dict | None = None) -> dict | None:
    """
    Deep scan with bear tagging. The ghost grade engine scores
    trend quality regardless of direction — we just flip the
    interpretation (hull_bull=False is GOOD for bears).
    """
    result = deep_scan_ticker(ticker, df=df, tv_data=tv_data)
    if result is None:
        return None

    # Tag as bear setup
    result["direction"] = "BEAR"

    # For bears, we WANT hull_bull=False (bearish Hull MA)
    # Re-score: a "good" bear setup has bearish Hull, negative CMF, etc.
    d = result.get("daily", {})
    w = result.get("weekly", {})

    # Bear quality score (higher = better short/put candidate)
    bear_score = 0.0
    # Hull MA bearish = good
    if not d.get("hull_bull", True):
        bear_score += 1.5
    # Negative CMF = institutional selling
    cmf = d.get("cmf", 0)
    if cmf < -0.10:
        bear_score += 1.5
    elif cmf < -0.05:
        bear_score += 1.0
    elif cmf < 0:
        bear_score += 0.5
    # Squeeze about to fire (in a downtrend = explosive drop)
    if d.get("sqz_fire"):
        bear_score += 1.0
    elif d.get("sqz_coiled"):
        bear_score += 0.5
    # Fresh bear trend (5-30 bars)
    age = d.get("trend_age", 0)
    if 5 <= age <= 30:
        bear_score += 1.0
    elif 30 < age <= 50:
        bear_score += 0.5
    # RVOL (volume confirms the move)
    rvol = d.get("rvol", 0)
    if rvol >= 1.2:
        bear_score += 0.5
    # Not exhausted (W%R not at extremes)
    if not d.get("exh_ob") and not d.get("exh_os"):
        bear_score += 1.0

    # Grade the bear setup
    if bear_score >= 5.5:
        bear_grade = "A+"
    elif bear_score >= 4.5:
        bear_grade = "A"
    elif bear_score >= 3.5:
        bear_grade = "B"
    elif bear_score >= 2.5:
        bear_grade = "C"
    elif bear_score >= 1.5:
        bear_grade = "D"
    else:
        bear_grade = "F"

    result["bear_grade"] = bear_grade
    result["bear_score"] = round(bear_score, 1)

    # Weekly bear alignment
    w_bear = 0.0
    if not w.get("hull_bull", True):
        w_bear += 2.0
    if w.get("cmf", 0) < 0:
        w_bear += 1.0
    result["weekly_bear_score"] = round(w_bear, 1)

    # Multi-TF bear alignment
    result["bear_aligned"] = (bear_score >= 4.0 and w_bear >= 2.0)
    result["combined_bear_score"] = round(bear_score + w_bear, 1)

    return result


def bear_batch_deep_scan(tickers: list[str], tv_lookup: dict,
                         batch_size: int = 100) -> list[dict]:
    """
    Batch download OHLCV data and run bear-specific grading.
    """
    results = []
    errors = 0
    total = len(tickers)

    for batch_start in range(0, total, batch_size):
        batch = tickers[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"\r     🐻 Batch {batch_num}/{total_batches}: "
              f"downloading {len(batch)} tickers...", end="", flush=True)

        try:
            raw = yf.download(
                batch, period="3y", group_by="ticker",
                threads=True, progress=False,
            )
        except Exception as e:
            print(f"\n     ⚠ Batch download error: {e}")
            for ticker in batch:
                result = bear_deep_scan_ticker(ticker, tv_data=tv_lookup.get(ticker))
                if result:
                    results.append(result)
                else:
                    errors += 1
            continue

        for ticker in batch:
            try:
                if len(batch) == 1:
                    df = raw.copy()
                    # yf.download with a list always returns MultiIndex
                    if isinstance(df.columns, pd.MultiIndex):
                        df = df.droplevel("Ticker", axis=1)
                else:
                    df = raw[ticker].copy()
                    if isinstance(df.columns, pd.MultiIndex):
                        df = df.droplevel(0, axis=1)
                df = df.dropna(how="all")
                if df.empty or len(df) < 200:
                    errors += 1
                    continue
                result = bear_deep_scan_ticker(
                    ticker, df=df, tv_data=tv_lookup.get(ticker))
                if result:
                    results.append(result)
                else:
                    errors += 1
            except (KeyError, Exception):
                errors += 1

        pct = min((batch_start + len(batch)) / total * 100, 100)
        print(f"\r     🐻 Batch {batch_num}/{total_batches}: "
              f"{len(results)} graded, {errors} errors ({pct:.0f}%)"
              + " " * 10, end="", flush=True)

    print(f"\r     ✅ Bear-scanned {len(results)} tickers ({errors} errors)"
          + " " * 30)
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT FORMATTING  ████
# ═══════════════════════════════════════════════════════════════════

def _gc(grade: str) -> str:
    """ANSI color for grade (bear edition — red is good)."""
    c = {"A+": "\033[91m", "A": "\033[31m", "B": "\033[93m",
         "C": "\033[94m", "D": "\033[90m", "F": "\033[90m", "?": "\033[90m"}
    return f"{c.get(grade, '')}{grade}\033[0m"


def _format_bear_result(r: dict) -> str:
    """Format a single bear ticker result."""
    d = r.get("daily", {})
    w = r.get("weekly", {})
    hull = "BEAR ▼" if not d.get("hull_bull") else "BULL ▲ ⚠"
    cmf = d.get("cmf", 0)
    cmf_str = f"{cmf:+.2f}" + (" 🩸" if cmf < -0.10 else " ⚠" if cmf < 0 else "")
    sqz = "FIRE ⚡" if d.get("sqz_fire") else "COIL ◉" if d.get("sqz_coiled") else f"{d.get('sqz_ratio', 0):.2f}"
    name = r.get("name", r["ticker"])
    if len(name) > 25:
        name = name[:22] + "..."

    bg = _gc(r.get("bear_grade", "?"))

    line1 = (f"  {r['ticker']:<6} {name:<25} "
             f"│ 🐻 {bg} ({r.get('bear_score', 0)}/7)  "
             f"W: {r.get('weekly_bear_score', 0)}/3")
    line2 = (f"         │ HMA: {hull}  CMF: {cmf_str}  "
             f"SQZ: {sqz}  Age: {d.get('trend_age', 0)} ({d.get('trend_phase', '?')})")
    sign = "+" if d.get("trama_dist", 0) >= 0 else ""
    dc_str = "50<200 ☠" if d.get("golden_cross") is False else "50>200 ⚠" if d.get("golden_cross") else ""
    line3 = (f"         │ TRAMA Δ: {sign}{d.get('trama_dist', 0):.1f}%  "
             f"RVOL: {d.get('rvol', 0):.1f}x  Regime: {d.get('regime', '?')}  {dc_str}")
    line4 = (f"         │ Price: ${d.get('price', 0):.2f}  "
             f"RSI: {d.get('pctR_fast', 0):.0f}  "
             f"Aligned: {'✅' if r.get('bear_aligned') else '❌'}")
    return f"{line1}\n{line2}\n{line3}\n{line4}"


def print_bear_results(results: list[dict], funnel_stats: dict, quiet: bool = False):
    """Print formatted bear scanner output."""
    total = len(results)
    aligned = [r for r in results if r.get("bear_aligned")]
    strong_bears = [r for r in results if r.get("bear_score", 0) >= 4.0 and not r.get("bear_aligned")]

    print(f"\n{'='*72}")
    print(f"🐻 Bear Mode Screener — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   📊 Market: {funnel_stats.get('total', 0)} stocks → "
          f"Funnel: {funnel_stats.get('survivors', 0)} → "
          f"Deep scanned: {total}")
    print(f"{'='*72}")

    if aligned:
        print(f"\n☠️  A+ BEAR SETUPS — Multi-TF aligned ({len(aligned)}):\n")
        aligned.sort(key=lambda x: x.get("combined_bear_score", 0), reverse=True)
        for r in aligned:
            print(_format_bear_result(r))
            print()
    else:
        print("\n🏳️  No multi-timeframe bear A+ setups found.")
        print("   Maybe the bears are hibernating.\n")

    if not quiet:
        if strong_bears:
            print(f"📉 Daily A/A+ bears only ({len(strong_bears)}):\n")
            strong_bears.sort(key=lambda x: x.get("bear_score", 0), reverse=True)
            for r in strong_bears[:10]:
                print(_format_bear_result(r))
                print()
            if len(strong_bears) > 10:
                print(f"   ... and {len(strong_bears) - 10} more\n")

        # Grade distribution
        grades = {}
        for r in results:
            bg = r.get("bear_grade", "?")
            grades[bg] = grades.get(bg, 0) + 1
        dist = "  ".join(f"{k}: {v}" for k, v in sorted(grades.items()))
        above_a = sum(v for k, v in grades.items() if k in ("A+", "A"))
        print(f"📊 Bear Grade Distribution: {dist}")
        print(f"🐻 Actionable bears (A+/A): {above_a}\n")

    print(f"{'='*72}")
    quote = "Sell the rip. Buy the dip... in puts." if aligned else "No bear setups today. The bulls live another day."
    print(f"   🐻 Sam says: \"{quote}\"")
    print()


# ═══════════════════════════════════════════════════════════════════
# ████  SAVE / API OUTPUT  ████
# ═══════════════════════════════════════════════════════════════════

def _save_bear_api_output(results: list[dict], funnel_stats: dict):
    """Save to docs/api/bear-screener.json for pipeline consumption."""
    try:
        api_dir = PROJECT_ROOT / "docs" / "api"
        api_dir.mkdir(parents=True, exist_ok=True)

        aligned = [r for r in results if r.get("bear_aligned")]
        strong = [r for r in results if r.get("bear_score", 0) >= 4.0]

        output = {
            "scan_date": datetime.now().isoformat(),
            "direction": "BEAR",
            "description": "Bearish EMA stack scanner — pullback to resistance entries for puts/shorts",
            "funnel_stats": funnel_stats,
            "bear_aligned_count": len(aligned),
            "strong_bear_count": len(strong),
            "bear_setups": [{
                "ticker": r["ticker"],
                "name": r.get("name", r["ticker"]),
                "bear_grade": r.get("bear_grade"),
                "bear_score": r.get("bear_score"),
                "weekly_bear_score": r.get("weekly_bear_score"),
                "combined_bear_score": r.get("combined_bear_score"),
                "bear_aligned": bool(r.get("bear_aligned", False)),
                "price": r.get("daily", {}).get("price"),
                "regime": r.get("daily", {}).get("regime"),
                "cmf": r.get("daily", {}).get("cmf"),
                "sqz_ratio": r.get("daily", {}).get("sqz_ratio"),
                "sqz_coiled": bool(r.get("daily", {}).get("sqz_coiled", False)),
                "sqz_fire": bool(r.get("daily", {}).get("sqz_fire", False)),
                "rvol": r.get("daily", {}).get("rvol"),
                "trend_phase": r.get("daily", {}).get("trend_phase"),
                "hull_bull": bool(r.get("daily", {}).get("hull_bull", False)),
                "golden_cross": bool(r.get("daily", {}).get("golden_cross", False)),
            } for r in sorted(results,
                              key=lambda x: x.get("combined_bear_score", 0),
                              reverse=True)[:50]],
        }

        with open(api_dir / "bear-screener.json", "w") as f:
            json.dump(output, f, indent=2)
        print(f"  💾 Bear feed saved: docs/api/bear-screener.json")
    except Exception as e:
        print(f"  [WARN] Bear API save failed: {e}")


def _save_bear_history(results: list[dict], funnel_stats: dict):
    """Save date-stamped bear results for backtesting."""
    try:
        history_dir = PROJECT_ROOT / "docs" / "api" / "screener-history"
        history_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")

        rows = []
        for r in results:
            d = r.get("daily", {})
            rows.append({
                "ticker": r["ticker"],
                "bear_grade": r.get("bear_grade"),
                "bear_score": r.get("bear_score"),
                "weekly_bear_score": r.get("weekly_bear_score"),
                "combined_bear_score": r.get("combined_bear_score"),
                "bear_aligned": bool(r.get("bear_aligned", False)),
                "price": d.get("price"),
                "cmf": round(d.get("cmf", 0), 3),
                "hull_bull": bool(d.get("hull_bull", False)),
                "trend_phase": d.get("trend_phase"),
                "sqz_ratio": round(d.get("sqz_ratio", 0), 3),
                "rvol": round(d.get("rvol", 0), 2),
            })

        output = {
            "date": date_str,
            "scan_time": datetime.now().isoformat(),
            "direction": "BEAR",
            "funnel_stats": funnel_stats,
            "total_graded": len(rows),
            "bear_aligned_count": len([r for r in rows if r.get("bear_aligned")]),
            "results": rows,
        }

        filepath = history_dir / f"{date_str}_bear.json"
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# ████  CLI MAIN  ████
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="🐻 Bear Mode Screener — Bearish EMA stack pullback finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tickers", type=str, help="Comma-separated tickers (skip funnel)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--quiet", action="store_true", help="Only show A+/A setups")
    parser.add_argument("--csv", type=str, help="Save results to CSV file")
    args = parser.parse_args()

    t0 = time.time()
    funnel_stats = {"total": 0, "survivors": 0, "mode": "direct", "direction": "BEAR"}

    if args.tickers:
        tickers_to_scan = [t.strip().upper() for t in args.tickers.split(",")]
        tv_lookup = {}
        funnel_stats = {"total": len(tickers_to_scan),
                        "survivors": len(tickers_to_scan),
                        "mode": "direct", "direction": "BEAR"}
        print(f"🐻 Direct bear scan: {len(tickers_to_scan)} tickers\n")
    else:
        # ── WHOLE MARKET — TradingView bear funnel ──
        print("🐻 BEAR MODE SCAN — Loading bearish universe...\n")

        print("  ⚡ Stage 1: TradingView bulk API (bear filters)...")
        raw_stocks = _tv_fetch_bear_stocks()
        funnel_stats["total"] = len(raw_stocks)
        print(f"     → {len(raw_stocks)} bearish stocks loaded\n")

        print("  🔍 Stage 2: Progressive bear elimination funnel...")
        survivors = bear_funnel_filter(raw_stocks)
        funnel_stats["survivors"] = len(survivors)
        funnel_stats["mode"] = "market"

        tickers_to_scan = [s["ticker"] for s in survivors]
        tv_lookup = {s["ticker"]: s for s in survivors}

    # ── Stage 3+4: Bear deep scan ──
    print(f"  🧪 Stage 3: Batch deep scanning {len(tickers_to_scan)} "
          f"bear candidates (daily + weekly)...")
    results = bear_batch_deep_scan(tickers_to_scan, tv_lookup, batch_size=100)

    elapsed = time.time() - t0
    funnel_stats["elapsed_sec"] = round(elapsed, 1)
    funnel_stats["deep_scanned"] = len(results)
    print(f"\n  ⏱  Total time: {elapsed:.1f}s\n")

    if not results:
        print("❌ No valid bear results. The bulls won this round.")
        return

    results.sort(key=lambda x: x.get("combined_bear_score", 0), reverse=True)

    if args.json:
        output = {
            "scan_date": datetime.now().isoformat(),
            "direction": "BEAR",
            "funnel_stats": funnel_stats,
            "total_deep_scanned": len(results),
            "bear_aligned": [r for r in results if r.get("bear_aligned")],
            "strong_bears": [r for r in results
                             if r.get("bear_score", 0) >= 4.0
                             and not r.get("bear_aligned")],
            "all_results": results,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print_bear_results(results, funnel_stats, quiet=args.quiet)

    if args.csv:
        _save_bear_csv(results, args.csv)

    _save_bear_api_output(results, funnel_stats)
    _save_bear_history(results, funnel_stats)


def _save_bear_csv(results: list[dict], filepath: str):
    """Save flat CSV."""
    import csv
    rows = []
    for r in results:
        d = r.get("daily", {})
        rows.append({
            "ticker": r["ticker"],
            "name": r.get("name", ""),
            "bear_grade": r.get("bear_grade", ""),
            "bear_score": r.get("bear_score", 0),
            "weekly_bear_score": r.get("weekly_bear_score", 0),
            "combined_bear_score": r.get("combined_bear_score", 0),
            "bear_aligned": r.get("bear_aligned", False),
            "hull_bull": d.get("hull_bull"),
            "cmf": d.get("cmf"),
            "sqz_ratio": d.get("sqz_ratio"),
            "trend_age": d.get("trend_age"),
            "trend_phase": d.get("trend_phase"),
            "rvol": d.get("rvol"),
            "regime": d.get("regime"),
            "price": d.get("price"),
            "golden_cross": d.get("golden_cross"),
        })
    if rows:
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"💾 Saved {len(rows)} bear results to {filepath}")


# ═══════════════════════════════════════════════════════════════════
# ████  IMPORTABLE ENTRY POINT (for pipeline)  ████
# ═══════════════════════════════════════════════════════════════════

def run_bear_screener(save_history: bool = True) -> dict:
    """
    Importable entry point for the pipeline.
    Runs the full bear market scan, saves results, returns summary.

    Returns:
        {
            "results": [...],
            "funnel_stats": {...},
            "bear_aligned": [...],   # daily + weekly aligned bears
            "strong_bears": [...],   # bear_score >= 4.0
        }
    """
    t0 = time.time()

    # Stage 1: TradingView bulk fetch (bear)
    raw_stocks = _tv_fetch_bear_stocks()

    # Stage 2: Bear funnel
    survivors = bear_funnel_filter(raw_stocks, verbose=False)
    tv_lookup = {s["ticker"]: s for s in survivors}
    tickers = [s["ticker"] for s in survivors]

    # Stage 3: Bear deep scan
    results = bear_batch_deep_scan(tickers, tv_lookup, batch_size=100)
    results.sort(key=lambda x: x.get("combined_bear_score", 0), reverse=True)

    elapsed = time.time() - t0

    funnel_stats = {
        "total": len(raw_stocks),
        "survivors": len(survivors),
        "deep_scanned": len(results),
        "elapsed_sec": round(elapsed, 1),
        "mode": "market",
        "direction": "BEAR",
    }

    # Categorize
    bear_aligned = [r for r in results
                    if r.get("bear_aligned")]

    strong_bears = [r for r in results
                    if r.get("bear_score", 0) >= 4.0]

    # Save
    _save_bear_api_output(results, funnel_stats)

    if save_history:
        _save_bear_history(results, funnel_stats)

    return {
        "results": results,
        "funnel_stats": funnel_stats,
        "bear_aligned": bear_aligned,
        "strong_bears": strong_bears,
    }


if __name__ == "__main__":
    main()
