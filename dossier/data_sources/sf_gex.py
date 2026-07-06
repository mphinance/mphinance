"""
data_sources/sf_gex.py
----------------------
Gamma Exposure (dealer positioning) — net GEX per strike, gamma-flip level,
call/put walls, and the positive/negative-gamma regime.

Folded into the dossier from StrikeForge's `scanner/gex.py` (StrikeForge Tier-1,
see DAILY_REVIEW_PLAN.md), which itself was ported from TraderDaddy-Pro's
production `gammaExposure.ts`. This adds a dealer-positioning leg the dossier
lacks; it is the desk-grade replacement for "max pain" folklore. Instead of
guessing where price pins, GEX estimates how dealer hedging will behave.

Method (matches TraderDaddy / StrikeForge):
  - Per contract, dollar gamma per 1% move = OI * gamma * (spot*0.01) * spot * 100.
  - Calls add positive GEX, puts subtract it.
  - net_gex is summed per strike across the scanned expiry.
  - total_gex > 0 => positive-gamma regime: dealers sell rips / buy dips, moves
                     get DAMPENED, price mean-reverts (good for range/credit).
  - total_gex < 0 => negative-gamma regime: dealers chase, moves AMPLIFY
                     (trend/breakout risk; caution for premium sellers).
  - gamma flip (zero-gamma) level = price where net_gex crosses zero (linear
    interp, crossing nearest spot); a soft support/resistance / regime boundary.
  - call wall = strike with the largest positive net_gex at/above spot (resistance);
    put wall = strike with the largest negative net_gex at/below spot (support).

ADAPTATION / IMPORT REWIRING vs the StrikeForge original:
  1. `from scanner.greeks import bs_gamma` -> inlined `_bs_gamma` here (a ~10-line
     pure-scipy Black-Scholes gamma). StrikeForge derives gamma so GEX works on
     the yfinance fallback. We keep that fallback, but the LIVE path prefers
     Tradier's exchange-provided gamma (chains pulled with greeks=true), so the
     BS derivation only fires when a contract is missing greeks.
  2. StrikeForge's `compute_gex(contracts, spot)` took a pre-shaped contract list.
     We keep that exact function intact, and add `gex_read(ticker)` which sources
     the chain via `gamma_pin_screener.py`'s Tradier helpers (TRADIER_API_KEY)
     and reshapes Tradier rows -> the {strike,type,open_interest,iv,dte,gamma}
     shape `compute_gex` expects.

Fails soft everywhere: no key / no chain / bad data -> `gex_read` returns None;
`compute_gex` returns an empty-but-valid dict. Nothing raises.

Public API
----------
compute_gex(contracts, spot, r=0.045) -> dict
    Pure GEX math on a pre-shaped contract list (StrikeForge-native).
gex_read(ticker, expiry=None) -> dict | None
    Dossier entry point: fetch chain -> compute -> compact dict with keys
    gamma_flip, call_wall, put_wall, regime, net_gex (plus spot, expiry, etc.).
    Returns None when no GEX read is possible.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from typing import Optional

try:
    from dossier.utils.validate_api import safe_tradier_quote
except ImportError:
    def safe_tradier_quote(response, ticker: str = ""):
        try:
            data = response.json()
        except Exception:
            return None
        quotes = data.get("quotes") if isinstance(data, dict) else None
        if not isinstance(quotes, dict):
            return None
        quote = quotes.get("quote")
        if isinstance(quote, list):
            quote = quote[0] if quote else None
        return quote if isinstance(quote, dict) else None

CONTRACT_MULTIPLIER = 100


# ─────────────────────────────────────────────────────────────────────────────
# Inlined Black-Scholes gamma (replaces `from scanner.greeks import bs_gamma`)
# ─────────────────────────────────────────────────────────────────────────────

def _bs_gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes gamma (identical for calls and puts). Pure scipy.

    S=spot, K=strike, T=years to expiry, r=rate, sigma=annualised IV (fraction).
    Mirrors scanner.greeks.bs_gamma (q=0 carry). Raises ValueError on bad inputs;
    callers guard with try/except.
    """
    from scipy.stats import norm  # local import: keep module import cheap

    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        raise ValueError(f"Invalid BS inputs: S={S}, K={K}, T={T}, sigma={sigma}")
    sqrt_T = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
    return float(norm.pdf(d1) / (S * sigma * sqrt_T))


