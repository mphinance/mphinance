#!/usr/bin/env python3
"""
🔀 Institutional Fund Flow Clusters — the day-over-day flip TickerTrace already
sends but nothing reads.

`tickertrace.py::fetch_institutional_data()` returns a static snapshot
(`top_buying` / `top_selling`) that's a longer-window aggregate, already
surfaced in the report and AI narrative. It also returns `recent_changes` —
the raw day-over-day position deltas TickerTrace disclosed across its 40+
tracked ETFs (a ticker one fund just added, trimmed, or fully exited) — and
that field has been fetched, junk-filtered, and capped at 25 since it was
built, but nothing downstream ever reads it.

This is the freshest signal TickerTrace has: a snapshot says "funds have
been buying AAPL," this says "AAPL just got added to fund X's book, and
fund Y trimmed it the same day." Same spirit as insider_cluster_screener.py
gating on 2+ distinct insiders instead of one, or insider_sentiment.py
netting two one-sided screens into a signed read: a single fund nudging a
position is noise, but 2+ distinct funds moving the same ticker the same
direction on the same disclosure day is a much harder signal to fake — and
a fund fully exiting or initiating a position (NEW/REMOVED) is notable on
its own even from one fund, since that's a binary in/out decision rather
than a routine rebalance trim.

Pure post-processing, same pattern as insider_sentiment.py: no network
calls here, it just nets whatever `recent_changes` list generate.py already
fetched via tickertrace.py this run.

Usage (standalone — fetches live TickerTrace data itself):
    python -m dossier.institutional_momentum
    python -m dossier.institutional_momentum --json

Output: docs/api/institutional-momentum.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# A ticker with 2+ distinct funds moving it is a cluster; below that, only a
# full add/exit (NEW/REMOVED) from a single fund is notable enough to surface.
_MIN_CLUSTER_FUNDS = 2
_ENTRY_EXIT_TYPES = {"NEW", "REMOVED"}


def compute_fund_flow_clusters(changes: list[dict], min_cluster_funds: int = _MIN_CLUSTER_FUNDS) -> dict:
    """
    Group TickerTrace `recent_changes` rows by ticker and net them into a
    per-ticker fund-flow read.

    Pure function — never raises on empty/malformed input; missing,
    non-list, or non-dict entries are ignored rather than crashing.

    Args:
        changes: `recent_changes` from tickertrace.fetch_institutional_data(),
            rows shaped like {"fund", "ticker", "name", "sector", "weightDelta",
            "sharesDelta", "type": "NEW"|"REMOVED"|"CHANGED", "isOption",
            "fundCategory", ...}.
        min_cluster_funds: distinct-fund threshold for a "cluster" hit.

    Returns:
        {
          "generated_at": ISO timestamp,
          "total_changes": int,        # raw rows ingested
          "counts": {"accumulating": int, "distributing": int},
          "accumulating": [{ticker, name, sector, fund_count, funds: [...],
                             net_weight_delta, new_count, removed_count,
                             changed_count, notable}, ...],  # strongest first
          "distributing": [...],                              # same shape
        }
        `notable` is True when at least one fund fully added or exited the
        position (type NEW/REMOVED) rather than just trimming/adding size.
    """
    if not isinstance(changes, list):
        changes = []

    by_ticker: dict[str, dict] = {}
    total_changes = 0

    for row in changes:
        if not isinstance(row, dict):
            continue
        ticker = row.get("ticker")
        fund = row.get("fund")
        row_type = row.get("type")
        if not ticker or not fund:
            continue
        try:
            weight_delta = float(row.get("weightDelta") or 0)
        except (TypeError, ValueError):
            weight_delta = 0.0

        total_changes += 1
        entry = by_ticker.setdefault(ticker, {
            "ticker": ticker,
            "name": row.get("name") or ticker,
            "sector": row.get("sector") or "",
            "funds": [],
            "net_weight_delta": 0.0,
            "new_count": 0,
            "removed_count": 0,
            "changed_count": 0,
        })
        entry["funds"].append({
            "fund": fund,
            "type": row_type,
            "weight_delta": round(weight_delta, 4),
            "fund_category": row.get("fundCategory") or "",
        })
        entry["net_weight_delta"] += weight_delta
        if row_type == "NEW":
            entry["new_count"] += 1
        elif row_type == "REMOVED":
            entry["removed_count"] += 1
        else:
            entry["changed_count"] += 1

    accumulating, distributing = [], []
    for entry in by_ticker.values():
        fund_count = len(entry["funds"])
        notable = entry["new_count"] > 0 or entry["removed_count"] > 0
        if fund_count < min_cluster_funds and not notable:
            continue

        entry["fund_count"] = fund_count
        entry["net_weight_delta"] = round(entry["net_weight_delta"], 4)
        entry["notable"] = notable

        if entry["net_weight_delta"] > 0:
            accumulating.append(entry)
        elif entry["net_weight_delta"] < 0:
            distributing.append(entry)
        # net_weight_delta == 0 (funds cancel out): no net directional signal, skip

    accumulating.sort(key=lambda e: (-e["net_weight_delta"], -e["fund_count"]))
    distributing.sort(key=lambda e: (e["net_weight_delta"], -e["fund_count"]))

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_changes": total_changes,
        "counts": {"accumulating": len(accumulating), "distributing": len(distributing)},
        "accumulating": accumulating,
        "distributing": distributing,
    }


def format_institutional_momentum_text(result: dict) -> str:
    """One-line console summary, matching the style of format_breadth_text()."""
    counts = result.get("counts", {})
    return (
        f"🔀 Fund Flow — {counts.get('accumulating', 0)} accumulating, "
        f"{counts.get('distributing', 0)} distributing "
        f"across {result.get('total_changes', 0)} disclosed changes"
    )


def _save_api_output(result: dict) -> None:
    """Write machine-readable JSON to docs/api/institutional-momentum.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "institutional-momentum.json"
    out_path.write_text(json.dumps(result, indent=2))
    total = result["counts"]["accumulating"] + result["counts"]["distributing"]
    print(f"\n  💾  Saved {total} fund-flow-cluster tickers → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Institutional Fund Flow Clusters — nets TickerTrace's day-over-day position changes"
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    from dossier.data_sources.tickertrace import fetch_institutional_data
    institutional = fetch_institutional_data()
    result = compute_fund_flow_clusters(institutional.get("recent_changes", []))

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_institutional_momentum_text(result))

        if result["accumulating"]:
            print("\n  Accumulating (net fund buying):")
            for e in result["accumulating"]:
                flag = " 🆕" if e["notable"] else ""
                print(f"    {e['ticker']:<6}  funds:{e['fund_count']:>2}  "
                      f"net_weight:{e['net_weight_delta']:+.2f}%{flag}")

        if result["distributing"]:
            print("\n  Distributing (net fund selling):")
            for e in result["distributing"]:
                flag = " 🚪" if e["notable"] else ""
                print(f"    {e['ticker']:<6}  funds:{e['fund_count']:>2}  "
                      f"net_weight:{e['net_weight_delta']:+.2f}%{flag}")

    if not args.no_save:
        _save_api_output(result)


if __name__ == "__main__":
    main()
