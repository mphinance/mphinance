#!/usr/bin/env python3
"""
📅 Seasonality Screener — Calendar-Month Edge Finder

Finds stocks with a historically strong (or weak) track record during the
CURRENT calendar month. "Sell in May," the "Santa Claus rally," and dozens
of quieter single-name equivalents are real, measurable patterns in a
ticker's own price history — this screen measures them directly instead of
relying on market lore.

Different from every other screener in the dossier:
  - Every other screen reads the CURRENT tape (price, volume, RSI, earnings
    reaction, options positioning right now).
  - THIS reads the CALENDAR: for each ticker, how has it actually performed
    during this specific month across the last N years, and how consistent
    was that edge?

Method:
    For each ticker, pull `--years` years of daily history and, for every
    completed occurrence of the target month, compute the return from the
    month's first close to its last close. The in-progress current year is
    always excluded — its month isn't finished yet. Aggregate the yearly
    returns into an average, a win rate (share of years agreeing with the
    overall direction), a consistency measure, and a 3-year recency check.

Scoring (0–100), reflecting the CONVICTION of the edge (either direction):
    Win rate           (35 pts) — share of years matching the overall bias
    Avg magnitude       (30 pts) — |average monthly return|, capped at 6%
    Consistency         (20 pts) — inverse of return variance vs. the mean
    Recent confirmation (15 pts) — did the last 3 years agree with the bias

Grades: A+ (80+) · A (65–79) · B (50–64) · C (35–49) · D (<35)
`direction` marks whether the edge is "bullish" or "bearish" — a high grade
just means the pattern is strong and repeatable, not which way it points.

Usage:
    python -m dossier.seasonality_screener                    # core watchlist
    python -m dossier.seasonality_screener --tickers NVDA,AAPL
    python -m dossier.seasonality_screener --month 12          # override month
    python -m dossier.seasonality_screener --years 20          # lookback window
    python -m dossier.seasonality_screener --top 10
    python -m dossier.seasonality_screener --json
    python -m dossier.seasonality_screener --quiet             # A+/A only
    python -m dossier.seasonality_screener --no-save

Output: docs/api/seasonality-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"The calendar doesn't care about your thesis. It just remembers what happened." — Sam
"""

import argparse
import calendar
import json
import statistics
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("❌  pip install yfinance")
    sys.exit(1)

try:
    from dossier.utils.validate_api import check_yfinance_history
except ImportError:
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

LOOKBACK_YEARS = 15        # Default years of history to sample
MIN_YEARS = 5              # Minimum completed occurrences required to score
MIN_DAYS_IN_MONTH = 8      # Minimum trading sessions inside a month to count it


# ═══════════════════════════════════════════════════════════════════
# ████  AGGREGATION (pure — unit tested directly)  ████
# ═══════════════════════════════════════════════════════════════════

def _monthly_returns_by_year(hist, month: int, exclude_year: int | None = None,
                              min_days_in_month: int = MIN_DAYS_IN_MONTH) -> list[dict]:
    """
    For each year present in `hist`, compute the pct return from the first
    to the last trading-day close inside the given calendar month.

    Skips `exclude_year` (the in-progress current year) and any year whose
    month has too few sessions to be a reliable sample (early IPO years,
    gaps in the feed). Returns [{"year": int, "return_pct": float}, ...]
    sorted oldest-first.
    """
    if hist is None or hist.empty:
        return []
    df = hist[hist.index.month == month]
    out = []
    for year, group in df.groupby(df.index.year):
        if exclude_year is not None and year == exclude_year:
            continue
        if len(group) < min_days_in_month:
            continue
        first_close = float(group["Close"].iloc[0])
        last_close = float(group["Close"].iloc[-1])
        if first_close <= 0:
            continue
        ret = (last_close / first_close - 1.0) * 100.0
        out.append({"year": int(year), "return_pct": round(ret, 2)})
    out.sort(key=lambda r: r["year"])
    return out


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


