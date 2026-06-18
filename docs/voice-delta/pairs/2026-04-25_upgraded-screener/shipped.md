TITLE: I Upgraded Every Screener to a Scoring Model. Here’s What Changed.
SUBTITLE: Four tools. A small army of AI models. And a daily report that no longer takes 10 minutes to scroll
AUDIENCE: only_paid

Not financial advice. I am a trader, not your financial advisor. Past screener performance does not guarantee future picks.

(Note: This is a post about the process: how the code actually got written - with just a few results. I have a lot to share about actual money, broker changes for the Momentum Phund, and the overhaul of the Decay Derby wheel tracker, but I am saving that for the next post. One thing at a time.)

Finally, don’t forget to follow https://x.com/TraderDaddyBot - she’s getting upgraded everyday!

- 
- I heard something awhile back, I believe my my uncle, that sounds too simple to be useful: 

Every day, it gets a little easier. 

But you gotta do it every day. 

That is the hard part.

But it does get easier.

I have been sober long enough to know they are right. And I have been building trading systems long enough to know it applies there too. You do not wake up one morning with a working pipeline. You show up. You find what is holding you back. You refine it. You go to sleep. You do it again.

Last night I looked at four of the screeners that run every morning inside the Ghost Alpha pipeline and realized something uncomfortable. They were working, but they were lazy. They were simple pass/fail filters.

There is a limitation that lives in almost every basic screener. It stops looking the moment it finds something. You build a filter. Stock passes. Done. You never ask if there was something better three rows down. You never ask if the pass was barely passing or crushing it. You just take the first yes and move on.

That was most of the screeners in the Ghost Alpha pipeline. Four of them. They were picking decent setups, but they lacked nuance. They settled for “good enough” instead of hunting for the absolute best.

Last night I gutted all four and upgraded them from simple boolean filters into multi-factor scoring models. This is what changed.

- 
- 
[caption] A futuristic, minimalist data visualization showing four interconnected data streams merging into a glowing neon core. Dark mode, synthwave aesthetic, high contrast.
## The Leveraged ETF Screener
Old logic: Sort by ADX descending. Take the top one. Done.

Problem: ADX alone tells you a trend exists. It does not tell you if the trend started yesterday or ran for 45 days and is exhausted. It does not care about volume. It definitely does not care that the underlying just reported earnings and is gapping up 18% into resistance.

New logic: A six-factor EdgeScore. ADX still counts. But so does relative volume (is money actually flowing?), VWAP reclaim (is price respecting structure?), momentum direction, ATR compression before the move, and a quality gate that filters out tickers with spotty data.

Each factor has a weight. The score is a number. The top score wins. Simple, but it is at least asking the right questions.

- 
- https://www.traderdaddy.pro/screeners/leveraged

## The CSP Screener
Old logic: Find stocks with IV above some threshold. Collect premium. Hope.

New logic: That turned into a five-factor model that actually cares about whether you want to own the stock at the strike. Fair value gap. Short interest (if shorts are piling in, maybe do not sell a put). IV rank versus historical to see if you are actually getting paid well versus norms. Liquidity of the options chain. And a conviction tier that determines whether this is a Prime setup, a Choice, or a Select.

Prime means everything lined up. Choice means most things lined up. Select means it passed but you should probably keep one hand on your wallet.

- 
- https://www.traderdaddy.pro/screeners/csp-wheel

## The Momentum Screener
This one already had a 9-factor scoring model, so it was not broken in the same way. What it was missing was the pullback classifier.

A stock with full EMA stack alignment, strong ADX, good volume, but RSI at 72 and Stochastic at 85 is not the same setup as that same stock with RSI at 48 and Stochastic at 32. The first one is extended. The second one just reset.

I added Bounce 2.0 detection. It now flags when a trend-qualified stock has pulled back to a reasonable re-entry zone rather than being at a breakout point where everyone already got in two days ago.

- 
- https://www.traderdaddy.pro/screeners/momentum

## The LEAPS Screener
Longest time horizon, slowest moving, and somehow the most broken. It was sorting purely by fundamental score and ignoring whether the technical setup was actually set up to move.

Rebuilt with a combined score that weights both the fundamental side (revenue growth, margin, valuation gap to fair value) and the technical side (is it above its 200-day, is the trend intact, is IV low enough to make LEAPS worthwhile). Equal weighting. Conviction tiers.

- 
- https://www.traderdaddy.pro/screeners/leaps

## The part where I used a lot of AI models
I want to be honest about how this rebuild happened. I did not just sit down and rewrite this.

I queried multiple AI models at the same time. I gave each one the same context about what the screener was doing, what the bug was, and what I wanted to fix. Then I looked at what they each came back with.

Some of them agreed. Some of them caught things the others missed. One found a flaw in my weighting math that I would have shipped to production. Another pushed back on the pullback classification logic in a way that made me rethink the Stochastic threshold.

I am not talking about one assistant and one conversation. I am talking about running the same quantitative problem through multiple different models simultaneously, treating their outputs like a code review from a small team.

The thing that surprised me was how often they disagreed. And how those disagreements were the most useful part. When two models independently flag the same issue, you are probably looking at a real bug. When they disagree, you have to think harder about which one is right.

OpenRouter made this workflow frictionless. One API, 355 models as of this morning, switching between GPT-4o, Claude, Gemini, DeepSeek, Llama 4 like changing a setting in a dropdown. I am not going to tell you it is the cheapest option. Some runs hit a few cents. But the ability to run a logic question through multiple reasoning engines in under a minute is not something I am giving up.

- 
- 
[caption] A sleek, dark-mode terminal window with syntax-highlighted code showing an AI prompt. Neon green and blue accents on a dark charcoal background. High contrast, technical, cyberpunk aesthetic.
## What this means for the dossier
Starting today the daily report has a new section at the top of the premium content: Daily Cuts.

Three setups. Every morning. Before the market opens.

https://mphinance.github.io/mphinance/reports/latest.html

One momentum trade. One cash-secured put. One leveraged ETF play.

- 
- Each one gets a tier: Prime, Choice, or Select. Prime means everything in the scoring model lined up. Choice means most things did. Select means it cleared the bar but read the full setup before sizing up.

That is it. Not fifteen tickers. Not a wall of data. Three setups with a reason.

The rest of the report got significantly shorter. The Persistence Tracker now shows you the top Lifers in a single row instead of listing ninety tickers down the page. The individual ticker cards link out to the deep dive pages instead of embedding the entire EMA matrix inline. The Ghost Dev Log moved out of the daily report entirely because frankly you do not need to know that I was debugging the PDF converter at 11pm on a Tuesday.

If you have been subscribing and opening the report on your phone and feeling overwhelmed: I heard you. I just did not act on it until now. Sorry about that.

The dossier is at mphinance.github.io/mphinance/reports/latest.html and it runs every morning at 5AM CST.

Subscribe now

## What the smart money is actually buying right now
One more thing before you go. This part is for paid subscribers.

I run a tool called TickerTrace (I’ve since rolled this into TraderDaddy.Pro) that scrapes the daily holdings of 40+ ETFs, including Avantis AVUV. Avantis does not rebalance quarterly like most funds. They adjust holdings daily. Which means if you track them every single day for seven weeks, you get a real-time map of where a $9B small-cap value fund is putting money.

I ranked every position change from March 7 through April 25 by net portfolio weight added. Not share count, because a million shares of a $3 stock is not the same conviction as a million shares of a $30 stock. Weight tells you how much of the fund they are willing to bet on this name.

Here are the top three.
