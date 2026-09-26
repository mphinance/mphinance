# Why I built TickerTrace — outline

Two receipts, the manual process, the tool, the CTA. Nothing else.
Date: 2026-09-05. All numbers verified today.

---

## The two receipts (these are the whole proof)

| | Found it | Price then | Now | Return | SPY same window | **Excess** |
|---|---|---|---|---|---|---|
| **SHOO** Steven Madden | **2025-07-01** | **$24.64** | $43.68 | **+77.3%** | +26.1% | **+51.2 pts** |
| **MLI** Mueller Industries | **2024-12-30** | **$79.77** | $63.74 | **+63.0%** | +33.2% | **+29.8 pts** |

**MLI split 2-for-1 on 2026-07-01.** $79.77 is the real price you saw and what
your screenshots show. $39.10 is the split-adjusted figure; the +63.0% is
computed on the adjusted series, which is correct. **Use $79.77 in the prose.**
Same for the Dec 2025 follow-up: you saw **$113.73**, adjusted is $56.38.

Benchmark both against SPY in the post. It is the difference between "I picked
two stocks that went up" and "I beat the index by 51 and 30 points," and you
already made the alpha-vs-benchmark argument yourself on 2025-09-21 in
`using-beta-to-become-the-alpha`.

---

## Structure — FREE above the fold, SHOO behind the paywall

**Rule for the free half: do not name SHOO, do not use `SHOO_since.png`, do not
use your 9/5 SHOO chart.** Incidental appearance inside a sheet screenshot is
fine, but neither sheet actually contains it — the AVLV sheet is large-cap, and
the 9/21 AVUV list is GEF / ZUMZ / UPWK / SKYH / NBBK / FOSL / ASPN / REX /
CFFN / VSCO. Both are safe to show.

---

# FREE

### 1. Open on MLI

Found it in AVUV back when it was still a small cap. **$79.77 on 2024-12-30 →
$63.74 today, +63.0%, against SPY's +33.2%. +29.8 points of excess.**

(Split-adjusted entry is $39.10. Use $79.77 in the prose so it matches the
screenshots. MLI split 2-for-1 on 2026-07-01.)

Assets: `MLI_since.png`, `2025-12-16_MLI-dd_1.png` (your TradingView daily at
$114.03).

### 2. The old way — show the spreadsheet, don't describe it

Your own line from 2025-07-01:

> "every few days I download the $AVUV holdings file so I can keep an eye on
> what Avantis is buying — nearly 1/3 of my long term profits have come from
> pulling equities from this list"

> "This month I ended my VLOOKUPS and crazy manual tracking — dumped all the
> CSVs into the Gemini of Googs, out spits this beautiful list of institutional
> buying."

Asset: **`2025-09-21_scorecard_1.png`** — the `AVLV-0918` Google Sheet, columns
"Shares on 9/18 / Shares on 9/12 / Share Change / % Change". **MLI is visible in
it at 37.00%**, which ties the receipt to the method in one image. Perfect for
the free half and it contains no SHOO.

(Those percentages are share-count changes, not returns. Say so.)

### 3. The reader question — this is the hinge

From the comments on your own 2025-09-21 AVUV post:

> **casehuiz:** "How do you determine which stocks to buy from the list?"
> **TheRealBigL:** "@mphinance that makes sense, which do you look for?"
> **jeisa:** "Would you consider leap / calls or stocks?"

Three people asked the same thing and you never fully answered it in public.
That is the honest reason there is a paywall, and it beats any manufactured tease.

Asset: `2025-09-21_avuv-now.png` (the post with the comments visible).

### 4. Why the sheet couldn't answer it → why I built the tool

What the CSV-and-VLOOKUP method could not do:

- Download a holdings file by hand every few days, forever
- No history — two snapshots, never the shape of a build
- No way to separate real accumulation from a fund-wide inflow day
- No way to catch a provider file refresh posing as new positions
- One fund at a time. No cross-family view.
- AVUV only, until you hand-rolled AVLV as well

Every one of those is now a feature. That is the whole argument for the build.

### 5. The honest twist that JUSTIFIES the paywall

**By the time you wrote MLI up publicly on 2025-12-16 at $113.73, most of the
move was already behind it.** From that post to today: **+13.1% against SPY's
+14.4% — minus 1.3 points.**

