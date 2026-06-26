# Voice-Delta recurring agent — runbook

The job: keep `/VOICE-DELTA.md` learning from each newly published post. Pure
feed-the-writer. **This agent never writes a public word and never publishes
anything to Substack.** It only studies Michael's edits and sharpens the rules.

Runs weekly (Sunday evening). Opens a PR for Michael to read — it does NOT
auto-merge, because the whole point is his "is this reading me right?" review.

## Steps

1. `cd ~/mphinance && git fetch origin && git checkout -b voice-delta/refresh-<YYYY-MM-DD> origin/main`

2. `python3 docs/voice-delta/refresh.py`
   - Captures any local given-drafts (only finds new ones if run on Michael's box;
     in the cloud the cache isn't present — that's fine, the publish skill already
     commits given drafts at push time).
   - Refreshes `pairs/_archive.tsv` (recent published posts: date | title | slug).
   - Prints which pairs are "awaiting a shipped match."

3. For each pair `awaiting a shipped match`:
   - Read `pairs/<name>/given.md` (its H1 is the machine's title).
   - Find the matching row in `pairs/_archive.tsv` — match by topic/title/date.
     The shipped TITLE is often reworded (e.g. "Five Stocks" → "Four Small Cap
     Multi-Baggers"), so match on subject + date proximity, not string equality.
   - `python3 docs/voice-delta/fetch_shipped.py <slug> > pairs/<name>/shipped.md`
   - If no confident match exists yet (post not published, or ambiguous), leave it
     unmatched and note it in the PR body. Do not force a wrong pairing.

4. For every pair that became complete this run, diff `given.md` vs `shipped.md`
   and update `/VOICE-DELTA.md`:
   - Add receipts under the existing rules (How he rewrites / ADDS / CUTS /
     Consistency).
   - Promote a pattern to a new rule only when it shows up in **≥2 pairs**.
   - Update the pairs table and the `N = ` count at the top.
   - Maintain the **divergence** discipline: if a banned phrase or known-bad tic
     SURVIVED a ship, record it as "survived, not endorsed" — Michael's explicit
     rules outrank the corpus. Never infer permission from absence-of-edit.

5. Commit (`Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`)
   and open a PR with `gh`, title `voice-delta: refresh from <k> new pair(s)`.
   Body = the new receipts found + any unmatched pairs. **Do not merge.**

6. If 0 pairs became complete this run: do nothing, open no PR. (No empty noise.)

## Guardrails

- Never call the pusher, `--publish`, or any Substack write endpoint. Read-only on
  the live site (public `/api/v1/posts`, `/api/v1/archive` only).
- Never edit a `given.md` or a `shipped.md` after capture — they are evidence.
- Stay inside `docs/voice-delta/`, `/VOICE-DELTA.md`, and `/ACCURACY.md`. No other files.

## Accuracy harness (the "prove VOICE-DELTA can be accurate" loop)

The corpus is the evidence; the harness turns it into numbers.

- `score.py` is **deterministic**. It computes (a) token Jaccard between
  `given.md` and `shipped.md` (baseline edit budget), (b) the same for
  `predicted.md` vs `shipped.md` if a prediction exists (the accuracy metric),
  and (c) a rule-hit matrix detecting whether each rule in `/VOICE-DELTA.md`
  fired in the actual diff.  Output: `/ACCURACY.md`.

- `predict.py` is **LLM-driven**.  It packages `given.md` + `/VOICE-DELTA.md`
  into a prompt and asks a model to emit what Michael would most plausibly
  ship.  Uses the `anthropic` SDK + `ANTHROPIC_API_KEY` when available; falls
  back to printing the prompt for hand-piping.  Output: `pairs/<name>/predicted.md`.

- Workflow each refresh: `python3 predict.py --all`, then `python3 score.py`.
  Two new numbers move per pair: `j(P,S)` (accuracy) and `Δ` (gain vs baseline).
  Positive Δ = the rules helped.  The aggregate Δ is the headline.

The harness deliberately scopes the prediction to **editable rules**, not net-new
content.  A pair where the ship added a whole personal-story section the
machine couldn't have written will still get rule-edit credit; the rules are
not blamed for content they cannot generate.

## Diagnosis: capture is the bottleneck, again

v0 wired capture into the publish skill's step 7.  Two cached drafts since
(06-22, 06-23) shipped without ever being committed to the corpus — the cloud
routine saw an empty `origin/main` delta and (correctly) opened no PR.  Root
cause: step 7 didn't run, or its `|| true` swallowed a silent failure.

**Mitigation:** `refresh.py --commit` is now idempotent and self-committing.
Any path that touches `~/.mph-substack-cache/<date>_<slug>/post.md` can call
it as a one-liner and the capture lands in the corpus regardless of which
publish skill (or no skill at all) was used.

If a Sunday refresh has 0 newly-complete pairs and a non-empty
`~/.mph-substack-cache`, the chain to investigate is: was step 7 / the
fallback `refresh.py --commit` ever called for those drafts?
