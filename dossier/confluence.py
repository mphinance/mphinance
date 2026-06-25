"""
confluence.py — confluence ranking + day-over-day migration detection.

The synthesis layer the Daily Review is for: it takes the independent signal legs
produced by the step-1 data-source stages and answers the two questions Mike
actually asked for —
  1. "What does more than one independent source agree on TODAY?"  → compute_confluence
  2. "What MATURED since yesterday (escalate it)?"                  → compute_migration

Both functions are PURE and NEVER raise: on bad/empty input they return an empty
structure of the right shape. Errors caught internally print "[confluence] ...".

────────────────────────────────────────────────────────────────────────────
WIRING (orchestrator: how to call this from generate.py)
────────────────────────────────────────────────────────────────────────────
Insert ONE confluence stage AFTER all the leg-producing stages exist as local
vars (after [7b] options flow / [9] momentum_picks; institutional + universe are
earlier). All inputs already exist in generate.py:

    from dossier.confluence import compute_confluence, compute_migration
    from dossier.persistence.tracker import update_persistence, load_persistence

    # --- Stage Nc: Confluence watchlist ---
    confluence = compute_confluence(
        scanner_signals=scanner_signals,            # [{symbol, direction, score, strategy, ...}]
        triangle_signals=triangle_signals,          # [{ticker, signal_type, pattern, ...}]   ([6b])
        options_flow_signals=options_flow_signals,  # [{ticker, skew, top_score, has_short_dated, ...}] ([7b])
        institutional=institutional,                # {top_buying:[{ticker}], top_selling:[{ticker}]}
        momentum_picks=momentum_picks,              # {picks:[{ticker, score, is_pullback_setup, ...}]}
        universe_rows=universe_rows,                 # [{ticker, factor_score, market_cap, change_pct, ...}] ([2b])
        market_regime=market_regime,                # {regime, vix:{vix_level}, ...}  (optional context)
    )
    # confluence["watchlist"] -> ranked rows; feed builder.py + summary_api ("confluence").

    # --- Stage Nd: Day-over-day migration ---
    # First record each leg's appearance into its OWN namespace (Task A). The
    # default-namespace call (scanner_signals) already happens at Stage ~9; do NOT
    # duplicate it — only add the new namespaces:
    update_persistence([t["ticker"] for t in triangle_signals],     date, namespace="triangle")
    update_persistence([f["ticker"] for f in options_flow_signals], date, namespace="flow")
    update_persistence([p["ticker"] for p in momentum_picks.get("picks", [])], date, namespace="momentum")
    update_persistence([b["ticker"] for b in institutional.get("top_buying", [])], date, namespace="institutional")

    # Build today's per-namespace ticker sets (what fired today, by leg):
    namespaces_today = {
        "scanner":       [s["symbol"] for s in scanner_signals],
        "triangle":      [t["ticker"] for t in triangle_signals],
        "flow":          [f["ticker"] for f in options_flow_signals],
        "momentum":      [p["ticker"] for p in momentum_picks.get("picks", [])],
        "institutional": [b["ticker"] for b in institutional.get("top_buying", [])],
        "universe":      [r["ticker"] for r in universe_rows],
    }
    # The classified persistence per namespace (read-only — no new write):
    namespaces_persistence = {ns: load_persistence(ns) for ns in namespaces_today}

    migration = compute_migration(
        namespaces_today=namespaces_today,
        namespaces_persistence=namespaces_persistence,
        date=date,
    )
    # migration["migrations"] -> list; migration["migration_of_the_day"] -> one row|None.
    # Surface in builder.py + summary_api ("migration"); push the migration_of_the_day.

NOTE the ordering invariant: call update_persistence for the new namespaces
BEFORE load_persistence so today's appearance is reflected in the streak/class.
compute_migration compares each ticker's CURRENT (post-update) state against the
maturation ordering and persistence classes; it does not itself touch disk.
"""

from __future__ import annotations

from typing import Any, Iterable

