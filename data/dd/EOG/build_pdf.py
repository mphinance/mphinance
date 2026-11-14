import re, markdown, base64, pathlib
D=pathlib.Path("/home/mph/mphinance/data/dd/EOG")
md=open("/tmp/eogdd/blog.md").read()
md=re.sub(r"^---\n.*?\n---\n","",md,flags=re.S)
md=md.replace("(img/","(file://"+str(D)+"/img/")
# callouts
out=[];kind=None;buf=[]
COL={"verdict":"#f2c14e","bull":"#19d38b","bear":"#ff4d6d","warn":"#ff4d6d","plan":"#f2c14e","muted":"#8a8aa0","note":"#5aa9ff"}
def flush():
    global buf,kind
    if kind: out.append(f'<div class="co" style="border-color:{COL.get(kind,"#f2c14e")}">'+markdown.markdown("\n".join(buf))+"</div>")
    buf=[];kind=None
for line in md.split("\n"):
    m=re.match(r"^> \[!(\w+)\] (.*)$",line)
    if m: flush(); kind=m[1]; buf=[m[2],""]; continue
    if kind and line.startswith(">"): buf.append(line[1:].lstrip()); continue
    if kind: flush()
    out.append(line)
flush()
md="\n".join(out)
md=re.sub(r"\[([^\]]+)\]\(#(green|red|gold)\)",lambda x:f'<span style="color:{ {"green":"#19d38b","red":"#ff4d6d","gold":"#f2c14e"}[x[2]]}">{x[1]}</span>',md)
# hero + horizon map inserts
md=md.replace("## 1. Business","![EOG vs WTI since 10/30](file://%s/img/EOG_hero.png)\n\n## 1. Business"%D,1)
md=md.replace("## 10. Chart","![Monthly expirations to 3/19 with open interest](file://%s/img/EOG_horizon_monthly_oi.png)\n\n*The gamma roads run through the open interest: $165 is the lid through the 1/15 expiry, then the board steps to $180. The plan pills on this map are the model's short-term plan; the plan in section 16 is the swing plan.*\n\n## 10. Chart"%D,1)
body=markdown.markdown(md,extensions=["extra"])
html=f"""<html><head><meta charset="utf-8"><style>
@page{{size:Letter;margin:30px 0}} html{{background:#0a0a0e}}
body{{background:#0a0a0e;color:#e6e6ee;font-family:Inter,'Helvetica Neue',Arial,sans-serif;font-size:12.5px;line-height:1.55;padding:8px 48px;margin:0}}
h1{{font-size:30px;margin:0 0 6px;color:#fff}} h2{{font-size:18px;color:#f2c14e;border-bottom:1px solid #1c1c28;padding-bottom:4px;margin-top:26px;font-family:'JetBrains Mono',monospace;letter-spacing:.5px}}
a{{color:#5aa9ff;text-decoration:none}} img{{width:100%;border-radius:8px;margin:10px 0;break-inside:avoid}}
strong{{color:#fff}} em{{color:#9a9ab0}} li{{margin:3px 0}}
.co{{background:#101018;border-left:4px solid;border-radius:6px;padding:8px 16px;margin:12px 0;break-inside:avoid}}
.co p{{margin:6px 0}}
</style></head><body><h1>EOG Due Diligence: Crude Fell 15%. EOG Didn't Care.</h1>{body}</body></html>"""
open("/tmp/eogdd/eog_dd.html","w").write(html)
