import * as fs from 'fs';
import * as path from 'path';

// SID is read from ../secrets.env (SUBSTACK_SID=...) so it stays in sync with the
// rest of the toolchain and doesn't silently expire when hardcoded here.
function loadSid(): string {
  if (process.env.SUBSTACK_SID) return process.env.SUBSTACK_SID;
  const envPath = path.resolve(__dirname, '..', 'secrets.env');
  for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
    const t = line.trim();
    if (t && !t.startsWith('#') && t.includes('=')) {
      const i = t.indexOf('=');
      if (t.slice(0, i) === 'SUBSTACK_SID') return t.slice(i + 1).replace(/^['"]|['"]$/g, '');
    }
  }
  throw new Error('SUBSTACK_SID not found in env or ../secrets.env');
}

// Catch-up reach knobs.
const LIKE_CAP = 500;            // hard ceiling on likes per run
const WINDOW_DAYS = 14;          // only engage with content this fresh
const MAX_PAGES = 80;            // safety stop on feed pagination
const OWN_SUBDOMAIN = 'mphinance'; // skip our own posts/notes
const SID = loadSid();
const BASE = 'https://substack.com/api/v1';
const HEADERS = {
  'Cookie': `substack.sid=${SID}`,
  'Accept': 'application/json',
  'Content-Type': 'application/json',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
};

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function react(kind: 'post' | 'comment', id: number): Promise<boolean> {
  // post -> /post/{id}/reaction ; note -> /comment/{id}/reaction
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const res = await fetch(`${BASE}/${kind}/${id}/reaction`, {
        method: 'POST',
        headers: HEADERS,
        body: JSON.stringify({ reaction: '❤' }),
      });
      if (res.status === 429) { await sleep(10000); continue; }
      if (res.ok) return true;
      // 409/already-reacted etc. — treat as non-fatal, do not retry
      return false;
    } catch {
      await sleep(1500);
    }
  }
  return false;
}

async function run() {
  const cutoff = new Date(Date.now() - WINDOW_DAYS * 86400 * 1000);
  let url = `${BASE}/reader/feed`;
  let pages = 0;
  let liked = 0;
  let seenOld = 0;
  const seen = new Set<string>();
  const items: any[] = [];

  console.log(`Walking reads feed. Window ${WINDOW_DAYS}d, like cap ${LIKE_CAP}.`);

  while (pages < MAX_PAGES && liked < LIKE_CAP) {
    let data: any;
    try {
      const res = await fetch(url, { headers: HEADERS });
      if (res.status === 429) { console.log('Rate limited, waiting 10s...'); await sleep(10000); continue; }
      if (res.status === 401 || res.status === 403) { console.error('Auth failed — SID may be expired.'); break; }
      data = await res.json();
    } catch (e: any) { console.error('Feed fetch failed:', e.message); break; }

    const feed: any[] = data.items || [];
    if (feed.length === 0) break;
    pages++;

    for (const it of feed) {
      let kind: 'post' | 'comment' | null = null;
      let id: number | undefined;
      let when: Date | null = null;
      let author = 'Unknown';
      let title = '';
      let link = '';

      if (it.type === 'post' && it.post) {
        kind = 'post'; id = it.post.id;
        when = new Date(it.post.post_date);
        author = it.publication?.name || it.publication?.subdomain || 'Unknown';
        title = it.post.title || 'Untitled';
        link = it.post.canonical_url || (it.publication?.subdomain ? `https://${it.publication.subdomain}.substack.com/p/${it.post.slug}` : '');
        if (it.publication?.subdomain === OWN_SUBDOMAIN) continue; // skip our own
      } else if (it.type === 'comment' && it.context?.type === 'note' && it.comment) {
        kind = 'comment'; id = it.comment.id;
        when = new Date(it.context.timestamp || it.comment.date);
        author = it.context.users?.[0]?.name || it.comment.name || 'Unknown';
        title = 'Note';
        const body = (it.comment.body || '').replace(/\s+/g, ' ').trim();
        title = `Note: ${body.slice(0, 80)}`;
        if (it.comment.handle === OWN_SUBDOMAIN) continue;
      } else {
        continue; // userSuggestions, chat, etc.
      }

      if (!id) continue;
      const key = `${kind}:${id}`;
      if (seen.has(key)) continue;
      seen.add(key);

      if (when && when < cutoff) { seenOld++; continue; }
      seenOld = 0;

      const ok = await react(kind, id);
      if (ok) liked++;
      items.push({ kind, author, title, link, when: when?.toISOString().slice(0, 10), liked: ok });
      console.log(`${ok ? '❤️' : '· '} [${kind}] ${author} — ${title.slice(0, 60)}`);
      await sleep(250);
      if (liked >= LIKE_CAP) break;
    }

    // feed isn't strictly date-sorted; stop once we've seen a long run of stale items
    if (seenOld >= 40) { console.log('Reached stale items, stopping.'); break; }
    if (!data.nextCursor) break;
    url = `${BASE}/reader/feed?cursor=${encodeURIComponent(data.nextCursor)}`;
    await sleep(500);
  }

  // digest
  items.sort((a, b) => (b.when || '').localeCompare(a.when || ''));
  let md = `# Substack Reads Catch-Up (last ${WINDOW_DAYS} days)\n\n`;
  md += `*Walked ${pages} feed pages, liked ${liked} items (cap ${LIKE_CAP}).*\n\n`;
  for (const it of items) {
    md += `### [${it.kind}] ${it.title} — ${it.author} ${it.liked ? '❤️' : ''}\n`;
    md += `*${it.when || ''}*${it.link ? ` — [open](${it.link})` : ''}\n\n`;
  }
  const outDir = '/home/mph/.gemini/antigravity/brain/09965367-b7d3-42a0-94cf-f9897122b399/artifacts';
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'substack_reading_list.md'), md);
  // local copy for convenience
  fs.mkdirSync(path.resolve(__dirname, 'data'), { recursive: true });
  fs.writeFileSync(path.resolve(__dirname, 'data', 'engagement_digest.md'), md);

  console.log(`\nDone. Liked ${liked} items across ${pages} pages. Digest: data/engagement_digest.md`);
}

run().catch(console.error);
