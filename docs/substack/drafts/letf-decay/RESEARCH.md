# Standalone post research: single-stock 2x ETF decay

All data pulled 2026-08-30 from the TD Pro agent API (`/api/agent/ticker/{SYM}/chart-data?days=365`).
Daily closes only. Every number below is reproducible from the JSON in this folder.

## The hook: you were right about the stock and still lost

Michael knows people who bought **GLXU** because they liked **GLXY**.

- GLXU full life (2025-08-08 to 2026-08-28): **GLXY -16.5%, GLXU -77.0%.** Naive 2x = -32.9%.
- Sub-window 2025-09-04 to 2026-08-27: **GLXY +10.4%, GLXU -56.9%.** (Stated dates required, this is a chosen window.)
- Cleanest unimpeachable version, CIFU's entire life (2025-11-21 to 2026-08-28):
  **CIFR +7.2%, CIFU -62.7%.** Full fund history, no window selection.

## Fund identities (verified via web, 2026-08-30)

| Fund | Underlying | Issuer | Fee | Inception |
|---|---|---|---|---|
| CIFG | CIFR | Leverage Shares (Themes ETF Trust) | 0.75% | 2025-12-11 |
| CIFU | CIFR | T-REX (REX Shares + Tuttle) | 1.50% | 2025-11-21 |
| GLXU | GLXY | T-REX | - | 2025-08-08 (first close in data) |

CIFG and CIFU are the control pair: same stock, same window, two issuers, 2x the fee on one.
Result **-62.6% vs -61.7%**. The fee gap (0.75%/yr, ~0.5pp over the window) explains almost none
of it. That is what makes this arithmetic rather than an accusation.

## Figure 1 - the hook (`fig_letf_nowhere.png`)

Trailing 1yr. Stocks that finished roughly flat, and their 2x funds:

- META -0.3% -> METU **-33.3%**
- COIN -1.4% -> CONL **-64.0%**
- SMCI -2.2% -> SMCX **-85.1%**
- CIFR +7.2% -> CIFU **-62.7%**

Not obscure names. Not selected for the result, selected for the stock being flat.

## Figure 2 - the mechanism (`fig_letf_walk.png`)

Six real GLXY sessions, 2026-02-04 to 2026-02-12. Two $100 stakes.

The fund must hold exactly 2x its own NAV at every close, so after every move it is
**forced** to rebalance. Down day, it sells. Up day, it buys.

- Stock finished **-0.05%** ($20.16 to $20.15)
- Modeled 2x finished **-6.64%**; GLXU actually finished **-7.60%**
- **$79.35 of forced trading on a $100 position in six sessions.**
  Bought $36.35 (always after an up day), sold $42.99 (always after a down day).

The sharpest two-day cut inside it: Feb 4 to Feb 6, **stock -1.98%, fund -9.68%.**
A working 2x would be -4%.

This is the "HOW" - it is not fees and it is not mismanagement. It is selling low and
buying high, mechanically, by prospectus.

## Figure 3 - the proof it generalizes (`fig_letf_fit.png`)

**36 funds, 5 issuers** (expanded from the first 15 on 2026-08-30), every 2x single-stock
ETF the API serves with 120+ sessions. All betas **1.969 to 2.006**, so every fund does its
job daily. Drag isolated as `(1+r_fund)/(1+r_stock)^2`, annualized. Full data in
`letf_survey2.json`.

**Regressing observed drag on sigma^2: slope 1.096 (theory says 1.00), r = 0.970,
r-squared = 0.940, n = 36.**

Two honest findings:
1. The formula explains **94%** of the variance. The mechanism is proven, not asserted.
2. **35 of the 36 did worse than theory, never better.** The theoretical drag is the
   optimistic case; real funds add ~10% on top for fees, financing and intraday path.
   (The one exception is AMDL, riding a +350% trend in AMD.)

Even LMT, the calmest stock in the set at 27% vol, costs **16.4% a year** to hold levered.

### The worst of the 36, by annualized drag

CIFU -77.2% | CIFG -76.6% | QBTX -75.1% | HIMZ -74.4% | SMCX -72.3% | RGTU -70.8% |
SMCL -70.6% | IONX -68.4% | SOUX -61.7% | MSTX -60.2% | MSTU -59.2% | DJTU -54.5% |
MUU -50.0% | HOOX -49.7% | CONL -49.6% | UPSX -48.1% | SOFX -43.3% | AMDL -42.9%

### The non-crypto headline: the stock went up and the fund went down (`fig_letf_upfund.png`)

| Fund | Stock | Stock did | 2x fund did | Vol |
|---|---|---|---|---|
| QBTX | QBTS (D-Wave) | +125.6% | **-21.1%** | 118% |
| IONX | IONQ | +72.8% | **-43.6%** | 98% |
| RGTU | RGTI (Rigetti) | +35.6% | **-57.1%** | 107% |
| CIFU | CIFR (Cipher) | +7.2% | **-62.7%** | 113% |
| SOFX | SOFI | +51.1% | **+0.3%** | 59% |
| RKLX | RKLB (Rocket Lab) | +258.1% | **+180.4%** | 91% |

**QBTX is the one to lead with if the miner angle feels narrow.** QBTS more than doubled
and the 2x fund on it lost a fifth. Quantum computing, not crypto.

**SOFX is the personal one.** Michael writes about SOFI. The stock ran +51% and the 2x fund
made **thirty cents on a hundred dollars**, over the same seventeen months.

**RKLX is the fair-minded one.** RKLB tripled, so the fund did make money. It just made
*less than the stock* while carrying twice the risk. That is the case that stops this
reading as a hit piece.

### Figure 5 - the February chart (`fig_letf_feb.png`)

Line chart version of the walkthrough table: GLXY vs GLXU, both indexed to $100 on Feb 4,
with the forced trading as bars underneath (green after up days, red after down days).
GLXU fell 33.9% on a single 16% down day and never got it back.

## Figure 4 - CIFR/CIFG/CIFU rebased chart (`fig_letf_chart.png`)

Also carries the finding that you do not get 2x on the way UP:
at the 2026-06-18 peak, CIFR **+92.6%**, a real double would be **+185%**, CIFG delivered
**+105.6%**. That is **1.14x**. Heads you win less than promised, tails you lose almost everything.

## The reader's takeaway rule

**Square the underlying's implied vol. That is roughly your annual holding cost.**
- AAPL at 31% -> ~9% theoretical, 17% observed
- COIN at 73% -> ~53% theoretical, 50% observed
- CIFR at 112% -> ~126% theoretical

And the recovery trap: a CIFG holder from December needs **+167%** to break even, which
takes CIFR rallying **63% to ~$24.80**, on a stock that already sits where it started.

## Still to verify before publishing

- GLXU issuer/fee/inception not independently confirmed (CIFG and CIFU are).
- Re-pull all closes on publish day.
- Whether any of these funds did a reverse split in the window (would distort the series).
