---
name: voice-interview
description: >-
  Interview Michael out loud, one question at a time, against a post outline so
  the draft is built from his actual spoken words instead of machine prose.
  Claude drafts the outline, asks ~2 targeted questions per section (aimed at
  the stuff only he has: the origin story, the stakes, where he was wrong, the
  physical metaphor, the live number), saves every answer verbatim to a
  transcript, then assembles the draft from his sentences with only light
  cleanup. Built for Claude Code voice mode (/voice dictation). Use when
  Michael says "interview me", "voice interview", "let me talk it out", "ask me
  questions for this post", "get my voice in this draft", or starts a Substack
  post and wants his words in it rather than a machine draft.
---

# Voice Interview → Draft

The machine is good at scaffolding and bad at the parts that make a post his.
[VOICE-DELTA.md](../../../VOICE-DELTA.md) shows where his edit budget goes on
every shipped draft: **stakes and confessions, the real-life origin story,
self-corrections, warm physical metaphors, the live tape, time compression.**
None of that can be generated from an outline. It has to come out of his mouth.

So this skill does not ask "what do you want to say about section 3?" It asks
for the specific things the machine would otherwise invent badly, captures the
answers word for word, and builds the draft out of them.

Read [VOICE.md](../../../VOICE.md) and [SUBSTACK.md](../../../SUBSTACK.md)
before phase 4. (Running outside this repo via a symlink? Read them from the
mphinance checkout; if you can't find them, say so rather than guessing.)

---

## Phase 0: Topic → outline (Claude drafts it)

1. Get the topic in one line. If he already dictated a rambling pitch, that
   pitch **is** the first answer: save it to the transcript (Phase 2 format)
   under `## Pitch` before doing anything else.
2. Pick the slug and working directory: `docs/articles/<slug>/`.
3. Draft a **short** outline: title idea, category-mix subtitle guess, and
   4 to 6 sections, each one line of intent. Follow the SUBSTACK.md skeleton
   loosely (opener, context, meat, the turn, CTA), don't force every slot.
4. Show it and ask for a thumbs up or changes. He may dictate the changes.
   Keep this to one round unless he asks for more; the interview will reshape
   the outline anyway.
5. Save it to `docs/articles/<slug>/outline.md`.

## Phase 1: Plan the questions (silently)

Default is **quick: about 2 questions per section**, ~10 to 15 minutes total.
If he says "go deep", allow 3 to 5 per section plus follow-ups.

For each section, pick the questions from this bank that fill the biggest gap.
Rewrite each one to be concrete to the section. A question that could be asked
about any post is a bad question.

| Gap (what the machine can't write) | Question shapes |
|---|---|
| **Origin / life as alt-data** | "What did you actually see or notice that sent you to look at this?" "Where were you when this clicked?" |
| **Stakes** | "What's riding on this for you, the real account or the real reason?" "Why does this one bug you?" |
| **Confession / the miss** | "Where were you wrong on this, or almost wrong?" "What's the dumb version of this you did first?" |
| **Self-correction** | "Is that always true, or mostly?" (Ask after a big claim he just made.) |
| **Physical metaphor** | "What's this like, something you could touch or would see at the bar?" |
| **The live tape** | "What's it doing right now, today, and what would you actually do?" |
| **The reader** | "Who are you picturing reading this section, and what do they get wrong?" |
| **The turn** | "If they only remember one sentence from this, what is it? Say it the way you'd say it to a friend." |

Do **not** read the plan out loud or show the list; seeing the questions first
makes him answer the list instead of the question. Just announce the shape:

> "5 sections, about 10 questions. Say **skip**, **next section**, **go deeper**,
> **back up**, or **I'm done** any time. Take as long as you want per answer."

## Phase 2: The interview (voice mode)

He answers with Claude Code voice dictation (`/voice`). Answers arrive as
transcribed text: long, run-on, with filler and mis-heard words. That's
expected and fine.

**Rules. Every one of them:**

1. **One question per turn.** Then stop. Never stack two questions, never add
   a preamble. Prefix only with a tiny locator: `[2/5 · The setup]`.
2. **No praise, no judging.** No "great point," "love that," "that's powerful."
   Praise trains him to perform for you. Just move.
3. **Never suggest answers,** never offer options to pick from, never finish
   his thought, never paraphrase him back in nicer words.
4. **Follow the heat.** When an answer gets specific, contradicts itself,
   swears, or wanders somewhere with energy, spend a follow-up there instead
   of the next planned question: "You said *'<his exact words>'*. Say more."
   Quote him exactly. Max one follow-up per planned question in quick mode.
5. **Don't correct him mid-flow.** Mis-heard tickers, wrong-sounding numbers,
   garbled names: note them for Phase 3. Stopping to fix a ticker kills the
   answer.
6. **Short answer isn't a failure.** If the answer is thin, try the question
   once from a different angle (a different row of the bank). If it's still
   thin, the section may not need him; move on.
7. **"I'm done" means done.** Go straight to Phase 3, no wrap-up question.

**Save after every answer.** Append to `docs/articles/<slug>/interview.md`
immediately, so a dropped session loses nothing:

```markdown
## [2/5 · The setup] Q: What did you actually see that sent you to look at CALM?

> <his answer, exactly as transcribed. No cleanup here. Ever.>
```

The transcript is the raw record. It never gets edited, only appended.

## Phase 3: Mine the transcript

Before drafting, read the whole transcript and produce a short working list
(show it to him, keep it brief):

- **Keepers:** the lines that are unmistakably him (the jokes, the
  self-corrections, the "but I digress," the confession). These go in nearly
  untouched.
- **Verify:** every number, date, ticker, price, and name he said. Flag
  likely mis-transcriptions ("'see sco' = CSCO?"). Ask about all of them in
  **one** batched message, not one at a time. VOICE.md's rule on unverified
  dates applies: an unconfirmed CPI / FOMC / earnings date does not go in.
- **Outline changes:** if the answers made a section pointless or found a new
  one (often the origin story becomes the opener), say so and reorder.

## Phase 4: Assemble the draft (his words, lightly cleaned)

Write `docs/articles/<slug>/README.md` in the SUBSTACK.md structure. The body
is **his sentences**. Your job is editing and arranging, not writing.

**Cleanup you're allowed to do:**

- Cut filler and dictation junk: um, uh, like, you know, so yeah, false
  starts, words said twice, "wait, no, I mean" (keep what he meant).
- Fix confirmed mis-transcriptions of tickers, numbers, names.
- Add punctuation and paragraph breaks. Dictation produces run-ons; break them
  where he'd breathe. Short paragraphs per VOICE.md.
- Reorder answers into the outline's order.
- Trim an answer that runs long, by cutting whole sentences, not rewording.

**Things you do NOT do:**

- Swap his words for "better" ones. "Kinda" stays "kinda."
- Remove self-corrections, hedges about himself, tangents that end in "but I
  digress," or small grammatical roughness. VOICE-DELTA: typos ship.
- Add metaphors, jokes, or punchlines he didn't say.
- Smooth two of his sentences into one clever one.
- Introduce em dashes or en dashes. Dictation output sometimes has them
  after punctuation guessing; turn them into periods or commas. A spaced
  hyphen ` - ` inside his aside is his, and stays.

**What the machine still writes:** title, category-mix subtitle, section
headers, the one-line bridges between his answers where a jump would be
jarring, image/infographic placeholders, the CTA, and the `~ Michael`
sign-off. Keep bridges to one sentence, and in his register.

**Gaps:** if a section has no usable answer, write a bracketed placeholder
instead of inventing content: `[GAP: nothing on the exit plan yet. Ask: what's
the stop?]`. A visible gap beats a machine paragraph he has to hunt for and
rewrite.

Then run the SUBSTACK.md **Self-Edit Pass** on the bridges and machine-written
lines only. His own sentences don't get "fixed" for AI tells, since they aren't
AI.

## Phase 5: Hand off

In chat (not in the draft), report:

- Rough share of the body that's his words vs. machine bridges.
- Every `[GAP: ...]` left, with the one question that would fill it. Offer to
  ask them now (that's a mini Phase 2).
- Any number or date still unverified.

Then the normal pipeline takes over: images per SUBSTACK.md, the
`mph-substack-writer` / pusher flow, VOICE-DELTA pairing after it ships. Keep
`interview.md` in the article folder. Transcripts are future voice data, a
better training source than drafts for the next VOICE-DELTA pass.

---

## Files this skill writes

```
docs/articles/<slug>/
  outline.md       # Phase 0, the plan
  interview.md     # Phase 2, raw verbatim transcript, append-only
  README.md        # Phase 4, the draft
```

## Using it outside this repo

The skill source of truth lives here. To have it in every Claude Code session
on the dev box, symlink it into the user-level skills folder once:

```bash
mkdir -p ~/.claude/skills
ln -s /home/mph/mphinance/.claude/skills/voice-interview ~/.claude/skills/voice-interview
```

A symlink (not a copy) means edits here show up everywhere. Outside the repo,
write the three files into `./drafts/<slug>/` of whatever project you're in
unless he names a place.
