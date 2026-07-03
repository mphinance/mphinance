#!/usr/bin/env python3
"""
🌊 PEAD Screener — Post-Earnings-Announcement Drift

Finds stocks that popped on a recent earnings report and are still grinding
higher — the Post-Earnings-Announcement Drift (PEAD) anomaly. Decades of
academic research (Bernard & Thomas, 1989, and every replication since) show
that stocks with a strong positive earnings surprise keep drifting in the
same direction for weeks after the initial reaction, because the market is
slow to fully price in the surprise.

Different from every other screener in the dossier:
  - Earnings Momentum: looks BEFORE the print, at technical setup ahead of
                        an upcoming report
  - Golden Cross / SMA200 Reclaim: structural trend-change signals unrelated
                        to any specific catalyst
  - THIS: looks AFTER the print — did the stock gap on the reaction, and is
          it still drifting rather than fading? The catalyst already fired;
          this screen catches the follow-through everyone else has stopped
          watching.

Funnel architecture (3-stage, same pattern as vcp / tao / earnings_momentum):
    Stage 1 → TradingView bulk API: liquid stocks with a reported earnings
               date inside the lookback window
    Stage 2 → Progressive funnel: liquidity floor, not already collapsing
    Stage 3 → yfinance deep scan: locate the exact pre/post-earnings closes,
               measure the reaction gap and the drift since, cross-check the
               reported surprise %, confirm sustained volume interest

Scoring (0–100):
    Reaction gap       (30 pts) — size of the initial earnings-day move
    Drift continuation (35 pts) — how much further it has run since the gap
    Earnings surprise   (20 pts) — magnitude of the reported EPS beat
    Volume follow-through (15 pts) — sustained interest since the print

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)

Usage:
    python -m dossier.pead_screener                       # whole market
    python -m dossier.pead_screener --tickers NVDA,AAPL  # specific tickers
    python -m dossier.pead_screener --watchlist           # core watchlist only
    python -m dossier.pead_screener --days 10             # lookback window
    python -m dossier.pead_screener --top 20              # limit output
    python -m dossier.pead_screener --json                # machine output
    python -m dossier.pead_screener --quiet               # A+/A only
    python -m dossier.pead_screener --no-save             # skip JSON write

Output: docs/api/pead-screener.json (served via GitHub Pages)

Reference: Bernard, V. & Thomas, J. (1989). "Post-Earnings-Announcement
Drift: Delayed Price Response or Risk Premium?" Journal of Accounting Research.
"The print already happened. The drift is the part nobody's watching anymore." — Sam
"""

import argparse
import json
import sys
import time
from datetime import date, datetime
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

LOOKBACK_DAYS = 10     # Default: earnings reported within the last N trading days
MIN_GAP_PCT = 3.0      # Minimum earnings-day reaction to qualify as a "pop"

_TV_COLUMNS = [
    "name",                     # 0  ticker
    "description",              # 1  company name
    "close",                    # 2  last price
    "change",                   # 3  % change today
    "volume",                   # 4  today's volume
    "average_volume_30d_calc",  # 5  30d avg volume
    "market_cap_basic",         # 6  market cap
    "SMA50",                    # 7  SMA 50
    "SMA200",                   # 8  SMA 200
    "RSI",                      # 9  RSI(14)
    "earnings_release_date",    # 10 most recent past earnings date (unix seconds)
    "Perf.W",                   # 11 weekly performance %
    "Perf.1M",                  # 12 monthly performance %
]


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _tv_fetch_pead_candidates(lookback_days: int = LOOKBACK_DAYS) -> list[dict]:
    """
    One POST to TradingView → liquid stocks that reported earnings within
    the lookback window (with a calendar-day buffer for weekends/holidays).
    """
    now = time.time()
    earliest = now - lookback_days * 1.6 * 86400

    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 200_000},
            {"left": "close", "operation": "greater", "right": 5},
            {"left": "earnings_release_date", "operation": "in_range", "right": [earliest, now]},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": _TV_COLUMNS,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 10000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = safe_json(resp, "TradingView PEAD scan") or {}
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
            "sma_50": d[7],
            "sma_200": d[8],
            "rsi": d[9],
            "earnings_ts": d[10],
            "perf_1w": d[11],
            "perf_1m": d[12],
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — PROGRESSIVE FUNNEL  ████
# ═══════════════════════════════════════════════════════════════════

