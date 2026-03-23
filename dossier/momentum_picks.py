"""
Daily Momentum Picks — Gold 🥇, Silver 🥈, Bronze 🥉

Ranks ALL dossier tickers by a momentum-specific composite score
and returns the top 3. Unlike the general grade (A/B/C/D) which
blends technical + fundamental, this is PURE momentum:

Scoring factors (max ~100 raw, then quality multiplied):
  EMA Stack alignment:   10 pts  (21>34>55 = 10, includes PARTIAL BULLISH)
  Pullback Setup:        15 pts  (Bounce 2.0: EMA aligned + ADX>25 + Stoch<40 + near EMA21)
  ADX ACCELERATION:      18 pts  (daily/weekly ratio > 1.0 = breakout. Ratio > 1.7 = 88% WR in test)
  RSI sweet spot:        15 pts  (40-65 = max, <30 or >70 = low)
  Trend direction:        5 pts  (Bullish=5, Bearish=0)
  Relative Volume:       20 pts  (1.2-1.5 = optimal band from backtest. >2x = diminishing returns)
  Price vs EMA 21:       12 pts  (within 1 ATR = perfect pullback, ATR-normalized)
  MACD momentum:          5 pts  (histogram positive = accelerating)
  Institutional signal:   5 pts  (buying = bonus)

Then: final_score = raw_score * (quality_score / 100)
Quality filter penalizes SPACs, pinned acquisitions, junk bio, shells.

Weights calibrated from:
  - Screens_v2 backtest: 810 entries, RVOL 1.2-1.5 = 65.4% WR (best band)
  - Cross-sectional ADX study: 906 stocks, ADX daily/weekly > 1.7 = 88% 1M WR
  - ML feature importance (2026-03-05)
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PICKS_FILE = PROJECT_ROOT / "docs" / "backtesting" / "daily_picks.json"


def _clamp(val, lo=0, hi=100):
    return max(lo, min(hi, val))


def score_momentum(payload: dict) -> dict:
    """Score a single ticker on pure momentum factors. Returns dict with score breakdown."""
    ta = payload.get("technical_analysis", {})
    osc = ta.get("oscillators", {})
    vol = ta.get("volume", {})
    scores_data = payload.get("scores", {})
    tt = payload.get("tickertrace", {})
    sig = tt.get("signal", {}) or {}

    price = payload.get("currentPrice", 0)
    change_pct = payload.get("priceChangePct", 0)
    ema_stack = ta.get("ema_stack", "UNKNOWN")
    trend = payload.get("trendOverall", "")
    rsi = float(osc.get("rsi_14") or 50)
    adx = float(osc.get("adx_14") or 0)
    stoch_k = float(osc.get("stoch_k") or 50)
    macd_hist = osc.get("macd_hist")
    rel_vol = float(vol.get("rel_vol") or 1.0)

    # EMA values
    ema_21 = ta.get("ema", {}).get("21")

    breakdown = {}

    # ── WEIGHTS CALIBRATED FROM ML FEATURE IMPORTANCE (2026-03-05) ──
    # Stoch (0.22) > ADX (0.19) > RelVol (0.19) > RSI (0.18) > EMA21 prox (0.16)
    # EMA alignment (0.03) proved less predictive than oscillators

    # ── 1. EMA Stack (10 pts — relaxed: 21>34>55 core = same as full) ──
    ema_pts = {"FULL BULLISH": 10, "PARTIAL BULLISH": 10, "TANGLED": 2,
               "PARTIAL BEARISH": 1, "FULL BEARISH": 0, "UNKNOWN": 2}
    breakdown["ema_stack"] = ema_pts.get(ema_stack, 2)

    # ── 2. Pullback Setup — Bounce 2.0 (15 pts) ──
    # Composite of stoch + adx + proximity — the textbook setup
    pullback_score = 0
    is_pullback = False
    ema_aligned = ema_stack in ("FULL BULLISH", "PARTIAL BULLISH")
    near_ema21 = False
    if ema_21 and price:
        pct_from_ema = ((price - float(ema_21)) / float(ema_21)) * 100
        near_ema21 = -3 <= pct_from_ema <= 5

    if ema_aligned and adx >= 25 and stoch_k <= 40 and near_ema21:
        # Perfect Bounce 2.0
        pullback_score = 15
        is_pullback = True
    elif ema_aligned and adx >= 20 and stoch_k <= 50 and near_ema21:
        # Good pullback but not textbook
        pullback_score = 10
        is_pullback = True
    elif ema_aligned and stoch_k <= 40:
        # Has the pullback but maybe not near EMA21
        pullback_score = 6
    elif ema_aligned and adx >= 25:
        # Strong trend but no pullback yet
        pullback_score = 3
    breakdown["pullback"] = pullback_score

    # ── 3. ADX ACCELERATION (18 pts — daily/weekly ratio from cross-sectional study) ──
    # Test results: ratio > 1.7 = 88% 1M WR. ratio < 0.5 = 22% WR.
    # Daily ADX > weekly = breakout acceleration. Daily < weekly = trend dying.
    adx_weekly = None
    ta_extra = payload.get("technical_analysis", {}).get("adx_weekly")
    if ta_extra:
        adx_weekly = float(ta_extra)

    if adx_weekly and adx_weekly > 0:
        adx_ratio = adx / adx_weekly
        if adx_ratio >= 1.7:
            breakdown["adx"] = 18   # Daily HOT vs weekly — 88% WR
        elif adx_ratio >= 1.3:
            breakdown["adx"] = 15   # Daily leading — 65% WR
        elif adx_ratio >= 1.0:
            breakdown["adx"] = 12   # Daily = weekly — 55% WR
        elif adx_ratio >= 0.7:
            breakdown["adx"] = 6    # Daily lagging — 39% WR
        elif adx_ratio >= 0.5:
            breakdown["adx"] = 2    # Daily fading — 37% WR
        else:
            breakdown["adx"] = -3   # Daily dead vs weekly — 22% WR, PENALTY
    else:
        # Fallback: raw ADX scoring when weekly not available
        if adx < 20:
            breakdown["adx"] = 18
        elif adx < 25:
            breakdown["adx"] = 15
        elif adx < 30:
            breakdown["adx"] = 10
        elif adx < 40:
            breakdown["adx"] = 5
        elif adx < 50:
            breakdown["adx"] = 1
        else:
            breakdown["adx"] = -5

    # ── 4. RSI sweet spot (15 pts — was 10, ML importance 0.18) ──
    if 40 <= rsi <= 65:
        breakdown["rsi"] = 15
    elif 30 <= rsi < 40 or 65 < rsi <= 70:
        breakdown["rsi"] = 10
    elif rsi < 30:
        breakdown["rsi"] = 6   # oversold could bounce but risky
    else:
        breakdown["rsi"] = 1   # overbought >70

    # ── 5. Trend direction (5 pts — was 10, correlated with EMA stack) ──
    breakdown["trend"] = 5 if "Bullish" in trend else 0

    # ── 6. Relative Volume (20 pts — backtest: 1.2-1.5 = sweet spot) ──
    # Screens_v2 backtest: RVOL 1.2-1.5 = 65.4% WR, +2.04% avg 5d.
    # RVOL >= 1.75 = 50.7% WR (fading spike). RVOL >= 3.0 = 48% WR.
    # High RVOL often = news-driven spike that fades, not sustainable.
    if 1.2 <= rel_vol < 1.5:
        breakdown["rel_vol"] = 20   # Goldilocks zone — best WR
    elif 1.5 <= rel_vol < 1.75:
        breakdown["rel_vol"] = 16   # Good but slightly elevated
    elif 1.75 <= rel_vol < 2.0:
        breakdown["rel_vol"] = 10   # Fading returns
    elif rel_vol >= 2.0:
        breakdown["rel_vol"] = 5    # Likely news spike — will fade
    elif 1.0 <= rel_vol < 1.2:
        breakdown["rel_vol"] = 7    # Normal but below threshold
    elif rel_vol >= 0.7:
        breakdown["rel_vol"] = 2    # Low conviction
    else:
        breakdown["rel_vol"] = -3   # Dead volume — PENALTY

    # ── 7. Price vs EMA 21 (12 pts — ATR-normalized distance) ──
    # Using ATR adapts to each stock's volatility profile.
    if ema_21 and price:
        atr_val = float(ta.get("atr") or 0)
        if atr_val > 0:
            atr_dist = (price - float(ema_21)) / atr_val  # distance in ATR units
            if 0 <= atr_dist <= 0.3:
                breakdown["price_vs_ema"] = 12  # Right at EMA21 — perfect
            elif 0 <= atr_dist <= 0.7:
                breakdown["price_vs_ema"] = 9   # Healthy above
            elif atr_dist > 0.7:
                breakdown["price_vs_ema"] = 3   # Extended > 0.7 ATR above
            elif -0.3 <= atr_dist < 0:
                breakdown["price_vs_ema"] = 10  # Testing support — slight dip
            elif -0.7 <= atr_dist < -0.3:
                breakdown["price_vs_ema"] = 6   # Pulling back deeper
            else:
                breakdown["price_vs_ema"] = 1   # Way below EMA21
        else:
            # ATR unavailable, fall back to percentage
            pct_from_ema = ((price - float(ema_21)) / float(ema_21)) * 100
            if 0 <= pct_from_ema <= 2:
                breakdown["price_vs_ema"] = 12
            elif 0 <= pct_from_ema <= 5:
                breakdown["price_vs_ema"] = 9
            elif pct_from_ema > 5:
                breakdown["price_vs_ema"] = 3
            elif -2 <= pct_from_ema < 0:
                breakdown["price_vs_ema"] = 8
            else:
                breakdown["price_vs_ema"] = 1
    else:
        breakdown["price_vs_ema"] = 5

    # ── 8. MACD Momentum (5 pts) ──
    if macd_hist is not None:
        try:
            mh = float(macd_hist)
            if mh > 0:
                breakdown["macd"] = 5   # Accelerating
            elif mh > -0.5:
                breakdown["macd"] = 3   # Flattening (potential turn)
            else:
                breakdown["macd"] = 0   # Decelerating
        except (ValueError, TypeError):
            breakdown["macd"] = 2
    else:
        breakdown["macd"] = 2  # No data, neutral

    # ── 9. Institutional signal (5 pts) ──
    direction = (sig.get("direction") or "").upper()
    breakdown["institutional"] = 5 if "BUY" in direction else 0

    raw_total = sum(breakdown.values())

    # ── Quality Multiplier ──
    quality = {"quality_score": 100, "flags": {}, "reasons": [], "has_issues": False}
    try:
        from dossier.quality_filter import check_quality
        quality = check_quality(payload)
    except Exception:
        pass

    quality_score = quality["quality_score"]
    final_score = round(raw_total * (quality_score / 100))

    return {
        "ticker": payload.get("ticker", ""),
        "score": final_score,
        "raw_score": raw_total,
        "quality_score": quality_score,
        "quality_flags": quality.get("flags", {}),
        "quality_reasons": quality.get("reasons", []),
        "breakdown": breakdown,
        "is_pullback_setup": is_pullback,
        "price": price,
        "change_pct": change_pct,
        "grade": scores_data.get("grade", ""),
        "tech_score": scores_data.get("technical", 0),
        "ema_stack": ema_stack,
        "trend": trend,
        "rsi": round(rsi, 1),
        "adx": round(adx, 1),
        "stoch_k": round(stoch_k, 1),
        "rel_vol": round(rel_vol, 2),
    }


def pick_daily_momentum(ticker_payloads: list[dict], date: str) -> dict:
    """
    Rank all tickers and return Gold 🥇, Silver 🥈, Bronze 🥉 picks.

    ALWAYS attempts to fill 3 picks. Even on thin days, the top 3
    scored tickers get medals — the score tells you conviction level.

    Args:
        ticker_payloads: List of full ticker payload dicts (from enrichment)
        date: Report date string

    Returns:
        Dict with 'picks' (top 3), 'all_ranked' (full list), 'date'
    """
    scored = []
    for payload in ticker_payloads:
        try:
            result = score_momentum(payload)
            if result["ticker"]:
                scored.append(result)
        except Exception as e:
            print(f"    [WARN] Momentum scoring failed for {payload.get('ticker', '?')}: {e}")

    # Sort by momentum score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Assign medals — ALWAYS fill top 3 if we have >= 3 scored tickers
    medals = ["🥇 GOLD", "🥈 SILVER", "🥉 BRONZE"]
    picks = []
    for i, s in enumerate(scored[:3]):
        s["medal"] = medals[i]
        s["rank"] = i + 1
        picks.append(s)

    if len(picks) < 3 and len(scored) > len(picks):
        # Edge case: somehow we have more scored but didn't pick them
        for i in range(len(picks), min(3, len(scored))):
            scored[i]["medal"] = medals[i]
            scored[i]["rank"] = i + 1
            picks.append(scored[i])

    if not picks:
        print("    ⚠️  No momentum picks today — zero tickers scored")
    elif len(picks) < 3:
        print(f"    ⚠️  Only {len(picks)} pick(s) today — enrichment pool too thin")

    result = {
        "date": date,
        "picks": picks,
        "all_ranked": scored,
    }

    # Persist daily picks
    _save_picks(result, date)

    return result


def _save_picks(result: dict, date: str):
    """Append today's picks to the rolling picks file AND write API endpoint."""
    # ── Regime Awareness ──
    regime_data = {}
    try:
        from dossier.market_regime import detect_regime
        regime_data = detect_regime()
    except Exception as e:
        print(f"    [WARN] Regime detection failed: {e}")

    regime_name = regime_data.get("regime", "UNKNOWN")
    regime_note = "✅ Market favorable for momentum entries"
    if regime_name in ["FEAR", "PANIC"]:
        regime_note = "⚠️ High VIX — reduce size, tighten stops"
    elif regime_name == "ELEVATED":
        regime_note = "🟡 Caution — prefer pullback setups only"

    try:
        PICKS_FILE.parent.mkdir(parents=True, exist_ok=True)

        history = []
        if PICKS_FILE.exists():
            with open(PICKS_FILE) as f:
                history = json.load(f)

        # Remove existing entry for this date
        history = [h for h in history if h.get("date") != date]

        # Add today's picks (compact version)
        compact = {
            "date": date,
            "gold": {"ticker": result["picks"][0]["ticker"], "score": result["picks"][0]["score"]} if len(result["picks"]) > 0 else None,
            "silver": {"ticker": result["picks"][1]["ticker"], "score": result["picks"][1]["score"]} if len(result["picks"]) > 1 else None,
            "bronze": {"ticker": result["picks"][2]["ticker"], "score": result["picks"][2]["score"]} if len(result["picks"]) > 2 else None,
        }
        history.append(compact)

        # Keep last 90 days
        history = history[-90:]

        with open(PICKS_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"    [WARN] Daily picks save failed: {e}")

    # ── Write Static API Endpoint ──
    # Served via GitHub Pages at:
    #   https://mphinance.github.io/mphinance/api/daily-picks.json
    try:
        api_dir = PROJECT_ROOT / "docs" / "api"
        api_dir.mkdir(parents=True, exist_ok=True)

        medals = {0: "gold", 1: "silver", 2: "bronze"}
        api_picks = []
        # Top 10 with full detail (podium is top 3, rest are "ranked")
        for i, pick in enumerate(result.get("all_ranked", [])[:10]):
            api_picks.append({
                "rank": i + 1,
                "medal": medals.get(i, ""),
                "ticker": pick["ticker"],
                "score": pick["score"],
                "raw_score": pick.get("raw_score", pick["score"]),
                "quality_score": pick.get("quality_score", 100),
                "is_pullback_setup": pick.get("is_pullback_setup", False),
                "price": pick["price"],
                "change_pct": pick.get("change_pct", 0),
                "grade": pick.get("grade", ""),
                "ema_stack": pick.get("ema_stack", ""),
                "trend": pick.get("trend", ""),
                "rsi": pick.get("rsi", 0),
                "adx": pick.get("adx", 0),
                "stoch_k": pick.get("stoch_k", 0),
                "rel_vol": pick.get("rel_vol", 1.0),
                "breakdown": pick.get("breakdown", {}),
                "quality_flags": pick.get("quality_flags", {}),
                "quality_reasons": pick.get("quality_reasons", []),
                "tradingview_url": f"https://www.tradingview.com/chart/?symbol={pick['ticker']}",
                "regime_note": regime_note,
            })

        # Full ranking (compact — just ticker + score + pullback flag)
        all_ranked = []
        for s in result.get("all_ranked", []):
            all_ranked.append({
                "ticker": s["ticker"],
                "score": s["score"],
                "grade": s.get("grade", ""),
                "is_pullback": s.get("is_pullback_setup", False),
                "ema_stack": s.get("ema_stack", ""),
            })

        api_payload = {
            "date": date,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "market_regime": {
                "regime": regime_name,
                "vix": regime_data.get("vix", 0),
                "hedge_suggestions": regime_data.get("hedge_suggestions", []),
                "market_context": regime_data.get("market_context", ""),
            },
            "picks": api_picks,
            "total_scored": len(result.get("all_ranked", [])),
            "all_ranked": all_ranked,
            "scoring_weights": {
                "ema_stack": {"max": 10, "desc": "EMA 8>21>34>55>89 alignment"},
                "pullback": {"max": 15, "desc": "Bounce 2.0: EMA aligned + ADX>25 + Stoch<40 + near EMA21"},
                "adx": {"max": 18, "desc": "ADX FRESHNESS (<20=best, >50=penalty — backtest: <25=100% WR)"},
                "rsi": {"max": 15, "desc": "RSI sweet spot (40-65 optimal)"},
                "trend": {"max": 5, "desc": "Overall trend direction (Bullish/Bearish)"},
                "rel_vol": {"max": 20, "desc": "RVOL conviction (>1.5=80%WR, <0.7=penalty — 6.82R spread)"},
                "price_vs_ema": {"max": 12, "desc": "Price proximity to EMA 21"},
                "macd": {"max": 5, "desc": "MACD histogram momentum"},
                "institutional": {"max": 5, "desc": "TickerTrace institutional buying signal"},
            },
            "quality_gate": "final_score = raw_score × (quality_score / 100)",
            "history": history[-7:],  # Last 7 days of picks
        }

        api_path = api_dir / "daily-picks.json"
        with open(api_path, "w") as f:
            json.dump(api_payload, f, indent=2)
        print(f"    ✓ API endpoint: docs/api/daily-picks.json")
    except Exception as e:
        print(f"    [WARN] API endpoint write failed: {e}")




