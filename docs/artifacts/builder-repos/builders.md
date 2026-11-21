# What the builders make: repos by the people in the broker-MCP ecosystem

306 repos built by the 148 humans who work on broker MCP servers, graded against Michael's stack. Only repos with 5+ stars are included; the 0-4 star long tail was not graded.

Verdicts: noise 235, adjacent 57, covered 11, gap 3

## wshobson/agents
- stars: 42746 | lang: Python
- what: A marketplace of 93 plugins (199 agents, 185 skills, 103 commands) for coding tools, written once in Markdown and adapted to Claude Code, Codex CLI, Cursor, OpenCode and others.
- category: agent-skills
- vs stack: adjacent
- why: Same skills-as-Markdown packaging model as his alpha-skills, but aimed at software engineering, and the multi-harness generator and eval approach is worth a look.

## punkpeye/awesome-mcp-clients
- stars: 6643 | lang: 
- what: A curated list of MCP clients, pointing to glama.ai/mcp/clients for the current list.
- category: meta-list
- vs stack: noise
- why: A generic awesome-list of clients, nothing to do with brokers or trading.

## evalstate/fast-agent
- stars: 3973 | lang: Python
- what: A framework to code, build and evaluate agents with MCP, skills, ACP and A2A support (PyPI fast-agent-mcp).
- category: agent
- vs stack: adjacent
- why: A general agent framework that overlaps with the LangGraph agent in trading-agent but has no trading content.

## samyk/pwnat
- stars: 3940 | lang: C
- what: A NAT traversal tool that lets a client and server behind separate NATs connect with no third party or port forwarding.
- category: infra
- vs stack: noise
- why: Network hole punching, unrelated to trading.

## punkpeye/awesome-remote-mcp-servers
- stars: 3695 | lang: 
- what: A curated list of hosted remote MCP servers you connect to by URL.
- category: meta-list
- vs stack: noise
- why: A generic awesome-list, overlapping in spirit with awesome-broker-mcp but not broker-specific.

## punkpeye/fastmcp
- stars: 3289 | lang: TypeScript
- what: A TypeScript framework for building MCP servers, with OpenAPI to MCP conversion and auth; the README notes it targets legacy handshake-based MCP revisions.
- category: sdk
- vs stack: noise
- why: A generic MCP server framework, and his servers are Python.

## nickmccullum/algorithmic-trading-python
- stars: 2922 | lang: Jupyter Notebook
- what: The repo for the freeCodeCamp course Algorithmic Trading in Python, with an equal-weight S&P 500 fund and a quantitative momentum screen.
- category: trading-strategy
- vs stack: noise
- why: A beginner course; his momentum-mcp and scanline already cover momentum screening.

## Shpigford/chops
- stars: 2118 | lang: Swift
- what: A macOS app to browse, edit and manage AI agent skills across Claude Code, Cursor, Codex, Windsurf and Amp.
- category: tooling
- vs stack: adjacent
- why: A skill manager that could help organize the 133 skills in alpha-skills, but it is macOS only and adds no trading capability.

## he-yufeng/CoreCoder
- stars: 1934 | lang: Python
- what: A minimal readable coding agent of about 3,370 lines of Python inspired by Claude Code, positioned as the nanoGPT of coding agents.
- category: agent
- vs stack: noise
- why: A teaching-oriented coding agent, not trading related.

## punkpeye/mcp-remote
- stars: 1677 | lang: TypeScript
- what: A bridge that lets stdio-only MCP clients connect to remote MCP servers, with auth support.
- category: tooling
- vs stack: noise
- why: Generic MCP plumbing; TraderDaddy's native remote MCP is already reachable through daddymcp.

## anaisbetts/mcp-installer
- stars: 1541 | lang: JavaScript
- what: An MCP server that installs other MCP servers from npm or PyPI on request.
- category: tooling
- vs stack: noise
- why: Generic installer, no trading relevance, and he wants a lean tool stack.

## itsmostafa/aws-agent-skills
- stars: 1173 | lang: Python
- what: Skills for Claude Code and Codex covering 18 core AWS services.
- category: agent-skills
- vs stack: noise
- why: AWS cloud engineering skills, unrelated to trading.

## SecretiveShell/MCP-Bridge
- stars: 922 | lang: Python
- what: A middleware that exposes an OpenAI-compatible endpoint which can call MCP tools; the README asks for new maintainers.
- category: tooling
- vs stack: noise
- why: Generic MCP to OpenAI adapter with no trading content.

## guangxiangdebizi/FinanceMCP
- stars: 874 | lang: TypeScript
- what: A finance data MCP with 19 tools over Tushare, Qveris and Binance covering stocks, funds, bonds, macro and crypto, mainly China markets.
- category: data-api
- vs stack: noise
- why: Chinese-market and crypto data; his momentum-mcp and trading-agent already serve US equities and options.

## wshobson/maverick-mcp
- stars: 732 | lang: Python
- what: A local stock MCP server using yfinance for data, technical analysis, portfolio tracking and Python backtesting, with no API key for core tools.
- category: data-api
- vs stack: covered
- why: momentum-mcp already gives free-tool screening, OHLCV and technical analysis, and alpha-skills covers backtesting.

## nirholas/XActions
- stars: 662 | lang: HTML
- what: An X/Twitter automation toolkit with scrapers, a CLI and an MCP server with approval-gated write actions and no paid API.
- category: tooling
- vs stack: noise
- why: Social media automation; at most a distribution channel idea for Momentum Phinance, not a trading tool.

## Shpigford/nurb
- stars: 650 | lang: Python
- what: Agentic CAD for 3D printing, where an AI models parts and checks them against print physics in a live viewer.
- category: other
- vs stack: noise
- why: 3D printing, unrelated to trading.

## anaisbetts/mcp-youtube
- stars: 553 | lang: TypeScript
- what: An MCP server that uses yt-dlp to fetch YouTube subtitles for summarization.
- category: tooling
- vs stack: noise
- why: Video transcript tool with no trading relevance.

## punkpeye/awesome-mcp-devtools
- stars: 489 | lang: 
- what: A curated list of developer tools, SDKs and testing utilities for MCP server development.
- category: meta-list
- vs stack: noise
- why: A generic awesome-list for MCP development.

## domdomegg/airtable-mcp-server
- stars: 456 | lang: TypeScript
- what: An MCP server giving read and write access to Airtable bases.
- category: tooling
- vs stack: noise
- why: Airtable integration, not trading.

## GavinPHR/Multi-Agent-Path-Finding
- stars: 447 | lang: Python
- what: An anonymous multi-agent path finding library using conflict-based search and space-time A*.
- category: other
- vs stack: noise
- why: Robotics pathfinding, unrelated to the stack.

## domdomegg/computer-use-mcp
- stars: 405 | lang: TypeScript
- what: An MCP server that gives Claude full control of the local computer, with a warning about mistakes and prompt injection.
- category: tooling
- vs stack: noise
- why: Generic desktop control; the README itself warns against giving it trading-grade trust.

## evalstate/mcp-hfspace
- stars: 388 | lang: TypeScript
- what: An MCP server for using Hugging Face Spaces, now superseded by the official Hugging Face MCP server per its README.
- category: tooling
- vs stack: noise
- why: Superseded stub, unrelated to trading.

## itsmostafa/system-one-connector
- stars: 365 | lang: Go
- what: An MCP connector that gives agents access to cheap evaluation models such as Jev, D1, CLM and Laya.
- category: tooling
- vs stack: noise
- why: Model-evaluation connector with no trading content visible in the README.

## ferdousbhai/investor-agent
- stars: 349 | lang: TypeScript
- what: A financial research MCP server for long-term investors, hosted on Cloudflare Workers, that also advertises the hosted spicytrade options MCP.
- category: data-api
- vs stack: covered
- why: Research and options data (IV rank, term structure) are already covered by trading-agent's 56-tool MCP and TraderDaddy Pro.

## guangxiangdebizi/TradingAgents-MCPmode
- stars: 342 | lang: Python
- what: A multi-agent trading analysis system with 15 specialized agents, bull and bear debate rounds and three-layer risk review, using MCP tools with a Streamlit front end.
- category: agent
- vs stack: adjacent
- why: Overlaps the LangGraph agent in trading-agent; the configurable bull/bear and risk debate stages are an idea to compare, but it targets US, A-share and HK analysis, not execution.

## Shpigford/plylst
- stars: 332 | lang: SCSS
- what: A Rails app for building smart dynamic Spotify playlists.
- category: other
- vs stack: noise
- why: Music playlist app, unrelated.

## nirholas/cryptocurrency.cv
- stars: 331 | lang: TypeScript
- what: A free crypto news API aggregating 300+ sources with REST, RSS, sentiment and an MCP server.
- category: data-api
- vs stack: noise
- why: Crypto news only, and he is indifferent to crypto.

## keli-wen/agentic-harness-patterns-skill
- stars: 312 | lang: 
- what: An agent skill of harness engineering patterns (memory, permissions, context engineering, multi-agent coordination) distilled from Claude Code.
- category: agent-skills
- vs stack: adjacent
- why: Design guidance for agent harnesses that could inform trading-agent's memory and permission design, but it has no trading content.

## punkpeye/mcp-proxy
- stars: 299 | lang: TypeScript
- what: A TypeScript streamable HTTP and SSE proxy for stdio MCP servers, used by FastMCP.
- category: tooling
- vs stack: noise
- why: Generic MCP transport proxy.

## nirholas/three.ws
- stars: 284 | lang: JavaScript
- what: A platform for giving AI agents a 3D avatar body, an LLM brain and a Solana wallet, with a promoted token on pump.fun.
- category: other
- vs stack: noise
- why: Avatar and crypto token marketing, unrelated to his trading.

## Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers
- stars: 261 | lang: 
- what: A curated list of papers, benchmarks and tools on LLMs for quantitative trading, covering trading agents, benchmarks, arenas, stock prediction and factor mining.
- category: meta-list
- vs stack: adjacent
- why: A reading list that could seed new alpha-skills ideas, but it is a list, not a tool.

## guangxiangdebizi/QMT-MCP
- stars: 259 | lang: Python
- what: A modular FastMCP quant trading system on XTQuant/QMT with strategy generation, live and paper trading, backtesting and risk controls.
- category: broker-mcp
- vs stack: noise
- why: QMT is a China broker path, not usable for his US equities and options.

## keli-wen/mcp_chatbot
- stars: 252 | lang: Python
- what: A terminal and Streamlit chatbot that connects an LLM such as Qwen to MCP servers.
- category: other
- vs stack: noise
- why: A generic MCP chatbot demo.

## he-yufeng/FindJobs-Agent
- stars: 243 | lang: Python
- what: An LLM toolkit for skill analysis, AI interviews, resume scoring and job structuring.
- category: other
- vs stack: noise
- why: Job search tooling, unrelated.

## wshobson/financial-chat
- stars: 236 | lang: Python
- what: A Streamlit and FastAPI stock-analysis chat agent built on LangChain/LangGraph, OpenBB and Claude 3 Opus, with relative strength, FinViz universe scans, sentiment and R-multiple stops.
- category: agent
- vs stack: covered
- why: Screening, technicals and chart analysis are already served by mphinance/momentum-mcp and mphinance/trading-agent, which is also a LangGraph agent.