def _seasonality_stats(yearly_returns: list[dict], min_years: int = MIN_YEARS) -> dict | None:
    """
    Aggregate per-year returns into direction, win rate, and a 0-100
    conviction score. Returns None when there isn't enough history to
    trust the sample.
    """
    n = len(yearly_returns)
    if n < min_years:
        return None

    returns = [r["return_pct"] for r in yearly_returns]
    avg = statistics.fmean(returns)
    median = statistics.median(returns)
    stdev = statistics.pstdev(returns) if n > 1 else 0.0
    direction = "bullish" if avg >= 0 else "bearish"

    same_dir = sum(1 for r in returns if (r >= 0) == (avg >= 0))
    win_rate = same_dir / n

    win_rate_score = win_rate * 35.0
    magnitude_score = min(30.0, (abs(avg) / 6.0) * 30.0)
    cv = stdev / abs(avg) if abs(avg) > 1e-9 else 999.0
    consistency_score = max(0.0, 20.0 - min(20.0, cv * 6.0))
    recent = returns[-3:]
    recent_same = sum(1 for r in recent if (r >= 0) == (avg >= 0))
    recency_score = (recent_same / len(recent)) * 15.0

    score = round(win_rate_score + magnitude_score + consistency_score + recency_score)
    score = max(0, min(100, score))

    return {
        "years_of_data": n,
        "avg_return_pct": round(avg, 2),
        "median_return_pct": round(median, 2),
        "stdev_pct": round(stdev, 2),
        "win_rate": round(win_rate, 3),
        "direction": direction,
        "score": score,
        "grade": _letter_grade(score),
    }


# ═══════════════════════════════════════════════════════════════════
# ████  DEEP SCAN (yfinance)  ████
# ═══════════════════════════════════════════════════════════════════

def score_seasonality(ticker: str, month: int | None = None,
                       lookback_years: int = LOOKBACK_YEARS) -> dict | None:
    """
    Deep scan a single ticker for its historical edge during the target
    calendar month (current month by default).

    Returns a result dict on success, None if there isn't enough clean
    history to trust the sample.
    """
    try:
        today = date.today()
        target_month = month or today.month
        start = today - timedelta(days=365 * (lookback_years + 1))

        df = yf.Ticker(ticker).history(start=start.isoformat())
        ok, _ = check_yfinance_history(df, ticker, min_rows=200)
        if not ok:
            return None

        yearly = _monthly_returns_by_year(df, target_month, exclude_year=today.year)
        stats = _seasonality_stats(yearly)
        if stats is None:
            return None

        price = float(df["Close"].iloc[-1])
        return {
            "ticker": ticker,
            "price": round(price, 2),
            "month": target_month,
            "month_name": calendar.month_name[target_month],
            "years": yearly,
            **stats,
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


def print_results(results: list[dict], quiet: bool = False) -> None:
    for r in results:
        grade = r["grade"]
        if quiet and grade not in ("A+", "A"):
            continue
        arrow = "▲" if r["direction"] == "bullish" else "▼"
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Score:{r['score']:>3}  {arrow} {r['direction']:<8}  "
            f"Avg:{r['avg_return_pct']:+.1f}%  WinRate:{r['win_rate']*100:.0f}%  "
            f"({r['years_of_data']}y sample)"
        )


def _save_api_output(results: list[dict], month: int) -> None:
    """Write machine-readable JSON to docs/api/seasonality-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "seasonality-screener.json"
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "month": month,
        "month_name": calendar.month_name[month],
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
        description="Seasonality Screener — calendar-month historical edge finder"
    )
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist (default)")
    parser.add_argument("--month", type=int, default=0,
                         help="Target month 1-12 (default: current month)")
    parser.add_argument("--years", type=int, default=LOOKBACK_YEARS,
                         help=f"Lookback window in years (default {LOOKBACK_YEARS})")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    target_month = args.month if args.month else date.today().month

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    else:
        tickers = CORE_WATCHLIST

    print(f"\n📅  Seasonality Screener — {calendar.month_name[target_month]} "
          f"({len(tickers)} tickers, {args.years}y lookback)\n")

    results = []
    for i, ticker in enumerate(tickers):
        r = score_seasonality(ticker, month=target_month, lookback_years=args.years)
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"     {i + 1}/{len(tickers)} scanned — {len(results)} scored so far")
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
    print(f"  📅  SEASONALITY SCREENER RESULTS — {calendar.month_name[target_month]} — {len(results)} scored")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: Score = conviction (win rate + magnitude + consistency + recency), "
          f"not a buy/sell signal by itself")
    print(f"          Direction shows which way the historical edge points — check it before acting\n")

    if not args.no_save:
        _save_api_output(results, target_month)


if __name__ == "__main__":
    main()
