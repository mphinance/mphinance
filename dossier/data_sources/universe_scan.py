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


# Columns we want present on EVERY union row regardless of which preset caught it,
# so the merged output carries best-available price/vol/rsi/sector everywhere.
_UNION_EXTRA_COLUMNS = [
    "name", "close", "change", "relative_volume_10d_calc",
    "market_cap_basic", "RSI", "sector",
]


def _run_preset(preset_id: str, limit: int) -> list[dict]:
    """Run a canned PRESET (filter-based screen) by id and return raw rows.

    Replicates `backend.mcp_server.run_preset` by building a ScreenRequest from
    the preset's filters/sort, but AUGMENTS the column set with the fields the
    union wants (RSI, sector, rel-vol, mcap) so every row is comparable no matter
    which screen produced it. Returns [] on any failure — never raises.
    """
    try:
        if _SCANLINE_DIR not in sys.path:
            sys.path.insert(0, _SCANLINE_DIR)
        from backend.pipeline import run_screen
        from backend.models import ScreenRequest, Filter, SortKey
        from backend.presets import PRESETS
    except Exception as e:
        print(f"[universe_scan] scanline unavailable for preset '{preset_id}': {e}")
        return []

    preset = next((p for p in PRESETS if p["id"] == preset_id), None)
    if preset is None:
        print(f"[universe_scan] unknown preset: {preset_id}")
        return []

    # Preset columns first, then the union extras, de-duped, order-preserving.
    cols = list(dict.fromkeys(list(preset.get("columns", [])) + _UNION_EXTRA_COLUMNS))

    try:
        req = ScreenRequest(
            market=preset.get("market", "america"),
            filters=[Filter(**f) for f in preset.get("filters", [])],
            columns=cols,
            match=preset.get("match", "all"),
            sort=[SortKey(**s) for s in preset.get("sort", [])],
            limit=limit,
        )
        resp = run_screen(req)
    except Exception as e:
        print(f"[universe_scan] preset '{preset_id}' failed: {e}")
        return []

    rows = resp.get("rows", []) if isinstance(resp, dict) else getattr(resp, "rows", [])
    return rows or []


def _normalize_preset_row(r: dict) -> dict | None:
    """Map a raw scanline preset row to the union's flat schema (or None)."""
    tkr = (r.get("name") or "").upper()
    if not tkr:
        return None
    return {
        "ticker": tkr,
        "factor_score": r.get("factor_score"),  # presets don't score; stays None
        "price": r.get("close"),
        "change_pct": r.get("change"),
        "rel_vol": r.get("relative_volume_10d_calc"),
        "market_cap": r.get("market_cap_basic"),
        "rsi": r.get("RSI"),
        "sector": r.get("sector"),
    }


def _merge_into(union: dict[str, dict], source: str, row: dict) -> None:
    """Merge one normalized row into the union map, recording its source and
    filling any field that the existing entry is still missing (best-available)."""
    tkr = row["ticker"]
    existing = union.get(tkr)
    if existing is None:
        union[tkr] = {
            "ticker": tkr,
            "sources": [source],
            "factor_score": row.get("factor_score"),
            "price": row.get("price"),
            "change_pct": row.get("change_pct"),
            "rel_vol": row.get("rel_vol"),
            "market_cap": row.get("market_cap"),
            "rsi": row.get("rsi"),
            "sector": row.get("sector"),
        }
        return
    if source not in existing["sources"]:
        existing["sources"].append(source)
    # Backfill any value the prior screen didn't supply.
    for k in ("factor_score", "price", "change_pct", "rel_vol", "market_cap", "rsi", "sector"):
        if existing.get(k) is None and row.get(k) is not None:
            existing[k] = row[k]