# ─────────────────────────────────────────────────────────────────────────────
# Core GEX math (ported verbatim from StrikeForge scanner/gex.py)
# ─────────────────────────────────────────────────────────────────────────────

def _num(v) -> Optional[float]:
    try:
        if v is None:
            return None
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _is_call(row: dict) -> bool:
    return str(row.get("type", "")).strip().lower().startswith("c")


def compute_gex(contracts: list[dict], spot: float, r: float = 0.045) -> dict:
    """
    Gamma-exposure profile from a set of option contracts.

    contracts : list of dicts with at least {strike, type, open_interest, iv, dte}.
                iv is a fraction (0.30 = 30%); dte is calendar days. A supplied
                `gamma` is preferred; otherwise gamma is derived from iv + dte.
                Contracts from multiple expiries aggregate by strike.
    spot      : underlying price.

    Returns a JSON-safe dict: per-strike GEX, total_gex, gamma_flip, call/put
    walls, max-gamma strike, put/call GEX ratio, regime, and a plain-English read.
    """
    s = _num(spot)
    if not s or s <= 0 or not contracts:
        return _empty(s)

    one_pct = s * 0.01
    by_strike: dict[float, dict] = defaultdict(
        lambda: {"strike": 0.0, "call_gex": 0.0, "put_gex": 0.0,
                 "net_gex": 0.0, "call_oi": 0.0, "put_oi": 0.0})

    for c in contracts:
        k = _num(c.get("strike"))
        oi = _num(c.get("open_interest")) or 0.0
        iv = _num(c.get("iv"))
        dte = _num(c.get("dte"))
        if k is None or k <= 0 or oi <= 0:
            continue
        # Prefer a supplied gamma; else derive it from IV + DTE.
        gamma = _num(c.get("gamma"))
        if gamma is None:
            if iv is None or iv <= 0 or dte is None or dte <= 0:
                continue
            try:
                gamma = _bs_gamma(s, k, dte / 365.0, r, iv)
            except Exception:
                continue
        if gamma is None or not math.isfinite(gamma):
            continue

        dollar_gamma = oi * gamma * one_pct * s * CONTRACT_MULTIPLIER
        slot = by_strike[k]
        slot["strike"] = k
        if _is_call(c):
            slot["call_gex"] += dollar_gamma
            slot["call_oi"] += oi
        else:
            slot["put_gex"] += -dollar_gamma     # puts subtract (dealer short gamma)
            slot["put_oi"] += oi
        slot["net_gex"] = slot["call_gex"] + slot["put_gex"]

    strikes = sorted(by_strike.values(), key=lambda x: x["strike"])
    if not strikes:
        return _empty(s)

    total_gex = sum(x["net_gex"] for x in strikes)
    total_call = sum(x["call_gex"] for x in strikes)
    total_put = sum(x["put_gex"] for x in strikes)

    gamma_flip = _gamma_flip(strikes, s)
    call_wall = _call_wall(strikes, s)
    put_wall = _put_wall(strikes, s)
    max_gamma = max(strikes, key=lambda x: abs(x["net_gex"]))["strike"] if strikes else None

    regime, read = _interpret(total_gex)
    pc_ratio = (abs(total_put) / total_call) if total_call else None

    return {
        "spot": round(s, 4),
        "total_gex": total_gex,
        "total_call_gex": total_call,
        "total_put_gex": total_put,
        "gamma_flip": gamma_flip,
        "call_wall": call_wall,
        "put_wall": put_wall,
        "max_gamma_strike": max_gamma,
        "put_call_gex_ratio": round(pc_ratio, 4) if pc_ratio is not None else None,
        "regime": regime,
        "read": read,
        "by_strike": [
            {"strike": x["strike"], "net_gex": x["net_gex"],
             "call_gex": x["call_gex"], "put_gex": x["put_gex"],
             "call_oi": x["call_oi"], "put_oi": x["put_oi"]}
            for x in strikes
        ],
    }


