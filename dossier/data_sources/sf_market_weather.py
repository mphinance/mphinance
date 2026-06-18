"""
data_sources/sf_market_weather.py
----------------------------------
VIX / VIX3M / VVIX term-structure "should I trade today" macro read.

Folded into the dossier from StrikeForge's `scanner/market_weather.py`
(StrikeForge Tier-1, see DAILY_REVIEW_PLAN.md). This is a strict port: the
upstream module had NO `scanner.*` dependencies (it pulls VIX levels straight
from yfinance), so nothing needed inlining — only the public surface was
adapted.

Why this over the dossier's level-only `market_regime.py`: that one keys off the
absolute VIX level alone and ignores the term structure. The term structure is
the better "is the market scared" tell — when the front-month VIX trades ABOVE
the 3-month (backwardation), near-term protection is being bid up, which is a
caution/avoid signal even when the absolute level looks ordinary.

Regime ladder (absolute VIX):
    VIX < 15            calm
    15 <= VIX < 22      normal
    22 <= VIX < 30      elevated
    VIX >= 30           panic

Verdict ladder (regime + term structure):
    panic                       -> avoid
    backwardation AND elevated  -> avoid
    backwardation OR elevated   -> caution
    calm/normal contango        -> trade

Resilience contract: fail-OPEN and NEVER raises. Any fetch failure returns an
`available=False` payload with verdict 'trade' so a broken weather read can't
suppress the rest of the daily review. Cached in-process with a short TTL.

Public API
----------
market_weather(force_refresh=False) -> dict
    Dossier-shaped entry point. Keys: regime, vix, vix3m, vvix, term_structure,
    spread, verdict, trade_ok (bool), available, headline.
get_market_weather(force_refresh=False) -> dict
    StrikeForge-compatible alias (same payload minus the dossier convenience
    keys `term_structure` / `trade_ok`, which are added by `market_weather`).
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Thresholds (adapted from StrikeForge / mur vix_engine GravityConfig)
# ─────────────────────────────────────────────────────────────────────────────

_VIX_CALM = 15.0       # below this = calm / complacent
_VIX_NORMAL = 22.0     # 15-22 = ordinary chop
_VIX_ELEVATED = 30.0   # 22-30 = elevated; >=30 = panic

# yfinance symbols for the VIX cash index, the 3-month forward VIX, and VVIX.
_VIX_SYMBOL = "^VIX"
_VIX3M_SYMBOL = "^VIX3M"
_VVIX_SYMBOL = "^VVIX"   # vol-of-vol; informational only, does not gate verdict

# In-process cache TTL. VIX doesn't move enough intraday to refetch per call.
_CACHE_TTL_SEC = 120.0

_cache: dict | None = None
_cache_ts: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Classification
# ─────────────────────────────────────────────────────────────────────────────

def _classify_regime(vix: float) -> str:
    """Map an absolute VIX level to a regime label."""
    if vix < _VIX_CALM:
        return "calm"
    if vix < _VIX_NORMAL:
        return "normal"
    if vix < _VIX_ELEVATED:
        return "elevated"
    return "panic"


def _verdict_for(regime: str, backwardation: bool) -> str:
    """Fold regime + term-structure into a 'trade'/'caution'/'avoid' verdict."""
    if regime == "panic":
        return "avoid"
    if backwardation and regime == "elevated":
        return "avoid"
    if backwardation or regime in ("elevated",):
        return "caution"
    return "trade"


def _headline(vix: float, regime: str, structure: str, verdict: str) -> str:
    """A short banner phrase. No em dashes."""
    if verdict == "avoid":
        if structure == "backwardation":
            return f"Curve inverted, VIX {vix:.1f}. Sit on your hands today."
        return f"VIX {vix:.1f} and the market is scared. Not a trading day."
    if verdict == "caution":
        if structure == "backwardation":
            return "Term structure flipped to backwardation. Trade small, size down."
        return f"VIX {vix:.1f} is elevated. Edge is thinner, be picky."
    return f"Calm contango, VIX {vix:.1f}. Green light."


# ─────────────────────────────────────────────────────────────────────────────
# Fetch (yfinance — VIX cash is not on Tradier sandbox)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_last(symbol: str) -> float | None:
    """Latest close for a yfinance index symbol, or None on any error. Never raises."""
    try:
        import yfinance as yf

        t = yf.Ticker(symbol)
        # fast_info is cheap and usually populated for index symbols.
        try:
            fi = t.fast_info
            price = getattr(fi, "last_price", None)
            if price is not None:
                price = float(price)
                if price == price and price > 0:  # not NaN, positive
                    return price
        except Exception:
            pass

        # Fallback: short history pull.
        hist = t.history(period="5d", interval="1d")
        if hist is not None and not hist.empty and "Close" in hist.columns:
            val = float(hist["Close"].dropna().iloc[-1])
            if val == val and val > 0:
                return val
    except Exception as exc:
        logger.warning("sf_market_weather: fetch %s failed: %s", symbol, exc)
    return None


def _unavailable() -> dict:
    """Fail-open payload. Verdict 'trade' so a broken read never suppresses."""
    return {
        "available": False,
        "vix": None,
        "vix3m": None,
        "vvix": None,
        "spread": None,
        "structure": "unknown",
        "regime": "unknown",
        "verdict": "trade",
        "headline": "market weather unavailable",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_market_weather(force_refresh: bool = False) -> dict:
    """Fetch + classify the VIX term-structure read. Non-blocking, fail-open.

    Returns the StrikeForge-native payload (see module docstring). Cached
    in-process for `_CACHE_TTL_SEC`. NEVER raises.
    """
    global _cache, _cache_ts

    now = time.time()
    if not force_refresh and _cache is not None and (now - _cache_ts) < _CACHE_TTL_SEC:
        return _cache

    try:
        vix = _fetch_last(_VIX_SYMBOL)
        vix3m = _fetch_last(_VIX3M_SYMBOL)
        vvix = _fetch_last(_VVIX_SYMBOL)  # informational; never gates the verdict

        if vix is None:
            result = _unavailable()
            _cache, _cache_ts = result, now
            return result

        if vix3m is None:
            # VIX3M missing on some providers: degrade to contango (no signal).
            structure = "contango"
            spread = None
            backwardation = False
        else:
            spread = round(vix - vix3m, 2)
            backwardation = vix > vix3m
            structure = "backwardation" if backwardation else "contango"

        regime = _classify_regime(vix)
        verdict = _verdict_for(regime, backwardation)
        headline = _headline(vix, regime, structure, verdict)

        result = {
            "available": True,
            "vix": round(vix, 2),
            "vix3m": round(vix3m, 2) if vix3m is not None else None,
            "vvix": round(vvix, 2) if vvix is not None else None,
            "spread": spread,
            "structure": structure,
            "regime": regime,
            "verdict": verdict,
            "headline": headline,
        }
        _cache, _cache_ts = result, now
        return result

    except Exception as exc:
        logger.warning("sf_market_weather: unexpected failure (%s) — failing open", exc)
        result = _unavailable()
        _cache, _cache_ts = result, now
        return result


def market_weather(force_refresh: bool = False) -> dict:
    """Dossier-shaped market-weather read.

    Wraps `get_market_weather` and adds two convenience keys the dossier asked
    for:
      - `term_structure`: alias of `structure` ('contango'/'backwardation'/'unknown')
      - `trade_ok`: bool, True unless the verdict is 'avoid' (the trade-gate flag)

    Returns (keys): regime, vix, vix3m, vvix, spread, term_structure, structure,
    verdict, trade_ok, available, headline. NEVER raises.
    """
    try:
        w = dict(get_market_weather(force_refresh=force_refresh))
    except Exception as exc:  # belt-and-suspenders; get_market_weather is fail-open
        logger.warning("sf_market_weather.market_weather: failing open (%s)", exc)
        w = _unavailable()
    w["term_structure"] = w.get("structure", "unknown")
    w["trade_ok"] = w.get("verdict") != "avoid"
    return w


# ─────────────────────────────────────────────────────────────────────────────
# Light self-test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("=== market_weather() ===")
    print(json.dumps(market_weather(), indent=2))
