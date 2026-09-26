"""Render a Vero segment into a dark-theme, Bloomberg-terminal candlestick PNG.

Turns a PatternPulse / Vero segment (the setup candles, and optionally the hidden
continuation that played out) into a publish-ready chart image. Same look and libs
as the mphinance Gamma Map / kline_chart.py (klinecharts 9.8.10 + headless
Playwright screenshot) so the output drops straight into a Substack draft.

Two modes:
  * teaser  (default)     -> shows only the setup; masks the future. The
                            "Up or Down? You've got 3 seconds" social card.
  * --reveal              -> appends the hidden continuation behind a divider,
                            shades the reveal zone, and labels the outcome.
                            The teaching card ("here's the bull flag, here's
                            what it did").

Input is a Vero segment JSON (a SegmentResponse or SegmentFullResponse dump, or
the /segments/{id}/full API response). Fetch one and pipe it in, or hand it a file:

  # from a saved export
  python tools/segment_chart.py seg.json --reveal --out /tmp

  # straight from the API (already-played segment)
  curl -s -H "Authorization: Bearer $TOK" \
    https://api.vero.app/segments/<id>/full > seg.json
  python tools/segment_chart.py seg.json --reveal

The segment JSON shape it understands (extra keys are ignored):
  {
    "id": "...", "symbol": "AAPL" | "HIDDEN", "resolution": "5m",
    "lookback_candles": [{"t","o","h","l","c","v"}, ...],   # optional context
    "visible_candles":  [{"t","o","h","l","c","v"}, ...],   # the setup
    "hidden_candles":   [{"t","o","h","l","c","v"}, ...],   # the reveal (--reveal)
    "direction": "UP" | "DOWN",        # optional, for the outcome label
    "net_move_pct": 1.23,               # optional, for the outcome label
    "primary_tag": "chart:bull_flag",   # optional, drawn as a pattern chip
    "tags": ["chart:bull_flag", ...]
  }
"""
import argparse
import json
import sys
from pathlib import Path

# Vero namespaced tags -> human labels for the pattern chip.
TAG_LABELS = {
    "candle:doji": "DOJI", "candle:spinning_top": "SPINNING TOP",
    "candle:hammer": "HAMMER", "candle:shooting_star": "SHOOTING STAR",
    "candle:engulfing_bull": "BULL ENGULFING", "candle:engulfing_bear": "BEAR ENGULFING",
    "candle:morning_star": "MORNING STAR", "candle:evening_star": "EVENING STAR",
    "candle:marubozu_bull": "BULL MARUBOZU", "candle:marubozu_bear": "BEAR MARUBOZU",
    "chart:bull_flag": "BULL FLAG", "chart:bear_flag": "BEAR FLAG",
    "chart:ascending_triangle": "ASCENDING TRIANGLE",
    "chart:descending_triangle": "DESCENDING TRIANGLE",
    "chart:symmetrical_triangle": "SYMMETRICAL TRIANGLE",
    "chart:double_top": "DOUBLE TOP", "chart:double_bottom": "DOUBLE BOTTOM",
    "chart:wedge": "WEDGE", "chart:head_and_shoulders": "HEAD & SHOULDERS",
    "chart:inv_head_and_shoulders": "INV HEAD & SHOULDERS",
    "chart:channel_up": "CHANNEL UP", "chart:channel_down": "CHANNEL DOWN",
    "chart:cup_and_handle": "CUP & HANDLE",
}


def tag_label(tag):
    if not tag:
        return ""
    return TAG_LABELS.get(tag, tag.split(":", 1)[-1].replace("_", " ").upper())


def _candles(rows):
    """Normalize [{t,o,h,l,c,v}, ...] -> klinecharts rows."""
    out = []
    for r in rows or []:
        out.append({
            "t": r["t"], "o": float(r["o"]), "h": float(r["h"]),
            "l": float(r["l"]), "c": float(r["c"]), "v": float(r.get("v", 0)),
        })
    return out


VENDOR = Path(__file__).resolve().parent / "vendor" / "klinecharts-9.8.10.min.js"

