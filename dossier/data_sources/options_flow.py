"""
Options Flow — Once-Daily Tradier Snapshot
==========================================

A daily-batch reproduction of TD Pro's unusual-options-activity detector,
ported for the Ghost Alpha Dossier. Pulls the options chain (with greeks) for
each ticker across 0-90 DTE, filters contracts on quality thresholds, and
scores each survivor with the STATIC unusual-activity formula.

What this faithfully reproduces (from TD Pro):
  - Contract pre-filter   → backend/src/jobs/helpers/contractFiltering.ts
  - Tiered floors         → backend/src/services/filterConfig.ts
  - Static score (0-100+) → backend/src/services/unusualActivity.ts
        Vol/OI (max 40) + premium (max 30) + spread% (max 15) + DTE (max 15)
        + contra-day (+10) + fresh-position vol>OI (+10)

What is HONESTLY lost in a once-daily EOD batch (and why we label accordingly):
  - True SWEEP / BLOCK / SPLIT classification needs intraday Time & Sales.
    → We label trade type "DAILY_VOLUME", NOT a fake "SWEEP".
  - Reliable buy/sell sentiment needs live (not stale EOD) quotes.
    → Sentiment is emitted as low-confidence ("inferred").
  - OI posts T+1, so a same-morning run compares prior-day volume to fresh OI.

The load-bearing terms for a daily watchlist are Vol/OI and premium-skew; those
survive the batch translation intact.

Reuses the EXISTING Tradier client in dossier/gamma_pin_screener.py
(`_tradier_headers`, `get_options_expirations`, `get_options_chain`) — does NOT
rewrite a Tradier client.

Contract: NEVER raises. Every entry point returns None / [] and degrades.

    python -m dossier.data_sources.options_flow      # self-test on a few tickers

© mphinance — daily flow, honest labels.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# Ensure project root is importable so we can reuse the gamma screener's client.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dossier.gamma_pin_screener import (
        _tradier_headers,
        get_options_chain,
        get_options_expirations,
    )
    TRADIER_BASE = "https://api.tradier.com/v1"
except Exception as _imp_err:  # pragma: no cover — import guard, never fatal
    print(f"  [ERR] options_flow: could not import Tradier client: {_imp_err}")
    _tradier_headers = None  # type: ignore[assignment]
    get_options_chain = None  # type: ignore[assignment]
    get_options_expirations = None  # type: ignore[assignment]
    TRADIER_BASE = "https://api.tradier.com/v1"

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


# ═══════════════════════════════════════════════════════════════════
# ████  TIERED FILTER FLOORS — ported from filterConfig.ts  ████
# ═══════════════════════════════════════════════════════════════════
# Market-cap tier → {minPremium, minVolumeOI, minOI}. Mirrors the TD Pro
# FILTER_CONFIGS table 1:1 (mega / large / small).
FILTER_CONFIGS: dict[int, dict] = {
    1: {  # Mega-Cap / Indices ($200B+): SPY, QQQ, AAPL, NVDA, MSFT...
        "min_premium": 25_000,
        "min_volume_oi": 1.5,
        "min_oi": 100,
        "tier_name": "Mega-Cap",
    },
    2: {  # Large-Cap ($10B-$200B): PLTR, COIN, AMD, HOOD, SOFI...
        "min_premium": 20_000,
        "min_volume_oi": 1.35,
        "min_oi": 50,
        "tier_name": "Large-Cap",
    },
    3: {  # Small/Mid-Cap (<$10B): squeeze plays, early flows
        "min_premium": 15_000,
        "min_volume_oi": 1.25,
        "min_oi": 20,
        "tier_name": "Small-Cap",
    },
}


def get_filter_thresholds(market_cap: float | None) -> dict:
    """Pick tier floors by market cap (default to large-cap if unknown)."""
    if market_cap is None or market_cap <= 0:
        return FILTER_CONFIGS[2]
    if market_cap >= 200_000_000_000:
        return FILTER_CONFIGS[1]
    if market_cap >= 10_000_000_000:
        return FILTER_CONFIGS[2]
    return FILTER_CONFIGS[3]


# ═══════════════════════════════════════════════════════════════════
# ████  UNDERLYING QUOTE (for contra-day + tiering)  ████
# ═══════════════════════════════════════════════════════════════════

def _get_underlying_quote(ticker: str) -> dict | None:
    """
    Fetch spot quote via Tradier /markets/quotes. Returns dict with
    last, open, close, market_cap-ish (Tradier doesn't give cap reliably for
    equities here, so we leave cap to the caller / default tier). Never raises.
    """
    if _tradier_headers is None:
        return None
    try:
        resp = requests.get(
            f"{TRADIER_BASE}/markets/quotes",
            params={"symbols": ticker},
            headers=_tradier_headers(),
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        q = safe_tradier_quote(resp, ticker)
        if not q:
            return None
        last = q.get("last")
        if last is None:
            last = q.get("close")
        return {
            "last": float(last) if last is not None else 0.0,
            "open": float(q.get("open")) if q.get("open") is not None else None,
            "close": float(q.get("close")) if q.get("close") is not None else None,
            "prevclose": float(q.get("prevclose")) if q.get("prevclose") is not None else None,
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# ████  CONTRACT FILTERING — ported from contractFiltering.ts  ████
# ═══════════════════════════════════════════════════════════════════

def _dte_from_expiration(expiration: str) -> float:
    """Days to expiration from a YYYY-MM-DD string. Negative-safe (>=0)."""
    try:
        exp = datetime.strptime(expiration, "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        return max(0.0, float((exp - today).days))
    except Exception:
        return 0.0


def _passes_filter(opt: dict, spot: float, dte: float, thresholds: dict) -> bool:
    """
    Port of filterValidContracts() — cheapest checks first for early exit.
    Returns True if the contract survives.
    """
    volume = opt.get("volume") or 0
    oi = opt.get("open_interest") or 0
    last = opt.get("last")
    strike = opt.get("strike")

    # CHEAPEST: presence / type checks
    if not volume or not oi or not isinstance(last, (int, float)) or strike is None:
        return False
    if volume <= 0 or oi <= 0:
        return False

    volume_to_oi = volume / oi

    # CHEAP: OI minimum — bypassed when Vol/OI is extreme (>=50x).
    # Fresh contracts with massive accumulation (OI=16, Vol=1600) are strong
    # institutional signals despite low OI; the ratio tells the story.
    if oi < thresholds["min_oi"] and volume_to_oi < 50:
        return False

    # MEDIUM: Vol/OI ratio floor
    if volume_to_oi < thresholds["min_volume_oi"]:
        return False

    # EXPENSIVE: DTE-aware OTM limit. Institutional 30-90 DTE plays legitimately
    # run 25-45% OTM; 0DTE retail gamma noise tightens to 20%.
    if spot > 0:
        moneyness = abs((strike - spot) / spot)
        otm_limit = 0.20 if dte < 7 else 0.30 if dte < 30 else 0.45 if dte < 90 else 0.50
        if moneyness > otm_limit:
            return False

    # MOST EXPENSIVE: premium floor
    contract_size = opt.get("contract_size") or 100
    premium = last * volume * contract_size
    if premium < thresholds["min_premium"]:
        return False

    return True


# ═══════════════════════════════════════════════════════════════════
# ████  STATIC SCORING — ported from unusualActivity.ts  ████
# ═══════════════════════════════════════════════════════════════════

def _static_score(
    volume_to_oi: float,
    premium: float,
    bid_ask_spread_pct: float,
    dte: float,
) -> int:
    """
    calculateUnusualScore() — the STATIC formula (no ticker baselines).
    Vol/OI (40) + premium (30) + spread% (15) + DTE (15). Capped at 100 here;
    contra-day / fresh bonuses are added by the caller (can push above 100).
    """
    score = 0

    # Volume vs Open Interest (max 40)
    if volume_to_oi > 10:
        score += 40
    elif volume_to_oi > 5:
        score += 35
    elif volume_to_oi > 3:
        score += 25
    elif volume_to_oi > 2.5:
        score += 15

    # Premium Size (max 30)
    if premium > 1_000_000:
        score += 30
    elif premium > 500_000:
        score += 20
    elif premium > 100_000:
        score += 10

    # Bid-Ask Spread % (max 15) — tighter = more institutional
    if bid_ask_spread_pct < 2:
        score += 15
    elif bid_ask_spread_pct < 5:
        score += 8

    # Time decay — conviction-based (max 15)
    if dte < 1:
        score += 15
    elif dte < 4:
        score += 8
    elif dte < 8:
        score += 5
    elif dte < 30:
        score += 12
    elif dte < 90:
        score += 15
    else:
        score += 10

    return min(score, 100)


def _score_contract(opt: dict, spot: float, spot_open: float | None, dte: float) -> dict | None:
    """
    Score a single (already-filtered) contract. Returns an enriched dict, or
    None on bad data. Mirrors detectUnusualActivity()'s static path + the two
    daily-reproducible bonuses (contra-day, fresh-position).
    """
    try:
        volume = opt.get("volume") or 0
        oi = opt.get("open_interest") or 0
        last = opt.get("last") or 0
        bid = opt.get("bid") or 0
        ask = opt.get("ask") or 0
        strike = opt.get("strike")
        opt_type = (opt.get("option_type") or "").lower()  # 'call' / 'put'
        contract_size = opt.get("contract_size") or 100

        if oi <= 0 or volume <= 0 or last <= 0 or strike is None or opt_type not in ("call", "put"):
            return None

        volume_to_oi = volume / oi
        premium = last * volume * contract_size

        midpoint = (bid + ask) / 2 if (bid and ask) else 0
        bid_ask_spread = (ask - bid) if (bid and ask) else 0
        bid_ask_spread_pct = (bid_ask_spread / midpoint * 100) if midpoint > 0 else 100.0

        score = _static_score(volume_to_oi, premium, bid_ask_spread_pct, dte)

        flags: list[str] = []

        # ── Contra-day bonus (+10) ──
        # Calls while underlying closed down >1% from open = contrarian bullish.
        # Puts while underlying closed up >1% from open = contrarian bearish.
        is_contra = False
        if spot_open and spot_open > 0:
            price_change = (spot - spot_open) / spot_open
            if opt_type == "call" and price_change < -0.01:
                score += 10
                is_contra = True
                flags.append("CONTRARIAN_BULLISH")
            elif opt_type == "put" and price_change > 0.01:
                score += 10
                is_contra = True
                flags.append("CONTRARIAN_BEARISH")

        # ── Fresh-position bonus (+10) ──
        # Volume exceeding OI = new positioning, not churn of existing contracts.
        is_fresh = volume > oi
        if is_fresh:
            score += 10
            flags.append("FRESH_POSITION")

        # ── SHORT_DATED tag (0-3 DTE) — these underperform; warn, don't score ──
        if dte <= 3:
            flags.append("SHORT_DATED")

        # ── Sentiment (low-confidence by construction in a daily EOD batch) ──
        # Infer from where 'last' sits in the spread; fall back to contract-type bias.
        sentiment = "Bullish" if opt_type == "call" else "Bearish"
        if midpoint > 0 and ask > bid:
            hit_ask = last >= midpoint + (ask - midpoint) * 0.3
            hit_bid = last <= midpoint - (midpoint - bid) * 0.3
            if opt_type == "call":
                if hit_ask:
                    sentiment = "Bullish"
                elif hit_bid:
                    sentiment = "Bearish"
            else:  # put
                if hit_ask:
                    sentiment = "Bearish"
                elif hit_bid:
                    sentiment = "Bullish"

        return {
            "option_type": opt_type,
            "strike": strike,
            "expiration": opt.get("expiration_date") or opt.get("expiration"),
            "dte": int(dte),
            "volume": int(volume),
            "open_interest": int(oi),
            "volume_to_oi": round(volume_to_oi, 2),
            "last": round(float(last), 2),
            "bid": round(float(bid), 2) if bid else None,
            "ask": round(float(ask), 2) if ask else None,
            "premium": round(premium, 0),
            "bid_ask_spread_pct": round(bid_ask_spread_pct, 1),
            "score": int(score),
            # Honest labels — NOT a fake SWEEP. EOD batch can't see intraday T&S.
            "trade_type": "DAILY_VOLUME",
            "sentiment": sentiment,
            "sentiment_confidence": "inferred",  # low-confidence: stale EOD quote
            "is_contra": is_contra,
            "is_fresh": is_fresh,
            "short_dated": dte <= 3,
            "flags": flags,
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# ████  PER-TICKER SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def scan_flow(ticker: str, market_cap: float | None = None) -> dict | None:
    """
    Once-daily options-flow snapshot for one ticker.

    Pulls expirations within 0-90 DTE, gets each chain with greeks, filters
    contracts on the tiered quality floors, scores survivors with the static
    formula, then summarizes:
      - top_unusual         strikes by Vol/OI (vol >> OI)
      - top_premium         strikes by total $ premium
      - skew                bullish / bearish / balanced (call vs put premium)
      - has_fresh_position  any survivor with volume > OI
      - has_short_dated     any survivor at 0-3 DTE (underperform warning)

    Returns a dict, or None if no usable flow (never raises).
    """
    if get_options_expirations is None or get_options_chain is None:
        return None

    ticker = (ticker or "").strip().upper()
    if not ticker:
        return None

    try:
        quote = _get_underlying_quote(ticker)
        spot = quote["last"] if quote else 0.0
        spot_open = quote.get("open") if quote else None

        thresholds = get_filter_thresholds(market_cap)

        expirations = get_options_expirations(ticker)
        if not expirations:
            return None

        # Keep only 0-90 DTE expirations.
        dte_exps: list[tuple[str, float]] = []
        for exp in expirations:
            dte = _dte_from_expiration(exp)
            if 0 <= dte <= 90:
                dte_exps.append((exp, dte))
        if not dte_exps:
            return None

        scored: list[dict] = []
        for exp, dte in dte_exps:
            chain = get_options_chain(ticker, exp)
            if not chain:
                continue
            for opt in chain:
                if not isinstance(opt, dict):
                    continue
                if not _passes_filter(opt, spot, dte, thresholds):
                    continue
                row = _score_contract(opt, spot, spot_open, dte)
                if row is not None:
                    scored.append(row)

        if not scored:
            return None

        # ── Summaries ──
        by_voloi = sorted(scored, key=lambda r: r["volume_to_oi"], reverse=True)
        by_premium = sorted(scored, key=lambda r: r["premium"], reverse=True)

        call_premium = sum(r["premium"] for r in scored if r["option_type"] == "call")
        put_premium = sum(r["premium"] for r in scored if r["option_type"] == "put")
        total_premium = call_premium + put_premium

        # Call/put premium skew → one directional read.
        if total_premium > 0:
            call_share = call_premium / total_premium
            if call_share >= 0.65:
                skew = "bullish"
            elif call_share <= 0.35:
                skew = "bearish"
            else:
                skew = "balanced"
        else:
            call_share = 0.0
            skew = "balanced"

        has_fresh = any(r["is_fresh"] for r in scored)
        has_short_dated = any(r["short_dated"] for r in scored)
        top_score = max(r["score"] for r in scored)

        return {
            "ticker": ticker,
            "price": round(spot, 2),
            "contracts_scored": len(scored),
            "tier": thresholds["tier_name"],
            "top_score": top_score,
            # Top unusual-volume strikes (vol >> OI)
            "top_unusual": by_voloi[:5],
            # Largest-premium strikes
            "top_premium": by_premium[:5],
            # Directional read (low-confidence)
            "skew": skew,
            "call_premium": round(call_premium, 0),
            "put_premium": round(put_premium, 0),
            "call_premium_share": round(call_share, 2),
            "sentiment_confidence": "inferred",  # daily EOD batch — caveat the read
            # Flags
            "has_fresh_position": has_fresh,
            "has_short_dated": has_short_dated,
            "trade_type": "DAILY_VOLUME",  # honest label, not a fake SWEEP
            "scan_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
    except Exception as e:
        print(f"    [ERR] options_flow scan_flow({ticker}) failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# ████  BATCH ENTRY POINT  ████
# ═══════════════════════════════════════════════════════════════════

def fetch_options_flow(
    tickers: list[str],
    max_results: int = 10,
    market_caps: dict[str, float] | None = None,
) -> list[dict]:
    """
    Batch daily flow snapshot. Returns a list of per-ticker dicts (those with
    usable flow), ranked by top contract score, capped at max_results.
    Never raises — degrades to [].

    `market_caps` (optional): a {TICKER: market_cap} map so the per-ticker tier
    floors apply (small-cap names get looser thresholds). When a ticker is
    absent the scan defaults to the large-cap floor.
    """
    if not tickers:
        return []

    mcaps = {str(k).upper(): v for k, v in (market_caps or {}).items()}

    print("  Running daily options-flow snapshot (Tradier)...")
    results: list[dict] = []
    seen: set[str] = set()

    for raw in tickers:
        t = (raw or "").strip().upper()
        if not t or t in seen:
            continue
        seen.add(t)
        try:
            snap = scan_flow(t, market_cap=mcaps.get(t))
        except Exception as e:  # belt-and-suspenders; scan_flow already guards
            print(f"    [ERR] options_flow({t}): {e}")
            snap = None
        if snap is not None:
            results.append(snap)

    results.sort(key=lambda r: r.get("top_score", 0), reverse=True)
    out = results[:max_results]
    print(f"    Daily flow: {len(out)} tickers with usable flow")
    return out


# ═══════════════════════════════════════════════════════════════════
# ████  SELF-TEST  ████
# ═══════════════════════════════════════════════════════════════════

def _fmt_premium(p: float) -> str:
    if p >= 1_000_000:
        return f"${p/1_000_000:.1f}M"
    if p >= 1_000:
        return f"${p/1_000:.0f}K"
    return f"${p:.0f}"


def _print_snapshot(snap: dict) -> None:
    print(f"\n  ── {snap['ticker']}  (${snap['price']}, {snap['tier']}) "
          f"top_score={snap['top_score']}  contracts={snap['contracts_scored']}")
    print(f"     skew: {snap['skew'].upper()}  "
          f"(call {_fmt_premium(snap['call_premium'])} / put {_fmt_premium(snap['put_premium'])}, "
          f"call share {snap['call_premium_share']:.0%})  [confidence: {snap['sentiment_confidence']}]")
    flags = []
    if snap["has_fresh_position"]:
        flags.append("FRESH_POSITION")
    if snap["has_short_dated"]:
        flags.append("⚠ SHORT_DATED present (0-3 DTE underperform)")
    if flags:
        print(f"     flags: {', '.join(flags)}")
    print(f"     trade_type: {snap['trade_type']} (honest label — daily EOD batch, not intraday sweep)")

    print("     top unusual-volume strikes (vol >> OI):")
    for r in snap["top_unusual"][:3]:
        sd = " ⚠SHORT_DATED" if r["short_dated"] else ""
        fr = " FRESH" if r["is_fresh"] else ""
        print(f"       {r['option_type'].upper():4} ${r['strike']:<8g} {r['expiration']} "
              f"({r['dte']}DTE)  vol={r['volume']:>6} oi={r['open_interest']:>6} "
              f"V/OI={r['volume_to_oi']:>5.1f}  prem={_fmt_premium(r['premium'])}  "
              f"score={r['score']}{fr}{sd}")

    print("     largest-premium strikes:")
    for r in snap["top_premium"][:3]:
        print(f"       {r['option_type'].upper():4} ${r['strike']:<8g} {r['expiration']} "
              f"({r['dte']}DTE)  prem={_fmt_premium(r['premium'])}  "
              f"V/OI={r['volume_to_oi']:>5.1f}  score={r['score']}")


if __name__ == "__main__":
    test_tickers = ["NVDA", "AMD", "PLTR"]
    print(f"\n{'='*72}")
    print(f"  OPTIONS FLOW — daily snapshot self-test: {', '.join(test_tickers)}")
    print(f"{'='*72}")

    snapshots = fetch_options_flow(test_tickers, max_results=10)

    if not snapshots:
        print("\n  No usable flow returned (check TRADIER_API_KEY / market hours / OI freshness).")
    else:
        for s in snapshots:
            _print_snapshot(s)
    print(f"\n{'='*72}\n")
