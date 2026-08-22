"""Tests for dossier.analyst_revision_screener pure parsing + scoring helpers."""

from datetime import date

import pandas as pd
import pytest

from dossier.analyst_revision_screener import (
    _is_bullish_grade,
    _is_bearish_grade,
    _is_bullish_revision,
    _is_bearish_revision,
    _parse_date,
    _parse_analyst_revisions,
    cluster_size_score,
    pt_upside_score,
    recency_score,
    clean_signal_score,
    conviction_score,
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


# ── grade classification ────────────────────────────────────────────

class TestGradeClassification:
    def test_bullish_grades(self):
        for g in ("Buy", "Strong Buy", "Overweight", "Outperform", "Positive", "Accumulate"):
            assert _is_bullish_grade(g) is True

    def test_bearish_grades(self):
        for g in ("Sell", "Underperform", "Underweight", "Negative", "Reduce"):
            assert _is_bearish_grade(g) is True

    def test_neutral_grade_is_neither(self):
        assert _is_bullish_grade("Hold") is False
        assert _is_bearish_grade("Hold") is False
        assert _is_bullish_grade("Neutral") is False
        assert _is_bearish_grade("Neutral") is False

    def test_none_grade(self):
        assert _is_bullish_grade(None) is False
        assert _is_bearish_grade(None) is False

    def test_overweight_not_confused_with_underweight(self):
        assert _is_bullish_grade("Overweight") is True
        assert _is_bearish_grade("Overweight") is False
        assert _is_bearish_grade("Underweight") is True
        assert _is_bullish_grade("Underweight") is False


# ── _is_bullish_revision / _is_bearish_revision ─────────────────────

class TestRevisionClassification:
    def test_upgrade_action_is_bullish_regardless_of_grade(self):
        assert _is_bullish_revision("up", "Hold") is True
        assert _is_bullish_revision("up", "Buy") is True

    def test_downgrade_action_is_bearish_regardless_of_grade(self):
        assert _is_bearish_revision("down", "Hold") is True
        assert _is_bearish_revision("down", "Sell") is True

    def test_bullish_initiation(self):
        assert _is_bullish_revision("init", "Overweight") is True
        assert _is_bearish_revision("init", "Overweight") is False

    def test_bearish_initiation(self):
        assert _is_bearish_revision("init", "Underperform") is True
        assert _is_bullish_revision("init", "Underperform") is False

    def test_neutral_initiation_is_neither(self):
        assert _is_bullish_revision("init", "Hold") is False
        assert _is_bearish_revision("init", "Hold") is False

    def test_maintain_and_reiterate_are_neither(self):
        for action in ("main", "reit"):
            assert _is_bullish_revision(action, "Buy") is False
            assert _is_bearish_revision(action, "Sell") is False

    def test_none_action(self):
        assert _is_bullish_revision(None, "Buy") is False
        assert _is_bearish_revision(None, "Sell") is False


# ── _parse_analyst_revisions ─────────────────────────────────────────

def _row(firm, action, to_grade, grade_date, target=100.0):
    return {"Firm": firm, "Action": action, "ToGrade": to_grade, "GradeDate": grade_date, "currentPriceTarget": target}


class TestParseAnalystRevisions:
    def test_none_df(self):
        result = _parse_analyst_revisions(None)
        assert result["distinct_firms"] == 0
        assert result["firm_names"] == []
        assert result["price_targets"] == []
        assert result["downgrade_count"] == 0
        assert result["most_recent_date"] is None

    def test_empty_df(self):
        result = _parse_analyst_revisions(pd.DataFrame())
        assert result["distinct_firms"] == 0

    def test_two_distinct_bullish_firms_in_window(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jefferies", "up", "Buy", date(2026, 2, 1), 150.0),
            _row("Goldman Sachs", "up", "Overweight", date(2026, 2, 15), 160.0),
        ])
        result = _parse_analyst_revisions(df, lookback_days=30, as_of=as_of)
        assert result["distinct_firms"] == 2
        assert result["firm_names"] == ["Goldman Sachs", "Jefferies"]
        assert result["price_targets"] == [150.0, 160.0]
        assert result["most_recent_date"] == "2026-02-15"

    def test_same_firm_twice_counts_once(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jefferies", "up", "Buy", date(2026, 2, 1), 150.0),
            _row("Jefferies", "up", "Buy", date(2026, 2, 10), 155.0),
        ])
        result = _parse_analyst_revisions(df, lookback_days=30, as_of=as_of)
        assert result["distinct_firms"] == 1

    def test_stale_revision_outside_window_excluded(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jefferies", "up", "Buy", date(2025, 1, 1), 150.0),
        ])
        result = _parse_analyst_revisions(df, lookback_days=30, as_of=as_of)
        assert result["distinct_firms"] == 0

    def test_future_date_excluded(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jefferies", "up", "Buy", date(2026, 4, 1), 150.0),
        ])
        result = _parse_analyst_revisions(df, lookback_days=30, as_of=as_of)
        assert result["distinct_firms"] == 0

    def test_downgrades_counted_separately(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jefferies", "up", "Buy", date(2026, 2, 1), 150.0),
            _row("Barclays", "down", "Underweight", date(2026, 2, 5), 90.0),
        ])
        result = _parse_analyst_revisions(df, lookback_days=30, as_of=as_of)
        assert result["distinct_firms"] == 1
        assert result["downgrade_count"] == 1

    def test_neutral_actions_ignored(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jefferies", "main", "Buy", date(2026, 2, 1), 150.0),
            _row("Barclays", "reit", "Hold", date(2026, 2, 5), 90.0),
        ])
        result = _parse_analyst_revisions(df, lookback_days=30, as_of=as_of)
        assert result["distinct_firms"] == 0
        assert result["downgrade_count"] == 0

    def test_zero_price_target_excluded_from_targets(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jefferies", "init", "Buy", date(2026, 2, 1), 0.0),
        ])
        result = _parse_analyst_revisions(df, lookback_days=30, as_of=as_of)
        assert result["distinct_firms"] == 1
        assert result["price_targets"] == []

    def test_most_recent_date_picks_latest(self):
        as_of = date(2026, 3, 1)
        df = pd.DataFrame([
            _row("Jefferies", "up", "Buy", date(2026, 1, 5), 150.0),
            _row("Goldman Sachs", "up", "Buy", date(2026, 2, 20), 150.0),
        ])
        result = _parse_analyst_revisions(df, lookback_days=30, as_of=as_of)
        assert result["most_recent_date"] == "2026-02-20"


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


