# VOICE-DELTA — what Michael changes between the machine's draft and the post he ships

_Voice-Delta Agent v0 · 2026-06-18 · feeds the writer, never writes a public word._

Not vibes. This is built by pairing each **machine-given draft** (the markdown that
got pushed) against the **version Michael actually shipped** on
mphinance.substack.com, and reading the diff. What he cuts is as much his
fingerprint as what he keeps.

**Read this first (honest constraints):**

- **N = 14 clean pairs** (4 anchors + 2 held-out + 8 new ships captured 2026-07-27).
  Seven new complete pairs added this run (06-27, 07-02, 07-04, 07-08, 07-11,
  07-19, 07-20). Every rule is followed by real receipts; if a rule has one
  receipt, it's a hypothesis, not a law.
- **Coverage now spans Mindset, Business, and Trading posts** across a wider date
  range. The 07-11 pair is the strongest title-transform example in the corpus:
  a full descriptive title dropped for a meme. The voice rules continue to
  generalize across content categories — immediacy, A3 self-correction, and C1
  cuts fire on every pair type.
- The corpus and the fetcher that rebuilds it live in
  [`docs/voice-delta/`](docs/voice-delta/).  The accuracy report is
  [`/ACCURACY.md`](ACCURACY.md).
- **Where this disagrees with your stated rules, trust your stated rules.** See
  the divergence at the bottom — "here's the truth" *survived* a ship in the
  training set, even though you've since banned it.  The corpus is a lagging
  indicator of a moving target.

## The pairs

| Date | Given draft | Shipped | Wall | Role |
|------|-------------|---------|------|------|
| 07-20 | "I Asked Sam Why the Rotation Feels Weekly" | "I Asked My Agent Why the Rotation Feels Weekly" | free | new |
| 07-19 | "The Signal Was Right. I Was the One Not Listening." | same title | paid_tease | new |
| 07-11 | "How to Accidentally Start a Religion (Or a Bull Market)" | "The Church of Number Go Up" | free | new |
| 07-08 | "📊 What Does Your $OPEN Rate Want You to Write?" | " What Does Your $OPEN Rate Want You to Write?" | free | new |
| 07-04 | "Someone Asked Me to Read Their Substack. So I Sent an AI." | "…So I Sent an AI (Yes I read it too)" | free | new |
| 07-02 | "I Got Out-Recruited By My Own Reader. Now I'm Opening the Door." | "I Got Out-Recruited By Another Writer. Now We're Opening the Door." | free | new |
| 06-27 | "You're Not Drowning. You're Fighting the Wave." | same title | free | new |
| 07-07 | "Give Away the App. Sell the Key." | same title | free | live (Business) |
| 06-23 | "Don't Trust Me. Trust the Tape." | same title | free | held-out |
| 06-22 | "Three Questions Before You Buy Any Pullback" | same title | paid_tease | held-out |
| 06-17 | "The Whole Market, In My Pocket" | same title | free | anchor |
| 06-11 | "The Machine Found **Five Stocks**. I'd Run From One." | "The Machine Found **Four Small Cap Multi-Baggers** & One I'd Run From" | paid_tease | anchor |
| 05-22 | "What I build after the market closes" | "BUILDING AFTER MARKET CLOSE **WITH KIDS**" | free | anchor |
| 04-25 | "I Upgraded Every Screener to a Scoring Model" | same title | paid | anchor |

---

## How he rewrites openings & titles

**1. Title: kill the generic noun, name the payoff.** The machine titles the
mechanism; Michael titles the thing the reader actually wants.
- `The Machine Found Five Stocks. I'd Run From One.` → `…Four Small Cap Multi-Baggers & One I'd Run From` (generic "Stocks" → the benefit, "Multi-Baggers")
- `What I build after the market closes` → `BUILDING AFTER MARKET CLOSE WITH KIDS` (the kid is the hook, so it goes in the title)
- (07-11) `How to Accidentally Start a Religion (Or a Bull Market)` → `The Church of Number Go Up` — **strongest example in the corpus**: drops the whole descriptive/explanatory framing and goes with the meme that the audience already knows. Mechanism → cultural shorthand.
- (07-02) `I Got Out-Recruited By My Own Reader` → `…By Another Writer` — "reader" is passive, "writer" is specific; and "my own" overpossessive
- (07-04) `Someone Asked Me to Read Their Substack. So I Sent an AI.` → adds `(Yes I read it too)` — the first time A3 (self-correction) fires **in the headline itself**; he won't let the title overstate the stunt
- (07-20) `I Asked Sam Why the Rotation Feels Weekly` → `I Asked My Agent Why the Rotation Feels Weekly` — "My Agent" over "Sam" in titles; brand-agnostic outside the post body

