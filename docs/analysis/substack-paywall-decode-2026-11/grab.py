import json,sys,urllib.request,re,html,os
import time
def get(u):
    for i in range(6):
        try:
            r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
            v=json.load(urllib.request.urlopen(r,timeout=25)); time.sleep(1.5); return v
        except urllib.error.HTTPError as e:
            if e.code!=429: raise
            time.sleep(20*(i+1))
    raise SystemExit("429 forever")
def txt(h): return html.unescape(re.sub(r'<[^>]+>',' ',h or '')).strip()
host=sys.argv[1]; out=sys.argv[2]; os.makedirs(out,exist_ok=True)
d=get(f"https://{host}/api/v1/archive?sort=new&limit=12")
ps=[p for p in (d['posts'] if isinstance(d,dict) else d) if p['audience']=='only_paid'][:5]
for p in ps:
    full=get(f"https://{host}/api/v1/posts/{p['slug']}")
    body=txt(full.get('body_html'))
    try:
        cm=get(f"https://{host}/api/v1/post/{p['id']}/comments?all_comments=true&sort=best_first")
        comments=[]
        def walk(cs):
            for c in cs:
                if c.get('body'): comments.append(f"{c.get('name')}: {c['body']}")
                walk(c.get('children',[]))
        walk(cm.get('comments',[]))
    except Exception as e: comments=[f"ERR {e}"]
    rec=dict(date=p['post_date'][:10],title=p['title'],subtitle=p.get('subtitle'),desc=p.get('description'),
             wordcount=p.get('wordcount'),url=p.get('canonical_url'),preview_words=len(body.split()),
             preview=body,comments=comments,reactions=p.get('reaction_count'),postTags=[t.get('name') for t in p.get('postTags',[])])
    json.dump(rec,open(f"{out}/{p['slug'][:50]}.json","w"),indent=1)
    print(rec['date'],rec['wordcount'],'prev',rec['preview_words'],'cm',len(comments),rec['title'][:70])
