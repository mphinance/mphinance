# Amazon and I Own Qualcomm From the Same Price (Seven Cents Apart)

*Trading 60% | Options 30% | Mindset 10%*

![The titan and the guy with 70 shares, same ledge](hero_ledge.png)

I own 70 shares of Qualcomm. Average cost $161.33. Friday it dropped 5.82% and my broker app told me I'd lost $749.56 in one session, the kind of notification that makes you put the damn phone face down on the counter.

![70 shares, $161.33, and the red Friday](mph_position.png)

Then I reread the Amazon deal from September 8, slower. Amazon got warrants on 25 million Qualcomm shares. The strike is $161.26.

Seven cents. Amazon and I are long the same stock from the same price. One of us negotiated it (well, its lawyers did), and one of us bought it in lots of ten coming off a $142 low because he liked the chart. Guess which?

I didn't know about the warrant when I bought. I'm not going to pretend I saw Amazon coming, and I only did about a weekend of DD on the deal itself, so please do your own.


## What paid gets this time

Normally the paid section is a write-up. This time it's the instrument. The TraderMatrix Apex levels for QCOM export as a TradingView Pine script, and paid subscribers get the actual file below the cut. Paste it into Pine Editor, hit Add to Chart, and the six magnets, the gamma flip, the entry band, the stop and the expected-move envelope draw on your own chart. Not a screenshot of mine.

It's a snapshot, not a live feed: open interest moves and the levels move with it. The file was generated this morning, so it's a map dated today.

## The tape

Friday QCOM opened at $191.34, tagged $192.12, and closed $177.72. That's a 9.09% range on 54.4M shares, three times normal volume, the biggest bar of the whole six-week run. Open at the high, close near the low. A candle like that on that much volume is the market telling you where the sellers live.

Deal day did the same thing. September 8 it gapped from $168.74 to $180.40 on the Amazon news, printed $183.49, and closed at $174.09. Gave back more than half the gap before the bell. Twice the market has been handed the AI data-center story, and twice it sold into it.

Zoom out and this is attempt two at a data-center re-rate. QCOM ran from $120.88 in April to $257.56 by the end of May, then gave the entire thing back to $142 by August. Then it ran 35.2% in six weeks into Friday's high.

![The rejection, the shelf, the flip, the August low](QCOM_kline.png)

RSI rolled from 68.7 to 54.4. ADX is 22.9, barely a trend, just chop. It knifed through the 8 EMA and is holding above the 21. The 200-day is at $166.99, and the option chain has one real support strike, $160, right under my basis and Amazon's.

Amazon's strike, my cost, the 200-day and the put wall are stacked inside a $7 window. I don't get to claim I planned that, but I'll pretend anyway.

## The deal, and the part to be careful with

Amazon: up to $60 billion of Qualcomm AI data-center silicon and systems, 2026 through 2036. Custom inference chips, AI200 this year and AI250 next. Revenue starts in December, with Qualcomm's own targets at about $5B in FY27 and $15B in FY29.

![$60B is the ceiling on the scaffold, not the building](hero_ceiling.png)

The $60 billion is not an order. It's a ceiling on the qualifying payments that count toward Amazon's warrants vesting. There's no backlog, and the deal supplements Trainium and Inferentia rather than replacing them.

Now the warrants. 25 million shares at $161.26, around $4 billion of stock, on 1.068 billion outstanding. That's 2.34% dilution. Qualcomm is paying a customer in equity to be a customer.

FY25 revenue was $44.3B at a 54.2% gross margin. Data-center silicon runs in the 30s to low 40s. Blend $15B of 35%-margin revenue onto that base:

(44.3 x 0.542 + 15 x 0.35) / (44.3 + 15) = 49.3%

Revenue up 34%, gross profit up 22%, five points of margin gone. That's what the escape from smartphones costs. Congratulations, Qualcomm: you traded a great-margin business for a slightly-worse one. Growth business, technically.

## The bear case, stated fairly

From the FY25 10-K: Apple, Samsung and Xiaomi each exceeded 10% of revenue. China including Hong Kong was 46%.

All three are building their own silicon. Apple's C2 modem is why Friday happened at all: Qualcomm said its share of upcoming iPhones lands well below the old ~20% assumption and guided Apple product revenue down about 50% sequentially into the December quarter. Samsung has Exynos. Xiaomi has XRing.

Nvidia is now getting a version of the same treatment Qualcomm is getting from Apple: fund the customer, watch the customer build its own chips. Qualcomm knows how that movie ends.

![17 public counterparties](dealmap.png)

## Two people who wrote about this before me

