import json, math, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Polygon, Ellipse, FancyArrowPatch
import matplotlib.patheffects as pe

D = sys.argv[1]
st = json.load(open(f"{D}/st500.json", encoding="latin-1"))
lakes = json.load(open(f"{D}/lakes.json"))
BG, LAND, NEIGH, WATER = "#0b0f14", "#1c232c", "#12171d", "#0d2233"
GOLD, INK, DIM = "#e8b64c", "#e9edf2", "#8a96a3"

fig, ax = plt.subplots(figsize=(12, 12.2), dpi=160)
fig.patch.set_facecolor(BG); ax.set_facecolor(WATER)
ax.set_xlim(-93.3, -86.3); ax.set_ylim(41.85, 47.35)
ax.set_aspect(1 / math.cos(math.radians(44.7))); ax.axis("off")

def rings(geom):
    cs = geom["coordinates"]
    polys = cs if geom["type"] == "MultiPolygon" else [cs]
    return [p[0] for p in polys]

def ring_path(rs):
    verts, codes = [], []
    for r in rs:
        verts += r; codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 2) + [Path.CLOSEPOLY]
    return Path(verts, codes)

wi_path = None
for f in st["features"]:
    n = f["properties"]["NAME"]
    if n in ("Wisconsin", "Michigan", "Minnesota", "Illinois", "Iowa"):
        p = ring_path(rings(f["geometry"]))
        ax.add_patch(PathPatch(p, fc=LAND if n == "Wisconsin" else NEIGH,
                               ec="#3a4652" if n == "Wisconsin" else "#232b33", lw=1.2 if n == "Wisconsin" else 0.6, zorder=1))
        if n == "Wisconsin": wi_path = p
for f in lakes["features"]:
    g = f["geometry"]
    xs = [c[0] for r in rings(g) for c in r]; ys = [c[1] for r in rings(g) for c in r]
    if max(xs) < -94 or min(xs) > -86 or max(ys) < 42 or min(ys) > 47.5: continue
    ax.add_patch(PathPatch(ring_path(rings(g)), fc=WATER, ec="#1d3d55", lw=0.5, zorder=2))
clip = PathPatch(wi_path, transform=ax.transData, fc="none", ec="none")
ax.add_patch(clip)

def halo(t, w=3): t.set_path_effects([pe.withStroke(linewidth=w, foreground=BG)]); return t
def label(x, y, s, **kw):
    kw.setdefault("color", INK); kw.setdefault("fontsize", 10); kw.setdefault("zorder", 9)
    return halo(ax.text(x, y, s, **kw))

# Driftless Area (approx, clipped to state)
drift = Polygon([(-93.5, 45.0), (-92.2, 44.9), (-91.6, 44.95), (-91.0, 44.85), (-90.5, 44.55), (-90.15, 44.2),
                 (-89.95, 43.85), (-89.75, 43.55), (-89.7, 43.2), (-89.6, 42.9), (-89.45, 42.4), (-93.5, 42.4)],
                fc="#6b4f2a", alpha=0.55, ec="none", zorder=3)
ax.add_patch(drift); drift.set_clip_path(clip)
label(-90.95, 43.35, "THE DRIFTLESS AREA", fontsize=13, weight="bold", color="#f0c987", ha="center")
label(-90.95, 43.17, "the ice missed it\nold sandstone & limestone bluffs, deep coulees", fontsize=8.5, color="#d8c3a0", ha="center", va="top")

# Central Sands / Glacial Lake Wisconsin
sands = Ellipse((-89.95, 44.12), 1.15, 0.75, angle=-20, fc="#c9b37a", alpha=0.35, ec="#c9b37a", ls=":", lw=1, zorder=4)
ax.add_patch(sands); sands.set_clip_path(clip)
label(-89.95, 44.12, "CENTRAL SANDS\nold bed of Glacial\nLake Wisconsin", fontsize=8.5, color="#f1e2b8", ha="center", va="center", weight="bold")

# Tension Zone (approx S-curve band)
tz = [(-92.85, 45.6), (-92.2, 45.3), (-91.45, 44.98), (-90.75, 44.62), (-90.15, 44.4), (-89.55, 44.25),
      (-89.05, 44.38), (-88.6, 44.74), (-88.15, 44.98), (-87.7, 45.12)]
x, y = zip(*tz)
band, = ax.plot(x, y, color="#4fbf8f", lw=26, alpha=0.28, solid_capstyle="round", zorder=5)
core, = ax.plot(x, y, color="#4fbf8f", lw=1.6, ls=(0, (6, 3)), zorder=6)
band.set_clip_path(clip); core.set_clip_path(clip)
label(-91.0, 45.95, "NORTH: spruce bogs, hemlock, white pine,\nacid sandy soils, the Northwoods", fontsize=9, color="#9fe3c4", ha="center")
label(-89.55, 43.78, "SOUTH: oak savanna, prairie,\nhardwoods, long growing season", fontsize=9, color="#9fe3c4", ha="center")
label(-91.75, 45.38, "CURTIS'S TENSION ZONE", fontsize=11.5, weight="bold", color="#6fe0ad", rotation=-22, ha="center")

