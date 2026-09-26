#!/usr/bin/env python3
"""
🚩 Insider Cluster-Selling Screener — Multiple Insiders, Heading for the Exit

Finds stocks where 2+ *distinct* company insiders (officers, directors,
10% owners) made open-market sales within a recent window. A single
insider selling is weak evidence — it's routinely a scheduled 10b5-1 plan
sale, tax planning, or diversification, and means almost nothing on its
own. Two or more unrelated insiders selling independently in the same
window is a much harder signal to explain away, and it is the mirror
image of `insider_cluster_screener.py`'s "smart money agrees" buy signal
that nothing else in this dossier surfaces.

Different from every other screener in the dossier:
  - `insider_cluster_screener.py` gates on the same 2+-distinct-insider
    cluster idea but on the LONG side; THIS is the short-side mirror —
    a caution flag on names already on a watchlist, or a candidate list
    for puts/shorts, not a buy signal.
  - Short Squeeze gates on short-interest *positioning* data; THIS gates
    on insiders' own money leaving, which is a different (and earlier)
    tell than the short interest showing up in a biweekly FINRA report.
  - Unlike the buy screener, selling while a stock is EXTENDED above its
    50-day is treated as the stronger signal here (cashing out into
    strength), not the weaker one — the trend-context logic is inverted
    on purpose, not a copy-paste artifact.

Funnel architecture (3-stage, same pattern as insider_cluster_screener):
    Stage 1 → TradingView bulk API: liquid, filing-relevant universe
               (below ~$300M, Form 4 patterns get thin and noisy)
    Stage 2 → Progressive funnel: liquidity + cap floor only — insider
               data isn't a TradingView column, so there's nothing else
               to pre-filter on before the per-ticker deep scan
    Stage 3 → yfinance deep scan: hard-gates on 2+ distinct insiders
               selling in the lookback window, then scores conviction

Scoring (0–100):
    Cluster size       (35 pts) — distinct insiders selling; more = harder to wave off
    Total value sold    (25 pts) — aggregate $ across the cluster
    Recency             (20 pts) — days since the most recent sale in the cluster
    Clean signal        (12 pts) — no offsetting insider BUYS in the same window
    Trend context        (8 pts) — selling while extended above the 50-day
                                    (cashing out into strength, not routine)

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35, filtered out)

Usage:
    python -m dossier.insider_selling_cluster_screener                     # whole market
    python -m dossier.insider_selling_cluster_screener --tickers GME,AMC   # specific tickers
    python -m dossier.insider_selling_cluster_screener --watchlist         # core watchlist only
    python -m dossier.insider_selling_cluster_screener --days 60           # lookback window
    python -m dossier.insider_selling_cluster_screener --top 20            # limit output
    python -m dossier.insider_selling_cluster_screener --json              # machine output
    python -m dossier.insider_selling_cluster_screener --quiet             # A+/A only

Output: docs/api/insider-selling-cluster-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"One insider selling is estate planning. Three insiders selling is a going-away party." — Sam
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
_MIN_CAP = 300_000_000    # $300M floor — below this, Form 4 filing patterns are noisy
_MIN_AVG_VOL = 150_000    # liquidity floor
_MIN_PRICE = 3.0

# ─── Screen thresholds ────────────────────────────────────────────
_MIN_DISTINCT_SELLERS = 2   # the hard gate that defines a "cluster"
DEFAULT_LOOKBACK_DAYS = 90


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_candidates() -> list[dict]:
    """One POST to TradingView → liquid universe above the insider-data-relevant
    cap floor. Insider transactions aren't a TV column, so the per-ticker
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
    data = safe_json(resp, "TradingView Insider Selling Cluster scan") or {}
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
    """Narrow the TV universe before paying for per-ticker insider lookups."""
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ INSIDER SELLING CLUSTER FUNNEL: {total} stocks from TradingView")

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
    """Best-effort coercion of a yfinance insider-transactions date cell."""
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


def _is_purchase(transaction: str) -> bool:
    """Open-market buys — yfinance's Transaction text is free-form
    ('Purchase', 'Purchase at price ...'), so this matches on substring."""
    t = (transaction or "").lower()
    return "purchase" in t or t.startswith("buy")


