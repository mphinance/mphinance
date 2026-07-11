#!/usr/bin/env python3
"""
🩸 Capitulation Reversal Screener — Washouts Showing Signs of Life

Every other screener in the dossier hunts stocks going UP (uptrend
pullbacks, coils below highs, breakouts). This one hunts the opposite
setup: stocks that just got hammered — near their 52-week low, RSI
oversold, badly negative on the month — but where the tape is telling
you the selling is exhausting: a reversal candle, a volume climax, and
a rate-of-decline that's decelerating rather than accelerating.

Different from every other screener in the dossier:
  - High52 / NR7 / TAO: all require the stock to already be strong
  - Bear: hunts stocks still breaking DOWN
  - THIS: hunts stocks that broke down and are stabilizing — the
    contrarian bounce/reversal candidate, not the trend continuation

Funnel architecture (3-stage, same as nr7 / high52 / rvol):
    Stage 1 → TradingView bulk API: stocks down hard on the month,
               RSI oversold, within 25% of their 52-week low
    Stage 2 → Progressive funnel: liquidity floor, still trading above
               a hard capital-preservation floor, not a total blowup
    Stage 3 → yfinance deep scan: oversold depth, reversal candle
               quality, volume climax, decline deceleration

Scoring (0-100):
    Oversold depth        (30 pts) — RSI extremity + proximity to 52w low
    Reversal candle       (25 pts) — today's close position in its range
    Volume climax         (25 pts) — today's volume vs 20-day average
    Decline deceleration  (20 pts) — 5-day ROC vs the trailing 20-day pace

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.capitulation_screener                      # whole market
    python -m dossier.capitulation_screener --tickers NVDA,AAPL  # specific tickers
    python -m dossier.capitulation_screener --watchlist          # core watchlist only
    python -m dossier.capitulation_screener --top 20             # limit output
    python -m dossier.capitulation_screener --json               # machine output
    python -m dossier.capitulation_screener --quiet              # A+/A only

Output: docs/api/capitulation-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"The bottom isn't a price. It's the moment the selling runs out of sellers." — Sam
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
    "volume",                   # 4  session volume
    "average_volume_30d_calc",  # 5  30d avg volume
    "market_cap_basic",         # 6  market cap
    "RSI",                      # 7  RSI(14)
    "Perf.1M",                  # 8  1-month perf %
    "price_52_week_low",        # 9  52-week low
]

# ─── Funnel thresholds ────────────────────────────────────────────
_MIN_CAP = 300_000_000     # $300M market-cap floor — skip micro-cap wipeouts
_MIN_PRICE = 3.0           # skip sub-$3 names (delisting-risk noise)
_MAX_PCT_FROM_LOW = 25.0   # must be within 25% of the 52-week low
_MIN_PERF_1M = -60.0       # exclude total blowups (frauds, halts, bankruptcies)


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_capitulation_candidates() -> list[dict]:
    """
    One POST to TradingView → stocks down hard on the month with RSI
    oversold, sorted worst-performer-first (deepest washouts surface
    first). The reversal/volume-climax test happens in Stage 3.
    """
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 200_000},
            {"left": "close", "operation": "greater", "right": _MIN_PRICE},
            {"left": "market_cap_basic", "operation": "greater", "right": _MIN_CAP},
            # Beaten down but oversold, not fresh weakness
            {"left": "RSI", "operation": "less", "right": 38},
            {"left": "Perf.1M", "operation": "less", "right": -8},
            {"left": "Perf.1M", "operation": "greater", "right": _MIN_PERF_1M},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "Perf.1M", "sortOrder": "asc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView capitulation scan") or {}
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
            "rsi": d[7],
            "perf_1m": d[8],
            "low_52w": d[9],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """Cut the TV universe to genuine washout candidates."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ CAPITULATION FUNNEL: {total} stocks from TradingView")

    def _cut(remaining, label, predicate):
        after = [s for s in remaining if predicate(s)]
        if verbose:
            print(f"  │  {label:<52} {len(remaining):>5} → {len(after)}")
        return after

    # 1. Market cap floor
    survivors = _cut(
        stocks,
        f"Market cap ≥ ${_MIN_CAP / 1e6:.0f}M",
        lambda s: (s.get("market_cap") or 0) >= _MIN_CAP,
    )

    # 2. Within striking distance of the 52-week low
    survivors = _cut(
        survivors,
        f"Within {_MAX_PCT_FROM_LOW:.0f}% of 52-week low",
        lambda s: s.get("low_52w") and s["low_52w"] > 0
        and ((s.get("price") or 0) - s["low_52w"]) / s["low_52w"] * 100 <= _MAX_PCT_FROM_LOW,
    )

    # 3. Liquidity floor
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

def _oversold_score(rsi, pct_from_low: float) -> int:
    """30-pt scale: how washed out is this name right now."""
    if rsi is None:
        rsi_pts = 10
    elif rsi <= 20:
        rsi_pts = 20
    elif rsi <= 30:
        rsi_pts = 16
    elif rsi <= 35:
        rsi_pts = 10
    elif rsi <= 40:
        rsi_pts = 4
    else:
        rsi_pts = 0

    if pct_from_low <= 5:
        low_pts = 10
    elif pct_from_low <= 10:
        low_pts = 7
    elif pct_from_low <= 15:
        low_pts = 4
    elif pct_from_low <= 25:
        low_pts = 1
    else:
        low_pts = 0

    return min(rsi_pts + low_pts, 30)


