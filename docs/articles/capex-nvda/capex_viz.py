import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image
import io, os
import matplotlib.text as _mt
_o=_mt.Text.__init__
def _i(self,*a,**k):
    k.setdefault("parse_math",False); _o(self,*a,**k)
_mt.Text.__init__=_i
OUT="/home/mph/mphinance/docs/articles/capex-nvda/images"
BG="#0b0d12"; TXT="#e8e6e1"; MUT="#8b90a0"; GOLD="#E8B75A"; NV="#76B900"; GREY="#3a4152"; BLU="#6FA8FF"
plt.rcParams.update({"font.family":"DejaVu Sans","text.color":TXT})
FOOT="mphinance · NVDA Q2 FY27 filing ($48.7B hyperscaler rev), big-4 2026 capex guides (~$735B) · estimate, not advice"

# 1: one dollar
fig=plt.figure(figsize=(14.56,6.4),dpi=100,facecolor=BG); ax=fig.add_axes([0.06,0.30,0.88,0.22]); ax.set_axis_off(); ax.set_xlim(0,100); ax.set_ylim(0,1)
segs=[(27,NV,"~27¢  NVIDIA"),(33,GREY,"~33¢  rest of the servers\n(custom chips, memory, CPUs, storage)"),(40,"#262b38","~40¢  buildings, power, cooling, network")]
x=0
for w,c,l in segs:
    ax.add_patch(FancyBboxPatch((x+0.3,0.05),w-0.6,0.9,boxstyle="square,pad=0",fc=c,ec="none"))
    ax.text(x+w/2,0.5,l,ha="center",va="center",fontsize=12.5 if w>30 else 17,fontweight="bold",color="#0b0d12" if c==NV else TXT)
    x+=w
fig.text(0.06,0.86,"Where one dollar of Big Tech AI capex goes",fontsize=30,fontweight="bold")
fig.text(0.06,0.75,"Amazon, Google, Microsoft, Meta: ~$735B in 2026. Servers are ~60¢ of every dollar. Nvidia takes almost half of that.",fontsize=15,color=MUT)
fig.text(0.06,0.17,"Math: $48.7B Nvidia hyperscaler revenue per quarter ÷ ~$175B big-4 capex per quarter ≈ 25 to 30%. Server split from Alphabet's own disclosure.",fontsize=12,color=MUT)
fig.text(0.5,0.04,FOOT,ha="center",fontsize=10.5,color="#5d6273")
fig.savefig(f"{OUT}/01-capex-dollar.png",facecolor=BG); plt.close(fig)

# 2: NVDA DC split donut
fig=plt.figure(figsize=(14.56,8.2),dpi=100,facecolor=BG)
ax=fig.add_axes([0.04,0.10,0.5,0.66]); ax.set_aspect("equal")
vals=[48.7,40.3]; ax.pie(vals,colors=[NV,GOLD],startangle=90,counterclock=False,wedgeprops=dict(width=0.32,edgecolor=BG,linewidth=4))
ax.text(0,0.08,"$89B",ha="center",fontsize=34,fontweight="bold"); ax.text(0,-0.18,"data center\nrevenue, 1 quarter",ha="center",fontsize=13,color=MUT)
fig.text(0.05,0.88,"Half of Nvidia doesn't care what Amazon does",fontsize=30,fontweight="bold")
fig.text(0.05,0.81,"Nvidia data center revenue, quarter ended July 2026",fontsize=15,color=MUT)
fig.text(0.58,0.58,"$48.7B",fontsize=40,fontweight="bold",color=NV); fig.text(0.58,0.52,"Hyperscalers  (~55%)",fontsize=18)
fig.text(0.58,0.47,"Amazon, Google, Microsoft, Meta & co.\nThe ones the market spanked today.",fontsize=13,color=MUT)
fig.text(0.58,0.32,"$40.3B",fontsize=40,fontweight="bold",color=GOLD); fig.text(0.58,0.26,"Everyone else  (~45%)",fontsize=18)
fig.text(0.58,0.21,"AI clouds, sovereigns, enterprise.\nUp 138% from a year ago.",fontsize=13,color=MUT)
fig.text(0.5,0.03,"mphinance · NVDA Q2 FY27 (Motley Fool / NVDA CFO commentary) · not advice",ha="center",fontsize=10.5,color="#5d6273")
fig.savefig(f"{OUT}/02-nvda-split.png",facecolor=BG); plt.close(fig)

# 3: GIF - quarter capex fills, NVDA slice breaks off
frames=[]; N=40
cos=[("AMZN",77,"#FF9900"),("GOOGL",51,BLU),("MSFT",50,"#00A4EF"),("META",35,"#C6C9D2")]  # rough quarterly run-rate, sums ~207? scale label below
tot=sum(c[1] for c in cos)
for i in range(N+18):
    t=min(i/N,1.0); fig=plt.figure(figsize=(12,6.3),dpi=90,facecolor=BG)
    ax=fig.add_axes([0.07,0.30,0.86,0.25]); ax.set_axis_off(); ax.set_xlim(0,tot); ax.set_ylim(0,1)
    x=0
    for n,v,c in cos:
        w=v*min(1,t*1.0)
        ax.add_patch(FancyBboxPatch((x+0.4,0.08),max(w-0.8,0.01),0.84,boxstyle="square,pad=0",fc=c,ec="none",alpha=0.9))
        if t>0.25: ax.text(x+v/2,0.5,n,ha="center",va="center",fontsize=14,fontweight="bold",color="#0b0d12")
        x+=v
    fig.text(0.07,0.85,"One quarter of Big Tech AI capex",fontsize=24,fontweight="bold")
    fig.text(0.07,0.76,"AMZN $77B + GOOGL $51B (Q3 reported), MSFT ~$50B (guided), META ~$35B (last reported)",fontsize=13,color=MUT)
    if i>=N:
        k=min((i-N)/8,1.0)
        ax2=fig.add_axes([0.07,0.08,0.86*0.27,0.14]); ax2.set_axis_off(); ax2.set_xlim(0,1); ax2.set_ylim(0,1)
        ax2.add_patch(FancyBboxPatch((0,0.05),k,0.9,boxstyle="square,pad=0",fc=NV,ec="none"))
        if k>0.6: ax2.text(0.5,0.5,"~27¢ of every $1 → NVIDIA",ha="center",va="center",fontsize=13,fontweight="bold",color="#0b0d12")
    fig.text(0.5,0.015,"mphinance · company capex disclosures, NVDA filing · rough estimate",ha="center",fontsize=9,color="#5d6273")
    b=io.BytesIO(); fig.savefig(b,format="png",facecolor=BG); plt.close(fig); b.seek(0); frames.append(Image.open(b).convert("RGB"))
frames[0].save("/tmp/harvest/capex.gif",save_all=True,append_images=frames[1:],duration=[60]*N+[60]*8+[2400]+[60]*9,loop=0)
os.system(f'ffmpeg -loglevel error -y -i /tmp/harvest/capex.gif -vf "fps=15,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse" {OUT}/03-capex-flow.gif')
print(os.listdir(OUT))
