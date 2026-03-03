"""
Report Builder — Assembles all data into the final HTML report.

Uses Jinja2 to render the dark-terminal HTML template.
"""

from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from dossier.config import OUTPUT_DIR, AUTHOR, REPORT_TITLE, DISCLAIMER


TEMPLATE_DIR = Path(__file__).parent


def build_report(
    date: str,
    market: dict,
    institutional: dict,
    scanner_signals: list,
    persistence: dict,
    dossiers: list,
    ai_narrative: str = "",
    market_pulse: list = None,
    technical_setups: list = None,
    csp_setups: list = None,
) -> str:
    """Render the daily Alpha Dossier report as HTML. Returns path to HTML file."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("template.html")

    from zoneinfo import ZoneInfo
    est = ZoneInfo("America/New_York")
    generated_at = datetime.now(est).strftime("%Y-%m-%d %I:%M %p EST")

    content = template.render(
        title=REPORT_TITLE,
        author=AUTHOR,
        date=date,
        generated_at=generated_at,
        market=market,
        market_pulse=market_pulse or [],
        institutional=institutional,
        scanner_signals=scanner_signals,
        persistence=persistence,
        dossiers=dossiers,
        ai_narrative=ai_narrative,
        technical_setups=technical_setups or [],
        csp_setups=csp_setups or [],
        disclaimer=DISCLAIMER,
    )

    output_path = OUTPUT_DIR / f"{date}_alpha_dossier.html"
    with open(output_path, "w") as f:
        f.write(content)

    print(f"  ✓ Report saved to: {output_path}")
    return str(output_path)


def build_pdf(html_path: str) -> str | None:
    """Convert the HTML report directly to PDF using WeasyPrint."""
    try:
        from weasyprint import HTML
    except ImportError:
        print("  [WARN] weasyprint not installed, skipping PDF")
        return None

    try:
        pdf_path = html_path.replace(".html", ".pdf")
        HTML(filename=html_path).write_pdf(pdf_path)
        print(f"  ✓ PDF saved to: {pdf_path}")
        return pdf_path

    except Exception as e:
        print(f"  [WARN] PDF generation failed: {e}")
        return None