def format_picks_text(picks_data: dict) -> str:
    """Format picks as plain text with FULL factor breakdown for pipeline output."""
    if not picks_data or not picks_data.get("picks"):
        return "No momentum picks today."

    lines = ["", "DAILY MOMENTUM PICKS", "=" * 60]
    for p in picks_data["picks"]:
        bd = p.get("breakdown", {})
        pb_flag = " ⚡PULLBACK SETUP" if p.get("is_pullback_setup") else ""
        q_flag = f" ⚠️Q:{p.get('quality_score', 100)}" if p.get("quality_score", 100) < 100 else ""

        lines.append(
            f"\n{p['medal']}: {p['ticker']}  "
            f"FINAL: {p['score']}/100  (Raw: {p.get('raw_score', p['score'])}){pb_flag}{q_flag}"
        )
        lines.append(f"  ${p['price']:.2f}  [{p['change_pct']:+.1f}%]  Grade: {p['grade']}  {p['ema_stack']}")
        lines.append(f"  ├─ EMA Stack:    {bd.get('ema_stack', '?'):>3}/20")
        lines.append(f"  ├─ Pullback:     {bd.get('pullback', '?'):>3}/15" + (" ← Bounce 2.0!" if p.get("is_pullback_setup") else ""))
        lines.append(f"  ├─ ADX ({p['adx']}):   {bd.get('adx', '?'):>3}/15")
        lines.append(f"  ├─ RSI ({p['rsi']}):   {bd.get('rsi', '?'):>3}/10")
        lines.append(f"  ├─ Trend:        {bd.get('trend', '?'):>3}/10")
        lines.append(f"  ├─ Rel Vol:      {bd.get('rel_vol', '?'):>3}/10  ({p['rel_vol']}x)")
        lines.append(f"  ├─ Price/EMA21:  {bd.get('price_vs_ema', '?'):>3}/10")
        lines.append(f"  ├─ MACD:         {bd.get('macd', '?'):>3}/5")
        lines.append(f"  └─ Institutional:{bd.get('institutional', '?'):>3}/5")
        if p.get("quality_reasons"):
            for r in p["quality_reasons"]:
                lines.append(f"     ⚠️ {r}")

    return "\n".join(lines)

