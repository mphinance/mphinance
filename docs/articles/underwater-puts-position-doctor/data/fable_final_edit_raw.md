# Underwater After This Week? A Put Will Not Get You Back to Even

*Trading 60% | Options 40%*

<!-- hero: python3 scripts/generate_hero.py --pose casino_dealer --chalk "Recovery: $63.80. The put made it worse." --out docs/articles/underwater-puts-position-doctor/hero.png -->
![A put is a floor. Your basis is the ceiling you need to get back through.](hero.png)

If tech put you underwater this week, don't buy a put tonight.

The puts that paid this week were bought before the drop, when they were cheap. The put you want to buy tonight is after the drop, with the VIX at 20, on a hole. Same instrument. Opposite trade. The difference is one number you have to check before you click buy, and almost no chain screen shows it to you: what you paid for the shares you're trying to fix.

This post is the math for that, and the tool I built so you can run it in thirty seconds instead of thirty minutes.

> **TLDR: Underwater, a put caps the loss and raises the price you need to get back to even. Sell calls at or above your basis, price a 1x2 repair, or sell the shares and wheel. The Position Doctor runs all of it off the live chain against what you actually paid.**

<!--subscribe-->

## Got your broker wired to an AI? Paste this

If your broker is connected to Claude, ChatGPT, or another agent through MCP, this prompt runs the same diagnosis on your real position. Swap in your ticker and paste it. It only reads. If your agent offers to place a trade, say no.

```
Diagnose my TICKER position. Read only: do not place or stage any order.

1. From my broker: shares held, average cost (say which field you used), current price. Under 100 shares, stop.
2. From the live chain, using mid prices and the broker's own deltas, price per 100 shares:
   - protective put near -0.30 delta, ~60 days
   - covered call near 0.30 delta, ~35 days
   - covered call at the first strike at or above my cost, ~35 days
   - collar (that put plus that call), same expiration
   - 1x2 repair: buy 1 call at the money, sell 2 at the highest strike where the credit still covers it, 60 to 75 days
3. For each: net cost, floor, cap, net delta, and the RECOVERY PRICE, the stock price at expiration where the whole position is back to $0. Show the math. If the cap sits below it, write NEVER.
4. Flag any cap below my cost, any earnings date inside an expiration, and any wide bid/ask.
5. Add one more: sell the shares and sell a cash-secured put, with the wash-sale warning.
Give me the numbers and the trade-offs. No recommendation.
```

If it hands you a recovery price without the arithmetic, make it show the arithmetic.

## What this week did to you

If you own tech, you had a bad week. If you own anything else, you probably didn't notice.

The S&P 500 finished the week down about **2%**. Under that, **XLK fell 7.7%**, the semis ETF **SMH fell 10.5%**, cybersecurity fell 10%, software fell 7%. Staples, energy, and healthcare all went *up* 3 to 5 percent. Half the index is still above its 200-day. Equal-weight beat cap-weight. This was a tech beating, and the people who are underwater this week are underwater in the exact sector where the fear just got priced.

![Five days, Friday close to Friday close. Tech got hit, the defensives went up.](week.png)

The VIX closed the week at **20**, and the semis names moved a lot more than that. When implied volatility jumps, the put you want to buy gets expensive and the call you could sell gets rich, at the same time, off the same panic. One of those you pay for. The other pays you. Buying protection after a 10% drop in a name whose IV just jumped is buying fire insurance while the house is on fire, from a guy who can see the smoke.

That doesn't make the put always wrong. It means the cheapest protection is the wrong thing to shop for. What you want to know is what gets you back to even and what it costs you in upside, and that answer depends on your cost basis.

## Three ideas, then the tool

### A put is a floor

A put gives you the right, not the obligation, to sell 100 shares at a fixed price (the strike) until a fixed date. You pay a premium up front.

Own 100 shares and buy one put and you've built a floor. Below the strike, every dollar the stock loses is a dollar the put gains. Above the strike, the put does nothing and expires worth zero. The premium is gone either way.

Three things follow, and all three matter later:

1. **The floor is at the strike. Your entry has nothing to do with it.** A $50 put on shares you bought at $62 protects you below $50. The $12 between $62 and $50 is already yours.
2. **Protection costs money every day.** The premium decays with time. A put you buy and never need is a pure expense. Fine when you're insuring a gain. A bad trade when there's no gain to insure.
3. **A put only caps what you can lose from here.** It doesn't help with the price the stock has to reach for you to be whole. It raises that price by the premium, because now you have to earn that back too.

