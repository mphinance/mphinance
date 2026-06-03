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
```

Credentials come from the repo-root `.env` (gitignored). The scripts look for
`SUBSTACK_SID` and `SUBSTACK_HOSTNAME` and fall through to environment
variables of the same names. No more hardcoded cookies in source files.

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

Until that build runs, `Post.like()` / `Post.addComment()` will return
undefined or throw "not implemented." `npm run engage` will still produce
the reading list and comment queue, but the actual like requests will
silently no-op or error in the console.

## Scripts

### `npm run engage` — likes + reading list + comment queue
**This script auto-fires likes.** Not read-only. It:
1. Pulls your ~100 followed profiles
2. Iterates each profile's posts and notes from the last 14 days
3. Calls `post.like()` / `note.like()` on every one (hard cap: 200 likes/run)
4. Writes a markdown catch-up digest to `data/substack_reading_list.md`
5. Appends new Posts to `data/comment_queue.json` for your review (Notes are
   skipped — fewer signal-worthy comments)

Comments are NOT auto-fired. They wait in the queue for you.

### `npm run engage:comments` — fire approved comments
Reads `data/comment_queue.json`, posts every entry where `approved: true`
and `status: "pending"` and `comment` is non-empty, then flips status to
`sent`. Idempotent: rerunning won't double-post. Pass `-- --dry-run` to
preview without hitting the API.

Workflow:
```
npm run engage                       # likes everything, queues comment slots
# edit data/comment_queue.json, fill in comments, set approved:true
npm run engage:comments -- --dry-run # preview
npm run engage:comments              # send
```

Throttle: 1.5s between comments.

### `npm run explore`
Discovery / sandbox script for poking at the API.

### `npm run pulse`
Ticker pulse (see `ticker_pulse.ts`).

## Data layout
- `data/my-reads.json` + `data/my-reads.md` — your read list (generated)
- `data/daily-reads-digest.md` — daily digest summary
- `data/substack_reading_list.md` — last 2 weeks catch-up from `npm run engage`
- `data/comment_queue.json` — pending/sent comment queue
- `data/articles/` — cached article content

## Relationship to top-level Python tooling
- `../substack_dossier.py` / `../substack_poster.py` are the POST side
  (creating drafts via cookie-auth + ProseMirror JSON). Independent of this
  TS sub-project — they speak Substack's draft API directly.
- This sub-project is the READ + ENGAGE side, using substack-api's HTTP
  client + auth.

The two halves now share the same `.env` cookie at the repo root, so a
single SID rotation updates everything.
