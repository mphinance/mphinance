"""Ascending Reversal-Coil screener for the Daily Review dossier.

The MIRROR of downtrend_breakout. Where that detector fits a FALLING resistance
line through pivot HIGHS (lower highs) and catches a break UP through it, THIS one
catches the setup the moment BEFORE: a stock still pinned UNDER a declining (or
flat) 200-day SMA that is quietly building a base of HIGHER LOWS — a rising support
line through pivot LOWS — coiling UP into a flat-ish horizontal "lid" that sits
right at the falling 200DMA. An ascending triangle pressing into the 200DMA from
below. The longer downtrend is still intact (price below a declining 200), which is
what makes this a *reversal-in-waiting*, NOT a momentum-pullback / continuation.

Michael's manual DIS find (2026-06-18) that downtrend_breakout misses: higher lows
from ~$92.19 (3/27) rising to ~$97.95 (6/10), coiling under a ~$105-107 lid that is
the declining 200DMA (~$106.86), price $103.89 still below it, bearish EMA stack.
The actionable trigger is a confirmed daily CLOSE above the lid / reclaim of the
200DMA.

The detector fits its OWN rising support line over a LONG window (~190 bars /
~9 months) across significant pivot lows (reusing triangle_logic.pivot_low),
letting the older anchor sit on the major multi-month trough — "go further back for
the trend." It then locates a flat-ish lid the highs respect, anchored near the
declining 200DMA, and decides the tier from where price sits relative to that lid.
triangle_logic's compute_breakout_snapshot is reused only for the
universe-quality/liquidity gate and 20-day trend context.

Tiers:
  confirmed  fresh close ABOVE the lid / 200DMA, on volume, out of a real
             still-below-a-declining-200 base. The actionable signal.
  extended   reclaim happened but the entry has passed: reclaim older OR price run
             far above the lid. Detected for history but NOT a confluence leg.
  retest     reclaimed but price sits ON the lid (clearance < confirm). NOT a buy.
  forming    rising support + flat lid under a declining 200, close coiling into
             the lid from below, not through yet. The key watch tier (DIS lives
             here, or confirmed, depending on the bar).

Shape matches the other dossier screeners: per-ticker
`scan_ascending_reversal(t) -> dict|None` + batch
`generate_ascending_reversals(tickers, ...) -> list[dict]`.

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
    from .triangle_logic import BreakoutConfig, compute_breakout_snapshot, pivot_high, pivot_low
except Exception:  # pragma: no cover - allow running as a loose script
    from triangle_logic import BreakoutConfig, compute_breakout_snapshot, pivot_high, pivot_low  # type: ignore

HISTORY_PERIOD = "2y"
MIN_HISTORY_BARS = 260

# --- long-window line-fit parameters ---------------------------------------
LINE_WINDOW_BARS = 190          # ~9 months: long enough to reach the major trough
PIVOT_LEFT = 3                  # pivot-low half-window (L3R3 -> swing lows)
PIVOT_RIGHT = 3
MIN_LINE_SPAN_BARS = 25         # (newer_idx - older_idx) >= 25 -> real base
MIN_SLOPE_PCT_PER_BAR = 0.05    # rising support floor (reject near-flat / falling
                                # bases; gentler than downtrend_breakout's 0.20 — a
                                # higher-lows coil rises more slowly than a crash)
MAX_SLOPE_PCT_PER_BAR = 2.0     # too-steep support = a V-bounce, not a coil
CUTTHROUGH_TOL_PCT = 2.0        # a significant low between anchors may not pierce
                                # the support line by more than this (must be a floor)

# --- lid (flat resistance ceiling) parameters -------------------------------
LID_LOOKBACK_BARS = 130         # window the lid is measured over (~6 months)
LID_FLAT_MAX_SLOPE_PCT = 0.06   # |lid slope| per bar must be flat-ish (horizontal)
LID_MIN_TOUCHES = 2             # >=2 highs must press into the lid band
LID_TOUCH_BAND_PCT = 3.0        # a high within this % of the lid counts as a touch
LID_NEAR_200DMA_PCT = 6.0       # lid must sit within this % of the 200DMA (the lid
                                # IS the falling 200DMA pressing down)
RECLAIM_BUFFER_PCT = 0.5        # close must clear the lid by this to count as reclaim

# --- reclaim / tier parameters ----------------------------------------------
CONFIRM_RECENCY_BARS = 8        # reclaim within last N bars -> fresh confirmed
EXTENDED_RECENCY_BARS = 35      # (8, 35] -> entry passed but still valid (extended)
CONFIRM_CLEARANCE_PCT = 1.0     # price NOW must clear the lid by >=1% to be real
                                # (on-the-lid < 1% => retest, NOT confirmed)
EXTENDED_CLEARANCE_PCT = 12.0   # run this far above the lid => extended (stretched)
DROP_CLEARANCE_PCT = 30.0       # absurdly far above lid => stale, drop
VOL_REJECT = 0.90               # reclaim-bar volume < 0.9x 20d avg => no demand, drop
VOL_STRONG = 1.5

# --- downtrend / junk-rejection stack ---------------------------------------
SMA200_LEN = 200
SMA200_SLOPE_LOOKBACK = 20      # 200DMA must be flat/declining over this lookback
SMA200_MAX_RISE_PCT = 0.5       # 200DMA may rise no more than this over the lookback
                                # (reject names above a RISING 200 — those are the
                                # existing momentum-pullback / continuation setups)
BELOW_200DMA_MIN_PCT = 1.0      # forming: price must still be at least this far BELOW
                                # the 200DMA (the longer downtrend is intact)
DECLINE_DEPTH_FLOOR = 0.10      # major peak -> coil-low >= 10% (real prior decline)
DECLINE_DEPTH_KNIFE_CAP = 0.60  # reject > 60% collapse (falling knife)
RET20_CEIL = 12.0               # 1-mo return not blown-off (a coil, not a vertical)
FORMING_LOW_PCT = -8.0          # close within 8% below the lid -> forming (a coil
                                # pressing the 200DMA can sit a few % under it)
FORMING_HIGH_PCT = RECLAIM_BUFFER_PCT
FORMING_MAX_COIL_RANGE_PCT = 18.0  # recent 20-bar range must be a coil, not wide chop


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


def _sma200_context(hist: "pd.DataFrame") -> dict[str, Any] | None:
    """200DMA value now + slope over the recent lookback. Returns the level, the
    %-change over SMA200_SLOPE_LOOKBACK bars, and whether it is declining/flat."""
    close = hist["close"].astype(float).reset_index(drop=True)
    if len(close) < SMA200_LEN + SMA200_SLOPE_LOOKBACK:
        return None
    sma = close.rolling(SMA200_LEN).mean()
    now = _num(sma.iloc[-1])
    prev = _num(sma.iloc[-1 - SMA200_SLOPE_LOOKBACK])
    if now is None or prev is None or now <= 0 or prev <= 0:
        return None
    rise_pct = (now / prev - 1.0) * 100.0
    return {
        "sma200": now,
        "sma200_rise_pct": rise_pct,
        "declining_or_flat": rise_pct <= SMA200_MAX_RISE_PCT,
    }


def fit_ascending_support(sub: "pd.DataFrame") -> dict[str, Any] | None:
    """Fit the best multi-month RISING support line over the long window across two
    significant pivot lows (higher lows). Returns line geometry, or None. `sub` is
    the LINE_WINDOW_BARS tail, index-reset.

    Mirror of fit_descending_line: the older anchor may sit on the major multi-month
    trough (no recency bias on the older anchor). Selection prefers a long-span,
    well-anchored rising line, and rejects lines a significant intervening low
    pierces (not a true floor)."""
    n = len(sub)
    lows = sub["low"].astype(float).reset_index(drop=True)
    pl = pivot_low(lows, PIVOT_LEFT, PIVOT_RIGHT)
    piv = [(int(i), float(lows.iloc[i])) for i in np.flatnonzero(pl.notna().to_numpy())]
    if len(piv) < 2:
        return None

    best: dict[str, Any] | None = None
    for oi, op in piv:
        for ni, npr in piv:
            if ni - oi < MIN_LINE_SPAN_BARS:
                continue
            if npr <= op:                       # newer low must be HIGHER (ascending)
                continue
            slope = (npr - op) / (ni - oi)
            spb = abs(slope) / ((op + npr) / 2.0) * 100.0
            if spb < MIN_SLOPE_PCT_PER_BAR or spb > MAX_SLOPE_PCT_PER_BAR:
                continue

            def line(x: float, _op=op, _slope=slope, _oi=oi) -> float:
                return _op + _slope * (x - _oi)

            # The line must be a real floor: no significant intervening pivot low
            # may pierce it (below tolerance) between the two anchors.
            if any(oi < pi < ni and pp < line(pi) * (1.0 - CUTTHROUGH_TOL_PCT / 100.0)
                   for pi, pp in piv):
                continue

            # newer anchor must be reasonably recent so the support line is current.
            if (n - 1) - ni > 30:
                continue

            # Prefer the longest-span, highest-anchored rising line (a real
            # multi-month base), not a short shallow tail.
            score = slope * (ni - oi) + op * 0.5
            cand = {
                "older_idx": oi, "newer_idx": ni,
                "older_price": op, "newer_price": npr,
                "slope": slope, "slope_pct_per_bar": spb,
                "score": score,
            }
            if best is None or score > best["score"]:
                best = cand
    return best


def fit_flat_lid(sub: "pd.DataFrame", sma200: float | None) -> dict[str, Any] | None:
    """Find a flat-ish horizontal resistance lid the highs press into, sitting near
    the declining 200DMA. Returns {lid, touches, lid_slope_pct}, or None.

    The lid is the median of the cluster of pivot highs that form a flat ceiling.
    We anchor on the most recent ~LID_LOOKBACK_BARS bars."""
    tail = sub.tail(LID_LOOKBACK_BARS).reset_index(drop=True)
    highs = tail["high"].astype(float).reset_index(drop=True)
    ph = pivot_high(highs, PIVOT_LEFT, PIVOT_RIGHT)
    piv = [(int(i), float(highs.iloc[i])) for i in np.flatnonzero(ph.notna().to_numpy())]
    if len(piv) < LID_MIN_TOUCHES:
        return None

    # Candidate lid level = each pivot high; pick the one with the most touches in a
    # tight band, preferring the level near the 200DMA when available.
    best: dict[str, Any] | None = None
    for _ci, cp in piv:
        in_band = [(pi, pp) for pi, pp in piv
                   if abs(pp / cp - 1.0) * 100.0 <= LID_TOUCH_BAND_PCT]
        if len(in_band) < LID_MIN_TOUCHES:
            continue
        idxs = [pi for pi, _pp in in_band]
        prices = [pp for _pi, pp in in_band]
        lid = float(np.median(prices))
        span = max(idxs) - min(idxs)
        if span < MIN_LINE_SPAN_BARS:
            continue
        # lid must be flat-ish: slope between first and last touch is near-zero.
        first_p = in_band[0][1]; last_p = in_band[-1][1]
        lid_slope_pct = abs(last_p - first_p) / max(span, 1) / lid * 100.0
        if lid_slope_pct > LID_FLAT_MAX_SLOPE_PCT * 4:  # generous; lid is a band
            continue
        # near the 200DMA (the lid IS the falling 200 pressing down) when we have it.
        near_200 = True
        if sma200 is not None and sma200 > 0:
            near_200 = abs(lid / sma200 - 1.0) * 100.0 <= LID_NEAR_200DMA_PCT
        if not near_200:
            continue
        # score: more touches + flatter + nearer the 200DMA.
        score = len(in_band) * 10.0 - lid_slope_pct
        if sma200 is not None and sma200 > 0:
            score -= abs(lid / sma200 - 1.0) * 100.0
        cand = {"lid": lid, "touches": len(in_band),
                "lid_slope_pct": lid_slope_pct, "score": score}
        if best is None or score > best["score"]:
            best = cand
    return best


def _result(symbol, signal, pattern, sub, geom, *, lid, line_now, clearance_pct,
            reclaim_idx, decline, ret20, rsi_now, rsi_rising, vols, vol_ratio,
            above_emas, sma200, dist_to_200dma_pct, bars_since=None):
    dates = pd.to_datetime(sub["date"]).reset_index(drop=True)
    oi = geom["older_idx"]; ni = geom["newer_idx"]
    blend = min(decline * 100.0, 30.0)
    if vol_ratio:
        blend += min(max(vol_ratio - 1.0, 0.0) * 20.0, 20.0)
    if rsi_rising:
        blend += 10.0
    if pattern == "confirmed":
        blend += 15.0
    elif pattern == "forming":
        blend += 5.0
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
        "lid": round(lid, 2) if lid is not None else None,
        "reclaim_date": str(dates.iloc[reclaim_idx].date()) if reclaim_idx is not None else None,
        "line_now": round(line_now, 2),
        "clearance_pct": round(clearance_pct, 2),
        "bars_since_reclaim": bars_since,
        "decline_depth_pct": round(decline * 100.0, 2),
        "ret20_pct": round(ret20, 2) if ret20 is not None else None,
        "vol_ratio": round(vol_ratio, 2) if vol_ratio else None,
        "rsi14": round(rsi_now, 1) if rsi_now is not None else None,
        "rsi_rising": rsi_rising,
        "above_rising_emas": above_emas,
        "sma200": round(sma200, 2) if sma200 is not None else None,
        "dist_to_200dma_pct": round(dist_to_200dma_pct, 2) if dist_to_200dma_pct is not None else None,
        "last_close": round(float(sub["close"].iloc[-1]), 2),
    }


def scan_ascending_reversal(ticker: str, asof: str | None = None,
                            hist: "pd.DataFrame | None" = None) -> dict[str, Any] | None:
    """Detect an ascending reversal-coil (higher lows into a declining 200DMA lid)
    on one ticker's daily bars.

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

        # 200DMA context — the DEFINING gate. Computed on the FULL history (needs
        # 200+20 bars). Reject names above a rising 200 (momentum-pullback setups).
        smactx = _sma200_context(hist)
        if smactx is None:
            return None
        sma200 = smactx["sma200"]
        if not smactx["declining_or_flat"]:
            return None

        sub = hist.tail(LINE_WINDOW_BARS).reset_index(drop=True)
        n = len(sub)
        closes = sub["close"].astype(float).reset_index(drop=True)
        highs = sub["high"].astype(float).reset_index(drop=True)
        lows = sub["low"].astype(float).reset_index(drop=True)
        vols = sub["volume"].astype(float).reset_index(drop=True)
        last_close = float(closes.iloc[-1])
        if last_close <= 0:
            return None
        dist_to_200dma_pct = (last_close / sma200 - 1.0) * 100.0 if sma200 > 0 else None

        # EMA context. The downtrend_breakout reject is `above_rising_emas` (an
        # uptrend riding rising EMAs is a continuation). Inverted appropriately: this
        # setup is a base UNDER a declining 200, so a bearish/neutral EMA stack is
        # EXPECTED. We keep the same field for parity and use it as a sanity flag in
        # the forming tier; the 200DMA gate is what defines the downtrend here.
        ema20 = float(closes.ewm(span=20, adjust=False).mean().iloc[-1])
        ema50 = float(closes.ewm(span=50, adjust=False).mean().iloc[-1])
        above_rising_emas = (last_close > ema20 and ema20 > ema50)

        # Real prior decline depth: major peak over the window -> coil low.
        window_peak = float(highs.max())
        coil_low = float(lows.tail(LID_LOOKBACK_BARS).min())
        decline = (window_peak - coil_low) / window_peak if window_peak > 0 else 0.0
        if decline < DECLINE_DEPTH_FLOOR or decline > DECLINE_DEPTH_KNIFE_CAP:
            return None

        # RSI / vol labels.
        rsi_s = _rsi(closes)
        rsi_now = _num(rsi_s.iloc[-1]) if len(rsi_s) else None
        rsi_prev = _num(rsi_s.iloc[-4]) if len(rsi_s) > 4 else None
        rsi_rising = (rsi_now is not None and rsi_prev is not None and rsi_now > rsi_prev)

        # Rising support line (higher lows) + flat lid near the 200DMA. Both are
        # required for any tier — this is an ascending triangle, not a random base.
        geom = fit_ascending_support(sub)
        if geom is None:
            return None
        lidfit = fit_flat_lid(sub, sma200)
        if lidfit is None:
            return None
        lid = lidfit["lid"]
        if lid <= 0:
            return None

        clearance_pct = (last_close / lid - 1.0) * 100.0

        # blown-off vertical reject (a coil rises slowly; a 1-mo +12% is not a coil).
        if ret20 is not None and ret20 > RET20_CEIL:
            return None

        # ---------------- FORMING (no reclaim yet) --------------------------
        # Price still coiling UNDER the lid / 200DMA — the longer downtrend intact.
        if clearance_pct < FORMING_HIGH_PCT:
            if not (FORMING_LOW_PCT <= clearance_pct < FORMING_HIGH_PCT):
                return None
            # must still be meaningfully BELOW the declining 200DMA.
            if dist_to_200dma_pct is None or dist_to_200dma_pct > -BELOW_200DMA_MIN_PCT:
                return None
            # NOTE: unlike downtrend_breakout, we DON'T reject `above_rising_emas`
            # here. That reject kills genuine uptrend-pullbacks riding rising EMAs —
            # but THIS setup is defined by price sitting under a DECLINING 200DMA, so
            # a name there with rising SHORT EMAs is exactly the early coil we want,
            # not a continuation. The 200DMA gate IS the downtrend filter; the
            # uptrend-continuation reject is handled by the rising-200 rejection up
            # top (a real uptrend has a rising 200) + the RET20_CEIL blow-off cap.
            # coil gate: a tight 20-bar range, not wide chop.
            recent_range_pct = (float(highs.tail(20).max()) - float(lows.tail(20).min())) / last_close * 100.0
            if recent_range_pct > FORMING_MAX_COIL_RANGE_PCT:
                return None
            line_now = float(geom["older_price"] + geom["slope"] * ((n - 1) - geom["older_idx"]))
            return _result(symbol, "ascending_reversal_forming", "forming", sub, geom,
                           lid=lid, line_now=line_now, clearance_pct=clearance_pct,
                           reclaim_idx=None, decline=decline, ret20=ret20,
                           rsi_now=rsi_now, rsi_rising=rsi_rising, vols=vols,
                           vol_ratio=None, above_emas=above_rising_emas,
                           sma200=sma200, dist_to_200dma_pct=dist_to_200dma_pct)

        # ---------------- RECLAIM FOUND: confirmed / extended / retest ------
        # Price has closed above the lid. Locate the first decisive reclaim AFTER the
        # coil is established — i.e. after the support line's NEWER anchor (mirrors
        # downtrend_breakout searching range(ni+1, n)). Searching from the coil
        # forward avoids matching an early close that was still on the way DOWN
        # through the lid level during the prior decline.
        reclaim_idx = None
        lid_window_start = max(geom["newer_idx"] + 1, n - LID_LOOKBACK_BARS)
        for x in range(lid_window_start, n):
            if closes.iloc[x] > lid * (1.0 + RECLAIM_BUFFER_PCT / 100.0):
                reclaim_idx = x
                break
        if reclaim_idx is None:
            return None
        bars_since = (n - 1) - reclaim_idx

        # reclaim-bar volume (demand).
        v20 = float(vols.iloc[max(0, reclaim_idx - 20):reclaim_idx].mean()) if reclaim_idx >= 1 else float(vols.iloc[:reclaim_idx + 1].mean())
        bv = float(vols.iloc[reclaim_idx])
        vol_ratio = (bv / v20) if v20 and v20 > 0 else None

        # stale / blown-off-distance reject.
        if bars_since > EXTENDED_RECENCY_BARS:
            return None
        if clearance_pct > DROP_CLEARANCE_PCT:
            return None

        # RETEST tier: price sits ON the lid (reclaimed but pulled back to within
        # CONFIRM_CLEARANCE_PCT). NOT confirmed.
        if clearance_pct < CONFIRM_CLEARANCE_PCT:
            if bars_since <= EXTENDED_RECENCY_BARS and (vol_ratio is None or vol_ratio >= VOL_REJECT):
                return _result(symbol, "ascending_reversal_retest", "retest", sub, geom,
                               lid=lid, line_now=lid, clearance_pct=clearance_pct,
                               reclaim_idx=reclaim_idx, decline=decline, ret20=ret20,
                               rsi_now=rsi_now, rsi_rising=rsi_rising, vols=vols,
                               vol_ratio=vol_ratio, above_emas=above_rising_emas,
                               sma200=sma200, dist_to_200dma_pct=dist_to_200dma_pct,
                               bars_since=bars_since)
            return None

        # Real clearance -> confirmed or extended. Volume demand required.
        if vol_ratio is None or vol_ratio < VOL_REJECT:
            return None

        if bars_since <= CONFIRM_RECENCY_BARS and clearance_pct <= EXTENDED_CLEARANCE_PCT:
            pattern = "confirmed"
        else:
            # entry passed: reclaim older (>8 bars) or price run far above the lid.
            pattern = "extended"

        return _result(symbol, "ascending_reversal", pattern, sub, geom,
                       lid=lid, line_now=lid, clearance_pct=clearance_pct,
                       reclaim_idx=reclaim_idx, decline=decline, ret20=ret20,
                       rsi_now=rsi_now, rsi_rising=rsi_rising, vols=vols,
                       vol_ratio=vol_ratio, above_emas=above_rising_emas,
                       sma200=sma200, dist_to_200dma_pct=dist_to_200dma_pct,
                       bars_since=bars_since)
    except Exception:
        return None


def generate_ascending_reversals(tickers: list[str], asof: str | None = None,
                                 max_results: int = 10) -> list[dict[str, Any]]:
    """Scan a list of tickers, return up to `max_results` ascending-reversal signals.

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
        sig = scan_ascending_reversal(sym, asof=asof)
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
    sample = ["DIS", "NKE", "NVDA"]
    found = generate_ascending_reversals(sample, max_results=40)
    print(f"{len(found)} signal(s) of {len(sample)} scanned:")
    for sig in found:
        print(json.dumps(sig, default=str))
