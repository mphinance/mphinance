#!/usr/bin/env python3
"""Lint .claude/skills/*/SKILL.md manifests.

Adapted from the validation pattern in anthropics/financial-services
(scripts/check.py, Apache-2.0). Checks frontmatter, name/folder match, and
warns on broken relative links so skills don't drift from the code they document.

Usage:
    python scripts/check_skills.py          # lint, exit 1 on errors
    python scripts/check_skills.py --list    # list discovered skills
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / ".claude" / "skills"

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Return a flat key->value dict for a leading --- YAML block, or None."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    data: dict[str, str] = {}
    key = None
    for line in block.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            data[key] = m.group(2).strip()
        elif key and line.startswith(" "):
            # folded scalar continuation (description: >- ...)
            data[key] = (data[key] + " " + line.strip()).strip()
    return data


def check_skill(skill_md: Path, errors: list[str], warnings: list[str]) -> None:
    rel = skill_md.relative_to(REPO)
    folder = skill_md.parent.name
    text = skill_md.read_text(encoding="utf-8")

    fm = parse_frontmatter(text)
    if fm is None:
        errors.append(f"{rel}: missing or malformed YAML frontmatter")
        return

    name = fm.get("name", "").strip().strip("'\"")
    if not name:
        errors.append(f"{rel}: frontmatter missing 'name'")
    elif name != folder:
        errors.append(f"{rel}: name '{name}' != folder '{folder}'")

    desc = fm.get("description", "").strip()
    if not desc:
        errors.append(f"{rel}: frontmatter missing 'description'")
    elif "use when" not in desc.lower():
        warnings.append(f"{rel}: description has no 'Use when ...' trigger clause")

    # Relative links should resolve (warn — code may live in a sibling repo).
    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = target.split("#", 1)[0]
        if not path:
            continue
        if not (skill_md.parent / path).resolve().exists():
            warnings.append(f"{rel}: link target not found -> {target}")


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"No skills directory at {SKILLS_DIR.relative_to(REPO)}")
        return 1

    skills = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    if "--list" in sys.argv:
        for s in skills:
            print(s.parent.name)
        return 0

    if not skills:
        print("No SKILL.md files found.")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    for s in skills:
        check_skill(s, errors, warnings)

    for w in warnings:
        print(f"  warn: {w}")
    for e in errors:
        print(f" ERROR: {e}")

    status = "FAIL" if errors else "OK"
    print(
        f"\n{status} — {len(skills)} skills, "
        f"{len(errors)} error(s), {len(warnings)} warning(s)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
