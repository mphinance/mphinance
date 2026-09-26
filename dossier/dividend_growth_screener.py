#!/usr/bin/env python3
"""
💰 Dividend Growth Screener — quality income names, not yield traps

Every screener in the dossier hunts price momentum (breakouts, pullbacks,
reversals). None of them answer the question income-focused readers ask:
"what pays a growing, sustainable dividend right now?" A juicy headline
yield is often a warning sign (price collapsed, payout about to be cut) —
this screener explicitly scores AGAINST that pattern by rewarding a
multi-year track record of raises and a payout ratio that leaves room to
keep raising, not just today's yield number.

Funnel architecture (3-stage, same pattern as tao / high52 / capitulation):
    Stage 1 → TradingView bulk API: profitable, liquid, dividend-paying
               stocks in a 1-9% yield band (below 1% isn't an income name,
               above 9% is usually a trap the market has already priced in)
    Stage 2 → Progressive funnel: market cap floor, price holding above its
               200-day (a dividend payer riding a downtrend is a trap in
               progress), RSI not deeply distressed
    Stage 3 → yfinance deep scan: real dividend history (not just today's
               yield) to compute the consecutive-year raise streak and a
               trailing dividend CAGR, plus payout ratio and trend health

Scoring (0-100):
    Yield quality     (25 pts) — sweet spot 2-5%; too low or too high scores less
    Growth streak      (30 pts) — consecutive years of dividend raises
    Payout safety      (25 pts) — payout ratio in a sustainable 20-60% band
    Trend health       (20 pts) — price above its 200-day, 1yr return not negative

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.dividend_growth_screener                       # whole market
    python -m dossier.dividend_growth_screener --tickers KO,JNJ,ABBV # specific tickers
    python -m dossier.dividend_growth_screener --watchlist           # core watchlist only
    python -m dossier.dividend_growth_screener --top 20              # limit output
    python -m dossier.dividend_growth_screener --json                # machine output
    python -m dossier.dividend_growth_screener --quiet               # A+/A only

Output: docs/api/dividend-growth-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"A rising dividend is management writing you a check and signing its name
to the future. A yield that looks too good is usually the past." — Sam
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
    from dossier.utils.validate_api import (
        check_yfinance_history,
        check_yfinance_info,
        safe_json,
    )
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

    def check_yfinance_info(info, ticker):
        return info or {}

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
    "sector",                   # 7  sector
    "dividend_yield_recent",    # 8  dividend yield (%)
    "SMA200",                   # 9  SMA 200
    "RSI",                      # 10 RSI(14)
    "Perf.Y",                   # 11 1-year performance %
    "Perf.3M",                  # 12 3-month performance %
]

# ─── Funnel thresholds ────────────────────────────────────────────
_MIN_CAP = 1_000_000_000   # $1B — income names should be established
_MIN_RSI = 30              # below this = distressed sell-off, not a stable payer
_MAX_RSI = 78              # above this = blow-off, not a settled income name
_MIN_PERF_Y = -25.0        # more than 25% down over a year = trap risk


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_dividend_candidates() -> list[dict]:
    """
    One POST to TradingView → profitable, liquid stocks paying a 1-9%
    dividend yield. The band excludes both non-payers and the extreme
    headline yields that are usually a distressed price, not real income.
    """
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 150_000},
            {"left": "close", "operation": "greater", "right": 5},
            {"left": "market_cap_basic", "operation": "greater", "right": _MIN_CAP},
            {"left": "earnings_per_share_basic_ttm", "operation": "greater", "right": 0},
            {"left": "dividend_yield_recent", "operation": "in_range", "right": [1, 9]},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "dividend_yield_recent", "sortOrder": "desc"},
        "range": [0, 5000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView Dividend Growth scan") or {}
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
            "sector": d[7],
            "tv_yield_pct": d[8],
            "sma_200": d[9],
            "rsi": d[10],
            "perf_1y": d[11],
            "perf_3m": d[12],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """Cut the TV universe to candidates worth a full dividend-history scan."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ DIVIDEND GROWTH FUNNEL: {total} stocks from TradingView")

    def _cut(remaining, label, predicate):
        after = [s for s in remaining if predicate(s)]
        if verbose:
            print(f"  │  {label:<48} {len(remaining):>5} → {len(after)}")
        return after

    survivors = _cut(
        stocks,
        f"Market cap ≥ ${_MIN_CAP / 1e9:.0f}B",
        lambda s: (s.get("market_cap") or 0) >= _MIN_CAP,
    )

    # Price above its 200-day — a payer riding a downtrend is a trap in progress
    survivors = _cut(
        survivors,
        "Close above SMA200",
        lambda s: s.get("sma_200") is not None and (s.get("price") or 0) > s["sma_200"],
    )

    survivors = _cut(
        survivors,
        f"RSI {_MIN_RSI}-{_MAX_RSI} (not distressed, not blown off)",
        lambda s: _MIN_RSI <= (s.get("rsi") or 0) <= _MAX_RSI,
    )

    survivors = _cut(
        survivors,
        f"1-year return ≥ {_MIN_PERF_Y:.0f}%",
        lambda s: (s.get("perf_1y") if s.get("perf_1y") is not None else 0) >= _MIN_PERF_Y,
    )

    if verbose:
        print(f"  └─ {len(survivors)} candidates pass to Stage 3\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — YFINANCE DEEP SCAN + SCORING  ████
# ═══════════════════════════════════════════════════════════════════

def _resolve_yield_pct(info: dict, price: float, tv_yield_pct) -> float | None:
    """
    Compute yield from dividendRate/price where possible (more reliable than
    yfinance's dividendYield field, which has shipped as either a decimal
    like 0.0091 or an already-scaled percentage like 0.91 across versions —
    see the same fix in watchlist_dive.py).
    """
    rate = info.get("dividendRate")
    if rate and price and price > 0:
        return round(rate / price * 100, 2)
    raw = info.get("dividendYield")
    if raw:
        return round(raw * 100, 2) if raw < 1 else round(raw, 2)
    if tv_yield_pct:
        return round(float(tv_yield_pct), 2)
    return None


def _dividend_growth_streak(dividends: "pd.Series | None", as_of_year: int | None = None) -> tuple[int, float]:
    """
    Consecutive years of higher total dividends paid, and the trailing
    CAGR over up to 5 completed years. The current calendar year is always
    dropped before comparing — it's almost always a partial year of
    payments and would read as a false "cut" against a full prior year.

    Pure function: pass a pandas Series indexed by payment date (as
    yfinance's Ticker.dividends returns) with no network calls.
    """
    if dividends is None or len(dividends) == 0:
        return 0, 0.0

    as_of_year = as_of_year or datetime.utcnow().year
    yearly = dividends.groupby(dividends.index.year).sum()
    yearly = yearly[yearly.index < as_of_year]
    years = sorted(yearly.index)
    if len(years) < 2:
        return 0, 0.0

    streak = 0
    for i in range(len(years) - 1, 0, -1):
        if yearly[years[i]] > yearly[years[i - 1]]:
            streak += 1
        else:
            break

    lookback = min(5, len(years) - 1)
    start_val = float(yearly[years[-1 - lookback]])
    end_val = float(yearly[years[-1]])
    cagr = 0.0
    if lookback >= 1 and start_val > 0:
        cagr = ((end_val / start_val) ** (1 / lookback) - 1) * 100

    return streak, round(cagr, 2)


def _yield_score(yield_pct: float | None) -> int:
    """25-pt scale: 2-5% is the sweet spot; outside that is either too thin
    to matter or a headline yield the market is pricing as a risk."""
    if not yield_pct or yield_pct <= 0:
        return 0
    if 2.0 <= yield_pct <= 5.0:
        return 25
    if 1.5 <= yield_pct < 2.0 or 5.0 < yield_pct <= 6.5:
        return 18
    if 1.0 <= yield_pct < 1.5 or 6.5 < yield_pct <= 8.0:
        return 10
    return 4


def _streak_score(streak: int) -> int:
    """30-pt scale: longer consecutive-raise streaks score higher."""
    if streak >= 10:
        return 30
    if streak >= 7:
        return 25
    if streak >= 5:
        return 20
    if streak >= 3:
        return 14
    if streak >= 1:
        return 7
    return 0


def _payout_score(payout_ratio_pct: float | None) -> int:
    """25-pt scale: 20-60% payout leaves room to keep raising; >100% means
    the company is paying more than it earns."""
    if payout_ratio_pct is None or payout_ratio_pct <= 0:
        return 10   # unreported — partial credit, not treated as a red flag alone
    if payout_ratio_pct > 100:
        return 0
    if 20 <= payout_ratio_pct <= 60:
        return 25
    if 60 < payout_ratio_pct <= 80:
        return 15
    if payout_ratio_pct < 20:
        return 15
    return 5   # 80-100%


def _trend_score(price: float, sma200: float | None, perf_1y: float | None) -> int:
    """20-pt scale: a dividend payer should hold its long-term trend, not
    just its payment history."""
    score = 0
    if sma200 and not (isinstance(sma200, float) and math.isnan(sma200)) and price > sma200:
        score += 12
    if perf_1y is not None:
        if perf_1y >= 0:
            score += 8
        elif perf_1y >= -10:
            score += 4
    return min(score, 20)


def score_dividend_growth(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep-scan a single ticker for dividend growth quality.
    Returns None if the ticker isn't a real dividend payer or history is
    too thin to score (bad data, not a rejection on merit).
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
    if price <= 0:
        return None

    try:
        info = check_yfinance_info(tk.info, ticker)
    except Exception:
        info = {}

    try:
        dividends = tk.dividends
    except Exception:
        dividends = None

    yield_pct = _resolve_yield_pct(info, price, (tv_data or {}).get("tv_yield_pct"))
    if not yield_pct or yield_pct <= 0:
        return None   # not actually paying a dividend per fresh data

    payout_raw = info.get("payoutRatio")
    payout_ratio_pct = round(payout_raw * 100, 1) if payout_raw else None

    streak, cagr = _dividend_growth_streak(dividends)

    sma200 = (tv_data or {}).get("sma_200")
    if sma200 is None and len(hist) >= 200:
        _sma200_series = hist["Close"].rolling(200).mean()
        _last = _sma200_series.iloc[-1]
        sma200 = float(_last) if not math.isnan(_last) else None

    perf_1y = (tv_data or {}).get("perf_1y")
    if perf_1y is None and len(hist) >= 200:
        first = float(hist["Close"].iloc[0])
        perf_1y = (price - first) / first * 100 if first > 0 else None

    s_yield = _yield_score(yield_pct)
    s_streak = _streak_score(streak)
    s_payout = _payout_score(payout_ratio_pct)
    s_trend = _trend_score(price, sma200, perf_1y)
    total = s_yield + s_streak + s_payout + s_trend

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

    return {
        "ticker": ticker,
        "name": (tv_data or {}).get("name") or info.get("shortName") or ticker,
        "sector": (tv_data or {}).get("sector") or info.get("sector"),
        "price": round(price, 2),
        "yield_pct": yield_pct,
        "growth_streak_years": streak,
        "dividend_cagr_5y": cagr,
        "payout_ratio_pct": payout_ratio_pct,
        "perf_1y": round(perf_1y, 2) if perf_1y is not None else None,
        "market_cap": (tv_data or {}).get("market_cap") or info.get("marketCap"),
        "score": total,
        "grade": grade,
        "score_breakdown": {
            "yield": s_yield,
            "growth_streak": s_streak,
            "payout_safety": s_payout,
            "trend": s_trend,
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
        streak = r["growth_streak_years"]
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Yield:{r['yield_pct']:.1f}%  Streak:{streak}yr  Score:{r['score']:>3}  "
            f"{_fmt_cap(r['market_cap'])}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/dividend-growth-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "dividend-growth-screener.json"
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
    parser = argparse.ArgumentParser(description="Dividend Growth Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. KO,JNJ,ABBV)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n💰  Dividend Growth Screener — {len(tickers)} tickers\n")
        tv_map: dict[str, dict] = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n💰  Dividend Growth Screener — watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n💰  Dividend Growth Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_dividend_candidates()
        print(f"     → {len(raw)} profitable dividend payers in the 1-9% yield band\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates for dividend history...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_dividend_growth(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} qualifying payers found")
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
    print(f"  💰   DIVIDEND GROWTH SCREENER — {len(results)} quality payers")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: Streak = consecutive years of dividend raises (completed years only)")
    print(f"          Score rewards sustainable payout + trend, not just headline yield\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
