# Repo overlap audit

## Summary

74 repos, grouped into 11 clusters. The stack is mostly clean at the product level: the TraderDaddy family, the family and recovery apps, and the art and publishing pieces are all distinct jobs. Real redundancy exists in four places. First, three live market-data MCP and screening tools (momentum-mcp, trading-agent, scanline) that each cover screening and technical analysis. Second, a pile of archived Streamlit and script-era screeners that look like earlier attempts at the same thing. Third, the momentum_phund family and the yield ETF trackers, where names suggest successive attempts. Fourth, two fork copies of the same awesome-mcp-servers list. Everything below is grounded only in names, descriptions, topics, dates and the archived flag. Nothing here says delete. Items are "look at this".

## Clusters

### 1. Broker MCP and broker routing
- awesome-broker-mcp (1 star): verified directory of which brokers an AI can trade through.
- traderdaddy-bridge (1, archived): universal broker adapter, maps every broker into Tradier's API shape.
- tradier-desktop (0, archived): Tradier dashboard, Tauri v2 + React.

### 2. MCP servers and agent skills for market data
- momentum-mcp (37): MCP server for stock screening, OHLCV, TA, charts, financial news.
- trading-agent (1): Vesper, LangGraph agent plus a 56-tool MCP server (screeners, vol grading, EDGAR, dealer gamma, ETF flow).
- alpha-skills (33): AI trading skills for Claude/Gemini agents (backtesting, edge research, strategy design).
- daddymcp (0, archived): one-click MCP connector for TraderDaddy Pro flow data.
- traderdaddy-sdk (1, archived): typed SDK for the TraderDaddy Pro MCP API.

### 3. Screening and TA data
- scanline (5): neon market screener on live TradingView data, factor scoring, 1000+ fields.
- streamlit-tradingview-screen (0, archived): TradingView Screener in a Streamlit app.
- python-sheets-screener (0, archived): no description beyond the name, a Python screener feeding Sheets by the look of it. Unclear, needs a look.
- streamlit-stocks (5, archived): "streamlit stock app testing".
- streamlit-edgar-filings (0, archived): name only, EDGAR filings in Streamlit.
- stock-price-distribution (0, archived): name only. Unclear, needs a look.
- leveraged-etfs (0): leveraged long and short ETFs mapped to underlyings, best pick per side.
- webull_indicators (3): Webull desktop indicators.
- tv-code-library (0, archived): name only, TradingView code. Unclear, needs a look.
- GLXY-trading (2, archived): TradingView scripts for GLXY.
- pinesnake (0): Pine Script to Python bot converter targeting Tradier.
- truth-social-holdings (0, archived): name only. Unclear, needs a look.

### 4. Momentum Phund and yield ETF trackers
- momentum_phund (4): "Momentum Phund", no further description.
- momentum-phund-tasty (3): same name plus tasty, pushed 2026-11-20.
- momentum-hub (1, archived): no description, TypeScript.
- AMU (0): "Alpha Momentum University".
- yieldmax-intraday (2, archived): no description, Python.
- yieldmax-tracker (1, archived): no description, TypeScript.
- ulty-tracker (0, archived): no description, no language, last push 2025-07-14.

### 5. Options flow and GEX (TraderDaddy and AfterHour)
- aftermath (0): AfterHour forensic autopsy and signal intelligence engine, pushed today.
- afterhour-export (0): export your posts.
- daddybot (0, archived): Discord bot for TraderDaddy Pro flow alerts.
- daddyembed (0, archived): embeddable live flow widget.
- daddylens (0, archived): browser extension annotating tickers with flow data.
- daddyhome (0, archived): TRMNL e-ink and Home Assistant integration.
- DaddyBoard (0, archived): no description. Unclear, needs a look.
- apex-fieldtest-tracker (0): community field-test tracker for TraderDaddy Pro Apex levels.
- tightspread (0, archived): "TraderDaddy's better half", Reflex desktop app with MCP agents.
- wheelscope (0, archived): wheel screener and hedge calculator, showcase for the TraderDaddy Pro MCP.

### 6. Wheel and premium tools
- decay-derby (1): CSP/Wheel strategy tracker, pushed today.
- AllYouNeedIsWheel (4, archived fork): automated trading solutions, wheel by name.
- lp-ledger (0): tastytrade screenshots into an options track record.
- wheelscope (see cluster 5).

### 7. Publishing, content and link hubs
- Link hubs: mphinance-links, balloutt-trades-links, onetradewex-links, ryanlp-links (all static GitHub Pages link-in-bio).
- substack-toolkit (2): Claude skill and library for drafting Substack posts.
- substack-data-mining (0): name only. Unclear, needs a look.
- zero-hour-data (0) and zero-hour-site (0): JSON feed and the site that consumes it.
- freshshot (0): keeps README screenshots fresh.
- alpha-playbooks (3, archived), artifacts (0, archived, no description), Stack2LLM (0, archived): content-ish, unclear, needs a look for artifacts and Stack2LLM.
- mphinance (1): profile repo, name only.

### 8. Desktop and dashboard shells
- tradier-desktop (0, archived), tightspread (0, archived), trading-dashboard (2, archived, no description), DaddyBoard (0, archived, no description), ticker-browser (0, archived, AutoHotkey Edge launcher).