### Delta, in one paragraph

Delta is how much an option's price moves when the stock moves one dollar. A put with a delta of negative 0.30 gains about 30 cents when the stock drops a dollar and loses about 30 cents when it rises a dollar. Calls have positive delta, puts negative, and 100 shares of stock are exactly +100.

It does two jobs. **As a rough probability:** a 30-delta put is roughly a 30% bet the stock finishes below that strike at expiration. Close enough to size your thinking. A 50-delta put is at the money. A 10-delta put is a lottery ticket against a crash. **As a measure of how much of the move you still own:** add up every delta in the position. 100 shares plus one 30-delta put is about +70, so you still catch 70% of every move, up or down. Sell a 30-delta call against the same shares and you're at +70 from the other side. Do both, a collar, and you're around +40.

The trap: people hear "30-delta put" and think "I'm 30% protected." You're not. Delta is how much the put moves today, for a small move. Protection is what the put is worth at expiration, at the price you're scared of. Those are different questions, and the Doctor answers the second one with real payoff math, then shows net delta separately so you can see both.

### Your basis changes the answer

Here's the whole post in one example.

You bought 100 shares at **$62**. The stock is at **$53**. You're down **$900**.

The advice is "buy a put." The chain shows a 30-delta put at $49 for $1.80. You buy it.

What did you do? You paid **$180** so the worst case is now $13 a share, $62 down to the $49 floor, plus the $1.80 you just spent. Call it **$14.80 a share, $1,480**, as the most you can lose. That's real, and if the stock goes to $30 you'll be glad. Now the other side. If the stock goes nowhere, you're out the $180. If it claws all the way back to $62, you're even on the shares and still out the $180, so the price where the whole position is back to zero just moved from $62 to **$63.80**.

`(62.00 + 1.80) = $63.80 recovery, versus $62.00 doing nothing`

The put didn't lock in your loss. You still own the shares and they can still recover. It capped the loss and raised the recovery price, and when you're down, that's backwards. There's no gain here to protect. There's a hole, and you just made it $1.80 deeper.

Now flip it. Same 100 shares, bought at **$40**, stock at $53. You're up $1,300. That same $49 put now protects a real gain: the floor is $9 above your basis. Paying $180 to lock in at least `(49 - 40) x 100 - 180 = $720` of your $1,300 profit is a perfectly sane insurance decision.

Nothing changed but what you paid, and the verdict flipped.

## When buying a put is actually right

Four situations.

**You have a gain to defend.** Basis below the current price, you want to keep most of the upside and cap the downside through a window. That's what the Hedge Shopper in Ticker Lab is for. More on it below.

**There's a dated risk inside the window.** Earnings, a lockup expiry, a court date, a macro print. You're hedging a day, and short-dated protection is cheap next to standing insurance. Up on the shares, it's often worth it. Down, keep reading.

**You can't sell the shares.** Restricted stock. A long-term holding period that clears in three weeks. A concentrated position that would move the stock if you dumped it. For you, a put under basis is the right tool even though it raises the recovery price, because the alternative is no floor at all. The next few sections aren't written for you.

**You're making a bet, with no shares under it.** A put with no stock is a directional trade that the thing goes down. That lives in the Strategist in Ticker Lab, with long puts and bear put spreads ranked by probability of profit.

The case where a put is wrong is the one my inbox filled up with this week: underwater, no dated event, no reason you can't sell, and you feel sick looking at it. A put charges you for that feeling and leaves it exactly where it was.

## What the Position Doctor does

The Doctor asks for two numbers: how many shares you hold, and what you paid per share. Then it reads the live option chain and does three things.

![Two boxes and a button. Shares held, cost basis, Diagnose.](doctor_form.png)

**It diagnoses the position.** More than 2% under your basis is *underwater*. Within 2% either side is *near basis*. More than 2% above is *in profit*. That bucket decides the order of everything below it. Underwater means repair first, then income, then protection-plus-income, then protection last. Near basis means income first, because there's nothing to defend and nothing to repair. In profit means protection first and repair last.

**It prices five structures off the real chain.** Each on its own horizon, because they do different jobs. Income structures want time decay working for you, so they go short, about 35 days. A repair needs the stock to have room to travel, so it goes long, about 75 days. A protective put is standing insurance, so it sits in the middle, about 60 days.