Say that out loud. It is the strongest paragraph available to you:

> The public write-up wasn't the edge. Finding it thirteen months earlier was.
> Which is exactly why the name I'm watching right now is behind the paywall
> instead of in this paragraph.

That converts better than any hype line, and it is true.

### 6. TickerTrace + CTA

Assets: `tickertrace_stock_MLI.png`, `tickertrace_fund_AVUV.png`,
`tickertrace_fund_AVLV.png`.

- MLI — https://tickertrace.pro/stocks/MLI
- AVUV — https://tickertrace.pro/fund/AVUV
- AVLV — https://tickertrace.pro/fund/AVLV
- All stocks — https://tickertrace.pro/stocks

Route is `/stocks/` plural. `/ticker/` 404s.

Close the free half on TraderMatrix — the TickerTrace header already carries
"Trade it on TraderMatrix →", so the handoff is native.

---

# ===== PAYWALL BREAK =====

# PAID — SHOO

### 7. The answer to casehuiz's question

**I bought Steven Madden off this list on 2025-07-01 at $24.64. It is $43.68.
+77.3%, against SPY's +26.1%. +51.2 points of excess.**

Assets: `SHOO_since.png`, `2025-07-02_SHOO_1.png` (the original post, "my $SHOO
position is up 5% since yesterday").

### 8. And it is back on the list right now

- TickerTrace tags it **Accumulating** — 4 funds, 2 families, ~$22M exposure
- Net flow positive on the day, the week AND the month
- **AVUV: 292,425 → 375,603 shares in a week, +28.4%**, which is the **96.6th
  percentile** of that fund's own moves
- Caveat to state plainly: the `NEW` badges on AVSC/AVUS are a 2026-09-04
  provider file-refresh artifact (10,548 of 19,639 rows flagged that day), and
  the blended-weight chart's flat-then-step shape is the same artifact. Use the
  share count as the evidence. Owning this makes the tool look better, not worse.

Asset: `tickertrace_stock_SHOO.png`.

### 9. Why it passes the checks (this IS the answer to "how do you determine")

Lay out the actual filter, because that is what they are paying for:

1. **Above its last swing low?** Yes — bounced off $40.80 and held the rising line
2. **Positive interest coverage?** **26.1x**, D/E 0.13, current ratio 1.91
3. **Real growth at a sane price?** Revenue +18.2%, EPS +57%, gross margin 46.1%,
   forward P/E 19.4 → **PEG ≈ 1.07**
4. **Tradeable?** 852K–1.06M ADV, listed options, **IV rank ~0** so calls are
   historically cheap
5. **Did the fund add to THIS name or its whole book?** 96.6th percentile. This one.

### 10. The setup

Asset: `mph_SHOO_chart_2026-09-05.png` (your chart).

- **$43.68**, +1.92%, Trend **BULLISH**, RSI 48, range position 56.7% — not extended
- **PIN 45.00**, strongest OI at **$44.60**; **FLIP 34.96**, spot **6.9 ATR above
  the flip** — deep positive gamma, dips bought, rips sold
- Expected move ±7.2% into 9/18 → **$40.53–$46.83**. Max pain $40.00.

**Entry $43.00–43.70** on the trendline hold. **Stop $40.75** under the session
low and the rising line. **Target $44.60 pin, then $46.83.** Invalidation is a
close below $40.75.

### 11. Trigger block (verify prices day-of)

```
trade rule for this post (LONG only)
ticker: SHOO
setup: rising-trendline hold into the 45 pin
trigger: 43.70
stop: 40.75
target: 46.83
status 2026-09-05: LIVE (spot 43.68)
```

---

## PUBLISHING NOTE

`tools/create_draft_from_md.py` **has no paywall support** — it drops the `hr`
and emits no paywall node. **Set the paywall by hand in the Substack editor** at
the `===== PAYWALL BREAK =====` marker, and close the browser tab before any
API write or the autosave will clobber it.

Subtitle is the category mix, e.g. `Tools 50% | Trading 50%`.
Sign-off is exactly `~ Michael`.

---
---

# ADDENDUM — Rise, the shoutouts, and your own MLI paid post

## 1. You already wrote MLI on Substack

**`$MLI: THE COPPER-PLATED COMPOUNDER` — 2025-12-17, `only_paid`.**
https://mphinance.substack.com/p/mli-the-copper-plated-compounder

Published the day after the AfterHour DD post and the same day as the
desert-island "true GARP" post. **This is a gift, not a conflict.** Link it in
the free half and it does three jobs at once: it is a real receipt, it drives
new readers into your paid archive, and it sets up the honest line:

> I wrote the full Mueller thesis for paid subscribers in December, at $113.73.
> Here is the uncomfortable part. From that post to today it has done +13.1%
> while SPY did +14.4%. I did not make money on Mueller by writing about it. I
> made it by finding it thirteen months earlier, in a spreadsheet, when nobody
> was looking. That gap is the entire reason I built the tool.

That paragraph justifies the paywall, sells the archive, and explains TickerTrace
in one move. Put it in section 5.

**Caveat on the archive check:** the Substack archive API only returned 183
posts back to 2025-11-01. SHOO was bought July 2025, before that window, so I
**cannot** rule out an earlier SHOO post. Check before publishing the paid half.

## 2. Rise — ask, do not assert

**Rise (@riseab0v3)** — https://substack.com/@riseab0v3
Founder of Theta Daddies. 94 Substack subscribers. AfterHour `Rise`.

**I could not verify he ever posted about MLI.** I scanned his last 400
AfterHour posts back to 2025-02-25: zero mentions of MLI or Mueller. It may
predate that, it may have been in comments (the archive does not carry comment
bodies), or the memory may be off. **So write it as a question, not a claim.**
That is also the better move socially — a public "hey, did you ever pull the
trigger?" invites a reply and a restack. Asserting he passed on a +63% name and
being wrong does not.

Your own 2025-12-16 post is the hook, and it is already public:

> "@RaceyMcRacerson asked @Rise to review... I forgot to copy the link but go
> check it out. I've held $MLI since finding it in $AVUV back when it was still
> a small cap."

Suggested framing: *Rise got asked to look at Mueller back in December, around
the time I was writing it up. @Rise — did you ever buy it? Genuine question.*

**Why he belongs in this piece at all:** he is all over your archive — 27 posts.
The strongest lines to draw from, all yours:
- "Big thanks to @Rise for letting me steal a couple off his list" (2/13/25)
- "without @Rise I likely wouldn't have had the courage to start wheeling $200
  stocks myself, something I now do daily" (8/4/25)
- "@Rise didn't start wheeling UNTIL he was a millionaire either... He's an
  inspiration to me, and I'll very soon have my Dad's port mirroring his moves."
  (8/16/25)
- "I share @Rise philosophy that I don't mind as much what these stock prices
  return in the short term" (5/17/25)

The Theta Daddies are @Rise, @BobDog, @average_advisor. @RaceyMcRacerson is the
one who asked for the review — worth tagging too, it costs nothing.

## 3. Substack $MLI shoutouts — who else has written it

Search: https://substack.com/search/%24MLI
Screenshot: `substack_search_MLI.png`

Ranked by what they do for you:

1. **The Earnout Investor Club** — *"Lynch's Plumber: A $12 Billion Mid-Cap
   Hiding $1.4 Billion in Cash"*
   https://earnoutinvestor.substack.com/p/lynchs-plumber-a-12-billion-mid-cap
   **Best link on the list.** It frames MLI as a Peter Lynch pick, and you
   opened your 2025-01-19 AfterHour post quoting Lynch — "Invest in what you
   know" and "focus on the companies, not on the stocks" — while teaching your
   kid. That is a genuine thematic rhyme, not a manufactured one.

2. **Beating The Tide** — *"Mueller Industries (MLI): Why 28% Margins Won't Last
   Forever"*
   https://www.beatingthetide.com/p/mueller-industries-mli-deep-dive-stock-analysis-beating-the-tide
   **Link the bear case.** It is the single most credible thing you can do in a
   post about a name you are up 63% on, and it is exactly the "here is who
   disagrees with me" move that earns a restack from someone who is not already
   a fan.

3. **Quality Value Investing** (David J. Waldron) — two separate MLI pieces
   https://davidjwaldron.substack.com/p/mueller-industries-nyse-mli-4ff
   https://davidjwaldron.substack.com/p/mueller-industries-nyse-mli-e49
   Established value writer, has covered it more than once. Good Recommendation
   swap target.

4. **Misfit Alpha** — *"The Misfits: Mueller Industries (MLI)"*
   https://www.misfitalpha.com/p/the-misfits-mueller-industries-mli

5. **Monte Independent Investment Research**
   https://monteinvestments.substack.com/p/research-and-analysis-mueller-industries

Ignore the false positives the search returned: MELI (Mercado Libre), MLM
(multi-level marketing), and a couple of unrelated foreign-language posts.

**How to place them:** a short "other people who did the work on this one" block
at the end of the FREE half, right before the paywall. Three links max — Earnout
Investor, Beating The Tide, Quality Value Investing. Keep the bear case in.
Per your standing play, this is the restack-farming slot.

## 4. FOUND IT — Rise did cover MLI. On YouTube, not AfterHour.

That is why my scan of 400 of his AfterHour posts came up empty.

**"MLI at a glance"** — Theta Daddies, ~170 views, **posted roughly January 2026**
(YouTube reports "8 months ago" as of 2026-09-05; treat the month as approximate).
https://www.youtube.com/watch?v=qtC0eHz_pIU
Channel: https://www.youtube.com/@thetadaddies — **1.69K subscribers**

Confirmed via YouTube's oembed endpoint: title "MLI at a glance #thetagang
#trading #stockmarket #optionstrading #stocktrading #stocks #investing",
author "Theta Daddies".

### The timeline, which is the story

| Date | Who | What | MLI (as seen) |
|---|---|---|---|
| **2024-12-30** | **you** | found it in the AVUV file | **$79.77** |
| 2025-12-16 | you | AfterHour DD post, "@RaceyMcRacerson asked @Rise to review" | $113.73 |
| **2025-12-17** | **you** | **paid Substack: THE COPPER-PLATED COMPOUNDER** | **$112.60** |
| ~2026-01 | **Rise** | **YouTube: "MLI at a glance"** | ~$119.22 |
| 2026-01-15 | — | the run tops out | $130.76 |
| today | — | | $63.74 *(post-split)* |

Returns from each point, split-adjusted and benchmarked:

| From | MLI | SPY | Excess |
|---|---|---|---|
| your find, 12/30/24 | **+63.0%** | +33.2% | **+29.8** |
| your paid post, 12/17/25 | +14.2% | +15.7% | **−1.5** |
| Rise's video, ~1/5/26 | +7.9% | +12.6% | **−4.7** |
| the Jan peak, 1/15/26 | −1.7% | +11.9% | **−13.5** |

**That table is the thesis of the entire article and it is not a dunk on anyone.**
Every one of those people, you included, was right about the business. The only
variable that mattered was *when you saw it*. Thirteen months early: +29.8. One
month late: −4.7. Same company, same thesis, same chart.

Note that MLI split 2-for-1 on 2026-07-01, so the "as seen" prices are pre-split
and the returns are computed on the adjusted series. Both are correct; label them.

### How to write Rise in

Ask, do not assert — you still do not know whether he bought it, only that he
covered it.

> Rise put out an "MLI at a glance" video in January. @Rise — did you ever
> actually pull the trigger on it? Genuine question, and no wrong answer,
> because the point I am making is that I only beat it by finding it a year
> before either of us said a word out loud.

That is generous, it invites a reply, and it makes your own late write-up part
of the joke rather than something you are hiding.

**Links to give him:**
- Substack https://substack.com/@riseab0v3 (94 subs)
- YouTube https://www.youtube.com/@thetadaddies (1.69K subs)
- The video https://www.youtube.com/watch?v=qtC0eHz_pIU

Tag @RaceyMcRacerson too — he is the one who asked for the review in the first
place, and it costs you nothing.

---
---

# FINAL STRUCTURE — the obfuscated-reveal version

## The hook, up top, before anything else

Lead with `reveal_two_stocks.png`. Both curves, both benchmarked, one name shown
and one hidden:

- **MLI, revealed: +63.0%** (SPY +33.2% over the same window)
- **????? , hidden: +77.3%** (SPY +26.1% over its window)

Then the line that makes it work:

> Two stocks, same list, same method. I'm going to give you the whole story on
> the gold one for free — how I found it, when, and what it did. **The green one
> is the better trade and it's still actionable this week.** That one's for paid
> subs, and I'm not going to pretend otherwise.

That is an honest tease. You are showing the bigger number and withholding only
the ticker, which is the opposite of the usual bait. Say the quiet part: *I'm
giving away the second-best one.*

## Then the five beats, in order

**1. Why I do this — AVUV**
The method, in your own words from 2025-07-01: download the holdings file every
few days, ~1/3 of long-term profits came from it. Show
`2025-09-21_scorecard_1.png` (the `AVLV-0918` sheet with the literal share-count
columns). MLI is visible in it at 37.00%.

**2. MLI — the free receipt**
Found **2024-12-30 at $79.77** (pre-split; 2-for-1 on 2026-07-01). Now $63.74.
**+63.0% vs SPY +33.2%, +29.8 points.**
Assets: `MLI_since.png`, `2025-12-16_MLI-dd_1.png`, `mph_substack_MLI_paid.png`.
Link the December paid post — it drives archive signups and it sets up beat 4.

**3. Their part — how the idea travelled**
This is the section that makes the piece generous instead of self-congratulatory:

- You wrote MLI up on AfterHour **2025-12-16**
- **@RaceyMcRacerson** read it and asked **@Rise** to chart it
- Rise runs **TA Tuesday** — request a ticker in the comments, he makes a
  YouTube Short. His words: *"I'll make a quick YouTube short on it for you"*
- He delivered: **"MLI at a glance"**, ~January 2026, ~170 views
  https://www.youtube.com/shorts/qtC0eHz_pIU
- The request thread: https://afterhour.com/Rise/bcO4/ta-tuesday-is-back-make-your-r (12/16, same day as your post) or https://afterhour.com/Rise/beg0/ta-tuesday (1/6)

Assets: `rise_TA-tuesday_2025-12-16.png`, `rise_TA-tuesday_2026-01-06.png`,
`rise_substack_profile.png`.

Credit him properly, from your own archive: *"without @Rise I likely wouldn't
have had the courage to start wheeling $200 stocks myself."* Ask the question,
do not assert: **did you ever buy it?**

Links to give: https://www.youtube.com/@thetadaddies (1.69K subs) and
https://substack.com/@riseab0v3 (94 subs). **Not thetadaddies.ai** — it is a
paid platform with a Trade Journal, Options Screener, Portfolio Tracking and AI
Analysis, i.e. the same shelf as TraderMatrix, and this post's whole job is
sending readers to yours. Credit the people, skip the product page.

**4. The uncomfortable timing — this is the pivot to the tool**

| From | MLI | SPY | Excess |
|---|---|---|---|
| **your find, 12/30/24** | **+63.0%** | +33.2% | **+29.8** |
| your paid post, 12/17/25 | +14.2% | +15.7% | −1.5 |
| Rise's Short, ~1/5/26 | +7.9% | +12.6% | −4.7 |
| the Jan peak, 1/15/26 | −1.7% | +11.9% | −13.5 |

> Everybody in that table was right about Mueller. Me, Rise, the guy who asked
> him to look at it. The only variable that mattered was when. Thirteen months
> early beat the index by 30 points. One month late trailed it. Same company,
> same thesis, same chart.

**5. So I built the thing that finds them earlier**
What the spreadsheet could not do: no history, one fund at a time, cannot
separate real accumulation from a fund-wide inflow day, cannot catch a provider
file refresh, AVUV only.
Assets: `tickertrace_stock_MLI.png`, `tickertrace_fund_AVUV.png`,
`tickertrace_home.png`. Links in the earlier section. Close on TraderMatrix.

## ===== PAYWALL =====

**6. The green line is Steven Madden.** Everything from the earlier PAID section
— bought 2025-07-01 at $24.64, now $43.68, +77.3% vs SPY +26.1%, **+51.2 points**.
Back on the list right now (Accumulating, 4 funds, AVUV 292,425 → 375,603 in a
week, 96.6th percentile). The five checks. The setup: entry $43.00–43.70, stop
$40.75, targets $44.60 pin then $46.83.

Assets: `SHOO_since.png`, `mph_SHOO_chart_2026-09-05.png`,
`tickertrace_stock_SHOO.png`, `2025-07-02_SHOO_1.png`.

## Asset manifest — `/tmp/ah_media/`

**Free half:** `reveal_two_stocks.png` (hero) · `2025-09-21_scorecard_1.png` ·
`MLI_since.png` · `2025-12-16_MLI-dd_1.png` · `mph_substack_MLI_paid.png` ·
`rise_TA-tuesday_2025-12-16.png` · `rise_TA-tuesday_2026-01-06.png` ·
`rise_substack_profile.png` · `tickertrace_stock_MLI.png` ·
`tickertrace_fund_AVUV.png` · `tickertrace_home.png` · `substack_search_MLI.png`

**Paid half:** `SHOO_since.png` · `mph_SHOO_chart_2026-09-05.png` ·
`tickertrace_stock_SHOO.png` · `2025-07-02_SHOO_1.png` · `2025-07-05_port_1-3.png`

**Do not use above the paywall:** anything with SHOO visible.

---
---

# LOCKED OUTLINE + PICTURE LIST (this supersedes everything above)

Change per mph: **cut the "since my paid post" and "since Rise's Short" return
rows entirely.** Rise's was a reader request, scoring it is unfair and off-point.
The only return that appears is **since my first one, 2024-12-30**. The lead time
is the argument, not a comparison to anybody.

## Title
`TWO STOCKS, ONE SPREADSHEET`
Subtitle: `Tools 40% | Trading 40% | Process 20%`

## FREE HALF

| # | Beat | Picture |
|---|---|---|
| 1 | **The hook.** Both curves, one name hidden. I'm giving away the second-best one. | `reveal_two_stocks.png` |
| 2 | **Why I do this.** The AVUV holdings file, every few days, for years. | `2025-09-21_scorecard_1.png` (the AVLV sheet, MLI visible at 37.00%) |
| 3 | **MLI, the free one.** Found 2024-12-30 at $79.77. Now $63.74. **+63.0% vs SPY +33.2%.** | `MLI_since.png` |
| 4 | **Their part.** I wrote it up 12/16. Racey asked Rise to chart it. Rise runs TA Tuesday and made the Short. The idea travelled. | `rise_TA-tuesday_2025-12-16.png` |
| 5 | **The lead time is the whole point.** Thirteen months between the spreadsheet and the write-up. | `2025-12-16_MLI-dd_1.png` (your TradingView at $114.03) |
| 6 | **So I built the thing.** What the spreadsheet couldn't do. TickerTrace. | `tickertrace_fund_AVUV.png` |
| 7 | **CTA.** MLI in TraderMatrix, live. | `tradermatrix_MLI.png` |

## ===== PAYWALL HERE =====

## PAID HALF

| # | Beat | Picture |
|---|---|---|
| 8 | **The green line is SHOO.** Bought 2025-07-01 at $24.64. Now $43.68. **+77.3% vs SPY +26.1%.** | `2025-07-02_SHOO_1.png` (the original post) |
| 9 | **It's back on the list.** Accumulating, 4 funds, AVUV 292,425 → 375,603 in a week, 96.6th percentile. | `tickertrace_stock_SHOO.png` |
| 10 | **The five checks.** Swing low / coverage / PEG / tradeable / percentile-in-fund. | — |
| 11 | **The setup.** Entry, stop, target, trigger block. | `mph_SHOO_chart_2026-09-05.png` |

## Cut from the picture list
`SHOO_since.png` (redundant with the hero, and it names the ticker),
`mph_substack_MLI_paid.png` (link it instead of showing it),
`tickertrace_home.png`, `substack_search_MLI.png`, the desert-island shots,
the port shots. Twelve images is a slideshow, seven is a post.

## Numbers appearing in the piece, all verified 2026-09-05
- MLI: found 2024-12-30 **$79.77** (pre-split; 2:1 on 2026-07-01) → **$63.74**,
  **+63.0%**, SPY **+33.2%**, **+29.8 pts**
- SHOO: bought 2025-07-01 **$24.64** → **$43.68**, **+77.3%**, SPY **+26.1%**,
  **+51.2 pts**
- AVUV on SHOO: 292,425 → 375,603 shares in a week, **+28.4%**, 96.6th percentile
- SHOO fundamentals: coverage 26.1, D/E 0.13, rev +18.2%, EPS +57%, GM 46.1%,
  fwd P/E 19.4, PEG ~1.07, IV rank ~0
- SHOO levels: spot 43.68, pin 45.00 / strongest OI 44.60, flip 34.96,
  expected move ±7.2% to 9/18, max pain 40.00
- MLI in TraderMatrix: spot 63.74, pin 67.50 (492 OI), gamma flip 51.52, ER Oct 27
