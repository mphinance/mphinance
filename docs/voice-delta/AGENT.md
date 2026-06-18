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
- Stay inside `docs/voice-delta/` and `/VOICE-DELTA.md`. No other files.
