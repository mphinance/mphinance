# Agent skills harvest — Trendshift scan, 2026-09-06

Source: a one-time pass over trendshift.io (daily top 10, weekly, monthly Jul + Aug 2026, yearly),
filtered for AI-agent/skills/orchestration relevance, cross-checked against what's already in
`~/projects/tdpro/` and `~/projects/trading-agent/`. Raw listings (all ~100 entries, unfiltered)
live in the session scratchpad if the full data is ever needed again — this file is just the
curated, assignable subset.

Six of eleven finds are more relevant to `~/projects/trading-agent` than anything in `tdpro/` —
those are dropped as a local, uncommitted `AGENT_SKILLS_HARVEST.md` in that repo's `docs/` instead
of duplicated here.

## To assign

| Repo | Assign to | Why |
|---|---|---|
| `coreyhaines31/marketingskills` | `marketing/draft-skills/` | 70+ marketing skills, each references a shared `product-marketing.md` foundation doc + a "Related Skills" cross-reference section. Direct template for the 8 drafted skills already sitting there — they're missing the shared-foundation-doc pattern (`marketing/handoff-kit/PRODUCT-TRUTH.md` could serve that role). |
| `blader/humanizer` | `mphinance` (here) | Claude Code skill that strips 25 categorized AI-writing tells by learning from 2-3 paragraphs of real writing, then applies those voice markers to a rewrite. Same problem `VOICE.md` + the recent humanizer/self-edit-pass commit (`28735fba`) are already solving by hand — worth diffing our checklist against their 25-pattern taxonomy. |
| `msitarzewski/agency-agents` | `warroom/` | A full roster of specialized agent personas. Same shape as Nyx + spokes, worth comparing persona-definition structure against `warroom/agents/`. |
| `stablyai/orca` | `warroom/` | Hub-and-spoke coordination via git worktrees: one hub distributes a prompt, N spoke agents work in isolated worktrees, hub does side-by-side diff review and picks the merge. Closest analog to Nyx promoting from `inbox/<name>.md` to `todo.json` — except Orca's spokes get full worktree isolation rather than just writing files, which would let warroom spokes make actual code changes without stepping on each other. |
| `anthropics/skills` | `TraderDaddy-Pro---Whop/.claude/skills/`, also `trading-agent/skills/` | Anthropic's own canonical Agent Skills spec repo. Both of these already have skill directories following the shape informally — worth checking for drift against the actual spec. |

## Not assigned — competitive/landscape awareness only

`openai/codex`, `deepseek-ai/deepseek-harness`, `xai-org/grok-build` (coding-agent harnesses),
`block/buzz`, `666ghj/MiroFish` (agent swarm platforms), `firecrawl/firecrawl`, `D4Vinci/Scrapling`
(scraping infra) — all trended, none map to a specific gap in this workspace right now.
