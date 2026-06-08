"""
Mood Ring — regime history persistence and mood mapping.

Maps VIX regime names to mood colors/emojis and maintains an append-only,
date-keyed JSON history at landing/data/regime_history.json.
"""

from pathlib import Path
import json

# Matches the color system in AGENTS.md and the existing template regime_colors dict
_MOOD_MAP = {
    "CALM":     {"color": "#00ff41", "emoji": "🟢", "label": "risk-on"},
    "NORMAL":   {"color": "#00ff41", "emoji": "🟢", "label": "risk-on"},
    "ELEVATED": {"color": "#f0b400", "emoji": "🟡", "label": "neutral"},
    "FEAR":     {"color": "#e53935", "emoji": "🔴", "label": "risk-off"},
    "PANIC":    {"color": "#e53935", "emoji": "🔴", "label": "risk-off"},
}


def regime_to_mood(regime: str) -> dict:
    """Return {color, emoji, label} for a regime name. Falls back to gray/unknown."""
    return _MOOD_MAP.get(regime, {"color": "#888888", "emoji": "⚪", "label": "unknown"})


def append_regime_history(
    date: str,
    regime: str,
    vix_level: float,
    spy_change: float,
    history_path: Path,
) -> list:
    """
    Append today's regime entry to the history file (date-keyed, no duplicates).
    Re-running for the same date overwrites that day's entry.
    Returns the updated history list (newest-first).
    """
    history = []
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text())
            if not isinstance(history, list):
                history = []
        except Exception:
            history = []

    entry = {
        "date": date,
        "regime": regime,
        "regime_name": regime,
        "vix_level": round(float(vix_level), 2),
        "spy_change": round(float(spy_change), 4),
        "emoji": regime_to_mood(regime)["emoji"],
    }

    idx = next((i for i, e in enumerate(history) if e.get("date") == date), None)
    if idx is not None:
        history[idx] = entry
    else:
        history.append(entry)

    history.sort(key=lambda e: e.get("date", ""), reverse=True)

    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2))
    return history
