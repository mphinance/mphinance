---
name: linktree-hub
description: >-
  Build a custom link-in-bio page (a nicer, self-owned alternative to Linktree)
  for a friend/creator and ship it on GitHub Pages. Scrapes their existing
  linktr.ee to pull identity, bio, profile image, links, socials and theme
  color, then generates a single static index.html in a distinctive on-brand
  aesthetic, wires a QR code back to the live URL, creates the repo, pushes,
  and enables Pages.
  Use when Michael says "give them a better linktree", "make a link hub",
  "build a linktree page", "help out my friend's links", "clone the ballout
  thing for X", or hands over a linktr.ee URL and asks to prettify it.
trigger_phrases:
  - better linktree
  - link hub
  - link-in-bio
  - build a linktree
  - prettify their linktree
  - clone the ballout thing
  - help out my friend's links
---

# linktree-hub

Michael does free "here's a nicer Linktree" builds for trader friends. It's a
proof-of-work / goodwill engine (same spirit as the Automation Architect side
business). Each one is a single static `index.html` on GitHub Pages, themed to
the person, with a live QR code back to the page. This skill reproduces that
build end to end.

## Reference builds (steal from these)

- `mphinance/balloutt-trades-links` — the original. Violet + ember, his own
  background photo. Deep-teal/emerald + gold variant lives at
  `mphinance/onetradewex-links`.
- Clone one locally to reuse the template shell:
  `gh repo clone mphinance/onetradewex-links /tmp/ref`

The HTML shell is the same every time. **Only these change per person:** the
CSS `:root` palette, identity block (name/tagline/handle/bio), the link cards,
the socials, the QR target, and the disclosure/footer name.

## Step 1 — Scrape their linktr.ee

WebFetch is blocked by Linktree (403). Use the bundled scraper, which pulls the
`__NEXT_DATA__` JSON:

```bash
python scripts/scrape_linktree.py https://linktr.ee/THEIRHANDLE
```

It prints: username, pageTitle, description (bio), profilePictureUrl,
`backgroundHeroColor` (great theme seed), theme luminance, every link
(type/title/url), and the social links. Copy the profile image URL and the
links out of that.

## Step 2 — Assemble assets

```bash
mkdir -p ~/THEIRHANDLE-links/assets
curl -sL "<profilePictureUrl>" -o ~/THEIRHANDLE-links/assets/profile.jpg
# QR points at the FUTURE pages URL (know the repo name first):
python3 -c "import qrcode; from qrcode.constants import ERROR_CORRECT_H; \
qr=qrcode.QRCode(error_correction=ERROR_CORRECT_H,box_size=12,border=2); \
qr.add_data('https://mphinance.github.io/THEIRHANDLE-links/'); qr.make(fit=True); \
qr.make_image(fill_color='#07251f',back_color='white').save('$HOME/THEIRHANDLE-links/assets/qr.png')"
```

No landscape photo? The template blurs `profile.jpg` as the background — fine.

## Step 3 — Build index.html

Copy the reference `index.html` and change ONLY:

1. **`:root` palette** — seed the primary from `backgroundHeroColor`. Pick a
   *different* palette than the last build so each friend's page is distinct
   (ballout = violet/ember, onetradewex = emerald/gold). Recolor: `--bg`,
   `--deep`, `--emerald`/primary, `--emerald-bright`, `--gold`/accent, and the
   matching `rgba(...)` values throughout (favicon SVG too).
2. **Identity block** — `.name` (split a word into `<em>` for the italic
   accent), `.llc` tagline, `.handle`, `.bio`. Verbatim bio from the scrape.
3. **Link cards** — one `<a class="link">` per real link. First/best one gets
   `class="link feat"` + a `Featured` tag. Keep TraderDaddy links with their
   `?ref=` code intact. Group under `.rule` section headers.
4. **Socials** — one `.soc` per platform (TikTok/IG/YouTube/X/Discord SVGs are
   all in the reference).
5. **Footer + disclosure** — swap the name. Keep the risk-disclosure block.

Do NOT touch the animation/layout CSS or the ticker-tape script — they're
person-agnostic.

## Step 4 — Ship

```bash
cd ~/THEIRHANDLE-links && touch .nojekyll
git init -q && git add -A && git commit -q -m "THEIRHANDLE link hub"
gh repo create mphinance/THEIRHANDLE-links --public --source=. --push \
  --description "Custom link-in-bio hub for THEIRHANDLE — a nicer alternative to Linktree."
gh api -X POST repos/mphinance/THEIRHANDLE-links/pages \
  -f "source[branch]=main" -f "source[path]=/"
```

Poll `curl -s -o /dev/null -w "%{http_code}" https://mphinance.github.io/THEIRHANDLE-links/`
until 200 (first build takes a minute). Hand Michael the live URL + the repo
so he can pass it to his friend.

## Notes

- Keep the risk-disclosure block on every trader page. Affiliate links get the
  "may earn a commission" line.
- The QR must point at the final Pages URL, so decide the repo name before
  generating it.
- These are gifts for real people — get the name/handle/links exactly right;
  don't invent links that weren't on their linktree.
