#!/usr/bin/env python3
"""
⚓ Anchored VWAP Reclaim Screener

Anchors a volume-weighted average price at each ticker's own 52-week low and
asks one question none of the moving-average screens ask: is the price back
above what everyone who has bought since the yearly bottom actually paid,
on average?

Different from sma200_reclaim_screener.py: an SMA is a simple average of
CLOSING PRICES over a fixed window that keeps sliding forward every day. An
anchored VWAP is fixed at a specific event (here, the 52-week low) and
weights every session by how much volume traded, so it tracks the real
average cost basis of the buyers who stepped in off that low — not just
"price crossed a moving line." Below it, the average buyer since the low is
underwater and sits on the sell side the moment they're whole again
(overhead supply). Reclaiming it clears that supply and often marks a
genuine continuation entry, not just a bounce.

Method:
    1. Anchor at the lowest Low in the trailing window (up to 252 sessions).
    2. Build the anchored VWAP forward from that day: cumulative(typical
       price * volume) / cumulative(volume).
    3. Require a FRESH reclaim: price sat below the AVWAP at the start of
       the reclaim streak and has closed at/above it for 1-`--lookback`
       sessions since (not "has been above for months" — that's
       continuation, not a reclaim, and belongs in a different screen).

Scoring (0-100):
    Freshness         (30 pts) — reclaimed today scores highest, decays
                                  across the lookback window
    Distance above    (25 pts) — just cleared (0-3%) beats already extended
    Volume conviction (25 pts) — relative volume on the actual reclaim day
    Trend structure   (20 pts) — price above SMA50 confirms it isn't an
                                  isolated bounce inside a bigger downtrend

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.avwap_reclaim_screener                    # core watchlist
    python -m dossier.avwap_reclaim_screener --tickers NVDA,AAPL
    python -m dossier.avwap_reclaim_screener --lookback 5        # stricter freshness
    python -m dossier.avwap_reclaim_screener --top 10
    python -m dossier.avwap_reclaim_screener --json
    python -m dossier.avwap_reclaim_screener --quiet             # A+/A only
    python -m dossier.avwap_reclaim_screener --no-save

Output: docs/api/avwap-reclaim-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"The moving average doesn't know who paid what. The anchored VWAP does." — Sam
"""

import argparse
import json
import sys
import time
from datetime import datetime
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

ANCHOR_WINDOW = 252         # trailing sessions searched for the 52-week low
DEFAULT_LOOKBACK = 10       # max sessions since the reclaim to still count as "fresh"
MIN_ANCHOR_ROWS = 60        # need at least this many sessions to trust an anchor
SMA_TREND_WINDOW = 50


# ═══════════════════════════════════════════════════════════════════
# ████  AGGREGATION (pure — unit tested directly)  ████
# ═══════════════════════════════════════════════════════════════════

def _anchored_vwap(df, anchor_pos: int) -> list[float]:
    """
    Anchored VWAP from `anchor_pos` (inclusive) to the end of `df`.
    Returns a list aligned to df.iloc[anchor_pos:] — same length, index 0
    is the anchor day itself.
    """
    slice_df = df.iloc[anchor_pos:]
    typical = (slice_df["High"] + slice_df["Low"] + slice_df["Close"]) / 3.0
    vol = slice_df["Volume"].clip(lower=0)
    cum_pv = (typical * vol).cumsum()
    cum_v = vol.cumsum()
    out = []
    for pv, v in zip(cum_pv, cum_v):
        out.append(float(pv / v) if v > 0 else float(typical.iloc[0]))
    return out


def _reclaim_streak(closes: list[float], avwap: list[float], max_lookback: int) -> dict | None:
    """
    Walk backward from the last session counting consecutive closes at/above
    the anchored VWAP. Confirms it's a genuine below-to-above transition
    (not just "the whole visible window happens to be above") and that the
    streak is within `max_lookback` sessions — otherwise it's stale
    continuation, not a fresh reclaim. Returns None when there's no
    qualifying reclaim.
    """
    n = len(closes)
    if n < 2:
        return None

    streak = 0
    for i in range(n - 1, -1, -1):
        if closes[i] >= avwap[i]:
            streak += 1
        else:
            break

    if streak == 0 or streak > max_lookback:
        return None

    boundary = n - streak - 1
    if boundary < 0:
        return None  # streak covers the whole window — can't confirm the dip below
    if closes[boundary] >= avwap[boundary]:
        return None  # no actual crossing at the boundary

    reclaim_idx = n - streak
    return {"streak": streak, "reclaim_idx": reclaim_idx}


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


def _score_reclaim(pct_above: float, streak: int, max_lookback: int,
                    rel_vol_at_reclaim: float, above_sma50: bool | None) -> dict:
    """Pure scoring — no data access, unit tested directly."""
    freshness = max(0.0, 30.0 * (1 - (streak - 1) / max_lookback))

    if 0 <= pct_above <= 3:
        distance = 25.0
    elif 3 < pct_above <= 8:
        distance = 18.0
    elif pct_above > 8:
        distance = 8.0
    else:
        distance = 12.0  # shouldn't happen (qualifying reclaim implies >= 0) but stay safe

    if rel_vol_at_reclaim >= 2.0:
        volume = 25.0
    elif rel_vol_at_reclaim >= 1.5:
        volume = 20.0
    elif rel_vol_at_reclaim >= 1.2:
        volume = 14.0
    elif rel_vol_at_reclaim >= 1.0:
        volume = 8.0
    else:
        volume = 3.0

    if above_sma50 is None:
        trend = 12.0  # not enough history to judge — neutral, don't punish
    else:
        trend = 20.0 if above_sma50 else 8.0

    score = round(freshness + distance + volume + trend)
    score = max(0, min(100, score))
    return {
        "score": score,
        "grade": _letter_grade(score),
        "freshness_pts": round(freshness, 1),
        "distance_pts": distance,
        "volume_pts": volume,
        "trend_pts": trend,
    }


