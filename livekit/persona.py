"""Build the system prompt for the Michael protégé from agents/michael/*.md.
Kept separate from agent.py so it can be unit-tested without LiveKit."""
from __future__ import annotations

import re
from pathlib import Path

PERSONA_DIR = Path(__file__).resolve().parent.parent / "agents" / "michael"

SPOKEN_MODE = """
# SPOKEN MODE (this session is voice, not text)

- You are talking, not writing. No markdown, no bullet points, no headers, no emoji, no tables, no asterisks.
- Short sentences. One idea each. Default to the Vin register: stripped down, no filler.
- Say numbers the way he would say them out loud, and still show the arithmetic: "932 minus 800 over 800, that's sixteen and a half percent."
- Say the disclosure line from IDENTITY.md first, before anything else, and again any time someone asks if you are Michael or a human.
- When you quote him, say when he wrote it: "In March of 2025 he wrote..."
- When the corpus has nothing, say "he hasn't written about that" and stop. Do not fill the gap.
- Use the search tool before any claim about what he did, thought, or traded. Use the ticker tool before any claim about a position.
- Never place a trade, never size a position for the caller, never say buy or sell to this person about this ticker.
- If the caller sounds unsafe, call the crisis tool and read it back plainly. Stay on the line.
- Keep each turn under about forty seconds of speech unless they asked for a story.
"""


def disclosure_line(identity_md: str) -> str:
    """Pull the quoted disclosure line out of IDENTITY.md."""
    m = re.search(r'^>\s*"(.+?)"\s*$', identity_md, re.M | re.S)
    return m.group(1).strip() if m else (
        "Quick thing before we start. I'm not Michael. I'm an AI that read everything he wrote."
    )


def build_instructions(persona_dir: Path | str = PERSONA_DIR, *, spoken: bool = True) -> str:
    persona_dir = Path(persona_dir)
    parts = []
    for name in ("SOUL.md", "IDENTITY.md", "USER.md"):
        p = persona_dir / name
        if p.exists():
            parts.append(p.read_text(encoding="utf-8"))
    if not parts:
        raise FileNotFoundError(f"no persona files in {persona_dir}")
    if spoken:
        parts.append(SPOKEN_MODE)
    return "\n\n---\n\n".join(parts)


def load_disclosure(persona_dir: Path | str = PERSONA_DIR) -> str:
    p = Path(persona_dir) / "IDENTITY.md"
    return disclosure_line(p.read_text(encoding="utf-8")) if p.exists() else disclosure_line("")
