# AI-datacenter landlords vs. tenants: who's actually exposed to CoreWeave

*Research snapshot, 2026-10-19 after the close. Built from 5 research agents (IR releases, SEC filings, credit press, live TMPro data) plus the 10/17 GLXY research in this folder. Anything marked UNVERIFIED is just that. Not advice.*

## Why the whole group is down

Starting 10/13, CRWV's credit cracked in public:
- **Bonds:** the 9.625% 2032s hit a record ~14.5% yield, and the 9% 2031s traded at 76.5–81 cents (14.8–15.8% YTM).
- **CDS:** 5-year CDS spiked to a record 1,088–1,194bp, up from ~452bp in June. That implies roughly 63% odds of default over 5 years.
- **Macro:** a hot CPI print on 10/14 sent the 10Y above 5.3%.
- **Gartner:** a note said ~80% of neoclouds are gone by 2030 and named CRWV the most exposed.
- **Pushback:** JPMorgan and Jefferies called the move overdone on 10/16. The stock still finished the week down ~20%.

There was no rating action in October.

**The real contagion channel is financing, not tenancy.** Every landlord below funds its buildout with converts, secured notes, ATMs and GPU debt. When the sector's flagship borrower trades like distressed credit, everyone's cost of capital reprices at once. So names with zero CRWV revenue fell anyway.

## The map

| Landlord | Who pays the rent | CRWV share of AI book | Backstop on the lease | AI revenue live? | Next earnings |
|---|---|---|---|---|---|
| **GLXY** | CoreWeave only (Helios: 133MW live, 260MW Ph II H1-27, ~393MW+ optioned) | **~100%** | None disclosed (UNVERIFIED) | Ph I yes, since ~Jul-26 | **Oct 27, before the open (confirmed)** |
| **CORZ** | CoreWeave only (~500MW, 12yr, ~$8.7B) | **~100% of hosting** (~77% of total revenue, UNVERIFIED) | None disclosed; CORZ holds liens on the infrastructure | ~245MW live, ~200MW imminent | **Nov 5, before the open (confirmed)** |
| **APLD** | CoreWeave (400MW, ~$11B) + unnamed IG hyperscaler (200MW, ~$5B) + Delta Forge 2 (210MW, ~$5.2B) | **~31% of a ~$36B backlog** | **CRWV parent guaranty + $50M LC** on the restructured halls (A3-rated SPV) | 250MW live | Q2 FY27 UNVERIFIED (~Jan) |
| **CIFR** | AWS direct (300MW + 70MW Stingray, ~$5.5B) + Fluidstack (168MW, ~$3B) | **0%** | Google backs **$1.4B** of Fluidstack's lease (Google holds ~5.4% via warrants). AWS lease has no backstop. | **No.** 100% of revenue is still bitcoin. | UNVERIFIED (~Nov 2–11) |
| **WULF** | Fluidstack (>200MW, $3.7B) + **Anthropic direct** (401MW Hawesville KY, 20yr, ~$19B) | **0%** | Google backs Fluidstack for up to $3.2B (~8–14% stake). Anthropic is not Google-backed. | 102MW live; Anthropic starts H2-27 | UNVERIFIED (~Nov 4–15) |
| **IREN** | Microsoft (5yr, ~$9.7B, 20% prepaid) + 10 named AI cloud customers + unnamed frontier lab (reported to be **Anthropic**, UNVERIFIED) | **0%** | n/a. IREN is a GPU cloud **operator**, not just a landlord. | Yes; AI cloud passed mining in Q4 FY26 | UNVERIFIED (~Nov 5) |
| **NBIS** | Microsoft (~$17B, 5yr) + **Meta (up to $27B)** | **0%** (a CRWV competitor, not a counterparty) | ~60% funded by customer prepayments | Yes | UNVERIFIED |
| **HUT** | Unnamed IG tenant (Beacon Point 352MW, 15yr, $9.8B) + Fluidstack→Anthropic at River Bend (Google-backed, BBB- bond) | **0%** | Google, via Fluidstack | Ramping | not checked |

## Checking the Discord claims

