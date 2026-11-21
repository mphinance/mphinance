# Repo summaries vs Michael's stack

246 repos graded. Verdicts: noise 136, adjacent 91, gap 11, covered 8

## TauricResearch/TradingAgents
- stars: 123310 | license: Apache-2.0 | lang: Python
- what: Multi-agent LLM framework (analyst, researcher, trader roles) that runs a trading decision pipeline per ticker, with backtests and saved reports.
- category: agent
- access: n/a
- vs stack: adjacent
- why: Overlaps the LangGraph agent in mphinance/trading-agent (Vesper); worth knowing as the reference design, not a hole.

## punkpeye/awesome-mcp-servers
- stars: 98331 | license: MIT | lang: n/a
- what: not documented
- category: meta-list
- access: n/a
- vs stack: noise
- why: Generic MCP server list with an unreadable README, and mphinance/awesome-broker-mcp is the trading-specific version.

## modelcontextprotocol/servers
- stars: 92138 | license: NOASSERTION | lang: TypeScript
- what: Reference implementations of MCP servers from the MCP steering group, plus pointers to community servers.
- category: infra
- access: n/a
- vs stack: adjacent
- why: Protocol reference material for building servers like momentum-mcp, not a trading capability.

## sickn33/agentic-awesome-skills
- stars: 50058 | license: MIT | lang: Python
- what: Library of 3,055+ installable SKILL.md playbooks for coding agents, with a local catalog and plan preview tool (AAS Core).
- category: agent-skills
- access: n/a
- vs stack: noise
- why: General coding-agent skills with no trading focus, and mphinance/alpha-skills already covers the trading side.

## HKUDS/Vibe-Trading
- stars: 38627 | license: MIT | lang: Python
- what: Trading agent with a research lab, backtesting, options lab and multi-agent swarm, driven by one command and exposed over API and MCP.
- category: agent
- access: n/a
- vs stack: adjacent
- why: Backtesting and strategy research overlaps mphinance/alpha-skills and Vesper; the README excerpt does not show US options premium-selling depth.

## VoltAgent/awesome-agent-skills
- stars: 37393 | license: MIT | lang: n/a
- what: Curated list of 1000+ agent skills from dev teams and the community for Claude Code, Codex, Gemini CLI and others.
- category: meta-list
- access: n/a
- vs stack: noise
- why: Generic skills directory, not trading specific.

## QuantConnect/Lean
- stars: 22633 | license: Apache-2.0 | lang: C#
- what: Event-driven algorithmic trading engine in C# and Python with alternative data and live-trading support, plus the Lean CLI.
- category: infra
- access: both
- vs stack: adjacent
- why: Full algo platform that overlaps pinesnake and traderdaddy-bridge at a much heavier weight than his lean stack wants.

## we-promise/sure
- stars: 16935 | license: AGPL-3.0 | lang: Ruby
- what: Self-hosted personal finance app, a community fork of the abandoned Maybe Finance project.
- category: other
- access: n/a
- vs stack: noise
- why: Budgeting and net worth tracking, unrelated to trading tooling.

## modelcontextprotocol/registry
- stars: 7485 | license: NOASSERTION | lang: Go
- what: Community registry service where MCP clients discover published MCP servers, with a publish flow and API.
- category: infra
- access: n/a
- vs stack: adjacent
- why: A place to list momentum-mcp or daddymcp for discovery, not a capability gap.

## georgezouq/awesome-ai-in-finance
- stars: 6779 | license: CC0-1.0 | lang: n/a
- what: Curated list of LLM, deep learning, skills, MCP servers, market data and trading execution resources for finance.
- category: meta-list
- access: n/a
- vs stack: noise
- why: Duplicate awesome-list, and mphinance/awesome-broker-mcp is the verified execution-focused version.

## Polymarket/agents
- stars: 3817 | license: MIT | lang: Python
- what: Developer framework for building AI agents that trade on Polymarket, with API integration, RAG and news sourcing.
- category: agent
- access: trades
- vs stack: noise
- why: Prediction-market trading, outside his US equities and options focus.

## Polymarket/polymarket-cli
- stars: 2913 | license: none | lang: Rust
- what: Rust CLI to browse Polymarket markets, place orders and manage positions, also usable as a JSON API for agents.
- category: cli
- access: both
- vs stack: noise
- why: Prediction-market CLI, irrelevant to his trading.

## hyperliquid-dex/hyperliquid-python-sdk
- stars: 1889 | license: MIT | lang: Python
- what: Python SDK for Hyperliquid API trading using a public address and API wallet key.
- category: sdk
- access: trades
- vs stack: noise
- why: Crypto perps exchange SDK, and he is indifferent to crypto.

## koreainvestment/open-trading-api
- stars: 1676 | license: none | lang: Python
- what: Sample code repository for the Korea Investment & Securities open trading API, with an llms.txt guide for AI agents.
- category: sdk
- access: both
- vs stack: noise
- why: Korean broker API samples, not US equities or options.

## mnemox-ai/tradememory-protocol
- stars: 1450 | license: MIT | lang: Python
- what: Local-first memory and risk brake for AI trading agents: syncs fills, surfaces where your own history loses money, and can refuse orders that break your rules before they reach the broker (20 MCP tools).
- category: other
- access: both
- vs stack: gap
- why: Adds outcome-based trade memory and a pre-order guard driven by his own history, which nothing in his stack does; it syncs Alpaca fills read-only per the README.

## coinbase/agentkit
- stars: 1359 | license: NOASSERTION | lang: TypeScript
- what: Toolkit that gives AI agents a crypto wallet and onchain actions, in Node.js and Python.
- category: sdk
- access: trades
- vs stack: noise
- why: Crypto wallet tooling, irrelevant to his equities and options work.

## binance/binance-skills-hub
- stars: 1200 | license: none | lang: Python
- what: Binance marketplace of skills that let AI agents search tokens, trade, track wallets and use DeFi.
- category: agent-skills
- access: trades
- vs stack: noise
- why: Crypto exchange skills, outside his scope.

## alpacahq/alpaca-mcp-server
- stars: 1102 | license: MIT | lang: Python
- what: Alpaca's official MCP server for trading stocks, ETFs, crypto and options plus market data and portfolio management from LLM clients (v2, FastMCP rewrite).
- category: broker-mcp
- access: both
- vs stack: gap
- why: Official US equities and options execution over MCP, which his stack lacks outside Vesper's Webull orientation and the traderdaddy-bridge adapter layer.

## longbridge/longbridge-terminal
- stars: 1058 | license: Apache-2.0 | lang: Rust
- what: Rust CLI and TUI for the Longbridge platform covering quotes, options, portfolio and order submission, built for scripting and agent tool-calling.
- category: cli
- access: both
- vs stack: adjacent
- why: A broker CLI in the directory-worthy mold, but Longbridge is not his broker and no US-specific need is shown.

## LLMQuant/awesome-trading-agents
- stars: 1025 | license: CC0-1.0 | lang: n/a
- what: Curated list of LLM trading agents, MCP servers and agent skills for market research, strategy and execution.
- category: meta-list
- access: n/a
- vs stack: noise
- why: Duplicate awesome-list overlapping mphinance/awesome-broker-mcp.

## ariadng/metatrader-mcp-server
- stars: 857 | license: MIT | lang: Python
- what: MCP server that lets AI assistants trade through MetaTrader, with a WebSocket quote server and a Claude trading assistant skill.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: MetaTrader is a forex and CFD venue, not his US equities and options path.

## krakenfx/kraken-cli
- stars: 813 | license: MIT | lang: Rust
- what: Kraken CLI for crypto, tokenized stocks, forex and futures with JSON output, a built-in MCP server and paper trading on live prices.
- category: cli
- access: both
- vs stack: noise
- why: Crypto exchange tooling; tokenized stocks are for non-US customers per the README.

## alash3al/stash
- stars: 772 | license: Apache-2.0 | lang: Go
- what: Self-hosted persistent memory layer for AI agents (episodes, facts, working context) in Postgres, with an MCP server.
- category: infra
- access: n/a
- vs stack: adjacent
- why: General agent memory, not trading specific; related to the memory angle in tradememory-protocol.

## caiovicentino/polymarket-mcp-server
- stars: 753 | license: MIT | lang: Python
- what: MCP server with 45 tools, real-time monitoring and safety features for Claude to trade Polymarket.
- category: broker-mcp
- access: trades
- vs stack: noise
- why: Prediction-market trading, outside his scope.

## YichengYang-Ethan/oracle3-prediction-market-agent
- stars: 569 | license: Apache-2.0 | lang: Python
- what: Prediction-market engine and MCP server that finds no-arbitrage violations and trades them on Kalshi, Polymarket and Solana or on paper under risk limits.
- category: agent
- access: both
- vs stack: noise
- why: Prediction-market arbitrage, not his trading style or markets.

## okx/agent-trade-kit
- stars: 513 | license: MIT | lang: TypeScript
- what: OKX MCP server and CLI that connect AI agents to spot, swap, futures, options and grid bots.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto exchange MCP, and he is indifferent to crypto.

## base/base-mcp-legacy
- stars: 352 | license: MIT | lang: TypeScript
- what: Archived MCP server for the Base network and Coinbase API, replaced by docs on docs.base.org.
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: Deprecated and archived crypto stub.

## okx/onchainos-skills
- stars: 346 | license: MIT | lang: Rust
- what: OKX skills for AI agents covering wallet, token discovery, DEX swap, bridge and transaction broadcasting across 20+ chains.
- category: agent-skills
- access: trades
- vs stack: noise
- why: Onchain crypto skills, irrelevant to his trading.

## Oft3r/agentic-trading-desk
- stars: 338 | license: MIT | lang: Python
- what: Robinhood MCP-driven trading desk where Python scripts score stocks and ETFs on trend, momentum and macro sentiment and the human approves every order.
- category: agent-skills
- access: both
- vs stack: adjacent
- why: Indicator scoring and human-approved execution overlaps mphinance/alpha-skills and momentum-mcp, though the Robinhood MCP angle is worth a look for the directory.

## zerodha/kite-mcp-server
- stars: 332 | license: MIT | lang: Go
- what: Zerodha Kite MCP server, hosted at mcp.kite.trade, for market data, portfolio management and trade execution.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Indian broker with no US access; directory material for mphinance/awesome-broker-mcp, not for his stack.

## huygiatrng/AlpacaTradingAgent
- stars: 286 | license: Apache-2.0 | lang: Python
- what: Independent Alpaca-oriented fork of TradingAgents with live Alpaca integration, crypto support and automated trading.
- category: agent
- access: trades
- vs stack: adjacent
- why: Overlaps Vesper as an LLM agent, and Alpaca execution is better covered by the official alpaca-mcp-server.

