# Fact sheet: the unposted AI / broker drafts

Raw points pulled from the 5 unposted drafts, with the prose removed. Grouped by topic, not by draft.
Source tags: **D** = Skills Are Weak / Dispatcher · **K** = Skills Are Weak / Kitchen · **B1** = Broker Bot Wars Pt 1 · **B2** = Broker Bot Wars Pt 2 · **R** = AI Infra Restaurant (repo draft, older)

Flags: ⚠️ = contradicts another draft or is stale · ❓ = personal claim, needs Michael's OK · 🔍 = unverified fact

---

## 1. The setup (how he works now)

- Before: 5 coding agent windows open at once (D, K)
- Pain: typed prompts into the wrong window daily; lost track of which session was on which project; commits stepped on each other (D, K)
- Interim fix: renamed the sessions (K)
- His word for it at the time: "sounds exhausting" (K) ❓
- Movie ref: Avengers, "how does Fury see all of it" / "he turns" = Alt+Tab, human neck is the bottleneck (K)
- Now: talks out loud to ONE thing (Ember) (D, K)
- Ember: turns rambling into a brief → hands to a headless Claude Code worker → reads the diff + test output itself → reports back (D, K)
- Ember never writes code (D, K)
- Ember runs on a cheap model on purpose; talking + reading diffs doesn't need the expensive one (D, K)
- Workers: Sonnet, each in its own git worktree + own branch, per-worker dollar cap (D, K)
- Concurrency: ⚠️ "3 at once, rest wait in line, box has been OOM-killed before" (D) vs "2 cooks at a time" (K)
- Workers commit named files, never add-all, small commits (D, K)
- Orchestrator prompt is ~30 lines; scrubbed version is in a public gist (D): https://gist.github.com/mphinance/5e52ee671b2267e50f081969a3200f1d 🔍
- Key prompt rules (D):
  - "You are the mouth, the scoper and the reviewer. You do not write the code."
  - Review diff + test output yourself before reporting; say what the worker couldn't do / was unsure about
  - Never invent a result; haven't read the diff = don't know what changed
- He didn't invent any of it (D)

## 2. The rails (what workers can't do)

- Deny list: no push, no deploy, no payments CLI, no database client, no sudo (D, K)
- Real list is longer than 5 items (K)
- Ship ≠ merge: "ship" pushes a work branch + opens a DO-NOT-MERGE PR, only after he says yes out loud (D, K)
- Merging = production deploy, so merge stays his call, every time (D, K)
- The 2 rails that fixed his actual pain: one worktree per job; one front door (D)
- The rest is "damage control" (D)
- Backup API key slots: 6 wired into the code, never filled; primary got revoked; system dark most of a day (K) ❓🔍

## 3. What makes a skill strong (framework, used in D, K, B2)

- Most skill libraries = a paragraph of advice in a folder; model nods, then improvises (D, K)
- Strong skill = 4 parts: procedure · real tool/data source behind it · fixed output · a rail (what it must not do) (D, K, B2)
- The rail is the part most skills skip (K, B2)
- Example rail, DD template: every number carries a source or gets cut / marked unverified; dates verified or absent (D, K)
- Example: aggregator earnings date ≠ company/filing → "date not confirmed", left out (D)
- Example rail, 0DTE skill: drafts plan under hard risk rules, he places every order, skill doesn't get a vote (D, K)
- alpha-skills repo: github.com/mphinance/alpha-skills
  - ⚠️ count: 136 (D) / 137 (K) / 133 (B1) — repo today has **229 SKILL.md files** (2026-11-26, may include plugin dupes; pick one real number)
- "Some are rough, all have a procedure and a rail" (D)

## 4. Personal / kitchen material (K) — all ❓

