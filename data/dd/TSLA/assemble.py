"""Assemble the TSLA Super DD from the four research parts plus the call sections."""
import json
from pathlib import Path

D = Path(__file__).resolve().parent
parts = {p: json.loads((D / "parts" / f"{p}.json").read_text()) for p in "abcd"}

sections = sorted((s for p in parts.values() for s in p["sections"]), key=lambda s: s["n"])

sections += [
    {
        "n": 13,
        "title": "Steelman: bull vs bear",
        "summary": "Both sides agree the balance sheet is fine. The fight is whether a counter-trend dip in a risk-off tape is worth half a unit of risk.",
        "bullets": [
            {"text": "**Bull:** the $352 to $355 zone stacks the **$355** and **$350** dealer strikes, the two biggest volume nodes of the last 60 sessions and three prior lows (9/15, 10/16, 10/19).", "source": "TDPro GEX, yfinance"},
            {"text": "**Bull:** spot is in positive gamma, **4%** above a flip both models put at **$344 to $347**, so dealers lean against the move in both directions.", "source": "TDPro get_gex_ticker, get_apex_levels"},
            {"text": "**Bull:** the Street has not flinched: **10** target raises and **0** cuts in 30 days, mean target **$413.10**, and no firm moved after the 11/5 drop.", "source": "yfinance"},
            {"text": "**Bull:** **$45.45B** of cash plus **$30B** of undrawn lines. Nothing here gets forced.", "source": "Q3 10-Q, 9/29 8-K"},
            {"text": "**Bull:** the first target is real resistance, not a hope: the 11/4 close sits on the **$383.87** 200-day and the falling trendline.", "source": "yfinance"},
            {"text": "**Bear:** a breakout just failed. Price is under all nine averages, **-DI 36.4** leads **+DI 20.3**, and 11/5 closed below the zone on **2.05x** volume.", "source": "yfinance"},
            {"text": "**Bear:** **-$600M** of net dark pool selling in 5 days, and Stocktwits sentiment at **14**, extremely bearish.", "source": "TDPro get_dark_pool, Stocktwits"},
            {"text": "**Bear:** **2.6%** operating margin, **165.9x** forward earnings and a **0.35%** FCF yield. The multiple rides on robotaxi and Optimus, which management dates to **2027**.", "source": "Q3 10-Q, yfinance"},
            {"text": "**Bear:** beta **2.16** to SPY in a market reading risk-off (Market Health **4.5 of 5**, VIX curve inverted). It fell **14.6%** in two sessions last week with the Nasdaq.", "source": "yfinance, TDPro get_market_health"},
            {"text": "**Bear:** the **12/3** annual meeting, with Musk up for re-election and a SpaceX combination being explored, lands inside the hold.", "source": "Tesla DEF 14A, Q3 10-Q Item 5"},
        ],
    },
    {
        "n": 14,
        "title": "What would make me wrong",
        "summary": "A tag of $335 is a trade problem. A close back under $344 is the gamma regime flipping. Neither one says the business changed.",
        "figure": "img/TSLA.png",
        "caption": "TSLA daily with dealer levels",
        "bullets": [
            {"text": "**Too cautious:** a daily close above **$384**, the 200-day, without a dip first. That reclaims the trendline the 11/2 breakout lost, and this card never fills. That is a different setup, not a chase of this one.", "source": "yfinance"},
            {"text": "**The trade is wrong:** a trade at **$335** after a fill. That is under the 11/5 capitulation low of $338.15 and the 0.786 retrace at $340.49.", "source": "plan, yfinance"},
            {"text": "**The dip is not holding:** a daily close under **$344**, the gamma flip. Below it dealers chase moves instead of fading them, and volume under $350 is thin.", "source": "TDPro get_gex_ticker, yfinance"},
            {"text": "**The bigger picture breaks:** a close under **$331.12**, the 60-session low. That puts the **$297.38** July low back in play.", "source": "yfinance"},
            {"text": "**Event risk:** a SpaceX combination headline, a formal NHTSA investigation, or an EU FSD vote that fails. None of those has a date.", "source": "Q3 10-Q, Claims Journal, Electrive"},
        ],
    },
    {
        "n": 15,
        "title": "Catalyst calendar",
        "summary": "Tesla has nothing of its own scheduled before the 12/3 meeting. The dated risk is macro and NVDA.",
        "bullets": [],
    },
]

