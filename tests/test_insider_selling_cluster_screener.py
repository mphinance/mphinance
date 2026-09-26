"""Tests for dossier.insider_selling_cluster_screener pure parsing + scoring helpers."""

from datetime import date

import pandas as pd
import pytest

from dossier.insider_selling_cluster_screener import (
    _is_purchase,
    _is_sale,
    _parse_date,
    _parse_insider_sales,
    cluster_size_score,
    total_value_score,
    recency_score,
    clean_signal_score,
    trend_context_score,
    _letter_grade,
)


# ── _parse_date ────────────────────────────────────────────────────

class TestParseDate:
    def test_none(self):
        assert _parse_date(None) is None

    def test_date_passthrough(self):
        assert _parse_date(date(2026, 1, 5)) == date(2026, 1, 5)

    def test_timestamp(self):
        assert _parse_date(pd.Timestamp("2026-02-10")) == date(2026, 2, 10)

    def test_nat(self):
        assert _parse_date(pd.NaT) is None

    def test_string(self):
        assert _parse_date("2026-03-01") == date(2026, 3, 1)

    def test_bad_string(self):
        assert _parse_date("not a date") is None

    def test_other_type(self):
        assert _parse_date(12345) is None


# ── _is_purchase / _is_sale ─────────────────────────────────────────

class TestTransactionClassification:
    def test_purchase_plain(self):
        assert _is_purchase("Purchase") is True

    def test_sale_plain(self):
        assert _is_sale("Sale") is True

    def test_sale_variant(self):
        assert _is_sale("Sale (Sell)") is True

    def test_purchase_is_not_sale(self):
        assert _is_sale("Purchase") is False

    def test_sale_is_not_purchase(self):
        assert _is_purchase("Sale") is False

    def test_option_exercise_is_neither(self):
        assert _is_purchase("Option Exercise") is False
        assert _is_sale("Option Exercise") is False

    def test_none_input(self):
        assert _is_purchase(None) is False
        assert _is_sale(None) is False


# ── _parse_insider_sales ─────────────────────────────────────────────

def _row(insider, transaction, start_date, value=100_000, text=""):
    return {"Insider": insider, "Transaction": transaction, "Text": text, "Start Date": start_date, "Value": value}


def _text_row(insider, text, start_date, value=100_000):
    """Mirrors yfinance's current real-world shape: Transaction is blank,
    the actual wording ('Sale at price X per share.') lives in Text."""
    return {"Insider": insider, "Transaction": "", "Text": text, "Start Date": start_date, "Value": value}


class TestParseInsiderSales:
    def test_none_df(self):
        result = _parse_insider_sales(None)
        assert result["distinct_sellers"] == 0
        assert result["seller_names"] == []
        assert result["total_value"] == 0.0
        assert result["buy_count"] == 0
        assert result["most_recent_sale"] is None

    def test_empty_df(self):
        result = _parse_insider_sales(pd.DataFrame())
        assert result["distinct_sellers"] == 0

    def test_two_distinct_sellers_in_window(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jane CEO", "Sale", date(2026, 2, 1), 200_000),
            _row("John CFO", "Sale", date(2026, 2, 15), 50_000),
        ])
        result = _parse_insider_sales(df, lookback_days=90, as_of=as_of)
        assert result["distinct_sellers"] == 2
        assert result["seller_names"] == ["Jane CEO", "John CFO"]
        assert result["total_value"] == 250_000
        assert result["most_recent_sale"] == "2026-02-15"

    def test_same_insider_twice_counts_once(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jane CEO", "Sale", date(2026, 2, 1), 100_000),
            _row("Jane CEO", "Sale", date(2026, 2, 10), 100_000),
        ])
        result = _parse_insider_sales(df, lookback_days=90, as_of=as_of)
        assert result["distinct_sellers"] == 1
        assert result["total_value"] == 200_000

    def test_stale_sale_outside_window_excluded(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jane CEO", "Sale", date(2025, 1, 1), 100_000),
        ])
        result = _parse_insider_sales(df, lookback_days=90, as_of=as_of)
        assert result["distinct_sellers"] == 0

    def test_future_date_excluded(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jane CEO", "Sale", date(2026, 4, 1), 100_000),
        ])
        result = _parse_insider_sales(df, lookback_days=90, as_of=as_of)
        assert result["distinct_sellers"] == 0

    def test_buys_counted_separately_from_sellers(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jane CEO", "Sale", date(2026, 2, 1), 100_000),
            _row("Bob Director", "Purchase", date(2026, 2, 5), 50_000),
        ])
        result = _parse_insider_sales(df, lookback_days=90, as_of=as_of)
        assert result["distinct_sellers"] == 1
        assert result["buy_count"] == 1

    def test_missing_date_row_skipped(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jane CEO", "Sale", None, 100_000),
        ])
        result = _parse_insider_sales(df, lookback_days=90, as_of=as_of)
        assert result["distinct_sellers"] == 0

    def test_non_numeric_value_treated_as_zero(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jane CEO", "Sale", date(2026, 2, 1), "not-a-number"),
        ])
        result = _parse_insider_sales(df, lookback_days=90, as_of=as_of)
        assert result["distinct_sellers"] == 1
        assert result["total_value"] == 0.0

    def test_most_recent_sale_picks_latest(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jane CEO", "Sale", date(2026, 1, 5), 100_000),
            _row("John CFO", "Sale", date(2026, 2, 20), 100_000),
        ])
        result = _parse_insider_sales(df, lookback_days=90, as_of=as_of)
        assert result["most_recent_sale"] == "2026-02-20"

    def test_real_world_shape_blank_transaction_wording_in_text(self):
        # Matches yfinance's actual current data: "Transaction" is "", the
        # verb lives in "Text" ("Sale at price X per share.").
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _text_row("NOTO ANTHONY J.", "Sale at price 18.06 per share.", date(2026, 2, 1), 250_787),
            _text_row("SCHUPPENHAUER ERIC", "Sale at price 19.93 per share.", date(2026, 2, 10), 99_650),
            _text_row("SOME EXEC", "Purchase at price 20.00 per share.", date(2026, 2, 12), 40_000),
        ])
        result = _parse_insider_sales(df, lookback_days=90, as_of=as_of)
        assert result["distinct_sellers"] == 2
        assert result["total_value"] == 350_437
        assert result["buy_count"] == 1