# ──────────────────────────────────────────────────────────────────────────
# Leg taxonomy
# ──────────────────────────────────────────────────────────────────────────
# The genuinely INDEPENDENT legs (the audit's core rule): correlated
# momentum/trend sources (EMA-stack, Ghost-Alpha, technical-setups, momentum,
# the scanner survivors) all collapse into ONE "trend" leg — they are the same
# factor. Triangle, options flow, and institutional 13F are the decorrelated new
# legs. Regime is CONTEXT, never a leg.
TREND = "trend"
TRIANGLE = "triangle"
DOWNTREND_BREAKOUT = "downtrend_breakout"
FLOW = "flow"
INSTITUTIONAL = "institutional"

INDEPENDENT_LEGS = (TREND, TRIANGLE, DOWNTREND_BREAKOUT, FLOW, INSTITUTIONAL)

# Per-leg score contribution when the leg agrees bullishly.
_LEG_WEIGHT = {
    TREND: 1.0,
    TRIANGLE: 1.2,   # decorrelated + structural → slightly heavier
    DOWNTREND_BREAKOUT: 1.2,  # decorrelated structural reversal (Michael's edge)
    FLOW: 1.1,       # decorrelated smart-money read
    INSTITUTIONAL: 1.3,  # 13F conviction → heaviest single leg
}

# Maturation ordering for migration detection: a ticker MATURES as it climbs this
# ladder day-over-day (early universe presence → forming structure → confirmed
# breakout w/ flow → trend/momentum leadership). Higher index = more mature.
MATURATION_LADDER = [
    "universe",            # 0  showed up in the broad candidate scan
    "triangle_forming",    # 1  structure building
    "triangle_breakout",   # 2  structure confirmed
    "flow",                # 3  smart-money positioning
    "momentum",            # 4  trend leadership / Ghost-Alpha grade
]
_LADDER_RANK = {state: i for i, state in enumerate(MATURATION_LADDER)}

# Mega-cap ubiquity suppression: names that appear in everything every day carry
# no migration information. Anything at/above this cap is suppressed from the
# migration feed (still eligible for the confluence watchlist).
MEGA_CAP_FLOOR = 200_000_000_000  # $200B

# Fallback denylist for when a ticker's market cap is unknown (not in the
# universe scan). These are unambiguous mega-caps whose daily ubiquity carries no
# migration signal — suppress them even without a cap number.
_KNOWN_MEGA_CAPS = {
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "AVGO",
    "BRK.A", "BRK.B", "BRK-A", "BRK-B", "LLY", "JPM", "V", "MA", "XOM", "UNH",
    "WMT", "JNJ", "ORCL", "HD", "PG", "COST", "ABBV", "NFLX", "BAC", "KO",
    "CRM", "CVX", "AMD", "PEP", "TMO", "ADBE", "WFC", "MRK", "CSCO", "ACN",
    "MCD", "ABT", "LIN", "DIS", "INTC", "QCOM", "TXN", "IBM", "GE", "VZ",
}


# ──────────────────────────────────────────────────────────────────────────
# small helpers
# ──────────────────────────────────────────────────────────────────────────
def _sym(value: Any) -> str:
    """Normalize a ticker symbol to upper-case, or '' if unusable."""
    if value is None:
        return ""
    try:
        return str(value).strip().upper()
    except Exception:
        return ""


def _as_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def _ticker_of(row: Any) -> str:
    """Pull a ticker from a row that may key it as 'ticker' or 'symbol'."""
    if not isinstance(row, dict):
        return ""
    return _sym(row.get("ticker") or row.get("symbol"))


def _direction_is_bearish(direction: Any) -> bool:
    d = (str(direction or "")).upper()
    return "BEAR" in d or d == "BELOW" or "SELL" in d or "SHORT" in d


def _direction_is_bullish(direction: Any) -> bool:
    d = (str(direction or "")).upper()
    return "BULL" in d or d == "ABOVE" or "BUY" in d or "LONG" in d


