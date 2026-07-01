"""
Momentum Breadth Index — market-internals gauge for the daily scan universe.

Where mood_ring.py answers "how scared is the tape" (VIX regime), this answers
"how many of OUR names are actually participating." A single day's Gold/Silver/
Bronze podium can look great in a thin, narrow tape — breadth is the check on
that: what fraction of the whole scored universe (momentum_picks.py's
`all_ranked`) is trending clean, not just the top 3.

Four 0-100% components, averaged into one breadth_score:
  bullish_pct    — % with EMA stack FULL/PARTIAL BULLISH
  trending_pct   — % with ADX >= 25 (real trend, not chop)
  sweet_spot_pct — % with RSI in the 40-65 momentum zone
  pullback_pct   — % flagged as a Bounce 2.0 pullback setup

History is persisted date-keyed (dedup-overwrite same day, same pattern as
mood_ring.py's regime history) so the dossier can report breadth EXPANDING /
CONTRACTING vs N sessions ago instead of just today's snapshot.
"""

from __future__ import annotations

import json
from pathlib import Path

# 3-color HUD thresholds (see AGENTS.md / report/template.html):
#   green #00ff41 = risk-on / expanding   amber #f0b400 = neutral
#   red   #e53935 = risk-off / contracting
_STATES = [
    (65, {"state": "expanding", "color": "#00ff41", "emoji": "📈", "label": "Breadth Expanding"}),
    (35, {"state": "neutral", "color": "#f0b400", "emoji": "➖", "label": "Breadth Neutral"}),
    (0, {"state": "contracting", "color": "#e53935", "emoji": "📉", "label": "Breadth Contracting"}),
]


def _pct(count: int, total: int) -> float:
    return round(100.0 * count / total, 1) if total else 0.0


def classify_breadth(score: float) -> dict:
    """Map a 0-100 breadth score to a state dict (state/color/emoji/label)."""
    for floor, info in _STATES:
        if score >= floor:
            return dict(info)
    return dict(_STATES[-1][1])


def compute_breadth(all_ranked: list[dict]) -> dict:
    """
    Aggregate momentum_picks.py's `all_ranked` scored list into a breadth
    snapshot. Never raises — an empty/malformed list yields a zeroed result.
    """
    total = len(all_ranked)
    if not total:
        return {
            "total_scored": 0, "bullish_pct": 0.0, "trending_pct": 0.0,
            "sweet_spot_pct": 0.0, "pullback_pct": 0.0, "avg_score": 0.0,
            "breadth_score": 0.0, "sectors": {},
        }

    bullish = trending = sweet_spot = pullback = 0
    score_total = 0.0
    sectors: dict[str, dict] = {}

    for pick in all_ranked:
        ema_stack = str(pick.get("ema_stack") or "").upper()
        if "BULLISH" in ema_stack:
            bullish += 1
        if float(pick.get("adx") or 0) >= 25:
            trending += 1
        rsi = float(pick.get("rsi") or 0)
        if 40 <= rsi <= 65:
            sweet_spot += 1
        if pick.get("is_pullback_setup"):
            pullback += 1
        score_total += float(pick.get("score") or 0)

        sector = pick.get("sector") or "Other"
        s = sectors.setdefault(sector, {"count": 0, "bullish": 0, "score_total": 0.0})
        s["count"] += 1
        s["score_total"] += float(pick.get("score") or 0)
        if "BULLISH" in ema_stack:
            s["bullish"] += 1

    sector_breakdown = {
        name: {
            "count": s["count"],
            "bullish_pct": _pct(s["bullish"], s["count"]),
            "avg_score": round(s["score_total"] / s["count"], 1),
        }
        for name, s in sectors.items()
    }

    bullish_pct = _pct(bullish, total)
    trending_pct = _pct(trending, total)
    sweet_spot_pct = _pct(sweet_spot, total)
    pullback_pct = _pct(pullback, total)
    breadth_score = round((bullish_pct + trending_pct + sweet_spot_pct + pullback_pct) / 4, 1)

    return {
        "total_scored": total,
        "bullish_pct": bullish_pct,
        "trending_pct": trending_pct,
        "sweet_spot_pct": sweet_spot_pct,
        "pullback_pct": pullback_pct,
        "avg_score": round(score_total / total, 1),
        "breadth_score": breadth_score,
        "sectors": dict(sorted(sector_breakdown.items(), key=lambda kv: -kv[1]["avg_score"])),
    }


def load_history(path) -> list:
    """Load the breadth-history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_breadth(history: list, entry: dict) -> list:
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


def record_breadth(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_breadth(load_history(path), entry)
    save_history(path, updated)
    return updated


def breadth_trend(history: list, date: str, lookback: int = 5) -> dict:
    """
    Compare today's breadth_score to the entry ``lookback`` sessions back.

    Returns {"delta": float, "direction": "expanding"|"contracting"|"flat",
    "lookback_date": str|None}. Empty/insufficient history → delta 0, flat.
    """
    dated = [e for e in history if e.get("date") is not None]
    dated.sort(key=lambda e: e["date"])
    idx = next((i for i, e in enumerate(dated) if e["date"] == date), None)
    if idx is None or idx - lookback < 0:
        return {"delta": 0.0, "direction": "flat", "lookback_date": None}

    prior = dated[idx - lookback]
    delta = round(dated[idx].get("breadth_score", 0) - prior.get("breadth_score", 0), 1)
    if delta >= 5:
        direction = "expanding"
    elif delta <= -5:
        direction = "contracting"
    else:
        direction = "flat"
    return {"delta": delta, "direction": direction, "lookback_date": prior["date"]}


def format_breadth_text(breadth: dict) -> str:
    """One-line console summary, matching the style of format_picks_text()."""
    state = classify_breadth(breadth.get("breadth_score", 0))
    return (
        f"{state['emoji']} Breadth {breadth.get('breadth_score', 0)}/100 "
        f"({state['label']}) — {breadth.get('bullish_pct', 0)}% bullish, "
        f"{breadth.get('trending_pct', 0)}% trending, "
        f"{breadth.get('sweet_spot_pct', 0)}% in RSI sweet spot "
        f"across {breadth.get('total_scored', 0)} names"
    )