[LongYield's piece](https://longyield.substack.com/p/amazon-just-gave-qualcomm-a-60-billion) is the one to read on the deal. He nailed the line that matters: "The $60 billion is not an order. It is a ceiling on the payments that can count toward a warrant vesting through 2036." And he says out loud that Qualcomm is trading licensing revenue that's nearly pure profit for data-center revenue in the thirties. The equity is the price of admission.

[The Options Income wheel newsletter](https://wheelstrategy.substack.com/p/what-to-trade-this-week-15-wheel-b54) put QCOM in this week's free five: sell the $160 put, October 16 expiry, "about a 10% cushion." I checked it against the chain and it holds up. That put is $2.30 at the mid, 0.17 delta, a couple bucks under the options market's own one-sigma floor and right on a put wall with more than 4,000 contracts of open interest. Real strike, not a hope.

Calling a 0.17-delta put a "cushion" undersells it. That's roughly a one-in-six event, a moat until it isn't. Their framing also assumes you own none of it. I own 70, which changes the answer completely.

---

**PAYWALL GOES HERE. Set it in the Substack editor, then delete this line.**

## The instrument

![The Apex level ladder. This is what the Pine script draws.](crop_apex_ladder.png)

The Pine file is attached: QCOM-2026-09-20-tradingview.pine. What's in it: magnets at 180, 200, 190, 185, 175, 170 in order of strength, the gamma flip, entry band $175.00 to $177.72, stop $167.39, targets at $180 and $200, and the expected-move envelope. Snapshot as of this morning.

On the gamma flip: three models gave me three numbers today, because they look at different windows. Three quant models, three different answers, all delivered with total confidence. The flip sits somewhere in the low $150s to low $160s depending on how far out you look. Don't let anyone sell you a decimal on it, me included.

## Why $190

I said $190 looks like the target because a lot of selling happened there. That was a chart read. Then I checked whether the numbers agree.

TD Pro's card gives you two targets, T1 at $180 and T2 at $200. Using their own convention, entry at $176.36 (mid of the buy zone), stop at $167.39, risk $8.97 a share, I reproduced both cards to the decimal. T1 is 0.41x. T2 is 2.64x. The model is sound. It just never scored the level in between.

![R:R by target. Only one clears 1.5:1 inside the expected move.](targets.png)

$190 is 1.52x and sits at 0.79x the expected move. It's the only target over 1.5:1 that stays inside what the options market thinks is reachable by October 16. T1 pays you forty cents per dollar risked. T2 needs a move 1.44x the expected move, and their own card flags it with a warning triangle.

And "a lot of selling happened there" turns out to be literally true. Friday's candle got rejected two dollars above it, and there are 11K contracts of call open interest sitting at $190. Two independent things point at the same price.

![The $190 line with 11K OI, exactly where Friday's candle turned](crop_apex_chart.png)

That density makes it a take-profit level, not a breakout level.

## How to size it (the part that isn't about Qualcomm)

Van Tharp's position sizing is the most useful thing I've read on trading and the least used. Use a $100,000 account for the arithmetic and divide down if yours is smaller. Mine is.

Step one: R is what you lose if you're wrong. Entry $176.36, stop $167.39, so R = $8.97 per share, which happens to be exactly one ATR. That's on purpose. The stop sits one average day's range under the entry band.
>
Step two: R is also what picks your share count, not your gut. Shares = (account x risk %) / R. At 1% risk that's ($100,000 x 0.01) / $8.97 = 111 shares, a $19,576 position.

Risking one percent means buying almost twenty percent of the account in stock. Most people hear "1% risk" and size a tenth of that, or buy a round 100 shares with no idea what they just risked. The stop sets the size. Nothing else does.

![Tharp sizing on $100k. The break-even win rate column is the payoff.](tharp.png)

Step three is where it clicks: score each target in R, then ask what win rate it needs just to break even. $180 is 0.41R, which means you have to be right 71.1% of the time, forever, just to break even. $190 is 1.52R, and the break-even win rate drops to 39.7%. $200 is 2.64R and only needs 27.5%, but you have to actually get there.
>
Step four is the two numbers you know before you click: at 111 shares, +$1,514 if $190 hits, -$996 if the stop does.

## The 70-share problem

Now my actual position. I can't write a covered call on 70 shares. Contracts are 100. So the wheel, the thing my whole account is built around, is closed to me on this name. This is a teaching point about how a position gets stuck, not a trade.

![Three doors. Two of them lead back to the same room.](wheelmath.png)

Door A is going to 100 shares. Buy 30 at Friday's close, $5,331.60. New basis $166.25. Sell the October $190 call for $477.50 and the break-even drops to $161.47. If it's called away, +$2,852.80, or 17.2%, in 26 days, with about a one-in-three chance of that happening.

I'm not doing it, and I'm putting that in print so I can't quietly change my mind later. Adding 30 shares to a name that just got rejected on 3x volume is the exact move I'd tell someone else not to make. Pretty math is not a reason.

Door B is the wheel newsletter's trade: sell the $160 put, collect $230.50 against $16,000 of collateral, 1.44% for the month. If assigned you own 170 shares at $159.19, and the original 70 still don't fit a contract.

Door C is sit. 70 shares, up 10%, zero income, waiting.

I'm on C. Not because it's smart, because A means adding into weakness and B means owning 170 shares of a stock I currently have 70 of by accident. I buy in lots of ten because it feels like less commitment than buying in lots of a hundred. That's not a strategy, it's a flinch, and I made it back in August. Buy in lots of 100 or don't call it wheeling.

## Where that leaves me

Amazon's strike is $161.26 and it vests over a decade. Mine is $161.33 and I don't have a vesting schedule. Same ledge. Amazon's has a railing.

If $190 comes back around I'll be a seller into it, not a buyer through it. And if I'm wrong about all of this I'll write that too, because that's the arrangement.

Subscribe and the next one finds you. Half of every paid sub goes straight into the brokerage account you just read about, so you're funding the machine.

~ Michael