# ──────────────────────────────────────────────────────────────────────────
# 1) CONFLUENCE
# ──────────────────────────────────────────────────────────────────────────
def compute_confluence(
    *,
    scanner_signals: list[dict] | None = None,
    triangle_signals: list[dict] | None = None,
    downtrend_break_signals: list[dict] | None = None,
    options_flow_signals: list[dict] | None = None,
    institutional: dict | None = None,
    momentum_picks: dict | None = None,
    universe_rows: list[dict] | None = None,
    market_regime: dict | None = None,
) -> dict:
    """Rank tickers by how many INDEPENDENT, directionally-agreeing legs fire.

    Returns {"watchlist": [row, ...], "generated": <int count of multi-leg rows>}.

    Each row:
        {
          "ticker": str,
          "n_legs": int,                # distinct INDEPENDENT bullish legs
          "legs": [{"source","direction","detail"}, ...],   # incl. conflicts
          "score": float,
          "conflict": bool,
          "conflict_reason": str,
        }

    Rules (from the audit):
      • correlated trend sources collapse into ONE "trend" leg;
      • only bullish agreement counts toward n_legs; a bearish leg (bearish flow
        skew, institutional selling) is a CONFLICT that subtracts / flags amber;
      • SHORT_DATED (0-3 DTE) flow is a trap → NOT a clean bullish flow leg
        (penalized, flagged), never adds.
    """
    try:
        scanner_signals = _as_list(scanner_signals)
        triangle_signals = _as_list(triangle_signals)
        downtrend_break_signals = _as_list(downtrend_break_signals)
        options_flow_signals = _as_list(options_flow_signals)
        momentum_picks = momentum_picks if isinstance(momentum_picks, dict) else {}
        institutional = institutional if isinstance(institutional, dict) else {}
        universe_rows = _as_list(universe_rows)

        # registry: ticker -> aggregated state
        reg: dict[str, dict] = {}

        def cand(t: str) -> dict:
            if t not in reg:
                reg[t] = {
                    "ticker": t,
                    "legs": {},          # leg_name -> {"source","direction","detail"}
                    "conflicts": [],     # list of conflict reason strings
                    "extra": 0.0,        # magnitude/quality bonus (sub-leg)
                    "market_cap": None,
                }
            return reg[t]

        def add_leg(t: str, leg: str, direction: str, detail: str) -> None:
            c = cand(t)
            # First bullish leg of a kind wins the slot; keep the richest detail.
            existing = c["legs"].get(leg)
            if existing is None:
                c["legs"][leg] = {"source": leg, "direction": direction, "detail": detail}
            elif len(detail) > len(existing.get("detail", "")):
                existing["detail"] = detail

        def add_conflict(t: str, reason: str) -> None:
            c = cand(t)
            if reason not in c["conflicts"]:
                c["conflicts"].append(reason)

        # market caps from the universe rows (for ubiquity / context)
        for r in universe_rows:
            t = _ticker_of(r)
            if t:
                mc = r.get("market_cap")
                if isinstance(mc, (int, float)):
                    cand(t)["market_cap"] = mc

        # ── (a) TREND leg — collapse ALL correlated momentum sources into one ──
        # Sources: scanner survivors (non-core, directional), momentum picks.
        trend_tickers: dict[str, str] = {}  # ticker -> detail
        for s in scanner_signals:
            if not isinstance(s, dict):
                continue
            t = _ticker_of(s)
            if not t:
                continue
            strategy = s.get("strategy", "")
            direction = s.get("direction", "")
            if _direction_is_bearish(direction):
                add_conflict(t, f"bearish scanner ({strategy or 'signal'})")
                continue
            # Core-watchlist NEUTRAL rows are not a real trend leg.
            if strategy == "Core Watchlist" and not _direction_is_bullish(direction):
                continue
            detail = strategy or "scanner"
            sc = s.get("score")
            if isinstance(sc, (int, float)):
                detail = f"{detail} (score {sc})"
            trend_tickers.setdefault(t, detail)

        for p in _as_list(momentum_picks.get("picks")):
            if not isinstance(p, dict):
                continue
            t = _ticker_of(p)
            if not t:
                continue
            grade = p.get("grade") or ""
            sc = p.get("score")
            bits = ["momentum"]
            if grade:
                bits.append(str(grade))
            if isinstance(sc, (int, float)):
                bits.append(f"score {sc}")
            # momentum picks are a long-idea finder → bullish by construction
            trend_tickers[t] = " ".join(bits)

        for t, detail in trend_tickers.items():
            add_leg(t, TREND, "bullish", detail)

        # ── (b) TRIANGLE leg — breakout / forming (long structure) ──
        for tr in triangle_signals:
            if not isinstance(tr, dict):
                continue
            t = _ticker_of(tr)
            if not t:
                continue
            sig_type = tr.get("signal_type") or ""
            pattern = tr.get("pattern") or ""
            score = tr.get("triangle_score")
            detail = sig_type or pattern or "triangle"
            if isinstance(score, (int, float)):
                detail = f"{detail} (score {score:.0f})"
            add_leg(t, TRIANGLE, "bullish", detail)
            # confirmed breakouts carry a small magnitude bonus
            if pattern == "confirmed" or sig_type == "triangle_breakout":
                cand(t)["extra"] += 0.3

        # ── (b2) DOWNTREND-BREAKOUT leg — falling-trendline reversal (Michael's edge) ──
        # Only the fresh-actionable tiers drive confluence: confirmed (just broke the
        # multi-month falling line) and forming (coiling under it). extended (entry
        # passed) and retest (sitting on the line) are detected + persisted upstream
        # but NOT counted here — honors the "no extended names in the watchlist" rule.
        # Bullish-only; never a standalone buy.
        for db in downtrend_break_signals:
            if not isinstance(db, dict):
                continue
            t = _ticker_of(db)
            if not t:
                continue
            pattern = db.get("pattern") or ""
            if pattern not in ("confirmed", "forming"):
                continue
            if pattern == "confirmed":
                bd = db.get("break_date")
                detail = f"downtrend breakout (confirmed{', broke ' + str(bd) if bd else ''})"
                cand(t)["extra"] += 0.3  # fresh structural reversal → magnitude bonus
            else:
                detail = "downtrend breakout (forming — coiling under the line)"
            add_leg(t, DOWNTREND_BREAKOUT, "bullish", detail)

        # ── (c) FLOW leg — bullish skew adds, bearish = conflict, SHORT_DATED trap ──
        for fl in options_flow_signals:
            if not isinstance(fl, dict):
                continue
            t = _ticker_of(fl)
            if not t:
                continue
            skew = (fl.get("skew") or "balanced").lower()
            short_dated = bool(fl.get("has_short_dated"))
            top_score = fl.get("top_score")
            if skew == "bearish":
                add_conflict(t, "bearish options flow")
                continue
            if skew != "bullish":
                continue  # balanced → no clean directional leg
            if short_dated:
                # 0-3 DTE trap (~23% hit) — penalize, flag, do NOT count as clean.
                add_conflict(t, "flow bullish but SHORT_DATED (0-3 DTE trap)")
                cand(t)["extra"] -= 0.4
                continue
            detail = "bullish flow"
            if isinstance(top_score, (int, float)):
                detail = f"bullish flow (top {int(top_score)})"
            add_leg(t, FLOW, "bullish", detail)
            if fl.get("has_fresh_position"):
                cand(t)["extra"] += 0.2

        # ── (d) INSTITUTIONAL leg — 13F buying adds, selling = conflict ──
        for b in _as_list(institutional.get("top_buying")):
            t = _ticker_of(b)
            if not t:
                continue
            funds = b.get("funds") or b.get("fundCount")
            detail = "13F buying"
            if isinstance(funds, (int, float)):
                detail = f"13F buying ({int(funds)} funds)"
            add_leg(t, INSTITUTIONAL, "bullish", detail)
        for s in _as_list(institutional.get("top_selling")):
            t = _ticker_of(s)
            if t:
                add_conflict(t, "13F selling")

        # ── (e) REGIME — context only, never a leg ──
        regime_label = ""
        if isinstance(market_regime, dict):
            regime_label = str(market_regime.get("regime") or "")

        # ── assemble + score ──
        watchlist: list[dict] = []
        for t, c in reg.items():
            leg_rows = list(c["legs"].values())
            n_legs = len(leg_rows)
            conflict = bool(c["conflicts"])
            conflict_reason = "; ".join(c["conflicts"]) if conflict else ""

            # base score from weighted independent legs + magnitude/quality extra
            score = sum(_LEG_WEIGHT.get(lr["source"], 1.0) for lr in leg_rows)
            score += c["extra"]
            if conflict:
                score -= 0.75 * len(c["conflicts"])  # amber penalty

            # include conflict pseudo-legs in the visible leg list (direction bear)
            display_legs = leg_rows + [
                {"source": "conflict", "direction": "bearish", "detail": r}
                for r in c["conflicts"]
            ]

            watchlist.append({
                "ticker": t,
                "n_legs": n_legs,
                "legs": display_legs,
                "score": round(score, 3),
                "conflict": conflict,
                "conflict_reason": conflict_reason,
                "market_cap": c["market_cap"],
                "regime": regime_label,
            })

        # Sort: most agreeing legs first, then score. Conflicted names sink within
        # a tier via the score penalty.
        watchlist.sort(key=lambda r: (r["n_legs"], r["score"]), reverse=True)

        # Collapse the single-leg long tail: keep multi-leg rows in full, and cap
        # the 0/1-leg names to the strongest few so the watchlist leads with
        # decisions, not completeness.
        multi = [r for r in watchlist if r["n_legs"] >= 2]
        singles = [r for r in watchlist if r["n_legs"] < 2]
        SINGLE_TAIL_CAP = 8
        trimmed = multi + singles[:SINGLE_TAIL_CAP]

        return {"watchlist": trimmed, "generated": len(multi)}
    except Exception as e:
        print(f"[confluence] compute_confluence failed: {e}")
        return {"watchlist": [], "generated": 0}


