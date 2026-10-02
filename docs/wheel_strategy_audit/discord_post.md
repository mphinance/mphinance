# Discord Announcement: Blue-Chip Wheel Screener Update

**Image to attach**: `docs/wheel_strategy_audit/screenshots/discord_blue_chip_wheel_preview.png`

```markdown
Spent the morning tearing down one of the biggest options newsletters on Substack ("Options Income with The Wheel Strategy", $39/mo, 15k+ subs). 

I audited his last 12 weeks of trade recommendations (180 setups) to see how he picks them.

The secret? He is not scanning 5,000 stocks every Sunday. 

He rotates through a static pool of about 70 blue chips and ETFs. FCX was in 8 of the 12 weeks. UNH was in 8 weeks. PLTR was in 6 weeks. When you knock out companies with earnings this month and anything trading below its 200-day moving average, the entire market shrinks to about 20 names. 

Here are our backtest stats against his actual published newsletters across all of September:
- Stock Selection: We hit 58 out of 60 of his picks (96.7% universe overlap across 4 weeks).
- Strike Accuracy: 90% of our predicted strikes landed within 1 strike interval of what he published, with 55% matching the exact dollar strike.

I looked at TraderMatrix to see why our CSP screener was showing Bitcoin miners (CIFR, MARA) instead of blue chips like his. 

Found two bugs in the defaults:
1. The default $5,000 capital slider was hard-capping share prices at $50, which banned NVDA, QCOM, AMZN, and PLTR before Stage 1 even finished.
2. The default 1% weekly return required a 52% annualized yield. Quality blue chips pay 15% to 30%, so only high-beta crypto miners cleared the hurdle.

We just patched the engine and shipped a brand new one-click preset on TraderMatrix:

👉 **"Blue-Chip Wheel (All Grades)"**  
Link: https://www.tradermatrix.pro/screeners/csp-wheel

What it does:
- Lifts price ceiling to $500 (scans top 150 names by volume)
- Enforces price above 200-day SMA
- Automatically snaps to the put strike closest to 0.22 delta
- Caps each sector at max 3 names for real diversification
- Hard 14-day earnings blackout fence
- Ranks by annualized return

Ran it live on prod and got exactly 15 institutional setups: AFRM, MCHP, TXN, NOW, QCOM, DHR, CRWD, UAL, BMY, and NEM, all with deltas locked between -0.20 and -0.25.

Full teardown and case study dropping tomorrow with the math, but the preset is live on TraderMatrix right now if you want to run it for this week.

~ Michael
```