def _is_sale(transaction: str) -> bool:
    t = (transaction or "").lower()
    return "sale" in t or t.startswith("sell")


def _parse_insider_sales(
    df: "pd.DataFrame | None",
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    as_of: "date | None" = None,
) -> dict:
    """
    Reduce a yfinance stock.insider_transactions DataFrame to the
    cluster-selling signal within the lookback window: distinct sellers,
    aggregate $ sold, most recent sale date, and any offsetting buys.

    Never raises — a missing/malformed frame yields a zeroed result.
    """
    as_of = as_of or datetime.utcnow().date()
    cutoff = as_of - timedelta(days=lookback_days)

    sellers: set[str] = set()
    total_value = 0.0
    buy_count = 0
    most_recent_sale: "date | None" = None

    if isinstance(df, pd.DataFrame) and not df.empty:
        for _, row in df.iterrows():
            txn_date = _parse_date(row.get("Start Date") or row.get("Date"))
            if txn_date is None or txn_date < cutoff or txn_date > as_of:
                continue
            # yfinance's "Transaction" column is empty in current data; the
            # actual "Sale at price X per share." / "Purchase at price X..."
            # wording lives in "Text". Check both so this survives either shape.
            transaction = str(row.get("Transaction") or "") + " " + str(row.get("Text") or "")
            insider = str(row.get("Insider") or "Unknown").strip()
            value_raw = row.get("Value")
            value = float(value_raw) if isinstance(value_raw, (int, float)) and not pd.isna(value_raw) else 0.0

            if _is_sale(transaction):
                sellers.add(insider)
                total_value += value
                if most_recent_sale is None or txn_date > most_recent_sale:
                    most_recent_sale = txn_date
            elif _is_purchase(transaction):
                buy_count += 1

    return {
        "distinct_sellers": len(sellers),
        "seller_names": sorted(sellers),
        "total_value": total_value,
        "buy_count": buy_count,
        "most_recent_sale": most_recent_sale.isoformat() if most_recent_sale else None,
    }


def cluster_size_score(distinct_sellers: int) -> int:
    """35-pt scale: more distinct insiders selling = harder to wave off."""
    if distinct_sellers >= 4:
        return 35
    if distinct_sellers == 3:
        return 26
    if distinct_sellers == 2:
        return 18
    return 0


def total_value_score(total_value: float) -> int:
    """25-pt scale: aggregate $ sold across the cluster."""
    if total_value >= 5_000_000:
        return 25
    if total_value >= 1_000_000:
        return 18
    if total_value >= 250_000:
        return 10
    if total_value >= 50_000:
        return 5
    return 0


def recency_score(days_since_sale: "int | None") -> int:
    """20-pt scale: a fresher cluster is a fresher signal."""
    if days_since_sale is None:
        return 0
    if days_since_sale <= 7:
        return 20
    if days_since_sale <= 21:
        return 14
    if days_since_sale <= 45:
        return 8
    if days_since_sale <= 90:
        return 3
    return 0


def clean_signal_score(buy_count: int) -> int:
    """12-pt scale: insiders selling while OTHER insiders buy in the same
    window muddies the read (routine diversification vs. an exit) —
    reward a window with no offsetting buys."""
    if buy_count == 0:
        return 12
    if buy_count == 1:
        return 6
    return 0


def trend_context_score(price: float, sma50: "float | None") -> int:
    """8-pt scale: selling while EXTENDED above the 50-day reads as cashing
    out into strength — the more alarming version of the tell. Selling at
    or below the 50-day is more consistent with routine/planned selling
    (tax, diversification, a pre-set 10b5-1 schedule) and scores lower.
    This is intentionally the inverse of the buy screener's trend logic."""
    if sma50 is None or sma50 <= 0:
        return 4
    extension = price / sma50
    if extension >= 1.15:
        return 8
    if extension >= 1.05:
        return 4
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

