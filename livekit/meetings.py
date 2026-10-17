"""Parse recovery/district/meetings.md (the District 12 scrape) and answer
"what is the next meeting" without a database. Stdlib only."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_TIME = re.compile(r"^(Mon|Tues?|Wed|Thu|Thurs|Fri|Sat|Sun)[a-z]*\s*-\s*(\d{1,2}):(\d{2})\s*(AM|PM)", re.I)


@dataclass
class Meeting:
    name: str
    weekday: int  # 0 = Monday
    hour: int
    minute: int
    codes: str = ""
    notes: str = ""
    place: str = ""
    address: str = ""
    city: str = ""

    def next_start(self, now: datetime) -> datetime:
        delta = (self.weekday - now.weekday()) % 7
        start = (now + timedelta(days=delta)).replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
        if start <= now:
            start += timedelta(days=7)
        return start

    def spoken(self, now: datetime) -> str:
        start = self.next_start(now)
        when = start.strftime("%A at %-I:%M %p") if hasattr(start, "strftime") else str(start)
        bits = [f"{self.name}, {when}"]
        if self.place:
            bits.append(f"at {self.place}")
        if self.city:
            bits.append(f"in {self.city}")
        if self.codes:
            bits.append(f"({self.codes})")
        return " ".join(bits) + "."


def parse_meetings(text: str) -> list[Meeting]:
    out: list[Meeting] = []
    lines = [ln.rstrip() for ln in text.splitlines()]
    i = 0
    while i < len(lines):
        if i + 1 < len(lines) and _TIME.match(lines[i + 1] or ""):
            m = _TIME.match(lines[i + 1])
            name = lines[i].strip()
            day = m.group(1).lower()
            weekday = next((n for n, d in enumerate(_DAYS) if d.startswith(day[:3])), 6)
            hour = int(m.group(2)) % 12 + (12 if m.group(4).upper() == "PM" else 0)
            mt = Meeting(name=name, weekday=weekday, hour=hour, minute=int(m.group(3)))
            j = i + 2
            while j < len(lines) and not (j + 1 < len(lines) and _TIME.match(lines[j + 1] or "")):
                ln = lines[j].strip()
                if ln.startswith("Codes:"):
                    mt.codes = ln[6:].strip()
                elif ln.startswith("Notes:"):
                    mt.notes = ln[6:].strip()
                elif ln == "Location:" and j + 3 < len(lines):
                    mt.place = lines[j + 1].strip()
                    mt.address = lines[j + 2].strip()
                    mt.city = lines[j + 3].strip().split(",")[0]
                    j += 3
                j += 1
            out.append(mt)
            i = j
        else:
            i += 1
    return out


def load_meetings(root: Path | str) -> list[Meeting]:
    p = Path(root) / "recovery" / "district" / "meetings.md"
    return parse_meetings(p.read_text(encoding="utf-8")) if p.exists() else []


def next_meetings(meetings: list[Meeting], now: datetime, *, city: str | None = None, k: int = 3) -> list[Meeting]:
    pool = meetings
    if city:
        c = city.lower()
        pool = [m for m in meetings if c in m.city.lower() or c in m.address.lower()] or meetings
    return sorted(pool, key=lambda m: m.next_start(now))[:k]
