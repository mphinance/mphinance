#!/usr/bin/env python3
"""
🌀 NR7 Tight-Coil Screener — Coiling Springs Before Breakout

Finds stocks in uptrends where the most recent session's price range
(High − Low) is the tightest in the last 7 sessions — the NR7 pattern.

When a strong stock goes quiet — narrowing range, volume drying up,
RSI hovering in the 40-60 consolidation zone — energy is building. The
NR7 signal (coined by Toby Crabel, refined by Minervini's VCP concept)
marks the pause before the next directional move. Paired with a clean
uptrend structure it becomes a high-probability setup.

Different from every other screener in the dossier:
  - TAO Pullback: uptrend + pullback to EMA support
  - High52: pressing toward annual highs
  - RVol Breakout: volume explosion day itself
  - SMA200 Reclaim: trend rehabilitation after being below the line
  - THIS: measuring the coil — the tight consolidation BEFORE the move

Funnel architecture (3-stage, same as rvol / tao / high52 / sma200):
    Stage 1 → TradingView bulk API: filter universe in medium-term
               uptrends, RSI not extended, above SMA200
    Stage 2 → Progressive funnel: liquidity, above SMA50, not parabolic
    Stage 3 → yfinance deep scan: detect NR7 + range-contraction ratio,
               volume dry-up confirmation, RSI coil position, trend structure

Scoring (0–100):
    Range contraction  (35 pts) — tighter range vs 30-day average = more coil
    Trend structure    (30 pts) — EMA/SMA alignment quality
    RSI coil position  (20 pts) — 40-60 ideal; overbought/oversold penalised
    Volume dry-up      (15 pts) — volume contracting alongside price = pure coil

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)

Usage:
    python -m dossier.nr7_screener                       # whole market
    python -m dossier.nr7_screener --tickers NVDA,AAPL  # specific tickers
    python -m dossier.nr7_screener --watchlist           # core watchlist only
    python -m dossier.nr7_screener --top 20             # limit output
    python -m dossier.nr7_screener --json               # machine output
    python -m dossier.nr7_screener --quiet              # A+/A only

Output: docs/api/nr7-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"When a strong stock goes quiet, pay attention. The market is loading up." — Sam
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
    "Perf.3M",                  # 16 3-month perf %
    "Perf.6M",                  # 17 6-month perf %
]

# ─── Funnel thresholds ────────────────────────────────────────────
_MIN_CAP = 300_000_000    # $300M market-cap floor
_MAX_PERF_1M = 20.0       # exclude blow-offs (>20% in a month)


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_nr7_candidates() -> list[dict]:
    """
    One POST to TradingView → stocks in medium-term uptrends (above
    SMA200) with RSI in consolidation range and not parabolic.
    Sorted by Perf.3M descending so leading stocks appear first.
    The NR7 narrow-range test happens in Stage 3 via yfinance.
    """
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 200_000},
            {"left": "close", "operation": "greater", "right": 8},
            {"left": "market_cap_basic", "operation": "greater", "right": 300_000_000},
            # Must be above SMA200 — only established uptrends coil well
            {"left": "close", "operation": "greater", "right": "SMA200"},
            # RSI consolidation zone — not extended, not broken
            {"left": "RSI", "operation": "greater", "right": 35},
            {"left": "RSI", "operation": "less", "right": 68},
            # Has medium-term momentum (not just recovering from a crash)
            {"left": "Perf.3M", "operation": "greater", "right": 3},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "Perf.3M", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView NR7 scan") or {}
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
            "perf_6m": d[17],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """Cut the TV universe to coil-candidate stocks."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ NR7 COIL FUNNEL: {total} stocks from TradingView")

    def _cut(remaining, label, predicate):
        after = [s for s in remaining if predicate(s)]
        if verbose:
            print(f"  │  {label:<48} {len(remaining):>5} → {len(after)}")
        return after

    # 1. Market cap ≥ $300M
    survivors = _cut(
        stocks,
        f"Market cap ≥ ${_MIN_CAP / 1e6:.0f}M",
        lambda s: (s.get("market_cap") or 0) >= _MIN_CAP,
    )

    # 2. Price above SMA50 (short-term trend intact)
    survivors = _cut(
        survivors,
        "Close above SMA50 (short-term trend intact)",
        lambda s: s.get("sma_50") is not None and (s.get("price") or 0) > s["sma_50"],
    )

    # 3. Not a vertical blow-off (>20% in one month = too extended to coil)
    survivors = _cut(
        survivors,
        f"1-month gain ≤ {_MAX_PERF_1M:.0f}% (not parabolic)",
        lambda s: abs(s.get("perf_1m") or 0) <= _MAX_PERF_1M,
    )

    # 4. Not a penny stock / micro-cap liquidity floor
    survivors = _cut(
        survivors,
        "Avg volume ≥ 200k (liquid)",
        lambda s: (s.get("avg_vol_30d") or 0) >= 200_000,
    )

    if verbose:
        print(f"  └─ {len(survivors)} candidates pass to Stage 3\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — SCORING FUNCTIONS  ████
# ═══════════════════════════════════════════════════════════════════

def _is_nr7(ranges: list[float]) -> bool:
    """True if the last element is the minimum of all elements (NR7 or NR-N condition)."""
    if len(ranges) < 2:
        return False
    return ranges[-1] <= min(ranges[:-1])


def _range_contraction_score(range_ratio: float, is_nr7_flag: bool) -> int:
    """
    35-pt scale: how tight is today's range vs the 30-day average range.

    range_ratio = today_range / avg_30d_range.
    Lower ratio = more coil. NR7 confirmed → gets a 5-pt bonus.
    """
    if range_ratio <= 0:
        return 0
    if range_ratio <= 0.30:
        base = 30
    elif range_ratio <= 0.45:
        base = 24
    elif range_ratio <= 0.60:
        base = 16
    elif range_ratio <= 0.75:
        base = 8
    elif range_ratio <= 0.90:
        base = 3
    else:
        base = 0
    bonus = 5 if is_nr7_flag else 0
    return min(base + bonus, 35)


def _trend_score(price: float, ema20, ema50, sma200) -> int:
    """30-pt scale: reward cleaner EMA/SMA stacks."""
    score = 0
    if ema20 and price > ema20:
        score += 10
    if ema50 and price > ema50:
        score += 10
    if sma200 and isinstance(sma200, float) and not math.isnan(sma200) and price > sma200:
        score += 6
    if ema20 and ema50 and ema20 > ema50:
        score += 4
    return min(score, 30)


def _rsi_coil_score(rsi: float) -> int:
    """
    20-pt scale: RSI in the 40-60 coiling zone is ideal.

    Stocks with RSI overbought (>70) or weak (<40) get penalised —
    we want constructive consolidation, not exhaustion or damage.
    """
    if rsi is None or math.isnan(rsi):
        return 6  # unknown → partial credit
    if 45 <= rsi <= 58:
        return 20   # sweet spot: mid-range coil
    if 40 <= rsi < 45 or 58 < rsi <= 65:
        return 14
    if 35 <= rsi < 40 or 65 < rsi <= 70:
        return 6
    return 0   # overbought or below 35 = poor coil quality


def _volume_dryup_score(hist: pd.DataFrame) -> int:
    """
    15-pt scale: volume contracting alongside price = institutional
    holders are sitting tight. Recent 5-bar volume vs prior 25-bar avg.
    """
    try:
        vol = hist["Volume"]
        if len(vol) < 25:
            return 0
        recent_avg = float(vol.iloc[-5:].mean())
        prior_avg = float(vol.iloc[-25:-5].mean())
        if prior_avg <= 0:
            return 0
        ratio = recent_avg / prior_avg
        # Lower ratio = more volume dry-up = better coil
        if ratio <= 0.55:
            return 15
        if ratio <= 0.70:
            return 10
        if ratio <= 0.85:
            return 6
        if ratio <= 1.00:
            return 3
        return 0   # volume expanding = not a coil; may already be in motion
    except Exception:
        return 0


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — PER-TICKER DEEP SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def score_nr7(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep-scan a single ticker for NR7 tight-coil score.
    Returns None if the ticker doesn't qualify (insufficient history,
    range is not contracting, or trend is broken).
    tv_data: pre-fetched TradingView dict for fast EMA/RSI lookups.
    """
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="3mo", interval="1d")
    except Exception:
        return None

    ok, _ = check_yfinance_history(hist, ticker, min_rows=30)
    if not ok:
        return None

    price = float(hist["Close"].iloc[-1])
    if price <= 0:
        return None

    # ── NR7 calculation ──────────────────────────────────────────
    # Build daily ranges for the last 30 bars (High - Low)
    n_bars = min(len(hist), 30)
    recent = hist.iloc[-n_bars:]
    daily_ranges = (recent["High"] - recent["Low"]).tolist()

    if len(daily_ranges) < 7:
        return None

    today_range = daily_ranges[-1]
    last_7_ranges = daily_ranges[-7:]
    avg_30d_range = sum(daily_ranges) / len(daily_ranges)

    if avg_30d_range <= 0 or today_range <= 0:
        return None

    range_ratio = today_range / avg_30d_range
    nr7_flag = _is_nr7(last_7_ranges)

    # Hard requirement: range must be contracting meaningfully
    # (at least 15% tighter than average) to count as a coil
    if range_ratio > 0.90:
        return None

    # ── EMA/SMA ───────────────────────────────────────────────────
    ema20 = (tv_data or {}).get("ema_20") or float(
        hist["Close"].ewm(span=20, adjust=False).mean().iloc[-1]
    )
    ema50 = (tv_data or {}).get("sma_50") or float(
        hist["Close"].ewm(span=50, adjust=False).mean().iloc[-1]
    )
    _sma200_raw = (tv_data or {}).get("sma_200") or hist["Close"].rolling(200).mean().iloc[-1]
    sma200 = float(_sma200_raw) if _sma200_raw is not None else None

    # ── RSI ───────────────────────────────────────────────────────
    rsi_val = (tv_data or {}).get("rsi")
    if rsi_val is None:
        # Rough RSI from price history
        delta = hist["Close"].diff().iloc[-15:]
        gain = float(delta.clip(lower=0).mean())
        loss = float((-delta.clip(upper=0)).mean())
        rsi_val = 50.0 if loss == 0 else round(100 - 100 / (1 + gain / loss), 1)

    # ── Scoring ───────────────────────────────────────────────────
    s_range = _range_contraction_score(range_ratio, nr7_flag)
    s_trend = _trend_score(price, ema20, ema50, sma200)
    s_rsi   = _rsi_coil_score(rsi_val)
    s_vol   = _volume_dryup_score(hist)
    total   = s_range + s_trend + s_rsi + s_vol

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
    sma200_out = (
        round(sma200, 2)
        if sma200 is not None and not math.isnan(sma200)
        else None
    )

    return {
        "ticker": ticker,
        "name": (tv_data or {}).get("name") or ticker,
        "price": round(price, 2),
        "today_range": round(today_range, 3),
        "avg_30d_range": round(avg_30d_range, 3),
        "range_ratio": round(range_ratio, 3),
        "is_nr7": nr7_flag,
        "ema20": round(ema20, 2) if ema20 else None,
        "ema50": round(ema50, 2) if ema50 else None,
        "sma200": sma200_out,
        "rsi": round(rsi_val, 1) if rsi_val is not None else None,
        "adx": (tv_data or {}).get("adx"),
        "perf_3m": (tv_data or {}).get("perf_3m"),
        "market_cap": cap,
        "score": total,
        "grade": grade,
        "score_breakdown": {
            "range_contraction": s_range,
            "trend": s_trend,
            "rsi_coil": s_rsi,
            "volume_dryup": s_vol,
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
        nr7_tag = " ★NR7" if r.get("is_nr7") else ""
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Ratio:{r['range_ratio']:.2f}  RSI:{r['rsi'] or 'N/A':<5}  "
            f"Score:{r['score']:>3}  {_fmt_cap(r['market_cap'])}{nr7_tag}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/nr7-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "nr7-screener.json"
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
    parser = argparse.ArgumentParser(description="NR7 Tight-Coil Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🌀  NR7 Tight-Coil Screener — {len(tickers)} tickers\n")
        tv_map: dict[str, dict] = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🌀  NR7 Tight-Coil Screener — watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🌀  NR7 Tight-Coil Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_nr7_candidates()
        print(f"     → {len(raw)} stocks in uptrends with RSI in range\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_nr7(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} coiling setups found")
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
    print(f"  🌀   NR7 TIGHT-COIL SCREENER — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: Ratio = today's range / 30-day avg range (lower = tighter coil)")
    print(f"          NR7 ★ = today is the narrowest-range session of the last 7 days\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
