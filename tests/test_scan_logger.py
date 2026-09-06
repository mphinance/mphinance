"""Tests for dossier.backtesting.scan_logger pure helpers."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from dossier.backtesting.scan_logger import (
    _append_entry,
    _get_ticker_snapshot,
    _load_archive,
    log_todays_picks,
    update_forward_returns,
)


def test_load_archive_missing_file():
    with patch("dossier.backtesting.scan_logger.SCAN_ARCHIVE", Path("/tmp/_absent_scan_archive.jsonl")):
        assert _load_archive() == []


def test_load_archive_skips_malformed_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"ticker": "AAPL", "date": "2026-01-01"}\n')
        f.write("not json\n")
        f.write('{"ticker": "MSFT", "date": "2026-01-02"}\n')
        path = Path(f.name)
    try:
        with patch("dossier.backtesting.scan_logger.SCAN_ARCHIVE", path):
            entries = _load_archive()
        assert [e["ticker"] for e in entries] == ["AAPL", "MSFT"]
    finally:
        os.unlink(path)


def test_append_entry_roundtrip():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = Path(f.name)
    try:
        with patch("dossier.backtesting.scan_logger.SCAN_ARCHIVE", path):
            _append_entry({"ticker": "TSLA", "date": "2026-06-01"})
            _append_entry({"ticker": "NVDA", "date": "2026-06-01"})
            entries = _load_archive()
        assert [e["ticker"] for e in entries] == ["TSLA", "NVDA"]
    finally:
        os.unlink(path)


def test_get_ticker_snapshot_missing_file_returns_empty():
    with patch("dossier.backtesting.scan_logger.PROJECT_ROOT", Path("/tmp/_absent_project_root")):
        assert _get_ticker_snapshot("AAPL") == {}


def test_get_ticker_snapshot_reads_oscillators():
    """Regression: _get_ticker_snapshot referenced an undefined `osc` name,
    so the try/except swallowed a NameError and this always returned {}."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ticker_dir = root / "docs" / "ticker" / "AAPL"
        ticker_dir.mkdir(parents=True)
        (ticker_dir / "latest.json").write_text(json.dumps({
            "currentPrice": 210.5,
            "technical_analysis": {
                "ema_stack": "FULL BULLISH",
                "oscillators": {
                    "rsi_14": 62.3,
                    "di_plus": 28.1,
                    "di_minus": 12.4,
                    "williams_r": -18.2,
                    "mfi": 55.0,
                },
            },
            "scores": {"grade": "A", "technical": 88},
        }))

        with patch("dossier.backtesting.scan_logger.PROJECT_ROOT", root):
            snapshot = _get_ticker_snapshot("AAPL")

    assert snapshot["rsi_14"] == 62.3
    assert snapshot["di_plus"] == 28.1
    assert snapshot["di_minus"] == 12.4
    assert snapshot["williams_r"] == -18.2
    assert snapshot["mfi"] == 55.0
    assert snapshot["grade"] == "A"


def test_log_todays_picks_dedupes_existing_entries():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        api_dir = root / "docs" / "api"
        api_dir.mkdir(parents=True)
        picks_path = api_dir / "daily-picks.json"
        picks_path.write_text(json.dumps({
            "date": "2026-07-19",
            "picks": [
                {"ticker": "AAPL", "score": 80, "grade": "A", "medal": "gold"},
                {"ticker": "MSFT", "score": 70, "grade": "B", "medal": "silver"},
            ],
        }))
        archive_path = root / "docs" / "backtesting" / "scan_archive.jsonl"
        archive_path.parent.mkdir(parents=True)
        archive_path.write_text(json.dumps({"ticker": "AAPL", "date": "2026-07-19"}) + "\n")

        with patch("dossier.backtesting.scan_logger.PICKS_PATH", picks_path), \
             patch("dossier.backtesting.scan_logger.SCAN_ARCHIVE", archive_path), \
             patch("dossier.backtesting.scan_logger.DOSSIER_DIR", api_dir), \
             patch("dossier.backtesting.scan_logger.PROJECT_ROOT", root):
            log_todays_picks()
            entries = _load_archive()

        tickers = [e["ticker"] for e in entries]
        assert tickers.count("AAPL") == 1  # already logged, not duplicated
        assert "MSFT" in tickers


def test_log_todays_picks_missing_file_noop():
    with patch("dossier.backtesting.scan_logger.PICKS_PATH", Path("/tmp/_absent_daily_picks.json")), \
         patch("dossier.backtesting.scan_logger.SCAN_ARCHIVE", Path("/tmp/_absent_scan_archive_2.jsonl")):
        log_todays_picks()  # should print an error and return without raising


def test_update_forward_returns_uses_ticker_history_not_download():
    """Regression: yf.download() returns MultiIndex columns on the yfinance
    version this pipeline runs, which makes hist["Close"].iloc[d] a 1-element
    Series — float() on it raises "not 'Series'", caught by the bare except,
    silently leaving every entry unvalidated. This ran in prod for 6+ weeks
    with 0/158 archive entries ever getting a fwd_5d. yf.Ticker().history()
    doesn't have that problem (same fix already used by
    track_record_generator.py's _get_forward_returns)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({"ticker": "AAPL", "date": "2020-01-01", "price": 100.0}) + "\n")
        path = Path(f.name)

    import pandas as pd
    closes = [100.0 + i for i in range(22)]  # enough rows for the fwd_21d lookup
    fake_ticker = MagicMock()
    fake_ticker.history.return_value = pd.DataFrame({"Close": closes})

    try:
        with patch("dossier.backtesting.scan_logger.SCAN_ARCHIVE", path), \
             patch("yfinance.Ticker", return_value=fake_ticker), \
             patch("time.sleep"):
            update_forward_returns()
            entries = _load_archive()
    finally:
        os.unlink(path)

    assert len(entries) == 1
    entry = entries[0]
    assert entry["fwd_5d"] == round((closes[5] - 100.0) / 100.0 * 100, 2)
    assert entry["fwd_21d"] == round((closes[21] - 100.0) / 100.0 * 100, 2)
