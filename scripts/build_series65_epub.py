#!/usr/bin/env python3
"""Build the Series 65 study EPUB from the pass-the-65 markdown sources.

Reads the course markdown out of the sibling `pass-the-65` repo
(NotebookLM/ folder) and writes a single EPUB with an accuracy
disclaimer as the first page. Output drops into the gitignored
notebooklm/ scratch folder by default.

Usage:
    PYTHONIOENCODING=utf-8 python scripts/build_series65_epub.py

Then publish via:
    gh release upload study-materials notebooklm/series65-study-guide.epub \
        --repo mphinance/pass-the-65 --clobber

Requires: ebooklib, markdown  (pip install ebooklib markdown)
"""
import os
from pathlib import Path

import markdown
from ebooklib import epub

REPO_ROOT = Path(__file__).resolve().parents[1]
# Sibling checkout of github.com/mphinance/pass-the-65
SRC = Path(os.environ.get(
    "PASS65_SRC",
    REPO_ROOT.parent / "pass-the-65" / "NotebookLM",
))
OUT = Path(os.environ.get(
    "PASS65_EPUB_OUT",
    REPO_ROOT / "notebooklm" / "series65-study-guide.epub",
))

# (filename, chapter title) in reading order
CHAPTERS = [
    ("00-course-overview.md",                       "Course Overview"),
    ("domain-1-laws-and-regulations.md",            "Domain 1: Laws and Regulations"),
    ("domain-2-investment-vehicles.md",             "Domain 2: Investment Vehicles"),
    ("domain-3-recommendations-and-strategies.md",  "Domain 3: Recommendations and Strategies"),
    ("domain-4-economic-factors.md",                "Domain 4: Economic Factors"),
    ("cheat-sheet-all-domains.md",                  "Cheat Sheet: All Domains"),
    ("common-exam-traps.md",                        "Common Exam Traps"),
    ("mnemonics.md",                                "Mnemonics"),
]

DISCLAIMER_HTML = """
<h1>Read This First: Disclaimer</h1>
<p><strong>This is a free, AI-assisted study aid. It is not official exam
material, it is not legal, financial, tax, or investment advice, and it is not
a substitute for the official NASAA Series 65 content outline or an accredited
prep course.</strong></p>
<p>This guide was compiled with the help of AI tools, and like any study aid it
can contain mistakes: outdated rules, wrong figures, oversimplifications, or
flat-out errors. Securities laws, dollar thresholds, and exam weightings change.
Always verify anything you plan to rely on against a current, authoritative
source before you trust it.</p>
<p>Use this as a supplement and a study warm-up, not as your single source of
truth. Confirm the facts, take real practice exams, and when in doubt, defer to
the official materials and a qualified instructor.</p>
<p>No warranty of any kind is made as to accuracy or completeness. You use this
material at your own risk, and the author is not liable for any outcome,
including exam results, that comes from using it. Passing the Series 65 is on
you. Good luck. You've got this.</p>
"""

CSS = """
body { font-family: Georgia, serif; line-height: 1.5; padding: 0 6%; }
h1 { font-size: 1.6em; margin-top: 1.2em; }
h2 { font-size: 1.3em; border-bottom: 1px solid #ccc; padding-bottom: .2em; }
h3 { font-size: 1.1em; }
code { background: #f4f4f4; padding: 1px 4px; border-radius: 3px; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #bbb; padding: 6px 8px; text-align: left; }
blockquote { border-left: 3px solid #888; margin-left: 0; padding-left: 1em; color: #444; }
"""


def main() -> None:
    book = epub.EpubBook()
    book.set_identifier("mphinance-series65-study-guide")
    book.set_title("Pass the 65: A Free Series 65 Study Guide")
    book.set_language("en")
    book.add_author("Michael Hanko (mphinance)")

    style = epub.EpubItem(uid="style", file_name="style/main.css",
                          media_type="text/css", content=CSS)
    book.add_item(style)

    md = markdown.Markdown(extensions=["extra", "sane_lists", "toc"])
    chapters = []

    disc = epub.EpubHtml(title="Disclaimer", file_name="chap_disclaimer.xhtml", lang="en")
    disc.content = f"<html><head></head><body>{DISCLAIMER_HTML}</body></html>"
    disc.add_item(style)
    book.add_item(disc)
    chapters.append(disc)

    for i, (fname, title) in enumerate(CHAPTERS):
        md.reset()
        html = md.convert((SRC / fname).read_text(encoding="utf-8"))
        ch = epub.EpubHtml(title=title, file_name=f"chap_{i:02d}.xhtml", lang="en")
        ch.content = f"<html><head></head><body>{html}</body></html>"
        ch.add_item(style)
        book.add_item(ch)
        chapters.append(ch)

    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters

    OUT.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(OUT), book)
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(chapters)} chapters)")


if __name__ == "__main__":
    main()
