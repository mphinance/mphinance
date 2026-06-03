"""Tests for dossier.momentum_picks pure scoring helpers."""
import pytest
from dossier.momentum_picks import _clamp, score_momentum


class TestClamp:
    def test_in_range(self):
        assert _clamp(50) == 50

    def test_below_min(self):
        assert _clamp(-5) == 0

    def test_above_max(self):
        assert _clamp(150) == 100

    def test_at_boundaries(self):
        assert _clamp(0) == 0
        assert _clamp(100) == 100

    def test_custom_range(self):
        assert _clamp(50, 0, 200) == 50
        assert _clamp(-1, 0, 200) == 0
        assert _clamp(300, 0, 200) == 200


class TestScoreMomentum:
    def _full_bull_payload(self):
        return {
            "ticker": "NVDA",
            "currentPrice": 950.0,
            "priceChangePct": 2.5,
            "trendOverall": "Bullish",
            "ema_stack": "FULL BULLISH",
            "fortress_tier": "FORTRESS",
            "scores": {"grade": "A", "technical": 90},
            "technical_analysis": {
                "ema_stack": "FULL BULLISH",
                "ema": {"21": 920.0},
                "oscillators": {
                    "rsi_14": 55,
                    "adx_14": 35,
                    "stoch_k": 30,
                    "macd_hist": 0.5,
                },
                "volume": {"rel_vol": 2.0, "avg_vol_20d": 30_000_000},
            },
            "tickertrace": {"signal": {"direction": "BUY"}},
        }

    def test_returns_required_keys(self):
        result = score_momentum(self._full_bull_payload())
        for key in ("ticker", "score", "raw_score", "quality_score", "breakdown"):
            assert key in result

    def test_full_bull_scores_high(self):
        result = score_momentum(self._full_bull_payload())
        assert result["score"] > 60, f"Expected high score, got {result['score']}"

    def test_ticker_preserved(self):
        result = score_momentum(self._full_bull_payload())
        assert result["ticker"] == "NVDA"

    def test_score_nonnegative(self):
        result = score_momentum(self._full_bull_payload())
        assert result["score"] >= 0

    def test_empty_payload_does_not_crash(self):
        result = score_momentum({})
        assert isinstance(result["score"], (int, float))

    def test_pullback_setup_detected(self):
        payload = self._full_bull_payload()
        # EMA aligned, ADX>=25, stoch<=40, near EMA21 (price 950 vs EMA21 920 → ~3.3%)
        payload["technical_analysis"]["oscillators"]["stoch_k"] = 38
        result = score_momentum(payload)
        # Near EMA21 check: price=950, ema21=920 → pct = (950-920)/920*100 = 3.26 → -3<=3.26<=5 → True
        assert result["is_pullback_setup"] is True

    def test_bearish_scores_lower(self):
        payload = self._full_bull_payload()
        payload["trendOverall"] = "Bearish"
        payload["technical_analysis"]["ema_stack"] = "FULL BEARISH"
        payload["ema_stack"] = "FULL BEARISH"
        payload["technical_analysis"]["oscillators"]["rsi_14"] = 75
        payload["technical_analysis"]["oscillators"]["adx_14"] = 10
        payload["technical_analysis"]["volume"]["rel_vol"] = 0.5
        bull_score = score_momentum(self._full_bull_payload())["score"]
        bear_score = score_momentum(payload)["score"]
        assert bear_score < bull_score
