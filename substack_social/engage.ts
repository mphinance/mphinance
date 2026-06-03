import { SubstackClient } from 'substack-api';
import * as fs from 'fs';
import * as path from 'path';

// ─── Load SID from repo-root .env (search up from here) ─────────────────────
function loadEnv(): Record<string, string> {
  const candidates = [
    path.resolve(__dirname, '.env'),
    path.resolve(__dirname, '..', '.env'),
    path.resolve(__dirname, '..', '..', '.env'),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      const out: Record<string, string> = {};
      for (const line of fs.readFileSync(p, 'utf8').split(/\r?\n/)) {
        const t = line.trim();
        if (!t || t.startsWith('#') || !t.includes('=')) continue;
        const [k, ...rest] = t.split('=');
        out[k.trim()] = rest.join('=').trim().replace(/^"(.*)"$/, '$1');
      }
      return out;
    }
  }
  return {};
}

const env = loadEnv();
const sid = process.env.SUBSTACK_SID || env.SUBSTACK_SID;
const pubUrl = process.env.SUBSTACK_HOSTNAME || env.SUBSTACK_HOSTNAME || 'mphinance.substack.com';

if (!sid) {
  console.error('No SUBSTACK_SID found. Set it in repo-root .env or as an env var.');
  process.exit(1);
}

async function run() {
  const client = new SubstackClient({
    token: sid,
    publicationUrl: pubUrl,
    // substack.com 429s well below the lib's default of 25/s. Resolving each
    // followed profile now costs 2 calls (feed + public_profile), so keep this
    // low — ~3/s mirrors engage.py's 0.4s spacing and stays under the limit.
    maxRequestsPerSecond: 3,
  });

  const isConnected = await client.testConnectivity();
  if (!isConnected) {
    console.error("Not connected! SID might be expired.");
    return;
  }
  
  let me;
  try {
     me = await client.ownProfile();
     console.log(`Authenticated as ${me.name}`);
  } catch (e) {
     console.error("Failed to get own profile:", e.message);
     return;
  }
  
  const following = [];
  try {
     for await (const user of me.following({ limit: 100 })) {
        following.push(user);
     }
  } catch (e) {
     console.error("Failed getting following:", e.message);
  }
  
  console.log(`Found ${following.length} followed profiles.`);
  
  const twoWeeksAgo = new Date();
  twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);
  
  const items: any[] = [];
  let likedCount = 0;
  let attempts = 0;
  
  for (const prof of following) {
     console.log(`Checking @${prof.slug}`);
     try {
       for await (const post of prof.posts({ limit: 10 })) {
         if (post.publishedAt && post.publishedAt > twoWeeksAgo) {
            attempts++;
            let liked = false;
            try {
              if (likedCount < 200) {
                 await post.like();
                 likedCount++;
                 liked = true;
              }
            } catch(e: any) { console.error(`Like Post failed: ${e.message}`); }
            
            let url = "";
            try {
               const fp = await post.fullPost();
               url = fp.url;
            } catch(e) {
               url = `https://${prof.slug}.substack.com/p/${post.id}`;
            }

            items.push({
               type: 'Post',
               author: prof.name,
               title: post.title || 'Untitled',
               url: url,
               snippet: post.truncatedBody || post.body || "",
               date: post.publishedAt,
               liked
            });
         }
       }
       
       for await (const note of prof.notes({ limit: 20 })) {
         // Some type mappings use createdAt for notes
         const noteDate = (note as any).createdAt || (note as any).publishedAt;
         if (noteDate && new Date(noteDate) > twoWeeksAgo) {
            attempts++;
            let liked = false;
            try {
              if (likedCount < 200) {
                 await note.like();
                 likedCount++;
                 liked = true;
              }
            } catch(e: any) { console.error(`Like Note failed: ${e.message}`); }
            
            items.push({
               type: 'Note',
               author: prof.name,
               title: 'Note',
               url: `https://substack.com/profile/${prof.id}/note/${note.id}`,
               snippet: note.body || "",
               date: new Date(noteDate),
               liked
            });
         }
       }
     } catch(e: any) {
         console.error(`Error processing @${prof.slug}: ${e.message}`);
     }
     
     if (likedCount >= 200) {
       console.log("Reached 200 likes. Stopping early.");
       break;
     }
  }
  
  items.sort((a, b) => b.date.getTime() - a.date.getTime());

  // ─── Reading-list markdown ────────────────────────────────────────────────
  let md = `# Your Substack Catch-Up (Last 2 Weeks)\n\n`;
  md += `*Processed ${attempts} items, successfully liked ${likedCount} recent posts across your network.*\n\n`;
  for (const item of items) {
    const status = item.liked ? "❤️ Liked" : "📝 Read";
    md += `### [${item.type}] ${item.title} by ${item.author} (${status})\n`;
    md += `*${item.date.toISOString().split('T')[0]}* — [Read Here](${item.url})\n\n`;
    const snippet = typeof item.snippet === 'string' ? item.snippet.replace(/\n/g, '\n> ') : '';
    md += `> ${snippet.substring(0, 300)}...\n\n`;
    md += `---\n\n`;
  }

  const dataDir = path.resolve(__dirname, 'data');
  fs.mkdirSync(dataDir, { recursive: true });
  const readingPath = path.join(dataDir, 'substack_reading_list.md');
  fs.writeFileSync(readingPath, md);
  console.log(`Reading list written to ${readingPath}`);

  // ─── Comment review queue ────────────────────────────────────────────────
  // engage.ts auto-likes. Comments are NOT auto-fired — they queue here for
  // Michael to review/edit, then engage_comments.ts posts only `approved: true` ones.
  // Only queue Posts (skip Notes — they get fewer signal-worthy comments).
  const queuePath = path.join(dataDir, 'comment_queue.json');
  let existingQueue: any[] = [];
  if (fs.existsSync(queuePath)) {
    try { existingQueue = JSON.parse(fs.readFileSync(queuePath, 'utf8')); } catch {}
  }
  const existingUrls = new Set(existingQueue.map((q: any) => q.url));

  const newQueue = items
    .filter(it => it.type === 'Post' && !existingUrls.has(it.url))
    .map(it => ({
      url: it.url,
      author: it.author,
      title: it.title,
      date: it.date.toISOString().split('T')[0],
      snippet: (typeof it.snippet === 'string' ? it.snippet : '').substring(0, 240),
      // Edit this; engage_comments.ts only fires comments with body.length > 0
      comment: "",
      // Flip to true after you've written a comment and want it sent
      approved: false,
      // Bookkeeping
      status: "pending", // pending | sent | skipped
      added: new Date().toISOString(),
    }));

  const mergedQueue = [...existingQueue, ...newQueue];
  fs.writeFileSync(queuePath, JSON.stringify(mergedQueue, null, 2));
  console.log(`Comment queue: +${newQueue.length} new (${mergedQueue.length} total pending) → ${queuePath}`);

  console.log(`Total attempts: ${attempts}, total liked: ${likedCount}`);
  console.log(`\nNext: edit ${queuePath}, set comment + approved:true, then run "npm run engage:comments"`);
}

run().catch(console.error);