## wshobson/mcp-trader
- stars: 274 | license: none | lang: n/a
- what: Archived MCP server for stock traders, superseded by wshobson/maverick-mcp.
- category: other
- access: n/a
- vs stack: noise
- why: Archived stub, and mphinance/momentum-mcp covers screening and technicals.

## Bitget-AI/agent_hub
- stars: 234 | license: MIT | lang: JavaScript
- what: Official Bitget toolkit (CLI, MCP, SDK, skills, signals) connecting AI agents to Bitget crypto trading with 89 UTA v3 operations.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto exchange toolkit, outside his scope.

## code-rabi/interactive-brokers-mcp
- stars: 227 | license: MIT | lang: JavaScript
- what: Unofficial, alpha-state MCP server for Interactive Brokers that retrieves market data and positions, runs Flex Queries and places market, limit and stop orders.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: US broker execution MCP worth listing in mphinance/awesome-broker-mcp, but community and alpha, so not a stack addition.

## alpacahq/cli
- stars: 211 | license: Apache-2.0 | lang: Go
- what: Alpha Go CLI for the Alpaca Trading API for stocks and crypto, built for agents with no confirmation prompts and paper trading as default.
- category: cli
- access: both
- vs stack: adjacent
- why: Same Alpaca access as alpaca-mcp-server through a CLI, so redundant if the MCP is adopted.

## Polymarket/agent-skills
- stars: 201 | license: none | lang: unlisted
- what: An agent skill (SKILL.md plus reference files) teaching agents to authenticate, place orders, read markets, stream data and bridge assets on the Polymarket prediction market.
- category: agent-skills
- access: trades
- vs stack: noise
- why: Prediction markets and onchain bridging are outside his US equities and options trading.

## okx/agent-skills
- stars: 201 | license: MIT | lang: Shell
- what: Markdown agent skills that drive the okx CLI to trade, query market data and run grid/DCA bots on the OKX crypto exchange.
- category: agent-skills
- access: both
- vs stack: noise
- why: Crypto exchange tooling, and he is indifferent to crypto except as a tool category.

## upstox/upstox-python
- stars: 192 | license: MIT | lang: Python
- what: The official Python SDK for the Upstox API v2, covering order placement, portfolio, websocket market data and 33 options strategy examples.
- category: sdk
- access: both
- vs stack: adjacent
- why: A clean broker SDK, but Upstox is an Indian broker and his Hands layer is US-focused (traderdaddy-bridge).

## TradingGoose/TradingGoose-Studio
- stars: 172 | license: AGPL-3.0 | lang: TypeScript
- what: A self-hosted visual workflow studio where AI agents analyze market signals and portfolio state, then act through approvals, alerts, services or broker actions.
- category: agent
- access: both
- vs stack: adjacent
- why: Overlaps the Vesper LangGraph agent plus alpha-skills as a Brain/Hands pipeline, but as a visual no-code studio rather than his code-first stack.

## alpacahq/alpaca-skills
- stars: 170 | license: Apache-2.0 | lang: Python
- what: Official SKILL.md files for Alpaca's Trading and Broker APIs covering backtesting, paper trading (CLI and MCP), order placement and Broker API onboarding.
- category: agent-skills
- access: both
- vs stack: adjacent
- why: Broker-specific skills sit beside alpha-skills (analysis) and traderdaddy-bridge (broker adapter) without adding analysis he lacks.

## tigerfintech/openapi-python-sdk
- stars: 153 | license: none | lang: Python
- what: Python SDK for Tiger Brokers OpenAPI covering market data, news, trading, account and push streams.
- category: sdk
- access: both
- vs stack: adjacent
- why: Another broker SDK, for an Asia-focused broker outside his US stack.

## rcontesti/IB_MCP
- stars: 141 | license: MIT | lang: Python
- what: An MCP server on the Interactive Brokers Web API (not TWS), still under active development with possibly incomplete features.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: A community IBKR broker MCP worth a row in awesome-broker-mcp, but not a hole in his own stack.

## coinbase/agentic-wallet-skills
- stars: 128 | license: MIT | lang: JavaScript
- what: Coinbase agent wallet skills, marked deprecated in favor of Wallet MCP.
- category: agent-skills
- access: n/a
- vs stack: noise
- why: Deprecated crypto wallet skills, irrelevant to his trading.

## TermiX-official/binance-mcp
- stars: 97 | license: none | lang: TypeScript
- what: An MCP server for the Binance API to view portfolio, convert tokens and execute trades with market impact mitigation.
- category: broker-mcp
- access: trades
- vs stack: noise
- why: Crypto exchange MCP, and he is indifferent to crypto.

## bybit-exchange/skills
- stars: 95 | license: MIT | lang: JavaScript
- what: A single-URL SKILL.md that lets any AI assistant trade Bybit spot, derivatives and earn in natural language.
- category: agent-skills
- access: trades
- vs stack: noise
- why: Crypto exchange skill with no US equities or options content.

## ferdousbhai/tasty-agent
- stars: 89 | license: MIT | lang: TypeScript
- what: A tastytrade MCP server (stdio or Cloudflare Workers) with quotes, greeks, IV rank, multi-leg orders and a dry-run check that blocks orders on warnings.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Strong options-oriented tastytrade MCP, but momentum-phund-tasty already covers tastytrade tooling and the official tastytrade-mcp in this batch is the safer pick.

## sudowealth/schwab-mcp
- stars: 87 | license: none | lang: TypeScript
- what: An unofficial Schwab MCP server on Cloudflare Workers with OAuth, account and order tools, quotes, movers and option chains with greeks.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: A community Schwab broker MCP for the directory, not a capability he is missing.

## tastyware/tastytrade-cli
- stars: 79 | license: MIT | lang: Python
- what: A command line interface for Tastytrade to view option chains, trade stocks, futures and options, view portfolio and watchlists.
- category: cli
- access: both
- vs stack: adjacent
- why: Overlaps his own momentum-phund-tasty tastytrade tooling; a CLI rather than an MCP.

## binance/binance-cli
- stars: 75 | license: none | lang: Rust
- what: A simple Rust command line client for the Binance API.
- category: cli
- access: both
- vs stack: noise
- why: Crypto exchange CLI.

## longbridge/skills
- stars: 73 | license: MIT | lang: Python
- what: Thirteen agent skills over Longbridge data covering market data, technical analysis, derivatives, fundamentals, portfolio and earnings across HK, US, A-share and Singapore markets.
- category: agent-skills
- access: both
- vs stack: adjacent
- why: Analysis-style skills overlap alpha-skills, but tied to the Longbridge broker with Asia-first markets.

## jkoelker/schwab-mcp
- stars: 72 | license: MIT | lang: Python
- what: A Schwab MCP server with market data, balances, positions and equity and options orders (OCO, bracket), where trading is gated behind a Discord approval workflow and read-only mode is the default safe start.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Second community Schwab MCP, with a notable human-approval gate on orders but no new capability for his stack.

## PublicDotCom/publicdotcom-mcp-server
- stars: 67 | license: Apache-2.0 | lang: Python
- what: Public.com's MCP server for quotes, option chains and greeks, tax lots, and stock, option and crypto orders, where preflight checks run before every order except cancel and the server rather than the model decides whether an order goes out.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Official broker MCP with multi-leg options and server-side order gating, a good Hands-layer entry that traderdaddy-bridge could wrap.

## RohanAnandPandit/trading212-mcp-server
- stars: 66 | license: MIT | lang: Python
- what: An MCP server for the Trading 212 public API exposing account data, positions, orders, pies, instruments and history, plus an analysis prompt.
- category: broker-mcp
- access: n/a
- vs stack: adjacent
- why: Trading 212 is a UK and EU broker, so it is directory material rather than a hole in his stack.

## trade-it-inc/trade-it-mcp
- stars: 62 | license: CC0-1.0 | lang: unlisted
- what: A guide and skill for Trade It's hosted MCP that connects multiple brokerages to an AI assistant to review accounts and orders and trade stocks, options, crypto and futures.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: A multi-broker aggregator that overlaps the idea of traderdaddy-bridge, but as a hosted third-party service.

## passiv/snaptrade-sdks
- stars: 58 | license: MIT | lang: PHP
- what: The SDKs for SnapTrade, a unified API connecting apps to retail brokerage accounts for trading or read-only use.
- category: sdk
- access: both
- vs stack: adjacent
- why: Another unified broker layer that overlaps traderdaddy-bridge, but via a commercial key-gated service.

## elcukro/bank-mcp
- stars: 55 | license: MIT | lang: TypeScript
- what: A read-only MCP server for bank account data over Plaid, Teller, Enable Banking and Tink.
- category: data-api
- access: read-only
- vs stack: noise
- why: Banking data, not trading.

## gate/gate-skills
- stars: 50 | license: none | lang: PowerShell
- what: An open skills marketplace giving agents access to Gate's cryptocurrency exchange for trade, earn, assets and market analysis.
- category: agent-skills
- access: both
- vs stack: noise
- why: Crypto exchange skills.

## bybit-exchange/trading-mcp
- stars: 45 | license: MIT | lang: TypeScript
- what: An MCP server for Bybit's V5 API with roughly 400 tools across market data, trading, positions, assets, earn and WebSocket streams.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto exchange MCP, and the 400-tool surface is the opposite of his lean-stack preference.

## gate/gate-mcp
- stars: 45 | license: MIT | lang: Shell
- what: An MCP server exposing the Gate.io exchange API for market data, trading and account management.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto exchange MCP.

## HephaestLab/TraderHarness
- stars: 43 | license: NOASSERTION | lang: Python
- what: A leakage-resistant backtest environment for LLM trading agents with point-in-time data masking, deterministic replay and training-trajectory export, using A-share data.
- category: infra
- access: n/a
- vs stack: adjacent
- why: Evaluating an agent without lookahead leakage is not something alpha-skills backtesting is documented to do, but its data is A-share only.

## Litash/moomoo-api-mcp
- stars: 42 | license: Apache-2.0 | lang: Python
- what: An MCP server over the moomoo-api SDK for market data, account info and orders, defaulting to simulate-only paper mode unless credentials are supplied.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Community moomoo broker MCP, directory material with a safe paper default.

## PublicDotCom/claw-skill-public-dot-com
- stars: 42 | license: Apache-2.0 | lang: Python
- what: An OpenClaw skill for a Public.com account to view portfolio, get quotes and greeks, and place equity, crypto and 2-6 leg options orders including iron condors.
- category: agent-skills
- access: both
- vs stack: adjacent
- why: The skill-form sibling of Public's MCP server, with multi-leg options but no new capability for him.

