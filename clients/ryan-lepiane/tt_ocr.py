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

# The "spreadsheet" layout: Ryan's own light-background open-book / risk panel
# (Google-Sheets style). Columns are segmented dynamically from the gridlines
# (see detect_gridlines), so this is just the expected order + meaning.
SPREADSHEET_COLUMNS = [
    "trade_description", "credit_rcvd", "debit_paid", "max_profit", "max_loss",
    "bp_usd", "bp_pct", "position_type", "risk_type", "date_opened",
]


# ---------------------------------------------------------------------------
# Layout detection
# ---------------------------------------------------------------------------
def mean_brightness(im, sample=64):
    """Cheap average brightness (0-255) over a downsampled grayscale copy."""
    g = im.convert("L").resize((sample, sample))
    px = list(g.getdata())
    return sum(px) / len(px)


def detect_layout(im, ocr_text=None):
    """Return 'order_chains', 'curve', or 'spreadsheet'.

    Primary signal: OCR text keywords. Geometric/brightness fallback works with
    no OCR at all:
      - spreadsheet : light background (mean brightness high) + wide. Ryan's
                      open-book sheet is dark-text-on-white with gridlines.
      - order_chains: small, near-square, dark background.
      - curve       : wide ~1.6:1, dark background.
    """
    if ocr_text:
        t = ocr_text.lower()
        if "trade description" in t and "date opened" in t:
            return "spreadsheet"
        if "order chains" in t or ("total p/l" in t and "avg trd" in t):
            return "order_chains"
        if "bp eff" in t or ("max profit" in t and "pop" in t):
            return "curve"
    w, h = im.size
    aspect = w / h
    # The tastytrade trade UIs are dark; Ryan's sheet is light.
    if mean_brightness(im) > 180:
        return "spreadsheet"
    if w <= 760 and 0.85 <= aspect <= 1.20:
        return "order_chains"
    if aspect >= 1.35:
        return "curve"
    return "order_chains" if w <= 760 else "curve"


# ---------------------------------------------------------------------------
# Gridline detection (for the spreadsheet layout) -- pure PIL, no numpy.
# ---------------------------------------------------------------------------
def detect_gridlines(gray, axis, region, line_frac=0.85):
    """Find gridline positions along `axis` ('x' or 'y') inside `region`
    (l, t, r, b in pixels). A gridline is a row/column that is non-white for
    most of its length. Returns merged center positions in image coordinates.
    """
    l, t, r, b = region
    px = gray.load()
    hits = []
    if axis == "x":
        span = range(t, b)
        denom = max(1, b - t)
        for x in range(l, r):
            nonwhite = sum(1 for y in span if px[x, y] < 245)
            if nonwhite / denom > line_frac:
                hits.append(x)
    else:
        span = range(l, r)
        denom = max(1, r - l)
        for y in range(t, b):
            nonwhite = sum(1 for x in span if px[x, y] < 245)
            if nonwhite / denom > line_frac:
                hits.append(y)
    # merge consecutive hits into single lines
    merged = []
    for v in hits:
        if merged and v - merged[-1][-1] <= 3:
            merged[-1].append(v)
        else:
            merged.append([v])
    return [int(sum(g) / len(g)) for g in merged]


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
# Risk-type auto-derivation
# ---------------------------------------------------------------------------
# DEFINED risk = the most you can lose is bounded and known up front:
#   spreads, butterflies, condors, zebras, diagonals, covered positions, AND
#   long single options (max loss = the premium/debit paid).
# UNDEFINED risk = potentially unbounded / margin-defined:
#   naked short puts/calls, short strangles/straddles, and long futures/stock.
#
# NOTE: a naive "long singles are undefined" rule is WRONG and disagrees with
# Ryan's own sheet (he correctly marks long calls / LEAPS as Defined). This
# derivation was validated to match all 25 rows of his real open-book sheet.
# It is only a FALLBACK; if the screenshot has a Risk Type column we use his
# value and keep it user-editable.
_DEFINED_HINTS = ("spread", "butterfly", "condor", "zebra", "diagonal",
                  "covered", "long call", "long put", "leaps", "super bull")
_UNDEFINED_HINTS = ("short put", "short call", "strangle", "straddle")


def derive_risk_type(description):
    """Return 'Def' / 'Undef' / None from a Trade Description string."""
    if not description:
        return None
    d = description.lower()
    # long futures / stock (no premium cap) -> undefined
    if re.search(r"/\w+.*\blong\b", d) and "call" not in d and "put" not in d:
        return "Undef"
    has_naked = any(h in d for h in _UNDEFINED_HINTS) and "spread" not in d
    has_defined = any(h in d for h in _DEFINED_HINTS)
    if has_naked and not has_defined:
        return "Undef"
    if has_defined and not has_naked:
        return "Def"
    if has_naked and has_defined:
        # mixed structure that still carries a naked short leg (e.g. Super Bull)
        return "Undef"
    return None


# ---------------------------------------------------------------------------
# Spreadsheet (open-book / risk panel) extraction
# ---------------------------------------------------------------------------
def parse_inf(text):
    """Money cell that may be the infinity glyph. Returns float, 'inf', or None."""
    if text is None:
        return None
    t = text.strip()
    if not t or t in ("-", "—"):
        return None
    if "∞" in t or t.lower() in ("inf", "infinity", "00", "oo"):
        return "inf"
    return parse_money(t)


