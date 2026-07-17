"""
Sector Leadership Concentration — is today's tape led by one sector, or is
strength rotating across the board?

breadth_index.py answers "how many names are participating," factor_leaderboard.py
answers "which scoring factor is driving it," and score_dispersion.py answers
"is the score distribution a lone standout or a broad pack." None of the three
look at *which sectors* those scores belong to. Two days can have identical
breadth, the same top factor, and the same dispersion shape while looking
completely different underneath: one where the top 15 names are 10 Tech
tickers (a single-sector melt-up), and one where the same 15 names are spread
across 8 different sectors (a genuine broad rotation).

This aggregates momentum_picks.py's `all_ranked` scored list into a sector
concentration snapshot: which sector holds the largest share of the top-scored
group, and how that share compares ("lift") to that sector's share of the
whole scanned universe — a lift near 1.0 means the sector isn't over- or
under-represented at the top; a lift well above 1.0 means it's punching above
its weight in leadership.

History is persisted date-keyed (dedup-overwrite same day), same pattern as
breadth_index.py / factor_leaderboard.py / score_dispersion.py, so the dossier
can report leadership rotating between sectors over N sessions instead of
just today's snapshot.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

# 3-color HUD thresholds (see AGENTS.md / report/template.html):
#   green #00ff41 = broad rotation      amber #f0b400 = concentrated leadership
#   red   #e53935 = monolithic (one sector owns the tape)
_MIN_SCORED_FOR_SIGNAL = 3
_CONCENTRATED_SHARE = 0.40
_MONOLITHIC_SHARE = 0.65


def classify_leadership(leading_share: float, total_scored: int) -> dict:
    """Map (leading_share, total_scored) to a state dict (state/color/emoji/label)."""
    if total_scored < _MIN_SCORED_FOR_SIGNAL:
        return {"state": "insufficient", "color": "#888888", "emoji": "❔", "label": "Insufficient Data"}
    if leading_share >= _MONOLITHIC_SHARE:
        return {"state": "monolithic", "color": "#e53935", "emoji": "🎯", "label": "Monolithic — One Sector Owns The Tape"}
    if leading_share >= _CONCENTRATED_SHARE:
        return {"state": "concentrated", "color": "#f0b400", "emoji": "🧭", "label": "Concentrated Leadership"}
    return {"state": "broad", "color": "#00ff41", "emoji": "🌐", "label": "Broad Rotation — No Single Sector Dominates"}


def compute_sector_leadership(all_ranked: list[dict], top_n: int = 15) -> dict:
    """
    Aggregate momentum_picks.py's `all_ranked` scored list into a sector
    leadership snapshot. Never raises — an empty/malformed list yields a
    zeroed result.
    """
    rows = []
    for pick in all_ranked:
        try:
            score = float(pick.get("score") or 0)
        except (TypeError, ValueError):
            continue
        sector = pick.get("sector") or "Other"
        rows.append((score, sector))

    total = len(rows)
    if not total:
        return {
            "total_scored": 0, "top_group_size": 0, "leading_sector": None,
            "leading_count": 0, "leading_share": 0.0, "baseline_share": 0.0,
            "lift": 0.0, "sector_breakdown": {}, "num_sectors_represented": 0,
            **classify_leadership(0.0, 0),
        }

    rows.sort(key=lambda r: r[0], reverse=True)
    top_group = rows[:min(top_n, total)]

    top_sectors = Counter(sector for _, sector in top_group)
    leading_sector, leading_count = top_sectors.most_common(1)[0]
    leading_share = leading_count / len(top_group)

    full_sectors = Counter(sector for _, sector in rows)
    baseline_share = full_sectors[leading_sector] / total
    lift = round(leading_share / baseline_share, 2) if baseline_share else 0.0

    return {
        "total_scored": total,
        "top_group_size": len(top_group),
        "leading_sector": leading_sector,
        "leading_count": leading_count,
        "leading_share": round(leading_share, 2),
        "baseline_share": round(baseline_share, 2),
        "lift": lift,
        "sector_breakdown": dict(top_sectors.most_common()),
        "num_sectors_represented": len(top_sectors),
        **classify_leadership(leading_share, total),
    }


def load_history(path) -> list:
    """Load the leadership-history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_leadership(history: list, entry: dict) -> list:
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


def record_leadership(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_leadership(load_history(path), entry)
    save_history(path, updated)
    return updated


def leadership_rotation(history: list, date: str, lookback: int = 5) -> dict:
    """
    Compare today's leading sector to the entry ``lookback`` sessions back.

    Returns {"rotated": bool, "prior_sector": str|None, "lookback_date": str|None}.
    Empty/insufficient history → rotated False, prior_sector None.
    """
    dated = [e for e in history if e.get("date") is not None]
    dated.sort(key=lambda e: e["date"])
    idx = next((i for i, e in enumerate(dated) if e["date"] == date), None)
    if idx is None or idx - lookback < 0:
        return {"rotated": False, "prior_sector": None, "lookback_date": None}

    prior = dated[idx - lookback]
    prior_sector = prior.get("leading_sector")
    rotated = prior_sector is not None and prior_sector != dated[idx].get("leading_sector")
    return {"rotated": rotated, "prior_sector": prior_sector, "lookback_date": prior["date"]}


def format_leadership_text(leadership: dict) -> str:
    """One-line console summary, matching the style of format_dispersion_text()."""
    state = classify_leadership(
        leadership.get("leading_share", 0), leadership.get("total_scored", 0)
    )
    return (
        f"{state['emoji']} Sector Leadership: {state['label']} — "
        f"{leadership.get('leading_sector', 'n/a')} holds "
        f"{int(leadership.get('leading_share', 0) * 100)}% of top "
        f"{leadership.get('top_group_size', 0)} (lift {leadership.get('lift', 0)}x) "
        f"across {leadership.get('num_sectors_represented', 0)} sectors"
    )