# ──────────────────────────────────────────────────────────────────────────
# 2) MIGRATION
# ──────────────────────────────────────────────────────────────────────────
def _ladder_state_today(ticker: str, namespaces_today: dict[str, Iterable[str]]) -> str | None:
    """Most-mature ladder state a ticker occupies TODAY across the namespaces.

    Triangle is split into forming vs breakout via the 'triangle' namespace
    membership PLUS the per-leg detail isn't available here, so the caller passes
    a 'triangle_breakout' / 'triangle_forming' namespace if it wants the split;
    otherwise a bare 'triangle' namespace maps to triangle_breakout (most mature
    triangle state). Returns the highest-ranked state, or None.
    """
    states: list[str] = []
    present = {ns for ns, tickers in namespaces_today.items()
               if ticker in {_sym(x) for x in _as_list(list(tickers))}}

    if "momentum" in present or "scanner" in present:
        states.append("momentum")
    if "flow" in present:
        states.append("flow")
    if "triangle_breakout" in present:
        states.append("triangle_breakout")
    if "triangle_forming" in present:
        states.append("triangle_forming")
    if "triangle" in present and "triangle_breakout" not in present and "triangle_forming" not in present:
        states.append("triangle_breakout")
    if "universe" in present:
        states.append("universe")

    if not states:
        return None
    return max(states, key=lambda s: _LADDER_RANK.get(s, -1))


