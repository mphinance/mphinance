# Underwater on a Stock? Read This Before You Buy a Put

_What delta actually tells you, when buying a put protects you and when it just locks in your loss, and how the Position Doctor prices five ways out of a losing share position against the one number that matters: your cost basis._

A lot of people are sitting on shares they bought higher. The advice they get is always the same: "buy a put." Sometimes that is right. Often it is a way to pay money to make a loss permanent. The difference comes down to one number, your cost basis, and almost nobody checks it before they click buy.

This guide does two things. First, it teaches the three ideas you need to reason about any of this: what a put is, what delta is, and why your basis changes the answer. Second, it walks through the Position Doctor in Ticker Lab, which prices five structures around your actual shares and tells you which ones get you back to even and which ones cannot.

> **The short version:**
>
> - A put is a floor. Delta is how much of the move it catches. Neither one cares what you paid.
> - If you are DOWN, a put struck below your basis does not protect you. It guarantees the loss between your basis and the strike, and charges you for it.
> - The number that matters when you are down is the **recovery price**: where the whole position, shares plus whatever you add, is back to even. Doing nothing recovers at your basis. Anything that recovers lower is doing real work.
> - Selling calls, selling a call at your basis, and the 1×2 repair ratio can all lower that number. A put never does.
> - The Doctor needs 100 shares and your basis. It will not guess either.

## Part 1: The three ideas

### What a put actually is

A put option gives you the right, not the obligation, to sell 100 shares at a fixed price (the strike) until a fixed date (the expiration). You pay a premium up front for that right.

If you own 100 shares and buy one put, you have built a floor. Below the strike, every dollar the stock loses is a dollar the put gains, so your position stops losing. Above the strike the put does nothing, and at expiration it is worth zero. The premium is gone either way.

Three things follow from that, and all three matter later:

1. **The floor is at the strike, not at your entry.** A $50 put on shares you bought at $62 protects you below $50. It does nothing about the $12 between $62 and $50. That gap is already yours.
2. **Protection costs money every day.** The premium decays with time (theta). A put you buy and never need is a pure expense. That is fine for insurance on a gain. It is a bad trade when you have no gain to insure.
3. **A put does not help you recover.** It caps what you can lose from here. It does nothing to the price the stock has to reach for you to be whole again. If anything it raises it, because you now need to earn back the premium too.

### What delta is, in one paragraph

Delta is how much an option's price moves when the stock moves one dollar. A put with a delta of −0.30 gains about 30 cents when the stock drops a dollar, and loses about 30 cents when it rises a dollar. Calls have positive delta, puts have negative delta, and 100 shares of stock have a delta of exactly +100 (one dollar of stock move is one hundred dollars of position move).

Delta is useful for two different jobs:

**As a rough probability.** A 30-delta put is roughly a 30% bet that the stock finishes below that strike at expiration. It is not exact, but it is close enough to size your thinking. A 50-delta put is at the money. A 10-delta put is a lottery ticket against a crash.

**As a measure of how much of the move you still own.** Add up the deltas of everything in the position and you get your net exposure in share-equivalents. 100 shares plus one −30-delta put is a net delta of about +70: you still participate in 70% of every move, up or down, inside the range where that put's delta holds. Sell a +30-delta call against the same shares and you are at +70 again, but from the other side. Do both (a collar) and you are around +40.

> **The trap with delta:** people hear "30-delta put" and think "I am 30% protected." You are not. Delta tells you how much the put moves *today, for a small move*. Protection is what the put is worth *at expiration, at the price you are worried about*. Those are different questions. The Doctor and the Hedge Shopper both answer the second one with real payoff math, and then show you the net delta separately so you can see both.

### Why your cost basis changes everything

Here is the whole guide in one example.

You bought 100 shares at $62. The stock is at $53. You are down $900.

The advice is "buy a put." The chain shows a 30-delta put at $49 for $1.80. You buy it.

What have you done? You have paid $180 to guarantee that the worst case is now a $13 loss per share ($62 basis to $49 floor), plus the $1.80 premium. You have locked in a floor that is $13 under water and charged yourself for the privilege. If the stock goes nowhere, you lose the $180. If the stock recovers to $62, you are back to even on the shares and still out the $180, so your real recovery price just moved up to $63.80.

That put is not wrong because puts are bad. It is wrong because the question "what is the cheapest protection?" is the wrong question when you have nothing to protect. You do not have a gain. You have a hole. The right question is "what gets me out of the hole, and what does it cost me in upside?"

Now flip it. Same 100 shares, bought at $40, stock at $53. You are up $1,300. That same $49 put now protects a real gain: the floor is $9 above your basis. Paying $180 to lock in at least $720 of your $1,300 profit is a perfectly sensible insurance decision.

Same stock. Same put. Same price. Opposite verdict. The only thing that changed was the basis.

