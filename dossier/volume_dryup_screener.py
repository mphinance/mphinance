#!/usr/bin/env python3
"""
🤫 Volume Dry-Up (VDU) Screener — The Quiet Before the Move

Every volume screener in this dossier (RVol, capitulation's climax leg)
hunts the day volume EXPLODES. This one hunts the opposite: stocks where
volume has gone unusually QUIET while price holds a tight range near its
highs. That's the classic O'Neil/IBD "volume dry-up" precursor — sellers
have stepped away, the float is locked up, and the next real volume day
tends to be a pocket pivot or breakout, not another leg down.

Different from every other screener in the dossier:
  - RVol: catches the volume explosion AFTER it happens
  - VCP / NR7: catch price-range contraction, blind to volume
  - THIS: catches volume contraction specifically, while price is still
    coiled near strength — the setup RVol will trigger on next

Funnel architecture (same 3-stage pattern as rvol / high52 / tao):
    Stage 1 → TradingView bulk API: volume below 30d average, price above
               SMA50 (no falling knives), decent liquidity floor
    Stage 2 → Progressive funnel: VDU ratio, tight weekly range, RSI band,
               market cap / avg volume floors
    Stage 3 → yfinance deep scan: exact dry-up ratio, price-range
               tightness (5d vs 20d true range), EMA alignment, 52w-high
               proximity

Scoring (0-100):
    Dry-up intensity     (35 pts) — how far below average is volume
    Range tightness      (25 pts) — 5-day range contraction vs 20-day
    Trend structure       (20 pts) — EMA20/SMA50 alignment (still coiled UP)
    52-wk high proximity  (20 pts) — closer to highs = more likely pocket pivot

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.volume_dryup_screener                       # whole market
    python -m dossier.volume_dryup_screener --tickers NVDA,AAPL  # specific tickers
    python -m dossier.volume_dryup_screener --watchlist          # core watchlist only
    python -m dossier.volume_dryup_screener --top 20             # limit output
    python -m dossier.volume_dryup_screener --json               # machine output
    python -m dossier.volume_dryup_screener --quiet              # A+/A only

Output: docs/api/volume-dryup-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"The loudest signal is the one nobody's trading." — Sam
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

# Same columns as rvol / ghost_alpha for consistency
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
    "Stoch.K",                  # 16 Stochastic K
    "High.1M",                  # 17 1-month high (proxy for range)
    "Low.1M",                   # 18 1-month low
    "Perf.3M",                  # 19 3-month perf %
]


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_vdu_candidates() -> list[dict]:
    """
    One POST to TradingView → stocks where today's volume is below the
    30-day average AND price is above SMA50 (coiled inside an uptrend,
    not just abandoned).
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
            # Volume < 30d average — the pre-filter for any dry-up signal
            {"left": "volume", "operation": "less", "right": "average_volume_30d_calc"},
            # Trend intact: price above SMA 50 (coiling inside strength, not decaying)
            {"left": "close", "operation": "greater", "right": "SMA50"},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "average_volume_30d_calc", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView VDU scan") or {}
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
            "stoch_k": d[16],
            "high_1m": d[17],
            "low_1m": d[18],
            "perf_3m": d[19],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL FILTERS  ████
# ═══════════════════════════════════════════════════════════════════

# Maximum VDU ratio to pass to Stage 3 (saves yfinance calls)
_MAX_VDU_RATIO = 0.65  # volume must be at most 65% of the 30d average
_MIN_CAP = 500_000_000   # $500M market cap floor
_MIN_AVG_VOL = 300_000   # 300K avg daily volume floor


def _compute_vdu_ratio(stock: dict) -> float:
    """VDU ratio = today's volume / 30-day average volume. Lower = quieter."""
    avg = stock.get("avg_vol_30d") or 0
    return (stock.get("volume") or 0) / avg if avg > 0 else 1.0


