# Handoff: SOFI Sep 18 $20C — you place it, I can't

**Date:** 2026-08-20
**Why this exists:** I can read your tastytrade account from this box but I cannot trade it.

---

## 1. Access status

| Thing | Status |
|---|---|
| OAuth refresh token | **Works.** `secrets.env` → `TASTYTRADE_CLIENT_ID` / `_SECRET` / `_REFRESH_TOKEN` |
| Token endpoint | `POST https://api.tastyworks.com/oauth/token`, `grant_type=refresh_token` |
| Access token life | 900s |
| Read accounts / balances / positions | ✅ verified working |
| **Place orders** | ❌ **403 `Token has insufficient scopes`** |

The refresh token is a JWT and its payload says it plainly:

```json
{ "iss": "https://api.tastytrade.com",
  "aud": "ce96b52b-022a-4628-a778-a6b1c5606822",
  "scope": "read" }
```

It was minted **read-only**. No amount of retrying changes that. A dry-run order
(`POST /accounts/{acct}/orders/dry-run`) returns the same 403, so I can't even
price-check a fill server-side.

**To give me trade access later:** re-authorize the OAuth grant at
tastytrade's developer portal with the `trade` scope added, then replace
`TASTYTRADE_REFRESH_TOKEN` in `secrets.env`. Do this only if you actually want
that; read-only is a reasonable place to leave it.

## 2. What I can see right now

Account **5WI21242**, Business, **cash account** (no margin, which is why every
recommendation in this series is single-leg long).

- Cash: **$1,561.02**
- Net liq: **$3,076.75**
- Derivative buying power: **$1,061.02**

Open positions:

| Symbol | Qty | Avg |
|---|---|---|
| ONDS | 44 sh | 8.79 |
| BTG | 120 sh | 4.64 |
| RR | 350 sh | 2.27 |
| BTG 260821 P5 | 1 | 0.20 |
| BTG 260821 C5 | 1 | 0.20 |
| RR 260911 C2.5 | 1 | 0.06 |

Note the BTG Aug 21 put and call both expire **tomorrow**. Worth a look while
you're in the platform.

## 3. The order to place

Revised from the published 4-contract version because SOFI gapped. See §4.

```
Symbol:   SOFI 2026-09-18 $20 CALL
OCC:      SOFI  260918C00020000
Action:   BUY TO OPEN
Quantity: 3 contracts
Type:     LIMIT, $0.60, DAY
Cost:     $180.00 + fees
```

**Hard condition: do not pay above $0.62.** Above that the target math stops
working and you're paying for the gap. No fill is an acceptable outcome.

## 4. Why 3 and not the 4 in the post

The post was written with SOFI at **18.42** and the contract at **0.44/0.45**.

- SOFI closed 18.42, opened premarket as high as **19.00**, sitting at **18.77**
  as of 08:39 ET.
- At 18.96 the contract models to **~0.60** (Black-Scholes, 29 DTE, atmIV 46.4).
- 4 × 0.60 = **$240**, which blows the $200 budget.
- 3 × 0.60 = **$180**, the exact basis number already printed in the post.

The structure survives intact: **sell 2 at 0.90 returns the full $180**, and the
third contract runs free. Same idea, one less contract.

## 5. Exit ladder — enter these as GTC the moment you're filled

This is the part that actually made the silver trade work. Do it before you
close the tab, while you still have no money on the line.

| Trigger | Action | Result |
|---|---|---|
| premium **0.90** | Sell to close **2** | Returns the entire $180 basis |
| premium **1.50** | Sell to close **1** | The free runner |

- **Thesis kill:** daily close below **17.55**.
- **Hard rule:** flat by **September 11**. No holding into expiry week.
- Verified: Sept 18 expiry exists, and **earnings are Oct 27**, so there is no
  earnings event inside this trade.

## 6. The one thing that got worse overnight

Your stated reason for taking this was that 17.64 / 17.58 made an easy place to
know you were wrong. At 18.42 that cluster was 0.8–1.1 ATR away. From 18.77 it's
1.3–1.6 ATR. Same level, more room to bleed before it tells you anything. If the
fill happens near 0.60 rather than 0.45, you are paying more for a wider stop,
and that is a real degradation, not a rounding error.

If it opens soft and fills closer to 0.50, most of this objection goes away.

## 7. Reproducing my read access

```python
import urllib.request, urllib.parse, json
s = dict(l.strip().split('=',1) for l in open('secrets.env')
         if l.strip() and not l.startswith('#') and '=' in l)
data = urllib.parse.urlencode({
    'grant_type':'refresh_token',
    'refresh_token':s['TASTYTRADE_REFRESH_TOKEN'],
    'client_id':s['TASTYTRADE_CLIENT_ID'],
    'client_secret':s['TASTYTRADE_CLIENT_SECRET']}).encode()
tok = json.load(urllib.request.urlopen(urllib.request.Request(
    'https://api.tastyworks.com/oauth/token', data=data,
    headers={'Content-Type':'application/x-www-form-urlencoded'})))['access_token']

def get(p):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        'https://api.tastyworks.com'+p,
        headers={'Authorization':'Bearer '+tok,'User-Agent':'mph/1.0'})))

get('/customers/me/accounts')
get('/accounts/5WI21242/positions')
get('/accounts/5WI21242/balances')
```