## Yijia-Xiao/FinanceHarness
- stars: 225 | lang: Python
- what: An autonomous financial deep-research CLI agent with a progressive-disclosure tool catalog and SKILL.md files that compose tools into reusable workflows, grounding every figure to its source.
- category: agent
- vs stack: adjacent
- why: The SKILL.md workflow idea parallels mphinance/alpha-skills, and the grounding-every-figure approach is worth a look, but it is a research agent rather than a trading one.

## koreainvestment/kis-ai-extensions
- stars: 223 | lang: JavaScript
- what: An npm plugin for Claude Code, Cursor, Codex and Gemini CLI that turns Korea Investment Securities OpenAPI into strategy design, Lean backtesting and signal-based order skills, with MCP server and hooks that block key leaks and force confirmation on live orders.
- category: broker-mcp
- vs stack: adjacent
- why: It is a Korean-market broker path he does not trade, though its prod-order confirmation hooks are a neat pattern next to mphinance/traderdaddy-bridge.

## luohy15/y-agent
- stars: 218 | lang: Python
- what: A personal agent app that gives web and Telegram one entry point into a cloud workspace on EC2 where Claude Code does the work.
- category: agent
- vs stack: noise
- why: A general dev-workflow agent shell with nothing trading-specific.

## GavinPHR/Space-Time-AStar
- stars: 212 | lang: Python
- what: A pathfinding library adding a time dimension to A* so routes avoid dynamic obstacles.
- category: other
- vs stack: noise
- why: Robotics path planning, unrelated to trading.

## samyk/frisky
- stars: 197 | lang: C++
- what: Frida and related tooling for reverse engineering and augmenting iOS and macOS binaries.
- category: tooling
- vs stack: noise
- why: Binary reversing tools with no trading relevance.

## he-yufeng/ContractGuard
- stars: 152 | lang: Python
- what: An AI agent that reads an uploaded contract and returns red flags, unfair terms and plain-English explanations.
- category: agent
- vs stack: noise
- why: Legal document review, not trading.

## kukapay/freqtrade-mcp
- stars: 151 | lang: Python
- what: An MCP server that drives a Freqtrade crypto bot through its REST API for AI-agent trading operations.
- category: broker-mcp
- vs stack: noise
- why: Crypto-only bot control, and he is indifferent to crypto.

## nirholas/pump-fun-sdk
- stars: 150 | lang: TypeScript
- what: A TypeScript SDK, CLI and MCP server for the Pump protocol on Solana covering bonding curves, AMM pools and creator fees.
- category: sdk
- vs stack: noise
- why: Solana memecoin tooling, off his stack.

## samyk/glitchsink
- stars: 145 | lang: C++
- what: A voltage-glitching tool that bypasses microcontroller bootloader and debugger protections without modifying the target board.
- category: tooling
- vs stack: noise
- why: Hardware security research, unrelated.

## qrak/LLM_trader
- stars: 141 | lang: Python
- what: A paper-trading LLM agent that renders a chart each closed candle, sends it with indicators and retrieved memory of its own closed trades to a multimodal model, validates with deterministic rules, and publishes the prompt, memory and every loss on a public ledger.
- category: memory
- vs stack: gap
- why: The closed-trade memory retrieval loop and public audit ledger with honest results is a technique his stack does not document, though it runs on crypto (BTC/USDC) and ccxt.

## SecretiveShell/MCP-searxng
- stars: 132 | lang: Python
- what: An MCP server exposing SearXNG web search to agents.
- category: tooling
- vs stack: noise
- why: Generic search MCP, not trading.

## kukapay/crypto-indicators-mcp
- stars: 131 | lang: JavaScript
- what: An MCP server offering 50+ crypto technical indicators and strategies for AI trading agents.
- category: data-api
- vs stack: covered
- why: Technical analysis tools are already in mphinance/momentum-mcp, and this one is crypto-focused.

## evalstate/mcp-webcam
- stars: 126 | lang: TypeScript
- what: An MCP server that captures live webcam images via a tool or resource request.
- category: tooling
- vs stack: noise
- why: Webcam capture has nothing to do with trading.

## murrlincoln/Based-Agent
- stars: 120 | lang: Python
- what: not documented
- category: other
- vs stack: noise
- why: The README is empty and the name suggests a Base-chain crypto agent, which is outside his interest.

## mr-karan/hodor
- stars: 117 | lang: TypeScript
- what: An agentic code reviewer for GitHub PRs, GitLab MRs and local diffs that gives an LLM confined inspection tools and posts structured findings as comments.
- category: tooling
- vs stack: noise
- why: Code review tooling, not trading.

## evalstate/mcp-miro
- stars: 113 | lang: TypeScript
- what: An MCP server for the Miro whiteboard covering boards, stickies and bulk operations.
- category: tooling
- vs stack: noise
- why: Whiteboard integration, unrelated.

## CadeYu/spring-alpha
- stars: 108 | lang: Python
- what: A multi-agent earnings research workbench (Spring Boot, Next.js, LangGraph, LlamaIndex RAG, PGVector) running three agents over SEC filings for earnings, sentiment and cash flow, with no trading.
- category: agent
- vs stack: adjacent
- why: Its EvidencePack RAG over SEC filings overlaps the EDGAR tools in mphinance/trading-agent, but the heavy Java stack and no-trading scope make it reference reading only.

## nirholas/crypto-vision
- stars: 97 | lang: TypeScript
- what: A self-hosted crypto intelligence REST API on Hono aggregating market, DeFi, news and on-chain data with 58 AI agents and x402 per-datapoint payments.
- category: data-api
- vs stack: noise
- why: Crypto data aggregation, off his stack.

## anaisbetts/XamarinEvolve2014
- stars: 88 | lang: C#
- what: Demo app repo for a 2014 Xamarin Evolve talk on building apps the GitHub way.
- category: other
- vs stack: noise
- why: An old conference demo, unrelated.

## congde/web3-quant-sandbox
- stars: 88 | lang: Python
- what: An offline-first Web3 quant research sandbox bundling dashboards, factor mining, backtests, risk audit, paper trading, strategy DSL and a formula-history academy, using bundled sample data and no real orders.
- category: trading-strategy
- vs stack: noise
- why: A crypto teaching sandbox with sample data, not something to adopt.

## pashpashpash/manga-reader
- stars: 87 | lang: Python
- what: Generates a narrated video recap of a manga volume PDF using GPT-4 Vision and ElevenLabs.
- category: other
- vs stack: noise
- why: Manga video generation, unrelated.

## nirholas/agenti
- stars: 84 | lang: TypeScript
- what: An MCP server and SDK giving AI agents wallets, x402 payments, market data and Solana tools.
- category: sdk
- vs stack: noise
- why: Crypto wallet and payment layer for agents, off his stack.

## tadasant/mcp-server-stability-ai
- stars: 84 | lang: TypeScript
- what: An MCP server for Stability AI image generation, editing and upscaling.
- category: tooling
- vs stack: noise
- why: Image generation, unrelated.

## guangxiangdebizi/MySQL_MCP
- stars: 81 | lang: TypeScript
- what: A MySQL MCP server with multi-database connections, CRUD, transactions and rollback, with credentials passed by header so the AI does not see them.
- category: tooling
- vs stack: noise
- why: A generic database MCP.

## maheshmurag/workshop-mcp-agent-example
- stars: 80 | lang: Python
- what: A workshop example of an orchestrator workflow that plans across agents to grade a student assignment using filesystem and fetch MCP servers.
- category: agent
- vs stack: noise
- why: A tutorial demo with a grading task, not trading.

## nutdnuy/quant-investment-papers
- stars: 80 | lang: not set
- what: A private personal library of quant papers and textbooks on alpha, factors, algo trading and portfolio management, noted as containing copyrighted material.
- category: meta-list
- vs stack: noise
- why: A private reference collection with nothing to install or reuse.

## SecretiveShell/MCP-wolfram-alpha
- stars: 76 | lang: Python
- what: An MCP server that queries the Wolfram Alpha API.
- category: tooling
- vs stack: noise
- why: A generic computation lookup, not trading.

## cliffhall/GooseTeam
- stars: 74 | lang: TypeScript
- what: An MCP server and protocol letting Goose agents register, message each other and share tasks.
- category: infra
- vs stack: noise
- why: Agent collaboration plumbing, unrelated to trading.

## guangxiangdebizi/Quant2Ptrader-MCP
- stars: 74 | lang: TypeScript
- what: An MCP server that converts JoinQuant strategy code into Ptrade platform format with a change report and risk notes.
- category: tooling
- vs stack: adjacent
- why: The strategy-converter idea mirrors mphinance/pinesnake (Pine to Python for Tradier), but it targets Chinese platforms he does not use.

## kukapay/cryptopanic-mcp-server
- stars: 74 | lang: Python
- what: An MCP server delivering CryptoPanic crypto news to AI agents.
- category: data-api
- vs stack: noise
- why: Crypto news feed, and he has financial news in mphinance/momentum-mcp.

## mr-karan/monkeybeat
- stars: 74 | lang: Python
- what: A single-file app that builds random 10-stock NSE portfolios and compares them to the benchmark index.
- category: trading-strategy
- vs stack: noise
- why: An Indian-market curiosity app testing random picks, not useful for premium selling.

## huacnlee/gpui-shell-benchs
- stars: 73 | lang: JavaScript
- what: A collection of native apps generated by AI coding agents to benchmark the gpui-shell runtime.
- category: tooling
- vs stack: noise
- why: UI framework benchmarks, unrelated.

## rhnvrm/pi-mesh
- stars: 72 | lang: TypeScript
- what: A file-based multi-agent coordination extension for Pi covering presence, messaging and file reservations without a daemon.
- category: infra
- vs stack: noise
- why: Coding-agent coordination, not trading.

## olaservo/shannon-thinking
- stars: 72 | lang: TypeScript
- what: An MCP server that structures problem solving along Claude Shannon's define, model, implement approach.
- category: tooling
- vs stack: noise
- why: A generic reasoning tool.

## zd87pl/ai-crypto-trader
- stars: 72 | lang: Python
- what: An experimental crypto trading system of microservices combining market monitoring, social sentiment, AI signals and automated execution, with a dashboard.
- category: agent
- vs stack: noise
- why: Crypto-only hobby project, and he is indifferent to crypto.

## calclavia/htm-tensorflow
- stars: 68 | lang: Python
- what: A Keras-style Tensorflow implementation of Numenta's HTM algorithm with MNIST experiments.
- category: other
- vs stack: noise
- why: Old ML research code with no trading relevance.

## crazyyanchao/llmcompiler
- stars: 65 | lang: Python
- what: An agent architecture that plans tasks as a DAG and runs them in parallel to cut LLM calls and token cost, with a SQL-query example.
- category: agent
- vs stack: adjacent
- why: Parallel function-calling planner is a pattern that could speed his LangGraph agent in mphinance/trading-agent, but it is not trading-specific.

## edkdev/defi-trading-mcp
- stars: 59 | lang: JavaScript
- what: An MCP server that lets an AI quote and swap tokens, scan memecoins and manage portfolios across 17+ blockchains.
- category: broker-mcp
- vs stack: noise
- why: DeFi execution path, which does not touch US equities or options.

