"""
Market Internals feed — combines seven existing "breadth-style" daily signals
(breadth_index, factor_leaderboard, score_dispersion, sector_leadership,
quality_breadth, extension_index, follow_through_index) into one time-series
snapshot for a dashboard page.

Each of those modules already computes a daily reading and appends it to its
own dated history file under landing/data/*_history.json (see
dossier/generate.py Stages 10a-10a7) — but nothing reads them back. Today
they're printed to the pipeline log and folded into narrative prose, then
otherwise stranded: there's no page where Michael can see "is the tape
getting more extended day over day" or "is leadership rotating sectors"
as a trend instead of a one-day snapshot.

This module adds no new computation — it's pure plumbing on top of data
that already exists: read the six history files, trim each to a rolling
window, and write one combined JSON for docs/market-internals.html to
render as sparklines.
"""

from __future__ import annotations

import json
from pathlib import Path

from dossier.breadth_index import classify_breadth, load_history as _load_breadth_history
from dossier.extension_index import load_history as _load_extension_history
from dossier.factor_leaderboard import load_history as _load_factor_history
from dossier.follow_through_index import load_history as _load_follow_through_history
from dossier.quality_breadth import load_history as _load_quality_history
from dossier.score_dispersion import load_history as _load_dispersion_history
from dossier.sector_leadership import load_history as _load_leadership_history

DEFAULT_WINDOW = 20

HISTORY_FILES = {
    "breadth": "breadth_history.json",
    "dispersion": "score_dispersion_history.json",
    "sector_leadership": "sector_leadership_history.json",
    "quality": "quality_breadth_history.json",
    "extension": "extension_index_history.json",
    "factors": "factor_leaderboard_history.json",
    "follow_through": "follow_through_index_history.json",
}


def _trend(history: list, field: str, window: int) -> list[dict]:
    """Last `window` (date, value) points for `field`, oldest first.

    Sorts defensively (history files are already date-sorted by their own
    `record_*` writers, but this doesn't assume that) and skips entries
    missing the field rather than raising.
    """
    rows = sorted(history, key=lambda e: e.get("date", ""))[-window:]
    return [
        {"date": e.get("date"), "value": e[field]}
        for e in rows
        if e.get(field) is not None
    ]


def _latest(history: list) -> dict | None:
    return history[-1] if history else None


def _latest_breadth(history: list) -> dict | None:
    """Same as `_latest`, but merges in state/color/emoji/label.

    Unlike the other five compute_* functions, compute_breadth() doesn't
    bake classify_breadth()'s state dict into its return value (see
    format_breadth_text(), which calls classify_breadth() separately at
    render time) — so it's added here for a uniform "latest" shape.
    """
    entry = _latest(history)
    if entry is None:
        return None
    return {**entry, **classify_breadth(entry.get("breadth_score", 0))}


def build_internals(data_dir, window: int = DEFAULT_WINDOW) -> dict:
    """
    Aggregate the seven breadth-style history files under `data_dir`
    (landing/data) into one dashboard-ready snapshot. Never raises — a
    missing or empty history file just yields an empty trend and a null
    "latest" for that metric, same never-raise contract as the seven
    upstream `compute_*` functions.
    """
    data_dir = Path(data_dir)

    breadth = _load_breadth_history(data_dir / HISTORY_FILES["breadth"])
    dispersion = _load_dispersion_history(data_dir / HISTORY_FILES["dispersion"])
    leadership = _load_leadership_history(data_dir / HISTORY_FILES["sector_leadership"])
    quality = _load_quality_history(data_dir / HISTORY_FILES["quality"])
    extension = _load_extension_history(data_dir / HISTORY_FILES["extension"])
    factors = _load_factor_history(data_dir / HISTORY_FILES["factors"])
    follow_through = _load_follow_through_history(data_dir / HISTORY_FILES["follow_through"])

    return {
        "window": window,
        "breadth": {
            "trend": _trend(breadth, "breadth_score", window),
            "latest": _latest_breadth(breadth),
        },
        "dispersion": {
            "trend": _trend(dispersion, "coefficient_of_variation", window),
            "latest": _latest(dispersion),
        },
        "sector_concentration": {
            "trend": _trend(leadership, "leading_share", window),
            "latest": _latest(leadership),
        },
        "junk_index": {
            "trend": _trend(quality, "leaders_flagged_pct", window),
            "latest": _latest(quality),
        },
        "extension": {
            "trend": _trend(extension, "net_extension", window),
            "latest": _latest(extension),
        },
        "factor_mix": {
            "latest": _latest(factors),
        },
        "follow_through": {
            "trend": _trend(follow_through, "leaders_advance_pct", window),
            "latest": _latest(follow_through),
        },
    }


def write_internals_api(path, data_dir, window: int = DEFAULT_WINDOW) -> dict:
    """Build the combined snapshot and write it to `path` as JSON. Returns the snapshot."""
    snapshot = build_internals(data_dir, window=window)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snapshot, indent=2))
    return snapshot
