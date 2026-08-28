"""Tests for dossier.report.builder.build_report — mainly the GEX dealer
positioning panel wiring (gex_reads was computed in generate.py but never
reached the template before).
"""
from dossier.report import builder


def _minimal_market():
    return {
        "vix": {"vix_level": 15.2, "regime_name": "Calm", "regime_desc": "Low vol"},
        "sector_rotation": [],
    }


def _minimal_institutional():
    return {
        "top_buying": [],
        "top_selling": [],
        "divergences": [],
        "sector_inflows": [],
        "sector_outflows": [],
    }


def _minimal_persistence():
    return {
        "summary": {"lifers": 0, "high_conviction": 0, "total_tracked": 0},
        "lifers": [],
        "high_conviction": [],
    }


def _build(tmp_path, monkeypatch, **kwargs):
    monkeypatch.setattr(builder, "OUTPUT_DIR", tmp_path)
    path = builder.build_report(
        date="1999-01-01",
        market=_minimal_market(),
        institutional=_minimal_institutional(),
        scanner_signals=[],
        persistence=_minimal_persistence(),
        dossiers=[],
        **kwargs,
    )
    return open(path).read()


class TestGexReadsPanel:
    def test_gex_reads_rendered_when_present(self, tmp_path, monkeypatch):
        gex_reads = [{
            "ticker": "AAPL",
            "spot": 231.5,
            "regime": "negative",
            "gamma_flip": 228.0,
            "call_wall": 235,
            "put_wall": 225,
            "read": "Negative gamma: dealers amplify moves.",
        }]
        html = _build(tmp_path, monkeypatch, gex_reads=gex_reads)
        assert "GEX.DEALER.POSITIONING" in html
        assert "AAPL" in html
        assert "Negative gamma: dealers amplify moves." in html

    def test_gex_panel_omitted_when_empty(self, tmp_path, monkeypatch):
        html = _build(tmp_path, monkeypatch, gex_reads=[])
        assert "GEX.DEALER.POSITIONING" not in html

    def test_gex_reads_defaults_to_no_panel(self, tmp_path, monkeypatch):
        """build_report is called without gex_reads by any caller not yet
        updated — must not crash and must simply omit the panel."""
        html = _build(tmp_path, monkeypatch)
        assert "GEX.DEALER.POSITIONING" not in html
