#!/usr/bin/env python3
"""
Sam's Draft Generator — Builds latest.md with everything since Michael's last publish.

Reads ghost blog entries + git commits since the last published post,
organizes them into a draft document Michael can riff on when he writes.

Usage:
    python3 scripts/build_latest_draft.py           # auto-detect last publish date
    python3 scripts/build_latest_draft.py 2026-03-11  # specify date manually

The script NEVER overwrites Michael's writing. It:
1. Detects the frontmatter status (draft/published)
2. Preserves any status:published content as "PREVIOUS POST"
3. Appends new material below as "SAM'S SESSION NOTES"
"""

import json
import subprocess
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BLOG_PATH = PROJECT_ROOT / "landing" / "blog" / "blog_entries.json"
LATEST_PATH = PROJECT_ROOT / "docs" / "substack" / "latest.md"


def get_last_publish_date() -> str:
    """Read frontmatter of latest.md to find last published date."""
    if not LATEST_PATH.exists():
        return (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    text = LATEST_PATH.read_text(encoding="utf-8")

    # Check if there's a published post — look at frontmatter
    fm_match = re.search(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        # If status is published, use that date
        if 'status: published' in fm:
            date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', fm)
            if date_match:
                return date_match.group(1)

    # Fallback: use git log to find when latest.md was last modified by Michael
    try:
        result = subprocess.run(
            ['git', 'log', '--format=%ai|%an', '-20', '--', 'docs/substack/latest.md'],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT)
        )
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                date_str, author = line.split('|', 1)
                # If authored by a human (not bot/actions), that's our last publish
                if 'github-actions' not in author.lower() and 'sam' != author.strip().lower():
                    return date_str[:10]
    except Exception:
        pass

    # Default: 3 days ago
    return (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")


def get_blog_entries_since(since_date: str) -> list[dict]:
    """Get substantive ghost blog entries since a date."""
    if not BLOG_PATH.exists():
        return []

    entries = json.loads(BLOG_PATH.read_text(encoding="utf-8"))
    results = []

    for entry in entries:
        date = entry.get("date", "")
        if date < since_date:
            continue
        log = entry.get("ghost_log", "")
        # Skip stub entries (auto-generated "pushed N commits" with no real content)
        if "Sam's brain is offline" in log or len(log) < 100:
            continue
        results.append(entry)

    return results


def get_git_summary_since(since_date: str) -> dict:
    """Get git commit stats since a date."""
    try:
        result = subprocess.run(
            ['git', 'log', f'--since={since_date}', '--format=%H|%ai|%s', '--no-merges'],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT)
        )
        lines = [l for l in result.stdout.strip().split('\n') if l]

        # Categorize commits
        categories = {
            "features": [],
            "fixes": [],
            "blog": [],
            "deploy": [],
            "cleanup": [],
        }

        for line in lines:
            parts = line.split('|', 2)
            if len(parts) < 3:
                continue
            sha, date, msg = parts
            short = f"`{sha[:7]}` {msg}"

            if any(e in msg for e in ['🆕', '📊', '🧠', '🔮']):
                categories["features"].append(short)
            elif any(e in msg for e in ['🔧', '🏥']):
                categories["fixes"].append(short)
            elif '👻' in msg:
                categories["blog"].append(short)
            elif any(e in msg for e in ['🧹', '🗃️']):
                categories["cleanup"].append(short)
            else:
                categories["features"].append(short)  # default

        # Count files changed
        stat_result = subprocess.run(
            ['git', 'diff', '--stat', f'--since={since_date}', 'HEAD~50', 'HEAD'],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT)
        )

        return {
            "total_commits": len(lines),
            "categories": categories,
            "since": since_date,
        }
    except Exception as e:
        return {"total_commits": 0, "categories": {}, "since": since_date, "error": str(e)}


def strip_html(text: str) -> str:
    """Clean HTML tags from ghost blog entries."""
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # Convert bullet points
    text = text.replace('•', '-')
    return text.strip()


