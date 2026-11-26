# Outline: AI / broker series (3 posts)

Built from `factsheet-ai-broker-series.md`. Beats only, no prose. The words are Michael's.

## Default calls on the 6 contradictions (override any of them)
1. **Skill count**: alpha-skills has **144 unique skills** on GitHub today (229 SKILL.md files counting plugin copies). Use "about 140" and re-check on publish day.
2. **Workers at once**: say "two at a time". The 3 + OOM story only goes in if it actually happened.
3. **Kid's age**: cut it. The joke works without it.
4. **IBKR**: drop "IBKR built a server that can't submit." Say "the most-used IBKR MCP is one community dev (@NitayRabi, 171 of 183 commits)." Verify before naming him.
5. **Who "I" is**: Michael, every post. Ember is a tool he talks to, named in the third person.
6. **Kitchen**: K (line kitchen, expediter, the pass) wins. R (restaurant-as-AI-stack) is out of this series.

Global cuts: worker cost numbers, Public.com maintainer's city and side projects, "I know your username".

---

## Post 1: The Kitchen (ships first; Post 3 leans on its framework)
**Working title**: Skills Are Weak. Rails Are the Point.
**Subtitle**: `AI 60% | Life 40%`-style mix, numbers TBD

1. **Cold open**: 5 agent windows, typing into the wrong one, commits stepping on each other. The Fury/Alt+Tab bit: the neck is the bottleneck.
2. **The fix**: one front door. Talk out loud to Ember. Ember writes the brief, hands it to a worker, reads the diff itself, reports back. It never writes code, and it runs on a cheap model on purpose.
3. **The line**: worker = cook with its own station (worktree + branch). Two at a time.
4. **The kitchen story** (❓ his to tell or cut): punished at the counter, bussing at 14, omelets at 15, Dad's island-stove rule (the cook faces the room). That rule is the whole design.
5. **The card above the pass**: deny list mapped to the line. Gas line = deploy, register = payments, walk-in = database, front-door key = push, another cook's knife = sudo.
6. **Ship ≠ merge**: a do-not-merge PR, opened only after he says yes. Merge is his call every time.
7. **What a strong skill is**: procedure + real data + fixed output + rail. Most libraries skip the rail. Examples: the DD template rule (every number sourced or cut; the earnings-date story) and the 0DTE skill (it doesn't get a vote).
8. **The admission**: the 6 empty backup key slots, and being dark most of a day (❓ keep only if he's fine owning it). Good humility beat.
9. **Close**: the interview step. The one part that can't be automated is his experience. Link alpha-skills (about 140) and the orchestrator gist.

Cut from D/K: the duplicate Dispatcher framing. D and K become one post.

---

## Post 2: The Doors (Broker Bot Wars Pt 1)
**Working title**: Which Brokers Will Let an AI Place a Trade?
**Subtitle**: `Trading 50% | AI 50%`-style

1. **Open**: the anecdote. He wired up an agent, said "autonomous" out loud, asked it to buy, and the broker had no door. The Napoleon Dynamite joke goes here, without the age.
2. **The question**: which brokers can an AI actually order through? Nobody had a straight list.
3. **Method** (short): 94 brokers checked at the source, about 500 links, dependency files read, then a second pass whose only job was to prove the first one wrong. It corrected 11 of 19 entries.
4. **The scoreboard**: 64 first-party servers, 12 with nothing (checked twice). Official servers that can place orders: Alpaca, Webull, tastytrade, TradeStation. Schwab's order path is community-built.
5. **Gotchas** (the fun part): E*TRADE's place_order is never registered as a tool, OANDA's is a FastAPI app pretending to be MCP, and the IBKR one is a single person. A README saying "MCP" proves nothing.
6. **Thesis**: separate the brain from the hands. A guardrail in a config file gets edited at 2 a.m. Let the agent be smart without being armed.
7. **Close**: link awesome-broker-mcp. The alpha-skills → directory selector is one line. momentum-mcp gets one line only if the 73 is verified; otherwise cut it.

Cut: Vesper plug unless he wants it.

---

## Post 3: The People (Broker Bot Wars Pt 2)
**Working title**: Your Broker's AI Is One Guy
**Subtitle**: `Trading 50% | AI 30% | Recovery 20%`-style

1. **Hook stat**: 100 of 246 repos are at least 80% one person's commits. That's about 2 in 5.
2. **The census**: 104 companies, 133 individuals, 9 lists. 490 humans commit across the 246; 119 individuals own a repo outright.
3. **Faces** (handles and commit counts only, no personal detail): Public's MCP is one DevRel person with 52 commits; @weig wrote all 426 commits of the Schwab CLI; Luno's MCP is @echarrod at 111 of 114. Pick 3, not 8.
4. **What the READMEs promise** (mentions, not tested): read-only switch 75, paper default 60, kill switch 12, hard loss cap 7 (2.8%). More off-switches than ceilings.
5. **Standouts**: a9lim/tasty-mcp, whose $100 max-loss cap always lets closing orders through, and tradememory-protocol, which refuses rule-breaking orders. One line each for LLM_trader and MEICAgent. 6 of the 11 best finds have fewer than 5 stars.
6. **Practical**: check the last commit date, plan for that person leaving, and watch the no-license trap (k1xme/schwab-mcp, cmike444/tastytrade-mcp). A number the agent can't cross beats a better prompt. If you can switch safety off from the trading chair, it's a suggestion.
7. **Close** (❓): the sponsor parallel, one person with a day job who picks up the phone. "Stayed sober by not keeping it in the house." That's the strongest ending in the series if he wants it public.

Optional: the NotebookLM companion and the broker-people poster as a figure.

---

## Order and checks before any push
- Order: Post 1 → Post 2 → Post 3.
- Before each push: re-pull the counts, verify every 🔍, close the Substack tab, and back up the existing draft (Dispatcher 224084512, Kitchen 224799516, Pt1 224767660, Pt2 225954163).
- Dispatcher draft: delete or archive it once Post 1 replaces it.
