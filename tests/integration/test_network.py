"""Live network integration tests (marked ``network``; skipped by default).

Run explicitly with:  uv run pytest -m network
"""

from __future__ import annotations

import pytest

from cofa_forward.config import get_config
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