## JudyaiLab/hackathon-trading-agent
- stars: 41 | license: none | lang: Python
- what: A hackathon crypto trading agent with three strategies, risk layers and ERC-8004 onchain identity, paper traded on Kraken.
- category: agent
- access: trades
- vs stack: noise
- why: A crypto hackathon entry with self-reported results.

## verygoodplugins/robinhood-mcp
- stars: 41 | license: MIT | lang: Python
- what: A read-only MCP server for Robinhood portfolio research with no trade execution.
- category: broker-mcp
- access: read-only
- vs stack: adjacent
- why: Read-only Robinhood portfolio access for the directory, though a Robinhood connector is already in his tool list.

## mphinance/momentum-mcp
- stars: 37 | license: Apache-2.0 | lang: Python
- what: His own MCP server for screening, OHLCV, technical analysis, charts and news, now with scanline merged in.
- category: data-api
- access: read-only
- vs stack: covered
- why: This is his own mphinance/momentum-mcp.

## tastytrade/tastytrade-mcp
- stars: 37 | license: NOASSERTION | lang: TypeScript
- what: The tastytrade open API MCP server for quotes, option chains, balances, positions, watchlists and order entry, with dry-run-gated orders, a read-only env switch and an environment tag on every order result.
- category: broker-mcp
- access: both
- vs stack: gap
- why: It is the official tastytrade MCP with fail-closed read-only and dry-run gates, which fits his premium-selling wheel bias and which momentum-phund-tasty (tooling, not an MCP) does not provide.

## Polymarket/polymarket-us-python
- stars: 36 | license: MIT | lang: Python
- what: The official Python SDK for the Polymarket US API with public endpoints for events and markets.
- category: sdk
- access: n/a
- vs stack: noise
- why: Prediction market SDK, outside his trading.

## caiovicentino/hyperliquid-mcp-server
- stars: 36 | license: MIT | lang: Python
- what: A Portuguese-language MCP server to trade on the Hyperliquid DEX with Claude.
- category: broker-mcp
- access: trades
- vs stack: noise
- why: Crypto DEX, and he is indifferent to crypto.

## ozmnf4/ninjatrader-mcp
- stars: 36 | license: none | lang: JavaScript
- what: An MCP server for NinjaTrader with local and cloud modes for accounts, positions, orders, market data and NinjaScript.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: A futures-platform MCP, and pinesnake targets Tradovate next, so it is related but not needed now.

## ArjunDivecha/ibkr-mcp-server
- stars: 35 | license: MIT | lang: Python
- what: An Interactive Brokers MCP server over TWS or Gateway with multi-account support, quotes, options chains, shortable shares, P&L and orders behind live-trading and size limits.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: A second community IBKR MCP with paper default and live-trading off, directory material only.

## mphinance/alpha-skills
- stars: 33 | license: MIT | lang: Python
- what: A library of AI agent skills for Claude and Gemini covering quant trading, backtesting, edge research and market intelligence.
- category: agent-skills
- access: n/a
- vs stack: covered
- why: His own repo, the Brain of the stack.

## passiv/snaptrade-cli
- stars: 33 | license: none | lang: TypeScript
- what: SnapTrade's official CLI that links brokerage accounts via OAuth, shows portfolios and executes live trades from the command line.
- category: cli
- access: both
- vs stack: adjacent
- why: Multi-broker aggregation overlaps traderdaddy-bridge, but it is a CLI on a paid aggregator, not an AI-facing adapter.

## 9crusher/mcp-server-kalshi
- stars: 32 | license: MIT | lang: Python
- what: MCP server for Kalshi prediction markets: market discovery, orderbooks, candlesticks, settlement rules and trade execution.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Prediction markets are outside his US equities and options focus.

## plaid/ai-coding-toolkit
- stars: 32 | license: MIT | lang: Python
- what: Plaid's toolkit of prompts, rules and a sandbox MCP server (mock data, docs search, sandbox tokens, webhook simulation) for building Plaid integrations.
- category: infra
- access: read-only
- vs stack: noise
- why: Banking integration dev tooling, not trading.

## webull-inc/webull-openapi-mcp
- stars: 31 | license: Apache-2.0 | lang: Python
- what: Official Webull OpenAPI MCP server giving AI assistants market data, screener, fundamentals and account/trading access for stocks, options, futures, crypto and event contracts across many regions.
- category: broker-mcp
- access: both
- vs stack: gap
- why: Vesper is Webull-oriented but needs no broker keys, and this is the official Webull order-capable MCP covering stocks and options that none of his repos provide.

## rohitsingh-iitd/robinhood-mcp-server
- stars: 30 | license: MIT | lang: Python
- what: MCP server wrapping the Robinhood Crypto API with REST and WebSocket for account management, market data and trading.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto only, and he is indifferent to crypto.

## Kucoin/kucoin-skills-hub
- stars: 29 | license: MIT | lang: unknown
- what: Skills marketplace giving agents access to the KuCoin exchange via its OpenAPI, currently GET (read-only) endpoints only.
- category: agent-skills
- access: read-only
- vs stack: noise
- why: Crypto exchange skills, irrelevant to his equities and options work.

## luno/luno-mcp
- stars: 29 | license: MIT | lang: Go
- what: MCP server for the Luno cryptocurrency exchange API.
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: Crypto exchange MCP, outside his focus.

## pashpashpash/schwab-cli
- stars: 28 | license: MIT | lang: Rust
- what: Agent-first Rust CLI with full Schwab API parity: OAuth, balances, positions, orders with preview/place/replace/cancel, quotes, option chains and streaming, with live-trading safety rails.
- category: cli
- access: both
- vs stack: adjacent
- why: Schwab execution with option chains is useful, but traderdaddy-bridge already maps brokers to the Tradier shape, so it is a candidate adapter source rather than a hole.

## thammo4/uvatradier
- stars: 28 | license: Apache-2.0 | lang: Python
- what: Python wrapper for the Tradier brokerage API covering account data, equity and option orders and market data.
- category: sdk
- access: both
- vs stack: covered
- why: traderdaddy-bridge already normalizes brokers into Tradier's API shape, and pinesnake targets Tradier.

## crypto-com/cdcx-cli
- stars: 27 | license: Apache-2.0 | lang: Rust
- what: Agent-first Rust CLI and TUI for the Crypto.com Exchange with WebSocket streaming, paper trading and an MCP tool server mode.
- category: cli
- access: trades
- vs stack: noise
- why: Crypto exchange tooling.

## dangelov/mcp-snaptrade
- stars: 26 | license: MIT | lang: Go
- what: Proof-of-concept Go MCP server that exposes SnapTrade account data to Claude.
- category: broker-mcp
- access: read-only
- vs stack: adjacent
- why: Demo-grade SnapTrade bridge, overlaps traderdaddy-bridge in purpose but adds nothing proven.

## edkdev/hyperliquid-mcp
- stars: 24 | license: MIT | lang: Python
- what: MCP server for Hyperliquid trading built on the official SDK with bracket orders, market data and vaults.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto perps DEX, outside his focus.

## 0xjmp/mcp-tradovate
- stars: 22 | license: MIT | lang: Go
- what: Go MCP server for the Tradovate platform to manage accounts and market data through Claude Desktop.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Tradovate is the next target for pinesnake, so worth knowing, but it is futures and a small community server.

## BrainDAO/mcp-polymarket
- stars: 22 | license: MIT | lang: TypeScript
- what: MCP server for Polymarket market data, order books, trading and portfolio tracking.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Prediction market, outside his focus.

## MoomooOpen/moomoo-agent-hub
- stars: 21 | license: none | lang: Shell
- what: Official moomoo skill set of 11 skills for quotes, trading, content search, technical analysis and a grid strategy via the moomoo CLI.
- category: agent-skills
- access: both
- vs stack: adjacent
- why: Official broker skills with some analysis overlap with alpha-skills and momentum-mcp, and he has no moomoo coverage.

## crypto-com/crypto-agent-trading
- stars: 21 | license: Apache-2.0 | lang: TypeScript
- what: Two agent skills for trading crypto and checking balances via the Crypto.com App and Exchange.
- category: agent-skills
- access: trades
- vs stack: noise
- why: Crypto only.

## GigabrainGG/hyperliquid-mcp
- stars: 20 | license: none | lang: Python
- what: Python MCP server for HyperLiquid perps and spot with market, limit and bracket orders and order management.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto perps, outside his focus.

## htx-exchange/htx-skills-hub
- stars: 20 | license: MIT | lang: JavaScript
- what: HTX exchange skills for AI assistants covering spot and USDT-M futures trading, market data and account management.
- category: agent-skills
- access: both
- vs stack: noise
- why: Crypto exchange skills.

## BingX-API/api-ai-skills
- stars: 19 | license: none | lang: Python
- what: Skill library for the BingX exchange API covering perpetual futures, spot, copy trading and WebSocket streams.
- category: agent-skills
- access: both
- vs stack: noise
- why: Crypto exchange skills.

## laplace0x/awesome-agent-trading
- stars: 18 | license: MIT | lang: Python
- what: Curated list of tools, MCP servers, skills and APIs for AI agent trading across US equities and options, crypto and prediction markets.
- category: meta-list
- access: n/a
- vs stack: noise
- why: A broad awesome-list that duplicates the role of awesome-broker-mcp.

## visusnet/trade-republic-mcp-server
- stars: 18 | license: MIT | lang: TypeScript
- what: MCP server plus Claude skill for Trade Republic built on a reverse-engineered unofficial API to check balances, view market data and trade.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Unofficial API for a European broker he does not use.

## zerodha/kite-cli
- stars: 18 | license: MIT | lang: Rust
- what: Official Zerodha Kite CLI and TUI with live quotes, option chains, portfolio management and order placement.
- category: cli
- access: both
- vs stack: noise
- why: Indian broker, not US markets.

## Polymarket/polymarket-us-typescript
- stars: 17 | license: MIT | lang: TypeScript
- what: Official TypeScript SDKs for Polymarket US with public and authenticated endpoints for events and trading.
- category: sdk
- access: both
- vs stack: noise
- why: Prediction market SDK.

## tigerfintech/tigeropen-skill
- stars: 17 | license: none | lang: unknown
- what: Skill plugin for Tiger Brokers OpenAPI (Python and Java SDKs) letting AI tools query quotes, place orders and manage accounts.
- category: agent-skills
- access: both
- vs stack: adjacent
- why: Tiger Brokers serves Asian markets, so it is not a likely route, but it is an official broker skill.

## longbridge/longbridge-mcp
- stars: 16 | license: Apache-2.0 | lang: Rust
- what: Rust MCP server with 164 tools for quotes, options, order routing, fundamentals, analyst ratings, calendars and portfolio analytics across US and HK markets.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Broad US options and data coverage overlaps momentum-mcp and Vesper, and the broker is HK-centric.

