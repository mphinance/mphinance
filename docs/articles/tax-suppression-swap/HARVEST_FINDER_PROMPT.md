Build "Harvest Finder" in TraderMatrix. We promised it publicly tonight: https://mphinance.substack.com/p/the-proprietary-mphinance-tax-suppression (read it first, it is the spec in plain English). Plan first, show me the plan, then build.

WHAT IT DOES
For a logged-in user with a connected broker: find their unrealized losers in taxable accounts, and for each one suggest 2 to 3 "cousins" (correlated but NOT substantially identical tickers) they could swap into to harvest the tax loss while keeping the exposure. Show the correlation, the beta-adjusted dollar amount, and the wash-sale "safe to buy back" date.

THE MATH (already prototyped; port it, don't reinvent it)
Prototype: /home/mph/mphinance/docs/articles/tax-suppression-swap/data/finder.py (and pairs.py, metals.py). Same box, read them.
- Daily returns from adjusted closes: r = P_t / P_{t-1} - 1
- Correlation: Pearson on the last 90 trading days of returns
- Beta of A on B: cov(rA, rB) / var(rB). Use the SAME ddof for both (the prototype originally mixed them and was off ~1%)
- Beta sizing: dollars of cousin to match risk = position value x beta(A on B)
- Candidate pool: the other tickers users search/watch most (ticker_search_events, user_watchlists) plus sector/theme ETFs (SMH SOXX XLK IGV CIBR SKYY XLC XLY XLE XLV XLF XLU XLI ARKK IBIT WGMI URA NLR UFO WARP DRAM QTUM BOTZ FINX BLOK TAN GRID MAGS XBI IBB GLD SLV GDX SIL IWM QQQ SPY). Make the pool config, not hardcoded.
- Precompute nightly (a correlation matrix over the pool is cheap); serve from cache. Don't compute per request.

RULES
- Only show cousins with corr >= 0.70. If the best is below that, say "no good cousin right now" with the best number shown. That's a real answer (RDDT, NFLX, UBER had none on 10/29).
- Never suggest the same company in another share class (GOOG/GOOGL) or a fund tracking the same index as the holding. Flag "gray zone" pairs instead of hiding them: two funds on the same underlying (IBIT/FBTC), or overlap like GDX/SIL at 0.98.
- Taxable accounts only. If the broker data says IRA/Roth/HSA, skip it, and warn if the user holds the SAME ticker in a retirement account (buying there inside the window kills the loss permanently).
- Wash-sale window = 30 days before AND after the sale. If the transactions data shows a buy of that ticker in the last 30 days, flag it. Safe-buyback date = sale date + 31 days.
- Show short-term vs long-term on each loser if lots allow (short-term losses offset short-term gains first, so they're worth more).
- Flag DRIP if we can detect it; otherwise a static reminder to turn it off.
- No order placement. Read only. It suggests; the user acts.
- Footer on every view: "Not tax advice. Talk to your CPA." Keep the "tax move, not a hedge" line from the post: the cousin falls when the original falls.

FIND BEFORE YOU BUILD (tell me what you found)
- Where connected broker positions + cost basis live (connect_trade_account_id shows up in wheel_positions and trade_journal_entries; there's also a get_my_broker_positions MCP tool) and whether account type (taxable vs IRA) is available
- Where we already get daily bars (reuse it, don't add a new data vendor)
- How existing nightly jobs are scheduled, and the existing page/component patterns to copy (dark theme)

SHIP IN THIS ORDER
1. Nightly correlation/beta job + table, with a quick check that RKLB-WARP ~0.91, IONQ-RGTI ~0.92, MU-DRAM ~0.93, NVDA-MU ~0.38 come out close (they will drift a bit from 10/29)
2. API endpoint: losers + cousins for the current user
3. UI: a Harvest Finder page (loser card -> cousin chips with corr, "moves 1.4x", beta-sized $, buyback date)
4. MCP tool get_harvest_candidates so the agents/Arya can answer "what can I harvest?"
5. Tests for the wash-sale date math and the account-type filter

Branch + PR, don't push to main. Tell me what you couldn't verify.