# The chart lib is vendored (tools/vendor) and inlined at build time so rendering
# has zero network dependency — it works in CI, web sessions, and offline, unlike
# a CDN <script> tag. Fonts fall back to the system monospace stack for the same reason.
HTML = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<script>__KLINE__</script>
<style>
  html,body{margin:0;background:#0a0a0e;color:#e6e6ee;
    font-family:'JetBrains Mono','Share Tech Mono',ui-monospace,'DejaVu Sans Mono',monospace}
  .wrap{width:1200px;padding:18px}
  .symrow{display:flex;align-items:baseline;gap:12px;margin-bottom:4px}
  .sym{font-family:'Share Tech Mono',monospace;font-size:30px;letter-spacing:1px}
  .meta{font-size:14px;color:#8a8aa0}
  .chip{font-family:'Share Tech Mono',monospace;font-size:13px;letter-spacing:1px;
        color:#0a0a0e;background:#00d68f;padding:3px 10px;border-radius:4px}
  .out{margin-left:auto;font-size:20px}
  .out.pos{color:#00d68f} .out.neg{color:#ff4d6d} .out.q{color:#f0b400}
  #chart{width:1164px;height:560px;background:#101018;border:1px solid #1c1c28;border-radius:10px;margin-top:10px}
  .tag{font-family:'Share Tech Mono',monospace;color:#8a8aa0;font-size:12px;margin-top:8px;letter-spacing:1px}
</style></head><body><div class="wrap">
  <div class="symrow">
    <div class="sym" id="sym"></div>
    <div class="meta" id="meta"></div>
    <div class="chip" id="chip" style="display:none"></div>
    <div class="out" id="out"></div>
  </div>
  <div id="chart"></div>
  <div class="tag" id="foot"></div>
</div>
<script>
const CFG = __CFG__;
const rows = CFG.candles.map(r=>({timestamp:Date.parse(r.t),
  open:r.o,high:r.h,low:r.l,close:r.c,volume:r.v}));

document.getElementById('sym').textContent = CFG.sym;
document.getElementById('meta').textContent = CFG.meta || '';
const chipEl = document.getElementById('chip');
if(CFG.chip){ chipEl.textContent = CFG.chip; chipEl.style.display=''; }
const outEl = document.getElementById('out');
if(CFG.reveal && CFG.outcome){
  outEl.textContent = CFG.outcome.text;
  outEl.className = 'out ' + CFG.outcome.cls;
} else if(!CFG.reveal){
  outEl.textContent = 'UP or DOWN?'; outEl.className = 'out q';
}
document.getElementById('foot').textContent = CFG.foot || '';

const chart = klinecharts.init('chart',{styles:{
  grid:{horizontal:{color:'#16161f'},vertical:{color:'#16161f'}},
  candle:{type:'candle_solid',
    bar:{upColor:'#00d68f',downColor:'#ff4d6d',upBorderColor:'#00d68f',downBorderColor:'#ff4d6d',upWickColor:'#00d68f',downWickColor:'#ff4d6d'},
    priceMark:{last:{show:false},high:{color:'#8a8aa0'},low:{color:'#8a8aa0'}},
    tooltip:{showRule:'none'}},
  xAxis:{axisLine:{color:'#1c1c28'},tickLine:{color:'#1c1c28'},tickText:{color:'#8a8aa0'}},
  yAxis:{axisLine:{color:'#1c1c28'},tickLine:{color:'#1c1c28'},tickText:{color:'#8a8aa0'}},
  indicator:{lastValueMark:{show:false},tooltip:{showRule:'none'}}
}});
chart.applyNewData(rows);
if(CFG.show_ema){ chart.createIndicator({name:'EMA',calcParams:[8,21]},true,{id:'candle_pane'}); }
chart.createIndicator('VOL');
// Fit all candles across the full chart width (no dead space, no scroll-off).
const AXIS_W = 62, PAD = 16;
const space = Math.max(3, (1164 - AXIS_W - PAD) / Math.max(rows.length, 1));
chart.setBarSpace(space);
chart.setOffsetRightDistance(PAD);

// Vertical divider + shaded reveal zone at the setup/continuation boundary.
klinecharts.registerOverlay({name:'reveal_edge',totalStep:1,lock:true,
  needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({coordinates,bounding})=>{
    if(!coordinates[0])return[]; const x=coordinates[0].x;
    return [
      {type:'rect',ignoreEvent:true,
       attrs:{x:x,y:0,width:Math.max(0,bounding.width-x),height:bounding.height},
       styles:{style:'fill',color:'rgba(240,180,0,0.06)'}},
      {type:'line',ignoreEvent:true,
       attrs:{coordinates:[{x,y:0},{x,y:bounding.height}]},
       styles:{color:'#f0b400',size:1.2,style:'dashed',dashedValue:[6,5]}},
      {type:'text',ignoreEvent:true,attrs:{x:x+6,y:8,text:'REVEAL'},
       styles:{color:'#f0b400',size:11.5,family:"'Share Tech Mono',monospace",
         backgroundColor:'#0a0a0ecc',paddingLeft:5,paddingRight:5,paddingTop:2,paddingBottom:2}}];
  }});
if(CFG.reveal && CFG.boundary_ts){
  chart.createOverlay({name:'reveal_edge',points:[{timestamp:CFG.boundary_ts}]});
}
window.__ready=true;
</script></body></html>"""


def build(seg, reveal, footer, out_dir, name):
    lookback = _candles(seg.get("lookback_candles"))
    visible = _candles(seg.get("visible_candles"))
    hidden = _candles(seg.get("hidden_candles"))

    setup = lookback + visible
    if not setup:
        raise SystemExit("segment has no lookback/visible candles to render")

    candles = setup + (hidden if reveal else [])
    boundary_ts = None
    if reveal and hidden:
        from datetime import datetime
        boundary_ts = int(datetime.fromisoformat(
            hidden[0]["t"].replace("Z", "+00:00")).timestamp() * 1000)

    sym = seg.get("symbol") or "HIDDEN"
    res = seg.get("resolution", "")
    meta = f"{res}  ·  {len(visible)} setup" + (f" + {len(hidden)} reveal" if reveal and hidden else "")

    outcome = None
    if reveal:
        direction = seg.get("direction")
        pct = seg.get("net_move_pct")
        if direction or pct is not None:
            arrow = "▲" if (direction == "UP" or (pct or 0) >= 0) else "▼"
            cls = "pos" if (direction == "UP" or (pct or 0) >= 0) else "neg"
            pct_txt = f"{pct:+.2f}%" if pct is not None else ""
            outcome = {"text": f"{arrow} {direction or ''} {pct_txt}".strip(), "cls": cls}

    cfg = {
        "sym": sym, "meta": meta,
        # The pattern chip telegraphs the answer, so it only shows on the reveal
        # card — never on the "call it" teaser.
        "chip": tag_label(seg.get("primary_tag")) if reveal else "",
        "candles": candles,
        "reveal": bool(reveal),
        "boundary_ts": boundary_ts,
        "outcome": outcome,
        "show_ema": len(candles) >= 21,
        "foot": footer,
    }
    if not VENDOR.exists():
        raise SystemExit(f"vendored chart lib missing: {VENDOR}")
    kline_js = VENDOR.read_text()
    # Inject the library first (plain replace, not .format/%), then the config.
    html = HTML.replace("__KLINE__", kline_js).replace("__CFG__", json.dumps(cfg))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    htmlp = out / f"{name}.html"
    htmlp.write_text(html)
    return htmlp


def shoot(htmlp, out_dir, name):
    import os
    from playwright.sync_api import sync_playwright
    png = Path(out_dir) / f"{name}.png"
    # Honor a pinned browser binary when Playwright's bundled build doesn't match
    # the pre-installed one (e.g. PW_CHROMIUM_PATH=/opt/pw-browsers/chromium-*/chrome-linux/chrome).
    exe = os.environ.get("PW_CHROMIUM_PATH")
    launch_kw = {"executable_path": exe} if exe else {}
    with sync_playwright() as p:
        b = p.chromium.launch(**launch_kw)
        pg = b.new_page(viewport={"width": 1240, "height": 720}, device_scale_factor=2)
        pg.goto(f"file://{htmlp}")
        pg.wait_for_function("window.__ready===true", timeout=15000)
        pg.wait_for_timeout(1200)
        pg.locator(".wrap").screenshot(path=str(png))
        b.close()
    return png


def main():
    ap = argparse.ArgumentParser(description="Render a Vero segment to a dark-theme PNG.")
    ap.add_argument("segment", help="path to a Vero segment JSON, or '-' for stdin")
    ap.add_argument("--reveal", action="store_true",
                    help="append the hidden continuation + outcome (teaching card)")
    ap.add_argument("--footer", default="VERO · See the signal.",
                    help="footer caption (brand line)")
    ap.add_argument("--out", default="/tmp/vero", help="output directory")
    ap.add_argument("--name", default=None, help="output basename (default: segment id/symbol)")
    ap.add_argument("--html-only", action="store_true",
                    help="write the HTML but skip the Playwright screenshot")
    a = ap.parse_args()

    raw = sys.stdin.read() if a.segment == "-" else Path(a.segment).read_text()
    seg = json.loads(raw)

    name = a.name or seg.get("id") or seg.get("symbol") or "segment"
    name = str(name).replace("/", "_").replace(":", "_")

    htmlp = build(seg, a.reveal, a.footer, a.out, name)
    if a.html_only:
        print(f"{name}\t{htmlp}")
        return
    pngp = shoot(htmlp, a.out, name)
    print(f"{name}\t{pngp}")


if __name__ == "__main__":
    main()
