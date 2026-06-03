# SPEC — Autonomous Loop Work Queue

This file is the brief for the autonomous coding loop (`.github/workflows/claude-autonomous.yml`).
On the first run it gets decomposed into `feature_list.json`; after that, the loop
works through the features one PR at a time. **Edit this file to steer what gets built.**

Rules the loop must respect (these are enforced again in `.github/CLAUDE.md`):

- Every change ships as a PR to `main` — never a direct push. You merge.
- One feature per run. Keep diffs tight and scoped to the feature.
- Reuse existing patterns; match the surrounding code style.
- Never commit secrets. No edits to `.github/workflows/*`. No deleting generated
  `docs/` artifacts (e.g. `docs/ticker/*/deep_dive.*`).
- There is no formal test suite yet — validate by running the affected stage/script
  and say how. Don't claim tests passed when none ran.

---

## Goal

Harden and lightly extend the existing pipeline and tooling without changing any
output formats that downstream stages or the published site depend on.

## Features

1. **Test scaffold.** Add a `tests/` directory with `pytest` configured (a
   `requirements-dev.txt` or a `[pytest]`/`pyproject`-free `pytest.ini`), plus one
   real test for an existing pure helper (e.g. a momentum-scoring or parsing
   function in `dossier/`). This unblocks the "run tests first" step for every
   later feature.

2. **Input validation on external API responses.** In the dossier data-fetch
   stage, add defensive checks for the known failure shapes (empty/`"null"`-string
   payloads from Tradier, missing keys from yfinance) so a bad upstream response
   fails loudly with a clear message instead of corrupting downstream data.

3. **Substack engagement resilience.** In `substack_social/`, add bounded retries
   with clear logging around the network calls so a transient failure doesn't abort
   the whole engage/pulse run. Don't change the vendored fork in `vendor/`.

4. **Wire `auto_backtest.py` into the daily pipeline.** Add it as a late stage of
   the dossier run, guarded so a backtest failure does not fail the whole pipeline.

## Out of scope (do not touch without a new spec)

- Trading logic / signal math changes.
- Anything under `vaultguard/` or `algo/` (separate host, separate lifecycle).
- Deploy scripts, SSH, or production hosts.
