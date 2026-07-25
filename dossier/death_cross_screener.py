#!/usr/bin/env python3
"""
💀 Death Cross Alert Screener — Fresh 50/200 MA Breakdowns

Finds stocks where the 50-day SMA has crossed BELOW the 200-day SMA
(Death Cross) within the last 15 trading days — the bearish mirror of
golden_cross_screener.py, catching the trend-change signal while it's
still fresh instead of confirmed-by-CNBC lag.

Different from every other screener in the dossier:
  - Golden Cross: SMA50 crossing ABOVE SMA200 — this is its mirror
  - Bear Screener: EMA 8/21/34/55/89 stacked bearish (continuation, not
    a fresh trend-CHANGE signal)
  - Capitulation: hunts stocks bottoming out and reversing UP
  - THIS: SMA50 crossing below SMA200 (two moving averages), caught
    fresh (≤15 days old) — put / short candidates riding a new downtrend

Funnel architecture (3-stage, same as golden_cross / sma200 / nr7 / rvol):
    Stage 1 → TradingView bulk API: SMA50 < SMA200 (cross confirmed),
               not yet extended (SMA50 ≥ SMA200 * 0.88), RSI 25–65
    Stage 2 → Python funnel: liquidity + proximity floor
    Stage 3 → yfinance deep scan: confirm the 50/200 crossover happened
               within the last 15 trading days; score by recency + trend

Scoring (0–100):
    Cross recency      (40 pts) — fresher = more valuable (≤3 days → 40)
    Trend alignment    (30 pts) — price below EMA20 + SMA50 well below SMA200
    RSI health         (20 pts) — 35–52 ideal (trending down); extremes penalised
    Volume expansion   (10 pts) — volume rising around the crossover date

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)

Usage:
    python -m dossier.death_cross_screener               # whole market
    python -m dossier.death_cross_screener --tickers NVDA,AAPL
    python -m dossier.death_cross_screener --watchlist
    python -m dossier.death_cross_screener --top 20
    python -m dossier.death_cross_screener --json
    python -m dossier.death_cross_screener --quiet       # A+/A only
    python -m dossier.death_cross_screener --no-save     # skip JSON write

Output: docs/api/death-cross.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"A death cross is late by definition too. Fresh is the only edge." — Sam
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
_CROSS_LOOKBACK = 15   # trading days — how far back to search for a crossover

_TV_COLUMNS = [
    "name",                     # 0  ticker
    "description",              # 1  company name
    "close",                    # 2  last price
    "change",                   # 3  % change today
    "volume",                   # 4  session volume
    "average_volume_30d_calc",  # 5  30-day avg volume
    "market_cap_basic",         # 6  market cap
    "SMA200",                   # 7  200-day SMA
    "SMA50",                    # 8  50-day SMA
    "EMA20",                    # 9  20-day EMA
    "RSI",                      # 10 RSI(14)
    "ADX",                      # 11 ADX(14)
    "Perf.W",                   # 12 weekly perf %
    "Perf.1M",                  # 13 monthly perf %
    "High.1Y",                  # 14 52-week high
]


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_death_cross_candidates() -> list[dict]:
    """
    One POST to TradingView → pre-filtered death-cross zone candidates.

    Server-side: SMA50 currently below SMA200 (cross confirmed), not yet
    extended past 12% gap (stale crosses filtered later by yfinance), RSI
    in a range that hasn't already crashed into bounce territory.
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
            # Death cross territory: SMA50 below SMA200
            {"left": "SMA50", "operation": "less", "right": "SMA200"},
            # Not stale — SMA50 within 12% of SMA200 (fresh cross zone)
            {"left": "SMA50", "operation": "greater", "right": "SMA200*0.88"},
            # Not already crashed into bounce territory, not parabolic either
            {"left": "RSI", "operation": "in_range", "right": [25, 65]},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    data = safe_json(resp, "death-cross TV scan")
    if not data or "data" not in data:
        return []

    results = []
    for row in data["data"]:
        d = row.get("d", [])
        if len(d) < len(_TV_COLUMNS):
            continue
        try:
            results.append({
                "ticker":      d[0],
                "name":        d[1] or d[0],
                "price":       d[2],
                "change_pct":  d[3],
                "volume":      d[4],
                "avg_vol_30d": d[5],
                "market_cap":  d[6],
                "sma_200":     d[7],
                "sma_50":      d[8],
                "ema_20":      d[9],
                "rsi":         d[10],
                "adx":         d[11],
                "perf_1w":     d[12],
                "perf_1m":     d[13],
                "high_1y":     d[14],
            })
        except (IndexError, TypeError):
            continue
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PYTHON FUNNEL  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """Tighten the TradingView universe before expensive yfinance calls."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ DC FUNNEL: {total} stocks from TradingView")

    # Liquidity + size floor
    survivors = [s for s in stocks if (
        (s["market_cap"] or 0) >= 300_000_000
        and (s["avg_vol_30d"] or 0) >= 150_000
    )]
    if verbose:
        print(f"  ├─ Cap ≥$300M + Vol ≥150K ─────────→ {len(survivors)} ({total - len(survivors)} cut)")

    # Both SMAs must be populated — cross requires real data
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["sma_200"] and s["sma_200"] > 0
        and s["sma_50"] and s["sma_50"] > 0
    )]
    if verbose:
        print(f"  ├─ SMA50 + SMA200 populated ────────→ {len(survivors)} ({prev - len(survivors)} cut)")

    # SMA50/SMA200 gap ≤ 12% (below) — stale crosses have wider gaps
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["sma_50"] >= s["sma_200"] * 0.88
    )]
    if verbose:
        print(f"  ├─ SMA50/SMA200 gap ≤ 12% ──────────→ {len(survivors)} ({prev - len(survivors)} cut)")

    if verbose:
        pct = (1 - len(survivors) / total) * 100 if total > 0 else 0
        print(f"  └─ FUNNEL DONE: {len(survivors)} survivors ({pct:.0f}% eliminated)\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  SCORING HELPERS (public — importable for tests)  ████
# ═══════════════════════════════════════════════════════════════════

def detect_death_cross(sma50: "pd.Series", sma200: "pd.Series",
                       lookback: int = _CROSS_LOOKBACK) -> "int | None":
    """
    Scan backward through aligned SMA series for a death cross.

    Returns how many bars ago SMA50 crossed from ≥ SMA200 to < SMA200.
    Returns None if no such cross found within `lookback` bars.
    """
    for i in range(1, min(lookback + 1, len(sma50) - 1)):
        s50_now  = sma50.iloc[-i]
        s200_now = sma200.iloc[-i]
        s50_prev  = sma50.iloc[-(i + 1)]
        s200_prev = sma200.iloc[-(i + 1)]

        if any(pd.isna(v) for v in (s50_now, s200_now, s50_prev, s200_prev)):
            continue

        if s50_prev >= s200_prev and s50_now < s200_now:
            return i

    return None


def _recency_score(days: int) -> int:
    """Cross recency — fresher = higher score (40 pts max)."""
    if days <= 3:  return 40
    if days <= 5:  return 34
    if days <= 7:  return 26
    if days <= 10: return 18
    if days <= 15: return 10
    return 4


def _trend_score(price: float, ema20: "float | None",
                 sma50: float, sma200: float) -> int:
    """
    Trend alignment after the death cross (30 pts max).

    Full marks require price below EMA20 and SMA50 comfortably below SMA200.
    """
    pts = 0
    # Price below 20-day EMA (near-term momentum against them)
    if ema20 and price < ema20:
        pts += 15
    # SMA50 relative disadvantage vs SMA200 (gap quality)
    if sma200 > 0:
        gap_pct = (sma200 - sma50) / sma200 * 100
        if gap_pct >= 3:
            pts += 15
        elif gap_pct >= 1.5:
            pts += 10
        elif gap_pct > 0:
            pts += 5
    return min(pts, 30)


def _rsi_score(rsi: float) -> int:
    """RSI health for a post-death-cross setup (20 pts max)."""
    if 35 <= rsi <= 52:  return 20   # trending-down zone — ideal
    if 28 <= rsi < 35 or 52 < rsi <= 60:  return 13
    if 22 <= rsi < 28 or 60 < rsi <= 68:  return 6
    return 2


def _volume_score(rvol_at_cross: float) -> int:
    """Volume at the crossover bar relative to 30-day average (10 pts max)."""
    if rvol_at_cross >= 2.0:  return 10
    if rvol_at_cross >= 1.5:  return 7
    if rvol_at_cross >= 1.2:  return 4
    return 1


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — DEEP SCAN (yfinance)  ████
# ═══════════════════════════════════════════════════════════════════

def score_death_cross(ticker: str, tv_data: "dict | None" = None) -> "dict | None":
    """
    Deep scan a single ticker for a fresh death cross setup.

    Returns a result dict on success, None if data is insufficient or no
    50/200 SMA breakdown is detected within the last 15 trading days.
    """
    try:
        df = yf.Ticker(ticker).history(period="2y")
        ok, _ = check_yfinance_history(df, ticker, min_rows=210)
        if not ok:
            return None

        close  = df["Close"]
        volume = df["Volume"]
        sma50  = close.rolling(50).mean()
        sma200 = close.rolling(200).mean()
        ema20  = close.ewm(span=20, adjust=False).mean()

        if pd.isna(sma200.iloc[-1]) or pd.isna(sma50.iloc[-1]):
            return None

        current_price  = float(close.iloc[-1])
        current_sma50  = float(sma50.iloc[-1])
        current_sma200 = float(sma200.iloc[-1])
        current_ema20  = float(ema20.iloc[-1])

        # Must currently have SMA50 below SMA200 (death cross confirmed)
        if current_sma50 >= current_sma200:
            return None

        # SMA gap > 15% = cross is months old, not fresh
        gap_pct = (current_sma200 - current_sma50) / current_sma200 * 100
        if gap_pct > 15.0:
            return None

        # ── Detect crossover ──────────────────────────────────────
        days_since = detect_death_cross(sma50, sma200, lookback=_CROSS_LOOKBACK)
        if days_since is None:
            return None

        # Volume at the crossover bar
        avg_vol_30 = float(volume.rolling(30).mean().iloc[-1])
        cross_vol  = float(volume.iloc[-days_since])
        rvol = (cross_vol / avg_vol_30) if avg_vol_30 > 0 else 1.0

        # ── RSI (Wilder's) ────────────────────────────────────────
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss.replace(0, float("nan"))
        rsi_val = float((100 - 100 / (1 + rs)).iloc[-1])

        if pd.isna(rsi_val) or not (15 <= rsi_val <= 70):
            return None

        # ── Scoring ───────────────────────────────────────────────
        rec_pts  = _recency_score(days_since)
        trnd_pts = _trend_score(current_price, current_ema20, current_sma50, current_sma200)
        rsi_pts  = _rsi_score(rsi_val)
        vol_pts  = _volume_score(rvol)

        total = rec_pts + trnd_pts + rsi_pts + vol_pts

        if   total >= 80: grade = "A+"
        elif total >= 65: grade = "A"
        elif total >= 50: grade = "B"
        elif total >= 35: grade = "C"
        else:             grade = "D"

        return {
            "ticker":          ticker,
            "name":            (tv_data or {}).get("name", ticker),
            "price":           round(current_price, 2),
            "score":           total,
            "grade":           grade,
            "days_since_cross": days_since,
            "sma50":           round(current_sma50, 2),
            "sma200":          round(current_sma200, 2),
            "gap_pct":         round(gap_pct, 2),
            "rsi":             round(rsi_val, 1),
            "rvol_at_cross":   round(rvol, 2),
            "market_cap":      (tv_data or {}).get("market_cap"),
            "change_pct":      (tv_data or {}).get("change_pct", 0),
            "score_breakdown": {
                "recency":  rec_pts,
                "trend":    trnd_pts,
                "rsi":      rsi_pts,
                "volume":   vol_pts,
            },
        }

    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT & FORMATTING  ████
# ═══════════════════════════════════════════════════════════════════

_GRADE_COLOR = {
    "A+": "\033[95m", "A": "\033[91m", "B": "\033[33m",
    "C": "\033[93m", "D": "\033[90m",
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
        if quiet and r["grade"] not in ("A+", "A"):
            continue
        print(
            f"  {_gc(r['grade']):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Cross:{r['days_since_cross']}d ago  Gap:{r['gap_pct']:.1f}%  "
            f"RSI:{r['rsi']:<5}  Score:{r['score']:>3}  {_fmt_cap(r['market_cap'])}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/death-cross.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "death-cross.json"
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
    parser = argparse.ArgumentParser(description="Death Cross Alert Screener")
    parser.add_argument("--tickers",   help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top",       type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json",      action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet",     action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save",   action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n💀  Death Cross Screener — {len(tickers)} tickers\n")
        tv_map: dict[str, dict] = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n💀  Death Cross Screener — watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n💀  Death Cross Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_death_cross_candidates()
        print(f"     → {len(raw)} stocks in death-cross zone\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 2: Deep scanning {len(candidates)} candidates for fresh breakdowns...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_death_cross(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} death crosses found")
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
    print(f"  💀   DEATH CROSS ALERT — {len(results)} fresh breakdowns (≤{_CROSS_LOOKBACK} days old)")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: Gap = (SMA200 − SMA50) / SMA200 %  |  Cross = days since SMA50 crossed below SMA200\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
