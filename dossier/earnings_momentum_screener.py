#!/usr/bin/env python3
"""
📅 Earnings Momentum Screener — Strong Setups Before the Print

Finds stocks with upcoming earnings (within 7 trading days) that also carry
a strong technical setup — the window where premium expansion meets trend
confirmation. The signal: stock is already acting right BEFORE the catalyst.

Different from every other screener in the dossier:
  - TAO / NR7 / RVol: setup quality with no time gate
  - Golden Cross / SMA200 Reclaim: structural trend changes
  - Sector Rotation: inter-sector relative performance
  - THIS: a TIME-LOCKED screen — earnings within 7 days + strong technicals.
           Miss it and the catalyst is gone. That's the edge.

Why pre-earnings technical setups matter:
  A stock already in a clean uptrend, with RSI in the healthy zone, rising
  ADX, and expanding relative volume, going into an earnings report is a
  completely different risk/reward than a beaten-down name. The technical
  strength signals institutional accumulation AHEAD of the print — someone
  knows, or thinks they know, something. Whether you play the momentum into
  print, set up a strangle, or just add to context, this screen hands you
  the shortlist every week.

Funnel architecture (3-stage, same pattern as nr7 / tao / golden_cross):
    Stage 1 → TradingView bulk API: technically healthy stocks (above SMA200,
               RSI 40-70, decent ADX, liquid)
    Stage 2 → Python funnel: cap / volume / trend quality gates
    Stage 3 → yfinance: fetch earnings calendar + price history;
               gate on earnings within MAX_DAYS, then score the setup

Scoring (0–100):
    Earnings proximity  (35 pts) — the time premium component; closer = more
                                    urgent and typically more vol-expanded
    Trend alignment     (25 pts) — price above EMA20 + SMA50; EMA stacking
    RSI health          (20 pts) — 45–65 optimal pre-earnings (not overbought)
    ADX strength        (12 pts) — trending, not coasting
    Volume expansion    ( 8 pts) — relative volume rising pre-print

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)

Usage:
    python -m dossier.earnings_momentum_screener               # whole market
    python -m dossier.earnings_momentum_screener --tickers NVDA,AAPL
    python -m dossier.earnings_momentum_screener --watchlist
    python -m dossier.earnings_momentum_screener --days 5      # earnings ≤5 days
    python -m dossier.earnings_momentum_screener --top 20
    python -m dossier.earnings_momentum_screener --json
    python -m dossier.earnings_momentum_screener --quiet       # A+/A only
    python -m dossier.earnings_momentum_screener --no-save     # skip JSON write

Output: docs/api/earnings-momentum.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"A strong stock going into earnings isn't luck. It's a tell." — Sam
"""

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta
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
        "AMD", "AVGO", "JPM", "GS", "V", "MA", "PLTR", "XOM",
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
    "Perf.W",                   # 12 weekly perf %
    "Perf.1M",                  # 13 monthly perf %
    "Perf.3M",                  # 14 3-month perf %
    "Stoch.RSI.K",              # 15 Stoch RSI K
]

_MIN_CAP = 500_000_000     # $500M market-cap floor
_MIN_AVG_VOL = 300_000     # 300k avg volume floor

