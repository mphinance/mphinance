TITLE: How to make your own MCP trading agent
SUBTITLE: AI 45% | Trading 40% | Mindset 15%
AUDIENCE: only_paid

- 
- An AI that can read the market is a research assistant. An AI that can place an order is a liability. The entire craft of building a trading agent lives in the distance between those two sentences. This piece is about the distance, not the order.

The part where the robot buys the stock is the easy one. It is three lines of config. The reason you do not already have a bot trading your account is not that the buy button is hard to wire. It is that wiring the buy button to a thing that occasionally makes stuff up is how you wake up short 40 contracts of some ticker you have never heard of, wondering what the hell happened.

An agent is a text file of instructions, plus a list of tools it’s allowed to use, running in a loop against a model.

That’s the whole thing. Three parts. Learn them and you can build anything.

So here is how I actually connect an AI to my brokerage. What I let it touch, what I never let it touch, and the boring scaffolding that stands between a good idea and a margin call.

Subscribe now

Two quick things first, both free, both mine. If you have never built an agent at all, start with the plain-English primer on the three pieces every agent is made of: Building Agents: The Part Nobody Explains. If you want to see real ones running, here are five working examples pulled straight from my own three-agent mesh: Agents in the Wild: Real Examples. Those two are the ground floor. This piece is the trading floor.

We also have a full developer’s section and MCP server at TDPro.

- 
- Let me start with the piece that is easy to get wrong: what MCP even is.

## MCP is a USB port for your AI
MCP stands for Model Context Protocol. Think of it as a standard plug. A "connector" is just a small server that exposes tools, which are functions the model is allowed to call, over a web address. The model does not know or care whether a tool reads a database, hits your broker, or fetches your old newsletter posts. It sees a menu of things it can call, and it calls them.

Every trading agent worth building has three layers, and you should hold them apart in your head like they are three different people.

- Data in. Screeners, options flow, gamma, your own positions. Read-only. My data brain is TraderDaddy Pro: gamma exposure, dark-pool prints, unusual activity, directional flow. Not one of those tools can place a trade. That is the entire point of that layer (fun fact - every time I say “that is the entire point” I’m accused of being AI).

- The brain. The model itself. Mine is named Sam. She reads the data tools, reasons over them, and drafts a plan.

- Order out. The broker. This is the one dangerous layer, and it is the one you gate to hell and back.

Get that mental model right and everything after it is plumbing. Get it wrong and no amount of clever prompting saves you.

## The shopping menu: which brokers can an AI actually trade through?
I got so tired of "does broker X have an MCP server or not" that I built a directory and checked 65 brokers at the source. I opened each one's own docs, read the actual tool list, and wrote down a yes or a no (by “I opened”, I mean Sam did my work of course). 27 have official servers. 15 have nothing, confirmed. A "no" is a real answer, so I list those too.

- 
- The only axis that matters the moment you are about to hand keys to a robot is this: can it place an order?

- Places a real order on a single tool call. Alpaca, Robinhood, Tradier, tastytrade, Kraken, and a couple dozen more.

- Draft only. It builds the order, you press send in the broker's own app. Interactive Brokers is the marquee case here, and the directory puts it plainly: the AI never submits an IBKR order to the market. It writes the order into a tab you approve by hand.

- Read only. It can look. It cannot touch.

Now rank those by how easy it is to hurt yourself. IBKR sits at the safe end: it cannot execute by design, so it is the safest thing that still trades. Alpaca, Kraken, and Webull default to paper, so live money is an opt-in you flip on purpose. Robinhood, Tradier, and most community servers go live on a single tool call: real money, no second thought. And Public.com has no paper mode at all, so there is no training-wheels version to hide behind. Respect it accordingly.

If you are building your first one, start with a paper-first or draft-only broker. I run my read layer against everything, and my write layer against IBKR in draft-only mode, so the worst the machine can do is hand me an order I still have to look at before it is real.

The full directory of all 65 is open and free. Knowing which broker will even talk to your robot should not cost you anything.

## Build the read layer first. Let it read for a week before it writes
Here is the shape of my server. One process, one web address, one token, and behind it right now about 35 tools. It started life as 13. That is the quiet magic of MCP: you add a capability by writing a function.

from fastmcp import FastMCP
mcp = FastMCP("supermcp", auth=auth.build())

@mcp.tool
async def get_positions() -> list[dict]:
    """Raw positions across brokers (tastytrade + ibkr) with DELAYED marks. Never live quotes."""
    return await _all_positions()That is a complete, working tool. And that docstring is not a comment. It is the instruction the model reads to decide when to reach for this tool. Your docstrings are prompt engineering now. Write them like it.

The adapter pattern underneath is simple on purpose. Every broker gets mapped into one common shape: broker, symbol, underlying, quantity, avg_price, delayed_mark, cost_basis, market_value. tastytrade comes straight off its SDK on delayed marks. IBKR I pull live from my own app, not from the exchange. Webull and Schwab are stories for another day. And there is one iron law for every adapter: if it fails, it returns an empty list. It never crashes the server. One broker going dark cannot take down the whole agent. Hold onto that one, it matters later.

You deploy this like any web app. A process behind a web server, a service that restarts itself, an HTTPS address. Paste that address into Claude as a custom connector and every tool shows up in the model's menu. There is nothing proprietary about it. Any spec-compliant MCP server works the same way.

Build this entire layer first. Then let the agent do nothing but read for a week before you ever let it write a single thing. You will learn fast what it is genuinely good at and what it quietly invents.

## On hallucinating agents
The base model will always hallucinate a price without a web-search or other kind of tool - it’s behind the day it ships. You fix that with one line in the prompt: answer only from the data in front of you, never invent a number you cannot derive from it. Done.

The real danger is a capable model, a live order tool, and no envelope around it. A model with a place_order function and a vague instruction to "trade the setup" is a coin flip with your money and a genuinely creative imagination for new ways to blow it up. The fix for that is not a smarter model. The fix is to stop asking the model to decide and start asking it to check.

Fair warning on the stakes before you decide whether to keep reading. Half of what you pay for this newsletter gets traded live in the same IBKR and tastytrade accounts these agents watch. This is not a theory of trading robots. It is the thing my subscribers fund. Below the line: the exact rules my agent checks instead of guessing at, the four locks between it and my money, and the thirteen hours yesterday I handed one a live SLV position and watched what it did with 158 chances to screw it up.

https://pastebin.com/rAdnVWhD

Share
