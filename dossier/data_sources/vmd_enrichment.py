"""
VMD (Variational Mode Decomposition) Enrichment
================================================

Decomposes a stock's price time series into K smooth oscillating modes:
  - Mode 1 (slow)  → Macro trend (like the bass line)
  - Mode 2 (mid)   → Swing component (rhythm section)
  - Mode 3 (fast)  → Short-term oscillation / noise

Returns:
  - vmd_regime:      "trending" | "mean_reverting" | "transitioning"
  - vmd_trend_slope: Slope of the slow mode (positive = bullish, negative = bearish)
  - vmd_momentum:    Denoised momentum score (-100 to 100) from slow+mid modes
  - vmd_noise_ratio: How much of the signal is noise (0-1, higher = choppier)
  - vmd_forecast:    3-day projected direction from mode extrapolation

Uses the vmdpy library (Variational Mode Decomposition for Python).
Ref: Dragomiretskiy & Zosso (2014), "Variational Mode Decomposition"
"""

import numpy as np
import yfinance as yf
import json
import sys

try:
    from vmdpy import VMD
except ImportError:
    VMD = None


def _compute_slope(series, window=10):
    """Linear regression slope of last N points, normalized."""
    if len(series) < window:
        return 0.0
    y = series[-window:]
    x = np.arange(window)
    slope = np.polyfit(x, y, 1)[0]
    return slope


def _mode_energy(mode):
    """Energy (variance) of a mode."""
    return float(np.var(mode))