## suhailkakar/prediction-market-starter-kit
- stars: 59 | lang: TypeScript
- what: A full-stack Next.js prediction-market app on Polymarket with gasless embedded wallets, search, price charts and trading.
- category: other
- vs stack: noise
- why: Polymarket frontend starter, not in his equities and options focus.

## kukapay/whale-tracker-mcp
- stars: 58 | lang: Python
- what: An MCP server that tracks crypto whale transactions through the Whale Alert API.
- category: data-api
- vs stack: noise
- why: Crypto on-chain whale data, while his whale work is equity 13F in mphinance/aftermath.

## jgalea/grocery-cli
- stars: 56 | lang: Go
- what: An agent-friendly Go CLI that searches and prices baskets across online supermarkets behind one interface.
- category: cli
- vs stack: noise
- why: Grocery shopping, unrelated to trading.

## mr-karan/nomad-events-sink
- stars: 55 | lang: Go
- what: A Go agent that collects Nomad cluster events and forwards them to sinks such as HTTP.
- category: infra
- vs stack: noise
- why: Nomad ops plumbing with no trading link.

## KyuRish/mcp-dashboards
- stars: 54 | lang: TypeScript
- what: An MCP Apps server that renders data as interactive dashboards with 32 chart tools and 21 themes inside AI clients.
- category: tooling
- vs stack: adjacent
- why: Inline chart rendering overlaps with the chart generation in mphinance/momentum-mcp but is a general dashboard layer, not a trading one.

## kukapay/crypto-feargreed-mcp
- stars: 52 | lang: Python
- what: An MCP server serving the Crypto Fear and Greed Index, real-time and historical, from Alternative.me.
- category: data-api
- vs stack: noise
- why: Crypto sentiment index only.

## nutdnuy/invest-like-apo-resources
- stars: 52 | lang: n/a
- what: A Thai-language resource kit for AI investment research: LLM wiki, book-to-skill method, source-note and decision-log templates, and a Webull referral link.
- category: agent-skills
- vs stack: adjacent
- why: Book-to-skill and decision-log templates echo mphinance/alpha-skills, and it uses the Webull API he targets, but it is a lecture resource list.

## Code-MonkeyZhang/cloud-music-mcp
- stars: 50 | lang: Python
- what: A local MCP server for NetEase Cloud Music handling login, playback and playlist collection.
- category: other
- vs stack: noise
- why: Music player integration, unrelated.

## jaenster/puppeteer-mcp-claude
- stars: 48 | lang: TypeScript
- what: A Puppeteer-based browser automation MCP server for Claude.
- category: tooling
- vs stack: noise
- why: Generic browser MCP, nothing trading specific.

## kukapay/crypto-sentiment-mcp
- stars: 47 | lang: Python
- what: An MCP server giving agents Santiment crypto sentiment balance, social volume, dominance and trending words.
- category: data-api
- vs stack: noise
- why: Crypto-only sentiment; his sentiment tooling is equity oriented.

## caiovicentino/eoq-quantization
- stars: 46 | lang: Python
- what: A quantization method for LLMs (Walsh-Hadamard rotation plus Lloyd-Max centroids) claiming smaller size than GGUF Q4_K_M with near-FP16 perplexity.
- category: other
- vs stack: noise
- why: Model compression research, not trading.

## rhnvrm/listmonk-mcp
- stars: 45 | lang: Python
- what: An MCP server for managing a self-hosted Listmonk newsletter instance: subscribers, lists, campaigns, templates and analytics.
- category: tooling
- vs stack: noise
- why: Newsletter admin, though loosely relevant to publishing; no trading overlap.

## 0xIchigo/Data-Structures-and-Algorithms-in-Rust
- stars: 45 | lang: Rust
- what: A personal collection of data structures and algorithms in Rust with explanations.
- category: other
- vs stack: noise
- why: Learning repo.

## domdomegg/programmatic-mcp-prototype
- stars: 44 | lang: TypeScript
- what: A prototype MCP agent with progressive tool discovery via search_tools/execute_tool, TypeScript code composition of tools, state persistence and skill building.
- category: agent
- vs stack: adjacent
- why: Progressive tool discovery speaks to his habit of cutting overlapping MCP tools and the 56-tool server in mphinance/trading-agent, but it is a prototype.

## guangxiangdebizi/FinanceMCP-DCTHS
- stars: 44 | lang: TypeScript
- what: An MCP server for Chinese market data through the Tushare API, covering Eastmoney and Tonghuashun sector indexes.
- category: data-api
- vs stack: noise
- why: China A-share data, not US markets.

## m-turnergane/stock-screener
- stars: 44 | lang: Python
- what: A Streamlit stock screener with sector-adjusted valuation, DCF, RSI, moving average crossovers and Plotly dashboards.
- category: data-api
- vs stack: covered
- why: mphinance/momentum-mcp and mphinance/scanline already screen with technicals and factor scoring.

## nirholas/universal-crypto-mcp
- stars: 44 | lang: TypeScript
- what: An MCP server with hundreds of EVM-chain tools for balances, gas, price feeds, wallets, DeFi and x402 payments.
- category: broker-mcp
- vs stack: noise
- why: Crypto breadth server, not his domain.

## caiovicentino/eikos
- stars: 43 | lang: Python
- what: Open 4B and 27B decision models that answer structured questions about a state in one forward pass and return calibrated probabilities per option, aimed at finance and trade finance rules.
- category: other
- vs stack: adjacent
- why: Calibrated confidence for act-or-escalate decisions could inform a risk gate, but it is a model for applying rulebooks, not a market tool.

## itsmostafa/qi
- stars: 43 | lang: Go
- what: A local SQLite search CLI that indexes notes and docs and returns ranked hits with exact file and line ranges, shipped with an agent skill and Claude Code plugin.
- category: tooling
- vs stack: adjacent
- why: Cheap retrieval over notes could back a trade journal or skills library, but nothing in it is trading specific.

## SecretiveShell/MCP-timeserver
- stars: 42 | lang: Python
- what: A simple MCP server exposing current date and time by timezone.
- category: tooling
- vs stack: noise
- why: Trivial utility.

## rock3r/maradona
- stars: 42 | lang: Kotlin
- what: A Compose Multiplatform library that renders Mermaid diagrams natively on Desktop, Android and iOS.
- category: tooling
- vs stack: noise
- why: UI rendering library with no trading link.

## caiovicentino/claude-call
- stars: 41 | lang: Python
- what: A voice-call interface for a Claude Code session using local whisper STT and edge-tts, with no API key.
- category: tooling
- vs stack: noise
- why: Voice I/O for Claude Code, not a trading capability.

## anaisbetts/mcp-computer-use
- stars: 40 | lang: Rust
- what: A Rust MCP server for mouse, keyboard and screen control that mirrors OpenAI's Computer Use tool schema.
- category: tooling
- vs stack: noise
- why: Desktop automation, nothing trading specific.

## keli-wen/cospan
- stars: 40 | lang: JavaScript
- what: A tool that orchestrates coding agents (Antigravity, Codex, Claude Code, DeepSeek Harness) through one async delegation protocol.
- category: tooling
- vs stack: noise
- why: Coding-agent orchestration, not trading.

## kukapay/uniswap-trader-mcp
- stars: 40 | lang: JavaScript
- what: An MCP server that quotes and executes Uniswap V3 swaps with slippage control across chains.
- category: broker-mcp
- vs stack: noise
- why: DEX execution, crypto only.

## kukapay/dune-analytics-mcp
- stars: 40 | lang: Python
- what: An MCP server that fetches Dune Analytics query results and runs queries, returning CSV.
- category: data-api
- vs stack: noise
- why: On-chain analytics for crypto.

## nirholas/Binance-MCP
- stars: 40 | lang: TypeScript
- what: A Binance exchange MCP server with 478+ tools covering spot data, orders, earn, staking and wallet.
- category: broker-mcp
- vs stack: noise
- why: Crypto exchange path, which he does not trade.

## warren618/AlphaForge
- stars: 39 | lang: Python
- what: A crypto perpetuals quant framework: factor mining, rolling IC and FDR evaluation, greedy combo search, walk-forward backtest with funding, liquidation and slippage, then paper and live.
- category: trading-strategy
- vs stack: adjacent
- why: The FDR-corrected factor evaluation and Newey-West metrics are a rigorous method worth borrowing for mphinance/alpha-skills, but it targets crypto perps.

## kukapay/crypto-skills
- stars: 38 | lang: Python
- what: A set of agent skills for crypto and blockchain tasks, installable through the Skills CLI.
- category: agent-skills
- vs stack: noise
- why: Crypto skills, while his mphinance/alpha-skills covers equities and options.

## nirholas/UCAI
- stars: 38 | lang: Python
- what: A Python CLI that generates MCP servers from smart contract ABIs so agents can read and call EVM contracts.
- category: tooling
- vs stack: noise
- why: Smart contract tooling, irrelevant to him.

## nirholas/defi-agents
- stars: 37 | lang: TypeScript
- what: A JSON API of 40+ DeFi, portfolio and trading agent definitions in 18 languages with a Claude Code plugin.
- category: agent-skills
- vs stack: noise
- why: DeFi agent prompt catalog, crypto focused.

## caiovicentino/polarengine-vllm
- stars: 36 | lang: Python
- what: a vLLM plugin that runs PolarQuant (now renamed HLWQ) weight-quantized LLMs using Walsh-Hadamard rotation and Lloyd-Max centroids to cut VRAM.
- category: infra
- vs stack: noise
- why: local LLM inference quantization has no bearing on his trading stack.

## nirholas/bnbchain-mcp
- stars: 35 | lang: TypeScript
- what: an MCP server exposing BNB Chain, opBNB and EVM tools for chain data, token safety, swaps and storage.
- category: other
- vs stack: noise
- why: crypto chain tooling, and he is indifferent to crypto.

## nirholas/github-to-mcp
- stars: 35 | lang: TypeScript
- what: converts any GitHub repository into an MCP server by extracting tools from OpenAPI specs, READMEs, code and GraphQL.
- category: tooling
- vs stack: noise
- why: generic MCP generator, not trading related.

## nirholas/extract-llms-docs
- stars: 35 | lang: TypeScript
- what: a web app and MCP server that fetches llms.txt and install.md documentation from any docs site for agents.
- category: tooling
- vs stack: noise
- why: generic docs extraction, nothing for trading.

## cliffhall/puzzlebox
- stars: 34 | lang: TypeScript
- what: an MCP server hosting finite state machines as subscribable resources so multiple clients can coordinate agents by state.
- category: infra
- vs stack: adjacent
- why: a state machine coordination idea that could gate multi-agent trade flow, but he has no stated need for it.

## nirholas/lyra-tool-discovery
- stars: 34 | lang: TypeScript
- what: a CLI that finds MCP servers on GitHub and npm and uses an AI model to draft plugin configs.
- category: tooling
- vs stack: noise
- why: MCP discovery tooling, and his awesome-broker-mcp already does the verified version for brokers.

## Code-MonkeyZhang/ticktick-mcp-enhanced
- stars: 33 | lang: Python
- what: a local MCP server over the official TickTick API for managing todos from LLM apps.
- category: other
- vs stack: noise
- why: a task manager connector, unrelated to trading.

