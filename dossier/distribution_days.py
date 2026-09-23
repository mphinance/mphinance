"""
Distribution/Accumulation Day Count — IBD-style institutional-selling tracker.

market_regime.py reads VIX level/term-structure and SPY price action; none of
the existing stats count the one thing classic market-timing methodology (IBD's
"distribution day" count, used to call the 2000, 2008 and 2022 tops) actually
watches: how many sessions in the trailing window closed the major indices
DOWN on HIGHER volume than the prior session — the fingerprint of institutions
quietly selling into strength rather than retail panic-selling on a gap down.

A "distribution day" = index closes down >= 0.2% on volume higher than the
prior session's. An "accumulation day" is the mirror (closes up >= 0.2% on
higher volume) — institutions buying. Counted over a trailing 25-session
window (IBD's standard), tracked for both SPY and QQQ since a top can show up
in one index before the other.

0-2 distribution days = healthy uptrend. 3-4 = caution, watch closely.
5+ in either index = the market is "under pressure" — IBD's classic threshold
for downgrading from "confirmed uptrend" to "uptrend under pressure" or worse.

History is persisted date-keyed (dedup-overwrite same day), same pattern as
vol_risk_premium.py / breadth_index.py, so the dossier can report distribution
count building or clearing over N sessions instead of just today's snapshot.
"""

from __future__ import annotations

import json
from pathlib import Path

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

DISTRIBUTION_WINDOW = 25
_MOVE_THRESHOLD_PCT = 0.2
INDEXES = ("SPY", "QQQ")

# 3-color HUD thresholds (see AGENTS.md / report/template.html):
#   green #00ff41 = healthy   amber #f0b400 = caution   red #e53935 = under pressure
_HEALTHY_MAX = 2
_CAUTION_MAX = 4
_STATES = [
    (_HEALTHY_MAX, {"state": "healthy", "color": "#00ff41", "emoji": "🟢", "label": "Healthy — Uptrend Intact"}),
    (_CAUTION_MAX, {"state": "caution", "color": "#f0b400", "emoji": "🟡", "label": "Caution — Watch Closely"}),
    (float("inf"), {"state": "pressure", "color": "#e53935", "emoji": "🔴", "label": "Under Pressure — Institutional Selling"}),
]


def classify_pressure(distribution_count: int) -> dict:
    """Map a trailing-window distribution-day count to a state dict."""
    for ceiling, info in _STATES:
        if distribution_count <= ceiling:
            return dict(info)
    return dict(_STATES[-1][1])


def count_session_days(hist, window: int = DISTRIBUTION_WINDOW) -> dict:
    """
    Classify each session in the trailing ``window`` as distribution,
    accumulation or neutral (close-to-close % change vs. prior day's volume).

    Never raises — malformed/short input yields a zeroed result. Returns:
        {"distribution_days": int, "accumulation_days": int,
         "sessions_counted": int, "distribution_dates": [str, ...]}
    """
    empty = {"distribution_days": 0, "accumulation_days": 0, "sessions_counted": 0, "distribution_dates": []}
    if hist is None or hist.empty or "Close" not in hist.columns or "Volume" not in hist.columns:
        return empty

    closes = hist["Close"]
    volumes = hist["Volume"]
    n = len(hist)
    if n < 2:
        return empty

    start = max(1, n - window)
    distribution = 0
    accumulation = 0
    counted = 0
    distribution_dates = []

    for i in range(start, n):
        prev_close = closes.iloc[i - 1]
        cur_close = closes.iloc[i]
        prev_vol = volumes.iloc[i - 1]
        cur_vol = volumes.iloc[i]
        if prev_close in (None, 0) or any(
            v is None for v in (cur_close, prev_vol, cur_vol)
        ):
            continue
        try:
            pct_change = (float(cur_close) - float(prev_close)) / float(prev_close) * 100
            cur_vol_f = float(cur_vol)
            prev_vol_f = float(prev_vol)
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        if pct_change != pct_change or cur_vol_f != cur_vol_f or prev_vol_f != prev_vol_f:
            continue  # NaN in price/volume data — skip rather than misclassify

        counted += 1
        higher_volume = cur_vol_f > prev_vol_f
        if pct_change <= -_MOVE_THRESHOLD_PCT and higher_volume:
            distribution += 1
            label = hist.index[i]
            distribution_dates.append(str(getattr(label, "date", lambda: label)()))
        elif pct_change >= _MOVE_THRESHOLD_PCT and higher_volume:
            accumulation += 1

    return {
        "distribution_days": distribution,
        "accumulation_days": accumulation,
        "sessions_counted": counted,
        "distribution_dates": distribution_dates,
    }