**It measures every candidate against what you paid.** The current price is only the starting point.

One thing it doesn't do, and this week it matters: it doesn't know about earnings. If a report lands inside a structure's window, implied volatility gets crushed after it, which hurts the long legs and helps the short ones. We're in earnings season. Check the date before you pick a horizon.

## The five structures, plus the one I would actually do

Every structure gives something up. The caveat line on each card says what. Read it before the rationale.

### Protective put. A floor.

Buy one put per 100 shares, around 30 delta.

**What it does:** Below the strike, you stop losing. Above it, you keep everything.

**What it costs:** The premium, every time, whether you need it or not.

**When it's right:** You're in profit and the strike sits above your basis.

**When it's wrong:** You're underwater. The Doctor's caveat on this card says it plainly: the floor is already under your basis, you're paying premium to cap a loss you're partly sitting in, and it doesn't help you get back to even.

### Covered call. Income.

Sell one call per 100 shares, around 30 delta, above the current price.

**What it does:** You collect the premium now, and that cash lowers your effective basis by the same amount. If the stock finishes below the strike you keep the shares and the premium and do it again.

**What it costs:** Your upside stops at the strike. If the stock rips past it, your shares get called away at the strike and you miss the rest.

**The trap when you're underwater:** The 30-delta strike might be *below* your basis. If it is, the Doctor flags it in red: the cap is below your basis, and if it rips you get assigned into a realized loss. You collected **$150** of premium and then sold your $62 shares at $57. That's a bad trade dressed up as income.

NBIS this week is the live version. Two weeks underwater, the Doctor's 30-delta call was the $200 strike, **$42.81** under the basis. It pays **$810**, and the card says it in red.

### Covered call at basis. Income without the trap.

This one only shows up when you're underwater, and it exists because of the trap above.

Instead of the 30-delta call, you sell the first strike at or above your cost basis. The premium is thinner because the strike is further away, but assignment can never book a loss. If you get called away, it's at a price at or above what you paid.

**What it does:** Collects some premium, lowers your recovery price by that amount, and if the stock rallies all the way back you exit at break-even or better.

**What it costs:** Less premium than the nearer call, and the downside is still completely open. It's a cap. There's still no floor.

In the example, say the $62 call 35 days out pays **$0.60**. Your recovery price drops from $62 to **$61.40**. Not a lot, but it's in the right direction, which is more than the put can say. And in a week like this one, with IV elevated, that $0.60 is more like a dollar.

`62.00 - 0.60 = $61.40 recovery. The put made it $63.80.`

When you're only slightly down, the at-basis strike is sometimes *closer* to the money than the 30-delta one, and then it's the richer call with the tighter cap. The card tells you which way it cuts.

### Collar. A floor paid for by a cap.

Buy the protective put and sell the covered call at the same time. The call pays for most or all of the put.

**What it does:** Boxes the position between the two strikes, often for close to zero net cost.

**What it costs:** Everything above the call strike. And if both strikes sit under your basis, which is common when you're well underwater, the Doctor says so: this locks the position into a loss range and takes recovery off the table. A zero-cost collar on an underwater position is a zero-cost way to guarantee you lose. This is the one structure where "locked in" is the right phrase, and the short call is the part doing the locking.

### Repair ratio, the 1 by 2. Recover twice as fast.

This is the one most of my readers have never seen priced, and it's the one built for the underwater case.

Per 100 shares: buy one call at the money, sell two calls at a higher strike. The two short calls pay for the one long call, so the structure is usually a small credit or close to free. One short call is covered by the long call, the other by your shares, so there's no naked upside.

**What it does:** Between the two strikes you own 200 shares' worth of upside instead of 100. The stock only has to climb half as far to get you back to even.

**What it costs:** Your upside stops dead at the upper strike. Above it the shares get called away and the extra call cancels the extra gain. And the downside is completely unchanged. Don't mistake it for a hedge.

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

You're whole at **$57.50** and out with a small profit at **$58**, instead of needing **$62**. My first draft had the gain at $1,500. It's $1,000. The conclusion survived and the number didn't, which is why the arithmetic goes in the post.

![The 1x2 at expiration, every cell typed out. Two-for-one between $53 and $58, dead stop at $58.](repair.png)

The Doctor picks the highest upper strike whose two short calls still pay for the long call. Higher cap, more room to run. The trade-off is that a lower upper strike collects more credit, and credit lowers the recovery price. The card shows both so you can pick.

