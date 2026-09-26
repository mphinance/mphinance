"""
Volatility Risk Premium (VRP) — implied vol vs. what the tape actually did.

market_regime.py and sf_market_weather.py both classify the market off the
*absolute level* or *term structure* of VIX. Neither compares that
forward-looking implied-vol read against the volatility SPY actually
realized. VRP does:

    VRP = VIX (30d implied) − realized SPY volatility (trailing 20 trading
          days, close-to-close, annualized)

A positive VRP means options are pricing in more movement than the tape has
delivered lately — the classic backdrop for selling premium (CSPs, covered
calls, credit spreads). A negative VRP means realized vol is running hotter
than what's priced in — a caution flag for premium sellers and a green light
for buying options outright.

History is persisted date-keyed (dedup-overwrite same day), same pattern as
breadth_index.py / mood_ring.py, so the dossier can report VRP compressing or
expanding over N sessions instead of just today's snapshot.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

try:
    from dossier.utils.validate_api import check_yfinance_history
except ImportError:  # pragma: no cover - import-path fallback, mirrors market_regime.py
    def check_yfinance_history(df, ticker, min_rows=2):
        if df is None or df.empty:
            return False, f"{ticker}: empty history"
        if len(df) < min_rows:
            return False, f"{ticker}: only {len(df)} row(s)"
        missing = {"Close", "High", "Low", "Volume"} - set(df.columns)
        if missing:
            return False, f"{ticker}: missing columns {sorted(missing)}"
        return True, ""

REALIZED_VOL_WINDOW = 20
_TRADING_DAYS = 252

# 3-color HUD thresholds (see AGENTS.md / report/template.html):
#   green #00ff41 = premium rich (sell vol)   amber #f0b400 = fair
#   red   #e53935 = premium cheap (buy vol)
_STATES = [
    (5.0, {"state": "rich", "color": "#00ff41", "emoji": "💰", "label": "Premium Rich — Favor Selling Vol"}),
    (-5.0, {"state": "fair", "color": "#f0b400", "emoji": "⚖️", "label": "Fairly Priced"}),
    (float("-inf"), {"state": "cheap", "color": "#e53935", "emoji": "🎯", "label": "Premium Cheap — Favor Buying Vol"}),
]


def classify_vrp(vrp: float) -> dict:
    """Map a VRP (VIX − realized vol, in points) to a state dict."""
    for floor, info in _STATES:
        if vrp >= floor:
            return dict(info)
    return dict(_STATES[-1][1])


def compute_realized_vol(spy_hist, window: int = REALIZED_VOL_WINDOW):
    """
    Annualized close-to-close realized volatility (%) over the trailing
    ``window`` sessions. Returns None (never raises) when there isn't enough
    clean data to compute it.
    """
    if spy_hist is None or spy_hist.empty or "Close" not in spy_hist.columns:
        return None
    closes = spy_hist["Close"].dropna()
    if len(closes) < window + 1:
        return None
    log_returns = np.log(closes / closes.shift(1)).dropna()
    if len(log_returns) < window:
        return None
    daily_std = float(log_returns.iloc[-window:].std())
    if np.isnan(daily_std):
        return None
    return round(daily_std * np.sqrt(_TRADING_DAYS) * 100, 2)


def compute_vrp(vix_level: float, realized_vol: float) -> dict:
    """Build a VRP snapshot dict from an already-fetched VIX level + realized vol."""
    vrp = round(vix_level - realized_vol, 2)
    ratio = round(vix_level / realized_vol, 2) if realized_vol else None
    result = {
        "vix_level": round(vix_level, 2),
        "realized_vol_20d": round(realized_vol, 2),
        "vrp": vrp,
        "vrp_ratio": ratio,
        "available": True,
    }
    result.update(classify_vrp(vrp))
    return result


def fetch_and_compute_vrp(vix_level=None) -> dict:
    """
    Fetch SPY history and compute today's VRP snapshot. Never raises — any
    fetch/validation failure yields ``{"available": False, "reason": ...}``
    so the caller can skip persistence without crashing the pipeline stage.

    Pass ``vix_level`` when the caller already has a fresh VIX read (e.g.
    market_regime.detect_regime()) to avoid a duplicate ^VIX fetch.
    """
    import yfinance as yf

    if vix_level is None:
        try:
            vix_hist = yf.Ticker("^VIX").history(period="5d")
        except Exception as exc:
            return {"available": False, "reason": f"^VIX fetch failed: {exc}"}
        ok, reason = check_yfinance_history(vix_hist, "^VIX", min_rows=1)
        if not ok:
            return {"available": False, "reason": reason}
        vix_level = float(vix_hist["Close"].iloc[-1])

    try:
        spy_hist = yf.Ticker("SPY").history(period="2mo")
    except Exception as exc:
        return {"available": False, "reason": f"SPY fetch failed: {exc}"}

    ok, reason = check_yfinance_history(spy_hist, "SPY", min_rows=REALIZED_VOL_WINDOW + 1)
    if not ok:
        return {"available": False, "reason": reason}

    realized_vol = compute_realized_vol(spy_hist)
    if realized_vol is None:
        return {"available": False, "reason": "SPY realized vol could not be computed"}

    return compute_vrp(vix_level, realized_vol)


def load_history(path) -> list:
    """Load the VRP-history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_vrp(history: list, entry: dict) -> list:
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


def record_vrp(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_vrp(load_history(path), entry)
    save_history(path, updated)
    return updated


def vrp_trend(history: list, date: str, lookback: int = 5) -> dict:
    """
    Compare today's VRP to the entry ``lookback`` sessions back.

    Returns {"delta": float, "direction": "richening"|"cheapening"|"flat",
    "lookback_date": str|None}. Empty/insufficient history → delta 0, flat.
    """
    dated = [e for e in history if e.get("date") is not None and e.get("vrp") is not None]
    dated.sort(key=lambda e: e["date"])
    idx = next((i for i, e in enumerate(dated) if e["date"] == date), None)
    if idx is None or idx - lookback < 0:
        return {"delta": 0.0, "direction": "flat", "lookback_date": None}

    prior = dated[idx - lookback]
    delta = round(dated[idx]["vrp"] - prior["vrp"], 2)
    if delta >= 3:
        direction = "richening"
    elif delta <= -3:
        direction = "cheapening"
    else:
        direction = "flat"
    return {"delta": delta, "direction": direction, "lookback_date": prior["date"]}


def format_vrp_text(vrp_data: dict) -> str:
    """One-line console summary, matching the style of format_breadth_text()."""
    if not vrp_data.get("available"):
        return f"⏭️  VRP unavailable ({vrp_data.get('reason', 'unknown')})"
    return (
        f"{vrp_data['emoji']} VRP {vrp_data['vrp']:+.1f} pts ({vrp_data['label']}) — "
        f"VIX {vrp_data['vix_level']:.1f} vs {vrp_data['realized_vol_20d']:.1f}% realized (20d)"
    )