## webull-inc/webull-agent-skills
- stars: 14 | license: Apache-2.0 | lang: Python
- what: Older Webull OpenAPI agent skill that the README says is being archived in favor of a new repository.
- category: agent-skills
- access: both
- vs stack: noise
- why: Deprecated and superseded by the newer Webull repos.

## guangxiangdebizi/PolyMarket-MCP
- stars: 13 | license: Apache-2.0 | lang: TypeScript
- what: MCP server giving AI assistants Polymarket market data, positions and trading history.
- category: data-api
- access: read-only
- vs stack: noise
- why: Prediction market data.

## webull-inc/webull-openapi-skills
- stars: 13 | license: Apache-2.0 | lang: Python
- what: Webull agent skill that trades stocks, options, futures, crypto and event contracts and queries market data via CLI, with configurable risk controls.
- category: agent-skills
- access: both
- vs stack: adjacent
- why: Skill layer over the same official Webull API, so it only matters if the Webull MCP is adopted.

## okx/plugin-store
- stars: 12 | license: MIT | lang: Rust
- what: A store of agent plugins for OKX installed via npx skills; the README is minimal.
- category: agent-skills
- access: n/a
- vs stack: noise
- why: Crypto exchange plugin store.

## NT-NinjaTrader/mcp-skills
- stars: 11 | license: Apache-2.0 | lang: Python
- what: Agent skills that teach an assistant to trade futures through NinjaTrader MCP servers, covering sizing, structure, position health and alerting, proposing orders for approval.
- category: agent-skills
- access: both
- vs stack: adjacent
- why: Futures only, but its propose-then-approve pattern resembles Vesper's approval gate.

## nirholas/robinhood-mcp
- stars: 11 | license: Apache-2.0 | lang: TypeScript
- what: MCP servers for the Robinhood Crypto Trading API with a read-only data server and an opt-in trading server with spend caps.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto only.

## shaanmajid/prediction-mcp
- stars: 11 | license: MIT | lang: TypeScript
- what: MCP server for unified Kalshi and Polymarket market data, flagged as early development.
- category: data-api
- access: read-only
- vs stack: noise
- why: Prediction markets.

## spotware/ctrader-skills
- stars: 11 | license: NOASSERTION | lang: Python
- what: Agent skills documenting how to drive cTrader MCP servers correctly, including units, workflows and operational patterns.
- category: agent-skills
- access: n/a
- vs stack: adjacent
- why: cTrader is forex and CFD oriented, so it is only a reference for skill design.

## EklavyaSehraway/Robinhood-Mcp-Trader
- stars: 10 | license: none | lang: Python
- what: Automated weekly swing trader scanning the S&P 500 and about 110 ETFs with AI news review, a React dashboard and optional Robinhood MCP execution, paper first.
- category: agent
- access: trades
- vs stack: adjacent
- why: Overlaps Vesper as a screener-plus-LLM trading agent with a human toggle, but is a small swing-trade project.

## KyuRish/trading212-mcp-server
- stars: 10 | license: MIT | lang: Python
- what: MCP server for Trading 212 with 32 tools for portfolio analytics, order management, pies and dividends, with rate-limit handling.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Trading 212 is a UK/EU retail broker, irrelevant to his US equities and options trading.

## aryankeluskar/polymarket-mcp
- stars: 10 | license: none | lang: TypeScript
- what: MCP server for Polymarket prediction markets that searches markets, events and recent trades through the public API with no authentication.
- category: data-api
- access: read-only
- vs stack: noise
- why: Prediction markets are outside his equities and options stack.

## orkblutt/etoro-mcp
- stars: 10 | license: none | lang: TypeScript
- what: MCP server wrapping the eToro API with 34 tools, including placing limit orders and DCA ladders, with crypto examples in the README.
- category: broker-mcp
- access: both
- vs stack: noise
- why: eToro with crypto-heavy examples does not touch his US options workflow.

## PublicDotCom/publicdotcom-cli
- stars: 9 | license: Apache-2.0 | lang: Python
- what: Command-line client for the Public.com Trading API to authenticate, view portfolio and quotes, run preflight checks and submit order requests.
- category: cli
- access: both
- vs stack: adjacent
- why: Another US broker entry for the awesome-broker-mcp directory, but he has no Public.com account in his stack and traderdaddy-bridge already normalizes brokers.

## capital-com-sv/capital-mcp
- stars: 9 | license: MIT | lang: Python
- what: MCP server for the Capital.com Open API that lets an LLM access a Capital.com trading account, with trading on by default and a demo-account warning.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Capital.com is a CFD broker, irrelevant to his US equities and options.

## kea0811/ig-trading-mcp
- stars: 9 | license: NOASSERTION | lang: JavaScript
- what: Node.js client for the IG REST API with a built-in MCP server of 21 tools for forex, indices and commodities trading.
- category: broker-mcp
- access: both
- vs stack: noise
- why: IG is a CFD and forex broker, not his market.

## patrickpxp/ibkr-mcp-server
- stars: 9 | license: MIT | lang: Python
- what: MCP server for Interactive Brokers via TWS API in Docker, exposing account data, positions, orders, executions, contracts and market data snapshots, with a skill included.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: IBKR is a real US options broker but he has no IBKR leg in his stack, and traderdaddy-bridge already maps brokers to Tradier's shape.

## revolut-engineering/revolut-agent-skills
- stars: 9 | license: none | lang: Python
- what: Official Revolut collection of agent skills teaching Claude Code, Cursor and Copilot how to use Revolut services, in technical preview.
- category: agent-skills
- access: n/a
- vs stack: noise
- why: Revolut is a consumer fintech bank, not a US trading venue.

## xyonium/futu-opend-mcp
- stars: 9 | license: MIT | lang: Python
- what: MCP server exposing Futu OpenD read-only research quote APIs (prices, financials, news, shareholders, macro) through an already-logged-in gateway, with no trading.
- category: data-api
- access: read-only
- vs stack: noise
- why: Futu serves HK and China markets and he already has momentum-mcp and Vesper for US research data.

## alpacahq/agentic
- stars: 8 | license: MIT | lang: not stated
- what: Alpaca's official multi-platform plugin marketplace covering hosted MCP, a local Trading MCP, and the Alpaca Trading CLI for the Trading, Market Data and Broker APIs.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Official Alpaca agent tooling worth listing in the directory, but he has no Alpaca leg and traderdaddy-bridge already maps brokers into Tradier's shape.

## davdunc/mcp_etrade
- stars: 8 | license: none | lang: Python
- what: E*TRADE MCP server with OAuth 1.0a, account management, R-multiple risk calculations, watch lists, option chains, alerts and trading guardrails.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: US options broker MCP with built-in risk guardrails, but he has no E*TRADE leg; duplicates kerryjiang/OpenEtradeMcp in this batch.

## gemini/developer-platform
- stars: 8 | license: NOASSERTION | lang: TypeScript
- what: Gemini crypto exchange developer suite with an MCP server, Go and TypeScript SDKs, samples and Claude Code skills.
- category: sdk
- access: both
- vs stack: noise
- why: Crypto exchange tooling, and he is indifferent to crypto.

## PublicDotCom/publicdotcom-perplexity-skill
- stars: 7 | license: Apache-2.0 | lang: Python
- what: Agent skill for Perplexity Computer to use a Public.com account: portfolio, quotes, option chains and greeks, and placing equity, crypto and multi-leg options orders.
- category: agent-skills
- access: both
- vs stack: adjacent
- why: Duplicates PublicDotCom/publicdotcom-agent-skill in this batch, and multi-leg options are already reachable through his Tradier-shaped bridge.

## bhavesh0009/angel-one-mcp-server
- stars: 7 | license: MIT | lang: Python
- what: MCP server for Angel One SmartAPI covering Indian equity, commodity and derivatives portfolio, orders, GTT rules and market data.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Indian broker, outside his US market focus.

## oilst/kraken-mcp
- stars: 7 | license: MIT | lang: Python
- what: MCP server exposing the Kraken Pro REST API (orders, ticker, OHLC, order book) as tools for Gemini CLI.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto exchange tooling, and he is indifferent to crypto.

## visusnet/coinbase-mcp-server
- stars: 7 | license: MIT | lang: TypeScript
- what: Coinbase Advanced Trading MCP server plus a Claude Skill for an autonomous crypto trading agent that executes real trades.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto trading bot, outside his equities and options focus.

## webull-inc/webull-openapi-cli
- stars: 7 | license: Apache-2.0 | lang: Go
- what: Alpha-preview Go CLI for the Webull OpenAPI to trade stocks, options, futures, crypto and event contracts, with JSON output, dry-run, order confirmation and OAuth device auth.
- category: cli
- access: both
- vs stack: gap
- why: Webull is the broker Vesper is oriented to, and this is an official agent-first CLI with dry-run and structured output that nothing in his stack wraps; webull_indicators only does desktop indicators.

## bybit-exchange/bybit-skills-hub
- stars: 6 | license: none | lang: not stated
- what: Bybit skill file teaching agents to trade spot, perpetuals, inverse and options on Bybit through 274 API endpoints via curl.
- category: agent-skills
- access: both
- vs stack: noise
- why: Crypto exchange skill, and he is indifferent to crypto.

## disciplinedware/swiftward-ai-trading-agents
- stars: 6 | license: MIT | lang: HTML
- what: Multi-agent AI trading harness with an ERC-8004 on-chain identity, a risk engine and Kraken CLI, built for a hackathon.
- category: agent
- access: trades
- vs stack: noise
- why: Crypto and on-chain hackathon project; Vesper already covers his agent needs.

## dwellir-public/hyperliquid-skills
- stars: 6 | license: MIT | lang: not stated
- what: Agent skill giving coding agents knowledge of Hyperliquid infrastructure through Dwellir: HyperEVM JSON-RPC, Info API, gRPC streaming and order book WebSocket.
- category: agent-skills
- access: n/a
- vs stack: noise
- why: Hyperliquid is a crypto perp venue, outside his stack.

## j0nl1/trade-republic-mcp
- stars: 6 | license: none | lang: Rust
- what: Rust MCP server for Trade Republic that shows portfolio, positions, P&L, ticker data, instrument search and bond analytics with 2FA login.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: Trade Republic is a European retail broker, not his market.

## parlay-run/parlay-mcp
- stars: 6 | license: MIT | lang: not stated
- what: Hosted MCP server that searches and compares prediction markets across Polymarket, Kalshi, Limitless and Manifold; the repo is only a connection reference.
- category: data-api
- access: read-only
- vs stack: noise
- why: Prediction markets are outside his stack.

