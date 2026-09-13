# NOBODY BANS THE TABLET
*AI 50% | Mindset 30% | Trading 20%*

In 2020 my kid was two years old and the world was locked in the house. We had rules about screens. We had opinions about screens. Then we had a toddler, two working parents, and nowhere to go, and the tablet went into the little hands like everybody else's did.

You know who raised my kid that spring? Blippi. The orange-suspenders guy. And I'd love to tell you it rotted his brain, because that's the story you're supposed to tell, but the actual result was that Blippi taught him his colors and his first ten numbers.

The lesson stuck with me. It's like trying to stop kids from watching YouTube or using a tablet. It needs to be directed, healthy portions, don't overuse any one tool, get confirmation. You don't ban the thing. You point it somewhere safe and you check the output.

I watched the same physics at Six Flags. No kid in history has ever stopped swinging on the monkey bars because a parent yelled stop. The move that actually works is telling them which bars are low enough that the fall doesn't hurt.

Hold that thought, because the AI-in-trading argument is the same argument, and I want to pick a fight with a guy I mostly agree with.

## The guy who banned the tablet

Obsidian Edit (he writes at [substack.com/@obsidianedit](https://substack.com/@obsidianedit)) posted a note in July that a lot of people nodded along to:

> "I'd like to talk about AI, why do I not use ANY LLM in our entire platform and all our models? ... our models can and WILL beat any LLM or chatbot system all day every day. LLMs are noisy and you're going to get a DIFFERENT output every single time that is randomized. This means inconsistency... Additionally, LLMs are great at inferring and data capturing/gathering/organizing but they are NOT good at autonomous decision looping. So, for that reason I do not have any LLM feature."

Now, the wink first: he posted this right after shipping a feature called **Flash Agentic**. Even the guy who bans LLMs needed the word "Agentic" on the box. I'm not dunking on him, I'm pointing out that the marketing gravity is so strong it bends the light around a no-AI shop.

Because here's what he actually said, once you strip the all-caps: don't let a non-deterministic thing pull the trigger on a decision loop. Non-deterministic just means you can ask it the same question twice and get two different answers. That claim is narrower than "AI is bad," and it's correct.

It's also the exact rule my own stack runs on. He and I agree completely on which part is dangerous. We just built the fence differently. He banned the tablet. I handed it over with rules.

Three rules, specifically. Then one story about the day the fence broke, because that's the part that keeps me honest.

## Rule 1: authority is inverted

In my trading system (I code-name it Vesper, and Claude is the AI wired into it), a deterministic Python risk engine sizes every trade. Deterministic meaning: same inputs, same answer, every single time. Boring math, no vibes.

The AI sits below that engine, not above it. **Claude can narrate a decision, reject it, or shrink it. It can never originate a position or increase its size.** The creative, chatty, occasionally-wrong thing has exactly one direction of authority: down.

This wasn't an accident, it's written into the project's own roadmap as a standing rule. When we surveyed the open-source trading-agent landscape, two real projects got named and explicitly rejected. Straight from the doc: "AutoHedge's 'Director Agent' lets an LLM generate the strategy itself rather than narrate a deterministically-computed one, and FinceptTerminal's 'AI Quant Lab' pushes ML/RL strategy discovery. Both are the opposite of this codebase's standing rule that an LLM may narrate, reject, or shrink, never originate a position or increase size."

An LLM directing strategy is a toddler steering the car because he watched a lot of Blippi episodes about trucks. Confident. Enthusiastic. No.

## Rule 2: the fence lives in the pipe, not the model

Here's where most "AI safety" in trading products goes wrong: they put the rule in the prompt. "You are a helpful assistant, please do not YOLO the account." A prompt is a suggestion. My fence is plumbing.

The stack runs two separate servers. One holds zero broker credentials by design, built for research and screeners, so nothing running there can ever place an order no matter what it's asked to do. The other one is the only place an order path exists at all, and it's gated behind its own OAuth "trade" scope, a separate key from read-only access.

On that server, every order moves through a cryptographic ticket handshake. Staging an order computes a SHA-256 hash, a one-way fingerprint, of the exact payload, and issues a single-use ticket good for **120 seconds**. Firing the order re-hashes whatever it's handed and refuses unless it matches byte-for-byte. The code's own docstring says it plainly: **"what got approved is byte-for-byte what gets sent."**

The dollar cap fails closed. Any one order is capped at the smaller of **$1,000** flat or **25% of the account's actual net liquidation value** (net liq is just what the account is really worth right now, everything marked to market). And if the system can't read the account's current value? The cap becomes **$0**. Refuse everything. The code's own reasoning: **"a cap computed from an unknown book is not a cap."**

And the master kill switch defaults OFF. A human has to deliberately turn trading on. Doing nothing is the safe state. These are the low monkey bars. The kid can swing all day.

## The day the fence broke

Now the part I'd rather skip, which is exactly why it stays in.

One specific commit, a migration landed on August 28, 2026, deleted the notional cap, the ticket handshake, and the kill switch. All three, at once, silently. Nobody did it on purpose, a migration just didn't carry the safety code forward. The very next commit, **49 minutes later**, put all three back with tests attached.

Here's the part that actually matters more than the scary part: this system has never taken a real trade in its life. It's still 100% paper money, today, as I write this. So that 49-minute window cost nothing, but that's timing, not virtue. The system working is that the gap got caught and closed in under an hour, not that it never opens.

So no, I'm not telling you my fence never fails. It failed once, quietly, and the honest lesson isn't "I built it right." It's that fences are things you check, not things you trust. Get confirmation. Same rule as the tablet.

## Rule 3: read the rules to the machine, out loud

The trading server doesn't hide its rules in some app's system prompt where nobody can audit them. It hands any connecting AI client, Claude included, a literal rules document as part of the protocol itself. The fence text ships with the fence.

That document says, verbatim: **"Voice may do anything that cannot increase exposure... Approve and resume are strictly forbidden from the voice interface... If a setup triggers, inform the operator: 'Press it yourself, I cannot approve this.'"**

I love that line. The AI's job at the moment of truth is to tell me to press the button myself.

My favorite detail in the whole document is the humble one: it warns that voice models mishear tickers. Its own example is hearing "NVDA" as "in video." So the AI is required to echo back the resolved ticker and quantity out loud before doing anything, and to refuse to guess on anything ambiguous. That's not paranoia about superintelligence. That's paranoia about a bad microphone, which is the kind of paranoia that actually saves accounts.

## Sometimes the correct fence is no AI at all

And sometimes I land exactly where Obsidian Edit does.

I'm about to launch Vespryx ([vespryx.com](https://vespryx.com), a Chrome extension) for TraderMatrix members. It draws live options-dealer positioning straight onto your chart: the support and resistance "walls" where dealers are heavy, the max-gamma pin the price gets dragged toward, the gamma flip where dealer behavior changes character. A rule-based verdict panel fires **UPSIDE SETUP / DOWNSIDE SETUP / NO SETUP** off three fixed, named conditions.

There is zero LLM anywhere in it. It's marketed as "not an adviser." Pure data visualization, same verdict on the same data every time.

Vesper's internal rules document has a line I think about constantly: **"Respect the tape over narrative."** The tape is the actual prices printing, and narrative is the story anyone, human or machine, tells about them. Vespryx is that principle shipped with no AI in the loop at all. Same instinct as Obsidian Edit. I just applied it where I decided the correct fence was "don't put the non-deterministic thing here at all" instead of "cage it."

## This was never AI vs. no AI

Everyone serious ends up building a fence. Obsidian Edit's fence is a ban. Mine is inverted authority, plumbing that gates the trigger, and rules read aloud to the machine. And on some decisions, mine is a ban too. The smart move is knowing which fence fits which decision, the way you know which monkey bars are low enough.

What's not legitimate is what most brokers bolting "AI" onto a brokerage account right now are actually doing: neither. No ban, no cage, just a chatbot with a marketing budget standing next to your money. When you evaluate any AI trading product, including mine, ask one question: where does the fence live? If the answer is "in the prompt," walk.

Vespryx goes live for TraderMatrix members soon. If you want to see what "respect the tape over narrative" looks like with the AI fenced all the way out of the loop, that's the one to watch.

~ Michael
