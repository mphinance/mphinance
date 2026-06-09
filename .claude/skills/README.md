# Skills

Domain playbooks Sam (and any agent) loads on demand, instead of pasting the
same context every session. Each skill is a folder with a `SKILL.md` that has
YAML frontmatter (`name`, `description`) plus the operational meat.

Layout and conventions are adapted from Anthropic's
[`anthropics/financial-services`](https://github.com/anthropics/financial-services)
reference repo (Apache-2.0) — we borrowed the *structure* (file-based skills,
a manifest linter, a connector manifest), not their institutional content.

## Current skills

| Skill | What it does |
|-------|--------------|
| [`momentum-squeeze`](momentum-squeeze/SKILL.md) | Two-phase squeeze → pullback momentum playbook |
| [`0dte-flow`](0dte-flow/SKILL.md) | 0DTE XSP day-trading decision support (signals → exit cascade) |
| [`batch-scanner`](batch-scanner/SKILL.md) | Run all screener strategies → Google Sheets |
| [`stock-analyzer`](stock-analyzer/SKILL.md) | ML 5-day price-range prediction + technical insights |

Each skill links back to its full root-level guide as the source of truth.

## Adding a skill

1. `mkdir .claude/skills/<slug>` and add `SKILL.md`.
2. Frontmatter `name:` must equal the folder name. Write `description:` as
   *"<what it does>. Use when <trigger>."* — that's what tells Sam when to load it.
3. Run the linter: `python scripts/check_skills.py`.

## Important note (borrowed framing)

The upstream repo's hard rule: agents **draft analyst work product for human
review** — they do not execute transactions. These skills are decision support.
`0dte-flow` in particular is a planning aid: **Michael places every order.**
