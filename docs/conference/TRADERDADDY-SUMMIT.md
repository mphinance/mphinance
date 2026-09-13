# TraderDaddy Live

### Two day summit. Schedule outline v1.

**Format:** 2 days, in person, one main stage, one workshop room.
**Rule that governs the whole program:** no performance claim goes on stage without a benchmark, a sample size, and a link to the data.

---

## The Thesis

A fund pays a semiconductor analyst three hundred grand a year to explain what is happening inside a fab.

We already have that person. She works there. She has been posting about lead times for eight months and nobody has ever asked her to connect it to a trade.

**Retail's only genuinely unfair advantage is that retail has jobs.** Nurses see which drugs move before the print. Freight brokers watch rates soften six weeks ahead of a guidance cut. HVAC installers know which builders stopped ordering. Insurance adjusters see the claims curve bend. That is expensive alt data, bought badly and late by funds, sitting in a Discord for free because the people holding it do not think of it as market information.

The other half of the community has the inverse problem. They can read a chain, size a position, and manage a roll, but they have no idea what is actually happening inside the companies they trade.

Two days of putting those two people in the same room.

- **Day 1, The Floor.** Domain knowledge into thesis. Members are the program.
- **Day 2, The Machine.** The mechanics that turn a thesis into a strike, and the proof that any of it works.

Day 1 is why people come. Day 2 is why they subscribe.

---

# DAY 1: THE FLOOR

| Time | Session | Fmt |
|---|---|---|
| 09:00 | Welcome: what this is for | 15m |
| 09:20 | Keynote: Your Job Is Alt Data | 25m |
| 09:50 | THE FLOOR I | 40m |
| 10:35 | THE FLOOR II | 40m |
| 11:20 | Break | 15m |
| 11:35 | THE FLOOR III | 40m |
| 12:15 | Lunch, cards collected | 60m |
| 13:15 | Panel: When Your Edge Is Also Your Employer | 55m |
| 14:15 | THE FLOOR IV | 40m |
| 15:00 | Macro Texture: The Ground Truth Read | 35m |
| 15:40 | Lightning: The Thing I See At Work | 50m |
| 16:30 | Close: the four theses go on one slide | 20m |
| 18:30 | Loss Night | open |

### 09:20 Keynote: Your Job Is Alt Data
Short on purpose. Every job is a data feed. You stand inside a company's operations all day and then read its stock like a stranger.

Ends with the assignment: **write your one thing on the card in your badge.** One thing you know from work that is not in a filing yet. Cards are collected at lunch and drive the afternoon lightning round.

### THE FLOOR (four sessions, 40m each)
The signature format. Two chairs.

- **Seat one, the operator.** Works in the industry. Cannot necessarily trade it.
- **Seat two, the trader.** Can trade anything. Knows nothing about the industry.

A moderator drives them to one live output on the screen: **a thesis with a ticker, a mechanism, a timeframe, an invalidation, and a way to be measured.** The room watches domain knowledge become a position with a stop on it.

Four industries, cast from whatever the membership actually has. Likely candidates: semis and hardware, freight and logistics, healthcare and pharma, energy and the trades.

*Casting note:* pick operators who post specifics, not people who post opinions. The operator does not need stage experience. The moderator carries the session.

### 13:15 Panel: When Your Edge Is Also Your Employer
Not optional. The event is actively telling people to convert workplace observation into positions, and running that program without this panel is reckless.

- Mosaic theory and where it stops
- Why "everyone at work knows this" is not a defense
- Blackout windows and trading policies
- The specific risk of posting it in a Discord under a handle tied to your employer

*Forced question:* read your last work related post out loud and say whether you would show it to your general counsel.

### 15:40 Lightning: The Thing I See At Work
Twelve members, four minutes, hard cutoff, pulled from the lunch cards. One observation from your job, why it is early, which ticker it touches.

Cheapest hour to produce and the one people will quote for a year. It also recruits next year's Floor operators.

### 18:30 Loss Night
Open mic, three minutes, one rule: **you may only present a loss.** Pivot to a win and the mic goes away. It is the only social format that produces real conversation in a room full of traders, because it removes the incentive to perform.

---

# DAY 2: THE MACHINE

