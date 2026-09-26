# Your Chatbot Is The Least Valuable AI You Will Build

*AI 60% | Business 30% | Mindset 10%*

![hero](hero.png)

**There are sixteen AI agents living in our repo right now. I named all of them. For a long stretch this summer I was still the thing slowing everything down.**

Not the models. Not the API budget. Me. A guy with twenty-seven open GitHub issues and a stack of agent reports he hadn't read.

Every pitch you see for "AI for small business" is a chatbot on your website. That's the demo, because a chatbot is easy to film. It's also the part of our stack I think about least, and if you run a small business and you only build one thing, I'd tell you to build almost anything else first.

I'm not an AI guy and I don't want to be one. I'm a trader who got tired of doing his own paperwork. Take that for whatever it's worth.

## What we actually are

TraderMatrix Pro is small. Art runs the community, I write the screeners and the engine. There's no support team. No QA, no ops, no PM. There's a Postgres database, a Discord server, a Next.js app, and about nine hundred things that need somebody to look at them.

That shape is the whole reason AI is worth anything to us. Nobody here is getting replaced. The work was just sitting there not getting done.

Start with the part customers see. It gets more valuable the deeper in you go.

## Layer one: the part customers touch

Arya is our in-app assistant. She answers questions about the platform and pulls live options data on demand through a tool-calling loop, so when somebody asks "what's the gamma picture on NVDA" she actually goes and gets it instead of hallucinating a number. There's a voice mode with speech-to-text and text-to-speech. There's a public MCP server so you can point your own Claude at our data and skip our UI entirely.

That last one is the only piece of layer one I'd call clever, and I only think so because it was cheap. Our data endpoints already existed. Wrapping them as tools meant a customer's own AI could use the product, which is a distribution channel that didn't exist eighteen months ago. I still don't know what it's worth. Ask me in a year.

The honest scorecard on layer one: it's table stakes. It doesn't make us money and it doesn't save me time. It's the price of looking like a 2026 company. Build it, don't fall in love with it.

## Layer two: the intake layer, where the money actually is

This is the part I'd tell a plumber, a bakery, or a two-person SaaS to build first.

Every business has an inbound pile. Ours is Discord. We have channels called `#app-feedback` and `#report-a-bug`, and for a long time they worked the way your inbox works: somebody reports something real, it scrolls, it's gone.

Now a bot polls those channels every sixty seconds. When a new message lands it does three things with a cheap model. It fuzzy-matches the message against every open GitHub issue to see if we already know. It scores importance one through five. It picks a category from a fixed list of eleven domain labels.

If it matches an existing issue, it appends the new report as a comment on that issue and replies in Discord so the member knows they were heard. If it's new and scores three or higher, it opens a GitHub issue. If it's low importance it just reacts with 👀, and if I disagree I slap a 🎫 on the message and it files anyway.

We had a second hole in the same wall. The in-app support widget wrote to a database table and sent an email, and that was it. A real security disclosure came through it once and never touched the issue pipeline. Same triage now runs on that path too, with one deliberate difference: widget reports open an issue but never trigger an automatic fix attempt, because that free-text box also catches billing questions and account problems and you don't want a robot writing code in response to "I can't log in."

There's more in this layer than I have room for. Nightly sentiment scoring on chat sessions so I can see whether people are frustrated without reading every transcript. An IPO headline classifier where regex runs first and the model is a second pass, invoked only when regex confidence drops under 0.7. A health watchdog that runs every two minutes, reconnects Redis, clears zombie jobs, warms stale database connections, and only calls a model when something is actually wrong.

Same move every time. The pipes already worked. The model just makes one cheap judgment call inside them.

I should show you one that went the other way, because the wins are boring without it. We had two scheduled GitHub jobs, a daily standup and a health monitor, that were supposed to read the repo and post a status to Discord. The health monitor's response parsing broke, nothing caught it, and it posted "Warning: Degraded Performance" into our ops channel every thirty minutes for days. *Nothing was degraded.* Both jobs are sitting in the repo right now with their schedules commented out and a note explaining why, which is a nicer way of saying I turned them off and never fixed them. Model output you don't parse strictly is just a very expensive way to cry wolf.

## Layer three: the admin page nobody sees

This is the one I wanted to write about. A real engineer will find plenty in here to laugh at. Fine. It ships.

So, the sixteen. They're grouped into four guilds, and the names are load-bearing, because a name tells you what the thing is allowed to care about.

**payments-guardian** only looks at Stripe, subscriptions, affiliates and promos, and it is the meanest one because billing is the domain where a bug costs a real person real money. **quant-verifier** audits every number a trader will act on: pricing, greeks, expected moves, GEX, win rates, lookahead bias. **seam-coordinator** exists because our screeners publish into Discord, so a new alert needs somebody checking the webhook tier before paid content leaks to the free channel. **design-critic** tells me my UI is ugly. **migration-auditor** reads database migrations so I don't drop a column at 11pm. **release-captain** is the one that says no.