def _reversal_candle_score(hist: pd.DataFrame) -> int:
    """
    25-pt scale: today's close position within its own range.

    A close near the top of the day's range after a beatdown is the
    classic "hammer" signature — sellers pushed it down, buyers
    pushed it back up before the close. A green day earns a bonus.
    """
    try:
        last = hist.iloc[-1]
        high, low, close, open_ = last["High"], last["Low"], last["Close"], last["Open"]
        day_range = high - low
        if day_range <= 0:
            return 0
        pos = (close - low) / day_range

        if pos >= 0.8:
            base = 15
        elif pos >= 0.6:
            base = 10
        elif pos >= 0.4:
            base = 5
        else:
            base = 0

        bonus = 10 if close > open_ else 0
        return min(base + bonus, 25)
    except Exception:
        return 0


def _volume_climax_score(hist: pd.DataFrame) -> int:
    """
    25-pt scale: today's volume vs the trailing 20-day average.

    A volume spike on a washout/reversal day is the signature of
    capitulation — the last weak hands selling into strong hands.
    """
    try:
        vol = hist["Volume"]
        if len(vol) < 21:
            return 0
        today_vol = float(vol.iloc[-1])
        avg_vol_20 = float(vol.iloc[-21:-1].mean())
        if avg_vol_20 <= 0:
            return 0
        ratio = today_vol / avg_vol_20

        if ratio >= 3.0:
            return 25
        if ratio >= 2.0:
            return 18
        if ratio >= 1.5:
            return 12
        if ratio >= 1.0:
            return 6
        return 0
    except Exception:
        return 0


def _stabilization_score(hist: pd.DataFrame) -> int:
    """
    20-pt scale: is the decline decelerating?

    Compares the actual 5-day rate-of-change to the rate implied by
    the trailing 20-day trend. A 5-day ROC materially better than the
    20-day pace means the bleeding is slowing — early stabilization.
    """
    try:
        closes = hist["Close"]
        if len(closes) < 21:
            return 0
        c_now, c_5, c_20 = float(closes.iloc[-1]), float(closes.iloc[-6]), float(closes.iloc[-21])
        if c_5 <= 0 or c_20 <= 0:
            return 0
        roc_5 = (c_now - c_5) / c_5 * 100
        roc_20 = (c_now - c_20) / c_20 * 100
        expected_5d_pace = roc_20 * (5 / 20)
        improvement = roc_5 - expected_5d_pace

        if improvement >= 10:
            return 20
        if improvement >= 6:
            return 14
        if improvement >= 3:
            return 8
        if improvement >= 0:
            return 3
        return 0
    except Exception:
        return 0


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — PER-TICKER DEEP SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def score_capitulation(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep-scan a single ticker for a capitulation-reversal score.
    Returns None if the ticker doesn't qualify (insufficient history,
    not actually near its 52-week low, or hasn't declined enough to
    call this a washout).
    """
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="6mo", interval="1d")
    except Exception:
        return None

    ok, _ = check_yfinance_history(hist, ticker, min_rows=25)
    if not ok:
        return None

    price = float(hist["Close"].iloc[-1])
    if price <= 0:
        return None

    low_52w = (tv_data or {}).get("low_52w") or float(hist["Low"].min())
    if not low_52w or low_52w <= 0:
        return None
    pct_from_low = (price - low_52w) / low_52w * 100

    # Hard requirement: must genuinely be near the 52-week low
    if pct_from_low > _MAX_PCT_FROM_LOW:
        return None

    rsi_val = (tv_data or {}).get("rsi")
    if rsi_val is None:
        delta = hist["Close"].diff().iloc[-15:]
        gain = float(delta.clip(lower=0).mean())
        loss = float((-delta.clip(upper=0)).mean())
        rsi_val = 50.0 if loss == 0 else round(100 - 100 / (1 + gain / loss), 1)

    s_oversold = _oversold_score(rsi_val, pct_from_low)
    s_candle = _reversal_candle_score(hist)
    s_volume = _volume_climax_score(hist)
    s_stable = _stabilization_score(hist)
    total = s_oversold + s_candle + s_volume + s_stable

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
        "name": (tv_data or {}).get("name") or ticker,
        "price": round(price, 2),
        "low_52w": round(low_52w, 2),
        "pct_from_low": round(pct_from_low, 2),
        "rsi": round(rsi_val, 1) if rsi_val is not None else None,
        "perf_1m": (tv_data or {}).get("perf_1m"),
        "market_cap": (tv_data or {}).get("market_cap"),
        "score": total,
        "grade": grade,
        "score_breakdown": {
            "oversold_depth": s_oversold,
            "reversal_candle": s_candle,
            "volume_climax": s_volume,
            "decline_deceleration": s_stable,
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
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"FromLow:{r['pct_from_low']:>5.1f}%  RSI:{r['rsi'] or 'N/A':<5}  "
            f"Score:{r['score']:>3}  {_fmt_cap(r['market_cap'])}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/capitulation-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "capitulation-screener.json"
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
    parser = argparse.ArgumentParser(description="Capitulation Reversal Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🩸  Capitulation Reversal Screener — {len(tickers)} tickers\n")
        tv_map: dict[str, dict] = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🩸  Capitulation Reversal Screener — watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🩸  Capitulation Reversal Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_capitulation_candidates()
        print(f"     → {len(raw)} stocks oversold and down hard on the month\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("perf_1m") or 0)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_capitulation(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} reversal setups found")
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
    print(f"  🩸   CAPITULATION REVERSAL SCREENER — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: FromLow = % above the 52-week low (lower = closer to the washout)")
    print(f"          Score rewards oversold depth + a reversal candle + volume climax\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
