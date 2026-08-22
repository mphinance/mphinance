#!/usr/bin/env python3
"""
📈 Analyst Revision Cluster Screener — Multiple Firms, One Direction

Finds stocks where 2+ *distinct* sell-side firms turned bullish (an upgrade,
or a new bullish-rated initiation) within a recent window. A single analyst
call is noise — one firm chasing price, one intern's model update. Two or
more independent shops turning bullish in the same window, especially with
price targets meaningfully above the tape, is a much harder signal to fake.

Different from every other screener in the dossier:
  - Per-ticker enrichment already surfaces individual analyst notes as a
    display field, but nothing scores or screens the universe on *clusters*
    of revisions the way `insider_cluster_screener.py` does for Form 4 buys.
  - Insider Cluster gates on insiders' own cash; THIS gates on outside
    analyst conviction — a different, complementary "smart money agrees"
    read that isn't fakeable by a single firm's house view.
  - PEAD / Earnings Momentum key off the earnings print itself; THIS keys
    off analyst reaction, which can cluster well after (or before) an
    earnings date on thesis changes, channel checks, or sector re-ratings.

Funnel architecture (3-stage, same pattern as insider_cluster / short_squeeze):
    Stage 1 → TradingView bulk API: liquid universe above a cap floor where
               sell-side coverage is dense enough for clusters to be real
    Stage 2 → Progressive funnel: liquidity + cap floor only — analyst
               revisions aren't a TradingView column, so there's nothing
               else to pre-filter on before the per-ticker deep scan
    Stage 3 → yfinance deep scan: hard-gates on 2+ distinct firms turning
               bullish in the lookback window, then scores conviction

Scoring (0-100):
    Cluster size     (35 pts) — distinct firms turning bullish; more = harder to fake
    Price target upside (25 pts) — avg upside of new targets vs current price
    Recency            (20 pts) — days since the most recent bullish revision
    Clean signal        (12 pts) — no offsetting downgrades in the same window
    Conviction level     (8 pts) — any "Strong Buy" grade in the cluster

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35, filtered out)

Usage:
    python -m dossier.analyst_revision_screener                     # whole market
    python -m dossier.analyst_revision_screener --tickers NVDA,AAPL # specific tickers
    python -m dossier.analyst_revision_screener --watchlist         # core watchlist only
    python -m dossier.analyst_revision_screener --days 45           # lookback window
    python -m dossier.analyst_revision_screener --top 20            # limit output
    python -m dossier.analyst_revision_screener --json              # machine output
    python -m dossier.analyst_revision_screener --quiet              # A+/A only

Output: docs/api/analyst-revision-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"One upgrade is a house view. Three houses in a month is a trend." — Sam
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
]

# ─── Funnel thresholds ────────────────────────────────────────────
_MIN_CAP = 500_000_000    # $500M floor — below this, sell-side coverage is too thin for clusters
_MIN_AVG_VOL = 150_000    # liquidity floor
_MIN_PRICE = 3.0

# ─── Screen thresholds ────────────────────────────────────────────
_MIN_DISTINCT_FIRMS = 2   # the hard gate that defines a "cluster"
DEFAULT_LOOKBACK_DAYS = 30   # revisions cluster on a faster clock than insider buys

_BULLISH_GRADE_MARKERS = (
    "buy", "overweight", "outperform", "positive", "accumulate", "add",
)
_BEARISH_GRADE_MARKERS = (
    "sell", "underperform", "underweight", "negative", "reduce",
)


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_candidates() -> list[dict]:
    """One POST to TradingView → liquid universe above the coverage-relevant
    cap floor. Analyst revisions aren't a TV column, so the per-ticker
    yfinance deep scan in Stage 3 does all the real work."""
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": _MIN_AVG_VOL},
            {"left": "close", "operation": "greater", "right": _MIN_PRICE},
            {"left": "market_cap_basic", "operation": "greater", "right": _MIN_CAP},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 5000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView Analyst Revision scan") or {}
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
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """Narrow the TV universe before paying for per-ticker revision lookups."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ ANALYST REVISION FUNNEL: {total} stocks from TradingView")

    survivors = [
        s for s in stocks
        if (s.get("market_cap") or 0) >= _MIN_CAP
        and (s.get("avg_vol_30d") or 0) >= _MIN_AVG_VOL
    ]
    if verbose:
        print(f"  │  Cap ≥${_MIN_CAP/1e6:.0f}M + Vol ≥{_MIN_AVG_VOL/1000:.0f}k"
              f" {total:>18} → {len(survivors)}")
        print(f"  └─ {len(survivors)} candidates pass to Stage 3\n")
    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  PURE PARSING + SCORING HELPERS (importable for tests)  ████
