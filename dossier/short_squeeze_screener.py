#!/usr/bin/env python3
"""
🔥 Short Squeeze Screener — Heavily Shorted Names Turning Up

Finds stocks carrying elevated short interest that are also showing the
first technical signs of igniting — a reclaim of EMA20, RSI turning up out
of a base, and volume expanding. Short interest alone is not a signal (a
heavily shorted stock can grind lower for months); the technical ignition
leg is what separates "shorts are right so far" from "shorts are about to
get squeezed."

Different from every other screener in the dossier:
  - RVol / High52 / NR7: pure price-and-volume signals, no positioning data
  - Capitulation: hunts oversold washouts, no short-interest requirement
  - THIS: the only screen that gates on short-interest data (% of float
    short, days-to-cover, month-over-month change) before scoring the setup

Funnel architecture (3-stage, same pattern as nr7 / vcp / sma200_reclaim):
    Stage 1 → TradingView bulk API: liquid small/mid-cap universe (short
               squeezes lose their punch in mega-caps), RSI off the floor
    Stage 2 → Progressive funnel: liquidity, cap ceiling, not already
               parabolic (the squeeze should be starting, not over)
    Stage 3 → yfinance deep scan: hard-gates on shortPercentOfFloat, then
               scores short-interest intensity + technical ignition

Scoring (0–100):
    Short interest      (35 pts) — % of float short; more fuel for a squeeze
    Days to cover        (20 pts) — short ratio; more days = more forced buying
    Short interest trend (15 pts) — MoM change in shares short; rising = shorts
                                     still piling in, not yet covering
    EMA20 reclaim        (12 pts) — price back above the 20-day trend line
    RSI turning up        (10 pts) — momentum building, not yet blown off
    Volume ignition        (8 pts) — today's volume vs the 20-day average

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)

Usage:
    python -m dossier.short_squeeze_screener                       # whole market
    python -m dossier.short_squeeze_screener --tickers GME,AMC     # specific tickers
    python -m dossier.short_squeeze_screener --watchlist           # core watchlist only
    python -m dossier.short_squeeze_screener --top 20              # limit output
    python -m dossier.short_squeeze_screener --json                # machine output
    python -m dossier.short_squeeze_screener --quiet               # A+/A only

Output: docs/api/short-squeeze-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"Shorts don't lose to a better argument. They lose to a bid that won't stop." — Sam
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
    from dossier.utils.validate_api import (
        safe_json,
        check_yfinance_history,
        check_yfinance_info,
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
        if not info:
            print(f"    [WARN] {ticker}: yfinance .info returned empty", file=sys.stderr)
            return {}
        return info

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
    "Perf.1M",                  # 12 monthly perf %
]

# ─── Funnel thresholds ────────────────────────────────────────────
_MIN_CAP = 100_000_000     # $100M floor — below this, short data is unreliable
_MAX_CAP = 15_000_000_000  # $15B ceiling — squeezes lose their punch in mega-caps
_MIN_AVG_VOL = 200_000     # liquidity floor
_MAX_PERF_1M = 40.0        # exclude names that already squeezed (blow-off risk)
_MIN_SHORT_PCT = 10.0      # hard gate: % of float short (percent units, e.g. 10.0 = 10%)


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_squeeze_candidates() -> list[dict]:
    """
    One POST to TradingView → liquid small/mid-cap stocks with RSI off the
    floor (turning up, not still in freefall). Short-interest data isn't
    available from the free TV scanner, so it's fetched per-ticker in
    Stage 3 where it acts as a hard gate.
    """
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": _MIN_AVG_VOL},
            {"left": "close", "operation": "greater", "right": 3},
            {"left": "market_cap_basic", "operation": "greater", "right": _MIN_CAP},
            {"left": "market_cap_basic", "operation": "less", "right": _MAX_CAP},
            # Turning up, not crushed and not already extended
            {"left": "RSI", "operation": "greater", "right": 38},
            {"left": "RSI", "operation": "less", "right": 72},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "RSI", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView Short Squeeze scan") or {}
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
            "perf_1m": d[12],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """Narrow the TV universe before paying for per-ticker short-interest lookups."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ SHORT SQUEEZE FUNNEL: {total} stocks from TradingView")

    def _cut(remaining, label, predicate):
        after = [s for s in remaining if predicate(s)]
        if verbose:
            print(f"  │  {label:<48} {len(remaining):>5} → {len(after)}")
        return after

    survivors = _cut(
        stocks,
        f"Cap ${_MIN_CAP/1e6:.0f}M-${_MAX_CAP/1e9:.0f}B + Vol ≥{_MIN_AVG_VOL/1000:.0f}k",
        lambda s: (
            _MIN_CAP <= (s.get("market_cap") or 0) <= _MAX_CAP
            and (s.get("avg_vol_30d") or 0) >= _MIN_AVG_VOL
        ),
    )

    survivors = _cut(
        survivors,
        f"1-month gain ≤ {_MAX_PERF_1M:.0f}% (not already squeezed)",
        lambda s: (s.get("perf_1m") or 0) <= _MAX_PERF_1M,
    )

    if verbose:
        print(f"  └─ {len(survivors)} candidates pass to Stage 3\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  SCORING HELPERS (public — importable for tests)  ████
# ═══════════════════════════════════════════════════════════════════

def short_interest_score(pct_float: float) -> int:
    """35-pt scale: % of float short — more short interest = more fuel."""
    if pct_float >= 30:
        return 35
    if pct_float >= 20:
        return 30
    if pct_float >= 15:
        return 25
    if pct_float >= _MIN_SHORT_PCT:
        return 18
    return 0


def days_to_cover_score(short_ratio: float) -> int:
    """20-pt scale: short ratio (days to cover) — more days = more forced buying."""
    if short_ratio >= 10:
        return 20
    if short_ratio >= 7:
        return 16
    if short_ratio >= 5:
        return 12
    if short_ratio >= 3:
        return 8
    if short_ratio >= 1:
        return 4
    return 0


def short_interest_trend_score(shares_short: float, shares_short_prior: float) -> int:
    """
    15-pt scale: month-over-month change in shares short.

    Rising short interest into a firming tape means shorts are still adding
    even as price stabilizes — that's more fuel, not less. Falling short
    interest usually means the covering already happened and the move (if
    any) is behind, not ahead.
    """
    if not shares_short_prior or shares_short_prior <= 0:
        return 7
    pct_change = (shares_short - shares_short_prior) / shares_short_prior
    if pct_change >= 0.10:
        return 15
    if pct_change >= 0:
        return 10
    if pct_change >= -0.10:
        return 5
    return 0


def ema_reclaim_score(price: float, ema20: "float | None") -> int:
    """12-pt scale: price back above EMA20 = short-term trend flipping up."""
    if ema20 is None or ema20 <= 0:
        return 0
    if price > ema20:
        return 12
    if price >= ema20 * 0.97:
        return 6
    return 0


def rsi_turn_score(rsi: "float | None") -> int:
    """10-pt scale: RSI building momentum without being blown off already."""
    if rsi is None:
        return 0
    if 50 <= rsi <= 68:
        return 10
    if 40 <= rsi < 50 or 68 < rsi <= 75:
        return 5
    return 0


def volume_ignition_score(rvol: float) -> int:
    """8-pt scale: today's volume vs the 20-day average."""
    if rvol >= 2.5:
        return 8
    if rvol >= 1.5:
        return 5
    if rvol >= 1.0:
        return 2
    return 0


def _letter_grade(score: int) -> str:
    if score >= 80:
        return "A+"
    if score >= 65:
        return "A"
    if score >= 50:
        return "B"
    if score >= 35:
        return "C"
    return "D"


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — YFINANCE DEEP SCAN + SCORING  ████
# ═══════════════════════════════════════════════════════════════════

def score_squeeze(ticker: str, tv_data: "dict | None" = None) -> "dict | None":
    """
    Deep scan a single ticker for a short-squeeze setup.

    Hard-gates on shortPercentOfFloat ≥ _MIN_SHORT_PCT — this is a
    positioning screen first; the technical legs only matter once that
    gate is cleared. Returns None if data is insufficient or the gate fails.
    """
    try:
        stock = yf.Ticker(ticker)

        info = check_yfinance_info(stock.info, ticker)
        if not info:
            return None

        pct_float_raw = info.get("shortPercentOfFloat")
        if pct_float_raw is None:
            return None
        pct_float = float(pct_float_raw) * 100

        if pct_float < _MIN_SHORT_PCT:
            return None

        short_ratio = float(info.get("shortRatio") or 0)
        shares_short = float(info.get("sharesShort") or 0)
        shares_short_prior = float(info.get("sharesShortPriorMonth") or 0)

        df = stock.history(period="6mo")
        ok, _ = check_yfinance_history(df, ticker, min_rows=40)
        if not ok:
            return None

        close = df["Close"]
        volume = df["Volume"]
        current_price = float(close.iloc[-1])

        ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, float("nan"))
        rsi_series = 100 - 100 / (1 + rs)
        rsi_val = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else None

        avg_vol_20d = float(volume.iloc[-21:-1].mean())
        today_vol = float(volume.iloc[-1])
        rvol = today_vol / avg_vol_20d if avg_vol_20d > 0 else 0.0

        si_pts = short_interest_score(pct_float)
        dtc_pts = days_to_cover_score(short_ratio)
        trend_pts = short_interest_trend_score(shares_short, shares_short_prior)
        ema_pts = ema_reclaim_score(current_price, ema20)
        rsi_pts = rsi_turn_score(rsi_val)
        vol_pts = volume_ignition_score(rvol)

        total_score = si_pts + dtc_pts + trend_pts + ema_pts + rsi_pts + vol_pts
        grade = _letter_grade(total_score)

        # Skip D grades — the short-interest gate already narrowed the field;
        # a D here means the technicals aren't confirming yet.
        if grade == "D":
            return None

        return {
            "ticker": ticker,
            "name": (tv_data or {}).get("name", ticker),
            "price": round(current_price, 2),
            "score": total_score,
            "grade": grade,
            "short_pct_float": round(pct_float, 2),
            "short_ratio": round(short_ratio, 2),
            "shares_short": shares_short or None,
            "shares_short_prior_month": shares_short_prior or None,
            "ema_20": round(ema20, 2),
            "rsi": round(rsi_val, 1) if rsi_val is not None else None,
            "rvol": round(rvol, 2),
            "market_cap": (tv_data or {}).get("market_cap"),
            "change_pct": (tv_data or {}).get("change_pct", 0),
            "score_breakdown": {
                "short_interest": si_pts,
                "days_to_cover": dtc_pts,
                "short_interest_trend": trend_pts,
                "ema_reclaim": ema_pts,
                "rsi_turn": rsi_pts,
                "volume_ignition": vol_pts,
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
        change = r.get("change_pct", 0) or 0
        chg_str = f"+{change:.1f}%" if change >= 0 else f"{change:.1f}%"
        cap_str = _fmt_cap(r["market_cap"])
        rsi_str = f"{r['rsi']:.1f}" if r["rsi"] is not None else "—"

        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Score:{r['score']:>3}  SI:{r['short_pct_float']:>5.1f}%  "
            f"DTC:{r['short_ratio']:>4.1f}  RSI:{rsi_str:<5}  RVol:{r['rvol']:<4.1f}  "
            f"{chg_str:>6}  {cap_str}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/short-squeeze-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "short-squeeze-screener.json"
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
    parser = argparse.ArgumentParser(description="Short Squeeze Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. GME,AMC)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🔥  Short Squeeze Screener — {len(tickers)} tickers\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🔥  Short Squeeze Screener — core watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🔥  Short Squeeze Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_squeeze_candidates()
        print(f"     → {len(raw)} pre-filtered candidates from TradingView\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("avg_vol_30d") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates for short interest...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_squeeze(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} squeeze setups found so far")
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

    print(f"\n{'═' * 105}")
    print(f"  🔥  SHORT SQUEEZE SCREENER RESULTS — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 105}\n")

    print_results(results, quiet=args.quiet)

    if not args.no_save and not args.tickers and not args.watchlist:
        _save_api_output(results)


if __name__ == "__main__":
    main()
