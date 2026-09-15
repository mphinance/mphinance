#!/usr/bin/env python3
"""
👛 Pocket Pivot Screener — The Trigger Day Volume Dry-Up Sets Up

`volume_dryup_screener.py` finds stocks going QUIET before the move — its own
docstring calls out that "the next real volume day tends to be a pocket pivot
or breakout." This screener is that trigger day: the classic O'Neil/IBD
"pocket pivot" — an up day where volume outguns the heaviest DOWN day of the
prior 10 sessions, while price is still close to its 50-day line (i.e. early
in the move, not already extended into a breakout other screens already
catch).

Different from every other screener in the dossier:
  - RVol: any big-volume day, up or down, no base context
  - High52 / Golden Cross: catch the move AFTER it's already broken out
  - Volume Dry-Up: the quiet coil BEFORE the trigger
  - THIS: the trigger itself — institutional buying showing up as volume
    that swamps recent selling, while the stock is still cheap to the
    50-day (the "buy before the crowd notices" entry O'Neil write about)

Funnel architecture (same 3-stage pattern as rvol / high52 / volume_dryup):
    Stage 1 → TradingView bulk API: today is an up day, above-average
               volume, price already above SMA50 (trend intact)
    Stage 2 → Progressive funnel: not already extended past the base,
               liquidity / market cap floors, RSI band
    Stage 3 → yfinance deep scan: exact pocket-pivot ratio (today's volume
               vs. the worst down-day volume of the prior 10 sessions —
               TradingView has no such field, must be computed from history)

Scoring (0-100):
    Volume dominance   (35 pts) — today's volume ÷ max down-day volume (10d)
    Base proximity      (25 pts) — % above SMA50 (closer = earlier = better)
    Trend structure      (20 pts) — EMA20/SMA50 alignment
    RSI momentum          (20 pts) — trending but not overbought yet

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.pocket_pivot_screener                       # whole market
    python -m dossier.pocket_pivot_screener --tickers NVDA,AAPL  # specific tickers
    python -m dossier.pocket_pivot_screener --watchlist          # core watchlist only
    python -m dossier.pocket_pivot_screener --top 20             # limit output
    python -m dossier.pocket_pivot_screener --json               # machine output
    python -m dossier.pocket_pivot_screener --quiet              # A+/A only

Output: docs/api/pocket-pivot-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"Volume doesn't lie. It shows up before price admits what's happening." — Sam
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

# Same columns as rvol / volume_dryup for consistency
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
]

# Prior-days lookback for the pocket-pivot volume comparison (O'Neil default)
_LOOKBACK_DAYS = 10
# Max distance above the 50-day line before it's a breakout, not a pocket pivot
_MAX_BASE_DIST_PCT = 25
_MIN_CAP = 500_000_000   # $500M market cap floor
_MIN_AVG_VOL = 300_000   # 300K avg daily volume floor


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_pocket_pivot_candidates() -> list[dict]:
    """
    One POST to TradingView → up-day stocks, above-average volume, trading
    above their 50-day line (trend already intact — this isn't a bottom-fish).
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
            {"left": "change", "operation": "greater", "right": 0},
            {"left": "volume", "operation": "greater", "right": "average_volume_30d_calc"},
            {"left": "close", "operation": "greater", "right": "SMA50"},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView pocket pivot scan") or {}
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
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

def _base_dist_pct(stock: dict) -> float:
    """% distance of price above SMA50. Negative means below the line."""
    sma50 = stock.get("sma_50") or 0
    price = stock.get("price") or 0
    if sma50 <= 0:
        return 999.0
    return (price - sma50) / sma50 * 100


def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """
    Cut the TV universe to likely pocket-pivot candidates before paying the
    cost of yfinance API calls (which is where the exact volume comparison
    against the trailing 10-day worst down-day happens).
    """
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ POCKET PIVOT FUNNEL: {total} stocks from TradingView")

    def _cut(remaining, label, predicate):
        after = [s for s in remaining if predicate(s)]
        if verbose:
            print(f"  │  {label:<42} {len(remaining):>5} → {len(after)}")
        return after

    # 1. Up day — pocket pivots only exist on up days by definition
    survivors = _cut(stocks, "Up day (change > 0)", lambda s: (s.get("change_pct") or 0) > 0)

    # 2. Not already extended — still close to the 50-day line, not a breakout chase
    survivors = _cut(
        survivors,
        f"Within {_MAX_BASE_DIST_PCT}% above SMA50 (not extended)",
        lambda s: 0 <= _base_dist_pct(s) <= _MAX_BASE_DIST_PCT,
    )

    # 3. Market cap ≥ $500M (liquid, institutionally accessible)
    survivors = _cut(
        survivors,
        f"Market cap ≥ ${_MIN_CAP / 1e6:.0f}M",
        lambda s: (s.get("market_cap") or 0) >= _MIN_CAP,
    )

    # 4. Avg daily volume ≥ 300K (tradeable size)
    survivors = _cut(
        survivors,
        f"Avg vol ≥ {_MIN_AVG_VOL / 1e3:.0f}K",
        lambda s: (s.get("avg_vol_30d") or 0) >= _MIN_AVG_VOL,
    )

    # 5. RSI 35-75 — trending, loose band (final scoring tightens this)
    survivors = _cut(
        survivors,
        "RSI 35-75",
        lambda s: 35 <= (s.get("rsi") or 0) <= 75,
    )

    if verbose:
        print(f"  └─ {len(survivors)} candidates pass to Stage 3\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — YFINANCE DEEP SCAN + SCORING  ████
# ═══════════════════════════════════════════════════════════════════

def _pocket_pivot_ratio(hist: "pd.DataFrame", lookback: int = _LOOKBACK_DAYS) -> float:
    """
    Today's volume ÷ the largest DOWN-day volume of the prior `lookback`
    sessions (today excluded). This is the core O'Neil pocket-pivot test:
    a ratio >= 1.0 means today's buying outguns the worst recent selling.

    Returns 0.0 if there's no down day in the window to compare against
    (an unbroken run of up days — the signal doesn't apply) or if there's
    not enough history to evaluate the window at all.
    """
    if len(hist) < lookback + 2:
        return 0.0
    closes = hist["Close"]
    vols = hist["Volume"]
    diffs = closes.diff()
    prior_diffs = diffs.iloc[-(lookback + 1):-1]
    prior_vols = vols.iloc[-(lookback + 1):-1]
    down_vols = prior_vols[prior_diffs < 0]
    if down_vols.empty:
        return 0.0
    max_down_vol = float(down_vols.max())
    if max_down_vol <= 0:
        return 0.0
    today_vol = float(vols.iloc[-1])
    return today_vol / max_down_vol


def _volume_dominance_score(ratio: float) -> int:
    """35-pt scale — how decisively today's volume beats the worst recent down day."""
    if ratio >= 2.5:
        return 35
    if ratio >= 1.75:
        return 28
    if ratio >= 1.35:
        return 20
    if ratio >= 1.0:
        return 12
    return 0  # doesn't clear the bar — not a real pocket pivot


def _base_proximity_score(price: float, sma50: float) -> int:
    """25-pt scale — pocket pivots fire EARLY, close to the 50-day line.
    Too far above it and the easy entry is already gone (that's a breakout,
    other screens in this dossier already catch it)."""
    if sma50 is None or sma50 <= 0:
        return 0
    dist_pct = (price - sma50) / sma50 * 100
    if dist_pct < 0:
        return 0  # below the 50-day — trend not confirmed yet
    if dist_pct <= 3:
        return 25
    if dist_pct <= 8:
        return 18
    if dist_pct <= 15:
        return 10
    if dist_pct <= _MAX_BASE_DIST_PCT:
        return 4
    return 0


def _trend_score(price: float, ema20, sma50) -> int:
    """20-pt EMA/SMA alignment score."""
    if ema20 and sma50 and price > ema20 and ema20 > sma50:
        return 20   # Price > EMA20 > SMA50: stacked uptrend
    if ema20 and price > ema20:
        return 12   # Price above EMA20 but SMA50 lags
    if sma50 and price > sma50:
        return 7    # Above SMA50 only
    return 0


def _rsi_momentum_score(rsi) -> int:
    """20-pt scale — trending but with room left before overbought."""
    if rsi is None:
        return 0
    if 45 <= rsi <= 65:
        return 20
    if 40 <= rsi <= 70:
        return 12
    if 35 <= rsi <= 75:
        return 5
    return 0


def score_pocket_pivot(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep-scan a single ticker for a pocket-pivot day. Returns None if the
    ticker doesn't qualify (too little history, ratio < 1.0, etc).
    tv_data: the pre-fetched TradingView dict (saves re-computing from yf).
    """
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="6mo", interval="1d")
    except Exception:
        return None

    ok, _ = check_yfinance_history(hist, ticker, min_rows=_LOOKBACK_DAYS + 2)
    if not ok:
        return None

    ratio = _pocket_pivot_ratio(hist)
    if ratio < 1.0:
        return None

    price = float(hist["Close"].iloc[-1])
    volume_today = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0

    if tv_data:
        change_pct = tv_data.get("change_pct") or 0
        ema20_tv = tv_data.get("ema_20")
        sma50_tv = tv_data.get("sma_50")
        rsi = tv_data.get("rsi")
        adx = tv_data.get("adx")
    else:
        change_pct = (
            (price - float(hist["Close"].iloc[-2])) / float(hist["Close"].iloc[-2]) * 100
            if len(hist) >= 2 else 0.0
        )
        ema20_tv = None
        sma50_tv = None
        rsi = None
        adx = None

    if change_pct <= 0:
        return None

    ema20 = ema20_tv or float(hist["Close"].ewm(span=20, adjust=False).mean().iloc[-1])
    sma50 = sma50_tv or float(hist["Close"].rolling(50).mean().iloc[-1])

    # ── Scoring ──────────────────────────────────────────────────
    s_vol   = _volume_dominance_score(ratio)
    s_base  = _base_proximity_score(price, sma50)
    s_trend = _trend_score(price, ema20, sma50)
    s_rsi   = _rsi_momentum_score(rsi)
    total   = s_vol + s_base + s_trend + s_rsi

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

    cap = tv_data.get("market_cap") if tv_data else None
    dist_pct = round((price - sma50) / sma50 * 100, 1) if sma50 else None

    return {
        "ticker": ticker,
        "name": (tv_data or {}).get("name") or ticker,
        "price": round(price, 2),
        "change_pct": round(change_pct, 2),
        "pocket_pivot_ratio": round(ratio, 2),
        "volume": volume_today,
        "sma50": round(sma50, 2),
        "ema20": round(ema20, 2),
        "dist_above_sma50_pct": dist_pct,
        "rsi": rsi,
        "adx": adx,
        "market_cap": cap,
        "score": total,
        "grade": grade,
        "score_breakdown": {
            "volume_dominance": s_vol,
            "base_proximity": s_base,
            "trend_structure": s_trend,
            "rsi_momentum": s_rsi,
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
        chg = r["change_pct"]
        chg_str = f"+{chg:.1f}%"
        dist = r.get("dist_above_sma50_pct")
        dist_str = f"+{dist:.1f}% off SMA50" if dist is not None else ""
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"PP:{r['pocket_pivot_ratio']:<5.2f}×  Score:{r['score']:>3}  "
            f"{chg_str:>6}  {dist_str:<20}  {_fmt_cap(r['market_cap'])}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/pocket-pivot-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pocket-pivot-screener.json"
    grade_counts = {}
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
    parser = argparse.ArgumentParser(description="Pocket Pivot Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n👛  Pocket Pivot Screener — {len(tickers)} tickers\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n👛  Pocket Pivot Screener — watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n👛  Pocket Pivot Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_pocket_pivot_candidates()
        print(f"     → {len(raw)} up-day stocks above SMA50 on above-average volume\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_pocket_pivot(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} pocket pivots found")
        time.sleep(0.05)

    results.sort(key=lambda r: r["score"], reverse=True)

    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    grade_counts = {}
    for r in results:
        grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1

    print(f"\n{'═' * 100}")
    print(f"  👛  POCKET PIVOT SCREENER RESULTS — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: PP = today's volume ÷ worst down-day volume of the prior {_LOOKBACK_DAYS} days")
    print(f"          (>=1.0× means today's buying outguns the worst recent selling)\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