def _find_row(ticker: str, classified: dict) -> dict | None:
    """Locate a ticker's row in a classified namespace dict.

    Prefers the complete `all` list (every tracked ticker, including the 4-9d
    "watch" band the named buckets omit); falls back to the named buckets for
    older classified shapes that predate `all`. Returns the row dict or None.
    """
    if not isinstance(classified, dict):
        return None
    for row in _as_list(classified.get("all")):
        if isinstance(row, dict) and _sym(row.get("ticker")) == ticker:
            return row
    for cls in ("lifers", "high_conviction", "new_signals"):
        for row in _as_list(classified.get(cls)):
            if isinstance(row, dict) and _sym(row.get("ticker")) == ticker:
                return row
    return None


def _persistence_class_for(ticker: str, classified: dict) -> str:
    """Find a ticker's persistence class within one classified namespace dict."""
    row = _find_row(ticker, classified)
    if row is None:
        return "absent"
    # Prefer the explicit class label (set by classify_history); else derive.
    cls = row.get("class")
    if cls in ("lifer", "high_conviction", "new", "watch"):
        return cls
    days = row.get("days")
    days = int(days) if isinstance(days, (int, float)) else 0
    if days >= 20:
        return "lifer"
    if days >= 10:
        return "high_conviction"
    if days <= 3:
        return "new"
    return "watch"


