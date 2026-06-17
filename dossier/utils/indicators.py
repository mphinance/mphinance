"""Shared technical-indicator helpers used across dossier data-source modules."""

import numpy as np


def _ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def _sma(series, window):
    return series.rolling(window=window).mean()


def _rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _macd(series, fast=12, slow=26, signal=9):
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd = ema_fast - ema_slow
    signal_line = _ema(macd, signal)
    hist = macd - signal_line
    return macd, signal_line, hist


def _safe(val, decimals=2):
    if val is None:
        return None
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return None
        return round(f, decimals)
    except (ValueError, TypeError):
        return None