catalysts = [
    {"date": "2026-11-10", "event": "October CPI, 8:30am ET", "source": "[BLS](https://www.bls.gov/schedule/news_release/cpi.htm)"},
    {"date": "2026-11-17", "event": "NVDA earnings, 5pm ET call. NVDA fell 9.3% on 11/5 alongside TSLA, so the AI tape is shared (63-day correlation 0.56)", "source": "[NVIDIA](https://nvidianews.nvidia.com/news/nvidia-sets-conference-call-for-third-quarter-financial-results-6928873)"},
    {"date": "2026-11-20", "event": "Monthly options expiration. The gamma book behind the $344 flip and $355 support is mostly weeklies through mid-November", "source": "calendar rule, TDPro expirationsUsed"},
    {"date": "2026-12-03", "event": "Tesla annual meeting, 3pm CT: Class I directors including Musk, say-on-pay, auditor", "source": "[Tesla DEF 14A](https://www.sec.gov/Archives/edgar/data/0001318605/000110465926116700/tm267596-1_def14a.htm)"},
    {"date": "2026-12-04", "event": "This card expires if the dip never fills", "source": "plan"},
    {"date": "2026-12-08", "event": "FOMC, December 8 to 9, with projections", "source": "[Federal Reserve](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm)"},
    {"date": "2026-12-10", "event": "November CPI, 8:30am ET", "source": "[BLS](https://www.bls.gov/schedule/news_release/cpi.htm)"},
    {"date": "2026-12-18", "event": "Expiry of the Dec 18 calls", "source": "yfinance option expirations"},
    {"date": None, "event": "SpaceX combination: special committee exploring it, no terms, needs 50% of all Tesla shares", "source": "Q3 10-Q Item 5, US News/Reuters"},
    {"date": None, "event": "EU-wide FSD vote, reported for December, not on a published agenda", "source": "Electrive"},
    {"date": None, "event": "NHTSA audit AQ26002 outcome on Cybercab self-certification", "source": "Claims Journal"},
    {"date": None, "event": "Dallas Cybercab rides, said to start in November", "source": "Q3 call recap"},
    {"date": None, "event": "Q4 deliveries and Q4 earnings (yfinance shows 1/27/2027, not confirmed by Tesla)", "source": "yfinance"},
]

