"""
Dossier Summary API — The atomic content unit.

Generates docs/api/dossier-summary.json after each pipeline run.
This is the single source of truth for "what did the pipeline find today?"
that feeds all distribution channels:

  - Landing page (mphinance.com) — hero section, live picks
  - Substack posts — embedded data in daily digests
  - Discord (#sam-mph) — daily alerts
  - Alpha Momentum HUD — market context
  - Widgets — embeddable anywhere
  - Social media — auto-generated preview content

Usage (called by generate.py at end of pipeline):
    from dossier.report.summary_api import generate_summary_api
    generate_summary_api(date, market_pulse, scanner_signals, dossiers,
                         momentum_picks, market, ai_narrative)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
API_DIR = PROJECT_ROOT / "docs" / "api"


def generate_summary_api(
    date: str,
    market_pulse: list,
    scanner_signals: list,
    dossiers: list,
    momentum_picks: dict,
    market: dict,
    ai_narrative: str = "",
    technical_setups: list = None,
    daily_setups: dict = None,
    ghost_log: str = "",
    **kwargs,
) -> dict:
    """Generate the dossier summary JSON — the atomic content unit."""

    # ── Market Snapshot ──
    spy = next((p for p in market_pulse if p.get("symbol") == "SPY"), {})
    qqq = next((p for p in market_pulse if p.get("symbol") == "QQQ"), {})
    btc = next((p for p in market_pulse if p.get("symbol") == "BTC-USD"), {})
    vix_data = market.get("vix", {})

    # ── Momentum Picks (the money) ──
    picks = momentum_picks.get("picks", []) if momentum_picks else []
    gold_pick = picks[0] if picks else None
    silver_pick = picks[1] if len(picks) > 1 else None
    bronze_pick = picks[2] if len(picks) > 2 else None

    # ── Sam's Quote ──
    try:
        from dossier.report.ghost_quotes import get_daily_quote, format_quote
        quote = get_daily_quote(date)
        quote_text = quote["text"]
        quote_category = quote["category"]
    except Exception:
        quote_text = "The market doesn't care about your feelings."
        quote_category = "trading"

    # ── Top Signals (unique tickers, top 5) ──
    seen = set()
    top_signals = []
    for s in scanner_signals:
        sym = s.get("symbol", "")
        if sym and sym not in seen:
            seen.add(sym)
            top_signals.append({
                "symbol": sym,
                "strategy": s.get("strategy", ""),
                "score": s.get("score", 0),
            })
            if len(top_signals) >= 5:
                break

    # ── Dossier Grades ──
    grades = {}
    for d in dossiers:
        grade = d.get("grade", "")
        if grade:
            grades[grade] = grades.get(grade, 0) + 1

    # ── One-liner narrative (first sentence of AI narrative) ──
    one_liner = ""
    if ai_narrative:
        # Strip HTML and get first sentence
        import re
        clean = re.sub(r'<[^>]+>', '', ai_narrative)
        sentences = clean.split('.')
        if sentences:
            one_liner = sentences[0].strip() + '.'

    # ── Synthesis sections (Daily Review v2) — passed via kwargs ──
    # Only the PUBLIC subset (confluence/migration/market_weather) is emitted;
    # your_book + analyst overlay are private and handled by the push, not here.
    confluence = kwargs.get("confluence") or {}
    migration = kwargs.get("migration") or {}
    market_weather = kwargs.get("market_weather") or {}
    sector_rs = kwargs.get("sector_rs") or {}

    confluence_section = _confluence_summary(confluence)
    migration_section = _migration_summary(migration)

    # ── Build the summary ──
    summary = {
        "meta": {
            "date": date,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report_url": f"https://mphinance.github.io/mphinance/reports/{date}_alpha_dossier.html",
            "pipeline_version": "2.1",
        },
        "market": {
            "spy": {"price": spy.get("price", 0), "change_pct": spy.get("pct_change", 0)},
            "qqq": {"price": qqq.get("price", 0), "change_pct": qqq.get("pct_change", 0)},
            "btc": {"price": btc.get("price", 0), "change_pct": btc.get("pct_change", 0)},
            "vix": vix_data.get("vix_level", 0),
            "regime": vix_data.get("regime_name", "UNKNOWN"),
            "regime_emoji": _regime_emoji(vix_data.get("vix_level", 0)),
        },
        "picks": {
            "gold": _pick_summary(gold_pick) if gold_pick else None,
            "silver": _pick_summary(silver_pick) if silver_pick else None,
            "bronze": _pick_summary(bronze_pick) if bronze_pick else None,
            "total_graded": len(picks),
        },
        "signals": {
            "count": len(scanner_signals),
            "top_5": top_signals,
            "grade_distribution": grades,
        },
        "narrative": {
            "one_liner": one_liner,
            "full_length": len(ai_narrative),
        },
        "sam": {
            "quote": quote_text,
            "category": quote_category,
            "ghost_log_preview": _strip_html(ghost_log)[:200] if ghost_log else "",
        },
        "coverage": {
            "dossiers_enriched": len(dossiers),
            "technical_setups": len(technical_setups) if technical_setups else 0,
            "benchmarks": len(market_pulse),
        },
        # ── Daily Review v2 synthesis (PUBLIC subset only) ──
        # NOTE: your_book (Mike's live IBKR positions) and analyst_overlap (a
        # third party's private list) are DELIBERATELY excluded — this JSON is
        # published to public GitHub Pages. Those go only into the private push.
        "confluence": confluence_section,
        "migration": migration_section,
        "sector_rs": _sector_rs_summary(sector_rs),
        "market_weather": {
            "regime": market_weather.get("regime"),
            "vix": market_weather.get("vix"),
            "term_structure": market_weather.get("term_structure"),
            "verdict": market_weather.get("verdict"),
            "trade_ok": market_weather.get("trade_ok"),
            "headline": market_weather.get("headline"),
        } if market_weather else None,
    }

    # ── Write to disk ──
    API_DIR.mkdir(parents=True, exist_ok=True)

    # Current summary (always overwritten)
    summary_path = API_DIR / "dossier-summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Date-stamped archive
    archive_path = API_DIR / f"dossier-{date}.json"
    with open(archive_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Latest redirect (for simple fetching)
    latest_path = API_DIR / "latest.json"
    with open(latest_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  ✓ Summary API: {summary_path}")
    print(f"  ✓ Archive: {archive_path}")
    if gold_pick:
        print(f"  🥇 Gold Pick: {gold_pick['ticker']} ({gold_pick.get('score', '?')}/100)")

    return summary


def _confluence_summary(confluence: dict) -> dict:
    """Shape the confluence watchlist for the summary API (top multi-leg names)."""
    watchlist = (confluence or {}).get("watchlist") or []
    rows = []
    for r in watchlist:
        if r.get("n_legs", 0) < 2:
            continue  # the API surfaces only multi-leg convergence
        rows.append({
            "ticker": r.get("ticker"),
            "n_legs": r.get("n_legs"),
            "score": r.get("score"),
            "conflict": r.get("conflict", False),
            "conflict_reason": r.get("conflict_reason", ""),
            "legs": [{"source": l.get("source"), "direction": l.get("direction"),
                      "detail": l.get("detail")} for l in (r.get("legs") or [])],
        })
        if len(rows) >= 8:
            break
    top = rows[0] if rows else None
    return {
        "count": len(rows),
        "top": top,
        "watchlist": rows,
    }


def _migration_summary(migration: dict) -> dict:
    """Shape the migration feed for the summary API."""
    migrations = (migration or {}).get("migrations") or []
    motd = (migration or {}).get("migration_of_the_day")
    return {
        "count": len(migrations),
        "migration_of_the_day": motd,
        "migrations": migrations[:10],
    }


def _sector_rs_summary(sector_rs: dict) -> dict | None:
    """Compact sector-RS snapshot for the public summary API."""
    if not sector_rs or not sector_rs.get("ranked"):
        return None
    leaders = [
        {"ticker": r["ticker"], "name": r["name"], "composite_rs": r["composite_rs"],
         "rotation": r["rotation"]}
        for r in sector_rs.get("leaders", [])[:3]
    ]
    laggards = [
        {"ticker": r["ticker"], "name": r["name"], "composite_rs": r["composite_rs"],
         "rotation": r["rotation"]}
        for r in sector_rs.get("laggards", [])[:3]
    ]
    return {
        "leaders": leaders,
        "laggards": laggards,
        "sector_count": len(sector_rs.get("ranked", [])),
        "generated_at": sector_rs.get("generated_at"),
    }


def _your_book_summary(your_book: dict) -> dict:
    """Shape the IBKR 'Your Book' overlay for the summary API."""
    positions = (your_book or {}).get("positions") or []
    actionable = [p for p in positions
                  if p.get("action") in ("ADD", "TRIM") or p.get("overlap")]
    return {
        "ok": bool((your_book or {}).get("ok")),
        "position_count": len(positions),
        "actionable": [{
            "ticker": p.get("ticker"),
            "action": p.get("action"),
            "signal_sources": p.get("signal_sources", []),
            "note": p.get("note", ""),
            "unrealized_pnl": p.get("unrealized_pnl"),
        } for p in actionable[:5]],
        "net_liq": (your_book or {}).get("net_liq"),
        "daily_pnl": (your_book or {}).get("daily_pnl"),
    }


def _analyst_summary(analyst_overlay: dict) -> dict:
    """Shape the nightly analyst-watchlist cross-reference for the summary API."""
    summ = (analyst_overlay or {}).get("summary") or {}
    return {
        "confirmed": summ.get("confirmed", []),
        "off_radar": summ.get("off_radar", []),
        "overlap_count": summ.get("overlap_count", 0),
    }


def _pick_summary(pick: dict) -> dict:
    """Extract the key fields from a momentum pick."""
    return {
        "ticker": pick.get("ticker", ""),
        "score": pick.get("score", 0),
        "grade": pick.get("grade", ""),
        "entry": pick.get("entry_price", 0),
        "target": pick.get("target_price", 0),
        "stop": pick.get("stop_price", 0),
        "upside_pct": pick.get("upside_pct", 0),
        "chart_url": f"https://mphinance.github.io/mphinance/ticker/{pick.get('ticker', 'SPY')}/chart.png",
    }


def _regime_emoji(vix: float) -> str:
    """Map VIX level to emoji."""
    if vix < 15:
        return "🟢"
    elif vix < 20:
        return "🟡"
    elif vix < 30:
        return "🔴"
    else:
        return "💀"


def _strip_html(text: str) -> str:
    """Strip HTML tags from text."""
    import re
    return re.sub(r'<[^>]+>', '', text)