MAX_DAYS = 7               # Default earnings-within window


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_candidates() -> list[dict]:
    """
    One POST to TradingView → technically healthy stocks above SMA200,
    RSI in the healthy zone, with meaningful ADX.  Sorted by 3-month
    performance so leading names appear first.  Earnings-calendar gate
    happens in Stage 3 via yfinance.
    """
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": _MIN_AVG_VOL},
            {"left": "close", "operation": "greater", "right": 8},
            {"left": "market_cap_basic", "operation": "greater", "right": _MIN_CAP},
            # Uptrend confirmed
            {"left": "close", "operation": "greater", "right": "SMA200"},
            {"left": "close", "operation": "greater", "right": "SMA50"},
            # RSI healthy — not extended, not broken
            {"left": "RSI", "operation": "greater", "right": 40},
            {"left": "RSI", "operation": "less", "right": 72},
            # Trending — some ADX confirmation
            {"left": "ADX", "operation": "greater", "right": 15},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "Perf.3M", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView earnings-momentum scan") or {}
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
            "perf_1w": d[12],
            "perf_1m": d[13],
            "perf_3m": d[14],
            "stoch_k": d[15],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """Cut the TV universe to technically-sound candidates for calendar check."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ EARNINGS MOMENTUM FUNNEL: {total} stocks from TradingView")

    def _cut(remaining, label, predicate):
        after = [s for s in remaining if predicate(s)]
        if verbose:
            print(f"  │  {label:<52} {len(remaining):>5} → {len(after)}")
        return after

    survivors = _cut(
        stocks,
        f"Market cap ≥ ${_MIN_CAP / 1e6:.0f}M",
        lambda s: (s.get("market_cap") or 0) >= _MIN_CAP,
    )
    survivors = _cut(
        survivors,
        "SMA200 not None (trend data present)",
        lambda s: s.get("sma_200") is not None,
    )
    survivors = _cut(
        survivors,
        f"Avg volume ≥ {_MIN_AVG_VOL // 1000}k",
        lambda s: (s.get("avg_vol_30d") or 0) >= _MIN_AVG_VOL,
    )
    # Exclude blow-offs — stocks already +25% in a month rarely set up cleanly
    survivors = _cut(
        survivors,
        "1-month gain ≤ 25% (not parabolic)",
        lambda s: abs(s.get("perf_1m") or 0) <= 25,
    )

    if verbose:
        print(f"  └─ {len(survivors)} candidates pass to Stage 3 (earnings calendar check)\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — SCORING FUNCTIONS  ████
# ═══════════════════════════════════════════════════════════════════

def _earnings_days_away(ticker: str, max_days: int = MAX_DAYS) -> int | None:
    """
    Return how many calendar days until the next earnings report, or None if
    no earnings are scheduled within max_days (or the calendar is unavailable).

    Uses yfinance .calendar which returns a dict with an 'Earnings Date' key
    containing a list of datetime.date objects.
    """
    try:
        cal = yf.Ticker(ticker).calendar
        if not cal:
            return None
        dates = cal.get("Earnings Date") or []
        today = date.today()
        for ed in dates:
            # calendar entries can be datetime.date or datetime.datetime
            if hasattr(ed, "date"):
                ed = ed.date()
            days_away = (ed - today).days
            if 0 <= days_away <= max_days:
                return days_away
        return None
    except Exception:
        return None


def _proximity_score(days_away: int) -> int:
    """
    35-pt scale: closer earnings = higher urgency / vol premium expansion.

    ≤ 2 days  → 35   (imminent — vol crush imminent, act now or not at all)
      3-4 days → 28   (this week, still time to position)
      5-6 days → 18   (next week, early-mover window)
        7 days → 10   (just within the window)
    """
    if days_away <= 2:
        return 35
    if days_away <= 4:
        return 28
    if days_away <= 6:
        return 18
    return 10


def _trend_score(price: float, ema_20: float | None,
                 sma_50: float | None, sma_200: float | None) -> int:
    """
    25-pt scale: how cleanly the stock is trending into the print.

    Components:
      Price vs EMA20  (12 pts) — above and within 10%  → full marks
      Price vs SMA50  ( 8 pts) — above SMA50 → 8, else 0
      SMA50 vs SMA200 ( 5 pts) — SMA50 above SMA200 → 5 (golden structure)
    """
    pts = 0

    if ema_20 and ema_20 > 0:
        pct = (price - ema_20) / ema_20 * 100
        if 0 <= pct <= 10:
            pts += 12  # above EMA20 but not extended
        elif -3 <= pct < 0:
            pts += 6   # just below — still close
        # above 10% = extended, earns 0

    if sma_50 and price > sma_50:
        pts += 8

    if sma_50 and sma_200 and sma_50 > sma_200:
        pts += 5

    return min(25, pts)


def _rsi_score(rsi: float) -> int:
    """
    20-pt scale: RSI health going into the print.

    45–65 is the goldilocks zone pre-earnings: trending, not overbought.
    Extremes below 35 or above 75 are penalised — overbought prints have
    more room to disappoint; oversold often means something is wrong.
    """
    if 45 <= rsi <= 65:
        return 20
    if 40 <= rsi < 45 or 65 < rsi <= 70:
        return 13
    if 35 <= rsi < 40 or 70 < rsi <= 75:
        return 6
    return 2


def _adx_score(adx: float) -> int:
    """
    12-pt scale: ADX trend strength pre-print.

    A strong trending stock going into earnings has institutional conviction
    behind it — that's what we want.
    """
    if adx >= 35:
        return 12
    if adx >= 25:
        return 9
    if adx >= 20:
        return 6
    if adx >= 15:
        return 3
    return 0


def _volume_score(rel_vol: float) -> int:
    """
    8-pt scale: relative volume expansion heading into the print.

    Pre-earnings accumulation typically shows up as quietly elevated volume.
    """
    if rel_vol >= 2.0:
        return 8
    if rel_vol >= 1.5:
        return 6
    if rel_vol >= 1.2:
        return 4
    return 1


def _grade(score: int) -> str:
    if score >= 80:
        return "A+"
    if score >= 65:
        return "A"
    if score >= 50:
        return "B"
    if score >= 35:
        return "C"
    return "D"


def score_earnings_momentum(
    ticker: str,
    tv_data: dict | None = None,
    max_days: int = MAX_DAYS,
) -> dict | None:
    """
    Full Stage-3 scan for one ticker.

    1. Check earnings calendar — gate on max_days window.
    2. Fetch 60 days of price history for relative-volume computation.
    3. Score the setup and return a result dict, or None if no qualifying print.
    """
    days_away = _earnings_days_away(ticker, max_days=max_days)
    if days_away is None:
        return None

    # Pull recent history for relative-volume calculation
    try:
        hist = yf.Ticker(ticker).history(period="60d")
    except Exception:
        hist = pd.DataFrame()

    ok, reason = check_yfinance_history(hist, ticker, min_rows=20)
    if not ok:
        return None

    tv = tv_data or {}
    price = tv.get("price") or (float(hist["Close"].iloc[-1]) if not hist.empty else 0)
    rsi = float(tv.get("rsi") or 50)
    adx = float(tv.get("adx") or 0)
    ema_20 = tv.get("ema_20")
    sma_50 = tv.get("sma_50")
    sma_200 = tv.get("sma_200")

    # Relative volume: today's volume vs 20-day avg
    vol_series = hist["Volume"]
    avg_vol = float(vol_series.iloc[:-1].tail(20).mean()) if len(vol_series) > 1 else 1
    today_vol = float(vol_series.iloc[-1]) if len(vol_series) >= 1 else 0
    rel_vol = today_vol / avg_vol if avg_vol > 0 else 1.0

    prox  = _proximity_score(days_away)
    trend = _trend_score(price, ema_20, sma_50, sma_200)
    rsi_s = _rsi_score(rsi)
    adx_s = _adx_score(adx)
    vol_s = _volume_score(rel_vol)

    score = prox + trend + rsi_s + adx_s + vol_s

    return {
        "ticker": ticker,
        "name": tv.get("name") or ticker,
        "price": round(price, 2),
        "change_pct": round(tv.get("change_pct") or 0, 2),
        "market_cap": tv.get("market_cap") or 0,
        "days_until_earnings": days_away,
        "rsi": round(rsi, 1),
        "adx": round(adx, 1),
        "rel_vol": round(rel_vol, 2),
        "perf_1w": round(tv.get("perf_1w") or 0, 2),
        "perf_1m": round(tv.get("perf_1m") or 0, 2),
        "score": score,
        "grade": _grade(score),
        "score_breakdown": {
            "proximity": prox,
            "trend": trend,
            "rsi": rsi_s,
            "adx": adx_s,
            "volume": vol_s,
        },
    }


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT  ████
# ═══════════════════════════════════════════════════════════════════

def _save_api_output(results: list[dict], max_days: int = MAX_DAYS) -> None:
    """Write docs/api/earnings-momentum.json for GitHub Pages consumption."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "scan_date": date.today().isoformat(),
        "max_days_to_earnings": max_days,
        "total_results": len(results),
        "results": results,
    }
    out_path = out_dir / "earnings-momentum.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  ✓ Saved → {out_path} ({len(results)} results)")


