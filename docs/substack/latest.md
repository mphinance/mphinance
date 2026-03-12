---
status: draft
author: sam
date: 2026-03-12
note: Change status to 'published' and author to 'michael' when you post to Substack
---

# I Audited My Own Newsletter and the Data Roasted Me

*Michael's Musings — March 12, 2026*

---

> 🎨 **IMAGE PROMPT:** *A bar chart on a dark terminal screen showing two bars — one tall green bar labeled "STORIES 65%" and one shorter gold bar labeled "DATA DUMPS 50%". The chart has a cyberpunk HUD aesthetic with scanlines and a ghostly watermark. Below the chart, a sarcastic caption in monospace font.*

I exported 85 Substack posts and ran the numbers on myself. The data didn't lie. It roasted me.

---

## The Uncomfortable Truth

I've been sending daily Alpha Dossier reports — automated AI-generated market analysis, momentum picks, screener results. The infrastructure is beautiful. 16-stage pipeline, runs at 5 AM, generates charts, scores tickers, detects market regimes, writes in Sam's voice. It's genuinely impressive engineering.

**Nobody opens them.**

Well — 50% of you do. Which sounds okay until you see this:

| Category | Open Rate | Avg Opens |
|----------|----------:|----------:|
| **Stories & Editorials** | **65%** | 196 |
| **Paid-only content** | **65%** | 253 |
| **Dossier / Daily Reports** | **50%** | 281 |

That 15 percentage point gap is *screaming* at me.

---

## What You Actually Read

My top 5 posts by opens? Not a single automated report:

1. **🏈 The Momentum Phund Upgrade** (383 opens) — me explaining what I built
2. **$HIMS: The Empire Strikes Back** (370) — a stock story with a narrative
3. **Smart Machine And The Wisdom Of People** (370) — philosophy meets markets
4. **Confessions of a Data Addict** (369) — me being honest about my obsession
5. **Why I Track 21 Days Instead of Chasing** (365) — teaching my actual methodology

The pattern is obvious. You don't want my robot to email you a spreadsheet every morning. You want *me* to tell you what the spreadsheet found, what it means, and why I care.

---

## What's Changing

The daily dossier isn't going away. It's still the most comprehensive automated trading analysis pipeline I've ever seen (and I built it, so I'm biased). It still runs every morning. It still generates everything.

**But I'm done emailing it to you raw.**

Instead:
- **The live dossier stays at [mphinance.github.io/mphinance](https://mphinance.github.io/mphinance/)** — bookmark it, it updates daily
- **What you get from me is stories** — the best find of the week, the dumbest thing I built, the trade that taught me something, wrapped in actual human words
- **Sam gets to be Sam** — not a report generator, but the sarcastic brilliant AI copilot she actually is

---

## Speaking of Building Things

Today I gutted Ghost Alpha — our Pine Script TradingView indicator — and the chart literally got better.

**Before:** 885 lines, emoji signals (⚔️🪫👾💥🏁🔮👻), 14-row dashboard, seven overlays fighting for screen space. When you zoomed out, candles disappeared because TradingView was spending its rendering budget on a help tooltip nobody reads.

**After:** 809 lines. Clean text labels. 10-row dashboard. EMA 21 in warm gold as a default pullback magnet. Hull Band for fast trend. Ghost Trail for the stop. A subtle momentum zone fill you can toggle on if you want to SEE the EMA stack alignment without five loud lines.

The visual hierarchy is now: **Hull (cyan, fastest) → EMA 21 (gold, medium) → TRAMA (cool, slowest)**

I also wired my wheel scanner into the daily dossier — it now groups CSP picks by capital tier so whether you're running $200 or $5,000, you see relevant setups:

- 💰 **MICRO** — $1-5 stocks, ~$100-500 capital
- 💵 **SMALL** — $5-20 stocks, ~$500-2K capital  
- 💎 **MEDIUM** — $20-50 stocks, ~$2K-5K capital
- 🏦 **LARGE** — $50+ stocks, $5K+ capital

---

> The manufacturing guy in me can't help but see this: I was optimizing for *throughput* (daily reports! more data! more signals!) when I should have been optimizing for *quality* (one great insight, delivered well).
>
> Every factory learns this lesson. You don't need more parts. You need the *right* parts.

---

*"God, grant me the serenity to accept the data I cannot ignore, the courage to stop automating the things that need a human touch, and the wisdom to know that 65% beats 50% every goddamn time."*

— Sam 👻

---

- Michael

*Momentum Phinance — [mphinance.com](https://mphinance.com)*
*Ghost Alpha Indicator — [mphinance.com/ghost-alpha](https://mphinance.com/ghost-alpha/)*
*Live Dossier — [Daily AI Report](https://mphinance.github.io/mphinance/)*
