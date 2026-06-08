"""Tests for the portfolio audit engine (dossier/portfolio_audit.py).

Fixture = a real Momentum Phund IBKR snapshot. All analysis is pure, so we feed
the engine a fixed book and assert on the math + flags — no network, no MCP.
"""

import pytest

from dossier import portfolio_audit as pa

# ── Real IBKR MCP snapshot (Momentum Phund) ──
SUMMARY = {
    "currency": "USD", "net_liquidation": 1598.37, "buying_power": 760.08,
    "gross_position_value": 838.29, "total_cash_value": 760.08,
    "available_funds": 760.08, "leverage": "0.52",
}
POSITIONS = {"positions": [
    {"contract_description": "CECO", "position": 1, "market_price": 77,
     "market_value": 77, "average_price": 80.4667, "unrealized_pnl": -3.4667},
    {"contract_description": "EBAY", "position": 1, "market_price": 109.31,
     "market_value": 109.31, "average_price": 110.31, "unrealized_pnl": -1.0,
     "asset_class": "STK"},
    {"contract_description": "KMI", "position": 3, "market_price": 31.68,
     "market_value": 95.04, "average_price": 35.0633, "unrealized_pnl": -10.15,
     "asset_class": "STK"},
    {"contract_description": "ONDS", "position": 10, "market_price": 10.24,
     "market_value": 102.40, "average_price": 9.6617, "unrealized_pnl": 5.78,
     "asset_class": "STK"},
    {"contract_description": "VBIL", "position": 4, "market_price": 75.51,
     "market_value": 302.04, "average_price": 75.735, "unrealized_pnl": -0.90},
    {"contract_description": "XLV", "position": 1, "market_price": 152.5,
     "market_value": 152.5, "average_price": 150.425, "unrealized_pnl": 2.075,
     "asset_class": "STK"},
]}
BALANCES = {"balances": [{"currency": "USD", "cash_balance": 760.08}]}


@pytest.fixture
def book():
    return pa.normalize_ibkr(POSITIONS, SUMMARY, BALANCES)


@pytest.fixture
def audit(book, tmp_path):
    # Empty ticker_dir so fuse/sector are deterministic (no repo coverage leaks in).
    return pa.audit_portfolio(book, ticker_dir=tmp_path, asof="2026-06-07")


# ── normalize ──
def test_normalize_counts_and_account(book):
    assert len(book["holdings"]) == 6
    assert book["account"]["net_liquidation"] == 1598.37
    assert book["account"]["cash"] == 760.08


def test_normalize_cost_basis_and_cash_equiv_flag(book):
    kmi = next(h for h in book["holdings"] if h["symbol"] == "KMI")
    assert kmi["cost_basis"] == round(35.0633 * 3, 2)  # avg * qty
    vbil = next(h for h in book["holdings"] if h["symbol"] == "VBIL")
    assert vbil["is_cash_equivalent"] is True
    assert next(h for h in book["holdings"] if h["symbol"] == "XLV")["is_cash_equivalent"] is False


# ── sleeves ──
def test_split_sleeves(book):
    s = pa.split_sleeves(book)
    assert s["cash_equivalent_value"] == 302.04          # VBIL only
    assert round(s["risk_value"], 2) == round(838.29 - 302.04, 2)  # gross - cash-eq
    assert {h["symbol"] for h in s["cash_equivalents"]} == {"VBIL"}


# ── weights / concentration ──
def test_weights_top_is_largest_risk_name(book):
    w = pa.compute_weights(book)
    # VBIL is the biggest position but is cash-equiv, so top risk name is XLV.
    assert w["top"]["symbol"] == "XLV"
    xlv = next(h for h in w["holdings"] if h["symbol"] == "XLV")
    assert xlv["weight_risk"] == pytest.approx(152.5 / 536.25 * 100, abs=0.1)


def test_cash_equiv_excluded_from_hhi_and_risk_weight(book):
    w = pa.compute_weights(book)
    vbil = next(h for h in w["holdings"] if h["symbol"] == "VBIL")
    assert vbil["weight_risk"] == 0.0
    # HHI over 5 risk names, each ~14-28% -> well under the 2500 concentrated line.
    assert w["hhi"] < 2500


# ── sectors ──
def test_sector_exposure_uses_static_map(book, tmp_path):
    sectors = pa.sector_exposure(book["holdings"], ticker_dir=tmp_path)
    assert "Cash Equivalent" not in sectors            # cash-eq excluded
    assert set(sectors) == {"Healthcare", "Consumer Discretionary",
                            "Energy", "Technology", "Industrials"}
    assert sum(v["weight_risk"] for v in sectors.values()) == pytest.approx(100, abs=0.5)


# ── pnl ──
def test_pnl_totals(audit):
    assert audit["pnl"]["winners"] == 2                # ONDS, XLV
    assert audit["pnl"]["losers"] == 4
    assert audit["pnl"]["unrealized"] == pytest.approx(-7.66, abs=0.05)


# ── flags ──
def test_flags_catch_cash_drag_and_defensive(audit):
    msgs = " ".join(f["message"] for f in audit["flags"])
    assert "Cash drag" in msgs        # 47.6% cash > 40%
    assert "Defensive posture" in msgs  # 66% cash+tbills > 60%


def test_largest_name_flagged_but_book_not_concentrated(audit):
    # XLV is 28.4% of the risk sleeve (>25%) -> single-name flag fires.
    # But the sleeve as a whole is balanced -> no HHI "concentrated book" flag.
    msgs = " ".join(f["message"] for f in audit["flags"])
    assert "Concentration: XLV" in msgs
    assert "Concentrated book" not in msgs


def test_dust_and_blind_spots_flagged(audit, tmp_path):
    msgs = " ".join(f["message"] for f in audit["flags"])
    # No dust here (smallest risk name CECO=$77 > $25 floor).
    assert "Dust positions" not in msgs
    # With an empty ticker_dir, every name is a dossier blind spot.
    assert "blind spots" in msgs


# ── concentration flag fires when it should ──
def test_concentration_flag_fires_on_lopsided_book(tmp_path):
    summary = {"net_liquidation": 1000, "total_cash_value": 0,
               "gross_position_value": 1000}
    positions = {"positions": [
        {"contract_description": "AAA", "position": 1, "market_value": 800,
         "average_price": 800, "unrealized_pnl": 0},
        {"contract_description": "BBB", "position": 1, "market_value": 200,
         "average_price": 200, "unrealized_pnl": 0},
    ]}
    book = pa.normalize_ibkr(positions, summary)
    audit = pa.audit_portfolio(book, ticker_dir=tmp_path)
    msgs = " ".join(f["message"] for f in audit["flags"])
    assert "Concentration:" in msgs            # AAA = 80% of risk
    assert "Concentrated book" in msgs         # HHI = 6800 > 2500


# ── render smoke ──
def test_renders_produce_strings(audit):
    md = pa.render_markdown(audit)
    html = pa.render_html(audit)
    assert "Portfolio Audit" in md and "| Symbol |" in md
    assert "<!DOCTYPE html>" in html and "Audit Flags" in html


def test_run_from_snapshot_roundtrip(tmp_path):
    snap = {"positions": POSITIONS, "summary": SUMMARY, "balances": BALANCES}
    audit = pa.run_from_snapshot(snap, ticker_dir=tmp_path, asof="2026-06-07")
    assert audit["account"]["net_liquidation"] == 1598.37
    assert len(audit["holdings"]) == 6
