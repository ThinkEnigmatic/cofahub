"""WorldPop population adapter tests (offline extraction + mocked download + live)."""

from __future__ import annotations

import math

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from cofa_forward.ingestion.population import (
    WorldPopAdapter,
    population_at,
    population_within_radius,
)


def _make_tif(path, arr, lon_min, lat_max, res=0.01, nodata=-99999.0):
    transform = from_origin(lon_min, lat_max, res, res)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=arr.shape[0],
        width=arr.shape[1],
        count=1,
        dtype="float32",
        transform=transform,
        crs="EPSG:4326",
        nodata=nodata,
    ) as dst:
        dst.write(arr.astype("float32"), 1)
    return str(path)


def test_population_at_nearest_cell(tmp_path):
    arr = np.full((10, 10), -99999.0, dtype="float32")
    arr[5, 5] = 42.0
    p = _make_tif(tmp_path / "pop.tif", arr, lon_min=150.0, lat_max=10.0)
    # point near (150.05, 9.95) -> pixel (5,5)
    assert math.isclose(population_at(p, lat=9.95, lon=150.05), 42.0)


def test_population_at_nodata_returns_nan(tmp_path):
    arr = np.full((10, 10), -99999.0, dtype="float32")
    p = _make_tif(tmp_path / "pop.tif", arr, lon_min=150.0, lat_max=10.0)
    assert math.isnan(population_at(p, lat=9.95, lon=150.05))


def test_population_within_radius_sums(tmp_path):
    # 10x10 grid, 0.01 deg ~ 1.1 km. Put population on 3 cells near center.
    arr = np.full((10, 10), -99999.0, dtype="float32")
    arr[5, 5] = 10.0
    arr[5, 6] = 20.0
    arr[6, 5] = 30.0
    arr[9, 9] = 999.0  # far away
    p = _make_tif(tmp_path / "pop.tif", arr, lon_min=150.0, lat_max=10.0)
    total = population_within_radius(p, lat=9.95, lon=150.05, radius_km=2.0)
    assert math.isclose(total, 60.0)  # 10+20+30, excludes the far cell


def test_iso3_mapping():
    assert WorldPopAdapter.iso3("PW") == "PLW"
    assert WorldPopAdapter.iso3("FM") == "FSM"
    assert WorldPopAdapter.iso3("MH") == "MHL"
    assert WorldPopAdapter.iso3("XX") == "XX"


@pytest.mark.network
def test_live_worldpop_majuro():
    adapter = WorldPopAdapter()
    # Majuro atoll ~ (7.12N, 171.18E); expect a plausible population within 10 km
    pop = adapter.population_within_radius("MH", 7.12, 171.18, 10.0)
    assert pop > 1000  # Majuro urban population is in the thousands