## theelderwand/tradestation-mcp
- stars: 6 | license: MIT | lang: Python
- what: MCP server with 36 tools covering the TradeStation API: market data, brokerage accounts, and order execution including OCO and bracket orders, plus 5 prompts.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Solid US equities and options broker MCP, but he has no TradeStation leg and traderdaddy-bridge already maps brokers into Tradier's shape.

## zachmelin/QuestradeMCP
- stars: 6 | license: MIT | lang: JavaScript
- what: Unofficial Questrade MCP server with OAuth token refresh, accounts, positions, balances, order history, quotes and candles.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: Questrade is a Canadian broker, and the README text describes only account and market data access.

## PublicDotCom/publicdotcom-agent-skill
- stars: 5 | license: Apache-2.0 | lang: Python
- what: Public.com agent skill covering portfolio, order search with fills, tax lots, quotes, option chains and greeks, multi-leg strategy quotes, bonds and event contracts.
- category: agent-skills
- access: both
- vs stack: adjacent
- why: Public.com options coverage is broad but he has no Public.com leg; duplicates the Perplexity variant in this batch.

## adibhattar95/upstox-mcp-server
- stars: 5 | license: none | lang: Python
- what: Plugin-based MCP server for Upstox APIs for trading and fund analysis, with sandbox app setup for Claude Desktop.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Upstox is an Indian broker, outside his market.

## bostrovsky/tastytrade_MCP_Server
- stars: 5 | license: MIT | lang: Python
- what: MCP server exposing 43 TastyTrade tools with OAuth, covering stocks, options, futures and crypto orders for conversational trading in Claude Desktop and ChatGPT.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: tastytrade is options-friendly and close to his wheel style, but momentum-phund-tasty already covers his tastytrade tooling.

## gate/gate-cli
- stars: 5 | license: none | lang: Go
- what: Go CLI for the Gate crypto exchange API covering spot, futures, margin and earn, plus market intelligence info and news commands.
- category: cli
- access: both
- vs stack: noise
- why: Crypto exchange CLI, and he is indifferent to crypto.

## itsmostafa/schwab-mcp
- stars: 5 | license: MIT | lang: Go
- what: Single-binary Go MCP server for the Schwab Trader API that reads accounts and balances, pulls market data and places live trades.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Schwab is a major US equities and options broker, but he has no Schwab leg and traderdaddy-bridge already maps brokers into Tradier's shape.

## kelvingao/ibkr-mcp
- stars: 5 | license: NOASSERTION | lang: Python
- what: MCP server for Interactive Brokers with account summary, option chains, Greeks, risk monitoring, built-in strategies (covered calls, iron condors, PMCC, verticals) and playbook adjustment suggestions.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Options strategy and risk logic overlaps his wheelscope and Vesper options tooling; duplicates patrickpxp/ibkr-mcp-server on the broker side.

## kerryjiang/OpenEtradeMcp
- stars: 5 | license: Apache-2.0 | lang: C#
- what: C# MCP server exposing E*TRADE API operations as auto-generated tools with an interactive OAuth 1.0a flow, shipped as NuGet packages.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Same E*TRADE coverage as davdunc/mcp_etrade, and he has no E*TRADE leg.

## mexcdevelop/mexc-cli
- stars: 5 | license: MIT | lang: Go
- what: Go CLI for the MEXC crypto exchange with 309 operations, JSON output, read-only and dry-run flags, and generated skill docs and an MCP server.
- category: cli
- access: both
- vs stack: noise
- why: Crypto exchange CLI, and he is indifferent to crypto.

## BJLG-92/oanda-mcp-server
- stars: 4 | license: none | lang: Python
- what: REST API server for Oanda forex trading (account, positions, market and limit orders, prices, history), deployed on Railway and described as MCP-compatible.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Forex broker tooling, outside his equities and options focus.

## alan-d-smith/synthetix-alpha
- stars: 4 | license: MIT | lang: Python
- what: Autonomous risk-gated trading agent where LLM agents research strategies from arXiv, and a deterministic runtime trades options, equities and crypto on Alpaca paper, with the model never in the order path.
- category: agent
- access: trades
- vs stack: adjacent
- why: The research-to-runtime separation echoes alpha-skills plus Vesper, but it adds no capability he lacks and runs on Alpaca paper only.

## khoks/ClaudeTrading
- stars: 4 | license: none | lang: Shell
- what: Autonomous Alpaca paper-trading system driven by Claude Code skills and scheduled tasks, with scale-in and scale-out strategies and trailing stops, hard-coded to the paper API.
- category: agent
- access: trades
- vs stack: adjacent
- why: Overlaps alpha-skills and Vesper as a Claude-driven trading loop, and it is paper-only on Alpaca.

## major/schwab-agent
- stars: 4 | license: MIT | lang: Go
- what: Archived Go CLI that let AI agents trade via the Schwab API with JSON output and safety guards; the README says to use schwab-agent-rs instead.
- category: cli
- access: trades
- vs stack: noise
- why: Archived and superseded, so not worth tracking.

## maven81g/tradestation_mcp
- stars: 4 | license: none | lang: JavaScript
- what: MCP server for TradeStation with quotes, bars, option chains, account data and an order preview tool that does not execute trades.
- category: broker-mcp
- access: read-only
- vs stack: adjacent
- why: TradeStation is a broker he has no MCP for, but it is read-only and not in his wheel or Tradier flow.

## tomasgesino/schwab-mcp
- stars: 4 | license: MIT | lang: JavaScript
- what: MCP server for Schwab built for wheel management, with read tools for accounts, chains and history and write tools like sell_cash_secured_put and sell_covered_call that default to dry_run=true.
- category: broker-mcp
- access: both
- vs stack: gap
- why: Adds wheel-specific order entry on Schwab with dry-run default; his wheelscope and decay-derby track the wheel but nothing places it through a broker MCP.

## Impa-Ventures/hyperliquid-mcp
- stars: 3 | license: MIT | lang: TypeScript
- what: MCP server wrapping the Hyperliquid SDK with wallet-keyed tools for clearinghouse state on that onchain exchange.
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: Crypto perp DEX, and he is indifferent to crypto.

## cejor6/kalshi-mcp-server
- stars: 3 | license: MIT | lang: Python
- what: Self-hosted MCP server for Kalshi prediction markets with RSA-PSS auth, rate limiting, 26 tools and a two-step prepare/confirm order flow with safety caps.
- category: broker-mcp
- access: trades
- vs stack: noise
- why: Prediction markets, not US equities or options.

## dcsoft4/schwab_cli
- stars: 3 | license: NOASSERTION | lang: Python
- what: Python scripts giving CLI access to a Schwab account: quotes, market and limit orders, balances, positions, and entry helpers like buy-low or breakout orders.
- category: cli
- access: trades
- vs stack: adjacent
- why: Schwab CLI with token modules, but he already routes brokers through traderdaddy-bridge and has no Schwab need stated.

## longportapp/longport-mcp
- stars: 3 | license: Apache-2.0 | lang: Rust
- what: Official open-source MCP server for LongPort developers, hosted at mcp.longportapp.com with OAuth 2.1 and Prometheus metrics.
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: Asia-focused broker, outside his US equities and options trading.

## morettimarco/fineco-mcp
- stars: 3 | license: none | lang: Python
- what: MCP server that ingests Fineco Bank export files into local SQLite and exposes 5 tools for cash flow and portfolio analysis.
- category: data-api
- access: read-only
- vs stack: noise
- why: Italian bank export analysis, irrelevant to his trading.

## Bitget-AI/agent-mcp
- stars: 2 | license: MIT | lang: TypeScript
- what: Official Bitget MCP server for crypto trading with 89 UTA v3 operations behind 14 intent verbs, with read-only and paper-trading modes.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto exchange, and he is indifferent to crypto.

## Manu3511/UPSTOX-MCP-Server
- stars: 2 | license: none | lang: Python
- what: MCP server for Upstox that handles OAuth and exposes tools to ask Claude about portfolio, cash and positions.
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: Indian broker, outside his markets.

## alexandermazza/kalshi-trading-mcp
- stars: 2 | license: MIT | lang: Python
- what: Kalshi MCP server with 20+ tools including weather forecasting, ensemble analysis, edge calculation and safety controls like price caps and daily limits.
- category: broker-mcp
- access: trades
- vs stack: noise
- why: Prediction markets with weather models, irrelevant to his trading.

## anaisbetts/stonex-mcp
- stars: 2 | license: MIT | lang: TypeScript
- what: TypeScript client for the StoneX Client REST API plus an MCP server, authenticated by an exported browser cookies.txt file.
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: StoneX is not part of his US equity and options flow, and the cookie auth is fragile.

## chrisguidry/etrade-mcp
- stars: 2 | license: none | lang: Python
- what: MCP server giving read-only access to E*TRADE accounts through seven tools for profiles, accounts, balances, positions and quotes.
- category: broker-mcp
- access: read-only
- vs stack: adjacent
- why: E*TRADE portfolio monitoring only; worth listing in awesome-broker-mcp but it adds no trading path or analysis.

## cmike444/tastytrade-mcp
- stars: 2 | license: none | lang: Python
- what: MCP server for TastyTrade with 72 tools over the full API, DXLink real-time quotes, options Greeks, OAuth 2.1 and stdio or HTTP transport.
- category: broker-mcp
- access: both
- vs stack: gap
- why: Adds a full tastytrade trading and options Greeks path; he only has momentum-phund-tasty tooling and trading-agent is Webull-oriented.

## enderekici/trading212-mcp
- stars: 2 | license: MIT | lang: TypeScript
- what: Comprehensive MCP server for Trading 212 covering account, portfolio, order execution and history, deployable via Docker.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Trading 212 is a UK and EU broker, outside his US flow.

## florinel-chis/oanda-mcp
- stars: 2 | license: MIT | lang: Python
- what: MCP server for the OANDA v20 API with 22 read tools and 7 write tools that are only registered when trading is enabled, practice environment by default.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Forex and CFD broker, outside his equities and options focus.

## iwanbk/moomoo-mcp
- stars: 2 | license: NOASSERTION | lang: Go
- what: Go MCP server for Moomoo/Futu offering read-only tools for system health, market data and account info with token-efficient columnar output.
- category: broker-mcp
- access: read-only
- vs stack: adjacent
- why: Moomoo has US access and the gated read-only design is clean, but it duplicates data he already gets from momentum-mcp.

## ozmnf4/tradovate-mcp
- stars: 2 | license: none | lang: JavaScript
- what: MCP server for Tradovate that reads positions and balances, places, modifies and cancels orders, gets quotes and depth, and manages price alerts.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Futures broker; relevant only because pinesnake lists Tradovate as its next target.

## rock3r/fineco-helper
- stars: 2 | license: Apache-2.0 | lang: Rust
- what: Single Rust binary exposing an owner-only remote MCP over read-only Fineco portfolio, market, tax and order data with credential isolation.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: Italian bank, irrelevant to his trading.

