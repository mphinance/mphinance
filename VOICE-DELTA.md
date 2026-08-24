# VOICE-DELTA — what Michael changes between the machine's draft and the post he ships

_Voice-Delta Agent v0.4 · 2026-08-24 · feeds the writer, never writes a public word._

Not vibes. This is built by pairing each **machine-given draft** (the markdown that
got pushed) against the **version Michael actually shipped** on
mphinance.substack.com, and reading the diff. What he cuts is as much his
fingerprint as what he keeps.

**Read this first (honest constraints):**

- **N = 14 clean pairs** (4 anchors + 2 held-out captured 2026-06-25, + 1 live
  ship 2026-07-07, + 1 live ship 2026-07-08, + 1 live ship 2026-07-09, + 1
  live ship 2026-07-11, + 1 dual-voice ship 2026-07-13, + 1 live ship 2026-07-15,
  + 1 live ship 2026-07-19, + 1 live ship 2026-07-20). Still not statistics, but
  enough to test whether the rules below GENERALIZE to pairs they weren't
  derived from.  Every rule is followed by real receipts; if a rule has one
  receipt, it's a hypothesis, not a law.
- **Ticker redaction is now a law, not a hypothesis (4 pairs).** The 07-13
  "we called this exact trade" masking (PEP, HOOD → blank) was called a
  hypothesis when we had one pair. It replicated on 07-11 (NVDA → blank inside
  "The ticker is the good man.   is a real company"), 07-19 (FIG blanked in
  the opening sentence and both trade-rule callouts; SLB blanked in the
  paywall tease), and 07-20 (KTOS, AVAV blanked in the defense-tech
  correlation list; PLTR blanked in the "carrying the whole tape" line but
  kept later where it's already the metaphor). Read: **when a live trade or a
  named position is in play, tickers get masked in the reader-facing text**;
  he still names the ticker in the code-block trade rule (07-15 confirmed
  this shape) but strips it from prose. Full rule under "Consistency fixes"
  below.
- **The 07-15 pair is the first publish-triggers-trade ship** ("Money Where My
  Mouth Is"). Two hypothesis-only tells, both driven by the mechanic: (a) he
  **converted a decorative figure into a literal machine-readable block** — the
  machine put the trade only inside a PNG trade-card; he re-typed the full trade
  as a parseable code block (Symbol/Action/Broker/Size/Entry/Stop/Targets) because
  a downstream parser reads the post to place the order. When a figure is
  load-bearing for automation, he refuses to let it live only as an image. (b) He
  **flagged the image as decoration vs the real thing**: added `So that's the
  pretty picture, but what follows here is the ACTUAL trigger that will place the
  ACTUAL order.` before the block. Also: prepended the confession-header fragment
  `Character defect admission time.` to the opener, corrected the CRWV number to
  the real `$115 for about 30 percent` + compressed time with `(today)`, and used
  his spaced-hyphen header `## The fix - this post as the trigger`. One pair, so
  hypotheses, not laws.
- **The 07-13 pair is the first dual-voice ship** ("The Robot Wanted to Brag").
  The machine co-narrated a whole section AS Sam; Michael bookended in his own
  voice.  Sam's entire brag body, the "call before the close" beat, the
  loss-reveal ("I have math."), and the `~ Michael` closer shipped **verbatim** —
  the honesty-flex conceit was a clean keeper.  His edit budget went almost
  entirely to two places: the OPENING (toned the recovery-adjacent self-flagging
  down to a wry observation) and the FEATURE LIST (rewrote the machine's prose
  tour into branded product taxonomy).  New this pair, hypothesis-only: he
  **redacted the tickers** (PEP, HOOD → blank) inside the "we called this exact
  trade" claim, the way he masks usernames — read as compliance, not style.  One
  pair, so not a law.
- **The 07-09 pair is the first crypto/Macro ship** ("I Tokenized My $GLXY").
  Two edit patterns fired hard: (a) he added a first-person confession to the
  TAIL of nearly every analytical section, and (b) he cut the machine's clever
  metaphors for a bare punch.  Both are the "add the stakes / kill the
  scaffolding" rules below, and they held on non-trading content.
- **The 07-07 pair is the first Business-category ship** (the daddy-* SDK
  funnel manifesto).  The corpus was trading-heavy; watch whether these rules
  hold on non-trading posts.  Early read: immediacy, self-correcting
  parentheticals, and the meta-transition cut all fired again — the voice is
  content-independent.
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
| 07-20 | "I Asked **Sam** Why the Rotation Feels Weekly" | "I Asked **My Agent** Why the Rotation Feels Weekly" | free | live (Macro, ticker-redaction replication) |
| 07-19 | "The Signal Was Right. I Was the One Not Listening." | same title | paid | live (Trading, ticker-redaction replication) |
| 07-15 | "Money Where My Mouth Is…" | same title | free | live (Money-Where-Mouth-Is #1, publish-triggers-trade) |
| 07-13 | "…Show the Losses **First**." | "…Show the Losses **Too**." | free | live (Business, dual-voice) |
| 07-11 | "How to Accidentally Start a Religion (Or a Bull Market)" | "**The Church of Number Go Up**" | free | live (Mindset/Macro, first NON-trading rule survey) |
| 07-09 | "I Tokenized My $GLXY. Do You Actually Own Yours?" | "…Own **Your Tokenized Stocks? (No)**" | paid | live (Macro/crypto) |
| 07-08 | "What Does Your $OPEN Rate Want You to Write?" | same title | free | live (Business, meta) |
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
- (07-09) `Do You Actually Own Yours?` → `Do You Actually Own Your Tokenized Stocks? (No)` — two moves: expand the vague "Yours" to the keyword phrase ("Tokenized Stocks", better share-card + search), then **answer the question in the title with a parenthetical** `(No)`. He'll spoil the payoff up front if the answer is the hook.
- (07-13) `Show the Losses **First**.` → `Show the Losses **Too**.` — softened the combative ordering verb ("First" = *I* forced it to show losses before it bragged) to the additive honesty of "Too." When the frame is honesty, he pulls the swagger out of the title verb.
- (07-11) `How to Accidentally Start a Religion (Or a Bull Market)` → `The Church of Number Go Up` — killed the how-to framing and the split-parenthetical entirely, replaced with a **meme-shape noun-phrase** ("Number Go Up" is the crypto/bull-market catchphrase). Reader knows what the post is about from the title alone, no verb needed. Same move as `…Multi-Baggers`: title the *feeling*, not the mechanism.
- (07-20) `I Asked **Sam** Why…` → `I Asked **My Agent** Why…` — *renaming for audience*. Body keeps every "Sam" reference; only the title generalizes to "My Agent." Read: when the title reaches cold readers who don't know the persona, he swaps the in-house name for the category noun; when the body has already introduced her, he can name her. **First pair to show this — hypothesis, not law.**

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

**3. Add the stakes — the *why* under the line.**
- `twelve browser tabs and a quiet panic.` → `…a quiet panic to see if I can get my trades in before others got into the office.`
- `Then I remembered I have this fancy Claude thing.` → `…and I've been wanting to show him what Code is capable of outside of trading.`
- **(07-09, strongest replication yet) He appended a first-person confession to the TAIL of nearly every analytical section.** This is the "confession-first ethos" his own $OPEN-rate data predicts, applied as a section-closer rather than an opener:
  - Mt. Gox paragraph (machine text, verbatim) + `I've had hardware wallets for 10 years now.`
  - `That is a hole in the floor nobody's put a cone in front of yet.` + `And I don't tend to watch where I'm walking all the time.`
  - `Always working is also always exposed.` + `It's why I fell in love with crypto, but it's a double-edged sword.`
  - Takeaway for the writer: end analytical sections with a hook for a personal admission. Don't close on the clean abstract line; leave him room to warm it with an "I".

**3b. Cut the clever metaphor for a bare punch.** Where the machine reached for a
constructed image, he deleted it and let the raw fact (often + `!`) carry it.
- (07-09) `Twenty-three million holding up one-point-three trillion. That's not a vault. That's a magic trick, and the audience found out.` → `Twenty-three million holding up one-point-three trillion!` (killed the magic-trick metaphor entirely)
- (07-09) `So when I say I know how this works, I mean I've got skin in it, not a hot take from the sidelines.` → `I know how this works, I've got skin in it - this isn't a hot take from the sidelines.` (cut the "So when I say… I mean" wind-up; note his ` - ` spaced hyphen)

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
- (07-11) `time runs faster down there,` → `time runs faster down there (it is sci-fi),` — parenthetical undercuts his own "distance in time" setup with a wink at the mechanism. He will not let the sci-fi premise pass as if it were a real place.
- (07-11) added out of nowhere in the middle of the invalidation-level rule: `Once again - it's ok to admit it. Say it with me once if it's been a while. "I was wrong". Back to the invalidation level.` — self-correcting *for the reader*: interrupts his own paragraph to grant permission for the word he's about to require, then resumes. Same spaced-hyphen tic.
- (07-19) `My screener never did.` → `My screener never did, so I never wrote about it, as I've always made sure to back my claims with data.` — dulls the clean "I missed it" line with the *why* he'd normally miss it, defending the discipline instead of the miss.
- (07-19) `They just needed one small change. Or worse, they never actually traded with it.` → `…Or worse, they never actually followed with it (I'm glaring at a few people I know who are currently laughing as they read this - you know who you are).` (parenthetical inside-joke aside; softens `traded` → `followed`)
- (07-20) `it has been quietly driving me insane.` → `…it has been (not so) quietly driving me insane.` (parenthetical self-correction of "quietly")
- (07-20) `This is my data run and my read, nothing more.` → `This is my data run and my read **and my noggin**, nothing more.` (adds a third item to the list to knock the seriousness down)

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
- (07-13) `Now here is the part I do not get to write. Take it away.` → `Now, to hand the mic to Sam.` — cut the self-referential windup (and the `## Sam:` header + horizontal rule); the handoff line carries the voice change on its own. Also `So here is the deal today.` → `Here's the deal today.` (drop the "So", contract "here is").
- (07-08) cut `I vibe-coded it in a day, and the code is free, because a dashboard that only flatters you is not a dashboard, it is a mirror you paid for.` — killed the whole "because" clause: he refuses to explain *why* the tool is free-and-in-browser. The next paragraph starts making the actual argument. Same reflex as 07-07: no thesis-announcement, just start the thesis.
- (07-11) cut `I laughed. Then I stopped laughing, because I'd spent that same week reading Tchaikovsky and arguing with friends about exactly this, and I realized the show wasn't doing science fiction. It was doing a documentary with the serial numbers filed off. Swap the robes for a blazer and the halo for an upward candlestick, and you have not changed the story at all. You've just changed the pew.` — the entire "here is my thesis about what the show *really* is" paragraph deleted; replaced with a Tchaikovsky/Lovegrove blockquote that just *shows* the thesis. Windup replaced by evidence.
- (07-11) also cut the doubled windup `Wit, if you read Sanderson, tells stories exactly like this. A joke, a beat, then the second laugh, the one you don't enjoy. I'm not telling you what's false. I'm telling you what the words meant to the people using them, and letting you notice how little that resembles what you were handed.` — same reflex: the *explanation of how the piece works* dies; the piece is allowed to do its own work.
- (07-11) `So here is the entire discipline, and it's nothing fancier than keeping the question mark screwed on.` — cut. The next paragraph just starts giving the discipline. Book-ending phrase "the whole entire ___" is a machine tell he strips.
- (07-19) cut the whole opening thesis line `I spent a week trying to prove my favorite indicator was broken. It wasn't. I was.` — the *title* already says exactly this ("The Signal Was Right. I Was the One Not Listening."). He will not repeat the title as the opener. First sentence dives straight into the story.
- (07-19) cut `That is the part that stung. The signal was sitting on my screen the whole time. I just built a scanner that was looking at a different thing.` — three sentences of *feeling about* the miss, deleted; the miss stands on its own line above and the next section jumps to what most traders do next. He refuses to explain the emotional beat between action and consequence.
- (07-19) cut `I named it what it is. Bottom of the coil. That is the whole game. You are not trying to catch the falling knife. You are trying to catch the moment the spring lets go.` — an entire naming-plus-metaphor windup, deleted. The scan is already named earlier ("bottom of the coil"), so the reveal is redundant, and the "not X, but Y" closer is exactly the machine construction he strips.

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
- (07-13) cut the recovery-adjacent `That is how you stay sick.` and de-confessed the whole opener: `I have been the guy who screenshots only the wins… I did that when I was newer, dumber, and a lot less honest with myself.` → `It must be nice to be the guy who only wins in the market… It's beyond tempting to come up here and pretend it's all wins.` **Nuance / partial counter to rule 3:** normally he ADDS first-person confession; here he REMOVED his own self-implication and made it a wry general observation. Read: he'll drop the "I was sick" self-flagging when a lighter, sardonic frame lands the same honesty without the heavy admission. The recovery *word* ("sick") dies; the humility survives as tone.
- (07-19) **weaves rather than leads with the recovery frame.** `In recovery nobody tells you to go find a better program when you are struggling. They tell you to work the one you have.` → `Nobody tells you to go find a better program when you are struggling in recovery and they shouldn't here either. They tell you to work the one you have.` The word "recovery" survives, but the *structure* flips: he refuses to open the paragraph FROM inside the rooms as "in recovery, X"; instead he opens with the general claim and glues recovery on as a subordinate clause. Same wisdom, less lectern.
- (07-19) also dropped the specificity: `the twelve years I have spent putting my life back together` → `the years I have spent putting my life back together` — number gone. Program-specific ("12 years" ≈ AA-milestone) → human ("years").
- (07-19) cut the entire closing recovery paragraph: `One boring, honest day at a time. Same as everything else worth keeping.` and the paragraph before it — the "sober day at a time" cadence would have sealed the post in recovery voice; he strips it and lets `Trade with it.` be the last non-CTA line.
- (07-11) cut the entire closing recovery paragraph: `Recovery taught me this before markets did. Half the wreckage in my life came from stories I swallowed without pulling a single thread, because pulling the thread meant the story might not hold, and I needed it to hold. Getting sober was mostly learning to read my own primary sources. The market just charges tuition for the same lesson. Put the question mark back on. Every time.` — heaviest recovery close in the corpus, deleted whole. **Fires on non-trading content too** (this is the religion/mindset post). The rule generalizes: when a post lands on a big idea, he refuses to seal it with a recovery bow, even when it fits.

---

## Consistency fixes he makes every time (canon + framing)

- **Sam is "her."** Every Sam pronoun the machine wrote as male got flipped: `feel his stomach drop` → `her`, `his best C-3PO` → `her`, `He just did` → `She just did`, `he would actually take` → `she would actually take`. (The TraderDaddyBot is "she" too.)
- **`the` → `my`** (ownership): `the entire job` → `my entire job`; `The only knock` → `My only knock`.
- **Solo `I/my` → branded `Phund/we`** when it's about the account: `my own brokerage account… what I'm holding` → `the Momentum Phund's brokerage account… what we're holding`. (07-13) `What **I** actually built` → `What **we** actually built` — same conversion on the product, not just the account.
- **Generic → named brand:** `options flow in another` → `TradingView in another`; `I built a button` → `The Claude button`. (07-13) named the in-app assistant: `TraderLady` → `TraderLady (Arya)`, while keeping **Sam** as the post's narrator voice — the swarm has two named AIs and he distinguishes them.
- **Feature lists become branded product taxonomy, not prose. (07-13, hypothesis — first pair)** When the machine wrote a narrative tour (`It watches the tape for size…`), he rewrote it into named product categories, each a `Label. One-line promise. Component, component, component.` block pulled straight from the live product: `Options Flow. See what smart money is doing before the move happens. …Unusual Activity, Live Flow, Heat Map, Sector & Earnings Flow.` He also ADDED categories/detail the machine under-specified (`Calendars & Intel`, portfolio tracker, AI strategy ranker, CSP setups). Takeaway for the writer: when the post lists what the platform does, give the real taxonomy in his terse label-tagline-components shape, not a friendly prose walk.
- **Disclaimer moves to the TOP and becomes a bit:** bottom-of-post `Not financial advice…` → top, rewritten: `Hi! I'm a super legit "not financial advice" disclaimer that you've read so you're not going to sue me now. Good talk.`
- **Typos ship.** `my my uncle`, `it slightly up` survive (07-07 added `an TraderDaddy SDK` and `TL,DR;`). He does not sand the post to corporate-smooth; the small imperfections read as a human was here.
- **Direct reader-address, unhedged.** He turns third-person copy at the reader mid-line: `a sales team that works for free.` → `…for free. I hope (hint, that's you).` and closes the piece by talking to the co-founder AND the reader: `Art, I solved it. Again.` → `…Again. You might wanna pick up the mic I'm about to drop.` **(07-07 only — single pair, not yet a law.)**
- **Adds the credibility clause on the product.** `the thing that's actually expensive to build and run.` → `…to build and run, and were designed by a team of professional traders with years of experience.` — when the post is the funnel, he slips the sell in as a subordinate clause, never a sentence of its own. **(07-07 only — watch on next Business post.)**
- **Ticker redaction inside prose when a live trade is in play (LAW — 4 pairs).** The machine names every ticker in-line. Michael blanks the ones tied to a *specific position or live-trade claim*, then names them in isolation (a code block, an explicit trade rule, a caption, or a `$TICKER`-tag disclosure). The prose reads as an anonymized case study; the trade rule reads as the record.
  - (07-13, first observation) `we called this exact trade — PEP, HOOD` → `…exact trade —   ,     ` (both tickers blanked)
  - (07-11) `NVDA is a real company, the chips are real` → `  is a real company, the chips are real` (NVDA blanked)
  - (07-19) `sat down to write you a trade on FIG` → `sat down to write you a trade on .` (FIG blanked in the opener); paywall tease `both trade rules, FIG and SLB, the real ones` → `both trade rules,   and ____, the real ones` (both blanked). Note the code-block trade rule below the wall still names FIG and SLB in full — the ticker survives where the parser reads it, dies where the reader reads it.
  - (07-20) `Palantir is carrying the whole tape by itself` → `  or   is carrying the whole tape by itself` (blanked, and `or` inserted so the second slot exists); `Palantir, Kratos, AVAV correlate` → `Palantir, ,    correlate` (KTOS, AVAV blanked; PLTR survives here because it's already the archetype/label). Read: he'll keep the name when it's operating as the *category shorthand* and blank it when it's making a specific position claim.
  - Read as compliance-shaped, not stylistic: the redactions cluster where the sentence could be read as a public buy/sell claim on a named security. Where the ticker is only naming an *industry* or a *pattern*, it survives.
- **Renaming Sam for outside vs inside audiences.** *(07-20 only — hypothesis, one pair.)* Title changed from `I Asked **Sam**` → `I Asked **My Agent**`, but every "Sam" reference INSIDE the body survives, plus an added Dr. Seuss beat (`One question, oh Sam-I-Am, why does this feel like it turns every week?`). Read: the title reaches strangers, so Sam gets category-shortened to "My Agent"; the body has already introduced her, so she can be named. Watch whether the next dual-audience post repeats this.

## What the machine already nails — don't "fix" these

The edits are surgical, not a rewrite. These survived verbatim across pairs, so the
machine's job is the scaffold plus the keeper lines:
- The spine line: `A screener does not pick trades…` (kept in both stock posts)
- `Bloomberg charges 24 grand a year for the version that doesn't.`
- The footer CTA: `Subscribe and the next one finds you. Half of every paid sub goes straight into the brokerage account you just read about, so you're funding the machine.`
- (07-13) An entire **second voice**: Sam's brag body shipped verbatim (`I am not a person. I do not get an ego hit from a green day…` through `I have math.`), including the loss-reveal section and the `~ Michael` closer. When the machine writes a distinct-persona section that is honest and cocky in equal measure, he leaves it alone — the persona is the machine's job, the bookend framing is his.

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

Fourteen pairs, the signal still **dense and consistent**: the machine builds a
clean scaffold and a few keeper lines; you spend your edit budget on **honesty
(self-correction), warmth (physical metaphors), immediacy (time compression),
distribution (shoutouts, plugs, canon), and — new law this refresh — ticker
discipline (masking named positions in prose while the trade rule keeps them
literal)**.

Four new pairs this refresh (07-08, 07-11, 07-19, 07-20) fire the same rules
across four different content shapes: Business/meta (07-08), Mindset/Macro
(07-11 — the first religion-adjacent post), paid Trading (07-19), and
free Macro (07-20). Every one of them cut a meta-transition windup, added
mid-paragraph self-corrections, and — in the three where a live position was
present — blanked tickers in the prose. The **07-19 recovery de-lead** ("in
recovery, X" → "X, in recovery, and here too") is a new *shape* of the same
C3 rule. The **07-11 close** deleted the heaviest recovery paragraph in the
corpus even though the whole post was about faith and stories — the "no
recovery bow on the last paragraph" rule generalizes hard.

_— Voice-Delta Agent v0.4_
