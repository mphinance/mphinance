#!/usr/bin/env python3
"""
check_data_freshness.py — flags docs/api/*.json outputs that look stale.

The dossier pipeline overwrites ~75 JSON files in docs/api/ every weekday
morning. If a pipeline stage silently fails partway through (a swallowed
exception, an API outage, a hung upstream fetch), the files it owns just
stop updating and nothing surfaces that until a reader notices the report
looks wrong. This is a standalone diagnostic CLI, not wired into the
pipeline — run it manually or from cron to catch that class of failure.

Usage:
    python scripts/check_data_freshness.py                # human-readable report
    python scripts/check_data_freshness.py --json-out FILE  # also write a JSON summary
    python scripts/check_data_freshness.py --grace-hours 12 --run-hour-utc 14

Exit code is 1 if any file with a usable timestamp is stale, else 0.
Dated archive snapshots (e.g. dossier-2026-04-07.json) are intentionally
excluded — they are append-only history, not "current state" and are
expected to look old.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = PROJECT_ROOT / "docs" / "api"

# Files named like "dossier-2026-04-07.json" are dated archive snapshots,
# not live state — they should stay "old" and would otherwise be false alarms.
ARCHIVE_NAME_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

TIMESTAMP_KEYS = ("generated_at", "generatedAt", "scan_date", "as_of", "asOf",
                  "last_updated", "timestamp", "date")


def parse_timestamp(raw) -> datetime | None:
    """Parse the various timestamp shapes seen across dossier JSON outputs."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    for candidate in (text, text.replace(" ", "T", 1)):
        try:
            dt = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return None


def extract_timestamp(data) -> datetime | None:
    """Look for a timestamp at the top level, then inside a nested 'meta' dict."""
    if not isinstance(data, dict):
        return None
    for key in TIMESTAMP_KEYS:
        ts = parse_timestamp(data.get(key))
        if ts:
            return ts
    meta = data.get("meta")
    if isinstance(meta, dict):
        for key in TIMESTAMP_KEYS:
            ts = parse_timestamp(meta.get(key))
            if ts:
                return ts
    return None


def last_expected_run(now: datetime, run_hour_utc: int = 14) -> datetime:
    """The most recent weekday run the pipeline should have already produced.

    The dossier runs weekday mornings (~14:00 UTC based on observed
    generated_at values). Weekends don't count as missed runs.
    """
    day = now
    while day.weekday() >= 5:  # Saturday=5, Sunday=6
        day -= timedelta(days=1)
    candidate = day.replace(hour=run_hour_utc, minute=0, second=0, microsecond=0)
    if candidate > now:
        day -= timedelta(days=1)
        while day.weekday() >= 5:
            day -= timedelta(days=1)
        candidate = day.replace(hour=run_hour_utc, minute=0, second=0, microsecond=0)
    return candidate


def classify(ts: datetime | None, now: datetime, grace_hours: float,
             run_hour_utc: int) -> str:
    if ts is None:
        return "NO_TIMESTAMP"
    threshold = last_expected_run(now, run_hour_utc) - timedelta(hours=grace_hours)
    return "STALE" if ts < threshold else "OK"


def scan_directory(directory: Path, now: datetime, grace_hours: float,
                    run_hour_utc: int) -> list[dict]:
    results = []
    for path in sorted(directory.glob("*.json")):
        if ARCHIVE_NAME_RE.search(path.stem):
            results.append({"file": path.name, "status": "ARCHIVE", "timestamp": None})
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as e:
            results.append({"file": path.name, "status": "PARSE_ERROR",
                             "timestamp": None, "error": str(e)})
            continue
        ts = extract_timestamp(data)
        status = classify(ts, now, grace_hours, run_hour_utc)
        age_hours = round((now - ts).total_seconds() / 3600, 1) if ts else None
        results.append({
            "file": path.name,
            "status": status,
            "timestamp": ts.isoformat() if ts else None,
            "age_hours": age_hours,
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR,
                         help="directory of JSON files to check (default: docs/api)")
    parser.add_argument("--grace-hours", type=float, default=6.0,
                         help="hours of slack past the expected run time before flagging stale")
    parser.add_argument("--run-hour-utc", type=int, default=14,
                         help="hour (UTC) the pipeline is expected to have run by")
    parser.add_argument("--json-out", type=Path, default=None,
                         help="optional path to write a JSON summary")
    args = parser.parse_args()

    if not args.dir.is_dir():
        print(f"error: {args.dir} is not a directory", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    results = scan_directory(args.dir, now, args.grace_hours, args.run_hour_utc)

    stale = [r for r in results if r["status"] == "STALE"]
    errors = [r for r in results if r["status"] == "PARSE_ERROR"]
    no_ts = [r for r in results if r["status"] == "NO_TIMESTAMP"]
    ok = [r for r in results if r["status"] == "OK"]

    print(f"Checked {len(results)} files in {args.dir} (as of {now.isoformat()})")
    print(f"  OK: {len(ok)}  STALE: {len(stale)}  NO_TIMESTAMP: {len(no_ts)}  "
          f"PARSE_ERROR: {len(errors)}")

    if stale:
        print("\nSTALE:")
        for r in stale:
            print(f"  {r['file']}: last updated {r['timestamp']} "
                  f"({r['age_hours']}h ago)")
    if errors:
        print("\nPARSE_ERROR:")
        for r in errors:
            print(f"  {r['file']}: {r['error']}")

    if args.json_out:
        args.json_out.write_text(json.dumps({
            "checked_at": now.isoformat(),
            "directory": str(args.dir),
            "results": results,
        }, indent=2))
        print(f"\nWrote summary to {args.json_out}")

    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