## weig/schwab_cli
- stars: 2 | license: MIT | lang: Python
- what: Terminal CLI and MCP server for the Schwab API with quotes, option chains, accounts, positions, history and a cached volatility/IVP dataset.
- category: cli
- access: n/a
- vs stack: adjacent
- why: The cached IVP dataset overlaps Vesper options vol grading, so it is related but not needed.

## DrWheelicus/questrade-mcp-server
- stars: 1 | license: NOASSERTION | lang: TypeScript
- what: MCP server for the Questrade API that inspects portfolio, quotes, market history, orders and account activity through outcome-oriented tools.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: Canadian broker, outside his US flow.

## Finance-LLMs/Upstox-MCP-Server
- stars: 1 | license: none | lang: TypeScript
- what: Upstox MCP server that reads account information, started as the unofficial implementation since there is no official one.
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: Indian broker, outside his markets.

## PublicDotCom/webinar-demos
- stars: 1 | license: none | lang: Python
- what: Python demo scripts for the Public.com API: delta-targeted single legs, vertical credit spreads with risk analysis, Greeks, and preflight order placement.
- category: other
- access: trades
- vs stack: adjacent
- why: Credit spread construction by delta and DTE echoes his premium-selling bias, but he already has wheelscope and a Tradier-shaped bridge.

## agrigoryan/questrade-cli
- stars: 1 | license: MIT | lang: TypeScript
- what: Command-line wrapper for the Questrade API with JSON-first output, L1 quote streaming and full order coverage.
- category: cli
- access: both
- vs stack: noise
- why: Canadian broker, outside his US flow.

## bybit-exchange/advanced-skills
- stars: 1 | license: none | lang: Python
- what: not documented
- category: agent-skills
- access: n/a
- vs stack: noise
- why: Empty README and description, and the owner is a crypto exchange, which he does not trade.

## bybit-exchange/trading-cli
- stars: 1 | license: none | lang: TypeScript
- what: Official Bybit V5 CLI for AI agents with about 435 commands, safety caps, a kill switch and auto-registered SKILL.md files.
- category: cli
- access: trades
- vs stack: noise
- why: Crypto exchange, and he is indifferent to crypto.

## chensirui2008/schwab-mcp
- stars: 1 | license: Apache-2.0 | lang: TypeScript
- what: Self-hosted Schwab MCP server on Cloudflare Workers with zero-trust OAuth 2.1, per-client read_only or full_access scopes, real-time quotes and options Greeks.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Per-client read_only versus full_access scoping is a good safety pattern, but it is Schwab and duplicates no hole he has.

## chongkwongsheng/saxo-mcp
- stars: 1 | license: MIT | lang: Python
- what: Local MCP server for the Saxo Bank OpenAPI that defaults to the SIM environment, with write tools gated behind an env flag and confirm=True.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Saxo is a European broker, outside his US flow.

## eToro/etoro-mcp-plugin
- stars: 1 | license: none | lang: 
- what: Cursor marketplace plugin pointing at eToro's live MCP endpoint, mcp.public-api.etoro.com.
- category: broker-mcp
- access: n/a
- vs stack: adjacent
- why: Official eToro MCP endpoint worth listing, but eToro is not in his stack.

## florinel-chis/etoro-mcp
- stars: 1 | license: MIT | lang: Python
- what: MCP server for the eToro public API with 105 tools across 12 toolsets, with trading and social writes behind opt-in gates.
- category: broker-mcp
- access: both
- vs stack: noise
- why: eToro with social features, outside his flow and heavy on tools he would cut.

## gabrielcerutti/etoro-mcp-server
- stars: 1 | license: MIT | lang: TypeScript
- what: MCP server wrapping the eToro API with 35 tools for portfolio analysis, market research and trading.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Another eToro wrapper, redundant with the others in this batch and outside his flow.

## gpolydatas/ibkr-mcp-server
- stars: 1 | license: Apache-2.0 | lang: Python
- what: MCP server for Interactive Brokers through TWS or IB Gateway: quotes, historical data, positions, and placing, modifying and cancelling orders across asset classes.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: IBKR is a major broker without a spot in his stack, but traderdaddy-bridge is his answer to multi-broker routing.

## ivanrad07/degiro-mcp
- stars: 1 | license: MIT | lang: Python
- what: Read-only MCP server for DEGIRO with portfolio, cash, trades and dividends, and an HTTP guard that blocks every non-read request.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: European broker, outside his US flow.

## jaketuring999/fidelity-mcp
- stars: 1 | license: none | lang: TypeScript
- what: Unofficial local MCP server with six read-only tools for Fidelity accounts, balances, positions, tax lots and performance, using your existing Chrome session.
- category: broker-mcp
- access: read-only
- vs stack: adjacent
- why: Fidelity is a US broker with tax lot reads, but it is read-only and browser-session based.

## jgalea/saxo-mcp
- stars: 1 | license: MIT | lang: TypeScript
- what: Read-only MCP server for the Saxo Bank OpenAPI covering portfolio, balances, positions, orders, instruments and prices, with no trading surface.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: European broker and a duplicate of the other Saxo server here.

## jiaweitang22/claude-fidelity-mcp
- stars: 1 | license: MIT | lang: TypeScript
- what: MCP server that drives the Fidelity website through Playwright browser automation (user logs in with 2FA themselves), exposing accounts, positions, quotes, dry-run-by-default orders, staged orders, rebalance plans and transfers.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Fidelity has no public API and the README itself warns this may violate ToS, so it is a fragile scrape worth listing in awesome-broker-mcp as community-only, not something to add to the lean stack.

## longbridge/extras-skills
- stars: 1 | license: MIT | lang: unspecified
- what: Prompt-only Agent Skills for Longbridge that are explicitly non-trading and non-financial (quizzes, engagement tools), needing no CLI, MCP or login.
- category: agent-skills
- access: n/a
- vs stack: noise
- why: The README says these skills are not about securities or trading, so they do nothing for his trading stack.

## mcp-research/sharplygroup__xtb-mcp-server
- stars: 1 | license: none | lang: unspecified
- what: MCP server exposing the XTB API (via the xtb-api-js library) for account data, margin, trades, trade history and tradeTransaction, with demo or live credentials.
- category: broker-mcp
- access: both
- vs stack: noise
- why: XTB is a non-US CFD/forex broker with no license declared, and he trades US equities and options.

## mgcrea/mcp-tastytrade
- stars: 1 | license: MIT | lang: TypeScript
- what: MCP server for the TastyTrade API with OAuth2 refresh, DXLink quote snapshots, option chains with greeks, expected move and opt-in trading tools.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Tastytrade is a broker he already touches via momentum-phund-tasty, but this is one of four near-identical tastytrade MCPs in the batch and adds nothing his stack lacks beyond a broker connector.

## mphinance/traderdaddy-sdk
- stars: 1 | license: MIT | lang: TypeScript
- what: Typed isomorphic SDK for the TraderDaddy Pro MCP API, the shared client behind DaddyBoard, DaddyBot, DaddyLens, DaddyMCP, DaddyHome and DaddyEmbed.
- category: sdk
- access: read-only
- vs stack: covered
- why: This is his own repo (mphinance/traderdaddy-sdk), already the shared client for the daddy-* family.

## mphinance/trading-agent
- stars: 1 | license: MIT | lang: Python
- what: Vesper, a LangGraph trading agent for Webull plus a 56-tool keyless MCP server (screeners, options vol grading, EDGAR filings, dealer gamma, ETF flow) and an owner-only 83-tool server.
- category: agent
- access: both
- vs stack: covered
- why: This is his own repo (mphinance/trading-agent, Vesper) and it is the spine of his stack.

## nutdnuy/QuantCornerBacktestingWebullMCP
- stars: 1 | license: NOASSERTION | lang: Python
- what: Suite of eight AI skills for long-only strategy research on top of an existing Webull MCP: setup, strategy design, data audit, backtest, validation, explanation and an HTML report.
- category: agent-skills
- access: read-only
- vs stack: covered
- why: Backtesting and validation skills are what mphinance/alpha-skills already provides, and the long-only focus does not fit his premium-selling approach.

## rangertaha/coinbase-mcp
- stars: 1 | license: MIT | lang: Go
- what: Go MCP server wrapping the Coinbase Advanced Trade API with toolsets, prompts and a CLI.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto exchange connector and he is indifferent to crypto except as a tool category.

## rishabjn10/Axion-Trader
- stars: 1 | license: none | lang: Python
- what: Autonomous crypto trading agent for Kraken using Gemini Flash, a rule engine, multi-timeframe confluence and three-tier risk management, with paper and live modes.
- category: agent
- access: trades
- vs stack: noise
- why: Crypto-only agent on Kraken, and Vesper already covers his agent-with-risk-gate pattern for equities and options.

## sblattj/etrade-mcp
- stars: 1 | license: MIT | lang: TypeScript
- what: MCP server for the E*TRADE Account and Order APIs with OAuth 1.0a, VIP-TOTP auto-renew, always-on account reads and opt-in order placement (equity, options, multi-leg spreads) behind a code-enforced two-step handshake.
- category: broker-mcp
- access: both
- vs stack: gap
- why: A US equity and options broker with multi-leg spread support and a preview-then-place handshake, and none of his repos connect to E*TRADE.

## tradernet-api/tradernet-mcp-claude
- stars: 1 | license: MIT | lang: unspecified
- what: Setup guide and config for the hosted Tradernet (Freedom) MCP endpoint, authenticated with API key and secret, covering quotes, portfolio, orders, news and alerts.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Freedom Finance Tradernet is not a broker he trades through, and this repo is a connection guide for a hosted endpoint.

## upstox/upstox-plugin-marketplace
- stars: 1 | license: MIT | lang: unspecified
- what: Claude Code plugin marketplace that installs the Upstox skill and MCP for trading NSE, BSE and MCX markets.
- category: agent-skills
- access: both
- vs stack: noise
- why: Indian-market broker plugin, outside his US equities and options focus.

## upstox/upstox-skills
- stars: 1 | license: MIT | lang: Python
- what: Agent Skill (SKILL.md standard) for the Upstox Developer API: order execution, market feeds and portfolio reads on NSE, BSE and MCX.
- category: agent-skills
- access: both
- vs stack: noise
- why: Indian-market broker skill, not relevant to US trading.

## varonmiranda/webull-claude-quant-bot
- stars: 1 | license: none | lang: Python
- what: not documented
- category: agent
- access: n/a
- vs stack: adjacent
- why: The description only claims an AI fundamental trading agent on Bloomberg, Capital IQ, Claude and Webull OpenAPI, which brushes Vesper's Webull orientation but the README has no content to confirm anything.