### The sixth one. Sell the damn shares.

The Doctor doesn't price this one, because it isn't an options structure around shares you keep. It's here because it's what I'd do with most of the names that got hit this week, and leaving it out of a post about getting back to even would be dishonest.

Sell the shares. Book the $900 loss. Then sell a cash-secured put at the strike you wish you had bought at in the first place, 35 days out, and collect premium while you wait.

In the example: sell at $53, sell the $50 put for, say, **$1.20**. If it expires worthless you made $120 on $5,000 of collateral in a month and you still don't own a stock that was going down. If you get assigned, your new basis is **$48.80**, and the climb back to your old $62 is now a climb from $48.80, with premium paying you every month along the way. The hole is the same $900. What changed is that your capital is earning rent at $50 instead of praying at $62.

`50.00 - 1.20 = $48.80 new basis if assigned, versus $62.00 holding`

![Every structure in the $62 / $53 example, ranked by the price you need to get back to.](recovery.png)

This also harvests the loss for taxes, which none of the five structures do. One caution, and it's a real one: if you buy the shares back inside 30 days, or get assigned inside 30 days, the loss doesn't disappear, it gets deferred into the new basis. Buying a call on the same name inside that window does the same thing. So the sell-and-wheel and the repair ratio are mutually exclusive for a month. I did corporate accounting for a living and I still check this every time.

That's the premium seller's answer: become the casino and get rich slowly. The other five are for when, for whatever reason, you're not ready to let the shares go.

## Reading the Doctor's answer

The page opens with a verdict in plain English: your P&L, how far the stock has to climb, and what you should be shopping for.

Below that, every card carries the same numbers. Read them in this order.

**Recovery** is the headline. The lowest share price at or above the current price where the whole position, your shares at your basis plus the new legs, is back to zero at expiration. Doing nothing recovers exactly at your basis. The card shows the difference in words. "$2.40 easier" means the structure lowered your recovery price by $2.40. "$1.80 harder" means it raised it, which every protective put does. "Cannot recover" means the structure's cap sits under your basis, so the position can never get whole at expiration with it on. The card prints **Never** in red instead of inventing a number.

**Floor** is the worst price per share you can be forced to exit at, or a dash if the downside is still open. Only structures with a long put have one.

**Cap** is where your upside stops. Only structures with a short call have one. If the cap sits below your basis, the card says so in red, because assignment there usually books a realized loss.

**Net delta** is your remaining exposure in share-equivalents. 100 shares is +100. A collar might leave you at +40. The repair ratio can leave you at +100 or more between the strikes and far less above them. Smaller means less of the next move, in either direction, is yours.

**The scenario grid** shows the whole position's P&L at four prices: a down move, flat, your basis, and an up move. Every card and the do-nothing baseline quote the same four prices, so they compare directly. This is where you see the trade-off in dollars instead of adjectives.

**Cost** is the net debit you pay or credit you collect to put it on, across all contracts.

**The caveat** is the thing that bites. It's on every card.

## The Hedge Shopper, for when you are up

The Hedge Shopper sits next to the Doctor in the same section of Ticker Lab and answers the other question: what's the cheapest way to protect a gain?

It takes your share count, optionally your basis and a daily average true range, and shops four structures: the protective put, the collar, the put-spread collar (a cheaper collar where the floor stops working below a lower put strike), and the bear put spread (a defined-cost tactical hedge). It sizes the move it's protecting against off the chain's expected move, floored by a volatility-scaled estimate so a quiet name isn't under-hedged. Then it drops any structure that costs more than the loss it removes and ranks the survivors by cost per dollar protected. Credits and zero-cost structures float to the top.