def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """
    Cut the TV universe to likely volume dry-up candidates before paying
    the cost of yfinance API calls.
    """
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ VDU FUNNEL: {total} stocks from TradingView")

    def _cut(remaining, label, predicate):
        after = [s for s in remaining if predicate(s)]
        if verbose:
            print(f"  │  {label:<42} {len(remaining):>5} → {len(after)}")
        return after

    # 1. VDU ratio ≤ 0.65× — meaningfully quiet, not just an average day
    survivors = _cut(
        stocks,
        f"VDU ratio ≤ {_MAX_VDU_RATIO}×",
        lambda s: _compute_vdu_ratio(s) <= _MAX_VDU_RATIO,
    )

    # 2. Not cratering: today's move within a tight +/-4% band (quiet, not panicked)
    survivors = _cut(
        survivors,
        "Change within ±4% (quiet, not panicked)",
        lambda s: abs(s.get("change_pct") or 0) <= 4,
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

    # 5. RSI 40-70 — neither oversold (dead) nor overbought (blown off already)
    survivors = _cut(
        survivors,
        "RSI 40-70",
        lambda s: 40 <= (s.get("rsi") or 0) <= 70,
    )

    if verbose:
        print(f"  └─ {len(survivors)} candidates pass to Stage 3\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — YFINANCE DEEP SCAN + SCORING  ████
# ═══════════════════════════════════════════════════════════════════

def _vdu_score(vdu_ratio: float) -> int:
    """35-pt scale for dry-up intensity. Lower ratio = deeper dry-up = more points."""
    if vdu_ratio <= 0.35:
        return 35
    if vdu_ratio <= 0.45:
        return 28
    if vdu_ratio <= 0.55:
        return 20
    if vdu_ratio <= 0.65:
        return 12
    return 5  # borderline but eligible


def _tightness_score(atr5: float, atr20: float) -> int:
    """25-pt scale for price-range contraction (5-day ATR vs 20-day ATR)."""
    if atr20 <= 0:
        return 0
    ratio = atr5 / atr20
    if ratio <= 0.55:
        return 25   # range has contracted hard — classic coil
    if ratio <= 0.7:
        return 18
    if ratio <= 0.85:
        return 10
    if ratio <= 1.0:
        return 4
    return 0  # range is expanding, not contracting


def _ema_score(price: float, ema20, sma50) -> int:
    """20-pt EMA/SMA alignment score."""
    if ema20 and sma50 and price > ema20 and ema20 > sma50:
        return 20   # Price > EMA20 > SMA50: stacked uptrend
    if ema20 and price > ema20:
        return 12   # Price above EMA20 but SMA50 lags
    if sma50 and price > sma50:
        return 7    # Above SMA50 only
    return 0


def _high52_score(price: float, high_52w: float) -> int:
    """20-pt scale for 52-week-high proximity (closer = more pocket-pivot potential)."""
    if high_52w <= 0:
        return 0
    dist_pct = (high_52w - price) / high_52w * 100
    if dist_pct <= 5:
        return 20
    if dist_pct <= 12:
        return 15
    if dist_pct <= 20:
        return 10
    if dist_pct <= 30:
        return 5
    return 0


def score_vdu(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep-scan a single ticker for volume dry-up score.
    Returns None if the ticker doesn't qualify (too little history, etc.).
    tv_data: the pre-fetched TradingView dict (saves re-computing VDU from yf).
    """
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return None

    ok, _ = check_yfinance_history(hist, ticker, min_rows=30)
    if not ok:
        return None

    price = float(hist["Close"].iloc[-1])
    high_52w = float(hist["High"].max())
    volume_today = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0
    avg_vol = int(hist["Volume"].rolling(30).mean().iloc[-1]) if "Volume" in hist.columns else 0

    if tv_data and tv_data.get("volume") and tv_data.get("avg_vol_30d"):
        vdu_ratio = tv_data["volume"] / tv_data["avg_vol_30d"]
        change_pct = tv_data.get("change_pct") or 0
        ema20_tv = tv_data.get("ema_20")
        sma50_tv = tv_data.get("sma_50")
    else:
        vdu_ratio = volume_today / avg_vol if avg_vol > 0 else 1.0
        change_pct = (
            (float(hist["Close"].iloc[-1]) - float(hist["Close"].iloc[-2]))
            / float(hist["Close"].iloc[-2]) * 100
            if len(hist) >= 2 else 0.0
        )
        ema20_tv = None
        sma50_tv = None

    if vdu_ratio > _MAX_VDU_RATIO:
        return None
    if abs(change_pct) > 4:
        return None

    # True range = High - Low (intraday range proxy for ATR)
    true_range = (hist["High"] - hist["Low"]).abs()
    atr5 = float(true_range.tail(5).mean())
    atr20 = float(true_range.tail(20).mean())

    ema20 = ema20_tv or (
        float(hist["Close"].ewm(span=20, adjust=False).mean().iloc[-1])
    )
    sma50 = sma50_tv or (
        float(hist["Close"].rolling(50).mean().iloc[-1])
    )

    # ── Scoring ──────────────────────────────────────────────────
    s_vdu   = _vdu_score(vdu_ratio)
    s_tight = _tightness_score(atr5, atr20)
    s_ema   = _ema_score(price, ema20, sma50)
    s_high  = _high52_score(price, high_52w)
    total   = s_vdu + s_tight + s_ema + s_high

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
    dist_to_high = round((high_52w - price) / high_52w * 100, 1) if high_52w > 0 else None

    return {
        "ticker": ticker,
        "name": (tv_data or {}).get("name") or ticker,
        "price": round(price, 2),
        "change_pct": round(change_pct, 2),
        "vdu_ratio": round(vdu_ratio, 2),
        "volume": volume_today,
        "avg_vol_30d": avg_vol,
        "atr5": round(atr5, 2),
        "atr20": round(atr20, 2),
        "high_52w": round(high_52w, 2),
        "dist_to_52h_pct": dist_to_high,
        "ema20": round(ema20, 2),
        "sma50": round(sma50, 2),
        "rsi": (tv_data or {}).get("rsi"),
        "adx": (tv_data or {}).get("adx"),
        "market_cap": cap,
        "score": total,
        "grade": grade,
        "score_breakdown": {
            "vdu_intensity": s_vdu,
            "range_tightness": s_tight,
            "ema_align": s_ema,
            "high52_prox": s_high,
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
        chg_str = f"+{chg:.1f}%" if chg >= 0 else f"{chg:.1f}%"
        dist = r.get("dist_to_52h_pct")
        dist_str = f"{dist:.1f}% to 52H" if dist is not None else ""
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"VDU:{r['vdu_ratio']:<5.2f}×  Score:{r['score']:>3}  "
            f"{chg_str:>6}  {dist_str:<18}  {_fmt_cap(r['market_cap'])}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/volume-dryup-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "volume-dryup-screener.json"
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
    parser = argparse.ArgumentParser(description="Volume Dry-Up Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🤫  Volume Dry-Up Screener — {len(tickers)} tickers\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🤫  Volume Dry-Up Screener — watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🤫  Volume Dry-Up Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_vdu_candidates()
        print(f"     → {len(raw)} stocks with volume below 30d avg\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_vdu(ticker, tv_data=tv_map.get(ticker, c))
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} VDU setups found")
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
    print(f"  🤫  VOLUME DRY-UP SCREENER RESULTS — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: VDU = today's volume ÷ 30-day avg (lower = quieter/more coiled)")
    print(f"          Dist = % below 52-week high (lower = near breakout)\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