- **"CRWV is GLXY's largest tenant": understated.** CRWV is GLXY's **only** AI tenant. Helios II (830MW) was still unleased as of the Q2 call.
- **"CRWV is a large APLD customer": true but shrinking.** It's ~31% of backlog now. APLD also has the best protection in the group, a CoreWeave parent guaranty plus a $50M letter of credit.
- **"CORZ tied in tightly with CRWV": true.** It's the most concentrated name after GLXY. CoreWeave's bid to acquire CORZ was voted down by CORZ shareholders on 10/30/25, so CRWV is a customer, not the parent.
- **"CIFR has AMZN and GOOGL": true.** AWS is a direct tenant, and Google guarantees $1.4B of the Fluidstack lease. The catch is that **none of it is on the income statement yet**: Q2 revenue was 100% bitcoin.
- **"IREN has MSFT and NVDA, rumors of Anthropic": true, and the rumor is credible.** The Information reported it on 10/11. Neither company has confirmed.
- **"WULF has Anthropic and Google": true but separate.** Google backs the Fluidstack lease. The Anthropic lease is direct and not Google-backed, and it doesn't pay until H2-2027.
- **"NBIS has MSFT and META": true.** Meta's deal grew to as much as $27B.
- **"GLXY on the 200-week MA": not possible.** GLXY has only been listed on Nasdaq since May 2025.
- **"Institutions loading up before earnings": no evidence.** There were zero dark-pool blocks on GLXY or CRWV in 10 sessions.

## What would happen to each landlord if CRWV restructured

- **Built, energized halls get kept.** Bankruptcy precedent from CORZ and APLD is that a debtor keeps money-making leases. A rejected energized hall re-lets in about 2–4.5 months at comparable $/MW (CBRE vacancy is under 1.4%), and §502(b)(6) caps the damages on rejected leases.
- **The real risk is the unbuilt phases.** GLXY Phase II/III and the CORZ options still under construction are executory contracts. If CRWV rejects them before they're energized, that's 12–24+ months of re-leasing risk on capex the landlord already spent.
- **Ranking by downside:** GLXY (100% CRWV, big unbuilt phases, no disclosed guaranty) > CORZ (100% CRWV, but direct liens and more built) > APLD (parent guaranty plus diversification) >> CIFR / WULF / IREN / NBIS / HUT. The last five have no CRWV revenue. Their risk is **financing and execution**, not tenant default.

## What this means for the wheel

1. **The "zero CRWV" names are a financing-cost trade, not a tenant-credit trade.** They bounce when CRWV bonds and CDS stabilize, not when someone points out their tenants are Amazon and Microsoft. Watch CRWV's 2031/2032 bond prices; that's the tell for the whole group.
2. **Earnings season sits right in this window.** GLXY reports 10/27 and CORZ 11/5 (both confirmed), and the rest probably fall in the first half of November. Any put expiring after a report is an earnings bet. Confirm each date before choosing an expiry.
3. **Cleanest credit in the group:** IREN and NBIS (investment-grade customers, revenue already flowing) and APLD (guaranty plus diversification).
   - **CIFR** has great tenants but no AI revenue yet, so it's an execution bet.
   - **WULF**'s Anthropic lease is big, but its cash flow arrives in 2027 while its converts mature in 2030–31.
   - **GLXY** and **CORZ** are the pure CRWV-credit bets.

## Open questions

- Does GLXY's Helios lease carry a CRWV parent guaranty or an SPV structure like APLD's? This is the best question for the 10/27 call.
- Is CORZ's CRWV revenue lockboxed to its $3.3B notes?
- Exact earnings dates for CIFR, WULF, IREN and NBIS.
- Which of CRWV's anonymized Customers A, B and C (36%, 26% and 10% of revenue) are Microsoft, OpenAI and Meta.

Sources: GLXY 10-Q (6/30/26) and the [10/13/26 earnings-date release](https://finviz.com/news/402092/galaxy-schedules-webcast-and-investor-call-to-review-third-quarter-2026-results-on-october-27-2026); CORZ 8-K (notes, 4/22/26) and 10/15/26 earnings-date PR; [CORZ/CRWV deal termination](https://www.businesswire.com/news/home/20251030641010/en/); APLD 8-K/A (Mar-26 restructuring) and FQ1 FY27 release; CIFR 8-Ks (AWS, Fluidstack/Google); WULF 8-K/10-Q; IREN FY26 release and 7/20/26 contracts release; [CNBC 10/14](https://www.cnbc.com/2026/10/14/coreweave-stock-bond-yields-ai-debt.html) and [10/16](https://www.cnbc.com/2026/10/16/coreweave-stock-selloff-analysts.html) on CRWV credit; [DCD on APLD's hyperscaler lease](https://datacenterdynamics.com/en/news/applied-digital-secures-5bn-15-year-lease-with-hyperscaler-at-north-dakota-data-center-campus/); TMPro live data 10/19.
