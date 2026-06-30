#!/usr/bin/env python3
"""
🌀 VCP (Volatility Contraction Pattern) Screener

Finds stocks coiling before a breakout — Mark Minervini's most famous setup.
The VCP identifies stocks in an established uptrend where volatility is
progressively contracting and volume is drying up, leaving a coiled spring
ready to launch on any fresh demand.

Why VCP is distinct from every other screener in the dossier:
  - TAO Pullback:   finds pullbacks in live EMA uptrends (active trend momentum)
  - RVol Breakout:  catches the *explosion* — the day volume returns with force
  - High52:         stocks pressing toward their annual ceiling
  - THIS:           finds the *silence before the explosion* — the setup before
                    the setup that RVol catches. These names are quiet NOW.

Three-stage funnel (same architecture as high52 / tao / rvol / sma200-reclaim):
    Stage 1 → TradingView bulk API: filter for uptrend + base-building RSI range
               + weekly/monthly performance constraints (not already running)
    Stage 2 → Progressive funnel: liquidity, 52w proximity, proximity to MAs
    Stage 3 → yfinance deep scan: measure actual ATR contraction, volume dry-up,
               and base tightness — the three pillars of true VCP quality

Scoring (0–100):
    ATR contraction   (35 pts) — recent ATR vs baseline: lower ratio = tighter coil
    Volume dry-up     (30 pts) — recent avg vol vs prior avg vol: drying = constructive
    Trend health      (20 pts) — position vs SMA50/SMA200 + RSI zone
    Base tightness    (15 pts) — 10-day close range vs ATR: narrower = more coiled

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)

Usage:
    python -m dossier.vcp_screener                       # whole market
    python -m dossier.vcp_screener --tickers NVDA,AAPL  # specific tickers
    python -m dossier.vcp_screener --watchlist           # core watchlist only
    python -m dossier.vcp_screener --top 20              # limit output
    python -m dossier.vcp_screener --json                # machine output
    python -m dossier.vcp_screener --quiet               # A+/A only

Output: docs/api/vcp-screener.json (served via GitHub Pages)

Reference: Minervini, M. (2013). Trade Like a Stock Market Wizard. McGraw-Hill.
"Volatility contraction is the stock market's version of a pressure cooker." — Sam
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
    "volume",                   # 4  today's volume
    "average_volume_30d_calc",  # 5  30d avg volume
    "market_cap_basic",         # 6  market cap
    "SMA200",                   # 7  SMA 200
    "SMA50",                    # 8  SMA 50
    "EMA20",                    # 9  EMA 20
    "RSI",                      # 10 RSI(14)
    "ADX",                      # 11 ADX(14)
    "ATR",                      # 12 ATR(14)
    "Perf.W",                   # 13 weekly performance %
    "Perf.1M",                  # 14 monthly performance %
    "Perf.3M",                  # 15 3-month performance %
    "High.1Y",                  # 16 52-week high
    "Low.1Y",                   # 17 52-week low
]


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_vcp_candidates() -> list[dict]:
    """
    One POST to TradingView → pre-filtered VCP base candidates.

    Server-side: uptrend (above both SMAs), RSI in base zone (not overbought,
    not crashed), price action subdued (not in the middle of a run), decent
    liquidity floor.
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
            # Uptrend required: above both key MAs
            {"left": "close", "operation": "greater", "right": "SMA200"},
            {"left": "close", "operation": "greater", "right": "SMA50"},
            # RSI: in base-building zone — not overbought, not in freefall
            {"left": "RSI", "operation": "in_range", "right": [40, 68]},
            # Not in a huge recent run — VCP forms during a *pause*, not a rip
            {"left": "Perf.W", "operation": "in_range", "right": [-8, 6]},
            {"left": "Perf.1M", "operation": "in_range", "right": [-20, 25]},
            # Some trend present — pure dead stocks don't form VCPs
            {"left": "ADX", "operation": "greater", "right": 15},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView VCP scan") or {}
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
            "perf_3m": d[15],
            "high_1y": d[16],
            "low_1y": d[17],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """
    Narrow the TV universe to likely VCP base candidates before paying
    the cost of yfinance deep-scan calls.
    """
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ VCP FUNNEL: {total} stocks from TradingView")

    # 2A: Liquidity floor
    survivors = [s for s in stocks if (
        (s["market_cap"] or 0) >= 300_000_000
        and (s["avg_vol_30d"] or 0) >= 250_000
    )]
    if verbose:
        print(f"  ├─ Cap ≥$300M + Vol ≥250K ──────────→ {len(survivors)} ({total - len(survivors)} cut)")

    # 2B: Not too far from the 52-week high — VCP forms near highs, not at the lows
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["high_1y"] is not None and s["high_1y"] > 0 and s["price"] is not None
        and s["price"] >= s["high_1y"] * 0.65
    )]
    if verbose:
        print(f"  ├─ Within 35% of 52w high ──────────→ {len(survivors)} ({prev - len(survivors)} cut)")

    # 2C: Not too extended above SMA50 — VCP requires the stock to be in a controlled pause
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["sma_50"] is not None and s["sma_50"] > 0 and s["price"] is not None
        and s["price"] <= s["sma_50"] * 1.20
    )]
    if verbose:
        print(f"  ├─ Within 20% above SMA50 (pausing) ─→ {len(survivors)} ({prev - len(survivors)} cut)")

    # 2D: RSI confirmation — base-building zone
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["rsi"] is not None and 40 <= s["rsi"] <= 68
    )]
    if verbose:
        print(f"  ├─ RSI 40-68 (base zone) ───────────→ {len(survivors)} ({prev - len(survivors)} cut)")

    if verbose:
        pct = (1 - len(survivors) / total) * 100 if total > 0 else 0
        print(f"  └─ FUNNEL DONE: {len(survivors)} survivors ({pct:.0f}% eliminated)\n")

    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  SCORING HELPERS (public — importable for tests)  ████