- Punished by being sat at the kitchen counter as a kid; learned there anyway
- Bussed tables at 14
- Cooked Sunday omelets at 15, in braces
- He + family put up a few hundred lbs of sausage a year
- Jambalaya is his; secret is paprika he smokes, dries and grinds himself
- Dad's rule: stove against the wall is overrated; put stove + sink on an island in the middle so the cook faces the room
- Kitchen roles mapped: Ember = expediter (doesn't cook) · workers = cooks w/ own station · deny list = card taped above the pass
- Rules-of-the-line mapping: gas line = deploy · register = payments · walk-in = database · front-door key = push · another cook's knife = sudo
- Last step before a draft = he gives Ember his experiences via questions (the interview); the one thing that can't be automated

## 5. Broker directory: Awesome Broker MCP (B1)

- Free + public; question it answers: which brokers can an AI actually place an order through
- 94 brokers checked at the source (B1)
- 64 first-party servers (B1)
- 12 confirmed to have nothing; checked twice (B1)
- ~500 links probed; dependency files read (B1)
- Method: every entry opened at the broker's own docs or server repo; 2nd pass whose only job was to refute the 1st (B1)
- 2nd pass: 11 of 19 original entries needed correction; 2 written-off brokers had a route; 2 servers flipped (B1)
- Repo description (live): "verified directory of broker MCP servers — official vs community, what each can really trade, and who has no route at all"; last push 2026-11-17
- Subtitle brokers named: Schwab, Fidelity, Robinhood, IBKR, tastytrade, Alpaca, Webull, TradeStation, E*TRADE, Public (B1)

### Specific findings
- A README that says MCP isn't proof of MCP (B1)
- E*TRADE: library has a `place_order` function it never registers as a tool (B1, B2)
- OANDA: its one "order-capable" server has no MCP SDK in dependencies; it's a FastAPI app claiming MCP in prose; found via requirements.txt (B1)
- IBKR: built a server that physically cannot submit orders (B1) 🔍
- Alpaca + Kraken: paper by default; can turn trading tools off server-side (B1)
- Most community servers go live on a tool call with no broker-enforced approval step (B1)
- Official server that CAN place orders: Alpaca, Webull, tastytrade, TradeStation (B2)
- Schwab's order path is community-built, not Schwab's (B2)

### Thesis points
- Separate the brain from the hands: what decides the trade shouldn't be the connector that submits (B1)
- A guardrail in a config file gets edited at 2 a.m. (B1)
- Let the agent be smart without being armed (B1)

### The ecosystem plug (B1)
- alpha-skills = the brain; has a selector that reaches back into the broker directory once a plan is ready
- momentum-mcp: 73 open MCP tools on free data 🔍
- Vesper: agent built on all of it, still stops for a human

### Anecdote (B1) ❓
- He wired an agent to read a chart + decide; said "autonomous" out loud to another person; asked it to buy; it couldn't because his broker had no door
- Napoleon Dynamite "skills" joke told to his kid ⚠️ "he is four" ❓

## 6. Who builds broker MCPs (B2)

### Repo census
- 246 live GitHub repos cited by the directory
- Owners: companies 104 · individuals 133 · lists-of-lists 9 (=246)
- 36 broker/vendor orgs ship their own repos
- 490 humans commit across the 246
- 119 individuals own one outright
- 56 people commit to official broker repos; 30 read as firm staff
- 100 of 246 repos are ≥80% one person's commits (~2 in 5)

### Named maintainers
- Public.com: Tarric Sookdeo (@tarricsookdeo), DevRel; only human committer on Public's MCP (52 commits); touches all 7 Public repos ⚠️ (draft also lists his city + side projects; cut)
- Tiger Brokers: @tigersk, openapi-python-sdk, 1,443 commits
- OKX: @lilyDong 730 + @okxboon 457, onchainos-skills
- Longbridge: Jason Lee (@huacnlee), 253 commits on the terminal
- Luno: @echarrod, 111 of 114 commits on the official MCP
- IBKR MCP: @NitayRabi, 171 of 183 ⚠️ draft phrases it as "IBKR is NitayRabi"; almost certainly community, not IBKR staff
- Schwab CLI: @weig, all 426 commits
- Maintainers named per page in the directory

### README census (all 246, mentions only, not tested)
- 183 of 246 are MCP servers
- 75 read-only switch / trading tools off
- 60 dry-run or paper default
- 39 order memory / outcome history
- 35 preview-then-place / confirm step
- 28 tag orders with environment (live vs paper)
- 12 kill switch / halt
- 7 hard loss cap (2.8%)
- Takeaway: safety lives in a switch + a default; going live must be on purpose. More kill switches (12) than ceilings (7).

### Standouts
- a9lim/tasty-mcp: write tools behind a hard cap on total potential max-loss across positions + working orders; default $100; refuses naked short calls; always lets closing orders through (cap that blocks the exit = trap)
- mnemox-ai/tradememory-protocol: 1,450★, 20 MCP tools, local-first memory + risk brake, syncs fills, finds where history loses money, can refuse rule-breaking orders; @zychenpeng 408 of 410 commits
- qrak/LLM_trader: 141★, public ledger of every loss
- joncovington/MEICAgent: Claude Code agent, 0DTE iron condors on tastytrade, risk gates, dry-run default, paper shadow of 4 risk profiles vs live quotes
- No license (= all rights reserved): k1xme/schwab-mcp, cmike444/tastytrade-mcp
- 6 of the 11 best finds have <5 stars

### Thesis points (B2)
- A broker's AI surface is often one person; when they stop, the door closes
- Check the last commit date before wiring in; plan for that person leaving
- A number the agent can't cross beats a better prompt
- If you can switch safety off from the trading chair, it's a suggestion
- Companion NotebookLM notebook: briefing, gap analysis, infographic, audio (needs Google sign-in)
- Related repo artifact: docs/artifacts/broker-people/ (gap poster + explorer)

### Close (B2) ❓
- Recovery tie-in: sponsor = one person with a day job who picks up the phone; brokerages run the same program staffed by one name; "stayed sober by not keeping it in the house"

## 7. Older repo draft: AI infra as a restaurant (R)

Separate, older, generic. Overlaps the kitchen metaphor in K. Points only:
- Models = chefs (labor, not product)
- Ollama = your own kitchen; capex hardware, marginal cost electricity
- Open WebUI / LibreChat / AnythingLLM = dining rooms
- LiteLLM / OpenClaw = maître d' (routing, cost tracking, fallback)
- Chroma / Qdrant / Weaviate = pantry (RAG)
- Flowise / Langflow = recipe cards
- Langfuse = health inspector (observability = trade journal for AI)
- Unstructured = prep cook
- MetaMCP = kitchen manager (MCP tools)
- Field is ~3 yrs old, vocabulary not settled
- Has an infographic: ai-stack-restaurant-infographic.png

---

## Contradictions to settle before writing
1. Skill count: 133 / 136 / 137 vs 229 live
2. Workers at once: 2 or 3
3. Kid's age
4. IBKR: "built a server that can't submit" (B1) vs "IBKR is NitayRabi" (B2)
5. Who is "I": B1 flips between Ember and Michael
6. Two kitchen metaphors (K vs R): pick one, they collide

## Dropped on purpose
- The worker cost numbers in D (Michael: don't know what those are)
