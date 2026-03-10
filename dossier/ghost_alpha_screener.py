#!/usr/bin/env python3
"""
👻 Ghost Alpha Screener — Whole-Market A+ Setup Finder

Port of ghost_alpha.pine V2 grading with a FUNNEL architecture:
  Stage 1 → TradingView bulk API: fetch ~8000 US stocks in ONE request
  Stage 2 → Progressive filters eliminate 90%+ using pre-computed technicals
  Stage 3 → yfinance deep scan on ~100-200 survivors for full 5-axis grading
  Stage 4 → Multi-timeframe alignment (daily + weekly must both be A/A+)

Total time: ~3-5 minutes for the ENTIRE US equity market.

The 5 Independent Axes (max 5.0):
  1. Trend Direction  — Hull MA direction
  2. Volume Flow      — Chaikin Money Flow (CMF)
  3. Volatility       — ATR Squeeze ratio (0.75–1.5 sweet spot)
  4. Trend Maturity   — Bars since Hull flip (5–30 = fresh)
  5. Exhaustion       — Williams %R + TRAMA distance

Usage:
    python -m dossier.ghost_alpha_screener                       # Whole market
    python -m dossier.ghost_alpha_screener --tickers NVDA,AVGO   # Specific tickers
    python -m dossier.ghost_alpha_screener --watchlist            # Core watchlist only
    python -m dossier.ghost_alpha_screener --json                 # Machine output
    python -m dossier.ghost_alpha_screener --quiet                # Only A+/A setups

© mph1nance + Sam the Quant Ghost
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

try:
    from dossier.config import CORE_WATCHLIST, SECTOR_ETFS
except ImportError:
    CORE_WATCHLIST = [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
        "AMD", "AVGO", "TSM", "MRVL", "QCOM",
        "JPM", "GS", "V", "MA",
        "PLTR", "COIN", "HOOD", "SOFI",
        "XOM", "OXY",
    ]
    SECTOR_ETFS = [
        "XLK", "XLF", "XLE", "XLV", "XLI",
        "XLC", "XLRE", "XLP", "XLU", "XLB", "XLY",
    ]


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCANNER  ████
# ═══════════════════════════════════════════════════════════════════
# One POST request → ~8000 US stocks with pre-computed technicals.
# This replaces thousands of individual API calls.

TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"

TV_COLUMNS = [
    "name",                     # 0  ticker
    "description",              # 1  company name
    "close",                    # 2  last price
    "change",                   # 3  % change today
    "volume",                   # 4  today's volume
    "average_volume_30d_calc",  # 5  30d avg volume
    "market_cap_basic",         # 6  market cap
    "SMA200",                   # 7  SMA 200
    "SMA50",                    # 8  SMA 50
    "EMA21",                    # 9  EMA 21 (exact Tao stack)
    "RSI",                      # 10 RSI(14)
    "ADX",                      # 11 ADX(14)
    "ATR",                      # 12 ATR(14)
    "Perf.W",                   # 13 weekly performance %
    "Perf.1M",                  # 14 monthly performance %
    "Recommend.All",            # 15 TV signal (-1 to +1)
    "Stoch.K",                  # 16 Stochastic K
    "BB.upper",                 # 17 Bollinger upper
    "BB.lower",                 # 18 Bollinger lower
    "Perf.3M",                  # 19 3-month performance %
    # ── Ghost Grade Axis Columns ──────────────────────
    "W.R",                      # 20 Williams %R (Axis 5: Exhaustion)
    "ADX+DI",                   # 21 +DI (Axis 4: Trend direction)
    "ADX-DI",                   # 22 -DI (Axis 4: Trend direction)
    "EMA50",                    # 23 EMA 50 (golden cross)
    "EMA200",                   # 24 EMA 200 (golden cross)
    "Recommend.MA",             # 25 MA recommendation -1 to +1 (Axis 1)
    "relative_volume_10d_calc", # 26 Relative volume 10d (Axis 2)
    "Stoch.RSI.K",              # 27 Stoch RSI K (Axis 5: Momentum)
    "MACD.macd",                # 28 MACD line (trend confirmation)
    "EMA34",                    # 29 EMA 34 (exact Tao stack)
    "EMA55",                    # 30 EMA 55 (exact Tao stack)
    "CCI20",                    # 31 CCI 20 (mean reversion filter)
    "ChaikinMoneyFlow",         # 32 CMF (Axis 2: direct! No yfinance needed)
    "HullMA9",                  # 33 Hull MA 9 (Axis 1: trend proxy)
    "EMA89",                    # 34 EMA 89 (exact Tao stack)
]


def _tv_fetch_all_stocks() -> list[dict]:
    """
    Fetch the entire US equity universe from TradingView's scanner API.
    Returns list of dicts with pre-computed technicals.
    Server-side filters do the heavy lifting — we get ~1500 stocks
    instead of ~3100+ by pushing axis filters into the API payload.
    One request. ~2 seconds. Beautiful.
    """
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            # ── Hard floors (always applied) ──
            {"left": "close", "operation": "greater", "right": 5},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 500_000},
            {"left": "market_cap_basic", "operation": "greater", "right": 300_000_000},
            # ── Ax4: ADX ≥ 15 (some trend) ──
            {"left": "ADX", "operation": "greater", "right": 15},
            # ── Ax5: RSI not extreme (20-75) ──
            {"left": "RSI", "operation": "greater", "right": 20},
            {"left": "RSI", "operation": "less", "right": 75},
            # ── Ax1: MACD > 0 (momentum confirmation) ──
            {"left": "MACD.macd", "operation": "greater", "right": 0},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": TV_COLUMNS,
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
            # Ghost Grade axis columns
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
        })

    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════
# Each stage eliminates the biggest group of losers first.
# The order matters — biggest cuts first = fastest total scan.

def funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """
    Progressive filter funnel. Each stage is designed to cut
    the most disqualified tickers first, using data we already have.

    Returns only the survivors worth deep-scanning.
    """
    import time as _t
    _t0 = _t.time()
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ FUNNEL: {total} stocks loaded (server pre-filtered: $5+, Vol 500K+, Cap $300M+, ADX≥15, RSI 20-75)")

    # ── STAGE 2A: Price & Liquidity Floor ─────────────────────────
    # Eliminates penny stocks, illiquid, micro-caps
    # Cuts: ~50-60% of universe
    survivors = [s for s in stocks if (
        s["price"] >= 5.0
        and s["avg_vol_30d"] >= 500_000
        and (s["market_cap"] or 0) >= 300_000_000  # $300M+
    )]
    cut = total - len(survivors)
    if verbose:
        print(f"  ├─ Price ≥$5 + Vol ≥500K + Cap ≥$300M → {len(survivors)} survive ({cut} cut)")

    # ── STAGE 2B: Trend Direction — SMA 200 ───────────────────────
    # Ax1 proxy: If price below SMA 200, weekly trend fails.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["sma_200"] is not None
        and s["price"] > s["sma_200"]
    )]
    if verbose:
        print(f"  ├─ Ax1: Price > SMA 200 (bull) ─────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2C: Golden Cross — EMA 50 > EMA 200 ────────────────
    # Ax1 proxy: Strongest trend confirmation. Eliminates stocks
    # that are above SMA200 but losing momentum.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("ema_50") is not None
        and s.get("ema_200") is not None
        and s["ema_50"] > s["ema_200"]
    )]
    if verbose:
        print(f"  ├─ Ax1: Golden Cross (EMA50>200) ──→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2D: EMA Stacking (Tao: 21>34>55>89 EXACT) ───────
    # Ax1+4: TV has all 4 Tao EMAs natively. No proxies.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("ema_21") is not None
        and s.get("ema_34") is not None
        and s.get("ema_55") is not None
        and s.get("ema_89") is not None
        and s["ema_21"] > s["ema_34"] > s["ema_55"] > s["ema_89"]
    )]
    if verbose:
        print(f"  ├─ Ax1: EMA Stack 21>34>55>89 ────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2E: MACD Momentum Confirmation ─────────────────────
    # Ax1: MACD line > 0 = short-term momentum still accelerating.
    # Stacked EMAs + negative MACD = coasting on a dying move.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("macd") is None
        or s["macd"] > 0
    )]
    if verbose:
        print(f"  ├─ Ax1: MACD > 0 (momentum) ──────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2F: Monthly Performance > 0 ────────────────────────
    # Ax4: If 30-day return is negative, the trend is unwinding
    # even if EMAs haven't crossed yet. Demand recent confirmation.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("perf_1m") is None
        or s["perf_1m"] > 0
    )]
    if verbose:
        print(f"  ├─ Ax4: Perf.1M > 0% (recent) ───→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2G: MA Recommendation ──────────────────────────────
    # Ax1 proxy: TV's composite MA signal. Anything < -0.3 = SELL.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("recommend_ma") is None
        or s["recommend_ma"] > -0.3
    )]
    if verbose:
        print(f"  ├─ Ax1: MA Recommend > -0.3 ──────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2H: Keltner / Extension Filter ─────────────────────
    # Ax5 proxy: If price >8% above EMA 21, way extended.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["ema_21"] is not None
        and s["ema_21"] > 0
        and ((s["price"] - s["ema_21"]) / s["ema_21"] * 100) <= 8.0
        and ((s["price"] - s["ema_21"]) / s["ema_21"] * 100) >= -8.0
    )]
    if verbose:
        print(f"  ├─ Ax5: Within ±8% EMA 21 (Kelt) ─→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2F: Williams %R Zone ───────────────────────────────
    # Ax5 proxy: Williams %R from TV. Kill overbought (> -20)
    # and deeply oversold (< -80) — Axis 5 will score 0.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("williams_r") is None  # keep if no data
        or (-80 <= s["williams_r"] <= -20)
    )]
    if verbose:
        print(f"  ├─ Ax5: W%R -80 to -20 (no exh) ──→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2G: Stoch RSI Overbought ───────────────────────────
    # Ax5 proxy: Stoch RSI K > 85 = very overbought momentum.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("stoch_rsi_k") is None
        or s["stoch_rsi_k"] <= 85
    )]
    if verbose:
        print(f"  ├─ Ax5: Stoch.RSI.K ≤85 ─────────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2K: Stochastic K < 80 ─────────────────────────────
    # Ax5: Classic overbought filter. Stoch.K > 80 = extended.
    # Bounce 2.0 wants ≤40, but ≤80 catches the worst offenders.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("stoch_k") is None
        or s["stoch_k"] < 80
    )]
    if verbose:
        print(f"  ├─ Ax5: Stoch.K < 80 ────────────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2L: CCI20 Goldilocks Zone ─────────────────────────
    # Ax5: CCI > 100 = statistically overbought,
    # CCI < -100 = oversold. Sweet spot is -100 to +100.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s.get("cci20") is None
        or (-100 <= s["cci20"] <= 100)
    )]
    if verbose:
        print(f"  ├─ Ax5: CCI20 ±100 (goldilocks) ─→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2M: RSI Exhaustion Pre-Filter ─────────────────────
    # RSI > 75 = overbought, RSI < 20 = deeply oversold
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["rsi"] is not None
        and 20 <= s["rsi"] <= 75
    )]
    if verbose:
        print(f"  ├─ Ax5: RSI 20-75 (no extremes) ──→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2N: ADX Trend Strength + Direction ────────────────
    # Ax4 proxy: ADX < 15 = no trend. Also require +DI > -DI
    # for bullish directional confirmation.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["adx"] is not None
        and s["adx"] >= 15
        and (s.get("adx_plus_di") is None or s.get("adx_minus_di") is None
             or s["adx_plus_di"] > s["adx_minus_di"])
    )]
    if verbose:
        print(f"  ├─ Ax4: ADX ≥15 + DI bull ────────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2O: Volume Life Check ─────────────────────────────
    # Ax2 proxy: Use TV's relative_volume_10d if available,
    # fall back to raw volume ratio.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        (s.get("rvol_10d") is not None and s["rvol_10d"] >= 0.3)
        or (s.get("rvol_10d") is None
            and s["volume"] > 0 and s["avg_vol_30d"] > 0
            and (s["volume"] / s["avg_vol_30d"]) >= 0.3)
    )]
    if verbose:
        print(f"  ├─ Ax2: RVOL ≥0.3 (not dead) ─────→ {len(survivors)} survive ({prev - len(survivors)} cut)")

    # ── STAGE 2P: Weekly Performance Sanity ─────────────────────
    # Ax3+5: Blow-off territory kills volatility + exhaustion axes.
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["perf_1w"] is None
        or (-15 <= s["perf_1w"] <= 15)
    )]
    if verbose:
        print(f"  ├─ Ax3: Weekly ±15% (no blow-off) → {len(survivors)} survive ({prev - len(survivors)} cut)")

    if verbose:
        pct = (1 - len(survivors) / total) * 100 if total > 0 else 0
        elapsed = _t.time() - _t0
        print(f"  └─ FUNNEL COMPLETE: {len(survivors)} survivors ({pct:.0f}% eliminated) [{elapsed:.1f}s]")
        print()

    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — FULL GHOST ALPHA V2 ENGINE  ████
# ═══════════════════════════════════════════════════════════════════
# Only called for funnel survivors. Exact Pine Script port.

def wma(series: pd.Series, period: int) -> pd.Series:
    """Weighted Moving Average — matches Pine Script ta.wma()."""
    weights = np.arange(1, period + 1, dtype=float)
    return series.rolling(period).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )


def hma(series: pd.Series, period: int) -> pd.Series:
    """Hull Moving Average — exact Pine Script HMA()."""
    half = max(period // 2, 1)
    sqrt_p = max(int(round(math.sqrt(period))), 1)
    wma_half = wma(series, half)
    wma_full = wma(series, period)
    diff = 2 * wma_half - wma_full
    return wma(diff, sqrt_p)


def calculate_trama(df: pd.DataFrame, length: int = 34) -> tuple[pd.Series, pd.Series]:
    """
    TRAMA — exact Pine Script port (lines 180-184).
    Returns (trama_series, t_tc_series).
    """
    high, low, close = df["High"], df["Low"], df["Close"]

    hh = high.rolling(length).max()
    t_hh = (hh.diff() > 0).astype(float)

    ll = low.rolling(length).min()
    t_ll = (ll.diff() < 0).astype(float)

    active = ((t_hh > 0) | (t_ll > 0)).astype(float)
    t_tc = active.rolling(length).mean() ** 2

    trama = np.full(len(close), np.nan)
    trama[0] = close.iloc[0]
    for i in range(1, len(close)):
        tc = t_tc.iloc[i] if not np.isnan(t_tc.iloc[i]) else 0.0
        prev = trama[i - 1] if not np.isnan(trama[i - 1]) else close.iloc[i]
        trama[i] = prev + tc * (close.iloc[i] - prev)

    return pd.Series(trama, index=close.index), t_tc


def calculate_cmf(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Chaikin Money Flow — exact Pine Script port (lines 381-384)."""
    high, low, close, volume = df["High"], df["Low"], df["Close"], df["Volume"]
    candle_range = high - low
    mf = candle_range.replace(0, np.nan)
    mf = ((close - low) - (high - close)) / mf
    mf = mf.fillna(0)
    mfv = mf * volume
    vol_sma = volume.rolling(period).mean()
    cmf = mfv.rolling(period).mean() / vol_sma.replace(0, np.nan)
    return cmf.fillna(0)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """True Range → ATR."""
    high, low, close = df["High"], df["Low"], df["Close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def calculate_williams_r(df: pd.DataFrame, period: int) -> pd.Series:
    """Williams %R — exact Pine Script."""
    high, low, close = df["High"], df["Low"], df["Close"]
    hh = high.rolling(period).max()
    ll = low.rolling(period).min()
    denom = (hh - ll).replace(0, np.nan)
    return 100.0 * (close - hh) / denom


def calculate_rvol(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Relative Volume."""
    vol = df["Volume"]
    baseline = vol.rolling(period).mean().replace(0, np.nan)
    return (vol / baseline).fillna(0)


def compute_ghost_grade(df: pd.DataFrame, hull_len: int = 55, trama_len: int = 34,
                        exh_fast: int = 21, exh_slow: int = 112,
                        exh_threshold: int = 20,
                        exh_fast_smooth: int = 7, exh_slow_smooth: int = 3) -> dict:
    """
    Compute Ghost Alpha V2 grade for a DataFrame of OHLCV data.
    Works on both daily and weekly DataFrames.
    """
    min_bars = max(hull_len, trama_len, exh_slow) + 50
    if df is None or len(df) < min_bars:
        return {"grade": "?", "score": 0, "error": f"Need {min_bars} bars, got {len(df) if df is not None else 0}"}

    close = df["Close"]
    price = float(close.iloc[-1])

    # ── Hull MA ──
    hull_series = hma(close, hull_len)
    hull_val = hull_series.iloc[-1]
    hull_prev = hull_series.iloc[-3] if len(hull_series) > 3 else hull_val
    hull_bull = hull_val > hull_prev

    # ── TRAMA ──
    trama_series, t_tc_series = calculate_trama(df, trama_len)
    trama_val = trama_series.iloc[-1]
    trama_prev = trama_series.iloc[-2] if len(trama_series) > 1 else trama_val
    trama_dist = (price - trama_val) / trama_val * 100 if trama_val != 0 else 0
    regime_bull = trama_val > trama_prev
    t_tc = t_tc_series.iloc[-1] if not np.isnan(t_tc_series.iloc[-1]) else 0
    regime_strong = t_tc > 0.25
    regime_moderate = t_tc > 0.09

    # ── CMF ──
    cmf = calculate_cmf(df)
    cmf_val = float(cmf.iloc[-1])

    # ── ATR Squeeze ──
    atr = calculate_atr(df, 14)
    atr_baseline = atr.rolling(50).mean()
    atr_val = float(atr.iloc[-1])
    baseline_val = float(atr_baseline.iloc[-1]) if not np.isnan(atr_baseline.iloc[-1]) else atr_val
    sqz_ratio = atr_val / baseline_val if baseline_val > 0 else 1.0
    sqz_coiled = sqz_ratio < 0.75
    sqz_ratio_prev = float(atr.iloc[-2] / atr_baseline.iloc[-2]) if (
        len(atr) > 1 and not np.isnan(atr_baseline.iloc[-2]) and atr_baseline.iloc[-2] > 0
    ) else sqz_ratio
    sqz_fire = sqz_ratio >= 0.75 and sqz_ratio_prev < 0.75

    # ── Williams %R Exhaustion ──
    s_pctR = calculate_williams_r(df, exh_fast)
    l_pctR = calculate_williams_r(df, exh_slow)
    if exh_fast_smooth > 1:
        s_pctR = s_pctR.ewm(span=exh_fast_smooth, adjust=False).mean()
    if exh_slow_smooth > 1:
        l_pctR = l_pctR.ewm(span=exh_slow_smooth, adjust=False).mean()

    s_pctR_val = float(s_pctR.iloc[-1]) if not np.isnan(s_pctR.iloc[-1]) else -50
    l_pctR_val = float(l_pctR.iloc[-1]) if not np.isnan(l_pctR.iloc[-1]) else -50
    exh_ob = s_pctR_val >= -exh_threshold and l_pctR_val >= -exh_threshold
    exh_os = s_pctR_val <= (-100 + exh_threshold) and l_pctR_val <= (-100 + exh_threshold)

    # ── Trend Age ──
    hull_bull_series = hull_series > hull_series.shift(2)
    trend_age = 0
    for i in range(len(hull_bull_series) - 1, -1, -1):
        if hull_bull_series.iloc[i] == hull_bull:
            trend_age += 1
        else:
            break
    trend_phase = "FRESH" if trend_age < 5 else "YOUNG" if trend_age < 20 else "MATURE" if trend_age < 50 else "AGING"

    # ── RVOL ──
    rvol = calculate_rvol(df)
    rvol_val = float(rvol.iloc[-1])

    # ── SMA 50/200 ──
    sma_50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
    sma_200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    golden_cross = sma_50 > sma_200 if sma_50 and sma_200 else None

    # ═══════════════════════════════════════════════════════════
    # ████  GRADE V2 SCORING — Pine Script Lines 531-558  ████
    # ═══════════════════════════════════════════════════════════

    ax1 = 1.0 if hull_bull else 0.0
    ax2 = 1.0 if cmf_val > 0.10 else 0.5 if cmf_val > 0.0 else 0.0
    ax3 = 1.0 if (0.75 <= sqz_ratio <= 1.5) or sqz_fire else 0.0
    ax4 = 1.0 if 5 <= trend_age <= 30 else 0.5 if 30 < trend_age <= 50 else 0.0
    no_exh = not exh_ob and not exh_os
    ax5 = 1.0 if (no_exh and abs(trama_dist) < 3.0) else 0.5 if no_exh else 0.0

    g_score = ax1 + ax2 + ax3 + ax4 + ax5
    if g_score >= 4.5:
        grade = "A+"
    elif g_score >= 4.0:
        grade = "A"
    elif g_score >= 3.0:
        grade = "B"
    elif g_score >= 2.0:
        grade = "C"
    elif g_score >= 1.0:
        grade = "D"
    else:
        grade = "F"

    if regime_strong:
        regime = "BULL" if regime_bull else "BEAR"
    elif regime_moderate:
        regime = "MODERATE"
    else:
        regime = "CHOP"

    return {
        "grade": grade,
        "score": round(g_score, 1),
        "axes": {"trend": ax1, "volume": ax2, "volatility": ax3, "maturity": ax4, "exhaustion": ax5},
        "hull_bull": hull_bull,
        "cmf": round(cmf_val, 3),
        "sqz_ratio": round(sqz_ratio, 2),
        "sqz_coiled": sqz_coiled,
        "sqz_fire": sqz_fire,
        "trend_age": trend_age,
        "trend_phase": trend_phase,
        "pctR_fast": round(s_pctR_val, 1),
        "pctR_slow": round(l_pctR_val, 1),
        "exh_ob": exh_ob,
        "exh_os": exh_os,
        "trama_dist": round(trama_dist, 2),
        "regime": regime,
        "rvol": round(rvol_val, 2),
        "price": round(price, 2),
        "sma_50": round(sma_50, 2) if sma_50 else None,
        "sma_200": round(sma_200, 2) if sma_200 else None,
        "golden_cross": golden_cross,
    }


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 4 — MULTI-TIMEFRAME DEEP SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def resample_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily OHLCV to weekly bars."""
    return df.resample("W").agg({
        "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum",
    }).dropna()


def deep_scan_ticker(ticker: str, df: pd.DataFrame = None,
                     tv_data: dict | None = None) -> dict | None:
    """
    Full Ghost Alpha V2 deep scan on daily + weekly timeframes.
    Accepts a pre-downloaded DataFrame (from batch download)
    or fetches its own if df is None.
    """
    try:
        if df is None:
            stock = yf.Ticker(ticker)
            df = stock.history(period="3y")
        if df is None or len(df) < 200:
            return None

        # Daily grade
        daily_grade = compute_ghost_grade(df, hull_len=55, trama_len=34, exh_fast=21, exh_slow=112)

        # Weekly grade (higher-TF adapted params)
        weekly_df = resample_to_weekly(df)
        if len(weekly_df) < 50:
            weekly_grade = {"grade": "?", "score": 0, "error": "Insufficient weekly data"}
        else:
            weekly_grade = compute_ghost_grade(weekly_df, hull_len=89, trama_len=55, exh_fast=14, exh_slow=55)

        d_score = daily_grade.get("score", 0)
        w_score = weekly_grade.get("score", 0)
        both_aligned = d_score >= 4.0 and w_score >= 4.0
        either_hot = d_score >= 4.0 or w_score >= 4.0

        result = {
            "ticker": ticker,
            "daily": daily_grade,
            "weekly": weekly_grade,
            "both_aligned": both_aligned,
            "either_hot": either_hot,
            "combined_score": round(d_score + w_score, 1),
        }

        if tv_data:
            result["name"] = tv_data.get("name", ticker)
            result["market_cap"] = tv_data.get("market_cap")

        return result
    except Exception:
        return None


def batch_deep_scan(tickers: list[str], tv_lookup: dict,
                    batch_size: int = 100) -> list[dict]:
    """
    Batch download OHLCV data via yf.download() with threading,
    then run Ghost Grade on each ticker. ~3-5x faster than sequential.
    """
    results = []
    errors = 0
    total = len(tickers)

    for batch_start in range(0, total, batch_size):
        batch = tickers[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"\r     📦 Batch {batch_num}/{total_batches}: "
              f"downloading {len(batch)} tickers...", end="", flush=True)

        try:
            # yf.download with threads=True parallelizes HTTP requests
            raw = yf.download(
                batch, period="3y", group_by="ticker",
                threads=True, progress=False,
            )
        except Exception as e:
            print(f"\n     ⚠ Batch download error: {e}")
            # Fall back to individual downloads for this batch
            for ticker in batch:
                result = deep_scan_ticker(ticker, tv_data=tv_lookup.get(ticker))
                if result:
                    results.append(result)
                else:
                    errors += 1
            continue

        # Process each ticker from the batch DataFrame
        for ticker in batch:
            try:
                if len(batch) == 1:
                    # Single ticker: no multi-level columns
                    df = raw.copy()
                else:
                    df = raw[ticker].copy()
                df = df.dropna(how="all")
                if df.empty or len(df) < 200:
                    errors += 1
                    continue
                result = deep_scan_ticker(ticker, df=df,
                                          tv_data=tv_lookup.get(ticker))
                if result:
                    results.append(result)
                else:
                    errors += 1
            except (KeyError, Exception):
                errors += 1

        pct = min((batch_start + len(batch)) / total * 100, 100)
        print(f"\r     📦 Batch {batch_num}/{total_batches}: "
              f"{len(results)} graded, {errors} errors ({pct:.0f}%)"
              + " " * 10, end="", flush=True)

    print(f"\r     ✅ Scanned {len(results)} tickers ({errors} errors)"
          + " " * 30)
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT FORMATTING  ████
# ═══════════════════════════════════════════════════════════════════

def _gc(grade: str) -> str:
    """ANSI color for grade."""
    c = {"A+": "\033[96m", "A": "\033[92m", "B": "\033[94m",
         "C": "\033[93m", "D": "\033[91m", "F": "\033[31m", "?": "\033[90m"}
    return f"{c.get(grade, '')}{grade}\033[0m"


def _format_result(r: dict) -> str:
    """Format a single ticker result."""
    d, w = r["daily"], r["weekly"]
    hull = "BULL ▲" if d.get("hull_bull") else "BEAR ▼"
    exh = "OB ⚠" if d.get("exh_ob") else "OS ⚠" if d.get("exh_os") else "CLEAR"
    sqz = "FIRE ⚡" if d.get("sqz_fire") else "COIL ◉" if d.get("sqz_coiled") else f"{d.get('sqz_ratio', 0):.2f}"
    name = r.get("name", r["ticker"])
    if len(name) > 25:
        name = name[:22] + "..."

    line1 = (f"  {r['ticker']:<6} {name:<25} "
             f"│ W: {_gc(w.get('grade', '?'))} ({w.get('score', 0)}/5)  "
             f"D: {_gc(d.get('grade', '?'))} ({d.get('score', 0)}/5)")
    line2 = (f"         │ HMA: {hull}  CMF: {d.get('cmf', 0):+.2f}  "
             f"SQZ: {sqz}  Age: {d.get('trend_age', 0)} ({d.get('trend_phase', '?')})  %R: {exh}")
    sign = "+" if d.get("trama_dist", 0) >= 0 else ""
    gc_str = "50>200 ✓" if d.get("golden_cross") else "50<200 ✗" if d.get("golden_cross") is not None else ""
    line3 = (f"         │ TRAMA Δ: {sign}{d.get('trama_dist', 0):.1f}%  "
             f"RVOL: {d.get('rvol', 0):.1f}x  Regime: {d.get('regime', '?')}  {gc_str}")
    # Axis breakdown
    axes = d.get("axes", {})
    line4 = (f"         │ Axes: T:{axes.get('trend', 0):.0f} V:{axes.get('volume', 0):.1f} "
             f"σ:{axes.get('volatility', 0):.0f} M:{axes.get('maturity', 0):.1f} "
             f"E:{axes.get('exhaustion', 0):.1f}")
    return f"{line1}\n{line2}\n{line3}\n{line4}"


def print_results(results: list[dict], funnel_stats: dict, quiet: bool = False):
    """Print formatted scanner output."""
    total = len(results)
    both_a = [r for r in results if r["both_aligned"]]
    daily_hot = [r for r in results if r["daily"].get("score", 0) >= 4.0 and not r["both_aligned"]]
    weekly_hot = [r for r in results if r["weekly"].get("score", 0) >= 4.0 and not r["both_aligned"]]

    print(f"\n{'='*72}")
    print(f"👻 Ghost Alpha Screener — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   📊 Market: {funnel_stats.get('total', 0)} stocks → "
          f"Funnel: {funnel_stats.get('survivors', 0)} → "
          f"Deep scanned: {total}")
    print(f"{'='*72}")

    if both_a:
        print(f"\n🏆 A+ SETUPS — Weekly & Daily aligned ({len(both_a)}):\n")
        both_a.sort(key=lambda x: x["combined_score"], reverse=True)
        for r in both_a:
            print(_format_result(r))
            print()
    else:
        print("\n💀 No multi-timeframe A+ setups found.")
        print("   Patience is a position.\n")

    if not quiet:
        if daily_hot:
            print(f"📈 Daily A/A+ only ({len(daily_hot)}):\n")
            daily_hot.sort(key=lambda x: x["daily"].get("score", 0), reverse=True)
            for r in daily_hot[:10]:  # Cap at 10
                print(_format_result(r))
                print()
            if len(daily_hot) > 10:
                print(f"   ... and {len(daily_hot) - 10} more\n")

        if weekly_hot:
            print(f"📅 Weekly A/A+ only ({len(weekly_hot)}):\n")
            weekly_hot.sort(key=lambda x: x["weekly"].get("score", 0), reverse=True)
            for r in weekly_hot[:10]:
                print(_format_result(r))
                print()
            if len(weekly_hot) > 10:
                print(f"   ... and {len(weekly_hot) - 10} more\n")

        # Grade distribution
        grades = {}
        for r in results:
            dg = r["daily"].get("grade", "?")
            grades[dg] = grades.get(dg, 0) + 1
        dist = "  ".join(f"{k}: {v}" for k, v in sorted(grades.items()))
        below = sum(v for k, v in grades.items() if k not in ("A+", "A"))
        print(f"📊 Daily Grade Distribution: {dist}")
        print(f"💀 No-Trade Zone: {below} tickers below A\n")

    print(f"{'='*72}")
    quote = "God-tier setups. Execute with conviction." if both_a else "No A+ setups today. The market owes you nothing."
    print(f"   👻 Sam says: \"{quote}\"")
    print()


def output_json(results: list[dict], funnel_stats: dict):
    """Machine-readable JSON output."""
    output = {
        "scan_date": datetime.now().isoformat(),
        "funnel_stats": funnel_stats,
        "total_deep_scanned": len(results),
        "a_plus_setups": [r for r in results if r["both_aligned"]],
        "daily_hot": [r for r in results if r["daily"].get("score", 0) >= 4.0 and not r["both_aligned"]],
        "weekly_hot": [r for r in results if r["weekly"].get("score", 0) >= 4.0 and not r["both_aligned"]],
        "all_results": results,
    }
    print(json.dumps(output, indent=2, default=str))


# ═══════════════════════════════════════════════════════════════════
# ████  CLI MAIN  ████
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="👻 Ghost Alpha Screener — Whole-market A+ setup finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tickers", type=str, help="Comma-separated tickers (skip funnel)")
    parser.add_argument("--watchlist", action="store_true", help="Core watchlist only (skip funnel)")
    parser.add_argument("--sectors", action="store_true", help="Include sector ETFs with watchlist")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--csv", type=str, help="Save results to CSV file")
    parser.add_argument("--quiet", action="store_true", help="Only show A+/A setups")
    parser.add_argument("--no-funnel", action="store_true", help="Skip TradingView funnel, scan all given tickers")
    args = parser.parse_args()

    t0 = time.time()
    funnel_stats = {"total": 0, "survivors": 0, "mode": "direct"}

    # ── Determine scan mode ──
    if args.tickers:
        # Direct ticker list — skip funnel
        tickers_to_scan = [t.strip().upper() for t in args.tickers.split(",")]
        tv_lookup = {}
        funnel_stats = {"total": len(tickers_to_scan), "survivors": len(tickers_to_scan), "mode": "direct"}
        print(f"👻 Direct scan: {len(tickers_to_scan)} tickers\n")

    elif args.watchlist:
        # Core watchlist — skip funnel
        tickers_to_scan = list(CORE_WATCHLIST)
        if args.sectors:
            tickers_to_scan = list(dict.fromkeys(tickers_to_scan + SECTOR_ETFS))
        tv_lookup = {}
        funnel_stats = {"total": len(tickers_to_scan), "survivors": len(tickers_to_scan), "mode": "watchlist"}
        print(f"👻 Watchlist scan: {len(tickers_to_scan)} tickers\n")

    else:
        # ── WHOLE MARKET — TradingView funnel ──
        print("👻 WHOLE MARKET SCAN — Loading US equity universe...\n")

        # Stage 1: Bulk fetch
        print("  ⚡ Stage 1: TradingView bulk API...")
        raw_stocks = _tv_fetch_all_stocks()
        funnel_stats["total"] = len(raw_stocks)
        print(f"     → {len(raw_stocks)} US stocks loaded\n")

        # Stage 2: Progressive funnel
        print("  🔍 Stage 2: Progressive elimination funnel...")
        survivors = funnel_filter(raw_stocks)
        funnel_stats["survivors"] = len(survivors)
        funnel_stats["mode"] = "market"

        tickers_to_scan = [s["ticker"] for s in survivors]
        tv_lookup = {s["ticker"]: s for s in survivors}

    # ── Stage 3+4: Batch deep scan survivors ──
    print(f"  🧪 Stage 3: Batch deep scanning {len(tickers_to_scan)} tickers (daily + weekly)...")
    results = batch_deep_scan(tickers_to_scan, tv_lookup, batch_size=100)

    elapsed = time.time() - t0
    funnel_stats["elapsed_sec"] = round(elapsed, 1)
    funnel_stats["deep_scanned"] = len(results)
    print(f"\n  ⏱  Total time: {elapsed:.1f}s\n")

    if not results:
        print("❌ No valid results.")
        return

    results.sort(key=lambda x: x["combined_score"], reverse=True)

    if args.json:
        output_json(results, funnel_stats)
    else:
        print_results(results, funnel_stats, quiet=args.quiet)

    if args.csv:
        _save_csv(results, args.csv)

    _save_api_output(results, funnel_stats)


def run_screener(save_history: bool = True) -> dict:
    """
    Importable entry point for the pipeline.
    Runs the full market scan, saves results, returns summary.

    Returns:
        {
            "results": [...],
            "funnel_stats": {...},
            "a_plus": [...],   # daily A+ with weekly A+
            "top_6": [...],    # 5.0 daily + A+ weekly
        }
    """
    t0 = time.time()

    # Stage 1: TradingView bulk fetch
    raw_stocks = _tv_fetch_all_stocks()

    # Stage 2: Funnel
    survivors = funnel_filter(raw_stocks, verbose=False)
    tv_lookup = {s["ticker"]: s for s in survivors}
    tickers = [s["ticker"] for s in survivors]

    # Stage 3: Batch deep scan
    results = batch_deep_scan(tickers, tv_lookup, batch_size=100)
    results.sort(key=lambda x: x["combined_score"], reverse=True)

    elapsed = time.time() - t0

    funnel_stats = {
        "total": len(raw_stocks),
        "survivors": len(survivors),
        "deep_scanned": len(results),
        "elapsed_sec": round(elapsed, 1),
        "mode": "market",
    }

    # Categorize
    a_plus = [r for r in results
              if r["daily"].get("score", 0) >= 4.5
              and r["weekly"].get("score", 0) >= 4.0]

    top_6 = [r for r in results
             if r["daily"].get("score", 0) >= 5.0
             and r["weekly"].get("score", 0) >= 4.5]

    # Save current + historical
    _save_api_output(results, funnel_stats)

    if save_history:
        _save_history(results, funnel_stats)

    return {
        "results": results,
        "funnel_stats": funnel_stats,
        "a_plus": a_plus,
        "top_6": top_6,
    }


def _save_history(results: list[dict], funnel_stats: dict):
    """Save date-stamped results for backtesting history."""
    try:
        history_dir = PROJECT_ROOT / "docs" / "api" / "screener-history"
        history_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Save all graded results (compact format for backtesting)
        rows = []
        for r in results:
            d, w = r["daily"], r["weekly"]
            rows.append({
                "ticker": r["ticker"],
                "daily_grade": d.get("grade"),
                "daily_score": d.get("score"),
                "weekly_grade": w.get("grade"),
                "weekly_score": w.get("score"),
                "combined": r.get("combined_score"),
                "price": d.get("price"),
                "cmf": round(d.get("cmf", 0), 3),
                "hull_bull": d.get("hull_bull"),
                "trend_phase": d.get("trend_phase"),
                "sqz_ratio": round(d.get("sqz_ratio", 0), 3),
                "rvol": round(d.get("rvol", 0), 2),
            })

        output = {
            "date": date_str,
            "scan_time": datetime.now().isoformat(),
            "funnel_stats": funnel_stats,
            "total_graded": len(rows),
            "a_plus_count": len([r for r in rows if r["daily_score"] and r["daily_score"] >= 4.5
                                 and r["weekly_score"] and r["weekly_score"] >= 4.0]),
            "results": rows,
        }

        filepath = history_dir / f"{date_str}.json"
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)
    except Exception:
        pass


