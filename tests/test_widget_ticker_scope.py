"""
Regression tests for the Alpha.HUD ticker widgets (docs/widgets/*.html).

Background
----------
Every ticker widget fetches ``ticker/{TICKER}/latest.json`` inside an IIFE
where ``ticker`` is a block-scoped local.  ``full-hud.html`` defines its
render helper ``buildHUD`` *outside* that IIFE, so when the helper's markup
referenced ``${ticker}`` it threw ``ReferenceError: ticker is not defined``.

That error was swallowed by the fetch ``.catch`` and rendered as the
misleading "this ticker isn't on the watchlist yet" message — making the
widget look like it required a watchlist entry when in fact the data had
loaded fine.  TSLA (which *has* data) failed exactly like an untracked
ticker.

These tests lock in the contract: any ``${ticker}`` reference must be in a
scope that can actually see ``ticker``.
"""

import re
from pathlib import Path

import pytest

WIDGET_DIR = Path(__file__).resolve().parent.parent / "docs" / "widgets"

TICKER_WIDGETS = [
    "full-hud.html",
    "signal-bar.html",
    "technical-matrix.html",
    "valuation.html",
    "options-flow.html",
    "institutional.html",
    "ai-synthesis.html",
]


def _read(name):
    return (WIDGET_DIR / name).read_text()


@pytest.mark.parametrize("name", TICKER_WIDGETS)
def test_widget_exists_and_fetches_ticker_json(name):
    src = _read(name)
    assert "ticker/${ticker}/latest.json" in src, (
        f"{name} should fetch the per-ticker latest.json feed"
    )
    # ticker must be derived from the URL query param
    assert re.search(r"(let|const)\s+ticker\s*=", src), (
        f"{name} must declare a ticker variable from the query param"
    )


def test_full_hud_buildhud_receives_ticker():
    """``buildHUD`` lives outside the IIFE, so ticker must be passed in.

    This is the exact regression: previously ``function buildHUD(d)`` used a
    bare ``${ticker}`` it could not see.
    """
    src = _read("full-hud.html")

    # The helper must accept ticker as a parameter ...
    assert re.search(r"function buildHUD\s*\(\s*d\s*,\s*ticker\s*\)", src), (
        "buildHUD must accept ticker as a parameter"
    )
    # ... and the call site must pass it.
    assert re.search(r"buildHUD\s*\(\s*d\s*,\s*ticker\s*\)", src), (
        "buildHUD must be called with the ticker argument"
    )
    # Guard against the old broken call signature creeping back.
    assert not re.search(r"buildHUD\s*\(\s*d\s*\)", src), (
        "buildHUD(d) without ticker reintroduces the ReferenceError bug"
    )


def test_full_hud_distinguishes_missing_data_from_render_error():
    """A 404 (untracked) and a render error must show different messages.

    Otherwise a genuine bug masquerades as 'not on the watchlist' again.
    """
    src = _read("full-hud.html")
    # 404 path: status check before parsing JSON
    assert "if (!r.ok)" in src, "full-hud must check response.ok for missing tickers"
    # The watchlist copy stays for the real 'no data' case ...
    assert "on the watchlist yet" in src
    # ... but render failures get their own, non-watchlist message.
    assert "Could not load" in src, (
        "render errors must surface a distinct message, not the watchlist copy"
    )