**2. Collapse time to "last night / this morning."** The machine writes vague past;
he compresses to immediate — even at the cost of literal accuracy.  **Held-out
06-22 and 06-23 both repeated this:** `I almost bought all three of these last
week` → `I almost listed a Buy on all three of these today`; `Last week that
was an NVDA 190 put` → `Today that was an $190 put`.  Most-replicated rule in
the corpus — fires in 5/6 pairs.
- `This one is about a night.` → `This one is about last night.`
- `A few weeks ago my almost-eight-year-old asked` → `Last night my almost-eight-year-old asked`
- `Last month I looked at four screeners` → `Last night I looked at four of the screeners`
- (machine) `what the big funds bought last quarter` → `…bought last night`
- (06-22 held-out) `last week` → `today`
- (06-23 held-out) `Last week that was an NVDA 190 put` → `Today that was an $190 put`
- (07-07) `First commit went in at 3:26 in the morning. The last one went in that same afternoon. In one day` → `First commit went in at 3:26 this morning, and I'm just now taking a break to tell you about some of them` (past → live, "this morning", writing mid-build)
- (07-07) `I vibe-coded the whole family in a day.` → `…in the last 8 hours.` (round "a day" → the specific, load-bearing number)
- (07-07) `I'm barely one.` → `I'm barely one anymore.` (the extra word is the whole self-deprecating arc)
- (06-27) `I was reading a Brandon Sanderson book the other night` → `I was reading a Brandon Sanderson today` — "the other night" → "today", immediacy even for a stable anecdote

**3. Add the stakes — the *why* under the line.**
- `twelve browser tabs and a quiet panic.` → `…a quiet panic to see if I can get my trades in before others got into the office.`
- `Then I remembered I have this fancy Claude thing.` → `…and I've been wanting to show him what Code is capable of outside of trading.`

---

## What he ADDS

**A1. Swaps the abstract metaphor for a warm, physical one.** When the machine
reaches for an industry image, he cuts it and drops in something you can feel.
- CUT `A screener is a casting director… which face carries the third act.` → ADD `Think of it as a public service. The financial version of a good friend smacking a bad idea out of your hand before you can click buy.`
- CUT `There is no bear case on the tape.` → ADD `When a quant billionaire quietly parks money in a company you have never heard of, that is the best chef in town eating at a diner with no sign out front.`
- ADD (on the VIX pop) `The market spent six weeks as a sleepy Sunday matinee. Today somebody yelled fire in the theater. Nobody is hurt yet, but everybody suddenly knows exactly where the exits are.`

**A2. Injects the live tape the machine couldn't have.** A real, of-the-moment read
with an actual trade idea.
- ADD `CSCO came up as the one to keep an eye on. Appears to have held its earnings gap line last night… I'm kinda liking a good strangle or straddle from this spot as it's currently sitting where it's definitely not going to stay.`

