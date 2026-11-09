# Adversarial review: one-dispatcher post, about to publish

You are the reviewer for a piece that is about to go out publicly under Michael's name on his
Substack (Momentum Phinance, mphinance.substack.com). Your job is to ATTACK it, not to approve
it. Find what will backfire.

## Hard rules for you
- **Read only. Do not edit, write, or create any file. Do not touch the Substack draft.**
- Return your findings as your final message, nothing else.

## What to read (all in ~/mphinance)
- `VOICE.md`, especially **"What This Voice NEVER Does"** and the humanizer-sourced tells at the
  bottom of that section (not-X-but-Y, forced triads, inflated significance, borrowed authority,
  decorative bolding).
- `SUBSTACK.md` for the formatting rules (no em/en dashes, category-mix subtitle, no footer
  blocks, colored skimmer lines, the sign-off).
- `articles/get-more-done-with-ai/_live_draft.md`: **this is the real current text on Substack**,
  including the edits Michael just made by hand. Review THIS, not the file version.
- `articles/get-more-done-with-ai/post.md`: the repo version, for comparison. Note where the two
  now disagree; Michael's hand edits win, but the disagreement itself matters.

## Specific things to check

1. **Did the hand edits break the spine of the argument?** He cut the three verbatim prompt lines
   and replaced that block with a one-line pointer plus a screenshot, and he cut the closing
   "Five windows felt like speed. It was noise with a progress bar." Say plainly whether the
   piece still delivers the promise its title makes ("I talk to one dispatcher instead"), or
   whether the middle is now a pointer with no payload.
2. **The orphaned list.** One line reading "Two of them fixed my actual pain:" was deleted, but
   the two paragraphs it introduced are still there. Does the section still read, or does it now
   float?
3. **Typos and mechanical errors, exact strings.** There is at least a "hree" that should be
   "three", a double space after a word, and a ".." that should be an ellipsis or a comma. Find
   every one you can and give the exact string and the fix.
4. **Dashes.** Any em or en dash anywhere is a hard ban. A spaced hyphen used as a dash counts.
5. **Factual claims, verified with tools, not assumed.** Confirm or refute each of these against
   the actual sources; run the commands:
   - that the gist URL in the post resolves (curl -sI)
   - that `github.com/mphinance/alpha-skills` exists and that "136 of these in the open" is a
     defensible number (`gh api repos/mphinance/alpha-skills/git/trees/HEAD?recursive=1` and count)
   - that the two smoke-test figures $0.37 and $0.53 appear consistently and are not contradicted
     anywhere in the draft
   - that the TraderMatrix links are the referral form he uses elsewhere
   Report any claim that is overstated or unverifiable.
6. **Colored skimmer lines.** The house rule is one colored bold line per section. Two were
   deleted in his edit. Say which sections now have none and whether that matters on the page.
7. **Voice.** Riff on the specific lines that work and the specific ones that read as AI or as
   filler. Include "ooh, another butterfly!" and "the master of my own…something" in your
   assessment; he wrote those, so judge whether they land or undercut the point, and say which.

## Deliverable, in this order
1. **Ship or hold**, one line, with the single reason.
2. **Concrete edits in priority order.** For each: the exact quoted text, the exact replacement,
   and one clause on why. Only edits you would actually make.
3. **What you would NOT change and why** (he wrote it, do not sand off his voice without a reason).
4. **What you could not verify.**