def score_insider_selling_cluster(
    ticker: str,
    tv_data: "dict | None" = None,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> "dict | None":
    """
    Deep scan a single ticker for a cluster-selling setup.

    Hard-gates on 2+ distinct insiders selling within the lookback window —
    a single insider's sale isn't a cluster. Returns None if data is
    insufficient or the gate fails.
    """
    try:
        stock = yf.Ticker(ticker)

        signal = _parse_insider_sales(stock.insider_transactions, lookback_days=lookback_days)
        if signal["distinct_sellers"] < _MIN_DISTINCT_SELLERS:
            return None

        df = stock.history(period="6mo")
        ok, _ = check_yfinance_history(df, ticker, min_rows=40)
        if not ok:
            return None

        close = df["Close"]
        current_price = float(close.iloc[-1])
        sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None

        days_since = None
        if signal["most_recent_sale"]:
            days_since = (datetime.utcnow().date() - date.fromisoformat(signal["most_recent_sale"])).days

        cluster_pts = cluster_size_score(signal["distinct_sellers"])
        value_pts = total_value_score(signal["total_value"])
        recency_pts = recency_score(days_since)
        clean_pts = clean_signal_score(signal["buy_count"])
        trend_pts = trend_context_score(current_price, sma50)

        total_score = cluster_pts + value_pts + recency_pts + clean_pts + trend_pts
        grade = _letter_grade(total_score)

        # Skip D grades — the 2+-seller gate already narrowed the field; a D
        # here means the cluster is thin, stale, or muddied by insider buys.
        if grade == "D":
            return None

        return {
            "ticker": ticker,
            "name": (tv_data or {}).get("name", ticker),
            "price": round(current_price, 2),
            "score": total_score,
            "grade": grade,
            "distinct_sellers": signal["distinct_sellers"],
            "seller_names": signal["seller_names"],
            "total_value": round(signal["total_value"], 2),
            "buy_count": signal["buy_count"],
            "most_recent_sale": signal["most_recent_sale"],
            "days_since_sale": days_since,
            "market_cap": (tv_data or {}).get("market_cap"),
            "change_pct": (tv_data or {}).get("change_pct", 0),
            "score_breakdown": {
                "cluster_size": cluster_pts,
                "total_value": value_pts,
                "recency": recency_pts,
                "clean_signal": clean_pts,
                "trend_context": trend_pts,
            },
        }

    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT & FORMATTING  ████
# ═══════════════════════════════════════════════════════════════════

_GRADE_COLOR = {
    "A+": "\033[91m", "A": "\033[31m", "B": "\033[93m",
    "C": "\033[94m", "D": "\033[90m",
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


def _fmt_value(value) -> str:
    if not value:
        return "—"
    if value >= 1e6:
        return f"${value/1e6:.1f}M"
    return f"${value/1e3:.0f}k"


def print_results(results: list[dict], quiet: bool = False) -> None:
    for r in results:
        grade = r["grade"]
        if quiet and grade not in ("A+", "A"):
            continue
        change = r.get("change_pct", 0) or 0
        chg_str = f"+{change:.1f}%" if change >= 0 else f"{change:.1f}%"
        cap_str = _fmt_cap(r["market_cap"])
        val_str = _fmt_value(r["total_value"])

        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Score:{r['score']:>3}  Sellers:{r['distinct_sellers']:>2}  "
            f"Sold:{val_str:>7}  Buys:{r['buy_count']:>2}  "
            f"{chg_str:>6}  {cap_str}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/insider-selling-cluster-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "insider-selling-cluster-screener.json"
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
    parser = argparse.ArgumentParser(description="Insider Cluster-Selling Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. GME,AMC)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--days", type=int, default=DEFAULT_LOOKBACK_DAYS, help="Lookback window in days")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🚩  Insider Selling Cluster Screener — {len(tickers)} tickers\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🚩  Insider Selling Cluster Screener — core watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🚩  Insider Selling Cluster Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_candidates()
        print(f"     → {len(raw)} pre-filtered candidates from TradingView\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates for insider selling clusters "
          f"(last {args.days}d)...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_insider_selling_cluster(ticker, tv_data=tv_map.get(ticker, c), lookback_days=args.days)
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
    print(f"  🚩  INSIDER SELLING CLUSTER SCREENER RESULTS — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 105}\n")

    print_results(results, quiet=args.quiet)

    if not args.no_save and not args.tickers and not args.watchlist:
        _save_api_output(results)


if __name__ == "__main__":
    main()
