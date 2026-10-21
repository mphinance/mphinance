---
name: gamma-horizon
description: Build "The Next 6 Weeks" map for a ticker: daily candles + Keltner 1/2 ATR on the left, every option expiry in the next ~60 days on the right with the call wall, put wall, magnet and settle level projected to each date, stepped roads that change when an expiry rolls off, the options-implied move cone, and a rule-based plan (entry / stop / T1 / T2) that is logged and graded. Use when Michael says "6 week map", "horizon map", "apexweek", "the next 6 weeks for X", "run it for these tickers", "gamma path", "where are the walls into opex", "grade the plans", or asks for the swing-timeframe version of Tomorrow's Map. Sibling of gamma-tomorrow (next session) — this is the multi-week view.
---

# The Next 6 Weeks

```bash
cd /home/mph/mphinance
node tools/gamma_horizon.mjs NVDA --out /tmp/gh            # chart + logs the plan
node tools/gamma_horizon.mjs NVDA --out /tmp/gh --no-log   # chart only
node tools/gamma_horizon.mjs --grade                       # re-grade every logged plan
```

Flags: `--days N` (forward window, 60), `--bars N` (daily candles, 65), `--minshare PCT`
(OI share an expiry needs to count as major, 5), `--no-log`. Writes PNG + HTML + JSON
sidecar. Keys: `.env_td_api`. Daily bars come from Yahoo.

**Arya runs the same model** as `/tm apexweek` (`~/TraderDiscord-v2/bot/horizon_map.py`,
TraderMatrix look via `bot/tm_theme.py`). When the model changes here, port it there, and
the other way round, or the two drift. TraderMatrix's own Magnet Path still reads each
expiry alone: issue #1150 on avorojeykin/TraderDaddy-Pro---Whop.

## The model (v3, 2026-10-18) — each rule came from a real wrong chart

1. **Gamma, not open interest.** `expiryStats.callWall/putWall` from the API are the
   largest-OI strike for that expiry alone (documented in TM's `gexExpiryStats.ts`). MU
   10/09 said "call 1200" while that expiry's gamma piled at 1100. Every level here is
   computed from the `/gex/:sym/matrix` gamma.
2. **The board on a date is every expiry still alive**, not one expiry read alone. Dealers
   hedge the whole book. TM's Magnet Path does it per expiry and zig-zags
   (NVDA 10/18: 225 → 237.5 → 200 → 210 → 205 while the real lid was 230 the whole way).
3. **Merge the daily, weekly and monthly matrices.** The default grid is 10 columns and
   dropped NVDA's 11/06, 11/13 and 11/27 weeklies.
4. **Project gamma to the date; don't freeze today's.** Ratio per strike and expiry:
   `[φ(d1_t)/√T_t] / [φ(d1_now)/√T_now]`, σ from the expiry's priced move (`emPoints`),
   spot held, capped 12×. ATM gamma swells into expiry, OTM fades. The frozen board
   dropped NVDA's 205 floor to 190 after 10/30; projected, the 11/20 monthly's puts hold
   205 into 11/20.
5. **Today is t=0.** Read today's board at t=0, not "just before the first expiry"; with
   projection those differ (a weekly's OTM wall fades as it nears). Hand-offs are measured
   from today: "105 is the lid now, 110 by 10/16" vs "230 until 11/20, then 240".
6. **A wall must be ≥10% of its board** to count. MU's "put wall" was a -$15M strike $4
   under spot on a book with a +$155M strike.
7. **Size is on the chart.** Road width scales with the wall's projected dollar gamma and
   the end labels carry it (`UP · 240 · $36M`). A flat max-wall line hid that a lid was
   $97M now and $22M after the monthly.
8. **The strike data stops at ±15% of spot** (server-side `STRIKE_RANGE_PCT`, no param).
   The chart marks the edge; a wall past it is invisible, not absent.
9. **Strip = roads.** The per-expiry number strip shows the same midpoint reading the
   roads use, so the two never disagree.
10. **The upside row leads with the lid, not the flip** ("it can wick over, it tends to
    close under"). From the SPY map audit: lids held on the close 5/5, the flip 3/6.

## The plan and its grading

Entry = heaviest significant strike at least ½ ATR under spot (put wall or long-gamma
cushion), else a 1-ATR pullback. Stop 1 ATR under entry. T1 = nearest call wall ≥ ½ ATR
away on any board, else Keltner. T2 = upper 2-ATR Keltner or T1 + 1 ATR.

Every run logs the plan to `data/gamma_maps/horizon/<SYM>.json` (force-add: `*.json` is
gitignored). Fill = the low reaches the zone and the close holds its bottom. After the fill,
stop is checked first if a bar touches both. A plan whose window ends unfilled is NO FILL;
one that ends filled and unresolved is EXPIRED. Grades are durable once resolved. Cron
`e7584067` runs `--grade` weekdays 17:20 ET.

**No hit rate before 10 resolved plans across 5 different plan days.** Plans drawn on one
day share one tape: the 10/08 batch had 13 of its first 14 stopped within a week in one
selloff, positive- and negative-gamma names alike. That is one observation about the
market, not 14 about the method. Do not lower either number to make a chart look better.

Known weakness the 10/08 batch exposed: the plan is always a long pullback buy with no
market filter. Candidates once there is a real sample: skip entries while SPY is below its
own flip or under its 21 EMA; a short-side plan in negative gamma.

## Sharing

Charts for people outside the group: say the PLAN row is fixed rules, not a track record
(Arya's card says so in the header and footer). Thin books (< $1M net gamma) get a banner;
read their levels lightly.
