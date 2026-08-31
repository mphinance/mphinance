# VOICE-DELTA — what Michael changes between the machine's draft and the post he ships

_Voice-Delta Agent v0 · 2026-06-18 · feeds the writer, never writes a public word._

Not vibes. This is built by pairing each **machine-given draft** (the markdown that
got pushed) against the **version Michael actually shipped** on
mphinance.substack.com, and reading the diff. What he cuts is as much his
fingerprint as what he keeps.

**Read this first (honest constraints):**

- **N = 18 complete pairs** (previous 10 anchors/held-out/live ships + 8 new
  from 2026-08-31 refresh: 06-26 measure-voice-file, 06-27 youre-not-drowning,
  07-02 out-recruited, 07-04 mygreenknight, 07-08 open-rate-what-to-write,
  07-11 accidental-religion, 07-19 signal-was-right (paid), undated career-interview).
  Still not statistics, but enough to test whether the rules below GENERALIZE to
  pairs they weren't derived from.  Every rule is followed by real receipts; if a
  rule has one receipt, it's a hypothesis, not a law.
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
| 07-19 | "The Signal Was Right. I Was the One Not Listening." | same title | paid | live (paid; FIG + SLB coil trade) |
| 07-11 | "How to Accidentally Start a Religion (Or a Bull Market)" | "The Church of Number Go Up" | free | live |
| 07-08 | "📊 What Does Your $OPEN Rate Want You to Write?" | same title | free | live |
| 07-04 | "Someone Asked Me to Read Their Substack. So I Sent an AI." | "…(Yes I read it too)" | free | live (mygreenknight shoutout) |
| 07-02 | "I Got Out-Recruited By My Own Reader. Now I'm Opening the Door." | "…By Another Writer…" | free | live |
| 06-27 | "You're Not Drowning. You're Fighting the Wave." | same title | free | live |
| 06-26 | "Stop Vibing Your AI Voice File. Measure It." | "…(Write Better With AI)" | free | live |
| undated | "Let a robot interview you about your own life" | "WHAT DO I WANT TO DO WITH MY LIFE? — Answer It On Your Way To Work" | free | live |
| 07-15 | "Money Where My Mouth Is…" | same title | free | live (Money-Where-Mouth-Is #1, publish-triggers-trade) |
| 07-13 | "…Show the Losses **First**." | "…Show the Losses **Too**." | free | live (Business, dual-voice) |
| 07-09 | "I Tokenized My $GLXY. Do You Actually Own Yours?" | "…Own **Your Tokenized Stocks? (No)**" | paid | live (Macro/crypto) |
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
- (07-11) `How to Accidentally Start a Religion (Or a Bull Market)` → `The Church of Number Go Up` — replaced descriptive process title with a punchy cultural reference (crypto "Number Go Up" meme). The machine explained the theme; Michael named the institution.
- (07-04) `Someone Asked Me to Read Their Substack. So I Sent an AI.` → `…(Yes I read it too)` — added self-correcting parenthetical to the title itself, deflecting the implied "he outsourced the reading."
- (undated) `Let a robot interview you about your own life` → `"WHAT DO I WANT TO DO WITH MY LIFE?" — Answer It On Your Way To Work` — strongest title-as-reader's-voice yet: machine titled the tool; Michael titled the reader's own existential question in ALL CAPS, then added a context/action frame as subtitle ("On Your Way To Work"). He'll shout the reader's unspoken question back at them.

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
- (06-27) `the other night` → `today` — immediacy fires on a Mindset post (non-trading), confirming the rule is content-independent.

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
- (07-02) `I am opening the affiliate program up` → adds `kinda without the other founders' permission. That's how we roll. I hope :)` — mid-sentence admission of a potentially awkward move, sealed with a smiley. Won't let a clean "I did this" claim stand without the caveat that undercuts it.
- (07-02) Exact numbers fuzzed: `122 signups. 66 of them are still paying` → `over 100 signups, and at least half of them are still paying` — would not let the machine's precise numbers stand; rounded them rather than let them look more certain than they are.
- (07-04) `the answer was immediate` + `(considering I've yet to answer him on Discord, and am letting this post do so for me)` — admits the post IS the reply, not a follow-up to one. The parenthetical self-corrects the implied "I responded immediately" with the truth that he still hasn't responded on Discord.
- (07-04) `(most of which I already knew, but it's been a minute and was nice to catch up!)` — deflates "the AI found amazing insights" with "I already knew most of this."
- (07-08) `I built a free tool` → `I updated a free tool` — one word. Won't let "built" stand if the honest word is "updated."
- (07-11) `The Greek Septuagint rendered it parthenos` → `Some Greek dude rendered it parthenos` — replaces academic proper noun with casual demystification. He will swap technical vocabulary for plain colloquial when the term is doing status-signaling rather than explaining.
- (07-19) `so I never wrote about it` + adds `as I've always made sure to back my claims with data` — self-corrects the potential "why didn't you tell us about this signal?" implication up front.
- (undated) `because they were able to automate themselves out of a career (hi)` — the one-word parenthetical `(hi)` as ultra-compressed self-inclusion. New micro-variant of this rule: will identify himself within a described group with a single word in parentheses rather than a full aside.

**A4. Wires the post into the network.** The machine writes in a vacuum; he adds the
restack bait and the product clicks.
- ADD `Math & Cynce had a great macro write-up yesterday - go read his if you're not sure what's going on.`
- ADD `don't forget to follow https://x.com/TraderDaddyBot - she's getting upgraded everyday!` + a direct `traderdaddy.pro/screeners/…` link under each screener.
- (07-04) ADDED entire new section `## Substack, While I Have You` — a product-critique / platform-suggestion section added mid-post when the post gives him a relevant observation about a platform. He uses posts to make product suggestions directly to platform operators ("A simple 'hey, a writer in your space just subscribed' would have connected us weeks ago"). The post becomes a channel for direct feedback, not just reader-facing content.

**A5. The self-deprecating tangent.** An unprompted opinion that undercuts himself.
The machine stays on task; Michael wanders and deflates.
- ADD `It's called Crossover, because that's what Sam named it because I can't be bothered to actually name the things I create. Side note - if you're one of those that will dwell on a name or colors or logo for longer than the actual product took you to make - for the love of God let AI do it.`
- ADD (after the FIRE "one more year" math) `Except I can't measure sanity in a little chart.`
- (07-04) ADD `People - if you want something in life… try this crazy thing called asking.` — tangential life-advice dropped into the opener when the post's premise is just "someone asked me a favor and I said yes."
- (undated) ADD `So, if you want some advice on how to work smarter, not harder - Gemini says I'm your guy.` — after sharing what the AI interview told him about his own career, punctuates with wry humor that lets the AI be the authority.
- (06-26) ADD note that the harness caught him violating his own "Here's the truth" rule: `It's definitely not perfect yet, as it loves to call me out when I miss one of my own edit rules, such as "Here's the Truth"` — willingness to publish the fact that he failed his own style-rule.

**A6. Dog-foods the tool and shares the uncomfortable result.** When the post introduces a tool or process Michael built, he runs it on himself and shares what came back — including what he didn't want to hear.
- (undated) After presenting the career-interview prompt: `I ran myself through the exact interview I am about to share with you. The first part wasn't a complete surprise… apparently I want to become an Automation Consultant/Architect for small businesses.` — shares his own AI-interview result verbatim, including the surprising career direction he didn't know he had.
- (06-26) Shares that his voice-file accuracy harness caught a banned phrase he missed himself (`Here's the truth` survived in his corpus). Two pairs — hypothesis promoted to rule. The machine's output is evidence he'll use against himself.

---

## What he CUTS

**C1. The meta-transition / windup** — the announce-before-you-say-it line.
- `Now the confession. This isn't a Bloomberg terminal…` → `This isn't a Bloomberg terminal…`
- `Here is the part that made me sit up. I built this machine…` → `So here's the conviction. I built this machine…`
- (07-07) cut the two windup lines whole: `So here's the argument I've been losing at dinner, finally written down as the thing that wins it.` and `That's the whole thesis. The rest of this is proof that it's already running.` — he refuses to announce the thesis before making it; the claims just start.
- (07-13) `Now here is the part I do not get to write. Take it away.` → `Now, to hand the mic to Sam.` — cut the self-referential windup (and the `## Sam:` header + horizontal rule); the handoff line carries the voice change on its own. Also `So here is the deal today.` → `Here's the deal today.` (drop the "So", contract "here is").
- (06-27) Cut two-paragraph opener: `I named myself Momentum Phinance and it took me an embarrassingly long time to notice I'd been describing my whole life. Momentum is just a wave. You don't argue with it…` — the whole "here's what this is about" framing before the actual content. Also cut `I want to talk about the weaknesses and the unfortunate situations everybody tells you to "turn into strengths."` — direct announce-before-you-say-it.
- (07-11) Cut `I laughed. Then I stopped laughing, because I'd spent that same week reading Tchaikovsky and arguing with friends about exactly this, and I realized the show wasn't doing science fiction. It was doing a documentary with the serial numbers filed off.` — the "here's when I had the realization" bridge cut; shipped goes straight from the Orville story to the abstraction.
- (07-11) Cut `So here is the entire discipline, and it's nothing fancier than keeping the question mark screwed on.` — classic announce-before-announce cut.
- (07-08) Cut `Now the part you can actually use.` — another announce-before-you-say-it, even a short one.

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
- (07-11) Cut entire recovery closer: `Recovery taught me this before markets did. Half the wreckage in my life came from stories I swallowed without pulling a single thread, because pulling the thread meant the story might not hold, and I needed it to hold. Getting sober was mostly learning to read my own primary sources. The market just charges tuition for the same lesson.` — the wisdom was kept (implied in the rest), the explicit "in recovery" attribution was dropped.
- (07-19) `In recovery nobody tells you to go find a better program when you are struggling. They tell you to work the one you have.` → `Nobody tells you to go find a better program when you are struggling in recovery and they shouldn't here either.` — the "In recovery" framing at the front was collapsed into the middle, de-emphasizing the program-room setting while preserving the wisdom. **Also kept:** (07-27) "Urge surfing, the literal version. It's a term they actually teach you in recovery." survived verbatim — C3 nuance: recovery jargon ships when it IS the metaphor's load-bearing term, not just a program reference or aside.

---

## Consistency fixes he makes every time (canon + framing)

- **Sam is "her."** Every Sam pronoun the machine wrote as male got flipped: `feel his stomach drop` → `her`, `his best C-3PO` → `her`, `He just did` → `She just did`, `he would actually take` → `she would actually take`. (The TraderDaddyBot is "she" too.)
- **`the` → `my`** (ownership): `the entire job` → `my entire job`; `The only knock` → `My only knock`.
- **Solo `I/my` → branded `Phund/we`** when it's about the account: `my own brokerage account… what I'm holding` → `the Momentum Phund's brokerage account… what we're holding`. (07-13) `What **I** actually built` → `What **we** actually built` — same conversion on the product, not just the account.
- **Generic → named brand:** `options flow in another` → `TradingView in another`; `I built a button` → `The Claude button`. (07-13) named the in-app assistant: `TraderLady` → `TraderLady (Arya)`, while keeping **Sam** as the post's narrator voice — the swarm has two named AIs and he distinguishes them.
- **Feature lists become branded product taxonomy, not prose. (07-13, hypothesis — first pair)** When the machine wrote a narrative tour (`It watches the tape for size…`), he rewrote it into named product categories, each a `Label. One-line promise. Component, component, component.` block pulled straight from the live product: `Options Flow. See what smart money is doing before the move happens. …Unusual Activity, Live Flow, Heat Map, Sector & Earnings Flow.` He also ADDED categories/detail the machine under-specified (`Calendars & Intel`, portfolio tracker, AI strategy ranker, CSP setups). Takeaway for the writer: when the post lists what the platform does, give the real taxonomy in his terse label-tagline-components shape, not a friendly prose walk.
- **Tickers in body prose are redacted.** When a post names a specific stock ticker in regular narrative text (not in a machine-readable trade block), the shipped version blanks it. Five pairs total: PEP + HOOD (07-13, first observed), ONDS (07-02), NVDA (06-27), NVDA (07-11), FIG + SLB in paywall teaser (07-19). Trade blocks that fire real orders ship intact (07-15, 07-19 trade rules). Read as compliance/legal, not style.
- **Bold inline markdown stripped.** When given.md uses `**bold**` for section items within body paragraphs (trait headers, policy tiers, section labels), the shipped removes the bold formatting. Text stays; markup goes. Two pairs: 06-27 stripped `**ADHD is a wave too.**`, `**Knowing where your water ends.**`, `**Urge surfing, the literal version.**` etc.; 07-02 stripped `**General affiliates earn 15% recurring.**`, `**Proven performers scale to 25 or 35%.**` etc.
- **Disclaimer moves to the TOP and becomes a bit:** bottom-of-post `Not financial advice…` → top, rewritten: `Hi! I'm a super legit "not financial advice" disclaimer that you've read so you're not going to sue me now. Good talk.`
- **Typos ship.** `my my uncle`, `it slightly up` survive (07-07 added `an TraderDaddy SDK` and `TL,DR;`). He does not sand the post to corporate-smooth; the small imperfections read as a human was here.
- **Direct reader-address, unhedged.** He turns third-person copy at the reader mid-line: `a sales team that works for free.` → `…for free. I hope (hint, that's you).` and closes the piece by talking to the co-founder AND the reader: `Art, I solved it. Again.` → `…Again. You might wanna pick up the mic I'm about to drop.` **(07-07 only — single pair, not yet a law.)**
- **Adds the credibility clause on the product.** `the thing that's actually expensive to build and run.` → `…to build and run, and were designed by a team of professional traders with years of experience.` — when the post is the funnel, he slips the sell in as a subordinate clause, never a sentence of its own. **(07-07 only — watch on next Business post.)**

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

**Eighteen pairs**, the signal remains **dense and consistent**: the machine builds a clean
scaffold and a few keeper lines; you spend your edit budget on **honesty
(self-correction), warmth (physical metaphors), immediacy (time compression), and
distribution (shoutouts, plugs, canon)**.

The 2026-08-31 refresh added 8 new complete pairs, confirming prior hypotheses
and promoting several patterns to rules:

1. **Ticker redaction is now a rule** (5 pairs total): tickers in body prose blank on
   ship; trade-block tickers for the automation mechanic ship intact (07-15, 07-19).
2. **Bold inline markdown stripped** promoted from observation to rule (2 pairs).
3. **A6 (dog-fooding: uses tool on self, shares uncomfortable result)** promoted from
   hypothesis to rule (2 pairs: career-interview + measure-voice-file).
4. **Immediacy (Rule 2) confirmed on Mindset content** — not just trading posts (06-27).
5. **C1 (meta-windup cut) fires across all content types** — 5 new receipts.
6. **Title-as-reader's-voice** reaches its fullest form (undated career-interview):
   the machine titles the tool; Michael shouts the reader's own unresolved question
   back at them in ALL CAPS.

The held-out pairs, the Business posts, and now the Mindset/paid posts all
replicate the core rules. The voice is content-independent. When someone says
"VOICE.md isn't accurate," this is the answer: pair the drafts against the ships,
run the harness, point at the Δ.

_— Voice-Delta Agent v0.4 (2026-08-31 refresh, 8 new pairs)_
