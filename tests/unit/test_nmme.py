"""NMME adapter tests (offline parse/extract + mocked + live)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from cofa_forward.ingestion.nmme import (
    NmmeAdapter,
    cycle_to_yyyymm,
    extract_point,
    parse_cycle_listing,
    prate_to_mm_day,
    target_months,
)


def test_cycle_to_yyyymm():
    assert cycle_to_yyyymm("oct2026ic") == "202610"
    assert cycle_to_yyyymm("jan2025ic") == "202501"
    assert cycle_to_yyyymm("dec2025ic") == "202512"


def test_parse_cycle_listing_sorted():
    html = '<a href="oct2026ic/"> <a href="jan2026ic/"> <a href="dec2025ic/"> <a href="..">'
    cycles = parse_cycle_listing(html)
    assert cycles[0] == "dec2025ic"
    assert cycles[-1] == "oct2026ic"


def test_target_months():
    months = target_months([801, 802])
    assert str(months[0].date()) == "2026-10-01"
    assert str(months[1].date()) == "2026-11-01"


def _synthetic_ds():
    lat = np.linspace(90, -90, 181)
    lon = np.linspace(0, 359, 360)
    target = np.arange(801, 813)
    fcst = np.zeros((12, 181, 360), dtype="float32")
    fcst[:, :, :] = 1.0  # 1 mm/s everywhere
    return xr.Dataset(
        {"fcst": (("target", "lat", "lon"), fcst)},
        coords={"target": target, "lat": lat, "lon": lon},
    )


def test_extract_point():
    ds = _synthetic_ds()
    s = extract_point(ds, lat=7.3, lon=134.5)
    assert len(s) == 12
    assert s.iloc[0] == 1.0
    assert str(s.index[0].date()) == "2026-10-01"


def test_prate_to_mm_day():
    s = pd.Series([1.0], index=pd.DatetimeIndex(["2026-10-01"]))
    out = prate_to_mm_day(s)
    assert math.isclose(out.iloc[0], 86400.0)


def test_get_forecast_mocked(monkeypatch):
    adapter = NmmeAdapter()
    adapter.raw_dir = __import__("pathlib").Path("/tmp/nmme_cache")

    monkeypatch.setattr(adapter, "latest_cycle", lambda: "oct2026ic")

    def fake_open(url, model, variable, cycle):
        return _synthetic_ds()

    monkeypatch.setattr(adapter, "_open", fake_open)
    r = adapter.get_forecast(7.3, 134.5, variable="prate", model="CanESM5")
    assert r["ok"] is True
    assert r["cycle"] == "oct2026ic"
    assert r["units"] == "mm/day"
    assert len(r["series"]) == 12
    assert math.isclose(r["series"].iloc[0], 86400.0)  # 1 mm/s -> 86400 mm/day


@pytest.mark.network
def test_live_nmme_forecast():
    adapter = NmmeAdapter()
    r = adapter.get_forecast(7.3, 134.5, variable="prate", model="CanESM5")
    assert r["ok"], f"live NMME failed: {r.get('error')}"
    assert len(r["series"]) == 12
    assert r["series"].notna().all()
    # monthly precip at Palau is order ~5-15 mm/day
    assert r["series"].mean() > 0


@pytest.mark.network
def test_live_nmme_multimodel():
    adapter = NmmeAdapter()
    r = adapter.get_multimodel(7.3, 134.5, variable="prate")
    assert r["ok"], f"live NMME multimodel failed: {r.get('error')}"
    assert r["n_models"] >= 2
    assert len(r["ensemble_mean"]) == 12
