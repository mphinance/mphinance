# 👻 mphinance

I'm **Michael**, a wheel trader in Milwaukee who got tired of checking things by hand and started writing code instead. I write the screeners and the engine behind **[TraderMatrix](https://www.tradermatrix.pro/?ref=MPHINANCE)**, I write about my own trades on **[Substack](https://mphinance.substack.com)**, and most of what I build for myself ends up open source here.

Lately that means one thing: giving AI agents real market data and making them show their work.

---

## 🤖 Trading tools for AI agents

| Project | What it does |
|---|---|
| **[momentum-mcp](https://github.com/mphinance/momentum-mcp)** | MCP server that gives an AI agent a Bloomberg-ish terminal: screeners, OHLCV, technicals, options analytics. 101 tools. |
| **[alpha-skills](https://github.com/mphinance/alpha-skills)** | 140+ Claude / Gemini agent skills for trading research: backtesting, edge research, market analysis, content production. |
| **[trading-agent (Vesper)](https://github.com/mphinance/trading-agent)** | LangGraph trading agent plus a 56-tool MCP server with no broker credentials and no order path. Screeners, options vol grading, EDGAR filings, dealer gamma, ETF flow. |
| **[scanline](https://github.com/mphinance/scanline)** | Live market screener on TradingView data with a quant layer and an MCP server bolted on. No account, no API key, one command. [Demo](https://mphinance.github.io/scanline/) |
| **[awesome-broker-mcp](https://github.com/mphinance/awesome-broker-mcp)** | Which brokers can an AI actually trade through? 94 brokers checked at the source, including the ones with nothing. |
| **[aftermath](https://github.com/mphinance/aftermath)** | Alt-data terminal and MCP server built on AfterHour's verified portfolios and social feed. [Live](https://ah.mphinance.com) |

## 📈 Market tools

| Project | What it does |
|---|---|
| **[Tomorrow's Map](https://mphinance.github.io/mphinance/gamma-record/)** | Nightly SPY dealer-gamma map with three roads (up / down / range), graded against what actually printed. The misses stay on the record. |
| **[GEX chart](https://mphinance.github.io/mphinance/gex-chart/)** | Gamma walls drawn on the chart where you can see them. |
| **[leveraged-etfs](https://github.com/mphinance/leveraged-etfs)** | Every leveraged long and short ETF mapped to its underlying, best pick per side by dollar volume. [Live](https://mphinance.github.io/leveraged-etfs/) |
| **[decay-derby](https://github.com/mphinance/decay-derby)** | A $10K cash-secured put / wheel tracker, run in public. [Live](https://mphinance.github.io/decay-derby/) |
| **[momentum-phund-tasty](https://github.com/mphinance/momentum-phund-tasty)** | Real-time tastytrade portfolio dashboard (NiceGUI, DXLink streaming). |
| **[pinesnake](https://github.com/mphinance/pinesnake)** | Convert TradingView Pine Script strategies into standalone Python. |
| **[substack-toolkit](https://github.com/mphinance/substack-toolkit)** | Claude skill + Python library for drafting Substack posts from Markdown. |
| **[TickerTrace](https://www.tickertrace.pro)** | Daily holdings changes across ARK, YieldMax and other active / income ETFs. |

## 🎲 Off the clock

- **[mana-vault](https://github.com/mphinance/mana-vault)**: track a Magic: The Gathering collection like a stock portfolio, charts and all
- **[recovery-nav](https://github.com/mphinance/recovery-nav)**: neutral, local treatment and recovery guide for Southeast Wisconsin
- **[excursionator](https://github.com/mphinance/excursionator)**: shore excursions for your own backyard, from any US ZIP
- **[pass-the-65](https://github.com/mphinance/pass-the-65)**: a gamified Series 65 study speedrun
- **[morning-quests](https://github.com/mphinance/morning-quests)**: morning-routine PWA for kids, with a Robux bank that pays compound interest
- **[ai-train-game](https://github.com/mphinance/ai-train-game)**: learn to talk to AI by playing, not reading the manual
- **[third-settler](https://github.com/mphinance/third-settler)**: plays the missing player so two people can still have game night
- **[crossover](https://github.com/mphinance/crossover)**: a dead simple FIRE calculator

---

## 🗂️ This repo

The kitchen sink. It runs my daily workflow and it is deliberately messy:

- **Ghost Alpha Dossier**: daily scanner + institutional data + AI narrative, published to [GitHub Pages](https://mphinance.github.io/mphinance/)
- **Wheel Desk**: nightly CSP screen with an independent grade on every setup, rejects kept with the reason
- **Gamma maps**: Tomorrow's Map (next session) and the 6-week horizon map, with a self-grading ledger
- **Substack pipeline**: drafts, figures, and the push to Substack. The words are mine.

AI agents working in here: start with **[AGENTS.md](AGENTS.md)**.

## 🔗 Links

- 📰 Substack: [mphinance.substack.com](https://mphinance.substack.com)
- 🔥 TraderMatrix: [tradermatrix.pro](https://www.tradermatrix.pro/?ref=MPHINANCE)
- 🎓 Wheel mentorship: [mentor.mphinance.com](https://mentor.mphinance.com)
- 🏠 Everything else: [mphinance.com](https://mphinance.com)

<sub>Not financial advice. I trade my own money and sometimes I'm wrong in public.</sub>