# 45th parallel
ax.plot([-93.3, -86.3], [45, 45], color=GOLD, lw=1, ls=(0, (2, 3)), alpha=0.8, zorder=6)
label(-93.2, 44.95, "45°N", fontsize=9, color=GOLD, va="top")
ax.plot(-90.0, 45.0, marker="*", ms=14, color=GOLD, mec=BG, zorder=10)
label(-89.88, 45.08, "45°N × 90°W marker (Poniatowski)\nhalfway from equator to pole", fontsize=8, color=GOLD, va="bottom")

# Ice lobes
def lobe(p0, p1, name, lx, ly, **kw):
    a = FancyArrowPatch(p0, p1, arrowstyle="simple,head_length=1.6,head_width=1.4,tail_width=0.55",
                        mutation_scale=14, fc="#bfe6ff", ec="#5aa9d6", alpha=0.85, lw=0.8, zorder=7,
                        connectionstyle=kw.pop("cs", "arc3,rad=0"))
    ax.add_patch(a); label(lx, ly, name, fontsize=9, color="#bfe6ff", style="italic", **kw)
lobe((-87.95, 45.0), (-89.05, 43.35), "Green Bay Lobe", -89.35, 44.62, ha="center", cs="arc3,rad=0.15")
lobe((-87.25, 44.35), (-87.55, 42.75), "Lake Michigan\nLobe", -86.85, 43.75, ha="center")
lobe((-90.9, 46.45), (-91.15, 45.75), "Chippewa Lobe", -91.35, 46.5, ha="center")
lobe((-92.05, 46.95), (-92.55, 46.2), "Superior Lobe", -92.55, 47.12, ha="center")
lobe((-89.55, 46.2), (-89.6, 45.35), "Wisconsin Valley\n/ Langlade Lobes", -88.85, 45.9, ha="center")

# Niagara Escarpment
esc = [(-86.95, 45.28), (-87.35, 44.88), (-87.75, 44.55), (-88.05, 44.38), (-88.27, 44.17), (-88.33, 43.95), (-88.36, 43.7), (-88.33, 43.45)]
x, y = zip(*esc)
ax.plot(x, y, color="#d98b5f", lw=2.2, zorder=6, path_effects=[pe.Stroke(linewidth=4, foreground=BG), pe.Normal()])
label(-87.1, 45.62, "NIAGARA ESCARPMENT\nsame rock ledge as Niagara Falls", fontsize=8.5, color="#f0a87e", ha="center")

# Kettle Moraine
km = [(-88.06, 43.82), (-88.12, 43.68), (-88.23, 43.52), (-88.3, 43.36), (-88.33, 43.24), (-88.4, 43.07), (-88.47, 42.9), (-88.7, 42.8)]
x, y = zip(*km)
ax.plot(x, y, color="#c792ea", lw=4, zorder=7, solid_capstyle="round", path_effects=[pe.Stroke(linewidth=6.5, foreground=BG), pe.Normal()])
label(-88.05, 42.62, "KETTLE MORAINE\nwhere the Green Bay and Lake Michigan\nlobes met and dumped their gravel", fontsize=8.5, color="#dcb8f5", ha="left")

# Menominee Forest (approx county block) + Wolf River
men = Polygon([(-88.98, 45.12), (-88.43, 45.12), (-88.43, 44.86), (-88.98, 44.86)], fc="#0f5a32", alpha=0.75, ec="#4fbf8f", lw=1, zorder=6)
ax.add_patch(men)
label(-88.3, 45.32, "MENOMINEE FOREST\nthe res: one solid block of\nforest, visible from orbit", fontsize=8.5, color="#9fe3c4", ha="left", weight="bold")
wolf = [(-88.98, 45.5), (-88.86, 45.35), (-88.74, 45.18), (-88.68, 45.02), (-88.64, 44.9), (-88.6, 44.78)]
x, y = zip(*wolf)
ax.plot(x, y, color="#5aa9d6", lw=1.8, zorder=7)
label(-89.05, 45.5, "Wolf River", fontsize=8, color="#a9cfe8", style="italic", ha="right")

# Route
route = [(-87.91, 43.04), (-88.33, 43.24), (-88.45, 43.77), (-88.54, 44.02), (-88.42, 44.26), (-88.02, 44.52),
         (-88.45, 44.81), (-88.62, 45.0), (-88.86, 45.38)]
path = [route[0], route[1], (-88.36, 43.5), route[2], route[3], route[4], route[5], (-88.3, 44.68), route[6],
        (-88.52, 44.9), route[7], (-88.68, 45.0), (-88.74, 45.18), route[8]]
