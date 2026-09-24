#!/usr/bin/env python3
"""
Hero image generator for Substack drafts.

Takes one mascot pose from docs/substack/assets/mascot/ (each pose has a
blank chalkboard region baked in by the image model) and writes real,
crisp HTML/CSS text onto that chalkboard -- a stat, a formula, a one-liner
tied to the specific post -- instead of relying on the image model to
render text (it garbles anything more than a word or two).

Renders with headless Chromium so the output is pixel-exact, then crops to
1024x1024 to match the existing hero_image convention in docs/substack/.

Usage:
    python3 scripts/generate_hero.py \\
        --pose midnight_builder \\
        --chalk "Boolean filters -> EdgeScore" \\
        --out docs/substack/musings/2026-04-25_hero.png

    python3 scripts/generate_hero.py --list-poses
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MASCOT_DIR = REPO_ROOT / "docs" / "substack" / "assets" / "mascot"

# Chalkboard blank-rectangle position for each pose, as fractions of the
# 1024x1024 source image (left, top, width, height). Calibrated by eye
# against each generated pose -- adjust here if a render looks off.
DEFAULT_COORDS = {
    "calm_edge":       {"left": 0.68, "top": 0.09, "width": 0.26, "height": 0.09},
    "stressed_ego":    {"left": 0.06, "top": 0.17, "width": 0.14, "height": 0.09},
    "casino_dealer":   {"left": 0.14, "top": 0.19, "width": 0.62, "height": 0.10},
    "surfer":          {"left": 0.36, "top": 0.20, "width": 0.28, "height": 0.15},
    "ap_clerk":        {"left": 0.625,"top": 0.06, "width": 0.225,"height": 0.23},
    "data_detective":  {"left": 0.10, "top": 0.10, "width": 0.55, "height": 0.12},
    "midnight_builder":{"left": 0.685,"top": 0.115,"width": 0.245,"height": 0.075},
    "aisle_auditor":   {"left": 0.10, "top": 0.10, "width": 0.55, "height": 0.12},
    "circle_chair":    {"left": 0.685,"top": 0.185,"width": 0.24, "height": 0.11},
    "professor":       {"left": 0.10, "top": 0.25, "width": 0.23, "height": 0.28},
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ width:1024px; height:1024px; overflow:hidden; }}
  .stage {{ position:relative; width:1024px; height:1024px; }}
  .stage img {{ position:absolute; top:0; left:0; width:1024px; height:1024px; }}
  .chalk {{
    position:absolute;
    left:{left}px; top:{top}px; width:{width}px; height:{height}px;
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    text-align:center;
    color:#eef6f6;
    text-shadow: 0 0 3px rgba(255,255,255,0.25);
    line-height:1.12;
    transform:rotate(-1.2deg);
    padding:4px;
  }}
  .chalk-plain {{
    font-family:'Kalam', cursive;
    font-weight:700;
    font-size:{font_size}px;
  }}
  .chalk-title {{
    font-family:'Kalam', cursive;
    font-weight:700;
    font-size:{title_size}px;
  }}
  .chalk-subtitle {{
    margin-top:6px;
    font-family:'Kalam', cursive;
    font-weight:400;
    color:#f0b400;
    font-size:{subtitle_size}px;
    letter-spacing:0.5px;
  }}
</style></head>
<body>
  <div class="stage">
    <img src="{img_path}">
    <div class="chalk">{chalk_inner}</div>
  </div>
</body></html>
"""


def list_poses():
    for f in sorted(MASCOT_DIR.glob("mascot_*.png")):
        name = f.stem.replace("mascot_", "")
        c = DEFAULT_COORDS.get(name)
        flag = "" if c and c["width"] > 0 else "  (no chalkboard calibrated)"
        print(f"  {name}{flag}")


def render(pose: str, text: str, out_path: Path, font_size: int | None,
           title: str | None = None, subtitle: str | None = None):
    img_path = MASCOT_DIR / f"mascot_{pose}.png"
    if not img_path.exists():
        sys.exit(f"No such pose: {pose} (looked for {img_path}). Use --list-poses.")

    coords = DEFAULT_COORDS.get(pose)
    if not coords or coords["width"] == 0:
        sys.exit(f"Pose '{pose}' has no chalkboard region calibrated in hero_chalk_coords "
                  f"(see DEFAULT_COORDS in this script) -- pick a different pose or add coords.")

    left = round(coords["left"] * 1024)
    top = round(coords["top"] * 1024)
    width = round(coords["width"] * 1024)
    height = round(coords["height"] * 1024)
    fs = font_size or max(16, min(34, int(height * 0.34)))

    # Title/subtitle live ON the chalkboard itself (that's what the prop is for),
    # not a separate banner over the mascot. Two stacked chalk lines share the
    # board's height, so both need to shrink to fit -- there's no room to also
    # keep an unrelated --chalk stat once --title is used.
    if title:
        title_size = font_size or (
            28 if len(title) <= 24 else (22 if len(title) <= 40 else 17)
        )
        subtitle_size = max(12, int(title_size * 0.5))
        chalk_inner = f'<div class="chalk-title">{title}</div>'
        if subtitle:
            chalk_inner += f'<div class="chalk-subtitle">{subtitle}</div>'
    else:
        title_size = subtitle_size = 0
        chalk_inner = f'<div class="chalk-plain">{text}</div>'

    html = HTML_TEMPLATE.format(
        img_path=img_path.resolve(),
        left=left, top=top, width=width, height=height,
        font_size=fs, title_size=title_size, subtitle_size=subtitle_size,
        chalk_inner=chalk_inner,
    )
    tmp_html = Path("/tmp") / "phinance_hero_render.html"
    tmp_html.write_text(html)

    tmp_shot = Path("/tmp") / "phinance_hero_render_shot.png"
    subprocess.run([
        "chromium", "--headless", "--disable-gpu", "--no-sandbox",
        "--window-size=1024,1024", f"--screenshot={tmp_shot}",
        # Without this the shot fires before the Kalam webfont loads and the
        # chalk falls back to a default serif.
        "--virtual-time-budget=8000",
        "--hide-scrollbars", f"file://{tmp_html}",
    ], check=True, capture_output=True)

    from PIL import Image
    im = Image.open(tmp_shot).crop((0, 0, 1024, 1024))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path)
    print(f"saved {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pose", help="mascot pose name, e.g. midnight_builder (see --list-poses)")
    ap.add_argument("--chalk", help="short text to write on the chalkboard (a stat, formula, one-liner) -- ignored if --title is given")
    ap.add_argument("--out", help="output PNG path, 1024x1024")
    ap.add_argument("--font-size", type=int, default=None)
    ap.add_argument("--title", help="post title, written onto the chalkboard itself (the mascot's prop is the cover-image real estate, not a separate banner)")
    ap.add_argument("--subtitle", help="category-mix subtitle line, written on the chalkboard under --title, smaller")
    ap.add_argument("--list-poses", action="store_true")
    args = ap.parse_args()

    if args.list_poses:
        list_poses()
        return

    if not (args.pose and args.out and (args.chalk or args.title)):
        ap.error("--pose, --out, and one of --chalk/--title are required (or use --list-poses)")

    render(args.pose, args.chalk, Path(args.out), args.font_size, args.title, args.subtitle)


if __name__ == "__main__":
    main()