def _funnel_filter(stocks: list[dict], verbose: bool = True) -> list[dict]:
    """
    Narrow the TV universe before paying the cost of yfinance deep scans.
    Most of the real gating (the gap + drift itself) happens in Stage 3.
    """
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ PEAD FUNNEL: {total} stocks from TradingView")

    # 2A: Liquidity floor
    survivors = [s for s in stocks if (
        (s["market_cap"] or 0) >= 300_000_000
        and (s["avg_vol_30d"] or 0) >= 250_000
    )]
    if verbose:
        print(f"  ├─ Cap ≥$300M + Vol ≥250K ──────────→ {len(survivors)} ({total - len(survivors)} cut)")

    # 2B: Not actively collapsing — a fading name isn't drifting, it's dying
    prev = len(survivors)
    survivors = [s for s in survivors if (
        s["perf_1w"] is None or s["perf_1w"] >= -12
    )]
    if verbose:
        print(f"  ├─ 1W return ≥ -12% (not cratering) → {len(survivors)} ({prev - len(survivors)} cut)")

    if verbose:
        pct = (1 - len(survivors) / total) * 100 if total > 0 else 0
        print(f"  └─ FUNNEL DONE: {len(survivors)} survivors ({pct:.0f}% eliminated)\n")

    return survivors


# ═══════════════════════════════════════════════════════════════════
# ████  SCORING HELPERS (public — importable for tests)  ████
# ═══════════════════════════════════════════════════════════════════

def gap_score(gap_pct: float) -> int:
    """Size of the earnings-day reaction (30 pts max). Bigger pop = more conviction."""
    if gap_pct >= 15:
        return 30
    if gap_pct >= 10:
        return 25
    if gap_pct >= 7:
        return 20
    if gap_pct >= 5:
        return 14
    if gap_pct >= 3:
        return 8
    return 0


def drift_score(drift_pct: float) -> int:
    """
    How much further the stock has run since the reaction day (35 pts max).

    drift_pct = % change from the reaction-day close to the current close.
    Positive and growing = the drift is intact. Negative = the gap is fading.
    """
    if drift_pct >= 10:
        return 35
    if drift_pct >= 5:
        return 28
    if drift_pct >= 2:
        return 20
    if drift_pct >= 0:
        return 12
    if drift_pct >= -3:
        return 4
    return 0


def surprise_score(surprise_pct: float | None) -> int:
    """
    Magnitude of the reported EPS beat (20 pts max).

    None (surprise data unavailable) gets a neutral partial credit rather
    than being penalized — plenty of legitimate drifts lack clean data.
    """
    if surprise_pct is None:
        return 10
    if surprise_pct >= 15:
        return 20
    if surprise_pct >= 8:
        return 16
    if surprise_pct >= 3:
        return 11
    if surprise_pct >= 0:
        return 6
    return 0


def volume_score(vol_ratio: float) -> int:
    """
    Sustained volume interest since the print vs the pre-earnings baseline
    (15 pts max). vol_ratio = post-earnings avg volume / pre-earnings avg volume.
    """
    if vol_ratio >= 2.0:
        return 15
    if vol_ratio >= 1.5:
        return 11
    if vol_ratio >= 1.2:
        return 7
    if vol_ratio >= 1.0:
        return 3
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
# ████  STAGE 3 — DEEP SCAN (yfinance)  ████
# ═══════════════════════════════════════════════════════════════════

def _recent_earnings_event(ticker: str, max_days: int) -> dict | None:
    """
    Return the most recent PAST earnings report within max_days calendar
    days, as {"date": date, "after_hours": bool, "surprise_pct": float|None},
    or None if there isn't one (or the calendar is unavailable).

    after_hours marks whether the report landed post-close (the price
    reaction shows up on the NEXT trading day) vs pre-market (same day).
    """
    try:
        df = yf.Ticker(ticker).get_earnings_dates(limit=6)
        if df is None or df.empty:
            return None
        today = date.today()
        for ts, row in df.iterrows():
            reported = row.get("Reported EPS")
            if reported is None or pd.isna(reported):
                continue    # future report — hasn't happened yet
            ed = ts.date() if hasattr(ts, "date") else ts
            days_ago = (today - ed).days
            if 0 <= days_ago <= max_days:
                surprise = row.get("Surprise(%)")
                surprise = None if surprise is None or pd.isna(surprise) else float(surprise)
                after_hours = getattr(ts, "hour", 16) >= 12
                return {"date": ed, "after_hours": after_hours, "surprise_pct": surprise}
            if days_ago > max_days:
                return None    # rows are newest-first; nothing closer left
        return None
    except Exception:
        return None


