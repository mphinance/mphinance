#!/usr/bin/env python3
"""
🛡️ Resilience Screener — Who Held Up When SPY Sold Off

Every drawdown reveals who is being held by conviction money. This screen
looks only at the sessions where SPY closed down hard and asks what the stock
did on those same days. A name that shrugs off the market's worst days while
still participating on its good days has a low DOWN-capture and a healthy
UP-capture: the market's own tape is telling you where the sellers aren't.

Different from the other relative screens in the dossier:
  - RS Leadership: the stock/SPY ratio line at a new high (a trend measure)
  - THIS: day-by-day behavior on SPY's down days (a stress-test measure),
    so it can flag a stock whose RS line is flat but who never gets sold

Detection (pure yfinance history, stock aligned to SPY by date):
    Down days  → sessions in the last 120 where SPY fell <= -0.7%
                 (needs >= _MIN_DOWN_DAYS of them, or the sample is noise)
    Down-capture = mean stock return on SPY down days / mean SPY return
    Up-capture   = same on SPY up days (> +0.7%)
    Hold rate    = share of SPY down days where the stock closed green or
                   fell less than half as much as SPY

Scoring (0-100):
    Down-capture (40 pts) — lower is better (negative = rose while SPY fell)
    Hold rate    (25 pts) — frequency of outperforming the selloff
    Up-capture   (20 pts) — still keeps up when the market rallies
    Trend        (15 pts) — price above SMA50, SMA50 above SMA200

Grades: A+ (80+) · A (65-79) · B (50-64) · C (35-49) · D (<35)

Usage:
    python -m dossier.resilience_screener --tickers NVDA,AAPL
    python -m dossier.resilience_screener --watchlist
    python -m dossier.resilience_screener --json --no-save

Output: docs/api/resilience-screener.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

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

PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from dossier.config import CORE_WATCHLIST
except ImportError:
    CORE_WATCHLIST = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD"]

BENCHMARK = "SPY"
_LOOKBACK = 120            # sessions of paired returns examined
_DOWN_THRESH = -0.007      # SPY daily return that counts as a "down day"
_UP_THRESH = 0.007
_MIN_DOWN_DAYS = 6


def _paired_returns(stock: "pd.Series", spy: "pd.Series") -> "pd.DataFrame":
    """Daily returns for stock and SPY on their shared dates, last _LOOKBACK rows."""
    df = pd.concat([stock.pct_change(), spy.pct_change()], axis=1, join="inner").dropna()
    df.columns = ["stock", "spy"]
    return df.tail(_LOOKBACK)


def capture_stats(rets: "pd.DataFrame") -> dict | None:
    """Down/up capture and hold rate; None if too few SPY down days to trust."""
    down = rets[rets["spy"] <= _DOWN_THRESH]
    if len(down) < _MIN_DOWN_DAYS:
        return None
    up = rets[rets["spy"] >= _UP_THRESH]
    down_cap = float(down["stock"].mean() / down["spy"].mean())
    up_cap = float(up["stock"].mean() / up["spy"].mean()) if len(up) else None
    held = (down["stock"] >= 0) | (down["stock"] > down["spy"] * 0.5)
    return {
        "down_days": int(len(down)),
        "down_capture": down_cap,
        "up_capture": up_cap,
        "hold_rate": float(held.mean()),
    }


def _down_score(down_cap: float) -> int:
    if down_cap <= 0.3:
        return 40
    if down_cap <= 0.6:
        return 32
    if down_cap <= 0.9:
        return 22
    if down_cap <= 1.1:
        return 10
    return 0


def _hold_score(hold_rate: float) -> int:
    if hold_rate >= 0.75:
        return 25
    if hold_rate >= 0.6:
        return 19
    if hold_rate >= 0.5:
        return 12
    if hold_rate >= 0.4:
        return 6
    return 0


def _up_score(up_cap: float | None) -> int:
    if up_cap is None:
        return 0
    if up_cap >= 1.2:
        return 20
    if up_cap >= 0.9:
        return 15
    if up_cap >= 0.6:
        return 8
    return 0


def _trend_score(last: float, sma50: float, sma200: float | None) -> int:
    pts = 0
    if last > sma50:
        pts += 9
    if sma200 is not None and sma50 > sma200:
        pts += 6
    return pts


def _grade(total: int) -> str:
    if total >= 80:
        return "A+"
    if total >= 65:
        return "A"
    if total >= 50:
        return "B"
    if total >= 35:
        return "C"
    return "D"


def _fetch_closes(ticker: str) -> "pd.Series | None":
    try:
        hist = yf.Ticker(ticker).history(period="1y", interval="1d")
    except Exception:
        return None
    ok, _ = check_yfinance_history(hist, ticker, min_rows=150)
    if not ok or "Close" not in hist.columns:
        return None
    closes = hist["Close"].dropna()
    closes.index = closes.index.tz_localize(None) if closes.index.tz is not None else closes.index
    return closes


def score_resilience(ticker: str, stock: "pd.Series | None" = None,
                     spy: "pd.Series | None" = None) -> dict | None:
    """Score one ticker; None if data is thin, SPY had too few down days, or the
    stock is in a downtrend / got hit harder than the market. Series may be
    injected (tests, shared SPY fetch); otherwise fetched from yfinance."""
    if stock is None:
        stock = _fetch_closes(ticker)
    if spy is None:
        spy = _fetch_closes(BENCHMARK)
    if stock is None or spy is None or len(stock) < 150:
        return None

    stats = capture_stats(_paired_returns(stock, spy))
    if stats is None or stats["down_capture"] > 0.9:
        return None

    last = float(stock.iloc[-1])
    sma50_v = stock.rolling(50).mean().iloc[-1]
    if pd.isna(sma50_v) or last <= float(sma50_v):
        return None
    sma50 = float(sma50_v)
    sma200_v = stock.rolling(200).mean().iloc[-1]
    sma200 = None if pd.isna(sma200_v) else float(sma200_v)

    s_down = _down_score(stats["down_capture"])
    s_hold = _hold_score(stats["hold_rate"])
    s_up = _up_score(stats["up_capture"])
    s_trend = _trend_score(last, sma50, sma200)
    total = s_down + s_hold + s_up + s_trend

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "down_days": stats["down_days"],
        "down_capture": round(stats["down_capture"], 2),
        "up_capture": None if stats["up_capture"] is None else round(stats["up_capture"], 2),
        "hold_rate_pct": round(stats["hold_rate"] * 100, 0),
        "score": total,
        "grade": _grade(total),
        "score_breakdown": {
            "down_capture": s_down,
            "hold_rate": s_hold,
            "up_capture": s_up,
            "trend": s_trend,
        },
    }


def _save_api_output(results: list[dict]) -> None:
    """Write machine-readable JSON to docs/api/resilience-screener.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "resilience-screener.json"
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Resilience Screener")
    parser.add_argument("--tickers", help="Comma-separated list (e.g. NVDA,AAPL)")
    parser.add_argument("--watchlist", action="store_true", help="Scan core watchlist")
    parser.add_argument("--top", type=int, default=0, help="Limit to top N results")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    else:
        tickers = list(CORE_WATCHLIST)

    spy = _fetch_closes(BENCHMARK)
    if spy is None:
        print("❌  Could not fetch SPY history; aborting.")
        sys.exit(1)

    results = []
    for t in tickers:
        r = score_resilience(t, spy=spy)
        if r:
            results.append(r)
        time.sleep(0.05)
    results.sort(key=lambda r: r["score"], reverse=True)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n🛡️  Resilience — {len(results)} held-up names of {len(tickers)} scanned\n")
    for r in results:
        up = "n/a" if r["up_capture"] is None else f"{r['up_capture']:.2f}"
        print(
            f"  {r['grade']:>3}  {r['ticker']:<6} ${r['price']:<8.2f} "
            f"down-cap {r['down_capture']:.2f} over {r['down_days']} SPY down days, "
            f"held {r['hold_rate_pct']:.0f}%, up-cap {up}  Score:{r['score']}"
        )
    if not args.no_save:
        _save_api_output(results)


if __name__ == "__main__":
    main()
