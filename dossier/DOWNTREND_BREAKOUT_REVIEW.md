# Downtrend-Breakout Screener — Code Review Findings

> Pick-up-later punch list from a high-effort `/code-review` of commit **`6bb1a9a`**
> (`feat(dossier): downtrend-breakout screener`), run 2026-06-21.
> Scope: `dossier/data_sources/downtrend_breakout.py`, `downtrend_breakout_chart.py`,
> and the `generate.py` / `confluence.py` edits.
>
> No crashers. Pipeline-integration wiring (scoping, the new `compute_confluence`
> param, persistence write, `pivot_high` reuse) all verified **safe**. Everything
> below is behavioral / quality. Fix top-down.

## 🔴 Worth fixing — affects whether setups surface correctly

- [ ] **1. `forming` carries the same confluence weight as a confirmed break.**
  `confluence.py` — the new `DOWNTREND_BREAKOUT` leg block adds a full
  `_LEG_WEIGHT[DOWNTREND_BREAKOUT]=1.2` independent leg for `pattern == "forming"`,
  identical to a confirmed reversal. A `forming` setup (price coiling *under* the
  line, not broken yet) + one other leg (e.g. flow) can reach the actionable
  multi-leg watchlist on an unconfirmed setup.
  **Fix:** weight `forming` lighter (e.g. add via a smaller `extra` bonus rather
  than a full leg, or a reduced leg weight), or don't let a `forming`-only name
  count toward the multi-leg threshold. Confirmed should outrank forming.

- [ ] **2. First-break lockout → misses fresh re-breaks (false negatives).**
  `downtrend_breakout.py::fit_descending_line` — the break search
  `for x in range(ni + 1, n): if close > line: broke = x; break` locks onto the
  *first* close-through after the newer anchor. A name that poked above the line
  months ago, fell back under, then broke out cleanly a few days ago returns the
  stale old break → `bars_since > EXTENDED_RECENCY_BARS (35)` → dropped. This
  silently misses exactly the fresh setups the screener exists to catch.
  **Fix:** for the selected line, use the **most recent** decisive close-through
  (or the freshest re-break after a fall-back-under), not the first.

- [ ] **3. `line_now` output field is mislabeled (stale reference).**
  `downtrend_breakout.py::_result` (and the break-tier callers) — for break
  tiers, `line_now` is set to `line_at_break` (the line's value at the *old* break
  bar), and `clearance_pct` is measured against that stale level. So
  `EXTENDED_CLEARANCE_PCT` / `DROP_CLEARANCE_PCT` compare to an out-of-date
  reference, and a name far above *today's* line can dodge the cull.
  **Fix:** report the line extrapolated to the last bar as `line_now`; keep
  `line_at_break` as its own field; decide deliberately which the clearance
  thresholds should use (probably today's line for the DROP cull).

## 🟡 Known follow-ups — review confirms what was already flagged at handoff

- [ ] **4. Migration namespace is write-only.**
  `generate.py` writes `update_persistence(namespace="downtrend_breakout")` but
  the namespace is **not** in `namespaces_today` (stage 10b) nor in
  `confluence.py::MATURATION_LADDER` / `_ladder_state_today`. So history accrues
  but migration never produces a maturation event for a downtrend break.
  **Fix:** add a `downtrend_breakout` rung to `MATURATION_LADDER` (e.g. between
  `universe` and `flow`), map it in `_ladder_state_today`, and add it to
  `namespaces_today` + `namespaces_persistence`.

- [ ] **5. Double yfinance fetch (binding constraint).**
  `generate.py` stages `[6b]` triangle and `[6c]` downtrend build a heavily
  overlapping universe and each fetches 2y daily bars per ticker independently —
  yfinance on the static IP is the rate-limit constraint. `scan_downtrend_break`
  already accepts `hist=`.
  **Fix:** fetch 2y bars once per ticker into a shared cache/dict and pass `hist=`
  into both screeners.

## ⚪ Cleanup — tidy when convenient

- [ ] **6. `fit_descending_line` and `_forming_candidate` are ~90% duplicated.**
  Same `pivot_high` call, pivot-pair loop, span/slope/cut-through filters, scoring.
  Geometry tuning currently has to happen in two places that will drift.
  **Fix:** have `_forming_candidate` reuse `fit_descending_line` with break-search
  disabled (or factor the shared pivot-pair scan into one helper).

- [ ] **7. `_num` / `_rsi` re-implemented; three divergent RSI variants.**
  `dossier/utils/indicators.py` already exports `_rsi` / `_safe`. This module rolls
  its own `_num` + Wilder-EWM `_rsi`, and `downtrend_breakout_chart.py` inlines a
  *third* RSI. A ticker's RSI in the signal dict can disagree with the RSI drawn on
  its chart.
  **Fix:** import the shared helpers; render the chart RSI from the same source.

- [ ] **8. Dead / unused state.**
  `VOL_STRONG = 1.5` is defined but never referenced; `vols` is threaded through
  every `_result(...)` call but never read inside `_result`.
  **Fix:** remove `VOL_STRONG` (or wire it into the strength blend if that was the
  intent) and drop the unused `vols=` param.

### Also noted (low severity, optional)
- `_result` strength `blend` is a bespoke additive point system (magic constants
  35/20/10/15/55) not comparable to other screeners' `signal_strength`. Consider a
  shared strength convention if cross-screener comparison ever matters.
- The `retest` tier is effectively unreachable for a price that retraces to just
  *below* the broken line (`fit` requires `last_close > line_at_break`, else falls
  to `forming`). Minor edge; revisit if retest-of-broken-resistance-as-support
  becomes a wanted signal.
- `fit_descending_line` is ~O(pivots³) (nested cut-through scan per pair); fine at
  current scale, watch if the window or pivot sensitivity widens.

---

**Suggested order:** 1 → 2 → 3 (output correctness), then 4 → 5 (finish the
integration), then 6 → 8 (cleanup). #1 and #2 are the two that actually change
which names surface.