def _save_csv(results: list[dict], filepath: str):
    """Save flat CSV."""
    import csv
    rows = []
    for r in results:
        d, w = r["daily"], r["weekly"]
        rows.append({
            "ticker": r["ticker"],
            "name": r.get("name", ""),
            "daily_grade": d.get("grade", ""),
            "daily_score": d.get("score", 0),
            "weekly_grade": w.get("grade", ""),
            "weekly_score": w.get("score", 0),
            "combined_score": r.get("combined_score", 0),
            "both_aligned": r.get("both_aligned", False),
            "hull_bull": d.get("hull_bull"),
            "cmf": d.get("cmf"),
            "sqz_ratio": d.get("sqz_ratio"),
            "trend_age": d.get("trend_age"),
            "trend_phase": d.get("trend_phase"),
            "trama_dist": d.get("trama_dist"),
            "rvol": d.get("rvol"),
            "regime": d.get("regime"),
            "price": d.get("price"),
        })
    if rows:
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"💾 Saved {len(rows)} results to {filepath}")


def _save_api_output(results: list[dict], funnel_stats: dict):
    """Save to docs/api/ghost-alpha-screener.json for pipeline consumption."""
    try:
        api_dir = PROJECT_ROOT / "docs" / "api"
        api_dir.mkdir(parents=True, exist_ok=True)
        both_a = [r for r in results if r["both_aligned"]]
        output = {
            "scan_date": datetime.now().isoformat(),
            "funnel_stats": funnel_stats,
            "a_plus_count": len(both_a),
            "a_plus_setups": [{
                "ticker": r["ticker"],
                "name": r.get("name", r["ticker"]),
                "daily_grade": r["daily"].get("grade"),
                "daily_score": r["daily"].get("score"),
                "weekly_grade": r["weekly"].get("grade"),
                "weekly_score": r["weekly"].get("score"),
                "combined_score": r.get("combined_score"),
                "price": r["daily"].get("price"),
                "regime": r["daily"].get("regime"),
                "cmf": r["daily"].get("cmf"),
                "sqz_ratio": r["daily"].get("sqz_ratio"),
                "rvol": r["daily"].get("rvol"),
                "trend_phase": r["daily"].get("trend_phase"),
            } for r in both_a],
        }
        with open(api_dir / "ghost-alpha-screener.json", "w") as f:
            json.dump(output, f, indent=2)
    except Exception:
        pass


if __name__ == "__main__":
    main()
