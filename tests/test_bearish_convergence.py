"""Tests for dossier.bearish_convergence — multi-screen agreement on the short side."""

from dossier.bearish_convergence import (
    ALWAYS_BEARISH_SCREEN_FILES,
    BEARISH_SCREEN_FILES,
    DIRECTION_AWARE_SCREEN_FILES,
    _load_bearish_only,
    load_bearish_legs,
)


class TestLoadBearishOnly:
    def test_filters_out_bullish_rows(self, tmp_path, monkeypatch):
        import dossier.screener_convergence as sc

        monkeypatch.setattr(sc, "PROJECT_ROOT", tmp_path)
        api_dir = tmp_path / "docs" / "api"
        api_dir.mkdir(parents=True)
        (api_dir / "obv-divergence.json").write_text(
            '{"results": [' +
            '{"ticker": "UP", "score": 70, "grade": "A", "direction": "bullish"},' +
            '{"ticker": "DOWN", "score": 70, "grade": "A", "direction": "bearish"}' +
            ']}'
        )
        rows = _load_bearish_only("obv-divergence.json")
        assert [r["ticker"] for r in rows] == ["DOWN"]

    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        import dossier.screener_convergence as sc

        monkeypatch.setattr(sc, "PROJECT_ROOT", tmp_path)
        assert _load_bearish_only("nope.json") == []

    def test_non_dict_rows_are_skipped(self, tmp_path, monkeypatch):
        import dossier.screener_convergence as sc

        monkeypatch.setattr(sc, "PROJECT_ROOT", tmp_path)
        api_dir = tmp_path / "docs" / "api"
        api_dir.mkdir(parents=True)
        (api_dir / "seasonality-screener.json").write_text('{"results": ["garbage"]}')
        assert _load_bearish_only("seasonality-screener.json") == []


class TestLoadBearishLegs:
    def test_loads_always_bearish_and_direction_filtered_legs(self, tmp_path, monkeypatch):
        import dossier.screener_convergence as sc

        monkeypatch.setattr(sc, "PROJECT_ROOT", tmp_path)
        api_dir = tmp_path / "docs" / "api"
        api_dir.mkdir(parents=True)
        (api_dir / "death-cross.json").write_text(
            '{"results": [{"ticker": "AAPL", "score": 80, "grade": "A+"}]}'
        )
        (api_dir / "seasonality-screener.json").write_text(
            '{"results": [' +
            '{"ticker": "AAPL", "score": 60, "grade": "B", "direction": "bearish"},' +
            '{"ticker": "MSFT", "score": 90, "grade": "A+", "direction": "bullish"}' +
            ']}'
        )
        legs = load_bearish_legs()
        assert set(legs.keys()) == set(BEARISH_SCREEN_FILES.keys())
        assert [r["ticker"] for r in legs["death_cross"]] == ["AAPL"]
        assert [r["ticker"] for r in legs["seasonality"]] == ["AAPL"]
        assert legs["insider_selling_cluster"] == []
        assert legs["obv_divergence"] == []


class TestBearishScreenFilesRegistry:
    def test_always_bearish_screens_are_registered(self):
        for name in ("death_cross", "insider_selling_cluster"):
            assert name in ALWAYS_BEARISH_SCREEN_FILES
            assert name in BEARISH_SCREEN_FILES

    def test_direction_aware_screens_are_registered(self):
        for name in ("obv_divergence", "seasonality"):
            assert name in DIRECTION_AWARE_SCREEN_FILES
            assert name in BEARISH_SCREEN_FILES

    def test_no_overlap_between_the_two_registries(self):
        assert set(ALWAYS_BEARISH_SCREEN_FILES) & set(DIRECTION_AWARE_SCREEN_FILES) == set()
