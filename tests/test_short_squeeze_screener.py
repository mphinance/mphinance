"""Tests for dossier.short_squeeze_screener pure scoring helpers."""

import pytest

from dossier.short_squeeze_screener import (
    short_interest_score,
    days_to_cover_score,
    short_interest_trend_score,
    ema_reclaim_score,
    rsi_turn_score,
    volume_ignition_score,
    _letter_grade,
)


# ── short_interest_score ──────────────────────────────────────────

class TestShortInterestScore:
    def test_extreme(self):
        assert short_interest_score(30.0) == 35

    def test_above_extreme(self):
        assert short_interest_score(45.0) == 35

    def test_boundary_20(self):
        assert short_interest_score(20.0) == 30

    def test_just_below_20(self):
        assert short_interest_score(19.9) == 25

    def test_boundary_15(self):
        assert short_interest_score(15.0) == 25

    def test_just_below_15(self):
        assert short_interest_score(14.9) == 18

    def test_boundary_10(self):
        assert short_interest_score(10.0) == 18

    def test_below_gate(self):
        assert short_interest_score(9.9) == 0

    def test_zero(self):
        assert short_interest_score(0.0) == 0

    def test_returns_int(self):
        assert isinstance(short_interest_score(20.0), int)


# ── days_to_cover_score ───────────────────────────────────────────

class TestDaysToCoverScore:
    def test_max(self):
        assert days_to_cover_score(10.0) == 20

    def test_above_max(self):
        assert days_to_cover_score(20.0) == 20

    def test_boundary_7(self):
        assert days_to_cover_score(7.0) == 16

    def test_boundary_5(self):
        assert days_to_cover_score(5.0) == 12

    def test_boundary_3(self):
        assert days_to_cover_score(3.0) == 8

    def test_boundary_1(self):
        assert days_to_cover_score(1.0) == 4

    def test_below_1(self):
        assert days_to_cover_score(0.5) == 0

    def test_zero(self):
        assert days_to_cover_score(0.0) == 0

    def test_returns_int(self):
        assert isinstance(days_to_cover_score(5.0), int)


# ── short_interest_trend_score ────────────────────────────────────

class TestShortInterestTrendScore:
    def test_no_prior_data(self):
        assert short_interest_trend_score(1_000_000, 0) == 7

    def test_prior_none_like(self):
        assert short_interest_trend_score(1_000_000, None) == 7

    def test_shorts_adding_aggressively(self):
        # +15% month over month
        assert short_interest_trend_score(1_150_000, 1_000_000) == 15

    def test_boundary_10pct_up(self):
        assert short_interest_trend_score(1_100_000, 1_000_000) == 15

    def test_shorts_flat_up_slightly(self):
        assert short_interest_trend_score(1_050_000, 1_000_000) == 10

    def test_shorts_unchanged(self):
        assert short_interest_trend_score(1_000_000, 1_000_000) == 10

    def test_shorts_trimming_slightly(self):
        # -5%
        assert short_interest_trend_score(950_000, 1_000_000) == 5

    def test_boundary_minus_10pct(self):
        assert short_interest_trend_score(900_000, 1_000_000) == 5

    def test_shorts_covering_fast(self):
        # -20%
        assert short_interest_trend_score(800_000, 1_000_000) == 0

    def test_returns_int(self):
        assert isinstance(short_interest_trend_score(1_100_000, 1_000_000), int)


# ── ema_reclaim_score ─────────────────────────────────────────────

class TestEmaReclaimScore:
    def test_above_ema(self):
        assert ema_reclaim_score(105.0, 100.0) == 12

    def test_just_below_ema_within_3pct(self):
        assert ema_reclaim_score(98.0, 100.0) == 6

    def test_boundary_97pct(self):
        assert ema_reclaim_score(97.0, 100.0) == 6

    def test_further_below(self):
        assert ema_reclaim_score(90.0, 100.0) == 0

    def test_ema_none(self):
        assert ema_reclaim_score(100.0, None) == 0

    def test_ema_zero(self):
        assert ema_reclaim_score(100.0, 0.0) == 0

    def test_returns_int(self):
        assert isinstance(ema_reclaim_score(105.0, 100.0), int)


# ── rsi_turn_score ────────────────────────────────────────────────

class TestRsiTurnScore:
    def test_sweet_spot(self):
        assert rsi_turn_score(55.0) == 10

    def test_boundary_50(self):
        assert rsi_turn_score(50.0) == 10

    def test_boundary_68(self):
        assert rsi_turn_score(68.0) == 10

    def test_marginal_low(self):
        assert rsi_turn_score(45.0) == 5

    def test_marginal_high(self):
        assert rsi_turn_score(72.0) == 5

    def test_too_low(self):
        assert rsi_turn_score(35.0) == 0

    def test_too_high(self):
        assert rsi_turn_score(80.0) == 0

    def test_none(self):
        assert rsi_turn_score(None) == 0

    def test_returns_int(self):
        assert isinstance(rsi_turn_score(55.0), int)


# ── volume_ignition_score ─────────────────────────────────────────

class TestVolumeIgnitionScore:
    def test_strong_surge(self):
        assert volume_ignition_score(3.0) == 8

    def test_boundary_25(self):
        assert volume_ignition_score(2.5) == 8

    def test_moderate(self):
        assert volume_ignition_score(2.0) == 5

    def test_boundary_15(self):
        assert volume_ignition_score(1.5) == 5

    def test_light(self):
        assert volume_ignition_score(1.2) == 2

    def test_boundary_1(self):
        assert volume_ignition_score(1.0) == 2

    def test_below_average(self):
        assert volume_ignition_score(0.5) == 0

    def test_returns_int(self):
        assert isinstance(volume_ignition_score(2.0), int)


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
            short_interest_score(50.0)
            + days_to_cover_score(15.0)
            + short_interest_trend_score(1_200_000, 1_000_000)
            + ema_reclaim_score(105.0, 100.0)
            + rsi_turn_score(60.0)
            + volume_ignition_score(3.0)
        )
        assert total == 100

    def test_below_gate_short_interest_still_scores_zero_on_that_leg(self):
        # Below the 10% hard-gate threshold, the short interest leg
        # contributes nothing even if other legs are strong.
        assert short_interest_score(5.0) == 0