def _gamma_flip(strikes: list[dict], spot: float) -> Optional[float]:
    """Zero-gamma level: net_gex sign change, linearly interpolated, nearest spot."""
    if len(strikes) < 2:
        return None
    best = None
    for a, b in zip(strikes, strikes[1:]):
        na, nb = a["net_gex"], b["net_gex"]
        if (na > 0 > nb) or (na < 0 < nb):
            ratio = abs(na) / (abs(na) + abs(nb)) if (abs(na) + abs(nb)) else 0.0
            level = a["strike"] + ratio * (b["strike"] - a["strike"])
            dist = abs(level - spot)
            if best is None or dist < best[1]:
                best = (level, dist)
    return round(best[0], 2) if best else None


def _call_wall(strikes: list[dict], spot: float) -> Optional[float]:
    above = [x for x in strikes if x["strike"] >= spot and x["net_gex"] > 0]
    return max(above, key=lambda x: x["net_gex"])["strike"] if above else None


def _put_wall(strikes: list[dict], spot: float) -> Optional[float]:
    below = [x for x in strikes if x["strike"] <= spot and x["net_gex"] < 0]
    return min(below, key=lambda x: x["net_gex"])["strike"] if below else None


def _interpret(total_gex: float) -> tuple[str, str]:
    if total_gex > 0:
        return ("positive", "Positive gamma: dealers dampen moves (sell rips, buy "
                            "dips). Expect mean reversion and a tighter range.")
    if total_gex < 0:
        return ("negative", "Negative gamma: dealers amplify moves (chase). Expect "
                           "bigger swings and trend/breakout risk.")
    return ("neutral", "Neutral gamma: little hedging pressure either way.")