| Time | Session | Fmt |
|---|---|---|
| 09:00 | Dealer Positioning: What GEX Actually Is | 45m |
| 09:50 | How Income ETFs Find Strikes | 50m |
| 10:40 | Break | 15m |
| 10:55 | Volatility: Implied, Realized, and the Gap | 45m |
| 11:45 | Panel: The Premium Is Real / The Premium Is Rent | 45m |
| 12:30 | Lunch | 60m |
| 13:30 | Reading The Tape: Flow, Listings, and What They Miss | 40m |
| 14:15 | THE AUDIT, live | 75m |
| 15:35 | Workshop: Benchmark What You Already Have | 60m |
| 16:40 | The Circuit Breaker | 25m |
| 17:05 | Close: roadmap and the pledge | 20m |

*Workshop room runs parallel all day: Build One Agent, and a hands on data lab pulling the endpoints used in the morning sessions.*

### 09:00 Dealer Positioning: What GEX Actually Is
Mechanics first, because the next two sessions depend on it and most of the room is using the word without the model behind it.

- Why a dealer hedges, and why that hedging is mechanical rather than opinionated
- Positive gamma pins price, negative gamma accelerates it. Same tape, opposite behavior.
- The flip level as the regime boundary, not a support line
- Walls: what makes a strike sticky, and when a wall stops mattering
- Charm and vanna into expiry, and why Thursday afternoon is a different market than Tuesday morning
- **What it is blind to:** GEX is a snapshot of one input. It does not know why anyone is positioned that way.

### 09:50 How Income ETFs Find Strikes
The session I would build the whole second day around. Thirty billion dollars of systematic option writing runs on published rules, files its holdings daily, and almost nobody reads it.

**Part one, what you actually own.** Three archetypes that look identical on a yield screen and behave nothing alike:

- **Covered call on a real equity sleeve.** Owns the shares, writes against them.
- **Synthetic long.** Owns Treasuries plus an options structure replicating the underlying. Holds none of the stock. Most buyers do not know this.
- **Total return swap.** Exposure is a contract with a bank. No options at all.

**Part two, the strike fingerprint.** Every fund leaves one, visible in the daily holdings:

- **Weighted moneyness.** How far out of the money they write. A fund writing at 1.3 percent over is doing something categorically different from one writing at 5.
- **Weighted DTE.** Three days versus thirty. Weekly rollers create recurring, schedulable supply at a known strike band. Monthly writers do not.
- **Call coverage.** What share of the book is actually written against, which is the difference between the marketed strategy and the live one.
- **Upside room.** The number that tells a holder how much of a rally they are permitted to keep. When it goes negative the fund is already capped and the holder does not know it.

**Part three, why an equity trader should care even if they never buy one.** Those written calls are dealer long calls. A fund rolling billions weekly into the same strike band is manufacturing the wall you were looking at in the 09:00 session. If a name has income ETFs written on it, there is a ceiling on the tape with a calendar attached to it.

**Part four, the history.** Pull the archive and watch strike discipline change. Funds widen their strikes after they get run over in a rally, and tighten when they need to defend a distribution. That drift is a behavioral tell and it is only visible over time.

*Data:* `api.tickertrace.pro/api/v1/income` for the overview across the fund universe, `/api/v1/income/{fund}` for a single fund, plus the holdings history for the drift analysis. The archetype, weighted moneyness, weighted DTE, call coverage, and upside room fields are already there. This session is a live screen share, not slides.

### 10:55 Volatility: Implied, Realized, and the Gap
- What the market thinks it will move versus what it did
- Why range based estimators pull more out of the same bars than close to close does
- The premium ratio, and what it looks like when there is no edge in selling
- Reading two numbers instead of one: **the index rising on a strong day is not a warning by itself. It is a warning when the vol of vol legs up with it.** One is noise. The two together are positioning.
- Translating a ratio into a strike you would actually accept assignment on

### 11:45 Panel: The Premium Is Real / The Premium Is Rent You Pay Later
*The disagreement:* is selling volatility a structural edge, or fair compensation for a tail that eventually collects?

Four seats: a systematic seller with a multi year record, a tail buyer who made their year in one week, someone who explains where the premium originates, and a small account trader running it under real capital constraints.

*Forced question:* what does your book do in a week the index gaps down twelve percent, and has that already happened to you?

### 13:30 Reading The Tape: Flow, Listings, and What They Miss
- What a large print does and does not tell you, and why "unusual" is mostly a hedge
- New options listings as an early institutional tell, and the noise problem when a venue's list flip flops
- Persistence: which names keep reappearing versus one day wonders
- Where every flow read fails, which is that you see the trade and never the reason

