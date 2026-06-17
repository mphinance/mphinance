"""Tests for dossier/utils/indicators.py shared helpers."""
import math
import pandas as pd
import numpy as np
import pytest

from dossier.utils.indicators import _ema, _sma, _rsi, _macd, _safe


# ─── Fixed input series ───────────────────────────────────────────

PRICES = pd.Series([10.0, 11.0, 10.5, 12.0, 11.5, 13.0, 12.5, 14.0, 13.5, 15.0])


# ─── _ema ─────────────────────────────────────────────────────────

def test_ema_returns_series():
    result = _ema(PRICES, span=3)
    assert isinstance(result, pd.Series)
    assert len(result) == len(PRICES)


def test_ema_last_value_reasonable():
    result = _ema(PRICES, span=3)
    # EMA of rising prices should be between first and last price
    assert PRICES.iloc[0] < result.iloc[-1] < PRICES.iloc[-1] * 1.1


def test_ema_span1_equals_original():
    # span=1 → weight alpha=1 → EMA == series itself
    result = _ema(PRICES, span=1)
    pd.testing.assert_series_equal(result, PRICES)


# ─── _sma ─────────────────────────────────────────────────────────

def test_sma_returns_series():
    result = _sma(PRICES, window=3)
    assert isinstance(result, pd.Series)


def test_sma_first_window_minus_1_is_nan():
    result = _sma(PRICES, window=3)
    # first window-1 values should be NaN
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert not pd.isna(result.iloc[2])


def test_sma_known_value():
    result = _sma(PRICES, window=3)
    # index 2: mean of [10, 11, 10.5] = 10.5
    assert math.isclose(result.iloc[2], (10.0 + 11.0 + 10.5) / 3)


# ─── _rsi ─────────────────────────────────────────────────────────

def test_rsi_values_in_range():
    result = _rsi(PRICES, window=3)
    valid = result.dropna()
    assert (valid >= 0).all() and (valid <= 100).all()


def test_rsi_rising_series_above_50():
    rising = pd.Series([float(i) for i in range(1, 21)])
    rsi = _rsi(rising, window=5).dropna()
    assert rsi.iloc[-1] > 50


def test_rsi_falling_series_below_50():
    falling = pd.Series([float(i) for i in range(20, 0, -1)])
    rsi = _rsi(falling, window=5).dropna()
    assert rsi.iloc[-1] < 50


# ─── _macd ────────────────────────────────────────────────────────

def test_macd_returns_three_series():
    long_prices = pd.Series([float(i) for i in range(1, 51)])
    macd, signal, hist = _macd(long_prices)
    assert isinstance(macd, pd.Series)
    assert isinstance(signal, pd.Series)
    assert isinstance(hist, pd.Series)


def test_macd_hist_is_macd_minus_signal():
    long_prices = pd.Series([float(i) for i in range(1, 51)])
    macd, signal, hist = _macd(long_prices)
    pd.testing.assert_series_equal(hist, macd - signal)


def test_macd_ticker_enrichment_and_indicators_agree():
    # both modules must produce identical results — regression guard
    long_prices = pd.Series([float(i) + (i % 3) * 0.1 for i in range(1, 51)])
    macd1, sig1, hist1 = _macd(long_prices)
    # re-compute inline to be independent
    ema_fast = _ema(long_prices, 12)
    ema_slow = _ema(long_prices, 26)
    macd2 = ema_fast - ema_slow
    sig2 = _ema(macd2, 9)
    hist2 = macd2 - sig2
    pd.testing.assert_series_equal(macd1, macd2)
    pd.testing.assert_series_equal(hist1, hist2)


# ─── _safe ────────────────────────────────────────────────────────

def test_safe_none_returns_none():
    assert _safe(None) is None


def test_safe_nan_returns_none():
    assert _safe(float("nan")) is None


def test_safe_inf_returns_none():
    assert _safe(float("inf")) is None
    assert _safe(float("-inf")) is None


def test_safe_normal_float():
    assert _safe(3.14159, 2) == 3.14


def test_safe_integer():
    assert _safe(42) == 42.0


def test_safe_string_number():
    assert _safe("12.345", 1) == 12.3


def test_safe_invalid_string():
    assert _safe("not-a-number") is None


def test_safe_default_decimals():
    assert _safe(1.23456) == 1.23


# ─── Cross-module consistency ─────────────────────────────────────

def test_indicators_imported_by_ticker_enrichment():
    pytest.importorskip("feedparser")
    from dossier.data_sources import ticker_enrichment
    assert ticker_enrichment._ema is _ema
    assert ticker_enrichment._sma is _sma
    assert ticker_enrichment._rsi is _rsi
    assert ticker_enrichment._macd is _macd
    assert ticker_enrichment._safe is _safe


def test_indicators_imported_by_technical_setups():
    pytest.importorskip("yfinance")
    from dossier.data_sources import technical_setups
    assert technical_setups._ema is _ema
    assert technical_setups._sma is _sma
    assert technical_setups._rsi is _rsi
    assert technical_setups._safe is _safe
