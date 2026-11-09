# Editor brief: articles/get-more-done-with-ai/post.md

You are the editor. One file, one job: make this draft read like Michael, then prove it.

## Read first (in ~/mphinance)
- `VOICE.md`, especially the **"What This Voice NEVER Does"** list and the humanizer-sourced
  patterns at the bottom of that section (not-X-but-Y, forced triads, inflated significance,
  borrowed authority, decorative bolding).
- `SUBSTACK.md` in full (hard rules, formatting, structure, the self-edit pass).
- The target file: `articles/get-more-done-with-ai/post.md`.

## What this file is
A Substack post: "Your AI Skills Are Weak. I Talk to One Dispatcher Instead."
Subtitle `*AI 70% | Business 30%*`. It argues for one orchestrator ("one front door") that
writes briefs for headless Claude Code workers versus running five coding windows by hand.

## DO
1. Run the SUBSTACK.md self-edit pass: mark every line that trips a voice tell, then rewrite
   only those lines. Do not restructure lines that did not trip anything.
2. Tighten. Short paragraphs, about 3 sentences max. Lead with the strongest line.
3. Preserve every fact exactly: $0.37 and $0.53 (the two smoke tests), ~30 line prompt,
   136 skills in the open, hard $5 budget, three workers at once, the gist URL, and the
   two TraderMatrix links before the paywall. Do not invent a number, a date or a quote.
4. Keep these markers exactly: the H1, the italic subtitle line, the hero image line,
   `<!--subscribe-->`, the section headings, `<!--share-->`, and the sign-off `~ Michael`
   on its own line as the last paragraph.
5. **NO FOOTER BLOCKS.** Hard rule, he has flagged this repeatedly. Do not add or keep a
   `> **TLDR: ...**` blockquote, a recap or summary paragraph, a "the honest numbers" style
   round-up, or any closing back-matter. The post opens with the hero, then the first line of
   the story. Delete any of these you find, except a section that carries facts found nowhere
   else (if you cut a number's only home, keep that section and say so in your report).
5. The banned openers stay banned: no "Here's the truth", no "Real talk", no "Everyone gets
   this wrong", no "Let me be honest". PG-13 profanity is fine and welcome.

## DON'T
- No em dashes or en dashes anywhere. Ever.
- Do not touch any image file, do not rename anything, do not commit or push.
- Do not change the gist URL or the TraderMatrix links.
- Do not add a byline, tags line, content warning, author's note or disclaimer.

## VERIFY (must run before you report)
```
python3 tools/voice_lint.py articles/get-more-done-with-ai/post.md
```
Zero ERRORs required. Report every WARN that remains and say why it is acceptable or fix it.

## REPORT
- Exact file path written.
- The voice_lint command and its real output (error and warning counts).
- What you changed, grouped by tell, with the before/after for the sharpest three.
- What you deliberately left alone and why.
- Anything you could not verify.
