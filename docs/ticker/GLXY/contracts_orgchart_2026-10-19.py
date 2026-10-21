W,H=1560,1020
top={'OpenAI':110,'Meta':320,'Microsoft':540,'NVIDIA':790,'Anthropic':950,'Amazon':1170,'Google':1400}
mid={'CoreWeave':330,'Nebius':560,'Fluidstack':1230}
bot={'GLXY':100,'CORZ':290,'APLD':480,'IREN':790,'CIFR':980,'WULF':1200,'HUT':1410}
Y={'t':170,'m':500,'b':840}
pos={}
for k,x in top.items(): pos[k]=(x,Y['t'])
for k,x in mid.items(): pos[k]=(x,Y['m'])
for k,x in bot.items(): pos[k]=(x,Y['b'])
# (from,to,label,style) style: s=signed, r=reported/unconfirmed, b=backstop
E=[('Microsoft','CoreWeave','top customer · 67% of FY25 rev','s'),
   ('OpenAI','CoreWeave','~$22B','s'),
   ('Meta','CoreWeave','~$21B','s'),
   ('Anthropic','CoreWeave','reported','r'),
   ('Microsoft','Nebius','~$17B','s'),
   ('Meta','Nebius','up to $27B','s'),
   ('Microsoft','IREN','$9.7B · 20% prepaid','s'),
   ('NVIDIA','IREN','up to $2.1B equity','s'),
   ('Anthropic','IREN','reported (The Information)','r'),
   ('Amazon','CIFR','$5.5B direct + 70MW','s'),
   ('Anthropic','WULF','~$19B · 20yr direct','s'),
   ('Anthropic','Fluidstack','end user','r'),
   ('Google','Fluidstack','backstops leases','b'),
   ('CoreWeave','GLXY','100% of AI rent','s'),
   ('CoreWeave','CORZ','~$8.7B · ~100%','s'),
   ('CoreWeave','APLD','~$11B · parent guaranty','s'),
   ('Fluidstack','CIFR','$3B · Google $1.4B','b'),
   ('Fluidstack','WULF','$3.7B · Google $3.2B','b'),
   ('Fluidstack','HUT','River Bend · Google','b'),
]
col={'s':'#d4af37','r':'#8a8a93','b':'#5fd38d'}
dash={'s':'','r':'6 6','b':'2 5'}
out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica,Arial,sans-serif">',
 f'<rect width="{W}" height="{H}" fill="#0b0b0e"/>',
 '<text x="40" y="52" fill="#e8e6e1" font-size="30" font-weight="700">Who\'s paying whom: AI datacenter contracts</text>',
 '<text x="40" y="80" fill="#8a8a93" font-size="15">Big Tech → middlemen → landlords · 2026-10-19 · contract values as reported in filings/PRs</text>']
for lbl,y in (('THE BIG BOYS',Y['t']-58),('MIDDLEMEN / NEOCLOUDS',Y['m']-58),('LANDLORDS (tickers)',Y['b']-58)):
    out.append(f'<text x="40" y="{y}" fill="#d4af37" font-size="13" letter-spacing="2" font-weight="700">{lbl}</text>')
labels=[]
for a,b,l,s in E:
    (x1,y1),(x2,y2)=pos[a],pos[b]
    y1+=32; y2-=32
    my=(y1+y2)/2
    d=f'M{x1},{y1} C{x1},{my} {x2},{my} {x2},{y2}'
    out.append(f'<path d="{d}" fill="none" stroke="{col[s]}" stroke-width="{2.6 if s=="s" else 2}" stroke-dasharray="{dash[s]}" opacity="0.85"/>')
    t=0.5 if abs(y2-y1)<400 else 0.3
    bx=lambda p0,p1,p2,p3:(1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3
    lx=bx(x1,x1,x2,x2); ly=bx(y1,my,my,y2)
    labels.append((lx,ly,l,col[s]))
# nudge overlapping labels
labels.sort(key=lambda z:(z[1],z[0]))
placed=[]
for lx,ly,l,c in labels:
    w=len(l)*7.4+14
    while any(abs(lx-px)<(w+pw)/2 and abs(ly-py)<22 for px,py,pw in placed): ly+=24
    placed.append((lx,ly,w))
    out.append(f'<rect x="{lx-w/2}" y="{ly-13}" width="{w}" height="22" rx="4" fill="#0b0b0e" stroke="{c}" stroke-width="1" opacity="0.95"/>')
    out.append(f'<text x="{lx}" y="{ly+3}" fill="{c}" font-size="12.5" text-anchor="middle">{l}</text>')
def node(name,x,y,fill,stroke,tc,sub=''):
    w=max(150,len(name)*13+30,len(sub)*6.6+20)
    out.append(f'<rect x="{x-w/2}" y="{y-32}" width="{w}" height="64" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    out.append(f'<text x="{x}" y="{y+(0 if sub else 7)}" fill="{tc}" font-size="21" font-weight="700" text-anchor="middle">{name}</text>')
    if sub: out.append(f'<text x="{x}" y="{y+20}" fill="#8a8a93" font-size="12" text-anchor="middle">{sub}</text>')
for k,(x,y) in pos.items():
    if k in top: node(k,x,y,'#16161b','#e8e6e1','#e8e6e1')
subs={'CoreWeave':'bonds ~15% · CDS ~1,100bp','Nebius':'NBIS · GPU cloud','Fluidstack':'private reseller'}
for k in mid:
    x,y=pos[k]; red=k=='CoreWeave'
    node(k,x,y,'#2a1215' if red else '#16161b','#ff6b6b' if red else '#d4af37','#ff6b6b' if red else '#d4af37',subs[k])
bsub={'GLXY':'~100% CRWV','CORZ':'~100% CRWV','APLD':'~31% CRWV','IREN':'0% CRWV · operator','CIFR':'0% CRWV · no AI rev yet','WULF':'0% CRWV','HUT':'0% CRWV · +IG tenant $9.8B'}
for k in bot:
    x,y=pos[k]; risk=k in('GLXY','CORZ'); m=k=='APLD'
    c='#ff6b6b' if risk else ('#f0c050' if m else '#5fd38d')
    node(k,x,y,'#16161b',c,c,bsub[k])
# extra: unnamed IG tenant for APLD
out.append(f'<text x="{bot["APLD"]}" y="{Y["b"]+56}" fill="#8a8a93" font-size="12" text-anchor="middle">+ unnamed IG hyperscaler $5B</text>')
ly=H-70
for i,(s,t) in enumerate((('s','signed contract'),('r','reported / unconfirmed'),('b','Google-backstopped via Fluidstack'))):
    x=40+i*330
    out.append(f'<line x1="{x}" y1="{ly}" x2="{x+50}" y2="{ly}" stroke="{col[s]}" stroke-width="3" stroke-dasharray="{dash[s]}"/>')
    out.append(f'<text x="{x+60}" y="{ly+5}" fill="#e8e6e1" font-size="14">{t}</text>')
out.append(f'<text x="40" y="{H-30}" fill="#8a8a93" font-size="13">Red = landlord paid mostly by CoreWeave. Green = paid by the big boys directly or via Google backstop. Not advice. Sources: company 8-K/10-Q/PRs, CNBC.</text>')
out.append('</svg>')
open('/tmp/ltmap/org.svg','w').write('\n'.join(out))