def _empty(spot) -> dict:
    return {
        "spot": spot, "total_gex": 0.0, "total_call_gex": 0.0, "total_put_gex": 0.0,
        "gamma_flip": None, "call_wall": None, "put_wall": None,
        "max_gamma_strike": None, "put_call_gex_ratio": None,
        "regime": "neutral", "read": "Not enough data for a GEX read.",
        "by_strike": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Dossier entry point — source the chain via the gamma_pin_screener Tradier layer
# ─────────────────────────────────────────────────────────────────────────────

def _tradier_helpers():
    """Import the Tradier chain helpers from the gamma-pin screener.

    Returns (get_options_expirations, get_options_chain, find_nearest_expiration)
    or None on any import failure (degrade — gex_read then returns None).
    """
    try:
        from dossier.gamma_pin_screener import (
            get_options_expirations,
            get_options_chain,
            find_nearest_expiration,
        )
        return get_options_expirations, get_options_chain, find_nearest_expiration
    except Exception:
        try:
            from gamma_pin_screener import (  # fallback when run outside the package
                get_options_expirations,
                get_options_chain,
                find_nearest_expiration,
            )
            return get_options_expirations, get_options_chain, find_nearest_expiration
        except Exception:
            return None


def _shape_contract(opt: dict, expiry: str) -> Optional[dict]:
    """Map one Tradier option row -> the dict shape compute_gex consumes.

    Tradier (greeks=true) gives per-contract greeks incl. gamma and mid_iv.
    We pass gamma straight through when present; otherwise we hand compute_gex
    the iv + dte so it can derive gamma via _bs_gamma.
    """
    strike = opt.get("strike")
    oi = opt.get("open_interest", 0) or 0
    opt_type = str(opt.get("option_type", "")).lower()  # 'call' / 'put'
    if strike is None or oi <= 0 or opt_type not in ("call", "put"):
        return None

    greeks = opt.get("greeks") or {}
    gamma = greeks.get("gamma")
    iv = greeks.get("mid_iv") or greeks.get("smv_vol") or opt.get("implied_volatility")

    # DTE from the contract's own expiration date if present, else the scan expiry.
    exp_str = opt.get("expiration_date") or expiry
    dte = None
    if exp_str:
        try:
            d = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = max((d - datetime.now().date()).days, 0)
        except (ValueError, TypeError):
            dte = None

    return {
        "strike": strike,
        "type": opt_type,
        "open_interest": oi,
        "iv": iv,
        "dte": dte,
        "gamma": gamma,
    }


def gex_read(ticker: str, expiry: Optional[str] = None) -> dict | None:
    """Dealer-positioning GEX read for one ticker.

    Fetches the option chain (Tradier, via the gamma_pin_screener helpers),
    reshapes it, and runs `compute_gex`. Targets the nearest expiry to `expiry`
    (defaults to ~today, i.e. the front expiration) when not given.

    Returns a compact dict on success:
        {ticker, spot, expiry, regime, net_gex, gamma_flip, call_wall, put_wall,
         total_call_gex, total_put_gex, put_call_gex_ratio, max_gamma_strike, read}
    or None when no read is possible (no key, no chain, no usable data). NEVER raises.
    """
    try:
        helpers = _tradier_helpers()
        if helpers is None:
            return None
        get_expirations, get_chain, find_nearest = helpers

        target = expiry or datetime.now().strftime("%Y-%m-%d")
        expirations = get_expirations(ticker)
        if not expirations:
            return None
        exp_date = find_nearest(expirations, target)
        # find_nearest only accepts a match within 3 days; if the requested target
        # is far out (e.g. default = today on a weekend), fall back to the first
        # available expiry so we still get a read.
        if not exp_date:
            exp_date = expirations[0]

        raw_chain = get_chain(ticker, exp_date)
        if not raw_chain:
            return None

        # Spot: Tradier embeds the underlying via greeks? No — derive from the
        # chain's ATM, or pull a quote. Cheapest reliable spot here is a quote.
        spot = _fetch_spot(ticker)
        if spot is None:
            return None

        contracts = []
        for opt in raw_chain:
            if not isinstance(opt, dict):
                continue
            shaped = _shape_contract(opt, exp_date)
            if shaped is not None:
                contracts.append(shaped)
        if not contracts:
            return None

        gex = compute_gex(contracts, spot)
        if not gex or not gex.get("by_strike"):
            return None

        return {
            "ticker": ticker.upper(),
            "spot": gex.get("spot"),
            "expiry": exp_date,
            "regime": gex.get("regime"),
            "net_gex": gex.get("total_gex"),
            "gamma_flip": gex.get("gamma_flip"),
            "call_wall": gex.get("call_wall"),
            "put_wall": gex.get("put_wall"),
            "total_call_gex": gex.get("total_call_gex"),
            "total_put_gex": gex.get("total_put_gex"),
            "put_call_gex_ratio": gex.get("put_call_gex_ratio"),
            "max_gamma_strike": gex.get("max_gamma_strike"),
            "read": gex.get("read"),
        }
    except Exception:
        # Hard degrade contract — gex_read must never raise.
        return None


def _fetch_spot(ticker: str) -> Optional[float]:
    """Last/close price for the underlying via Tradier quotes. None on any error."""
    try:
        import requests
        from dossier.gamma_pin_screener import TRADIER_BASE, _tradier_headers
    except Exception:
        try:
            import requests  # noqa: F811
            from gamma_pin_screener import TRADIER_BASE, _tradier_headers
        except Exception:
            return None
    try:
        resp = requests.get(
            f"{TRADIER_BASE}/markets/quotes",
            params={"symbols": ticker},
            headers=_tradier_headers(), timeout=10)
        if resp.status_code != 200:
            return None
        q = safe_tradier_quote(resp, ticker)
        if not q:
            return None
        price = q.get("last") or q.get("close")
        return float(price) if price else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Light self-test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    # 1) Pure-math smoke test (no network): synthetic chain around spot=100.
    print("=== compute_gex (synthetic) ===")
    synthetic = [
        {"strike": 95, "type": "put", "open_interest": 5000, "iv": 0.25, "dte": 7},
        {"strike": 100, "type": "call", "open_interest": 8000, "iv": 0.22, "dte": 7},
        {"strike": 100, "type": "put", "open_interest": 6000, "iv": 0.24, "dte": 7},
        {"strike": 105, "type": "call", "open_interest": 9000, "iv": 0.23, "dte": 7},
        {"strike": 110, "type": "call", "open_interest": 3000, "iv": 0.26, "dte": 7},
    ]
    g = compute_gex(synthetic, 100.0)
    print(json.dumps({k: v for k, v in g.items() if k != "by_strike"}, indent=2))

    # 2) Live reads (need TRADIER_API_KEY + network).
    for tk in ("SPY", "NVDA"):
        print(f"\n=== gex_read({tk}) ===")
        print(json.dumps(gex_read(tk), indent=2, default=str))
