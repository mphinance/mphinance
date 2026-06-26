#!/usr/bin/env python3
"""
tt-ocr  -  turn Tastytrade screenshots into structured trade data.

Reads a folder (or single file) of Tastytrade screenshots, detects which of the
two repeating layouts each image uses, crops the rigid stat regions, OCRs them,
and writes structured JSON + a CSV that build.py can turn into a dashboard.

Two layouts (auto-detected):
  - "order_chains"  : the realized/working-PnL table (small, ~square image).
                      Header "<TICKER> Order Chains", a GAIN/LOSS/OPEN/CLSD
                      filter bar, and a summary row with Total P/L + Avg Trd Pr,
                      then per-chain blocks with a status (Open Pos / Closing /
                      Custom / Roll) and per-leg rows.
  - "curve"         : the Trade Analysis payoff view (wide ~1.6:1 image) with a
                      bottom stat bar: POP, EXT, P50, Delta, Theta, Vega, CVaR,
                      Max Profit, Max Loss, BP Eff. These are trade PLANS.

Design choices that matter:
  * REGION-BASED, not full-image OCR. The layouts are rigid, so we crop fixed
    relative regions and OCR only the few cells that matter. That is far more
    reliable for the numbers (ticker, total_pl, status) than dumping the whole
    image into tesseract.
  * NEVER FABRICATE. If the OCR engine is unavailable or a field reads empty /
    low confidence, the field is emitted as null and added to a "flags" list.
    A track record built on guessed P&L is worse than no track record.
  * Status awareness. An Order Chains "Total P/L" can be an OPEN (unrealized)
    mark, not a realized close. Only chains whose status reads as closed are
    written to the CSV with a realized_pl; open chains go in as open positions.

OCR engine:
  Uses pytesseract (the Tesseract binary must be installed) when available.
  Preprocessing: 3x upscale -> grayscale -> invert (UI text is light-on-dark)
  -> Otsu-ish threshold. If pytesseract/Tesseract is not installed, the tool
  still runs: it detects layouts, crops every region, saves the crops to a
  --debug dir, and emits nulls + a clear flag. The production read step is then
  either (a) install Tesseract, or (b) a vision-LLM pass over the saved crops
  (the crops isolate exactly one value each, which any vision model reads
  trivially). This file documents both.

Usage:
  python tt_ocr.py samples/                      # OCR a folder -> data/ocr_trades.csv + .json
  python tt_ocr.py samples/ADBE_order_chains.png # single file
  python tt_ocr.py samples/ --debug crops/       # also dump every cropped region
  python tt_ocr.py samples/ -o data/ocr_trades   # custom output stem

Free tool by Michael / Momentum Phinance. Built for Ryan LePiane
(LP Options Academy, https://ryanlepiane.substack.com). Generalizes to any
Tastytrade user.
"""

import os
import re
import sys
import csv
import json
import glob

try:
    from PIL import Image, ImageOps
except ImportError:
    print("ERROR: Pillow is required (pip install pillow).", file=sys.stderr)
    sys.exit(1)

# Optional OCR engine -------------------------------------------------------
try:
    import pytesseract
    # probe the actual binary, not just the wrapper
    pytesseract.get_tesseract_version()
    HAVE_OCR = True
except Exception:
    HAVE_OCR = False


# ---------------------------------------------------------------------------
# Region maps (relative coordinates: left, top, right, bottom as fractions)
# Calibrated against Ryan's real public screenshots (Tastytrade mobile/desktop
# Order Chains ~501x510; Curve ~1220x770). Verified: on ADBE_order_chains.png
# the 'total_pl' region isolates exactly "-653.00" and 'ticker' -> "ADBE".
# ---------------------------------------------------------------------------
ORDER_CHAINS_REGIONS = {
    "ticker":          (0.00, 0.000, 0.55, 0.065),   # "<TICKER> Order Chains"
    "filter_bar":      (0.00, 0.090, 1.00, 0.165),   # GAIN / LOSS / OPEN / CLSD
    "total_pl":        (0.55, 0.280, 0.80, 0.345),   # red/green summary number
    "avg_trade_price": (0.80, 0.280, 1.00, 0.345),
    # summary strategy label of the top chain (e.g. "Custom",
    # "Futures Option w/ a roll"). NOTE: the per-chain status words
    # (Open Pos / Closing / Custom / Roll) repeat lower down, once per chain
    # block, so reliable status needs the table parser or a CLSD-filtered shot.
    "summary_strategy": (0.00, 0.395, 0.45, 0.450),
    "chain_table":     (0.00, 0.450, 1.00, 1.000),   # per-leg rows + status live here
}

