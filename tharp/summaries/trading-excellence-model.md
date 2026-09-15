# Trading Excellence Model — Summary

Source: `Trading-Excellence-Model.pdf` (18 pages, Van Tharp Institute lead-magnet e-book). Fully read, not OCR'd — this one has a real text layer.

## The 5 pillars

Tharp's holistic framework, circular/iterative (traders enter at different points, revisit each area repeatedly):

1. **Peak Performance Mindset** — trading is an inner game first. Managing emotional state, self-sabotage, bias vs. logic. Practical check before any trade: "What emotional state am I in right now? Am I following my plan or reacting to fear/boredom/excitement?"
2. **Position Sizing** — "the often-ignored key to trading success." His own words: *"You can trade a mediocre system with good position sizing and make money, but you can trade a great system with poor position sizing and go broke."* The worked example here is the plain-language ancestor of everything in the Definitive Guide: Trader A risks 2% per trade with a plan; Trader B risks 10% on one trade, 1% on another, by "gut feel." Same signals, A compounds steadily, B wipes out. **The one-line quick-win test**: before any trade, ask "if this is a total loss, how much of my account do I lose? If more than 1–2%, you're overexposed."
3. **Trading Process Architecture** — systems must fit *you*, your objectives, and the market — not be borrowed wholesale. "A system that doesn't fit you will almost always fail you." Practical check: "Do I have a written plan for this trade? Does it fit my system rules, or am I improvising?" If you don't have a written system, "you're not trading, you're gambling."
4. **Trading Mastery** — specialization + deliberate practice over hundreds of trades, not system-hopping. Check: could you teach someone else to trade your system exactly as you do? If not, you don't have mastery yet, you have habits.
5. **Transformational Growth** — the markets as a mirror for personal psychology; the "outer game" (trading) can't outrun the "inner game" (self-work) forever.

## Why this matters for an autonomous trading agent

Position Sizing (pillar 2) is the one with hard math behind it — that's what the Definitive Guide is for (see `definitive-guide-position-sizing.md`). The other four pillars are mostly about a human trader's psychology, which doesn't transfer directly to an autonomous agent — but two things do translate:
- **Pillar 3's "written plan" discipline** maps directly onto requiring every trade proposal to carry an explicit invalidation condition before entry (the "Drawing the Line" idea from the Substack piece) — an agent that has to write its exit condition before the trade fires is the automatable version of "don't improvise."
- **Pillar 2's 1–2% quick-win check** is a trivial, cheap guardrail to hardcode: reject/flag any proposal whose stated risk exceeds a fixed % of current NetLiq, independent of whatever position-sizing model generated it.
