# Seven ways I sabotage a good trade, and the desk that won't let me

*Trading 50% | Building 30% | Mindset 20%*

![hero](hero.png)

**[OPEN, your words: a futures moment where you knew the setup and still blew the trade on size or emotion.]**

**[SPINE LINE: I didn't need a better entry. I needed the dumb stuff to be expensive.]**

## The 45% trader

**[Your line: I win about 45% of my trades and I do about as well as my friend who wins 85%. Win rate isn't the score; how big the wins are against the losses is. My problem was never picking the trade. It was knowing how big to go, and when to sit out. Use only numbers you actually have.]**

## Revenge sizing

**[The feeling: I'll make it back on the next one. Your story?]**

What the desk does: after a loss, the next trade can't risk more than the one that just lost, and a cooldown starts.

## The tilt streak

**[The feeling: three red and you're not trading your plan anymore. Your story?]**

What the desk does: three losses in a row and it locks you out.

## Just one more contract

**[The feeling: the setup looks great, round up. Your story?]**

What the desk does: sizes from your remaining loss room and an ATR stop, always rounds down. If one contract risks too much it says REFUSED and tells you why.

![Risk 1% is refused with the reason; at 5% it fits](demo.gif)

*Practice market, made-up prices. 1% risk gets REFUSED with the reason. At 5% it fits.*


## The stop I'll set in a second

**[The feeling: I'm in, I'll place the stop in a sec. Your story?]**

What the desk does: the stop goes out right after the fill. If it isn't acknowledged in 5 seconds, it flattens and halts.

![Ticket: stop unprotected before the fill, acked after](ui-ticket-preview.png)

*Before the fill the stop reads UNPROTECTED. After, ACKED. If that flip doesn't happen in 5 seconds, it flattens.*


## Giving it room

**[The feeling: hope dressed up as trade management. Your story?]**

What the desk does: stops only move toward price. Breakeven, ATR trail, EMA 21 trail. Never wider.

![Manage trade panel](ui-manage-trade.png)

*The trail buttons say "not earned yet" until price pays for them.*


## The impulse click

**[The feeling: it's moving, hit it. Your story?]**

What the desk does: you STAGE first, then hold PLACE for 600 ms. The AI can stage. Only you place.

## The win rate lie

**[The feeling: my win rate is fine, so I'm fine. Callback to the 45% vs 85% line from the top: a win rate means nothing without the size of the wins next to the losses.]**

What the desk does: shows your win rate next to the win rate you need to break even, prices your fees as a share of 1R, and flags SMALL SAMPLE under 30 trades.

![Topstep's Big Board, top 25 live funded traders](big_board.jpg)

*Topstep's Big Board. The #1 live funded trader took home $533,350 batting 25.3%. 15 of the 26 names are under 50%. One is over 80. (Batting average here reads like winning days, not winning trades.) Source: Topstep.*

## Someone else's trade

**[Cut this one if there's no story. The feeling: someone in Discord called it, jump in.]**

What the desk does: the analyst alert can draw their entry, stop and target, but the one-click STAGE for it is off by default. The easiest button on screen shouldn't be someone else's trade.

## What it won't do

**[Short and blunt: it won't make you profitable (your README already says this). It stands between you and the version of you that shows up after two losses. Alpha software. No real-money order has gone through it yet. It does not track Topstep's trailing floor for you.]**

## Free, open, offline

**[Why it's free and open source: there's no edge in it to steal, and nobody should run a closed program that places orders on their eval. Runs offline on a practice market so you can tilt on fake money first.]**

![The whole desk mid-trade](desk-in-trade.png)

*The whole desk, mid-trade, on the practice market.*

[github.com/tradernetwork/projectx-desk](https://github.com/tradernetwork/projectx-desk)

~ Michael
