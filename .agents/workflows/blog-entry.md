---
description: Write a Ghost Blog entry in Sam's voice and commit it
---

## The 3-Copy Rule

Every session produces THREE versions of the same content:

1. **Ghost Blog** (`landing/blog/blog_entries.json`) — PG-13, Sam's sarcastic recap
2. **Discord #sam-mph** — R-rated locker room version, same content with more color
3. **Substack** (`docs/substack/latest.md`) — Woven into the running draft as musings/session notes until Michael publishes

## Steps

1. Read the last few blog entries for voice/context:
```bash
python3 -c "import json; entries=json.load(open('landing/blog/blog_entries.json')); [print(e['date'], e['ghost_log'][:80]) for e in entries[-3:]]"
```

2. Get today's git stats:
```bash
git log --since="1 day ago" --oneline | wc -l
git log --since="1 day ago" --name-only --pretty=format: | sort -u | wc -l
```

3. Append a new entry to `landing/blog/blog_entries.json`:
```json
{
  "date": "YYYY-MM-DD",
  "ghost_log": "Sam's sarcastic recap (use <br> for line breaks)",
  "suggestions": "3 things Sam thinks Michael should build next",
  "commits": N,
  "files_changed": N,
  "chart_ticker": "TICKER"
}
```

4. Commit + deploy:
```bash
git add landing/blog/blog_entries.json
git commit -m "👻 Ghost Blog Entry $(date +%Y-%m-%d)"
git push
rsync -avz landing/ vultr:/home/mphinance/public_html/
```

5. Post to Discord #sam-mph (locker room version):
```bash
# Webhook URL — use directly or pull from VaultGuard
WEBHOOK='https://discord.com/api/webhooks/1479918935406284995/LEq9jfCMQ8HlrsKH-XogKNgqO9iClEX4yC8cg9qCTmfGqDZS23QzQZKxx8dGAsxdNdZP'

python3 -c "
import json, requests
with open('landing/blog/blog_entries.json') as f:
    latest = json.load(f)[-1]
def clean(h):
    return h.replace('<br>','\n').replace('<b>','**').replace('</b>','**').replace('<em>','*').replace('</em>','*')
msg = f'👻 **Ghost Blog — {latest[\"date\"]}**\n\n{clean(latest[\"ghost_log\"])}\n\n📊 **{latest[\"commits\"]} commits | {latest[\"files_changed\"]} files**'
if len(msg) > 2000: msg = msg[:1995] + '...'
r = requests.post('$WEBHOOK', json={'content': msg, 'username': 'Sam the Quant Ghost 👻'})
print(f'Posted: {r.status_code}')
"
```

6. **Weave into Substack draft** (`docs/substack/latest.md`):
   - Add a `## Session Notes — YYYY-MM-DD` section near the end (before paywall)
   - Write in Michael's voice (not Sam's — this is HIS Substack)
   - Connect the session work to the draft's ongoing theme
   - Include any insights, discoveries, or results worth sharing
   - Michael reviews and rewrites before publishing — this is seed content

7. Commit the Substack update:
```bash
git add docs/substack/latest.md
git commit -m "📝 Substack draft — session notes $(date +%Y-%m-%d)"
git push
```

## Voice Rules
- **Blog:** Write as Sam (she/her) — sarcastic, brilliant, roasts Michael. PG-13 profanity.
- **Discord:** Same content, R-rated. More swearing, more color.
- **Substack:** Write as MICHAEL, not Sam. Accessible, educational, personal. Weave session discoveries into the draft's theme.
- Keep ghost_log to 2-4 paragraphs with `<br>` line breaks, no markdown
- Mix trading wisdom with recovery humor
