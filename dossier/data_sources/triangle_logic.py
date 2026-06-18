from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import numpy as np
import pandas as pd


BREAKOUT_COMPUTE_DEBUG = True


def _profile_add(profile: dict[str, float] | None, key: str, delta: float) -> None:
    if profile is None:
        return
    profile[key] = profile.get(key, 0.0) + float(delta)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def zero_if_nan(value: float | int | None) -> float:
    if value is None:
        return 0.0
    try:
        if pd.isna(value):
            return 0.0
    except TypeError:
        pass
    return float(value)


@dataclass(frozen=True)
class BreakoutConfig:
    min_avg_dollar_vol: float = 5_000_000.0
    dollar_vol_len: int = 20
    fast_ema_len: int = 10
    slow_ema_len: int = 20
    ema_slope_len: int = 5
    rel_vol_len: int = 20
    short_vol_len: int = 5
    long_vol_len: int = 20
    atr_short_len: int = 5
    atr_long_len: int = 20
    min_qualified_price: float = 2.0
    min_avg_share_vol_qualified: int = 300_000
    avg_share_vol_len_qualified: int = 20
    required_history_bars_qualified: int = 100
    use_atr_pct_ceiling_qualified: bool = False
    max_atr_pct_qualified: float = 12.0
    damage_lookback_bars: int = 10
    max_recent_drawdown_pct: float = 25.0
    smooth_lookback_bars: int = 5
    min_smoothness: float = 0.2
    min_consecutive_up_bars: int = 2
    td_triangle_lookback_bars: int = 60
    td_triangle_recent_bars: int = 5
    td_support_flat_max_pct: float = 12.5
    td_min_support_touches: int = 2
    td_max_support_touch_cluster_bars: int = 4
    td_support_break_invalidation_pct: float = 3.0
    td_support_pivot_left_bars: int = 2
    td_support_pivot_right_bars: int = 2
    td_min_support_touch_separation_bars: int = 5
    td_min_support_rebound_pct: float = 2.0
    td_min_support_touch_span_bars: int = 8
    td_max_support_touch_age_bars: int = 20
    td_support_max_positive_slope_pct: float = 0.35
    td_support_max_negative_slope_pct: float = 0.12
    td_support_right_touch_max_age_bars: int = 20
    td_support_right_touch_min_significance: float = 25.0
    td_descending_min_drop_pct: float = 2.5
    td_descending_min_height_abs: float = 3.0
    td_compression_max_ratio: float = 0.80
    td_max_vertex_gap_pct: float = 30.0
    td_max_bars_to_vertex: int = 15
    td_resolved_min_triangle_progress_pct: float = 50.0
    td_breakout_buffer_pct: float = 1.0
    td_breakout_recent_bars: int = 8
    td_structure_recent_bars: int = 8
    td_forming_invalidation_lookback_bars: int = 15
    td_max_triangle_age_bars: int = 10
    td_anchor_recent_bars: int = 8
    td_projected_anchor_max_bars_ahead: int = 12
    td_projected_anchor_max_height_pct: float = 12.5
    td_pivot_left_bars: int = 2
    td_pivot_right_bars: int = 2
    td_use_pivot_upper_line: bool = True
    td_max_pivot_separation_bars: int = 25
    td_pivot_min_relative_height_pct: float = 25.0
    td_min_pivot_separation_bars: int = 10
    td_min_bars_from_breakout_for_upper_pivot: int = 2
    td_pivot_min_prominence_pct: float = 1.0
    td_pivot_min_rebound_pct: float = 1.0
    td_pivot_significance_min_score: float = 25.0
    td_pivot_bulk_lookback_bars: int = 6
    td_left_high_min_price_advantage_pct: float = 0.5
    td_left_high_max_candidates: int = 6
    td_right_high_max_candidates: int = 8
    td_upper_line_overshoot_tolerance_pct: float = 1.0
    td_upper_line_significant_overshoot_penalty: float = 2.5
    td_upper_anchor_recency_bars: int = 15
    td_upper_anchor_late_window_bars: int = 9
    td_upper_anchor_max_bars_before_breakout: int = 14
    td_upper_anchor_ma_proximity_pct: float = 2.5
    td_upper_anchor_ma_context_weight: float = 0.45
    td_support_launch_gain_weight: float = 0.24
    td_support_body_alignment_weight: float = 0.12
    td_min_structure_range_ratio: float = 0.34
    td_min_triangle_start_height_pct: float = 5.0
    td_weak_shallow_max_height_abs: float = 10.0
    td_enable_shape_prescreen: bool = True
    td_prescreen_trend_bypass: bool = True
    td_prescreen_max_left_candidates: int = 8
    td_prescreen_recent_support_band_pct: float = 9.0
    td_prescreen_min_compression_ratio: float = 1.03
    td_prescreen_min_support_cluster_count: int = 1
    td_prescreen_accept_score: float = 30.0
    min_trend_score_stage_1: float = 35.0
    min_trend_score_stage_2: float = 60.0
    min_trend_score_stage_3: float = 70.0
    min_trend_score_stage_4: float = 85.0
    sustained_high_price_threshold: float = 600.0
    sustained_high_price_min_avg_dollar_vol: float = 100_000_000.0
    trend_outlier_return_window: int = 20
    trend_outlier_correlation_window: int = 60
    trend_outlier_min_stock_return_1d_pct: float = 1.5
    trend_outlier_max_benchmark_return_1d_pct: float = -0.5
    trend_outlier_min_relative_return_1d_pct: float = 2.5
    trend_outlier_min_stock_return_5d_pct: float = 4.0
    trend_outlier_max_benchmark_return_5d_pct: float = -0.1
    trend_outlier_min_relative_return_5d_pct: float = 5.0
    trend_outlier_min_stock_return_pct: float = 5.0
    trend_outlier_max_benchmark_return_pct: float = -2.0
    trend_outlier_min_relative_return_pct: float = 8.0
    trend_outlier_min_correlation: float = 0.20


EARLY = {
    "lookback_bars": 8,
    "min_gain_pct": 6.0,
    "min_up_bar_pct": 55.0,
    "near_high_pct": 8.0,
    "min_rel_vol": 1.15,
    "min_vol_trend_pct": 2.0,
    "min_accel_spread": 1.0,
    "min_roc_short": 2.0,
}

RUNAWAY = {
    "lookback_bars": 12,
    "min_gain_pct": 15.0,
    "min_up_bar_pct": 70.0,
    "near_high_pct": 4.0,
    "min_rel_vol": 1.30,
    "min_vol_trend_pct": 10.0,
    "min_accel_spread": 3.0,
    "min_roc_short": 5.0,
    "min_atr_expansion": 1.20,
}

CLIMAX = {
    "lookback_bars": 12,
    "min_gain_pct": 20.0,
    "min_up_bar_pct": 75.0,
    "near_high_pct": 2.5,
    "min_rel_vol": 1.75,
    "min_vol_trend_pct": 15.0,
    "min_accel_spread": 5.0,
    "min_roc_short": 7.0,
    "min_atr_expansion": 1.35,
    "stretch_pct": 20.0,
}

SUSTAINED = {
    "lookback_bars": 63,
    "min_gain_pct": 25.0,
    "min_up_bar_pct": 56.0,
    "near_high_pct": 14.0,
    "min_smoothness": 0.28,
    "long_min_smoothness": 0.24,
    "max_drawdown_pct": 32.0,
}

SUSTAINED_LONG_WINDOWS = [126, 189, 252]


def _empty_trend_outlier_metrics() -> dict[str, Any]:
    return {
        "Trend Outlier": 0,
        "Trend Outlier Score": 0.0,
        "Trend Outlier Benchmark": "",
        "Trend Outlier Window": "",
        "Trend Outlier Stock Return 1D": np.nan,
        "Trend Outlier Benchmark Return 1D": np.nan,
        "Trend Outlier Relative Return 1D": np.nan,
        "Trend Outlier Stock Return 5D": np.nan,
        "Trend Outlier Benchmark Return 5D": np.nan,
        "Trend Outlier Relative Return 5D": np.nan,
        "Trend Outlier Stock Return 20D": np.nan,
        "Trend Outlier Benchmark Return 20D": np.nan,
        "Trend Outlier Relative Return 20D": np.nan,
        "Trend Outlier Correlation 60D": np.nan,
    }


def compute_trend_outlier_metrics(
    history_df: pd.DataFrame,
    benchmark_histories: dict[str, pd.DataFrame] | None,
    cfg: BreakoutConfig,
) -> dict[str, Any]:
    if not benchmark_histories:
        return _empty_trend_outlier_metrics()
    if history_df.empty or "date" not in history_df.columns or "close" not in history_df.columns:
        return _empty_trend_outlier_metrics()

    stock_work = history_df[["date", "close"]].copy()
    stock_work["date"] = pd.to_datetime(stock_work["date"], errors="coerce").dt.normalize()
    stock_work["stock_close"] = pd.to_numeric(stock_work["close"], errors="coerce")
    stock_work = stock_work.dropna(subset=["date", "stock_close"]).sort_values("date")
    if len(stock_work) <= 1:
        return _empty_trend_outlier_metrics()

    return_window = max(int(cfg.trend_outlier_return_window), 1)
    outlier_windows = {
        1: (
            float(cfg.trend_outlier_min_stock_return_1d_pct),
            float(cfg.trend_outlier_max_benchmark_return_1d_pct),
            float(cfg.trend_outlier_min_relative_return_1d_pct),
        ),
        5: (
            float(cfg.trend_outlier_min_stock_return_5d_pct),
            float(cfg.trend_outlier_max_benchmark_return_5d_pct),
            float(cfg.trend_outlier_min_relative_return_5d_pct),
        ),
        return_window: (
            float(cfg.trend_outlier_min_stock_return_pct),
            float(cfg.trend_outlier_max_benchmark_return_pct),
            float(cfg.trend_outlier_min_relative_return_pct),
        ),
    }
    corr_window = max(int(cfg.trend_outlier_correlation_window), max(outlier_windows) + 1)
    benchmark_candidates: list[dict[str, Any]] = []
    for benchmark_symbol, benchmark_df in benchmark_histories.items():
        if benchmark_df is None or benchmark_df.empty or "date" not in benchmark_df.columns or "close" not in benchmark_df.columns:
            continue
        benchmark_work = benchmark_df[["date", "close"]].copy()
        benchmark_work["date"] = pd.to_datetime(benchmark_work["date"], errors="coerce").dt.normalize()
        benchmark_work["benchmark_close"] = pd.to_numeric(benchmark_work["close"], errors="coerce")
        benchmark_work = benchmark_work.dropna(subset=["date", "benchmark_close"]).sort_values("date")
        aligned = stock_work.merge(benchmark_work, on="date", how="inner").tail(max(corr_window + 1, return_window + 1))
        if len(aligned) <= 1:
            continue
        window_returns: dict[int, tuple[float, float, float]] = {}
        for window in outlier_windows:
            if len(aligned) <= window:
                continue
            stock_start = float(aligned["stock_close"].iloc[-window - 1])
            stock_end = float(aligned["stock_close"].iloc[-1])
            benchmark_start = float(aligned["benchmark_close"].iloc[-window - 1])
            benchmark_end = float(aligned["benchmark_close"].iloc[-1])
            if stock_start <= 0 or benchmark_start <= 0:
                continue
            stock_return_pct = ((stock_end / stock_start) - 1.0) * 100.0
            benchmark_return_pct = ((benchmark_end / benchmark_start) - 1.0) * 100.0
            relative_return_pct = stock_return_pct - benchmark_return_pct
            window_returns[window] = (stock_return_pct, benchmark_return_pct, relative_return_pct)
        if not window_returns:
            continue
        corr_aligned = aligned.tail(corr_window + 1)
        correlation = np.nan
        if len(corr_aligned) >= min(corr_window, 20):
            corr_frame = pd.DataFrame(
                {
                    "stock_return": corr_aligned["stock_close"].pct_change(),
                    "benchmark_return": corr_aligned["benchmark_close"].pct_change(),
                }
            ).dropna()
            if len(corr_frame) >= 10:
                correlation = corr_frame["stock_return"].corr(corr_frame["benchmark_return"])
        benchmark_candidates.append(
            {
                "benchmark": str(benchmark_symbol).strip().upper(),
                "window_returns": window_returns,
                "correlation": correlation,
            }
        )

    if not benchmark_candidates:
        return _empty_trend_outlier_metrics()

    qualified_by_corr = [
        item
        for item in benchmark_candidates
        if pd.notna(item["correlation"]) and float(item["correlation"]) >= float(cfg.trend_outlier_min_correlation)
    ]
    if qualified_by_corr:
        selected = max(qualified_by_corr, key=lambda item: float(item["correlation"]))
    else:
        selected = next((item for item in benchmark_candidates if item["benchmark"] == "SPY"), benchmark_candidates[0])

    selected_window_returns = selected["window_returns"]
    correlation = selected["correlation"]
    qualified_windows: list[tuple[float, int, float, float, float]] = []
    for window, (stock_return_pct, benchmark_return_pct, relative_return_pct) in selected_window_returns.items():
        if window != 1:
            continue
        min_stock_return, max_benchmark_return, min_relative_return = outlier_windows[window]
        if (
            stock_return_pct >= min_stock_return
            and benchmark_return_pct <= max_benchmark_return
            and relative_return_pct >= min_relative_return
        ):
            window_weight = 1.25 if window == 1 else 1.10 if window == 5 else 1.0
            window_score = (
                min(max(stock_return_pct, 0.0), 35.0) * 0.9
                + min(max(abs(benchmark_return_pct), 0.0), 18.0) * 1.2
                + min(max(relative_return_pct, 0.0), 45.0) * 1.5
            ) * window_weight
            qualified_windows.append((window_score, window, stock_return_pct, benchmark_return_pct, relative_return_pct))
    qualified_windows.sort(key=lambda item: item[0], reverse=True)
    is_outlier = bool(qualified_windows)
    score, selected_window, stock_return_pct, benchmark_return_pct, relative_return_pct = (
        qualified_windows[0] if qualified_windows else (0.0, return_window, np.nan, np.nan, np.nan)
    )
    if is_outlier:
        if pd.notna(correlation):
            score += max(float(correlation), 0.0) * 12.0
    return_1d = selected_window_returns.get(1, (np.nan, np.nan, np.nan))
    return_5d = selected_window_returns.get(5, (np.nan, np.nan, np.nan))
    return_20d = selected_window_returns.get(return_window, (np.nan, np.nan, np.nan))
    return {
        "Trend Outlier": int(is_outlier),
        "Trend Outlier Score": round(float(score), 2),
        "Trend Outlier Benchmark": selected["benchmark"],
        "Trend Outlier Window": f"{selected_window}D" if is_outlier else "",
        "Trend Outlier Stock Return 1D": round(float(return_1d[0]), 4) if pd.notna(return_1d[0]) else np.nan,
        "Trend Outlier Benchmark Return 1D": round(float(return_1d[1]), 4) if pd.notna(return_1d[1]) else np.nan,
        "Trend Outlier Relative Return 1D": round(float(return_1d[2]), 4) if pd.notna(return_1d[2]) else np.nan,
        "Trend Outlier Stock Return 5D": round(float(return_5d[0]), 4) if pd.notna(return_5d[0]) else np.nan,
        "Trend Outlier Benchmark Return 5D": round(float(return_5d[1]), 4) if pd.notna(return_5d[1]) else np.nan,
        "Trend Outlier Relative Return 5D": round(float(return_5d[2]), 4) if pd.notna(return_5d[2]) else np.nan,
        "Trend Outlier Stock Return 20D": round(float(return_20d[0]), 4) if pd.notna(return_20d[0]) else np.nan,
        "Trend Outlier Benchmark Return 20D": round(float(return_20d[1]), 4) if pd.notna(return_20d[1]) else np.nan,
        "Trend Outlier Relative Return 20D": round(float(return_20d[2]), 4) if pd.notna(return_20d[2]) else np.nan,
        "Trend Outlier Correlation 60D": round(float(correlation), 4) if pd.notna(correlation) else np.nan,
    }


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def roc(series: pd.Series, length: int) -> pd.Series:
    return (series / series.shift(length) - 1.0) * 100.0


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    return pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def atr(df: pd.DataFrame, length: int) -> pd.Series:
    return true_range(df).rolling(length).mean()


def pivot_low(series: pd.Series, left: int, right: int) -> pd.Series:
    values = series.to_numpy(dtype=float)
    out = np.full(len(values), np.nan)
    for idx in range(left, len(values) - right):
        window = values[idx - left : idx + right + 1]
        if np.isnan(window).any():
            continue
        if values[idx] == np.min(window) and np.sum(window == values[idx]) == 1:
            out[idx] = values[idx]
    return pd.Series(out, index=series.index)


def pivot_high(series: pd.Series, left: int, right: int) -> pd.Series:
    values = series.to_numpy(dtype=float)
    out = np.full(len(values), np.nan)
    for idx in range(left, len(values) - right):
        window = values[idx - left : idx + right + 1]
        if np.isnan(window).any():
            continue
        if values[idx] == np.max(window) and np.sum(window == values[idx]) == 1:
            out[idx] = values[idx]
    return pd.Series(out, index=series.index)


def barssince(condition: pd.Series) -> pd.Series:
    result: list[float] = []
    bars_since: int | None = None
    for value in condition.fillna(False).astype(bool):
        if value:
            bars_since = 0
        elif bars_since is not None:
            bars_since += 1
        result.append(float(bars_since) if bars_since is not None else np.nan)
    return pd.Series(result, index=condition.index)


def _coerce_pivot_dates(dates: pd.Series | None, length: int) -> pd.Series:
    if dates is None:
        return pd.Series([pd.NaT] * length)
    return pd.to_datetime(dates, errors="coerce")


