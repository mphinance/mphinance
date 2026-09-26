"""Tests for backtesting.fetch_cache — the journal-style resume cache.

These deliberately use plain dicts/strings (not DataFrames) so they run with
no pandas, yfinance, or network — just the stdlib cache logic.
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backtesting"))

from fetch_cache import FetchCache, cached_fetch_map, stable_key


def test_stable_key_is_order_independent():
    # Same logical content, different dict ordering -> same key.
    assert stable_key("ns", {"a": 1, "b": 2}) == stable_key("ns", {"b": 2, "a": 1})
    assert stable_key("ns", "AAPL") != stable_key("ns", "TSLA")


def test_put_get_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        cache = FetchCache(d)
        cache.put("k1", {"close": [1, 2, 3]})
        assert cache.get("k1") == {"close": [1, 2, 3]}


def test_get_miss_returns_none():
    with tempfile.TemporaryDirectory() as d:
        assert FetchCache(d).get("absent") is None


def test_cached_fetch_map_only_fetches_misses():
    with tempfile.TemporaryDirectory() as d:
        cache = FetchCache(d)
        calls = []

        def fetch(missing):
            calls.append(list(missing))
            return {t: f"data-{t}" for t in missing}

        # First pass: everything is a miss.
        r1 = cached_fetch_map(["AAPL", "TSLA"], fetch, cache, "ohlc:1d:2026-01-01")
        assert r1 == {"AAPL": "data-AAPL", "TSLA": "data-TSLA"}
        assert calls == [["AAPL", "TSLA"]]

        # Second pass: AAPL cached, only NVDA should be fetched.
        r2 = cached_fetch_map(["AAPL", "NVDA"], fetch, cache, "ohlc:1d:2026-01-01")
        assert r2 == {"AAPL": "data-AAPL", "NVDA": "data-NVDA"}
        assert calls[-1] == ["NVDA"]  # AAPL served from cache, not re-fetched


def test_namespace_isolates_windows():
    with tempfile.TemporaryDirectory() as d:
        cache = FetchCache(d)
        fetch = lambda missing: {t: f"v-{t}" for t in missing}
        cached_fetch_map(["AAPL"], fetch, cache, "ohlc:1d:2026-01-01")

        seen = []

        def fetch2(missing):
            seen.extend(missing)
            return {t: f"v-{t}" for t in missing}

        # Different window namespace -> AAPL is a miss again.
        cached_fetch_map(["AAPL"], fetch2, cache, "ohlc:1d:2026-02-01")
        assert seen == ["AAPL"]


def test_items_fetcher_cannot_resolve_are_absent():
    with tempfile.TemporaryDirectory() as d:
        cache = FetchCache(d)
        # Fetcher returns nothing for a delisted ticker.
        result = cached_fetch_map(["DEAD"], lambda missing: {}, cache, "ns")
        assert result == {}


def test_ttl_expiry_treated_as_miss():
    with tempfile.TemporaryDirectory() as d:
        cache = FetchCache(d, max_age_seconds=0.05)
        cache.put("k", "value")
        assert cache.get("k") == "value"
        time.sleep(0.1)
        assert cache.get("k") is None  # stale -> miss


def test_corrupt_entry_is_a_miss_not_a_crash():
    with tempfile.TemporaryDirectory() as d:
        cache = FetchCache(d)
        # Write garbage where a pickle is expected.
        with open(os.path.join(d, "bad.pkl"), "w") as f:
            f.write("not a pickle")
        assert cache.get("bad") is None


def test_no_temp_files_left_after_put():
    with tempfile.TemporaryDirectory() as d:
        cache = FetchCache(d)
        cache.put("k", {"x": 1})
        leftovers = [n for n in os.listdir(d) if n.endswith(".tmp")]
        assert leftovers == []
