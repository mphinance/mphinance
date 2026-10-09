TITLE: The Slowest Part of My AI Pipeline Is Me
SUBTITLE: AI 60% | Business 30% | Mindset 10%
AUDIENCE: everyone

1 list of questions","title":null,"type":"image/png","href":null,"belowTheFold":false,"topImage":true,"internalRedirect":null,"isProcessing":false,"align":null,"offset":false}" class="sizing-normal" alt="Phinance mascot at the midnight build desk: 16 agents -> 1 list of questions" title="Phinance mascot at the midnight build desk: 16 agents -> 1 list of questions" srcset="https://substackcdn.com/image/fetch/$s_!Bgma!,w_424,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F6722cc5f-b753-46ea-8415-656b403a2c21_1024x1024.png 424w, https://substackcdn.com/image/fetch/$s_!Bgma!,w_848,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F6722cc5f-b753-46ea-8415-656b403a2c21_1024x1024.png 848w, https://substackcdn.com/image/fetch/$s_!Bgma!,w_1272,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F6722cc5f-b753-46ea-8415-656b403a2c21_1024x1024.png 1272w, https://substackcdn.com/image/fetch/$s_!Bgma!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F6722cc5f-b753-46ea-8415-656b403a2c21_1024x1024.png 1456w" sizes="100vw" fetchpriority="high">
- 
- Earlier this week an AI agent found a hole in our paywall. Don’t tell  though, that way he’ll never find out I almost broke his system.

One of our premium screener feeds was handing its full signal list to anyone who asked. No login, no subscription. The "Premium" lock on the page was a blur effect sitting on top of data the browser had already downloaded. If you knew where to look, you got the whole thing for free.

I didn't find it. A run called #69 did, in 64 minutes, at a time of day when I was doing something else, probably working very hard on something somewhere. It wrote the regression tests, broke its own fix on purpose to prove the tests would catch it, ran the full suite (8,795 tests, zero new failures), and then did the thing I'm proudest of: it decided not to ship. It opened a pull request and wrote me a note explaining that a change to paywall logic was a call a human should sign.

That pull request sat in my queue for days before I merged it.

Subscribe now

## What I'd steal from this article
If you run something small, this is the order I'd do it in. I could be wrong about most of it. I'm not wrong about the first one.

- Start where things get dropped. For us that was Discord bug reports. Route them, dedupe them, file them. The chatbot can wait. This is free context.

- Cheap model for sorting, expensive model for work. Classifying and routing runs fine on a flash-tier model for a fraction of a cent. Save the big ones for things that write code. Everyone knows this part.

- Cache on the source's timestamp, not a timer. The timer version was 648 calls a day, mostly re-reading nothing.

- Write the house rules down once. Every rule in my agents' prompt is a mistake I already made once. Before I built a launcher page for them, they only got followed on the days I remembered to type them.

- Parse model output strictly, and fail quiet. We had a scheduled health check whose parsing broke. It posted "Warning: Degraded Performance" into our ops channel every thirty minutes for days. Nothing was degraded. It's still turned off.

- Build the inbox that tells you what's yours. It only works once the rest exists, and it's the one I'd miss most.

We never had people doing any of this. Before the agents it was me, getting to it eventually, which mostly meant never.

## The chatbot is the demo
Every "AI for small business" pitch I get is a chatbot on your website. I understand why. A chatbot is easy to film.

- 
- We have one. Arya answers platform questions and pulls live options data through tool calls, so when somebody asks about the gamma picture on   she goes and gets it instead of inventing a number. There's a voice mode. There's a public MCP server so you can point your own Claude at our data and skip our UI entirely.

It's table stakes, and it doesn't save me an hour a week. If you run a small business and you only build one AI thing, I'd build almost anything else first.

What I'd build first is the boring part. Our members report bugs in Discord, in channels called #app-feedback and #report-a-bug, and for a long time those worked like your email inbox: somebody reports something real, it scrolls, it's gone. Now a bot reads every new message, checks it against every open GitHub issue, scores it 1 to 5, and either files a new issue or tacks the report onto the one we already have. The member gets a reply so they know somebody heard them.

Now "stuff people told us" is a list. Once you have a list, you can point robots at it.

## The Agent Launcher
TraderMatrix is small. Art runs the community, I write the screeners and the engine. There's no QA team, no ops person, no PM. There are 16 AI agents living in our repo, and I named all of them. payments-guardian only looks at Stripe and billing. quant-verifier audits every number a trader will act on. release-captain is the one that says no. a11y-mobile opens everything on an iPhone in Safari and finds out it's broken, which is a job I refuse to do and my members do every day.

This is the admin page where I point them at things.

- 
- 
[caption] The Agent Launcher. Pick a pass, pick a domain.You pick a kind of pass (bug hunt, hardening, usability, math check, ideate, or fix one specific issue) and a part of the codebase (options flow, screeners, billing, Discord, eleven of them in total). Then you hit go. I can read the prompt that will get sent in a big text box and manually input additional stuff or edit the existing prompt if I’d like, but I rarely have to anymore. The whole point is to fix the damn engine before you get on the road so you don’t have to worry about it right?

Before this page existed, launching a code review meant opening a terminal and typing a prompt from memory. Which meant the good reviews were the ones where I happened to remember the good prompt. Now the prompt gets built for me. Pick "Hardening" on "Screeners" and the team, the file paths and the house rules come with it.

