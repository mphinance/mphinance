# 🎯 0DTE Day Trading Flow — Round 1

> **For Michael's Monday morning session.**
> Ghost Alpha signals → Tradier XSP 0DTE options → Same-day close.
> **Authors:** Claude + Gemini (collaborative design)

---

## Why XSP

`TRADING_AGENT_PROMPT.md` spec'd this from the start. XSP (Mini-SPX Index) is:
- **1/10th of SPX** — cheaper contracts, perfect for a $75 account
- **Cash-settled** — no assignment risk, European-style
- **0DTE available M/W/F** on Tradier (standard index options)

| | SPY | XSP |
|---|---|---|
| Price | ~$672 | ~$674 |
| Style | American (assignment risk) | **European (cash-settled)** |
| 0DTE 2-3 OTM | $0.40–$0.80 | **$0.15–$0.50** |

> **Fallback:** If XSP chain isn't available on Tradier or L2 options aren't active, fall back to SPY 5+ OTM ($0.10–$0.30).

---

## The Flow

```
 SIGNAL          ENTRY              MANAGE              EXIT
┌──────┐    ┌──────────┐    ┌─────────────────┐    ┌──────────┐
│Ghost │    │BTO 0DTE  │    │IFTTT cascade    │    │STC by    │
│Alpha │───→│XSP 2-3   │───→│(8 rules below)  │───→│2:30 PM   │
│A+/A  │    │OTM       │    │check every 30s  │    │MANDATORY │
└──────┘    └──────────┘    └─────────────────┘    └──────────┘
```

---

## Position Sizing — Two Shots on $75

| Rule | Value |
|------|-------|
| Max per trade | **$30** |
| Buffer | **$10** |
| Available capital | $75 - $10 = **$65** |
| Trades per day | **2 sequential** (not concurrent) |
| Strike selection | **2–3 OTM** ($0.15–$0.50/contract) |
| Max daily loss | **$60** (2 full losers = walk away) |

---

## IFTTT Rules (Cascading — First Match Wins)

### ENTER IF:

```
Ghost Alpha Grade ≥ B on SPY 5min
AND signal = mega_bull OR mega_bear
AND RVOL > 1.2
AND time 9:30–11:30 AM ET
AND trend_age < 15 bars
AND no open 0DTE position
```

### EXIT — Priority Order:

| # | Type | IF | THEN |
|---|------|-----|------|
| S1 | 🔴 Hard Stop | Loss ≥ **-50%** | **SELL** — non-negotiable |
| S2 | 🔴 Grade Death | Grade drops to **D or F** | **SELL** — thesis dead |
| S3 | 🔴 Reversal | Signal flips bull↔bear | **SELL** — wrong side |
| T1 | ⏰ EOD | Time ≥ **2:30 PM ET** | **SELL** — theta cliff |
| P1 | 🟢 Double | Gain ≥ **+100%** | **SELL** — take the W |
| P2 | 🟢 Fading Edge | Gain ≥ +30% AND Grade → C | **SELL** — lock profit |
| P3 | 🟢 Afternoon | Gain ≥ +50% AND time > 1 PM | **SELL** — theta eating you |
| T2 | ⏰ Dead Money | Time ≥ 12 PM AND position ±10% | **SELL** — free up for trade 2 |

### RE-ENTRY:

| # | IF | THEN |
|---|-----|------|
| R1 | Trade 1 closed + buying power ≥ $20 + new A+/A signal | Enter Trade 2 |
| R2 | 2 losers today | **DONE. Walk away.** |

---

## Risk Guardrails (NON-NEGOTIABLE)

| Rule | Value |
|------|-------|
| Max per trade | $30 |
| Max daily loss | $60 (2 losers = done) |
| Max open positions | 1 at a time |
| Auto-close time | 2:30 PM ET |
| No averaging down | EVER |
| Grade minimum | B (3.0/5) |
| Trading window | 9:30–11:30 AM ET entries only |
| Friday 0DTE | NO (triple witching risk) |

---

## Tradier API — XSP Option Orders

### Get Today's 0DTE Chain
```bash
curl -s -H "Authorization: Bearer $TRADIER_TOKEN" \
  "https://api.tradier.com/v1/markets/options/chains?symbol=XSP&expiration=$(date +%Y-%m-%d)"
```

### Buy to Open (0DTE Call)
```bash
curl -s -X POST -H "Authorization: Bearer $TRADIER_TOKEN" \
  "https://api.tradier.com/v1/accounts/$ACCOUNT_ID/orders" \
  -d "class=option&symbol=XSP&option_symbol=XSP260310C00675000&side=buy_to_open&quantity=1&type=limit&price=0.35&duration=day"
```

### Sell to Close
```bash
curl -s -X POST -H "Authorization: Bearer $TRADIER_TOKEN" \
  "https://api.tradier.com/v1/accounts/$ACCOUNT_ID/orders" \
  -d "class=option&symbol=XSP&option_symbol=XSP260310C00675000&side=sell_to_close&quantity=1&type=limit&price=0.70&duration=day"
```

### Option Symbol Format
`XSP260310C00675000` = XSP, 2026-03-10, Call, $675 strike

---

## What Exists vs What's Needed

### ✅ Already Built
- Tradier API integration (Venus `services/tradier_service.py`)
- Market clock, quotes, trade preview/execute endpoints
- Trade journal (`/api/auto-trade/log`)
- Ghost Alpha v6.2 + Grade V2 signals
- Webhook JSON payload in Pine Script
- Equity smart buyer (`/api/auto-trade/run`) — live on Venus

### 🟢 Monday Plan (Manual — No Code Required)
1. Watch Ghost Alpha dashboard on SPY 5min
2. When Grade A+/A fires with mega signal → open Tradier, buy XSP 0DTE option
3. Apply IFTTT exit rules → sell on Tradier
4. If trade 1 closes → eligible for trade 2 on next signal
5. Close everything by 2:30 PM ET

---

## Monday Morning Checklist

- [ ] Venus running: `ssh venus-public "curl -s http://localhost:8100/api/health"`
- [ ] Buying power: `ssh venus-public "curl -s http://localhost:8100/api/portfolio/tradier"`
- [ ] Verify XSP options chain loads on Tradier web app
- [ ] Verify L2 options are active on account
- [ ] Ghost Alpha loaded on SPY 5min in TradingView
- [ ] Grade on open: if F/D → sit on hands
- [ ] First mega signal → check XSP 0DTE chain, pick 2-3 OTM
- [ ] Enter if premium $0.15–$0.50 and Grade ≥ B
- [ ] Apply IFTTT exit rules
- [ ] Screenshot entry for blog
- [ ] Close all by 2:30 PM ET
- [ ] Log results

---

*"0DTE options are like Mike Tyson — they can make you rich in 5 minutes or knock you out in 3. The difference is whether you have a plan when you walk in the ring." — Ember 👻*
