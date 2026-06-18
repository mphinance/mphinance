# voice-delta corpus

Backing data for [`/VOICE-DELTA.md`](../../VOICE-DELTA.md). Pairs the machine's
**given** draft against the version Michael **shipped**, so the diff can be read.

```
pairs/<date>_<slug>/
    given.md     # the machine's output (repo / ~/.mph-substack-cache)
    shipped.md   # what published on mphinance.substack.com (fetched)
fetch_shipped.py # rebuilds shipped.md from the live site (public API, no auth)
```

## Rebuild / extend

```bash
python3 fetch_shipped.py --list                 # recent posts: date | title | slug
python3 fetch_shipped.py <slug> > shipped.md     # one post's shipped text
```

**Fetch path (resolves AUTONOMY_PLAN open question #1):** public Substack JSON
endpoints — `…/api/v1/posts/<slug>` for a body, `…/api/v1/archive` for the index.
No auth. For `only_paid` posts you get the free portion up to the paywall, which
still gives a usable delta on everything above the wall. The
substack-toolkit/authenticated path is only needed if we ever want to diff
*below* the paywall; not worth it for v0.

## Adding a pair

1. Find the machine draft (`~/.mph-substack-cache/<date>_<slug>/post.md`, or
   `articles/*/substack-post.md`, or `docs/substack*`), copy it to
   `pairs/<date>_<slug>/given.md`.
2. `python3 fetch_shipped.py <slug> > pairs/<date>_<slug>/shipped.md`
3. Re-read the diffs and update `/VOICE-DELTA.md`.

The bottleneck is **given-draft survival** — only a couple live locally per month,
so save the machine output at publish time if you want more pairs later.