## evalstate/fast-agent-docs
- stars: 33 | lang: Python
- what: not documented
- category: other
- vs stack: noise
- why: the description says it is the documentation site for fast-agent, which is not trading related.

## nirholas/crypto-data-aggregator
- stars: 33 | lang: TypeScript
- what: a free crypto market data app covering coins, DeFi protocols, portfolios, alerts and sentiment, with an MCP server.
- category: data-api
- vs stack: noise
- why: crypto only, and momentum-mcp already covers his equity data needs.

## ferdousbhai/wsb-analyst-mcp
- stars: 32 | lang: Python
- what: an MCP server that fetches WallStreetBets posts, comments and shared links for LLM analysis, with a README plug for a hosted options brief service.
- category: data-api
- vs stack: adjacent
- why: retail sentiment scraping from WSB is a small slice of what he gets from the Stocktwits and AfterMath sentiment feeds, so only a possible extra source.

## he-yufeng/AnyCoder
- stars: 32 | lang: Python
- what: a roughly 1300 line terminal coding agent that works with 100+ models through litellm.
- category: agent
- vs stack: noise
- why: a general coding agent clone, not trading.

## kukapay/kukapay-mcp-servers
- stars: 32 | lang:
- what: an index of Kukapay's MCP servers for crypto, blockchain and Web3 data and services.
- category: meta-list
- vs stack: noise
- why: crypto-focused list of servers.

## kukapay/opcua-mcp
- stars: 32 | lang: Python
- what: an MCP server connecting AI agents to OPC UA industrial systems to monitor and control operational data.
- category: other
- vs stack: noise
- why: industrial automation, irrelevant to trading.

## nirholas/crypto-market-data
- stars: 32 | lang: TypeScript
- what: a live crypto and DeFi dashboard on CoinGecko and DeFiLlama data with a companion MCP server.
- category: data-api
- vs stack: noise
- why: crypto only.

## nirholas/mcp-notify
- stars: 32 | lang: Go
- what: watches the official MCP Registry for new, changed and removed servers and notifies via Discord, Slack, email and webhooks, with a CLI, Go SDK and MCP server.
- category: tooling
- vs stack: adjacent
- why: could alert on new broker MCP servers appearing in the registry, which would feed awesome-broker-mcp upkeep.

## kukapay/awesome-alpha-arena
- stars: 31 | lang:
- what: a curated list of open-source clones, frameworks, experiments and articles inspired by nof1.ai's Alpha Arena LLM trading competition.
- category: meta-list
- vs stack: adjacent
- why: a list of LLM trading agent arenas and prompt setups that is useful reading next to trading-agent, though mostly crypto via CCXT.

## kukapay/hyperliquid-info-mcp
- stars: 30 | lang: Python
- what: an MCP server giving real-time data and insights from the Hyperliquid perp DEX.
- category: data-api
- vs stack: noise
- why: crypto perp DEX data.

## rangertaha/urlinsane
- stars: 30 | lang: Go
- what: a typosquatting detection tool for OSINT investigations across multilingual domains.
- category: tooling
- vs stack: noise
- why: domain security tool, unrelated to trading.

## guangxiangdebizi/China-Central-Policy-MCP
- stars: 29 | lang: JavaScript
- what: an MCP server that searches and parses State Council policy documents from gov.cn into structured data.
- category: data-api
- vs stack: noise
- why: Chinese government policy data, outside his US equities and options focus.

## kukapay/jupiter-mcp
- stars: 29 | lang: JavaScript
- what: an MCP server that executes Solana token swaps through Jupiter's Ultra API.
- category: broker-mcp
- vs stack: noise
- why: a Solana swap execution path, and he is indifferent to crypto.

## he-yufeng/AgentProbe
- stars: 28 | lang: Python
- what: a pytest plugin that snapshots AI agent outputs as baselines and catches regressions in CI with semantic comparison and mock LLMs.
- category: tooling
- vs stack: adjacent
- why: regression testing could harden trading-agent and alpha-skills outputs, which he does not appear to have.

## Manoj7ar/Prism
- stars: 27 | lang: Python
- what: a Windows desktop AI agent with an Electron overlay and FastAPI backend that reads the screen and automates multi-step tasks using Gemini 3.
- category: agent
- vs stack: noise
- why: general desktop automation.

## murrlincoln/anet
- stars: 27 | lang: TypeScript
- what: a CLI stack for autonomous agents covering ERC-8004 identity, ERC-8128 signing, X402 payments and XMTP messaging.
- category: infra
- vs stack: noise
- why: on-chain agent economy tooling, outside his stack.

## SecretiveShell/MCP-actions-adapter
- stars: 26 | lang: Python
- what: an adapter that turns an MCP server into a GPT Actions compatible API, exposed through a Cloudflare tunnel.
- category: tooling
- vs stack: noise
- why: a generic bridge, and he already ships his own MCP distribution via daddymcp.

## SecretiveShell/MCP-llms-txt
- stars: 26 | lang: Python
- what: an MCP server that adds Awesome-llms-txt documentation into a conversation as resources.
- category: tooling
- vs stack: noise
- why: generic docs helper.

## kukapay/modbus-mcp
- stars: 26 | lang: Python
- what: an MCP server that standardizes Modbus industrial IoT data for AI agents.
- category: other
- vs stack: noise
- why: industrial IoT, irrelevant.

## nutdnuy/portfolio-optimization-ai-plugin
- stars: 25 | lang: Python
- what: a Claude Code and Codex plugin that runs audited Riskfolio-Lib portfolio optimization workflows from data intake to weights, diagnostics and limitations, with no brokerage or order placement.
- category: agent-skills
- vs stack: adjacent
- why: allocation optimization is not something alpha-skills clearly covers, but it is a portfolio-level tool and his edge is premium selling and momentum screens.

## Manoj7ar/Sally
- stars: 24 | lang: TypeScript
- what: a voice-first macOS accessibility agent for hands-free web navigation, powered by Gemini.
- category: agent
- vs stack: noise
- why: accessibility agent, unrelated.

## heubme2020/datasinking
- stars: 24 | lang: Python
- what: a REST API and 8-tool MCP server serving full-text annual and quarterly financial reports for US, China, Europe, Japan, Korea and Taiwan as section-addressable Markdown.
- category: data-api
- vs stack: adjacent
- why: section-level report fetch is a token-saving idea, but trading-agent already has EDGAR filings for US names and he trades only US.

## SecretiveShell/mcp-windows
- stars: 23 | lang: Python
- what: an MCP server for the Windows API with media and other system controls.
- category: other
- vs stack: noise
- why: OS control, unrelated.

## major/porkbun-mcp
- stars: 23 | lang: Python
- what: an MCP server for the Porkbun API to manage domains, DNS records, DNSSEC and SSL certificates.
- category: other
- vs stack: noise
- why: domain registrar admin, unrelated.

## zhangzhongnan928/mcp-pa-ai-agent
- stars: 23 | lang: Python
- what: an MCP server of personal assistant tools for calendar, tasks and email.
- category: other
- vs stack: noise
- why: generic personal assistant.

## kukapay/rug-check-mcp
- stars: 22 | lang: Python
- what: an MCP server that flags rug-pull risks in Solana meme tokens.
- category: risk-guard
- vs stack: noise
- why: a risk check, but for Solana meme tokens, so not usable for US equities.

## kukapay/token-minter-mcp
- stars: 22 | lang: JavaScript
- what: an MCP server that lets agents mint ERC-20 tokens across 21 blockchains.
- category: other
- vs stack: noise
- why: token minting, irrelevant.

## kukapay/nearby-search-mcp
- stars: 22 | lang: Python
- what: an MCP server for nearby place search with IP-based location detection.
- category: other
- vs stack: noise
- why: location search, unrelated.

## olaservo/skilljack-mcp
- stars: 22 | lang: TypeScript
- what: MCP server that discovers Agent Skills from local dirs, GitHub or well-known URLs and serves them to the LLM via server instructions and a load-skill tool.
- category: agent-skills
- vs stack: adjacent
- why: Could be a delivery path for his alpha-skills library over MCP, but he does not need a skill server to publish skills.

## caiovicentino/Solana-MCP
- stars: 21 | lang: TypeScript
- what: MCP server on Solana Agent Kit that lets agents check balances, transfer tokens, swap and fetch prices on Solana.
- category: other
- vs stack: noise
- why: Solana DeFi, and he is indifferent to crypto.

## keli-wen/One-Poem-Suffices
- stars: 21 | lang: TeX
- what: Markdown source of a personal blog on AI agents, context engineering and harness engineering.
- category: other
- vs stack: noise
- why: A blog, no trading content.

## koreainvestment/koreainvestment-mcp
- stars: 21 | lang: Python
- what: MCP search service that finds Korea Investment & Securities APIs (334 across domestic and overseas stocks, futures, bonds) by natural-language query.
- category: broker-mcp
- vs stack: adjacent
- why: It searches API docs rather than placing orders and targets a Korean broker, so it is no broker path for his US stack.

## terencebeauj/Trading_bot_BollingerBands
- stars: 21 | lang: MQL5
- what: MQL5 Expert Advisor trading Bollinger Bands volatility on a single currency, offered as a starter template.
- category: trading-strategy
- vs stack: noise
- why: A forex MT5 example bot, with nothing for equities or options.

## georgezouq/ai-trader
- stars: 19 | lang: Python
- what: RL/LSTM stock and futures trader on Keras and rqalpha that combines sentiment, technical and fundamental factors.
- category: trading-strategy
- vs stack: noise
- why: An old ML research project on a Chinese backtest engine, not related to his skills-driven approach.

## rock3r/atc
- stars: 19 | lang: JavaScript
- what: Daemonless lease and queue system that coordinates exclusive Android and iOS device access across concurrent coding agents.
- category: tooling
- vs stack: noise
- why: Mobile device coordination for coding agents, with no trading relevance.

## suhailkakar/polymarket-data
- stars: 19 | lang: TypeScript
- what: Community TypeScript client with Zod validation for the public Polymarket Data and Gamma APIs.
- category: sdk
- vs stack: noise
- why: Prediction-market SDK, outside his equities and options focus.

## wshobson/backhacker
- stars: 18 | lang: Python
- what: not documented
- category: trading-strategy
- vs stack: adjacent
- why: Empty README, the description only says legacy Backtrader bot and backtester, which his alpha-skills backtesting already outclasses.

## jack-arturo/edd-appsmith-stats
- stars: 18 | lang: JavaScript
- what: Appsmith dashboard that gives real-time BI reporting for Easy Digital Downloads on a WordPress database.
- category: other
- vs stack: noise
- why: WordPress sales reporting, unrelated to trading.

## Code-MonkeyZhang/persona-agent
- stars: 18 | lang: TypeScript
- what: Open-source customizable AI companion chat app with personas, voice, an agent marketplace, MCP and skill support.
- category: agent
- vs stack: noise
- why: A companion chat product, not a trading agent.

## KyuRish/mcp-server-for-fiverr-unofficial
- stars: 18 | lang: Python
- what: Unofficial MCP server for searching public Fiverr gig listings.
- category: other
- vs stack: noise
- why: Freelance marketplace search, not trading.