def _pivot_date_str(dates: pd.Series, idx: int) -> str | None:
    if idx < 0 or idx >= len(dates):
        return None
    value = dates.iloc[idx]
    if pd.isna(value):
        return None
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def _safe_pct_distance(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    result = np.full_like(denominator, np.nan, dtype=float)
    valid_mask = denominator > 0
    result[valid_mask] = (numerator[valid_mask] / denominator[valid_mask]) * 100.0
    return result


def _score_low_pivot(
    lows: pd.Series,
    highs: pd.Series,
    idx: int,
    pivot_indices: list[int],
    dates: pd.Series,
    cfg: BreakoutConfig,
) -> dict[str, Any]:
    price = float(lows.iloc[idx])
    prev_idx = pivot_indices[pivot_indices.index(idx) - 1] if pivot_indices.index(idx) > 0 else None
    separation_bars = int(idx - prev_idx) if prev_idx is not None else len(lows)

    left_slice = highs.iloc[max(0, idx - cfg.td_support_pivot_left_bars) : idx]
    right_slice = highs.iloc[idx + 1 : min(len(highs), idx + 1 + cfg.td_support_pivot_right_bars + cfg.td_support_pivot_left_bars)]
    left_high = float(left_slice.max()) if not left_slice.empty else np.nan
    right_high = float(right_slice.max()) if not right_slice.empty else np.nan
    prominence_ref_candidates = [value for value in [left_high, right_high] if pd.notna(value)]
    prominence_ref = min(prominence_ref_candidates) if prominence_ref_candidates else np.nan
    prominence_pct = ((prominence_ref / price) - 1.0) * 100.0 if pd.notna(prominence_ref) and price > 0 else 0.0
    rebound_or_rejection_pct = ((right_high / price) - 1.0) * 100.0 if pd.notna(right_high) and price > 0 else 0.0

    range_low = float(lows.min())
    range_high = float(highs.max())
    range_size = range_high - range_low
    relative_height_score = 100.0 * clamp01((range_high - price) / range_size) if range_size > 0 else 0.0
    recency_score = 100.0 * clamp01(1.0 - ((len(lows) - 1 - idx) / max(len(lows) - 1, 1)))
    separation_score = 100.0 * clamp01(separation_bars / max(cfg.td_triangle_lookback_bars, 1))
    significance_score = (
        min(max(prominence_pct, 0.0) * 10.0, 100.0) * 0.35
        + min(max(rebound_or_rejection_pct, 0.0) * 10.0, 100.0) * 0.30
        + relative_height_score * 0.20
        + recency_score * 0.10
        + separation_score * 0.05
    )

    return {
        "idx": int(idx),
        "date": _pivot_date_str(dates, idx),
        "price": price,
        "kind": "low",
        "prominence_pct": round(float(prominence_pct), 4),
        "rebound_or_rejection_pct": round(float(rebound_or_rejection_pct), 4),
        "separation_bars": int(separation_bars),
        "relative_height_score": round(float(relative_height_score), 4),
        "recency_score": round(float(recency_score), 4),
        "significance_score": round(float(significance_score), 4),
    }


def _score_high_pivot(
    highs: pd.Series,
    lows: pd.Series,
    idx: int,
    pivot_indices: list[int],
    dates: pd.Series,
    cfg: BreakoutConfig,
) -> dict[str, Any]:
    price = float(highs.iloc[idx])
    prev_idx = pivot_indices[pivot_indices.index(idx) - 1] if pivot_indices.index(idx) > 0 else None
    separation_bars = int(idx - prev_idx) if prev_idx is not None else len(highs)
    bulk_lookback = max(int(cfg.td_pivot_bulk_lookback_bars), 2)

    left_slice = lows.iloc[max(0, idx - cfg.td_pivot_left_bars) : idx]
    right_slice = lows.iloc[idx + 1 : min(len(lows), idx + 1 + cfg.td_pivot_right_bars + cfg.td_pivot_left_bars)]
    left_low = float(left_slice.min()) if not left_slice.empty else np.nan
    right_low = float(right_slice.min()) if not right_slice.empty else np.nan
    prominence_ref_candidates = [value for value in [left_low, right_low] if pd.notna(value)]
    prominence_ref = max(prominence_ref_candidates) if prominence_ref_candidates else np.nan
    prominence_pct = ((price / prominence_ref) - 1.0) * 100.0 if pd.notna(prominence_ref) and prominence_ref > 0 else 0.0
    rebound_or_rejection_pct = ((price / right_low) - 1.0) * 100.0 if pd.notna(right_low) and right_low > 0 else 0.0

    range_low = float(lows.min())
    range_high = float(highs.max())
    range_size = range_high - range_low
    relative_height_score = 100.0 * clamp01((price - range_low) / range_size) if range_size > 0 else 0.0
    recency_score = 100.0 * clamp01(1.0 - ((len(highs) - 1 - idx) / max(len(highs) - 1, 1)))
    separation_score = 100.0 * clamp01(separation_bars / max(cfg.td_triangle_lookback_bars, 1))

    pre_start = max(0, idx - bulk_lookback)
    post_end = min(len(highs), idx + 1 + bulk_lookback)
    pre_highs = highs.iloc[pre_start : idx + 1].reset_index(drop=True)
    post_highs = highs.iloc[idx:post_end].reset_index(drop=True)
    pre_lows = lows.iloc[pre_start : idx + 1]
    post_lows = lows.iloc[idx:post_end]

    up_bar_ratio = 0.0
    if len(pre_highs) >= 2:
        up_bar_ratio = float((pre_highs.diff().iloc[1:] > 0).sum()) / max(len(pre_highs) - 1, 1)
    down_bar_ratio = 0.0
    if len(post_highs) >= 2:
        down_bar_ratio = float((post_highs.diff().iloc[1:] < 0).sum()) / max(len(post_highs) - 1, 1)

    advance_ref = float(pre_lows.min()) if not pre_lows.empty else np.nan
    reversal_ref = float(post_lows.min()) if not post_lows.empty else np.nan
    advance_pct = ((price / advance_ref) - 1.0) * 100.0 if pd.notna(advance_ref) and advance_ref > 0 else 0.0
    reversal_pct = ((price / reversal_ref) - 1.0) * 100.0 if pd.notna(reversal_ref) and reversal_ref > 0 else 0.0
    nearby_highs = highs.iloc[pre_start:post_end]
    near_peak_threshold = price * 0.985
    peak_width_bars = int((nearby_highs >= near_peak_threshold).sum()) if not nearby_highs.empty else 1

    run_shape_score = (
        100.0 * clamp01(up_bar_ratio) * 0.30
        + min(max(advance_pct, 0.0) * 8.0, 100.0) * 0.35
        + 100.0 * clamp01(down_bar_ratio) * 0.20
        + min(max(reversal_pct, 0.0) * 8.0, 100.0) * 0.15
    )
    peak_bulk_score = min(max((peak_width_bars - 1) / max(bulk_lookback - 1, 1), 0.0), 1.0) * 100.0
    significance_score = (
        min(max(prominence_pct, 0.0) * 10.0, 100.0) * 0.20
        + min(max(rebound_or_rejection_pct, 0.0) * 10.0, 100.0) * 0.15
        + relative_height_score * 0.25
        + run_shape_score * 0.30
        + peak_bulk_score * 0.05
        + recency_score * 0.10
        + separation_score * 0.05
    )

    return {
        "idx": int(idx),
        "date": _pivot_date_str(dates, idx),
        "price": price,
        "kind": "high",
        "prominence_pct": round(float(prominence_pct), 4),
        "rebound_or_rejection_pct": round(float(rebound_or_rejection_pct), 4),
        "separation_bars": int(separation_bars),
        "relative_height_score": round(float(relative_height_score), 4),
        "run_shape_score": round(float(run_shape_score), 4),
        "peak_bulk_score": round(float(peak_bulk_score), 4),
        "recency_score": round(float(recency_score), 4),
        "significance_score": round(float(significance_score), 4),
    }


def find_significant_pivot_lows(
    lows: pd.Series,
    highs: pd.Series,
    cfg: BreakoutConfig,
    dates: pd.Series | None = None,
) -> dict[str, Any]:
    pivot_series = pivot_low(lows, cfg.td_support_pivot_left_bars, cfg.td_support_pivot_right_bars)
    pivot_indices = [int(idx) for idx in np.flatnonzero(pivot_series.notna().to_numpy())]
    pivot_dates = _coerce_pivot_dates(dates, len(lows))
    records = [
        _score_low_pivot(lows, highs, idx, pivot_indices, pivot_dates, cfg)
        for idx in pivot_indices
    ]
    significant_records = [
        record
        for record in records
        if record["prominence_pct"] >= cfg.td_pivot_min_prominence_pct
        and record["rebound_or_rejection_pct"] >= cfg.td_pivot_min_rebound_pct
        and record["significance_score"] >= cfg.td_pivot_significance_min_score
    ]
    return {
        "pivot_series": pivot_series,
        "records": records,
        "significant_records": significant_records,
    }


def find_significant_pivot_highs(
    highs: pd.Series,
    lows: pd.Series,
    cfg: BreakoutConfig,
    dates: pd.Series | None = None,
) -> dict[str, Any]:
    pivot_series = pivot_high(highs, cfg.td_pivot_left_bars, cfg.td_pivot_right_bars)
    pivot_indices = [int(idx) for idx in np.flatnonzero(pivot_series.notna().to_numpy())]
    pivot_dates = _coerce_pivot_dates(dates, len(highs))
    records = [
        _score_high_pivot(highs, lows, idx, pivot_indices, pivot_dates, cfg)
        for idx in pivot_indices
    ]
    significant_records = [
        record
        for record in records
        if record["prominence_pct"] >= cfg.td_pivot_min_prominence_pct
        and record["rebound_or_rejection_pct"] >= cfg.td_pivot_min_rebound_pct
        and record["significance_score"] >= cfg.td_pivot_significance_min_score
    ]
    return {
        "pivot_series": pivot_series,
        "records": records,
        "significant_records": significant_records,
    }


def build_left_high_candidates(
    pivot_records: list[dict[str, Any]],
    cfg: BreakoutConfig,
) -> list[dict[str, Any]]:
    if not pivot_records:
        return []

    scored_records: list[dict[str, Any]] = []
    for record in pivot_records:
        prominence_score = min(max(float(record.get("prominence_pct", 0.0)), 0.0) * 10.0, 100.0)
        left_anchor_score = (
            float(record.get("relative_height_score", 0.0)) * 0.40
            + float(record.get("significance_score", 0.0)) * 0.25
            + float(record.get("run_shape_score", 0.0)) * 0.20
            + float(record.get("peak_bulk_score", 0.0)) * 0.10
            + prominence_score * 0.05
        )
        enriched = dict(record)
        enriched["left_anchor_score"] = round(float(left_anchor_score), 4)
        scored_records.append(enriched)

    dominance_filtered: list[dict[str, Any]] = []
    for record in scored_records:
        price = float(record["price"])
        idx = int(record["idx"])
        dominated = False
        for other in scored_records:
            if int(other["idx"]) <= idx:
                continue
            other_price = float(other["price"])
            if price <= 0:
                continue
            price_advantage_pct = ((other_price / price) - 1.0) * 100.0
            if price_advantage_pct < cfg.td_left_high_min_price_advantage_pct:
                continue
            if float(other["left_anchor_score"]) >= float(record["left_anchor_score"]) * 0.90:
                dominated = True
                break
        if not dominated:
            dominance_filtered.append(record)

    dominance_filtered.sort(
        key=lambda record: (
            float(record["left_anchor_score"]),
            float(record.get("relative_height_score", 0.0)),
            float(record["price"]),
        ),
        reverse=True,
    )
    return dominance_filtered[: cfg.td_left_high_max_candidates]


def build_right_high_candidates(
    pivot_records: list[dict[str, Any]],
    breakout_reference_idx: int,
    closes: pd.Series,
    cfg: BreakoutConfig,
) -> list[dict[str, Any]]:
    if not pivot_records:
        return []

    sma20 = closes.rolling(20, min_periods=5).mean()
    sma50 = closes.rolling(50, min_periods=10).mean()
    candidates: list[dict[str, Any]] = []
    for record in pivot_records:
        idx = int(record["idx"])
        bars_before_breakout = breakout_reference_idx - idx
        if bars_before_breakout < cfg.td_min_bars_from_breakout_for_upper_pivot:
            continue
        if bars_before_breakout > cfg.td_upper_anchor_max_bars_before_breakout:
            continue
        close_price = float(closes.iloc[idx]) if idx < len(closes) else np.nan
        prev_close = float(closes.iloc[idx - 1]) if idx > 0 else close_price
        ma_values = [
            float(value)
            for value in [sma20.iloc[idx] if idx < len(sma20) else np.nan, sma50.iloc[idx] if idx < len(sma50) else np.nan]
            if pd.notna(value) and float(value) > 0
        ]
        ma_proximity_score = 0.0
        ma_context_score = 0.0
        if ma_values and pd.notna(close_price) and close_price > 0:
            min_ma_distance_pct = min(abs((close_price / ma_value) - 1.0) * 100.0 for ma_value in ma_values)
            ma_proximity_score = 100.0 * clamp01(
                1.0 - (min_ma_distance_pct / max(cfg.td_upper_anchor_ma_proximity_pct, 0.01))
            )
            reclaim_components = 0.0
            near_ma_count = 0
            for ma_value in ma_values:
                if abs((close_price / ma_value) - 1.0) * 100.0 <= cfg.td_upper_anchor_ma_proximity_pct:
                    near_ma_count += 1
                if prev_close < ma_value <= close_price:
                    reclaim_components += 45.0
                elif close_price >= ma_value:
                    reclaim_components += 20.0
                elif abs((close_price / ma_value) - 1.0) * 100.0 <= cfg.td_upper_anchor_ma_proximity_pct:
                    reclaim_components += 12.5
            if near_ma_count >= 2:
                reclaim_components += 20.0
            ma_context_score = min(reclaim_components, 100.0)
        right_anchor_recency_score = 100.0 * clamp01(
            1.0 - (bars_before_breakout / max(cfg.td_upper_anchor_recency_bars, 1))
        )
        late_window_score = 100.0 * clamp01(
            1.0
            - (
                max(
                    bars_before_breakout - cfg.td_min_bars_from_breakout_for_upper_pivot,
                    0,
                )
                / max(
                    cfg.td_upper_anchor_late_window_bars - cfg.td_min_bars_from_breakout_for_upper_pivot,
                    1,
                )
            )
        )
        prominence_score = min(max(float(record.get("prominence_pct", 0.0)), 0.0) * 10.0, 100.0)
        right_anchor_score = (
            right_anchor_recency_score * 0.26
            + late_window_score * 0.24
            + float(record.get("significance_score", 0.0)) * 0.12
            + float(record.get("run_shape_score", 0.0)) * 0.08
            + float(record.get("peak_bulk_score", 0.0)) * 0.05
            + float(record.get("relative_height_score", 0.0)) * 0.05
            + prominence_score * 0.03
            + ma_proximity_score * (cfg.td_upper_anchor_ma_context_weight * 0.50)
            + ma_context_score * (cfg.td_upper_anchor_ma_context_weight * 0.50)
        )
        enriched = dict(record)
        enriched["bars_before_breakout"] = int(bars_before_breakout)
        enriched["right_anchor_recency_score"] = round(float(right_anchor_recency_score), 4)
        enriched["late_window_score"] = round(float(late_window_score), 4)
        enriched["ma_proximity_score"] = round(float(ma_proximity_score), 4)
        enriched["ma_context_score"] = round(float(ma_context_score), 4)
        enriched["right_anchor_score"] = round(float(right_anchor_score), 4)
        candidates.append(enriched)

    candidates.sort(
        key=lambda record: (
            float(record["right_anchor_score"]),
            -int(record["bars_before_breakout"]),
            float(record["price"]),
        ),
        reverse=True,
    )
    return candidates[: cfg.td_right_high_max_candidates]


def build_support_line_candidates(
    pivot_records: list[dict[str, Any]],
    lows: pd.Series,
    highs: pd.Series,
    closes: pd.Series,
    cfg: BreakoutConfig,
    reference_high_idx: int | None = None,
) -> list[dict[str, Any]]:
    if not pivot_records:
        return []

    x = np.arange(len(lows), dtype=float)
    candidate_records = pivot_records
    valid_candidates: list[dict[str, Any]] = []
    touch_tolerance_pct = max(cfg.td_support_flat_max_pct * 0.20, 0.75)
    wick_break_tolerance_pct = max(cfg.td_support_flat_max_pct * 0.10, 0.30)

    for newer_record in candidate_records:
        newer_idx = int(newer_record["idx"])
        newer_price = float(newer_record["price"])
        newer_significance = float(newer_record.get("significance_score", 0.0))
        support_touch_age_bars = int((len(lows) - 1) - newer_idx)
        if support_touch_age_bars > cfg.td_support_right_touch_max_age_bars:
            continue
        if newer_significance < cfg.td_support_right_touch_min_significance:
            continue

        for older_record in candidate_records:
            older_idx = int(older_record["idx"])
            if older_idx >= newer_idx:
                continue
            separation = newer_idx - older_idx
            if separation < cfg.td_min_support_touch_separation_bars:
                continue

            older_price = float(older_record["price"])
            slope = (newer_price - older_price) / max(separation, 1)
            avg_price = (older_price + newer_price) / 2.0 if (older_price + newer_price) > 0 else np.nan
            slope_pct_per_bar = (slope / avg_price) * 100.0 if pd.notna(avg_price) and avg_price > 0 else np.nan
            if pd.isna(slope_pct_per_bar):
                continue
            if slope_pct_per_bar > cfg.td_support_max_positive_slope_pct:
                continue
            if slope_pct_per_bar < -cfg.td_support_max_negative_slope_pct:
                continue

            price_alignment_pct = abs((older_price / newer_price) - 1.0) * 100.0 if newer_price > 0 else np.nan
            if pd.isna(price_alignment_pct):
                continue
            price_alignment_score = 100.0 * clamp01(1.0 - (price_alignment_pct / max(cfg.td_support_flat_max_pct, 0.01)))
            launch_end_idx = (
                int(reference_high_idx)
                if reference_high_idx is not None and int(reference_high_idx) > older_idx
                else newer_idx
            )
            launch_high = float(highs.iloc[older_idx : launch_end_idx + 1].max()) if launch_end_idx >= older_idx else older_price
            launch_gain_pct = ((launch_high / older_price) - 1.0) * 100.0 if older_price > 0 else 0.0
            launch_gain_score = min(max(launch_gain_pct, 0.0) * 3.5, 100.0)
            span_score = 100.0 * clamp01(separation / max(len(lows) - 1, 1))

            line_values = older_price + slope * (x - older_idx)
            valid_slice = slice(older_idx, len(lows))
            eval_lows = lows.iloc[valid_slice].to_numpy(dtype=float)
            eval_closes = closes.iloc[valid_slice].to_numpy(dtype=float)
            eval_line = line_values[valid_slice]

            low_dev_pct = _safe_pct_distance(eval_lows - eval_line, eval_line)
            close_dev_pct = _safe_pct_distance(eval_closes - eval_line, eval_line)
            break_penalty = float(np.nansum(np.clip(-(low_dev_pct + wick_break_tolerance_pct), a_min=0.0, a_max=None)))
            close_break_penalty = float(np.nansum(np.clip(-(close_dev_pct + wick_break_tolerance_pct), a_min=0.0, a_max=None))) * 1.5

            touch_records = []
            touch_distances = []
            touch_body_gap_pct: list[float] = []
            for record in candidate_records:
                idx = int(record["idx"])
                if idx < older_idx or idx > len(lows) - 1:
                    continue
                line_price = float(older_price + slope * (idx - older_idx))
                if line_price <= 0:
                    continue
                pivot_price = float(record["price"])
                dist_pct = ((pivot_price - line_price) / line_price) * 100.0
                if dist_pct < -wick_break_tolerance_pct:
                    continue
                if abs(dist_pct) <= touch_tolerance_pct:
                    touch_records.append(record)
                    touch_distances.append(abs(dist_pct))
                    close_price = float(closes.iloc[idx]) if idx < len(closes) else np.nan
                    if pd.notna(close_price) and close_price > 0:
                        close_gap_pct = max(((close_price / line_price) - 1.0) * 100.0, 0.0)
                        touch_body_gap_pct.append(close_gap_pct)

            touch_count = len(touch_records)
            if touch_count < cfg.td_min_support_touches:
                continue
            touch_indices = [int(record["idx"]) for record in touch_records]
            support_touch_span_bars = int(max(touch_indices) - min(touch_indices)) if len(touch_indices) >= 2 else 0
            if support_touch_span_bars < cfg.td_min_support_touch_span_bars:
                continue
            clustered_too_tightly = (
                len(touch_indices) >= 2
                and int(max(touch_indices) - min(touch_indices)) <= cfg.td_max_support_touch_cluster_bars
            )
            if clustered_too_tightly:
                continue

            support_band_pct = max(touch_distances) if touch_distances else np.nan
            support_end_price = float(older_price + slope * ((len(lows) - 1) - older_idx))
            current_support_broken = float(closes.iloc[-1]) < support_end_price * (1.0 - cfg.td_support_break_invalidation_pct / 100.0)
            if current_support_broken:
                continue

            touch_significance = sum(float(record.get("significance_score", 0.0)) for record in touch_records)
            flatter_score = 100.0 * clamp01(1.0 - (abs(slope_pct_per_bar) / max(cfg.td_support_max_positive_slope_pct, cfg.td_support_max_negative_slope_pct, 0.01)))
            right_touch_recency_score = 100.0 * clamp01(1.0 - (support_touch_age_bars / max(cfg.td_support_right_touch_max_age_bars, 1)))
            right_touch_score = newer_significance * 0.60 + right_touch_recency_score * 0.40
            avg_touch_body_gap_pct = float(np.nanmean(touch_body_gap_pct)) if touch_body_gap_pct else np.nan
            body_alignment_score = (
                100.0 * clamp01(1.0 - (avg_touch_body_gap_pct / max(cfg.td_support_flat_max_pct, 0.01)))
                if pd.notna(avg_touch_body_gap_pct)
                else 50.0
            )
            left_alignment_score = (
                price_alignment_score * 0.34
                + float(older_record.get("significance_score", 0.0)) * 0.18
                + flatter_score * 0.10
                + launch_gain_score * cfg.td_support_launch_gain_weight
                + body_alignment_score * cfg.td_support_body_alignment_weight
                + span_score * 0.12
            )
            candidate_score = (
                right_touch_score * 0.30
                + left_alignment_score * 0.28
                + touch_significance * 0.20
                + min(touch_count, 4) * 5.0
                + flatter_score * 0.07
                - break_penalty * 1.0
                - close_break_penalty
            )

            valid_candidates.append(
                {
                    "older_idx": older_idx,
                    "newer_idx": newer_idx,
                    "older_price": older_price,
                    "newer_price": newer_price,
                    "slope": float(slope),
                    "slope_pct_per_bar": float(slope_pct_per_bar),
                    "support_end_price": support_end_price,
                    "touch_count": touch_count,
                    "touch_indices": touch_indices,
                    "support_touch_span_bars": support_touch_span_bars,
                    "support_touch_age_bars": support_touch_age_bars,
                    "support_band_pct": support_band_pct,
                    "clustered_too_tightly": clustered_too_tightly,
                    "price_alignment_pct": float(price_alignment_pct),
                    "price_alignment_score": float(price_alignment_score),
                    "launch_gain_pct": float(launch_gain_pct),
                    "launch_gain_score": float(launch_gain_score),
                    "avg_touch_body_gap_pct": float(avg_touch_body_gap_pct) if pd.notna(avg_touch_body_gap_pct) else np.nan,
                    "body_alignment_score": float(body_alignment_score),
                    "right_touch_score": float(right_touch_score),
                    "left_alignment_score": float(left_alignment_score),
                    "candidate_score": float(candidate_score),
                }
            )

    valid_candidates.sort(
        key=lambda candidate: (
            float(candidate["candidate_score"]),
            -abs(float(candidate["slope_pct_per_bar"])),
            float(candidate["support_end_price"]),
        ),
        reverse=True,
    )
    return valid_candidates


def up_bar_pct(close: pd.Series, lookback_bars: int) -> float:
    if len(close) < lookback_bars:
        return np.nan
    window = close.tail(lookback_bars).reset_index(drop=True)
    up_bars = float((window.diff().iloc[1:] > 0).sum())
    return (up_bars / max(lookback_bars - 1, 1)) * 100.0


def max_consecutive_up_bars(close: pd.Series, lookback_bars: int) -> int:
    if len(close) < lookback_bars:
        return 0
    window = close.tail(lookback_bars).reset_index(drop=True)
    consec = 0
    max_consec = 0
    for idx in range(1, len(window)):
        if window.iloc[idx] > window.iloc[idx - 1]:
            consec += 1
            max_consec = max(max_consec, consec)
        else:
            consec = 0
    return max_consec


def _triangle_date_lookup(recent: pd.DataFrame):
    dates = pd.to_datetime(recent["date"], errors="coerce") if "date" in recent.columns else pd.Series([pd.NaT] * len(recent))

    def _date_at(idx: int | None) -> str | None:
        if idx is None or idx < 0 or idx >= len(dates):
            return None
        value = dates.iloc[idx]
        if pd.isna(value):
            return None
        return pd.Timestamp(value).strftime("%Y-%m-%d")

    return dates, _date_at


def _format_date_value(value: Any) -> str | None:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return pd.Timestamp(parsed).strftime("%Y-%m-%d")


def _business_date_offset_from_last(df: pd.DataFrame, bars_offset: float | int | None) -> str | None:
    if bars_offset is None or pd.isna(bars_offset) or "date" not in df.columns or df.empty:
        return None
    last_date = pd.to_datetime(df["date"].iloc[-1], errors="coerce")
    if pd.isna(last_date):
        return None
    offset = int(round(float(bars_offset)))
    try:
        return pd.Timestamp(last_date + pd.tseries.offsets.BDay(offset)).strftime("%Y-%m-%d")
    except Exception:
        return None


def _date_from_bars_ago(df: pd.DataFrame, bars_ago: float | int | None) -> str | None:
    if bars_ago is None or pd.isna(bars_ago) or "date" not in df.columns or df.empty:
        return None
    idx = int(round((len(df) - 1) - float(bars_ago)))
    if idx < 0 or idx >= len(df):
        return _business_date_offset_from_last(df, -float(bars_ago))
    return _format_date_value(df["date"].iloc[idx])


def _compute_support_touch_metrics(
    recent: pd.DataFrame,
    lows: pd.Series,
    highs: pd.Series,
    closes: pd.Series,
    cfg: BreakoutConfig,
    reference_high_idx: int | None = None,
) -> dict[str, Any]:
    support_pivot_info = find_significant_pivot_lows(
        lows,
        highs,
        cfg,
        recent["date"] if "date" in recent.columns else None,
    )
    support_pivots = support_pivot_info["pivot_series"]
    all_support_records = support_pivot_info["records"]
    significant_support_records = support_pivot_info["significant_records"]
    candidate_support_records = significant_support_records if significant_support_records else all_support_records
    support_line_candidates = build_support_line_candidates(
        candidate_support_records,
        lows,
        highs,
        closes,
        cfg,
        reference_high_idx=reference_high_idx,
    )
    best_support_line = support_line_candidates[0] if support_line_candidates else None

    if best_support_line is not None:
        filtered_touch_indices = [int(idx) for idx in best_support_line["touch_indices"]]
        filtered_touch_prices = [float(lows.iloc[idx]) for idx in filtered_touch_indices]
        support_touch_count = int(best_support_line["touch_count"])
        support_touch_span_bars = int(best_support_line["support_touch_span_bars"])
        support_touch_age_bars = int(best_support_line["support_touch_age_bars"])
        support_band_pct = float(best_support_line["support_band_pct"]) if pd.notna(best_support_line["support_band_pct"]) else np.nan
        clustered_too_tightly = bool(best_support_line["clustered_too_tightly"])
        support_ref = float(best_support_line["support_end_price"])
        support_line_start_idx = int(best_support_line["older_idx"])
        support_line_end_idx = len(lows) - 1 if len(lows) > 0 else None
        support_line_start_price = float(best_support_line["older_price"])
        support_line_end_price = float(best_support_line["support_end_price"])
        support_line_slope = float(best_support_line["slope"])
    else:
        valid_support_pivots = support_pivots.dropna()
        support_ref = float(valid_support_pivots.min()) if not valid_support_pivots.empty else float(lows.min())
        filtered_touch_indices = []
        filtered_touch_prices = []
        support_touch_count = 0
        support_touch_span_bars = 0
        support_touch_age_bars = len(lows)
        support_band_pct = np.nan
        clustered_too_tightly = False
        support_line_start_idx = None
        support_line_end_idx = len(lows) - 1 if len(lows) > 0 else None
        support_line_start_price = support_ref
        support_line_end_price = support_ref
        support_line_slope = 0.0

    return {
        "support_pivots": support_pivots,
        "support_pivot_records": support_pivot_info["records"],
        "significant_support_pivot_records": support_pivot_info["significant_records"],
        "support_line_candidates": support_line_candidates,
        "best_support_line": best_support_line,
        "support_ref": support_ref,
        "filtered_touch_indices": filtered_touch_indices,
        "filtered_touch_prices": filtered_touch_prices,
        "support_touch_count": support_touch_count,
        "support_touch_span_bars": support_touch_span_bars,
        "support_touch_age_bars": support_touch_age_bars,
        "support_band_pct": support_band_pct,
        "clustered_too_tightly": clustered_too_tightly,
        "support_line_start_idx": support_line_start_idx,
        "support_line_end_idx": support_line_end_idx,
        "support_line_start_price": support_line_start_price,
        "support_line_end_price": support_line_end_price,
        "support_line_slope": support_line_slope,
    }


def _compute_legacy_support_validation(
    recent: pd.DataFrame,
    closes: pd.Series,
    support_pivots: pd.Series,
    cfg: BreakoutConfig,
) -> dict[str, Any]:
    highs = recent["high"]
    lows = recent["low"]

    legacy_start = cfg.td_max_support_touch_cluster_bars + 1
    legacy_slice = recent.iloc[legacy_start:]
    legacy_support_pivots = support_pivots.iloc[legacy_start:]
    legacy_valid_pivots = legacy_support_pivots.dropna()
    legacy_support_ref = float(legacy_valid_pivots.min()) if not legacy_valid_pivots.empty else (float(legacy_slice["low"].min()) if not legacy_slice.empty else np.nan)
    legacy_touch_dist_pct = (
        ((legacy_slice["low"] - legacy_support_ref) / legacy_support_ref) * 100.0
        if not legacy_slice.empty and legacy_support_ref > 0
        else pd.Series(np.nan, index=legacy_slice.index)
    )
    legacy_touch_candidate_mask = pd.Series(
        legacy_support_pivots.notna().to_numpy()
        & legacy_touch_dist_pct.ge(0).to_numpy()
        & legacy_touch_dist_pct.le(cfg.td_support_flat_max_pct).to_numpy(),
        index=legacy_slice.index,
    )
    legacy_touch_indices = np.flatnonzero(legacy_touch_candidate_mask.to_numpy())
    legacy_filtered_touch_indices: list[int] = []
    legacy_filtered_touch_prices: list[float] = []
    legacy_rebound_threshold = (
        legacy_support_ref * (1.0 + cfg.td_min_support_rebound_pct / 100.0)
        if not np.isnan(legacy_support_ref) and legacy_support_ref > 0
        else np.nan
    )
    legacy_highs = legacy_slice["high"].reset_index(drop=True)
    legacy_lows = legacy_slice["low"].reset_index(drop=True)

    for touch_idx in legacy_touch_indices:
        touch_price = float(legacy_lows.iloc[touch_idx])
        if not legacy_filtered_touch_indices:
            legacy_filtered_touch_indices.append(int(touch_idx))
            legacy_filtered_touch_prices.append(touch_price)
            continue

        prev_touch_idx = legacy_filtered_touch_indices[-1]
        if int(touch_idx - prev_touch_idx) < cfg.td_min_support_touch_separation_bars:
            if touch_price < legacy_filtered_touch_prices[-1]:
                legacy_filtered_touch_indices[-1] = int(touch_idx)
                legacy_filtered_touch_prices[-1] = touch_price
            continue

        rebound_high = float(legacy_highs.iloc[prev_touch_idx : touch_idx + 1].max())
        had_rebound = not np.isnan(legacy_rebound_threshold) and rebound_high >= legacy_rebound_threshold
        if had_rebound:
            legacy_filtered_touch_indices.append(int(touch_idx))
            legacy_filtered_touch_prices.append(touch_price)

    legacy_touch_count = len(legacy_filtered_touch_indices)
    legacy_clustered = (
        legacy_touch_count >= cfg.td_min_support_touches
        and len(legacy_filtered_touch_indices) > 0
        and int(max(legacy_filtered_touch_indices) - min(legacy_filtered_touch_indices)) <= cfg.td_max_support_touch_cluster_bars
    )
    legacy_support_flat_ok = legacy_touch_count >= cfg.td_min_support_touches and not legacy_clustered
    legacy_support_broken_now = (
        legacy_support_flat_ok
        and not np.isnan(legacy_support_ref)
        and float(closes.iloc[-1]) < legacy_support_ref * (1.0 - cfg.td_support_break_invalidation_pct / 100.0)
    )

    return {
        "legacy_support_ref": legacy_support_ref,
        "legacy_touch_count": legacy_touch_count,
        "legacy_support_flat_ok": legacy_support_flat_ok,
        "legacy_support_broken_now": legacy_support_broken_now,
    }


def _find_upper_pivot_pair(
    highs: pd.Series,
    lows: pd.Series,
    closes: pd.Series,
    x: np.ndarray,
    cfg: BreakoutConfig,
    dates: pd.Series | None = None,
) -> dict[str, Any]:
    slope, intercept = np.polyfit(x, highs.to_numpy(dtype=float), 1)
    upper_slope_now = float(slope)
    upper_line_now = float(intercept + slope * x[-1])
    pivot_high_info: dict[str, Any] = {"records": [], "significant_records": []}
    pivot_pair_found = False
    pivot_pair_score = np.nan
    pivot_older_idx: int | None = None
    pivot_newer_idx: int | None = None
    pivot_older_price = np.nan
    pivot_newer_price = np.nan
    selected_right_anchor_recency_score = 0.0
    selected_late_window_score = 0.0
    selected_ma_context_score = 0.0
    selected_ma_proximity_score = 0.0
    selected_overshoot_penalty_raw = 0.0
    selected_significant_overshoot_count = 0

    if cfg.td_use_pivot_upper_line:
        range_low = float(lows.min())
        range_high = float(highs.max())
        range_size = range_high - range_low
        min_pivot_price = (
            range_low + range_size * (cfg.td_pivot_min_relative_height_pct / 100.0)
            if range_size > 0
            else np.nan
        )
        pivot_high_info = find_significant_pivot_highs(highs, lows, cfg, dates)
        all_pivot_records = pivot_high_info["records"]
        significant_pivot_records = pivot_high_info["significant_records"]
        candidate_records = significant_pivot_records if significant_pivot_records else all_pivot_records
        significant_record_map = {int(record["idx"]): record for record in significant_pivot_records}
        breakout_reference_idx = len(highs) - 1
        left_candidate_records = build_left_high_candidates(candidate_records, cfg)
        right_candidate_records = build_right_high_candidates(candidate_records, breakout_reference_idx, closes, cfg)
        left_candidate_map = {int(record["idx"]): record for record in left_candidate_records}
        right_candidate_map = {int(record["idx"]): record for record in right_candidate_records}
        best_pair_score = -np.inf
        best_pair: tuple[int, int, float, float] | None = None
        best_pair_meta: dict[str, Any] | None = None

        for newer_idx in [int(record["idx"]) for record in right_candidate_records]:
            newer_price = float(highs.iloc[newer_idx])
            if not np.isnan(min_pivot_price) and newer_price < min_pivot_price:
                continue
            newer_record = right_candidate_map.get(newer_idx, {})
            newer_significance = float(newer_record.get("significance_score", 0.0))
            newer_recency_score = float(newer_record.get("right_anchor_recency_score", 0.0))
            late_window_score = float(newer_record.get("late_window_score", 0.0))
            right_anchor_score = float(newer_record.get("right_anchor_score", 0.0))
            ma_context_score = float(newer_record.get("ma_context_score", 0.0))
            ma_proximity_score = float(newer_record.get("ma_proximity_score", 0.0))

            for older_idx in [int(record["idx"]) for record in left_candidate_records]:
                if older_idx >= newer_idx:
                    continue
                separation = newer_idx - older_idx
                if separation < cfg.td_min_pivot_separation_bars or separation > cfg.td_max_pivot_separation_bars:
                    continue

                older_price = float(highs.iloc[older_idx])
                if not np.isnan(min_pivot_price) and older_price < min_pivot_price:
                    continue
                if older_price < newer_price:
                    continue
                older_record = left_candidate_map.get(older_idx, {})
                older_significance = float(older_record.get("significance_score", 0.0))
                left_anchor_score = float(older_record.get("left_anchor_score", 0.0))

                candidate_slope = (newer_price - older_price) / max(separation, 1)
                if candidate_slope >= 0:
                    continue

                line_values = older_price + candidate_slope * (x - older_idx)
                valid_slice = slice(older_idx, breakout_reference_idx + 1)
                eval_highs = highs.iloc[valid_slice].to_numpy(dtype=float)
                eval_line = line_values[valid_slice]
                overshoot_pct = _safe_pct_distance(eval_highs - eval_line, eval_line)
                touch_tolerance_pct = max(cfg.td_support_flat_max_pct * 0.20, 0.75)
                overshoot_tolerance_pct = max(cfg.td_support_flat_max_pct * 0.10, cfg.td_upper_line_overshoot_tolerance_pct)
                touch_count = int(np.nansum((overshoot_pct >= -touch_tolerance_pct) & (overshoot_pct <= touch_tolerance_pct)))
                overshoot_penalty = float(np.nansum(np.clip(overshoot_pct - overshoot_tolerance_pct, a_min=0.0, a_max=None)))
                cutthrough_penalty = float(np.nansum((overshoot_pct > overshoot_tolerance_pct) & (np.arange(len(eval_highs)) > (newer_idx - older_idx)))) * 2.0

                significant_overshoot_penalty = 0.0
                significant_overshoot_count = 0
                for sig_idx, sig_record in significant_record_map.items():
                    if sig_idx < older_idx or sig_idx > breakout_reference_idx or sig_idx in {older_idx, newer_idx}:
                        continue
                    line_price_at_sig = float(older_price + candidate_slope * (sig_idx - older_idx))
                    if line_price_at_sig <= 0:
                        continue
                    sig_price = float(highs.iloc[sig_idx])
                    sig_overshoot_pct = ((sig_price / line_price_at_sig) - 1.0) * 100.0
                    if sig_overshoot_pct <= overshoot_tolerance_pct:
                        continue
                    significant_overshoot_count += 1
                    significance_weight = max(float(sig_record.get("significance_score", 0.0)), 0.0) / 100.0
                    significant_overshoot_penalty += (
                        max(sig_overshoot_pct - overshoot_tolerance_pct, 0.0)
                        * max(significance_weight, 0.25)
                        * cfg.td_upper_line_significant_overshoot_penalty
                    )

                separation_score = 100.0 * clamp01(
                    (separation - cfg.td_min_pivot_separation_bars)
                    / max(cfg.td_max_pivot_separation_bars - cfg.td_min_pivot_separation_bars, 1)
                )
                significance_score = older_significance * 0.55 + newer_significance * 0.45
                right_anchor_staleness_penalty = max(
                    (breakout_reference_idx - newer_idx) - cfg.td_upper_anchor_late_window_bars,
                    0,
                )
                candidate_pair_score = (
                    left_anchor_score * 0.22
                    + right_anchor_score * 0.34
                    + significance_score * 0.12
                    + separation_score * 0.03
                    + newer_recency_score * 0.08
                    + late_window_score * 0.12
                    + ma_context_score * 0.07
                    + ma_proximity_score * 0.05
                    + min(touch_count, 4) * 3.5
                    - overshoot_penalty * 0.70
                    - cutthrough_penalty
                    - significant_overshoot_penalty
                    - significant_overshoot_count * 7.0
                    - right_anchor_staleness_penalty * 2.0
                )

                if candidate_pair_score > best_pair_score:
                    best_pair_score = candidate_pair_score
                    best_pair = (older_idx, newer_idx, older_price, newer_price)
                    best_pair_meta = {
                        "right_anchor_recency_score": newer_recency_score,
                        "late_window_score": late_window_score,
                        "ma_context_score": ma_context_score,
                        "ma_proximity_score": ma_proximity_score,
                        "overshoot_penalty_raw": float(
                            overshoot_penalty
                            + cutthrough_penalty
                            + significant_overshoot_penalty
                            + significant_overshoot_count * 7.0
                        ),
                        "significant_overshoot_count": int(significant_overshoot_count),
                    }

        if best_pair is not None:
            older_idx, newer_idx, older_price, newer_price = best_pair
            pivot_older_idx = int(older_idx)
            pivot_newer_idx = int(newer_idx)
            pivot_older_price = float(older_price)
            pivot_newer_price = float(newer_price)
            pivot_pair_found = True
            pivot_pair_score = float(best_pair_score)
            upper_slope_now = (newer_price - older_price) / max(newer_idx - older_idx, 1)
            upper_line_now = float(older_price + upper_slope_now * (x[-1] - older_idx))
            if best_pair_meta is not None:
                selected_right_anchor_recency_score = float(best_pair_meta["right_anchor_recency_score"])
                selected_late_window_score = float(best_pair_meta["late_window_score"])
                selected_ma_context_score = float(best_pair_meta["ma_context_score"])
                selected_ma_proximity_score = float(best_pair_meta["ma_proximity_score"])
                selected_overshoot_penalty_raw = float(best_pair_meta["overshoot_penalty_raw"])
                selected_significant_overshoot_count = int(best_pair_meta["significant_overshoot_count"])

    return {
        "upper_slope_now": upper_slope_now,
        "upper_line_now": upper_line_now,
        "pivot_pair_found": pivot_pair_found,
        "pivot_pair_score": pivot_pair_score,
        "upper_pivot_records": pivot_high_info["records"] if cfg.td_use_pivot_upper_line else [],
        "significant_upper_pivot_records": pivot_high_info["significant_records"] if cfg.td_use_pivot_upper_line else [],
        "pivot_older_idx": pivot_older_idx,
        "pivot_newer_idx": pivot_newer_idx,
        "pivot_older_price": pivot_older_price,
        "pivot_newer_price": pivot_newer_price,
        "right_anchor_recency_score": selected_right_anchor_recency_score,
        "late_window_score": selected_late_window_score,
        "ma_context_score": selected_ma_context_score,
        "ma_proximity_score": selected_ma_proximity_score,
        "upper_overshoot_penalty_raw": selected_overshoot_penalty_raw,
        "upper_significant_overshoot_count": selected_significant_overshoot_count,
    }


def _compute_triangle_window_scores(
    *,
    support_band_pct: float,
    descending_drop_pct: float,
    compression_ratio: float,
    vertex_gap_pct: float,
    breakout_pct: float,
    cfg: BreakoutConfig,
) -> dict[str, float]:
    support_score_raw = 100.0 * clamp01(1.0 - (support_band_pct / cfg.td_support_flat_max_pct)) if not np.isnan(support_band_pct) else 0.0
    descending_score_raw = 100.0 * clamp01((-descending_drop_pct) / (cfg.td_descending_min_drop_pct * 2.0)) if not np.isnan(descending_drop_pct) else 0.0
    compression_score_raw = 100.0 * clamp01(1.0 - (compression_ratio / cfg.td_compression_max_ratio)) if not np.isnan(compression_ratio) else 0.0
    vertex_score_raw = 100.0 * clamp01(1.0 - (vertex_gap_pct / cfg.td_max_vertex_gap_pct)) if not np.isnan(vertex_gap_pct) else 0.0
    breakout_score_raw = 100.0 * clamp01(breakout_pct / (cfg.td_breakout_buffer_pct * 2.0 + 0.0001)) if not np.isnan(breakout_pct) else 0.0
    structure_score_raw = support_score_raw * 0.30 + descending_score_raw * 0.25 + compression_score_raw * 0.25 + vertex_score_raw * 0.20
    return {
        "support_score_raw": support_score_raw,
        "descending_score_raw": descending_score_raw,
        "compression_score_raw": compression_score_raw,
        "vertex_score_raw": vertex_score_raw,
        "structure_score_raw": structure_score_raw,
        "breakout_score_raw": breakout_score_raw,
    }


def _triangle_raw_metric_defaults() -> dict[str, Any]:
    return {
        "TD Support Band %": np.nan,
        "TD Vertex Date": None,
        "TD Breakout Date": None,
        "TD Bars Since Breakout": np.nan,
        "TD Structure Range Ratio": np.nan,
        "TD Structure Start Height $": np.nan,
        "TD Structure Start Height %": np.nan,
        "TD Triangle Progress %": np.nan,
        "TD Upper Pivot Newer Bars From Now": np.nan,
        "TD Upper Overshoot Penalty Raw": 0.0,
        "TD Upper Significant Overshoot Count": 0,
        "TD Right Anchor MA20 Distance %": np.nan,
        "TD Right Anchor MA50 Distance %": np.nan,
        "TD Upper Pair Quality Raw": 0.0,
        "TD Support Credibility Raw": 0.0,
        "TD Horizontal Support Raw": 0.0,
        "TD Rising Support Raw": 0.0,
        "TD MA Support Raw": 0.0,
        "TD Descending Highs Raw": 0.0,
        "TD Compression Raw": 0.0,
        "TD Vertex Raw": 0.0,
        "TD Broad Structure Raw": 0.0,
        "TD Breakout Recency Raw": 0.0,
        "TD Right Anchor Recency Raw": 0.0,
        "TD Triangle Maturity Raw": 0.0,
        "TD Breakout Strength Raw": 0.0,
        "TD MA Interaction Raw": 0.0,
        "TD Reversal Context Raw": 0.0,
        "TD Trend Context Raw": 0.0,
        "TD Anti Decline Raw": 0.0,
        "TD Support Failure Penalty Raw": 0.0,
        "TD Staleness Penalty Raw": 0.0,
        "TD Severe Decline Penalty Raw": 0.0,
        "TD Overshoot Penalty Raw": 0.0,
        "Geometry Weighted": 0.0,
        "Timeliness Weighted": 0.0,
        "Context Weighted": 0.0,
        "Penalty Weighted": 0.0,
        "Triangle Composite Score": 0.0,
    }


TRIANGLE_SCORE_WEIGHTS: dict[str, float] = {
    "geometry": 1.0,
    "timeliness": 1.0,
    "context": 1.0,
    "penalty": 1.0,
    "upper_pair": 0.30,
    "descending_highs": 0.15,
    "compression": 0.15,
    "vertex": 0.10,
    "broad_structure": 0.10,
    "support_credibility": 0.20,
    "breakout_recency": 0.35,
    "right_anchor_recency": 0.25,
    "triangle_maturity": 0.20,
    "breakout_strength": 0.20,
    "ma_interaction": 0.35,
    "reversal_context": 0.35,
    "trend_context": 0.15,
    "anti_decline": 0.15,
    "support_failure_penalty": 0.35,
    "staleness_penalty": 0.25,
    "severe_decline_penalty": 0.20,
    "overshoot_penalty": 0.20,
}


def _compute_triangle_composite_components(row: pd.Series) -> dict[str, float]:
    weights = TRIANGLE_SCORE_WEIGHTS
    geometry_weighted = (
        weights["upper_pair"] * zero_if_nan(row.get("upper_pair_quality_raw"))
        + weights["descending_highs"] * zero_if_nan(row.get("descending_highs_raw"))
        + weights["compression"] * zero_if_nan(row.get("compression_raw"))
        + weights["vertex"] * zero_if_nan(row.get("vertex_raw"))
        + weights["broad_structure"] * zero_if_nan(row.get("broad_structure_raw"))
        + weights["support_credibility"] * zero_if_nan(row.get("support_credibility_raw"))
    ) * weights["geometry"]
    timeliness_weighted = (
        weights["breakout_recency"] * zero_if_nan(row.get("breakout_recency_raw"))
        + weights["right_anchor_recency"] * zero_if_nan(row.get("right_anchor_recency_raw"))
        + weights["triangle_maturity"] * zero_if_nan(row.get("triangle_maturity_raw"))
        + weights["breakout_strength"] * zero_if_nan(row.get("breakout_strength_raw"))
    ) * weights["timeliness"]
    context_weighted = (
        weights["ma_interaction"] * zero_if_nan(row.get("ma_interaction_raw"))
        + weights["reversal_context"] * zero_if_nan(row.get("reversal_context_raw"))
        + weights["trend_context"] * zero_if_nan(row.get("trend_context_raw"))
        + weights["anti_decline"] * zero_if_nan(row.get("anti_decline_raw"))
    ) * weights["context"]
    penalty_weighted = (
        weights["support_failure_penalty"] * zero_if_nan(row.get("support_failure_penalty_raw"))
        + weights["staleness_penalty"] * zero_if_nan(row.get("staleness_penalty_raw"))
        + weights["severe_decline_penalty"] * zero_if_nan(row.get("severe_decline_penalty_raw"))
        + weights["overshoot_penalty"] * zero_if_nan(row.get("overshoot_penalty_raw"))
    ) * weights["penalty"]
    triangle_composite_score = geometry_weighted + timeliness_weighted + context_weighted - penalty_weighted
    return {
        "geometry_weighted": geometry_weighted,
        "timeliness_weighted": timeliness_weighted,
        "context_weighted": context_weighted,
        "penalty_weighted": penalty_weighted,
        "triangle_composite_score": triangle_composite_score,
    }


def _resolve_triangle_anchor(
    *,
    closes: pd.Series,
    support_line_start_idx: int | None,
    support_line_start_price: float,
    support_line_slope: float,
    pivot_older_idx: int | None,
    pivot_older_price: float,
    upper_slope_now: float,
    bars_to_vertex: float,
    breakout_pct: float,
    cfg: BreakoutConfig,
) -> dict[str, Any]:
    length = len(closes)
    if length == 0 or support_line_start_idx is None or pivot_older_idx is None:
        return {
            "anchor_type": "none",
            "anchor_idx": None,
            "anchor_bars_from_now": np.nan,
            "anchor_price_gap_pct": np.nan,
        }

    x = np.arange(length, dtype=float)
    support_line_values = support_line_start_price + support_line_slope * (x - support_line_start_idx)
    upper_line_values = pivot_older_price + upper_slope_now * (x - pivot_older_idx)
    breakout_threshold_values = upper_line_values * (1.0 + cfg.td_breakout_buffer_pct / 100.0)
    resolved_window_start = max(0, length - cfg.td_anchor_recent_bars)
    resolved_indices = [
        idx
        for idx in range(resolved_window_start, length)
        if breakout_threshold_values[idx] > 0 and float(closes.iloc[idx]) >= breakout_threshold_values[idx]
    ]
    if resolved_indices:
        anchor_idx = int(min(resolved_indices))
        support_at_anchor = float(support_line_values[anchor_idx])
        upper_at_anchor = float(upper_line_values[anchor_idx])
        anchor_gap_pct = ((upper_at_anchor - support_at_anchor) / support_at_anchor) * 100.0 if support_at_anchor > 0 else np.nan
        return {
            "anchor_type": "resolved",
            "anchor_idx": anchor_idx,
            "anchor_bars_from_now": float((length - 1) - anchor_idx),
            "anchor_price_gap_pct": anchor_gap_pct,
        }

    if (
        pd.notna(bars_to_vertex)
        and bars_to_vertex > 0
        and bars_to_vertex <= cfg.td_projected_anchor_max_bars_ahead
        and pd.notna(breakout_pct)
        and breakout_pct >= -max(cfg.td_breakout_buffer_pct * 3.0, 3.0)
    ):
        projected_anchor_idx = int((length - 1) + max(round(float(bars_to_vertex)), 1))
        support_at_anchor = float(support_line_start_price + support_line_slope * (projected_anchor_idx - support_line_start_idx))
        upper_at_anchor = float(pivot_older_price + upper_slope_now * (projected_anchor_idx - pivot_older_idx))
        anchor_gap_pct = ((upper_at_anchor - support_at_anchor) / support_at_anchor) * 100.0 if support_at_anchor > 0 else np.nan
        if pd.notna(anchor_gap_pct) and 0 <= anchor_gap_pct <= cfg.td_projected_anchor_max_height_pct:
            return {
                "anchor_type": "projected",
                "anchor_idx": projected_anchor_idx,
                "anchor_bars_from_now": float(projected_anchor_idx - (length - 1)),
                "anchor_price_gap_pct": anchor_gap_pct,
            }

    return {
        "anchor_type": "none",
        "anchor_idx": None,
        "anchor_bars_from_now": np.nan,
        "anchor_price_gap_pct": np.nan,
    }


def _build_triangle_window_result(
    *,
    recent: pd.DataFrame,
    date_at,
    support_flat_ok: bool,
    descending_highs_ok: bool,
    compression_ok: bool,
    near_vertex_ok: bool,
    structure_ok: bool,
    current_support_intact: bool,
    support_touch_count: int,
    support_touch_span_bars: int,
    support_touch_age_bars: int,
    support_band_pct: float,
    breakout_pct: float,
    breakout_bar: bool,
    still_above_breakout: bool,
    compression_ratio: float,
    vertex_gap_pct: float,
    descending_drop_pct: float,
    pivot_pair_found: bool,
    pivot_pair_score: float,
    support_ref: float,
    support_line_start_idx: int | None,
    support_line_end_idx: int | None,
    support_line_start_price: float,
    support_line_end_price: float,
    support_line_slope: float,
    upper_slope_now: float,
    upper_line_now: float,
    pivot_older_idx: int | None,
    pivot_newer_idx: int | None,
    pivot_older_price: float,
    pivot_newer_price: float,
    bars_to_vertex: float,
    anchor_type: str,
    anchor_idx: int | None,
    anchor_bars_from_now: float,
    anchor_price_gap_pct: float,
    structure_score_raw: float,
    breakout_score_raw: float,
) -> dict[str, Any]:
    upper_line_end_idx = len(recent) - 1 if len(recent) > 0 else None
    resolved_breakout_date = date_at(anchor_idx) if anchor_type == "resolved" else None
    resolved_bars_since_breakout = anchor_bars_from_now if anchor_type == "resolved" else np.nan
    vertex_date = _business_date_offset_from_last(recent, bars_to_vertex)

    return {
        "support_flat_ok": int(support_flat_ok),
        "descending_highs_ok": int(descending_highs_ok),
        "compression_ok": int(compression_ok),
        "near_vertex_ok": int(near_vertex_ok),
        "structure_ok": int(structure_ok),
        "current_support_intact": int(current_support_intact),
        "support_touch_count": support_touch_count,
        "support_touch_span_bars": support_touch_span_bars,
        "support_touch_age_bars": support_touch_age_bars,
        "support_band_pct": support_band_pct,
        "breakout_pct": breakout_pct,
        "breakout_bar": int(breakout_bar),
        "still_above_breakout": int(still_above_breakout),
        "compression_ratio": compression_ratio,
        "vertex_gap_pct": vertex_gap_pct,
        "descending_drop_pct": descending_drop_pct,
        "pivot_pair_found": int(pivot_pair_found),
        "pivot_pair_score": pivot_pair_score,
        "triangle_window_bars": int(len(recent)),
        "triangle_window_start_date": date_at(0),
        "triangle_window_end_date": date_at(len(recent) - 1 if len(recent) > 0 else None),
        "support_ref": support_ref,
        "support_line_start_idx": support_line_start_idx,
        "support_line_end_idx": support_line_end_idx,
        "support_line_start_date": date_at(support_line_start_idx),
        "support_line_end_date": date_at(support_line_end_idx),
        "support_line_start_price": support_line_start_price,
        "support_line_end_price": support_line_end_price,
        "support_line_slope": support_line_slope,
        "upper_line_slope": upper_slope_now,
        "upper_line_now": upper_line_now,
        "upper_line_end_idx": upper_line_end_idx,
        "upper_line_end_date": date_at(upper_line_end_idx),
        "pivot_older_idx": pivot_older_idx,
        "pivot_newer_idx": pivot_newer_idx,
        "pivot_older_date": date_at(pivot_older_idx),
        "pivot_newer_date": date_at(pivot_newer_idx),
        "pivot_older_price": pivot_older_price,
        "pivot_newer_price": pivot_newer_price,
        "bars_to_vertex": bars_to_vertex,
        "breakout_date": resolved_breakout_date,
        "bars_since_breakout": resolved_bars_since_breakout,
        "vertex_date": vertex_date,
        "anchor_type": anchor_type,
        "anchor_idx": anchor_idx,
        "anchor_date": date_at(anchor_idx),
        "anchor_bars_from_now": anchor_bars_from_now,
        "anchor_price_gap_pct": anchor_price_gap_pct,
        "structure_score_raw": structure_score_raw,
        "breakout_score_raw": breakout_score_raw,
    }


def _triangle_window_metrics(
    recent: pd.DataFrame,
    cfg: BreakoutConfig,
    debug_profile: dict[str, float] | None = None,
) -> dict[str, Any]:
    window_started_at = time.perf_counter() if debug_profile is not None else 0.0
    lows = recent["low"]
    highs = recent["high"]
    closes = recent["close"]
    _, date_at = _triangle_date_lookup(recent)

    support_flat_ok = (
        True
    )

    early_high = highs.shift(cfg.td_triangle_recent_bars).rolling(
        cfg.td_triangle_lookback_bars - cfg.td_triangle_recent_bars
    ).max().iloc[-1]
    recent_high = float(highs.tail(cfg.td_triangle_recent_bars).max())
    descending_drop_pct = ((recent_high / early_high) - 1.0) * 100.0 if pd.notna(early_high) and early_high > 0 else np.nan

    x = np.arange(len(highs), dtype=float)
    upper_started_at = time.perf_counter() if debug_profile is not None else 0.0
    upper_line_metrics = _find_upper_pivot_pair(
        highs,
        lows,
        closes,
        x,
        cfg,
        recent["date"] if "date" in recent.columns else None,
    )
    if debug_profile is not None:
        _profile_add(debug_profile, "triangle_upper", time.perf_counter() - upper_started_at)
    upper_slope_now = upper_line_metrics["upper_slope_now"]
    upper_line_now = upper_line_metrics["upper_line_now"]
    pivot_pair_found = bool(upper_line_metrics["pivot_pair_found"])
    pivot_pair_score = upper_line_metrics["pivot_pair_score"]
    pivot_older_idx = upper_line_metrics["pivot_older_idx"]
    pivot_newer_idx = upper_line_metrics["pivot_newer_idx"]
    pivot_older_price = upper_line_metrics["pivot_older_price"]
    pivot_newer_price = upper_line_metrics["pivot_newer_price"]

    support_started_at = time.perf_counter() if debug_profile is not None else 0.0
    support_metrics = _compute_support_touch_metrics(
        recent,
        lows,
        highs,
        closes,
        cfg,
        reference_high_idx=pivot_older_idx,
    )
    if debug_profile is not None:
        _profile_add(debug_profile, "triangle_support", time.perf_counter() - support_started_at)
    support_pivots = support_metrics["support_pivots"]
    support_ref = support_metrics["support_ref"]
    filtered_touch_indices = support_metrics["filtered_touch_indices"]
    support_touch_count = support_metrics["support_touch_count"]
    support_touch_span_bars = support_metrics["support_touch_span_bars"]
    support_touch_age_bars = support_metrics["support_touch_age_bars"]
    support_band_pct = support_metrics["support_band_pct"]
    clustered_too_tightly = support_metrics["clustered_too_tightly"]
    support_line_start_idx = support_metrics["support_line_start_idx"]
    support_line_end_idx = support_metrics["support_line_end_idx"]
    support_line_start_price = support_metrics["support_line_start_price"]
    support_line_end_price = support_metrics["support_line_end_price"]
    support_line_slope = support_metrics["support_line_slope"]

    support_flat_ok = (
        support_touch_count >= cfg.td_min_support_touches
        and support_touch_span_bars >= cfg.td_min_support_touch_span_bars
        and support_touch_age_bars <= cfg.td_support_right_touch_max_age_bars
        and not np.isnan(support_band_pct)
        and support_band_pct <= cfg.td_support_flat_max_pct
        and not clustered_too_tightly
        and support_line_start_idx is not None
    )
    current_support_intact = support_touch_count >= cfg.td_min_support_touches

    recent_range = float(highs.tail(cfg.td_triangle_recent_bars).max() - lows.tail(cfg.td_triangle_recent_bars).min())
    whole_range = float(highs.max() - lows.min())
    compression_ratio = recent_range / whole_range if whole_range > 0 else np.nan
    compression_ok = not np.isnan(compression_ratio) and compression_ratio <= cfg.td_compression_max_ratio

    structure_start_candidates = [idx for idx in [support_line_start_idx, pivot_older_idx] if idx is not None]
    structure_start_idx = min(structure_start_candidates) if structure_start_candidates else None
    structure_range_ratio = np.nan
    structure_start_height_abs = np.nan
    structure_start_height_pct = np.nan
    broad_structure_ok = False
    if structure_start_idx is not None and whole_range > 0 and support_line_start_idx is not None and pivot_older_idx is not None:
        active_highs = highs.iloc[structure_start_idx:]
        active_lows = lows.iloc[structure_start_idx:]
        active_range = float(active_highs.max() - active_lows.min()) if len(active_highs) > 0 else np.nan
        structure_range_ratio = active_range / whole_range if pd.notna(active_range) and whole_range > 0 else np.nan
        support_at_start = float(support_line_start_price + support_line_slope * (structure_start_idx - support_line_start_idx))
        upper_at_start = float(pivot_older_price + upper_slope_now * (structure_start_idx - pivot_older_idx))
        structure_start_height_abs = upper_at_start - support_at_start
        structure_start_height_pct = (
            ((upper_at_start - support_at_start) / support_at_start) * 100.0
            if support_at_start > 0
            else np.nan
        )
        broad_structure_ok = (
            pd.notna(structure_range_ratio)
            and structure_range_ratio >= cfg.td_min_structure_range_ratio
            and pd.notna(structure_start_height_pct)
            and structure_start_height_pct >= cfg.td_min_triangle_start_height_pct
        )

    descending_highs_pct_ok = (
        upper_slope_now < 0
        and not np.isnan(descending_drop_pct)
        and descending_drop_pct <= -cfg.td_descending_min_drop_pct
    )
    descending_highs_height_ok = (
        upper_slope_now < 0
        and pd.notna(structure_start_height_abs)
        and float(structure_start_height_abs) >= cfg.td_descending_min_height_abs
    )
    descending_highs_base_ok = bool(descending_highs_pct_ok or descending_highs_height_ok)
    descending_highs_ok = (
        descending_highs_base_ok and pivot_pair_found
        if cfg.td_use_pivot_upper_line
        else descending_highs_base_ok
    )

    vertex_gap_pct = ((upper_line_now - support_ref) / support_ref) * 100.0 if support_ref > 0 else np.nan
    bars_to_vertex = (
        (upper_line_now - support_ref) / abs(upper_slope_now)
        if upper_slope_now < 0 and upper_line_now > support_ref
        else np.nan
    )

    breakout_pct = ((float(closes.iloc[-1]) / upper_line_now) - 1.0) * 100.0 if upper_line_now > 0 else np.nan

    anchor_started_at = time.perf_counter() if debug_profile is not None else 0.0
    anchor_metrics = _resolve_triangle_anchor(
        closes=closes,
        support_line_start_idx=support_line_start_idx,
        support_line_start_price=support_line_start_price,
        support_line_slope=support_line_slope,
        pivot_older_idx=pivot_older_idx,
        pivot_older_price=pivot_older_price,
        upper_slope_now=upper_slope_now,
        bars_to_vertex=bars_to_vertex,
        breakout_pct=breakout_pct,
        cfg=cfg,
    )
    if debug_profile is not None:
        _profile_add(debug_profile, "triangle_anchor", time.perf_counter() - anchor_started_at)
    anchor_type = str(anchor_metrics["anchor_type"])
    anchor_idx = anchor_metrics["anchor_idx"]
    anchor_bars_from_now = anchor_metrics["anchor_bars_from_now"]
    anchor_price_gap_pct = anchor_metrics["anchor_price_gap_pct"]

    projected_vertex_idx = (
        float((len(highs) - 1) + bars_to_vertex)
        if pd.notna(bars_to_vertex)
        else np.nan
    )
    triangle_progress_pct = np.nan
    if (
        structure_start_idx is not None
        and anchor_idx is not None
        and pd.notna(projected_vertex_idx)
        and projected_vertex_idx > float(structure_start_idx)
        and int(anchor_idx) >= int(structure_start_idx)
    ):
        triangle_progress_pct = (
            (float(anchor_idx) - float(structure_start_idx))
            / max(projected_vertex_idx - float(structure_start_idx), 1.0)
        ) * 100.0

    standard_near_vertex_ok = (
        not np.isnan(vertex_gap_pct)
        and vertex_gap_pct <= cfg.td_max_vertex_gap_pct
        and not np.isnan(bars_to_vertex)
        and bars_to_vertex <= cfg.td_max_bars_to_vertex
    )
    early_breakout_ok = bool(
        anchor_type == "resolved"
        and pd.notna(vertex_gap_pct)
        and vertex_gap_pct <= cfg.td_max_vertex_gap_pct
        and pd.notna(triangle_progress_pct)
        and triangle_progress_pct >= cfg.td_resolved_min_triangle_progress_pct
        and anchor_bars_from_now is not None
        and pd.notna(anchor_bars_from_now)
        and float(anchor_bars_from_now) <= cfg.td_breakout_recent_bars
    )
    if anchor_type == "projected":
        near_vertex_ok = bool(
            standard_near_vertex_ok
            and pd.notna(bars_to_vertex)
            and bars_to_vertex > 0
        )
    elif anchor_type == "resolved":
        near_vertex_ok = bool(standard_near_vertex_ok or early_breakout_ok)
    else:
        near_vertex_ok = False

    support_pre_anchor_ok = True
    upper_pre_anchor_ok = True
    if anchor_type == "resolved" and anchor_idx is not None:
        support_pre_anchor_ok = all(int(idx) < int(anchor_idx) for idx in filtered_touch_indices)
        upper_pre_anchor_ok = pivot_newer_idx is not None and int(pivot_newer_idx) < int(anchor_idx)

    structure_ok = bool(
        support_flat_ok
        and descending_highs_ok
        and compression_ok
        and near_vertex_ok
        and broad_structure_ok
        and support_pre_anchor_ok
        and upper_pre_anchor_ok
        and anchor_type in {"resolved", "projected"}
    )
    breakout_bar = structure_ok and not np.isnan(breakout_pct) and breakout_pct >= cfg.td_breakout_buffer_pct and float(closes.iloc[-1]) > upper_line_now
    still_above_breakout = not np.isnan(upper_line_now) and float(closes.iloc[-1]) >= upper_line_now * (1.0 + cfg.td_breakout_buffer_pct / 100.0)
    score_started_at = time.perf_counter() if debug_profile is not None else 0.0
    score_metrics = _compute_triangle_window_scores(
        support_band_pct=support_band_pct,
        descending_drop_pct=descending_drop_pct,
        compression_ratio=compression_ratio,
        vertex_gap_pct=vertex_gap_pct,
        breakout_pct=breakout_pct,
        cfg=cfg,
    )
    sma20 = closes.rolling(20, min_periods=5).mean()
    sma50 = closes.rolling(50, min_periods=10).mean()
    ma20_distance_pct = np.nan
    ma50_distance_pct = np.nan
    if pivot_newer_idx is not None and 0 <= int(pivot_newer_idx) < len(closes):
        newer_close = float(closes.iloc[int(pivot_newer_idx)])
        sma20_value = sma20.iloc[int(pivot_newer_idx)]
        sma50_value = sma50.iloc[int(pivot_newer_idx)]
        if pd.notna(sma20_value) and sma20_value > 0 and newer_close > 0:
            ma20_distance_pct = abs((newer_close / float(sma20_value)) - 1.0) * 100.0
        if pd.notna(sma50_value) and sma50_value > 0 and newer_close > 0:
            ma50_distance_pct = abs((newer_close / float(sma50_value)) - 1.0) * 100.0

    horizontal_support_raw = 0.0
    rising_support_raw = 0.0
    ma_support_raw = 0.0
    support_credibility_raw = 0.0
    if support_line_start_idx is not None:
        horizontal_support_raw = (
            score_metrics["support_score_raw"]
            + min(support_touch_count, 4) * 8.0
            + 100.0 * clamp01(support_touch_span_bars / max(cfg.td_triangle_lookback_bars, 1)) * 0.35
        )
    if support_metrics["best_support_line"] is not None:
        best_support_line = support_metrics["best_support_line"]
        slope_scale = max(cfg.td_support_max_positive_slope_pct, cfg.td_support_max_negative_slope_pct, 0.01)
        support_slope_pct_per_bar = (
            ((support_line_slope / ((support_line_start_price + support_line_end_price) / 2.0)) * 100.0)
            if (support_line_start_price + support_line_end_price) > 0
            else np.nan
        )
        slope_friendliness = (
            100.0 * clamp01(1.0 - (abs(zero_if_nan(support_slope_pct_per_bar)) / slope_scale))
            if pd.notna(support_slope_pct_per_bar)
            else 50.0
        )
        rising_support_raw = (
            slope_friendliness * 0.55
            + zero_if_nan(best_support_line.get("launch_gain_score")) * 0.25
            + zero_if_nan(best_support_line.get("body_alignment_score", 50.0)) * 0.20
        )
        ma_scores: list[float] = []
        for idx in [int(idx) for idx in filtered_touch_indices]:
            low_price = float(lows.iloc[idx])
            close_price = float(closes.iloc[idx])
            for ma_series in (sma20, sma50):
                if idx >= len(ma_series):
                    continue
                ma_value = ma_series.iloc[idx]
                if pd.isna(ma_value) or ma_value <= 0:
                    continue
                low_dist_pct = abs((low_price / float(ma_value)) - 1.0) * 100.0 if low_price > 0 else np.nan
                close_dist_pct = abs((close_price / float(ma_value)) - 1.0) * 100.0 if close_price > 0 else np.nan
                near_dist_pct = np.nanmin([low_dist_pct, close_dist_pct])
                if pd.notna(near_dist_pct):
                    ma_scores.append(100.0 * clamp01(1.0 - (near_dist_pct / 4.0)))
        if ma_scores:
            ma_support_raw = float(np.nanmean(ma_scores))
    support_credibility_raw = horizontal_support_raw + rising_support_raw + ma_support_raw

    broad_structure_raw = (
        100.0 * clamp01(zero_if_nan(structure_range_ratio) / max(cfg.td_min_structure_range_ratio, 0.01)) * 0.55
        + 100.0 * clamp01(zero_if_nan(structure_start_height_pct) / max(cfg.td_min_triangle_start_height_pct, 0.01)) * 0.45
    )
    breakout_recency_raw = 0.0
    if anchor_type == "resolved" and pd.notna(anchor_bars_from_now):
        breakout_recency_raw = 100.0 * clamp01(
            1.0 - (float(anchor_bars_from_now) / max(cfg.td_breakout_recent_bars, 1))
        )
    right_anchor_bars_from_now = float((len(highs) - 1) - pivot_newer_idx) if pivot_newer_idx is not None else np.nan
    right_anchor_recency_raw = (
        100.0 * clamp01(1.0 - (right_anchor_bars_from_now / max(cfg.td_upper_anchor_max_bars_before_breakout, 1)))
        if pd.notna(right_anchor_bars_from_now)
        else 0.0
    )
    triangle_maturity_raw = zero_if_nan(triangle_progress_pct)
    ma_interaction_raw = (
        zero_if_nan(upper_line_metrics.get("ma_context_score")) * 0.65
        + zero_if_nan(upper_line_metrics.get("ma_proximity_score")) * 0.35
    )
    recent_5d_return_pct = (
        ((float(closes.iloc[-1]) / float(closes.iloc[-6])) - 1.0) * 100.0
        if len(closes) >= 6 and float(closes.iloc[-6]) > 0
        else 0.0
    )
    recent_up_days = int((closes.tail(4).diff().iloc[1:] > 0).sum()) if len(closes) >= 4 else 0
    reversal_context_raw = (
        min(max(recent_5d_return_pct, 0.0) * 12.0, 100.0) * 0.45
        + min(recent_up_days * 25.0, 100.0) * 0.25
        + ma_interaction_raw * 0.30
    )
    recent_20_slope = float(closes.iloc[-1] - closes.iloc[-20]) / 19.0 if len(closes) >= 20 else np.nan
    older_20_slope = float(closes.iloc[-20] - closes.iloc[-40]) / 20.0 if len(closes) >= 40 else np.nan
    anti_decline_raw = 0.0
    if pd.notna(recent_20_slope):
        anti_decline_raw += 100.0 * clamp01(max(recent_20_slope, 0.0) / max(float(closes.iloc[-1]) * 0.02, 0.01)) * 0.50
    if pd.notna(recent_20_slope) and pd.notna(older_20_slope):
        anti_decline_raw += 100.0 * clamp01((recent_20_slope - min(older_20_slope, 0.0)) / max(abs(older_20_slope), 0.01)) * 0.50
    support_failure_penalty_raw = 0.0
    if support_line_end_price > 0:
        support_failure_penalty_raw = max(
            ((support_line_end_price - float(closes.iloc[-1])) / support_line_end_price) * 100.0,
            0.0,
        )
    staleness_penalty_raw = max(zero_if_nan(anchor_bars_from_now) - cfg.td_breakout_recent_bars, 0.0)
    severe_decline_penalty_raw = max(40.0 - anti_decline_raw, 0.0) * 0.35
    overshoot_penalty_raw = zero_if_nan(upper_line_metrics.get("upper_overshoot_penalty_raw"))
    result = _build_triangle_window_result(
        recent=recent,
        date_at=date_at,
        support_flat_ok=support_flat_ok,
        descending_highs_ok=descending_highs_ok,
        compression_ok=compression_ok,
        near_vertex_ok=near_vertex_ok,
        structure_ok=structure_ok,
        current_support_intact=current_support_intact,
        support_touch_count=support_touch_count,
        support_touch_span_bars=support_touch_span_bars,
        support_touch_age_bars=support_touch_age_bars,
        support_band_pct=support_band_pct,
        breakout_pct=breakout_pct,
        breakout_bar=breakout_bar,
        still_above_breakout=still_above_breakout,
        compression_ratio=compression_ratio,
        vertex_gap_pct=vertex_gap_pct,
        descending_drop_pct=descending_drop_pct,
        pivot_pair_found=pivot_pair_found,
        pivot_pair_score=pivot_pair_score,
        support_ref=support_ref,
        support_line_start_idx=support_line_start_idx,
        support_line_end_idx=support_line_end_idx,
        support_line_start_price=support_line_start_price,
        support_line_end_price=support_line_end_price,
        support_line_slope=support_line_slope,
        upper_slope_now=upper_slope_now,
        upper_line_now=upper_line_now,
        pivot_older_idx=pivot_older_idx,
        pivot_newer_idx=pivot_newer_idx,
        pivot_older_price=pivot_older_price,
        pivot_newer_price=pivot_newer_price,
        bars_to_vertex=bars_to_vertex,
        anchor_type=anchor_type,
        anchor_idx=anchor_idx,
        anchor_bars_from_now=anchor_bars_from_now,
        anchor_price_gap_pct=anchor_price_gap_pct,
        structure_score_raw=score_metrics["structure_score_raw"],
        breakout_score_raw=score_metrics["breakout_score_raw"],
    )
    result.update(
        {
            "structure_range_ratio": structure_range_ratio,
            "structure_start_height_abs": structure_start_height_abs,
            "structure_start_height_pct": structure_start_height_pct,
            "triangle_progress_pct": triangle_progress_pct,
            "upper_pivot_newer_bars_from_now": right_anchor_bars_from_now,
            "upper_overshoot_penalty_raw": overshoot_penalty_raw,
            "upper_significant_overshoot_count": int(zero_if_nan(upper_line_metrics.get("upper_significant_overshoot_count"))),
            "right_anchor_ma20_distance_pct": ma20_distance_pct,
            "right_anchor_ma50_distance_pct": ma50_distance_pct,
            "upper_pair_quality_raw": max(zero_if_nan(pivot_pair_score), 0.0),
            "horizontal_support_raw": horizontal_support_raw,
            "rising_support_raw": rising_support_raw,
            "ma_support_raw": ma_support_raw,
            "support_credibility_raw": support_credibility_raw,
            "descending_highs_raw": score_metrics["descending_score_raw"],
            "compression_raw": score_metrics["compression_score_raw"],
            "vertex_raw": score_metrics["vertex_score_raw"],
            "broad_structure_raw": broad_structure_raw,
            "breakout_recency_raw": breakout_recency_raw,
            "right_anchor_recency_raw": right_anchor_recency_raw,
            "triangle_maturity_raw": triangle_maturity_raw,
            "breakout_strength_raw": score_metrics["breakout_score_raw"],
            "ma_interaction_raw": ma_interaction_raw,
            "reversal_context_raw": reversal_context_raw,
            "anti_decline_raw": anti_decline_raw,
            "support_failure_penalty_raw": support_failure_penalty_raw,
            "staleness_penalty_raw": staleness_penalty_raw,
            "severe_decline_penalty_raw": severe_decline_penalty_raw,
            "overshoot_penalty_raw": overshoot_penalty_raw,
        }
    )
    if debug_profile is not None:
        _profile_add(debug_profile, "triangle_score", time.perf_counter() - score_started_at)
        _profile_add(debug_profile, "triangle_window_total", time.perf_counter() - window_started_at)
    return result


def _passes_triangle_shape_prescreen(
    work: pd.DataFrame,
    cfg: BreakoutConfig,
    debug_profile: dict[str, float] | None = None,
    stage: int = 0,
) -> dict[str, Any]:
    if len(work) < cfg.td_triangle_lookback_bars:
        return {
            "passed": False,
            "bypassed": False,
            "reason": "insufficient_history",
            "best_candidate_score": 0.0,
        }

    prescreen_started_at = time.perf_counter() if debug_profile is not None else 0.0
    if cfg.td_prescreen_trend_bypass and stage > 0:
        if debug_profile is not None:
            _profile_add(debug_profile, "triangle_prescreen", time.perf_counter() - prescreen_started_at)
        return {
            "passed": True,
            "bypassed": True,
            "reason": "trend_bypass",
            "best_candidate_score": 100.0,
        }

    highs = work["high"]
    lows = work["low"]
    closes = work["close"]
    lookback = min(len(work), max(cfg.td_triangle_lookback_bars + 20, 90))
    recent = work.tail(lookback).reset_index(drop=True)
    recent_highs = recent["high"]
    recent_lows = recent["low"]
    recent_closes = recent["close"]
    whole_range = float(recent_highs.max() - recent_lows.min())
    if not pd.notna(whole_range) or whole_range <= 0:
        if debug_profile is not None:
            _profile_add(debug_profile, "triangle_prescreen", time.perf_counter() - prescreen_started_at)
        return {
            "passed": False,
            "bypassed": False,
            "reason": "no_range",
            "best_candidate_score": 0.0,
        }

    pivot_info = find_significant_pivot_highs(recent_highs, recent_lows, cfg, recent.get("date"))
    candidate_records = pivot_info["significant_records"] if pivot_info["significant_records"] else pivot_info["records"]
    left_candidates = build_left_high_candidates(candidate_records, cfg)[: cfg.td_prescreen_max_left_candidates]
    if not left_candidates:
        if debug_profile is not None:
            _profile_add(debug_profile, "triangle_prescreen", time.perf_counter() - prescreen_started_at)
        return {
            "passed": False,
            "bypassed": False,
            "reason": "no_left_candidates",
            "best_candidate_score": 0.0,
        }

    best_candidate_score = 0.0
    for candidate in left_candidates:
        left_idx = int(candidate["idx"])
        if left_idx >= len(recent) - max(cfg.td_min_pivot_separation_bars, 12):
            continue
        segment_highs = recent_highs.iloc[left_idx:].reset_index(drop=True)
        segment_lows = recent_lows.iloc[left_idx:].reset_index(drop=True)
        segment_closes = recent_closes.iloc[left_idx:].reset_index(drop=True)
        seg_len = len(segment_highs)
        if seg_len < max(cfg.td_min_pivot_separation_bars + 4, 18):
            continue

        third = max(seg_len // 3, 4)
        early_slice = slice(0, third)
        late_slice = slice(seg_len - third, seg_len)

        early_range = float(segment_highs.iloc[early_slice].max() - segment_lows.iloc[early_slice].min())
        late_range = float(segment_highs.iloc[late_slice].max() - segment_lows.iloc[late_slice].min())
        if not (pd.notna(early_range) and pd.notna(late_range) and early_range > 0):
            continue

        compression_ratio = late_range / early_range

        left_high = float(segment_highs.iloc[0])
        late_high = float(segment_highs.iloc[late_slice].max())
        descending_ok = late_high <= left_high * 1.05

        recent_support_low = float(segment_lows.iloc[late_slice].min())
        if recent_support_low <= 0:
            continue
        support_band_threshold = recent_support_low * (cfg.td_prescreen_recent_support_band_pct / 100.0)
        support_cluster_count = int(
            np.nansum(np.abs(segment_lows.iloc[late_slice].to_numpy(dtype=float) - recent_support_low) <= support_band_threshold)
        )

        short_ma = segment_closes.rolling(8, min_periods=3).mean()
        short_ma_slope = float(short_ma.iloc[-1] - short_ma.iloc[max(len(short_ma) - 4, 0)]) if len(short_ma) >= 4 else 0.0
        ma_slope_ok = short_ma_slope >= -whole_range * 0.02

        compression_score = 100.0 * clamp01(
            (cfg.td_prescreen_min_compression_ratio - compression_ratio) / max(cfg.td_prescreen_min_compression_ratio, 0.01)
        )
        support_score = 100.0 * clamp01(
            support_cluster_count / max(cfg.td_prescreen_min_support_cluster_count + 1, 1)
        )
        descending_score = 100.0 if descending_ok else 0.0
        ma_score = 100.0 if ma_slope_ok else 0.0
        candidate_score = compression_score * 0.35 + support_score * 0.25 + descending_score * 0.25 + ma_score * 0.15
        best_candidate_score = max(best_candidate_score, float(candidate_score))

        if (
            support_cluster_count >= cfg.td_prescreen_min_support_cluster_count
            and descending_ok
            and ma_slope_ok
            and candidate_score >= cfg.td_prescreen_accept_score
        ):
            if debug_profile is not None:
                _profile_add(debug_profile, "triangle_prescreen", time.perf_counter() - prescreen_started_at)
            return {
                "passed": True,
                "bypassed": False,
                "reason": "score_pass",
                "best_candidate_score": float(candidate_score),
            }

        if (
            compression_ratio <= cfg.td_prescreen_min_compression_ratio
            and support_cluster_count >= cfg.td_prescreen_min_support_cluster_count
            and descending_ok
            and ma_slope_ok
        ):
            if debug_profile is not None:
                _profile_add(debug_profile, "triangle_prescreen", time.perf_counter() - prescreen_started_at)
            return {
                "passed": True,
                "bypassed": False,
                "reason": "hard_pass",
                "best_candidate_score": float(candidate_score),
            }

    if debug_profile is not None:
        _profile_add(debug_profile, "triangle_prescreen", time.perf_counter() - prescreen_started_at)
    return {
        "passed": False,
        "bypassed": False,
        "reason": "shape_reject",
        "best_candidate_score": float(best_candidate_score),
    }


def compute_triangle_metrics(
    df: pd.DataFrame,
    stage: int,
    cfg: BreakoutConfig,
    *,
    refresh_mode: bool = False,
    debug_profile: dict[str, float] | None = None,
) -> dict[str, Any]:
    triangle_started_at = time.perf_counter() if debug_profile is not None else 0.0
    work = df.tail(max(cfg.td_triangle_lookback_bars + cfg.td_forming_invalidation_lookback_bars + 20, 120)).copy()
    if len(work) < cfg.td_triangle_lookback_bars:
        return {
            "TD Triangle": 0,
            "TD Triangle Score": 0.0,
            "TD Triangle Forming": 0,
            "TD Triangle Forming Score": 0.0,
            "Non Breaking Triangle": 0,
            "Near Miss Triangle": 0,
            "Open Weak Triangle": 0,
            "Shallow Weak Triangle": 0,
            "TD Prescreen Passed": 0,
            "TD Prescreen Bypassed": 0,
            "TD Prescreen Reason": "insufficient_history",
            "TD Prescreen Best Score": 0.0,
            "TD Triangle Rejection Stage": "insufficient_history",
            **_triangle_raw_metric_defaults(),
        }

    prescreen_result = {
        "passed": True,
        "bypassed": False,
        "reason": "disabled",
        "best_candidate_score": 100.0,
    }
    if cfg.td_enable_shape_prescreen:
        prescreen_result = _passes_triangle_shape_prescreen(
            work,
            cfg,
            debug_profile=debug_profile,
            stage=stage,
        )
    if not bool(prescreen_result.get("passed", False)):
        return {
            "TD Triangle": 0,
            "TD Triangle Score": 0.0,
            "TD Triangle Forming": 0,
            "TD Triangle Forming Score": 0.0,
            "Non Breaking Triangle": 0,
            "Near Miss Triangle": 0,
            "Open Weak Triangle": 0,
            "Shallow Weak Triangle": 0,
            "TD Prescreen Passed": 0,
            "TD Prescreen Bypassed": int(bool(prescreen_result.get("bypassed", False))),
            "TD Prescreen Reason": str(prescreen_result.get("reason", "shape_reject")),
            "TD Prescreen Best Score": round(float(prescreen_result.get("best_candidate_score", 0.0)), 2),
            "TD Triangle Rejection Stage": "prescreen",
            **_triangle_raw_metric_defaults(),
        }

    window_metrics: list[dict[str, Any]] = []
    metric_index: list[pd.Timestamp | int] = []
    loop_started_at = time.perf_counter() if debug_profile is not None else 0.0
    first_end_idx = cfg.td_triangle_lookback_bars - 1
    if refresh_mode:
        recent_window_count = max(
            int(cfg.td_forming_invalidation_lookback_bars),
            int(cfg.td_max_triangle_age_bars),
            int(cfg.td_breakout_recent_bars),
            int(cfg.td_structure_recent_bars),
        ) + 1
        first_end_idx = max(first_end_idx, len(work) - recent_window_count)
    for end_idx in range(first_end_idx, len(work)):
        recent = work.iloc[end_idx - cfg.td_triangle_lookback_bars + 1 : end_idx + 1].copy()
        window_metrics.append(_triangle_window_metrics(recent, cfg, debug_profile=debug_profile))
        metric_index.append(work.index[end_idx])
    if debug_profile is not None:
        _profile_add(debug_profile, "triangle_window_loop", time.perf_counter() - loop_started_at)
        _profile_add(debug_profile, "triangle_window_count", float(len(window_metrics)))

    post_started_at = time.perf_counter() if debug_profile is not None else 0.0
    metrics_df = pd.DataFrame(window_metrics, index=metric_index)
    structure_ok_series = metrics_df["structure_ok"].astype(bool)
    breakout_bar_series = metrics_df["breakout_bar"].astype(bool)
    structure_bars_since_series = barssince(structure_ok_series)
    breakout_bars_since_series = barssince(breakout_bar_series)

    metrics_df["structure_bars_since"] = structure_bars_since_series
    metrics_df["breakout_bars_since"] = breakout_bars_since_series
    metrics_df["structure_recent_ok"] = pd.Series(
        structure_bars_since_series.notna().to_numpy()
        & (structure_bars_since_series.to_numpy() <= cfg.td_structure_recent_bars),
        index=metrics_df.index,
    ).astype(int)
    metrics_df["structure_fresh_ok"] = pd.Series(
        structure_bars_since_series.notna().to_numpy()
        & (structure_bars_since_series.to_numpy() <= cfg.td_max_triangle_age_bars),
        index=metrics_df.index,
    ).astype(int)
    metrics_df["latched_structure_support_ok"] = pd.Series(
        structure_bars_since_series.notna().to_numpy()
        & (
            (structure_bars_since_series == 0).to_numpy()
            | metrics_df["current_support_intact"].astype(bool).to_numpy()
        ),
        index=metrics_df.index,
    ).astype(int)
    metrics_df["breakout_recent_ok"] = pd.Series(
        breakout_bars_since_series.notna().to_numpy()
        & (breakout_bars_since_series.to_numpy() <= cfg.td_breakout_recent_bars),
        index=metrics_df.index,
    ).astype(int)

    forming_max_distance_below_resistance_pct = max(cfg.td_breakout_buffer_pct * 3.0, 3.0)
    metrics_df["near_resistance_for_forming"] = pd.Series(
        metrics_df["breakout_pct"].notna().to_numpy()
        & (metrics_df["breakout_pct"].to_numpy() >= -forming_max_distance_below_resistance_pct)
        & (metrics_df["breakout_pct"].to_numpy() < cfg.td_breakout_buffer_pct),
        index=metrics_df.index,
    ).astype(int)

    forming_invalidation_breakout_pct = max(cfg.td_breakout_buffer_pct * 2.0, 2.0)
    metrics_df["recent_max_breakout_pct"] = metrics_df["breakout_pct"].rolling(
        cfg.td_forming_invalidation_lookback_bars, min_periods=1
    ).max()
    metrics_df["no_recent_resolved_breakout_for_forming"] = pd.Series(
        metrics_df["recent_max_breakout_pct"].notna().to_numpy()
        & (metrics_df["recent_max_breakout_pct"].to_numpy() < forming_invalidation_breakout_pct),
        index=metrics_df.index,
    ).astype(int)

    metrics_df["td_triangle_forming"] = pd.Series(
        metrics_df["structure_ok"].astype(bool).to_numpy()
        & metrics_df["structure_fresh_ok"].astype(bool).to_numpy()
        & metrics_df["near_resistance_for_forming"].astype(bool).to_numpy()
        & metrics_df["no_recent_resolved_breakout_for_forming"].astype(bool).to_numpy()
        & ~metrics_df["still_above_breakout"].astype(bool).to_numpy(),
        index=metrics_df.index,
    ).astype(int)
    metrics_df["td_triangle_raw"] = pd.Series(
        metrics_df["structure_recent_ok"].astype(bool).to_numpy()
        & metrics_df["structure_fresh_ok"].astype(bool).to_numpy()
        & metrics_df["latched_structure_support_ok"].astype(bool).to_numpy()
        & metrics_df["breakout_recent_ok"].astype(bool).to_numpy(),
        index=metrics_df.index,
    ).astype(int)
    metrics_df["td_triangle"] = metrics_df["td_triangle_raw"].astype(int)
    metrics_df.loc[metrics_df["td_triangle"].astype(bool), "td_triangle_forming"] = 0
    metrics_df["td_triangle_forming_score"] = np.where(
        metrics_df["td_triangle_forming"].astype(bool),
        metrics_df["structure_score_raw"],
        0.0,
    )
    metrics_df["td_triangle_score"] = np.where(
        metrics_df["td_triangle"].astype(bool),
        metrics_df["structure_score_raw"] * 0.70 + metrics_df["breakout_score_raw"] * 0.30,
        0.0,
    )
    if debug_profile is not None:
        _profile_add(debug_profile, "triangle_post", time.perf_counter() - post_started_at)
        _profile_add(debug_profile, "triangle_total", time.perf_counter() - triangle_started_at)

    latest = metrics_df.iloc[-1]
    selected = latest

    def _select_recent_drawable_candidate(candidates_df: pd.DataFrame) -> pd.Series | None:
        if candidates_df.empty:
            return None
        drawable_candidates = candidates_df[candidates_df["pivot_pair_found"].astype(bool)]
        if not drawable_candidates.empty:
            return drawable_candidates.iloc[-1]
        return candidates_df.iloc[-1]

    if int(latest["td_triangle"]) == 1:
        triangle_candidates = metrics_df[metrics_df["td_triangle"].astype(bool)]
        drawable_selected = _select_recent_drawable_candidate(triangle_candidates)
        if drawable_selected is not None:
            selected = drawable_selected
    elif int(latest["td_triangle_forming"]) == 1:
        forming_candidates = metrics_df[metrics_df["td_triangle_forming"].astype(bool)]
        drawable_selected = _select_recent_drawable_candidate(forming_candidates)
        if drawable_selected is not None:
            selected = drawable_selected

    rejection_stage = "active"
    if int(latest["td_triangle"]) == 1:
        rejection_stage = "triangle_active"
    elif int(latest["td_triangle_forming"]) == 1:
        rejection_stage = "forming_active"
    elif not bool(latest["pivot_pair_found"]):
        rejection_stage = "upper_pair"
    elif not bool(latest["support_flat_ok"]):
        rejection_stage = "support"
    elif not bool(latest["structure_ok"]):
        rejection_stage = "structure"
    elif not bool(latest["structure_recent_ok"]):
        rejection_stage = "structure_recent"
    elif not bool(latest["latched_structure_support_ok"]):
        rejection_stage = "latched_support"
    elif not bool(latest["breakout_recent_ok"]):
        rejection_stage = "breakout_recent"
    else:
        rejection_stage = "final"

    non_breaking_triangle = int(
        int(latest["td_triangle"]) == 0
        and int(latest["structure_ok"]) == 1
        and int(latest["structure_fresh_ok"]) == 1
        and int(latest["near_resistance_for_forming"]) == 1
        and int(latest["no_recent_resolved_breakout_for_forming"]) == 1
        and int(latest["still_above_breakout"]) == 0
        and int(latest["near_vertex_ok"]) == 1
        and pd.notna(latest["triangle_progress_pct"])
        and float(latest["triangle_progress_pct"]) >= max(cfg.td_resolved_min_triangle_progress_pct, 75.0)
        and pd.notna(latest["bars_to_vertex"])
        and float(latest["bars_to_vertex"]) >= 0.0
        and float(latest["bars_to_vertex"]) <= max(float(cfg.td_max_bars_to_vertex), 8.0)
        and zero_if_nan(latest["breakout_pct"]) < cfg.td_breakout_buffer_pct
    )
    if non_breaking_triangle:
        latest = latest.copy()
        selected = selected.copy()
        latest["td_triangle_forming"] = 0
        selected["td_triangle_forming_score"] = 0.0

    open_weak_triangle = bool(
        int(selected["pivot_pair_found"]) == 1
        and int(selected["support_flat_ok"]) == 1
        and int(selected["compression_ok"]) == 1
        and int(selected["near_vertex_ok"]) == 0
        and (
            (
                int(selected["descending_highs_ok"]) == 1
                and pd.notna(selected["bars_to_vertex"])
                and float(selected["bars_to_vertex"]) > 35.0
                and (
                    (
                        pd.notna(selected["structure_start_height_pct"])
                        and float(selected["structure_start_height_pct"]) < 25.0
                    )
                    or (
                        pd.notna(selected["compression_ratio"])
                        and float(selected["compression_ratio"]) > 0.30
                    )
                )
            )
            or (
                pd.notna(selected["bars_to_vertex"])
                and float(selected["bars_to_vertex"]) > 60.0
                and pd.notna(selected["structure_start_height_abs"])
                and float(selected["structure_start_height_abs"]) <= 2.0
            )
            or (
                pd.notna(selected["bars_to_vertex"])
                and float(selected["bars_to_vertex"]) > 25.0
                and pd.notna(selected["vertex_gap_pct"])
                and float(selected["vertex_gap_pct"]) > 15.0
                and pd.notna(selected["breakout_pct"])
                and float(selected["breakout_pct"]) < -10.0
            )
        )
    )
    shallow_weak_triangle = bool(
        int(selected["pivot_pair_found"]) == 1
        and int(selected["support_flat_ok"]) == 1
        and int(selected["compression_ok"]) == 1
        and int(selected["near_vertex_ok"]) == 1
        and (
            int(selected["descending_highs_ok"]) == 0
            or (
                pd.notna(selected["pivot_pair_score"])
                and float(selected["pivot_pair_score"]) < 60.0
                and pd.notna(selected["breakout_pct"])
                and float(selected["breakout_pct"]) < 0.5
            )
        )
        and pd.notna(selected["descending_drop_pct"])
        and float(selected["descending_drop_pct"]) > -cfg.td_descending_min_drop_pct
        and pd.notna(selected["structure_start_height_abs"])
        and float(selected["structure_start_height_abs"]) <= cfg.td_weak_shallow_max_height_abs
        and pd.notna(selected["vertex_gap_pct"])
        and float(selected["vertex_gap_pct"]) <= cfg.td_max_vertex_gap_pct
    )
    near_miss_triangle = bool(
        int(selected["pivot_pair_found"]) == 1
        and pd.notna(selected["support_line_start_date"])
        and pd.notna(selected["support_line_end_date"])
        and int(latest["td_triangle"]) == 0
        and int(latest["td_triangle_forming"]) == 0
        and int(non_breaking_triangle) == 0
        and not open_weak_triangle
        and not shallow_weak_triangle
        and int(selected["descending_highs_ok"]) == 1
        and int(selected["compression_ok"]) == 1
        and (
            (
                pd.notna(selected["pivot_pair_score"])
                and float(selected["pivot_pair_score"]) >= 60.0
            )
            or (
                pd.notna(selected["breakout_pct"])
                and float(selected["breakout_pct"]) >= 1.0
                and pd.notna(selected["structure_start_height_abs"])
                and float(selected["structure_start_height_abs"]) >= 2.5
            )
            or (
                pd.notna(selected["breakout_pct"])
                and float(selected["breakout_pct"]) > 0.0
                and pd.notna(selected["structure_start_height_abs"])
                and float(selected["structure_start_height_abs"]) >= 20.0
            )
        )
        and (
            (
                pd.notna(selected["breakout_pct"])
                and float(selected["breakout_pct"]) > 0.0
            )
            or (
                pd.notna(selected["bars_to_vertex"])
                and float(selected["bars_to_vertex"]) <= 25.0
            )
            or (
                pd.notna(selected["right_anchor_recency_raw"])
                and float(selected["right_anchor_recency_raw"]) >= 60.0
            )
            or int(selected["near_vertex_ok"]) == 1
        )
        and (
            int(selected["near_vertex_ok"]) == 0
            or int(latest["structure_recent_ok"]) == 0
            or int(latest["breakout_recent_ok"]) == 0
            or str(selected["anchor_type"]) == "none"
        )
    )
    if open_weak_triangle:
        latest = latest.copy()
        selected = selected.copy()
        latest["td_triangle"] = 0
        latest["td_triangle_forming"] = 0
        selected["td_triangle_score"] = 0.0
        selected["td_triangle_forming_score"] = 0.0
        if rejection_stage == "triangle_active":
            rejection_stage = "open_weak_excluded"
    if shallow_weak_triangle:
        latest = latest.copy()
        selected = selected.copy()
        latest["td_triangle"] = 0
        latest["td_triangle_forming"] = 0
        selected["td_triangle_score"] = 0.0
        selected["td_triangle_forming_score"] = 0.0
        if rejection_stage == "triangle_active":
            rejection_stage = "shallow_weak_excluded"
        elif rejection_stage == "forming_active":
            rejection_stage = "shallow_weak_excluded"
    composite_components = _compute_triangle_composite_components(selected)

    return {
        "TD Triangle": int(latest["td_triangle"]),
        "TD Triangle Score": round(float(selected["td_triangle_score"]), 2),
        "TD Triangle Forming": int(latest["td_triangle_forming"]),
        "TD Triangle Forming Score": round(float(selected["td_triangle_forming_score"]), 2),
        "Non Breaking Triangle": non_breaking_triangle,
        "Near Miss Triangle": int(near_miss_triangle),
        "Open Weak Triangle": int(open_weak_triangle),
        "Shallow Weak Triangle": int(shallow_weak_triangle),
        "TD Prescreen Passed": int(bool(prescreen_result.get("passed", False))),
        "TD Prescreen Bypassed": int(bool(prescreen_result.get("bypassed", False))),
        "TD Prescreen Reason": str(prescreen_result.get("reason", "disabled")),
        "TD Prescreen Best Score": round(float(prescreen_result.get("best_candidate_score", 0.0)), 2),
        "TD Triangle Rejection Stage": rejection_stage,
        "TD Support Flat OK": int(selected["support_flat_ok"]),
        "TD Descending Highs OK": int(selected["descending_highs_ok"]),
        "TD Compression OK": int(selected["compression_ok"]),
        "TD Near Vertex OK": int(selected["near_vertex_ok"]),
        "TD Structure OK": int(selected["structure_ok"]),
        "TD Structure Recent OK": int(latest["structure_recent_ok"]),
        "TD Breakout Recent OK": int(latest["breakout_recent_ok"]),
        "TD Latched Support OK": int(latest["latched_structure_support_ok"]),
        "TD Breakout %": round(float(selected["breakout_pct"]), 4) if pd.notna(selected["breakout_pct"]) else np.nan,
        "TD Compression Ratio": round(float(selected["compression_ratio"]), 4) if pd.notna(selected["compression_ratio"]) else np.nan,
        "TD Vertex Gap %": round(float(selected["vertex_gap_pct"]), 4) if pd.notna(selected["vertex_gap_pct"]) else np.nan,
        "TD Descending Drop %": round(float(selected["descending_drop_pct"]), 4) if pd.notna(selected["descending_drop_pct"]) else np.nan,
        "TD Support Touch Count": int(selected["support_touch_count"]),
        "TD Support Touch Span Bars": int(selected["support_touch_span_bars"]),
        "TD Support Touch Age Bars": int(selected["support_touch_age_bars"]),
        "TD Upper Pivot Pair Found": int(selected["pivot_pair_found"]),
        "TD Upper Pivot Pair Score": round(float(selected["pivot_pair_score"]), 2) if pd.notna(selected["pivot_pair_score"]) else np.nan,
        "TD Triangle Window Bars": int(selected["triangle_window_bars"]) if pd.notna(selected["triangle_window_bars"]) else 0,
        "TD Triangle Window Start Date": selected["triangle_window_start_date"],
        "TD Triangle Window End Date": selected["triangle_window_end_date"],
        "TD Support Price": round(float(selected["support_ref"]), 4) if pd.notna(selected["support_ref"]) else np.nan,
        "TD Support Line Start Index": int(selected["support_line_start_idx"]) if pd.notna(selected["support_line_start_idx"]) else np.nan,
        "TD Support Line End Index": int(selected["support_line_end_idx"]) if pd.notna(selected["support_line_end_idx"]) else np.nan,
        "TD Support Line Start Date": selected["support_line_start_date"],
        "TD Support Line End Date": selected["support_line_end_date"],
        "TD Support Line Start Price": round(float(selected["support_line_start_price"]), 4) if pd.notna(selected["support_line_start_price"]) else np.nan,
        "TD Support Line End Price": round(float(selected["support_line_end_price"]), 4) if pd.notna(selected["support_line_end_price"]) else np.nan,
        "TD Support Line Slope": round(float(selected["support_line_slope"]), 6) if pd.notna(selected["support_line_slope"]) else np.nan,
        "TD Upper Line Slope": round(float(selected["upper_line_slope"]), 6) if pd.notna(selected["upper_line_slope"]) else np.nan,
        "TD Upper Line Price": round(float(selected["upper_line_now"]), 4) if pd.notna(selected["upper_line_now"]) else np.nan,
        "TD Upper Line End Index": int(selected["upper_line_end_idx"]) if pd.notna(selected["upper_line_end_idx"]) else np.nan,
        "TD Upper Line End Date": selected["upper_line_end_date"],
        "TD Upper Pivot Older Index": int(selected["pivot_older_idx"]) if pd.notna(selected["pivot_older_idx"]) else np.nan,
        "TD Upper Pivot Newer Index": int(selected["pivot_newer_idx"]) if pd.notna(selected["pivot_newer_idx"]) else np.nan,
        "TD Upper Pivot Older Date": selected["pivot_older_date"],
        "TD Upper Pivot Newer Date": selected["pivot_newer_date"],
        "TD Upper Pivot Older Price": round(float(selected["pivot_older_price"]), 4) if pd.notna(selected["pivot_older_price"]) else np.nan,
        "TD Upper Pivot Newer Price": round(float(selected["pivot_newer_price"]), 4) if pd.notna(selected["pivot_newer_price"]) else np.nan,
        "TD Bars To Vertex": round(float(selected["bars_to_vertex"]), 4) if pd.notna(selected["bars_to_vertex"]) else np.nan,
        "TD Vertex Date": selected.get("vertex_date"),
        "TD Breakout Date": selected.get("breakout_date"),
        "TD Bars Since Breakout": round(float(selected["bars_since_breakout"]), 4) if pd.notna(selected.get("bars_since_breakout")) else np.nan,
        "TD Anchor Type": selected["anchor_type"],
        "TD Anchor Index": int(selected["anchor_idx"]) if pd.notna(selected["anchor_idx"]) else np.nan,
        "TD Anchor Date": selected["anchor_date"],
        "TD Anchor Bars From Now": round(float(selected["anchor_bars_from_now"]), 4) if pd.notna(selected["anchor_bars_from_now"]) else np.nan,
        "TD Anchor Price Gap %": round(float(selected["anchor_price_gap_pct"]), 4) if pd.notna(selected["anchor_price_gap_pct"]) else np.nan,
        "TD Support Band %": round(float(selected["support_band_pct"]), 4) if pd.notna(selected["support_band_pct"]) else np.nan,
        "TD Structure Range Ratio": round(float(selected["structure_range_ratio"]), 4) if pd.notna(selected["structure_range_ratio"]) else np.nan,
        "TD Structure Start Height $": round(float(selected["structure_start_height_abs"]), 4) if pd.notna(selected["structure_start_height_abs"]) else np.nan,
        "TD Structure Start Height %": round(float(selected["structure_start_height_pct"]), 4) if pd.notna(selected["structure_start_height_pct"]) else np.nan,
        "TD Triangle Progress %": round(float(selected["triangle_progress_pct"]), 4) if pd.notna(selected["triangle_progress_pct"]) else np.nan,
        "TD Upper Pivot Newer Bars From Now": round(float(selected["upper_pivot_newer_bars_from_now"]), 4) if pd.notna(selected["upper_pivot_newer_bars_from_now"]) else np.nan,
        "TD Upper Overshoot Penalty Raw": round(float(selected["upper_overshoot_penalty_raw"]), 4) if pd.notna(selected["upper_overshoot_penalty_raw"]) else 0.0,
        "TD Upper Significant Overshoot Count": int(selected["upper_significant_overshoot_count"]) if pd.notna(selected["upper_significant_overshoot_count"]) else 0,
        "TD Right Anchor MA20 Distance %": round(float(selected["right_anchor_ma20_distance_pct"]), 4) if pd.notna(selected["right_anchor_ma20_distance_pct"]) else np.nan,
        "TD Right Anchor MA50 Distance %": round(float(selected["right_anchor_ma50_distance_pct"]), 4) if pd.notna(selected["right_anchor_ma50_distance_pct"]) else np.nan,
        "TD Upper Pair Quality Raw": round(float(selected["upper_pair_quality_raw"]), 4) if pd.notna(selected["upper_pair_quality_raw"]) else 0.0,
        "TD Support Credibility Raw": round(float(selected["support_credibility_raw"]), 4) if pd.notna(selected["support_credibility_raw"]) else 0.0,
        "TD Horizontal Support Raw": round(float(selected["horizontal_support_raw"]), 4) if pd.notna(selected["horizontal_support_raw"]) else 0.0,
        "TD Rising Support Raw": round(float(selected["rising_support_raw"]), 4) if pd.notna(selected["rising_support_raw"]) else 0.0,
        "TD MA Support Raw": round(float(selected["ma_support_raw"]), 4) if pd.notna(selected["ma_support_raw"]) else 0.0,
        "TD Descending Highs Raw": round(float(selected["descending_highs_raw"]), 4) if pd.notna(selected["descending_highs_raw"]) else 0.0,
        "TD Compression Raw": round(float(selected["compression_raw"]), 4) if pd.notna(selected["compression_raw"]) else 0.0,
        "TD Vertex Raw": round(float(selected["vertex_raw"]), 4) if pd.notna(selected["vertex_raw"]) else 0.0,
        "TD Broad Structure Raw": round(float(selected["broad_structure_raw"]), 4) if pd.notna(selected["broad_structure_raw"]) else 0.0,
        "TD Breakout Recency Raw": round(float(selected["breakout_recency_raw"]), 4) if pd.notna(selected["breakout_recency_raw"]) else 0.0,
        "TD Right Anchor Recency Raw": round(float(selected["right_anchor_recency_raw"]), 4) if pd.notna(selected["right_anchor_recency_raw"]) else 0.0,
        "TD Triangle Maturity Raw": round(float(selected["triangle_maturity_raw"]), 4) if pd.notna(selected["triangle_maturity_raw"]) else 0.0,
        "TD Breakout Strength Raw": round(float(selected["breakout_strength_raw"]), 4) if pd.notna(selected["breakout_strength_raw"]) else 0.0,
        "TD MA Interaction Raw": round(float(selected["ma_interaction_raw"]), 4) if pd.notna(selected["ma_interaction_raw"]) else 0.0,
        "TD Reversal Context Raw": round(float(selected["reversal_context_raw"]), 4) if pd.notna(selected["reversal_context_raw"]) else 0.0,
        "TD Anti Decline Raw": round(float(selected["anti_decline_raw"]), 4) if pd.notna(selected["anti_decline_raw"]) else 0.0,
        "TD Support Failure Penalty Raw": round(float(selected["support_failure_penalty_raw"]), 4) if pd.notna(selected["support_failure_penalty_raw"]) else 0.0,
        "TD Staleness Penalty Raw": round(float(selected["staleness_penalty_raw"]), 4) if pd.notna(selected["staleness_penalty_raw"]) else 0.0,
        "TD Severe Decline Penalty Raw": round(float(selected["severe_decline_penalty_raw"]), 4) if pd.notna(selected["severe_decline_penalty_raw"]) else 0.0,
        "TD Overshoot Penalty Raw": round(float(selected["overshoot_penalty_raw"]), 4) if pd.notna(selected["overshoot_penalty_raw"]) else 0.0,
        "Geometry Weighted": round(float(composite_components["geometry_weighted"]), 4),
        "Timeliness Weighted": round(float(composite_components["timeliness_weighted"]), 4),
        "Context Weighted": round(float(composite_components["context_weighted"]), 4),
        "Penalty Weighted": round(float(composite_components["penalty_weighted"]), 4),
        "Triangle Composite Score": round(float(composite_components["triangle_composite_score"]), 4),
    }


def compute_breakout_snapshot(
    history_df: pd.DataFrame,
    *,
    symbol: str,
    cfg: BreakoutConfig | None = None,
    refresh_mode: bool = False,
    benchmark_histories: dict[str, pd.DataFrame] | None = None,
) -> dict[str, Any]:
    cfg = cfg or BreakoutConfig()
    debug_profile: dict[str, float] | None = {} if BREAKOUT_COMPUTE_DEBUG else None
    snapshot_started_at = time.perf_counter() if debug_profile is not None else 0.0
    if history_df.empty:
        return {"Symbol": symbol, "Error": "No history"}

    df = history_df.copy()
    df.columns = [str(col).lower() for col in df.columns]
    df = df.loc[:, ~pd.Index(df.columns).duplicated()].copy()
    df = df.sort_values("date").reset_index(drop=True)

    required_columns = {"date", "open", "high", "low", "close", "volume"}
    if not required_columns.issubset(df.columns):
        return {"Symbol": symbol, "Error": "Missing required OHLCV columns"}

    indicator_started_at = time.perf_counter() if debug_profile is not None else 0.0
    df["ema_fast"] = ema(df["close"], cfg.fast_ema_len)
    df["ema_slow"] = ema(df["close"], cfg.slow_ema_len)
    df["ema_slope_pct"] = roc(df["ema_fast"], cfg.ema_slope_len)
    df["avg_dollar_vol"] = (df["close"] * df["volume"]).rolling(cfg.dollar_vol_len).mean()
    df["short_vol_avg"] = df["volume"].rolling(cfg.short_vol_len).mean()
    df["long_vol_avg"] = df["volume"].rolling(cfg.long_vol_len).mean()
    df["vol_trend_pct"] = ((df["short_vol_avg"] / df["long_vol_avg"]) - 1.0) * 100.0
    df["rel_vol_base"] = df["volume"].rolling(cfg.rel_vol_len).mean()
    df["rel_vol"] = df["volume"] / df["rel_vol_base"]
    df["atr_short"] = atr(df, cfg.atr_short_len)
    df["atr_long"] = atr(df, cfg.atr_long_len)
    df["atr_expansion"] = df["atr_short"] / df["atr_long"]
    df["roc_short"] = roc(df["close"], 3)
    df["roc_medium"] = roc(df["close"], 10)
    df["accel_spread"] = df["roc_short"] - df["roc_medium"]
    df["stretch_over_fast_pct"] = ((df["close"] / df["ema_fast"]) - 1.0) * 100.0
    df["avg_share_vol_qualified"] = df["volume"].rolling(cfg.avg_share_vol_len_qualified).mean()
    if debug_profile is not None:
        _profile_add(debug_profile, "snapshot_indicators", time.perf_counter() - indicator_started_at)

    outlier_started_at = time.perf_counter() if debug_profile is not None else 0.0
    trend_outlier_metrics = compute_trend_outlier_metrics(df, benchmark_histories, cfg)
    if debug_profile is not None:
        _profile_add(debug_profile, "snapshot_trend_outlier", time.perf_counter() - outlier_started_at)

    quality_started_at = time.perf_counter() if debug_profile is not None else 0.0
    row = df.iloc[-1]
    trend_aligned = bool(row["close"] > row["ema_fast"] and row["ema_fast"] > row["ema_slow"])
    ema_slope_up = bool(pd.notna(row["ema_slope_pct"]) and row["ema_slope_pct"] > 0)
    liquidity_ok = bool(pd.notna(row["avg_dollar_vol"]) and row["avg_dollar_vol"] >= cfg.min_avg_dollar_vol)
    price_qualified_ok = bool(row["close"] >= cfg.min_qualified_price)
    share_vol_qualified_ok = bool(
        pd.notna(row["avg_share_vol_qualified"]) and row["avg_share_vol_qualified"] >= cfg.min_avg_share_vol_qualified
    )
    history_qualified_ok = len(df) >= cfg.required_history_bars_qualified
    atr_pct_qualified = (row["atr_short"] / row["close"]) * 100.0 if pd.notna(row["atr_short"]) and row["close"] > 0 else np.nan
    atr_pct_qualified_ok = (
        (not cfg.use_atr_pct_ceiling_qualified)
        or (pd.notna(atr_pct_qualified) and atr_pct_qualified <= cfg.max_atr_pct_qualified)
    )

    recent_high = float(df["high"].tail(cfg.damage_lookback_bars).max())
    drawdown_pct = ((recent_high - row["close"]) / recent_high) * 100.0 if recent_high > 0 else np.nan
    damage_ok = bool(pd.notna(drawdown_pct) and drawdown_pct <= cfg.max_recent_drawdown_pct)

    smooth_window = df["close"].tail(cfg.smooth_lookback_bars + 1).reset_index(drop=True)
    if len(smooth_window) >= cfg.smooth_lookback_bars + 1:
        net_move = abs(float(smooth_window.iloc[-1] - smooth_window.iloc[0]))
        total_move = float(smooth_window.diff().abs().sum())
        smoothness_ratio = net_move / total_move if total_move > 0 else 0.0
    else:
        smoothness_ratio = np.nan
    smoothness_ok = bool(pd.notna(smoothness_ratio) and smoothness_ratio >= cfg.min_smoothness)

    ema_deviation_pct = abs(float(row["close"] - row["ema_fast"])) / float(row["ema_fast"]) * 100.0 if pd.notna(row["ema_fast"]) and row["ema_fast"] > 0 else np.nan
    ema_stability_ok = bool(pd.notna(ema_deviation_pct) and ema_deviation_pct <= 50.0)
    structure_ok = max_consecutive_up_bars(df["close"], EARLY["lookback_bars"]) >= cfg.min_consecutive_up_bars
    trend_quality_ok = damage_ok and smoothness_ok and ema_stability_ok and structure_ok
    universe_quality_ok = liquidity_ok and price_qualified_ok and share_vol_qualified_ok and history_qualified_ok and atr_pct_qualified_ok
    if debug_profile is not None:
        _profile_add(debug_profile, "snapshot_quality", time.perf_counter() - quality_started_at)

    trend_started_at = time.perf_counter() if debug_profile is not None else 0.0
    def stage_metrics(stage_cfg: dict[str, float]) -> dict[str, float]:
        lookback = int(stage_cfg["lookback_bars"])
        if len(df) < lookback:
            return {
                "run_gain_pct": np.nan,
                "off_high_pct": np.nan,
                "up_bar_pct": np.nan,
            }
        start_close = float(df["close"].iloc[-lookback])
        run_gain_pct = ((row["close"] / start_close) - 1.0) * 100.0 if start_close > 0 else np.nan
        window_high = float(df["high"].tail(lookback).max())
        off_high_pct = ((window_high - row["close"]) / window_high) * 100.0 if window_high > 0 else np.nan
        return {
            "run_gain_pct": run_gain_pct,
            "off_high_pct": off_high_pct,
            "up_bar_pct": up_bar_pct(df["close"], lookback),
        }

    def sustained_metrics_for_window(lookback: int) -> dict[str, float]:
        if len(df) < lookback:
            return {
                "run_gain_pct": np.nan,
                "off_high_pct": np.nan,
                "up_bar_pct": np.nan,
                "smoothness": np.nan,
                "max_drawdown_pct": np.nan,
            }
        window = df.tail(lookback).reset_index(drop=True)
        start_close = float(window["close"].iloc[0])
        end_close = float(window["close"].iloc[-1])
        run_gain_pct = ((end_close / start_close) - 1.0) * 100.0 if start_close > 0 else np.nan
        window_high = float(window["high"].max())
        off_high_pct = ((window_high - end_close) / window_high) * 100.0 if window_high > 0 else np.nan
        net_move = max(end_close - start_close, 0.0)
        total_move = float(window["close"].diff().abs().sum())
        sustained_smoothness = net_move / total_move if total_move > 0 else 0.0
        running_high = window["close"].cummax()
        drawdowns = ((running_high - window["close"]) / running_high.replace(0, np.nan)) * 100.0
        max_drawdown_pct = float(drawdowns.max()) if not drawdowns.dropna().empty else np.nan
        return {
            "run_gain_pct": run_gain_pct,
            "off_high_pct": off_high_pct,
            "up_bar_pct": up_bar_pct(window["close"], lookback),
            "smoothness": sustained_smoothness,
            "max_drawdown_pct": max_drawdown_pct,
        }

    def sustained_metrics() -> dict[str, float]:
        return sustained_metrics_for_window(int(SUSTAINED["lookback_bars"]))

    def sustained_window_qualifies(metrics: dict[str, float], min_smoothness: float | None = None) -> bool:
        smoothness_floor = SUSTAINED["min_smoothness"] if min_smoothness is None else min_smoothness
        return bool(
            pd.notna(metrics["run_gain_pct"])
            and metrics["run_gain_pct"] >= SUSTAINED["min_gain_pct"]
            and pd.notna(metrics["up_bar_pct"])
            and metrics["up_bar_pct"] >= SUSTAINED["min_up_bar_pct"]
            and pd.notna(metrics["off_high_pct"])
            and metrics["off_high_pct"] <= SUSTAINED["near_high_pct"]
            and pd.notna(metrics["smoothness"])
            and metrics["smoothness"] >= smoothness_floor
            and pd.notna(metrics["max_drawdown_pct"])
            and metrics["max_drawdown_pct"] <= SUSTAINED["max_drawdown_pct"]
        )

    def sustained_duration_bonus() -> tuple[float, int, float]:
        candidate_windows = [window for window in SUSTAINED_LONG_WINDOWS if len(df) >= window]
        if int(SUSTAINED["lookback_bars"]) < len(df) < max(SUSTAINED_LONG_WINDOWS):
            candidate_windows.append(len(df))
        candidate_windows = sorted({window for window in candidate_windows if window > int(SUSTAINED["lookback_bars"])})
        best_window = 0
        best_bonus = 0.0
        best_months = 0.0
        for window in candidate_windows:
            metrics = sustained_metrics_for_window(window)
            if not sustained_window_qualifies(metrics, min_smoothness=SUSTAINED["long_min_smoothness"]):
                continue
            months = float(window) / 21.0
            if window >= 252:
                bonus = 70.0
            elif window >= 189:
                bonus = 48.0
            elif window >= 126:
                bonus = 28.0
            else:
                bonus = max(10.0, months * 4.0)
            if bonus > best_bonus:
                best_window = int(window)
                best_bonus = float(bonus)
                best_months = months
        return best_bonus, best_window, best_months

    def stage_one_subtype() -> str:
        lookback = min(24, max(10, len(df) - 4))
        if lookback < 10:
            return "Consolidation Breakout"
        prior = df.iloc[-lookback - 3 : -3].copy()
        if len(prior) < 10:
            return "Consolidation Breakout"
        start_close = float(prior["close"].iloc[0])
        end_close = float(prior["close"].iloc[-1])
        slope_pct = ((end_close / start_close) - 1.0) * 100.0 if start_close > 0 else 0.0
        net_move = abs(end_close - start_close)
        total_move = float(prior["close"].diff().abs().sum())
        prior_smoothness = net_move / total_move if total_move > 0 else 0.0
        range_pct = ((float(prior["high"].max()) - float(prior["low"].min())) / start_close) * 100.0 if start_close > 0 else 0.0
        if slope_pct >= 3.0 and prior_smoothness >= 0.32:
            return "Trendline Breakout"
        if range_pct <= 18.0 or prior_smoothness < 0.32:
            return "Consolidation Breakout"
        return "Trendline Breakout"

    early_metrics = stage_metrics(EARLY)
    run_metrics = stage_metrics(RUNAWAY)
    climax_metrics = stage_metrics(CLIMAX)
    sustained_trend_metrics = sustained_metrics()
    sustained_long_bonus, sustained_duration_bars, sustained_duration_months = sustained_duration_bonus()

    early_gain_ok = pd.notna(early_metrics["run_gain_pct"]) and early_metrics["run_gain_pct"] >= EARLY["min_gain_pct"]
    early_up_bars_ok = pd.notna(early_metrics["up_bar_pct"]) and early_metrics["up_bar_pct"] >= EARLY["min_up_bar_pct"]
    early_near_high_ok = pd.notna(early_metrics["off_high_pct"]) and early_metrics["off_high_pct"] <= EARLY["near_high_pct"]
    early_rel_vol_ok = pd.notna(row["rel_vol"]) and row["rel_vol"] >= EARLY["min_rel_vol"]
    early_vol_trend_ok = pd.notna(row["vol_trend_pct"]) and row["vol_trend_pct"] >= EARLY["min_vol_trend_pct"]
    early_acceleration_ok = pd.notna(row["roc_short"]) and pd.notna(row["accel_spread"]) and row["roc_short"] >= EARLY["min_roc_short"] and row["accel_spread"] >= EARLY["min_accel_spread"]
    early_match = universe_quality_ok and trend_quality_ok and trend_aligned and ema_slope_up and early_gain_ok and early_up_bars_ok and early_near_high_ok and early_acceleration_ok and early_vol_trend_ok and early_rel_vol_ok
    early_core_fails = (0.0 if trend_aligned else 1.0) + (0.0 if ema_slope_up else 1.0) + (0.0 if early_gain_ok else 1.0) + (0.0 if early_up_bars_ok else 1.0) + (0.0 if early_near_high_ok else 0.5) + (0.0 if early_acceleration_ok else 0.5)
    early_confirm_fails = (0 if liquidity_ok else 1) + (0 if early_vol_trend_ok else 1) + (0 if early_rel_vol_ok else 1)

    run_gain_ok = pd.notna(run_metrics["run_gain_pct"]) and run_metrics["run_gain_pct"] >= RUNAWAY["min_gain_pct"]
    run_up_bars_ok = pd.notna(run_metrics["up_bar_pct"]) and run_metrics["up_bar_pct"] >= RUNAWAY["min_up_bar_pct"]
    run_near_high_ok = pd.notna(run_metrics["off_high_pct"]) and run_metrics["off_high_pct"] <= RUNAWAY["near_high_pct"]
    run_rel_vol_ok = pd.notna(row["rel_vol"]) and row["rel_vol"] >= RUNAWAY["min_rel_vol"]
    run_vol_trend_ok = pd.notna(row["vol_trend_pct"]) and row["vol_trend_pct"] >= RUNAWAY["min_vol_trend_pct"]
    run_acceleration_ok = pd.notna(row["roc_short"]) and pd.notna(row["accel_spread"]) and row["roc_short"] >= RUNAWAY["min_roc_short"] and row["accel_spread"] >= RUNAWAY["min_accel_spread"]
    run_atr_ok = pd.notna(row["atr_expansion"]) and row["atr_expansion"] >= RUNAWAY["min_atr_expansion"]
    runaway_match = universe_quality_ok and trend_aligned and ema_slope_up and run_gain_ok and run_up_bars_ok and run_near_high_ok and run_acceleration_ok and run_vol_trend_ok and run_rel_vol_ok and run_atr_ok
    run_core_fails = (0.0 if trend_aligned else 1.0) + (0.0 if ema_slope_up else 1.0) + (0.0 if run_gain_ok else 1.0) + (0.0 if run_up_bars_ok else 1.0) + (0.0 if run_near_high_ok else 0.5) + (0.0 if run_acceleration_ok else 0.5)
    run_confirm_fails = (0 if liquidity_ok else 1) + (0 if run_vol_trend_ok else 1) + (0 if run_rel_vol_ok else 1) + (0 if run_atr_ok else 1)

    climax_gain_ok = pd.notna(climax_metrics["run_gain_pct"]) and climax_metrics["run_gain_pct"] >= CLIMAX["min_gain_pct"]
    climax_up_bars_ok = pd.notna(climax_metrics["up_bar_pct"]) and climax_metrics["up_bar_pct"] >= CLIMAX["min_up_bar_pct"]
    climax_near_high_ok = pd.notna(climax_metrics["off_high_pct"]) and climax_metrics["off_high_pct"] <= CLIMAX["near_high_pct"]
    climax_rel_vol_ok = pd.notna(row["rel_vol"]) and row["rel_vol"] >= CLIMAX["min_rel_vol"]
    climax_vol_trend_ok = pd.notna(row["vol_trend_pct"]) and row["vol_trend_pct"] >= CLIMAX["min_vol_trend_pct"]
    climax_acceleration_ok = pd.notna(row["roc_short"]) and pd.notna(row["accel_spread"]) and row["roc_short"] >= CLIMAX["min_roc_short"] and row["accel_spread"] >= CLIMAX["min_accel_spread"]
    climax_atr_ok = pd.notna(row["atr_expansion"]) and row["atr_expansion"] >= CLIMAX["min_atr_expansion"]
    climax_stretch_ok = pd.notna(row["stretch_over_fast_pct"]) and row["stretch_over_fast_pct"] >= CLIMAX["stretch_pct"]
    climax_match = universe_quality_ok and trend_aligned and ema_slope_up and climax_gain_ok and climax_up_bars_ok and climax_near_high_ok and climax_acceleration_ok and climax_vol_trend_ok and climax_rel_vol_ok and climax_atr_ok and climax_stretch_ok
    climax_core_fails = (0.0 if trend_aligned else 1.0) + (0.0 if ema_slope_up else 1.0) + (0.0 if climax_gain_ok else 1.0) + (0.0 if climax_up_bars_ok else 1.0) + (0.0 if climax_near_high_ok else 0.5) + (0.0 if climax_acceleration_ok else 0.5)
    climax_confirm_fails = (0 if liquidity_ok else 1) + (0 if climax_vol_trend_ok else 1) + (0 if climax_rel_vol_ok else 1) + (0 if climax_atr_ok else 1) + (0 if climax_stretch_ok else 1)

    sustained_gain_ok = pd.notna(sustained_trend_metrics["run_gain_pct"]) and sustained_trend_metrics["run_gain_pct"] >= SUSTAINED["min_gain_pct"]
    sustained_up_bars_ok = pd.notna(sustained_trend_metrics["up_bar_pct"]) and sustained_trend_metrics["up_bar_pct"] >= SUSTAINED["min_up_bar_pct"]
    sustained_near_high_ok = pd.notna(sustained_trend_metrics["off_high_pct"]) and sustained_trend_metrics["off_high_pct"] <= SUSTAINED["near_high_pct"]
    sustained_smooth_ok = pd.notna(sustained_trend_metrics["smoothness"]) and sustained_trend_metrics["smoothness"] >= SUSTAINED["min_smoothness"]
    sustained_drawdown_ok = pd.notna(sustained_trend_metrics["max_drawdown_pct"]) and sustained_trend_metrics["max_drawdown_pct"] <= SUSTAINED["max_drawdown_pct"]
    sustained_match = universe_quality_ok and trend_aligned and ema_slope_up and sustained_gain_ok and sustained_up_bars_ok and sustained_near_high_ok and sustained_smooth_ok and sustained_drawdown_ok
    sustained_core_fails = (0.0 if trend_aligned else 1.0) + (0.0 if ema_slope_up else 1.0) + (0.0 if sustained_gain_ok else 1.0) + (0.0 if sustained_up_bars_ok else 1.0) + (0.0 if sustained_near_high_ok else 0.5) + (0.0 if sustained_smooth_ok else 0.5) + (0.0 if sustained_drawdown_ok else 0.5)

    climax_candidate = climax_match or (universe_quality_ok and pd.notna(climax_metrics["run_gain_pct"]) and climax_metrics["run_gain_pct"] >= 18 and climax_core_fails <= 1.5 and climax_confirm_fails <= 2)
    sustained_candidate = sustained_match or (universe_quality_ok and pd.notna(sustained_trend_metrics["run_gain_pct"]) and sustained_trend_metrics["run_gain_pct"] >= 35 and sustained_core_fails <= 2.0)
    runaway_candidate = runaway_match or (universe_quality_ok and pd.notna(run_metrics["run_gain_pct"]) and run_metrics["run_gain_pct"] >= 12 and run_core_fails <= 1.5 and run_confirm_fails <= 2)
    early_candidate = early_match or (universe_quality_ok and trend_quality_ok and pd.notna(early_metrics["run_gain_pct"]) and early_metrics["run_gain_pct"] >= 6 and early_core_fails <= 2.0 and early_confirm_fails <= 2)

    # Exhaustion is exclusive and cautionary. Constructive trend tags can overlap,
    # using the same tolerant stage candidates that make them useful for review.
    early_signal_name = stage_one_subtype() if early_candidate else ""
    constructive_trend_flags = {
        "Trendline Breakout": early_signal_name == "Trendline Breakout",
        "Consolidation Breakout": early_signal_name == "Consolidation Breakout",
        "Breakout Continuation": runaway_candidate,
        "Sustained Uptrend": sustained_candidate,
    }

    if climax_candidate:
        candidate_stage = 4
    elif sustained_candidate:
        candidate_stage = 3
    elif runaway_candidate:
        candidate_stage = 2
    elif early_candidate:
        candidate_stage = 1
    else:
        candidate_stage = 0

    active_run_gain_pct = climax_metrics["run_gain_pct"] if candidate_stage == 4 else sustained_trend_metrics["run_gain_pct"] if candidate_stage == 3 else run_metrics["run_gain_pct"] if candidate_stage == 2 else early_metrics["run_gain_pct"] if candidate_stage == 1 else np.nan
    active_up_bar_pct = climax_metrics["up_bar_pct"] if candidate_stage == 4 else sustained_trend_metrics["up_bar_pct"] if candidate_stage == 3 else run_metrics["up_bar_pct"] if candidate_stage == 2 else early_metrics["up_bar_pct"] if candidate_stage == 1 else np.nan
    active_off_high_pct = climax_metrics["off_high_pct"] if candidate_stage == 4 else sustained_trend_metrics["off_high_pct"] if candidate_stage == 3 else run_metrics["off_high_pct"] if candidate_stage == 2 else early_metrics["off_high_pct"] if candidate_stage == 1 else np.nan
    active_trend_lookback = (
        CLIMAX["lookback_bars"]
        if candidate_stage == 4
        else SUSTAINED["lookback_bars"]
        if candidate_stage == 3
        else RUNAWAY["lookback_bars"]
        if candidate_stage == 2
        else EARLY["lookback_bars"]
        if candidate_stage == 1
        else np.nan
    )
    trend_breakout_bars_since = max(float(active_trend_lookback) - 1.0, 0.0) if pd.notna(active_trend_lookback) else np.nan
    trend_breakout_date = _date_from_bars_ago(df, trend_breakout_bars_since)

    gain_score = max(float(pd.Series([active_run_gain_pct]).fillna(0.0).iloc[0]), 0.0)
    up_bar_score = max(float(pd.Series([active_up_bar_pct]).fillna(0.0).iloc[0]) - 50.0, 0.0)
    vol_trend_score = max(float(pd.Series([row["vol_trend_pct"]]).fillna(0.0).iloc[0]), 0.0)
    rel_vol_score = max((float(row["rel_vol"]) - 1.0) * 100.0, 0.0) if pd.notna(row["rel_vol"]) else 0.0
    atr_expand_score = max((float(row["atr_expansion"]) - 1.0) * 100.0, 0.0) if pd.notna(row["atr_expansion"]) else 0.0
    near_high_score = max(10.0 - float(active_off_high_pct), 0.0) if pd.notna(active_off_high_pct) else 0.0
    smoothness_score = clamp01((float(smoothness_ratio) - cfg.min_smoothness) / max(1.0 - cfg.min_smoothness, 0.01)) * 100.0 if pd.notna(smoothness_ratio) else 0.0
    stability_score = max(30.0 - float(ema_deviation_pct), 0.0) if pd.notna(ema_deviation_pct) else 0.0
    last_close = float(row["close"]) if pd.notna(row["close"]) else 0.0
    avg_dollar_vol = float(row["avg_dollar_vol"]) if pd.notna(row["avg_dollar_vol"]) else 0.0
    sustained_high_price_liquidity_bonus = 0.0
    if (
        candidate_stage == 3
        and last_close >= cfg.sustained_high_price_threshold
        and avg_dollar_vol >= cfg.sustained_high_price_min_avg_dollar_vol
        and sustained_gain_ok
        and sustained_up_bars_ok
        and sustained_near_high_ok
        and sustained_drawdown_ok
    ):
        sustained_high_price_liquidity_bonus = 12.0
        if avg_dollar_vol >= cfg.sustained_high_price_min_avg_dollar_vol * 5:
            sustained_high_price_liquidity_bonus = 18.0
    constructive_trend_signal_count = sum(1 for is_match in constructive_trend_flags.values() if is_match)
    trend_multi_signal_bonus = (
        min(max(constructive_trend_signal_count - 1, 0) * 10.0, 25.0)
        if candidate_stage in {1, 2, 3}
        else 0.0
    )

    gain_score_capped = min(gain_score, 18.0 if candidate_stage == 1 else 30.0 if candidate_stage == 2 else 45.0 if candidate_stage == 3 else 40.0)
    vol_trend_score_capped = min(vol_trend_score, 20.0 if candidate_stage == 1 else 35.0 if candidate_stage == 2 else 40.0 if candidate_stage == 3 else 45.0)
    rel_vol_score_capped = min(rel_vol_score, 60.0 if candidate_stage == 1 else 90.0 if candidate_stage == 2 else 90.0 if candidate_stage == 3 else 120.0)
    atr_score_capped = min(atr_expand_score, 18.0 if candidate_stage == 1 else 28.0 if candidate_stage == 2 else 24.0 if candidate_stage == 3 else 40.0)
    accel_score = min(max(float(pd.Series([row["accel_spread"]]).fillna(0.0).iloc[0]), 0.0), 3.5 if candidate_stage == 1 else 5.0 if candidate_stage == 2 else 4.0 if candidate_stage == 3 else 7.0) * 10.0 + min(max(float(pd.Series([row["roc_short"]]).fillna(0.0).iloc[0]), 0.0), 5.0 if candidate_stage == 1 else 7.0 if candidate_stage == 2 else 6.0 if candidate_stage == 3 else 10.0) * 3.0
    late_move_penalty = (
        max(float(pd.Series([row["stretch_over_fast_pct"]]).fillna(0.0).iloc[0]) - (8.0 if candidate_stage == 1 else 12.0 if candidate_stage == 2 else 16.0 if candidate_stage == 3 else 18.0), 0.0) * (1.0 if candidate_stage == 4 else 2.0)
        + max(float(pd.Series([row["roc_short"]]).fillna(0.0).iloc[0]) - (6.0 if candidate_stage == 1 else 8.0 if candidate_stage == 2 else 9.0 if candidate_stage == 3 else 12.0), 0.0) * (1.5 if candidate_stage == 4 else 3.0)
        + max(float(pd.Series([row["accel_spread"]]).fillna(0.0).iloc[0]) - (3.0 if candidate_stage == 1 else 5.0 if candidate_stage == 2 else 5.0 if candidate_stage == 3 else 7.0), 0.0) * (2.0 if candidate_stage == 4 else 4.0)
        + max(float(pd.Series([row["atr_expansion"]]).fillna(0.0).iloc[0]) - (1.30 if candidate_stage == 1 else 1.45 if candidate_stage == 2 else 1.55 if candidate_stage == 3 else 1.70), 0.0) * 50.0
    )

    if candidate_stage == 1:
        score = gain_score_capped * 1.10 + up_bar_score * 0.55 + accel_score * 0.65 + vol_trend_score_capped * 0.35 + rel_vol_score_capped * 0.20 + near_high_score * 0.55 + smoothness_score * 0.18 + stability_score * 0.40 - late_move_penalty * 1.20
    elif candidate_stage == 2:
        score = gain_score_capped * 1.15 + up_bar_score * 0.65 + accel_score * 0.75 + vol_trend_score_capped * 0.40 + rel_vol_score_capped * 0.22 + atr_score_capped * 0.25 + near_high_score * 0.60 + smoothness_score * 0.20 + stability_score * 0.35 - late_move_penalty * 1.00
    elif candidate_stage == 3:
        score = gain_score_capped * 1.20 + up_bar_score * 0.55 + accel_score * 0.35 + vol_trend_score_capped * 0.25 + rel_vol_score_capped * 0.12 + atr_score_capped * 0.12 + near_high_score * 0.55 + smoothness_score * 0.70 + stability_score * 0.45 - late_move_penalty * 0.75
        score += sustained_long_bonus
        score += sustained_high_price_liquidity_bonus
    elif candidate_stage == 4:
        score = gain_score_capped * 1.10 + up_bar_score * 0.60 + accel_score * 0.80 + vol_trend_score_capped * 0.35 + rel_vol_score_capped * 0.20 + atr_score_capped * 0.20 + near_high_score * 0.70 + smoothness_score * 0.12 + stability_score * 0.20 - late_move_penalty * 0.60
    else:
        score = 0.0
    score += trend_multi_signal_bonus
    score = max(float(score), 0.0)

    stage_thresholds = {
        1: float(cfg.min_trend_score_stage_1),
        2: float(cfg.min_trend_score_stage_2),
        3: float(cfg.min_trend_score_stage_3),
        4: float(cfg.min_trend_score_stage_4),
    }
    stage = candidate_stage if candidate_stage > 0 and score >= stage_thresholds.get(candidate_stage, 0.0) else 0
    if stage == 4:
        emitted_trend_flags = {
            "Trendline Breakout": False,
            "Consolidation Breakout": False,
            "Breakout Continuation": False,
            "Sustained Uptrend": False,
            "Trend Exhaustion": True,
            "Trend Outlier": bool(trend_outlier_metrics["Trend Outlier"]),
        }
        trend_signal_count = 1 + int(bool(trend_outlier_metrics["Trend Outlier"]))
        trend_multi_signal_bonus = 0.0
    elif stage in {1, 2, 3}:
        emitted_trend_flags = {
            **constructive_trend_flags,
            "Trend Exhaustion": False,
            "Trend Outlier": bool(trend_outlier_metrics["Trend Outlier"]),
        }
        trend_signal_count = constructive_trend_signal_count + int(bool(trend_outlier_metrics["Trend Outlier"]))
    else:
        emitted_trend_flags = {
        "Trendline Breakout": False,
        "Consolidation Breakout": False,
        "Breakout Continuation": False,
        "Sustained Uptrend": False,
        "Trend Exhaustion": False,
        "Trend Outlier": bool(trend_outlier_metrics["Trend Outlier"]),
        }
        trend_signal_count = int(bool(trend_outlier_metrics["Trend Outlier"]))
        trend_multi_signal_bonus = 0.0
    if stage == 0 and not bool(trend_outlier_metrics["Trend Outlier"]):
        score = 0.0
    elif bool(trend_outlier_metrics["Trend Outlier"]):
        outlier_score = float(trend_outlier_metrics["Trend Outlier Score"])
        if stage == 0:
            score = outlier_score
        elif stage != 4:
            score += min(outlier_score * 0.20, 20.0)
    if debug_profile is not None:
        _profile_add(debug_profile, "snapshot_trend", time.perf_counter() - trend_started_at)

    triangle_started_at = time.perf_counter() if debug_profile is not None else 0.0
    triangle_metrics = compute_triangle_metrics(
        df,
        stage,
        cfg,
        refresh_mode=refresh_mode,
        debug_profile=debug_profile,
    )
    if debug_profile is not None:
        _profile_add(debug_profile, "snapshot_triangle", time.perf_counter() - triangle_started_at)
    resolved_triangle_breakout_date = triangle_metrics.get("TD Breakout Date")
    resolved_triangle_bars_since = triangle_metrics.get("TD Bars Since Breakout")
    technical_breakout_date = resolved_triangle_breakout_date or (trend_breakout_date if stage > 0 else None)
    technical_bars_since_breakout = (
        resolved_triangle_bars_since
        if pd.notna(resolved_triangle_bars_since)
        else trend_breakout_bars_since
        if stage > 0 and pd.notna(trend_breakout_bars_since)
        else np.nan
    )

    snapshot = {
        "Symbol": symbol.upper(),
        "Trend Score": round(score, 2),
        "TD Trend Context Raw": round(score, 4),
        "Trendline Breakout": int(emitted_trend_flags["Trendline Breakout"]),
        "Consolidation Breakout": int(emitted_trend_flags["Consolidation Breakout"]),
        "Breakout Continuation": int(emitted_trend_flags["Breakout Continuation"]),
        "Sustained Uptrend": int(emitted_trend_flags["Sustained Uptrend"]),
        "Trend Exhaustion": int(emitted_trend_flags["Trend Exhaustion"]),
        "Trend Outlier": int(emitted_trend_flags["Trend Outlier"]),
        "Trend Outlier Score": trend_outlier_metrics["Trend Outlier Score"],
        "Trend Outlier Benchmark": trend_outlier_metrics["Trend Outlier Benchmark"],
        "Trend Outlier Window": trend_outlier_metrics["Trend Outlier Window"],
        "Trend Outlier Stock Return 1D": trend_outlier_metrics["Trend Outlier Stock Return 1D"],
        "Trend Outlier Benchmark Return 1D": trend_outlier_metrics["Trend Outlier Benchmark Return 1D"],
        "Trend Outlier Relative Return 1D": trend_outlier_metrics["Trend Outlier Relative Return 1D"],
        "Trend Outlier Stock Return 5D": trend_outlier_metrics["Trend Outlier Stock Return 5D"],
        "Trend Outlier Benchmark Return 5D": trend_outlier_metrics["Trend Outlier Benchmark Return 5D"],
        "Trend Outlier Relative Return 5D": trend_outlier_metrics["Trend Outlier Relative Return 5D"],
        "Trend Outlier Stock Return 20D": trend_outlier_metrics["Trend Outlier Stock Return 20D"],
        "Trend Outlier Benchmark Return 20D": trend_outlier_metrics["Trend Outlier Benchmark Return 20D"],
        "Trend Outlier Relative Return 20D": trend_outlier_metrics["Trend Outlier Relative Return 20D"],
        "Trend Outlier Correlation 60D": trend_outlier_metrics["Trend Outlier Correlation 60D"],
        "Trend Signal Count": int(trend_signal_count),
        "Trend Multi Signal Bonus": round(float(trend_multi_signal_bonus), 2),
        "Stage": stage if stage > 0 else np.nan,
        "Universe Quality OK": int(universe_quality_ok),
        "Trend Quality OK": int(trend_quality_ok),
        "Trend Aligned": int(trend_aligned),
        "EMA Slope Up": int(ema_slope_up),
        "Last Close": round(float(row["close"]), 4),
        "Average Dollar Volume": round(float(row["avg_dollar_vol"]), 2) if pd.notna(row["avg_dollar_vol"]) else np.nan,
        "Relative Volume": round(float(row["rel_vol"]), 4) if pd.notna(row["rel_vol"]) else np.nan,
        "Volume Trend %": round(float(row["vol_trend_pct"]), 4) if pd.notna(row["vol_trend_pct"]) else np.nan,
        "ATR Expansion": round(float(row["atr_expansion"]), 4) if pd.notna(row["atr_expansion"]) else np.nan,
        "Run Gain %": round(float(active_run_gain_pct), 4) if pd.notna(active_run_gain_pct) else np.nan,
        "Up Bar %": round(float(active_up_bar_pct), 4) if pd.notna(active_up_bar_pct) else np.nan,
        "Off High %": round(float(active_off_high_pct), 4) if pd.notna(active_off_high_pct) else np.nan,
        "Sustained Duration Bars": int(sustained_duration_bars) if stage == 3 else 0,
        "Sustained Duration Months": round(float(sustained_duration_months), 2) if stage == 3 else 0.0,
        "Sustained Duration Bonus": round(float(sustained_long_bonus), 2) if stage == 3 else 0.0,
        "Sustained High Price Liquidity Bonus": round(float(sustained_high_price_liquidity_bonus), 2) if stage == 3 else 0.0,
        **triangle_metrics,
        "TD Breakout Date": technical_breakout_date,
        "TD Bars Since Breakout": round(float(technical_bars_since_breakout), 4) if pd.notna(technical_bars_since_breakout) else np.nan,
    }
    if debug_profile is not None:
        _profile_add(debug_profile, "snapshot_total", time.perf_counter() - snapshot_started_at)
        snapshot["__compute_profile__"] = debug_profile
    return snapshot