CURVE_REGIONS = {
    "ticker":     (0.00, 0.00, 0.30, 0.075),
    "stat_bar":   (0.00, 0.88, 1.00, 1.000),   # POP / Max Profit / Max Loss / BP Eff
    "legs_strip": (0.00, 0.07, 1.00, 0.180),   # BUY/SELL strike callouts
}

STATUS_WORDS = ("open pos", "closing", "custom", "roll", "closed")
CLOSED_HINTS = ("closing", "closed", "clsd")


# ---------------------------------------------------------------------------
# Layout detection
# ---------------------------------------------------------------------------
def detect_layout(im, ocr_text=None):
    """Return 'order_chains' or 'curve'.

    Primary signal: OCR text keywords ("Order Chains" / "POP" / "BP Eff").
    Geometric fallback (works with no OCR): Order Chains screenshots are small
    and near-square; Curve screenshots are wide (~1.6:1).
    """
    if ocr_text:
        t = ocr_text.lower()
        if "order chains" in t or ("total p/l" in t and "avg trd" in t):
            return "order_chains"
        if "bp eff" in t or ("max profit" in t and "pop" in t):
            return "curve"
    w, h = im.size
    aspect = w / h
    if w <= 760 and 0.85 <= aspect <= 1.20:
        return "order_chains"
    if aspect >= 1.35:
        return "curve"
    # last resort: smaller files are order chains
    return "order_chains" if w <= 760 else "curve"


# ---------------------------------------------------------------------------
# OCR helpers
# ---------------------------------------------------------------------------
def crop_rel(im, box):
    w, h = im.size
    l, t, r, b = box
    return im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))


def preprocess(cell, scale=3):
    """Upscale, grayscale, invert (light-on-dark -> dark-on-light), threshold."""
    cell = cell.convert("L")
    cell = cell.resize((cell.width * scale, cell.height * scale))
    cell = ImageOps.invert(cell)
    cell = ImageOps.autocontrast(cell)
    # simple threshold; tesseract handles the rest
    return cell.point(lambda p: 0 if p < 140 else 255)


def ocr_cell(cell, psm=7, whitelist=None):
    """OCR a single preprocessed cell. Returns '' when no engine."""
    if not HAVE_OCR:
        return ""
    cfg = f"--psm {psm}"
    if whitelist:
        cfg += f" -c tessedit_char_whitelist={whitelist}"
    try:
        return pytesseract.image_to_string(preprocess(cell), config=cfg).strip()
    except Exception:
        return ""


def parse_money(text):
    """Pull the first signed decimal from OCR text. None if not confident."""
    if not text:
        return None
    t = text.replace(",", "").replace(" ", "")
    neg = t.strip().startswith("(") and t.strip().endswith(")")
    m = re.search(r"-?\d+\.\d{1,2}", t)
    if not m:
        return None
    val = float(m.group(0))
    return -abs(val) if neg else val


def parse_ticker(text):
    if not text:
        return None
    # strip "Order Chains" and keep a leading futures-or-equity symbol
    text = re.sub(r"order\s*chains", "", text, flags=re.I).strip()
    m = re.search(r"/?[A-Z0-9]{1,6}", text.upper())
    return m.group(0) if m else None


