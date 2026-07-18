#!/usr/bin/env python3
"""
📈 MACD Bullish Crossover Screener — Fresh Momentum Ignition

Finds stocks where the MACD line just crossed above its signal line
within the last few sessions — the classic "momentum ignition" signal.
No other screener in the dossier keys off MACD directly: TAO/VCP/NR7
watch EMA stacks and coil patterns, RVol watches volume surges, High52
watches proximity to highs. This one watches the oscillator that swing
traders have used for 40+ years to time entries into a fresh uptrend.

A crossover on its own is noisy — most fire in choppy, going-nowhere
tape. This screener only keeps crosses that happen ON TOP of a trend
filter (price above SMA50) and that are still fresh (within 5 sessions),
so it's the "just turned" signal, not a lagging confirmation days late.

Funnel architecture (3-stage, same as rvol / high52):
    Stage 1 → TradingView bulk API: currently MACD-bullish (macd > signal)
               AND price above SMA50 (trend filter)
    Stage 2 → Progressive funnel: liquidity floor, RSI not blown-off,
               weekly move not already parabolic
    Stage 3 → yfinance deep scan: exact crossover day (via full MACD/signal
               history), histogram strength, trend context, volume confirm

Scoring (0–100):
    Cross freshness       (35 pts) — days since the crossover (0 = today)
    Histogram strength    (25 pts) — MACD − signal spread, normalized to price
    Trend context         (25 pts) — price vs SMA50/SMA200 alignment
    Volume confirmation   (15 pts) — volume on the cross day vs 20-day avg

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)

Usage:
    python -m dossier.macd_cross_screener                       # whole market
    python -m dossier.macd_cross_screener --tickers NVDA,AAPL  # specific tickers
    python -m dossier.macd_cross_screener --watchlist           # core watchlist only
    python -m dossier.macd_cross_screener --top 20             # limit output
    python -m dossier.macd_cross_screener --json               # machine output
    python -m dossier.macd_cross_screener --quiet              # A+/A only

Output: docs/api/macd-cross-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"MACD isn't magic. It's just momentum, translated." — Sam
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
    "RSI",                      # 9  RSI(14)
    "Perf.W",                   # 10 weekly perf %
    "Perf.1M",                  # 11 monthly perf %
    "MACD.macd",                # 12 MACD line
    "MACD.signal",              # 13 MACD signal line
]

# ─── Funnel thresholds ────────────────────────────────────────────
_MAX_DAYS_SINCE_CROSS = 5   # only count crosses within the last N sessions
_MIN_CAP = 300_000_000      # $300M market-cap floor
_MIN_AVG_VOL = 300_000      # 300K avg daily volume floor


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_macd_candidates() -> list[dict]:
    """
    One POST to TradingView → stocks currently MACD-bullish (macd above
    signal) trading above their 50-day SMA. Exact crossover timing is
    refined in Stage 3 since TV only reports the current snapshot.
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
            {"left": "market_cap_basic", "operation": "greater", "right": 300_000_000},
            # Currently bullish: MACD line above its signal line
            {"left": "MACD.macd", "operation": "greater", "right": "MACD.signal"},
            # Trend filter: no falling knives
            {"left": "close", "operation": "greater", "right": "SMA50"},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView MACD scan") or {}
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
            "rsi": d[9],
            "perf_1w": d[10],
            "perf_1m": d[11],
            "macd": d[12],
            "macd_signal": d[13],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """Cut the TV universe to plausible fresh-MACD-cross candidates."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ MACD-CROSS FUNNEL: {total} stocks from TradingView")

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

    # 2. Avg daily volume ≥ 300K (tradeable size)
    survivors = _cut(
        survivors,
        f"Avg vol ≥ {_MIN_AVG_VOL / 1e3:.0f}K",
        lambda s: (s.get("avg_vol_30d") or 0) >= _MIN_AVG_VOL,
    )

    # 3. RSI ≤ 78 — not already blown off before we even confirm the cross
    survivors = _cut(
        survivors,
        "RSI ≤ 78 (not blown off)",
        lambda s: (s.get("rsi") or 0) <= 78,
    )

    # 4. Weekly move ≤ 20% — not already a parabolic spike
    survivors = _cut(
        survivors,
        "Weekly gain ≤ 20% (not parabolic)",
        lambda s: abs(s.get("perf_1w") or 0) <= 20,
    )

    if verbose:
        print(f"  └─ {len(survivors)} candidates pass to Stage 3\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — YFINANCE DEEP SCAN + SCORING  ████
# ═══════════════════════════════════════════════════════════════════

def _compute_macd(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Standard 12/26/9 MACD line + signal line from a close-price series."""
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


def _days_since_bullish_cross(
    macd: pd.Series, signal: pd.Series, max_lookback: int = _MAX_DAYS_SINCE_CROSS
) -> int | None:
    """
    Days since MACD most recently crossed above its signal line, scanning
    backward from the latest bar. Returns None if MACD isn't currently
    above signal, or if the most recent cross is older than max_lookback.
    """
    if len(macd) < 2 or len(signal) < 2:
        return None
    if macd.iloc[-1] <= signal.iloc[-1]:
        return None   # not currently bullish

    n = len(macd)
    for days_ago in range(0, max_lookback + 1):
        i = n - 1 - days_ago
        if i <= 0:
            break
        if macd.iloc[i] > signal.iloc[i] and macd.iloc[i - 1] <= signal.iloc[i - 1]:
            return days_ago
    return None   # bullish, but the cross itself predates the lookback window


