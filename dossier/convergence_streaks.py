#!/usr/bin/env python3
"""
🔥 Convergence Streaks — tickers that keep clearing the multi-screen bar, day after day

screener_convergence.py answers "who's converging TODAY" — how many independent
screens agree on a ticker in a single snapshot. That's already a strong signal,
but a name that clears 3 screens once and vanishes tomorrow is a different
animal from one that's cleared 3+ screens for four sessions running. The first
is a one-day coincidence; the second is the algo staying convinced while the
tape keeps changing underneath it.

repeat_offenders.py is the closest existing thing, but it counts appearances
across the gold/silver/bronze podium + top signal hits from the archived daily
dossier — it never looks at screener_convergence's own multi-screen agreement
metric. This is that metric's memory: did today's convergence tickers show up
yesterday too, and the day before, and is their screen_count growing or fading
across the streak.

History is persisted date-keyed (dedup-overwrite same day, same pattern as
breadth_index.py / sector_leadership.py) so a streak survives across pipeline
runs instead of resetting every night.

Usage:
    python -m dossier.convergence_streaks              # from persisted history
    python -m dossier.convergence_streaks --min-days 3
    python -m dossier.convergence_streaks --json

Output: docs/api/convergence-streaks.json

© mphinance + Sam the Quant Ghost
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_HISTORY_PATH = PROJECT_ROOT / "landing" / "data" / "convergence_history.json"


def load_history(path) -> list:
    """Load the convergence-history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def snapshot_from_convergence(date: str, convergence: dict) -> dict:
    """Compress a screener_convergence `compute_convergence()` payload down to
    {"date": ..., "tickers": {ticker: screen_count}} for cheap history storage."""
    counts: dict[str, int] = {}
    tickers = convergence.get("tickers") if isinstance(convergence, dict) else None
    if isinstance(tickers, list):
        for t in tickers:
            if isinstance(t, dict) and t.get("ticker"):
                counts[t["ticker"]] = t.get("screen_count", 0)
    return {"date": date, "tickers": counts}


def append_snapshot(history: list, entry: dict) -> list:
    """Return a new history list with ``entry`` added, deduped by ``date``."""
    date = entry.get("date")
    kept = [e for e in history if e.get("date") != date]
    kept.append(entry)
    kept.sort(key=lambda e: e.get("date", ""))
    return kept


def save_history(path, history: list) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(history, indent=2))


def record_snapshot(path, date: str, convergence: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_snapshot(load_history(path), snapshot_from_convergence(date, convergence))
    save_history(path, updated)
    return updated


def compute_streaks(history: list, min_days: int = 2) -> dict:
    """
    Find tickers appearing in the convergence report on consecutive recorded
    days, ending on the most recent date in ``history``. A ticker missing from
    even one day breaks its streak back to zero. Never raises on empty or
    malformed input.
    """
    dated = [
        e for e in history
        if isinstance(e, dict) and e.get("date") and isinstance(e.get("tickers"), dict)
    ]
    dated.sort(key=lambda e: e["date"])

    if not dated:
        return {"as_of": None, "min_days": min_days, "streak_count": 0, "tickers": []}

    seen_tickers: set[str] = set()
    for e in dated:
        seen_tickers |= set(e["tickers"].keys())

    streaks = []
    for ticker in seen_tickers:
        run = []  # [(date, screen_count), ...] most-recent-first while walking back
        for e in reversed(dated):
            count = e["tickers"].get(ticker)
            if count is None:
                break
            run.append((e["date"], count))
        if len(run) < min_days:
            continue
        run.reverse()  # oldest -> newest within the streak
        first_count, last_count = run[0][1], run[-1][1]
        if last_count > first_count:
            trend = "growing"
        elif last_count < first_count:
            trend = "fading"
        else:
            trend = "flat"
        streaks.append({
            "ticker": ticker,
            "streak_days": len(run),
            "first_seen": run[0][0],
            "screen_count": last_count,
            "trend": trend,
        })

    streaks.sort(key=lambda s: (s["streak_days"], s["screen_count"]), reverse=True)

    return {
        "as_of": dated[-1]["date"],
        "min_days": min_days,
        "streak_count": len(streaks),
        "tickers": streaks,
    }


def format_streaks_text(streaks: dict) -> str:
    """One-line console summary, matching the style of format_breadth_text()."""
    if not streaks.get("tickers"):
        return f"🔥 Convergence Streaks — none holding {streaks.get('min_days', 2)}+ days yet"
    top = streaks["tickers"][0]
    return (
        f"🔥 Convergence Streaks — {streaks['streak_count']} tickers holding "
        f"{streaks['min_days']}+ days, led by {top['ticker']} "
        f"({top['streak_days']}d, {top['screen_count']}x screens, {top['trend']})"
    )


def _save_api_output(streaks: dict) -> None:
    """Write machine-readable JSON to docs/api/convergence-streaks.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "convergence-streaks.json"
    out_path.write_text(json.dumps(streaks, indent=2))
    print(f"\n  💾  Saved {streaks['streak_count']} convergence streaks → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convergence Streaks — persistent multi-screen agreement across days"
    )
    parser.add_argument("--history", default=str(DEFAULT_HISTORY_PATH),
                         help="Path to the persisted convergence-history JSON")
    parser.add_argument("--min-days", type=int, default=2,
                         help="Minimum consecutive days a ticker must hold to count (default 2)")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    history = load_history(args.history)
    streaks = compute_streaks(history, min_days=args.min_days)

    if args.json:
        print(json.dumps(streaks, indent=2))
    else:
        print(format_streaks_text(streaks))
        for s in streaks["tickers"]:
            print(f"  {s['ticker']:<6}  {s['streak_days']}d  {s['screen_count']}x screens  {s['trend']}")

    if not args.no_save:
        _save_api_output(streaks)


if __name__ == "__main__":
    main()