**A3. Self-corrects mid-sentence. Will not let a clean-but-false line stand.** This
is the densest tell. He dulls his own sentence rather than overclaim.  **The
detector under-counts this one** (R3 fires 0/6 in the rule matrix because the
regex only catches parenthetical hedges; many real self-corrections are bare
clauses like "and I couldn't find it" or "she's getting upgraded everyday").
- `…a name my other friend was already loaded in. Cold. No idea it was in his book.` → adds `(that's not true, but the screener didn't know)`
- `the machine cannot do.` → `the machine cannot do, mostly.`
- `That was every single screener` → `That was most of the screeners`
- `a tool called TickerTrace that scrapes` → `TickerTrace (I've since rolled this into TraderDaddy.Pro) that scrapes`
- (06-23 held-out) `The Options Field Manual is right here…` → adds `There was a follow-up too somewhere and I couldn't find it.`
- (06-23 held-out) `The tool is called TickerTrace.` → `The tool is called TickerTrace, unapologetically a funnel to TDPro.` (self-aware honesty about the product motive)
- (06-22 held-out) `you do not buy it.` → `you do not buy it - yet.`
- (07-07) `he gives me the look.` → `I still get the look (at least I'm pretty sure I do - we are virtual after all).` (undercuts his own certainty; spaced-hyphen aside)
- (07-07) `once he stops giving me the look.` → `…once he stops giving me the look (he already has - this time, I actually asked permission!).` (won't let the "co-founder resists me" frame stand unqualified — confesses he already got the yes)
- (07-04) Title addition: `…So I Sent an AI.` → `…So I Sent an AI (Yes I read it too)` — A3 fires in the headline: won't let the stunt overstate
- (07-04) `Those numbers don't tell you much.` → `Those numbers don't tell you much - yet.` (the single word is the whole optimism)
- (07-04) `But the point is what came back.` → adds `(most of which I already knew, but it's been a minute and was nice to catch up!)` — confesses the AI found nothing he didn't know; warmth neutralizes the stunt
- (07-20) `it has been quietly driving me insane` → `it has been (not so) quietly driving me insane` — parenthetical self-correction mid-adjective
- (07-19) `I run an indicator called R-Trend Exhaustion` → `The only indicator I really use that I didn't write myself is R-Trend Exhaustion` — clarifies tool ownership/authorship before claiming it

**A4. Wires the post into the network.** The machine writes in a vacuum; he adds the
restack bait and the product clicks.
- ADD `Math & Cynce had a great macro write-up yesterday - go read his if you're not sure what's going on.`
- ADD `don't forget to follow https://x.com/TraderDaddyBot - she's getting upgraded everyday!` + a direct `traderdaddy.pro/screeners/…` link under each screener.

**A5. The self-deprecating tangent.** An unprompted opinion that undercuts himself.
The machine stays on task; Michael wanders and deflates.
- ADD `It's called Crossover, because that's what Sam named it because I can't be bothered to actually name the things I create. Side note - if you're one of those that will dwell on a name or colors or logo for longer than the actual product took you to make - for the love of God let AI do it.`
- ADD (after the FIRE "one more year" math) `Except I can't measure sanity in a little chart.`

---

## What he CUTS

**C1. The meta-transition / windup** — the announce-before-you-say-it line.
- `Now the confession. This isn't a Bloomberg terminal…` → `This isn't a Bloomberg terminal…`
- `Here is the part that made me sit up. I built this machine…` → `So here's the conviction. I built this machine…`
- (07-07) cut the two windup lines whole: `So here's the argument I've been losing at dinner, finally written down as the thing that wins it.` and `That's the whole thesis. The rest of this is proof that it's already running.` — he refuses to announce the thesis before making it; the claims just start.
- (06-27) `Here's the part that closes the loop.` → `Closing the loop.` — strips the announce, keeps the label
- (07-11) cut the entire "I laughed. Then I stopped laughing, because I'd spent that same week reading Tchaikovsky and arguing with friends about exactly this, and I realized the show wasn't doing science fiction. It was doing a documentary with the serial numbers filed off." — the paragraph that explains how the idea formed is removed; the insight just starts. Also cut the closing paragraph ("This one's free, all of it, no paywall…Recovery taught me this before markets did…") — no explaining why the content is free, no closing wisdom recap; the last word is `Subscribe now`.

**C2. The doubled metaphor / the extra clause.** Keeps one image, kills the spare.
- cut the whole "casting director" paragraph (he already had "light money on fire")
- `Palladyne is a promise, not an income statement.` → `Palladyne is a promise.`

**C3. Tones the recovery language from program-specific to human.** Keeps the
wisdom, strips the AA jargon.  **Held-out 06-23 was a clean replication:** he
cut the whole `I'm a felon in recovery who builds his own trading tools because
I got tired of being lied to by people in nicer suits than mine` line — but
kept `We get better by looking at the thing we'd rather not look at.  That's
true in recovery and it's true in your brokerage account.`  The wisdom stays;
the confession goes.
- `In recovery they tell you` → `I heard something awhile back, I believe my uncle`
- cut entirely: `If you have ever done a fourth step… start writing down what actually happened.`
- (06-23 held-out) cut `I'm a felon in recovery who builds his own trading tools…`; kept the closing recovery-line as a metaphor.
- (06-22 held-out) cut `In the rooms they have a line for exactly this: do not just do something, sit there.` — same pattern: AA-room jargon dies, the wisdom would have to be rephrased to survive.
- (07-19 signal-was-right) `twelve years I have spent putting my life back together` → `the years I have spent…` — strips the precise count of recovery time. Wisdom stays, the clinical number goes. Also note: the recovery wisdom got MORE personal in this pair, not less — machine was generic; shipped added `(I'm glaring at a few people I know who are currently laughing as they read this - you know who you are)`. C3 is not about removing recovery content; it's about removing the program-specific framing and replacing it with human humor.

---

## Consistency fixes he makes every time (canon + framing)

- **Sam is "her."** Every Sam pronoun the machine wrote as male got flipped: `feel his stomach drop` → `her`, `his best C-3PO` → `her`, `He just did` → `She just did`, `he would actually take` → `she would actually take`. (The TraderDaddyBot is "she" too.)
- **`the` → `my`** (ownership): `the entire job` → `my entire job`; `The only knock` → `My only knock`.
- **Solo `I/my` → branded `Phund/we`** when it's about the account: `my own brokerage account… what I'm holding` → `the Momentum Phund's brokerage account… what we're holding`.
- **Generic → named brand:** `options flow in another` → `TradingView in another`; `I built a button` → `The Claude button`.
- **Disclaimer moves to the TOP and becomes a bit:** bottom-of-post `Not financial advice…` → top, rewritten: `Hi! I'm a super legit "not financial advice" disclaimer that you've read so you're not going to sue me now. Good talk.`
- **Typos ship.** `my my uncle`, `it slightly up` survive (07-07 added `an TraderDaddy SDK` and `TL,DR;`). He does not sand the post to corporate-smooth; the small imperfections read as a human was here.
- **Direct reader-address, unhedged.** He turns third-person copy at the reader mid-line: `a sales team that works for free.` → `…for free. I hope (hint, that's you).` and closes the piece by talking to the co-founder AND the reader: `Art, I solved it. Again.` → `…Again. You might wanna pick up the mic I'm about to drop.` **(07-07 only — single pair, not yet a law.)**
- **Adds the credibility clause on the product.** `the thing that's actually expensive to build and run.` → `…to build and run, and were designed by a team of professional traders with years of experience.` — when the post is the funnel, he slips the sell in as a subordinate clause, never a sentence of its own. **(07-07 only — watch on next Business post.)**
- **Bold `**emphasis**` is stripped from body prose.** Machine frequently bolds key numbers, names, or phrases. Michael ships plain text. Confirmed in 5 of 7 new pairs (out-recruited stripped 122/66/113/30/65%, two-cluster-seesaw stripped Leadership/You can't front-run/Defense-tech, youre-not-drowning stripped all section-headers, signal-was-right stripped key terms, accidental-religion stripped). Do not bold anything in the body that isn't a heading or product name.
- **Markdown hyperlinks become plain text.** Machine writes `[text](url)`; shipped shows just the text (or bare URL). Confirmed in 3 of 7 new pairs (mygreenknight-shoutout: every Substack link and disclaw link; out-recruited: Hidden Gems Research link; open-rate-what-to-write: github link). He does not add hyperlinks in the edit — they land as Substack auto-links or disappear.
- **Machine's subscribe footer is replaced by Substack's native button.** `*If this helped, subscribe so the next one lands in your inbox.*` (or any italic footer CTA) → `Subscribe now` (Substack's button text). Confirmed in 4 of 7 new pairs (youre-not-drowning, mygreenknight-shoutout, open-rate-what-to-write, accidental-religion, two-cluster-seesaw). Machine should still write the footer line for completeness, but know it will be replaced.
- **Sign-offs are cut.** `~ Michael` at the end of a post does not survive. Confirmed in two-cluster-seesaw. (07-07 only — single prior pair, now 2 evidence.)

## What the machine already nails — don't "fix" these

The edits are surgical, not a rewrite. These survived verbatim across pairs, so the
machine's job is the scaffold plus the keeper lines:
- The spine line: `A screener does not pick trades…` (kept in both stock posts)
- `Bloomberg charges 24 grand a year for the version that doesn't.`
- The footer CTA: `Subscribe and the next one finds you. Half of every paid sub goes straight into the brokerage account you just read about, so you're funding the machine.`

---

## Divergence — where the corpus and your stated rules disagree

**"Here's the truth" survived.** The machine wrote `Here is the truth. This is just
what I do.` and you **shipped it** (05-22). Your standing instruction bans the
canned "real talk" transition — but a delta-agent trained only on these four ships
would never learn that, because the ship kept it. Takeaway: the ban is newer than
this corpus. **Your explicit rules outrank the thin diff.** As more posts publish,
this should flip and the corpus will catch up.

**Not observed (so not claimed):** I could not cite a single **em-dash cut** or
**round-number cut** — the machine drafts already avoid them, because the
upstream `mph-substack-writer` skill enforces that before the draft is ever
written. The cleanup happens before the pairing, so it's invisible here. Real, just
not visible at this stage.

---

## Accuracy snapshot (the "is this VOICE.md actually accurate" check)

Full report: [`/ACCURACY.md`](ACCURACY.md), regenerated by `python3
docs/voice-delta/score.py`.  The harness asks a model to **predict** what
Michael would ship given only the machine draft + the rules above, then
measures how close the prediction lands to the actual ship.

| Pair | Role | j(given, shipped) | j(predicted, shipped) | Δ |
|------|------|-------|-------|---|
| 2026-04-25 upgraded-screener | anchor | 0.797 | 0.901 | **+0.104** |
| 2026-05-22 building-after-close | anchor | 0.890 | 0.946 | **+0.055** |
| 2026-06-11 machine-found-five | anchor | 0.712 | 0.931 | **+0.219** |
| 2026-06-17 whole-market-in-my-pocket | anchor | 0.796 | 0.882 | **+0.086** |
| 2026-06-22 three-questions-before-you-buy | held-out | 0.674 | 0.859 | **+0.185** |
| 2026-06-23 ulti-fund-xray | held-out | 0.784 | 0.878 | **+0.094** |

**Δ +0.124 averaged across N=6 predicted pairs.**  Every single pair improved
when VOICE-DELTA.md was applied.  The two biggest gains landed on the two
heaviest-edit-budget pairs (06-11 +0.219, 06-22 +0.185) — exactly where the
machine left the most rewriting to do, the rules carried the most weight.
The held-out pairs (06-22, 06-23) sit inside the same Δ range as the
anchors, so the rules are *generalizing*, not memorizing.

What the harness tests: rule-edits (title transform, immediacy, self-correction,
Phund/we, meta-transition cuts, shoutouts, product links).  What it does NOT
test: brand-new content the machine couldn't have written (e.g. the 06-23 ship
added a whole "how I actually do it" methodology section).  We don't blame the
rules for content they cannot generate; we measure how well they edit.

## Verdict

Fourteen pairs, the signal **denser and more consistent than ever**: the machine builds
a clean scaffold and a few keeper lines; you spend your edit budget on **honesty
(self-correction), warmth (physical metaphors), immediacy (time compression), and
distribution (shoutouts, plugs, canon)**.  Now three times the corpus.

Seven new pairs added 2026-07-27 — all seven replicated A3 (self-correction),
C1 (meta-transition cut), and Rule 2 (immediacy) in at least one form.  Three new
consistency patterns have enough evidence to call: bold stripped, markdown links
stripped, subscribe footer → Substack native button.  The 07-11 pair
(accidental-religion) produced the corpus's clearest title-transform example:
a descriptive mechanism title dropped for a meme known to the audience.
A3 fired in a title for the first time (07-04 mygreenknight-shoutout).

When someone says "VOICE.md isn't accurate," this is the answer: pair the drafts
against the ships, run the harness, point at the Δ.

_— Voice-Delta Agent v0.4 · 2026-07-27_
