# Morning, Michael. Here is the whole thing in plain words.

## What you asked for
Look at every repo in the broker directory, compare them to what you already built, tell you what is
actually missing, write up the repos, and put it all in a NotebookLM notebook.

## What I actually found

I graded all 246 repos. Blunt version: **most of them are not worth your time.** 136 are dead stubs,
marketing, crypto-only, or copies of lists like yours. 91 are related but not needed. That leaves
**eleven** that fill a real hole.

Almost all eleven are one kind of thing: **official MCP servers for big brokers you have no way to trade
through right now.** You have the directory (which broker supports an AI) and the idea of a universal
adapter, but the brokers you can actually drive are basically Tradier and Webull. Sitting open:

- **Schwab** - two versions. One is built for the wheel (`sell_cash_secured_put`, `sell_covered_call`),
  and it defaults to dry-run so you cannot fat-finger it.
- **tastytrade** - the official one, dry-run gated. Plus a second that caps total possible loss at $100 by
  default and refuses naked short calls. That cap is a genuinely good idea.
- **E*TRADE**, **TradeStation**, **Alpaca**, and the **official Webull** server plus its CLI.

The one that is NOT a broker, and the one I would read first: **tradememory-protocol**. A memory for your
trading agent. It watches your own fills, works out where *you* lose money, and can **refuse an order**
that breaks your rules before it reaches the broker. Nothing you have does that. For a small account
selling premium, a thing that says "no, not that one" beats another screener.

Eight repos I marked as things you already have, mostly Tradier wrappers and your own repos.

## The bonus I did with the leftover time
I also audited **your own 74 repos against each other**, since you like a lean stack. Two things worth your
eye:

- **Three tools are all doing screening and technical analysis**: momentum-mcp, Vesper (trading-agent) and
  scanline. The report suggests picking one home for that job. momentum-mcp is probably it, since it has
  the traction.
- **A pile of archived Streamlit and script-era screeners** look like earlier attempts at the same thing
  (streamlit-stocks, streamlit-tradingview-screen, python-sheets-screener and friends), plus two forks of
  the same awesome-mcp-servers list.

Nothing there says delete. It says look. Full report is `overlap.md`.

## What I did with it
- Per-repo write-ups for all 246, each with a one-line "what it is" and a verdict against your stack.
- A short gap report with just the eleven, and what I would do.
- A designed "What you're missing" poster page (page 8 of the deck).
- All of it published and downloadable on your artifact page:
  https://mphinance.github.io/mphinance/artifacts/broker-people/
- A NotebookLM notebook with everything as sources, **including an audio overview** if you would rather
  listen on the way somewhere.
- `data.md` (every person, broker and repo) so an agent can read it without OCR-ing images.

## Honest caveats
- Eight writing passes did the grading, so the wording is consistent but not perfectly calibrated. I
  verified the eleven gaps by hand against GitHub (stars, license, last push) and the headline numbers on
  the deck and poster, and they all match. I did not re-check the 91 adjacent or 136 noise myself.
- Stars are not quality. Four of the eleven have 0 to 4 stars. The best ideas are in the quiet repos.
- Two good ones have **no license**, so all rights reserved. Read them, do not copy code.
- One quirk I caught and fixed: `github.com/schwab` is a man named Michael Schwab, not the broker. That
  logo is now a text wordmark.

## If you only read one line
Scroll to **mnemox-ai/tradememory-protocol**, then look at the two Schwab and two tastytrade servers. That
is the useful part. Everything else is scenery.
