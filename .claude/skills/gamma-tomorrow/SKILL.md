---
name: gamma-tomorrow
description: >-
  Build "Tomorrow's Map" for a ticker: one chart with recent candles on the left
  and three branching roads on the right (trend up / trend down / range), each
  waypoint labelled with what dealer gamma does to price at that level, plus an
  IF / IF / ELSE block underneath. Grades the previous night's map against what
  the session actually printed. Use when Michael says "tomorrow's map", "run the
  gamma map", "what's the SPY map", "where are the levels for tomorrow", "how did
  last night's map do", "score the map", or asks what happens at a given strike
  if the day trends up, trends down, or ranges.
---

# Tomorrow's Map

One picture that answers "if tomorrow trends down, what happens and where" without
making the reader interpret a gamma chart.

**Run it after the close.** The whole point is the book as it stands going into the
next session.

```bash
cd /home/mph/mphinance
node tools/gamma_tomorrow.mjs SPY --out /tmp/gamma
```

Flags: `--sessions N` (history days, default 3), `--band PCT` (strike range around
spot, default 1.4), `--out DIR`. Writes an HTML and a 3200x1900 PNG.

Keys: `.env_td_api` (bare `X-API-Key` on one line, no `KEY=` prefix).

## What the chart says

| element | meaning |
|---|---|
| PIN | heaviest strike within 1.5 of spot. What price is wrestling with. |
| FLIP | gamma flip. Above it dealers brake, below it they chase. |
| BRAKE | heaviest long-gamma strike between spot and the ceiling. Rallies stall here. |
| ACCELERANT | heaviest SHORT-gamma strike above spot. Dealers buy into strength, so price speeds UP through it. Not a wall. |
| CEILING | heaviest long-gamma strike above spot. Where the move dies. |
| TRAPDOOR / LAST SHELF | first significant strike below spot. "Shelf" if dealers are long gamma there, "trapdoor" if short. |
| THIN CUSHION | the only positive-gamma strike below spot. Small but it is the real bid. |
| PUT WALL | heaviest short-gamma strike below spot. A crowd, not a floor. |
| dimmed + `*` | beyond a typical day's move. A tail, not a plan. |

## The rules that were learned the hard way

Each of these came from the tool being confidently wrong on a real session. Do not
quietly undo them.

**Build levels from gamma that survives tonight.** `byStrike` includes contracts
expiring at today's close, and they are often the loudest strikes on the board.
On 2026-09-25, 70% of the 772 level and 80% of 770 were 0DTE, while the 761 put
wall was 99% real. The tool pulls `/gex/:sym/matrix` and sums only expiries after
today. A map of tomorrow built from a book that evaporates tonight is a map of
nothing.

**A big negative strike below spot is a crowd, not a floor.** Positive net GEX
means dealers are forced to buy; negative means they sell into weakness. On
2026-09-23 the tool called 760 the floor purely because it had the biggest
negative number, while TDPro's own level table correctly flagged 763 as support.
Price bottomed at 763.33 the next day.

**Rallies stall into heavy long gamma, not just at the top of it.** Dealers sell
rips into any large positive strike. The 9/24 map said "nothing gives until 772"
and price topped at 770.29 on a +$495M shelf.

**A short-gamma strike ABOVE spot is an accelerant, not a wall.** Mirror of the
downside rule, and it was wrong here for a week: a big negative strike above spot
was labelled WALL / "needs volume", telling a reader to fade a level the model's
own physics says should rip. Dealers short gamma there must buy into strength.

**Never assert structure from an absence of signal.** A missing strike used to
default to netGEX 0, and `0 >= 0` is true, so an unlisted level was always called
a SHELF you can lean on and an unknown pin always "settles". Both defaults biased
toward the calm, supportive read exactly when the tool had no data. Thresholds are
relative to the biggest level in the band, so a book with trivial size still
produced confident labels; there is now an absolute floor and a THIN BOOK banner.

**Do the ET conversions properly.** Session-close and the 0DTE cutoff were
hardcoded to UTC-4, which is EDT only. Every winter that marked the session closed
an hour early and baked a truncated high/low into the ledger permanently. Use
`Intl.DateTimeFormat` with `America/New_York`. A session from a prior date is
closed regardless of hour, which is also what makes half days grade correctly.

**The flip is a daily state, not an intraday trigger.** Across 1,954 one-minute
snapshots, the put/call GEX ratio and distance-from-flip correlate at -0.98 and
agree 99.95% of the time. They are one signal, not two. Four of five sessions had
zero flip crossings; the regime changed over a weekend. When the flip sits within
0.04% of spot the chart says so, because that is the state where it manufactures
crossings that mean nothing.

**Scale to a realistic day.** The yardstick is the median move from the *prior
close*, not intraday high-to-low, because that is what the roads project from and
it includes the overnight gap. On 9/24 the gap was 70% of the whole day's move.

## The ledger

Every after-close run appends its levels to `data/gamma_maps/<SYM>.json`, and the
next run grades the previous map against what that session printed: which road
fired, whether the cushion held, whether the flip capped the rally. The result
prints as a LAST CALL row and the graded levels are drawn back over that session
in green or red with the real high and low marked.

A session is only gradeable after 16:00 ET. Before that the panel reads IN FLIGHT
and **the ledger is not written**, so an intraday book never gets recorded as a
closing map. If a bad entry does get in, delete it from the JSON by hand.

**Only score levels price actually approached.** A level further from spot than a
typical day travels will pass a "never reached it" test on any quiet session, and a
null model with levels at arbitrary round numbers scores identically. Levels price
came nowhere near are marked UNTESTED, drawn grey, and excluded from the ratio.

Under that rule 2026-09-24 grades 3/3 on tested levels with 3 levels never in play.
The headline used to read 4/4.

**Never publish an accuracy number before it is one.** A grade is written into its
ledger entry permanently the first time its session closes, so the record builds
itself and old maps stay graded after the history feed rolls past them. The note
publishes a hit rate only once `MIN_GRADED` (10) sessions are on the clock; below
that it states how many days have been graded and explicitly declines to claim a
rate. One session is a number, not a track record. Do not lower that threshold to
make the post look better.

**Review the prior days before drawing a new one.** Every run backfills any
ungraded entry whose session has closed, then builds the new map. The ledger is
the memory; the chart is just today's view of it.

## Publishing

For a Substack post, pair the PNG with `tools/gen_image.py` cover art and push with
`tools/push_substack.py <workspace>/post.md`. Workspace needs `post.md` plus the
PNGs it references by relative path. House rules apply: no em dashes, sign-off is
exactly `~ Michael`, subtitle is a category mix like `*Trading 80% | Process 20%*`.

Draft the structure, never the voice. Michael rewrites the sentences.

## Known open

- Road weighting from ledger base rates. Needs a real sample; see MIN_GRADED.
- The UP and DOWN branches can both fire on a whipsaw day. That is now its own
  verdict and scores as a MISS rather than letting the chart claim it called both.
- Fonts load from Google on render. On a network-restricted cron the PNG still
  ships, silently, in a fallback monospace.
- The TradingView indicator's gamma flip disagrees with TDPro's by about 3 points
  (766.33 vs 769.22 on 9/23). Unresolved, and every up-road waypoint depends on it.
- The dev API caps at 30 requests/minute. The tool backs off and retries.