## Mohammad-Faiz-Cloud-Engineer/Antigravity-Tool-Kit
- stars: 18 | lang: JavaScript
- what: CLI that installs a template pack of specialist agents, skills and workflows for AI-assisted software development.
- category: agent-skills
- vs stack: noise
- why: Generic dev-productivity skills, with no trading skills and nothing beyond alpha-skills.

## jkoelker/python-tradeking
- stars: 18 | lang: Python
- what: Python wrapper for the TradeKing OAuth API covering market quotes.
- category: sdk
- vs stack: noise
- why: TradeKing is long defunct (now Ally Invest), and his traderdaddy-bridge already normalizes brokers.

## zachgoll/photography-portfolio-tutorial
- stars: 18 | lang: TypeScript
- what: Next.js photography portfolio tutorial project from create-next-app boilerplate.
- category: other
- vs stack: noise
- why: Web tutorial, not trading.

## rhnvrm/machine-learning-nanodegree
- stars: 17 | lang: HTML
- what: Project notebooks and reports from Udacity's Machine Learning Nanodegree.
- category: other
- vs stack: noise
- why: Coursework, not trading.

## Yijia-Xiao/Know2BIO
- stars: 17 | lang: Python
- what: Benchmark and biomedical knowledge graph harmonizing heterogeneous database sources.
- category: other
- vs stack: noise
- why: Biomedical research, not trading.

## agustinsacco/phosphor
- stars: 17 | lang: TypeScript
- what: Open-source desktop workspace for coding agents built on the pi agent, with per-task worktrees, diffs and a reviewed-knowledge "Brain".
- category: agent
- vs stack: noise
- why: A coding-agent IDE, not a trading tool.

## cliffhall/mcp-c64
- stars: 17 | lang: JavaScript
- what: MCP server for developing BASIC and 6502 assembly programs for the Commodore 64 with VICE and 64tass.
- category: other
- vs stack: noise
- why: Retro-computing dev tool, not trading.

## gsalaz98/clifford
- stars: 17 | lang: Jupyter Notebook
- what: Personal collection of QuantConnect and Quantopian research notebooks on stock and crypto strategies.
- category: trading-strategy
- vs stack: noise
- why: Dated personal research notebooks, with nothing that his alpha-skills lacks.

## guangxiangdebizi/email-mcp
- stars: 17 | lang: TypeScript
- what: Streamable HTTP email MCP with five fixed tools for IMAP/SMTP and Gmail API with multi-account switching.
- category: tooling
- vs stack: noise
- why: A generic email MCP, not trading.

## kukapay/crypto-rss-mcp
- stars: 17 | lang: Python
- what: MCP server that aggregates crypto news from RSS feeds with keyword filtering and OPML import.
- category: data-api
- vs stack: noise
- why: Crypto news, and he already has equity news in momentum-mcp.

## JmPotato/fp-growth-rs
- stars: 16 | lang: Rust
- what: Pure Rust implementation of the FP-Growth frequent-itemset mining algorithm.
- category: other
- vs stack: noise
- why: A generic data-mining library, with no trading use shown in the README.

## kukapay/crypto-orderbook-mcp
- stars: 16 | lang: Python
- what: MCP server computing order book depth and imbalance across Binance, Kraken, Coinbase, Bitfinex, OKX and Bybit.
- category: data-api
- vs stack: noise
- why: Crypto exchange order books, outside his equities and options focus.

## orkblutt/QFreqtradeUI
- stars: 16 | lang: C++
- what: Qt desktop GUI that monitors and controls a freqtrade bot through its REST API.
- category: tooling
- vs stack: noise
- why: A crypto freqtrade front end, not his stack.

## satohubai/onchain-agents
- stars: 16 | lang: JavaScript
- what: Scored daily-updated index of 498 onchain agent tools (frameworks, MCPs, wallets, payment rails), also exposed as a 48-tool MCP.
- category: meta-list
- vs stack: noise
- why: Onchain agent directory, and he is indifferent to crypto.

## toby/mirror-mcp
- stars: 16 | lang: TypeScript
- what: MCP server with a reflect tool that lets an LLM question itself recursively through MCP sampling.
- category: tooling
- vs stack: noise
- why: A self-reflection novelty tool, with no trading memory or risk function.

## Code-MonkeyZhang/mini-agent-ts
- stars: 15 | lang: TypeScript
- what: Minimal roughly 2,000-line terminal LLM agent in TypeScript with Agent Skills and MCP support, a port of MiniMax's Mini-Agent.
- category: agent
- vs stack: noise
- why: A generic terminal agent, and his agent work is already in trading-agent.

## Matvey-Kuk/gaggimate-mcp
- stars: 15 | lang: JavaScript
- what: MCP server that lets an AI read espresso shot data and rewrite the machine profile in a feedback loop.
- category: other
- vs stack: noise
- why: Espresso machine control, though the read-results-then-tune loop is a pattern only.

## YichengYang-Ethan/0dte-strategy
- stars: 14 | lang: Python
- what: SPX 0DTE research repo with a documented trail of falsified GEX/Vanna strategies and an active rule-based long-gamma rebuild (walls, bucketed Vanna, IV spike, target-price engine) with pre-declared kill gates.
- category: trading-strategy
- vs stack: adjacent
- why: Overlaps his GEX and dealer gamma work on 0DTE, but it is research in progress, and the kill-gate falsification method and Vanna bucketing are worth reading.

## calclavia/rl
- stars: 14 | lang: Python
- what: Keras and OpenAI Gym reinforcement learning library with an A3C agent.
- category: other
- vs stack: noise
- why: Generic RL, with no trading content.

## calclavia/Voltz-Mod-Pack
- stars: 14 | lang: Groovy
- what: Minecraft mod pack of Universal Electricity tech mods.
- category: other
- vs stack: noise
- why: A game mod pack.

## tadasant/mcp-server-ssh-rails-runner
- stars: 14 | lang: TypeScript
- what: MCP server that runs Rails console commands over SSH with read-only, dry-run and mutate tools.
- category: tooling
- vs stack: noise
- why: Rails admin tool, though the dry-run-before-mutate split echoes a risk-gating idea.

## Vikranth3140/NSE-BSE-Stock-Prices-Automation
- stars: 13 | lang: JavaScript
- what: Google Sheets script that pulls NSE and BSE quotes and fundamentals via GOOGLEFINANCE.
- category: data-api
- vs stack: noise
- why: Indian-market spreadsheet quotes, and momentum-mcp already supplies free US quotes.

## rhnvrm/mattermost-cli
- stars: 13 | lang: Python
- what: Mattermost CLI for humans and agents to read and send messages and get an overview of mentions and unread.
- category: cli
- vs stack: noise
- why: Team chat tooling, not trading.

## YichengYang-Ethan/clawdfolio
- stars: 13 | lang: Python
- what: Python CLI and library for multi-broker (Longport, Moomoo/Futu) portfolio analytics: VaR/CVaR, GARCH, Fama-French exposure, and a risk-driven covered call signal backtested 2014-2026.
- category: cli
- vs stack: adjacent
- why: Covered-call signal gated by a bubble score overlaps his wheel work (wheelscope), but the broker paths are Asia-only and the factor and GARCH risk metrics are not in his stack.

## domdomegg/mcp-aggregator
- stars: 13 | lang: TypeScript
- what: TypeScript service that combines several remote MCP servers behind one endpoint with a single login.
- category: infra
- vs stack: noise
- why: Generic MCP plumbing, nothing trading-specific, and he is trimming MCP tools not adding layers.

## guangxiangdebizi/AI-web-mcpmode
- stars: 13 | lang: JavaScript
- what: FastAPI and WebSocket chat web app that calls MCP tools, with SQLite conversation history.
- category: tooling
- vs stack: noise
- why: Generic MCP chat front end with no finance content.

## nickmccullum/algorithmic-trading
- stars: 13 | lang: Python
- what: not documented
- category: other
- vs stack: adjacent
- why: Empty README, but the repo name points at algorithmic trading so it may hold strategy code worth a glance.

## nickmccullum/quant-finance-fundamentals
- stars: 13 | lang: Python
- what: not documented
- category: other
- vs stack: adjacent
- why: Empty README, described as basic quant finance tools reused across projects.

## zd87pl/hermes-g2-hud
- stars: 13 | lang: TypeScript
- what: TypeScript HUD that shows Hermes agent status, cron jobs and notifications on Even Realities G2 smart glasses over a WebSocket gateway, with voice commands.
- category: tooling
- vs stack: adjacent
- why: He runs Hermes agents and cron jobs, so a glanceable status display is a curiosity, but it is not trading.

## punkpeye/mcp-ping
- stars: 12 | lang: TypeScript
- what: MCP server that pings a host, built mainly as a FastMCP demo.
- category: tooling
- vs stack: noise
- why: A toy demo server.

## aryankeluskar/canvas-mcp
- stars: 12 | lang: TypeScript
- what: MCP tools for Canvas LMS and Gradescope: courses, modules, assignments, and resource search.
- category: other
- vs stack: noise
- why: Student coursework tooling, unrelated to trading.

## beatra-ai/ai-logo-maker-skill
- stars: 12 | lang: Python
- what: Agent skill that turns a brand name or reference image into logo concepts, rendered through a paid Beatra account.
- category: agent-skills
- vs stack: noise
- why: Logo generation skill tied to a credit-based vendor.

## caiovicentino/jev-risk-check-provider
- stars: 12 | lang: TypeScript
- what: x402 risk-check provider returning signed pre-payment verdicts using OFAC lists, phishing feeds, transaction simulation and EIP-7702 drainer watch, priced per check.
- category: risk-guard
- vs stack: noise
- why: Crypto wallet payment screening, and he is indifferent to crypto.

## chrisguidry/measured
- stars: 12 | lang: Python
- what: Python library for physical measurements and quantities with unit and dimension checking.
- category: sdk
- vs stack: noise
- why: Units library with no trading use.

## domdomegg/mcp-local-tunnel
- stars: 12 | lang: TypeScript
- what: Relay and agent that expose local MCP servers to remote clients such as Claude.ai without opening ports.
- category: infra
- vs stack: noise
- why: Generic tunneling, not trading.

## domdomegg/gmail-mcp
- stars: 12 | lang: TypeScript
- what: MCP server for Gmail to read, send, archive and manage email.
- category: tooling
- vs stack: noise
- why: Generic email MCP, and Gmail is already connected for him.

## florinel-chis/go-m2rest
- stars: 12 | lang: Go
- what: Dependency-free Go client for the Magento 2 REST API with typed reads, a searchCriteria builder and hardening switches.
- category: sdk
- vs stack: noise
- why: E-commerce API client.

## jaenster/d2-clientless
- stars: 12 | lang: Zig
- what: Zig clientless Diablo II 1.14d Battle.net client speaking BNCS, MCP, BNFTP and D2GS protocols.
- category: other
- vs stack: noise
- why: Game client where MCP means a Battle.net protocol, not Model Context Protocol.

## keli-wen/rondo
- stars: 12 | lang: HTML
- what: Agent skills for long-horizon work, including /long-horizon and /handoff, installable via npx skills or as a plugin.
- category: agent-skills
- vs stack: noise
- why: General agent workflow skills with nothing market-specific, and alpha-skills is his skills home.

