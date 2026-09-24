#!/usr/bin/env python3
"""
Sector Health Monitor — which sectors the algo's picks are actually working in.

`screen_health.py` breaks the validated scan archive down by strategy, grade,
regime, and EMA stack — but never by sector, even though every archived pick
already carries a `sector` field (see `scan_logger.py::_get_ticker_snapshot`).
This fills that gap: rolling win rate + avg forward return per sector, plus a
hot/cold trend (most recent half of the window vs. the half before it) so a
sector that's heating up or fading shows up before it's obvious from the
picks alone.

Usage:
    python dossier/backtesting/sector_health.py          # Print sector dashboard
    python dossier/backtesting/sector_health.py --json    # Output as JSON for API
"""

import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dossier.backtesting.screen_health import _load_validated_entries

SECTOR_HEALTH_API = PROJECT_ROOT / "docs" / "api" / "sector-health.json"

PERIODS = [
    ("fwd_1d", "1d"),
    ("fwd_3d", "3d"),
    ("fwd_5d", "5d"),
    ("fwd_10d", "10d"),
    ("fwd_21d", "21d"),
]

MIN_ENTRIES_PER_SECTOR = 3
MIN_TREND_ENTRIES = 6
HOT_THRESHOLD = 1.5
COLD_THRESHOLD = -1.5


def _is_valid_return(v) -> bool:
    """Guard against NaN forward returns — scan_logger writes plain float('nan')
    for entries yfinance couldn't price, and Python's json module round-trips
    that as a bare `NaN` token that silently poisons every avg() it touches."""
    return v is not None and not (isinstance(v, float) and math.isnan(v))


def _calc_sector(group: list[dict], label: str, window: int) -> dict:
    """Calculate rolling metrics + hot/cold trend for one sector's entries."""
    recent = sorted(group, key=lambda x: x.get("date", ""))[-window:]

    result = {
        "label": label,
        "total_entries": len(group),
        "window_size": len(recent),
        "periods": {},
        "trend": None,
    }

    for field, plabel in PERIODS:
        vals = [e[field] for e in recent if _is_valid_return(e.get(field))]
        if not vals:
            continue

        wr = sum(1 for v in vals if v > 0) / len(vals) * 100
        avg = sum(vals) / len(vals)

        result["periods"][plabel] = {
            "win_rate": round(wr, 1),
            "avg_return": round(avg, 2),
            "best": round(max(vals), 2),
            "worst": round(min(vals), 2),
            "n": len(vals),
        }

    # Trend: split the window's dated 5d returns in half and compare the
    # older half's avg to the newer half's — is this sector heating up or
    # cooling off relative to itself, not just its all-time average.
    dated_5d = sorted(
        [(e.get("date", ""), e["fwd_5d"]) for e in recent if _is_valid_return(e.get("fwd_5d"))],
        key=lambda x: x[0],
    )
    if len(dated_5d) >= MIN_TREND_ENTRIES:
        mid = len(dated_5d) // 2
        older_avg = sum(v for _, v in dated_5d[:mid]) / mid
        newer_avg = sum(v for _, v in dated_5d[mid:]) / (len(dated_5d) - mid)
        delta = round(newer_avg - older_avg, 2)

        if delta > HOT_THRESHOLD:
            direction = "🔥 heating up"
        elif delta < COLD_THRESHOLD:
            direction = "🧊 cooling off"
        else:
            direction = "→ flat"

        result["trend"] = {
            "older_avg_5d": round(older_avg, 2),
            "newer_avg_5d": round(newer_avg, 2),
            "delta": delta,
            "direction": direction,
        }

    return result


