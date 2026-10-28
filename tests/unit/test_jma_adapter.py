"""JMA RSMC Tokyo adapter tests (offline normalization + mocked fetch)."""

from __future__ import annotations

from cofa_forward.ingestion.base import FetchResult
from cofa_forward.ingestion.jma import JmaTyphoonAdapter, normalize_jma_spec


def _spec_payload():
    return [
        {
            "part": "title",
            "issue": {"UTC": "2026-10-28T03:45:00Z", "JST": "2026-10-28T12:45:00+09:00"},
            "typhoonNumber": "2631",
            "name": {"jp": "インファ", "en": "In-fa"},
            "category": {"jp": "台風", "en": "TY"},
        },
        {
            "part": {"jp": "実況", "en": "Analysis"},
            "maximumWind": {
                "sustained": {"m/s": "50", "kt": "100"},
                "gust": {"m/s": "70", "kt": "140"},
            },
            "galeWarning": [{"area": "北", "range": {"km": 330, "nm": 180}}],
            "stormWarning": [{"area": {"en": "All"}, "range": {"km": 110, "nm": 60}}],
            "position": {"deg": [15.0, 159.4]},
            "pressure": "950",
        },
        {
            "part": {"jp": "予報 １２時間後", "en": "Forecast for 12 hours ahead"},
            "advancedHours": 12,
            "position": {"deg": [15.4, 157.1]},
            "pressure": "945",
            "maximumWind": {"sustained": {"m/s": "50", "kt": "100"}},
            "probabilityCircleRadius": {"km": 55, "nm": 30},
            "validtime": {"UTC": "2026-10-28T15:00:00Z"},
        },
    ]


def test_normalize_jma_spec():
    norm = normalize_jma_spec(_spec_payload())
    assert norm["meta"]["name_en"] == "In-fa"
    assert norm["meta"]["typhoon_number"] == "2631"
    assert norm["analysis"]["position"] == {"lat": 15.0, "lon": 159.4}
    assert norm["analysis"]["pressure_hpa"] == 950.0
    assert norm["analysis"]["wind_sustained_kt"] == 100.0
    assert norm["analysis"]["storm_radius_km"] == 110.0
    assert len(norm["forecasts"]) == 1
    fc = norm["forecasts"][0]
    assert fc["hours"] == 12
    assert fc["probability_circle_km"] == 55.0


def test_normalize_jma_spec_empty():
    norm = normalize_jma_spec([])
    assert norm == {"meta": {}, "analysis": {}, "forecasts": []}


def test_active_storms(monkeypatch):
    adapter = JmaTyphoonAdapter()

    def fake_fetch(url, params=None, timeout=None):
        return FetchResult(
            True,
            "jma-rsmc-tokyo",
            url,
            data=[
                {
                    "tropicalCyclone": "TC2637",
                    "typhoonNumber": "2631",
                    "category": "TY",
                    "issue": "x",
                }
            ],
        )

    monkeypatch.setattr(adapter, "fetch_json", fake_fetch)
    r = adapter.active_storms()
    assert r["ok"] is True
    assert r["n_active"] == 1
    assert r["storms"][0]["tc_id"] == "TC2637"


def test_storm_details(monkeypatch):
    adapter = JmaTyphoonAdapter()

    def fake_fetch(url, params=None, timeout=None):
        return FetchResult(True, "jma-rsmc-tokyo", url, data=_spec_payload())

    monkeypatch.setattr(adapter, "fetch_json", fake_fetch)
    r = adapter.storm_details("TC2637")
    assert r["ok"] is True
    assert r["meta"]["name_en"] == "In-fa"
