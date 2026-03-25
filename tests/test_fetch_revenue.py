"""
Tests for dossier/fetch_revenue.py — critical edge cases.

Run: python -m pytest tests/ -v
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════

@pytest.fixture
def tmp_output(tmp_path):
    """Patch OUTPUT_FILE to use a temporary directory."""
    output = tmp_path / "revenue_stats.json"
    with patch("dossier.fetch_revenue.OUTPUT_FILE", output):
        yield output


@pytest.fixture
def mock_stripe():
    """Mock the stripe module entirely."""
    mock = MagicMock()
    with patch.dict("sys.modules", {"stripe": mock}):
        yield mock


# ═══════════════════════════════════════════════════
# TEST 1: Zero gross revenue — no ZeroDivisionError
# ═══════════════════════════════════════════════════

def _make_stripe_mock(charges=None, payouts=None):
    """Build a mock stripe module with sensible defaults."""
    mock = MagicMock()
    mock.api_key = "sk_test_fake"

    mock_charges = MagicMock()
    mock_charges.data = charges or []
    mock_charges.has_more = False
    mock.Charge.list.return_value = mock_charges

    mock_payouts = MagicMock()
    mock_payouts.data = payouts or []
    mock_payouts.has_more = False
    mock.Payout.list.return_value = mock_payouts

    mock_balance = MagicMock()
    mock_balance.available = []
    mock_balance.pending = []
    mock.Balance.retrieve.return_value = mock_balance

    mock_subs = MagicMock()
    mock_subs.data = []
    mock.Subscription.list.return_value = mock_subs

    return mock


def test_stripe_zero_gross_no_crash(tmp_output):
    """When no succeeded charges exist, fee_rate_pct should be 0, not ZeroDivisionError."""
    mock_stripe = _make_stripe_mock()

    with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}):
        with patch.dict("sys.modules", {"stripe": mock_stripe}):
            # Re-import to pick up the mock
            from dossier.fetch_revenue import fetch_stripe_data
            result = fetch_stripe_data()

    assert result is not None
    assert result["stripe_audit"]["fee_rate_pct"] == 0
    assert result["stripe_audit"]["gross_charges"] == 0
    assert result["stripe_audit"]["net_revenue"] == 0


# ═══════════════════════════════════════════════════
# TEST 2: TastyTrade zero net deposited — no ZeroDivisionError
# ═══════════════════════════════════════════════════

def test_tastytrade_zero_net_deposited_no_crash(tmp_output):
    """When deposits == withdrawals (net = 0), pnl_pct should be 0."""
    from dossier.fetch_revenue import fetch_tastytrade_data

    with patch.dict("os.environ", {
        "TASTYTRADE_REFRESH_TOKEN": "fake_token",
        "TASTYTRADE_CLIENT_ID": "fake_id",
        "TASTYTRADE_CLIENT_SECRET": "fake_secret",
    }):
        with patch("dossier.fetch_revenue.requests") as mock_requests:
            # Token response
            mock_token_resp = MagicMock()
            mock_token_resp.status_code = 200
            mock_token_resp.json.return_value = {"access_token": "fake_access"}

            # Account response
            mock_acct_resp = MagicMock()
            mock_acct_resp.json.return_value = {
                "data": {"items": [{"account": {"account-number": "TEST123"}}]}
            }

            # Balance — net deposited = 0 (deposits == withdrawals in txns)
            mock_bal_resp = MagicMock()
            mock_bal_resp.json.return_value = {
                "data": {"net-liquidating-value": "1000", "cash-balance": "500"}
            }

            # Positions — empty
            mock_pos_resp = MagicMock()
            mock_pos_resp.json.return_value = {"data": {"items": []}}

            # Transactions — deposit $500, withdraw $500 → net = 0
            mock_txn_resp = MagicMock()
            mock_txn_resp.json.return_value = {
                "data": {"items": [
                    {"transaction-type": "Money Movement", "net-value": "500",
                     "transaction-sub-type": "", "underlying-symbol": ""},
                    {"transaction-type": "Money Movement", "net-value": "-500",
                     "transaction-sub-type": "", "underlying-symbol": ""},
                ]}
            }

            mock_requests.post.return_value = mock_token_resp
            mock_requests.get.side_effect = [
                mock_acct_resp, mock_bal_resp, mock_pos_resp, mock_txn_resp
            ]

            result = fetch_tastytrade_data()

    assert result is not None
    # net_deposited = 500 - 500 = 0, so pnl_pct should be 0 (not crash)
    assert result["pnl_pct"] == 0


# ═══════════════════════════════════════════════════
# TEST 3: Allocation preserves previous actuals
# ═══════════════════════════════════════════════════

def test_allocation_preserves_previous_actuals(tmp_output):
    """Allocation 'actual' values should persist from the previous run."""
    # Write a previous revenue_stats.json with known allocation
    previous = {
        "allocation": {
            "brokerage": {"actual": 42.00},
            "paychecks": {"actual": 20.00},
            "tax_savings": {"actual": 15.00},
        }
    }
    tmp_output.write_text(json.dumps(previous))

    # One charge for $100, succeeded
    mock_charge = MagicMock()
    mock_charge.status = "succeeded"
    mock_charge.refunded = False
    mock_charge.amount = 10000  # $100 in cents
    mock_charge.amount_refunded = 0
    mock_charge.created = int(datetime(2026, 3, 1).timestamp())

    mock_bt = MagicMock()
    mock_bt.fee = 320  # $3.20
    type(mock_bt).fee = PropertyMock(return_value=320)
    mock_charge.balance_transaction = mock_bt

    # Payouts — $100 paid
    mock_payout = MagicMock()
    mock_payout.status = "paid"
    mock_payout.amount = 10000
    mock_payout.created = int(datetime(2026, 3, 1).timestamp())

    mock_stripe = _make_stripe_mock(
        charges=[mock_charge],
        payouts=[mock_payout],
    )

    with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}):
        with patch.dict("sys.modules", {"stripe": mock_stripe}):
            from dossier.fetch_revenue import fetch_stripe_data
            result = fetch_stripe_data()

    assert result is not None
    # Should preserve the previous actual, not overwrite with target
    assert result["allocation"]["brokerage"]["actual"] == 42.00
    assert result["allocation"]["paychecks"]["actual"] == 20.00
    assert result["allocation"]["tax_savings"]["actual"] == 15.00


# ═══════════════════════════════════════════════════
# TEST 4: Malformed wash sale dates don't crash
# ═══════════════════════════════════════════════════

def test_wash_sale_malformed_dates(tmp_output):
    """Wash sales with invalid date strings should be silently skipped."""
    previous = {
        "brokerage": {
            "wash_sales": [
                {"symbol": "GOOD", "wash_sale_end": "2099-12-31", "realized_loss": -100},
                {"symbol": "BAD1", "wash_sale_end": "not-a-date"},
                {"symbol": "BAD2", "wash_sale_end": ""},
                {"symbol": "BAD3"},  # missing key entirely
                {"symbol": "OLD", "wash_sale_end": "2020-01-01"},  # expired
            ]
        }
    }
    tmp_output.write_text(json.dumps(previous))

    from dossier.fetch_revenue import fetch_tastytrade_data

    with patch.dict("os.environ", {
        "TASTYTRADE_REFRESH_TOKEN": "fake_token",
        "TASTYTRADE_CLIENT_ID": "fake_id",
        "TASTYTRADE_CLIENT_SECRET": "fake_secret",
    }):
        with patch("dossier.fetch_revenue.requests") as mock_requests:
            mock_token_resp = MagicMock()
            mock_token_resp.status_code = 200
            mock_token_resp.json.return_value = {"access_token": "fake_access"}

            mock_acct_resp = MagicMock()
            mock_acct_resp.json.return_value = {
                "data": {"items": [{"account": {"account-number": "TEST123"}}]}
            }

            mock_bal_resp = MagicMock()
            mock_bal_resp.json.return_value = {
                "data": {"net-liquidating-value": "1000", "cash-balance": "500"}
            }

            mock_pos_resp = MagicMock()
            mock_pos_resp.json.return_value = {"data": {"items": []}}

            mock_txn_resp = MagicMock()
            mock_txn_resp.json.return_value = {"data": {"items": []}}

            mock_requests.post.return_value = mock_token_resp
            mock_requests.get.side_effect = [
                mock_acct_resp, mock_bal_resp, mock_pos_resp, mock_txn_resp
            ]

            # This should NOT crash even with malformed wash sale dates
            result = fetch_tastytrade_data()

    assert result is not None
    # Only the GOOD (future date) wash sale should survive
    assert len(result["wash_sales"]) == 1
    assert result["wash_sales"][0]["symbol"] == "GOOD"


# ═══════════════════════════════════════════════════
# TEST 5: Closed positions with premium — correct net P&L
# ═══════════════════════════════════════════════════

def test_closed_position_premium_tracking(tmp_output):
    """Closed positions should compute net_pnl = realized_stock_pnl + premium."""
    from dossier.fetch_revenue import fetch_tastytrade_data

    with patch.dict("os.environ", {
        "TASTYTRADE_REFRESH_TOKEN": "fake_token",
        "TASTYTRADE_CLIENT_ID": "fake_id",
        "TASTYTRADE_CLIENT_SECRET": "fake_secret",
    }):
        with patch("dossier.fetch_revenue.requests") as mock_requests:
            mock_token_resp = MagicMock()
            mock_token_resp.status_code = 200
            mock_token_resp.json.return_value = {"access_token": "fake_access"}

            mock_acct_resp = MagicMock()
            mock_acct_resp.json.return_value = {
                "data": {"items": [{"account": {"account-number": "TEST123"}}]}
            }

            mock_bal_resp = MagicMock()
            mock_bal_resp.json.return_value = {
                "data": {"net-liquidating-value": "1000", "cash-balance": "500"}
            }

            # No open positions — all closed
            mock_pos_resp = MagicMock()
            mock_pos_resp.json.return_value = {"data": {"items": []}}

            # Transactions: bought ACME at $10, sold at $12, plus $3 premium from STO
            mock_txn_resp = MagicMock()
            mock_txn_resp.json.return_value = {
                "data": {"items": [
                    # Stock buy
                    {"transaction-type": "Trade", "transaction-sub-type": "Buy to Open",
                     "net-value": "-100", "underlying-symbol": "ACME",
                     "instrument-type": "Equity", "quantity": "10"},
                    # Stock sell
                    {"transaction-type": "Trade", "transaction-sub-type": "Sell to Close",
                     "net-value": "120", "underlying-symbol": "ACME",
                     "instrument-type": "Equity", "quantity": "10"},
                    # Option premium (STO)
                    {"transaction-type": "Trade", "transaction-sub-type": "Sell to Open",
                     "net-value": "30", "underlying-symbol": "ACME",
                     "instrument-type": "Option", "quantity": "1"},
                ]}
            }

            mock_requests.post.return_value = mock_token_resp
            mock_requests.get.side_effect = [
                mock_acct_resp, mock_bal_resp, mock_pos_resp, mock_txn_resp
            ]

            result = fetch_tastytrade_data()

    assert result is not None
    # Should have 1 closed position for ACME
    acme_positions = [p for p in result["positions_with_premiums"] if p["symbol"] == "ACME"]
    assert len(acme_positions) == 1

    acme = acme_positions[0]
    assert acme["closed"] is True
    assert acme["stock_pnl"] == 20.0     # 120 - 100 = 20
    assert acme["premium"] == 30.0        # $30 collected
    assert acme["net_pnl"] == 50.0        # 20 + 30 = 50
    assert acme["strategy"] == "Wheel (closed)"
