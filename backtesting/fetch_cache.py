"""On-disk fetch cache — journal-style resume for expensive data pulls.

The problem this solves
-----------------------
Our backtests fetch OHLC over the network inside the main loop and never
persist it. When anything downstream throws — an evaluation bug, a bad
ticker, a rate-limit halfway through — the whole run dies and the *next*
run re-downloads every bar again, paying full network cost for data we
already had.

The pattern (adapted from six-ddc/codex-dynamic-workflows' journal cache,
MIT-licensed): key every expensive call by a stable hash of its inputs and
persist the result to disk the instant it succeeds. A re-run reuses every
completed pull and only re-fetches the misses. A crash no longer nukes the
expensive work that already finished.

This module is deliberately dependency-free (stdlib only) so it can be unit
tested without pandas, yfinance, or a network. It stores whatever picklable
object the fetch function returns — a DataFrame, a dict, anything.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
import tempfile
import time
from typing import Callable, Dict, Iterable, List, Optional, TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T")


def stable_key(*parts: object) -> str:
    """Deterministic short hash of the given parts.

    Uses sorted-key JSON so dict ordering never changes the key, and
    ``default=str`` so datetimes and other odd types hash by their string
    form instead of blowing up.
    """
    payload = json.dumps(parts, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class FetchCache:
    """A tiny persistent key -> object store backed by pickle files.

    Each entry is one file, written atomically (temp file + ``os.replace``)
    so a crash mid-write can never leave a half-written entry that poisons
    the next run. An optional ``max_age_seconds`` treats stale entries as
    misses, so day-old OHLC isn't silently served to a fresh backtest while
    still giving full resume within a session.
    """

    def __init__(self, cache_dir: str, max_age_seconds: Optional[float] = None):
        self.cache_dir = cache_dir
        self.max_age_seconds = max_age_seconds
        os.makedirs(cache_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.pkl")

    def _fresh(self, path: str) -> bool:
        if self.max_age_seconds is None:
            return True
        try:
            age = time.time() - os.path.getmtime(path)
        except OSError:
            return False
        return age <= self.max_age_seconds

    def get(self, key: str) -> Optional[object]:
        """Return the cached object, or None on miss / stale / unreadable."""
        path = self._path(key)
        if not os.path.exists(path) or not self._fresh(path):
            return None
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception as e:  # a corrupt entry is a miss, never a crash
            log.warning("FetchCache: unreadable entry %s (%s); treating as miss", key, e)
            return None

    def put(self, key: str, value: object) -> None:
        """Persist ``value`` under ``key`` atomically."""
        path = self._path(key)
        fd, tmp = tempfile.mkstemp(dir=self.cache_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(tmp, path)  # atomic on POSIX
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def clear(self) -> int:
        """Delete all entries. Returns the number removed (mostly for tests)."""
        removed = 0
        for name in os.listdir(self.cache_dir):
            if name.endswith(".pkl"):
                os.remove(os.path.join(self.cache_dir, name))
                removed += 1
        return removed


def cached_fetch_map(
    items: Iterable[str],
    fetch_missing: Callable[[List[str]], Dict[str, T]],
    cache: FetchCache,
    namespace: str,
) -> Dict[str, T]:
    """Resolve ``items`` to values, fetching only the cache misses.

    ``fetch_missing`` is called at most once, with just the missing items,
    and must return a ``{item: value}`` dict. Whatever it returns is
    persisted per-item, so the *next* call reuses it. Items the fetcher
    can't resolve are simply absent from the result — same contract as a
    plain ``{ticker: df}`` fetch loop.

    ``namespace`` should encode everything that makes a value distinct
    besides the item itself (e.g. start date + bar interval), so a different
    backtest window doesn't reuse another window's bars.
    """
    items = list(items)
    resolved: Dict[str, T] = {}
    missing: List[str] = []

    for item in items:
        hit = cache.get(stable_key(namespace, item))
        if hit is not None:
            resolved[item] = hit  # type: ignore[assignment]
        else:
            missing.append(item)

    if not missing:
        log.info("FetchCache[%s]: %d/%d served from cache", namespace, len(resolved), len(items))
        return resolved

    log.info(
        "FetchCache[%s]: %d hit, %d miss -> fetching",
        namespace, len(resolved), len(missing),
    )
    fetched = fetch_missing(missing) or {}
    for item, value in fetched.items():
        cache.put(stable_key(namespace, item), value)
        resolved[item] = value
    return resolved
