"""
Factor Leaderboard — which momentum factor is actually driving today's tape.

momentum_picks.py scores every ticker on 10 weighted factors (EMA stack, ADX,
RSI, relative volume, MACD, etc.) but only ever surfaces the *summed* score —
never which factor is doing the work. Two days can both produce a strong
podium for very different reasons (a low-vol grind vs. a volume-driven
breakout), and that distinction is invisible in the current output.

This aggregates momentum_picks.py's `all_ranked` breakdown across the whole
scored universe: for each factor, average its points as a % of that factor's
max possible points, then rank factors by that average. The top factor is
"what's actually firing today" — new writing material, not a display of
data that already existed elsewhere.

History is persisted date-keyed (dedup-overwrite same day), same pattern as
breadth_index.py / mood_ring.py, so the dossier can report a factor rising or
fading over N sessions instead of just today's snapshot.
"""

from __future__ import annotations

import json
from pathlib import Path

# Max points per factor, mirrored from momentum_picks.py::score_momentum().
# Keep in sync if those weights change.
MAX_POINTS = {
    "ema_stack": 10,
    "pullback": 15,
    "adx": 18,
    "rsi": 15,
    "trend": 5,
    "rel_vol": 15,
    "price_vs_ema": 12,
    "macd": 5,
    "institutional": 5,
    "fortress": 10,
}

FACTOR_LABELS = {
    "ema_stack": "EMA Stack Alignment",
    "pullback": "Pullback Setup (Bounce 2.0)",
    "adx": "ADX Trend Strength",
    "rsi": "RSI Sweet Spot",
    "trend": "Trend Direction",
    "rel_vol": "Relative Volume",
    "price_vs_ema": "Price vs EMA21",
    "macd": "MACD Momentum",
    "institutional": "Institutional Buying",
    "fortress": "Fortress Quality",
}


def compute_leaderboard(all_ranked: list[dict]) -> dict:
    """
    Aggregate momentum_picks.py's `all_ranked` scored list into a per-factor
    leaderboard. Never raises — an empty/malformed list yields a zeroed result.
    """
    total = len(all_ranked)
    if not total:
        return {"total_scored": 0, "factors": []}

    sums = {factor: 0.0 for factor in MAX_POINTS}
    counted = {factor: 0 for factor in MAX_POINTS}

    for pick in all_ranked:
        breakdown = pick.get("breakdown") or {}
        for factor in MAX_POINTS:
            if factor not in breakdown:
                continue
            try:
                sums[factor] += float(breakdown[factor])
                counted[factor] += 1
            except (TypeError, ValueError):
                continue

    factors = []
    for factor, max_pts in MAX_POINTS.items():
        n = counted[factor]
        if not n:
            continue
        avg_points = sums[factor] / n
        avg_pct = max(0.0, min(100.0, round(100.0 * avg_points / max_pts, 1)))
        factors.append({
            "factor": factor,
            "label": FACTOR_LABELS.get(factor, factor),
            "avg_points": round(avg_points, 2),
            "max_points": max_pts,
            "avg_pct": avg_pct,
            "n": n,
        })

    factors.sort(key=lambda f: -f["avg_pct"])

    return {"total_scored": total, "factors": factors}


def load_history(path) -> list:
    """Load the factor-leaderboard history list. Missing/corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_leaderboard(history: list, entry: dict) -> list:
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


def record_leaderboard(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_leaderboard(load_history(path), entry)
    save_history(path, updated)
    return updated


def factor_trend(history: list, date: str, factor: str, lookback: int = 5) -> dict:
    """
    Compare a factor's avg_pct today to its avg_pct ``lookback`` sessions back.

    Returns {"delta": float, "direction": "rising"|"fading"|"flat",
    "lookback_date": str|None}. Missing entry/factor or insufficient history
    → delta 0, flat.
    """
    dated = [e for e in history if e.get("date") is not None]
    dated.sort(key=lambda e: e["date"])
    idx = next((i for i, e in enumerate(dated) if e["date"] == date), None)
    if idx is None or idx - lookback < 0:
        return {"delta": 0.0, "direction": "flat", "lookback_date": None}

    def _pct_for(entry: dict) -> float | None:
        for f in entry.get("factors", []):
            if f.get("factor") == factor:
                return f.get("avg_pct")
        return None

    now_pct = _pct_for(dated[idx])
    prior = dated[idx - lookback]
    prior_pct = _pct_for(prior)
    if now_pct is None or prior_pct is None:
        return {"delta": 0.0, "direction": "flat", "lookback_date": prior["date"]}

    delta = round(now_pct - prior_pct, 1)
    if delta >= 10:
        direction = "rising"
    elif delta <= -10:
        direction = "fading"
    else:
        direction = "flat"
    return {"delta": delta, "direction": direction, "lookback_date": prior["date"]}


def format_leaderboard_text(leaderboard: dict) -> str:
    """One-line console summary, matching the style of format_breadth_text()."""
    factors = leaderboard.get("factors", [])
    if not factors:
        return "🔧 Factor Leaderboard: no scored universe today"

    top3 = ", ".join(f"{f['label']} ({f['avg_pct']}%)" for f in factors[:3])
    return (
        f"🔧 Factor Leaderboard: {top3} — across {leaderboard.get('total_scored', 0)} names"
    )
