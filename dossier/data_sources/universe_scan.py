"""
universe_scan.py — broad, factor-ranked candidate universe via scanline.

WHY: the dossier's native universe (`ghost_alpha_screener._tv_fetch_all_stocks`)
sorts by market cap and deep-scans only the ~200 BIGGEST names, so strong
small/mid-cap momentum names (UMAC, UAMY, QBTS, RKLB, ...) never enter the
candidate set and fall through every downstream screener. This module leverages
scanline's `run_screen` (TradingView universe + direction-aware composite factor
scoring) to produce a size-agnostic, momentum-ranked candidate list that can feed
the deep screeners (Bounce 2.0, triangle, flow).

We IMPORT scanline rather than vendoring it (leverage, don't xerox). Override its
location with the SCANLINE_DIR env var; defaults to /home/mph/scanline.

Never raises — returns [] on any failure so a degraded universe can't sink the run.
"""
from __future__ import annotations

import os
import sys

_SCANLINE_DIR = os.environ.get("SCANLINE_DIR", "/home/mph/scanline")

# Columns we want back; scanline auto-adds whatever the factor needs (Perf.6M etc.)
DEFAULT_COLUMNS = [
    "name", "close", "change", "relative_volume_10d_calc", "market_cap_basic",
    "RSI", "ADX", "sector", "Perf.W", "Perf.1M", "Perf.3M",
]


def _load_scanline():
    """Import scanline's screening core from SCANLINE_DIR. Raises on failure."""
    if _SCANLINE_DIR not in sys.path:
        sys.path.insert(0, _SCANLINE_DIR)
    from backend.pipeline import run_screen
    from backend.models import ScreenRequest, Filter, Factor, FactorWeight, SortKey
    from backend.presets import FACTOR_PRESETS
    return run_screen, ScreenRequest, Filter, Factor, FactorWeight, SortKey, FACTOR_PRESETS


def scan_universe(
    factor: str = "momentum",
    sort_field: str = "Perf.1M",
    limit: int = 300,
    min_mcap: float = 3e8,
    min_volume: float = 300_000,
    min_price: float = 3.0,
) -> list[dict]:
    """Return a factor-ranked candidate universe as a list of dicts.

    The query is SORTED server-side by `sort_field` (default 1-month performance)
    so the candidate pool is momentum-led, not size-led — otherwise TradingView
    hands back the biggest names first and small/mid-cap movers never get pulled.
    The composite `factor` then re-ranks within that pool.

    Each row: ticker, factor_score, price, change_pct, rel_vol, market_cap,
    rsi, adx, sector, perf_1m. [] on any failure.
    """
    try:
        run_screen, ScreenRequest, Filter, Factor, FactorWeight, SortKey, FACTOR_PRESETS = _load_scanline()
    except Exception as e:  # scanline missing / import error
        print(f"[universe_scan] scanline unavailable: {e}")
        return []

    fp = next((f for f in FACTOR_PRESETS if f["id"] == factor), None)
    weights = [FactorWeight(**w) for w in fp["weights"]] if fp else []

    req = ScreenRequest(
        market="america",
        columns=DEFAULT_COLUMNS,
        filters=[
            Filter(field="market_cap_basic", op=">", value=min_mcap),
            Filter(field="volume", op=">", value=min_volume),
            Filter(field="close", op=">", value=min_price),
        ],
        match="all",
        factor=Factor(weights=weights) if weights else None,
        sort=[SortKey(field=sort_field, dir="desc")],
        limit=limit,
    )

    try:
        resp = run_screen(req)
    except Exception as e:
        print(f"[universe_scan] run_screen failed: {e}")
        return []

    rows = resp.get("rows", []) if isinstance(resp, dict) else getattr(resp, "rows", [])
    out: list[dict] = []
    for r in rows:
        tkr = (r.get("name") or "").upper()
        if not tkr:
            continue
        out.append({
            "ticker": tkr,
            "factor_score": r.get("factor_score"),
            "price": r.get("close"),
            "change_pct": r.get("change"),
            "rel_vol": r.get("relative_volume_10d_calc"),
            "market_cap": r.get("market_cap_basic"),
            "rsi": r.get("RSI"),
            "adx": r.get("ADX"),
            "sector": r.get("sector"),
            "perf_1m": r.get("Perf.1M"),
        })
    # The server-side sort (sort_field) shaped the POOL; re-rank the returned set
    # by composite factor_score so the output is best-first.
    out.sort(key=lambda r: (r["factor_score"] is not None, r["factor_score"] or 0.0), reverse=True)
    return out


def universe_tickers(**kwargs) -> list[str]:
    """Just the ticker symbols from scan_universe()."""
    return [r["ticker"] for r in scan_universe(**kwargs)]


if __name__ == "__main__":
    rows = scan_universe(limit=200)
    print(f"universe size: {len(rows)}\n")
    print(f"{'#':>3} {'TKR':6}{'factor':>8}{'chg%':>7}{'relVol':>7}{'mcap':>9}{'RSI':>5}  sector")
    for i, r in enumerate(rows[:20]):
        mc = r["market_cap"]
        mcs = f"{mc/1e9:.1f}B" if isinstance(mc, (int, float)) else "—"
        fs = f"{r['factor_score']:.2f}" if isinstance(r["factor_score"], (int, float)) else "—"
        print(f"{i+1:>3} {r['ticker']:6}{fs:>8}{r['change_pct']!s:>7}{r['rel_vol']!s:>7}{mcs:>9}{r['rsi']!s:>5}  {r['sector']}")

    # Validation: do the small/mid-cap names the native funnel MISSED now show up?
    watch = {"NFLX", "UMAC", "UAMY", "HOOD", "QBTS", "WDC", "AMD", "RKLB"}
    ranks = {r["ticker"]: i + 1 for i, r in enumerate(rows) if r["ticker"] in watch}
    print("\nFriend-watchlist names now captured by the universe layer:")
    for t in sorted(watch):
        print(f"  {t:6} {'#'+str(ranks[t]) if t in ranks else 'not in top '+str(len(rows))}")
