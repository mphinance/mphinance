# Autonomy Plan: Agents While I Sleep

_Last updated: 2026-06-18_

The plan for what runs unattended across Michael's repos, and the one rule that
governs all of it. Written so a future session (or a future me) can pick this up
cold.

---

## 0. The Principle

**Automate the grunt. Protect the craft. Never automate the words a reader sees.**

The writing stays human, on purpose. Not sentiment: the *tell*. An automated
writer ships the same shape every day. Rotate it, have it ape other writers, the
sameness still leaks, and one day a reader clocks that nobody's home. Publicizing
the struggle and the gains in Michael's own words IS the human signal. Automate
that and you don't save time, you remove the proof a human exists. Same instinct
that kills em dashes and "here's the truth": you can smell a machine, so can the
readers.

Everything else is fair game. Code, tools, screeners, stock research, ideas,
data, prep, distribution, image rendering: send it hard.

The litmus test for any new agent: **does it feed the writer, or replace the
writer?** Feed = build it. Replace = defer or never.

The investing analogy holds only with bounded, reversible downside. These repos
qualify (low traffic, revertible, no real money at the merge step), so the
training wheels come off here. The discipline returns when any of this points at
a production system with real users or real dollars.

---

## 1. Status: What's Live Now (2026-06-18)

| Thing | Repo | State |
|-------|------|-------|
| Free-form improvement loop, opens a PR, auto-merges on green pytest | mphinance | LIVE (`.github/workflows/claude-autonomous.yml`, PR #44) |
| `pytest` CI gate on PRs | mphinance | LIVE (`.github/workflows/ci.yml`, PR #42) |
| "Daily Glow-Up" routine: ready PR, watches own CI, squash-merges on green | TickerTrace | LIVE (cloud routine `trig_01RQi59q535AgYZA49Pkj3oJ`, 15:00 UTC daily) |
| Old draft-PR graveyard cleared (#8, #9, #11, #12, #13, #15) | TickerTrace | DONE, all merged |
| Voice-delta v0 + weekly recurring agent (re-pairs each new post, opens a PR) | mphinance | LIVE (cloud routine `voice-delta-refresh` `trig_01K7bwuff8s1xVYo7ZkRgDTq`, Sun 03:00 UTC; PR #46) |
| Nightly builder: one self-contained screener/analytics change, auto-merge on green CI; IBKR read-only market data attached (no trading) | scanline | LIVE (cloud routine `scanline-nightly-builder` `trig_01N3VdigxVz4hyiYGb7yGFBe`, 08:00 UTC daily) |
| Loop brief widened from chores to building | mphinance | LIVE (PR #47) |
| Next-repos audit (scanline=send, alpha-skills=needs CI, rest defer) | mphinance | DONE (PR #45, `docs/autonomy/next-repos.md`) |

Both loops now do the same shape: **open a PR you can see, land it on green CI,
zero clicks from you.** No more direct-to-main invisibility, no more draft pile
rotting into conflicts.

The model, stated once: PR for the trail, CI for the gate, auto-merge for the
hands-off. Red CI leaves the PR open and nothing lands. It degrades safe.

---

## 2. The Lanes

| Idea | Lane | Verdict |
|------|------|---------|
| Code / tools / screeners / stock research loop | Feeds the work | **SEND IT** (widen the existing loop) |
| Voice-delta agent (learn my edits) | Feeds the writer | **BUILD** (next up) |
| Self-directing roadmap, code/features only | Feeds the work | Send it |
| Engagement / distribution (restacks, shoutouts) | Feeds reach | Send it (comments stay suggest-only) |
| Memory / decision journal across runs | Infrastructure | Send it |
| Auto-drafting full Substack posts | Replaces the writer | **DEFER / NEVER** |
| "One signal, every format" (auto posts + notes + threads) | Replaces the writer | Defer with auto-draft |
| Auto-write the post about the auto-taken trade | Replaces the writer | Drop the writing half, keep the trade/data |

---

## 3. Build Specs

### 3.1 Widen the code/tools/stocks loop  —  SEND IT

The mphinance nightly loop is currently briefed for "one small safe
improvement." Michael said help me on code, tools, stocks, ideas, so widen the
brief from chores to **building**: new screener strategies, new analysis/stat
outputs, new dashboard sections, real tooling, not just tests-and-fixes.

- Keep: PR + auto-merge on green, one coherent change per run, read
  `.github/CLAUDE.md` first, the "if nothing worth doing, report ideas" escape.
- Change: raise the ambition ceiling. Allow bigger diffs when the change is a
  self-contained tool or screener. Bias toward the "Ideas / backlog" list and
  toward things that produce **writing material** (a new screen surfaces new
  things to write about).
- Status: not yet done. One prompt edit to `claude-autonomous.yml`.

### 3.2 Voice-Delta Agent  —  BUILD NEXT

**The idea, sharpened by Michael:** don't mine vague phrasing. Pair every
**AI-given draft** against the **draft he actually shipped** and learn the
*diff*. What he deletes is as much his fingerprint as what he keeps. The delta is
the densest sample of his voice and editing judgment that exists.

**Corpus sources (confirmed 2026-06-18):**

- _Given drafts (the machine's output):_ live in the repo / local cache.
  - `~/.mph-substack-cache/<date>_<slug>/post.md` — cleanest; literally the
    markdown that got pushed. Only ~2 survive locally; more existed.
  - `articles/<project>/substack-post.md`
  - `docs/substack_draft_*.md`, `docs/substack/latest.md`
  - git history: drafts committed then edited (the commit-to-edit diff is a delta
    on its own).
- _Shipped versions (what Michael actually published):_ on
  mphinance.substack.com. His in-editor edits never return to the repo, so the
  live post is the only record of the final form. Fetch via the public post URL
  or the substack-toolkit API.

**Pairing key:** date + slug/title. The cache dir names (`<date>_<slug>`) map to
Substack slugs.

**Honest constraint:** the bottleneck is clean-pair count, not diffing. Probably
~a dozen good pairs, not hundreds. Fine. Voice signal is dense; a dozen real
before/afters is enough to write sharp rules.

**v0 deliverable:** `VOICE-DELTA.md` — not vibes, rules with receipts:
- what he cuts every time (the windup, the hype line, the round number, the em dash)
- what he adds (the cost-him-something beat, the specific figure, the joke)
- how he rewrites openings
Then Michael reads it and says whether it's reading him right. If the signal's
there, wire it as a recurring agent that re-learns from each new published post.
If thin, kill it cheap.

**Rule compliance:** studies his edits to sharpen HIS writing. Never writes a
public word. Pure feed-the-writer.

- Status: **v0 SHIPPED (2026-06-18).** `/VOICE-DELTA.md` written from 4 clean
  before/after pairs (06-17, 06-11, 05-22, 04-25); corpus + reusable fetcher in
  `docs/voice-delta/`. Awaiting Michael's read on whether it's reading him right.
  Open question #1 resolved: public Substack JSON API (no auth) — see below.

### 3.3 Self-directing roadmap (code only)  —  later

A weekly agent reads the repo and what shipped, then writes next week's backlog
the nightly loop pulls from. Decides what to **build**, never what to **write**.
Keeps the small nightly changes laddering toward something instead of brownian
motion.

### 3.4 Engagement / distribution  —  later

Restacks, the cross-writer shoutout relationships (farm reciprocal restacks),
surfacing who to reciprocate with. Moves Michael's work in front of people.
Authors no posts. Comments stay suggest-only (they're words in his name).

### 3.5 Memory / decision journal  —  later

A shared, persistent build log so the fleet stops being a goldfish that wakes
with amnesia every night and starts being a collaborator that remembers what it's
building toward over weeks.

---

## 4. Deferred / Never, and Why

- **Auto-drafting full Substack posts.** Every component already exists in the
  repo (mph-substack-writer, mph-figure, the pusher). Deliberately NOT connected.
  This is the words a reader sees. The tell makes it self-defeating.
- **"One signal, every format."** Auto posts + notes + threads. Auto-draft times
  five. Parked with auto-draft.

These aren't "too risky." They're off-principle. The downside isn't a bug, it's
that the work stops being his.

---

## 5. The One Guardrail That Survives Full Send

Even training wheels off, hold exactly one line: **do not auto-publish to the
real audience, and don't let the engagement bot go feral on the real Substack
account.** Not for code safety. Because the only irreversible thing here is
Michael's name going out on something dumb to real readers, or Substack flagging
the account as spammy and nuking distribution. Everything up to that step runs
wild. The final "post to humans" tap stays human, and it's 10 seconds.

This is the actual shape of "invest while you sleep": let the machine do
everything up to the trade, keep your thumb on the one trigger that's actually
irreversible.

---

## 6. Open Questions / Decisions Needed

1. ~~**Voice-delta fetch path:**~~ **RESOLVED (2026-06-18):** public Substack JSON
   API — `/api/v1/posts/<slug>` for bodies, `/api/v1/archive` for the index, no
   auth. Free portion of paid posts is enough for the above-the-wall delta. The
   authenticated substack-toolkit path is only needed to diff *below* the
   paywall; deferred. See `docs/voice-delta/fetch_shipped.py`.
2. **Loop ambition ceiling:** how big a diff is too big for an unattended merge
   on mphinance? Current soft cap is ~150 lines; widening 3.1 means raising it.
3. **Other repos:** which beyond mphinance + TickerTrace get a nightly loop?
   (scanline, traderdaddy-bridge, alpha-skills were floated. Each needs a CI
   check to gate on, or the routine self-validates by building.)

---

## 7. Next Actions (in order)

1. ~~Build the **voice-delta v0**~~ **DONE 2026-06-18** — `/VOICE-DELTA.md`
   shipped from 4 pairs (PR #46, merged) + weekly `voice-delta-refresh` routine.
   ← *Michael's read pending: is it reading him right?*
2. ~~**Widen the mphinance loop** brief (3.1)~~ **DONE 2026-06-18** (PR #47, merged).
3. ~~Decide the next repos (Q3) and stand up routines.~~ **DONE 2026-06-18** —
   audit in `docs/autonomy/next-repos.md` (PR #45). **scanline** stood up as a
   nightly cloud routine (`scanline-nightly-builder`, auto-merge on green CI,
   IBKR read-only market data attached per Michael — no order/trade tools).
   Remaining: **alpha-skills** is one cheap CI gate away from qualifying; the
   money/order/audience repos (mur, alpha-command-center, TD-Pro shipping) stay
   deferred on the section-5 hard line.

## 8. What's next (post-list)

- **alpha-skills**: add a compile/lint CI gate, then stand up its loop (the only
  remaining "feeds the work" candidate not blocked by the hard line).
- **Self-directing roadmap (3.3)** and **memory/decision journal (3.5)**: still
  later — the fleet now has three repos building; a shared backlog keeps them
  laddering instead of doing brownian motion.