x, y = zip(*path)
ax.plot(x, y, color=GOLD, lw=3.2, zorder=8, path_effects=[pe.Stroke(linewidth=6, foreground=BG), pe.Normal()])
ax.annotate("", xy=(-88.95, 45.5), xytext=route[8], arrowprops=dict(arrowstyle="-|>", color=GOLD, lw=3), zorder=8)
for i, (rx, ry) in enumerate(route):
    ax.plot(rx, ry, "o", ms=13, color=GOLD, mec=BG, mew=1.5, zorder=11)
    ax.text(rx, ry, str(i + 1), color=BG, fontsize=7.5, weight="bold", ha="center", va="center", zorder=12)

# Cities
cities = {"Milwaukee": (-87.91, 43.04, 0.1, -0.08), "Green Bay": (-88.02, 44.52, 0.12, -0.06), "Madison": (-89.4, 43.07, 0, -0.14),
          "Wausau": (-89.63, 44.96, -0.08, -0.13), "Stevens Point": (-89.57, 44.52, 0.1, 0.03), "Eau Claire": (-91.5, 44.81, 0, 0.1),
          "La Crosse": (-91.24, 43.8, 0.1, 0), "Fond du Lac": (-88.45, 43.77, -0.1, -0.14), "Oshkosh": (-88.54, 44.02, -0.12, 0),
          "Appleton": (-88.42, 44.26, -0.12, 0.02), "Sheboygan": (-87.71, 43.75, 0.09, 0), "Baraboo": (-89.74, 43.47, 0.1, -0.03),
          "Superior": (-92.1, 46.72, 0.08, -0.12)}
for n, (cx, cy, dx, dy) in cities.items():
    if n not in ("Milwaukee", "Green Bay", "Fond du Lac", "Oshkosh", "Appleton"):
        ax.plot(cx, cy, "o", ms=4, color=INK, mec=BG, zorder=10)
    label(cx + dx, cy + dy, n, fontsize=9.5 if n in ("Milwaukee", "Green Bay") else 8.5,
          weight="bold" if n in ("Milwaukee", "Green Bay") else "normal",
          ha="right" if dx < 0 else ("center" if dx == 0 else "left"), va="center")
label(-88.6, 44.1, "Lake\nWinnebago", fontsize=7.5, color="#7fb3d5", ha="center", style="italic", alpha=0)

# Lake effect note
a = FancyArrowPatch((-87.75, 42.28), (-86.45, 42.28), arrowstyle="-|>", mutation_scale=16, color="#7fb3d5", lw=1.5, zorder=8)
ax.add_patch(a)
label(-86.4, 42.15, "Westerly winds push most lake-effect\nsnow onto MICHIGAN's shore, not ours", fontsize=8, color="#a9cfe8", ha="right", va="top")
label(-86.85, 43.15, "LAKE\nMICHIGAN", fontsize=11, color="#4f7ea0", ha="center", weight="bold")
label(-88.6, 46.95, "LAKE SUPERIOR", fontsize=11, color="#4f7ea0", ha="center", weight="bold")

# Sun box
label(-93.2, 42.55, "THE SUN LINE: at 45°N the equinox noon sun sits 45° up (Sept 22-23).\n"
      "Lower sun = the same light smeared over more ground, so each square foot gets less.\n"
      "It fades a little every day. There is no switch that flips at 45°.",
      fontsize=8.5, color=GOLD, ha="left", va="center",
      bbox=dict(boxstyle="round,pad=0.5", fc="#151a21", ec=GOLD, lw=0.8))

# Title + route legend
fig.text(0.06, 0.965, "The Scars Under Wisconsin", color=INK, fontsize=26, weight="bold", ha="left", va="top")
fig.text(0.06, 0.93, "Ice, an invisible forest line, and the drive from Milwaukee to the Northwoods",
         color=DIM, fontsize=12.5, ha="left", va="top")
stops = ("THE DRIVE\n1  Milwaukee\n2  Holy Hill (the balloon)\n3  Fond du Lac\n4  Oshkosh\n5  Appleton\n"
         "6  Green Bay\n7  Cecil, Shawano Lake\n8  R to M, right on 45°N\n9  WI-55 up the Wolf. Deer.")
fig.text(0.70, 0.86, stops, color=GOLD, fontsize=9.5, ha="left", va="top", family="DejaVu Sans Mono",
         bbox=dict(boxstyle="round,pad=0.6", fc="#151a21", ec="#3a4652", lw=0.8))
fig.text(0.06, 0.03, "Boundaries hand-traced and approximate. Lobe arrows show ice flow direction during the last glaciation.",
         color=DIM, fontsize=8.5, ha="left")
out = sys.argv[2]
fig.savefig(out, facecolor=BG, bbox_inches="tight", pad_inches=0.3)
print(out)