## Part 2: When buying a put is actually right

Buying a put makes sense in three situations.

**You have a gain to defend.** Your basis is below the current price and you want to keep most of the upside while capping the downside through a specific window. The Hedge Shopper is built for this. It sizes the move you are protecting against off the chain's expected move, floors it with a volatility estimate so quiet names are not under-hedged, and ranks the structures by cost per dollar protected.

**There is a dated risk inside the window.** Earnings, a lockup expiry, a court date, a macro print. You are not hedging forever, you are hedging a day. Short-dated protection is cheap relative to standing insurance, and if you are up on the shares it is often worth it. If you are down, see below.

**You are not hedging shares at all. You are making a bet.** Buying a put without owning stock is a directional trade that the stock goes down. That is a different animal entirely and has nothing to do with the Doctor. The Strategist in Ticker Lab is where that lives, including long puts and bear put spreads, ranked with their probability of profit.

Buying a put is the wrong move in exactly the case most people reach for it: **you are underwater, there is no dated event, and you just feel sick about the position.** A put does not fix that feeling. It monetises it.

## Part 3: What the Position Doctor does

The Doctor asks for two numbers: how many shares you hold, and what you paid per share. Then it reads the live option chain and does three things.

**It diagnoses the position.** More than 2% under your basis is *underwater*. Within 2% either side is *near basis*. More than 2% above is *in profit*. That bucket decides what you need, and the Doctor reorders its entire answer around it.

| State | What you need, in order |
|---|---|
| Underwater | Repair, then income, then protection-plus-income, then protection last |
| Near basis | Income first (nothing to defend, nothing to repair), then the rest |
| In profit | Protection first, then protection-plus-income, then income, then repair |

**It prices five structures off the real chain.** Each one is shopped on its own horizon, because they do different jobs. Income structures want time decay working for you, so they go short dated (about 35 days). A repair needs the stock to have room to travel, so it goes long dated (about 75 days). A protective put is standing insurance, so it sits in the middle (about 60 days).

**It measures every candidate against your basis.** Not against the current price. Against what you paid.

## Part 4: The five structures, and what each one gives up

Every structure in the Doctor gives something up. The caveat line on each card says what. Read it before the rationale.

### Protective put — "a floor"

Buy one put per 100 shares, around 30 delta.

**What it does:** Below the strike, you stop losing. Above it, you keep everything.

**What it costs:** The premium, every time, whether you need it or not.

**When it is right:** You are in profit and the strike sits above your basis.

**When it is wrong:** You are underwater. The Doctor's caveat on this card says it in so many words: "the floor is already under your basis — this pays premium to cap a loss you are partly sitting in, it does not help you get back to even."

### Covered call — "income"

Sell one call per 100 shares, around 30 delta, above the current price.

**What it does:** You collect the premium now. That cash lowers your effective basis by the same amount. If the stock finishes below the strike, you keep the shares and the premium and do it again.

**What it costs:** Your upside stops at the strike. If the stock rips past it, your shares are called away at the strike and you miss the rest.

**The trap when you are underwater:** The 30-delta strike might be *below* your basis. If it is, the Doctor flags it: "the cap is BELOW your basis — if it rips, you are assigned into a realised loss." You collected $150 of premium and then sold your $62 shares at $57. That is a bad trade dressed up as income.

### Covered call at basis — "income without the trap"

This one only appears when you are underwater, and it exists because of the trap above.

Instead of selling the 30-delta call, you sell the first call strike at or above your cost basis. The premium is thinner because the strike is further away, but assignment can never book a loss: if you get called away, it is at a price at or above what you paid.

**What it does:** Collects some premium, lowers your recovery price by that amount, and if the stock rallies all the way back you exit at break-even or better.

**What it costs:** Less premium than the nearer call, and the downside is still completely open. This is a cap, not a floor.

The Doctor says which way the comparison cuts in each case. Sometimes the at-basis strike is actually *closer* to the money than the 30-delta one (when you are only slightly down), and then it is the richer call with the tighter cap. The card tells you which.

### Collar — "a floor paid for by a cap"

Buy the protective put and sell the covered call at the same time. The call premium pays for most or all of the put.

**What it does:** Boxes the position between the two strikes, often for close to zero net cost.

**What it costs:** Everything above the call strike. And if both strikes sit under your basis, which is common when you are well underwater, the Doctor says so: "this locks the position into a loss range and takes recovery off the table." A zero-cost collar on an underwater position is a zero-cost way to guarantee you lose.

### Repair ratio (1×2) — "recover twice as fast"

This is the one most people have never seen priced, and it is the one built specifically for the underwater case.

Per 100 shares: buy one call at the money, and sell two calls at a higher strike. The two short calls pay for the one long call, so the structure is usually a small credit or close to free. The second short call is covered by your shares, so there is no naked upside risk.