The run lands in a queue. Our exec box picks it up, opens a Discord thread, and works. One at a time.

- 
- 

Right now there are 19 runs waiting at a recent average of 19 minutes each:

19 x 19 = 361 minutes, or about 6 hours

The page says 5.9 because the real average is a hair under 19. I'm writing this while it runs.

## The Ledger
The Ledger tab keeps every run. 140 of them since the first one 54 days ago: 112 succeeded, 7 failed, 3 I cancelled myself, 17 queued, 1 running as I write this, down from the 19 in that screenshot. Click any run and you get two boxes: what the agent reported back, and the exact prompt it was sent.

- 
- 
[caption] The Ledger. Every run, how long it took, and a link to its Discord thread.
- 
- 
[caption] Run #69's report. Verdict first.
- 
- 
[caption] The prompt as sent. Generated, not typed.A few lines from that prompt are worth stealing. Every one of them is in there because something went wrong first.

"Nobody is watching." The run is unattended. So the prompt tells it not to ask a question and wait for an answer that isn't coming. Make the call, and write down why, so I can review the judgment afterwards.

"Never trust a count written into a prompt." This line used to list the tests that were already failing, so the agent wouldn't panic about them. Then those got fixed quietly, a different test started failing, and the stale list would have waved the new failure through as "expected." Now the agent runs the tests itself before it touches anything and compares before and after. Otherwise it can't tell a failure it caused from one it inherited.

"Leaving a finished fix sitting in a PR for someone to chase is a failed run, not a cautious one." I wrote that because early runs were timid and left everything for me. The prompt also says to stop and leave a PR anyway when the change touches auth, payments or a database migration, or when the agent isn't at least 90% sure it's right.

Run #69 had both rules in front of it. Paywall logic isn't technically "payments," so it was allowed to ship straight to production. It decided a paywall was close enough, left the PR, and explained why in plain English in the report. I'd have made the same call.

## Needs you
The agents worked, and that created a new problem.

They filed issues, wrote long reports and asked me things. At one point I had 27 open issues and no way to tell which ones were waiting on a decision only I could make. The bottleneck was me.

So there's a tab called Needs you.

- 
- 
[caption] Needs you. 12 decisions, 8 actions.A cheap model (Gemini Flash) reads every open issue, its comments and the latest agent report, and sorts it into a bucket: needs my decision, needs an action from me, ready to fix, waiting on whoever reported it, or stale. The first two buckets are the tab. Tonight that's 12 decisions and 8 actions. Each decision comes with multiple-choice answers and a recommendation, so most of them take one click. "Ready to fix" gets a button that queues the fix. The last two buckets are hidden, because neither one is mine.

It's also pretty dumb. Here's the same classifier helping me triage a bug:

- 
- 
[caption] MCP does not stand for Most Critical Path.It wants to know whether the affected users are "MCP (Most Critical Path)" users. MCP is the Model Context Protocol. We ship an MCP server. It's in the sidebar of the page this question is rendered on. And a few cards down:

- 
- 
[caption] There is no developer.Its recommended answer is "Assign it to a developer for immediate implementation." Buddy. I am the developer. You're looking at him.

I left both in on purpose. A cheap model is bad at knowing things and good at sorting. All it has to do is notice that an issue is waiting on a human and phrase the question so that human can answer it fast. A wrong guess in a multiple-choice question costs me two seconds, because I'm reading it anyway.

## Theta, but for API calls
The part that keeps this cheap is how the answers get cached, and if you sell premium you already understand it.

The lazy way to keep the tab fresh is to re-classify every issue on a timer. A timer is theta. You pay it every hour on every position whether the thing moved or not. Back when I had 27 open issues:

27 issues x 24 hours = 648 calls a day

Almost all of them re-read an issue that hadn't changed. So instead the cache is keyed to the issue's own "last updated" timestamp. If nobody commented, nothing changed, and the answer from yesterday is still the answer. On a normal day 3 or 4 issues actually change:

648 / 4 = 162 and 648 / 3 = 216

Same damn feature, somewhere between 1/162nd and 1/216th of the bill. It's the difference between paying decay on everything you hold and only paying when something trades.

## Coverage
The last tab is the one I look at least.

- 
- 
[caption] Coverage. The empty cells are the point.It shows when each part of the codebase was last reviewed, and through which lens. The header on the page warns that a domain with no runs hasn't been looked at, which is different from clean. The lens columns also only count runs that finished, so an empty cell can mean an agent tried and fell over.

Look at the Bug hunt column. Two entries in the whole table. The last full bug hunt on our core platform code was 53 days ago. Billing has never had its math checked. I run the passes I find interesting and skip the ones I don't, which is exactly what this page exists to catch.

## The bottleneck
I spent a lot of years being the bottleneck in my own life and calling it being busy. 

I did not expect to end up rebuilding the tenth step as an admin page for GitHub issues, but here we are.

Run #69 found the leak, fixed it, proved the fix, and stopped to ask. Then it waited days for me. Sixteen agents, 140 runs, and the slowest part of the pipeline is still the guy with the merge button. The one in the mirror.

If you want the boring version with the actual code paths, the registry and the classifier schema, say so in the comments and I'll write it up. Fair warning: it's boring.

Subscribe if you want more of the build-in-public stuff. Half of what this thing earns goes back into the names I write about, in my real accounts, so you can always check my work.

~ Michael