## nutdnuy/the-trading-dev-kit
- stars: 12 | lang: unknown
- what: Claude skill that scaffolds a five-layer rule-based trading setup: CLAUDE.md and Risk.md rules, playbooks, guardrail hooks, subagents and a plugin bundle.
- category: agent-skills
- vs stack: adjacent
- why: Overlaps alpha-skills on the strategy side, but the hooks-as-risk-guardrail and Risk.md layering is a pattern worth a look.

## jgalea/mailbox-mcp
- stars: 11 | lang: TypeScript
- what: TypeScript MCP server giving AI tools Gmail, IMAP and JMAP email access across multiple accounts.
- category: tooling
- vs stack: noise
- why: Another email MCP server.

## NitayRabi/fitbit-mcp
- stars: 10 | lang: TypeScript
- what: MCP server exposing Fitbit health and fitness data to AI assistants.
- category: other
- vs stack: noise
- why: Health data, unrelated.

## 6/slack-graph
- stars: 10 | lang: JavaScript
- what: Slack /graph command that renders ASCII bar charts from comma-separated values.
- category: tooling
- vs stack: noise
- why: Tiny Slack utility.

## KyuRish/patreon-mcp-server
- stars: 10 | lang: Python
- what: Python MCP server for the Patreon API covering campaigns, members and posts.
- category: other
- vs stack: noise
- why: Creator platform tool, unrelated to trading.

## YichengYang-Ethan/Market-Bubble-Index-Dashboard
- stars: 10 | lang: Python
- what: Python dashboard with a 7-indicator bubble index (QQQ deviation, VIX, CAPE, SKEW, breadth, credit, yield curve), a drawdown probability model with purged walk-forward validation, and regime-based position mapping.
- category: trading-strategy
- vs stack: covered
- why: Vesper's detect_bubble_risk and detect_market_top tools in mphinance/trading-agent already do market-top and bubble risk, though the purged walk-forward validation is a nice method.

## beatra-ai/ai-storyboard-generator-skill
- stars: 10 | lang: Python
- what: Agent skill that turns a script or ad brief into a shot list and storyboard key frames, rendered via a paid Beatra account.
- category: agent-skills
- vs stack: noise
- why: Video production skill.

## beatra-ai/viral-video-remake-skill
- stars: 10 | lang: Python
- what: Agent skill that breaks a short viral video into hook, beats and call to action and rebuilds it as a shot list and vertical clip.
- category: agent-skills
- vs stack: noise
- why: Video production skill.

## beatra-ai/ai-product-photography-skill
- stars: 10 | lang: Python
- what: Agent skill that turns a product photo into studio and lifestyle ecommerce images via a paid Beatra account.
- category: agent-skills
- vs stack: noise
- why: Ecommerce imagery skill.

## florinel-chis/magento2-cms-sync
- stars: 10 | lang: Python
- what: FastAPI and React web tool that compares and syncs CMS blocks and pages between Magento 2 stores.
- category: tooling
- vs stack: noise
- why: E-commerce content sync.

## guangxiangdebizi/PolicyAgents
- stars: 10 | lang: Python
- what: Streamlit and LangGraph prototype that runs three agents over a policy text to produce intent, gaps, positive impact and risk reports, with optional MCP tools.
- category: agent
- vs stack: noise
- why: Chinese policy text analysis demo, not market analysis.

## guangxiangdebizi/Akshare-MCP
- stars: 10 | lang: Python
- what: FastMCP SSE server over AkShare with three tools for Hong Kong, US and A-share historical prices.
- category: data-api
- vs stack: covered
- why: mphinance/momentum-mcp already serves US OHLCV, and the README says only three tools exist and it is unfinished.

## he-yufeng/ai-infra-notes
- stars: 10 | lang: Python
- what: Source-level engineering notes on inference engines, KV caches, scheduling, serving protocols and agent runtimes.
- category: other
- vs stack: noise
- why: LLM infrastructure reading notes, not trading.

## olaservo/code-execution-with-mcp
- stars: 10 | lang: TypeScript
- what: TypeScript demo of the code-execution-with-MCP pattern using the Claude Agent SDK, following Anthropic's engineering post.
- category: agent
- vs stack: adjacent
- why: A pattern for cutting tool-definition tokens, which could matter for his 56-tool Vesper server, but it is a demo.

## rock3r/cav
- stars: 10 | lang: Go
- what: Go CLI and agent skill that builds, checks and renders Cavalry motion graphics from the terminal.
- category: cli
- vs stack: noise
- why: Motion graphics tooling.

## sickn33/tidal-mcp
- stars: 10 | lang: Python
- what: Python MCP server for TIDAL with over 100 tools covering catalog, playlists and approval-gated writes.
- category: other
- vs stack: noise
- why: Music service server.

## zhangzhongnan928/mcp-blockchain-server
- stars: 10 | lang: TypeScript
- what: TypeScript MCP server that reads blockchain data and prepares transactions while the user signs in their own wallet.
- category: other
- vs stack: noise
- why: Crypto chain tooling, and he is indifferent to crypto.

## YichengYang-Ethan/prediction-market-pricing
- stars: 9 | lang: Python
- what: Working paper and code applying Wang Transform pricing to 291K prediction market contracts across 6 platforms to decompose risk premia.
- category: other
- vs stack: adjacent
- why: Research on pricing event contracts as an incomplete market, a novel angle but not equities or options.

## beatra-ai/photo-to-anime-skill
- stars: 9 | lang: Python
- what: Agent skill that restyles photos as anime, manga or cartoon art via a paid Beatra account.
- category: agent-skills
- vs stack: noise
- why: Image style skill.

## domdomegg/shell-exec-mcp
- stars: 9 | lang: TypeScript
- what: MCP server that runs bash commands with optional background jobs and a job status tool.
- category: tooling
- vs stack: noise
- why: Generic shell MCP, nothing to do with trading.

## florinel-chis/prestashop-mcp
- stars: 9 | lang: Python
- what: Local offline MCP server indexing 1,095+ PrestaShop documentation pages.
- category: tooling
- vs stack: noise
- why: E-commerce docs server, irrelevant to trading.

## florinel-chis/magento-graphql-docs-mcp
- stars: 9 | lang: Python
- what: Local STDIO MCP server for searching Magento 2 GraphQL documentation.
- category: tooling
- vs stack: noise
- why: E-commerce docs server, irrelevant to trading.

## hamen/pr-review-relay
- stars: 9 | lang: Shell
- what: Shell tool that hands a PR to other local AI coding agents (Claude, Codex, Cursor) for cross-review.
- category: tooling
- vs stack: noise
- why: Code review workflow, no trading relevance.

## he-yufeng/LiteBench
- stars: 9 | lang: Python
- what: Pip-installable benchmark runner for LLMs and agents with built-in and custom tasks.
- category: tooling
- vs stack: noise
- why: General LLM eval runner, not tied to his stack.

## he-yufeng/IslandEscape
- stars: 9 | lang: TypeScript
- what: Pixel-art survival trading game where four LLM NPCs bargain under a typed game engine that validates every action.
- category: other
- vs stack: noise
- why: A game; the propose-then-validate pattern is interesting but not a trading tool.

## he-yufeng/FlightBox
- stars: 9 | lang: Python
- what: Local-first recorder that logs, replays and diffs every LLM call an agent makes, with redacted evidence reports.
- category: tooling
- vs stack: adjacent
- why: Could audit Vesper agent runs, but he has no stated need for LLM call replay.

## keli-wen/token-history
- stars: 9 | lang: Python
- what: Snapshots Claude Code and Codex token usage to git daily and renders self-updating SVG charts and badges.
- category: tooling
- vs stack: noise
- why: Vanity usage charts, no trading overlap.

## nutdnuy/pairs-trading-research-skill
- stars: 9 | lang: Python
- what: Agent skill for pairs research: PCA/DBSCAN reduction, Engle-Granger cointegration, Benjamini-Hochberg FDR, formation/OOS split and cost-aware backtest.
- category: agent-skills
- vs stack: adjacent
- why: Rigorous stat-arb workflow that could be a skill beside alpha-skills, but pairs is not his premium-selling style.

## beatra-ai/beatra-skills
- stars: 8 | lang: Python
- what: Agent skills for AI image, voice, video and music generation that render on the paid Beatra service.
- category: agent-skills
- vs stack: noise
- why: Creative media skills tied to a paid service.

## caiovicentino/eikos-arena
- stars: 8 | lang: Python
- what: Paper-trading arena where Eikos-27B and Jev decision models trade 14 Hyperliquid perps with simulated money and pre-hashed rules.
- category: trading-strategy
- vs stack: noise
- why: Crypto perps model benchmark, and he is indifferent to crypto.

## domdomegg/starling-bank-mcp
- stars: 8 | lang: TypeScript
- what: MCP server for Starling Bank's developer API to view and control a bank account, with a warning about model mistakes.
- category: other
- vs stack: noise
- why: UK retail bank, not a broker or trading path.

## domdomegg/defuddle-fetch-mcp-server
- stars: 8 | lang: TypeScript
- what: Web fetch MCP server using Defuddle to return cleaned markdown, a drop-in for the default fetch server.
- category: tooling
- vs stack: noise
- why: Generic web fetch tool.

## florinel-chis/mage-seo
- stars: 8 | lang: PHP
- what: Laravel SaaS generating SEO content for Magento 2 stores with hallucination detection and approval workflows.
- category: other
- vs stack: noise
- why: E-commerce SEO, irrelevant.

## gistrec/RakLib
- stars: 8 | lang: PHP
- what: PHP RakNet UDP proxy that load balances Minecraft Bedrock players across game servers.
- category: infra
- vs stack: noise
- why: Minecraft proxy, irrelevant.

## gsalaz98/LeanVSCode
- stars: 8 | lang: TypeScript
- what: VSCode extension to manage QuantConnect LEAN cloud projects and view backtests.
- category: tooling
- vs stack: noise
- why: Early-stage QuantConnect editor plugin; he does not use LEAN.

## guangxiangdebizi/A-Scope-Research
- stars: 8 | lang: Python
- what: Multi-agent debate system for China A-share analysis with technical, fundamental, quant, sentiment and risk personas over MCP.
- category: agent
- vs stack: noise
- why: A-share market focus, though the debate-then-risk-review pattern is generic.

## guangxiangdebizi/WebwithMCP
- stars: 8 | lang: JavaScript
- what: FastAPI and vanilla JS chat web app that calls MCP tools with streaming and SQLite history.
- category: tooling
- vs stack: noise
- why: Generic MCP chat front end.

## hamen/android-mcp
- stars: 8 | lang: TypeScript
- what: MCP stdio server that controls Android devices over ADB.
- category: tooling
- vs stack: noise
- why: Android device control, irrelevant.

## he-yufeng/CodeJoust
- stars: 8 | lang: Python
- what: Runs several AI coding agents on the same bug and scores them on tests, diff, cost and time.
- category: tooling
- vs stack: noise
- why: Coding agent bake-off tool, no trading relevance.

## olaservo/skilljack-evals
- stars: 8 | lang: TypeScript
- what: CLI that evaluates Agent Skills across agent harnesses with deterministic verifiers and no-skill baselines.
- category: tooling
- vs stack: adjacent
- why: Could measure whether his 133 alpha-skills actually add value over a baseline.

