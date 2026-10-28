"""WeatherNext + NVIDIA Earth-2 adapter tests (offline, credential-gated)."""

from __future__ import annotations

from cofa_forward.ingestion.nvidia_earth2 import NvidiaEarth2Adapter
from cofa_forward.ingestion.weathernext import WeatherNextAdapter


def test_weathernext_requires_credentials_without_config():
    a = WeatherNextAdapter()
    info = a.check_availability()
    assert info["available"] is False
    assert "allowlist" in info["note"].lower()
    r = a.get_point_forecast(7.34, 134.48)
    assert r["ok"] is False
    assert "allowlist" in r["error"].lower()
    assert "access_note" in r


def test_nvidia_requires_credentials_without_key():
    a = NvidiaEarth2Adapter()
    info = a.check_availability()
    assert info["available"] is False
    r = a.get_point_forecast(7.34, 134.48)
    assert r["ok"] is False
    assert "access_note" in r


def test_weathernext_source_id_and_provenance_honesty():
    a = WeatherNextAdapter()
    assert a.source_id == "google-weathernext3"
    r = a.get_point_forecast(0, 0)
    # Never fabricate: the error must explain the gate, not return synthetic data.
    assert "ok" in r and r["ok"] is False
    assert "allowlist" in r["error"].lower()


def test_nvidia_source_id():
    a = NvidiaEarth2Adapter()
    assert a.source_id == "nvidia-earth2"
