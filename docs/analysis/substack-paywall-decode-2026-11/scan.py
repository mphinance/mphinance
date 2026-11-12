import json,sys,urllib.request,concurrent.futures as cf
def get(u):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
    return json.load(urllib.request.urlopen(r,timeout=20))
pubs={}
for kind in ["paid","rising","trending","all"]:
  for pg in range(0,5):
    try: d=get(f"https://substack.com/api/v1/category/public/153/{kind}?page={pg}")
    except Exception as e: break
    for p in d.get('publications',[]):
        host=p.get('custom_domain') or f"{p['subdomain']}.substack.com"
        pubs.setdefault(host,(kind,p.get('name')))
    if not d.get('more'): break
print(len(pubs),"pubs",file=sys.stderr)
def chk(h):
    try:
        d=get(f"https://{h}/api/v1/archive?sort=new&limit=20")
        ps=d['posts'] if isinstance(d,dict) else d
        ps=[p for p in ps if p.get('type')!='podcast']
        if not ps: return None
        paid=sum(p['audience']=='only_paid' for p in ps)
        return (paid/len(ps),len(ps),h,ps[0]['post_date'][:10])
    except Exception as e: return None
with cf.ThreadPoolExecutor(12) as ex:
    res=[r for r in ex.map(chk,pubs) if r]
for r in sorted(res,reverse=True):
    print(f"{r[0]:.2f} n={r[1]} last={r[3]} {r[2]} [{pubs[r[2]][0]}] {pubs[r[2]][1]}")