There's also **a11y-mobile**, whose entire job is to open the thing on a phone in iOS Safari and find out it's broken, which is a job I refuse to do and my members do every single day. Sam gets to watch all of it and she's got opinions, but she's not on the roster. She reads the community, not the code. But I digress.

Those sixteen get pointed at eleven code domains, from billing to auth to screeners to Discord, each one scoped by real file globs. And there are six lenses, which are basically jobs: bug hunt, hardening, usability, math check, ideate, issue fix.

There's a page in our admin panel where I pick a lens and a domain, and it shows me the exact prompt it's about to run before I spend a token on it. Then I hit go. The run gets queued in a database table, a poller on my exec box claims it, opens a Discord thread, and works. Seventy-six runs so far.

Three design decisions in there that I think are worth stealing, and I learned two of them the hard way.

**The prompt is generated, not remembered.** Before this page existed, launching a code review meant opening a session and typing a prompt from memory. Which meant the good reviews were the ones where I happened to remember the good prompt. Now the prompt comes out of the registry: pick a lens, and the team, the file globs, and the house rules come with it.

**The preview and the real thing come out of one function.** The prompt you see in the preview is rendered by the backend, by the same code the runner gets at claim time. If I had written a second formatter on the frontend to save a round trip, the preview would eventually drift from reality and I wouldn't find out until a run did the wrong thing to a file.

**The brakes live in the code, where I can't overrule them at midnight.** One run at a time, twelve runs a day, hard caps. A stuck launcher or a fat-fingered click loop can't burn a weekly limit overnight while I'm asleep.

## The best thing we built just asks me questions

Now the tab that actually changed my week.

The agents worked fine. That was the problem. They produced long reports and filed issues and asked me things, and I had twenty-seven open issues and no way to see which ones were genuinely stuck on a decision only I could make.

So there's a tab called "Needs You." A cheap classifier reads every open issue, including its comments and the latest agent report on it, and sorts it into one of five buckets. Needs your decision. Needs an action from you. Ready to fix. Waiting on the reporter. Looks stale.

The first two are the tab. The third gets a "Fix it now" button, because if there's no question left to ask, there's nothing for me to do but fire it. The last two are collapsed behind a toggle, because neither one is mine.

The classifier costs about a tenth of a cent per issue and it's cached on the issue's own `updated_at` timestamp, not a time-to-live. That distinction is the entire reason the feature is cheap.

If you sell premium you already understand this one. A TTL is theta. You pay it every hour on every position whether the thing moved or not: (27 * 24) = **648 calls a day**, forever, most of them re-reading an issue that nobody touched. Caching on the source's own timestamp means you only pay when something actually trades. On a normal day that's **3 or 4 issues**. Same damn feature, roughly **1/200th** of the bill.

All of it boils down to one deliverable: a shorter list of decisions with my name on them.

## What to steal

If you run something small, here's the order I'd do it in.

**Start where things get dropped, not where customers can see.** Your inbound pile is where the compounding is. Route it, dedupe it, score it, file it. I could be wrong about the order of everything below this line, but I'm not wrong about this one.

**Use the cheap model for judgment and save the expensive one for work.** Classification, routing, and dedup run fine on a flash-tier model for fractions of a cent. Reserve the big models for things that produce artifacts.

**Cache on the source's timestamp.** Not a timer. Get this wrong and you'll cancel a good feature the first time you open the invoice.

**Make every AI feature fail open.** Our sentiment scorer never throws. On any error it returns "unknown" and the row gets written anyway. An AI feature that can take down the thing it's attached to is a liability, and the bullsh*t part is that you'll find out at the worst possible hour.

**Put a preview and a budget on anything autonomous.** Read the prompt before you pay for it, and set a hard cap so it can't spend while you're asleep.

**Then build the inbox that tells you what's yours.** This is the last one because it's the one you can only build after the rest exists, and it's the one that gives you your week back.

None of this replaced a person. We never had the people. It replaced the version of me who was going to get to it eventually and never did.

## The part that isn't about software

I spent a lot of years being the bottleneck in my own life and calling it being busy. Recovery taught me the pile was never the problem. What I didn't have was an honest way to look at the pile and say which parts are actually mine today.

That's all the "Needs You" tab is. It's a fourth step for a codebase. Somebody else does the sorting, and what's left is the short list of things only I can answer, and I answer them.

The best thing I shipped this quarter is a list of questions. It took sixteen agents to get me there.

If you're building something small and you want the actual code paths, say so in the comments and I'll do a follow-up with the registry structure and the classifier schema. Fair warning: the code is boring.

Subscribe if you want the build-in-public stuff. Half of what this thing earns goes back into the names I write about, in my real accounts, so you can always check my work.

~ Michael
