"""Open-Meteo forecast adapter tests (offline: normalization + mocked fetch)."""

from __future__ import annotations

import pandas as pd
import pytest

from cofa_forward.ingestion.base import FetchResult
from cofa_forward.ingestion.weather import OpenMeteoForecastAdapter, normalize_forecast


def _payload():
    return {
        "latitude": 7.34,
        "longitude": 134.48,
        "elevation": 10.0,
        "timezone": "UTC",
        "generationtime_ms": 0.5,
        "current": {
            "time": "2026-10-28T00:00",
            "temperature_2m": 27.5,
            "relative_humidity_2m": 80.0,
            "precipitation": 0.0,
            "weather_code": 1,
            "wind_speed_10m": 5.0,
            "wind_direction_10m": 90.0,
            "surface_pressure": 1010.0,
        },
        "hourly": {
            "time": ["2026-10-28T00:00", "2026-10-28T01:00"],
            "temperature_2m": [27.5, 27.6],
            "precipitation": [0.0, 0.0],
        },
        "daily": {
            "time": ["2026-10-28"],
            "temperature_2m_max": [30.0],
            "temperature_2m_min": [25.0],
            "precipitation_sum": [5.0],
        },
        "hourly_units": {"temperature_2m": "°C"},
        "daily_units": {"temperature_2m_max": "°C"},
    }


def test_normalize_forecast():
    norm = normalize_forecast(_payload())
    assert norm["current"]["temperature_2m"] == 27.5
    assert list(norm["hourly"].columns) == ["temperature_2m", "precipitation"]
    assert len(norm["hourly"]) == 2
    assert isinstance(norm["hourly"].index, pd.DatetimeIndex)
    assert norm["hourly"].index.tz is not None
    assert norm["meta"]["latitude"] == 7.34


def test_normalize_forecast_rejects_non_dict():
    with pytest.raises(ValueError):
        normalize_forecast(None)


def test_get_forecast_success(monkeypatch):
    adapter = OpenMeteoForecastAdapter()

    def fake_fetch(url, params=None, timeout=None):
        return FetchResult(True, "open-meteo-forecast", url, data=_payload())

    monkeypatch.setattr(adapter, "fetch_json", fake_fetch)
    r = adapter.get_forecast(7.34, 134.48)
    assert r["ok"] is True
    assert len(r["hourly"]) == 2
    assert r["source"] == "open-meteo-forecast"


def test_get_forecast_network_failure(monkeypatch):
    adapter = OpenMeteoForecastAdapter()

    def fake_fetch(url, params=None, timeout=None):
        return FetchResult(False, "open-meteo-forecast", url, error="boom")

    monkeypatch.setattr(adapter, "fetch_json", fake_fetch)
    r = adapter.get_forecast(7.34, 134.48)
    assert r["ok"] is False
    assert r["error"] == "boom"


def test_get_model_comparison(monkeypatch):
    adapter = OpenMeteoForecastAdapter()
    payload = {
        "hourly": {
            "time": ["2026-10-28T00:00", "2026-10-28T01:00"],
            "temperature_2m_best_match": [27.5, 27.6],
            "temperature_2m_gfs_global": [27.8, 27.9],
            "temperature_2m_ecmwf_aifs025": [27.3, 27.4],
        }
    }

    def fake_fetch(url, params=None, timeout=None):
        return FetchResult(True, "open-meteo-forecast", url, data=payload)

    monkeypatch.setattr(adapter, "fetch_json", fake_fetch)
    r = adapter.get_model_comparison(7.34, 134.48, variable="temperature_2m")
    assert r["ok"] is True
    assert r["n_models"] == 3
    assert list(r["models"].columns) == ["best_match", "gfs_global", "ecmwf_aifs025"]
    assert len(r["models"]) == 2
