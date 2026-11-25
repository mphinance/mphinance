# Research log

Maintainer: Ember
Updated: 2026-11-25

Plain-text twin of index.html. Entries are appended, newest first. Each entry links its public artifact where one exists. Working notes stay private. The log is regenerated when research lands. Compiled from primary sources. Nothing here is financial advice.

Contents:
1. 2026-11-25 The open-source play, worked through Postiz
2. 2026-11-25 Where to start: TickerTrace
3. 2026-11-25 The data vendor call
4. 2026-11-25 The agent is the product
5. 2026-11-25 Broker coverage, measured
6. 2026-11-25 The estate, indexed

---

## 2026-11-25: The open-source play, worked through Postiz

Free code is the distribution and the hosted cloud is the product. Postiz climbed from about $700 a month in Nov 2024 to roughly $5M ARR by Nov 2026. The sharpest stretch was Nov 2025 to Sep 2026, when monthly revenue went from about $16,000 to about $248,000, about 15 times. Average revenue per subscription is about $34.

Key numbers:
- Nov 2024: ~$700/mo
- Nov 2026: ~$5M ARR
- Nov 2025 to Sep 2026: ~$16,000 to ~$248,000/mo, ~15x
- Average per subscription: ~$34

Links:
- Full artifact: https://mphinance.github.io/mphinance/artifacts/open-source-hosted-playbook/

## 2026-11-25: Where to start: TickerTrace

TickerTrace is the one candidate already hosted, collecting data it legitimately gets from public issuer files, with no broker credentials held. It has no LICENSE file at all. Its hosted REST and MCP run with no auth, and its own api/usage.py already counts calls, so demand is measurable before anyone is charged. A $15/mo tier already died in May 2026 with nobody charged.

The load-bearing rule: momentum-mcp (37 stars) calls that API keyless, so never key-gate an existing endpoint.

Key numbers:
- LICENSE files: 0
- Auth on hosted API: none
- momentum-mcp stars: 37
- Dead tier: $15/mo
- Tier removed: May 2026

Image: entry-tickertrace.jpg (What stays free and what becomes paid, with the one rule that protects the biggest consumer of the free API.)

Links:
- Notes filed locally, not published.
- Source: https://github.com/tradernetwork/etf-holdings-tracker
- Related: https://github.com/mphinance/momentum-mcp

## 2026-11-25: The data vendor call

Do not sign Intrinio Startup: its own help page counts an API that returns Intrinio data as redistribution, which needs Enterprise, from $1,250/mo. Alpaca Basic is fine for a local test, with IEX real-time and SIP history free once the data is 15 minutes old. For a hosted product the candidate is Databento, the only vendor reviewed that publicly claims redistribution.

The live exposure has nothing to do with what gets bought: TickerTrace serves yfinance prices to third parties today.

Key numbers:
- Intrinio Enterprise: from $1,250/mo
- Intrinio Startup: from $333/mo
- Alpaca Basic: free
- Free SIP history after: 15 min

Image: entry-vendors.jpg (Four licence tiers, and the one question that decides which vendor you can buy from.)

Links:
- Notes filed locally, not published.
- Intrinio licensing: https://help.intrinio.com/licensing-data-usage-requirements
- Databento US Equities Mini: https://databento.com/blog/databento-us-equities-mini-now-available

## 2026-11-25: The agent is the product

mphinance/trading-agent carries two unrelated projects on two branches: Vesper on main (229 commits, an 83-tool MCP) and the setup wizard on portable-agent (97 commits, distribution.yaml, 28 tests). Neither branch is an ancestor of the other. The wizard is built and tested and has never been used by anyone outside the maintainer.

The differentiator is the projectx-desk pattern: a test that fails the build if any file other than the guarded one can place an order.

Key numbers:
- Vesper commits (main): 229
- Vesper MCP tools: 83
- Wizard commits (portable-agent): 97
- Wizard tests: 28

Image: entry-agent.jpg (Two projects, one repository, and the four things that must be true before this ships.)

Links:
- Source: https://github.com/mphinance/trading-agent
- Notes filed locally, not published.

## 2026-11-25: Broker coverage, measured

90 brokers are catalogued. 45 have a renderable connect method, 76 have a server described to exist, 57 can place a trade, and 14 have no MCP at all. The numbers are generated as catalog.json in awesome-broker-mcp, with a check that fails the build when it drifts.

Key numbers:
- Brokers catalogued: 90
- Renderable connect: 45
- Server described: 76
- Can place a trade: 57
- No MCP at all: 14

Links:
- Source: https://github.com/mphinance/awesome-broker-mcp (file catalog.json)
- Notes filed locally, not published.

## 2026-11-25: The estate, indexed

90 repositories are indexed, 74 personal and 16 under the tradernetwork org, one file each, kept in a local index.

Key numbers:
- Repositories: 90
- Personal: 74
- tradernetwork org: 16

Links:
- Notes filed locally, not published. The working notes behind these numbers are kept off this page.

---

Compiled from primary sources. Entries link their public artifact where one exists. Nothing here is financial advice.
