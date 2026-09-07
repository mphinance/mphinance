"""
Volume Conviction Index — are today's momentum leaders being bought, or
drifting up on nobody's volume?

breadth_index.py, factor_leaderboard.py, score_dispersion.py,
sector_leadership.py, quality_breadth.py, extension_index.py and
follow_through_index.py all aggregate momentum_picks.py's `all_ranked`
scored list, but none of them look at `rel_vol` (relative volume vs the
20-day average) — the field that says whether a move has real participation
behind it. follow_through_index.py already asks whether the tape's *price*
agrees with the leaderboard; this asks the volume question that price alone
can't answer: a name can gap green on light volume (nobody's actually
trading it) just as easily as it can grind red on heavy volume (real
distribution). Two leaderboards can show identical follow-through and look
completely different underneath — one where the leaders are trading 2x+
average volume (real conviction), and one where they're drifting up on
sub-average volume (a move nobody's actually behind, more likely to fade
the first time someone tests it).

This narrows momentum_picks.py's `all_ranked` scored list the same way
follow_through_index.py does: % of the whole scanned universe showing
elevated relative volume (>= 1.5x, the same floor momentum_picks.py's own
scoring treats as a real participation signal) vs thin relative volume
(< 0.8x), then narrows to the top N names by score. A wide gap between
"leaders are elevated" and "universe is elevated" is the tell — either the
screen is finding names the market is actually trading (leaders elevated
while the broad universe is average) or the leaderboard is running ahead of
real participation (leaders thin while volume elsewhere is normal).

History is persisted date-keyed (dedup-overwrite same day), same pattern as
follow_through_index.py / extension_index.py, so the dossier can report
volume conviction strengthening or fading over N sessions instead of just
today's snapshot.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

# 3-color HUD thresholds (see AGENTS.md / report/template.html):
#   green #00ff41 = leaders confirmed by volume   amber #f0b400 = mixed
#   red   #e53935 = leaders running on thin volume
_MIN_LEADERS_FOR_SIGNAL = 3
_ELEVATED_REL_VOL = 1.5
_THIN_REL_VOL = 0.8
_CONFIRMED_FLOOR_PCT = 50.0
_THIN_CEIL_PCT = 15.0

DEFAULT_LEADER_COUNT = 10


def classify_volume_conviction(leaders_elevated_pct: float, leaders_n: int) -> dict:
    """Map the % of leaders showing elevated relative volume to a state dict."""
    if leaders_n < _MIN_LEADERS_FOR_SIGNAL:
        return {"state": "insufficient", "color": "#888888", "emoji": "❔", "label": "Insufficient Data"}
    if leaders_elevated_pct >= _CONFIRMED_FLOOR_PCT:
        return {"state": "confirmed", "color": "#00ff41", "emoji": "🔊", "label": "Leaders Confirmed — Real Volume Behind It"}
    if leaders_elevated_pct <= _THIN_CEIL_PCT:
        return {"state": "thin", "color": "#e53935", "emoji": "🔇", "label": "Leaders Thin — Nobody's Actually Trading It"}
    return {"state": "mixed", "color": "#f0b400", "emoji": "🤨", "label": "Mixed Volume Conviction"}


def _rel_vol(pick: dict) -> float | None:
    """Returns None when the pick carries no usable rel_vol.

    Deliberately not defaulted to 1.0 (the "average" baseline momentum_picks.py's
    own scorer falls back to): a missing field is unknown, not average, and
    silently defaulting it here would let a malformed batch read as a flat
    "mixed" verdict instead of surfacing that the data was missing.
    """
    try:
        raw = pick.get("rel_vol")
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _score(pick: dict) -> float:
    try:
        return float(pick.get("score") or 0)
    except (TypeError, ValueError):
        return 0.0


def _vol_stats(picks: list[dict]) -> dict:
    vols = [v for v in (_rel_vol(p) for p in picks) if v is not None]
    n = len(vols)
    if not n:
        return {"n": 0, "elevated_pct": 0.0, "thin_pct": 0.0, "avg_rel_vol": 0.0}
    elevated = sum(1 for v in vols if v >= _ELEVATED_REL_VOL)
    thin = sum(1 for v in vols if v < _THIN_REL_VOL)
    return {
        "n": n,
        "elevated_pct": round(100.0 * elevated / n, 1),
        "thin_pct": round(100.0 * thin / n, 1),
        "avg_rel_vol": round(statistics.mean(vols), 2),
    }


def compute_volume_conviction(all_ranked: list[dict], leader_count: int = DEFAULT_LEADER_COUNT) -> dict:
    """
    Aggregate momentum_picks.py's `all_ranked` scored list into a volume
    conviction snapshot. Never raises — an empty/malformed list yields a
    zeroed result.
    """
    total = len(all_ranked)
    if not total:
        return {
            "total_scored": 0, "leaders_n": 0,
            "universe_elevated_pct": 0.0, "universe_thin_pct": 0.0, "universe_avg_rel_vol": 0.0,
            "leaders_elevated_pct": 0.0, "leaders_thin_pct": 0.0, "leaders_avg_rel_vol": 0.0,
            "conviction_gap": 0.0,
            **classify_volume_conviction(0.0, 0),
        }

    universe = _vol_stats(all_ranked)
    if not universe["n"]:
        # No pick carried a usable rel_vol. Say so rather than publishing a
        # confident red verdict computed from nothing.
        return {
            "total_scored": total, "leaders_n": 0,
            "universe_elevated_pct": 0.0, "universe_thin_pct": 0.0, "universe_avg_rel_vol": 0.0,
            "leaders_elevated_pct": 0.0, "leaders_thin_pct": 0.0, "leaders_avg_rel_vol": 0.0,
            "conviction_gap": 0.0,
            **classify_volume_conviction(0.0, 0),
        }

    leaders = sorted(all_ranked, key=_score, reverse=True)[:leader_count]
    leader_stats = _vol_stats(leaders)
    conviction_gap = round(leader_stats["elevated_pct"] - universe["elevated_pct"], 1)

    return {
        "total_scored": total,
        "leaders_n": leader_stats["n"],
        "universe_elevated_pct": universe["elevated_pct"],
        "universe_thin_pct": universe["thin_pct"],
        "universe_avg_rel_vol": universe["avg_rel_vol"],
        "leaders_elevated_pct": leader_stats["elevated_pct"],
        "leaders_thin_pct": leader_stats["thin_pct"],
        "leaders_avg_rel_vol": leader_stats["avg_rel_vol"],
        "conviction_gap": conviction_gap,
        **classify_volume_conviction(leader_stats["elevated_pct"], leader_stats["n"]),
    }


def load_history(path) -> list:
    """Load the volume-conviction history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_volume_conviction(history: list, entry: dict) -> list:
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