### 14:15 THE AUDIT (live, 75m)
Centerpiece. A member submits a system in advance. One is selected. It goes on the projector and three people take it apart in front of its author, who is on stage, consenting, with right of reply throughout.

*What we hunt:* lookahead. Survivorship. Regime overfit. The same indicator computed four slightly different ways in four files, all named the same thing, none agreeing. Silent defaults, where a missing value quietly becomes zero and the pipeline prints the same confident verdict every day for a month.

*Rules:* the author volunteers, can stop it at any time, and no account balance goes on screen. We audit code and process, never the person.

*Compensation:* membership for life.

**The platform goes first.** One of our own screeners gets audited on stage before any member's does. If the host will not sit in the chair, the format is theater and everyone watching will know it.

### 15:35 Workshop: Benchmark What You Already Have
Hands on. Take whatever results you walked in with, add index excess return, deduplicate repeated picks, state a sample size.

A real share of the room will find their edge is inside the noise band. Say that from the stage before the session starts so nobody feels ambushed. It is still the most valuable hour of the two days.

*Seed example:* a convergence ranking that scored a name higher when more independent sources agreed on it. Four leg agreement returned 17 percent. Two leg returned 48 percent. Anti predictive for months. The raw read said flat. The benchmarked read said losing. Nobody catches that without the benchmark.

### 16:40 The Circuit Breaker
Closes the content, because it decides whether anyone is still here next year.

Sizing against account size. Three levels of stop: premium, thesis invalidation, and the portfolio breaker at fifteen percent off peak net liquidation. That last one is the rule everybody skips, and it is the only one that is emotional rather than mathematical, because obeying it means going flat and sitting still while every instinct demands you make it back.

Ends on the rule no model computes: never size a position that causes emotional distress. If you are checking your phone every thirty seconds, you are too big.

### 17:05 Close: The Pledge
Members who want in publish a benchmarked scorecard of at least thirty picks within twelve months, losses included, at a public URL. Signers go on the site. Next year the site shows who shipped and who did not.

Retention mechanism, year two marketing, and the only exit survey worth reading.

---

## Operations

**In person.** The whole thesis is that two people who would never meet end up in the same room, and the hallway is where an operator and a trader actually pair off. That does not happen over a stream. The Floor, Loss Night, and the Audit all need a physical room with the door closed.

**Size.** 120 to 200. Small enough that nobody hides and everyone can be met. Do not chase a bigger number in year one. A packed 150 room is a better asset than a half empty 400 room, in the photos and in the feeling.

**Venue.** One main room, one breakout room for the workshop track, and a bar or lounge area that stays open after 18:00 for Loss Night. Hotel conference space is the boring correct answer for v1 because it bundles AV, catering, and a room block. Independent venues are cheaper on paper and then charge you for everything the hotel included.

**The wifi is not a detail.** Half the program is people pulling live data on stage. A conference about verification that cannot reach an API is a story that follows the event for years. Get the hardwired drop for the stage, test it the day before, and have a cellular hotspot as backup.

**Dates.** Avoid opex week, avoid FOMC, avoid the first week of earnings season. A Friday and Saturday costs attendees one vacation day instead of two, which matters enormously for a room built around people with day jobs.

**City.** Pick for flight cost and hotel cost, not for prestige. Somewhere with a cheap major airport and sub two hundred dollar hotel rooms. Every dollar of travel cost is a member who does not come.

**Tickets.** Discounted for existing members, since the members are the program. Full price for non members with a trial included. The ticket should be priced to cover the room, not to profit. The event is the funnel and it does not need disguising.

**Budget floor, the things people forget.** Room rental, AV and a sound tech, catering and coffee (which is more than you think), event insurance and a liability rider, badges and printing, a recording setup, speaker travel for anyone brought in, and a contingency line. Get the AV quote before you commit to a venue. It is routinely the second largest line item and it is the one that surprises first time organizers.

**Room block.** Negotiate one with the hotel. It costs nothing, it lowers attendee cost, and the block pickup number gives you an early read on real attendance well before ticket sales tell you.

**Sponsors.** Data, brokers, infrastructure yes. Signal services, prop firm affiliates, anything selling picks or funded accounts, no, at any price. No sponsor gets a stage slot.