**What it does:** Between the two strikes, you now own 200 shares' worth of upside instead of 100. The stock only has to climb half as far to get you back to even.

**What it costs:** Your upside stops dead at the upper strike. Above it, the shares are called away and the extra call cancels the extra gain. And the downside is completely unchanged. This is a recovery accelerator, not a hedge.

**Worked example:** 100 shares at $62, stock at $53. Buy one $53 call, sell two $58 calls, roughly even money. Between $53 and $58 you gain $2 per $1 the stock moves. At $58 you have made $1,000 on the structure plus $500 on the shares, which is $1,500 against a $900 hole. You are out at a small profit at $58, instead of needing $62. The Doctor picks the highest upper strike whose two short calls still pay for the long call, because a higher cap is strictly better and that strike is the one closest to free.

## Part 5: Reading the Doctor's answer

The page opens with a verdict in plain English. Read it. It names your P&L, how far the stock has to climb, and what that means for what you should be shopping for.

Below that, every card carries the same set of numbers. Here is what each one means and which one to look at first.

**Recovery** is the headline. It is the lowest share price at or above the current price where the whole position, your shares at your basis plus the new legs, is back to zero at expiration. Doing nothing recovers exactly at your basis. The card shows the difference in words: "$2.40 easier" means the structure lowered your recovery price by $2.40. "$1.80 harder" means it raised it (every protective put does). "Cannot recover" means the structure's ceiling sits under water: the position can never get whole at expiration with that structure on. The Doctor returns that as an honest dash instead of inventing a number.

**Floor** is the worst price per share you can be forced to exit at, or a dash if the downside is still open. Only structures with a long put have a floor.

**Cap** is where your upside stops. Only structures with a short call have a cap. If the cap sits below your basis, the card says so in red. That means assignment is a realised loss.

**Net delta** is your remaining exposure in share-equivalents after the structure is on. 100 shares is +100. A collar might leave you at +40. The repair ratio can leave you at +100 or more between the strikes and far less above them. A smaller number means less of the next move, in either direction, is yours.

**The scenario grid** shows the whole position's P&L at four prices: a down move, flat, your basis, and an up move. Every card and the "do nothing" baseline quote the same four prices, so the cards compare directly. The band is sized off the longest horizon's expected move. This is where you see the trade-off in dollars rather than in adjectives.

**Cost** is the net debit you pay or the credit you collect to put the structure on, in dollars, across all contracts.

**The caveat** is the thing that bites. It is on every card because every structure gives something up.

## Part 6: The Hedge Shopper, for when you are up

The Hedge Shopper sits next to the Doctor in the same section of Ticker Lab and answers the other question: *what is the cheapest way to protect a gain?*

It takes your share count, optionally your basis and a daily average true range, and shops four structures: the protective put, the collar, the put-spread collar (a cheaper collar where the floor stops working below a lower put strike), and the bear put spread (a defined-cost tactical hedge). It sizes the move it is protecting against off the chain's expected move, floored by a volatility-scaled estimate so a quiet name is not under-hedged. Then it drops any structure that costs more than the loss it removes, and ranks the survivors by cost per dollar protected. Credits and zero-cost structures float to the top.

If you are in profit, start here. If you are underwater, start with the Doctor. If you are not sure which you are, the Doctor tells you in the first line.

## Part 7: What the Doctor will not do

- **It will not work under 100 shares.** Options trade in 100-share lots. A 60-share position cannot be covered or collared, and the Doctor says that instead of inventing a partial contract.
- **It will not guess your basis.** Every number on the page is measured against it. If you do not know it, look it up in your broker or your journal first. The Trade Journal's positions page has a "Diagnose" link on every eligible share lot that carries the count and average cost across for you.
- **It will not tell you the stock is going up.** It prices what each structure does *if* the stock reaches each scenario price. Whether it gets there is the market's business.
- **It will not offer a covered call at basis when you are in profit.** Above basis that structure degenerates into selling a deep in-the-money call, which is just selling your shares with extra steps.
- **It will not rank by a single made-up score.** Every card carries its own recovery price, floor, cap, delta and four-scenario P&L. The order comes from the diagnosis; the trade-offs stay visible.
- **It does not know about earnings.** If a report falls inside a structure's window, implied volatility will crush after it, which hurts the long legs and helps the short ones. Check the date before you commit to a horizon.

## Where to find it

Open any ticker in Ticker Lab and scroll to the "More on SYM" section. Position Doctor and Hedge Shopper are the last two cards. From the Trade Journal's Positions page, every long share lot of 100 or more has a "Diagnose" link that opens the Doctor with your numbers already in. You can also ask Arya: tell her the ticker, your share count and your basis, and ask what gets you back to even.

Both tools are Premium.