def record_volume_conviction(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_volume_conviction(load_history(path), entry)
    save_history(path, updated)
    return updated


def volume_conviction_trend(history: list, date: str, lookback: int = 5) -> dict:
    """
    Compare today's leaders_elevated_pct to the entry ``lookback`` sessions back.

    Returns {"delta": float, "direction": "strengthening"|"fading"|"flat",
    "lookback_date": str|None}. Empty/insufficient history → delta 0, flat.
    """
    dated = [e for e in history if e.get("date") is not None]
    dated.sort(key=lambda e: e["date"])
    idx = next((i for i, e in enumerate(dated) if e["date"] == date), None)
    if idx is None or idx - lookback < 0:
        return {"delta": 0.0, "direction": "flat", "lookback_date": None}

    prior = dated[idx - lookback]
    delta = round(dated[idx].get("leaders_elevated_pct", 0) - prior.get("leaders_elevated_pct", 0), 1)
    if delta >= 15:
        direction = "strengthening"
    elif delta <= -15:
        direction = "fading"
    else:
        direction = "flat"
    return {"delta": delta, "direction": direction, "lookback_date": prior["date"]}


def format_volume_conviction_text(volume_conviction: dict) -> str:
    """One-line console summary, matching the style of format_follow_through_text()."""
    state = classify_volume_conviction(
        volume_conviction.get("leaders_elevated_pct", 0), volume_conviction.get("leaders_n", 0)
    )
    return (
        f"{state['emoji']} Volume Conviction: {state['label']} — "
        f"{volume_conviction.get('leaders_elevated_pct', 0)}% of top "
        f"{volume_conviction.get('leaders_n', 0)} leaders at elevated volume vs "
        f"{volume_conviction.get('universe_elevated_pct', 0)}% of the universe "
        f"(gap {volume_conviction.get('conviction_gap', 0):+.1f})"
    )