## alex-feel/claude-code-artifacts-public
- stars: 7 | lang: Python
- what: Collection of reusable Claude Code skills, hooks, rules, agents and slash commands.
- category: agent-skills
- vs stack: noise
- why: General Claude Code config pack, no trading content.

## MayurK-cmd/Pacifica-Pilot
- stars: 7 | lang: Python
- what: CLI trading agent for Pacifica perpetual futures with Supermemory-backed persistent memory of trades and patterns, 13 trading tools and a Telegram remote.
- category: agent
- vs stack: adjacent
- why: Persistent trade and pattern memory is a hole for Vesper, but the venue is crypto perps and the memory is a hosted third-party service.

## beatra-ai/ai-podcast-voiceover-skill
- stars: 7 | lang: Python
- what: Agent skill that turns an article or script into a solo podcast episode, rendered on paid Beatra credits.
- category: agent-skills
- vs stack: noise
- why: Audio production, tied to a paid service.

## beatra-ai/ai-poster-maker-skill
- stars: 7 | lang: Python
- what: Agent skill that makes posters, banners and flyers, rendered on paid Beatra credits.
- category: agent-skills
- vs stack: noise
- why: Graphic design skill, tied to a paid service.

## florinel-chis/flow-oms
- stars: 7 | lang: PHP
- what: Multi-tenant order management system for Magento 2 stores built on Laravel and Filament.
- category: other
- vs stack: noise
- why: E-commerce OMS, irrelevant.

## florinel-chis/magento-api-mcp
- stars: 7 | lang: Python
- what: Local MCP server with SQLite FTS5 search over Magento 2 REST API OpenAPI specs.
- category: tooling
- vs stack: noise
- why: E-commerce docs server, irrelevant.

## guangxiangdebizi/web-retrieval-mcp
- stars: 7 | lang: TypeScript
- what: MCP tool that analyzes a web page's layout, headings, navigation, forms and images from a URL.
- category: tooling
- vs stack: noise
- why: Web structure scraper, irrelevant.

## jaredbroad/quantconnect-lean-stubs
- stars: 7 | lang: Python
- what: Pip package of QuantConnect LEAN API type stubs for local IDE autocomplete, noted as incomplete.
- category: sdk
- vs stack: noise
- why: LEAN typing stubs, he does not use QuantConnect.

## jgalea/telegram-mcp
- stars: 7 | lang: Python
- what: MCP server giving AI tools access to a real Telegram account over MTProto to read, search and send messages.
- category: tooling
- vs stack: noise
- why: Generic Telegram access, not a trade alert path he lacks.

## joncovington/MEICAgent
- stars: 7 | lang: Python
- what: Claude Code agent that runs the 0DTE Multiple Entry Iron Condor strategy on tastytrade, with a stack of risk gates, dry-run default, and a paper system shadow-trading four risk profiles against live quotes.
- category: agent
- vs stack: gap
- why: 0DTE index options with explicit risk gating and zero-capital paper shadowing on tastytrade matches his XSP 0DTE style and fills the risk-guard hole next to momentum-phund-tasty.

## mingi3314/tradelens
- stars: 7 | lang: Python
- what: Trading journal tool that imports HTS trade data from the clipboard and generates Obsidian markdown notes.
- category: tooling
- vs stack: adjacent
- why: A simple journal pipeline, nearest to decay-derby but mostly a Korean HTS importer.

## nutdnuy/AssetManagementToolkit
- stars: 7 | lang: Python
- what: Python research toolkit for risk metrics, covariance estimation, portfolio construction, simulation and CPPI/GOPI portfolio insurance, explicitly with no broker connection.
- category: sdk
- vs stack: adjacent
- why: Portfolio-level risk and insurance primitives he does not have, but aimed at asset allocation rather than premium selling.

## rohitsingh-iitd/zillow-mcp-server
- stars: 7 | lang: Python
- what: FastMCP server for Zillow property search, Zestimates, trends and a mortgage calculator.
- category: data-api
- vs stack: noise
- why: Real estate data, irrelevant.

## toby/flashback
- stars: 7 | lang: HTML
- what: Design skill that injects a chosen year's real design history, typefaces and palettes into agent output.
- category: agent-skills
- vs stack: noise
- why: Design taste skill, irrelevant.

## warren618/financial-analyst
- stars: 7 | lang: Python
- what: A multi-agent research workstation for single A-share stocks, with 13 tiered sub-agents, pluggable markdown memory, a self-improving dream loop and 12 MCP tools.
- category: agent
- vs stack: adjacent
- why: The outcome-tracked memory loop and trust-tiered agent design are worth a look, but it targets Chinese A-shares and overlaps trading-agent.

## chand1012/stonks
- stars: 6 | lang: Python
- what: A Python swing bot that buys pullbacks to the 50 SMA in uptrends and places bracket orders on Alpaca with 0.5% risk sizing.
- category: trading-strategy
- vs stack: noise
- why: A simple Alpaca bot; trading-agent and alpha-skills already cover screening and sizing, and it is not his premium-selling style.

## chand1012/webhook-trader
- stars: 6 | lang: Python
- what: An opinionated service that turns TradingView webhook alerts into Alpaca orders across multiple key pairs.
- category: tooling
- vs stack: covered
- why: traderdaddy-bridge already routes one algo to any broker, and pinesnake covers the TradingView-to-Python path.

## rhnvrm/pi-bash-readonly
- stars: 6 | lang: TypeScript
- what: A pi agent extension that wraps every bash call in a bwrap sandbox with a read-only filesystem and no network.
- category: tooling
- vs stack: noise
- why: Generic agent sandboxing for a different harness, unrelated to trading.

## SecretiveShell/mcp-mesh
- stars: 6 | lang: Python
- what: A p2p mesh overlay that lets MCP servers hosted on different devices register tools in a DHT behind an SSE/stdio gateway.
- category: infra
- vs stack: noise
- why: Generic MCP plumbing; he is trimming MCP overlap, not adding network layers.

## beatra-ai/xiaohongshu-cover-maker-skill
- stars: 6 | lang: Python
- what: An agent skill that makes Xiaohongshu vertical cover images, with rendering via a paid credit account.
- category: agent-skills
- vs stack: noise
- why: Social image generation for Chinese lifestyle posts, no trading relevance.

## beatra-ai/ai-image-realism-skill
- stars: 6 | lang: Python
- what: An agent skill that fixes AI-image artifacts like plastic skin and malformed hands, with credit-based rendering.
- category: agent-skills
- vs stack: noise
- why: Image realism tooling, no trading relevance.

## beatra-ai/multilingual-voiceover-skill
- stars: 6 | lang: Python
- what: An agent skill for multilingual voiceover from per-language scripts, with credit-based rendering.
- category: agent-skills
- vs stack: noise
- why: Audio generation, no trading relevance.

## beatra-ai/ai-voiceover-generator-skill
- stars: 6 | lang: Python
- what: An agent skill for picking voices and turning scripts into narration, with credit-based rendering.
- category: agent-skills
- vs stack: noise
- why: Voiceover tooling, no trading relevance.

## beatra-ai/ai-video-generator-skill
- stars: 6 | lang: Python
- what: An agent skill that generates and edits short AI videos, with credit-based rendering.
- category: agent-skills
- vs stack: noise
- why: Video generation, no trading relevance.

## beatra-ai/ecommerce-product-images-skill
- stars: 6 | lang: Python
- what: An agent skill that builds ecommerce listing image sets from product photos and SKU facts.
- category: agent-skills
- vs stack: noise
- why: Ecommerce imagery, no trading relevance.

## beatra-ai/ai-media-generator-skill
- stars: 6 | lang: Python
- what: An agent skill bundling AI image, video, music and voice generation plus public social data lookup behind one connection.
- category: agent-skills
- vs stack: noise
- why: General media generation, no trading relevance.

## caiovicentino/jev-align
- stars: 6 | lang: JavaScript
- what: A CLI that calls the Jev service to score LLM responses and agent plans for sycophancy, deception, overreach and hidden malicious steps.
- category: tooling
- vs stack: adjacent
- why: A plan verifier could in principle gate agent-proposed orders, but it depends on an external paid service and is generic.

## caiovicentino/opencode-remote
- stars: 6 | lang: TypeScript
- what: A PWA, blind relay and daemon that lets you control a local opencode agent from your phone with E2E encryption and passkey pairing.
- category: tooling
- vs stack: noise
- why: Remote control for a coding agent, not a trading tool.

## chrisguidry/you-need-an-mcp
- stars: 6 | lang: Python
- what: An MCP server that lets an LLM read and edit a YNAB budget, including transactions and scheduled transactions.
- category: other
- vs stack: noise
- why: Personal budgeting, not trading.

## edkdev/mt5-forex-mcp
- stars: 6 | lang: Python
- what: An MCP server for MetaTrader5 covering account info, positions, orders, ticks, OHLCV and indicators like RSI, MACD and ATR.
- category: broker-mcp
- vs stack: adjacent
- why: MT5 is a forex and CFD broker path he lacks, but it is outside his US equities and options focus.

## guangxiangdebizi/FinanceMCP-Alpha
- stars: 6 | lang: TypeScript
- what: A TypeScript MCP server that computes seven WorldQuant 101 alpha factors from Tushare A-share data.
- category: data-api
- vs stack: adjacent
- why: Alpha-factor computation is a technique alpha-skills may lack, but it is tied to Chinese Tushare data and only covers 7 factors.

## guangxiangdebizi/PPT-MCP
- stars: 6 | lang: TypeScript
- what: A Node.js MCP server for creating and managing PowerPoint files with PptxGenJS.
- category: tooling
- vs stack: noise
- why: Presentation tooling, not trading.

## he-yufeng/agentcikit
- stars: 6 | lang: Python
- what: A CLI bundle for CI evidence on agent work, including an MCP server gate, JSON-RPC record/replay, and tool-call safety regression tests.
- category: tooling
- vs stack: adjacent
- why: mcp-gate and tool-fence could test his 56-tool MCP server and guard against order-placing tool abuse, though it is generic.

## joelverhagen/mcp-insights
- stars: 6 | lang: PowerShell
- what: A scheduled snapshot of the public MCP registry with servers.json, CSV and a daily trend chart.
- category: meta-list
- vs stack: noise
- why: Registry statistics, not a trading resource.

## kelvingao/arxiv-mcp
- stars: 6 | lang: Python
- what: An MCP server for searching and retrieving arXiv papers by keyword.
- category: data-api
- vs stack: noise
- why: Academic paper search, not part of his stack.

## kelvingao/twsapi_tutorial
- stars: 6 | lang: Python
- what: A Sphinx tutorial for the native Python Interactive Brokers TWS API.
- category: sdk
- vs stack: adjacent
- why: IBKR tutorial material for a broker path he does not currently cover, but it is a tutorial and not a tool.

## nickmccullum/stockalerts
- stars: 6 | lang: Python
- what: not documented
- category: other
- vs stack: adjacent
- why: Empty README and description, so it cannot be judged beyond a stockalerts name that hints at price alerts.