def compute_sector_health(entries: list[dict], window: int = 20) -> dict:
    """Compute rolling win rate / avg return per sector, plus a hot/cold ranking."""
    by_sector = defaultdict(list)
    for e in entries:
        sector = e.get("sector") or "Unknown"
        by_sector[sector].append(e)

    health = {
        "generated_at": datetime.now().isoformat(),
        "total_validated": len(entries),
        "window": window,
        "by_sector": {},
        "hottest_sector": None,
        "coldest_sector": None,
    }

    for sector, group in sorted(by_sector.items(), key=lambda x: -len(x[1])):
        if len(group) >= MIN_ENTRIES_PER_SECTOR:
            health["by_sector"][sector] = _calc_sector(group, sector, window)

    # Rank sectors with enough 5d samples by avg 5d return to call out which
    # sector the algo's picks are actually working in right now.
    ranked = sorted(
        (
            (sector, data)
            for sector, data in health["by_sector"].items()
            if data["periods"].get("5d", {}).get("n", 0) >= MIN_ENTRIES_PER_SECTOR
        ),
        key=lambda x: -x[1]["periods"]["5d"]["avg_return"],
    )
    if ranked:
        health["hottest_sector"] = ranked[0][0]
        health["coldest_sector"] = ranked[-1][0]

    return health


def format_sector_health_text(health: dict) -> str:
    """One-line summary for pipeline stage logging."""
    n_sectors = len(health["by_sector"])
    if not n_sectors:
        return "no sectors with enough validated picks yet"
    hottest = health.get("hottest_sector") or "?"
    coldest = health.get("coldest_sector") or "?"
    return f"{n_sectors} sectors tracked — hottest: {hottest}, coldest: {coldest}"


def print_dashboard(health: dict):
    """Pretty-print the sector health dashboard."""
    print(f"\n{'='*80}")
    print(f"  SECTOR HEALTH MONITOR — {health['total_validated']} validated entries")
    print(f"  Window: last {health['window']} picks per sector")
    print(f"  Generated: {health['generated_at']}")
    print(f"{'='*80}")

    if not health["by_sector"]:
        print("\n  No sector has enough validated picks yet.")
        return

    print(f"\n  {'Sector':22s} {'n':>3s}  {'5d WR':>6s}  {'5d Avg':>7s}  {'10d WR':>6s}  Trend")
    for sector, data in health["by_sector"].items():
        p5 = data["periods"].get("5d", {})
        p10 = data["periods"].get("10d", {})
        trend = data["trend"]["direction"] if data["trend"] else ""
        print(f"  {sector:22s} {data['window_size']:3d}  "
              f"{p5.get('win_rate', 0):5.0f}%  "
              f"{p5.get('avg_return', 0):+6.2f}%  "
              f"{p10.get('win_rate', 0):5.0f}%  "
              f"{trend}")

    if health.get("hottest_sector"):
        print(f"\n  🔥 Hottest (best 5d avg): {health['hottest_sector']}")
    if health.get("coldest_sector"):
        print(f"  🧊 Coldest (worst 5d avg): {health['coldest_sector']}")


def write_health_json(window: int = 20) -> dict:
    """
    Compute sector health metrics and write docs/api/sector-health.json.

    Always writes a file, even with zero validated entries, so the API
    endpoint never 404s while the scan archive accumulates enough
    sector-tagged picks.
    """
    entries = _load_validated_entries()
    health = compute_sector_health(entries, window=window)
    SECTOR_HEALTH_API.parent.mkdir(parents=True, exist_ok=True)
    with open(SECTOR_HEALTH_API, "w") as f:
        json.dump(health, f, indent=2)
    return health


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sector Health Monitor")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--window", type=int, default=20, help="Rolling window size per sector")
    args = parser.parse_args()

    if args.json:
        health = write_health_json(window=args.window)
        print(f"✅ Sector health written to {SECTOR_HEALTH_API}")
        return

    entries = _load_validated_entries()
    if not entries:
        print("❌ No validated entries in scan archive yet")
        return

    health = compute_sector_health(entries, window=args.window)
    print_dashboard(health)


if __name__ == "__main__":
    main()