def _freshness_score(days_since_cross: int) -> int:
    """35-pt scale: the fresher the cross, the higher the score."""
    return {0: 35, 1: 30, 2: 24, 3: 17, 4: 9, 5: 3}.get(days_since_cross, 0)


def _hist_strength_score(hist_bps: float) -> int:
    """25-pt scale: MACD-signal spread normalized to price, in basis points."""
    if hist_bps >= 50:
        return 25
    if hist_bps >= 25:
        return 20
    if hist_bps >= 10:
        return 14
    if hist_bps >= 3:
        return 7
    return 2   # positive but negligible spread


def _trend_ctx_score(price: float, sma50, sma200) -> int:
    """25-pt scale: reward price/SMA alignment."""
    score = 0
    if sma50 and price > sma50:
        score += 10
    if sma200 and price > sma200:
        score += 10
    if sma50 and sma200 and sma50 > sma200:
        score += 5
    return min(score, 25)


def _volume_confirm_score(vol_ratio: float) -> int:
    """15-pt scale: was the cross backed by above-average volume?"""
    if vol_ratio >= 1.5:
        return 15
    if vol_ratio >= 1.2:
        return 10
    if vol_ratio >= 1.0:
        return 5
    return 0


def score_macd_cross(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep-scan a single ticker for a fresh MACD bullish-crossover score.
    Returns None if there's no qualifying fresh cross or history is too thin.
    tv_data: pre-fetched TradingView dict; used for SMA/RSI/cap lookups.
    """
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="6mo", interval="1d")
    except Exception:
        return None

    ok, _ = check_yfinance_history(hist, ticker, min_rows=60)
    if not ok:
        return None

    macd, signal = _compute_macd(hist["Close"])
    days_since_cross = _days_since_bullish_cross(macd, signal)
    if days_since_cross is None:
        return None

    price = float(hist["Close"].iloc[-1])
    if price <= 0:
        return None

    histogram = float(macd.iloc[-1] - signal.iloc[-1])
    hist_bps = (histogram / price) * 10_000

    sma50 = (tv_data or {}).get("sma_50") or float(
        hist["Close"].rolling(50).mean().iloc[-1]
    )
    _sma200_raw = (tv_data or {}).get("sma_200")
    if _sma200_raw is None and len(hist) >= 200:
        _sma200_raw = float(hist["Close"].rolling(200).mean().iloc[-1])
    sma200 = float(_sma200_raw) if _sma200_raw is not None else None

    # Volume confirmation: cross-day volume vs the trailing 20-day average
    cross_idx = len(hist) - 1 - days_since_cross
    vol = hist["Volume"] if "Volume" in hist.columns else None
    if vol is not None and cross_idx >= 20:
        cross_day_vol = float(vol.iloc[cross_idx])
        prior_avg_vol = float(vol.iloc[cross_idx - 20:cross_idx].mean())
        vol_ratio = cross_day_vol / prior_avg_vol if prior_avg_vol > 0 else 0.0
    else:
        vol_ratio = 0.0

    # ── Scoring ──────────────────────────────────────────────────
    s_fresh = _freshness_score(days_since_cross)
    s_hist = _hist_strength_score(hist_bps)
    s_trend = _trend_ctx_score(price, sma50, sma200)
    s_vol = _volume_confirm_score(vol_ratio)
    total = s_fresh + s_hist + s_trend + s_vol

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
        "days_since_cross": days_since_cross,
        "histogram": round(histogram, 4),
        "histogram_bps": round(hist_bps, 1),
        "vol_ratio": round(vol_ratio, 2),
        "sma50": round(sma50, 2) if sma50 else None,
        "sma200": round(sma200, 2) if sma200 else None,
        "rsi": (tv_data or {}).get("rsi"),
        "market_cap": (tv_data or {}).get("market_cap"),
        "score": total,
        "grade": grade,
        "score_breakdown": {
            "freshness": s_fresh,
            "histogram": s_hist,
            "trend": s_trend,
            "volume": s_vol,
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
        days = r["days_since_cross"]
        days_str = "TODAY" if days == 0 else f"{days}d ago"
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Cross:{days_str:<8}  Hist:{r['histogram_bps']:+.1f}bps  "
            f"Score:{r['score']:>3}  {_fmt_cap(r['market_cap'])}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/macd-cross-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "macd-cross-screener.json"
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
    parser = argparse.ArgumentParser(description="MACD Bullish Crossover Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n📈  MACD Bullish Crossover Screener — {len(tickers)} tickers\n")
        tv_map: dict[str, dict] = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n📈  MACD Bullish Crossover Screener — watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n📈  MACD Bullish Crossover Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_macd_candidates()
        print(f"     → {len(raw)} stocks currently MACD-bullish above SMA50\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_macd_cross(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} fresh crosses found")
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
    print(f"  📈  MACD BULLISH CROSSOVER SCREENER — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: Cross = sessions since MACD crossed above signal (fresher = better)")
    print(f"          Hist = MACD-signal spread in basis points of price\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
