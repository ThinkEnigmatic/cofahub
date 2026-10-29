"""PEAC seasonal rainfall outlook adapter tests (offline)."""

from __future__ import annotations

from datetime import date

from cofa_forward.ingestion.peac import PeacRainfallOutlookAdapter, parse_peac_outlook


def _row(name: str, final: str, prob: str) -> str:
    # 7 model cells + 1 final-outlook cell + 1 probability cell = 11 cells total.
    model_cells = "".join(f"<td><div><span>{final}</span></div></td>" for _ in range(7))
    return (
        f"<tr><td><strong>{name}</strong></td><td>L 7° N</td>"
        f"{model_cells}"
        f"<td><div><span>{final}</span></div></td>"
        f"<td><div align='center'>{prob}</div></td></tr>"
    )


_SAMPLE = (
    "<html><body>"
    "<h4>September, October, November (SON) 2024</h4>"
    "<table>"
    "<tr><td colspan='9'>Republic of Palau</td></tr>"
    + _row("Koror", "Above", "25:30:45")
    + "<tr><td colspan='9'>Republic of the Marshall Islands</td></tr>"
    + _row("Kwajalein", "Avg-Below", "35:35:30")
    + _row("Majuro", "Avg-Above", "30:35:35")
    + "</table>"
    "<p>Last Updated: September 16,&nbsp;2024</p>"
    "</body></html>"
)


def test_parse_peac_outlook_fields():
    p = parse_peac_outlook(_SAMPLE, today=date(2026, 10, 29))
    assert p["season_label"] == "SON"
    assert p["year"] == 2024
    assert p["season"] == "SON 2024"
    assert p["season_full"] == "September–October–November 2024"
    assert p["last_updated"] == "2024-09-16"


def test_parse_peac_outlook_stations():
    p = parse_peac_outlook(_SAMPLE)
    names = {s["name"] for s in p["stations"]}
    assert names == {"Koror", "Kwajalein", "Majuro"}
    koror = next(s for s in p["stations"] if s["name"] == "Koror")
    assert koror["final_outlook"] == "Above"
    assert koror["probabilities"] == "25:30:45"
    assert koror["probabilities_parsed"] == {"below": 25, "near": 30, "above": 45}
    assert koror["geo_id"] == "PAL-KOR"
    assert koror["country_code"] == "PW"


def test_parse_peac_outlook_freshness_guard():
    p = parse_peac_outlook(_SAMPLE, today=date(2026, 10, 29))
    # Updated 2024-09-16 -> ~2 years old -> stale.
    assert p["is_stale"] is True
    assert p["stale_days"] > 180


def test_parse_peac_outlook_graceful_on_garbage():
    p = parse_peac_outlook("<html><body>nothing</body></html>")
    assert p["stations"] == []
    assert p["is_stale"] is True


def test_peac_adapter_id():
    a = PeacRainfallOutlookAdapter()
    assert a.source_id == "noaa-peac-rainfall-outlook"