# ═══════════════════════════════════════════════════════════════════

def atr_contraction_score(contraction_ratio: float) -> int:
    """
    Score how much the recent ATR has contracted vs the baseline (35 pts max).

    contraction_ratio = recent_10d_atr / baseline_30d_atr
    Lower ratio = more compressed = higher score.
    """
    if contraction_ratio <= 0.50:
        return 35   # Extremely tight — less than half the baseline volatility
    if contraction_ratio <= 0.60:
        return 28
    if contraction_ratio <= 0.70:
        return 20
    if contraction_ratio <= 0.80:
        return 12
    if contraction_ratio <= 0.90:
        return 5
    return 0        # No meaningful contraction


def volume_dryup_score(dryup_ratio: float) -> int:
    """
    Score how much recent volume has dried up vs the prior average (30 pts max).

    dryup_ratio = recent_10d_avg_vol / prior_30d_avg_vol
    Lower ratio = quieter tape = more constructive basing.
    """
    if dryup_ratio <= 0.50:
        return 30   # Volume nearly silent — maximum dry-up
    if dryup_ratio <= 0.60:
        return 24
    if dryup_ratio <= 0.70:
        return 18
    if dryup_ratio <= 0.80:
        return 11
    if dryup_ratio <= 0.90:
        return 5
    return 0        # Volume not meaningfully declining


def trend_health_score(price: float, sma50: float | None, sma200: float | None,
                       rsi: float | None) -> int:
    """
    Trend and RSI health (20 pts max).

    Full score requires: above both SMAs, RSI in 50-65 sweet spot.
    """
    pts = 0
    if sma200 is not None and sma200 > 0 and price > sma200:
        pts += 6    # Above 200d — long-term trend intact
    if sma50 is not None and sma50 > 0 and price > sma50:
        pts += 5    # Above 50d — medium-term trend intact
    if rsi is not None:
        if 50 <= rsi <= 65:
            pts += 9    # Goldilocks RSI for a basing stock
        elif 45 <= rsi < 50 or 65 < rsi <= 70:
            pts += 6
        elif 40 <= rsi < 45:
            pts += 3
    return min(pts, 20)


def base_tightness_score(close_range_pct: float) -> int:
    """
    Score how tight the recent 10-day close range is as % of price (15 pts max).

    close_range_pct = (max_close_10d - min_close_10d) / current_price * 100
    Tighter range = more coiled = higher score.
    """
    if close_range_pct <= 3.0:
        return 15   # Extremely tight — less than 3% swing in 10 days
    if close_range_pct <= 5.0:
        return 12
    if close_range_pct <= 7.0:
        return 8
    if close_range_pct <= 10.0:
        return 4
    return 0        # Too wide — not a true VCP base yet


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
# ████  STAGE 3 — DEEP SCAN (yfinance)  ████
# ═══════════════════════════════════════════════════════════════════