## nutdnuy/price-action-backtest-plugin
- stars: 6 | lang: Python
- what: A research plugin that pulls Webull historical bars, backtests a price-action strategy with fees and slippage, and renders an audited HTML report.
- category: trading-strategy
- vs stack: adjacent
- why: Webull read-only data plus backtest reports touches his Webull-oriented trading-agent, but alpha-skills already covers backtesting.

## nutdnuy/Simulation_World_Quant_with_Python
- stars: 6 | lang: Python
- what: A small Python client for the WorldQuant Brain API to submit alpha simulations and fetch PnL results.
- category: sdk
- vs stack: noise
- why: WorldQuant Brain platform client, outside his workflow.

## phdargen/trueCastAgent
- stars: 6 | lang: TypeScript
- what: A TypeScript agent built on CDP AgentKit that powers a Farcaster mini app for prediction markets.
- category: agent
- vs stack: noise
- why: Onchain prediction-market social app, and he is indifferent to crypto.

## qrak/ti_numba
- stars: 6 | lang: Python
- what: A Numba-accelerated Python technical indicator library designed to avoid lookahead bias.
- category: sdk
- vs stack: adjacent
- why: Fast indicators could speed up scanline or backtests, but momentum-mcp already provides technical analysis.

## shanehull/fred-mcp
- stars: 5 | lang: Go
- what: A Go MCP server that wraps all 37 FRED API endpoints as typed tools, over stdio or HTTP/SSE with OAuth.
- category: data-api
- vs stack: adjacent
- why: FRED macro data is a source his MCP tools do not obviously expose, though TraderDaddy already has macro regime tools.

## AlexCatarino/Bovespa2QuantConnect
- stars: 5 | lang: C#
- what: A C# tool that writes data from various sources into QuantConnect's data format.
- category: tooling
- vs stack: noise
- why: The README says almost nothing and it targets QuantConnect and Bovespa, which he does not use.

## Royal-lobster/Plantifiles
- stars: 5 | lang: TypeScript
- what: A web and CLI/MCP tool where agents publish structured plans for team review and another agent pulls the approved Markdown.
- category: tooling
- vs stack: noise
- why: Generic agent plan-review workflow, not trading.

## SidharthK2/polymarket-agent
- stars: 5 | lang: TypeScript
- what: A Telegram bot with profiler, recommender and trading agents for discovering and trading Polymarket markets.
- category: agent
- vs stack: noise
- why: Prediction-market bot, and he is indifferent to crypto.

## WhymustIhaveaname/PerspectiveGap
- stars: 5 | lang: Python
- what: A benchmark for evaluating how well LLMs write prompts for multi-agent orchestration.
- category: other
- vs stack: noise
- why: LLM research benchmark, not trading.

## YichengYang-Ethan/crypto-return-prediction-kaggle
- stars: 5 | lang: Jupyter Notebook
- what: A LightGBM ensemble notebook predicting 24-hour returns across 355 cryptos for a Kaggle-style competition.
- category: trading-strategy
- vs stack: noise
- why: Crypto return prediction competition entry, and he is indifferent to crypto.

## alextitonis/Cognitive-Agent
- stars: 5 | lang: Python
- what: A leftover image-classifier training note for a cognitive agent, with instructions only on folder layout.
- category: other
- vs stack: noise
- why: Computer-vision stub unrelated to trading.

## aryankeluskar/ToolAlignBench
- stars: 5 | lang: TypeScript
- what: Code and a dataset benchmarking whether safety-aligned tool-calling LLM agents obey deployment instructions.
- category: other
- vs stack: noise
- why: Alignment research benchmark, not trading.

## beatra-ai/ai-image-generator-skill
- stars: 5 | lang: Python
- what: An agent skill that generates and edits images through a paid Beatra credit account.
- category: agent-skills
- vs stack: noise
- why: Creative media generation with no trading relevance.

## beatra-ai/beatra-ai
- stars: 5 | lang: not documented
- what: Org profile for Beatra, a credit-billed service giving agents image, video, music and speech generation via skills or MCP.
- category: other
- vs stack: noise
- why: Marketing profile for a media generation product.

## beatra-ai/lyrics-to-song-skill
- stars: 5 | lang: Python
- what: An agent skill that turns lyrics or a hook into a structured song brief for Suno-style rendering on Beatra credits.
- category: agent-skills
- vs stack: noise
- why: Music generation, irrelevant to trading.

## beatra-ai/ai-music-generator-skill
- stars: 5 | lang: Python
- what: An agent skill that turns a theme, lyrics or reference audio into songs and soundtracks via Beatra credits.
- category: agent-skills
- vs stack: noise
- why: Music generation, irrelevant to trading.

## beatra-ai/talking-avatar-video-skill
- stars: 5 | lang: Python
- what: An agent skill that turns a portrait and script into a talking avatar video via Beatra credits.
- category: agent-skills
- vs stack: noise
- why: Avatar video generation, irrelevant to trading.

## beepboop2025/narcoscope
- stars: 5 | lang: JavaScript
- what: A public data explorer for drug prices, precursor flows and seizures built from UNODC, INCB and EUDA data.
- category: data-api
- vs stack: noise
- why: Drug-market policy data, nothing to do with equities or options.

## bharadwajpro/Yahoo-Finance-Web-Scraping
- stars: 5 | lang: Python
- what: A Selenium scraper that pulls stock info from about 200 Yahoo Finance pages into a JSON file.
- category: tooling
- vs stack: covered
- why: momentum-mcp already serves OHLCV and screening data without scraping.

## bhavesh0009/options-day-trader-agent
- stars: 5 | lang: Python
- what: A Google ADK and Gemini agent that day-trades Indian NSE F&O options through an Angel One MCP server, with a diary of past trades, a risk-manager tool callback and paper/live modes.
- category: agent
- vs stack: adjacent
- why: The diary_reader trade-learnings loop and before_tool_callback risk gate echo trading-agent (Vesper) ideas, but it targets the Indian market and Angel One.

## caiovicentino/jev-shield
- stars: 5 | lang: JavaScript
- what: A stdio MCP firewall that screens every tool call, result and description with a semantic verification model and returns a probability.
- category: risk-guard
- vs stack: adjacent
- why: It guards against prompt injection between MCP client and server, not trade risk, but could wrap his MCP servers.

## caiovicentino/cls-ledger
- stars: 5 | lang: Python
- what: Research code and the AgentLife benchmark for LLM agent memory that consolidates facts into weights with a provenance ledger.
- category: memory
- vs stack: adjacent
- why: Agent memory research for personal-assistant facts, not trade memory, and no trading integration.

## calclavia/gym-music
- stars: 5 | lang: Python
- what: Music theory reinforcement learning rewards based on Magenta's RL Tuner.
- category: other
- vs stack: noise
- why: Music RL, irrelevant to trading.

## florinel-chis/magento-performance-review
- stars: 5 | lang: PHP
- what: An analysis tool that audits Magento 2 configuration, modules and infrastructure for performance problems.
- category: tooling
- vs stack: noise
- why: E-commerce performance auditing, unrelated.

## he-yufeng/IssueBenchKit
- stars: 5 | lang: Python
- what: A local builder that turns a GitHub issue or bug into a repeatable coding-agent benchmark task with scoring.
- category: tooling
- vs stack: noise
- why: Coding-agent benchmarking, not trading.

## he-yufeng/DRL-MultiFactorTrading
- stars: 5 | lang: Python
- what: Double DQN with transformer attention plus a Fama-French style multi-factor model, with volatility targeting, demoed on Hong Kong stocks.
- category: trading-strategy
- vs stack: noise
- why: Generic academic DRL strategy on HK equities, with no options or premium-selling angle.

## jkoelker/schwab-proxy
- stars: 5 | lang: Go
- what: An OAuth2 proxy that lets multiple clients share one Schwab API connection, with a schwab-py patcher and container image.
- category: infra
- vs stack: adjacent
- why: Solves the single-token Schwab limit that a Schwab adapter in traderdaddy-bridge would hit, but he has no Schwab path today to justify it.

## kelvingao/AQTLib
- stars: 5 | lang: Python
- what: An event-driven Python library for backtesting and live trading through Interactive Brokers via ib_insync.
- category: sdk
- vs stack: noise
- why: Generic algo-trading framework, and traderdaddy-bridge already covers broker abstraction.

## lwsinclair/IoT-Edge-MCP-Server
- stars: 5 | lang: Python
- what: An MCP server exposing MQTT, Modbus and industrial PLC devices as 11 tools.
- category: other
- vs stack: noise
- why: Industrial IoT, not finance.

## mphinance/scanline
- stars: 5 | lang: Python
- what: A TradingView-data market screener with a quant analytics layer, factor scoring and an MCP server.
- category: tooling
- vs stack: covered
- why: This is his own repo, mphinance/scanline.

## nickmccullum/algorithmic-trading-recording
- stars: 5 | lang: Python
- what: not documented
- category: other
- vs stack: adjacent
- why: README is empty, and the name suggests a course recording on algorithmic trading, which is likely noise.

## nutdnuy/self-driving-portfolio-skill
- stars: 5 | lang: Python
- what: A Claude Code and Codex skill that runs a governed six-stage strategic asset allocation pipeline from an IPS, with deterministic math and a tamper-evident audit trail.
- category: agent-skills
- vs stack: adjacent
- why: The hashed audit trail and fail-closed stage order are neat, but it is long-horizon allocation research with no brokerage integration, unlike his short-dated options focus.

## nutdnuy/Multi-period-Portfolio-Optimization-retirement_sdp
- stars: 5 | lang: Python
- what: A stochastic dynamic programming optimizer for retirement portfolios across life phases using Alpha Vantage data.
- category: trading-strategy
- vs stack: noise
- why: Retirement planning on SPY, AGG and GLD, unrelated to premium selling.

## phdargen/xoninAgent
- stars: 5 | lang: Python
- what: An X (Twitter) agent built on CDP AgentKit that scores wallet reputation and awards generative NFTs.
- category: agent
- vs stack: noise
- why: Crypto NFT bot, and he is indifferent to crypto.

## rudycelekli/rudycelekli
- stars: 5 | lang: Python
- what: A GitHub profile README for an AI researcher focused on verifiable agent systems.
- category: other
- vs stack: noise
- why: Personal profile page.

## rudycelekli/proofseal
- stars: 5 | lang: JavaScript
- what: Regression memory for coding agents: seals repo behavior and reports pass, drift, regressed or missing over MCP or CI.
- category: memory
- vs stack: noise
- why: It remembers code behavior for coding agents, not trades.

## seralifatih/congress-trading-pipeline
- stars: 5 | lang: TypeScript
- what: Pipelines that parse official House and Senate STOCK Act filings into deduplicated JSON, with a free 2025 snapshot dataset.
- category: data-api
- vs stack: covered
- why: Politician trades are already served by the TraderDaddy Pro MCP and Vesper's tool set, so this only adds a free primary-source parser.

## zd87pl/rlaif-trader
- stars: 5 | lang: Python
- what: A multi-agent Claude trading system with RAG, RL execution, and an AutoTrader loop that generates signal code, sandbox-backtests it, keeps or discards it, and hot-swaps live strategies.
- category: trading-strategy
- vs stack: gap
- why: The autonomous generate, backtest, keep/discard strategy loop is a technique alpha-skills lacks, since it has backtesting skills but no closed experimentation loop.