# ── cluster_size_score ───────────────────────────────────────────

class TestClusterSizeScore:
    def test_four_or_more(self):
        assert cluster_size_score(4) == 35
        assert cluster_size_score(7) == 35

    def test_three(self):
        assert cluster_size_score(3) == 26

    def test_two(self):
        assert cluster_size_score(2) == 18

    def test_below_gate(self):
        assert cluster_size_score(1) == 0
        assert cluster_size_score(0) == 0

    def test_returns_int(self):
        assert isinstance(cluster_size_score(3), int)


# ── total_value_score ────────────────────────────────────────────

class TestTotalValueScore:
    def test_top_tier(self):
        assert total_value_score(5_000_000) == 25
        assert total_value_score(10_000_000) == 25

    def test_million_plus(self):
        assert total_value_score(1_000_000) == 18

    def test_quarter_million(self):
        assert total_value_score(250_000) == 10

    def test_fifty_k(self):
        assert total_value_score(50_000) == 5

    def test_below_floor(self):
        assert total_value_score(10_000) == 0

    def test_zero(self):
        assert total_value_score(0) == 0


# ── recency_score ─────────────────────────────────────────────────

class TestRecencyScore:
    def test_none(self):
        assert recency_score(None) == 0

    def test_this_week(self):
        assert recency_score(7) == 20

    def test_three_weeks(self):
        assert recency_score(21) == 14

    def test_45_days(self):
        assert recency_score(45) == 8

    def test_90_days(self):
        assert recency_score(90) == 3

    def test_stale(self):
        assert recency_score(91) == 0
        assert recency_score(365) == 0

    def test_zero_days(self):
        assert recency_score(0) == 20


# ── clean_signal_score ───────────────────────────────────────────

class TestCleanSignalScore:
    def test_no_buys(self):
        assert clean_signal_score(0) == 12

    def test_one_buy(self):
        assert clean_signal_score(1) == 6

    def test_two_or_more_buys(self):
        assert clean_signal_score(2) == 0
        assert clean_signal_score(5) == 0


# ── trend_context_score (inverted vs. the buy screener on purpose) ──

class TestTrendContextScore:
    def test_no_sma_defaults_neutral(self):
        assert trend_context_score(100.0, None) == 4

    def test_zero_sma_defaults_neutral(self):
        assert trend_context_score(100.0, 0.0) == 4

    def test_at_or_below_sma_is_weakest(self):
        assert trend_context_score(95.0, 100.0) == 0

    def test_boundary_5pct_extended(self):
        assert trend_context_score(105.0, 100.0) == 4

    def test_moderately_extended(self):
        assert trend_context_score(110.0, 100.0) == 4

    def test_boundary_15pct_extended_is_strongest(self):
        assert trend_context_score(115.0, 100.0) == 8

    def test_very_extended_is_strongest(self):
        assert trend_context_score(130.0, 100.0) == 8


# ── _letter_grade ─────────────────────────────────────────────────

class TestLetterGrade:
    def test_a_plus(self):
        assert _letter_grade(80) == "A+"
        assert _letter_grade(100) == "A+"

    def test_a(self):
        assert _letter_grade(65) == "A"
        assert _letter_grade(79) == "A"

    def test_b(self):
        assert _letter_grade(50) == "B"
        assert _letter_grade(64) == "B"

    def test_c(self):
        assert _letter_grade(35) == "C"
        assert _letter_grade(49) == "C"

    def test_d(self):
        assert _letter_grade(0) == "D"
        assert _letter_grade(34) == "D"


# ── integration: total score plausibility ─────────────────────────

class TestScorePlausibility:
    def test_max_possible_score_is_100(self):
        total = (
            cluster_size_score(5)
            + total_value_score(6_000_000)
            + recency_score(1)
            + clean_signal_score(0)
            + trend_context_score(150.0, 100.0)
        )
        assert total == 100

    def test_thin_stale_muddied_cluster_scores_low(self):
        total = (
            cluster_size_score(2)
            + total_value_score(10_000)
            + recency_score(200)
            + clean_signal_score(3)
            + trend_context_score(95.0, 100.0)
        )
        assert total < 35
        assert _letter_grade(total) == "D"