def compute_distribution_days(index_histories: dict) -> dict:
    """
    Aggregate per-index session counts (see ``count_session_days``) across
    the indexes in ``index_histories`` ({"SPY": df, "QQQ": df, ...}) into one
    snapshot. The overall state is driven by the WORST (highest distribution
    count) index — a top forming in either SPY or QQQ matters.
    """
    per_index = {}
    for symbol, hist in index_histories.items():
        per_index[symbol] = count_session_days(hist)

    if not per_index:
        return {"per_index": {}, "worst_index": None, "distribution_days": 0,
                "accumulation_days": 0, **classify_pressure(0)}

    worst_symbol = max(per_index, key=lambda s: per_index[s]["distribution_days"])
    worst = per_index[worst_symbol]

    return {
        "per_index": per_index,
        "worst_index": worst_symbol,
        "distribution_days": worst["distribution_days"],
        "accumulation_days": worst["accumulation_days"],
        **classify_pressure(worst["distribution_days"]),
    }


def fetch_and_compute_distribution_days(indexes: tuple = INDEXES, window: int = DISTRIBUTION_WINDOW) -> dict:
    """
    Fetch SPY/QQQ history and compute today's distribution-day snapshot.
    Never raises — a fetch/validation failure for an index just drops it
    from the aggregate; total failure across all indexes yields
    ``{"available": False, "reason": ...}``.
    """
    import yfinance as yf

    index_histories = {}
    reasons = []
    for symbol in indexes:
        try:
            hist = yf.Ticker(symbol).history(period="3mo")
        except Exception as exc:
            reasons.append(f"{symbol} fetch failed: {exc}")
            continue
        ok, reason = check_yfinance_history(hist, symbol, min_rows=window + 1)
        if not ok:
            reasons.append(reason)
            continue
        index_histories[symbol] = hist

    if not index_histories:
        return {"available": False, "reason": "; ".join(reasons) or "no index data available"}

    result = compute_distribution_days(index_histories)
    result["available"] = True
    return result


def load_history(path) -> list:
    """Load the distribution-day history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_distribution_days(history: list, entry: dict) -> list:
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


def record_distribution_days(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_distribution_days(load_history(path), entry)
    save_history(path, updated)
    return updated


def distribution_trend(history: list, date: str, lookback: int = 5) -> dict:
    """
    Compare today's distribution-day count to the entry ``lookback``
    sessions back.

    Returns {"delta": int, "direction": "building"|"clearing"|"flat",
    "lookback_date": str|None}. Empty/insufficient history → delta 0, flat.
    """
    dated = [e for e in history if e.get("date") is not None and e.get("distribution_days") is not None]
    dated.sort(key=lambda e: e["date"])
    idx = next((i for i, e in enumerate(dated) if e["date"] == date), None)
    if idx is None or idx - lookback < 0:
        return {"delta": 0, "direction": "flat", "lookback_date": None}

    prior = dated[idx - lookback]
    delta = dated[idx]["distribution_days"] - prior["distribution_days"]
    if delta >= 2:
        direction = "building"
    elif delta <= -2:
        direction = "clearing"
    else:
        direction = "flat"
    return {"delta": delta, "direction": direction, "lookback_date": prior["date"]}


def format_distribution_days_text(data: dict) -> str:
    """One-line console summary, matching the style of format_vrp_text()."""
    if not data.get("available"):
        return f"⏭️  Distribution days unavailable ({data.get('reason', 'unknown')})"
    return (
        f"{data['emoji']} Distribution Days: {data['label']} — "
        f"{data['distribution_days']} distribution / {data['accumulation_days']} accumulation "
        f"in {DISTRIBUTION_WINDOW}d (worst: {data.get('worst_index', 'n/a')})"
    )
