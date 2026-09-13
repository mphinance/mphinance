# Prompt for the TraderDaddy repo

**Copy the plan over first, or the new session will regenerate from scratch and lose your edits.**

```bash
cp /home/mph/mphinance/docs/conference/TRADERDADDY-SUMMIT.md docs/
```

---

```
Read docs/TRADERDADDY-SUMMIT.md. It's a v1 schedule outline for a two day
in-person TraderDaddy Pro summit, with a Session Bank of about 42 candidate
sessions at the bottom. Don't rewrite it from scratch. Don't touch
Operations or The Grunt Work, those sections are mine.

THESIS: retail's only genuinely unfair advantage is that retail has jobs.
The community already contains the semiconductor analyst a fund pays $300k
for. Day 1 ("The Floor") pairs an operator who works in an industry but
can't trade it with a trader who can trade anything but knows nothing about
the industry, and drives them live to one written thesis with a ticker, a
mechanism, a timeframe, an invalidation, and a way to be measured. Day 2
("The Machine") is the mechanics that turn a thesis into a strike, plus the
proof that any of it works.

GOVERNING RULE: no performance claim goes on stage without a benchmark, a
sample size, and a link to the data. Applies to our own products with no
exception, and our own screener takes the Audit chair before any member's.

WHAT I WANT:

1. Double the Session Bank. It has ~42 candidates. Get it to 80+. I want a
   deep pool to cast from, not a finished schedule. Go wide across market
   structure, volatility, the income playbook, systems and verification,
   psychology, taxes and business, and the Day 1 industry tracks. Add
   tracks that aren't there yet if you can defend them. One line each:
   session title, and the one thing it teaches. Do not write essays.

2. For every session, mark whether we can demo it live with our own data,
   and name the source. What we have:
   - TraderDaddy Pro dev API (screeners, flow, GEX, earnings) and the older
     Railway agent API (charts, CBOE, enrich)
   - TickerTrace: https://api.tickertrace.pro (see /openapi.json for all
     paths, https only). /api/v1/income, /holdings, /options-listings,
     /institutional, /signals, /signal-performance, /divergences,
     /fund-effectiveness, /layering-patterns, /sectors
   - mphinance/TickerTrace repo: 122 daily holdings CSVs at
     etf-dashboard/public/data/history/ carrying full option legs
   A session we can screen-share beats a session we can only talk about.
   Sort the bank so the demoable ones are obvious.

3. Flag the 10 sessions that only WE can run. Anyone can do a covered call
   talk. Which ones require our data, our community, or our willingness to
   get audited in public? Those are the marketing.

4. Then rebuild the two day grid from the bank. Say what you cut and why.

5. Pressure test the Day 1 Floor format. It is the entire event and it
   rests on four people who have never spoken on a stage. How does it fail,
   and what has to be in the moderator brief to stop that?

6. Draft two artifacts that don't exist yet, as separate files:
   - The one page speaker agreement with the receipts clause.
   - The pre-commit interest form from Grunt Work step 1: city, month,
     price band, nights, and the fifty dollar refundable deposit question.
     The deposit count is the only number that predicts a full room.

CONSTRAINTS:
- No names. Roles only, like "the operator" or "the vol specialist".
- Outline and schedule form, not essay. Keep the time grid per day.
- No em dashes. No hype filler. Don't call anything "the key" or "where
  the magic happens".
- Sign off exactly: ~ Michael
- Push back. If a session doesn't earn its slot, cut it and say why.
```

---

## Separate prompt: the income-ETF roll analysis

Only if you want the data work. Unrelated to the program above.

```
Reconstruct income-ETF option roll events from the TickerTrace history and
measure what the underlying was doing around each roll.

DATA: mphinance/TickerTrace, etf-dashboard/public/data/history/
holdings_YYYY-MM-DD.csv. 122 daily files, 2026-02-25 to 2026-08-06, 38
columns. Option fields: Underlying_Ticker, Option_Strike, Option_Expiry,
Option_Type, Underlying_Price, DTE, Moneyness, and Share Quantity where
negative means written. Schema reference: https://api.tickertrace.pro/api/v1/income

ROLL = the Option_Expiry set changes for a fund plus underlying between
consecutive snapshots. Confirm with DTE jumping up then decaying daily.
Calendar gaps create phantom rolls, so check the prior snapshot exists.

THREE THINGS A PREVIOUS PASS GOT WRONG. Do not repeat them:
- It sampled files instead of reading all 122, and reported ~6 rolls for a
  weekly roller across 24 weeks. Read every file.
- It took the underlying from the fund's name and got them wrong. MSTY is
  MSTR, not MSFT. CONY is COIN, not CORN. Use the Underlying_Ticker column.
- Its output repeated the same Moneyness across three different rolls.
  That's a falsy-default bug, not a finding. Repeated values are broken
  until proven otherwise.

OUTPUT, single-underlying funds first, then diversified:
- Roll table: date, old and new expiry, old and new strike, spot on the
  roll day, moneyness, rolled up / down / flat.
- Joined to price: underlying return on R-1, R, R+1, R+5 via yfinance, and
  realized vol around the roll.
- Six month drift: did the fund widen strikes after getting run over in a
  rally, and tighten when defending a distribution.

State your real N and don't oversell it. The claim I want is descriptive,
where the ceiling is and when it resets, not causal.

Write it as a reusable script, not a one-off in /tmp.
```

~ Michael
