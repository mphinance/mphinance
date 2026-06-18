# Autonomy: Next Repos Audit (Plan Q3)

_Date: 2026-06-18_

Answers open question #3 in [`docs/AUTONOMY_PLAN.md`](../AUTONOMY_PLAN.md): **which
repos beyond mphinance + TickerTrace get a nightly loop?** The live model is
fixed — **PR for the trail, CI for the gate, auto-merge on green, degrade-safe
on red** — so the only question per repo is: is there a gate to merge on, is the
downside bounded and reversible, and does a loop actually feed the work.

The one hard line from plan section 5: **never auto-publish to a real audience,
never let a bot touch real money / real orders.** Any repo that does gets graded
"do not loop," full stop — a green build does not make a live trade or a public
post reversible.

`mphinance` and `TickerTrace` are already live and excluded here.

---

## Summary

| Repo | What it is | CI gate? | Bounded & reversible? | Verdict |
|------|-----------|----------|----------------------|---------|
| **scanline** | Market screener + quant-analytics layer over TradingView; app + static GitHub Pages demo; 16-tool MCP | **Yes** — offline `pytest` + `node --test` on every PR (`ci.yml`) | Yes — local app + public *demo* only, no money, no orders, fully revertible | **SEND IT** |
| **alpha-skills** | Suite of 113 agent "skills" (prompts/scripts) for quant + content; a daily-oracle cron | No test gate; only a scheduled oracle workflow | Mostly — prompt/markdown assets, revertible. Oracle hits OpenRouter (cost, not audience) | **Needs CI first** (build/lint gate) |
| **traderdaddy-bridge → `ibkr/mur`** | "Make Us Rich" — autonomous multi-LLM swarm that places **real IBKR orders** | Yes — `compileall` + real-bug ruff on every push/PR | **NO** — live account `U23401712`, real money, real orders | **DEFER (hard line)** |
| **TraderDaddy-Pro---Whop** | Production options-trading platform (Next.js + Express), deployed, real users + Discord | No hard build/test gate on PRs — only AI-*advisory* workflows | **NO** — production, real audience, paid product | **DEFER (hard line + no gate)** |
| **ask-sam** | Spec/docs for packaging Sam as a paid multi-tenant Discord bot ($7.99/mo on Whop) | No | Docs-stage today, but the product ships to a paying audience | **Defer** (pre-code; ships to real audience) |
| **traderlady** | Static landing page (React/Vite) for a Discord bot, on Cloudflare Pages | No (static build) | Public marketing page — low traffic, revertible, but it *is* a public face | **Defer** (thin backlog, public-facing copy) |
| **fire / crossover** | Static FIRE calculator, browser-only, GitHub Pages | `deploy.yml` only (no test gate) | Yes — static, no money, no orders | **Defer** (near-done, ~no backlog) |
| **alpha-command-center** | Strategy alert engine + **Tradier order execution**, prod on Railway | No PR test gate found | **NO** — real order execution, production | **DEFER (hard line)** |

**Net:** one clean "send it" (**scanline**), one "needs CI first" (**alpha-skills**),
and the rest defer. Three of the deferrals are non-negotiable: `mur`,
`alpha-command-center`, and the live half of TD Pro all touch real money, real
orders, or a real paying audience. That is exactly the irreversible thing plan
section 5 says stays human. A green CI does not un-place a trade or un-send a
post.

---

## Send it

### scanline — `/home/mph/scanline`

Everything the live model needs is already here. `ci.yml` runs an **offline**
test suite on every push and PR (`pytest tests/ -m "not live"` + node tests on
the frontend store/openin logic); live TradingView tests are deliberately
excluded so the gate is deterministic and network-free. There is a real, growing
backlog — computed columns, factor scoring, in-result stats, more MCP tools,
the showcase — so a loop builds, it doesn't churn. Downside is bounded: it's a
local app plus a *static* GitHub Pages demo. No money, no orders, no posting in
anyone's name; every change is a revertible diff. It already has `AGENTS.md` +
`CLAUDE.md` for the loop to read first. (Two housekeeping notes before wiring:
CI triggers on `master` while the repo is currently on a feature branch, and the
auto-merge step should target whatever the real default branch is — confirm
`master` vs `main`.)

**Nightly brief (draft):**
> You are the scanline nightly builder. Read `AGENTS.md` and `CLAUDE.md` first.
> Ship **one** coherent, self-contained improvement to the screener or its
> analytics: a new computed column, a factor/score, an in-result stat, a new MCP
> tool, a showcase widget, or a real bug fix. Add or update tests so the change
> is covered by the offline suite. Open a PR; the `ci.yml` gate (`pytest -m "not
> live"` + the node tests) is the wall — let it auto-merge on green, leave it
> open on red. One change per run; never touch the `live`-marked tests or hit
> the network in CI. If there's nothing worth building, open an issue with three
> ranked ideas instead of forcing a diff.

---

## Needs CI first

### alpha-skills — `/home/mph/alpha-skills`

The candidate is plausible — it's a big pile of agent skills (prompts + helper
scripts) and the downside is mostly markdown/script edits, which are revertible.
But there is **no gate to merge on**: the only workflow is a scheduled
`daily-oracle.py` cron, not a test/build check on PRs. Without a gate the loop
would be auto-merging unvalidated changes, which breaks the "CI for the gate"
contract. Activity is also thin (8 commits, last early May), so the backlog is
real but not urgent. Stand up a lightweight gate first — e.g. `python -m
compileall` over the scripts plus a YAML/front-matter lint over the skill files
(the same cheap "does it parse" gate `mur`'s `ci.yml` uses). Once a PR-triggered
check exists, this becomes a clean "send it." The oracle's OpenRouter calls are
a cost concern, not an audience concern, so they don't trip section 5.

---

## Defer (and why)

- **`ibkr/mur` (the "traderdaddy-bridge" candidate)** — has a fine CI gate, but
  it places **real orders on a live IBKR account** ($1,101 NetLiq, dynamic
  per-trade cap). This is the exact thing plan section 5 walls off. A passing
  build never makes a placed trade reversible. Improve it with a human in the
  loop; never an unattended auto-merge.
- **`TraderDaddy-Pro---Whop`** — production platform, real paying users, Discord
  audience, and **no hard build/test gate** on PRs (the AI workflows are
  advisory, they don't block). Two independent disqualifiers: it ships to a real
  audience, and there's nothing to merge on. If a build/typecheck/test gate ever
  lands, a loop could be scoped to a *non-shipping* internal area — but not the
  product itself.
- **`alpha-command-center`** — executes **Tradier orders** in production on
  Railway. Same hard line as `mur`.
- **`ask-sam`** — still spec/docs only (5 commits). When it grows code it will
  ship to a paying audience, so it inherits the section-5 line. Revisit when
  there's a non-shipping core with tests.
- **`traderlady`** — static marketing page. Low risk, but the backlog is thin
  and it's public-facing copy (words people see). Marginal feed-the-work value.
- **`fire` / crossover** — static, safe, but essentially finished (3 commits,
  no test gate). A loop would churn, not build.

---

## Recommendation

Wire **scanline** into the existing loop shape now — it's the only candidate
that's both gated and clearly off the section-5 hard line, with a real backlog.
Put **alpha-skills** one cheap CI gate away from joining it. Hold everything that
touches money, orders, or a live audience on the human side of the trigger,
exactly as the plan intends.
