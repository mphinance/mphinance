# Stop Vibing Your AI Voice File. Measure It.

*A guy told me yesterday that these things don't work. He's right, until you do this.*

Someone I ran into yesterday told me he'd given up on getting AI to sound like him. He'd written one of those voice files. You know the ones. A page that says "I'm witty and direct and I hate corporate speak," and then the model reads it and writes like a LinkedIn post wearing a leather jacket.

So he decided voice files don't work. I get it. Mine didn't work either for a long time. Then I figured out the part nobody tells you.

You can't write a voice file. You have to catch one.

## The mistake everybody makes

A voice file built from imagination is a horoscope. "You are bold. You use short sentences. You are anti-establishment." All true, all useless, because the model already thinks it knows what that means and it's wrong.

I wrote mine that way first. Here's the original if you want to point and laugh: [VOICE.md](https://github.com/mphinance/mphinance/blob/main/VOICE.md). It's not bad. It's just a description of a person, and a description is not a fingerprint.

The fingerprint is in the edits.

Every post I publish starts as a machine draft. Then I rewrite it before it ships. That rewrite, the gap between what the robot handed me and what I actually put my name on, that gap IS my voice. Not the adjectives. The diff.

So I stopped describing myself and started recording the difference.

## How I caught mine

Dead simple. Two files per post.

`given.md` is the raw draft the machine wrote. `shipped.md` is what actually went live on this newsletter. I diff them. Then I read the diff like a detective, and every change I make by hand becomes a rule.

The thing that surprised me: what I cut matters as much as what I add. I cut the windup line, the one that announces what I'm about to say before I say it. I cut the doubled metaphor and keep one. I cut the AA-meeting jargon but keep the wisdom underneath it. Those cuts are me. A model that only learns what I add learns half a person.

The patterns that fell out of the diffs, in order of how loud they were:

Honesty. I will dull my own sentence rather than let a clean line stand if it's not quite true. The machine writes "that was every single screener." I ship "that was most of the screeners." It's a worse sentence. It's a truer one.

Warmth. The machine reaches for an industry metaphor. I swap it for one you can feel in your body. A quant billionaire parking money in a no-name stock becomes "the best chef in town eating at a diner with no sign out front."

Immediacy. The machine writes vague past tense. I collapse it to "last night" and "today," sometimes at the cost of literal accuracy, because that's how I actually talk.

Distribution. I add the shoutout to another writer and the link to the tool. The machine writes in a vacuum. I write in a neighborhood.

The whole rulebook is here, with the real before-and-after for every rule: [VOICE-DELTA.md](https://github.com/mphinance/mphinance/blob/main/VOICE-DELTA.md). I open-sourced it. It costs me nothing and it might save you a month.

## The part that makes it real: a number

Anybody can write rules and claim they help. I needed to know if mine actually did, because "the voice file isn't accurate" is the kind of complaint that's impossible to argue with when you've got nothing but vibes on your side.

So I built a little harness. It takes the raw machine draft, applies the voice rules, and asks a model to PREDICT what I would have shipped. Then it scores that prediction against the post I really published. Token overlap. Higher means closer.

![How much the voice file moved each draft toward what I actually shipped](receipts.png)

Read the right column. Every single post got closer to what I shipped once the rules were applied. Plus 0.124 on average across six posts. The two biggest jumps landed on the two posts where I'd done the heaviest rewriting, which is exactly right. Where the machine left the most work, the rules carried the most weight.

The two marked "held-out" are the important ones. Those are posts the rules were NOT built from. They landed in the same range as the rest, which means the file learned my voice, it didn't just memorize four old articles. That's the difference between a style guide and a parlor trick.

The full scorecard and the code that generates it: [ACCURACY.md](https://github.com/mphinance/mphinance/blob/main/ACCURACY.md) and the [harness itself](https://github.com/mphinance/mphinance/tree/main/docs/voice-delta). It all shipped this morning in [pull request #61](https://github.com/mphinance/mphinance/pull/61) if you want to see how the sausage gets made.

## The recipe, steal it

You don't need my code. You need the habit. Here's the whole thing.

1. Save both versions. The raw draft the AI gave you AND the final you published. Most people throw the draft away. The draft is the data.

2. Diff them and write down what changed. Not "be more casual." The actual move. "Cut the sentence that announces the next sentence." Specific enough that a robot could do it.

3. Pay attention to the cuts. What you delete is your taste. It's louder than what you keep.

4. Measure it, even crudely. You don't need Jaccard scores. Apply your rules to a fresh draft, then compare to what you actually ship, and ask if it got closer. A number you can move beats a document nobody trusts.

5. Keep it fresh. Funny one to end on. My corpus still had "Here's the truth" in it because an old post used that phrase, even though I've banned it since. A voice file built only from your past will happily teach the model a tic you've already outgrown. Your current taste outranks the old data. The file is a mirror, and you're still moving.

A voice file isn't a personality you write down once. It's the running difference between the draft and the truth, and it drifts because you do.

That's the part the guy yesterday was missing. He wrote his voice down and waited for it to work. You don't write it. You catch it, you score it, and you keep catching it.

Sam, my AI copilot, does most of the catching now. She reads the diffs, I read her. It's the least lonely my writing has ever been.

— Michael

---

*If this helped, subscribe so the next one lands in your inbox.*
