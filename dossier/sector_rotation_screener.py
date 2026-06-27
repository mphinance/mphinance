#!/usr/bin/env python3
"""
🔄 Sector Rotation Screener — Stocks in Sectors Reversing Into Leadership

Catches the early-cycle rotation trade: the window between when a sector
starts outperforming and when the crowd piles into individual names.

Every sector rotation starts with the ETF. By the time the ETF is obvious,
the easy money is gone. This screener finds the individual stocks in sectors
that are JUST NOW showing a reversal-up rotation signal — they were lagging
on the 3-month window but are now leading on the 1-week window. That gap is
the opportunity. Catching two to three of these names per rotation cycle
compounds fast.

Different from every other screener in the dossier:
  - TAO / NR7 / RVol: pick setups from the whole market
  - High52: presses toward price highs (ignores sector context)
  - SMA200 Reclaim: trend rehabilitation (any sector)
  - THIS: sector-aware — filters by which sectors are actually rotating NOW

Funnel architecture (3-stage):
    Stage 1 → fetch_sector_rs(): identify sectors with reversing_up or
               accelerating rotation signals (1-week RS leading 3-month RS)
    Stage 2 → TradingView bulk API: uptrend universe filtered client-side
               to stocks in hot sectors (via sector field)
    Stage 3 → yfinance deep scan: trend, RSI, and volume momentum scoring

Scoring (0–100):
    Sector RS    (30 pts) — composite RS of the stock's sector
    Trend        (25 pts) — price above EMA20 / SMA50 / SMA200 stack
    RSI health   (25 pts) — trending zone 50-70; extended/broken penalised
    Volume       (20 pts) — volume expanding vs 30-day average

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)

Usage:
    python -m dossier.sector_rotation_screener               # whole market
    python -m dossier.sector_rotation_screener --top 20      # limit output
    python -m dossier.sector_rotation_screener --json        # machine output
    python -m dossier.sector_rotation_screener --quiet       # A+/A only
    python -m dossier.sector_rotation_screener --all-sectors # skip signal filter

Output: docs/api/sector-rotation.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"Rotation is the engine of the bull market. Catch it early or chase it forever." — Sam
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

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
TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"

# Map sector ETF → keywords to match the TradingView "sector" field (lowercase)
_SECTOR_MAP: dict[str, list[str]] = {
    "XLK":  ["technology"],
    "XLF":  ["finance", "financial"],
    "XLE":  ["energy"],
    "XLV":  ["health"],
    "XLI":  ["industrial"],
    "XLC":  ["communication"],
    "XLRE": ["real estate"],
    "XLP":  ["consumer non", "consumer staple", "consumer def"],
    "XLU":  ["utilit"],
    "XLB":  ["material"],
    "XLY":  ["consumer cycl", "consumer disc"],
}

_TV_COLUMNS = [
    "name",                     # 0  ticker
    "description",              # 1  company name
    "close",                    # 2  last price
    "volume",                   # 3  session volume
    "average_volume_30d_calc",  # 4  30d avg volume
    "market_cap_basic",         # 5  market cap
    "sector",                   # 6  GICS sector
    "SMA200",                   # 7  SMA 200
    "SMA50",                    # 8  SMA 50
    "EMA20",                    # 9  EMA 20
    "RSI",                      # 10 RSI(14)
    "Perf.W",                   # 11 weekly perf %
    "Perf.1M",                  # 12 monthly perf %
    "Perf.3M",                  # 13 3-month perf %
]

# Rotation signals worth acting on (others = stable / decelerating / unknown)
_SIGNAL_PRIORITY = {"reversing_up": 2, "accelerating": 1}


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — SECTOR RS: IDENTIFY HOT SECTORS  ████
# ═══════════════════════════════════════════════════════════════════

def fetch_hot_sectors(all_sectors: bool = False) -> dict[str, dict]:
    """
    Call fetch_sector_rs() and return a {etf: sector_row} map for sectors
    that are either reversing into leadership or already accelerating.

    all_sectors=True skips the signal filter (useful for --all-sectors flag).
    """
    try:
        from dossier.data_sources.sector_rs import fetch_sector_rs
        rs_data = fetch_sector_rs()
    except Exception as exc:
        print(f"  [WARN] Could not fetch sector RS: {exc}")
        return {}

    ranked = rs_data.get("ranked") or []
    hot: dict[str, dict] = {}
    for row in ranked:
        etf = row.get("ticker", "")
        signal = row.get("rotation", "")
        if all_sectors or signal in _SIGNAL_PRIORITY:
            hot[etf] = row
    return hot


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_candidates() -> list[dict]:
    """
    One POST to TradingView → uptrend universe with sector field.
    Server-side pre-filter: liquid, above SMA200, SMA50 > SMA200.
    Client-side sector filter happens after parsing.
    """
    payload = {
        "filter": [
            {"left": "type",       "operation": "in_range", "right": ["stock"]},
            {"left": "subtype",    "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange",   "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 300_000},
            {"left": "close",      "operation": "greater", "right": 8},
            {"left": "market_cap_basic", "operation": "greater", "right": 500_000_000},
            {"left": "close",      "operation": "greater", "right": "SMA200"},
            {"left": "SMA50",      "operation": "greater", "right": "SMA200"},
        ],
        "options":  {"lang": "en"},
        "symbols":  {"query": {"types": []}, "tickers": []},
        "columns":  _TV_COLUMNS,
        "sort":     {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range":    [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView sector rotation scan") or {}
    rows = data.get("data") or []

    results = []
    for item in rows:
        d = item.get("d", [])
        if len(d) < len(_TV_COLUMNS):
            continue
        ticker, price = d[0], d[2]
        if not ticker or price is None:
            continue
        results.append({
            "ticker":      ticker,
            "name":        d[1] or ticker,
            "price":       price,
            "volume":      d[3] or 0,
            "avg_vol_30d": d[4] or 0,
            "market_cap":  d[5] or 0,
            "tv_sector":   d[6] or "",
            "sma_200":     d[7],
            "sma_50":      d[8],
            "ema_20":      d[9],
            "rsi":         d[10],
            "perf_1w":     d[11],
            "perf_1m":     d[12],
            "perf_3m":     d[13],
        })
    return results


def _match_sector(tv_sector: str, hot_sectors: dict[str, dict]) -> tuple[str | None, dict | None]:
    """Return (etf, sector_row) if tv_sector matches a hot sector, else (None, None)."""
    sec_lower = (tv_sector or "").lower()
    for etf, row in hot_sectors.items():
        keywords = _SECTOR_MAP.get(etf, [])
        if any(kw in sec_lower for kw in keywords):
            return etf, row
    return None, None


def _filter_to_hot_sectors(
    stocks: list[dict], hot_sectors: dict[str, dict], verbose: bool = True
) -> list[dict]:
    """Keep only stocks whose TV sector matches a hot/rotating sector."""
    total = len(stocks)
    if verbose:
        sector_names = [row.get("name", etf) for etf, row in hot_sectors.items()]
        print(f"\n  ┌─ ROTATION FUNNEL: {total} uptrend stocks")
        print(f"  │  Hot sectors: {', '.join(sector_names) or 'none (use --all-sectors)'}")

    filtered = []
    for s in stocks:
        etf, row = _match_sector(s.get("tv_sector", ""), hot_sectors)
        if etf:
            s["sector_etf"]    = etf
            s["sector_name"]   = row.get("name", etf)
            s["sector_rs"]     = row.get("composite_rs", 0.0)
            s["sector_signal"] = row.get("rotation", "unknown")
            filtered.append(s)

    if verbose:
        print(f"  └─ {len(filtered)} candidates in rotating sectors → Stage 3\n")
    return filtered


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — SCORING FUNCTIONS  ████
# ═══════════════════════════════════════════════════════════════════

def _sector_rs_score(composite_rs: float, signal: str) -> int:
    """
    30-pt scale: composite sector RS + rotation signal bonus.

    composite_rs is percentage-point excess return vs SPY over a
    weighted 1w/1m/3m window. Reversal bonus favours sectors that
    JUST started outperforming (higher edge) vs sectors already extended.
    """
    if composite_rs >= 4.0:
        base = 25
    elif composite_rs >= 2.0:
        base = 18
    elif composite_rs >= 0.5:
        base = 10
    else:
        base = 4
    bonus = {"reversing_up": 5, "accelerating": 3}.get(signal, 0)
    return min(base + bonus, 30)


def _trend_score(price: float, ema20, sma50, sma200) -> int:
    """25-pt scale: cleaner EMA/SMA stack = higher score."""
    score = 0
    if ema20 and price > ema20:
        score += 8
    if sma50 and price > sma50:
        score += 8
    if sma200 and price > sma200:
        score += 6
    if ema20 and sma50 and ema20 > sma50:
        score += 3
    return min(score, 25)


def _rsi_health_score(rsi) -> int:
    """25-pt scale: strong trending zone 50-70 is ideal."""
    if rsi is None:
        return 8
    rsi = float(rsi)
    if 50 <= rsi <= 65:
        return 25
    if 45 <= rsi < 50 or 65 < rsi <= 70:
        return 18
    if 40 <= rsi < 45 or 70 < rsi <= 75:
        return 10
    return 0


def _volume_momentum_score(hist) -> int:
    """20-pt scale: volume expanding vs 30-day average confirms rotation buying."""
    try:
        vol = hist["Volume"]
        if len(vol) < 25:
            return 5
        recent_avg = float(vol.iloc[-5:].mean())
        prior_avg  = float(vol.iloc[-20:-5].mean())
        if prior_avg <= 0:
            return 5
        ratio = recent_avg / prior_avg
        if ratio >= 1.4:
            return 20
        if ratio >= 1.2:
            return 15
        if ratio >= 1.0:
            return 10
        if ratio >= 0.8:
            return 5
        return 2
    except Exception:
        return 5


def score_rotation(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Deep-scan a single ticker for sector rotation score.
    Returns None on insufficient data or missing sector context.
    tv_data: pre-fetched TradingView dict including sector RS fields.
    """
    td = tv_data or {}
    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="3mo", interval="1d")
    except Exception:
        return None

    ok, _ = check_yfinance_history(hist, ticker, min_rows=20)
    if not ok:
        return None

    price = float(hist["Close"].iloc[-1])
    if price <= 0:
        return None

    ema20  = td.get("ema_20")  or float(hist["Close"].ewm(span=20, adjust=False).mean().iloc[-1])
    sma50  = td.get("sma_50")  or float(hist["Close"].ewm(span=50, adjust=False).mean().iloc[-1])
    sma200 = td.get("sma_200")

    rsi_val = td.get("rsi")

    composite_rs = float(td.get("sector_rs") or 0.0)
    signal       = td.get("sector_signal", "unknown")

    s_sector = _sector_rs_score(composite_rs, signal)
    s_trend  = _trend_score(price, ema20, sma50, sma200)
    s_rsi    = _rsi_health_score(rsi_val)
    s_vol    = _volume_momentum_score(hist)
    total    = s_sector + s_trend + s_rsi + s_vol

    grade = "A+" if total >= 80 else "A" if total >= 65 else "B" if total >= 50 else "C" if total >= 35 else "D"

    return {
        "ticker":        ticker,
        "name":          td.get("name") or ticker,
        "price":         round(price, 2),
        "sector":        td.get("sector_name", ""),
        "sector_etf":    td.get("sector_etf", ""),
        "sector_rs":     composite_rs,
        "sector_signal": signal,
        "rsi":           round(float(rsi_val), 1) if rsi_val is not None else None,
        "perf_3m":       td.get("perf_3m"),
        "market_cap":    td.get("market_cap"),
        "score":         total,
        "grade":         grade,
        "score_breakdown": {
            "sector_rs": s_sector,
            "trend":     s_trend,
            "rsi":       s_rsi,
            "volume":    s_vol,
        },
    }


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT & FORMATTING  ████
# ═══════════════════════════════════════════════════════════════════

