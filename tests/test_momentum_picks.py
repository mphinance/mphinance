"""Tests for dossier/momentum_picks.py — momentum scoring and daily picks ranking."""

import copy
import json

import pytest

from dossier import momentum_picks
from dossier.momentum_picks import (
    _clamp,
    format_picks_text,
    pick_daily_momentum,
    score_momentum,
)


def _payload(**overrides):
    base = {
        "ticker": "AAPL",
        "currentPrice": 100.0,
        "priceChangePct": 1.5,
        "trendOverall": "Bullish",
        "sector": "Technology",
        "fortress_tier": "UNKNOWN",
        "technical_analysis": {
            "ema_stack": "FULL BULLISH",
            "ema": {"21": 98.0},
            "oscillators": {
                "rsi_14": 55,
                "adx_14": 30,
                "stoch_k": 35,
                "macd_hist": 0.5,
            },
            "volume": {"rel_vol": 1.8},
        },
        "scores": {"grade": "A", "technical": 80},
        "tickertrace": {"signal": {"direction": "BUY"}},
    }
    base.update(copy.deepcopy(overrides))
    return base


@pytest.fixture(autouse=True)
def _clean_quality(monkeypatch):
    """Pin quality_score=100 so these tests isolate the raw scoring math;
    tests that care about the quality multiplier override this explicitly."""
    import dossier.quality_filter as qf

    monkeypatch.setattr(
        qf,
        "check_quality",
        lambda payload: {"quality_score": 100, "flags": {}, "reasons": [], "has_issues": False},
    )


class TestClamp:
    def test_within_range(self):
        assert _clamp(50) == 50

    def test_clamps_low(self):
        assert _clamp(-5) == 0

    def test_clamps_high(self):
        assert _clamp(150) == 100

    def test_custom_bounds(self):
        assert _clamp(5, lo=10, hi=20) == 10


class TestScoreMomentumBreakdown:
    def test_full_bullish_perfect_pullback_scores_high(self):
        result = score_momentum(_payload())
        assert result["ticker"] == "AAPL"
        assert result["is_pullback_setup"] is True
        assert result["breakdown"]["ema_stack"] == 10
        assert result["breakdown"]["pullback"] == 15
        # quality=100 means no discount from raw_score
        assert result["score"] == result["raw_score"]

    @pytest.mark.parametrize(
        "ema_stack,expected",
        [
            ("FULL BULLISH", 10),
            ("PARTIAL BULLISH", 6),
            ("TANGLED", 2),
            ("PARTIAL BEARISH", 1),
            ("FULL BEARISH", 0),
            ("UNKNOWN", 2),
            ("some-garbage-value", 2),
        ],
    )
    def test_ema_stack_points(self, ema_stack, expected):
        payload = _payload()
        payload["technical_analysis"]["ema_stack"] = ema_stack
        assert score_momentum(payload)["breakdown"]["ema_stack"] == expected

    @pytest.mark.parametrize("adx,expected", [(45, 18), (35, 14), (27, 10), (18, 5), (5, 0)])
    def test_adx_tiers(self, adx, expected):
        payload = _payload()
        payload["technical_analysis"]["oscillators"]["adx_14"] = adx
        assert score_momentum(payload)["breakdown"]["adx"] == expected

    @pytest.mark.parametrize("rsi,expected", [(50, 15), (35, 10), (68, 10), (20, 6), (85, 1)])
    def test_rsi_tiers(self, rsi, expected):
        payload = _payload()
        payload["technical_analysis"]["oscillators"]["rsi_14"] = rsi
        assert score_momentum(payload)["breakdown"]["rsi"] == expected

    @pytest.mark.parametrize("rel_vol,expected", [(2.5, 15), (1.6, 12), (1.2, 7), (0.5, 2)])
    def test_rel_vol_tiers(self, rel_vol, expected):
        payload = _payload()
        payload["technical_analysis"]["volume"]["rel_vol"] = rel_vol
        assert score_momentum(payload)["breakdown"]["rel_vol"] == expected

    def test_trend_bearish_scores_zero(self):
        assert score_momentum(_payload(trendOverall="Bearish"))["breakdown"]["trend"] == 0

    def test_trend_bullish_scores_five(self):
        assert score_momentum(_payload(trendOverall="Very Bullish"))["breakdown"]["trend"] == 5

    @pytest.mark.parametrize(
        "price,ema21,expected",
        [
            (100, 99, 12),  # ~1% above -> perfect pullback zone
            (103, 100, 9),  # 3% above -> healthy
            (110, 100, 3),  # 10% above -> extended
            (99, 100, 8),  # -1% -> testing support
            (90, 100, 1),  # -10% -> below EMA21
        ],
    )
    def test_price_vs_ema_tiers(self, price, ema21, expected):
        payload = _payload(currentPrice=price)
        payload["technical_analysis"]["ema"]["21"] = ema21
        assert score_momentum(payload)["breakdown"]["price_vs_ema"] == expected

    def test_price_vs_ema_missing_ema21_defaults_neutral(self):
        payload = _payload()
        payload["technical_analysis"]["ema"] = {}
        assert score_momentum(payload)["breakdown"]["price_vs_ema"] == 5

    @pytest.mark.parametrize(
        "macd_hist,expected",
        [(1.0, 5), (-0.2, 3), (-2.0, 0), (None, 2), ("not-a-number", 2)],
    )
    def test_macd_tiers(self, macd_hist, expected):
        payload = _payload()
        payload["technical_analysis"]["oscillators"]["macd_hist"] = macd_hist
        assert score_momentum(payload)["breakdown"]["macd"] == expected

    def test_institutional_buy_signal_bonus(self):
        payload = _payload(tickertrace={"signal": {"direction": "BUY"}})
        assert score_momentum(payload)["breakdown"]["institutional"] == 5

    def test_institutional_sell_signal_no_bonus(self):
        payload = _payload(tickertrace={"signal": {"direction": "SELL"}})
        assert score_momentum(payload)["breakdown"]["institutional"] == 0

    def test_institutional_missing_signal_no_bonus(self):
        payload = _payload(tickertrace={})
        assert score_momentum(payload)["breakdown"]["institutional"] == 0

    @pytest.mark.parametrize(
        "tier,expected",
        [
            ("FORTRESS", 10),
            ("CASTLE", 6),
            ("HOUSE", 3),
            ("SHACK", 0),
            ("RUBBLE", -10),
            ("UNKNOWN", 0),
        ],
    )
    def test_fortress_tier_points(self, tier, expected):
        assert score_momentum(_payload(fortress_tier=tier))["breakdown"]["fortress"] == expected


