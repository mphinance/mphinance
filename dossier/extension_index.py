"""
Tape Extension Index — how stretched is the scanned universe right now?

breadth_index.py checks whether RSI sits in the 40-65 "sweet spot" and whether
ADX shows a real trend, but it never looks at the tails: how much of the
scanned universe is already overbought (chase risk) or oversold (capitulation,
a possible mean-reversion bounce). Two days can show identical breadth and
factor mix while one is quietly running hot (leaders already extended, RSI and
Stochastic both pinned near the top) and the other is coiled at the bottom (a
capitulation cluster) — that distinction is invisible in the current output.

This aggregates momentum_picks.py's `all_ranked` scored list into a tail-risk
snapshot: % overbought (RSI >= 70 and Stoch %K >= 80), % oversold (RSI <= 30
and Stoch %K <= 20), and a net_extension score (overbought_pct - oversold_pct)
classified into a chase-risk / balanced / capitulation regime.

History is persisted date-keyed (dedup-overwrite same day), same pattern as
breadth_index.py / sector_leadership.py / quality_breadth.py, so the dossier
can report the tape getting more overheated or more capitulated over N
sessions instead of just today's snapshot.
"""

from __future__ import annotations

import json
from pathlib import Path

# 3-color HUD thresholds (see AGENTS.md / report/template.html):
#   green #00ff41 = capitulation cluster (bounce candidates)  amber #f0b400 = balanced
#   red   #e53935 = chase risk (tape already extended)
_MIN_SCORED_FOR_SIGNAL = 5
_OVERBOUGHT_RSI = 70
_OVERBOUGHT_STOCH = 80
_OVERSOLD_RSI = 30
_OVERSOLD_STOCH = 20
_CHASE_RISK_NET = 15.0
_CAPITULATION_NET = -15.0


def classify_extension(net_extension: float, total_scored: int) -> dict:
    """Map (net_extension, total_scored) to a state dict (state/color/emoji/label)."""
    if total_scored < _MIN_SCORED_FOR_SIGNAL:
        return {"state": "insufficient", "color": "#888888", "emoji": "❔", "label": "Insufficient Data"}
    if net_extension >= _CHASE_RISK_NET:
        return {"state": "chase_risk", "color": "#e53935", "emoji": "🔥", "label": "Chase Risk — Tape Already Extended"}
    if net_extension <= _CAPITULATION_NET:
        return {"state": "capitulation", "color": "#00ff41", "emoji": "🩸", "label": "Capitulation Cluster — Bounce Candidates"}
    return {"state": "balanced", "color": "#f0b400", "emoji": "➖", "label": "Balanced — No Tail Extreme"}


def compute_extension_index(all_ranked: list[dict]) -> dict:
    """
    Aggregate momentum_picks.py's `all_ranked` scored list into a tape
    extension snapshot. Never raises — an empty/malformed list yields a
    zeroed result.
    """
    total = 0
    overbought = 0
    oversold = 0
    overbought_tickers = []
    oversold_tickers = []

    for pick in all_ranked:
        try:
            rsi = float(pick.get("rsi") or 0)
            stoch_k = float(pick.get("stoch_k") or 0)
        except (TypeError, ValueError):
            continue
        total += 1
        ticker = pick.get("ticker", "")
        if rsi >= _OVERBOUGHT_RSI and stoch_k >= _OVERBOUGHT_STOCH:
            overbought += 1
            if ticker:
                overbought_tickers.append(ticker)
        elif rsi <= _OVERSOLD_RSI and stoch_k <= _OVERSOLD_STOCH:
            oversold += 1
            if ticker:
                oversold_tickers.append(ticker)

    if not total:
        return {
            "total_scored": 0, "overbought_pct": 0.0, "oversold_pct": 0.0,
            "net_extension": 0.0, "overbought_tickers": [], "oversold_tickers": [],
            **classify_extension(0.0, 0),
        }

    overbought_pct = round(100.0 * overbought / total, 1)
    oversold_pct = round(100.0 * oversold / total, 1)
    net_extension = round(overbought_pct - oversold_pct, 1)

    return {
        "total_scored": total,
        "overbought_pct": overbought_pct,
        "oversold_pct": oversold_pct,
        "net_extension": net_extension,
        "overbought_tickers": overbought_tickers[:10],
        "oversold_tickers": oversold_tickers[:10],
        **classify_extension(net_extension, total),
    }


def load_history(path) -> list:
    """Load the extension-history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_extension(history: list, entry: dict) -> list:
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


def record_extension(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_extension(load_history(path), entry)
    save_history(path, updated)
    return updated


def extension_trend(history: list, date: str, lookback: int = 5) -> dict:
    """
    Compare today's net_extension to the entry ``lookback`` sessions back.

    Returns {"delta": float, "direction": "more_extended"|"more_capitulated"|"flat",
    "lookback_date": str|None}. Empty/insufficient history → delta 0, flat.
    """
    dated = [e for e in history if e.get("date") is not None]
    dated.sort(key=lambda e: e["date"])
    idx = next((i for i, e in enumerate(dated) if e["date"] == date), None)
    if idx is None or idx - lookback < 0:
        return {"delta": 0.0, "direction": "flat", "lookback_date": None}

    prior = dated[idx - lookback]
    delta = round(dated[idx].get("net_extension", 0) - prior.get("net_extension", 0), 1)
    if delta >= 10:
        direction = "more_extended"
    elif delta <= -10:
        direction = "more_capitulated"
    else:
        direction = "flat"
    return {"delta": delta, "direction": direction, "lookback_date": prior["date"]}


def format_extension_text(extension: dict) -> str:
    """One-line console summary, matching the style of format_leadership_text()."""
    state = classify_extension(
        extension.get("net_extension", 0), extension.get("total_scored", 0)
    )
    return (
        f"{state['emoji']} Tape Extension: {state['label']} — "
        f"{extension.get('overbought_pct', 0)}% overbought, "
        f"{extension.get('oversold_pct', 0)}% oversold "
        f"(net {extension.get('net_extension', 0):+.1f}) "
        f"across {extension.get('total_scored', 0)} names"
    )