def score_vcp(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep scan a single ticker for a VCP setup.

    Returns a result dict on success, None if data is insufficient
    or no meaningful contraction is detected.
    """
    try:
        df = yf.Ticker(ticker).history(period="1y")
        ok, _ = check_yfinance_history(df, ticker, min_rows=60)
        if not ok:
            return None

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        # ── True Range → ATR (Wilder's method via EWM) ─────────────
        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)
        atr_14 = tr.ewm(alpha=1 / 14, adjust=False).mean()

        # ── Compute rolling ATR windows ──────────────────────────────
        # Baseline: 30-bar rolling average of ATR
        atr_baseline = atr_14.rolling(30).mean()
        # Recent: 10-bar rolling average of ATR (the contracting window)
        atr_recent = atr_14.rolling(10).mean()

        if pd.isna(atr_baseline.iloc[-1]) or pd.isna(atr_recent.iloc[-1]):
            return None

        current_price = float(close.iloc[-1])
        b_atr = float(atr_baseline.iloc[-1])
        r_atr = float(atr_recent.iloc[-1])

        if b_atr <= 0:
            return None

        contraction_ratio = r_atr / b_atr

        # Hard cutoff: require at least 10% ATR contraction (ratio < 0.90)
        if contraction_ratio >= 0.90:
            return None

        # ── Volume dry-up ────────────────────────────────────────────
        recent_vol = float(volume.iloc[-10:].mean())
        prior_vol = float(volume.iloc[-40:-10].mean())

        if prior_vol <= 0:
            return None

        dryup_ratio = recent_vol / prior_vol

        # ── Base tightness (10-day close range) ──────────────────────
        recent_closes = close.iloc[-10:]
        close_range_pct = float(
            (recent_closes.max() - recent_closes.min()) / current_price * 100
        )

        # ── Trend SMAs ───────────────────────────────────────────────
        sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None

        if pd.isna(sma200 or float("nan")):
            sma200 = None
        if pd.isna(sma50 or float("nan")):
            sma50 = None

        # Must be in an uptrend — above at least SMA50
        if sma50 is None or current_price <= sma50:
            return None

        # ── RSI (Wilder's smoothing) ──────────────────────────────────
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, float("nan"))
        rsi_val = float((100 - 100 / (1 + rs)).iloc[-1])

        if pd.isna(rsi_val) or not (38 <= rsi_val <= 72):
            return None

        # ── Scoring ───────────────────────────────────────────────────
        atr_pts = atr_contraction_score(contraction_ratio)
        vol_pts = volume_dryup_score(dryup_ratio)
        trend_pts = trend_health_score(current_price, sma50, sma200, rsi_val)
        tight_pts = base_tightness_score(close_range_pct)

        total_score = atr_pts + vol_pts + trend_pts + tight_pts
        grade = _letter_grade(total_score)

        # Skip D grades — they add noise without value
        if grade == "D":
            return None

        return {
            "ticker": ticker,
            "name": (tv_data or {}).get("name", ticker),
            "price": round(current_price, 2),
            "score": total_score,
            "grade": grade,
            "contraction_ratio": round(contraction_ratio, 3),
            "dryup_ratio": round(dryup_ratio, 3),
            "close_range_pct": round(close_range_pct, 2),
            "rsi": round(rsi_val, 1),
            "atr_recent": round(r_atr, 3),
            "atr_baseline": round(b_atr, 3),
            "sma50": round(sma50, 2) if sma50 is not None else None,
            "sma200": round(sma200, 2) if sma200 is not None else None,
            "above_sma200": sma200 is not None and current_price > sma200,
            "market_cap": (tv_data or {}).get("market_cap"),
            "change_pct": (tv_data or {}).get("change_pct", 0),
            "adx": (tv_data or {}).get("adx"),
            "score_breakdown": {
                "atr_contraction": atr_pts,
                "volume_dryup": vol_pts,
                "trend_health": trend_pts,
                "base_tightness": tight_pts,
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
        ctr = r["contraction_ratio"]
        dry = r["dryup_ratio"]
        rng = r["close_range_pct"]
        above200 = "✓200" if r["above_sma200"] else "    "
        change = r.get("change_pct", 0) or 0
        chg_str = f"+{change:.1f}%" if change >= 0 else f"{change:.1f}%"
        cap_str = _fmt_cap(r["market_cap"])

        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Score:{r['score']:>3}  Ctr:{ctr:.2f}  Dry:{dry:.2f}  "
            f"Rng:{rng:.1f}%  RSI:{r['rsi']:<5.1f}  {above200}  "
            f"{chg_str:>6}  {cap_str}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/vcp-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "vcp-screener.json"
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
    parser = argparse.ArgumentParser(
        description="VCP (Volatility Contraction Pattern) Screener"
    )
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🌀  VCP Screener — {len(tickers)} tickers\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🌀  VCP Screener — core watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🌀  VCP (Volatility Contraction Pattern) Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_vcp_candidates()
        print(f"     → {len(raw)} pre-filtered candidates from TradingView\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_vcp(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} VCPs found so far")
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
    print(f"  🌀  VCP SCREENER RESULTS — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 105}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 105}")
    print(f"  Legend: Ctr = ATR contraction ratio (recent/baseline)  |  Dry = vol dry-up ratio")
    print(f"          Rng = 10-day close range %  |  ✓200 = also above SMA200\n")
    print(f"  The VCP setup: Ctr < 0.70 + Dry < 0.70 + Rng < 5% = coiled spring ready to break\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
