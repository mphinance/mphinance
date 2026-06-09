# Time to See If My Marketing Is Half as Good as My Trading

*Tags: traderdaddy pro, options flow, GEX, unusual activity, screeners, trading tools, review*

<!--
HERO IMAGE PROMPT (16:9) — generate in Substack:
Retro screen-print editorial poster, aged cream paper, muted navy / deep red / gold
palette, halftone texture, warm and a little tongue-in-cheek. A workbench seen from
above: a soldering iron and circuit board on one side morphing into a glowing trading
terminal on the other — the same hands that build the tool also trade with it. Stacks
of printouts labeled "OPTIONS FLOW," "MOMENTUM PULLBACK," "2X ETF," a coffee ring,
and a small hand-drawn GEX curve on a napkin. Banner ribbon along the bottom:
"I BUILD THE SCREENERS. THEN I TRADE THEM." No people's faces — just the bench, the
glow, and the receipts. Lived-in, honest, builder energy.
-->

*Quick disclosure up top, because most of you already know: I'm not a neutral observer here. I build for [TraderDaddy Pro](https://www.traderdaddy.pro/?ref=8DUEMWAJ). It's a startup — a small crew, founded and run by @Trading_With_Art, with a couple of members who've basically crossed over into the build with us. My corner of it is the screeners — the options flow scan, the momentum pullback, the 2x ETF screener — and a good chunk of the engine under the hood. So this isn't a review from the cheap seats. It's one of the people building the thing telling you what it actually does, and then handing you three reviews from members who don't work on it and have no reason to be nice.*

Alright. Time to find out if my marketing is half as good as my trading.

That's the bar, and it's a low one, because I'd rather ship a screener than write a sentence about it. But the members started leaving reviews in the channel this week, and a few of them were talking about tools our team built without knowing one of the builders was reading over their shoulder — so I figured I'd stop hiding behind the terminal and actually tell you what *we* built and why I think it's worth your time.

Here's the one thing I'd tattoo on this whole piece if I could: **it's a small crew, we ship improvements daily, and we trade the tools ourselves.** That last part is everything. I'm not selling you a screener I dreamed up and never touched — I'm building the exact tools I use to run the Momentum Phund in public, every market morning, with my own money on the line. When something's slow or wrong or missing, I feel it in my own account before you do, and it gets fixed. That's a different kind of product than a black box some marketing team is renting you.

I'll do it the only way I know how: real screenshots, real members, real numbers, and the parts where you still have to do the work yourself. No hype I can't back.

![TraderDaddy Pro — live institutional flow detection: sector flow heat and the most-watched tickers](dashboard.png)

---

## First, the part where other people talk and I shut up

Here's the thing about reviewing a product you built — nobody should believe you. So let me get out of the way and let three members who've never seen the inside of the repo do the talking.

**The one that made my week:**

![Member review — profitability up 69% since TD Pro launched](review-69-percent.png)

> *"My profitability % for my little portfolio is up 69% since TD Pro launched. The live and or recorded lessons are clutch, especially with the inflowing improvements daily."*

Up 69% on a "little portfolio." I didn't ask for that and I can't promise you'll match it — your results are your results. But that's a real member, in the real general channel, with no idea I'd be quoting him.

**The one about the tools I actually wrote:**

![Member review — uses the options flow, momentum pullback, and 2x ETF screeners most](review-screeners.png)

> *"Been using TD Pro for the last month or so and it's been a game changer, especially for improving my entry and exits into plays. The data is formatted in a variety of ways to suit whatever kind of trader you are. I use the options flow, momentum pullback and 2x ETF screeners most often. I recently added in the TradingView indicators which have been the icing on the cake."*

That paragraph is the whole reason I'm writing this. **The options flow, the momentum pullback, the 2x ETF screeners — those are the part I build.** When a member says they're improving entries and exits with them, that's not a marketing line landing. That's code working in someone's actual account — and it's the kind of thing that only happens because the whole team's pulling in the same direction. He also nailed the honest part, and I'm leaving it in on purpose:

> *"Highly recommended if you are looking to add TA to your trading skills but haven't known how to tie it all together. You still need to put in the work of learning technical analysis and trading data analysis."*

Read that twice. The tool doesn't trade for you. It hands you the data and the angles; you still have to learn to read them. Anybody who tells you different is selling you a dream, and I don't do that.

**The one that reads like a trading journal:**

![Member review — GEX calculator and Unusual Activity tab](review-gex-unusual.png)

This one's worth quoting at length because it's the most honest description of *how* the platform actually changes a trader's process that I've seen:

> *"The most simple statement I can say about Trader Daddy — it's changed the way I trade. I've tried multiple ways of trading — investing in shares solely, using index funds, learning how to trade options, running the wheel — CSP's and CC's, and trading 0DTE's on the SPX/NDX indexes. Perhaps the best thing about Trader Daddy is that it covers all the bases on these types of trades."*