def _streak_for(ticker: str, classified: dict) -> int:
    row = _find_row(ticker, classified)
    if row is None:
        return 0
    s = row.get("streak")
    return int(s) if isinstance(s, (int, float)) else 0


def _days_for(ticker: str, classified: dict) -> int:
    """Window day-count for a ticker in one classified namespace dict (0 if absent)."""
    row = _find_row(ticker, classified)
    if row is None:
        return 0
    d = row.get("days")
    return int(d) if isinstance(d, (int, float)) else 0


def _established_before_today(ticker: str, classified: dict) -> bool:
    """True if the ticker appeared in this namespace on at least one PRIOR day.

    days>=2 means it was recorded today PLUS at least one earlier day (the
    namespaced history is updated for today before this read), so it was present
    before today — i.e. a valid 'from' anchor for a maturation move. We use the
    raw day-count rather than the persistence class, because a short (≤3d) but
    real prior presence is still 'established' for ladder purposes even though it
    classifies as 'new'.
    """
    return _days_for(ticker, classified) >= 2


def compute_migration(
    *,
    namespaces_today: dict[str, Iterable[str]] | None = None,
    namespaces_persistence: dict[str, dict] | None = None,
    market_caps: dict[str, float] | None = None,
    date: str = "",
) -> dict:
    """Detect day-over-day MATURATION (not "ticker reappeared").

    Two complementary detectors:
      1. Maturation ladder — a ticker that, across the namespaces, has climbed the
         ordered sequence universe → triangle_forming → triangle_breakout → flow →
         momentum vs where it sat in yesterday's history. We infer "yesterday's"
         state from the namespaced persistence (a ticker already a lifer/high-conv
         in a more-mature namespace was there yesterday; a ticker that is 'new'
         today in the most-mature namespace just arrived → that's the migration).
      2. Persistence-class transitions — new → high_conviction → lifer within a
         namespace (escalating conviction).

    Mega-cap ubiquity is suppressed: names ≥ MEGA_CAP_FLOOR (when cap is known)
    are dropped from the feed.

    Returns {"migrations": [row, ...], "migration_of_the_day": row|None}.
    Each row: {ticker, from_state, to_state, direction, streak, note}.
    """
    try:
        namespaces_today = namespaces_today if isinstance(namespaces_today, dict) else {}
        namespaces_persistence = namespaces_persistence if isinstance(namespaces_persistence, dict) else {}

        # normalize today's sets to upper-case symbol sets
        today_sets = {
            ns: {_sym(x) for x in _as_list(list(tickers)) if _sym(x)}
            for ns, tickers in namespaces_today.items()
        }

        # all candidate tickers that fired in any namespace today
        all_today: set[str] = set()
        for s in today_sets.values():
            all_today |= s

        # market-cap lookup for ubiquity suppression. Prefer the explicit
        # market_caps map (passed from the universe scan); fall back to a
        # '_market_caps' map embedded in the universe persistence dict if present.
        caps = {_sym(k): v for k, v in (market_caps or {}).items()}
        if not caps:
            uni = namespaces_persistence.get("universe")
            if isinstance(uni, dict) and isinstance(uni.get("_market_caps"), dict):
                caps = {_sym(k): v for k, v in uni["_market_caps"].items()}

        def _is_mega(ticker: str) -> bool:
            mc = caps.get(ticker)
            if isinstance(mc, (int, float)):
                return mc >= MEGA_CAP_FLOOR
            # Cap unknown (not in the universe scan) → fall back to the denylist.
            return ticker in _KNOWN_MEGA_CAPS

        migrations: list[dict] = []

        for ticker in sorted(all_today):
            if _is_mega(ticker):
                continue

            to_state = _ladder_state_today(ticker, today_sets)
            if to_state is None:
                continue
            to_rank = _LADDER_RANK.get(to_state, -1)

            # Infer yesterday's most-mature state from persistence: the highest
            # ladder state in a namespace where the ticker was ALREADY established
            # before today (appeared on ≥1 prior day → a valid 'from' anchor).
            from_state = None
            from_rank = -1
            # map namespace -> ladder state(s) it implies
            ns_to_states = {
                "universe": ["universe"],
                "triangle": ["triangle_breakout"],
                "triangle_forming": ["triangle_forming"],
                "triangle_breakout": ["triangle_breakout"],
                "flow": ["flow"],
                "momentum": ["momentum"],
                "scanner": ["momentum"],
            }
            best_streak = 0
            for ns, states in ns_to_states.items():
                classified = namespaces_persistence.get(ns)
                if not _established_before_today(ticker, classified):
                    continue  # not present before today → not a maturation anchor
                streak = _streak_for(ticker, classified)
                for st in states:
                    rank = _LADDER_RANK.get(st, -1)
                    if rank > from_rank and rank < to_rank:
                        from_rank = rank
                        from_state = st
                        best_streak = max(best_streak, streak)

            # --- Maturation event: climbed at least one ladder rung ---
            if from_state is not None and to_rank > from_rank:
                migrations.append({
                    "ticker": ticker,
                    "from_state": from_state,
                    "to_state": to_state,
                    "direction": "bullish",
                    "streak": best_streak,
                    "note": f"matured {from_state} → {to_state}"
                            + (f" (streak {best_streak}d)" if best_streak else ""),
                    "_kind": "maturation",
                    "_rank_gain": to_rank - from_rank,
                })
                continue

            # --- Persistence-class escalation (conviction transition) ---
            # If not a ladder move, surface a new→high_conviction→lifer step in the
            # most-mature namespace the ticker fired in today.
            best_ns = None
            best_state_rank = -1
            for ns, states in ns_to_states.items():
                if ticker in today_sets.get(ns, set()):
                    r = max((_LADDER_RANK.get(st, -1) for st in states), default=-1)
                    if r > best_state_rank:
                        best_state_rank = r
                        best_ns = ns
            if best_ns is not None:
                classified = namespaces_persistence.get(best_ns)
                cls = _persistence_class_for(ticker, classified)
                streak = _streak_for(ticker, classified)
                if cls == "high_conviction":
                    migrations.append({
                        "ticker": ticker,
                        "from_state": "new",
                        "to_state": "high_conviction",
                        "direction": "bullish",
                        "streak": streak,
                        "note": f"conviction rising in {best_ns} (streak {streak}d)",
                        "_kind": "persistence",
                        "_rank_gain": 0,
                    })
                elif cls == "lifer":
                    migrations.append({
                        "ticker": ticker,
                        "from_state": "high_conviction",
                        "to_state": "lifer",
                        "direction": "bullish",
                        "streak": streak,
                        "note": f"now a lifer in {best_ns} (streak {streak}d)",
                        "_kind": "persistence",
                        "_rank_gain": 0,
                    })

        # Rank migrations: biggest ladder gain first, then maturation over
        # persistence, then longest streak. Pick the migration of the day.
        def _mig_key(m: dict) -> tuple:
            kind_rank = 1 if m.get("_kind") == "maturation" else 0
            return (m.get("_rank_gain", 0), kind_rank, m.get("streak", 0))

        migrations.sort(key=_mig_key, reverse=True)
        migration_of_the_day = migrations[0] if migrations else None

        # strip internal keys from the public payload
        def _clean(m: dict) -> dict:
            return {k: v for k, v in m.items() if not k.startswith("_")}

        return {
            "migrations": [_clean(m) for m in migrations],
            "migration_of_the_day": _clean(migration_of_the_day) if migration_of_the_day else None,
        }
    except Exception as e:
        print(f"[confluence] compute_migration failed: {e}")
        return {"migrations": [], "migration_of_the_day": None}
