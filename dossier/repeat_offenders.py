#!/usr/bin/env python3
"""
🔁 Repeat Offenders — tickers the algo keeps flagging night after night

Every archived `docs/api/dossier-YYYY-MM-DD.json` already records that day's
gold/silver/bronze picks and top signal hits. No single day's list says much
on its own, but a ticker that keeps reappearing across a trailing window is a
different story: the algo isn't reacting to one day's noise, it's staying
convinced across changing tape. That's a name worth a second look.

This module is pure post-processing over the existing daily archive — no
network calls, no re-scanning. It just re-reads the JSON files `generate.py`
already writes and counts.

Usage:
    python -m dossier.repeat_offenders                    # last 20 archived days
    python -m dossier.repeat_offenders --days 10           # shorter window
    python -m dossier.repeat_offenders --min-appearances 3 # stricter filter
    python -m dossier.repeat_offenders --json               # machine output

Output: docs/api/repeat-offenders.json (served via GitHub Pages)

© mphinance + Sam the Quant Ghost
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_PICK_TIERS = ("gold", "silver", "bronze")


def compute_repeat_offenders(daily_entries: list[dict], min_appearances: int = 2) -> dict:
    """
    Find tickers that recur across 2+ distinct archived days and rank them.

    Pure function — never raises on empty/malformed input; a day with no
    hits or a malformed entry just contributes nothing.

    Args:
        daily_entries: [{"date": "YYYY-MM-DD", "hits": [{"ticker": str, "source": str}, ...]}, ...]
        min_appearances: minimum distinct days a ticker must appear on to be kept

    Returns:
        {
          "generated_at": ISO timestamp,
          "window_days": number of daily entries considered,
          "min_appearances": int,
          "repeat_count": int,
          "tickers": [
            {
              "ticker": str,
              "appearances": int,        # distinct days seen
              "first_seen": "YYYY-MM-DD",
              "last_seen": "YYYY-MM-DD",
              "sources": ["gold", "signal:Ghost Alpha V2", ...],
            },
            ...
          ],
        }
    """
    by_ticker: dict[str, dict] = {}
    window_days = 0

    if isinstance(daily_entries, list):
        for day in daily_entries:
            if not isinstance(day, dict):
                continue
            date = day.get("date")
            hits = day.get("hits")
            if not date or not isinstance(hits, list):
                continue
            window_days += 1

            seen_today: dict[str, set] = {}
            for hit in hits:
                if not isinstance(hit, dict):
                    continue
                ticker = hit.get("ticker")
                source = hit.get("source")
                if not ticker or not source:
                    continue
                seen_today.setdefault(ticker, set()).add(source)

            for ticker, sources in seen_today.items():
                entry = by_ticker.setdefault(ticker, {
                    "ticker": ticker,
                    "dates": [],
                    "sources": set(),
                })
                entry["dates"].append(date)
                entry["sources"] |= sources

    repeats = []
    for ticker, entry in by_ticker.items():
        dates = sorted(entry["dates"])
        appearances = len(dates)
        if appearances < min_appearances:
            continue
        repeats.append({
            "ticker": ticker,
            "appearances": appearances,
            "first_seen": dates[0],
            "last_seen": dates[-1],
            "sources": sorted(entry["sources"]),
        })

    repeats.sort(key=lambda e: (e["appearances"], e["last_seen"]), reverse=True)

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "window_days": window_days,
        "min_appearances": min_appearances,
        "repeat_count": len(repeats),
        "tickers": repeats,
    }


def _hits_from_dossier(payload: dict) -> list[dict]:
    """Extract {"ticker", "source"} hits from one archived dossier's picks + top signals."""
    hits: list[dict] = []
    picks = payload.get("picks")
    if isinstance(picks, dict):
        for tier in _PICK_TIERS:
            pick = picks.get(tier)
            if isinstance(pick, dict) and pick.get("ticker"):
                hits.append({"ticker": pick["ticker"], "source": tier})

    signals = payload.get("signals")
    if isinstance(signals, dict):
        top_5 = signals.get("top_5")
        if isinstance(top_5, list):
            for s in top_5:
                if not isinstance(s, dict):
                    continue
                ticker = s.get("symbol") or s.get("ticker")
                strategy = s.get("strategy", "signal")
                if ticker:
                    hits.append({"ticker": ticker, "source": f"signal:{strategy}"})

    return hits


def _load_daily_archive(days: int, archive_dir: Path) -> list[dict]:
    """Load the most recent `days` archived dossier files as daily hit records."""
    if not archive_dir.exists():
        return []
    files = sorted(archive_dir.glob("dossier-????-??-??.json"))[-days:]

    entries = []
    for path in files:
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict):
            continue
        date = payload.get("meta", {}).get("date") if isinstance(payload.get("meta"), dict) else None
        date = date or path.stem.removeprefix("dossier-")
        entries.append({"date": date, "hits": _hits_from_dossier(payload)})

    return entries


def _save_api_output(result: dict) -> None:
    """Write machine-readable JSON to docs/api/repeat-offenders.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "repeat-offenders.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\n  💾  Saved {result['repeat_count']} repeat offenders → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Repeat Offenders — tickers the algo keeps flagging across the trailing window"
    )
    parser.add_argument("--days", type=int, default=20, help="Trailing archived days to consider (default: 20)")
    parser.add_argument("--min-appearances", type=int, default=2, help="Minimum distinct days to qualify (default: 2)")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    daily_entries = _load_daily_archive(args.days, PROJECT_ROOT / "docs" / "api")
    result = compute_repeat_offenders(daily_entries, min_appearances=args.min_appearances)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"\n🔁  Repeat Offenders — {result['repeat_count']} tickers across "
            f"{result['window_days']} archived days\n"
        )
        for e in result["tickers"]:
            sources = ", ".join(e["sources"])
            print(f"  {e['ticker']:<6}  {e['appearances']}x  {e['first_seen']} → {e['last_seen']}  [{sources}]")

    if not args.no_save:
        _save_api_output(result)


if __name__ == "__main__":
    main()