trade_plan = {
    "triggers": [
        {
            "label": "The dip",
            "condition": "a trade into **$352 to $355** with a daily close back at or above **$352**. That is the $355 and $350 dealer strikes, the two biggest volume nodes and three prior lows, sitting about **$9** above the $344 gamma flip",
            "stop": "**$335**, under the 11/5 low of $338.15. From a $353.50 fill that is **$18.50** of risk, **1.11 ATR**. It is inside the one-week expected move ($327 to $392), so this is a stop that can get tagged by a normal week",
        }
    ],
    "no_trade_zone": "above **$355**. Friday's **$358.22** is $3 over the zone and right under the $360 to $362.50 pin. A bounce off $356 does not fill, and that is fine",
    "targets": [
        "**$385.19**, the 11/4 close on the 200-day and the falling trendline (**1.7R** from $353.50; the $370 and $377.50 call walls sell first)",
        "**$398.50**, the 11/3 close at the 0.5 retrace (**2.4R**)",
    ],
    "options": {
        "structure": "**Dec 18 $355/$385 call debit spread**, which tops out at T1",
        "expiry": "Dec 18, 2026, which carries the 12/3 meeting, the 12/8 to 12/9 FOMC and 12/10 CPI",
        "debit": "**$13.65** at mid ($355 call 27.00 x 27.50, $385 call 13.45 x 13.75 at Friday's close). Bought on a fill at the zone it will cost less, so reprice it that day",
        "max_value": "**$30**, so about **1.2 to 1** on the debit at Friday's prices",
        "breakeven": "about **$368.65** at expiry. IV rank is **62.6**, but implied (52%) is about equal to realized (51 to 57%), so the spread is about the width of the move, not a discount. The single **Dec 18 $360 call** at **$24.53** mid is the simpler way to own it, breakeven **$384.53**",
    },
    "wheeler_alternative": "not on this week's list, which is long shares and long calls only. A put sold at the $335 stop level would pay for being wrong at the exact price the card says it is wrong, so the two don't mix. Not priced here.",
    "notes": [
        "Size **0.5R**, the whole list this week. TSLA's 63-day correlation is 0.66 to QQQ and 0.56 to NVDA, so it carries the tech tape with it.",
        "**The 12/3 annual meeting sits inside the hold** and the card has no exit before it. Going flat into 12/3 if the position is open and short of T1 is the cautious version.",
    ],
    "exit_if": [
        "a daily close under **$344**, the gamma flip, after a fill (the dip did not hold)",
        "a close under **$331.12**, the 60-session low",
        "no fill by **Fri 12/4**",
    ],
}

unverified = []
for p in parts.values():
    for u in p.get("unverified", []):
        if u not in unverified:
            unverified.append(u)

sources, seen = [], set()
for p in parts.values():
    for s in p.get("sources", []):
        key = s.get("url") or s.get("label")
        if key and key not in seen:
            seen.add(key)
            sources.append(s)

report = {
    "meta": {
        "ticker": "TSLA",
        "company": "Tesla",
        "date": "2026-11-07",
        "price": 358.22,
        "price_asof": "2026-11-06 close",
        "slug": "tsla-super-dd-tesla",
        "title": "TSLA Due Diligence: Tesla",
        "subtitle": "Research 50% | Trading 50%",
        "description": "Tesla due diligence: Q3 numbers, the $30B credit lines and SpaceX talks, a failed breakout, gamma walls, flow and dark pool, the 12/3 meeting, and a trade plan with a trigger, stop, targets and an options expression. Score: 5/10.",
        "cover": "img/TSLA.png",
    },
    "verdict": {
        "score": 5,
        "size_R": 0.5,
        "action": "BUY ON TRIGGER",
        "pitch": "Tesla is a car company priced like an AI and robotics company: **$20.6B** of **$28.05B** in Q3 revenue was still cars, at a **2.6%** operating margin. The stock just failed a breakout at $414 and fell to $338 in three sessions. It is the only name from this week's screen sitting in positive gamma, on a shelf where dealer strikes, volume and three prior lows stack at **$350 to $355**. This is a counter-trend dip buy in a risk-off tape, so it gets half a unit and a hard stop at **$335**.",
    },
    "sections": sections,
    "trade_plan": trade_plan,
    "catalysts": catalysts,
    "unverified": unverified,
    "sources": sources,
    "data": {
        "options_and_flow": parts["c"].get("data", {}),
        "technicals": parts["d"].get("data", {}),
        "levels": parts["d"].get("levels", []),
        "plan_check": parts["d"].get("plan_check", ""),
        "card": {
            "posted": "2026-11-07, w/e 11/13 forum thread, scored 6/10 before this review",
            "trigger": "Dip to $352-355 that holds",
            "stop": 335,
            "targets": [385.19, 398.5],
            "sizeR": 0.5,
            "expiresOn": "2026-12-04",
        },
    },
}

out = D / "2026-11-07.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
print(out, len(sections), "sections", len(catalysts), "catalysts", len(unverified), "unverified", len(sources), "sources")