# ---------------------------------------------------------------------------
# Per-layout extraction
# ---------------------------------------------------------------------------
def extract_order_chains(im, debug=None, name=""):
    regions = ORDER_CHAINS_REGIONS
    crops = {k: crop_rel(im, b) for k, b in regions.items()}
    if debug:
        for k, c in crops.items():
            c.save(os.path.join(debug, f"{name}_{k}.png"))

    flags = []
    ticker = parse_ticker(ocr_cell(crops["ticker"], psm=7))
    total_pl = parse_money(ocr_cell(crops["total_pl"], psm=7,
                                    whitelist="0123456789.-()"))
    avg_pr = parse_money(ocr_cell(crops["avg_trade_price"], psm=7,
                                  whitelist="0123456789.-()"))
    summary_strategy = (ocr_cell(crops["summary_strategy"], psm=7) or None)

    # Per-chain status (Open Pos / Closing / ...) lives in the stacked table,
    # and these screenshots often show multiple chains at once. We only assert
    # is_closed when the table parser finds an unambiguous closed/open status;
    # otherwise it stays null (never guessed).
    legs = _extract_legs(crops["chain_table"]) if HAVE_OCR else []
    status = None
    is_closed = None
    table_text = " ".join(str(v) for leg in legs for v in leg.values()).lower()
    found = [w for w in STATUS_WORDS if w in table_text]
    if found:
        status = found[0]
        if all(w in CLOSED_HINTS for w in found):
            is_closed = True
        elif all(w not in CLOSED_HINTS for w in found):
            is_closed = False  # all open -> unrealized mark, not a realized close

    if not HAVE_OCR:
        flags.append("NO_OCR_ENGINE: crops saved; values unread (install "
                     "Tesseract or run a vision-LLM pass over the crops)")
    for fld, val in (("ticker", ticker), ("total_pl", total_pl)):
        if val is None and HAVE_OCR:
            flags.append(f"LOW_CONFIDENCE:{fld}")
    if HAVE_OCR and is_closed is None:
        flags.append("STATUS_UNKNOWN: could not confirm open vs closed; "
                     "total_pl may be an unrealized mark")

    return {
        "layout": "order_chains",
        "ticker": ticker,
        "total_pl": total_pl,
        "avg_trade_price": avg_pr,
        "summary_strategy": summary_strategy,
        "chain_status": status,
        "is_closed": is_closed,
        # per-leg parsing from the rigid 6-column table is best-effort row
        # banding (computed above); empty when OCR is unavailable because
        # unread leg rows must never be invented.
        "legs": legs,
        "flags": flags,
    }


def _extract_legs(table_cell):
    """Best-effort per-leg rows. Columns (left->right):
       qty | expiry | dte | strike | C/P | action(BTC/STO/BTO).
       Returns [] if OCR unavailable; never fabricates."""
    if not HAVE_OCR:
        return []
    w, h = table_cell.size
    cols = {  # relative x bands within the table region
        "qty":    (0.00, 0.18),
        "expiry": (0.18, 0.40),
        "dte":    (0.40, 0.58),
        "strike": (0.58, 0.80),
        "right":  (0.80, 0.90),
        "action": (0.90, 1.00),
    }
    # detect row bands by scanning for the light highlighted cells; here we use
    # a fixed 3-row assumption per visible block as a pragmatic default and let
    # callers re-crop if needed. Rows that read empty are dropped (not guessed).
    legs = []
    row_h = 0.165  # ~ one leg row as a fraction of the table region
    y = 0.02
    while y + row_h <= 1.0 and len(legs) < 8:
        band = table_cell.crop((0, int(y * h), w, int((y + row_h) * h)))
        bw, bh = band.size
        leg = {}
        for col, (l, r) in cols.items():
            sub = band.crop((int(l * bw), 0, int(r * bw), bh))
            leg[col] = ocr_cell(sub, psm=7) or None
        if any(leg.values()):
            legs.append(leg)
        y += row_h
    return legs


