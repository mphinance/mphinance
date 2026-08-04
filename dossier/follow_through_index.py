"""
Follow-Through Index — are today's momentum leaders actually being paid, or
is the tape not yet buying the setup?

breadth_index.py, factor_leaderboard.py, score_dispersion.py, sector_leadership.py,
quality_breadth.py and extension_index.py all aggregate momentum_picks.py's
`all_ranked` scored list, but every one of them looks at *technical* fields
(EMA stack, ADX, RSI, sector, quality flags). None of them look at the one
field that says whether the market agrees with the screen right now:
`change_pct` — today's actual price move. A ticker can top the leaderboard on
EMA/ADX/RSI structure while trading red on the day; that's a very different
setup than a leaderboard where the top names are also the day's advancers.

This asks the classic advance/decline question (% of the scanned universe up
vs down today) and then narrows it: of the top N names by momentum score, what
% are actually advancing? A wide gap between "leaders are green" and "universe
is green" is the tell — either the screen is finding real relative strength
(leaders green while the broad universe is mixed/red) or the screen's picks
haven't been confirmed yet (leaders red while the universe is fine).

History is persisted date-keyed (dedup-overwrite same day), same pattern as
quality_breadth.py / extension_index.py, so the dossier can report
follow-through strengthening or fading over N sessions instead of just
today's snapshot.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

# 3-color HUD thresholds (see AGENTS.md / report/template.html):
#   green #00ff41 = leaders confirmed by price   amber #f0b400 = mixed
#   red   #e53935 = leaders not yet confirmed by price
_MIN_LEADERS_FOR_SIGNAL = 3
_CONFIRMED_FLOOR_PCT = 70.0
_UNCONFIRMED_CEIL_PCT = 30.0

DEFAULT_LEADER_COUNT = 10


def classify_follow_through(leaders_advance_pct: float, leaders_n: int) -> dict:
    """Map the % of leaders that are advancing today to a state dict."""
    if leaders_n < _MIN_LEADERS_FOR_SIGNAL:
        return {"state": "insufficient", "color": "#888888", "emoji": "❔", "label": "Insufficient Data"}
    if leaders_advance_pct >= _CONFIRMED_FLOOR_PCT:
        return {"state": "confirmed", "color": "#00ff41", "emoji": "✅", "label": "Leaders Confirmed — Price Agrees"}
    if leaders_advance_pct <= _UNCONFIRMED_CEIL_PCT:
        return {"state": "unconfirmed", "color": "#e53935", "emoji": "🛑", "label": "Leaders Unconfirmed — Price Isn't Buying It"}
    return {"state": "mixed", "color": "#f0b400", "emoji": "🤨", "label": "Mixed Follow-Through"}


def _change_pct(pick: dict) -> float | None:
    """Returns None when the pick carries no usable change_pct.

    Deliberately not 0.0: a missing field is unknown, not unchanged. Defaulting to
    zero here made every name read as flat, so advance_pct and decline_pct were both
    0.0 and the widget printed "Leaders Unconfirmed" every session regardless of tape.
    """
    try:
        raw = pick.get("change_pct")
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _score(pick: dict) -> float:
    try:
        return float(pick.get("score") or 0)
    except (TypeError, ValueError):
        return 0.0


def _ad_stats(picks: list[dict]) -> dict:
    changes = [c for c in (_change_pct(p) for p in picks) if c is not None]
    n = len(changes)
    if not n:
        return {"n": 0, "advance_pct": 0.0, "decline_pct": 0.0, "avg_change_pct": 0.0}
    advancers = sum(1 for c in changes if c > 0)
    decliners = sum(1 for c in changes if c < 0)
    return {
        "n": n,
        "advance_pct": round(100.0 * advancers / n, 1),
        "decline_pct": round(100.0 * decliners / n, 1),
        "avg_change_pct": round(statistics.mean(changes), 2),
    }


def compute_follow_through(all_ranked: list[dict], leader_count: int = DEFAULT_LEADER_COUNT) -> dict:
    """
    Aggregate momentum_picks.py's `all_ranked` scored list into an
    advance/decline + leader follow-through snapshot. Never raises — an
    empty/malformed list yields a zeroed result.
    """
    total = len(all_ranked)
    if not total:
        return {
            "total_scored": 0, "leaders_n": 0,
            "universe_advance_pct": 0.0, "universe_decline_pct": 0.0, "universe_avg_change_pct": 0.0,
            "leaders_advance_pct": 0.0, "leaders_decline_pct": 0.0, "leaders_avg_change_pct": 0.0,
            "follow_through_gap": 0.0,
            **classify_follow_through(0.0, 0),
        }

    universe = _ad_stats(all_ranked)
    if not universe["n"]:
        # No pick carried a usable change_pct. Say so rather than publishing a
        # confident red verdict computed from nothing.
        return {
            "total_scored": total, "leaders_n": 0,
            "universe_advance_pct": 0.0, "universe_decline_pct": 0.0, "universe_avg_change_pct": 0.0,
            "leaders_advance_pct": 0.0, "leaders_decline_pct": 0.0, "leaders_avg_change_pct": 0.0,
            "follow_through_gap": 0.0,
            **classify_follow_through(0.0, 0),
        }

    leaders = sorted(all_ranked, key=_score, reverse=True)[:leader_count]
    leader_stats = _ad_stats(leaders)
    follow_through_gap = round(leader_stats["advance_pct"] - universe["advance_pct"], 1)

    return {
        "total_scored": total,
        "leaders_n": leader_stats["n"],
        "universe_advance_pct": universe["advance_pct"],
        "universe_decline_pct": universe["decline_pct"],
        "universe_avg_change_pct": universe["avg_change_pct"],
        "leaders_advance_pct": leader_stats["advance_pct"],
        "leaders_decline_pct": leader_stats["decline_pct"],
        "leaders_avg_change_pct": leader_stats["avg_change_pct"],
        "follow_through_gap": follow_through_gap,
        **classify_follow_through(leader_stats["advance_pct"], leader_stats["n"]),
    }


def load_history(path) -> list:
    """Load the follow-through history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_follow_through(history: list, entry: dict) -> list:
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


