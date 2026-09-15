# Tharp Reference Library — Index

Markdown summaries built from mph's Van Tharp PDF collection at `/home/mph/mphinance/tharp/`, for eventual use as reference material when building position-sizing/risk logic into a trading agent. Markdown only for now, per mph's instruction — no agent-integration work done yet.

## Summarized

- **[trading-excellence-model.md](trading-excellence-model.md)** — Van Tharp Institute's 5-pillar framework overview (Peak Performance Mindset, Position Sizing, Trading Process Architecture, Trading Mastery, Transformational Growth). Short marketing e-book, fully read (real text layer, no OCR needed). Best single quote: "You can trade a mediocre system with good position sizing and make money, but you can trade a great system with poor position sizing and go broke."

- **[definitive-guide-position-sizing.md](definitive-guide-position-sizing.md)** — Tharp's 399-page reference book on position sizing. OCR'd incrementally (image-based PDF, no text layer). Complete so far: full table of contents, Chapter 8 (the five core sizing models — Units/Fixed$, Equal Units, Percent Margin, Percent Volatility, Percent Risk — with real backtest tables on a 55/21-day breakout system), Chapter 15 (models to avoid, including the exact Kelly Criterion formula and Tharp's explicit "avoid totally" verdict, Optimal f critique, and an independently-reproduced "mean lies, median tells the truth" simulation result). Chapters 2, 3, 4, 5, 6, 7, 9, 10-14, 16-18 not yet extracted (flagged in-file).

- **[systems-development-workbook.md](systems-development-workbook.md)** — "Developing a Winning Trading System That Fits You," a 154-page 3-day seminar transcript. Has a genuine (if messy) text layer — extracted directly, no OCR. **The richest source found**: the real marble-game origin of the "same trades, different sizing" demonstration (with its exact expectancy and Kelly% computed), the Ten Parts of a Good System, the expectancy formula with worked examples, a full exit-technique taxonomy (LeBeau Exit Efficiency Index, named exit types), and — most valuable of all — Tom Basso's exact worked example for trimming a winning position back down when its *current* risk (using the trailing stop, not the entry stop) exceeds your cap, a full pyramiding worked example using unrealized gains as new risk budget, and a genuinely new expectancy/reward-risk → portfolio-heat lookup table not found in the Definitive Guide.

- **[risk-successful-investor.md](risk-successful-investor.md)** — partial summary of Volume 1 of the 5-volume "Peak Performance Home Study Course." Image-based PDF, OCR-sampled rather than fully read. Most of the volume is psychological self-assessment (skipped); **Chapter VII, "Techniques to Objectively Measure Risk," is summarized in full** — standard-deviation-of-returns as a risk score (with a real 40-commodity-fund benchmark dataset), a 95%-confidence-interval formula for win-rate estimates, and a risk-of-ruin formula citation.

## Triaged and skipped (no file — confirmed via contents-page sampling, not skipped on title alone)

- **Volume 2 — Stress**: general/trading stress physiology, Arousal Theory, General Adaptation Syndrome, muscle-tension models. Pure psychology/physiology, no transferable mechanism.
- **Volume 3 — Attitude**: understanding losses via the Hydraulic Model and Servo-Mechanism model of the trader, self-esteem and meaning-of-money exercises. Pure psychology.
- **Volume 4 — Discipline**: beliefs, mental states, NLP-style reframing techniques, state management. Pure psychology, no formulas.
- **Volume 5 — Sound Decisions**: internal representation systems, the "TOTE Model," decision-strategy taxonomy. Pure NLP-flavored decision psychology, no quantitative content.

All four are confirmed to be the human-psychology-focused volumes of the same Peak Performance course referenced in `trading-excellence-model.md` — legitimate material for a human trader's self-development, but nothing an autonomous agent could use directly.

## Toolchain note (for continuing this extraction later)
`poppler-utils` and `tesseract-ocr` are installed system-wide on this box (not present by default — were `apt-get install`'d during this session). Image-based PDFs: `pdftoppm -f <first> -l <last> -r 150 -png <pdf> <prefix>` then `tesseract <page>.png -` per page. Check `pypdf.PdfReader(...).pages[i].extract_text()` first on any new PDF — some (like the Systems Development Workbook) have a real, if messy, text layer and don't need OCR at all; others (like the Definitive Guide and the 4-volume psychology series) are scanned images with only a pirate-distributor watermark in the actual text layer, and genuinely need OCR for anything real.
