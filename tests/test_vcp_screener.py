"""Tests for dossier.vcp_screener pure scoring helpers."""

import pytest

from dossier.vcp_screener import (
    atr_contraction_score,
    base_tightness_score,
    trend_health_score,
    volume_dryup_score,
    _letter_grade,
)


# ── atr_contraction_score ─────────────────────────────────────────

class TestAtrContractionScore:
    def test_extreme_contraction(self):
        assert atr_contraction_score(0.40) == 35

    def test_boundary_050(self):
        assert atr_contraction_score(0.50) == 35

    def test_just_above_050(self):
        assert atr_contraction_score(0.55) == 28

    def test_boundary_060(self):
        assert atr_contraction_score(0.60) == 28

    def test_just_above_060(self):
        assert atr_contraction_score(0.65) == 20

    def test_boundary_070(self):
        assert atr_contraction_score(0.70) == 20

    def test_just_above_070(self):
        assert atr_contraction_score(0.75) == 12

    def test_boundary_080(self):
        assert atr_contraction_score(0.80) == 12

    def test_just_above_080(self):
        assert atr_contraction_score(0.85) == 5

    def test_boundary_090(self):
        assert atr_contraction_score(0.90) == 5

    def test_no_contraction(self):
        assert atr_contraction_score(0.95) == 0

    def test_expansion(self):
        assert atr_contraction_score(1.20) == 0

    def test_returns_int(self):
        assert isinstance(atr_contraction_score(0.50), int)


# ── volume_dryup_score ────────────────────────────────────────────

class TestVolumeDryupScore:
    def test_max_dryup(self):
        assert volume_dryup_score(0.30) == 30

    def test_boundary_050(self):
        assert volume_dryup_score(0.50) == 30

    def test_just_above_050(self):
        assert volume_dryup_score(0.55) == 24

    def test_boundary_060(self):
        assert volume_dryup_score(0.60) == 24

    def test_just_above_060(self):
        assert volume_dryup_score(0.65) == 18

    def test_boundary_070(self):
        assert volume_dryup_score(0.70) == 18

    def test_just_above_070(self):
        assert volume_dryup_score(0.75) == 11

    def test_boundary_080(self):
        assert volume_dryup_score(0.80) == 11

    def test_just_above_080(self):
        assert volume_dryup_score(0.85) == 5

    def test_boundary_090(self):
        assert volume_dryup_score(0.90) == 5

    def test_no_dryup(self):
        assert volume_dryup_score(1.00) == 0

    def test_volume_surging(self):
        assert volume_dryup_score(1.50) == 0

    def test_returns_int(self):
        assert isinstance(volume_dryup_score(0.60), int)


# ── trend_health_score ────────────────────────────────────────────

class TestTrendHealthScore:
    def test_perfect_setup(self):
        # above both SMAs, RSI 55 (Goldilocks)
        score = trend_health_score(100.0, sma50=90.0, sma200=80.0, rsi=55.0)
        assert score == 20

    def test_above_both_smas_rsi_marginal(self):
        # above both, RSI 47 (just below sweet spot)
        score = trend_health_score(100.0, sma50=90.0, sma200=80.0, rsi=47.0)
        assert score == 6 + 5 + 6   # 17

    def test_above_sma50_only(self):
        score = trend_health_score(100.0, sma50=90.0, sma200=None, rsi=55.0)
        assert score == 5 + 9   # no SMA200 pts

    def test_sma200_none(self):
        score = trend_health_score(100.0, sma50=90.0, sma200=None, rsi=55.0)
        assert score < 20

    def test_rsi_none(self):
        score = trend_health_score(100.0, sma50=90.0, sma200=80.0, rsi=None)
        assert score == 6 + 5   # 11

    def test_below_sma50_no_sma50_pts(self):
        score = trend_health_score(85.0, sma50=90.0, sma200=80.0, rsi=55.0)
        # above SMA200 (6), RSI 55 (9), but below SMA50 (0)
        assert score == 6 + 9

    def test_capped_at_20(self):
        score = trend_health_score(100.0, sma50=90.0, sma200=80.0, rsi=58.0)
        assert score <= 20

    def test_rsi_low_zone(self):
        score = trend_health_score(100.0, sma50=90.0, sma200=80.0, rsi=41.0)
        assert score == 6 + 5 + 3   # 14


# ── base_tightness_score ──────────────────────────────────────────

class TestBaseTightnessScore:
    def test_extremely_tight(self):
        assert base_tightness_score(1.0) == 15

    def test_boundary_3pct(self):
        assert base_tightness_score(3.0) == 15

    def test_just_above_3pct(self):
        assert base_tightness_score(4.0) == 12

    def test_boundary_5pct(self):
        assert base_tightness_score(5.0) == 12

    def test_just_above_5pct(self):
        assert base_tightness_score(6.0) == 8

    def test_boundary_7pct(self):
        assert base_tightness_score(7.0) == 8

    def test_just_above_7pct(self):
        assert base_tightness_score(9.0) == 4

    def test_boundary_10pct(self):
        assert base_tightness_score(10.0) == 4

    def test_wide_base(self):
        assert base_tightness_score(12.0) == 0

    def test_returns_int(self):
        assert isinstance(base_tightness_score(3.0), int)


# ── _letter_grade ─────────────────────────────────────────────────

class TestLetterGrade:
    def test_a_plus(self):
        assert _letter_grade(80) == "A+"
        assert _letter_grade(95) == "A+"
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


# ── integration: total score plausibility ────────────────────────

class TestScorePlausibility:
    """Sanity checks that the components add up within valid bounds."""

    def test_perfect_vcp_max_score(self):
        total = (
            atr_contraction_score(0.40)    # 35
            + volume_dryup_score(0.40)     # 30
            + trend_health_score(100.0, sma50=90.0, sma200=80.0, rsi=55.0)  # 20
            + base_tightness_score(2.0)    # 15
        )
        assert total == 100

    def test_marginal_vcp_is_d_grade(self):
        # 5 + 5 + 20 + 4 = 34 → D (below 35 threshold)
        total = (
            atr_contraction_score(0.85)    # 5
            + volume_dryup_score(0.85)     # 5
            + trend_health_score(100.0, sma50=90.0, sma200=80.0, rsi=55.0)  # 20
            + base_tightness_score(8.0)    # 4
        )
        assert total == 34
        assert _letter_grade(total) == "D"

    def test_strong_vcp_is_a_grade(self):
        total = (
            atr_contraction_score(0.58)    # 28
            + volume_dryup_score(0.62)     # 18
            + trend_health_score(100.0, sma50=90.0, sma200=80.0, rsi=58.0)  # 20
            + base_tightness_score(4.5)    # 12
        )
        assert total == 78
        assert _letter_grade(total) == "A"