# ═══════════════════════════════════════════════════════════════════
# ████  DEEP SCAN (yfinance)  ████
# ═══════════════════════════════════════════════════════════════════

def score_avwap_reclaim(ticker: str, lookback: int = DEFAULT_LOOKBACK) -> dict | None:
    """
    Deep scan a single ticker for a fresh anchored-VWAP-from-the-52-week-low
    reclaim. Returns a result dict on success, None if there's no clean
    history or no qualifying reclaim (never raises).
    """
    try:
        df = yf.Ticker(ticker).history(period="18mo")
        ok, _ = check_yfinance_history(df, ticker, min_rows=MIN_ANCHOR_ROWS)
        if not ok:
            return None

        window = df.tail(ANCHOR_WINDOW)
        anchor_pos_in_window = int(window["Low"].values.argmin())
        anchor_date = window.index[anchor_pos_in_window]
        anchor_pos = df.index.get_loc(anchor_date)
        if isinstance(anchor_pos, slice):  # pragma: no cover - duplicate index guard
            anchor_pos = anchor_pos.start

        avwap = _anchored_vwap(df, anchor_pos)
        closes = df["Close"].iloc[anchor_pos:].tolist()

        reclaim = _reclaim_streak(closes, avwap, lookback)
        if reclaim is None:
            return None

        idx = reclaim["reclaim_idx"]
        volumes = df["Volume"].iloc[anchor_pos:].tolist()
        lookback_vol_start = max(0, idx - 20)
        prior_vols = volumes[lookback_vol_start:idx]
        avg_prior_vol = (sum(prior_vols) / len(prior_vols)) if prior_vols else 0.0
        reclaim_day_vol = volumes[idx] if idx < len(volumes) else volumes[-1]
        rel_vol_at_reclaim = (reclaim_day_vol / avg_prior_vol) if avg_prior_vol > 0 else 1.0

        price = float(closes[-1])
        avwap_now = float(avwap[-1])
        pct_above = ((price - avwap_now) / avwap_now) * 100.0 if avwap_now > 0 else 0.0

        above_sma50 = None
        if len(df) >= SMA_TREND_WINDOW:
            sma50 = float(df["Close"].tail(SMA_TREND_WINDOW).mean())
            above_sma50 = price >= sma50

        scoring = _score_reclaim(
            pct_above=pct_above, streak=reclaim["streak"], max_lookback=lookback,
            rel_vol_at_reclaim=rel_vol_at_reclaim, above_sma50=above_sma50,
        )

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "avwap": round(avwap_now, 2),
            "pct_above_avwap": round(pct_above, 2),
            "days_since_reclaim": reclaim["streak"],
            "anchor_date": anchor_date.strftime("%Y-%m-%d"),
            "anchor_window_days": len(df) - anchor_pos,
            "rel_vol_at_reclaim": round(rel_vol_at_reclaim, 2),
            "above_sma50": above_sma50,
            **scoring,
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
        print(
            f"  {_gc(grade):>14}  {r['ticker']:<6}  ${r['price']:<8.2f}  "
            f"Score:{r['score']:>3}  AVWAP:${r['avwap']:<8.2f}  "
            f"+{r['pct_above_avwap']:.1f}%  Reclaimed:{r['days_since_reclaim']}d ago  "
            f"RelVol:{r['rel_vol_at_reclaim']}x"
        )


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/avwap-reclaim-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "avwap-reclaim-screener.json"
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
        description="Anchored VWAP Reclaim Screener — 52-week-low AVWAP reclaims"
    )
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist (default)")
    parser.add_argument("--lookback", type=int, default=DEFAULT_LOOKBACK,
                         help=f"Max sessions since reclaim to count as fresh (default {DEFAULT_LOOKBACK})")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--quiet", action="store_true", help="Print A+/A only")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    else:
        tickers = CORE_WATCHLIST

    print(f"\n⚓  Anchored VWAP Reclaim Screener ({len(tickers)} tickers, "
          f"{args.lookback}-session freshness window)\n")

    results = []
    for i, ticker in enumerate(tickers):
        r = score_avwap_reclaim(ticker, lookback=args.lookback)
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
    print(f"  ⚓  AVWAP RECLAIM SCREENER RESULTS — {len(results)} scored")
    grade_summary = "  |  ".join(f"{g}: {n}" for g, n in sorted(grade_counts.items()))
    print(f"  {grade_summary}")
    print(f"{'═' * 100}\n")

    print_results(results, quiet=args.quiet)

    print(f"\n{'─' * 100}")
    print(f"  Legend: AVWAP anchored at the 52-week low — the average price paid by")
    print(f"          everyone who's bought since the yearly bottom. Reclaiming it clears")
    print(f"          overhead supply from that cohort. Fresher + higher volume = stronger.\n")

    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
