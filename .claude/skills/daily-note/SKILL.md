---
name: daily-note
description: >-
  The Jefferson Cut daily Substack Note: one short note a day, a trader-desk scene that shows a
  principle through a mistake and its dollar cost, never preaching. Drafted one at a time with
  Michael, then queued on coolify for a random 6:00 to 6:30 AM ET slot. Self-improving: every run
  folds Michael's edits and the notes' engagement back into this file and commits it. Use when
  Michael says "daily note", "tomorrow's note", "next note", "jefferson cut", "queue the note", or
  asks what a day's quotes are.
---

# Daily Note (The Jefferson Cut)

One note per day. Michael reviews every one before it is queued. **Never batch-queue notes he has
not approved**, and never generate all 366 days. He wants to go through them one at a time.

## Where things live

| What | Where |
|---|---|
| 366-day calendar row (posture, principle, trap, anchor) | `~/battle/tmp/Daily_Key_Points_Index.md`, or `~/battle/tmp/today "Oct 3"` (adds the live VIX veto) |
| Original Greene text for a day | `~/battle/tmp/The Daily Laws 366 Meditations.md`, heading `## October N` |
| Original Daily Reflections text | `~/battle/tmp/Daily Reflections.md`, heading `## October N` |
| Linter + canonical numbers | `~/battle/tmp/lint_dispatch.py` (reads `rules.json` from its own dir) |
| Methodology | `~/battle/tmp/THE_JEFFERSON_CUT_METHODOLOGY.md` |
| Older model drafts (reference only, never reuse text) | `~/battle/tmp/Substack_Notes_Oct_*` |
| Queue + poster | `tools/note_queue.py`, run **on coolify** (`ssh coolify`, `~/mphinance`). `substack-note-queue.timer` there fires every 5 min, linger on, Substack auth works there. |
| What has been queued/posted | `LOG.md` next to this file |

`~/battle/tmp/` is local-only and holds copyrighted source texts plus a credential file
(`telegram_bot`). Never copy anything from it into this repo, and never print `telegram_bot`.

## The loop, every run

1. **Self-improve first (no input needed).** On coolify run
   `python3 tools/substack_gateway.py notes 2` and match the ranked notes against `LOG.md`. Record
   likes/restacks/replies for every logged note in `LOG.md`. If a pattern shows up across 3+ notes
   (a hook style, a length, parable vs scene), add one line to **Learned** below with the numbers.
   Also diff what actually posted (from the gateway output) against the text in `LOG.md`; any line
   Michael changed in the app is a voice correction and goes into **Learned** too.
2. **Pull the day.** Show Michael the calendar row and the original quotes (Greene epigraph +
   Daily Law line, Daily Reflections quote). Quote, do not paraphrase.
3. **Draft one note** in the voice rules below. Read `VOICE.md` first if it has not been read this
   session. Offer two shapes when it helps: a straight desk scene, and a short parable (see Shapes).
4. **Lint.** Write to the scratchpad in the `### October N` format and run
   `python3 ~/battle/tmp/lint_dispatch.py <file>` until 0 errors, 0 warnings. Recompute every
   number by hand too; the linter only checks `rules.json` consistency, not arithmetic.
5. **Tell-audit before showing** (memory: voice-audit-before-showing). Read it once as a hostile
   reader hunting the Learned tells. Fix them before Michael sees it.
6. **Iterate with Michael.** Every line he flags becomes a Learned rule immediately, worded as the
   general pattern, not the specific sentence.
7. **Queue on approval only.** Random minute 0 to 30, so the time looks human:
   ```bash
   M=$(( RANDOM % 31 )); T=$(printf "YYYY-MM-DD 06:%02d" $M)
   ssh coolify "cat > /tmp/note.md" < note.md        # body only: no '#' headers, no '>'
   ssh coolify "cd mphinance && python3 tools/note_queue.py add '$T' /tmp/note.md && python3 tools/note_queue.py list"
   ```
   The queue renders `**bold**`, `*italic*`, `[text](url)` and blank-line paragraphs only, so the
   hook goes in as a bold line, not a blockquote.
8. **Log + commit.** Append the final text, queue id and slot to `LOG.md`, save any new Learned
   lines here, then `git add .claude/skills/daily-note && git commit` (only these paths, the repo
   has a lot of unrelated untracked files). Commit without asking; this skill owns its own folder.

## Voice rules (the brief)

Michael's north star, his words: *"Tradition Eleven says attraction rather than promotion. If you
lecture traders about spiritual axioms, they roll their eyes. But when you describe how an ego trip
after six green trades tempts a man to oversize and blow a 30% cash buffer, any trader who has ever
felt the sting of a margin call gets chills down their spine."*

- A concrete scene a trader feels in the gut, with real `rules.json` arithmetic. The principle is
  shown by the mistake and its cost, never stated.
- No Greene, AA, steps or spiritual vocabulary. First person only, no "you" (linter enforces).
- Blunt about the mechanism, humble about himself. Fragments and comma splices are allowed;
  bold the numbers only; endings do not need to resolve.
- No invented first-person history stated as fact ("68 trades this year"). Hypotheticals and
  "run it forward" math are fine.
- Sign-off `~ Michael` on its own line.

## Shapes

- **Desk scene.** One trade, one moment, one dollar figure that hurts. The Oct 2 roll-button note
  is the reference.
- **Parable ("a little Hoid").** Third-person story about "a trader", wry, told straight, with a
  last line that turns it back on the narrator ("I know him pretty well."). Good for days whose
  principle would otherwise come out preachy. Never name Hoid or quote Sanderson.
- **Weekend days** (markets closed): use a non-trading scene, such as rule-writing on Saturday or
  the weekly review, instead of pretending it is a Tuesday.
- **Hook.** A real source epigraph (e.g. the Greene day's Pericles or Chekhov line, attributed to
  the original author, never to Greene) beats an AI-minted aphorism. Michael's read on minted
  hooks: "I used AI to create an awesome quote and here's my explanation." Allowed, but prefer the
  real one when the day has a good epigraph.

## Learned

Tells Michael has flagged, newest last. Each one is a pattern to hunt, not just the sentence.

- 2026-10-01: **Parallel-fragment pair that restates the hook** ("The button got faster. The
  flinch did not change at all."). Cut it; the hook already said it.
- 2026-10-01: **Slogan closer** that echoes the hook ("Faster plumbing, same flinch."). End on a
  fact or an unresolved line instead.
- 2026-10-01: **The fix/lesson paragraph** ("So the stop goes in as a resting order..."). Showing
  the remedy turns attraction into promotion. Stop at the cost.
- 2026-10-01: **Wry explainer tag** on the last line ("which is the whole sales pitch"). Explaining
  the irony kills it. Let the numbers carry it.
- 2026-10-01: **"Here is what that X does."** setup sentence before the math. Just start the math.
- 2026-10-01: Three-beat fragment runs ("One tap... One swipe...") are borderline; watch them.
