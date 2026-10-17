# Helios re-leasing risk if CoreWeave defaults (2026-10-17)

## Verdict

**Moderate, not existential. Energized, rent-paying Phase I is the easiest 133 MW in America to re-let; unbuilt Phases II–III are the real exposure.**

- **Time-to-re-lease (Phase I):** 3–9 months to LOI, 6–15 to signed lease. Fits the indenture's 6/12-month cure window, without much margin.
- **Phases II–III:** 12–24+ months; the market is buying 2026–27 power and Galaxy's own 830 MW has sat unleased 9 months. A CRWV rejection would hit these unbuilt, executory leases first.
- **Rent haircut:** 10–30% on Phase I ($2.41M → ~$1.7–2.2M per critical MW-yr) to match peer miner-to-AI leases; 40–50% if a hyperscaler takes powered shell on AWS/Cipher terms. Phase II ($2.17M) has less to give back.
- **Most likely CRWV Ch. 11 outcome:** Phase I is assumed, not rejected: it earns money, the GPUs are lender collateral in bankruptcy-remote SPVs, and the end customer is (per Galaxy) a "multi-trillion dollar investment-grade public company."

## 1. Market backdrop (favors the landlord)

- CBRE H1 2026: vacancy **1.4%** (record low); >80% of construction preleased; **<1,500 MW** left to prelease in North America; 10+ MW rents +6.7%. https://www.cbre.com/insights/books/north-america-data-center-trends-h1-2026
- JLL midyear 2026: 25 GW absorbed (2x YoY); hyperscalers 59% of demand, neoclouds 11%; 66 GW under construction, 95% pre-committed; vacancy ~1% through 2028. https://www.datacenterdynamics.com/en/news/jll-data-center-demand-exceeds-expectations-doubles-year-over-year/
- **West Texas is not a discount location for training.** Cushman 2026: #1 tertiary market, **2.9 GW under construction** (more than all EMEA). https://propmodo.com/why-the-worlds-top-data-center-market-is-now-in-texas/ Hyperscalers lease there directly: MSFT took **700 MW at Crusoe/Abilene** after Oracle/OpenAI walked https://www.bloomberg.com/news/articles/2026-03-24/microsoft-to-rent-texas-data-center-dropped-by-oracle-openai ; MSFT $9.7B/200 MW at IREN Childress (~70 mi from Dickens), liquid-cooled, first hall accepted https://www.datacenterdynamics.com/en/news/iren-delivers-first-phase-of-ai-capacity-to-microsoft-in-texas/ ; AWS 15-yr $5.5B/300 MW with Cipher https://www.theenergymag.com/news/2025-11-03/cipher-amazon-ai-bitcoin ; Google-backstopped Fluidstack at Cipher Barber Lake (300 MW, Colorado City TX) https://investors.cipherdigital.com/news-releases/news-release-details/cipher-mining-signs-168-mw-10-year-ai-hosting-agreement/
- Negatives: SB6 emergency curtailment for >75 MW loads (ERCOT workshop 10/6/26) https://www.ercot.com/files/docs/2026/09/01/Agenda-SB6-Large-Load-Curtailment-Proposed-Operations-Framework-and-Registration-Workshop.docx ; Abbott audit (prior report). Latency only matters for inference tenants.

## 2. Re-tenanting precedents (no neocloud has failed yet)

| Case | Gap | Terms |
|---|---|---|
| Core Scientific: Ch.11 exit 1/23/24 → CRWV 16 MW (3/24), 200 MW (6/3/24) | 2–4.5 mo | $3.5B/200 MW/12 yr ≈ $1.46M/MW-yr https://businesswire.com/news/home/20240603752657/en/ |
| Crusoe Abilene: Oracle/OpenAI walk → MSFT 700 MW | weeks–months (3/2026) | undisclosed |
| MSFT drops CRWV capacity → OpenAI $11.9B (3/2025) | weeks | https://www.theblock.co/post/345670/coreweave-ai-infrastructure-deal-sam-altman-openai |
| APLD Ellendale: greenfield, 2023 → CRWV 5/28/25 | ~2 yrs | $11B/400 MW/15 yr ≈ $1.83M/MW-yr https://seekingalpha.com/news/4490437-applied-digital-rises-on-additional-150mw-lease-with-coreweave-in-north-dakota |
| TeraWulf–Fluidstack, Google backstop | n/a | $3.7B/200 MW/10 yr ≈ $1.85M/MW-yr https://www.tipranks.com/news/the-fly/google-to-backstop-1-8b-fluidstack-lease-obligation-to-support-terrawulf-deal-thefly |
| Cipher–Fluidstack, Google backstop | n/a | $3B/168 MW/10 yr ≈ $1.79M/MW-yr |
| Cipher–AWS | n/a | ≈ $1.22M/MW-yr (scope UNVERIFIED) |