def record_follow_through(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_follow_through(load_history(path), entry)
    save_history(path, updated)
    return updated


def follow_through_trend(history: list, date: str, lookback: int = 5) -> dict:
    """
    Compare today's leaders_advance_pct to the entry ``lookback`` sessions back.

    Returns {"delta": float, "direction": "strengthening"|"fading"|"flat",
    "lookback_date": str|None}. Empty/insufficient history → delta 0, flat.
    """
    dated = [e for e in history if e.get("date") is not None]
    dated.sort(key=lambda e: e["date"])
    idx = next((i for i, e in enumerate(dated) if e["date"] == date), None)
    if idx is None or idx - lookback < 0:
        return {"delta": 0.0, "direction": "flat", "lookback_date": None}

    prior = dated[idx - lookback]
    delta = round(dated[idx].get("leaders_advance_pct", 0) - prior.get("leaders_advance_pct", 0), 1)
    if delta >= 15:
        direction = "strengthening"
    elif delta <= -15:
        direction = "fading"
    else:
        direction = "flat"
    return {"delta": delta, "direction": direction, "lookback_date": prior["date"]}


def format_follow_through_text(follow_through: dict) -> str:
    """One-line console summary, matching the style of format_quality_text()."""
    state = classify_follow_through(
        follow_through.get("leaders_advance_pct", 0), follow_through.get("leaders_n", 0)
    )
    return (
        f"{state['emoji']} Follow-Through: {state['label']} — "
        f"{follow_through.get('leaders_advance_pct', 0)}% of top "
        f"{follow_through.get('leaders_n', 0)} leaders advancing vs "
        f"{follow_through.get('universe_advance_pct', 0)}% of the universe "
        f"(gap {follow_through.get('follow_through_gap', 0):+.1f})"
    )
