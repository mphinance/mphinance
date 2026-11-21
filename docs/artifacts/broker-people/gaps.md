# What you are missing: 246 repos graded against your stack

Every GitHub repo cited in `mphinance/awesome-broker-mcp`, graded against your stack (momentum-mcp,
alpha-skills, Vesper/trading-agent, TraderMatrix/TraderDaddy, traderdaddy-bridge, the daddy-* family,
wheelscope, scanline). Mined 2026-11-20, graded 2026-11-21.

## The shape of the 246

- **11 gaps** - fills something you do not have
- **8 covered** - you already have it; the overlap is named per repo
- **91 adjacent** - related, not obviously needed
- **136 noise** - dead stubs, marketing, generic awesome-lists, crypto-only, or irrelevant

That is the honest headline: the ecosystem is mostly one-off community MCP servers. Eleven things are real.

## The 11 gaps, and why

### Broker execution you cannot reach today
This is the whole story. You have the *directory* (awesome-broker-mcp) and an adapter theory
(traderdaddy-bridge maps brokers into Tradier's shape), but the execution paths you can actually drive
are Tradier and Vesper's keyless Webull. Five majors are open:

1. **k1xme/schwab-mcp** (0 stars, no license) - Schwab, 18 tools including option chains, order list,
   preview, place, cancel, replace, plus a Claude Code plugin of six safety skills. Schwab is the major
   one you have no route to at all.
2. **tomasgesino/schwab-mcp** (4 stars, MIT) - the *wheel-specific* Schwab server: `sell_cash_secured_put`
   and `sell_covered_call` with `dry_run=true` by default. This is your wheel bias expressed as a tool.
3. **sblattj/etrade-mcp** (1 star, MIT) - E*TRADE with OAuth 1.0a, VIP-TOTP auto-renew, equity, options
   and multi-leg spreads behind a code-enforced preview-then-place handshake.
4. **jonathansudhakar1/tradestation-cli-mcp** (0 stars, MIT) - all 42 TradeStation v3 REST endpoints as a
   library, a CLI and an MCP server, with streaming for stocks, options and futures.
5. **tastytrade/tastytrade-mcp** (37 stars, official) - the official one: quotes, chains, balances,
   positions, order entry, dry-run gated, read-only env switch, environment tag on every order result.
   Matches your premium-selling wheel bias directly. **cmike444/tastytrade-mcp** (2 stars) is the fuller
   sibling at 72 tools with DXLink realtime and option greeks.
6. **a9lim/tasty-mcp** (0 stars, AGPL-3.0) - the interesting one. Its write tools are gated by a hard cap
   on total potential max-loss across positions and working orders (default $100), it rejects short equity
   and naked short calls, and it always allows closing orders. That is an exposure-bounded order gate for
   a small account selling premium, which is exactly your stated account shape.
7. **alpacahq/alpaca-mcp-server** (1,102 stars, MIT) - Alpaca's official server, stocks, ETFs, crypto and
   options plus market data and portfolio, v2 FastMCP rewrite.
8. **webull-inc/webull-openapi-mcp** (31 stars, Apache-2.0) - the *official* Webull MCP. Vesper is Webull
   oriented but keyless by design; this is the order-capable one.
9. **webull-inc/webull-openapi-cli** (7 stars, Apache-2.0) - the Go CLI companion: dry-run, order
   confirmation, OAuth device auth, structured JSON output. Agent-first.

### The one that is not a broker
10. **mnemox-ai/tradememory-protocol** (1,450 stars, MIT) - local-first memory and a risk brake for AI
    trading agents: it syncs your fills, surfaces where your own history loses money, and can *refuse*
    orders that break your rules before they reach the broker (20 MCP tools, Alpaca sync shown read-only).
    Nothing in your stack does outcome-based trade memory. This is the most interesting non-obvious find
    in the whole set.

_(Ten numbered entries covering all 11 repos: tastytrade has two implementations, and Schwab has two, so
the count of repos exceeds the count of ideas.)_

## What you already cover (so you do not re-buy it)

- **thammo4/uvatradier**, **fi222/tradier-mcp**, **pipeworx-io/mcp-tradier** - all Tradier. You already
  normalize into Tradier through traderdaddy-bridge and pinesnake.
- **nutdnuy/QuantCornerBacktestingWebullMCP** - backtest and validation skills that alpha-skills covers.
- Your own repos, correctly identified: momentum-mcp, alpha-skills, trading-agent, traderdaddy-sdk.

## What I would do

1. **Take the three wheel-shaped ones seriously**: `tastytrade/tastytrade-mcp` (official, dry-run gated),
   `a9lim/tasty-mcp` (the max-loss gate is a genuinely good idea worth copying even if you do not run it),
   and `tomasgesino/schwab-mcp` (CSP and CC entry with dry-run default).
2. **Read `mnemox-ai/tradememory-protocol` end to end** - the pre-order refusal driven by your own losing
   history is the one idea here that is not already in your stack in any form.
3. **Treat the rest as a map, not a shopping list.** You have the directory; these are implementations.
   The value is knowing which broker has an official MCP with real order-gating, not adopting eleven servers.

## Caveats, stated plainly

- Grading was done in eight passes by separate workers against one stack description, so it is consistent
  in vocabulary, not perfectly calibrated. The 11 gaps I verified by hand against the GitHub API (stars,
  license, last push, archived all match). The 91 adjacent and 136 noise I did not individually re-check.
- Stars are not quality. Several of the most interesting gaps (a9lim, k1xme, jonathansudhakar1,
  cmike444) have 0 to 4 stars.
- Two of the strongest gaps carry **no license at all** (`k1xme/schwab-mcp`, `cmike444/tastytrade-mcp`),
  which means all rights reserved. Read, do not vendor.