Galaxy's $2.17–2.41M/MW-yr sits **15–40% above every peer**; that is the CRWV credit premium an IG replacement would price out. (Per-MW rents are my arithmetic on headline TCVs.)

**Key precedent, APLD 3/30/26:** CRWV paused two Ellendale halls, re-let them to **CoreWeave Compute Acquisition Co. VIII (SPV)** whose debt is rated **A3**, with a parent springing guaranty and a **$50M LC**, "substantially the same terms." https://ir.applieddigital.com/sec-filings/all-sec-filings/content/0001493152-26-014498/form8-ka.htm That is the template for a stressed CRWV keeping landlords whole. Galaxy's lease was amended 1/21/26 and 6/3/26; whether Phase I moved into an SPV is **UNVERIFIED** and the best Q3-call question.

## 3. End customer, Ch. 11 mechanics, the GPUs

- Galaxy Q1 call: Phase I GPUs serve a "multi-trillion dollar investment-grade public company"; unnamed (press infers MSFT). https://www.theenergymag.com/news/2026-04-29/galaxy-microsoft-helios-ai
- CRWV Q2 10-Q: Customer A 36% of revenue (71% a year ago), B 26%, C 10%; RPO **$103.7B**. https://www.sec.gov/Archives/edgar/data/1769628/000176962826000366/crwv-20260630.htm MSFT dependence is no longer the story.
- Ch. 11: nonresidential leases assumed/rejected within 120 days (+90; beyond that only with landlord consent), §365(d)(4) https://restructuring.weil.com/?p=10653 . Debtors assume contracts that make money; Phase I qualifies. Rejection damages are capped (greater of 1 yr or 15% of remaining rent, ≤3 yrs, §502(b)(6)); Galaxy's protection is the building, not the claim.
- GPUs: owned by CRWV SPVs, pledged to DDTL lenders (A3-rated, bankruptcy-remote). https://www.useluminix.com/reports/industry-analysis/who-is-financing-the-ai-buildout/source/4 (secondary). Lenders want clusters running in place, which aligns them with Galaxy; the end customer could buy compute from a successor operator without moving a rack.

## 4. Other bidders for Helios

- Q2 call, Novogratz: 830 MW "remains unleased," talks "in early stages" with "every flavor of potential tenant, including hyperscalers, neoclouds, and labs"; gating factor is Helios II energization in **late 2028** vs tenants chasing 2026 power; watching "guarantee and lease wrap structures from larger credit counterparties." https://www.gurufocus.com/news/9007532/galaxy-digital-inc-glxy-q2-2026-earnings-call-highlights-data-center-expansion-drives-growth-amid-crypto-volatility
- No tenant announced 8/15–10/17 (prior report); no sell-side note found that models re-leasing explicitly.
- Read-through: 830 MW unleased for 9 months says 2028 power is not scarce, not that 2026-energized Phase I would sit idle. Different product.

## 5. Bear counter-case

- Gartner 10/14/26: >80% of neoclouds gone independent by 2030; >$3.5T AI infra "exposed to impairment." https://www.gartner.com/en/newsroom/press-releases/2026-10-14-gartner-says-over-us-dollars-three-and-a-half-trillion-of-artificial-intelligence-infrastructure-spending-could-be-exposed-to-impairment-by-the-end-of-2030 CRWV 2032s ~15% YTM, CDS ~1,117 bp (secondary). https://www.roic.ai/news/ai-neocloud-stocks-slide-as-financing-fears-mount-10-15-2026
- GPU rental: H100 median ~$4.20/hr (Oct 2026), marketplace $1.80–3.50; down sharply from 2024. https://uvik.net/blog/gpu-price-index/ (vendor index). Falling compute prices squeeze neoclouds before landlords.
- Spec: 130–140 kW racks, direct liquid cooling (directory listing, UNVERIFIED) https://www.datacentermap.com/usa/texas/dickens/helios-data-center/ . That is now hyperscaler standard (IREN Childress is DLC for MSFT); the building is not stranded by spec, though a tenant wanting Rubin-era 600 kW racks may demand retrofits.
- Correlation risk: a CRWV failure arrives with wider neocloud distress and a sublease-GPU glut, cutting tenant urgency; that pushes timelines to the long end of the ranges.

## Open / UNVERIFIED
Phase I SPV assignment / LC; termination fee; Cipher–AWS site/scope; Helios cooling spec; assignability of the IG end-customer contract.
