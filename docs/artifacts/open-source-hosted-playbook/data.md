# Blueprinting commercial open source: the free code + paid convenience operator manual

Plain-data version. Compiled by Ember with NotebookLM, 25 Nov 2026.
Case study: Postiz, by Nevo David. Sources listed at the end.

## The model

Free code creates friction-free distribution. Hosted infrastructure is what you sell.

- Friction-free distribution: a public repository is a global marketing engine. Auditable code kills buyer skepticism and community pull requests speed development without new headcount.
- No feature gating: monetize server administration, pre-approved OAuth platform approvals, managed API keys and uptime instead of walling features.
- Self-funding flywheel: free tiers capture developer mindshare; high-intent buyers self-select into the paid cloud to buy back time.

Operator mindset shift: traditional SaaS spends on cold outbound to convince skeptical buyers. Open source spreads for free to build trust, and the transaction becomes buying operational convenience rather than code access.

## The case: Postiz

An agentic social media scheduler across 30-plus networks. Public AGPL-3.0 code, paid hosted cloud.

Tech stack (from the founder's technical posts and the GitHub repo):
- Monorepo: pnpm workspaces
- Frontend: Next.js (React)
- Backend: NestJS
- Data and ORM: Prisma on PostgreSQL
- Cache and queue: Redis with BullMQ
- Orchestration: Temporal
- Email: Resend

Repository metrics:
- GitHub stars: 42,400+
- Forks: 8,100+
- Docker downloads: 4,790,000+
- License: AGPL-3.0 since January 2025

The Docker image was the first community request and the first thing built. Self-hosters deploy through Coolify, Portainer or Unraid.

## The revenue timeline

- Nov 2024: about $700/month (founder-reported)
- Jan 2025: about $2,100/month (founder-reported)
- Jul 2025: $6,523/month (founder-reported)
- Aug 2025: $12,648/month (founder-reported, from the n8n turn)
- Nov 2025: $14,200 post figure, $16,049 Stripe (verified)
- Feb 2026: about $46,000/month (Stripe-verified)
- Jun 2026: about $152,000/month; $113k MRR, $1.3M ARR (Stripe-verified)
- Sep 2026: about $248,000/month (Stripe-verified)
- Oct 14 2026: $3.1M ARR, about $258,000+ MRR (founder-reported)
- Nov 2 2026: $375,142 MRR, $1,688,428 all-time (Stripe-verified via TrustMRR)
- Nov 24 2026: about $459,000 MRR, about $5M ARR (Stripe-verified)

Notes: the August 2025 figure comes from a post that mislabels the year as 2024. The Nov 2 subscriber count corrected a source typo to 10,302 active subscribers.

## Lever 1: open-source distribution

- Directory seeding: submit to Awesome Self-Hosted, Awesome OSS Alternatives and Open Alternative for high-authority backlinks and direct discovery.
- Micro-release marketing: ship every minor feature as a numbered version and post the notes to r/selfhosted and DEV.to. Open-source progress reads as news, not ads.
- Community-driven adaptation: build what early issues ask for. The Docker image drove container usage past 4.79 million downloads.

## Lever 2: automation ecosystems

Doubled monthly revenue from $6,523 to $12,648 in one month by moving into the n8n automation crowd.

- Expose a clean public API and webhooks.
- Ship an official n8n node, built in about an hour with Cursor from n8n's template.
- Cold-email community owners a value-first offer with an affiliate link, from dedicated warmed-up domains.
- Community moderators built ready-made n8n templates carrying affiliate links, becoming a zero-CAC sales force.
- Users who run software through background workflows churn less than dashboard users.

## Lever 3: agents and the MCP server

- MCP server shipped April 2025, a CLI, an OpenClaw skill in January 2026, and docs for 17 agents.
- Revenue multiplied fifteen times between November 2025 and September 2026, the months agent frameworks spread.
- Nevo's Brain, a free MCP server that plugs a growth playbook into an assistant, is a top-of-funnel developer magnet.
- Postiz sells the publishing layer with per-network rules, media upload and a human-approved calendar. The intelligence lives in the customer's own agent.

## Packaging and unit economics

- Self-hosted: free forever, AGPL-3.0, your own infra. You create your own platform developer apps (weeks of approvals).
- Cloud: subscription per plan, 7-day trial, pre-approved apps, capped channels, managed AI credits, automated updates, hosted MCP endpoints.
- Plans: $29 to $99 a month, about $23 to $79 billed yearly.
- October 2026 unit economics: $262,899 MRR across 7,683 subscriptions, about $34 per subscription a month.

## The four commercial open-source models

- Open core: core open source, enterprise features (SSO, SCIM, RBAC, audit logs) proprietary. Examples: GitLab, PostHog, Langfuse, Carbon, WPDeveloper.
- Managed cloud: sell convenience, uptime and infra management. Examples: Supabase, Grafana Labs, xCloud, Postiz Cloud.
- Dual licensing: copyleft plus a paid commercial license, requiring the vendor to hold all copyright via CLAs. Examples: Mattermost, Ever Gauzy.
- Support and services: software wholly free, sell SLAs, engineers and compliance certifications. Examples: Red Hat, Langfuse Enterprise.
- Source-available variants: Sentry's Functional Source License (converts to Apache-2.0 after two years) and n8n's Sustainable Use License.

## Peer benchmarking

- GitLab: open core, MIT core plus proprietary /ee, $579.9M FY24 revenue, 30k+ paying customers.
- Grafana Labs: managed cloud plus enterprise, open core plus proprietary cloud, $400M+ ARR, 20M users.
- Supabase: managed cloud, Apache-2.0, $25/mo Starter to $599/mo+ Team.
- n8n: sustainable use plus cloud, fair-code, 20 EUR/mo cloud to 667 EUR/mo self-hosted business.
- Cal.com: open core later partly closed, MIT core (Cal.diy) plus proprietary enterprise.
- Postiz: managed cloud, AGPL-3.0, about $459k MRR and about $5M ARR, bootstrapped.

## Failure post-mortems

- Linvo (2021): $5,000/month revenue but heavy server costs and manual support tickets with no automated leverage. Shut down, founder in debt.
- Log4j: critical infrastructure maintained by unpaid volunteers. Tidelift reports 60% of maintainers unpaid and 60% who have quit or are considering it.
- HashiCorp and Redis: relicensing to BSL (August 2023) and off BSD (March 2024) triggered OpenTofu within 72 hours and Valkey from AWS, Google and Oracle.

## Risks for the operator

- Platform dependence: all channels run on developer approvals the vendor holds and interfaces the platforms can change or revoke. The Railway incident took Postiz down about 15 hours and forced a 140-key rotation.
- Solo-founder optics: the "solo, no investors" story hides four remote employees plus paid ad help, and a self-reported burnout.
- Growth stunts: a staged firing and fake source-leak drew 400,000+ views, high attention and real trust risk.

## The playbook

Phase 1, strategy and repository:
1. Pick the license. AGPL-3.0 if cloud copycats are the threat. Keep core capability un-gated.
2. Architect a modern monorepo and ship a Docker Compose file for frictionless self-hosting.
3. Set OAuth boundaries: official approved flows only, no credential scraping, tokens stay local.

Phase 2, launch and seeding:
4. Seed the self-hosting directories as primary launch vectors.
5. Adopt a micro-release cadence across r/selfhosted and DEV.to.

Phase 3, automation ecosystems:
6. Build native nodes for n8n and Make.com with clear docs.
7. Value-first cold outreach to niche automation leaders with a template and an affiliate link.
8. Sell the workflow, not the UI, for lower churn and higher lifetime value.

Phase 4, agents:
9. Expose MCP and CLI surfaces for Claude, ChatGPT, Cursor and Codex.
10. Ship free developer magnets that funnel toward the paid cloud.

## Takeaways

- Code is distribution, convenience is revenue. Never gate core features.
- Ecosystem distribution beats feature depth. Embed into workflows people already run.
- Transparency outlasts hype. Anchor claims in processor-verified data and build real redundancy.

## Sources

Primary and verified:
- TrustMRR Postiz profile, Stripe-verified: https://trustmrr.com/startup/postiz
- Postiz GitHub repository: https://github.com/gitroomhq/postiz-app
- Postiz pricing: https://postiz.com/pricing
- Aiolum Postiz case study: https://aiolum.com/story/postiz/
- ARR Club, Postiz $5M ARR: https://www.arr.club/signal/postiz-hit-5m-arr-adding-2m-in-a-month-fully-bootstrapped
- wouldit.work Postiz case study: https://wouldit.work/case-studies/postiz
- Linux Foundation COSS report: https://www.linuxfoundation.org/hubfs/Research%20Reports/LFResearch_COSSReport_102926.pdf
- Open Core Ventures, the open core paradox: https://opencoreventures.com/insights/the-open-core-paradox/
- OSSAlt open-source business models: https://ossalt.com/guides/open-source-business-models-how-oss-companies-make-money
- readsignal open-source growth engine 2026: https://www.readsignal.io/article/open-source-growth-engine-2026
- startise, balancing growth and sustainability: https://startise.com/how-open-source-businesses-are-balancing-growth/
- itHub, how open source companies make money: https://www.ithub.directory/blog/how-do-open-source-companies-make-money
- Nevo David on DEV.to: https://dev.to/nevodavid/i-did-it-my-open-source-company-now-makes-142k-monthly-as-a-single-developer-1179
- Nevo David on Hacker News: https://news.ycombinator.com/item?id=46076878
- Dan Raine, the Raine Report: https://danraine.substack.com/p/he-gives-his-software-away-free-it
- Nevo David on X: https://x.com/wickedguro/status/2112240445187031273

Paywalled, not extracted:
- Indie Hackers, growing an open-source product to $1.3M ARR: https://www.indiehackers.com/post/tech/growing-an-open-source-product-to-1-3m-arr-in-two-years-hbMiXIoZsueV9D3L58DP
- Indie Hackers, $5M ARR: https://www.indiehackers.com/post/numbers/a-bootstrapped-social-media-scheduler-says-it-reached-5m-arr-e2ZJb6l2sNFMj9iVBH03
- Indie Hackers, $400K MRR: https://www.indiehackers.com/post/numbers/an-open-source-social-media-scheduler-has-passed-400k-mrr-its-founder-says-oP6Ojv6lcrtLTEBWbl9h
- gitpop, open source business models 2026: https://gitpop.com/blog/open-source-business-models-2026
- FourWeekMBA, the open core model: https://fourweekmba.com/open-core/
