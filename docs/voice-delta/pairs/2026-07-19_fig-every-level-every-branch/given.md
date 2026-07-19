# FIG at $24 Is Not the Trade. The Coil Under $25 Is.

*Trading 80% | Mindset 20%*

![The FIG level ladder: the gate at 25, the shelf at 21.75, the flip at 20](fig_levels.png)

I called FIG at eighteen. It is twenty-four now. That is not the flex you think it is.

Here is the part I have to keep saying out loud so I actually believe it. Being right about the bottom does not buy me a discount at twenty-four. The entry that mattered already happened, back on June 30, when the momentum turned and almost nobody was looking. Buying it green today, up thirty percent from that print, is a different trade with a worse price and a worse edge. That itch, the one that says get in before it leaves, is the same defect that used to run the rest of my life. I am not feeding it.

## Where FIG actually is

FIG bottomed at 16.80 on June 25. The turn printed around eighteen on the 30th. Since then it has climbed into a five-session coil pinned right under twenty-five, tapping 24.87, 24.35, 24.39 and getting rejected each time. It is tightening under a ceiling, not rolling over. Those are two very different things, and the difference is the whole post.

But it ran hard to get here. RSI is seventy-two. Stochastic is eighty-seven. My own tools flag the buy zone as pullback-wait, which is the machine politely telling me not to chase this exact candle. And it is only half way back. The two-hundred day sits at 30.66 and the ninety-day high is 30.30. FIG is recovering inside a bigger downdraft from the mid-thirties. Not done. Just not cheap right here.

## The ceiling and the floor, in order

The gate is twenty-five. That is the call wall, it is the fib retrace at 25.07, and it is the top of a May supply shelf where seventy-seven million shares changed hands. Three reasons stacked on one number. Above it the air opens up: 25.84, then 27.74, then thirty where the two-hundred day waits.

The floor that matters is the flip at twenty. That is the put wall and max pain together, sitting on a demand shelf from early July. Above it dealers are on my side. Below it they step back and it falls faster. In between, the shelf I actually want is 21.65 to 21.85: the twenty-one day EMA, the fib at 21.83, and the July 7 low, all crammed into the same tiny band.

## Every branch

I am not predicting which way it breaks. I am writing down what I do in each case, ahead of time, so the decision is already made when the candle prints. This is the part I am finally good at.

```
IF FIG closes and holds above 25 on above-average volume
    -> BREAKOUT long. buy-stop 25.10.
       trim 25.84, trim 27.74, runner 30.
       invalidate: back under 24.20, cut it.

ELSE IF FIG pulls back into 21.65-21.85 (21EMA / fib / July-7 low)
    -> PULLBACK long. this is the one I want. limit 21.75.
       stop 20.80, under the flip.
       targets 25, 25.84, 27.74.

    ELSE IF it flushes to 20.0-20.44 (put wall + demand shelf)
        -> ADD a second piece near 20.20. stop 19.40. same targets.

ELSE IF FIG loses 20 on a closing basis (flip breaks)
    -> DEAD. no long. expect 18.61 then 16.80. stand aside.

ELSE (chop between 21.85 and 24.9)
    -> NOTHING. wait for the 25 break or the 21.8 tag.
       the middle is where you donate.
```

## The pretty picture

![The FIG trade card: two legs, real broker, real size](fig_trade_card.png)

So that is the pretty picture. What follows here is the ACTUAL trigger that will place the ACTUAL order.

```
The trade rule for this post (LONG only, pullback leg):
Symbol: FIG
Action: BUY
Broker: IBKR (real)
Size: ~$50 (about 2 shares at the limit)
Entry: LMT $21.75, GTC, outside_rth = true (extended-hours eligible)
Stop: informational for now, ~$20.80 (below the 20 wall flip)
Targets: $25 gate, $25.84, $27.74
```

```
The trade rule for this post (LONG only, breakout leg):
Symbol: FIG
Action: BUY
Broker: IBKR (real)
Size: ~$50 (about 2 shares at the trigger)
Entry: STP-LMT trigger $25.10 / limit $25.35, GTC, outside_rth = true
Stop: informational for now, ~$24.20 (failed breakout, back under the gate)
Targets: $25.84, $27.74, $30 (200-day)
```

Small size on purpose. The money is real and it comes from you. Half of what this newsletter earns goes straight into the account these trades run in. Not a demo, not a screenshot from 2019, the exact shares.

## The finish is the whole game

I can find the bottom. I proved that at eighteen. The thing I am still learning, in the market and everywhere else, is to wait for my price instead of grabbing the first green candle that yells hurry. The plan above is me building the patience into a file so I do not have to summon it in the moment, because the moment is exactly when I never have it.

~ Michael

---

*Not financial advice. Do your own research. Don't trade on someone else's conviction.*

*If this helped, subscribe so the next one lands in your inbox.*
