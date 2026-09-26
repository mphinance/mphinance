# The Signal Was Right. I Was the One Not Listening.

*Mindset 50% | Trading 30% | Screening 20%*

I spent a week trying to prove my favorite indicator was broken. It wasn't. I was.

I sat down to write you a trade on FIG. My screener had already moved on from it, flashed it as done, run its course, go find the next one. So that is what I was going to tell you. And Sam, the AI I build all of this with, agreed with the screener. Nice and tidy.

Then I looked at my own chart and felt that little drop in my stomach you get when the machine is confidently wrong.

## The chart I actually trade off of

I run an indicator called R-Trend Exhaustion. It measures how stretched a stock is on two clocks at once, a fast one and a slow one. When both bury themselves at the bottom, the stock is coiled. Wound up. Sitting at the bottom of a spring. When the fast clock turns back up while the slow one is still down there, that is the release.

On FIG, it printed. Right at the bottom of the coil, days before the July 2 breakout. My eye saw it. My screener never did.

That is the part that stung. The signal was sitting on my screen the whole time. I just built a scanner that was looking at a different thing.

## What most traders do here

They fire the system.

They have a cold week, the account goes red, and they decide the whole thing has no edge. They go download a new indicator, a new strategy, a new guru, and they run that one until it has a cold week too. Then they fire that one.

A red week is not a reason to change the system. It is a reason to read it.

The people who think their system has no alpha usually had plenty. They just needed one small change. Or worse, they never actually traded with it. They cherry-picked the signals they liked and blamed the system for the ones they skipped. I have watched it in trading, and I have watched it in the twelve years I have spent putting my life back together one boring day at a time.

In recovery nobody tells you to go find a better program when you are struggling. They tell you to work the one you have. Harder. When you are winning is not when the process matters. When you are losing is the only time it counts.

## So I did not fire it. I investigated it.

I did not throw my screener out and bolt the exhaustion indicator on top in a panic. I tested it. Honestly. Across 176 names, every signal, no cherry-picking. I wanted to know exactly how it fits alongside the screener before I size up on it.

The exhaustion indicator is not a replacement for my screener. It is a second set of eyes. My screener is good at spotting the turn. The exhaustion indicator is good at telling me the stock was truly coiled before the turn, not just bouncing around in the mud. Two lenses. Same stock. You want both pointed at it before you size up.

So now I run it. Every morning. A scan that does one job: find the names sitting at the bottom of the coil, and flag the day one of them releases.

I named it what it is. Bottom of the coil. That is the whole game. You are not trying to catch the falling knife. You are trying to catch the moment the spring lets go.

## FIG, for the curious

FIG ran +44% off the $16.60 lows. It is stretched now, RSI 72, and the options market is not shy about it. The biggest gamma magnets sit at $25 and $29. Max pain is way down at $20, which is the market makers quietly telling you they would love to see this thing lower.

Here is the forward map. Price on the left, then where the option pins pull it across the next month. This is the chart I have not seen anyone else build.

![FIG magnet path. Spot at $24, the $25 and $29 gamma pins stacked above, the gamma flip way down at $19.](fig_magnet.png)

I asked Arya, TraderDaddy's AI, to pull the whole read apart for me. It is worth two minutes if you trade FIG: [Arya's full FIG breakdown](https://www.traderdaddy.pro/share/arya/YQPNwP3D?source=arya-chat&ref=MPHINANCE).

Chasing FIG here, at the top of the move, with an overbought reading and max pain pulling down, is exactly the mistake I almost made with the screener. The trade is not up here. The trade is the pullback, back toward the coil, where the spring re-loads.

That level, and the actual order I am placing on it, is below.

---

**Paid subscribers get the working half.** The three names sitting in the coil right now. The SLB level where three completely separate models all point at the same price, with the chart. And both trade rules, FIG and SLB, the real ones, that fire real orders in my real account. One share each, because I am honest about how little dry powder I have in there right now. Skin in the game is skin in the game even when the skin is small.

Half of every dollar this newsletter earns goes straight into the exact names I write about. You are not funding a guy with a course. You are funding the account these trades run in.

---

## The coil list, right now

Almost nothing is coiled this week. That is not a bug, that is the scan doing its job and refusing to make something up. Three names are actually wound up at the bottom:

**IREN** at $33.62. Fast and slow both buried. Freshest coil on the board.

**RGTI** at $14.11. Same story, deep on both clocks, no release yet.

**SMCI** at $24.18. In the coil, a touch shallower on the slow leg, but there.

These are stalk-list, not buy-now. The buy is the morning the fast clock turns up while the slow one is still down. That is the alert I am watching for. When one of them releases, you will hear about it.

## SLB, where everything agrees

This is the one I actually like. SLB triggered out of its coil already and pulled back. Here is why $45 matters so much.

The exhaustion scan says the coil re-loads near $45. The 200-day moving average sits at $45.63. And the forward gamma structure has a magnet meeting the gamma flip line at exactly $45 into the August 7 expiry, which is the one soft spot in an otherwise bullish month for it.

Three unrelated models. One number. That is what a real level looks like. Not a line I drew because it felt right. A price where the tape, the trend, and the options dealers all have business at the same time.

![SLB magnet path. The Aug 7 node drops to $45 and sits in negative gamma, right on the gamma-flip line. That is the soft spot.](slb_magnet.png)

Look at the August 7 node. The magnet drops to $45, turns red, and lands right on the gamma-flip line. That red dot on the orange line is the whole trade. If SLB dips into that window, the fast clock re-buries, the 200-day holds, and the flip is right there, that is the re-entry. Not chasing $47 today.

## The two trade rules

Machine-readable. These fire real orders in my IBKR account the moment I publish. One share each. Real money, real skin, honestly sized.

FIG rests down at the pullback, into the coil, where the spring re-loads:

```
trade rule for this post (LONG only)
Symbol:  FIG
Action:  BUY
Broker:  IBKR
Size:    1 share
Entry:   22.50 limit, GTC   (pullback into the coil, above max pain $20)
Stop:    19.40              (below the coil base, informational for now)
Targets: 25.00  (gamma magnet), then 29.00 (gamma magnet)
```

SLB rests at the $45 confluence, where all three models agree:

```
trade rule for this post (LONG only)
Symbol:  SLB
Action:  BUY
Broker:  IBKR
Size:    1 share
Entry:   45.50 limit, GTC   (200-day + coil re-load + Aug 7 gamma flip)
Stop:    43.50              (below the confluence, informational for now)
Targets: 48.00 (near-term pin), then 52.50 (Aug 21 monthly magnet)
```

I am not buying either top. Both orders rest below, where the spring re-loads. If they never come back, I never get filled, and that is fine. The whole point is to trade with the system instead of chasing away from it.

## The lesson, one more time

Your system is probably not broken. You are probably just cold, or skipping the signals you do not like, or one small honest change away from the thing working. Do not fire it on a red week. Read it. Investigate it. Trade with it.

One boring, honest day at a time. Same as everything else worth keeping.

~ Michael