def score_pead(ticker: str, tv_data: dict | None = None,
               lookback_days: int = LOOKBACK_DAYS) -> dict | None:
    """
    Deep scan a single ticker for a post-earnings drift setup.

    Returns a result dict on success, None if there's no recent qualifying
    earnings reaction or the drift has already faded.
    """
    try:
        event = _recent_earnings_event(ticker, max_days=int(lookback_days * 1.6))
        if event is None:
            return None
        earnings_date = event["date"]
        after_hours = event["after_hours"]

        df = yf.Ticker(ticker).history(period="3mo")
        ok, _ = check_yfinance_history(df, ticker, min_rows=30)
        if not ok:
            return None

        idx_dates = [ts.date() for ts in df.index]
        before_positions = [i for i, d in enumerate(idx_dates) if d < earnings_date]
        # After-hours reports react the NEXT trading day; pre-market reports
        # react the same day.
        after_positions = [
            i for i, d in enumerate(idx_dates)
            if (d > earnings_date if after_hours else d >= earnings_date)
        ]
        if not before_positions or not after_positions:
            return None

        idx_before = before_positions[-1]
        idx_after = after_positions[0]
        days_since = (len(df) - 1) - idx_after
        if not (0 <= days_since <= lookback_days):
            return None

        close = df["Close"]
        pre_close = float(close.iloc[idx_before])
        reaction_close = float(close.iloc[idx_after])
        current_close = float(close.iloc[-1])

        if pre_close <= 0 or reaction_close <= 0:
            return None

        gap_pct = (reaction_close - pre_close) / pre_close * 100
        if gap_pct < MIN_GAP_PCT:
            return None    # only chasing positive reactions

        drift_pct = (current_close - reaction_close) / reaction_close * 100

        volume = df["Volume"]
        pre_window = volume.iloc[max(0, idx_before - 30): idx_before]
        post_window = volume.iloc[idx_after:]
        baseline_vol = float(pre_window.mean()) if len(pre_window) else None
        recent_vol = float(post_window.mean()) if len(post_window) else None
        vol_ratio = (
            recent_vol / baseline_vol
            if baseline_vol and baseline_vol > 0 and recent_vol is not None
            else 1.0
        )

        gap_pts = gap_score(gap_pct)
        drift_pts = drift_score(drift_pct)
        surprise_pts = surprise_score(event["surprise_pct"])
        vol_pts = volume_score(vol_ratio)

        total_score = gap_pts + drift_pts + surprise_pts + vol_pts
        grade = _letter_grade(total_score)

        # Skip D grades — faded gaps add noise without value
        if grade == "D":
            return None

        return {
            "ticker": ticker,
            "name": (tv_data or {}).get("name", ticker),
            "price": round(current_close, 2),
            "score": total_score,
            "grade": grade,
            "earnings_date": earnings_date.isoformat(),
            "days_since_earnings": days_since,
            "gap_pct": round(gap_pct, 2),
            "drift_pct": round(drift_pct, 2),
            "surprise_pct": event["surprise_pct"],
            "volume_ratio": round(vol_ratio, 2),
            "market_cap": (tv_data or {}).get("market_cap"),
            "change_pct": (tv_data or {}).get("change_pct", 0),
            "score_breakdown": {
                "gap": gap_pts,
                "drift": drift_pts,
                "surprise": surprise_pts,
                "volume": vol_pts,
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
        cap_str = _fmt_cap(r["market_cap"])
        surprise = r["surprise_pct"]
        surprise_str = f"{surprise:+.1f}%" if surprise is not None else "  n/a"

        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Score:{r['score']:>3}  Gap:{r['gap_pct']:+.1f}%  Drift:{r['drift_pct']:+.1f}%  "
            f"Surprise:{surprise_str:>7}  {r['days_since_earnings']:>2}d ago  {cap_str}"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/pead-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pead-screener.json"
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
        description="PEAD (Post-Earnings-Announcement Drift) Screener"
    )
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist only")
    parser.add_argument("--days", type=int, default=LOOKBACK_DAYS,
                        help=f"Earnings-within window in trading days (default {LOOKBACK_DAYS})")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        print(f"\n🌊  PEAD Screener — {len(tickers)} tickers\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    elif args.watchlist:
        tickers = CORE_WATCHLIST
        print(f"\n🌊  PEAD Screener — core watchlist ({len(tickers)} tickers)\n")
        tv_map = {}
        candidates = [{"ticker": t, "name": t} for t in tickers]
    else:
        print(f"\n🌊  PEAD Screener — earnings reported within {args.days} trading days\n")
        print("  ⚡ Stage 1: TradingView bulk scan...")
        raw = _tv_fetch_pead_candidates(lookback_days=args.days)
        print(f"     → {len(raw)} pre-filtered candidates from TradingView\n")
        candidates = _funnel_filter(raw)
        tv_map = {s["ticker"]: s for s in raw}
        candidates.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    print(f"  🧪 Stage 3: Deep scanning {len(candidates)} candidates...")
    results = []
    for i, c in enumerate(candidates):
        ticker = c["ticker"]
        r = score_pead(ticker, tv_data=tv_map.get(ticker, c), lookback_days=args.days)
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(candidates)} scanned — {len(results)} drifts found so far")
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
    print(f"  🌊  PEAD SCREENER RESULTS — {len(results)} drifts")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 105}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 105}")
    print(f"  Legend: Gap = earnings-day reaction  |  Drift = move since the reaction close")
    print(f"          Surprise = reported EPS beat %  |  {args.days}d lookback window\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
