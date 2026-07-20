"""
Junk Rally Index — is today's leadership clean, or is quality_filter.py
quietly waving red flags at the names on top?

quality_filter.py already computes a 0-100 quality_score (SPAC / penny /
junk-bio / shell / low-liquidity / ADR / recent-IPO / pinned-price flags)
for every ticker inside momentum_picks.py's scoring, and applies it as a
multiplier on the final score. That per-ticker signal is used and then
discarded — nothing aggregates it across the scan universe the way
breadth_index.py, factor_leaderboard.py, and score_dispersion.py aggregate
their own angles on `all_ranked`.

This module asks: of the tickers actually leading today (the top N by
score), what fraction carry a quality flag at all? A tape where the podium
and the next several names are all clean is a very different regime from
one where half the "leaders" are penny stocks and recent IPOs riding thin
volume — even if the headline breadth/dispersion numbers look identical.
That's the "junk rally" pattern: a move that looks broad and strong until
you check who's actually running.

History is persisted date-keyed (dedup-overwrite same day), same pattern as
breadth_index.py / score_dispersion.py, so the dossier can report the junk
index rising or falling over N sessions instead of just today's snapshot.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

# 3-color HUD thresholds (see AGENTS.md / report/template.html):
#   green #00ff41 = clean leadership   amber #f0b400 = mixed   red #e53935 = junk rally
_MIXED_FLOOR_PCT = 20.0
_JUNK_RALLY_FLOOR_PCT = 50.0

DEFAULT_LEADER_COUNT = 10


def classify_quality(leaders_flagged_pct: float) -> dict:
    """Map the % of flagged leaders to a state dict (state/color/emoji/label)."""
    if leaders_flagged_pct >= _JUNK_RALLY_FLOOR_PCT:
        return {"state": "junk_rally", "color": "#e53935", "emoji": "🗑️", "label": "Junk Rally — Leaders Are Junk-Heavy"}
    if leaders_flagged_pct >= _MIXED_FLOOR_PCT:
        return {"state": "mixed_leadership", "color": "#f0b400", "emoji": "🤨", "label": "Mixed — Some Junk Up Top"}
    return {"state": "clean_leadership", "color": "#00ff41", "emoji": "✨", "label": "Clean Leadership"}


def _quality_score(pick: dict) -> float:
    try:
        raw = pick.get("quality_score")
        return float(raw) if raw is not None else 100.0
    except (TypeError, ValueError):
        return 100.0


def _score(pick: dict) -> float:
    try:
        return float(pick.get("score") or 0)
    except (TypeError, ValueError):
        return 0.0


def compute_quality_index(all_ranked: list[dict], leader_count: int = DEFAULT_LEADER_COUNT) -> dict:
    """
    Aggregate momentum_picks.py's `all_ranked` scored list into a leadership
    quality snapshot. Never raises — an empty/malformed list yields a
    zeroed, clean-by-default result.
    """
    total = len(all_ranked)
    if not total:
        return {
            "total_scored": 0, "leaders_n": 0,
            "universe_flagged_pct": 0.0, "universe_avg_quality": 100.0,
            "leaders_flagged_pct": 0.0, "leaders_avg_quality": 100.0,
            "junk_index": 0.0, "top_flags": {},
            **classify_quality(0.0),
        }

    universe_scores = [_quality_score(p) for p in all_ranked]
    universe_flagged = sum(1 for s in universe_scores if s < 100)
    universe_avg_quality = round(statistics.mean(universe_scores), 1)
    universe_flagged_pct = round(100.0 * universe_flagged / total, 1)

    # Leaders = top N by score. Don't assume `all_ranked` arrives pre-sorted.
    leaders = sorted(all_ranked, key=_score, reverse=True)[:leader_count]
    leaders_n = len(leaders)
    leader_scores = [_quality_score(p) for p in leaders]
    leaders_flagged = sum(1 for s in leader_scores if s < 100)
    leaders_avg_quality = round(statistics.mean(leader_scores), 1) if leaders_n else 100.0
    leaders_flagged_pct = round(100.0 * leaders_flagged / leaders_n, 1) if leaders_n else 0.0
    junk_index = round(100.0 - leaders_avg_quality, 1)

    flag_counts: dict[str, int] = {}
    for pick in leaders:
        flags = pick.get("quality_flags")
        if not isinstance(flags, dict):
            continue
        for name, is_set in flags.items():
            if is_set:
                flag_counts[name] = flag_counts.get(name, 0) + 1
    top_flags = dict(sorted(flag_counts.items(), key=lambda kv: -kv[1])[:5])

    return {
        "total_scored": total,
        "leaders_n": leaders_n,
        "universe_flagged_pct": universe_flagged_pct,
        "universe_avg_quality": universe_avg_quality,
        "leaders_flagged_pct": leaders_flagged_pct,
        "leaders_avg_quality": leaders_avg_quality,
        "junk_index": junk_index,
        "top_flags": top_flags,
        **classify_quality(leaders_flagged_pct),
    }


def load_history(path) -> list:
    """Load the quality-history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_quality(history: list, entry: dict) -> list:
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


def record_quality(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_quality(load_history(path), entry)
    save_history(path, updated)
    return updated


def quality_trend(history: list, date: str, lookback: int = 5) -> dict:
    """
    Compare today's junk_index to the entry ``lookback`` sessions back.

    Returns {"delta": float, "direction": "cleaning_up"|"getting_junkier"|"flat",
    "lookback_date": str|None}. Empty/insufficient history → delta 0, flat.
    """
    dated = [e for e in history if e.get("date") is not None]
    dated.sort(key=lambda e: e["date"])
    idx = next((i for i, e in enumerate(dated) if e["date"] == date), None)
    if idx is None or idx - lookback < 0:
        return {"delta": 0.0, "direction": "flat", "lookback_date": None}

    prior = dated[idx - lookback]
    delta = round(dated[idx].get("junk_index", 0) - prior.get("junk_index", 0), 1)
    if delta >= 5:
        direction = "getting_junkier"
    elif delta <= -5:
        direction = "cleaning_up"
    else:
        direction = "flat"
    return {"delta": delta, "direction": direction, "lookback_date": prior["date"]}


def format_quality_text(quality: dict) -> str:
    """One-line console summary, matching the style of format_dispersion_text()."""
    state = classify_quality(quality.get("leaders_flagged_pct", 0))
    top_flag = next(iter(quality.get("top_flags", {})), None)
    flag_note = f" (top flag: {top_flag})" if top_flag else ""
    return (
        f"{state['emoji']} Junk Index {quality.get('junk_index', 0)}/100 "
        f"({state['label']}) — {quality.get('leaders_flagged_pct', 0)}% of top "
        f"{quality.get('leaders_n', 0)} leaders flagged{flag_note}"
    )