def scan_universe_union(limit_per: int = 120) -> list[dict]:
    """Union of three complementary screens into one de-duped candidate set.

    Pure momentum (scan_universe) misses contrarian/reversal/thematic names that
    have NEGATIVE recent perf (RKLB, UAMY, NFLX, ...). To cover the spread the
    friend's nightly list actually spans, we merge THREE screens:
      (a) momentum        — the existing factor-ranked scan_universe()
      (b) unusual_volume  — PRESET: relative volume well above its 10-day average
      (c) rsi_oversold    — PRESET: RSI < 30, mean-reversion / bounce candidates

    Rows are de-duped by ticker; each output row records which screens caught it
    in `sources` (e.g. ["momentum","unusual_volume"]) and carries best-available
    price/change_pct/rel_vol/market_cap/rsi/sector/factor_score. Sorted by number
    of corroborating sources (desc), then factor_score (desc). [] on total failure.
    """
    union: dict[str, dict] = {}

    # (a) momentum — reuse the existing, working factor scan.
    try:
        for r in scan_universe(limit=limit_per):
            _merge_into(union, "momentum", {
                "ticker": r["ticker"],
                "factor_score": r.get("factor_score"),
                "price": r.get("price"),
                "change_pct": r.get("change_pct"),
                "rel_vol": r.get("rel_vol"),
                "market_cap": r.get("market_cap"),
                "rsi": r.get("rsi"),
                "sector": r.get("sector"),
            })
    except Exception as e:  # defensive — scan_universe already swallows its own
        print(f"[universe_scan] momentum leg failed: {e}")

    # (b) + (c) — the two canned presets.
    for source, preset_id in (("unusual_volume", "unusual_volume"), ("rsi_oversold", "rsi_oversold")):
        for raw in _run_preset(preset_id, limit=limit_per):
            norm = _normalize_preset_row(raw)
            if norm is not None:
                _merge_into(union, source, norm)

    out = list(union.values())
    # Multi-source names first (more screens agreeing = stronger), then by factor.
    out.sort(
        key=lambda r: (
            len(r["sources"]),
            r["factor_score"] is not None,
            r["factor_score"] or 0.0,
        ),
        reverse=True,
    )
    return out


def universe_union_tickers(limit_per: int = 120) -> list[str]:
    """Just the ticker symbols from scan_universe_union()."""
    return [r["ticker"] for r in scan_universe_union(limit_per=limit_per)]


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
    print("\nFriend-watchlist names captured by the MOMENTUM-only universe layer:")
    for t in sorted(watch):
        print(f"  {t:6} {'#'+str(ranks[t]) if t in ranks else 'not in top '+str(len(rows))}")

    # ---- UNION of complementary screens (momentum + unusual_volume + rsi_oversold) ----
    print("\n" + "=" * 64)
    union = scan_universe_union(limit_per=120)
    print(f"UNION universe size: {len(union)}")

    multi = [r for r in union if len(r["sources"]) > 1]
    print(f"\nMulti-source names (caught by >1 screen): {len(multi)}")
    print(f"{'TKR':8}{'chg%':>8}{'relVol':>8}{'RSI':>6}  sources")
    for r in multi[:25]:
        chg = f"{r['change_pct']:.1f}" if isinstance(r["change_pct"], (int, float)) else "—"
        rv = f"{r['rel_vol']:.1f}" if isinstance(r["rel_vol"], (int, float)) else "—"
        rsi = f"{r['rsi']:.0f}" if isinstance(r["rsi"], (int, float)) else "—"
        print(f"{r['ticker']:8}{chg:>8}{rv:>8}{rsi:>6}  {'+'.join(r['sources'])}")

    # Which previously-missed names does the UNION now capture, and via which screen?
    by_ticker = {r["ticker"]: r for r in union}
    print("\nFriend-watchlist names now captured by the UNION (via which screen):")
    for t in sorted(watch):
        hit = by_ticker.get(t)
        if hit:
            print(f"  {t:6} via {', '.join(hit['sources'])}")
        else:
            print(f"  {t:6} still missed (not in any of the 3 screens)")