**Recording.** All of it, free, within two weeks. The ticket buys the room and the hallway, not the information.

**Conduct.** Standard and enforced, with a named contact who is not on the program. Plus the addition this event specifically needs: **the Audit and Loss Night are about code and process, never about people or account balances.** The moment either becomes humiliation, nobody volunteers again and both formats die permanently.

---

## Where This Goes Wrong

**1. It reads as a two day commercial.** It is a vendor hosted event and pretending otherwise fools nobody. The fix is structural: one clearly labeled product session out of roughly fourteen, the receipts rule applies to our own numbers with no exception, and our screener takes the Audit chair first. If any of those three get quietly softened in planning, the event becomes the thing it was built as the alternative to.

**2. Nobody volunteers for the Audit.** The best session on Day 2 needs someone to accept public reputational risk. A cold call for volunteers comes back empty. Line one up privately before tickets go on sale, and be ready to audit our own screener as the only entry.

**3. The operators are the whole product and the operators are amateurs.** Day 1 lives or dies on four people who have never spoken at an event. Mitigation is casting and prep: people who post specifics, a thirty minute prep call each, strong moderators who can carry a quiet guest. Record one Floor session in advance as insurance and as the promo asset.

**4. Somebody trades on something they should not have said out loud.** The compliance panel is necessary and not sufficient. Every Floor session opens with the moderator stating the line, and any thesis built on stage gets checked against it before it goes on the slide.

**5. The room is half empty.** The one that actually kills first year events. A Discord with thousands of members converts to in person attendance at a rate that is always lower than it feels, because saying "hell yes" in a channel costs nothing and a flight costs six hundred dollars. Every deposit gets signed before the interest is measured. Mitigation is the pre commit list below, and a venue contract with an attrition clause you have actually read.

---

## The Grunt Work, In Order

Nothing here needs a decision from anyone else. This is the part that has to happen before the program is worth showing around.

**1. Measure real travel intent before spending a dollar.** Not a poll asking "would you come to a conference," which returns a meaningless yes. A form asking for a city, a month, a price band, and how many nights they would stay. Then the question that separates enthusiasm from attendance: **would you put down a fifty dollar refundable deposit to hold a seat.** The deposit count is the only number that predicts a full room. Everything downstream keys off it.

**2. Pick two candidate cities and two candidate weekends.** Constrain by airport cost and hotel cost. Put both options in the same form so the answer picks itself.

**3. Get three venue quotes.** Ask specifically for: room rental, AV package with a tech, food and beverage minimum, the attrition clause, and the cancellation terms. The F and B minimum is what actually sets the floor on your budget, and first time organizers usually find that out after signing.

**4. Build the budget from the quotes, then back into a ticket price.** Fixed costs divided by a conservative attendance number, which is the deposit count and not the interest count. If the ticket price that falls out is higher than the room will pay, the event is smaller or it is one day. Find that out now.

**5. Identify the four Floor operators privately.** Longest lead time of anything on the list, and the hardest to rush. Read back through the community for people who describe their actual work in detail rather than posting opinions. Approach individually, not in a channel. Nobody volunteers to be the semiconductor expert in public.

**6. Lock the Audit volunteer, or accept that it is our own screener.** Either answer is fine. Not having an answer two weeks out is not.

**7. Write the speaker agreement with the receipts clause in it.** One page. Send it before anyone is booked. Whoever will not sign it has told you something useful for free.

**8. Then, and only then, announce.** With a city, a date, a price, and a program. Announcing a conference before you have those four things is how you end up personally guaranteeing a hotel contract for an event nobody bought a ticket to.

Steps 1 through 4 are a couple of weekends of unglamorous work and they determine whether any of the rest is real.

---

## Session Bank

The schedule above uses maybe fourteen slots. Here is the pool to draw from and swap against, sorted by track. Each line is a session title and the one thing it teaches. Anything with a data source noted is already ours to demo live, which means it can be a screen share instead of slides.