def extract_spreadsheet(im, debug=None, name=""):
    """Segment Ryan's open-book sheet by its gridlines and OCR each cell.

    The column boundaries are detected from the vertical gridlines (not
    hard-coded), then mapped onto SPREADSHEET_COLUMNS in order. Row boundaries
    come from the horizontal gridlines. Demonstrated on ryan_spreadsheet.png:
    11 vertical gridlines -> the 10 documented columns; ~25 data rows.
    """
    gray = im.convert("L")
    w, h = im.size
    flags = []

    # Table lives left of the Portfolio Summary side card. Find the right edge
    # of the grid as the last strong vertical gridline before the white gutter.
    table_right = int(w * 0.70)
    vlines = detect_gridlines(gray, "x", (0, 0, table_right, h))
    # restrict vertical search height to where rows exist
    hlines = detect_gridlines(gray, "y", (0, 0, table_right, h))

    if debug and vlines and hlines:
        ov = im.copy()
        from PIL import ImageDraw
        d = ImageDraw.Draw(ov)
        for x in vlines:
            d.line([(x, hlines[0]), (x, hlines[-1])], fill=(255, 0, 0), width=1)
        for y in hlines:
            d.line([(vlines[0], y), (vlines[-1], y)], fill=(0, 120, 255), width=1)
        ov.save(os.path.join(debug, f"{name}_grid_overlay.png"))

    n_cols = len(SPREADSHEET_COLUMNS)
    rows_out = []
    geometry = {"vlines": vlines, "hlines": hlines}

    if len(vlines) < n_cols + 1 or len(hlines) < 3:
        flags.append("GRID_NOT_FOUND: could not segment %d cols / rows "
                     "(found %d vlines, %d hlines)"
                     % (n_cols + 1, len(vlines), len(hlines)))
        return {"layout": "spreadsheet", "positions": [], "geometry": geometry,
                "flags": flags}

    # Use the first n_cols+1 vertical lines as column edges.
    xedges = vlines[:n_cols + 1]
    # header is between hlines[0] and hlines[1]; data rows follow.
    for ri in range(1, len(hlines) - 1):
        y0, y1 = hlines[ri], hlines[ri + 1]
        if y1 - y0 < 8:
            continue
        cells = {}
        for ci, col in enumerate(SPREADSHEET_COLUMNS):
            cx0, cx1 = xedges[ci], xedges[ci + 1]
            cell = im.crop((cx0 + 1, y0 + 1, cx1 - 1, y1 - 1))
            if debug:
                cell.save(os.path.join(debug, f"{name}_r{ri}_{col}.png"))
            cells[col] = ocr_cell(cell, psm=7) if HAVE_OCR else None
        # normalize known numeric/inf columns
        rec = dict(cells)
        for mcol in ("credit_rcvd", "debit_paid", "max_profit", "max_loss",
                     "bp_usd", "bp_pct"):
            rec[mcol] = parse_inf(cells.get(mcol)) if HAVE_OCR else None
        if HAVE_OCR and not (rec.get("risk_type")):
            rec["risk_type"] = derive_risk_type(cells.get("trade_description"))
            if rec["risk_type"]:
                rec["risk_type_source"] = "derived"
        # drop fully empty rows (never invent)
        if any(v not in (None, "", "-") for v in cells.values()):
            rows_out.append(rec)

    if not HAVE_OCR:
        flags.append("NO_OCR_ENGINE: grid segmented & cells cropped (use "
                     "--debug to inspect); cell text unread. Region map is "
                     "real; production read = Tesseract or a vision-LLM pass.")

    return {"layout": "spreadsheet", "positions": rows_out,
            "geometry": geometry, "flags": flags}


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
    extractor = {"order_chains": extract_order_chains,
                 "curve": extract_curve,
                 "spreadsheet": extract_spreadsheet}[layout]
    rec = extractor(im, debug=debug, name=name)
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

    # spreadsheet layout -> a separate open-book positions CSV
    sheet_records = [r for r in records if r["layout"] == "spreadsheet"]
    book_rows = [p for r in sheet_records for p in r["positions"]]
    book_path = None
    if sheet_records:
        book_path = os.path.join(os.path.dirname(out_stem), "ocr_open_book.csv")
        bcols = SPREADSHEET_COLUMNS + ["risk_type_source"]
        with open(book_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=bcols, extrasaction="ignore")
            w.writeheader()
            for p in book_rows:
                w.writerow({c: ("" if p.get(c) is None else p.get(c))
                            for c in bcols})

    print(f"Processed {len(files)} image(s). OCR engine: "
          f"{'tesseract' if HAVE_OCR else 'NONE (crop-only)'}")
    for r in records:
        line = f"  {r['source']:28} -> {r['layout']:13}"
        if r["layout"] == "order_chains":
            line += f" ticker={r['ticker']} total_pl={r['total_pl']} status={r['chain_status']}"
        elif r["layout"] == "spreadsheet":
            g = r["geometry"]
            line += (f" segmented {len(g['vlines'])} vlines / "
                     f"{len(g['hlines'])} hlines -> {len(r['positions'])} rows")
        else:
            line += f" ticker={r['ticker']} max_loss={r.get('max_loss')}"
        if r["flags"]:
            line += "  [" + "; ".join(r["flags"]) + "]"
        print(line)
    print(f"Wrote {out_stem}.json and {out_stem}.csv ({len(rows)} chain rows)")
    if book_path:
        print(f"Wrote {book_path} ({len(book_rows)} open-book rows)")


if __name__ == "__main__":
    main()
