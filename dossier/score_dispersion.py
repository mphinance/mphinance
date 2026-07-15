"""
Score Dispersion Index — is today's leadership broad or a lone standout?

breadth_index.py answers "how many names are participating" and
factor_leaderboard.py answers "which scoring factor is driving it," but
neither looks at the *shape* of the score distribution itself. Two days can
have identical breadth and the same top factor while looking completely
different underneath: one where Gold pulls miles ahead of a mediocre pack
(a lone-wolf breakout), and one where the whole scored universe is bunched
up near the top (a broad, healthy rally) or bunched up near the bottom
(nothing is working, no real leadership anywhere).

This aggregates momentum_picks.py's `all_ranked` scored list into that
distribution shape: mean/median/stdev of score, the gap between the top
score and the median, and the coefficient of variation (stdev / mean) as a
scale-invariant measure of how spread out the pack is relative to how
strong it is on average.

History is persisted date-keyed (dedup-overwrite same day), same pattern as
breadth_index.py / factor_leaderboard.py, so the dossier can report the
dispersion regime widening or narrowing over N sessions instead of just
today's snapshot.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

# 3-color HUD thresholds (see AGENTS.md / report/template.html):
#   green #00ff41 = broad strength   amber #f0b400 = concentrated / lone standouts
#   red   #e53935 = flat tape, no real leadership
_FLAT_MEAN_FLOOR = 20.0
_CONCENTRATED_COV = 0.45


def classify_dispersion(mean_score: float, coefficient_of_variation: float) -> dict:
    """Map (mean_score, coefficient_of_variation) to a state dict (state/color/emoji/label)."""
    if mean_score < _FLAT_MEAN_FLOOR:
        return {"state": "flat", "color": "#e53935", "emoji": "😴", "label": "Flat Tape — No Leadership"}
    if coefficient_of_variation >= _CONCENTRATED_COV:
        return {"state": "concentrated", "color": "#f0b400", "emoji": "🎯", "label": "Concentrated — Few Standouts"}
    return {"state": "broad", "color": "#00ff41", "emoji": "🌊", "label": "Broad Strength"}


def compute_dispersion(all_ranked: list[dict]) -> dict:
    """
    Aggregate momentum_picks.py's `all_ranked` scored list into a score
    dispersion snapshot. Never raises — an empty/malformed list yields a
    zeroed result.
    """
    scores = []
    for pick in all_ranked:
        try:
            scores.append(float(pick.get("score") or 0))
        except (TypeError, ValueError):
            continue

    total = len(scores)
    if not total:
        return {
            "total_scored": 0, "top_score": 0.0, "mean_score": 0.0,
            "median_score": 0.0, "stdev_score": 0.0, "gap_top_to_median": 0.0,
            "coefficient_of_variation": 0.0,
            **classify_dispersion(0.0, 0.0),
        }

    scores.sort(reverse=True)
    top_score = scores[0]
    mean_score = statistics.mean(scores)
    median_score = statistics.median(scores)
    stdev_score = statistics.pstdev(scores) if total > 1 else 0.0
    coefficient_of_variation = round(stdev_score / mean_score, 2) if mean_score else 0.0

    return {
        "total_scored": total,
        "top_score": round(top_score, 1),
        "mean_score": round(mean_score, 1),
        "median_score": round(median_score, 1),
        "stdev_score": round(stdev_score, 1),
        "gap_top_to_median": round(top_score - median_score, 1),
        "coefficient_of_variation": coefficient_of_variation,
        **classify_dispersion(mean_score, coefficient_of_variation),
    }


def load_history(path) -> list:
    """Load the dispersion-history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_dispersion(history: list, entry: dict) -> list:
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


def record_dispersion(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_dispersion(load_history(path), entry)
    save_history(path, updated)
    return updated


def dispersion_trend(history: list, date: str, lookback: int = 5) -> dict:
    """
    Compare today's coefficient_of_variation to the entry ``lookback``
    sessions back.

    Returns {"delta": float, "direction": "widening"|"narrowing"|"flat",
    "lookback_date": str|None}. Empty/insufficient history → delta 0, flat.
    """
    dated = [e for e in history if e.get("date") is not None]
    dated.sort(key=lambda e: e["date"])
    idx = next((i for i, e in enumerate(dated) if e["date"] == date), None)
    if idx is None or idx - lookback < 0:
        return {"delta": 0.0, "direction": "flat", "lookback_date": None}

    prior = dated[idx - lookback]
    delta = round(
        dated[idx].get("coefficient_of_variation", 0) - prior.get("coefficient_of_variation", 0), 2
    )
    if delta >= 0.1:
        direction = "widening"
    elif delta <= -0.1:
        direction = "narrowing"
    else:
        direction = "flat"
    return {"delta": delta, "direction": direction, "lookback_date": prior["date"]}


def format_dispersion_text(dispersion: dict) -> str:
    """One-line console summary, matching the style of format_breadth_text()."""
    state = classify_dispersion(
        dispersion.get("mean_score", 0), dispersion.get("coefficient_of_variation", 0)
    )
    return (
        f"{state['emoji']} Dispersion: {state['label']} — "
        f"top {dispersion.get('top_score', 0)} vs median {dispersion.get('median_score', 0)} "
        f"(CoV {dispersion.get('coefficient_of_variation', 0)}) "
        f"across {dispersion.get('total_scored', 0)} names"
    )
