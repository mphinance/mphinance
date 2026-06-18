"""
Signal Persistence Tracker — 21-day rolling window.

Tracks which tickers appear in scans over time to identify:
- Lifers: 20+ days in the window (strong institutional commitment)
- High Conviction: 10-19 days (sustained interest)
- New Signals: 1-3 days

Storage: local JSON under PERSISTENCE_DIR, written atomically (temp file +
os.replace) so a crash mid-write can never wipe the accumulated streaks.

NAMESPACES: the default ("scanner") writes the historical `signal_history.json`
file byte-for-byte as before, so the existing pipeline call
`update_persistence(scanned_tickers, date)` is unchanged. Any other namespace
writes `signal_history_{namespace}.json`, giving each signal type (triangle,
flow, momentum, ...) an independent day-over-day history that the confluence /
migration layer reads.

The GCS code path that used to live here was retired with the runner migration
(Cloud Run → local Hetzner box); persistence is now local-only.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta

from dossier.config import PERSISTENCE_DIR

DEFAULT_NAMESPACE = "scanner"
WINDOW_DAYS = 21


def history_path(namespace: str = DEFAULT_NAMESPACE):
    """Resolve the JSON file path for a namespace.

    The default namespace keeps the original filename (`signal_history.json`)
    for backward compatibility; every other namespace gets its own
    `signal_history_{namespace}.json`.
    """
    if not namespace or namespace == DEFAULT_NAMESPACE:
        return PERSISTENCE_DIR / "signal_history.json"
    # Sanitize so a stray namespace can't escape the data dir.
    safe = "".join(c for c in str(namespace) if c.isalnum() or c in ("_", "-")).strip("_-")
    safe = safe or DEFAULT_NAMESPACE
    if safe == DEFAULT_NAMESPACE:
        return PERSISTENCE_DIR / "signal_history.json"
    return PERSISTENCE_DIR / f"signal_history_{safe}.json"


def _load_history(namespace: str = DEFAULT_NAMESPACE) -> dict:
    """Load signal history for a namespace from local disk. Never raises."""
    path = history_path(namespace)
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, IOError, OSError):
            pass
    return {}


def _save_history(history: dict, namespace: str = DEFAULT_NAMESPACE) -> None:
    """Atomically persist signal history for a namespace.

    Writes to a temp file in the same directory then os.replace()s it over the
    target, so a crash mid-write leaves the prior file intact (never a partial
    JSON that would zero out the 21-day streaks). Never raises.
    """
    path = history_path(namespace)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".sig_hist_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(history, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        except Exception:
            # Clean up the temp file on any failure so we don't litter the dir.
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            raise
    except Exception as e:
        print(f"[tracker] failed to save '{namespace}' history: {e}")


def _prune_old_dates(history: dict, today: str) -> dict:
    try:
        cutoff = datetime.strptime(today, "%Y-%m-%d") - timedelta(days=WINDOW_DAYS)
    except (ValueError, TypeError):
        return history
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    pruned = {}
    for ticker, dates in history.items():
        if not isinstance(dates, list):
            continue
        valid = [d for d in dates if d >= cutoff_str]
        if valid:
            pruned[ticker] = valid
    return pruned


def _streak(dates: list[str]) -> int:
    """Consecutive-appearance streak (gaps of >3 calendar days break it)."""
    if not dates:
        return 0
    sorted_dates = sorted(dates, reverse=True)
    streak = 1
    for i in range(1, len(sorted_dates)):
        try:
            d1 = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d")
            d2 = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
        except (ValueError, TypeError):
            break
        if (d1 - d2).days <= 3:
            streak += 1
        else:
            break
    return streak


def classify_history(history: dict) -> dict:
    """Bucket a loaded history dict into lifers / high_conviction / new_signals.

    Pure read — does not touch disk. Shared by update_persistence() and any
    caller that has already loaded a namespaced history (e.g. the migration
    layer) and just wants the persistence classes.
    """
    lifers = []
    high_conviction = []
    new_signals = []
    all_entries = []  # EVERY tracked ticker, incl. the 4-9d "watch" band the
                      # named buckets omit — the migration layer needs all of them.

    for ticker, dates in history.items():
        if not isinstance(dates, list):
            continue
        days = len(dates)
        entry = {"ticker": ticker, "days": days, "streak": _streak(dates),
                 "class": persistence_class(days)}
        all_entries.append(entry)

        if days >= 20:
            lifers.append(entry)
        elif days >= 10:
            high_conviction.append(entry)
        elif days <= 3:
            new_signals.append(entry)

    lifers.sort(key=lambda x: x["days"], reverse=True)
    high_conviction.sort(key=lambda x: x["days"], reverse=True)
    new_signals.sort(key=lambda x: x["days"], reverse=True)
    all_entries.sort(key=lambda x: x["days"], reverse=True)

    return {
        "lifers": lifers,
        "high_conviction": high_conviction,
        "new_signals": new_signals,
        "all": all_entries,
        "summary": {
            "lifers": len(lifers),
            "high_conviction": len(high_conviction),
            "new_signals": len(new_signals),
            "total_tracked": len(history),
        },
    }


def persistence_class(days: int) -> str:
    """Map a window day-count to a persistence class label."""
    if days >= 20:
        return "lifer"
    if days >= 10:
        return "high_conviction"
    if days <= 3:
        return "new"
    return "watch"


def update_persistence(
    tickers: list[str],
    date: str,
    namespace: str = DEFAULT_NAMESPACE,
) -> dict:
    """
    Record today's scan tickers for `namespace` and return persistence classes.

    With the default namespace this reads/writes `signal_history.json` exactly as
    before (backward compatible). Any other namespace uses an independent
    `signal_history_{namespace}.json`.

    Returns dict with lifers, high_conviction, new_signals, summary.
    """
    history = _load_history(namespace)
    history = _prune_old_dates(history, date)

    for ticker in tickers or []:
        if not ticker:
            continue
        if ticker not in history:
            history[ticker] = []
        if date not in history[ticker]:
            history[ticker].append(date)
            history[ticker].sort()

    _save_history(history, namespace)

    return classify_history(history)


def load_persistence(namespace: str = DEFAULT_NAMESPACE) -> dict:
    """Read-only helper: load + classify a namespace's history without writing.

    Useful for the migration layer, which needs yesterday/today persistence
    classes per namespace without recording a new scan.
    """
    return classify_history(_prune_old_dates(_load_history(namespace), datetime.now().strftime("%Y-%m-%d")))