### 9. Forks and upstream references
- awesome-mcp-servers (1, fork), awesome-mcp-servers-punkpeye (0, fork), developer-platform (0, fork), disclaw (0, fork), donetick (0, archived fork), ai-job-search (0, fork).

### 10. Recovery, family, learning and life apps
- recovery-nav, are-we-there-yet, morning-quests, kids-savings-tracker (archived), third-settler, mana-vault, ai-train-game, excursionator, crossover, pass-the-65.

### 11. Experiments and one-offs
- ember (0, archived, no description), hormuz-supply-monitor (0, archived, no description), twitter-discord-scraper (0, archived, no description), ulty-tracker (see cluster 4).

## Overlaps to look at

1. **Market-data MCP servers: momentum-mcp, trading-agent, daddymcp.** Real overlap. momentum-mcp (37 stars) does screening, OHLCV, TA, charts and news. trading-agent's 56-tool MCP covers screeners, EDGAR, vol, gamma, ETF flow. Screening and TA appear in both. Recommendation: look at folding the shared screening and TA tools into one, keeping the other for what is unique (Vesper agent, gamma, EDGAR). daddymcp is archived and tied to the TraderDaddy API, so leave it.
2. **Screeners: scanline vs momentum-mcp vs the archived Streamlit trio.** scanline is the live screener UI on TradingView data. streamlit-tradingview-screen and python-sheets-screener look like earlier attempts at that job, now archived. Recommendation: scanline supersedes them, no action needed beyond confirming nothing in the archived ones is missing. scanline versus momentum-mcp screening is a partial overlap, keep both only if one is the UI and the other the agent interface.
3. **momentum_phund, momentum-phund-tasty, momentum-hub, AMU.** Likely successive attempts at one idea, by name. The two momentum_phund repos have near-empty descriptions and both pushed recently. Recommendation: fold one into the other, or write one line each on why both exist. momentum-hub is archived and looks superseded. AMU is a separate name, unclear, needs a look.
4. **yieldmax-tracker, yieldmax-intraday, ulty-tracker.** Three trackers for what the names suggest is yield-ETF data, none with a description, all archived. Looks like one idea attempted three times. Recommendation: look at whether one covers the other two.
5. **Wheel: decay-derby, AllYouNeedIsWheel, wheelscope.** decay-derby is the live tracker. AllYouNeedIsWheel is an archived fork. wheelscope is an archived showcase for the TraderDaddy MCP. Little real overlap. Keep decay-derby as the one active wheel tool.
6. **Desktop shells: tradier-desktop, tightspread, trading-dashboard, DaddyBoard.** Four dashboards, all archived, last pushed between 2025-06 and 2026-07. Same job, abandoned. Recommendation: look at which one (if any) still matters. trading-dashboard and DaddyBoard have no description, unclear, needs a look.
7. **Awesome list forks: awesome-mcp-servers and awesome-mcp-servers-punkpeye.** Two forks of the same kind of list, one with a "comprehensive" description, one "A collection of MCP servers". awesome-broker-mcp is the original work. Recommendation: look at whether either fork is carrying local changes. If not, one is redundant.
8. **Link hubs: mphinance-links, balloutt-trades-links, onetradewex-links, ryanlp-links.** Same template, four brands. They serve different people and brands, so they are not duplicate products. Recommendation: keep all, but check they share one template rather than four drifting copies.
9. **substack-toolkit vs substack-data-mining.** Likely different directions (write versus mine), but substack-data-mining has no description. Unclear, needs a look.
10. **aftermath vs afterhour-export.** aftermath is the analysis engine, afterhour-export exports posts. Probably complementary. Look at whether the export belongs inside aftermath.

## Worth consolidating into one thing

The market-data MCP and screening layer: momentum-mcp, trading-agent and scanline, with the archived Streamlit screeners as history. Three live repos advertise screening plus technical analysis, and you already reach this territory through connected MCP servers. Pick one home for screening and TA (momentum-mcp has the traction at 37 stars), and have trading-agent and scanline call it, keeping only what is unique to each.

## Do not touch

- **TraderDaddy / TraderMatrix family** (daddybot, daddyembed, daddylens, daddyhome, daddymcp, traderdaddy-sdk, tightspread, apex-fieldtest-tracker, wheelscope, traderdaddy-bridge): a deliberate hub-and-spoke product line around one API, each spoke a different surface (Discord, browser, e-ink, SDK). Most are archived already. They look redundant to each other but are separate delivery surfaces for one product.
- **Recovery and family apps** (recovery-nav, are-we-there-yet, morning-quests, kids-savings-tracker, third-settler, ai-train-game, excursionator, crossover, mana-vault, pass-the-65): personal and community products with no trading overlap. recovery-nav serves a specific community need.
- **Art and publishing** (substack-toolkit, zero-hour-data and zero-hour-site, the link hubs, freshshot): a deliberate data/presentation split for zero-hour, and publishing tooling that stands alone.
- **Broker directory** (awesome-broker-mcp): original research, distinct from everything in the trading clusters.
