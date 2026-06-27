# NBIX — Single-Ticker Intel Sheet (TraderDaddy Pro MCP)

**Neurocrine Biosciences** · spot **$158.29** · snapshot 2026-06-21 (market closed, weekend)

This is a rundown of *everything the MCP can tell you about one ticker*, run live on NBIX.
Tools split into two buckets: **structural** (populated 24/7) and **live-market** (need an open tape).

---

## 1. Dealer Gamma Positioning — `get_gex_ticker`  ★ the richest one

| Field | Value | Read |
|---|---|---|
| Spot | $158.29 | — |
| Regime | **Negative Gamma** | dealers *amplify* moves — this is a trender, not a pinner |
| Total GEX | −$4,330 (≈ flat) | razor-thin / net-neutral — a low-gamma air pocket |
| Gamma flip | $137.36 | spot is 13.2% **above** it — the floor where things would get reflexive |
| Max-gamma strike | $145 | the heaviest OI shelf, sitting *below* price |
| Put/Call GEX ratio | 1.006 | balanced book |

**Key levels (net-GEX walls):**

| Strike | Net GEX | Type | Note |
|---|---|---|---|
| **$170** | +127.8K | resistance | call ceiling — 323 call OI, **zero puts**. The wall above. |
| $160 | −51.0K | resistance | first cap overhead (991 put OI) |
| **$155** | +44.1K | support | nearest shelf below spot |
| $145 | −128.4K | support | **biggest put wall** (939 put OI) — the real floor |
| $140 | −76.5K | support | secondary floor |

**The picture:** NBIX is floating in a thin-gamma pocket between **$155 support and $160 resistance**,
with a hard call ceiling at **$170** and a put-stuffed floor at **$145**. Because net gamma is
basically zero / short, dealers won't dampen moves — a push through $160 can *accelerate* toward
$170 rather than mean-revert. Opposite behavior to a positive-gamma index pin.

> **Contrast:** SPX earlier today = +$10.4B gamma, pinned at 7500 (mean-revert, fade the edges).
> NBIX = ~$0 gamma, above its flip (momentum, ride the break). Same tool, opposite playbook.

---

## 2. Unusual Options Flow — `get_unusual_activity`

```
ticker NBIX → 0 trades (market closed)
```
**Live-market tool.** During the session this surfaces large/anomalous sweeps & blocks scored for
unusualness (vol vs OI, premium size, sweep/block, bid/ask aggression) with a bull/bear tag —
"what's the smart money doing in NBIX." Empty on a weekend by design.

## 3. Put/Call Ratio — `get_put_call_ratios`

```
NBIX → ratio 0.0 (nearest weekly Jun 26; putVol 0 / callVol 0)
```
**Live-market tool.** Computes put÷call volume off the live Tradier chain for the nearest weekly.
Zero now (no volume on a closed tape). Intraday it's a fast sentiment gauge.

## 4. Earnings Positioning — `get_earnings_flow`

```
NBIX not present in the next 21 days
```
**No near-term earnings catalyst.** So any NBIX trade here is a *technical / positioning* play, not
an event play — no expected-move landmine to step on inside 3 weeks. (The tool *does* light up for
names that report soon — e.g. CCL on 2026-06-23 shows expected move 6.71%, $1.23M pre-earnings
premium, mixed sentiment — that's the kind of context you'd get if NBIX were on the docket.)

---

## What the MCP gives you for ONE ticker — the menu

| Tool | Scope | NBIX result | When it's live |
|---|---|---|---|
| `get_gex_ticker` | ticker | ✅ full gamma map | **24/7** (computed on demand) |
| `get_unusual_activity` | ticker | empty (closed) | market hours |
| `get_put_call_ratios` | ticker | 0 (closed) | market hours |
| `get_earnings_flow` | scan | not reporting <21d | always |
| `run_screener` | scan | (check membership) | always |
| `get_sector_flow` | sector | healthcare context | market hours |
| `get_economic_calendar` | macro | week's catalysts | always |

**Bottom line on NBIX right now:** clean technical setup, no earnings risk inside 3 weeks, sitting in
a low-gamma pocket between $155 and $160. The trade the structure implies: **$160 is the trigger** —
above it, negative gamma lets it run at the $170 call wall; the $145 put shelf is the line that
says you're wrong. Confirm with live flow + put/call once the tape opens Monday.
