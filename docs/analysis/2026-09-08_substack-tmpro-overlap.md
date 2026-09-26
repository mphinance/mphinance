# Substack readers who are also TMPro users — 2026-09-08

Pulled live: Substack subscriber list via SID-cookie dashboard scrape (`scripts/substack_export_subscribers.py`,
`/publish/subscribers`), TMPro (TraderDaddy Pro / TMPro, `~/TraderDaddy-Pro---Whop`) `users` table via
`railway run node scripts/export_users_for_subscriber_xref.mjs` against prod. Matched by lowercased email —
a floor estimate, since a reader can use different emails on each platform.

## Headline

- **1,133** total Substack subscribers
- **927** total TMPro users
- **196 Substack subscribers (17.3%) are also TMPro users** — matched by email
- Of those 196: **99 are TMPro `free` tier, 97 are TMPro `premium` tier** — almost an even split

## Substack subscriber base, by type

| Type | Count |
|---|---:|
| Free | 1,066 |
| Founders | 40 |
| Comp | 22 |
| Monthly Paid | 3 |
| Yearly Paid | 1 |
| Author (you) | 1 |
| **Total** | **1,133** |

## The 196 overlap readers, cross-tabbed (Substack type → TMPro tier)

| Substack type | TMPro free | TMPro premium | Total |
|---|---:|---:|---:|
| Free | 87 | 75 | 162 |
| Founders | 8 | 14 | 22 |
| Comp | 1 | 8 | 9 |
| Monthly Paid | 1 | 0 | 1 |
| Yearly Paid | 1 | 0 | 1 |
| Author | 1 | 0 | 1 |
| **Total** | **99** | **97** | **196** |

**Read on this:** among the overlap readers who pay you on Substack (Founders/Comp/Monthly/Yearly, excluding
your own Author row — 33 people), **67% are TMPro premium** (22 of 33). Among the overlap readers who read
you free on Substack (162 people), only **46% are TMPro premium** (75 of 162). Paying you on Substack does
correlate with paying on TMPro — a real signal that your most bought-in readers cluster across both products.

## Where the overlap TMPro accounts came from (acquisition `source`)

| Source | Count |
|---|---:|
| DIRECT | 70 |
| GOOGLE | 64 |
| REF:8DUEMWAJ *(your TMPro ref link)* | 24 |
| REF:HGR | 18 |
| REF:MPHINANCE *(your ref link, alt code)* | 4 |
| REF:QLMRUXSG | 4 |
| REF:QPQJ3APW | 4 |
| REF:NPYJ2DDX | 2 |
| REF:TRADINGWITHART | 2 |
| REF:FRIDGE | 1 |
| REF:VCTQ7RQV | 1 |
| INDICATOR_PAYMENT_LINK | 1 |
| REF:3DBNGSD3 | 1 |

**Your own referral link (`REF:8DUEMWAJ` + `REF:MPHINANCE`) directly converted 28 of the 196 overlap
readers into TMPro signups** (14.3% of the overlap group) — those are readers you can trace straight from
Substack to a TMPro account through your link.

## Other cuts

- **97** of the 196 overlap readers are TMPro `premium` **and currently active**
- **85** of the 196 have verified Discord on their TMPro account

## Paid Substack subscribers — full breakdown

"Paid" splits into two different things on Substack: money actually changing hands (Founders/Monthly/Yearly)
vs. **Comp** (you gifted the tier — no revenue). Keeping those separate:

| Group | n | In TMPro | TMPro premium |
|---|---:|---:|---:|
| **True paying** (Founders + Monthly + Yearly) | 44 | 24 (54.5%) | 14 (31.8% of all 44) |
| **Comp** (gifted, no revenue) | 22 | 9 (40.9%) | 8 (36.4% of all 22) |
| **Combined** | 66 | 33 (50.0%) | 22 (33.3% of all 66) |

Comp'd readers convert to TMPro premium at roughly the same rate as true payers — gifting the Substack tier
isn't diluting the signal.

### The 20 true-paying subscribers who are NOT yet TMPro users

This is the actionable list — people already paying you on Substack who haven't shown up in TMPro under
the same email. Worth a direct nudge with your ref link (`?ref=8DUEMWAJ`):

| Email | Substack type |
|---|---|
| lilwelder37@gmail.com | Founders |
| orchdork869@gmail.com | Founders |
| glassaholic@comcast.net | Founders |
| adityaw27@gmail.com | Monthly Paid |
| don@takeitoffmobileblasting.com | Founders |
| expressheating.wi@gmail.com | Founders |
| aaron_christophersen@hotmail.com | Founders |
| sanchitha.gs@gmail.com | Founders |
| substack.skeptic142@passmail.net | Founders |
| atul@finalysisgroup.com | Founders |
| wamitchell42@gmail.com | Founders |
| joe.milan@gmail.com | Founders |
| matt.crandell7@gmail.com | Founders |
| jguynn1980@gmail.com | Monthly Paid |
| manoj.r.13@gmail.com | Founders |
| addisonhayesodell@gmail.com | Founders |
| rwall7@gmail.com | Founders |
| lo_rezz@msn.com | Founders |
| alextrout1995@gmail.com | Founders |
| hualanl@yahoo.com | Founders |

### Note on the Comp list

Several `wi.rr.com` addresses in your Comp tier (`cathysadler`, `jsugden`, `bobbonnie`) read like Wisconsin
friends/family rather than reader-acquisition comps — worth knowing before reading too much into the Comp
conversion rate. Also: `avoroj@gmail.com` (Comp, TMPro premium via DIRECT) matches the Railway workspace
owner (Artur Vorojeykin) — likely your TMPro co-founder/engineer's own account, not an organic reader.

## Caveats

- Email-match only. Readers using a different email for Substack vs. TMPro (e.g. Gmail alias, work email)
  won't be caught — treat 196 as a floor, not a ceiling.
- TMPro `users` table comment notes it's "no longer synced with external platform" — `source`/`subscription_tier`
  reflect the app's own record, not Whop/Stripe directly.
- Substack scrape is a live UI snapshot (1,133 matched the dashboard's stated total exactly at pull time).
