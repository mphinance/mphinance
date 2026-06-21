"""Downtrend Trendline Break (Reversal) screener for the Daily Review dossier.

Michael's #1 setup: a stock that has been in a DOWNTREND making lower highs along
a falling resistance trendline, that then BREAKS OUT above that line — a reversal
out of the downtrend. NOT a descending triangle (no flat-support floor), NOT an
uptrend pullback, NOT a falling knife.

The detector fits its OWN descending resistance line over a LONG window
(~190 bars / ~9 months) across significant pivot highs (reusing
triangle_logic.pivot_high), letting the older anchor sit on the major multi-month
peak — "go further back for the trend." The break decision is rebuilt from the
line evaluated AT THE BREAK BAR. triangle_logic's compute_breakout_snapshot is
reused only for the universe-quality/liquidity gate and 20-day trend context.

Tiers:
  confirmed  recent break of the multi-month falling line, on volume, out of a
             real (non-knife) downtrend, price now CLEARS the line by a real
             margin. The actionable signal (NKE as-of ~2026-05-20).
  extended   same break but the entry has passed: break older OR price run far
             above the line ("a little close" — NKE mid-June). Detected for
             history but NOT an actionable confluence leg.
  retest     price broke but sits ON the line (clearance < confirm). NOT a buy.
  forming    clean falling line + real downtrend, close coiling into the
             underside from below, not through yet. The early watch.

Shape matches the other dossier screeners: per-ticker
`scan_downtrend_break(t) -> dict|None` + batch
`generate_downtrend_breaks(tickers, ...) -> list[dict]`.

HARD RULE: nothing here ever raises. Every failure path degrades to None / [].
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

try:
    import numpy as np
    import pandas as pd
    import yfinance as yf
except Exception:  # pragma: no cover - degrade if deps missing
    np = None  # type: ignore[assignment]
    pd = None  # type: ignore[assignment]
    yf = None  # type: ignore[assignment]

try:
    from .triangle_logic import BreakoutConfig, compute_breakout_snapshot, pivot_high
except Exception:  # pragma: no cover - allow running as a loose script
    from triangle_logic import BreakoutConfig, compute_breakout_snapshot, pivot_high  # type: ignore

HISTORY_PERIOD = "2y"
MIN_HISTORY_BARS = 260

# --- long-window line-fit parameters ---------------------------------------
LINE_WINDOW_BARS = 190          # ~9 months: long enough to reach the major peak
PIVOT_LEFT = 3                  # pivot-high half-window (L3R3 -> swing highs)
PIVOT_RIGHT = 3
MIN_LINE_SPAN_BARS = 25         # (newer_idx - older_idx) >= 25 -> real downtrend
MIN_SLOPE_PCT_PER_BAR = 0.20    # falling line floor (reject near-flat base ceiling)
MAX_SLOPE_PCT_PER_BAR = 3.0     # waterfall-crash cliff cap
CUTTHROUGH_TOL_PCT = 2.0        # a significant high between anchors may not pierce
                                # the line by more than this (line must be a ceiling)
BREAK_BUFFER_PCT = 0.5          # close must clear the line by this AT the break bar

# --- break / tier parameters ------------------------------------------------
CONFIRM_RECENCY_BARS = 8        # break within last N bars -> fresh confirmed
EXTENDED_RECENCY_BARS = 35      # (8, 35] -> entry passed but still valid (extended)
CONFIRM_CLEARANCE_PCT = 1.0     # price NOW must clear the line by >=1% to be real
                                # (on-the-line < 1% => retest, NOT confirmed)
EXTENDED_CLEARANCE_PCT = 12.0   # run this far above the line => extended (stretched)
DROP_CLEARANCE_PCT = 45.0       # absurdly far above line => stale, drop
VOL_REJECT = 0.90               # break-bar volume < 0.9x 20d avg => no demand, drop
VOL_STRONG = 1.5

# --- downtrend / junk-rejection stack ---------------------------------------
DECLINE_DEPTH_FLOOR = 0.12      # peak -> last close >= 12% (real prior downtrend)
DECLINE_DEPTH_KNIFE_CAP = 0.55  # reject > 55% collapse (falling knife)
RETEST_DECLINE_CAP = 0.45       # a retest (on-the-line) sitting on a near-knife
                                # (>45%) decline is a dead-cat bounce -> drop (DJT)
RET20_FLOOR = -3.0              # 1-mo return not strongly positive (not an uptrend)
FORMING_LOW_PCT = -2.5          # close within 2.5% below the line -> forming
FORMING_HIGH_PCT = BREAK_BUFFER_PCT
FORMING_MAX_COIL_RANGE_PCT = 9.0  # recent 20-bar range must be a tight coil, not
                                  # a wide chopping base (PYPL $40-52 ~13% => reject)


def _num(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:
        return None
    return f


def _rsi(close: "pd.Series", length: int = 14) -> "pd.Series":
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    roll_up = up.ewm(alpha=1.0 / length, min_periods=length).mean()
    roll_down = down.ewm(alpha=1.0 / length, min_periods=length).mean()
    rs = roll_up / roll_down.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def _fetch(symbol: str, asof: str | None = None) -> "pd.DataFrame | None":
    if yf is None:
        return None
    try:
        raw = yf.Ticker(symbol).history(period=HISTORY_PERIOD, auto_adjust=True)
    except Exception:
        return None
    if raw is None or raw.empty:
        return None
    hist = raw.reset_index()
    hist.columns = [str(c).lower() for c in hist.columns]
    if "date" not in hist.columns:
        hist = hist.rename(columns={hist.columns[0]: "date"})
    required = {"date", "open", "high", "low", "close", "volume"}
    if not required.issubset(set(hist.columns)):
        return None
    hist["date"] = pd.to_datetime(hist["date"])
    if hist["date"].dt.tz is not None:
        hist["date"] = hist["date"].dt.tz_localize(None)
    if asof is not None:
        hist = hist[hist["date"] <= pd.to_datetime(asof)].reset_index(drop=True)
    if len(hist) < MIN_HISTORY_BARS:
        return None
    return hist


def fit_descending_line(sub: "pd.DataFrame") -> dict[str, Any] | None:
    """Fit the best multi-month falling resistance line over the long window and
    locate its first decisive close-through (break). Returns line geometry +
    break bar, or None. `sub` is the LINE_WINDOW_BARS tail, index-reset.

    The line is anchored on two significant pivot highs. We DELIBERATELY allow the
    older anchor to sit on the major multi-month peak (no recency bias on the older
    anchor). Selection prefers a steep, long-span, high-anchored line (the real
    downtrend), and rejects lines a significant intervening high pierces (not a
    true ceiling)."""
    n = len(sub)
    highs = sub["high"].astype(float).reset_index(drop=True)
    closes = sub["close"].astype(float).reset_index(drop=True)
    ph = pivot_high(highs, PIVOT_LEFT, PIVOT_RIGHT)
    piv = [(int(i), float(highs.iloc[i])) for i in np.flatnonzero(ph.notna().to_numpy())]
    if len(piv) < 2:
        return None

    best: dict[str, Any] | None = None
    for oi, op in piv:
        for ni, npr in piv:
            if ni - oi < MIN_LINE_SPAN_BARS:
                continue
            if npr >= op:                       # newer high must be LOWER (descending)
                continue
            slope = (npr - op) / (ni - oi)
            spb = abs(slope) / ((op + npr) / 2.0) * 100.0
            if spb < MIN_SLOPE_PCT_PER_BAR or spb > MAX_SLOPE_PCT_PER_BAR:
                continue

            def line(x: float, _op=op, _slope=slope, _oi=oi) -> float:
                return _op + _slope * (x - _oi)

            # The line must be a real ceiling: no significant intervening pivot
            # high may pierce it (beyond tolerance) between the two anchors.
            if any(oi < pi < ni and pp > line(pi) * (1.0 + CUTTHROUGH_TOL_PCT / 100.0)
                   for pi, pp in piv):
                continue

            # First decisive close-through AFTER the newer anchor.
            broke = None
            for x in range(ni + 1, n):
                if closes.iloc[x] > line(x) * (1.0 + BREAK_BUFFER_PCT / 100.0):
                    broke = x
                    break
            if broke is None:
                continue

            line_at_break = line(broke)
            last_close = float(closes.iloc[-1])
            # Price as-of-now must still be above the level it broke (didn't give
            # the break fully back). Clearance tier decided by the caller.
            if last_close <= line_at_break:
                continue

            # Prefer the steepest, longest-span, highest-anchored line (the real
            # multi-month downtrend), not a short shallow tail.
            score = abs(slope) * (ni - oi) + op * 0.5
            cand = {
                "older_idx": oi, "newer_idx": ni,
                "older_price": op, "newer_price": npr,
                "slope": slope, "slope_pct_per_bar": spb,
                "break_idx": broke,
                "line_at_break": line_at_break,
                "break_close": float(closes.iloc[broke]),
                "score": score,
            }
            if best is None or score > best["score"]:
                best = cand
    return best


def _forming_candidate(sub, highs, closes):
    """Best descending pivot-pair line (no break required) for the forming tier."""
    n = len(sub)
    ph = pivot_high(highs, PIVOT_LEFT, PIVOT_RIGHT)
    piv = [(int(i), float(highs.iloc[i])) for i in np.flatnonzero(ph.notna().to_numpy())]
    best = None
    for oi, op in piv:
        for ni, npr in piv:
            if ni - oi < MIN_LINE_SPAN_BARS or npr >= op:
                continue
            slope = (npr - op) / (ni - oi)
            spb = abs(slope) / ((op + npr) / 2.0) * 100.0
            if spb < MIN_SLOPE_PCT_PER_BAR or spb > MAX_SLOPE_PCT_PER_BAR:
                continue

            def line(x, _op=op, _slope=slope, _oi=oi):
                return _op + _slope * (x - _oi)

            if any(oi < pi < ni and pp > line(pi) * (1.0 + CUTTHROUGH_TOL_PCT / 100.0)
                   for pi, pp in piv):
                continue
            # newer anchor must be reasonably recent so the line is current.
            if (n - 1) - ni > 30:
                continue
            score = abs(slope) * (ni - oi) + op * 0.5
            geom = {"older_idx": oi, "newer_idx": ni, "older_price": op,
                    "newer_price": npr, "slope": slope, "slope_pct_per_bar": spb,
                    "break_idx": None, "line_at_break": None, "score": score}
            if best is None or score > best["score"]:
                best = geom
    if best is None:
        return None
    line_now = best["older_price"] + best["slope"] * ((n - 1) - best["older_idx"])
    return line_now, best


def _result(symbol, signal, pattern, sub, geom, *, line_now, clearance_pct,
            break_idx, decline, ret20, rsi_now, rsi_rising, vols, vol_ratio,
            above_emas, bars_since=None):
    dates = pd.to_datetime(sub["date"]).reset_index(drop=True)
    oi = geom["older_idx"]; ni = geom["newer_idx"]
    blend = min(decline * 100.0, 35.0)
    if vol_ratio:
        blend += min(max(vol_ratio - 1.0, 0.0) * 20.0, 20.0)
    if rsi_rising:
        blend += 10.0
    if pattern == "confirmed":
        blend += 15.0
    strength = "strong" if blend >= 55 else "moderate" if blend >= 35 else "weak"
    return {
        "ticker": symbol,
        "signal_type": signal,
        "pattern": pattern,
        "signal_strength": strength,
        "older_pivot_date": str(dates.iloc[oi].date()),
        "older_pivot_price": round(geom["older_price"], 2),
        "newer_pivot_date": str(dates.iloc[ni].date()),
        "newer_pivot_price": round(geom["newer_price"], 2),
        "slope": round(geom["slope"], 5),
        "slope_pct_per_bar": round(geom["slope_pct_per_bar"], 4),
        "line_span_bars": int(ni - oi),
        "break_date": str(dates.iloc[break_idx].date()) if break_idx is not None else None,
        "line_at_break": round(geom["line_at_break"], 2) if geom.get("line_at_break") else None,
        "line_now": round(line_now, 2),
        "clearance_pct": round(clearance_pct, 2),
        "bars_since_break": bars_since,
        "decline_depth_pct": round(decline * 100.0, 2),
        "ret20_pct": round(ret20, 2) if ret20 is not None else None,
        "vol_ratio": round(vol_ratio, 2) if vol_ratio else None,
        "rsi14": round(rsi_now, 1) if rsi_now is not None else None,
        "rsi_rising": rsi_rising,
        "above_rising_emas": above_emas,
        "last_close": round(float(sub["close"].iloc[-1]), 2),
    }


def scan_downtrend_break(ticker: str, asof: str | None = None,
                         hist: "pd.DataFrame | None" = None) -> dict[str, Any] | None:
    """Detect a downtrend-trendline break on one ticker's daily bars.

    Returns a screener-shaped dict, or None when there's no qualifying setup (or
    anything goes wrong — this function never raises). `asof` truncates history for
    point-in-time testing; `hist` lets a caller supply already-fetched bars.
    """
    if np is None or not ticker:
        return None
    try:
        symbol = str(ticker).strip().upper()
        if not symbol:
            return None
        if hist is None:
            hist = _fetch(symbol, asof=asof)
        if hist is None:
            return None

        # Universe-quality / liquidity gate + trend context (reused engine).
        snap = compute_breakout_snapshot(
            hist, symbol=symbol,
            cfg=replace(BreakoutConfig(), required_history_bars_qualified=MIN_HISTORY_BARS),
        )
        if not snap or snap.get("Error"):
            return None
        if not snap.get("Universe Quality OK"):
            return None
        ret20 = _num(snap.get("Trend Outlier Stock Return 20D"))

        sub = hist.tail(LINE_WINDOW_BARS).reset_index(drop=True)
        n = len(sub)
        closes = sub["close"].astype(float).reset_index(drop=True)
        highs = sub["high"].astype(float).reset_index(drop=True)
        lows = sub["low"].astype(float).reset_index(drop=True)
        vols = sub["volume"].astype(float).reset_index(drop=True)
        last_close = float(closes.iloc[-1])
        if last_close <= 0:
            return None

        # EMA context for uptrend-pullback reject (NVDA/MRNA).
        ema20 = float(closes.ewm(span=20, adjust=False).mean().iloc[-1])
        ema50 = float(closes.ewm(span=50, adjust=False).mean().iloc[-1])
        above_rising_emas = (last_close > ema20 and ema20 > ema50)

        # Real prior downtrend depth: major peak over the window -> last close.
        window_peak = float(highs.max())
        decline = (window_peak - last_close) / window_peak if window_peak > 0 else 0.0

        # RSI / vol labels.
        rsi_s = _rsi(closes)
        rsi_now = _num(rsi_s.iloc[-1]) if len(rsi_s) else None
        rsi_prev = _num(rsi_s.iloc[-4]) if len(rsi_s) > 4 else None
        rsi_rising = (rsi_now is not None and rsi_prev is not None and rsi_now > rsi_prev)

        fit = fit_descending_line(sub)

        # ---------------- FORMING (no confirmed break yet) ------------------
        if fit is None:
            forming = _forming_candidate(sub, highs, closes)
            if forming is None:
                return None
            line_now, geom = forming
            dist_pct = (last_close / line_now - 1.0) * 100.0
            if not (FORMING_LOW_PCT <= dist_pct < FORMING_HIGH_PCT):
                return None
            if decline < DECLINE_DEPTH_FLOOR or decline > DECLINE_DEPTH_KNIFE_CAP:
                return None
            if above_rising_emas:
                return None
            # Coil gate: forming requires price COILING tightly under the line, not
            # chopping inside a wide flat base. Recent 20-bar high-low range must be
            # tight (<= FORMING_MAX_COIL_RANGE_PCT of price). PYPL's $40-52 base
            # (~13% range) is chop, not a coil -> reject.
            recent_range_pct = (float(highs.tail(20).max()) - float(lows.tail(20).min())) / last_close * 100.0
            if recent_range_pct > FORMING_MAX_COIL_RANGE_PCT:
                return None
            if ret20 is not None and ret20 > RET20_FLOOR:
                return None
            return _result(symbol, "downtrend_break_forming", "forming", sub, geom,
                           line_now=line_now, clearance_pct=dist_pct, break_idx=None,
                           decline=decline, ret20=ret20, rsi_now=rsi_now,
                           rsi_rising=rsi_rising, vols=vols, vol_ratio=None,
                           above_emas=above_rising_emas)

        # ---------------- BREAK FOUND: confirmed / extended / retest --------
        break_idx = fit["break_idx"]
        line_at_break = fit["line_at_break"]
        bars_since = (n - 1) - break_idx
        clearance_pct = (last_close / line_at_break - 1.0) * 100.0

        # depth band: real downtrend, not a falling knife.
        if decline < DECLINE_DEPTH_FLOOR:
            return None
        if decline > DECLINE_DEPTH_KNIFE_CAP:
            return None
        # not an uptrend pullback (NVDA): a falling line that broke long ago and is
        # now riding above rising EMAs is a continuation, not a reversal break.
        if above_rising_emas:
            return None

        # break-bar volume (demand).
        v20 = float(vols.iloc[max(0, break_idx - 20):break_idx].mean()) if break_idx >= 1 else float(vols.iloc[:break_idx + 1].mean())
        bv = float(vols.iloc[break_idx])
        vol_ratio = (bv / v20) if v20 and v20 > 0 else None

        # stale / blown-off-distance reject.
        if bars_since > EXTENDED_RECENCY_BARS:
            return None
        if clearance_pct > DROP_CLEARANCE_PCT:
            return None

        # RETEST tier: price sits ON the line (cleared the break but pulled back to
        # within CONFIRM_CLEARANCE_PCT). PYPL/DJT live here -> NOT confirmed.
        if clearance_pct < CONFIRM_CLEARANCE_PCT:
            if decline > RETEST_DECLINE_CAP:
                return None
            if bars_since <= EXTENDED_RECENCY_BARS and (vol_ratio is None or vol_ratio >= VOL_REJECT):
                return _result(symbol, "downtrend_break_retest", "retest", sub, fit,
                               line_now=line_at_break, clearance_pct=clearance_pct,
                               break_idx=break_idx, decline=decline, ret20=ret20,
                               rsi_now=rsi_now, rsi_rising=rsi_rising, vols=vols,
                               vol_ratio=vol_ratio, above_emas=above_rising_emas,
                               bars_since=bars_since)
            return None

        # Real clearance -> confirmed or extended. Volume demand required.
        if vol_ratio is None or vol_ratio < VOL_REJECT:
            return None

        if bars_since <= CONFIRM_RECENCY_BARS and clearance_pct <= EXTENDED_CLEARANCE_PCT:
            pattern = "confirmed"
        else:
            # entry passed: break older (>8 bars) or price run far above the line.
            pattern = "extended"

        return _result(symbol, "downtrend_break", pattern, sub, fit,
                       line_now=line_at_break, clearance_pct=clearance_pct,
                       break_idx=break_idx, decline=decline, ret20=ret20,
                       rsi_now=rsi_now, rsi_rising=rsi_rising, vols=vols,
                       vol_ratio=vol_ratio, above_emas=above_rising_emas,
                       bars_since=bars_since)
    except Exception:
        return None


def generate_downtrend_breaks(tickers: list[str], asof: str | None = None,
                              max_results: int = 10) -> list[dict[str, Any]]:
    """Scan a list of tickers, return up to `max_results` downtrend-break signals.

    Ranked confirmed -> extended -> retest -> forming, then deeper decline first.
    Never raises — bad tickers are skipped.
    """
    if not tickers:
        return []
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for t in tickers:
        try:
            sym = str(t).strip().upper()
        except Exception:
            continue
        if not sym or sym in seen:
            continue
        seen.add(sym)
        sig = scan_downtrend_break(sym, asof=asof)
        if sig:
            results.append(sig)
    rank = {"confirmed": 0, "extended": 1, "retest": 2, "forming": 3}
    results.sort(key=lambda i: (rank.get(i.get("pattern"), 4), -(i.get("decline_depth_pct") or 0)))
    try:
        limit = int(max_results)
    except (TypeError, ValueError):
        limit = 10
    return results[:max(0, limit)]


if __name__ == "__main__":
    import json
    sample = ["NKE", "PYPL", "NVDA", "MRNA", "DJT"]
    found = generate_downtrend_breaks(sample, max_results=40)
    print(f"{len(found)} signal(s) of {len(sample)} scanned:")
    for sig in found:
        print(json.dumps(sig, default=str))