# ═══════════════════════════════════════════════════════════════════

def _parse_date(val) -> "date | None":
    """Best-effort coercion of a yfinance upgrades_downgrades date cell/index."""
    if val is None or (not isinstance(val, str) and pd.isna(val)):
        return None
    if isinstance(val, pd.Timestamp):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        try:
            parsed = pd.to_datetime(val)
            return None if pd.isna(parsed) else parsed.date()
        except Exception:
            return None
    return None


def _is_bullish_grade(grade: "str | None") -> bool:
    g = (grade or "").lower()
    return any(marker in g for marker in _BULLISH_GRADE_MARKERS)


def _is_bearish_grade(grade: "str | None") -> bool:
    g = (grade or "").lower()
    return any(marker in g for marker in _BEARISH_GRADE_MARKERS)


def _is_bullish_revision(action: "str | None", to_grade: "str | None") -> bool:
    """yfinance's Action is 'up' (upgrade), 'down' (downgrade), 'init'
    (new coverage), 'main' (rating held) or 'reit' (reiterated). An upgrade
    is bullish by definition of the action; a fresh initiation only counts
    if it starts bullish-rated."""
    a = (action or "").lower()
    if a == "up":
        return True
    if a == "init":
        return _is_bullish_grade(to_grade)
    return False


def _is_bearish_revision(action: "str | None", to_grade: "str | None") -> bool:
    a = (action or "").lower()
    if a == "down":
        return True
    if a == "init":
        return _is_bearish_grade(to_grade)
    return False


def _parse_analyst_revisions(
    df: "pd.DataFrame | None",
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    as_of: "date | None" = None,
) -> dict:
    """
    Reduce a yfinance stock.upgrades_downgrades DataFrame to the
    revision-cluster signal within the lookback window: distinct bullish
    firms, their new price targets, the most recent bullish date, and any
    offsetting downgrades.

    Never raises — a missing/malformed frame yields a zeroed result.
    """
    as_of = as_of or datetime.utcnow().date()
    cutoff = as_of - timedelta(days=lookback_days)

    firms: set[str] = set()
    price_targets: list[float] = []
    grades: list[str] = []
    downgrade_count = 0
    most_recent: "date | None" = None

    if isinstance(df, pd.DataFrame) and not df.empty:
        for idx, row in df.iterrows():
            grade_date = _parse_date(row.get("GradeDate")) or _parse_date(idx)
            if grade_date is None or grade_date < cutoff or grade_date > as_of:
                continue

            action = row.get("Action")
            to_grade = row.get("ToGrade")
            firm = str(row.get("Firm") or "Unknown").strip()

            if _is_bullish_revision(action, to_grade):
                firms.add(firm)
                grades.append(str(to_grade or ""))
                target = row.get("currentPriceTarget")
                if isinstance(target, (int, float)) and not pd.isna(target) and target > 0:
                    price_targets.append(float(target))
                if most_recent is None or grade_date > most_recent:
                    most_recent = grade_date
            elif _is_bearish_revision(action, to_grade):
                downgrade_count += 1

    return {
        "distinct_firms": len(firms),
        "firm_names": sorted(firms),
        "price_targets": price_targets,
        "grades": grades,
        "downgrade_count": downgrade_count,
        "most_recent_date": most_recent.isoformat() if most_recent else None,
    }


def cluster_size_score(distinct_firms: int) -> int:
    """35-pt scale: more distinct firms turning bullish = harder to fake."""
    if distinct_firms >= 4:
        return 35
    if distinct_firms == 3:
        return 26
    if distinct_firms == 2:
        return 18
    return 0


def pt_upside_score(avg_upside_pct: "float | None") -> int:
    """25-pt scale: average upside of the cluster's new price targets vs
    the current price."""
    if avg_upside_pct is None:
        return 0
    if avg_upside_pct >= 25:
        return 25
    if avg_upside_pct >= 15:
        return 18
    if avg_upside_pct >= 8:
        return 10
    if avg_upside_pct >= 3:
        return 5
    return 0


def recency_score(days_since: "int | None") -> int:
    """20-pt scale: analyst revisions move on a faster clock than insider
    buys, so the thresholds are tighter."""
    if days_since is None:
        return 0
    if days_since <= 3:
        return 20
    if days_since <= 7:
        return 14
    if days_since <= 14:
        return 8
    if days_since <= 30:
        return 3
    return 0


