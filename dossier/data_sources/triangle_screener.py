"""Triangle-breakout screener for the Daily Review dossier.

Ported from TD Pro's `backend/src/scripts/run_triangle_detection.py` CLI, which
wraps the pure-pandas engine in `triangle_logic.py` (copied verbatim alongside
this file). Detects descending-triangle patterns — confirmed breakouts
("TD Triangle") and forming structures ("TD Triangle Forming") — over ~2y of
daily OHLCV.

Shape matches the other dossier screeners: per-ticker `scan_triangle(t) -> dict|None`
plus batch `generate_triangles(tickers, max_results) -> list[dict]`.

HARD RULE: nothing in here ever raises. Every failure path degrades to
None / [] so a single bad ticker can never break the pipeline.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

try:
    import pandas as pd  # noqa: F401  (used indirectly; kept for parity / future use)
    import yfinance as yf
except Exception:  # pragma: no cover - degrade if deps missing
    yf = None  # type: ignore[assignment]

try:
    from .triangle_logic import BreakoutConfig, compute_breakout_snapshot
except Exception:  # pragma: no cover - allow running as a loose script
    from triangle_logic import BreakoutConfig, compute_breakout_snapshot  # type: ignore


# Match the TD Pro CLI exactly.
HISTORY_PERIOD = "2y"
MIN_HISTORY_BARS = 300
# Cliff filter: a descending triangle's resistance is a gently-declining ceiling.
# When the engine anchors the upper line on a spike high it traces a crash instead
# (cuts through candles). Reject those. Calibrated in the CLI between clean
# triangles (~0.16%/bar) and cliffs (~0.98%/bar).
MAX_UPPER_SLOPE_PCT_PER_BAR = 0.45

# Build the config once: deeper history gate than the BreakoutConfig default (100).
_CFG = replace(BreakoutConfig(), required_history_bars_qualified=MIN_HISTORY_BARS)


def _num(value: Any) -> float | None:
    """Coerce numpy / NaN / None to a JSON-safe float, or None."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f


def scan_triangle(ticker: str) -> dict[str, Any] | None:
    """Run the triangle engine on one ticker's 2y daily bars.

    Returns a screener-shaped dict, or None when there's no qualifying pattern
    (or anything goes wrong — this function never raises).
    """
    if yf is None or not ticker:
        return None

    try:
        symbol = str(ticker).strip().upper()
        if not symbol:
            return None

        # Fetch 2y daily OHLCV.
        try:
            raw = yf.Ticker(symbol).history(period=HISTORY_PERIOD, auto_adjust=True)
        except Exception:
            return None
        if raw is None or raw.empty:
            return None

        # Lowercase columns to date/open/high/low/close/volume.
        hist = raw.reset_index()
        hist.columns = [str(c).lower() for c in hist.columns]
        if "date" not in hist.columns:
            # yfinance index is usually 'Date'; fall back to first column.
            hist = hist.rename(columns={hist.columns[0]: "date"})

        required = {"date", "open", "high", "low", "close", "volume"}
        if not required.issubset(set(hist.columns)):
            return None

        if len(hist) < MIN_HISTORY_BARS:
            return None

        snap = compute_breakout_snapshot(hist, symbol=symbol, cfg=_CFG)
        if not snap or snap.get("Error"):
            return None

        # Gate (a): liquidity / price / history quality.
        if not snap.get("Universe Quality OK"):
            return None

        # Gate (b): confirmed beats forming; neither -> no signal.
        is_confirmed = int(snap.get("TD Triangle", 0) or 0) == 1
        is_forming = int(snap.get("TD Triangle Forming", 0) or 0) == 1
        if is_confirmed:
            signal_type = "triangle_breakout"
        elif is_forming:
            signal_type = "triangle_forming"
        else:
            return None

        # Gate (c): cliff filter on the upper-line slope.
        upper_slope = _num(snap.get("TD Upper Line Slope"))
        ref_price = _num(snap.get("Last Close"))
        if upper_slope is not None and ref_price and ref_price > 0:
            if abs(upper_slope) / ref_price * 100.0 > MAX_UPPER_SLOPE_PCT_PER_BAR:
                return None

        # Strength from the 0-100 TD Triangle Score.
        score = _num(snap.get("TD Triangle Score")) or 0.0
        if score >= 70:
            strength = "strong"
        elif score >= 50:
            strength = "moderate"
        else:
            strength = "weak"

        last_close = _num(snap.get("Last Close"))

        return {
            "ticker": symbol,
            "signal_type": signal_type,
            "pattern": "confirmed" if is_confirmed else "forming",
            "signal_strength": strength,
            "composite_score": _num(snap.get("Triangle Composite Score")),
            "triangle_score": _num(snap.get("TD Triangle Score")),
            "compression_ratio": _num(snap.get("TD Compression Ratio")),
            "descending_drop_pct": _num(snap.get("TD Descending Drop %")),
            "vertex_gap_pct": _num(snap.get("TD Vertex Gap %")),
            "bars_to_vertex": _num(snap.get("TD Bars To Vertex")),
            "breakout_pct": _num(snap.get("TD Breakout %")),
            "upper_line_price": _num(snap.get("TD Upper Line Price")),
            "upper_line_slope": _num(snap.get("TD Upper Line Slope")),
            "support_price": _num(snap.get("TD Support Price")),
            "support_touch_count": _num(snap.get("TD Support Touch Count")),
            "anchor_type": snap.get("TD Anchor Type"),
            "trend_stage": _num(snap.get("Stage")),
            "price": round(last_close, 4) if last_close is not None else None,
        }
    except Exception:
        # Absolute backstop: never propagate.
        return None


def generate_triangles(tickers: list[str], max_results: int = 10) -> list[dict[str, Any]]:
    """Scan a list of tickers, return up to `max_results` triangle signals.

    Confirmed breakouts first, then forming; within each, higher triangle_score
    first. Never raises — bad tickers are skipped.
    """
    if not tickers:
        return []

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ticker in tickers:
        try:
            symbol = str(ticker).strip().upper()
        except Exception:
            continue
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        signal = scan_triangle(symbol)
        if signal:
            results.append(signal)

    # Rank: confirmed (0) before forming (1), then by triangle_score desc.
    def _sort_key(item: dict[str, Any]) -> tuple[int, float]:
        pattern_rank = 0 if item.get("pattern") == "confirmed" else 1
        score = item.get("triangle_score") or 0.0
        return (pattern_rank, -float(score))

    results.sort(key=_sort_key)

    try:
        limit = int(max_results)
    except (TypeError, ValueError):
        limit = 10
    if limit < 0:
        limit = 0
    return results[:limit]


if __name__ == "__main__":
    import json

    sample = ["NVDA", "AMD", "TSLA", "PLTR", "SOFI"]
    print(f"Scanning {len(sample)} tickers for triangle setups: {', '.join(sample)}")
    found = generate_triangles(sample, max_results=10)
    print(f"\n{len(found)} signal(s) found:\n")
    if not found:
        print("  (no qualifying triangle patterns)")
    for sig in found:
        print(json.dumps(sig, indent=2, default=str))
        print()