def enrich_ticker_vmd(ticker: str, period: str = "6mo", K: int = 3) -> dict | None:
    """
    Decompose price into K modes via VMD and extract trading signals.

    Args:
        ticker: Stock symbol
        period: yfinance period string
        K: Number of modes to decompose into (default 3: trend, swing, noise)

    Returns:
        dict with VMD-derived features, or None on failure
    """
    if VMD is None:
        print(f"  [VMD] vmdpy not installed, skipping {ticker}")
        return None

    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False)
        if df.empty or len(df) < 60:
            return None

        # Use Close prices
        if hasattr(df.columns, 'droplevel'):
            try:
                df.columns = df.columns.droplevel(1)
            except Exception:
                pass

        close = df["Close"].dropna().values.astype(float)
        if len(close) < 60:
            return None

        # Normalize to prevent numerical issues (VMD works better on centered data)
        mean_price = np.mean(close)
        std_price = np.std(close) if np.std(close) > 0 else 1
        signal = (close - mean_price) / std_price

        # ── VMD Parameters ──
        alpha = 2000    # Bandwidth constraint (higher = smoother modes)
        tau = 0.0       # Noise tolerance (0 = exact reconstruction)
        DC = 0          # No DC component
        init = 1        # Initialize uniformly
        tol = 1e-7      # Convergence tolerance

        # Run VMD
        u, u_hat, omega = VMD(signal, alpha, tau, K, DC, init, tol)

        # Sort modes by center frequency (slow → fast)
        omega_arr = np.array(omega)
        if omega_arr.ndim == 2:
            center_freqs = np.mean(np.abs(omega_arr), axis=0)  # shape: (iterations, K) → mean over iterations
        else:
            center_freqs = np.abs(omega_arr)
        sort_idx = np.argsort(center_freqs[:K])
        u = u[sort_idx]
        center_freqs = center_freqs[sort_idx]

        # Denormalize modes back to price units
        modes = u * std_price  # Scale back (offset doesn't matter for analysis)

        # ── Mode Analysis ──
        trend_mode = modes[0]    # Slowest oscillation
        swing_mode = modes[1] if K >= 2 else np.zeros_like(trend_mode)
        noise_mode = modes[-1]   # Fastest oscillation

        # Energy distribution
        energies = [_mode_energy(m) for m in modes]
        total_energy = sum(energies) if sum(energies) > 0 else 1
        noise_ratio = energies[-1] / total_energy
        trend_energy_pct = energies[0] / total_energy

        # ── Trend Slope ──
        # Slope of the slow mode (normalized by ATR-like measure)
        trend_slope = _compute_slope(trend_mode, window=min(20, len(trend_mode) // 2))
        avg_range = np.mean(np.abs(np.diff(close[-20:]))) if len(close) >= 20 else 1
        normalized_slope = trend_slope / avg_range if avg_range > 0 else 0

        # ── Denoised Momentum ──
        # Combine trend + swing modes, compute rate of change
        denoised = trend_mode + swing_mode
        if len(denoised) >= 10:
            roc_5 = (denoised[-1] - denoised[-6]) / (np.abs(denoised[-6]) + 1e-8) * 100
            roc_10 = (denoised[-1] - denoised[-11]) / (np.abs(denoised[-11]) + 1e-8) * 100 if len(denoised) >= 11 else roc_5
            momentum = float(np.clip((roc_5 + roc_10) / 2, -100, 100))
        else:
            momentum = 0.0

        # ── Regime Detection ──
        # Compare energy ratios and trend slope to classify
        if trend_energy_pct > 0.6 and abs(normalized_slope) > 0.5:
            regime = "trending"
        elif noise_ratio > 0.35:
            regime = "choppy"
        elif abs(normalized_slope) < 0.2 and noise_ratio < 0.25:
            regime = "mean_reverting"
        else:
            regime = "transitioning"

        # ── Mode Forecast (Simple Sine Extrapolation) ──
        # Extrapolate each mode by 3 days using last cycle
        forecast_days = 3
        forecast_sum = 0.0
        for mode in modes:
            # Use last 20 points to estimate local frequency/phase
            segment = mode[-20:]
            # Simple: linear extrapolation of slope
            slope = _compute_slope(segment, window=min(10, len(segment)))
            forecast_sum += slope * forecast_days

        forecast_direction = "bullish" if forecast_sum > 0.5 else "bearish" if forecast_sum < -0.5 else "neutral"
        forecast_magnitude = float(np.clip(abs(forecast_sum) / avg_range * 100, 0, 100))

        # ── Swing Extremes ──
        # Check if swing mode is near its cycle extremes (potential reversal)
        if len(swing_mode) >= 20:
            swing_pct = (swing_mode[-1] - np.min(swing_mode[-20:])) / (np.ptp(swing_mode[-20:]) + 1e-8) * 100
            swing_position = "overbought" if swing_pct > 80 else "oversold" if swing_pct < 20 else "mid_cycle"
        else:
            swing_pct = 50
            swing_position = "mid_cycle"

        result = {
            "vmd_regime": regime,
            "vmd_trend_slope": round(normalized_slope, 4),
            "vmd_momentum": round(momentum, 2),
            "vmd_noise_ratio": round(noise_ratio, 4),
            "vmd_trend_energy_pct": round(trend_energy_pct * 100, 1),
            "vmd_forecast_direction": forecast_direction,
            "vmd_forecast_magnitude": round(forecast_magnitude, 1),
            "vmd_swing_position": swing_position,
            "vmd_swing_pct": round(swing_pct, 1),
            "vmd_modes_K": K,
            "vmd_center_freqs": [round(float(f), 4) for f in center_freqs],
            "vmd_energy_distribution": [round(e / total_energy * 100, 1) for e in energies],
        }

        return result

    except Exception as e:
        print(f"  [VMD] Error decomposing {ticker}: {e}")
        return None


def batch_enrich_vmd(tickers: list) -> dict:
    """Run VMD enrichment on a list of tickers."""
    results = {}
    for t in tickers:
        print(f"  [VMD] Decomposing {t}...")
        res = enrich_ticker_vmd(t)
        if res:
            results[t] = res
            regime = res["vmd_regime"]
            slope = res["vmd_trend_slope"]
            emoji = "📈" if slope > 0 else "📉"
            print(f"    {emoji} {regime} | slope={slope:.3f} | momentum={res['vmd_momentum']:.1f} | noise={res['vmd_noise_ratio']:.1%}")
    return results


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    result = enrich_ticker_vmd(ticker)
    if result:
        print(json.dumps(result, indent=2))
    else:
        print(f"Failed to decompose {ticker}")
