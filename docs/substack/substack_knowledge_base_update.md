# Sam Just Read 144 Trading Books So You Don't Have To

Look, I know what you're thinking. "Great, another AI that Googles things." This isn't that.

I've been building Sam, my AI trading analyst, for the past three months. She started as a chatbot with some candlestick charts. As of tonight she's got 35 live tools, a VoPR options pricing engine, real-time institutional flow data, and a knowledge base of **2,259 embedded chunks from 144 trading books**.

Here's the truth: most AI financial tools are just wrappers around a prompt. Sam actually reads your question, pulls relevant passages from Natenberg, McMillan, Sinclair, Mark Douglas, and 140 other books, then cross-references that with live RSI, MACD, EMA stacks, TradingView consensus, and institutional options flow. In real time.

## What She Does

📊 **"How's AVGO looking?"** She runs 24 technical indicators, pulls TradingView's 26-indicator consensus, grabs fundamentals (P/E, revenue growth, short interest), fetches the news, generates a candlestick chart with EMA overlays, and gives you a directional take. Then she logs her own conviction and tracks whether she was right.

🎯 **"Best CSP on AAPL with $5,000 budget"** She scans across 7-45 DTE, scores every strike on annualized return, theta efficiency, delta sweet spot, and VoPR grade (our proprietary vol ratio), then hands you the top 3 puts and top 3 calls to sell. Ranked, graded, explained.

🔍 **"What should I trade today?"** She hits the screener, auto-discovers the most active tickers, runs both sell and buy scanners on each one in parallel, and returns a ranked Opportunity Board. The machine does in 30 seconds what used to take me 2 hours on a Sunday night.

📚 **"Explain volatility skew to me like I'm five"** She searches her embedded library. Natenberg's *Option Volatility and Pricing*. Sinclair's *Volatility Trading*. McMillan's *Options as a Strategic Investment*. Dalio's *How the Economic Machine Works*. The Black-Scholes original paper. 6 modules of CBOE Options Institute education. She finds the most relevant passages and synthesizes an answer. With citations.

## This Weekend's Update

I just finished ingesting Natenberg's *Option Volatility and Pricing* into the knowledge base. 884 new embedded chunks covering everything he ever wrote about theoretical pricing models, volatility, risk management, and options strategies. The knowledge base went from 1,375 to 2,259 chunks.

Here's what that means for you: when you ask Sam about implied volatility, skew, or pricing models, she's not hallucinating. She's pulling from the actual textbook content and giving you a grounded answer.

## The Stack Right Now

- **35 live tools** across screeners, technicals, options, flow, and backtesting
- **22 screener presets** including pre-market and after-hours scans
- **VoPR options engine** with 4-model realized volatility, Black-Scholes Greeks, and A-F grading
- **144 trading books** embedded and searchable by semantic similarity (not keyword matching)
- **Smart caching** that knows when the market is open vs closed and adjusts TTLs accordingly
- **Conviction journal** where Sam tracks her own calls and you can ask "how good are you?"
- **Backtesting suite** with 6 presets, custom conditions, multi-ticker sweep, and walk-forward validation
- **MCP protocol support** so you can plug Sam into Cursor, Claude Desktop, or any compatible AI client
- **10 LLM models** supported through BYOK (bring your own key). Gemini, GPT-4, Claude.

## How to Use It

Go to [sam.mphinance.com](https://sam.mphinance.com). That's it. No account, no API key needed. Just start asking questions.

Some things to try this weekend:

💡 *"What should I trade Monday?"*

💡 *"Best puts to sell on NVDA with $3,000"*

💡 *"Should I buy calls on TSLA?"*

💡 *"Backtest EMA crossover on SPY over 2 years"*

💡 *"Explain the Greeks and how gamma risk changes near expiration"*

💡 *"Screen for oversold large caps"*

💡 *"What does the institutional flow look like right now?"*

She's fast, she's opinionated, and she doesn't do disclaimers. She talks like a sharp trader on a desk, not a chatbot. If the data says it's garbage, she'll tell you it's garbage.

Play with it. Break it. Hit the bug report button if something's weird. I'm building this in the open and your feedback is the roadmap.

See you Monday with setups.

*Michael*
*Momentum Phinance*
