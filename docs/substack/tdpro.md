# TraderDaddy Pro — Design System

A design system for **TraderDaddy Pro** (`traderdaddy.pro`), a professional options-trading platform that surfaces unusual options activity, institutional flow, and AI-driven trade analysis in real time. The look is **a deep-navy options terminal** — Bloomberg-meets-prop-shop, lit by an electric-blue dot grid, with amber CTAs and signature green/red bull/bear semantics.

> Source: the entire system is reverse-engineered from the production Next.js frontend (Next 15 + Tailwind v4 + Frosted UI + Radix Themes + Lucide). No Figma was provided. Codebase mount: frontend/ (TraderDaddy frontend monorepo — read-only via the chat's local-mount).

---

## Index

| File | What it is |
| --- | --- |
| `README.md` | This file — brand context, content + visual + iconography rules. |
| `colors_and_type.css` | All design tokens (CSS variables) + semantic type classes. |
| `SKILL.md` | Cross-compatible Agent Skill manifest. |
| `assets/` | Logos, favicons, OG image, TraderLady avatar. |
| `preview/*.html` | Self-contained preview cards — populates the Design System tab. |
| `ui_kits/web-app/` | High-fidelity recreation of the web app (Header, Hero, StatsStrip, Flow Table, Filter Bar, AI chat, etc). |

There is **one product** in scope: the TraderDaddy Pro web app at `https://www.traderdaddy.pro` (single Next.js codebase serves both the marketing hero and the authenticated dashboards). There is also a separate TD Indicator site (`traderdaddyindicator.com`) referenced from the footer — not in this kit.

---

## Product context

TraderDaddy Pro is a **subscription-gated trading-intel platform** for retail options traders who want to "trade like an institution." Headline jobs-to-be-done:

- **Unusual Options Activity (UOA):** detect SWEEPS, BLOCKS, and GOLDEN SWEEPS the moment they hit the tape, with a proprietary conviction score (0–130+).
- **Smart-money intel:** congressional trades, insider activity, futures GEX, hedge-fund 13F-style ETF tracking.
- **Screeners:** Daily Cuts, Gamma Scan, Momentum Pullback, CSP Wheel, LEAPS, Earnings Gap, Reversal Finder.
- **AI coach (TraderLady):** an in-app chat persona that translates flow into plain-English actions.
- **Calendars:** earnings, macro/economic, politician + insider activity.

**Tiers:** `free` → `beginner` → `premium`. Free users see redacted/locked rows with an "Upgrade to Pro" gate. Premium adds an amber crown 👑.

**Brand voice in one line:** *"See What Institutions Trade. Before It Moves the Market."*

---

## CONTENT FUNDAMENTALS

How TraderDaddy writes copy — match this voice everywhere.

### Tone

- **Confident, slightly cocky, never apologetic.** "No noise. Just edge."
- **Insider lingo, not jargon.** The reader is assumed to know what a sweep, block, DTE, IV, GEX, P/C ratio, and LEAPS are — the product *interprets* these signals, it doesn't define them.
- **Money-first urgency.** Every page leads with a live indicator (pulsing dot, "LIVE · Institutional Flow Detection") and a dollar number.
- **Hype controlled by data.** The brand is hypey — *"see what institutions trade"*, *"before it moves the market"*, *"institutional alpha"* — but the numbers next to it are precise: `$2,341,000`, `Score 127`, `0–7 DTE`.

### Casing

- **Headlines:** Title Case with a serif twist (Playfair Display). *e.g. `Unusual Options Activity`, `See What Institutions Trade.`*
- **Section eyebrows / labels:** UPPERCASE with a `0.08em` letter-spacing. *e.g. `LIVE · INSTITUTIONAL FLOW DETECTION`, `SPY PUT/CALL RATIO`.*
- **Tier badges / flow type:** ALL CAPS, bold mono. *e.g. `EXTREME`, `INSTITUTIONAL`, `HIGH CONVICTION`, `GOLDEN SWEEP`, `SWEEP`, `BLOCK`, `SPLIT`.*
- **Buttons:** Sentence case for normal CTAs (`Start Free Trial`, `View Pricing →`), but the crown-pill upgrade is short and bold (`Pro`, `Upgrade to Premium`).
- **Microcopy:** lowercase with em-dashes is common in helper text (*"sweeps, blocks, and golden sweeps — detected as they hit the tape."*).

### Pronouns

- **"You" addresses the trader.** *"Your AI trading coach…"*, *"You always know what to do next."*
- **"We" is rare** — TraderDaddy speaks *from the desk*, not from a marketing team. When the product needs an author it's **"TraderLady"** (the AI), not "we."

### Punctuation & quirks

- **Em-dashes for cadence**: *"No noise. — Just edge."*, *"sweeps, blocks, and golden sweeps — detected as they hit the tape."*
- **Middle dots `·`** separate live indicators from labels: *`Live · Institutional Flow Detection`*, *`LIVE · CLOSED`*, *`Trusted by 100+ traders · Live data, updated every minute`*.
- **The arrow `→`** ends secondary CTAs (`View Pricing →`).
- **Inline strikethrough / lock icons** for premium-gated rows (`🔒`, `Unlock with Premium`).

### Emoji & symbols

- **Emoji are used sparingly and only as inline data glyphs**, never decoratively. Specifically:
  - `🟢` / `🔴` for breadth chips (`5/11 flow 🟢`, `3/11 price 🔴`).
  - `🔥` for "leading sector" callouts (`🔥 XLK +1.2%`).
- **Crown `👑` (or Lucide `Crown` icon)** signals premium tier.
- **No smileys, no marketing emoji, no faces.** The brand reads professional.

### Examples (lift these patterns)

- Hero headline: `See What Institutions Trade.` → *(linebreak)* → `Before It Moves the Market.` (amber→blue gradient on second line).
- Trust line: `● Trusted by 100+ traders · Live data, updated every minute`
- Page eyebrow: `● LIVE · INSTITUTIONAL FLOW DETECTION`
- Empty state: *"No unusual activity detected yet. Try adjusting your filters or check back later."*
- Error: *"Failed to load unusual activity data. Please ensure the backend is running."*
- Premium gate: *"Upgrade to Pro to unlock 47 more flows."*

---

## VISUAL FOUNDATIONS

### Color system

A **dark-navy canvas** with **one warm CTA accent (amber)**, **one cool brand accent (blue)**, and **strict bull/bear semantics (green/red)**. Purple is reserved for premium/tier and divergent flow.

- **Base:** `#0a0e1a` solid + a navy gradient `#0a0e27 → #0d1230 → #0a0e27` at 160°, with a `28px` electric-blue dot grid (`rgba(59,130,246,0.08)`) and a top-center radial glow.
- **Primary brand:** `#3b82f6` blue, with `#60a5fa` for hover and `#93c5fd` as heading/link tint on dark.
- **CTA accent:** `#f59e0b` → `#d97706` amber gradient (`135deg`).
- **Bull/bear:** `#10b981` / `#ef4444` (always; never red/green-swap).
- **Premium / tier:** `#a855f7` purple.

All cards, borders, and overlays are **translucent blue rgba** — never a flat neutral grey. The "TD wash" is `rgba(59, 130, 246, 0.15)` for borders and `rgba(17, 22, 51, 0.6)` for surfaces.

> Light mode exists (white bg, `#0f172a` ink) but the brand is **dark-first**. The marketing screenshots, the logo, the OG image, and 100% of the screenshots-as-shipped use dark.

### Typography

Four faces, each with a fixed job:

| Family | Role | When |
| --- | --- | --- |
| **Playfair Display** (700) | Display serif | Hero headlines, marketing splash. |
| **Outfit** (300–700) | Body sans | All UI body, buttons, nav. |
| **Space Mono** (400/700) | Data mono | Numbers, tickers, $premium, P/C ratios, times. |
| **Space Grotesk** + **JetBrains Mono** | Alt body / alt mono | Newer redesigned sections (ticker-search). |
| *Cormorant Garamond* | Loaded but rarely used | Available as `--font-cormorant`. |

**Rules of thumb**

- **Any number ≥ 2 digits is mono.** Always.
- **Ticker symbols are mono, blue-300, bold.**
- **Eyebrows are `Outfit 700` uppercase `0.08em`.**
- **Headlines hop to Playfair** to break the otherwise sans-heavy UI.
- **The signature gradient** `linear-gradient(125deg, #f59e0b, #fbbf24, #60a5fa)` is applied via `-webkit-background-clip: text` for the second half of hero headlines.

### Spacing

Tailwind v4 defaults (4px base). The common rhythm:

- `0.25rem / 0.5rem / 0.75rem / 1rem / 1.5rem / 2rem`
- Card padding: `1.5rem` (`p-6`) is the canonical interior; `2rem` for large.
- Section gap on main layouts: `space-y-6` (1.5rem) between major blocks.
- Container: `max-w-7xl` (1280px) centered, with `px-4 sm:px-6 lg:px-0`.

### Backgrounds

- **Page:** dot grid + top radial glow + 160° navy gradient (see globals.css recipe in tokens file).
- **Cards:** **glass** — `rgba(17, 22, 51, 0.6)` fill, `rgba(59, 130, 246, 0.15)` border, `border-radius: 1rem`. No backdrop-filter (intentional — perf).
- **Ambient orbs:** two giant, fixed, pointer-events-none radial gradients (blue + violet) that drift on a 25–30s ease-in-out via the `floatOrb` keyframe. Always behind content (`z-index: 0`).
- **No photos, no full-bleed imagery, no illustrations.** The "imagery" is the data itself — charts, tables, badges.

### Borders

- **1px solid** is the rule, always with translucent blue `rgba(59, 130, 246, ALPHA)`.
- Border alpha scale: `0.15` (default) → `0.20` (button/input) → `0.30` (hover) → `0.40` (focus/active/heavy emphasis).
- **Bull/bear borders** swap the blue for emerald/red rgba at the same alpha stops.

### Shadows

- **Card:** `0 2px 8px rgba(0,0,0,0.10)`.
- **Elevated card:** `0 4px 12px rgba(0,0,0,0.15)`.
- **Hover lift on interactive cards:** `0 10px 25px -5px rgba(59,130,246,0.10)` + `translateY(-2px)`.
- **Tier glow (Extreme / Institutional):** `0 0 8px 2px rgba(239,68,68,0.30)` (red) or `0 0 8px 2px rgba(147,51,234,0.30)` (purple) — pulses via `tierGlowExtreme` / `tierGlowInstitutional` keyframes.
- **Gold CTA:** `0 4px 20px rgba(245,158,11,0.25)`.
- **Header:** `0 1px 0 rgba(255,255,255,0.02), 0 10px 30px -20px rgba(0,0,0,0.6)` (inner highlight + outer drop).

### Radii

| Token | Value | Used for |
| --- | --- | --- |
| `--td-radius-xs` | 0.25rem (4px) | Tier badges (`EXTREME`, `INSTITUTIONAL`). |
| `--td-radius-sm` | 0.375rem (6px) | Flow badges (`GOLDEN SWEEP`, `SWEEP`). |
| `--td-radius-md` | 0.5rem (8px) | Small chips, segmented buttons. |
| `--td-radius-lg` | 0.75rem (12px) | Buttons, inputs, icon containers, segmented controls. |
| `--td-radius-xl` | 1rem (16px) | **Cards (canonical).** |
| `--td-radius-2xl` | 1.5rem (24px) | Large cards, hero blocks. |
| `--td-radius-pill` | 9999px | Trust badges, status chips, live pills. |

### Animation & motion

- **Easing:** `ease-in-out` (long, ambient) or plain `ease` (UI feedback). No bouncy springs.
- **Hover lift:** `translateY(-1px)` for buttons, `-2px` for cards, `-4px` for feature cards. Duration `200ms`.
- **Hover brightness:** `filter: brightness(1.10)` for gradient buttons (cheap, GPU-only).
- **Live pulse dot:** opacity + scale on a 2s loop with a `0 0 0 4px` box-shadow ring that fades — see `dotPulse` keyframe.
- **Tier badge glow:** opacity-only pulse (`0.75 → 1`) — compositor-safe, zero repaint.
- **Golden sweep shimmer:** a 40%-wide light sheen translates `-100% → 250%` with a `-15deg` skew over the badge surface; 3s loop.
- **Ambient orbs:** `translateY(0 → 30px)` + opacity drift over 25s.
- **Fade-in-up entrance:** `opacity 0→1`, `translateY(10px → 0)`, 0.3s ease, backwards fill.
- **Row entrance:** slide from left 8px + fade, 0.35s.
- **Reduced-motion:** all animations collapse to static keyframes under `prefers-reduced-motion: reduce` (see globals.css).
- **No bounces. No flips. No "wow" splash entrances.** This is a terminal.

### Hover & press states

- **Buttons:** `filter: brightness(1.10)` + `translateY(-1px)`. Active resets `translateY(0)`.
- **Secondary buttons:** swap background to `rgba(59,130,246,0.10)` and border to `0.30`.
- **Cards (interactive):** `translateY(-2px)` + tightened blue glow + border bumped to `0.30`.
- **Nav links:** color shift `gray-400 → blue-300`; active gets a `2px` underline that's itself a gradient `linear-gradient(90deg, #3b82f6, #60a5fa, #fbbf24)`.
- **Inputs:** border `0.20 → 0.50` on hover, `0.60 + outline-offset 2px` on focus.
- **Premium button:** has a permanent diagonal shimmer (`shimmer` keyframe, 3s loop) sliding across.

### Layout rules

- **Sticky header** (`top: 0; z-index: 50`) with a `backdrop-filter: blur(20px)`, a navy gradient (`180deg, rgba(10,14,39,0.98) → rgba(13,18,48,0.95)`), and a 1px blue border-bottom. Contains a `MarketPulseBanner` strip *inside* the header.
- **Container:** `max-w-7xl mx-auto`; tables can break out to `100vw` on `lg+` (see `tableBreakout`).
- **Grid:** the homepage uses a `3fr 2fr` chart grid at `lg+`, single column below.
- **Footer:** `mt-auto`, dark with brand color-coded inline links (amber = Pricing, green = Affiliate, violet = TD Indicator, Discord-purple = Discord).

### Transparency & blur

- **Cards never use backdrop-filter** (perf decision — kept solid translucent navy). The "glass" effect comes from the navy gradient page bg showing through `rgba(17,22,51,0.6)`.
- **The sticky header is the one exception**: `backdrop-filter: blur(20px)` so scrolling content blurs cleanly beneath it.
- **Sticky table headers** add a `backdrop-filter: blur(8px)` for the same reason.

### Cards — the canonical pattern

```
border-radius: 1rem;
background: rgba(17, 22, 51, 0.6);
border: 1px solid rgba(59, 130, 246, 0.15);
padding: 1.5rem;        /* or 2rem for `glassCardLarge` */
```

**Headers** sit inside cards with a slightly darker fill (`rgba(10,14,39,0.8)`), `1.5rem 1rem` padding, and a bottom border at `0.20` alpha. **Footers** mirror the header at `0.40` alpha background and a top border at `0.15` alpha.

### What we DON'T do

- ❌ No drop-shadow on text. (Tier glow is `box-shadow` on the badge container.)
- ❌ No blurred gradient hero blobs (we use tight radial dots + ambient orbs instead).
- ❌ No glassmorphic backdrop-filter on cards.
- ❌ No marketing photography. No stock illustrations.
- ❌ No rounded-left-border-accent cards (the AI-slop trope).
- ❌ No emoji decoration. Emoji only for breadth chips and 🔥 leading-sector.

---

## ICONOGRAPHY

**Icon library:** [Lucide](https://lucide.dev) (`lucide-react` 0.544). Every icon in the product comes from this one source — load via CDN at:

```html
<script src="https://cdn.jsdelivr.net/npm/lucide@latest"></script>
<i data-lucide="trending-up"></i>
```

### Usage rules

- **Stroke weight:** the Lucide default (`1.5–2`). Never re-rendered or customized.
- **Sizes:** `w-3 h-3` (12px, inside chips), `w-4 h-4` (16px, default in nav, buttons, header), `w-5 h-5` (20px, large icon containers / mobile menu), `w-8 h-8` (32px, stat icon containers).
- **Color:** always inherited from the surrounding text color or set via `style.color` on the parent — never via Lucide's fill props.
- **Wrapping:** decorative icons sit inside an "icon container" — a `0.75rem`-radius box with a translucent-blue fill and a 1px translucent-blue border. See `colors_and_type.css` `--td-radius-lg`.

### Common icon → meaning map (lifted from `lib/navigation.ts` + components)

| Icon | Used for |
| --- | --- |
| `Activity` | Options Flow nav |
| `Search` | Ticker search |
| `TrendingUp` / `TrendingDown` | Flow Analysis, sentiment, bull/bear cards |
| `Filter` | Screeners dropdown, table filters |
| `Wrench` | Smart Tools dropdown |
| `Calendar` | Calendars dropdown |
| `Target` | Signal scanners |
| `Crown` | Premium tier badge, upgrade CTAs |
| `Zap` | Real-time / live features |
| `BrainCircuit` | TraderLady AI |
| `Landmark` | Smart-money / institutional |
| `LayoutDashboard` | All-in-one / overview |
| `Flame` | Empty state, hot signals |
| `RefreshCw` | Loading, refresh |
| `Lock` | Premium-gated content |
| `LogOut`, `Settings`, `User`, `ChevronDown`, `Menu`, `X` | Standard UI chrome |
| `Users` | Trust / social proof |
| `DollarSign` | Affiliate, premium |
| `BookOpen` | Help & Wiki |
| `BarChart2` | TD Indicator (external link) |

### Logos & brand marks

- **`assets/logo.png`** — the full TraderDaddy wordmark: a stylised blue beardy face wearing sunglasses with **amber bar-chart "lenses"**, sitting above the wordmark *"Trader**Daddy**™"* (lighter `Trader` + bold `Daddy`). Used at `h-14` to `h-20` in the header.
- **`assets/traderlady-avatar.png`** — the AI chat persona avatar.
- **`assets/favicon-32x32.png`, `apple-touch-icon.png`** — favicons.
- **`assets/og-image.png`** — 1200×630 OG share image.
- **`assets/android-chrome-512x512.png`** — PWA / app icon.

### Discord (and other brand) icon

Discord's mark is **inlined as an SVG path** (see `Header.tsx`, `Footer.tsx`) — not from Lucide, since Lucide doesn't ship brand icons. Color: `#5865F2` (Discord blurple) on the footer, `#7B89FF` on dark surfaces inside the user dropdown. **Lift verbatim** from `assets/discord-icon.svg` (registered below).

### Custom / unicode glyphs

- `↻` for the auto-refresh indicator (`↻ Auto-refresh: ON`).
- `·` (middle dot) as a separator (NOT a hyphen, NOT a bullet).
- `→` for forward links.
- `●` for live-pulse dots (always paired with a CSS `animation: dotPulse`).

**No icon font, no SVG sprite.** Lucide-react ships per-component on the web app; for static HTML mocks use the Lucide CDN above.

---

## Fonts

All fonts are Google Fonts (loaded via `next/font/google` in the codebase). Use the CDN imports below for static HTML:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&family=Space+Mono:wght@400;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
```

> **No font substitutions made.** All four faces are first-party Google Fonts and available everywhere via the same CDN.

---

## How to use this system

1. **Drop in tokens.** Include `colors_and_type.css` and load the Google Fonts stylesheet (above).
2. **Match the page chrome.** Apply the navy gradient + dot grid to `<html>` (snippet in `colors_and_type.css` comments).
3. **Reach for cards.** Default to the glass card (`--td-bg-surface` + `--td-blue-border` + `--td-radius-xl`).
4. **Numbers go mono.** Anything financial — `$2.4M`, `127`, `0–7 DTE`, `09:23:14 ET` — uses `--td-font-mono` and a brand color (`--td-fg-bright` or `--td-gold-500` for emphasis).
5. **Bull/bear are sacred.** `#10b981` = bullish/calls/up, `#ef4444` = bearish/puts/down. Never swap.
6. **Lift, don't reinvent.** The `ui_kits/web-app/` recreations are the pixel-honest reference for component anatomy — copy from there.

---

## Caveats & gaps

- **No Figma.** Tokens are reverse-engineered from the production codebase.
- **Light mode is real but underused** — the brand reads dark-first; this system documents dark only. Light tokens exist in `colors_and_type.css` comments / `frontend/app/globals.css`.
- **Frosted UI** (a Whop/Radix-based component lib at `frosted-ui@0.0.1-canary.85`) underlies some primitives like `<Theme>` — we don't recreate it here; we inline equivalent styles.
- **The web app is the only product**; the marketing/landing pages are the same Next.js app's homepage when logged out. Treat both as one UI kit.
