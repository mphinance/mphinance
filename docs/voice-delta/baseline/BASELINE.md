# Voice baseline: pre-AI Michael

Source: `data/afterhour/mphinance.json` (1,172 AfterHour posts, Dec 2024 → Aug 2026).
Control window: **2024-12-19 → 2025-03-29, 109 posts, 14,637 words**. Corpus in `control_corpus.md`.

`check.py <draft.md>` scores a finished draft against this corpus. Read-only diagnostic, run it
before publishing. It does not touch predict.py, which grades VOICE-DELTA.md against shipped
Substack posts and must keep those as its target.

## Why this window

Em/en dash count per month, his own unedited posts:

```
2024-12 → 2025-03    0
2025-04              6
2025-07             24
2025-08             42
2026-01             25
2026-05              0   (no-em-dash rule enforced)
```

Four months of literal zero, then a step change. The dash arrival dates the moment LLM
assistance entered the writing. Everything before it is uncontaminated. VOICE.md and
voice-delta are both calibrated on *shipped Substack posts*, which all postdate this line,
so they are partly learning to imitate an already-influenced voice. This window is the control.

## Rate comparison (per 10k words, control vs Oct 2025–Aug 2026)

| tic | control | recent |
|---|---|---|
| "but I digress" | 4.1 | 0.2 |
| `-MPH` / `~MPH` signoff | 9.6 | 0.2 |
| "Edit:" correction at top of post | 4.1 | 0.3 |
| eggplant 🍆 | 2.0 | 0.0 |
| ffs | 1.4 | 0.0 |
| lol | 3.4 | 1.4 |
| @-mention of another poster | 42.4 | 25.9 |
| wheel / CSP / covered call / premium | 39.6 | 29.0 |
| "do your own DD" / not-advice hedge | 1.4 | 0.3 |
| profanity (fuck/shit) | 11.6 | 10.5 |
| `*italic*` mid-sentence emphasis | 26.0 | 30.1 |

Profanity and italic emphasis survived intact. The casual tics, the credit-giving, and the
wheeling identity all thinned out.

## What the baseline has that VOICE.md misses

**1. The signature lineage is `~MPH` → `~ Michael`.**
`-MPH` (2024-12-30), then `~MPH` (2025-01-24 onward). He was posting pseudonymously; the name
came later. So `~ Michael` is the *successor* to `~MPH`, not a separate Substack convention, and
the tilde is the through-line across both. `~ Michael` still appears zero times in 199k words of
AfterHour, so don't staple it onto an AH post, but the habit is one continuous thing.

**2. "but I digress" is a real signature tic.** Four times per 10k words in the control window,
essentially gone now. It's how he exits a tangent he enjoyed taking.

**3. He sources theses from his physical life, not from screens.**
The strongest and most-repeated move in the corpus, and VOICE.md doesn't name it:

- Counts shoe brands at his kid's basketball game to size up UAA vs NKE, coaches and parents
  in the stands included, then sells 4 CSPs on it.
- Egg prices at the store → digs up CALM.
- Crocs on every kid through a Wisconsin winter, and the position is still red, "I can't figure
  out why."
- Halloween in his neighborhood is candy for kids and shots for parents → HSY / BF.B.

Not "here's a screener hit." He notices something in the world and then goes to the numbers.
"News follows price" is documented; *my own life is the alt-data* is not, and it's the more
distinctive habit.

**4. He hedges his standing constantly, never his read.**
VOICE.md says "Never hedges." That is wrong at the person level. The control corpus is full of
"I'm not showing this to brag," "I'm not trying to tell anyone what to do and I'm not sure if
I'm even trying to give advice," "I only did about 45 seconds of DD on each so far, so please
do your own." He is blunt about the market and humble about himself. Those are separate axes,
and current output flattens them into one confident broadcast voice.

**5. He asks and expects answers.**
"Curious what others would have done." "Am I not popular enough? Lol." "Anyone have reason to
think UBER has *any* chance of breaking 70?" "Or maybe a TA person can double check me... I do
numbers." Question marks are equally frequent now, but they're rhetorical now and genuine then.

**6. He shows the arithmetic inline.**
`((932-800)/800)x100 = 16.5%`. He literally writes the formula in the post. The accountant
showing his work, not a rounded takeaway.

**7. He tagged people twice as often — and that was strategy, not voice.**
@squeezekid, @tronathan, @SIRJACK, at 42 per 10k words vs 26 now. Michael's own read: he needed
the popularity then. So the decline is not voice decay and should NOT be "restored." VOICE.md's
existing framing of cross-community linking as reciprocal-restack farming is accurate; the
baseline confirms the motive rather than contradicting it. Nothing to change here.

**8. He publishes, then corrects in public.**
"Edit - really am wondering what others would have done here." "Edit: *selling* options, not
buying." "*deleted original post and reposting, accidentally left part of account number."
Correction at the top, mistake left visible.

**9. The core identity is wheeler, not momentum trader.**
"I've made it no secret that I'm a wheeler." "Become the casino and get rich slowly." "When I
hear people say 'this stock has cheap options,' what I hear is 'someone's getting paid a ton of
pennies from all of us.'" His profile quote is the impatient-to-patient line. The 2025-01-25
post is the whole thesis: he watched someone buy top-tick RXRX calls, realized he's the one
taking that money, and wrote a post teaching them to sell instead. Selling premium to the
impatient is the belief. Screeners and momentum came later.

**10. Profanity is platform-calibrated, not a fixed ceiling.**
"I fucking love the conviction." "back that shit up with your pocket." "ffs." "bitches." The
rate is flat across the whole AH corpus (11.6 vs 10.5 per 10k). But this is an AfterHour ceiling,
not a universal one: AH isn't SEO'd and Substack is, so the PG-13 cap in VOICE.md is a correct
Substack constraint, not an error. The rule to record is that the ceiling moves by platform.

**11. Registers VOICE.md has no name for.**
The 2025-02-23 opener is four parallel rhetorical questions (round-trip flights, road trip
without going pee, blind date with an emergency call, scuba without checking oxygen) then the
turn: "I've said yes to all of these, and I too, have entered trades without an exit strategy."
That ladder structure is native and effective. The 1k-follower post is pure Anchorman riffing.
Neither is "irreverent educator"; both are him.

## Structural stats

- Median sentence: 14 words.
- Median post: 93 words. Longest control post: 611.
- Posts open with context or disclaimer more often than with a hook. The "bold opener" rule in
  VOICE.md is a Substack-era import, not a native habit.

## VOICE.md amendments — applied 2026-08-02

1. "but I digress" added to Vocabulary & Tics.
2. Hedging rule split: blunt on the read, humble on the standing.
3. New "Life as Alt-Data" section.
4. `~MPH` → `~ Michael` lineage noted at the signature rule.
5. Profanity documented as platform-calibrated (AH high, Substack SEO-capped).
6. Rhetorical-question-ladder added as a named opener structure.
7. Wheeling / premium-selling restored as the stated core belief.

Rejected after Michael's review:
- *Reframe cross-community links as gratitude.* Wrong. Early tagging was audience-building
  because he needed followers. Existing restack-farming framing stands.
- *Raise the Substack profanity ceiling.* Wrong. The AH ceiling is high because AH isn't
  SEO-indexed. Substack stays PG-13.