# ── pt_upside_score ───────────────────────────────────────────────

class TestPtUpsideScore:
    def test_none(self):
        assert pt_upside_score(None) == 0

    def test_top_tier(self):
        assert pt_upside_score(25) == 25
        assert pt_upside_score(40) == 25

    def test_mid_tier(self):
        assert pt_upside_score(15) == 18

    def test_low_tier(self):
        assert pt_upside_score(8) == 10

    def test_thin_tier(self):
        assert pt_upside_score(3) == 5

    def test_below_floor(self):
        assert pt_upside_score(1) == 0

    def test_negative_upside(self):
        assert pt_upside_score(-10) == 0


# ── recency_score ─────────────────────────────────────────────────

class TestRecencyScore:
    def test_none(self):
        assert recency_score(None) == 0

    def test_this_week(self):
        assert recency_score(3) == 20

    def test_one_week(self):
        assert recency_score(7) == 14

    def test_two_weeks(self):
        assert recency_score(14) == 8

    def test_one_month(self):
        assert recency_score(30) == 3

    def test_stale(self):
        assert recency_score(31) == 0
        assert recency_score(365) == 0

    def test_zero_days(self):
        assert recency_score(0) == 20


# ── clean_signal_score ───────────────────────────────────────────

class TestCleanSignalScore:
    def test_no_downgrades(self):
        assert clean_signal_score(0) == 12

    def test_one_downgrade(self):
        assert clean_signal_score(1) == 6

    def test_two_or_more_downgrades(self):
        assert clean_signal_score(2) == 0
        assert clean_signal_score(5) == 0


# ── conviction_score ──────────────────────────────────────────────

class TestConvictionScore:
    def test_strong_buy_present(self):
        assert conviction_score(["Buy", "Strong Buy"]) == 8

    def test_plain_bullish_grades(self):
        assert conviction_score(["Buy", "Overweight"]) == 5

    def test_empty(self):
        assert conviction_score([]) == 0


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
            + pt_upside_score(30)
            + recency_score(1)
            + clean_signal_score(0)
            + conviction_score(["Strong Buy"])
        )
        assert total == 100

    def test_thin_stale_muddied_cluster_scores_low(self):
        total = (
            cluster_size_score(2)
            + pt_upside_score(1)
            + recency_score(200)
            + clean_signal_score(3)
            + conviction_score([])
        )
        assert total < 35
        assert _letter_grade(total) == "D"
