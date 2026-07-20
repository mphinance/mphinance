# I Put My Favorite Indicator on Trial. It Lost.

*Screening 50% | Mindset 30% | Trading 20%*

![The backtest that talked me out of my own idea](hero.png)

I was about to sell you a FIG trade.

Then I looked closer and realized the trade was already nearly three weeks old. My screener flagged the bottom on June 29, my robot narrated it, and I was writing about the breakout like it was fresh news. I almost charged you for a bus that already left the station.

So I did the thing I tell everyone to do and almost never enjoy doing. I stopped, and I tested my own work against itself.

## The push that started it

Here's how the hole got found. My screener uses a Stochastic cross to call a turn. Fine. But that is not what my eye actually uses when I look at a chart. My eye uses the %R Trend Exhaustion indicator, the one that lights up when a stock is buried at the bottom of a coil on two timeframes at once. It's the tool I trust. And it wasn't in the screener at all.

That's a strange thing to admit out loud. The indicator I trust most was not in the machine I built to find trades. So the obvious move was to swap it in and watch the win rate climb.

It didn't climb.

## Five robots, five tweaks, 176 stocks

Instead of guessing, I sent five agents out at once. Each one ran a different version of the turn-detector across 176 names with a year of price history, scored the same way: buy the signal, measure where the stock was five and ten days later. No cherry-picking. Same math for all five.

![Five variants, one honest scoreboard](backtest.png)

The faithful version of my favorite indicator? Fifty percent win rate. A coin flip with a negative median. The noisy version was worse. And the plain Stochastic engine I already had, the one I was about to replace, quietly did the best job of the bunch.

On FIG specifically it was almost funny. My screener caught the bottom on June 29 at $19. My beloved indicator caught it on July 2 at $21, three days late and two dollars higher, after the run already started. The tool I trusted more was the tool that showed up late.

## The part I didn't want to write

A screener does not pick trades. It picks arguments.

The whipsaw I was worried about, the one I assumed my fancy indicator would fix? My old boring one already handled it. There's a cap in there I built months ago and forgot about, and it quietly swallowed the exact false signal I was scared of. I was about to bolt a new engine onto a car that was already steering fine.

The one real improvement out of all five tests was small and unsexy: wait for the stock to actually clear the top of its base before you buy. That single filter took a coin flip and turned it into a real edge. Not the indicator. The patience.

So the swap I was sure about got killed by my own backtest. And that is the most valuable thing that happened all week.

Most of the edge in this game is not the indicator you found. It's being willing to find out the indicator you love does not beat what you already had.

## Where my indicator actually belongs

My %R tool didn't lose because it's bad. It lost because I was asking it to do the wrong job. It doesn't call the bottom early. It confirms the coil. It's a different lens, not a replacement, and once I stopped trying to make it the whole engine it got a lot more useful.

Which is exactly why I built a daily scanner around it. Not to pick the trade. To tell me which stocks are sitting at the bottom of the coil right now, quietly, before the cross ever fires. That's the list I want before the cross, not after.

Almost nothing is coiled right now. That's not a bug. In a market like this, an empty list is the honest answer, and I would rather hand you an empty list than a bus that already left.

But there are a few. And one of them lined up three different tools on the exact same number, which is the kind of thing I stop scrolling for.

---

## The part where I put my money where my mouth is

Everything below is for paid subscribers, and I want to be straight about why. Half of what this newsletter earns goes straight into the brokerage account these exact names trade in. You are not buying a tip. You are watching me risk my own money on the same list, in real time.

What's behind the wall this week:

The three names actually sitting at the bottom of the coil right now, deep on both timeframes, no trigger yet. The stalk list.

The one name where my coil scanner, the gamma pin structure, and the 200-day line all mark the same re-load price for the same week. Not a signal firing today. A level I'm waiting for.

And the machine-readable trade block for the setup I like best, the one that fires a real limit order into my own account the moment I publish it.

<!-- PAYWALL -->

### The stalk list: three coils, no trigger yet

These three are buried deep on both the fast and slow timeframe, and neither has fired the trigger yet. That's the sweet spot. You're not chasing a move, you're waiting at the door for one.

- **IREN**, around $33.62. The deepest, cleanest coil on the whole board. Both legs pinned near the floor, no reversal candle yet.
- **RGTI**, around $14.11. Same shape, same depth. Buried and quiet.
- **SMCI**, around $24.18. In the box, a touch shallower on the slow leg, but in it.

The trigger is simple: the fast leg climbs back up and out of the floor. That's your signal the coil is uncoiling. Until then, these are watch-and-wait, not buy-now. Set the alert, don't force the entry.

### The confluence trade: SLB and the number that keeps showing up

SLB is not coiled anymore. It already ran off its early-July bottom near $45 up to $48, and it's sitting around $47 now, just under its 21-day line. Chasing it here is exactly the mistake I almost made with FIG.

The re-load is what's interesting. Three separate tools point at the same price:

- My coil scanner wants a pullback into the low $45s for the fast leg to re-bury.
- The 200-day moving average sits at $45.63.
- And the gamma pin structure for the August 7 expiry puts the magnet at $45, right where the gamma flip level sits. When the magnet and the flip land on the same price, that price becomes the fulcrum. Above it, dealers dampen the move. Below it, they feed it.

Three tools that don't talk to each other. One number. $45.

![SLB magnet path — where the pins pull price into August](slb_magnet.png)

I'm not chasing $47. If SLB comes back to the $45 to $45.63 zone with the fast leg re-burying, that's the entry, and it lines up with a level the options market is already defending.

### Trade rule for this post (LONG only)

This is the actual trigger that will place the actual order the moment this posts.

```
Symbol: SLB
Action: BUY
Broker: IBKR
Size: 10% NetLiq
Entry: 45.60 LMT GTC
Stop: 43.90 (informational)
Targets: 48.00 / 50.90 / 52.50
```

Entry is a resting limit below the market. If it doesn't come to my price, I don't own it. No chase. The targets map to the near-term gamma pin at $48, the 50% retracement at $50.90, and the August 21 monthly gamma magnet at $52.50, which is where the biggest open interest on the board is sitting.

## Why I keep showing you the losses

The most useful thing I did this week was prove myself wrong before it cost me anything. Not because I'm humble. Because in recovery you learn the hard way that the story you tell yourself is the most expensive thing you own, and the only cure is to check it against something outside your own head.

A backtest is just a fourth step for a trade. You write down what you believed, you look at what actually happened, and you sit in the gap. Most people never do it because the gap is uncomfortable. The gap is the whole point.

My favorite indicator lost. I'm keeping the loss, and I'm keeping the tool, in the seat where it actually belongs.

The confession before the tip. That's the whole newsletter. Half of every paid subscription goes straight back into the names on this list. You are literally funding the machine that funds the trades.

~ Michael
