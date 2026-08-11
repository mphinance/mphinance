# substack_social

mph's Substack engagement + reading pipeline. Built on top of the vendored
substack-api library at `../vendor/substack-api/`.

## Why a vendored library
`substack-api` on npm (v4.0.0) is read-only by design. This repo's vendored
fork (`../vendor/substack-api/`) adds the engagement methods mph implemented
on top of v4:
  - `Post.like()` — was throwing not-implemented, now calls `/post/{id}/reaction`
  - `Post.addComment(body)` — was throwing, now calls `/posts/{id}/comments`
  - `Comment.like()` — NEW
  - `Comment.like()` / `likeComment` / `createComment` in CommentService
  - `Profile.getNotesForProfile()` in ProfileService

See `../vendor/substack-api/` for the full source.

## Setup
```bash
cd substack_social
npm install   # resolves substack-api from ../vendor/substack-api
export SUBSTACK_SID="s%3A..."   # 'substack.sid' cookie from substack.com, required by all scripts
```

## ⚠️ Build status of the vendored fork
As of 2026-05-15, the `dist/` in `../vendor/substack-api/` is stale and
does NOT contain the new engagement methods. The source is in `src/` but
hasn't been re-built since mph's edits.

To rebuild:
```bash
cd ../vendor/substack-api
pnpm install   # pnpm v9 on Node 18, or pnpm v10 on Node 22+
pnpm build     # produces fresh dist/
cd -
npm install    # re-link to refreshed dist
```

Until that build runs, the library calls available are the v4.0.0 baseline
ones only. Engagement features will throw "not implemented" or return
undefined methods.

## Scripts
- `npm run engage`  — interactive engagement dashboard (currently safe-mode/read-only)
- `npm run explore` — exploration / discovery sandbox
- `npm run pulse`   — ticker cashtag pulse across curated finance Substacks
- `npm test`        — runs `retry.test.ts`, a manual check script for `retry.ts`
  (no test framework is wired up for this sub-project, same as the rest of the repo)

## Resilience (`retry.ts`)
All network calls in `engage.ts`/`ticker_pulse.ts` go through `withRetry()`, which:
- retries transient failures (5xx, timeouts, network errors, 429) with
  exponential back-off, honoring a `Retry-After` header when present
- fails immediately on non-retryable client errors (401/403/404/...) instead
  of burning through all attempts on a dead SID or bad request
- `checkConnectivity()` retries `testConnectivity()` a few times before a
  script reports "SID might be expired" — that check swallows its own error
  and just returns `false`, so a single call can't tell an expired session
  apart from a one-off network blip.

## Data
- `data/my-reads.json` + `data/my-reads.md` — your read list (generated)
- `data/daily-reads-digest.md` — daily digest summary
- `data/articles/` — cached article content

## Relationship to top-level Python tooling
- `../substack_dossier.py` / `../substack_poster.py` are the POST side
  (creating drafts via cookie-auth + ProseMirror JSON). Independent of this
  TS sub-project — they speak Substack's draft API directly.
- This sub-project is the READ + ENGAGE side, using substack-api's HTTP
  client + auth.

If a future task needs both create-draft AND like/comment, the two halves
can either share an SID/cookie via a shared `data/.substack_sid` file
(gitignored) or move toward a single typed client. For now they stay
independent.