def clean_signal_score(downgrade_count: int) -> int:
    """12-pt scale: other firms downgrading in the same window muddies the
    read (a split Street, not a consensus shift) — reward a window with no
    offsetting downgrades."""
    if downgrade_count == 0:
        return 12
    if downgrade_count == 1:
        return 6
    return 0


def conviction_score(grades: list[str]) -> int:
    """8-pt scale: a 'Strong Buy' in the cluster reads as higher conviction
    than a run of plain 'Buy'/'Overweight' calls."""
    if any("strong" in (g or "").lower() for g in grades):
        return 8
    if grades:
        return 5
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

def score_analyst_revision_cluster(
    ticker: str,
    tv_data: "dict | None" = None,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> "dict | None":
    """
    Deep scan a single ticker for a bullish-revision-cluster setup.

    Hard-gates on 2+ distinct firms turning bullish within the lookback
    window — a single analyst call isn't a cluster. Returns None if data is
    insufficient or the gate fails.
    """
    try:
        stock = yf.Ticker(ticker)

        signal = _parse_analyst_revisions(stock.upgrades_downgrades, lookback_days=lookback_days)
        if signal["distinct_firms"] < _MIN_DISTINCT_FIRMS:
            return None

        df = stock.history(period="6mo")
        ok, _ = check_yfinance_history(df, ticker, min_rows=5)
        if not ok:
            return None

        current_price = float(df["Close"].iloc[-1])

        avg_upside_pct = None
        if signal["price_targets"]:
            upsides = [(t - current_price) / current_price * 100 for t in signal["price_targets"]]
            avg_upside_pct = sum(upsides) / len(upsides)

        days_since = None
        if signal["most_recent_date"]:
            days_since = (datetime.utcnow().date() - date.fromisoformat(signal["most_recent_date"])).days

        cluster_pts = cluster_size_score(signal["distinct_firms"])
        upside_pts = pt_upside_score(avg_upside_pct)
        recency_pts = recency_score(days_since)
        clean_pts = clean_signal_score(signal["downgrade_count"])
        conviction_pts = conviction_score(signal["grades"])

        total_score = cluster_pts + upside_pts + recency_pts + clean_pts + conviction_pts
        grade = _letter_grade(total_score)

        # Skip D grades — the 2+-firm gate already narrowed the field; a D
        # here means the cluster is thin, stale, or muddied by downgrades.
        if grade == "D":
            return None

        return {
            "ticker": ticker,
            "name": (tv_data or {}).get("name", ticker),
            "price": round(current_price, 2),
            "score": total_score,
            "grade": grade,
            "distinct_firms": signal["distinct_firms"],
            "firm_names": signal["firm_names"],
            "avg_upside_pct": round(avg_upside_pct, 1) if avg_upside_pct is not None else None,
            "downgrade_count": signal["downgrade_count"],
            "most_recent_date": signal["most_recent_date"],
            "days_since_revision": days_since,
            "market_cap": (tv_data or {}).get("market_cap"),
            "change_pct": (tv_data or {}).get("change_pct", 0),
            "score_breakdown": {
                "cluster_size": cluster_pts,
                "pt_upside": upside_pts,
                "recency": recency_pts,
                "clean_signal": clean_pts,
                "conviction": conviction_pts,
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
    if not cap:
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
        upside = r.get("avg_upside_pct")
        upside_str = f"+{upside:.0f}%" if upside is not None else "—"

        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Score:{r['score']:>3}  Firms:{r['distinct_firms']:>2}  "
            f"Upside:{upside_str:>6}  Downgrades:{r['downgrade_count']:>2}  "
            f"{chg_str:>6}  {cap_str}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/analyst-revision-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "analyst-revision-screener.json"
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
    parser = argparse.ArgumentParser(description="Analyst Revision Cluster Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--days", type=int, default=DEFAULT_LOOKBACK_DAYS, help="Lookback window in days")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n📈  Analyst Revision Cluster Screener — {len(tickers)} tickers\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n📈  Analyst Revision Cluster Screener — core watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n📈  Analyst Revision Cluster Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_candidates()
        print(f"     → {len(raw)} pre-filtered candidates from TradingView\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates for analyst revision "
          f"clusters (last {args.days}d)...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_analyst_revision_cluster(ticker, tv_data=tv_map.get(ticker, c), lookback_days=args.days)
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} clusters found so far")
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
    print(f"  📈  ANALYST REVISION CLUSTER SCREENER RESULTS — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 105}\n")

    print_results(results, quiet=args.quiet)

    if not args.no_save and not args.tickers and not args.watchlist:
        _save_api_output(results)


if __name__ == "__main__":
    main()
