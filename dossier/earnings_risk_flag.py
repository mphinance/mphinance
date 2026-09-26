"""
Earnings Risk Flag — which of today's momentum leaders are about to report.

breadth_index.py, factor_leaderboard.py, score_dispersion.py, sector_leadership.py,
quality_breadth.py, extension_index.py and follow_through_index.py all aggregate
momentum_picks.py's `all_ranked` scored list, but every one of them looks purely at
*today's technicals*. None of them ask the one question that changes a leader's
risk profile overnight: is this name about to report earnings?

earnings_momentum_screener.py already asks a related question across the WHOLE
market ("which stocks with an upcoming print also look technically strong?"), but
it never looks at whether today's leaderboard itself is exposed. This flips it:
of the names ALREADY on today's leaderboard, which ones carry event risk in the
next N days? A reader eyeing the day's #1 momentum name has a very different
setup if that name reports Thursday than if it's insulated from a print for a
month.

Bounded to the top `leader_count` names (default 10) so the pipeline's per-run
yfinance calendar lookups stay cheap — this isn't a market-wide scan, just a
risk annotation on the leaderboard the dossier already produced.

History is persisted date-keyed (dedup-overwrite same day), same pattern as
follow_through_index.py / extension_index.py.

Output: docs/api/earnings-risk.json + landing/data/earnings_risk_history.json
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

try:
    import yfinance as yf
except ImportError:  # pragma: no cover - yfinance is a hard runtime dep elsewhere
    yf = None

DEFAULT_LEADER_COUNT = 10
DEFAULT_MAX_DAYS = 7


def days_until_earnings(ticker: str, max_days: int = DEFAULT_MAX_DAYS) -> int | None:
    """
    Calendar days until `ticker`'s next earnings report, or None if nothing is
    scheduled within `max_days` (or the calendar lookup fails/is unavailable).

    Same yfinance .calendar lookup as
    earnings_momentum_screener._earnings_days_away, kept as its own copy here
    since this module is meant to run standalone against a leaderboard.
    """
    if yf is None:
        return None
    try:
        cal = yf.Ticker(ticker).calendar
        if not cal:
            return None
        dates = cal.get("Earnings Date") or []
        today = date.today()
        best = None
        for ed in dates:
            if hasattr(ed, "date"):
                ed = ed.date()
            days_away = (ed - today).days
            if 0 <= days_away <= max_days and (best is None or days_away < best):
                best = days_away
        return best
    except Exception:
        return None


def _score(pick: dict) -> float:
    try:
        return float(pick.get("score") or 0)
    except (TypeError, ValueError):
        return 0.0


def compute_earnings_risk(
    all_ranked: list[dict],
    leader_count: int = DEFAULT_LEADER_COUNT,
    max_days: int = DEFAULT_MAX_DAYS,
    lookup_fn=days_until_earnings,
) -> dict:
    """
    Flag which of today's top `leader_count` momentum leaders (by score) report
    earnings within `max_days`. `lookup_fn` is injectable so tests never hit
    yfinance. Never raises — bad/empty input yields a zeroed result.
    """
    leaders = sorted(
        [p for p in (all_ranked or []) if p.get("ticker")],
        key=_score, reverse=True,
    )[:leader_count]

    flagged = []
    for pick in leaders:
        ticker = pick["ticker"]
        try:
            days = lookup_fn(ticker, max_days)
        except Exception:
            days = None
        if days is not None:
            flagged.append({
                "ticker": ticker,
                "score": pick.get("score"),
                "days_until_earnings": days,
            })
    flagged.sort(key=lambda f: f["days_until_earnings"])

    leaders_n = len(leaders)
    flagged_n = len(flagged)
    flagged_pct = round(100.0 * flagged_n / leaders_n, 1) if leaders_n else 0.0

    return {
        "leaders_n": leaders_n,
        "flagged_n": flagged_n,
        "flagged_pct": flagged_pct,
        "max_days": max_days,
        "flagged": flagged,
    }


def load_history(path) -> list:
    """Load the earnings-risk history list. Missing or corrupt file → []."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append_earnings_risk(history: list, entry: dict) -> list:
    """Return a new history list with `entry` added, deduped by `date`."""
    entry_date = entry.get("date")
    kept = [e for e in history if e.get("date") != entry_date]
    kept.append(entry)
    kept.sort(key=lambda e: e.get("date", ""))
    return kept


def save_history(path, history: list) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(history, indent=2))


def record_earnings_risk(path, entry: dict) -> list:
    """Load → dedup-append → save in one call. Returns the updated history list."""
    updated = append_earnings_risk(load_history(path), entry)
    save_history(path, updated)
    return updated


def format_earnings_risk_text(risk: dict) -> str:
    """One-line console summary, matching the style of format_follow_through_text()."""
    if not risk.get("leaders_n"):
        return "❔ Earnings Risk: insufficient data"
    if not risk.get("flagged_n"):
        return (
            f"🟢 Earnings Risk: none of today's top {risk['leaders_n']} leaders "
            f"report within {risk['max_days']}d"
        )
    names = ", ".join(
        f"{f['ticker']} ({f['days_until_earnings']}d)" for f in risk["flagged"][:5]
    )
    return (
        f"🟠 Earnings Risk: {risk['flagged_n']}/{risk['leaders_n']} "
        f"({risk['flagged_pct']}%) of today's leaders report within "
        f"{risk['max_days']}d — {names}"
    )


def save_api_output(risk: dict, out_dir) -> None:
    """Write docs/api/earnings-risk.json for GitHub Pages consumption."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        **risk,
    }
    out_path = out_dir / "earnings-risk.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  ✓ Saved → {out_path} ({risk.get('flagged_n', 0)} flagged)")
