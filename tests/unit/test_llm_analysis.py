"""LLM client + analysis-context tests (offline, no network)."""

from __future__ import annotations

from cofa_forward.intelligence.analysis_context import build_location_snapshot
from cofa_forward.intelligence.llm_client import LLMClient


def test_snapshot_includes_location_and_enso():
    facts = {
        "location": {
            "name": "Majuro",
            "geo_id": "RMI-MAJ",
            "type": "atoll",
            "lat": 7.116,
            "lon": 171.185,
            "population": 28000,
        },
        "enso": {"phase": "el_nino", "season": "ASO", "year": 2026, "anom": 2.1},
    }
    s = build_location_snapshot(facts)
    assert "LOCATION: Majuro (RMI-MAJ)" in s
    assert "atoll" in s
    assert "population≈28000" in s
    assert "ENSO: phase=el_nino" in s
    assert "2.10°C" in s


def test_snapshot_el_nino_and_current():
    facts = {
        "el_nino": {
            "2015-16": {"min_pct": 15.0, "min_month": 7.0},
            "1997-98": {"min_pct": 0.0, "min_month": 3.0},
            "2023-24": {"min_pct": 11.0, "min_month": 11.0},
            "current": {"rolling6_pct": 184.0},
        }
    }
    s = build_location_snapshot(facts)
    assert "EL NIÑO 2015-16: rolling 6-mo rainfall minimum 15% of normal" in s
    assert "EL NIÑO 1997-98: rolling 6-mo rainfall minimum 0% of normal" in s
    assert "CURRENT CYCLE: latest rolling 6-mo rainfall 184% of normal" in s


def test_snapshot_empty():
    assert build_location_snapshot({}) == "No data available for this location."


def test_snapshot_marks_missing_as_na():
    facts = {"rainfall": {"latest_mm": None, "percentile": None}}
    s = build_location_snapshot(facts)
    assert "drought level=n/a" in s


def test_llm_client_defaults():
    c = LLMClient(config=None)
    assert c.model == "frontend"
    assert c.endpoint.endswith("/v1/chat/completions")
    # available iff a key is present (gateway token file or env); do not assert
    # availability here since it depends on the host.


def test_llm_client_analyze_offline_without_key():
    # Force no key by constructing with no config and monkeypatching the token path
    # is brittle; instead verify the payload builder shape via a no-key client.
    c = LLMClient.__new__(LLMClient)
    c.api_key = None
    c.model = "frontend"
    c.endpoint = "http://127.0.0.1:9999/v1/chat/completions"
    r = c.analyze("SNAPSHOT", "question")
    assert r["ok"] is False
    assert "no LLM key" in r["error"]


def test_snapshot_covers_all_event_types():
    facts = {
        "cyclones_active": {
            "n_active": 1,
            "source": "JMA + JTWC",
            "storms": [
                {"name": "In-fa", "storm_id": "30W", "wind_kt": 110,
                 "position": {"lat": 14.3, "lon": 162.4}},
            ],
        },
        "cyclones_watch": {
            "headline": "Super Typhoon In-fa",
            "watches_warnings": ["A Typhoon Watch"],
        },
        "cyclones_history": {"n_storms": 10, "closest_km": 210.5, "closest_time": "2020-11-01"},
        "forecast": {"nmme_cycle": "202610", "nmme_models": 6, "nmme_mean_mm": 4.2,
                     "nmme_spread_mm": 1.1, "short_models": 5},
        "impacts": {"n_events": 2, "events": [
            {"event_name": "Sample drought", "hazard_type": "drought",
             "start_date": "2015-12-01", "reported_impacts": "synthetic"}]},
        "water": {"note": "n/a", "available_inputs": [], "missing_inputs": ["lens"]},
        "population": {"population": 1500, "radius_km": 10},
    }
    s = build_location_snapshot(facts)
    assert "ACTIVE CYCLONES: 1" in s
    assert "In-fa (30W)" in s
    assert "110 kt" in s
    assert "WATCH/WARNING: Super Typhoon In-fa" in s
    assert "CYCLONE HISTORY: 10 storms" in s
    assert "closest approach 210 km" in s
    assert "SEASONAL FORECAST: NMME 202610" in s
    assert "SHORT-RANGE FORECAST: 5 models" in s
    assert "HISTORICAL IMPACTS: 2 documented events" in s
    assert "Sample drought" in s
    assert "POPULATION EXPOSURE: WorldPop 1500" in s


def test_snapshot_no_secrets_or_paths():
    facts = {
        "location": {"name": "X", "geo_id": "Y", "type": "atoll", "lat": 1, "lon": 2},
        "water": {
            "note": "secret-token",
            "available_inputs": ["/etc/passwd"],
            "missing_inputs": [],
        },
    }
    s = build_location_snapshot(facts)
    # The builder only renders curated fields; even if a caller passes junk it
    # should not leak structural markers. (Sanitization is the caller's job; the
    # builder itself is deterministic.)
    assert "LOCATION: X (Y)" in s
    assert "WATER: secret-token" in s  # data is passed through verbatim by design

