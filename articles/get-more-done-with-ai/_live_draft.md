[IMAGE]

For these past few months in the beginning of building TraderMatrix.pro I was a glorified router for a bunch of expensive interns and I called it "productivity".

I had five coding windows open. I typed prompts into the wrong one, forgot which project a session was even on, and watched commits step on each other.

[BUTTON Subscribe now]

## One front door

I talk to one thing, out loud. It turns my rambling into a tight brief, hands the brief to a headless Claude Code worker, reads the diff when the worker finishes, and tells me what happened. Minions go off and do the work, report back to my dispatcher, who reports back to me while I sit here writing articles and buying stocks and ooh, butterfly.

[IMAGE]

The orchestrator runs on a cheap model, good ol’ DeepSeek v4.1. It’s super cheap, it’s fast, and it’s already got my rules in how I communicate. The workers are Sonnet, each in its own git worktree on its own branch, those little guys running off my Claude Subscription.

## The prompt

The SOUL.md in Hermes is what is doing the magic in this one, in a dedicated profile for just this purpose:



[IMAGE]

I put the scrubbed prompt in a gist so you can steal it: https://gist.github.com/mphinance/5e52ee671b2267e50f081969a3200f1d

## The rails

A prompt is the mouth - my mouth. The hands are a dispatch script that gets sent off from it, and the rules in it are what let me walk away and.. ooh, another butterfly!

[IMAGE]

One worktree per job, and workers commit named files, never "add all." That is how commits stopped stepping on each other.

One front door. I cannot type into the wrong window because there is only one window.

The rest is pretty much damage control. A deny list so a worker cannot push, deploy, touch the payments CLI, run a database client, or sudo anything. I keep at most hree running at once on this box because I haven’t invested enough  into my server holdings yet. 

The one I care about most: a yes to ship is not a yes to merge. Ship pushes a work branch and opens a do-not-merge pull request, and only after I say yes out loud. Merging deploys to production, so that call stays with yours truly, for I am the master of my own…something.

## Your skills are weak

Skill libraries are all over my feed. Most of them are a paragraph of advice in a folder. The model nods, then improvises.

A strong skill has four things: a procedure, a real tool or data source behind it, a fixed output, and a rail that says what it must not do.

[IMAGE]

My due diligence template is a good example of the rail part. Two of its ground rules: every number carries a source, or it gets cut or marked unverified. Dates are verified or absent. If an earnings date came from an aggregator and not the company or a filing, the draft says "date not confirmed" and leaves it out.

My 0DTE skill drafts the plan with hard risk rules. I place every order. The skill does not get a vote on that.

There are 136 of these in the open at github.com/mphinance/alpha-skills. Some are rough. All of them have a procedure and a rail.

## The part that is not about AI

I try to run the rest of my life the same way: one thing in front of me, and a rule I follow even when I do not feel like it. Here the honest voice waiting when the work is done tells me what I actually did, and it shows me a diff.

If you build something like this, tell me what breaks. I would rather hear it than find out in production.

If you want the data side of what I build on, here is tradermatrix.pro (that is my referral link) and youtube.com/@TraderMatrixHQ.

[BUTTON Share]

~ Michael