## vsoneji/schwab-mcp
- stars: 1 | license: none | lang: TypeScript
- what: Unofficial local MCP server for Charles Schwab with OAuth 2.0 PKCE, account and order tools, quotes, price history, movers and options chains, with account-identifier scrubbing.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Schwab is a major US options broker he does not cover, but this is unofficial with no license and its market data tools overlap momentum-mcp and Vesper, so it is a directory entry more than a gap.

## walkerhughes/tastytrade-mcp
- stars: 1 | license: none | lang: Python
- what: 12-tool TastyTrade MCP server built around trader questions (portfolio with P/L rollup, market data snapshot with IV metrics, option chain summary, preview/place/cancel order).
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Another tastytrade connector overlapping mgcrea/mcp-tastytrade and his own momentum-phund-tasty tooling, with no license declared.

## yogyrahmawan/tiger-mcp
- stars: 1 | license: MIT | lang: Go
- what: Go MCP server that reads Tiger Brokers market data, positions, assets and order history, and never places, modifies or cancels orders.
- category: broker-mcp
- access: read-only
- vs stack: adjacent
- why: Tiger is a lesser-used broker for him, but the structural read-only guarantee is a pattern worth noting for the directory.

## AjvoGod/trading212-mcp
- stars: 0 | license: MIT | lang: Python
- what: Read-only MCP server for Trading212 with raw account endpoints plus derived analytics (FIFO holding period, value test, allocation, realized P/L, dividends).
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: Trading212 is a UK and EU retail broker and this is a long-term holdings analyzer, not a premium-selling or momentum tool.

## BrainDAO/mcp-kalshi
- stars: 0 | license: none | lang: TypeScript
- what: MCP server for Kalshi prediction markets covering market discovery, pricing, order books, portfolio and limit or market orders.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Prediction markets are not equities or options and are outside what he trades.

## IG-incubator/IG-Skills
- stars: 0 | license: none | lang: unspecified
- what: SKILL.md definitions mapping natural language to IG Trading Platform REST calls for spot positions, market data, account and watchlists.
- category: agent-skills
- access: both
- vs stack: noise
- why: IG is a CFD and spread-betting platform, not his US equities and options workflow.

## MoomooOpen/moomoo-agent-plugin
- stars: 0 | license: MIT | lang: unspecified
- what: Plugin bundling a moomoo MCP and skills for quotes, stock screening, news and real or simulated trading, packaged for Claude Code, Cursor and Codex.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: moomoo trades US equities and options and has a simulated mode, but its quotes and screening overlap momentum-mcp and Vesper, so it is a directory entry rather than a gap.

## MoomooOpen/moomoo-cli
- stars: 0 | license: MIT | lang: Go
- what: Command-line tool for moomoo OpenAPI covering OAuth login, market data, trading, crypto trading, configuration and self-update.
- category: cli
- access: both
- vs stack: adjacent
- why: Same moomoo surface as moomoo-agent-plugin as a plain CLI, useful to know but not needed.

## OrestisStefanou/CoinbaseMcpServer
- stars: 0 | license: none | lang: Python
- what: Small MCP server for Coinbase Advanced Trade with product search, portfolio breakdown, order history and market order creation.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Crypto exchange connector and a near duplicate of rangertaha/coinbase-mcp.

## PublicDotCom/15-minute-prediction-market-bot
- stars: 0 | license: none | lang: Python
- what: Local Python bot with a browser dashboard that trades Public.com 15-minute prediction-market event contracts on BTC, ETH, gold and forex using price-range rules, take-profit, stop-loss and daily loss limits.
- category: agent
- access: trades
- vs stack: noise
- why: Event contracts on crypto and forex, not equities or options premium selling.

## Sambhram1/upstox-skill
- stars: 0 | license: none | lang: unspecified
- what: not documented
- category: agent-skills
- access: n/a
- vs stack: noise
- why: Empty README, and the description shows an Indian-market (Upstox) Claude Code skill, which is irrelevant to his US trading.

## SirAdlerBD/saxo-mcp
- stars: 0 | license: MIT | lang: TypeScript
- what: Minimal MCP server for the Saxo Bank OpenAPI (accounts, balances, positions, instrument search, quotes, historical bars), read-only unless SAXO_TRADING=enabled, with OAuth PKCE.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Saxo is a European multi-asset broker; the hard-block trading gate is nice but he does not trade there.

## Truthifi/truthifi-mcp
- stars: 0 | license: MIT | lang: unspecified
- what: Hosted MCP that gives an AI one verified household financial record (accounts, holdings, fees, performance, cash flow, budget, tax preview, Truthifi Score) and cannot move money.
- category: data-api
- access: read-only
- vs stack: noise
- why: Personal-finance and advisor-oversight aggregation, not trading signals or execution.

## Vanguard-oss/vanguard-advisor-tools
- stars: 0 | license: none | lang: Python
- what: not documented
- category: agent-skills
- access: n/a
- vs stack: noise
- why: The description says skills for Vanguard advisors backed by approved fund data, which is advisor and fund material unrelated to his trading.

## a9lim/tasty-mcp
- stars: 0 | license: AGPL-3.0 | lang: Python
- what: Tastytrade MCP server whose write tools are gated by a hard cap on total potential max-loss across positions and working orders (default $100), rejecting short equity and naked short calls, always allowing closing orders, with a rate limit.
- category: broker-mcp
- access: both
- vs stack: gap
- why: Adds an exposure-bounded order gate for LLM-driven options trading on tastytrade, which fits a small account selling premium and which none of his tooling enforces at the broker-MCP layer, though AGPL-3.0 limits reuse.

## abigaillhiggins/tradezero-mcp
- stars: 0 | license: MIT | lang: Python
- what: Read-only MCP server for TradeZero that syncs fills into a local SQLite journal, matches round trips and serves stats and fees, with a GET-only whitelisted client so it structurally cannot trade.
- category: broker-mcp
- access: read-only
- vs stack: adjacent
- why: A trade-journal-from-fills pattern is related to decay-derby tracking, but it is TradeZero-specific and he does not use that broker.

## agustinsacco/questrade-mcp
- stars: 0 | license: MIT | lang: JavaScript
- what: Read-only MCP server for Questrade covering balances, positions, activities, executions, orders, quotes, option chains with Greeks, candles, technicals and cross-account portfolio reports with context-safe pagination.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: Questrade is a Canadian broker and its technicals and option-chain tools overlap momentum-mcp and Vesper.

## aobathree/oanda-mcp
- stars: 0 | license: MIT | lang: Python
- what: Read-only MCP server for the OANDA v20 API with live prices, candles, account summary, positions, orders and transactions (README in Japanese).
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: Forex broker connector, outside his equities and options focus.

## bharadwajpro/tastytrade-mcp
- stars: 0 | license: none | lang: Go
- what: Configurable Go MCP server for tastytrade covering option chains, quotes, IV rank and percentile, DxLink streaming, balances, positions, margin, watchlists and gated order placement with TT_READ_ONLY=true as default.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: The fullest of the tastytrade MCPs in this batch with a read-only-by-default safety model, but still a duplicate of connectors he can already use and no license declared.

## bholzer/tastytrade-mcp
- stars: 0 | license: none | lang: TypeScript
- what: Lean single-tenant TypeScript MCP server for tastytrade built on the official @tastytrade/api SDK, with env-var auth, no database and stdio transport.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Yet another tastytrade connector overlapping mgcrea/mcp-tastytrade, with no license declared and a README excerpt that does not list its tools.

## deriv-com/deriv-api-plugin
- stars: 0 | license: MIT | lang: unspecified
- what: Plugin for Cursor, Claude Code, Codex and others that adds a hosted Deriv API docs MCP plus Agent Skills for building trading apps, trade types and lifecycle.
- category: agent-skills
- access: n/a
- vs stack: noise
- why: Deriv is a synthetic and binary options platform and this is an API-knowledge plugin for building apps, not for his trading.

## dersyshore7/tradestation-mcp-scanner
- stars: 0 | license: none | lang: TypeScript
- what: HTTP MCP server that scans a static universe of about 500 liquid options names via TradeStation data and returns a best ticker and a trade card, read-only, with separate paper/live automation lanes.
- category: broker-mcp
- access: read-only
- vs stack: adjacent
- why: The screen-to-trade-card pipeline overlaps momentum-mcp and Vesper screeners, and it only adds a TradeStation data source.

## dmikhailenko-hash/claude-mcp-plugin
- stars: 0 | license: MIT | lang: unknown
- what: Claude Code plugin that registers a remote TraderEvolution MCP server for orders, positions, account state and market data.
- category: broker-mcp
- access: trades
- vs stack: noise
- why: TraderEvolution is a niche platform with no sign of US options support, and it is a thin plugin manifest around a hosted server.

## etoro-builders/etoro-agent-skills
- stars: 0 | license: none | lang: unknown
- what: Markdown skills that teach runtime LLM agents to trade on the eToro Public API, covering single trades, bulk builds, rebalancing, conditional rules and safety norms such as confirmation and 401 handling.
- category: agent-skills
- access: trades
- vs stack: adjacent
- why: The confirmation and pending-vs-filled safety norms are a useful pattern next to alpha-skills, but eToro is not his broker set.

## fi222/tradier-mcp
- stars: 0 | license: none | lang: JavaScript
- what: Node MCP server exposing Tradier balances, positions, orders, gain/loss, quotes, option chains, and equity order placement and cancel, sandbox by default.
- category: broker-mcp
- access: both
- vs stack: covered
- why: traderdaddy-bridge already maps every broker into Tradier's API shape, and this is a thin wrapper with equity-only order placement.

## forsmark/saxo-cli
- stars: 0 | license: none | lang: TypeScript
- what: JSON-first Node CLI over the Saxo Bank OpenAPI that defaults to SIM and gates mutating trade commands behind explicit human permission.
- category: cli
- access: both
- vs stack: noise
- why: Saxo is a non-US broker and the CLI adds nothing to a US equities and options stack.

## harinivenkat02/QuestradeMCP
- stars: 0 | license: MIT | lang: JavaScript
- what: Unofficial MCP server for the Questrade API with OAuth refresh, accounts, positions, balances, order history, quotes, symbol search and candles.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: Questrade is a Canadian broker and this one is read-only, so it fills no US hole.

## hvilleg-dev/OANDA-MCP
- stars: 0 | license: none | lang: Python
- what: Production-style MCP and REST server for the OANDA v20 API, with 7 tools covering 37 actions, circuit breaker, rate limiting and 391 passing tests.
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: OANDA is forex and CFD, which is outside his US equities and options focus.