def _print_table(results: list[dict], quiet: bool = False) -> None:
    shown = [r for r in results if not quiet or r["grade"] in ("A+", "A")]
    if not shown:
        print("  (no results)" if quiet else "  (empty — no qualifying earnings this week)")
        return
    print(f"\n{'TICKER':<7} {'GRADE':<5} {'SCORE':>5} {'DAYS':>5} "
          f"{'RSI':>5} {'ADX':>5} {'RVOL':>5}  NAME")
    print("─" * 72)
    for r in shown:
        print(
            f"{r['ticker']:<7} {r['grade']:<5} {r['score']:>5}  "
            f"{r['days_until_earnings']:>4}d "
            f"{r['rsi']:>5.1f} {r['adx']:>5.1f} {r['rel_vol']:>5.2f}  "
            f"{r['name'][:28]}"
        )


# ═══════════════════════════════════════════════════════════════════
# ████  MAIN ENTRYPOINT  ████
# ═══════════════════════════════════════════════════════════════════

def run_screener(
    tickers: list[str] | None = None,
    watchlist_only: bool = False,
    max_days: int = MAX_DAYS,
    top_n: int | None = None,
) -> list[dict]:
    """
    Full scan pipeline.  Returns list of scored results sorted by score desc.

    tickers       — explicit list of tickers (skips Stage 1 TV scan)
    watchlist_only — use CORE_WATCHLIST as the candidate set
    max_days      — earnings-within window (default 7)
    top_n         — cap output to top N results
    """
    if tickers:
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif watchlist_only:
        candidates = [{"ticker": t, "name": t} for t in sorted(CORE_WATCHLIST)]
        print(f"  Using core watchlist ({len(candidates)} tickers)")
    else:
        print("  [Stage 1] Fetching candidates from TradingView...")
        raw = _tv_fetch_candidates()
        print(f"    → {len(raw)} stocks returned")
        candidates = _funnel_filter(raw)

    print(f"  [Stage 3] Checking earnings calendar for {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        result = score_earnings_momentum(ticker, tv_data=c, max_days=max_days)
        if result:
            results.append(result)
            print(f"    ✓ {ticker}: earnings in {result['days_until_earnings']}d — "
                  f"{result['grade']} ({result['score']})")
        time.sleep(0.1)  # gentle rate limit on yfinance

    results.sort(key=lambda r: (r["score"], -r["days_until_earnings"]), reverse=True)
    if top_n:
        results = results[:top_n]
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Earnings Momentum Screener — upcoming prints + strong setups"
    )
    parser.add_argument("--tickers", help="Comma-separated tickers (skip TV scan)")
    parser.add_argument("--watchlist", action="store_true", help="Use core watchlist")
    parser.add_argument("--days", type=int, default=MAX_DAYS,
                        help="Earnings within N days (default 7)")
    parser.add_argument("--top", type=int, default=None, help="Show top N results")
    parser.add_argument("--quiet", action="store_true", help="Show A+/A only")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument("--no-save", action="store_true", help="Skip JSON file write")
    args = parser.parse_args()

    explicit = [t.strip().upper() for t in args.tickers.split(",")] if args.tickers else None

    print(f"\n📅 EARNINGS MOMENTUM SCREENER  (earnings within {args.days} days)\n")
    results = run_screener(
        tickers=explicit,
        watchlist_only=args.watchlist,
        max_days=args.days,
        top_n=args.top,
    )

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        _print_table(results, quiet=args.quiet)

    if not args.no_save:
        _save_api_output(results, max_days=args.days)

    print(f"\n  {len(results)} qualifying setups found")
    a_plus = [r for r in results if r["grade"] == "A+"]
    a_grade = [r for r in results if r["grade"] == "A"]
    if a_plus:
        print(f"  🌟 A+: {', '.join(r['ticker'] for r in a_plus)}")
    if a_grade:
        print(f"  ⭐ A:  {', '.join(r['ticker'] for r in a_grade)}")


if __name__ == "__main__":
    main()
