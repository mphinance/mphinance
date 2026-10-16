# Underwater After This Week? A Put Will Not Get You Back to Even

*Trading 60% | Options 40%*

<!-- hero: python3 scripts/generate_hero.py --pose stressed_ego --chalk "Recovery price: $63.80 (the put made it worse)" --out docs/articles/underwater-puts-position-doctor/hero.png -->
![A put is a floor. Your basis is the ceiling you need to get back through.](hero.png)

[GAP: The position. The name you are holding red after this week, what you paid, what it closed at Friday, and the dollar hole. One paragraph, the way you'd say it at the bar. If nothing else is red, Crocs still is.]

Character defect admission time. The first thing I wanted to do Thursday night was buy a put on it. Not because I had a plan. Because I felt sick looking at it and a put is the thing you buy when you feel sick. I opened the chain, found a strike, and then did the one thing I'm about to spend this whole post telling you to do: I checked it against what I paid. The put would have raised the price I need to get back to even. I would have paid money to make my own hole deeper.

So this post is the math I ran instead, and the tool I built so you can run it in thirty seconds instead of thirty minutes.

## What this week did to you

If you own tech, you had a bad week. If you own anything else, you probably did not notice.

The S&P finished the week down about **1.1%**. Under that, **XLK fell 7.7%**, the semis ETF **SMH fell 10.5%**, cybersecurity fell 10%, software fell 7%. Staples, energy, and healthcare all went *up* 3 to 5 percent. Half the index is still above its 200-day. Equal-weight beat cap-weight. This was a tech beating, not a market crash, and the people who are underwater this week are underwater in the exact sector where the fear just got priced.

That last part is the whole reason to read the rest. The VIX went from about 16 to **20** this week, up 21%, and the semis names moved a lot more than that. When implied volatility jumps, two things happen at once: the put you want to buy gets expensive, and the call you could sell gets rich. The market just priced your insurance at panic rates, and it priced the premium you could collect at the same panic rates. One of those you pay. One of those you collect. Buying protection after a 10% drop in a name that just doubled its IV is buying fire insurance while the house is on fire, from a guy who can see the smoke.

That does not mean the put is always wrong. It means the question is not "what is the cheapest protection." The question is "what gets me back to even, and what does it cost me in upside." Those have different answers, and the second one depends on a number almost no chain screen shows you: your cost basis.

## Three ideas, then the tool

### A put is a floor

A put gives you the right, not the obligation, to sell 100 shares at a fixed price (the strike) until a fixed date. You pay a premium up front.

Own 100 shares and buy one put and you have built a floor. Below the strike, every dollar the stock loses is a dollar the put gains. Above the strike, the put does nothing and expires worth zero. The premium is gone either way.

Three things follow, and all three matter later:

1. **The floor is at the strike. Your entry has nothing to do with it.** A $50 put on shares you bought at $62 protects you below $50. It does nothing about the $12 between $62 and $50. That gap is already yours.
2. **Protection costs money every day.** The premium decays with time. A put you buy and never need is a pure expense. Fine for insuring a gain. A bad trade when there is no gain to insure.
3. **A put only caps what you can lose from here.** It does nothing to the price the stock has to reach for you to be whole, and it raises that price by the premium, because now you have to earn that back too.

### Delta, in one paragraph

Delta is how much an option's price moves when the stock moves one dollar. A put with a delta of negative 0.30 gains about 30 cents when the stock drops a dollar and loses about 30 cents when it rises a dollar. Calls have positive delta, puts negative, and 100 shares of stock are exactly +100.

Two jobs for it. **As a rough probability:** a 30-delta put is roughly a 30% bet the stock finishes below that strike at expiration. Not exact, close enough to size your thinking. A 50-delta put is at the money. A 10-delta put is a lottery ticket against a crash. **As a measure of how much of the move you still own:** add up every delta in the position. 100 shares plus one 30-delta put is about +70, so you still participate in 70% of every move, up or down. Sell a 30-delta call against the same shares and you are at +70 from the other side. Do both, a collar, and you are around +40.

The trap: people hear "30-delta put" and think "I'm 30% protected." You are not. Delta is how much the put moves today, for a small move. Protection is what the put is worth at expiration, at the price you are scared of. Different questions. The Doctor answers the second one with real payoff math and shows you the net delta separately so you can see both.

### Your basis changes the answer

Here is the whole post in one example.

You bought 100 shares at **$62**. The stock is at **$53**. You are down **$900**.

The advice is "buy a put." The chain shows a 30-delta put at $49 for $1.80. You buy it.

What did you do? You paid **$180** so that the worst case is now a $13 loss per share, $62 down to the $49 floor, plus the $1.80 you just spent. Call it **$14.80 a share, $1,480**, as the most you can lose. That is real, and if the stock goes to $30 you will be glad. But look at the other side. If the stock goes nowhere, you lose the $180. If the stock claws all the way back to $62, you are even on the shares and still out the $180, so the price where the whole position is back to zero just moved from $62 to **$63.80**.

`(62.00 + 1.80) = $63.80 recovery, versus $62.00 doing nothing`

A put does not lock in your loss. You still own the shares and they can still recover. What a put does is cap the loss and raise the recovery price. When you are down, that is the opposite of what you need. You do not have a gain to protect. You have a hole to climb out of, and you just made the hole $1.80 deeper.

Now flip it. Same 100 shares, bought at **$40**, stock at $53. You are up $1,300. That same $49 put now protects a real gain: the floor is $9 above your basis. Paying $180 to lock in at least `(49 - 40) x 100 - 180 = $720` of your $1,300 profit is a perfectly sane insurance decision.

Same stock, same put, same price, and the verdict flipped. The only thing that changed was what you paid.

## When buying a put is actually right

Four situations.

**You have a gain to defend.** Basis below the current price, you want to keep most of the upside and cap the downside through a window. That is what the Hedge Shopper in Ticker Lab is for, and I'll get to it.

**There is a dated risk inside the window.** Earnings, a lockup expiry, a court date, a macro print. You are not hedging forever, you are hedging a day. Short-dated protection is cheap relative to standing insurance. If you are up on the shares it is often worth it. If you are down, keep reading.

**You cannot sell the shares.** Restricted stock. A long-term holding period that clears in three weeks. A concentrated position that would move the stock if you dumped it. For you, a put under basis is the right tool even though it raises the recovery price, because the alternative is no floor at all. The next few sections are not written for you.

**You are not hedging shares. You are making a bet.** Buying a put with no stock is a directional trade that the thing goes down. Different animal. The Strategist in Ticker Lab is where that lives, with long puts and bear put spreads ranked by probability of profit.

The case where a put is wrong is the case I was in Thursday night: underwater, no dated event, no reason I cannot sell, and I just felt bad about it. A put charges you for that feeling and leaves it exactly where it was.

## What the Position Doctor does

The Doctor asks for two numbers: how many shares you hold, and what you paid per share. Then it reads the live option chain and does three things.

**It diagnoses the position.** More than 2% under your basis is *underwater*. Within 2% either side is *near basis*. More than 2% above is *in profit*. That bucket decides what you need, and the Doctor reorders its whole answer around it. Underwater means repair first, then income, then protection-plus-income, then protection last. Near basis means income first, because there is nothing to defend and nothing to repair. In profit means protection first and repair last.

**It prices five structures off the real chain.** Each on its own horizon, because they do different jobs. Income structures want time decay working for you, so they go short, about 35 days. A repair needs the stock to have room to travel, so it goes long, about 75 days. A protective put is standing insurance, so it sits in the middle, about 60 days.

**It measures every candidate against your basis.** Not against the current price. Against what you paid.

One thing it does not do, and this week it matters: it does not know about earnings. If a report lands inside a structure's window, implied volatility gets crushed after it, which hurts the long legs and helps the short ones. We are in earnings season right now. Check the date before you pick a horizon.

## The five structures, plus the one I would actually do

Every structure gives something up. The caveat line on each card says what. Read it before the rationale.

### Protective put. A floor.

Buy one put per 100 shares, around 30 delta.

**What it does:** Below the strike, you stop losing. Above it, you keep everything.

**What it costs:** The premium, every time, whether you need it or not.

**When it is right:** You are in profit and the strike sits above your basis.

**When it is wrong:** You are underwater. The Doctor's caveat on this card says it in so many words: the floor is already under your basis, this pays premium to cap a loss you are partly sitting in, and it does not help you get back to even.

### Covered call. Income.

Sell one call per 100 shares, around 30 delta, above the current price.

**What it does:** You collect the premium now, and that cash lowers your effective basis by the same amount. If the stock finishes below the strike you keep the shares and the premium and do it again.

**What it costs:** Your upside stops at the strike. If the stock rips past it, your shares get called away at the strike and you miss the rest.

**The trap when you are underwater:** The 30-delta strike might be *below* your basis. If it is, the Doctor flags it in red: the cap is below your basis, and if it rips you get assigned into a realized loss. You collected **$150** of premium and then sold your $62 shares at $57. That is a bad trade dressed up as income.

[GAP: Confession tail. You have done this one. Which name, which strike, what the assignment cost. One or two sentences, then move on. Don't moralize it.]

### Covered call at basis. Income without the trap.

This one only shows up when you are underwater, and it exists because of the trap above.

Instead of the 30-delta call, you sell the first strike at or above your cost basis. The premium is thinner because the strike is further away, but assignment can never book a loss. If you get called away, it is at a price at or above what you paid.

**What it does:** Collects some premium, lowers your recovery price by that amount, and if the stock rallies all the way back you exit at break-even or better.

**What it costs:** Less premium than the nearer call, and the downside is still completely open. This is a cap, not a floor.

In the example, say the $62 call 35 days out pays **$0.60**. Your recovery price drops from $62 to **$61.40**. Not a lot. But it is in the right direction, which is more than the put can say, and in a week like this one where IV is elevated, that $0.60 is more like a dollar.

`62.00 - 0.60 = $61.40 recovery. The put made it $63.80.`

The Doctor says which way the comparison cuts in each case. When you are only slightly down, the at-basis strike is sometimes *closer* to the money than the 30-delta one, and then it is the richer call with the tighter cap. The card tells you which.

### Collar. A floor paid for by a cap.

Buy the protective put and sell the covered call at the same time. The call pays for most or all of the put.

**What it does:** Boxes the position between the two strikes, often for close to zero net cost.

**What it costs:** Everything above the call strike. And if both strikes sit under your basis, which is common when you are well underwater, the Doctor says so: this locks the position into a loss range and takes recovery off the table. A zero-cost collar on an underwater position is a zero-cost way to guarantee you lose. That is the one structure here where "locked in" is the right phrase, because the short call is the part that locks.

### Repair ratio, the 1 by 2. Recover twice as fast.

This is the one most of my readers have never seen priced, and it is the one built for the underwater case.

Per 100 shares: buy one call at the money, sell two calls at a higher strike. The two short calls pay for the one long call, so the structure is usually a small credit or close to free. One short call is covered by the long call, the other by your shares, so there is no naked upside.

**What it does:** Between the two strikes you own 200 shares' worth of upside instead of 100. The stock only has to climb half as far to get you back to even.

**What it costs:** Your upside stops dead at the upper strike. Above it the shares get called away and the extra call cancels the extra gain. And the downside is completely unchanged. This is a recovery accelerator, not a hedge.

**Worked example, with the arithmetic typed out because I got it wrong the first time:** 100 shares at $62, stock at $53. Buy one $53 call, sell two $58 calls, roughly even money. Between $53 and $58 you make $2 for every $1 the stock moves.

```
At $58 on expiration:
  Long $53 call        $5 x 100  =  $500
  Two short $58 calls             =    $0
  Shares, $53 to $58   $5 x 100  =  $500
  Total gain                        $1,000
  The hole                           -$900
  Net                                 +$100
```

You are out at a small profit at **$58** instead of needing **$62**. Not $1,500 like I had in the first draft. $1,000. The conclusion survives, the number did not, and that is why the arithmetic goes in the post.

The Doctor picks the highest upper strike whose two short calls still pay for the long call. Higher cap, more room to run. The trade-off is that a lower upper strike collects more credit, and credit lowers the recovery price. The card shows both so you can pick which you want.

### The sixth one. Sell the damn shares.

The Doctor does not price this one, because it is not an options structure around shares you keep. I am putting it here because it is what I would do with most of the names that got hit this week, and leaving it out of a post about getting back to even would be dishonest.

Sell the shares. Book the $900 loss. Then sell a cash-secured put at the strike you wish you had bought at in the first place, 35 days out, and collect premium while you wait.

In the example: sell at $53, sell the $50 put for, say, **$1.20**. If it expires worthless you made $120 on $5,000 of collateral in a month and you still do not own a stock that was going down. If you get assigned, your new basis is **$48.80**, and the climb back to your old $62 is now a climb from $48.80, with premium paying you every month along the way. The hole is the same $900. What changed is that your capital is earning rent at $50 instead of praying at $62.

`50.00 - 1.20 = $48.80 new basis if assigned, versus $62.00 holding`

This also harvests the loss for taxes, which none of the five structures do. One caution, and it is a real one: if you buy the shares back inside 30 days, or get assigned inside 30 days, the loss does not disappear, it gets deferred into the new basis. And buying a call on the same name inside that window does the same thing. So the sell-and-wheel and the repair ratio are mutually exclusive for a month. I did corporate accounting for a living and I still check this every time.

That is the premium seller's answer. Become the casino. Get rich slowly. The other five are what you do when, for whatever reason, you are not willing to let the shares go yet.

## Reading the Doctor's answer

The page opens with a verdict in plain English. Read it. It names your P&L, how far the stock has to climb, and what that means for what you should be shopping for.

Below that, every card carries the same numbers. Here is which one to look at first.

**Recovery** is the headline. The lowest share price at or above the current price where the whole position, your shares at your basis plus the new legs, is back to zero at expiration. Doing nothing recovers exactly at your basis. The card shows the difference in words. "$2.40 easier" means the structure lowered your recovery price by $2.40. "$1.80 harder" means it raised it, which every protective put does. "Cannot recover" means the structure's ceiling sits under water: the position can never get whole at expiration with that structure on. The Doctor returns an honest dash instead of inventing a number.

**Floor** is the worst price per share you can be forced to exit at, or a dash if the downside is still open. Only structures with a long put have one.

**Cap** is where your upside stops. Only structures with a short call have one. If the cap sits below your basis, the card says so in red, because assignment there is a realized loss.

**Net delta** is your remaining exposure in share-equivalents. 100 shares is +100. A collar might leave you at +40. The repair ratio can leave you at +100 or more between the strikes and far less above them. Smaller means less of the next move, in either direction, is yours.

**The scenario grid** shows the whole position's P&L at four prices: a down move, flat, your basis, and an up move. Every card and the do-nothing baseline quote the same four prices, so they compare directly. This is where you see the trade-off in dollars instead of adjectives.

**Cost** is the net debit you pay or credit you collect to put it on, across all contracts.

**The caveat** is the thing that bites. It is on every card because every structure gives something up.

[GAP: The live number. Your actual position through the Doctor. Recovery price for do-nothing, for the at-basis call, for the repair. Three numbers and which one you picked. This is the paragraph people screenshot.]

## The Hedge Shopper, for when you are up

The Hedge Shopper sits next to the Doctor in the same section of Ticker Lab and answers the other question: what is the cheapest way to protect a gain?

It takes your share count, optionally your basis and a daily average true range, and shops four structures: the protective put, the collar, the put-spread collar (a cheaper collar where the floor stops working below a lower put strike), and the bear put spread (a defined-cost tactical hedge). It sizes the move it is protecting against off the chain's expected move, floored by a volatility-scaled estimate so a quiet name is not under-hedged. Then it drops any structure that costs more than the loss it removes and ranks the survivors by cost per dollar protected. Credits and zero-cost structures float to the top.

In profit, start there. Underwater, start with the Doctor. Not sure which you are? The Doctor tells you in the first line.

## What the Doctor will not do

- **Work under 100 shares.** Options trade in 100-share lots. A 60-share position cannot be covered or collared, and the Doctor says that instead of inventing a partial contract.
- **Guess your basis.** Every number on the page is measured against it. If you do not know it, look it up in your broker or your journal first. The Trade Journal's positions page has a Diagnose link on every eligible share lot that carries the count and average cost across for you.
- **Tell you the stock is going up.** It prices what each structure does *if* the stock reaches each scenario price. Whether it gets there is the market's business.
- **Offer the covered call at basis when you are in profit.** Above basis that structure degenerates into selling a deep in-the-money call, which is just selling your shares with extra steps.
- **Rank by a single made-up score.** Every card carries its own recovery, floor, cap, delta, and four-scenario P&L. The order comes from the diagnosis. The trade-offs stay visible.
- **Price the sixth structure.** Selling the shares is a decision you make, not a number the chain hands you.

## Where to find it

Open any ticker in Ticker Lab and scroll to the "More on SYM" section. Position Doctor and Hedge Shopper are the last two cards. From the Trade Journal's Positions page, every long share lot of 100 or more has a Diagnose link that opens the Doctor with your numbers already in. You can also ask Arya: give her the ticker, your share count, and your basis, and ask what gets you back to even.

Both tools are Premium. If this week put you underwater and you want the numbers instead of the feeling, that is what the subscription is for.

~ Michael