### Market structure and dealer mechanics
1. **What GEX Actually Is.** Why dealer hedging is mechanical rather than opinionated. Walls, the flip level as a regime boundary, and what it is blind to.
2. **How Income ETFs Find Strikes.** Thirty billion of systematic writing on published rules. Archetype, moneyness, DTE, coverage, upside room. *Data: `/api/v1/income` plus 122 daily holdings CSVs with full option legs.*
3. **Opex Week Is a Different Market.** Charm and vanna into expiry, why Thursday afternoon does not behave like Tuesday morning, and the monthly unclench.
4. **0DTE and What It Did to the Tape.** How same-day flow changes intraday behavior for everyone, including people who never touch it.
5. **Pin Risk and Friday Afternoon.** What actually happens at expiry: assignment, exercise, and the max pain argument, including where it is nonsense.
6. **Reading a Chain for Liquidity, Not Direction.** Spread, open interest versus volume, and how to know in advance that you will not be able to get out.
7. **Index Versus Single Name.** SPX, SPY, XSP: cash settlement, assignment risk, and the 1256 tax treatment nobody mentions until April.
8. **Dark Pools and Off-Exchange Prints.** What a big print means, what it does not, and why most "unusual" is a hedge.
9. **New Options Listings as an Early Tell.** When a venue lists a name, somebody asked. *Data: `/api/v1/options-listings`.*
10. **Short Interest, Borrow, and the Cost of Being Right Early.** Hard-to-borrow as a signal and as a trap.
11. **Index Rebalances as Forced Flow.** Scheduled, public, mandatory buying. The one calendar event with a known counterparty.
12. **Creation, Redemption, and Why an ETF Can Detach.** What an authorized participant does, and what it means when the mechanism jams.

### Volatility
13. **Implied, Realized, and the Gap.** The premium ratio, and what it looks like when there is no edge in selling.
14. **Two Numbers, Not One.** The index rising on a strong day is not a warning by itself. It is a warning when the vol of vol legs up with it.
15. **Skew and Term Structure.** What the shape is telling you that the level is not.
16. **Earnings: Right on Direction, Wrong on the Trade.** Crush, and why the obvious expression loses.
17. **PANEL: The Premium Is Real / The Premium Is Rent You Pay Later.** Structural edge or fair compensation for a tail that eventually collects.

### The income playbook
18. **The Wheel, Mechanically.** Delta and DTE selection, rolling for a credit and never for a debit, and the assignment math done honestly.
19. **Covered Calls Against Something You Actually Want to Keep.** Getting paid without accidentally selling your position.
20. **LEAPS and the Poor Man's Covered Call.** Where the leverage helps and where it quietly removes your margin for error.
21. **Small Account Reality.** Running any of this under real capital constraints, where one assignment is your whole week.

### Systems and verification
22. **Build One Agent.** File, tools, loop. Not a swarm. Hands on, everyone leaves with something that runs.
23. **THE AUDIT.** A member's system on the projector, taken apart live, with our own screener going first.
24. **Benchmark What You Already Have.** Index excess return, deduplication, sample size. The hour where edges vanish.
25. **Why Your Screener Keeps Finding the Same Forty Names.** Correlated filters, survivorship, and the illusion of a wide net.
26. **The Bug Class That Eats Everyone.** A missing value quietly becomes zero and the pipeline prints the same confident verdict for a month.
27. **Automating the Journal, Not the Judgment.** The four gates for what should and should not be a machine's job.

### The human side and the business
28. **The Circuit Breaker.** Sizing, the three stop levels, and the portfolio breaker everyone skips.
29. **Tilt, Revenge, and the Trade You Take to Get Even.** Character defects wearing a spreadsheet.
30. **Taxes for Active Traders.** Wash sales, 1256 contracts, and the mark to market election.
31. **PANEL: When Your Edge Is Also Your Employer.** Mosaic theory, blackout windows, and the line.
32. **PANEL: Guru Economics.** Selling education without becoming the thing you complain about.
33. **Loss Night.** Three minutes, losses only, mic taken if you pivot to a win.

### Day 1 Floor tracks, cast from the membership
34. Semis and hardware. 35. Freight and logistics. 36. Healthcare and pharma. 37. Energy, utilities, and the trades. 38. Insurance and claims. 39. Construction and homebuilding. 40. Retail and consumer. 41. Ag and food. 42. Defense and government contracting.

---

## Open Questions

- Two full days in person, or one day plus an optional workshop morning for people who came in the night before?
- Four Floor sessions or three, with the fourth slot going to a second lightning round?
- Does the pledge scorecard get hosted by us, which makes it real but makes us responsible for it, or self hosted with us only linking?

~ Michael
