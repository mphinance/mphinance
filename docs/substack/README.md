# Substack Drafts — Momentum Phinance

**Latest draft:** [`latest.md`](latest.md)

## All Posts (newest first)

| Date | File | Title |
|------|------|-------|
| 2026-04-25 | [quant-upgrade-post](musings/2026-04-25_quant-upgrade-post.md) | I Rebuilt Every Screener From Scratch. Here's What Changed. |
| 2026-04-24 | [the-wins-post](musings/2026-04-24_the-wins-post.md) | The Receipts |
| 2026-04-23 | [hypernet-constellation](musings/2026-04-23_hypernet-constellation.md) | HyperNet Constellation |
| 2026-04-22 | [value-averaging-car-fund](musings/2026-04-22_value-averaging-car-fund.md) | Value Averaging Car Fund |
| 2026-04-21 | [road-to-2k-wheel](musings/2026-04-21_road-to-2k-wheel.md) | Road to 2K Wheel |
| 2026-04-18 | [the-lodgepole-pine](musings/2026-04-18_the-lodgepole-pine.md) | The Lodgepole Pine |
| 2026-04-18 | [35-stock-portfolio](musings/2026-04-18_35-stock-portfolio.md) | 35 Stock Portfolio |
| 2026-04-15 | [emergency-fund-dividend-machine](musings/2026-04-15_emergency-fund-dividend-machine.md) | Emergency Fund Dividend Machine |
| 2026-04-14 | [usai-tax-day-gas-hedge](musings/2026-04-14_usai-tax-day-gas-hedge.md) | USAI Tax Day Gas Hedge |
| 2026-04-13 | [traderdaddy-bot-launch](musings/2026-04-13_traderdaddy-bot-launch.md) | TraderDaddy Bot Launch |
| 2026-03-07 | [sobriety-money-character](musings/2026-03-07_sobriety-money-character.md) | Sobriety, Money, and Character |

## Convention

- All drafts go in `musings/` as `YYYY-MM-DD_slug.md`
- Images go next to the post in `musings/` or in `musings/assets/`
- `latest.md` in this directory is always a copy of the most recent draft
- `latest_hero.png` is the hero image for the latest draft
- Every draft opens with the hero image, then a bold **TLDR:** paragraph in
  Michael's voice (concrete numbers, no keyword stuffing, ties back to the
  post's actual hook) before the body prose starts.

## Hero images (mascot pipeline)

The hero image is generated, not hand-prompted. There is a fixed mascot —
Michael's own likeness, illustrated in the same flat navy/cyan style every
time — with a small library of costume/pose variants in
`docs/substack/assets/mascot/` (`mascot_<pose>.png`, all 1024x1024, all
carrying the same "PHINANCE" branding and a blank chalkboard prop). Pick
whichever pose fits the post's actual subject:

| Pose | Vibe |
|---|---|
| `calm_edge` | confident, in control |
| `stressed_ego` | overwhelmed, chasing noise |
| `casino_dealer` | "become the casino" premium-selling posts |
| `surfer` | riding a trend / recovery-metaphor posts |
| `ap_clerk` | old-job/origin-story posts |
| `data_detective` | data-mining / forensic posts (autopsy, DM logs) |
| `midnight_builder` | pipeline/build/overnight-shipping posts |
| `aisle_auditor` | everyday-life-as-alt-data posts |
| `circle_chair` | recovery/sobriety posts (sincere, not comedic) |
| `professor` | explainer/teaching posts |

Every pose except `professor` carries the same small companion creature: a
snow-white arctic wolf pup with glowing cyan data-vein markings, named
after Michael's actual trading agent **Alpha** (alpha wolf, arctic being
his favorite animal family). `professor` swaps it for a small snowy owl
wearing matching glasses, since the professor/owl pairing was too good to
pass up. Never a ghost, on Michael's explicit ban.

To build a hero image for a draft:

```sh
python3 scripts/generate_hero.py --list-poses
python3 scripts/generate_hero.py \
    --pose midnight_builder \
    --chalk "Boolean filters -> EdgeScore" \
    --out docs/substack/musings/YYYY-MM-DD_hero.png
```

`--chalk` is real HTML text rendered with headless Chromium and composited
onto the pose's blank chalkboard region, not text the image model draws
itself, because it reliably garbles anything longer than a word or two.
Keep it short: a before/after, a formula, a one-line stat specific to that
post. Also copy the result over `latest_hero.png` to keep it in sync.

New poses go through `~/projects/openrouter` (OpenRouter image-generation
models, e.g. `google/gemini-3-pro-image`) using one of the existing poses
as the likeness reference so the face/hair/stubble stay consistent, then
need their chalkboard rectangle measured and added to `DEFAULT_COORDS` in
`scripts/generate_hero.py`.

## Formatting Rules

- **No markdown tables** in post content (Substack can't render them)
- **No em dashes** (—) ever
- See `VOICE.md` in repo root for full style guide
