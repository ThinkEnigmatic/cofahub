"""Live network integration tests (marked ``network``; skipped by default).

Run explicitly with:  uv run pytest -m network
"""

from __future__ import annotations

import pytest

from cofa_forward.config import get_config
from cofa_forward.ingestion.enso import CpcOniAdapter
from cofa_forward.ingestion.ibtracs import FAS_BBOX, IbtracsAdapter
from cofa_forward.ingestion.jma import JmaTyphoonAdapter
from cofa_forward.ingestion.rainfall import OpenMeteoArchiveAdapter
from cofa_forward.ingestion.weather import OpenMeteoForecastAdapter

pytestmark = pytest.mark.network


def test_live_forecast():
    cfg = get_config()
    adapter = OpenMeteoForecastAdapter(config=cfg)
    r = adapter.get_forecast(7.342, 134.478, forecast_days=7)
    assert r["ok"], f"live forecast failed: {r.get('error')}"
    assert len(r["hourly"]) > 0
    assert "temperature_2m" in r["hourly"].columns


def test_live_archive_rainfall():
    cfg = get_config()
    adapter = OpenMeteoArchiveAdapter(config=cfg)
    r = adapter.get_rainfall(7.342, 134.478, "2023-01-01", "2023-12-31")
    assert r["ok"], f"live archive failed: {r.get('error')}"
    assert r["n_days"] >= 350


def test_live_oni():
    adapter = CpcOniAdapter()
    r = adapter.get_oni()
    assert r["ok"], f"live ONI failed: {r.get('error')}"
    assert r["latest"]["anom"] != 0.0
    assert r["phase"] in ("el_nino", "la_nina", "neutral")
    assert len(r["series"]) > 900  # 1950 -> present


def test_live_jma_active_storms():
    adapter = JmaTyphoonAdapter()
    r = adapter.active_storms()
    assert r["ok"], f"live JMA failed: {r.get('error')}"
    assert r["n_active"] >= 0
    # if there is an active storm, its details must be fetchable
    for storm in r["storms"][:2]:
        d = adapter.storm_details(storm["tc_id"])
        assert d["ok"], f"JMA storm details failed: {d.get('error')}"
        assert d["analysis"].get("position") is not None


def test_live_ibtracs_fas_tracks():
    adapter = IbtracsAdapter()
    r = adapter.get_tracks(bbox=FAS_BBOX)
    assert r["ok"], f"live IBTrACS failed: {r.get('error')}"
    assert r["n_storms"] > 0
    assert r["n_points"] > 0