## jaenster/degiro-mcp
- stars: 0 | license: MIT | lang: Zig
- what: Remote and local MCP server in Zig for DeGiro via its private web API, reading portfolio, orders, transactions and prices and optionally placing orders, with TOON-compact output.
- category: broker-mcp
- access: both
- vs stack: noise
- why: DeGiro is a European broker built on an unofficial private API.

## jluzny/ibkr-mcp-rs
- stars: 0 | license: none | lang: Rust
- what: Rust MCP server for Interactive Brokers exposing quotes, account info, positions and gateway status, with order placement infrastructure that is described as extensible rather than finished.
- category: broker-mcp
- access: read-only
- vs stack: adjacent
- why: IBKR is a US-capable broker he does not cover, but the README gives no options chain or finished order tooling, so it is only a lead.

## jonathansudhakar1/tradestation-cli-mcp
- stars: 0 | license: MIT | lang: Python
- what: Python library, CLI (`ts`) and MCP server (`ts-mcp`) wrapping all 42 TradeStation v3 REST endpoints, with streaming data for stocks, options, futures and crypto plus accounts, positions and order execution.
- category: broker-mcp
- access: both
- vs stack: gap
- why: TradeStation is a US options and futures broker with a full order API, and nothing in his stack is built around it.

## joncovington/tastytrade-mcp
- stars: 0 | license: MIT | lang: Python
- what: MCP server for Tastytrade using OAuth2 and the official SDK, with keyring-stored credentials, option strategy building, account and order inspection, and live trading gated behind ENABLE_LIVE_TRADING.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: He already has momentum-phund-tasty for tastytrade, so this is a safer-gated alternative rather than a new capability.

## jramkissoon/mcp-coinbase
- stars: 0 | license: Apache-2.0 | lang: Go
- what: Go MCP server for public Coinbase Advanced Trade market data (spot prices, L2 books, OHLCV candles, trades), no authentication required.
- category: data-api
- access: read-only
- vs stack: noise
- why: Crypto market data, and he is indifferent to crypto.

## k1xme/schwab-mcp
- stars: 0 | license: none | lang: Python
- what: Streamable-HTTP MCP server with 18 Schwab tools covering quotes, option chains, price history, movers, accounts, and order list, preview, place, cancel and replace, plus a Claude Code plugin of six skills for tool selection and safety.
- category: broker-mcp
- access: both
- vs stack: gap
- why: Schwab with option chains and full order management is a major US broker his stack does not reach, and the bundled skills cut LLM roundtrips.

## kadengriffith/kalshi
- stars: 0 | license: none | lang: Python
- what: Agent skill and Python CLI for querying Kalshi prediction markets, orderbooks, balances and trades, with a working directory for prompts, learnings and portfolio snapshots.
- category: agent-skills
- access: both
- vs stack: noise
- why: Prediction markets are outside US equities and options.

## koreyboone/fidelity-mcp
- stars: 0 | license: none | lang: JavaScript
- what: MCP bridge that drives Fidelity Trader+ Desktop through the WebView2 Chrome DevTools Protocol to read and control the ChartIQ chart from a WSL2 agent.
- category: broker-mcp
- access: n/a
- vs stack: adjacent
- why: It is the only route to Fidelity that does not use an official API, but it is a Windows-only CDP hack that controls chart state.

## lwsinclair/wealthsimple-mcp-server
- stars: 0 | license: none | lang: unknown
- what: Wealthsimple MCP server with limited tools for searching promotions and Help Centre articles and checking service status.
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: Canadian broker, and it only serves help articles and promotions, with no accounts or trading.

## m-turnergane/qte-mcp-trading-engine
- stars: 0 | license: none | lang: Python
- what: Python monorepo for a semi-autonomous trading engine that started on Questrade and is pivoting to IBKR live-shadow mode, with fail-closed config and the broker disabled by default.
- category: agent
- access: n/a
- vs stack: adjacent
- why: The fail-closed live-versus-shadow safety design is a reference worth reading for Vesper, but this is an unfinished skeleton with no orders.

## markvalderrama001-svg/tastytrade-mcp
- stars: 0 | license: MIT | lang: JavaScript
- what: 42-tool Tastytrade MCP Worker that dry-runs every order, requires an operator switch plus per-order chat confirmation for live orders, and reports performance versus SPY and QQQ.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Strong gate matrix and options-book reads, but momentum-phund-tasty already covers tastytrade for him.

## Mathuran/questrade-mcp
- stars: 0 | license: MIT | lang: TypeScript
- what: Deno MCP server for Questrade with outcome-oriented tools that bundle several API calls into one answer, read-only because the place and cancel tools are implemented but disabled.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: Canadian broker and read-only.

## mattiad19/trade-republic-mcp
- stars: 0 | license: MIT | lang: TypeScript
- what: Local read-only macOS MCP server for Trade Republic using an unofficial API, with an enforced topic allowlist and no buy, sell or cancel tools.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: European retail broker on an unofficial API, and read-only.

## nawesan12/ctrader-mcp
- stars: 0 | license: none | lang: TypeScript
- what: Remote HTTP MCP server for a cTrader demo account that reads the account, runs deterministic smart-money-concepts analysis, and places orders under server-enforced risk limits with a journal.
- category: broker-mcp
- access: both
- vs stack: noise
- why: cTrader is a forex and CFD platform and the analysis is SMC, which does not fit his wheel and momentum approach.

## ozmnf4/tastytrade-mcp
- stars: 0 | license: none | lang: JavaScript
- what: MCP server for Tastytrade that reads accounts, positions, quotes, option chains and watchlists and can place, modify and cancel orders, with a sandbox mode.
- category: broker-mcp
- access: both
- vs stack: adjacent
- why: Another tastytrade wrapper next to momentum-phund-tasty, with no gating details in the README.

## pipeworx-io/mcp-tradier
- stars: 0 | license: MIT | lang: JavaScript
- what: Pipeworx gateway MCP exposing Tradier option chains with greeks, IV and open interest, expirations and related stock and options market data.
- category: data-api
- access: read-only
- vs stack: covered
- why: Tradier option chain data already comes through traderdaddy-bridge, and Vesper's options vol grading goes further.

## rahul91-ai/upstox-custom-mcp
- stars: 0 | license: none | lang: Python
- what: not documented
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: The README is empty and Upstox is an Indian broker, so it is irrelevant to a US trader.

## sajneb/saxo_mcp
- stars: 0 | license: none | lang: Python
- what: Python MCP server for Saxo OpenAPI covering accounts, positions, orders, quotes and charts with a precheck, place and cancel flow, SIM by default and live opt-in.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Saxo is a non-US broker and the third Saxo wrapper in this batch.

## sheikhomer/T212MCP
- stars: 0 | license: none | lang: TypeScript
- what: Trading212 MCP server with a single read-only GetPortfolio tool.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: UK and EU retail broker with one tool.

## sigvardt/saxo-bank-mcp
- stars: 0 | license: none | lang: Python
- what: FastMCP server for Saxo Bank OpenAPI that is SIM-first with live writes disabled by default, plus portfolio, derivatives and optimisation analytics and an analytics skill.
- category: broker-mcp
- access: read-only
- vs stack: noise
- why: Saxo is not his broker; the analytics layer overlaps TraderMatrix and Vesper anyway.

## teratron/tigertrade-mcp
- stars: 0 | license: none | lang: C#
- what: MCP server that bridges to the Tiger Trade desktop terminal to read chart state and broker accounts, with order submission behind explicit safety flags and an EULA disclaimer.
- category: broker-mcp
- access: both
- vs stack: noise
- why: It depends on a desktop terminal install and unclear EULA standing, and Tiger Trade is not his platform.

## tigerfintech/tigeropen-skill-us
- stars: 0 | license: none | lang: unknown
- what: Agent Skills package for the TradeUP OpenAPI (US market) with Python and Java SDK skills for querying data, placing equity and options orders, and managing accounts.
- category: agent-skills
- access: trades
- vs stack: adjacent
- why: A US broker with options orders, but it is a small-broker SDK skill and not one he trades through.

## trade-it-inc/openclaw-skill
- stars: 0 | license: MIT | lang: Python
- what: OpenClaw skill that teaches agents to use the Trade It API to link and trade on Robinhood, E*Trade, Schwab, Webull, Public, Tastytrade, Coinbase and Kraken, with an optional mode that submits orders without a second execution step.
- category: agent-skills
- access: trades
- vs stack: adjacent
- why: One API fronting many US brokers overlaps traderdaddy-bridge, though it is a third-party hosted layer and not his own.

## trade-it-inc/skills
- stars: 0 | license: MIT | lang: unknown
- what: Developer skills that give a coding assistant the context to build onboarding and trading flows with the Trade It SDK and API.
- category: agent-skills
- access: n/a
- vs stack: adjacent
- why: Companion to the Trade It brokerage aggregator, useful only if he evaluates that layer against traderdaddy-bridge.

## upstox/mcp-server-upstox-api
- stars: 0 | license: none | lang: TypeScript
- what: MCP server for the Upstox trading API that runs locally on a Cloudflare-style dev setup with OAuth client credentials.
- category: broker-mcp
- access: n/a
- vs stack: noise
- why: Indian broker.

## venkateshTechmates/UpstoxMcp
- stars: 0 | license: none | lang: Python
- what: Upstox MCP server with 12 tools for profile, margin, quotes, and order place, cancel and book, deployable to Render with sandbox and live modes.
- category: broker-mcp
- access: both
- vs stack: noise
- why: Indian broker and a duplicate of the other Upstox servers in this batch.

## wdaniel1993/tr-cli
- stars: 0 | license: none | lang: Python
- what: Small unofficial Trade Republic CLI using push-approval login for portfolio, quotes and instrument details.
- category: cli
- access: read-only
- vs stack: noise
- why: European retail broker on an unofficial API.

## XBTFX/xbtfx-mcp-server
- stars: 0 | license: MIT | lang: TypeScript
- what: MCP server for the XBTFX Trading API that trades forex, metals, indices, crypto, stocks and energies through MetaTrader 5 accounts.
- category: broker-mcp
- access: trades
- vs stack: noise
- why: MetaTrader 5 CFD broker, outside his US equities and options focus.

## yourbourse/trade-server-mcp
- stars: 0 | license: Apache-2.0 | lang: TypeScript
- what: MCP server that lets Claude and other assistants check account, pull quotes and place or manage orders on a YourBourse Trade Server, with a client (trader) mode and a broker (admin) mode, installed via .mcpb or npx.
- category: broker-mcp
- access: trades
- vs stack: adjacent
- why: A broker MCP for one white-label trade server (YourBourse), so it is a possible entry for awesome-broker-mcp, but it adds no US equity or options screening or analytics beyond what momentum-mcp and Vesper already cover, and the README does not say which brokers run on it.
