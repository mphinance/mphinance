"""Retrieval over Michael's published corpus. Stdlib only, so it runs in CI
without the LiveKit stack and can be reused by any other agent.

Sources (all relative to the repo root):
  data/afterhour/mphinance.json   ~1,200 AfterHour posts, dated
  articles/*/*.md                  Substack long-form drafts
  docs/articles/*/README.md        Substack long-form drafts

The scoring is BM25 over a crude tokenizer. It is not clever and does not
need to be: the corpus is about 1.5 MB and a phone call wants the three
best-dated snippets, not a vector database.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

_TOKEN = re.compile(r"\$?[a-z0-9][a-z0-9'%.]*")
_STOP = frozenset(
    "a an the and or but if of to in on at for with by from as is are was were be been "
    "it its this that these those i me my we our you your he him his she her they them "
    "their so do did does not no yes just like get got have has had will would can could "
    "about into than then there here what when where which who why how all any some".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP and len(t) > 1]


@dataclass
class Doc:
    id: str
    date: str  # YYYY-MM-DD or "" when unknown
    source: str  # "afterhour" | "article"
    title: str
    body: str
    tickers: list[str] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)


@dataclass
class Hit:
    doc: Doc
    score: float
    snippet: str

    def as_text(self, width: int = 700) -> str:
        head = f"[{self.doc.date or 'undated'} | {self.doc.source}"
        if self.doc.title:
            head += f" | {self.doc.title}"
        head += "]"
        return f"{head}\n{self.snippet[:width]}"


class Corpus:
    def __init__(self, docs: list[Doc]):
        self.docs = docs
        self._df: Counter[str] = Counter()
        for d in docs:
            d.tokens = tokenize(d.body)
            self._df.update(set(d.tokens))
        self._avgdl = (sum(len(d.tokens) for d in docs) / len(docs)) if docs else 0.0
        self._tf = [Counter(d.tokens) for d in docs]

    # ---------- loading ----------

    @classmethod
    def load(cls, root: Path | str) -> "Corpus":
        root = Path(root)
        docs: list[Doc] = []
        docs += _load_afterhour(root / "data" / "afterhour" / "mphinance.json")
        docs += _load_articles(root / "articles", "post.md", "substack-post.md")
        docs += _load_articles(root / "docs" / "articles", "README.md")
        return cls(docs)

    # ---------- search ----------

    def search(self, query: str, k: int = 3, *, pure_only: bool = False) -> list[Hit]:
        """BM25 top-k. `pure_only` restricts AfterHour hits to posts before
        2026-01-31, the dated pivot VOICE.md identifies as the last day of
        zero-AI-involvement writing."""
        q = tokenize(query)
        if not q or not self.docs:
            return []
        n = len(self.docs)
        k1, b = 1.5, 0.75
        scored: list[tuple[float, int]] = []
        for i, d in enumerate(self.docs):
            if pure_only and d.source == "afterhour" and d.date >= "2026-01-31":
                continue
            tf = self._tf[i]
            dl = len(d.tokens) or 1
            s = 0.0
            for t in q:
                f = tf.get(t)
                if not f:
                    continue
                idf = math.log(1 + (n - self._df[t] + 0.5) / (self._df[t] + 0.5))
                s += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / self._avgdl))
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        return [Hit(self.docs[i], s, _snippet(self.docs[i].body, q)) for s, i in scored[:k]]

    def by_ticker(self, ticker: str, k: int = 5) -> list[Doc]:
        t = ticker.upper().lstrip("$")
        hits = [d for d in self.docs if t in d.tickers]
        hits.sort(key=lambda d: d.date, reverse=True)
        return hits[:k]


# ---------- helpers ----------

def _load_afterhour(path: Path) -> list[Doc]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: list[Doc] = []
    for p in raw:
        body = (p.get("body") or "").strip()
        if len(body) < 40:
            continue
        tickers = [t.upper().lstrip("$") for t in (p.get("tickers") or []) if t]
        tickers += [m.upper() for m in re.findall(r"\$([A-Za-z]{1,5})\b", body)]
        out.append(
            Doc(
                id=f"ah:{p.get('id')}",
                date=(p.get("createdAt") or "")[:10],
                source="afterhour",
                title="",
                body=body,
                tickers=sorted(set(tickers)),
            )
        )
    return out


def _load_articles(folder: Path, *names: str) -> list[Doc]:
    if not folder.exists():
        return []
    out: list[Doc] = []
    for sub in sorted(folder.iterdir()):
        if not sub.is_dir():
            continue
        for name in names:
            f = sub / name
            if f.exists():
                body = f.read_text(encoding="utf-8", errors="replace")
                title = _first_heading(body) or sub.name
                date = _front_matter_date(body)
                out.append(
                    Doc(
                        id=f"art:{sub.name}",
                        date=date,
                        source="article",
                        title=title,
                        body=body,
                        tickers=sorted(set(m.upper() for m in re.findall(r"\$([A-Za-z]{1,5})\b", body))),
                    )
                )
                break
    return out


def _first_heading(md: str) -> str:
    for line in md.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def _front_matter_date(md: str) -> str:
    m = re.search(r"^date:\s*['\"]?(\d{4}-\d{2}-\d{2})", md, re.M)
    return m.group(1) if m else ""


def _snippet(body: str, q: list[str], width: int = 700) -> str:
    """Window around the first query term that appears, else the opening."""
    low = body.lower()
    best = -1
    for t in q:
        i = low.find(t)
        if i != -1 and (best == -1 or i < best):
            best = i
    if best == -1:
        return body[:width]
    start = max(0, best - width // 3)
    return body[start : start + width]
