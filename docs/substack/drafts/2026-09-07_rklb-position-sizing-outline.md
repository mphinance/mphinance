# Position sizing ate every clever idea I had this week — article outline

Date: 2026-09-07 (Mon). RKLB spot $64.26. Not held. Nothing placed. Write when
the Phund has more cash — right now $613.83 free against $3,096.72 netliq.

---

## The hook

I finally wired Van Tharp's actual position-sizing math into the trade-rule
engine instead of just having Arya talk about it in Discord. First real trade
I ran it against, it killed every version of the idea except the boring one.

## Where this started

- Went to sell a covered call on RKLB in one account, checked the IV, realized
  I'd be capping upside for the cheapest premium this thing has offered all
  year. Backed out.
- Came to the Phund side wanting to flip that into a positive: if premium's
  this cheap, be a buyer, not a seller. Same fact, opposite trade.

## Round 1 — the ATM call didn't fit at all

- R-based sizing (risk% of netliq, position size = risk$ / stop-or-premium)
  on a small account hits a wall options don't have on stock: contracts come
  in $100-multiplier lumps. A share count can hit 2% risk exactly. A contract
  can't.
- The RKLB call that actually matched the breakout thesis needed **17% of the
  book** for one contract. A 50% soft-stop only brought that to 8.6%. Either
  way, one contract alone blew every sane risk cap before it even moved.

## Round 2 — "wait for the dip" (the idea that felt clever)

- Took a deliberately silly example strike ($85c, 10/16 — 32% OTM, just to
  stress-test the math) and modeled what it would cost if RKLB actually pulled
  back to its $60 support level a couple weeks out, using Black-Scholes off
  the contract's own IV.
- At a glance: the pullback price is dramatically cheaper ($13-30/contract vs
  $120 today), cheap enough for 2-3 contracts to fit the risk budget instead
  of zero. Looked like a real answer.

## Round 3 — the correction that flips it

- Held IV flat in that model. RKLB's ivRank is **0.8 out of 100** — the floor
  of its own 52-week band, still drifting down. That's exactly the wrong
  variable to hold still through a projection of the event (a support test)
  that's the classic trigger for vol to expand off a floor.
- Swept IV instead of fixing it: at a realistic "real selloff" vol (~100%),
  the same contract, after the stock actually drops 7%, can cost **more than
  it does right now** ($56-114/contract vs $120 today). Vega swamps the
  "further from spot" discount. The cheap-dip thesis doesn't survive contact
  with a name sitting at its own floor.
- The actually-correct read: cheap IV is the case for buying premium *now*,
  not for waiting on a dip that's likely to reprice vol against you before you
  get in.

## Round 4 — the account reality check

- Went to check real numbers and found IBKR is gone — drained to zero back on
  2026-08-25. The Phund isn't a separate IBKR book anymore; it IS the
  tastytrade account. One venue, not two.
- Real numbers: $3,096.72 netliq, **$613.83 free cash**. It's a cash account,
  no margin — so buying power is capped by settled cash, not by the risk
  math, and that cap can bind well before the risk-% or position-size caps
  do once other positions (the ONDS/RR/ACHR wheel stuff) are already holding
  capital.
- Checked whether a side tool (supermcp) could get real order execution back.
  It can't — by design. Live routing is off there, dry-run only, described in
  its own docs as "regulatory-gated, not just a code flag." No shortcut.

## Where it landed

- Long call: dead on contract granularity alone, before IV was even the
  issue.
- Covered call: dead on IV being at the floor (backwards trade to run into
  cheap premium) and dead a second time on capital (100 shares = $6,426,
  nowhere close to available).
- Shares: the only version that survived every check. R-based size wanted
  9-13 shares depending which cap you hit first; cash-on-hand was the actual
  limit, at 9 shares.

## The trade, whenever there's cash for it

- Entry: limit near $63 (pullback into the GEX support shelf at $60-64, not
  chasing spot)
- Stop: $58.50 (below the $60 support wall)
- Size: risk-based off real net liq at the time, capped by whichever of
  risk%/position-value/free-cash binds first — that last one is new, and it's
  the one that actually mattered here.

## The actual thesis for the piece

Position sizing isn't a formula you apply once and move on. It's a stack of
real constraints — contract lumpiness, where IV sits in its own range, cash
vs. margin — and each one can kill a *different* clever idea for a completely
different reason. The boring answer (a handful of shares with a real stop)
is what's left standing after all of them get a turn. That's the article:
not "I found a great trade," it's "here's what it actually takes to find out
an idea doesn't work, instead of guessing."

## Numbers to re-verify before publishing (all stale/example as of 2026-09-07)

- RKLB spot, GEX walls (flip $65.76, support $60/$55, resistance $65/$67/$70)
- ivRank / ATM IV (was 0.8/100, 65.0% — re-pull, don't reuse this print)
- Phund netliq / free cash (was $3,096.72 / $613.83)
- Whether RKLB is even the live stock-recap pick that day, or a different name
  entirely by the time there's cash to run this
