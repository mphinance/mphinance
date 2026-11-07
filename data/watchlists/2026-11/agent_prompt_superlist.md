You're building Michael's weekly "super list" machine: your own skills and screeners that find a few long setups each week, test them honestly, and hand him cards he can approve. Work in /home/mph/mphinance. Design it your way. Below is what one attempt already learned, so don't repeat its mistakes.

## What exists (read these first)
- data/watchlists/2026-11/: last two weeks' work. board_1106.json and board_1113.json are the card format. plan_1106.json is the plan format. we1113/verdict.md and we1113/plan_1113.json are the last run's output. README.md and r1-r3_bull/bear.md plus verdict.md are the 11/01 debate.
- .claude/skills/: stock-recap (all 14 TraderMatrix screeners, flow, 13F/TickerTrace, ranked by agreement), wheel-desk (nightly CSP grades), coil-scan (Williams %R coil), gamma-horizon (6-week levels and a graded plan), magnet-path, batch-scanner, momentum-squeeze (SKILL.md only, no script).
- .claude/skills/stock-recap/scripts/score_history.mjs: grades past shortlists against SPY.
- TDPro MCP tools (sector flow, market health, breadth, GEX, dark pool, insider, institutional, run_screener) and the Trading MCP tools (TickerTrace ETF flows), via ToolSearch.
- The public grader Michael's plans are scored on: https://www.tradermatrix.pro/mphinance (api.traderdaddy.pro/api/plan-receipts/mphinance). Its rules: shares on daily bars, a close-based trigger fills at that close, stop before target in the same bar, one position per card, R at the stated size.

## What the last run learned (measured, not opinion)
1. More screeners agreeing is not an edge. Over 79 trading days, 2 sources beat SPY 49% of the time, 3 sources 48%, 4+ sources 45%. The names on the most lists were one crowded AI/semis/miner bet. Treat agreement as a crowding flag unless you can show otherwise with your own backtest.
2. Week 1 (w/e 11/06): dip-only triggers missed both winners (AMZN +7.88%, PYPL +3.91%), because strong names don't dip on schedule. The trigger rule saved two bad holds (EQT -10.8%, NVDA -8.8%). USB stopped by one cent at a round number. TXN's first target was below its breakout fill. Following the rules: -1.52R. Just holding: -1.92%, against SPY -2.70%.
3. The last run's 1 ATR stop and 1.5R-to-T1 rule cut everything but TSLA. That was a choice, not a law. Test whether it's the right one.
4. A "fix" step once pushed targets further out to pass a reward-to-risk check. That games the test. Targets must come from real chart levels.
5. Data traps: the screeners went premium-gated on 2026-10-27 and stock-recap ran 1 of 14 for ten days without anyone noticing. Check health counts every run and fail loudly. Earnings dates in the recap conflict with screener rows, so verify them. Two volatility screeners return blank IV. 69 multi-source names and XLF plus the defensives never got tested last time.

## What to build
1. Your own screens. Not just a merge of the existing ones: design setups you can defend (for example, relative strength inside the sectors money is flowing into, institutional accumulation without price extension, post-earnings drift, breakouts from a base). Cover single stocks, sector ETFs and institutional flow.
2. A backtest for every screen before you trust it: what it would have picked on past dates, forward 5 and 20 sessions, against SPY and against a random pick from the same universe. Report hit rate and median excess with n. Kill screens that don't beat SPY. Watch for lookahead (no data the screen couldn't have had that day).
3. A testing stage on the picks themselves: real bars, extension (Michael doesn't chase: high RSI plus a big 1-month gain plus far above fast EMAs), earnings inside the hold, option liquidity, 126-day correlation (correlated clusters total 1R or less), a bull and bear argument, then an independent retest that tries to break the plan. Fixes may move a trigger to a real level, shrink size or cut a name, never stretch a target.
4. Output for w/e 11/20 in the existing formats: board_1120.json (cards plus a `cut` list with reasons) and plan_1120.json (passes `npx tsx src/scripts/sealPlanWeek.ts --file=... --dry-run`, run from a fresh worktree of origin/main of /home/mph/TraderDaddy-Pro---Whop/backend). Mix long shares or long calls only, 4R total at most.
5. Package it as skills under .claude/skills/<name>/ with SKILL.md (frontmatter name equal to the folder, description "<what it does>. Use when <trigger>.") and runnable scripts, then run `python scripts/check_skills.py`. Every screen should tag where each name came from, so the public record can later show which screens actually feed winners.
6. A short report: what you built, each screen's backtest numbers, what you'd keep and kill, and how your w/e 11/20 list compares to the last run's method.

## Hard rules
- Never cat, echo, grep or log .env_td_api, .env_agent_api or any header holding a key. Scripts load them. A key in your output is a leak (it happened last run).
- Read-only against everything outside your own files. Do not post to Discord, do not create or edit TraderMatrix watchlists, do not seal a plan (dry runs only), do not place orders, do not commit or push. Michael approves and posts.
- Work in a new folder, data/watchlists/2026-11/we1120/, and new skill folders. Don't edit the existing skills or tools; if you find a bug in them, report it.
- Say plainly when a source failed or a number is unverified. A short list is a fine answer. An honest "nothing passed" beats a padded one.
