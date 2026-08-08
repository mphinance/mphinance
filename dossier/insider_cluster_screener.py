#!/usr/bin/env python3
"""
🕵️ Insider Cluster-Buying Screener — Multiple Insiders, One Direction

Finds stocks where 2+ *distinct* company insiders (officers, directors,
10% owners) made open-market purchases within a recent window. A single
insider buying is weak evidence — it could be a scheduled 10b5-1 plan
purchase or one person's idiosyncratic conviction. Two or more unrelated
insiders buying independently in the same window is a much harder signal
to fake, and it is the one true "smart money agrees" positioning tell that
nothing else in this dossier surfaces.

Different from every other screener in the dossier:
  - Per-ticker enrichment (`data_sources/ticker_enrichment.py`) already
    fetches `stock.insider_transactions`, but only as a display field on
    single-ticker dossier cards — it never scores or screens the universe.
  - Short Squeeze gates on short-interest positioning; THIS gates on the
    opposite side — insiders putting their own cash on the long side.
  - Nothing else requires 2+ *distinct* buyers; this is a cluster screen,
    not a single-transaction screen.

Funnel architecture (3-stage, same pattern as short_squeeze / nr7 / vcp):
    Stage 1 → TradingView bulk API: liquid, filing-relevant universe
               (below ~$300M, Form 4 patterns get thin and noisy)
    Stage 2 → Progressive funnel: liquidity + cap floor only — insider
               data isn't a TradingView column, so there's nothing else
               to pre-filter on before the per-ticker deep scan
    Stage 3 → yfinance deep scan: hard-gates on 2+ distinct insiders
               buying in the lookback window, then scores conviction

Scoring (0–100):
    Cluster size       (35 pts) — distinct insiders buying; more = harder to fake
    Total value bought  (25 pts) — aggregate $ across the cluster
    Recency             (20 pts) — days since the most recent buy in the cluster
    Clean signal        (12 pts) — no offsetting insider SALES in the same window
    Trend context        (8 pts) — buying near/below the 50-day (not chasing)

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35, filtered out)

Usage:
    python -m dossier.insider_cluster_screener                     # whole market
    python -m dossier.insider_cluster_screener --tickers GME,AMC   # specific tickers
    python -m dossier.insider_cluster_screener --watchlist         # core watchlist only
    python -m dossier.insider_cluster_screener --days 60           # lookback window
    python -m dossier.insider_cluster_screener --top 20            # limit output
    python -m dossier.insider_cluster_screener --json               # machine output
    python -m dossier.insider_cluster_screener --quiet             # A+/A only

Output: docs/api/insider-cluster-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"One insider buying is a hunch. Three insiders buying is a memo nobody sent you." — Sam
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
_MIN_DISTINCT_BUYERS = 2   # the hard gate that defines a "cluster"
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
    data = safe_json(resp, "TradingView Insider Cluster scan") or {}
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
        print(f"\n  ┌─ INSIDER CLUSTER FUNNEL: {total} stocks from TradingView")

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


def _parse_insider_transactions(
    df: "pd.DataFrame | None",
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    as_of: "date | None" = None,
) -> dict:
    """
    Reduce a yfinance stock.insider_transactions DataFrame to the
    cluster-buying signal within the lookback window: distinct purchasers,
    aggregate $ bought, most recent buy date, and any offsetting sales.

    Never raises — a missing/malformed frame yields a zeroed result.
    """
    as_of = as_of or datetime.utcnow().date()
    cutoff = as_of - timedelta(days=lookback_days)

    buyers: set[str] = set()
    total_value = 0.0
    sale_count = 0
    most_recent_buy: "date | None" = None

    if isinstance(df, pd.DataFrame) and not df.empty:
        for _, row in df.iterrows():
            txn_date = _parse_date(row.get("Start Date") or row.get("Date"))
            if txn_date is None or txn_date < cutoff or txn_date > as_of:
                continue
            # yfinance's "Transaction" column is empty in current data; the
            # actual "Purchase at price X per share." / "Sale at price X..."
            # wording lives in "Text". Check both so this survives either shape.
            transaction = str(row.get("Transaction") or "") + " " + str(row.get("Text") or "")
            insider = str(row.get("Insider") or "Unknown").strip()
            value_raw = row.get("Value")
            value = float(value_raw) if isinstance(value_raw, (int, float)) and not pd.isna(value_raw) else 0.0

            if _is_purchase(transaction):
                buyers.add(insider)
                total_value += value
                if most_recent_buy is None or txn_date > most_recent_buy:
                    most_recent_buy = txn_date
            elif _is_sale(transaction):
                sale_count += 1

    return {
        "distinct_buyers": len(buyers),
        "buyer_names": sorted(buyers),
        "total_value": total_value,
        "sale_count": sale_count,
        "most_recent_buy": most_recent_buy.isoformat() if most_recent_buy else None,
    }


def cluster_size_score(distinct_buyers: int) -> int:
    """35-pt scale: more distinct insiders buying = harder to fake."""
    if distinct_buyers >= 4:
        return 35
    if distinct_buyers == 3:
        return 26
    if distinct_buyers == 2:
        return 18
    return 0


def total_value_score(total_value: float) -> int:
    """25-pt scale: aggregate $ bought across the cluster."""
    if total_value >= 5_000_000:
        return 25
    if total_value >= 1_000_000:
        return 18
    if total_value >= 250_000:
        return 10
    if total_value >= 50_000:
        return 5
    return 0


def recency_score(days_since_buy: "int | None") -> int:
    """20-pt scale: a fresher cluster is a fresher signal."""
    if days_since_buy is None:
        return 0
    if days_since_buy <= 7:
        return 20
    if days_since_buy <= 21:
        return 14
    if days_since_buy <= 45:
        return 8
    if days_since_buy <= 90:
        return 3
    return 0


def clean_signal_score(sale_count: int) -> int:
    """12-pt scale: insiders buying while OTHER insiders sell in the same
    window muddies the read (routine diversification vs. conviction) —
    reward a window with no offsetting sales."""
    if sale_count == 0:
        return 12
    if sale_count == 1:
        return 6
    return 0


def trend_context_score(price: float, sma50: "float | None") -> int:
    """8-pt scale: buying near/below the 50-day reads as a value/support
    signal rather than insiders chasing an already-extended tape."""
    if sma50 is None or sma50 <= 0:
        return 4
    extension = price / sma50
    if extension <= 1.05:
        return 8
    if extension <= 1.15:
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

def score_insider_cluster(
    ticker: str,
    tv_data: "dict | None" = None,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> "dict | None":
    """
    Deep scan a single ticker for a cluster-buying setup.

    Hard-gates on 2+ distinct insiders buying within the lookback window —
    a single insider's purchase isn't a cluster. Returns None if data is
    insufficient or the gate fails.
    """
    try:
        stock = yf.Ticker(ticker)

        signal = _parse_insider_transactions(stock.insider_transactions, lookback_days=lookback_days)
        if signal["distinct_buyers"] < _MIN_DISTINCT_BUYERS:
            return None

        df = stock.history(period="6mo")
        ok, _ = check_yfinance_history(df, ticker, min_rows=40)
        if not ok:
            return None

        close = df["Close"]
        current_price = float(close.iloc[-1])
        sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None

        days_since = None
        if signal["most_recent_buy"]:
            days_since = (datetime.utcnow().date() - date.fromisoformat(signal["most_recent_buy"])).days

        cluster_pts = cluster_size_score(signal["distinct_buyers"])
        value_pts = total_value_score(signal["total_value"])
        recency_pts = recency_score(days_since)
        clean_pts = clean_signal_score(signal["sale_count"])
        trend_pts = trend_context_score(current_price, sma50)

        total_score = cluster_pts + value_pts + recency_pts + clean_pts + trend_pts
        grade = _letter_grade(total_score)

        # Skip D grades — the 2+-buyer gate already narrowed the field; a D
        # here means the cluster is thin, stale, or muddied by sales.
        if grade == "D":
            return None

        return {
            "ticker": ticker,
            "name": (tv_data or {}).get("name", ticker),
            "price": round(current_price, 2),
            "score": total_score,
            "grade": grade,
            "distinct_buyers": signal["distinct_buyers"],
            "buyer_names": signal["buyer_names"],
            "total_value": round(signal["total_value"], 2),
            "sale_count": signal["sale_count"],
            "most_recent_buy": signal["most_recent_buy"],
            "days_since_buy": days_since,
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
            f"Score:{r['score']:>3}  Buyers:{r['distinct_buyers']:>2}  "
            f"Bought:{val_str:>7}  Sales:{r['sale_count']:>2}  "
            f"{chg_str:>6}  {cap_str}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/insider-cluster-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "insider-cluster-screener.json"
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
    parser = argparse.ArgumentParser(description="Insider Cluster-Buying Screener")
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
        print(f"\n🕵️  Insider Cluster Screener — {len(tickers)} tickers\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🕵️  Insider Cluster Screener — core watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print("\n🕵️  Insider Cluster Screener — whole US equity market\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_candidates()
        print(f"     → {len(raw)} pre-filtered candidates from TradingView\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates for insider clusters "
          f"(last {args.days}d)...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_insider_cluster(ticker, tv_data=tv_map.get(ticker, c), lookback_days=args.days)
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
    print(f"  🕵️  INSIDER CLUSTER SCREENER RESULTS — {len(results)} setups")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 105}\n")

    print_results(results, quiet=args.quiet)

    if not args.no_save and not args.tickers and not args.watchlist:
        _save_api_output(results)


if __name__ == "__main__":
    main()
