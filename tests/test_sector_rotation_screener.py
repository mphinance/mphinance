"""Tests for dossier/sector_rotation_screener.py — Sector Rotation Screener."""

import pandas as pd
import pytest

from dossier.sector_rotation_screener import (
    _filter_to_hot_sectors,
    _match_sector,
    _rsi_health_score,
    _sector_rs_score,
    _trend_score,
    _volume_momentum_score,
    score_rotation,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_hist(n: int = 60, price: float = 100.0, vol_recent_mult: float = 1.2) -> pd.DataFrame:
    """Synthetic OHLCV history with optional volume expansion in the last 5 bars."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    closes = [price * (1 + 0.002 * i) for i in range(n)]
    base_vol = 1_000_000
    vols = [int(base_vol * (vol_recent_mult if i >= n - 5 else 1.0)) for i in range(n)]
    r = price * 0.012
    return pd.DataFrame(
        {
            "Open":   [c - r * 0.1 for c in closes],
            "High":   [c + r / 2   for c in closes],
            "Low":    [c - r / 2   for c in closes],
            "Close":  closes,
            "Volume": vols,
        },
        index=idx,
    )


def _tv_stock(
    ticker="TEST",
    price=100.0,
    tv_sector="Technology",
    ema_20=96.0,
    sma_50=90.0,
    sma_200=80.0,
    avg_vol_30d=500_000,
    rsi=55.0,
    market_cap=5e9,
    perf_3m=15.0,
    sector_etf="XLK",
    sector_name="Technology",
    sector_rs=3.5,
    sector_signal="reversing_up",
) -> dict:
    return {
        "ticker":        ticker,
        "name":          ticker,
        "price":         price,
        "volume":        400_000,
        "avg_vol_30d":   avg_vol_30d,
        "market_cap":    market_cap,
        "tv_sector":     tv_sector,
        "sma_200":       sma_200,
        "sma_50":        sma_50,
        "ema_20":        ema_20,
        "rsi":           rsi,
        "perf_1w":       1.5,
        "perf_1m":       5.0,
        "perf_3m":       perf_3m,
        "sector_etf":    sector_etf,
        "sector_name":   sector_name,
        "sector_rs":     sector_rs,
        "sector_signal": sector_signal,
    }


def _hot_sectors() -> dict[str, dict]:
    return {
        "XLK": {"name": "Technology", "rotation": "reversing_up", "composite_rs": 3.5},
        "XLF": {"name": "Financials",  "rotation": "accelerating", "composite_rs": 2.1},
    }


# ─── _match_sector ────────────────────────────────────────────────

def test_match_sector_technology():
    etf, row = _match_sector("Technology", _hot_sectors())
    assert etf == "XLK"
    assert row["name"] == "Technology"


def test_match_sector_finance():
    etf, row = _match_sector("Finance", _hot_sectors())
    assert etf == "XLF"


def test_match_sector_case_insensitive():
    etf, _ = _match_sector("TECHNOLOGY", _hot_sectors())
    assert etf == "XLK"


def test_match_sector_partial():
    etf, _ = _match_sector("High Technology", _hot_sectors())
    assert etf == "XLK"


def test_match_sector_no_match():
    etf, row = _match_sector("Energy", _hot_sectors())
    assert etf is None
    assert row is None


def test_match_sector_empty():
    etf, row = _match_sector("", _hot_sectors())
    assert etf is None


# ─── _filter_to_hot_sectors ───────────────────────────────────────

def test_filter_keeps_matching_stock():
    stocks = [_tv_stock(tv_sector="Technology")]
    result = _filter_to_hot_sectors(stocks, _hot_sectors(), verbose=False)
    assert len(result) == 1
    assert result[0]["sector_etf"] == "XLK"


def test_filter_drops_cold_sector():
    stocks = [_tv_stock(tv_sector="Energy")]
    result = _filter_to_hot_sectors(stocks, _hot_sectors(), verbose=False)
    assert len(result) == 0


def test_filter_mixed_sectors():
    stocks = [
        _tv_stock("A", tv_sector="Technology"),
        _tv_stock("B", tv_sector="Energy"),
        _tv_stock("C", tv_sector="Financial Services"),
    ]
    result = _filter_to_hot_sectors(stocks, _hot_sectors(), verbose=False)
    assert len(result) == 2
    tickers = {r["ticker"] for r in result}
    assert tickers == {"A", "C"}


def test_filter_empty_input():
    assert _filter_to_hot_sectors([], _hot_sectors(), verbose=False) == []


def test_filter_empty_hot_sectors():
    stocks = [_tv_stock(tv_sector="Technology")]
    result = _filter_to_hot_sectors(stocks, {}, verbose=False)
    assert len(result) == 0


# ─── _sector_rs_score ─────────────────────────────────────────────

def test_sector_rs_high_with_reversal_bonus():
    score = _sector_rs_score(4.5, "reversing_up")
    assert score == 30  # capped at 30


def test_sector_rs_high_accelerating():
    score = _sector_rs_score(4.5, "accelerating")
    assert score == 28


def test_sector_rs_moderate():
    score = _sector_rs_score(2.5, "reversing_up")
    assert score == 23  # 18 base + 5 bonus


def test_sector_rs_low():
    score = _sector_rs_score(0.2, "stable")
    assert score == 4


def test_sector_rs_monotone():
    assert _sector_rs_score(0.2, "") < _sector_rs_score(1.0, "") < _sector_rs_score(3.0, "")


# ─── _trend_score ─────────────────────────────────────────────────

def test_trend_full_stack():
    assert _trend_score(100.0, 96.0, 90.0, 80.0) == 25


def test_trend_missing_sma200():
    score = _trend_score(100.0, 96.0, 90.0, None)
    assert score == 19  # 8 + 8 + 3 = 19


def test_trend_below_ema20():
    score = _trend_score(90.0, 96.0, 85.0, 80.0)
    assert score < 25


def test_trend_below_all():
    assert _trend_score(70.0, 80.0, 85.0, 90.0) == 0


# ─── _rsi_health_score ────────────────────────────────────────────

def test_rsi_sweet_spot():
    assert _rsi_health_score(58.0) == 25


def test_rsi_borderline_low():
    assert _rsi_health_score(47.0) == 18


def test_rsi_borderline_high():
    assert _rsi_health_score(68.0) == 18


def test_rsi_overbought():
    assert _rsi_health_score(80.0) == 0


def test_rsi_oversold():
    assert _rsi_health_score(30.0) == 0


def test_rsi_none():
    assert _rsi_health_score(None) == 8


def test_rsi_monotone():
    assert _rsi_health_score(58) > _rsi_health_score(47) > _rsi_health_score(38)


# ─── _volume_momentum_score ───────────────────────────────────────

def test_volume_momentum_strong_expansion():
    hist = _make_hist(vol_recent_mult=1.5)
    assert _volume_momentum_score(hist) == 20


def test_volume_momentum_moderate():
    hist = _make_hist(vol_recent_mult=1.25)
    assert _volume_momentum_score(hist) == 15


def test_volume_momentum_flat():
    hist = _make_hist(vol_recent_mult=1.05)
    assert _volume_momentum_score(hist) == 10


def test_volume_momentum_contracting():
    hist = _make_hist(vol_recent_mult=0.85)
    assert _volume_momentum_score(hist) == 5


def test_volume_momentum_heavy_contraction():
    hist = _make_hist(vol_recent_mult=0.5)
    assert _volume_momentum_score(hist) == 2


def test_volume_momentum_insufficient_rows():
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    hist = pd.DataFrame({"Volume": [500_000] * 10}, index=idx)
    assert _volume_momentum_score(hist) == 5


# ─── score_rotation (integration via monkeypatch) ─────────────────

def test_score_rotation_healthy_stock_qualifies(monkeypatch):
    """Stock in a rotating sector with strong volume should produce a valid score."""
    import yfinance as yf

    hist = _make_hist(n=60, price=100.0, vol_recent_mult=1.4)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    last_price = float(hist["Close"].iloc[-1])
    tv = _tv_stock(
        price=last_price,
        ema_20=last_price * 0.97,
        sma_50=last_price * 0.93,
        sma_200=last_price * 0.80,
        rsi=58.0,
        sector_rs=3.5,
        sector_signal="reversing_up",
    )
    result = score_rotation("TECH", tv_data=tv)
    assert result is not None
    assert 0 <= result["score"] <= 100
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert result["sector_signal"] == "reversing_up"


def test_score_rotation_empty_history_returns_none(monkeypatch):
    """Empty yfinance history → return None without raising."""
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_rotation("EMPTY") is None


def test_score_rotation_short_history_returns_none(monkeypatch):
    """Fewer than 20 bars → return None without raising."""
    import yfinance as yf

    hist = _make_hist(n=10)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_rotation("SHORT") is None


def test_score_rotation_breakdown_keys(monkeypatch):
    """score_breakdown must contain all four expected keys."""
    import yfinance as yf

    hist = _make_hist(n=60, vol_recent_mult=1.3)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    last_price = float(hist["Close"].iloc[-1])
    tv = _tv_stock(price=last_price, rsi=55.0)
    result = score_rotation("KEYS", tv_data=tv)
    if result is not None:
        for key in ("sector_rs", "trend", "rsi", "volume"):
            assert key in result["score_breakdown"]


def test_score_rotation_total_equals_sum_of_breakdown(monkeypatch):
    """score must equal the sum of score_breakdown values."""
    import yfinance as yf

    hist = _make_hist(n=60, vol_recent_mult=1.3)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    last_price = float(hist["Close"].iloc[-1])
    tv = _tv_stock(price=last_price, rsi=55.0)
    result = score_rotation("SUM", tv_data=tv)
    if result is not None:
        assert result["score"] == sum(result["score_breakdown"].values())
