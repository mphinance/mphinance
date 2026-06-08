"""
Market Mood Ring — pure surfacing layer on top of the existing market regime.

`detect_regime()` (dossier/market_regime.py) already classifies the day into one of
five VIX-based regimes (CALM / NORMAL / ELEVATED / FEAR / PANIC). This module does
**not** compute any new signal — it only:

  1. maps each regime to a "mood" (risk posture + HUD color + emoji), and
  2. persists a deduped, date-keyed history of regimes so the dossier header can
     render a mood-ring banner with a strip of the last ~10 days.

Colors follow the 3-color HUD system (see AGENTS.md / report/template.html):
  green  #00ff41 = risk-on        amber #f0b400 = neutral / caution
  red    #e53935 = risk-off / extreme
"""

from __future__ import annotations

import json
from pathlib import Path

# Regime → mood. Greens for the two benign regimes, amber for elevated caution,
# red for the two stress regimes — same thresholds the template already uses.
_MOODS = {
    "CALM":     {"mood": "risk-on",  "color": "#00ff41", "emoji": "😎", "label": "Risk-On"},
    "NORMAL":   {"mood": "risk-on",  "color": "#00ff41", "emoji": "🙂", "label": "Risk-On"},
    "ELEVATED": {"mood": "neutral",  "color": "#f0b400", "emoji": "😐", "label": "Caution"},
    "FEAR":     {"mood": "risk-off", "color": "#e53935", "emoji": "😨", "label": "Risk-Off"},
    "PANIC":    {"mood": "risk-off", "color": "#e53935", "emoji": "😱", "label": "Risk-Off"},
}

_UNKNOWN_MOOD = {"mood": "unknown", "color": "#888888", "emoji": "❓", "label": "Unknown"}


def regime_to_mood(regime) -> dict:
    """Map a regime name to its mood dict. Unknown / falsy → grey 'unknown' mood."""
    if not regime:
        return dict(_UNKNOWN_MOOD)
    return dict(_MOODS.get(str(regime).upper(), _UNKNOWN_MOOD))


def load_history(path) -> list:
    """Load the regime-history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_regime(history: list, entry: dict) -> list:
    """
    Return a new history list with ``entry`` added, deduped by ``date``.

    Re-running for a date that already exists OVERWRITES that day's entry instead
    of duplicating it. Result is sorted by date ascending.
    """
    date = entry.get("date")
    kept = [e for e in history if e.get("date") != date]
    kept.append(entry)
    kept.sort(key=lambda e: e.get("date", ""))
    return kept


def save_history(path, history: list) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(history, indent=2))


def record_regime(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_regime(load_history(path), entry)
    save_history(path, updated)
    return updated


def build_mood_ring(history: list, today: dict | None = None, strip_len: int = 10) -> dict:
    """
    Build the template context for the mood-ring banner.

    ``today`` is the history entry for the current date; if omitted, the most
    recent entry is used. Returns ``{}`` when there is no history at all.
    """
    if not history:
        return {}

    current = today or history[-1]
    mood = regime_to_mood(current.get("regime"))

    strip = []
    for e in history[-strip_len:]:
        m = regime_to_mood(e.get("regime"))
        strip.append({
            "date": e.get("date"),
            "regime": e.get("regime"),
            "emoji": m["emoji"],
            "color": m["color"],
        })

    return {
        "date": current.get("date"),
        "regime": current.get("regime"),
        "regime_name": current.get("regime_name"),
        "vix_level": current.get("vix_level"),
        "spy_change": current.get("spy_change"),
        "mood": mood["mood"],
        "color": mood["color"],
        "emoji": mood["emoji"],
        "label": mood["label"],
        "strip": strip,
    }