Then he gets specific, and this is where I get to nerd out:

> *"Finding the GEX calculator gave me an edge right out of the gate, detailing the put/call walls and the GEX flip zone. However, when I found the Unusual Activity tab under the Options Flow, it absolutely changed my perspective on the market... Filtering to +5M options trades, limiting to unusual trades, and hunting for trades that rate +80 for a score on how 'unusual' they are, I'm finding new ways to print. For me, it's been like having a roadmap on how to trade the market."*

That's not me describing the product. That's a member describing the *exact workflow* the product is built to enable — and three other people reacted with hearts. I'll take it.

---

## Okay, now I'll talk — here's what's actually under the hood

The reviews hit the highlights. Let me give you the builder's tour of the pieces I reach for every single morning, because I trade this account in public and these are the tools I use to do it.

**The screeners (my corner of the build).** Options flow, momentum pullback, 2x ETF — plus more. They're not generic stock screens with a fresh coat of paint. The momentum pullback screener is built around the exact reversal entry I run on the Momentum Phund: a name that's pulled back into support with the flow still underneath it. The 2x ETF screener is for the leveraged crowd who know what they're holding. The point isn't "here are 500 stocks" — it's "here are the handful that match a real setup."

![The Elite Momentum Pullback screener — trend filter, pullback trigger, entry & score, with the filter set I actually use](screener.png)

**Unusual Activity, under Options Flow.** This is the one the third reviewer obsessed over, and rightly. You filter to big premium (+5M), limit to genuinely unusual trades, and sort by an unusual-score so you're not drowning in noise. It's the difference between *seeing* options flow and *using* it.

![The Unusual Activity feed — flow type, sentiment, strike, expiry, premium, volume, and the unusual score on every line](unusual-activity.png)

**The GEX calculator.** Total GEX, the gamma flip level, max gamma strike, and the whole GEX-by-strike chart, laid out so you can see where the dealers are pinned and where the floor falls out. Look at the shot below: spot at $731.69 sitting *below* a gamma flip at $742.08 — that's negative-gamma, vol-pressure territory, and the bar chart shows you exactly which strikes are doing the pulling. If you trade 0DTE on SPY, SPX, or NDX, this is the map. The reviewer called it an edge "right out of the gate." It is.

![GEX calculator — spot vs. gamma flip, total GEX, max gamma strike, and the GEX-by-strike chart with the flip zone marked](gex.png)

**TradingView indicators.** The "icing on the cake," per the screener review — the platform data plus your own TA on the chart, in the place you already work.

**Live and recorded lessons.** This is the part the +69% member singled out. The data is only as good as your ability to read it — so there's actual teaching attached, live and recorded, and it ships improvements basically daily. (I know, because some of those daily improvements are me pushing code.)

There's more — market pulse, sector flow, earnings flow, even congressional trade tracking — but I'd rather you find the two or three that fit how *you* trade than drown you in a feature list. The second reviewer said it best: *the data is formatted in a variety of ways to suit whatever kind of trader you are.*

---

## The honest part (because that's the whole brand)

I'm not going to stand here and tell you a tool will make you money. The member said it cleaner than I could: **you still have to put in the work.** TraderDaddy Pro is the best set of trading tools I've used — and I'd say that even if I weren't one of the people building it — but it's a roadmap, not a chauffeur. It surfaces the unusual trade, the pullback, the wall, the flip zone. You still have to decide what to do about it, size it for your life, and live with the red days. I have plenty of those in public; you've read them.

And yes, the link below is my referral link. Most of you already knew I'm on the team, so I'm not going to be coy about it — and look, this is a startup. A small crew shipping improvements daily because we actually trade this stuff ourselves. If you sign up through the link, it helps us keep the lights on and keep building the kind of tools you just read three strangers rave about. Fair trade, I think. And if you want to follow the person steering the whole ship, go give @Trading_With_Art a read — he's the founder, and he's building this in public the same way I write the Phund in public.

**[Come see what the reviews are about → traderdaddy.pro](https://www.traderdaddy.pro/?ref=8DUEMWAJ)**

So — was my marketing half as good as my trading? You tell me. Drop a comment with the one screener or tool you'd want me to walk through in detail next, and I'll write the deep-dive on whichever gets the most asks. I read every reply.

\- Michael

*Full disclosure, restated plainly: I'm part of the TraderDaddy Pro team and the link above is a referral link. The three reviews are real, unsolicited, and from members who don't work on the platform. Nothing here is financial advice — it's one builder-trader telling you about the tools he uses with his own real money. Trading involves real risk and you can lose money. The +69% figure is one member's self-reported result and is not typical or guaranteed. Do your own work and size for the downside.*