def extract_curve(im, debug=None, name=""):
    regions = CURVE_REGIONS
    crops = {k: crop_rel(im, b) for k, b in regions.items()}
    if debug:
        for k, c in crops.items():
            c.save(os.path.join(debug, f"{name}_{k}.png"))
    flags = []
    ticker = parse_ticker(ocr_cell(crops["ticker"], psm=7))
    stat_text = ocr_cell(crops["stat_bar"], psm=6)
    if not HAVE_OCR:
        flags.append("NO_OCR_ENGINE: crops saved; stat bar unread")

    def grab(label):
        m = re.search(label + r"[^\d\-($]*([(\-]?\$?[\d,\.]+\)?)",
                      stat_text, re.I)
        return parse_money(m.group(1)) if m else None

    return {
        "layout": "curve",
        "ticker": ticker,
        "pop": grab("pop"),
        "max_profit": grab("max profit"),
        "max_loss": grab("max loss"),
        "bp_eff": grab("bp eff"),
        "stat_text_raw": stat_text or None,
        "flags": flags,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def process_image(path, debug=None):
    im = Image.open(path).convert("RGB")
    name = os.path.splitext(os.path.basename(path))[0]
    # quick full-image OCR only to aid layout detection (cheap, optional)
    hint = ""
    if HAVE_OCR:
        try:
            hint = pytesseract.image_to_string(im).strip()
        except Exception:
            hint = ""
    layout = detect_layout(im, hint)
    rec = (extract_order_chains if layout == "order_chains"
           else extract_curve)(im, debug=debug, name=name)
    rec["source"] = os.path.basename(path)
    return rec


def to_csv_rows(records):
    """Map OCR records onto the build.py trade schema. Closed chains -> a row
    with realized_pl; open chains/curves -> open-position rows (blank P/L)."""
    rows = []
    for r in records:
        if r["layout"] != "order_chains":
            continue
        realized = r["total_pl"] if r.get("is_closed") else None
        rows.append({
            "date_opened": "", "date_closed": "", "ticker": r.get("ticker") or "",
            "strategy": "", "debit_or_credit": "", "entry_price": "",
            "exit_price": "", "max_profit": "", "max_loss": "", "breakeven": "",
            "bp_used": "",
            "realized_pl": "" if realized is None else realized,
            "notes": "from tt-ocr; status=%s%s" % (
                r.get("chain_status"),
                "" if not r["flags"] else " | FLAGS: " + "; ".join(r["flags"])),
        })
    return rows


def main():
    args = [a for a in sys.argv[1:]]
    debug = None
    out_stem = None
    paths_in = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--debug":
            i += 1; debug = args[i]
        elif a in ("-o", "--out"):
            i += 1; out_stem = args[i]
        else:
            paths_in.append(a)
        i += 1

    if not paths_in:
        print(__doc__)
        sys.exit(0)

    here = os.path.dirname(os.path.abspath(__file__))
    if out_stem is None:
        out_stem = os.path.join(here, "data", "ocr_trades")
    if debug:
        os.makedirs(debug, exist_ok=True)

    files = []
    for p in paths_in:
        if os.path.isdir(p):
            for ext in ("*.png", "*.jpg", "*.jpeg"):
                files += glob.glob(os.path.join(p, ext))
        else:
            files.append(p)
    files = sorted(set(files))

    if not HAVE_OCR:
        print("!! Tesseract OCR engine NOT found. Running in crop+detect mode:")
        print("   layouts are detected and every region is cropped (use --debug")
        print("   to save them), but text values are emitted as null + flagged.")
        print("   Install with: apt-get install tesseract-ocr && pip install pytesseract")
        print()

    records = [process_image(f, debug=debug) for f in files]

    with open(out_stem + ".json", "w") as f:
        json.dump(records, f, indent=2)
    rows = to_csv_rows(records)
    cols = ["date_opened", "date_closed", "ticker", "strategy",
            "debit_or_credit", "entry_price", "exit_price", "max_profit",
            "max_loss", "breakeven", "bp_used", "realized_pl", "notes"]
    with open(out_stem + ".csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(rows)

    print(f"Processed {len(files)} image(s). OCR engine: "
          f"{'tesseract' if HAVE_OCR else 'NONE (crop-only)'}")
    for r in records:
        line = f"  {r['source']:28} -> {r['layout']:13}"
        if r["layout"] == "order_chains":
            line += f" ticker={r['ticker']} total_pl={r['total_pl']} status={r['chain_status']}"
        else:
            line += f" ticker={r['ticker']} max_loss={r.get('max_loss')}"
        if r["flags"]:
            line += "  [" + ", ".join(r["flags"]) + "]"
        print(line)
    print(f"Wrote {out_stem}.json and {out_stem}.csv ({len(rows)} chain rows)")


if __name__ == "__main__":
    main()
