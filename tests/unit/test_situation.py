"""Situation brief + alert summary tests."""

from __future__ import annotations

from cofa_forward.intelligence.situation import build_live_sections, drought_alert_summary


def test_drought_alert_summary_red():
    alerts = drought_alert_summary({"peac_index": "Red", "quintile": "Drier", "d0_d4": "D2"})
    assert any("RED" in a for a in alerts)
    assert any("D2" in a for a in alerts)
    assert any("Drier" in a for a in alerts)


def test_drought_alert_summary_benign():
    assert (
        drought_alert_summary({"peac_index": "Dark Green", "quintile": "Wetter", "d0_d4": None})
        == []
    )
    assert drought_alert_summary(None) == []


def test_build_live_sections_handles_missing():
    sections = build_live_sections(
        enso=None, active_storms=None, drought=None, sea_level=None, marine=None, compound=[]
    )
    titles = [s["title"] for s in sections]
    assert "ENSO" in titles
    assert "Compound hazards" in titles
    # Missing data is stated, not fabricated.
    for s in sections:
        assert s["items"]


def test_build_live_sections_compound_flags():
    sections = build_live_sections(
        enso=None,
        active_storms=None,
        drought=None,
        sea_level=None,
        marine=None,
        compound=["Drought + large seas"],
    )
    compound = next(s for s in sections if s["title"] == "Compound hazards")
    assert any("Drought + large seas" in i["text"] for i in compound["items"])
