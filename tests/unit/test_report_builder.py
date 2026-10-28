"""Report builder tests."""

from __future__ import annotations

from cofa_forward.intelligence.report_builder import build_markdown_report


def test_report_contains_sections_and_evidence_tags():
    meta = {"report_date": "2026-10-28", "data_cutoff": "2026-10-28T00:00:00Z"}
    sections = [
        {
            "title": "Regional situation",
            "items": [
                {
                    "text": "Heavy rain possible.",
                    "evidence_type": "forecast",
                    "source": "Open-Meteo",
                },
                {"text": "No confirmed storms.", "evidence_type": "analyst"},
            ],
        },
    ]
    sources = [
        {"source_id": "open-meteo-forecast", "retrieved_at": "2026-10-28T00:00:00Z", "status": "ok"}
    ]
    gaps = ["No ENSO source configured."]

    md = build_markdown_report(meta, sections, sources, gaps)

    assert "# COFA FORWARD" in md
    assert "## Regional situation" in md
    assert "[forecast]" in md
    assert "Open-Meteo" in md
    assert "## Information gaps" in md
    assert "No ENSO source configured." in md
    assert "## Data sources" in md
    assert "open-meteo-forecast" in md


def test_report_empty_gaps():
    md = build_markdown_report({"report_date": "x"}, [], [])
    assert "None recorded." in md
