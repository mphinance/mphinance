"""
Sector Relative Strength — Ranks S&P 500 sectors vs SPY.

Computes excess-return (RS) for each sector ETF vs SPY over three lookback
windows (1w, 1m, 3m) and produces a composite rank. Used by the dossier to
surface rotation context — "Technology leading, Energy rolling over" — that
feeds Michael's writing and the pipeline's daily summary.

Usage:
    from dossier.data_sources.sector_rs import fetch_sector_rs
    data = fetch_sector_rs()   # uses config SECTOR_ETFS vs SPY

Returns dict with keys:
  ranked     — list[dict] sorted strongest → weakest composite RS
  leaders    — top 3 sectors (outperforming SPY)
  laggards   — bottom 3 sectors (weakest RS)
  generated_at — ISO UTC timestamp
"""

from __future__ import annotations

from datetime import datetime, timezone

import yfinance as yf

from dossier.config import SECTOR_ETFS
from dossier.utils.retry import retry
from dossier.utils.validate_api import check_yfinance_history

# Sector ETF → human-readable name
_SECTOR_NAMES: dict[str, str] = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Health Care",
    "XLI": "Industrials",
    "XLC": "Comm Services",
    "XLRE": "Real Estate",
    "XLP": "Consumer Staples",
    "XLU": "Utilities",
    "XLB": "Materials",
    "XLY": "Consumer Discret.",
}

# Lookback windows: label → number of trading bars
_WINDOWS: dict[str, int] = {"1w": 5, "1m": 21, "3m": 63}

# Composite RS weights (sum to 1.0; recalibrated per available windows)
_WEIGHTS: dict[str, float] = {"1w": 0.25, "1m": 0.35, "3m": 0.40}


def _pct_return(closes: "pd.Series", n_bars: int) -> float | None:
    """% change from n_bars ago to the most-recent close. None if not enough data."""
    if closes is None or len(closes) < n_bars + 1:
        return None
    entry = float(closes.iloc[-(n_bars + 1)])
    if entry == 0:
        return None
    return round((float(closes.iloc[-1]) - entry) / entry * 100, 2)


def _excess_return(sector_ret: float | None, bench_ret: float | None) -> float | None:
    """RS = sector return − benchmark return (percentage-point excess)."""
    if sector_ret is None or bench_ret is None:
        return None
    return round(sector_ret - bench_ret, 2)


def _rotation_signal(rs_1w: float | None, rs_3m: float | None) -> str:
    """
    Classify recent momentum vs longer-term RS:
      reversing_up   — was lagging 3m, now leading 1w
      reversing_down — was leading 3m, now lagging 1w
      accelerating   — already leading and 1w RS outpaces 3m RS by >1.5pp
      decelerating   — already leading/lagging but 1w RS lags 3m RS by >1.5pp
      stable         — little change between 1w and 3m RS
      unknown        — insufficient data
    """
    if rs_1w is None or rs_3m is None:
        return "unknown"
    if rs_1w > 0 and rs_3m <= 0:
        return "reversing_up"
    if rs_1w <= 0 and rs_3m > 0:
        return "reversing_down"
    if rs_1w - rs_3m > 1.5:
        return "accelerating"
    if rs_3m - rs_1w > 1.5:
        return "decelerating"
    return "stable"


def _composite_rs(rs: dict[str, float | None]) -> float:
    """Weighted composite RS score across available windows."""
    total_weight = sum(_WEIGHTS[lbl] for lbl in _WINDOWS if rs.get(lbl) is not None)
    if total_weight == 0:
        return 0.0
    weighted = sum(
        rs[lbl] * _WEIGHTS[lbl]
        for lbl in _WINDOWS
        if rs.get(lbl) is not None
    )
    return round(weighted / total_weight, 2)


@retry(max_retries=2, initial_delay=1.0)
def _fetch_closes(ticker: str) -> "pd.Series":
    """Fetch ~3 months of daily closes for one ticker, with validation."""
    hist = yf.Ticker(ticker).history(period="3mo")
    ok, reason = check_yfinance_history(hist, ticker, min_rows=10)
    if not ok:
        raise ValueError(reason)
    return hist["Close"]


def fetch_sector_rs(
    sector_etfs: list[str] | None = None,
    benchmark: str = "SPY",
) -> dict:
    """
    Rank S&P 500 sectors by relative strength vs the benchmark.

    Args:
        sector_etfs: ETF tickers to scan (defaults to config.SECTOR_ETFS)
        benchmark:   comparison ticker (default "SPY")

    Returns empty dict on benchmark fetch failure so the pipeline stays up.
    """
    etfs = sector_etfs if sector_etfs is not None else SECTOR_ETFS

    # Benchmark closes — everything falls through if this fails
    try:
        bench_closes = _fetch_closes(benchmark)
    except Exception as exc:
        print(f"    [WARN] Sector RS: could not fetch {benchmark}: {exc}")
        return {}

    bench_rets = {lbl: _pct_return(bench_closes, n) for lbl, n in _WINDOWS.items()}

    ranked: list[dict] = []
    for etf in etfs:
        try:
            closes = _fetch_closes(etf)
        except Exception as exc:
            print(f"    [WARN] Sector RS: skipping {etf}: {exc}")
            continue

        sector_rets = {lbl: _pct_return(closes, n) for lbl, n in _WINDOWS.items()}
        rs = {
            lbl: _excess_return(sector_rets[lbl], bench_rets[lbl])
            for lbl in _WINDOWS
        }
        comp = _composite_rs(rs)

        ranked.append({
            "ticker": etf,
            "name": _SECTOR_NAMES.get(etf, etf),
            "rs": rs,
            "abs_ret": sector_rets,
            "composite_rs": comp,
            "rotation": _rotation_signal(rs.get("1w"), rs.get("3m")),
        })

    # Strongest composite RS first
    ranked.sort(key=lambda x: x["composite_rs"], reverse=True)
    for i, row in enumerate(ranked):
        row["rank"] = i + 1

    leaders = ranked[:3]
    laggards = list(reversed(ranked[-3:])) if len(ranked) >= 3 else list(reversed(ranked))

    return {
        "ranked": ranked,
        "leaders": leaders,
        "laggards": laggards,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