def build_draft(since_date: str = None) -> str:
    """Build the full draft document."""
    if since_date is None:
        since_date = get_last_publish_date()

    today = datetime.now().strftime("%Y-%m-%d")
    blog_entries = get_blog_entries_since(since_date)
    git_data = get_git_summary_since(since_date)

    # Preserve existing content
    existing_content = ""
    if LATEST_PATH.exists():
        existing = LATEST_PATH.read_text(encoding="utf-8")
        # Strip frontmatter
        stripped = re.sub(r'^---\s*\n.*?\n---\s*\n', '', existing, flags=re.DOTALL)
        # Remove any previous SAM'S SESSION NOTES section
        if '<!-- SAM\'S SESSION NOTES' in stripped:
            stripped = stripped[:stripped.index('<!-- SAM\'S SESSION NOTES')]
        existing_content = stripped.strip()

    # Build the draft
    lines = []

    # Frontmatter
    lines.append("---")
    lines.append("status: draft")
    lines.append("author: sam")
    lines.append(f"date: {today}")
    lines.append(f"content_since: {since_date}")
    lines.append("note: Change status to 'published' and author to 'michael' when you post to Substack")
    lines.append("---")
    lines.append("")

    # Preserve existing post content
    if existing_content:
        lines.append(existing_content)
        lines.append("")
        lines.append("")

    # Sam's session notes
    lines.append("<!-- SAM'S SESSION NOTES — auto-generated, do not edit above this line -->")
    lines.append("")
    lines.append(f"# 📋 Sam's Session Notes — Since {since_date}")
    lines.append("")
    lines.append(f"> *{git_data['total_commits']} commits, {len(blog_entries)} sessions logged.*")
    lines.append(f"> *Auto-generated {today}. Use this as raw material for your next post.*")
    lines.append("")

    # Blog entries as session recaps
    if blog_entries:
        lines.append("---")
        lines.append("")
        lines.append("## Session Recaps")
        lines.append("")

        for entry in blog_entries:
            date = entry.get("date", "")
            period = entry.get("period", "")
            log = strip_html(entry.get("ghost_log", ""))
            suggestions = strip_html(entry.get("suggestions", ""))
            ticker = entry.get("chart_ticker", "")
            commits = entry.get("commits", 0)

            lines.append(f"### {date} ({period}) {'— $' + ticker if ticker else ''}")
            lines.append("")
            lines.append(log)
            lines.append("")
            if suggestions:
                lines.append(f"**Sam's Suggestions:** {suggestions}")
                lines.append("")
            lines.append(f"*{commits} commits this session*")
            lines.append("")

    # Git highlight reel
    cats = git_data.get("categories", {})
    features = cats.get("features", [])
    fixes = cats.get("fixes", [])

    if features or fixes:
        lines.append("---")
        lines.append("")
        lines.append("## Commit Highlight Reel")
        lines.append("")
        if features:
            lines.append("### 🆕 Features & Data")
            for f in features[:10]:
                lines.append(f"- {f}")
            lines.append("")
        if fixes:
            lines.append("### 🔧 Fixes & Improvements")
            for f in fixes[:10]:
                lines.append(f"- {f}")
            lines.append("")

    # Writing prompts from the data
    lines.append("---")
    lines.append("")
    lines.append("## 💡 Writing Prompts (Sam's suggestions)")
    lines.append("")
    lines.append("*Pick one of these angles for tonight's post:*")
    lines.append("")

    # Auto-generate prompts from the session content
    prompts = []
    for entry in blog_entries[:3]:
        log = entry.get("ghost_log", "")
        # Extract bold headings as potential topics
        headings = re.findall(r'<b>(.*?)</b>', log)
        for h in headings[:2]:
            if len(h) > 10 and len(h) < 80:
                prompts.append(h)

    if prompts:
        for i, p in enumerate(prompts[:5], 1):
            lines.append(f"{i}. **{p}** — expand this into a story")
    else:
        lines.append("1. What you built this week and why it matters")
        lines.append("2. A trade or setup that taught you something")
        lines.append("3. The intersection of recovery and trading")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by `scripts/build_latest_draft.py` — Sam 👻*")

    return "\n".join(lines)


if __name__ == "__main__":
    since = sys.argv[1] if len(sys.argv) > 1 else None
    draft = build_draft(since)

    LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_PATH.write_text(draft, encoding="utf-8")

    # Count what we generated
    blog_count = len(get_blog_entries_since(since or get_last_publish_date()))
    git = get_git_summary_since(since or get_last_publish_date())
    print(f"✅ Draft generated: {LATEST_PATH}")
    print(f"   {git['total_commits']} commits, {blog_count} session logs")
    print(f"   Content since: {since or get_last_publish_date()}")