class TestScoreMomentumPullback:
    def test_good_pullback_not_textbook(self):
        payload = _payload()
        payload["technical_analysis"]["oscillators"]["adx_14"] = 22
        payload["technical_analysis"]["oscillators"]["stoch_k"] = 45
        result = score_momentum(payload)
        assert result["breakdown"]["pullback"] == 10
        assert result["is_pullback_setup"] is True

    def test_has_pullback_but_far_from_ema(self):
        payload = _payload()
        payload["technical_analysis"]["ema"]["21"] = 50  # far below price
        payload["technical_analysis"]["oscillators"]["stoch_k"] = 35
        result = score_momentum(payload)
        assert result["breakdown"]["pullback"] == 6
        assert result["is_pullback_setup"] is False

    def test_strong_trend_no_pullback_yet(self):
        payload = _payload()
        payload["technical_analysis"]["oscillators"]["stoch_k"] = 80
        payload["technical_analysis"]["ema"]["21"] = 50
        result = score_momentum(payload)
        assert result["breakdown"]["pullback"] == 3
        assert result["is_pullback_setup"] is False

    def test_bearish_ema_stack_no_pullback_credit(self):
        payload = _payload()
        payload["technical_analysis"]["ema_stack"] = "FULL BEARISH"
        result = score_momentum(payload)
        assert result["breakdown"]["pullback"] == 0
        assert result["is_pullback_setup"] is False


class TestScoreMomentumRobustness:
    def test_missing_technical_analysis_uses_defaults(self):
        payload = {"ticker": "ZZZZ", "currentPrice": 10, "priceChangePct": 0}
        result = score_momentum(payload)
        assert result["ticker"] == "ZZZZ"
        assert result["rsi"] == 50.0
        assert result["adx"] == 0.0
        assert result["stoch_k"] == 50.0
        assert result["rel_vol"] == 1.0

    def test_missing_ticker_defaults_empty_string(self):
        assert score_momentum({})["ticker"] == ""

    def test_sector_defaults_to_other(self):
        assert score_momentum(_payload(sector=None))["sector"] == "Other"

    def test_quality_score_multiplies_final_score(self, monkeypatch):
        import dossier.quality_filter as qf

        monkeypatch.setattr(
            qf,
            "check_quality",
            lambda payload: {
                "quality_score": 50,
                "flags": {"is_spac": True},
                "reasons": ["SPAC"],
                "has_issues": True,
            },
        )
        result = score_momentum(_payload())
        assert result["quality_score"] == 50
        assert result["score"] == round(result["raw_score"] * 0.5)
        assert result["quality_reasons"] == ["SPAC"]

    def test_quality_filter_failure_degrades_to_clean(self, monkeypatch):
        import dossier.quality_filter as qf

        def _boom(payload):
            raise RuntimeError("boom")

        monkeypatch.setattr(qf, "check_quality", _boom)
        result = score_momentum(_payload())
        assert result["quality_score"] == 100
        assert result["score"] == result["raw_score"]


