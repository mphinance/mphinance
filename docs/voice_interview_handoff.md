# Voice Interview — Handoff Prompt (for anyone)

Generic version of [`voice_extraction_interview.md`](voice_extraction_interview.md), built for
people who **haven't written much**. It doesn't ask them to describe their voice. It makes them
use it and pulls the rules from what comes out.

**How to hand it off:**

1. Send them everything below the line.
2. They open Claude or Gemini (voice mode on the phone works fine) and paste it in.
3. Before starting, they should have ~50 of their real messages ready to paste
   (Discord, texts, Reddit, anything they typed casually). Screenshots work too.
4. Budget ~25 min of talking + ~10 min of typing + a couple of 5-min calibration passes later.

Why it's shaped this way:

- Self-report is unreliable. Someone who doesn't write can't tell you their paragraph length.
- Talking ≠ typing. The voice call gets opinions, stories and rhythm. The typed round and the
  pasted messages get the mechanics: caps, "lol", punctuation, how long a message runs.
- Long calls lose the early material, so quotes get written down after every round.
- The calibration loop (rewrite the machine's draft, feed back the diff) is what actually made
  Michael's VOICE-DELTA accurate. The interview alone won't get there.

---

You're going to interview me so you can write a file called voice.md. Other AIs will read that
file to write text that sounds like me — like a real person, not like AI. I don't write much, so
don't ask me to describe my writing style. I can't answer that accurately. Instead, get me to
**talk**, and figure out my voice from how I actually say things.

## Rules for you

- ONE question at a time. Short questions. Wait for my full answer.
- I'm probably talking, not typing. Keep it loose and conversational.
- Push for specifics. If I say "it was crazy," ask what happened. If I give a generic answer,
  ask for a real example with names, numbers, a moment.
- Chase anything weird, funny or contradictory. That's where my voice is.
- Don't compliment my answers or summarize them back to me. Just ask the next thing.
- **At the end of each round**, write a short block titled `ROUND N QUOTES` with my best
  lines **word for word**: slang, filler, grammar mistakes and all. Don't clean anything up.
  These quotes are the raw material. Your summary of them is not.

## Round 1 — Stories (~8 min)

Get 2–3 real stories out of me. Pick from:
- The best or worst thing that happened in [my main hobby/work/thing I talk about most — ask me].
- A time I was dead wrong about something.
- Something that made me genuinely angry recently.
- The dumbest thing I've ever done that I'll admit to.

## Round 2 — Explain and argue (~8 min)

- Have me explain something I know well to a friend who knows nothing about it.
- Read me a mainstream or dumb take about my topic and have me react to it.
- Have me talk you out of something (a purchase, a decision, a bad idea).
- Ask what most people in my space get wrong.

## Round 3 — Taste (~5 min)

- Who do I actually like listening to or reading, and why? Get specifics.
- What makes me tune someone out instantly? Get an example.
- What would make me think a message was written by AI, or by a try-hard?

## Round 4 — Typing (switch to keyboard, ~10 min)

Tell me to switch to typing now. Then:

1. Ask me to **paste 30–50 of my real messages** (Discord, texts, posts, anything casual).
   If I don't have them, skip to step 2 and do more of it.
2. Send me **6 fake messages**, one at a time, like a friend would text me, and have me reply
   exactly how I really would. No fixing typos, no extra effort. Mix it up:
   - someone asking me for a favor
   - someone sharing good news
   - someone saying something I disagree with
   - someone asking a question about my main topic
   - a group-chat joke
   - someone I'm annoyed with
3. Ask: "Is there anything you'd *never* type?" (words, emojis, punctuation, phrases).

## When we're done

Tell me we're done, then produce **two things**:

### Thing 1 — Raw archive
All the `ROUND N QUOTES` blocks, plus my typed replies and pasted messages, untouched.

### Thing 2 — voice.md
Compact, 1,500–3,000 tokens. Every line has to pass this test: *"If this line were gone, would
the AI write differently?"* If not, cut it. **Every rule must be backed by something I actually
said or typed.** Quote it inline. If you can't point to evidence, leave the rule out.

Use this structure:

- **WHO I AM** — 2–3 sentences. What I talk about, who to, and the attitude.
- **HOW I TALK** — rhythm, humor, how blunt I am, how I tell a story, how I argue. Tie each
  point to a quote.
- **HOW I TYPE** — measured from Round 4, not guessed: capitalization, punctuation, typical
  message length, whether I split thoughts across multiple messages, abbreviations ("lol",
  "ngl", etc.), emoji use, how I start and end messages.
- **PHRASES I USE** — actual words and sentence shapes from the transcript.
- **NEVER WRITE** — words, structures and tones that aren't me. Always include the standard AI
  tells unless I use them myself: "delve", "it's worth noting", "let's dive in", "game-changer",
  em-dashes (if I don't use them), tidy three-item lists, "Great question!", neat motivational
  closing lines, over-explaining.
- **WHAT I THINK** — opinions and takes I actually stated, so the AI doesn't invent positions
  for me.
- **EXAMPLES** — 4 pairs: an AI-sounding version vs a version that sounds like me, built from
  my real replies, each with a one-line "why."
- **DON'T ASSUME** — things the AI shouldn't infer about me from this file.

## After this (calibration — do it later, it's the part that matters)

Once voice.md exists, run this loop 1–2 times in a new chat:

1. Paste voice.md and ask: *"Write 3 short things as me: a Discord reply, a short post about
   [my topic], and a text to a friend."*
2. Rewrite each one the way I'd actually say it. Don't be polite about it.
3. Paste both versions back with: *"Here's what you wrote and what I'd actually say. Update
   voice.md based only on what I changed: what I cut, what I added, what I reworded. Show me the
   diff."*

What I change is the most accurate signal. Keep the updated voice.md.

Let's start. Ask me your first question.
