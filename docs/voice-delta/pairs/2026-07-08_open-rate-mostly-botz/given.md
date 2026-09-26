# 🤖 Your $OPEN Rate? Mostly $BOTZ.

*Business 50% | AI 30% | Mindset 20%*

I opened my own Substack export this week. The one Substack hands you and nobody actually reads.

Then I read it. All of it. Not the pretty growth chart. The 163 little files buried three folders deep that log every single time somebody, or something, opened one of my emails. 44,393 rows of it.

Here is what those rows told me: **97% of my "opens" are machines.**

## Let me be specific, before you screenshot that

They are not bots in the scary sense. Nobody is farming me. What is actually happening is Apple Mail Privacy Protection and Gmail's image proxy. Both of them pre-fetch the little tracking pixel the second the email lands in the inbox, before a human touches anything.

The pixel fires at delivery. Not at reading. So the "open" gets counted whether you read me over coffee or your phone quietly loaded the image at 3am while you slept.

That is the whole trick of an open rate. It is not a lie exactly. It is a number measuring a robot's reflex and handing it to you like it measured a human's attention.

Here is my actual donut. Purple is the privacy proxy. Orange is Gmail. The tiny slivers at the bottom, the iPhones and the Macs and the actual thumbs, that is you.

![61.4% privacy proxy, 35.3% Gmail. The slivers are the humans.](who-actually-reads.png)

My headline open rate says 38.7%. Feels good. Looks like a real number on a dashboard. Out of 44,393 opens, roughly 1,465 came from a device I can prove had a person behind it.

Your newsletter looks exactly like this. So does every newsletter you have ever been jealous of. The person quoting their open rate at you on a podcast is quoting a robot's reflex. Almost nobody says that out loud. I just did.

## So I built the thing that says it

The tool is open source. It runs entirely in your browser, nothing uploads, nothing gets stored. You drop in your own export zip and it reads the whole thing, the part Substack never bothers to surface.

I vibe-coded the whole thing in a day. The link is at the bottom and the code is free, because a dashboard that only flatters you is not a dashboard, it is a mirror you paid for.

Almost none of it needed AI, by the way. The "your readers are robots" finding is arithmetic on a user-agent string. The recommendation engine that tells you what to write next is plain Python rules. Most of the AI-for-creators market is selling you a wrapper around a `groupby`. This one is honest about that.

## The part that stung more than the robots

I clustered every post I have ever written by topic and joined it to open rate.

My recovery and psychology writing, the addiction-and-discipline stuff, the posts where I map getting sober onto not blowing up an account, opens best of anything I do. My AI-terminal and screener content, the stuff I am proudest of building, opens worst.

![Themes, ranked by who actually opens them.](themes.png)

Sit with that. I spend my energy on the tools. My readers show up for the confession. That is either a redirect or a fight worth having in public, and I honestly do not know which yet.

## The title formula, since yours probably isn't working

You want to know why your titles do not get clicks? Your own data already knows. Here is mine, measured across the whole archive.

![What actually moves open rate in a title.](title-formula.png)

A `$TICKER` in the title is worth **+7 points**. A question mark, **+4.6**. And the one that hurts: putting a number in your title actually **costs** you a couple points. The whole listicle gospel, the "7 ways to" thing everybody swears by, is backwards for my list.

Look at the title of this post again. Ticker pun, question mark, no digits. I did not guess. I read the file.

## And they decide fast

One more, because it changes how you should think about the paywall. Of the paying subscribers I could trace, the median gap between their last open and their first payment is **0.7 days**.

They do not marinate. They read something that lands, and they convert while it is still hot. Which means the ask belongs inside the post that is working, not in some drip sequence three days later when the feeling is gone.

A screener does not pick trades. And a growth chart does not tell you why anyone paid you. The export does. You just have to open the ugly file.

## Go break your own numbers

The whole thing is free and open. Drop in your export and find out how many of your readers are actually awake.

[github.com/mphinance/substack-data-mining](https://github.com/mphinance/substack-data-mining)

I put half of what this newsletter earns back into the exact names I write about. I am not going to hide the one tool that shows me my open rate is mostly a robot's reflex. If it stings me, it will teach you.

We spend so much of this counting the wrong opens. The likes, the pixel-fires, the vanity number that a machine loaded while we slept. The count that matters is the small one. The 1,465. The people actually awake and reading and deciding, in less than a day, that you were worth it.

Write for them. Everything else is Gmail loading an image.

~ Michael

---

*If this helped, subscribe so the next one lands in your inbox.*