You can run both on ASTS yourself in the [ASTS Ticker Lab](https://www.tradermatrix.pro/ticker-search/ASTS/lab?ref=MPHINANCE).

In profit, start there. Underwater, start with the Doctor. Not sure which you are? The Doctor's first line tells you.

## What the Doctor will not do

- **Work under 100 shares.** Options trade in 100-share lots. A 60-share position can't be covered or collared, and the Doctor says that instead of inventing a partial contract.
- **Guess your basis.** Every number on the page is measured against it. If you don't know it, look it up in your broker or the Trade Journal first.
- **Tell you the stock is going up.** It prices what each structure does *if* the stock reaches each scenario price. Whether it gets there is the market's business.
- **Offer the covered call at basis when you're in profit.** Above basis that structure degenerates into selling a deep in-the-money call, which is just selling your shares with extra steps.
- **Rank by a single made-up score.** Every card carries its own recovery, floor, cap, delta, and four-scenario P&L. The order comes from the diagnosis. The trade-offs stay visible.
- **Price the sixth structure.** Selling the shares is your call, and the chain can't price it for you.

## Where to find it

Open any ticker in Ticker Lab and scroll to the "More on SYM" section. Position Doctor and Hedge Shopper are the last two cards. From the Trade Journal's Positions page, every long share lot of 100 or more has a Diagnose link that opens the Doctor with your numbers already in. You can also ask Arya: give her the ticker, your share count, and your basis, and ask what gets you back to even.

Ticker Lab lives on [tradermatrix.pro](https://www.tradermatrix.pro/?ref=MPHINANCE) (that's my referral link), and the walkthroughs are on [youtube.com/@TraderMatrixHQ](https://www.youtube.com/@TraderMatrixHQ).

Both tools are Premium. If this week put you underwater and you want the numbers instead of the feeling, that's what the subscription is for.

Below the line: NBIS and ASTS through the Doctor, bought one week ago and two weeks ago. Same trades, opposite answers, and the one-line formula that tells you which side of that you're on.

<!--share-->

<!--paywall-->

## $NBIS and $ASTS, one week vs two

Two of this week's beaten-up names, two entry dates: the close on Friday, October 2, or the close a week later on Friday, October 9. Everything below is the production Doctor off Friday's closing chain, 100 shares. The covered calls and collars are November, the protective puts and repair spreads are December.

![NBIS and ASTS into Friday, with both entry prices and the repair cap marked.](live_charts.png)

### $NBIS, closed Friday at $165.47

**Bought October 2 at $242.81.** Down **$7,734**, 31.9%. The stock has to climb **46.7%** just to get you level.

- **Do nothing:** recovery at **$242.81**.
- **Protective put**, the December $145 for **$14.08** a share, **$1,407.50** all in. The floor is $97.81 under your basis. Recovery moves up to **$256.89**.
- **30-delta call**, the November $200 for **$8.10**. Collects **$810**, but the cap is $42.81 under your basis. Assigned at $200, you're out **$3,471**. Cannot recover.
- **Call at basis**, the November $250 for **$2.20**. Recovery drops to **$240.61**. That's the whole improvement.
- **1x2 repair**, buy one December $165 call, sell two December $200s, for a **$50 credit**. Cannot recover. If NBIS gets back to $200 by December 18, doing nothing leaves you down **$4,281**. The repair leaves you down **$731**.
- **Collar**, the November $150 put and $205 call for **$502.50**. Both strikes under your basis. It boxes the loss between **$4,283.50** and **$9,783.50**.

`(200 - 242.81) x 100 = -$4,281 doing nothing at $200`
`-4,281 + (200 - 165) x 100 + 50 = -$731 with the repair`

**Bought October 9 at $221.07.** Down **$5,560**, 25.1%. Needs **33.6%**.

- **Do nothing:** **$221.07**.
- **Protective put**, same December $145: recovery **$235.15**.
- **30-delta call**, same November $200 for $8.10. Cap still under basis. Assigned, you're out **$1,297**.
- **Call at basis**, the November $230 for **$3.63**: recovery **$217.45**.
- **1x2 repair**, the exact same December $165/$200 for the exact same $50 credit: recovery **$192.79**. That's **$28.28 easier**, and at $200 you're up **$1,443**.

`(S - 221.07) + (S - 165) + 0.50 = 0, so S = $192.79`

![The Doctor on NBIS bought October 9: the 1x2 gets you whole at $192.79.](doctor_nbis_1wk.png)

The strikes and the credit didn't change. One week of entry price is the difference between "cannot recover" and "whole at $192.79."

### $ASTS, closed Friday at $40.66

**Bought October 2 at $58.45.** Down **$1,779**, 30.4%. Needs **43.8%**.

- **Do nothing:** **$58.45**.
- **Protective put**, the December $35 for **$2.93**: recovery **$61.38**. The floor is $23.45 under your basis.
- **30-delta call**, the November $50 for **$1.80**. Cap under basis. Assigned at $50, you're out **$665**.
- **Call at basis**, the November $60 for **$0.71**: recovery **$57.74**. Seventy-one cents.
- **1x2 repair**, buy one December $40 call, sell two $45s, for a **$210 credit**. Cannot recover. At $45 you're down **$635** instead of **$1,345**.
- **Collar**, the November $36 put and $50 call for **$42**. Locks the loss between **$887** and **$2,287**.

![The Doctor on ASTS bought October 2: same repair, recovery Never.](doctor_asts_2wk.png)

**Bought October 9 at $50.97.** Down **$1,031**, 20.2%. Needs **25.4%**.

- **Do nothing:** **$50.97**.
- **Protective put**, same December $35: recovery **$53.90**.
- **30-delta call**, the November $50 for **$1.80**. The cap is 97 cents under your basis, but the premium is bigger than the gap, so this one does recover: **$49.17**. Assigned at $50, you're up **$83**. That's the exception to the red flag: a cap under basis only books a loss if the premium doesn't cover the gap.
- **Call at basis**, the November $55 for **$1.07**: recovery **$49.91**. Here the nearer call is the better income trade.
- **1x2 repair**, same December $40/$45 for the same $210 credit: recovery **$44.44**. That's **$6.53 easier**, and at $45 you're up **$113**.

`(50 - 50.97) x 100 + 180 = +$83 if the $50 call is assigned`
`(S - 50.97) + (S - 40) + 2.10 = 0, so S = $44.44`

![Every structure, both names, both entry dates. CAN'T means the cap is under your basis.](live_grid.png)

### The repair ceiling

You can tell whether a 1x2 can ever get you whole with one line of arithmetic. At the short strike, the shares and the long call have both paid you everything they're going to, and that's as good as it gets. So the highest basis a repair can rescue is:

`2 x short strike - long strike + credit per share`

NBIS: `2 x 200 - 165 + 0.50 = $235.50`. The October 9 basis of $221.07 is under it, so the repair works. The October 2 basis of $242.81 is over it, so the repair cannot.

ASTS: `2 x 45 - 40 + 2.10 = $52.10`. $50.97 is under it. $58.45 is over it.

If your basis is above the ceiling, the 1x2 shrinks the hole and that's all it does. That's where selling the shares and wheeling the put comes back into the conversation, because the repair already told you it can't finish the job. These are December structures, so look up both earnings dates before you put either one on.

Plug your own basis into the [NBIS lab](https://www.tradermatrix.pro/ticker-search/NBIS/lab?ref=MPHINANCE) or the [ASTS lab](https://www.tradermatrix.pro/ticker-search/ASTS/lab?ref=MPHINANCE) and check which side of the ceiling you're on.

~ Michael

=====CHANGELOG=====
- Cut the repeated "almost no chain screen shows you your basis" line from the end of the week section and from "It measures every candidate." The intro already makes that point.
- Collapsed the VIX paragraph's double explanation (put gets expensive / call gets rich, then insurance at panic rates / premium at panic rates) into one pass.
- Removed the second "puts that paid this week were bought before the drop" from the end of "When buying a put is actually right." It's the opening of the post and didn't need an encore.
- Fixed the contradiction in point 3 under "A put is a floor," which said the put "does nothing to" the recovery price and then that it raises it.
- Rewrote the "not X, it's Y" constructions: "the question is not... the question is...", "not hedging forever, hedging a day", "You are not hedging shares. You are making a bet.", "a cap, not a floor", "a recovery accelerator, not a hedge", "a decision you make, not a number."
- Softened the mic-drop endings: merged "Same stock, same put, same price, and the verdict flipped. The only thing that changed..." into one line, folded "Different questions." into the trap paragraph, and turned "Become the casino. Get rich slowly." into a clause.
- Reworded the $1,500 / $1,000 first-draft correction so it reads as a plain admission instead of a staged contrast. Both numbers kept.
- Moved the ASTS October 2 screenshot to after the collar bullet. The image line is unchanged, but it was splitting the bullet list in two.
- Fixed "before you open the chain" in the repair ceiling section, since the formula needs the strikes and credit from the chain. Now says "with one line of arithmetic."
- Dropped the duplicate Diagnose-link mention under "Guess your basis." It stays in "Where to find it."
- "Cap" definition now says assignment below basis "usually" books a loss, so it stops contradicting the ASTS $50 call exception explained below the paywall.
- Trimmed "The caveat ... because every structure gives something up," which repeats the structures section's opening line.
- Added contractions throughout and shortened a handful of sentences in the structure cards and the verdict section. No numbers, strikes, dates, formulas, links, images, markers, or headings changed.
