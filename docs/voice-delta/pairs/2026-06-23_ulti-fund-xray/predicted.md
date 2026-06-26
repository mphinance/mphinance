# Don't Trust Me. Trust the Tape.

*Watch the pros sell options, graded, for free. Then watch the thing I built that does it while I sleep.*

A while back I wrote a manual on how to sell options. Strikes, moneyness, when to roll, how to actually keep the premium instead of handing it back. [The Options Field Manual is right here, free preview and the epub.](https://mphinance.substack.com/p/the-options-field-manual-free-preview)

You shouldn't take my word for any of it. So don't. Watch a fund with hundreds of millions of dollars on the line sell options, and let a tool grade them in real time, for free. That teaches you more than I can.

The tool is called TickerTrace. Point it at any option-income ETF and it pulls the whole options book apart on the table. Today's example is ULTI, the REX Shares option-income fund.

![ULTI Option Strategy Map: spot price plotted against every written strike](strategy-map.png)

Lesson one, strike selection. The Strategy Map plots spot price against every strike they wrote. SPCX is a cash-secured put sitting 13% in the money. MU is a covered call 5% out. The first thing the manual teaches is that where you sell decides whether you keep the premium or give it back. Now you can watch a pro make that call across every position at once.

![The ULTI option book: strike, weight, spot, and moneyness for every contract, expiring in 3 days](option-book.png)

Those are the receipts. The actual book, all 78 contracts, every one expiring in three days. Strike, weight, spot, and how far in or out of the money each one sits. No modeling and no marketing math, just the positions as they are.

![Six strategy scorecards grading the options overlay](scorecards.png)

Lesson two, how they manage it. DTE Management scores 100 out of 100, because the average contract is three days from expiry. This fund is a 0-DTE machine wearing an ETF costume. Premium Capture comes in at 65: they kept about 30% of gross, $2.8M net. The marketing shows you the yield. It does not show you this.

![Roll behavior, detected spreads, and peer comparison ranking ULTI #1 of 9](roll-spreads-peers.png)

Lesson three, rolling. 152 rolls detected, 151 of them weekend gap rolls. Roll Behavior scores a rough 25.8 out of 100, because rolling a zero-day book over the weekend is a high-wire act and the tool says so out loud. And yet, against eight sibling funds, ULTI still ranks #1 of 9. Best of a wild bunch. You would never learn either half of that sentence from a fact sheet.

That is the lesson, and the lesson is not "buy ULTI." It is that you can grade any income fund yourself, for free, before you trust it with a dollar.

## But you don't run an ETF

So here is how I actually do it, stripped to the bone. No black box.

I only sell when the premium is genuinely rich, which means implied volatility is trading above realized. If the market isn't paying me extra to take the risk, I don't take it. Then I don't sell at some textbook delta. I sell the put **at support**, the price level the chart has already defended, on a name I'd be happy to own there. Short-dated weeklies, roughly 5% below spot. Today that was an NVDA $190 put for Friday, four days out, about 5% under the price. And I measure the return on the cash I actually tie up, the strike minus the premium I collected, not the whole strike. One hard rule with no exceptions: if earnings land before expiry, I don't sell it. Selling premium through a print is the classic way to blow up.

That's the whole method. Rich premium, sold at support, short-dated, on a name you want, never through earnings.

## If you want to build one yourself

It's simpler than it sounds, and you don't need mine. You write the agent a charter (who it is and, more important, what it is NOT allowed to touch: no trading, no spending, no posting to the world, freeze on a STOP file), a goal broken into one-cycle steps, and a memory file it reloads every time it wakes. Then you run one prompt on a timer. Each firing it does ONE small thing, writes down what it learned, commits, and reschedules itself. Small steps plus a tight leash plus memory is the whole trick.

Here is that loop prompt, stripped generic. Point it at your own repo and put it on a timer:

```
Wake cycle. Working dir: <your repo>. You run on a timer; each firing ships ONE small thing.
(0) STOP CHECK: if a file named STOP exists, or INBOX.md starts with "stop", freeze and do not reschedule.
(1) Sync: git pull. Read INBOX.md, treat each line as an instruction from me, do it, then delete the lines you handled.
(2) Load context: CHARTER.md (who you are + what you may NOT touch), GOAL.md (the standing goal + roadmap), MEMORY.md (what you've learned). Skim the last 5 LOG.md entries.
(3) Pick the NEXT unchecked roadmap step. If the roadmap is done, derive the next on-goal step and add it first. INBOX overrides everything.
(4) Do exactly that one step, in THIS repo only. Keep it runnable: tests green, the build produces valid output. Verify before you trust it.
(5) Reflect: write ONE lesson back to MEMORY.md so next time you start smarter. Prune anything that is now wrong.
(6) Journal: prepend a dated LOG.md entry. Commit with a plain message and push.
(7) Reschedule this same prompt (default about an hour). Then stop.
```

Step 0 is the part people skip, and it's the part that matters. The leash is what lets the thing run while you sleep without ever doing something you'd have to apologize for.

So go look. Grade whatever income ETF is sitting in your account right now: **[tickertrace.pro/fund/ULTI](https://tickertrace.pro/fund/ULTI)**. Read the manual. Sell at support when the premium's rich. And if any of this was useful, send it to the one person you know who's holding a yield they can't explain.

We get better by looking at the thing we'd rather not look at. That's true in recovery and it's true in your brokerage account.

\- Michael, Managing Partner, The Phund