_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_RESET  = "\033[0m"
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
    current_sector = None
    for r in results:
        grade = r["grade"]
        if quiet and grade not in ("A+", "A"):
            continue
        if r.get("sector") != current_sector:
            current_sector = r.get("sector")
            print(f"\n  ── {current_sector} ({r.get('sector_etf', '')}) ──")
        sig = r.get("sector_signal", "")
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"RSI:{r['rsi'] or 'N/A':<5}  SectorRS:{r['sector_rs']:+.1f}  "
            f"Score:{r['score']:>3}  {_fmt_cap(r['market_cap'])}  [{sig}]"
        )


def _save_api_output(results: list[dict], hot_sectors: dict[str, dict]) -> None:
    """Write machine-readable JSON to docs/api/sector-rotation.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sector-rotation.json"

    grade_counts: dict[str, int] = {}
    for r in results:
        grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "hot_sectors": [
            {
                "etf":    etf,
                "name":   row.get("name", etf),
                "signal": row.get("rotation", "unknown"),
                "rs":     row.get("composite_rs", 0),
            }
            for etf, row in hot_sectors.items()
        ],
        "count":        len(results),
        "grade_counts": grade_counts,
        "results":      results,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\n  💾  Saved {len(results)} results → {out_path}")


# ═══════════════════════════════════════════════════════════════════
# ████  MAIN  ████
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Sector Rotation Screener")
    parser.add_argument("--top",         type=int, default=0,  help="Limit to top N results")
    parser.add_argument("--json",        action="store_true",   help="Machine-readable JSON output")
    parser.add_argument("--quiet",       action="store_true",   help="Print A+/A only")
    parser.add_argument("--no-save",     action="store_true",   help="Don't write JSON to docs/")
    parser.add_argument("--all-sectors", action="store_true",
                        help="Include all sectors (skip rotation signal filter)")
    args = parser.parse_args()

    print("\n🔄  Sector Rotation Screener — stocks in rotating sectors\n")

    print("  ⚡ Stage 1: Sector RS — identifying rotating sectors...")
    hot_sectors = fetch_hot_sectors(all_sectors=args.all_sectors)
    if not hot_sectors:
        print("  No rotating sectors detected today. Try --all-sectors to see all.")
        if not args.all_sectors:
            return
    else:
        for etf, row in hot_sectors.items():
            print(f"     {etf:<5} {row.get('name', etf):<22}  "
                  f"RS:{row.get('composite_rs', 0):+.1f}  [{row.get('rotation', '')}]")

    print("\n  ⚡ Stage 2: TradingView bulk scan → filter to hot sectors...")
    raw = _tv_fetch_candidates()
    print(f"     → {len(raw)} uptrend stocks pre-filtered")
    candidates = _filter_to_hot_sectors(raw, hot_sectors)

    if not candidates:
        print("  No candidates found in rotating sectors. Try --all-sectors.")
        return

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_rotation(ticker, tv_data=c)
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} setups found")
        time.sleep(0.05)

    results.sort(key=lambda r: (r.get("sector", ""), -r["score"]))

    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    grade_counts: dict[str, int] = {}
    for r in results:
        grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1

    print(f"\n{'═' * 100}")
    print(f"  🔄   SECTOR ROTATION SCREENER — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: SectorRS = composite sector RS vs SPY · [reversing_up] = best early signal\n")

    if not args.no_save:
        _save_api_output(results, hot_sectors)


if __name__ == "__main__":
    main()