class TestPickDailyMomentum:
    def test_ranks_and_assigns_medals(self, monkeypatch):
        monkeypatch.setattr(momentum_picks, "_save_picks", lambda *a, **kw: None)
        low = _payload(ticker="LOW")
        low["technical_analysis"]["ema_stack"] = "FULL BEARISH"
        low["technical_analysis"]["oscillators"]["adx_14"] = 5
        low["trendOverall"] = "Bearish"
        mid = _payload(ticker="MID")
        high = _payload(ticker="HIGH", fortress_tier="FORTRESS")

        result = pick_daily_momentum([low, mid, high], "2026-01-01")

        assert result["date"] == "2026-01-01"
        assert [p["ticker"] for p in result["picks"]] == ["HIGH", "MID", "LOW"]
        assert result["picks"][0]["medal"] == "🥇 GOLD"
        assert result["picks"][1]["medal"] == "🥈 SILVER"
        assert result["picks"][2]["medal"] == "🥉 BRONZE"
        assert [p["rank"] for p in result["picks"]] == [1, 2, 3]
        scores = [p["score"] for p in result["all_ranked"]]
        assert scores == sorted(scores, reverse=True)

    def test_skips_ticker_that_raises_during_scoring(self, monkeypatch):
        monkeypatch.setattr(momentum_picks, "_save_picks", lambda *a, **kw: None)
        bad_payload = {"ticker": "BAD", "technical_analysis": "not-a-dict"}
        good_payload = _payload(ticker="GOOD")

        result = pick_daily_momentum([bad_payload, good_payload], "2026-01-01")

        assert [p["ticker"] for p in result["all_ranked"]] == ["GOOD"]

    def test_payload_without_ticker_excluded(self, monkeypatch):
        monkeypatch.setattr(momentum_picks, "_save_picks", lambda *a, **kw: None)
        result = pick_daily_momentum([{}], "2026-01-01")
        assert result["all_ranked"] == []
        assert result["picks"] == []


class TestSavePicks:
    def test_writes_history_and_api_json(self, tmp_path, monkeypatch):
        import dossier.market_regime as market_regime

        monkeypatch.setattr(momentum_picks, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(
            momentum_picks, "PICKS_FILE", tmp_path / "docs" / "backtesting" / "daily_picks.json"
        )
        monkeypatch.setattr(
            market_regime,
            "detect_regime",
            lambda: {
                "regime": "NEUTRAL",
                "vix": 15.0,
                "hedge_suggestions": [],
                "market_context": "calm",
            },
        )

        payloads = [_payload(ticker="AAA"), _payload(ticker="BBB", fortress_tier="CASTLE")]
        pick_daily_momentum(payloads, "2026-02-02")

        picks_file = tmp_path / "docs" / "backtesting" / "daily_picks.json"
        assert picks_file.exists()
        history = json.loads(picks_file.read_text())
        assert history[-1]["date"] == "2026-02-02"
        assert history[-1]["gold"]["ticker"] in ("AAA", "BBB")

        api_file = tmp_path / "docs" / "api" / "daily-picks.json"
        assert api_file.exists()
        api_payload = json.loads(api_file.read_text())
        assert api_payload["market_regime"]["regime"] == "NEUTRAL"
        assert api_payload["total_scored"] == 2
        assert len(api_payload["picks"]) == 2

    def test_replaces_existing_entry_for_same_date(self, tmp_path, monkeypatch):
        import dossier.market_regime as market_regime

        monkeypatch.setattr(momentum_picks, "PROJECT_ROOT", tmp_path)
        picks_file = tmp_path / "docs" / "backtesting" / "daily_picks.json"
        monkeypatch.setattr(momentum_picks, "PICKS_FILE", picks_file)
        monkeypatch.setattr(
            market_regime,
            "detect_regime",
            lambda: {"regime": "NEUTRAL", "vix": 15.0, "hedge_suggestions": [], "market_context": ""},
        )

        pick_daily_momentum([_payload(ticker="AAA")], "2026-02-02")
        pick_daily_momentum([_payload(ticker="BBB")], "2026-02-02")

        history = json.loads(picks_file.read_text())
        same_date_entries = [h for h in history if h["date"] == "2026-02-02"]
        assert len(same_date_entries) == 1
        assert same_date_entries[0]["gold"]["ticker"] == "BBB"


class TestFormatPicksText:
    def test_no_picks_returns_message(self):
        assert format_picks_text({}) == "No momentum picks today."
        assert format_picks_text({"picks": []}) == "No momentum picks today."

    def test_formats_pullback_and_quality_flags(self):
        picks_data = {
            "picks": [
                {
                    "medal": "🥇 GOLD",
                    "ticker": "AAPL",
                    "score": 88,
                    "raw_score": 90,
                    "is_pullback_setup": True,
                    "quality_score": 80,
                    "price": 150.25,
                    "change_pct": 2.3,
                    "grade": "A",
                    "ema_stack": "FULL BULLISH",
                    "adx": 30.0,
                    "rsi": 55.0,
                    "rel_vol": 1.8,
                    "breakdown": {
                        "ema_stack": 10,
                        "pullback": 15,
                        "adx": 14,
                        "rsi": 15,
                        "trend": 5,
                        "rel_vol": 12,
                        "price_vs_ema": 9,
                        "macd": 5,
                        "institutional": 5,
                        "fortress": 6,
                    },
                    "quality_reasons": ["Low float"],
                }
            ]
        }
        text = format_picks_text(picks_data)
        assert "🥇 GOLD: AAPL" in text
        assert "Bounce 2.0!" in text
        assert "⚠️ Low float" in text
