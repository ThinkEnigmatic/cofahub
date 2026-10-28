"""CHIRPS adapter tests (offline sample_point + mocked series + live network)."""

from __future__ import annotations

import math

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from cofa_forward.ingestion.chirps import (
    ChirpsAdapter,
    monthly_cog_url,
    sample_point,
)


def _make_tif(path, arr, lon_min, lat_max, res=0.05, nodata=-9999.0):
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
    return path


def test_monthly_cog_url():
    assert monthly_cog_url(2020, 1).endswith("chirps-v3.0.2020.01.cog")
    assert "2020" in monthly_cog_url(2020, 12) and ".12.cog" in monthly_cog_url(2020, 12)


def test_sample_point_max_valid(tmp_path):
    # 10x10 grid, lon 130.., lat 10.. at 0.05 deg. Center nodata, one cell = 123.4
    arr = np.full((10, 10), -9999.0, dtype="float32")
    arr[4, 4] = 123.4
    path = _make_tif(tmp_path / "m.tif", arr, lon_min=130.0, lat_max=10.0)
    # point maps near center (130.2, 9.8) -> center cell is nodata; window max = 123.4
    val = sample_point(str(path), lat=9.8, lon=130.2)
    assert math.isclose(val, 123.4, abs_tol=1e-3)


def test_sample_point_all_nodata_returns_nan(tmp_path):
    arr = np.full((10, 10), -9999.0, dtype="float32")
    path = _make_tif(tmp_path / "m.tif", arr, lon_min=130.0, lat_max=10.0)
    assert math.isnan(sample_point(str(path), lat=9.8, lon=130.2))


def test_sample_point_missing_file_returns_nan():
    assert math.isnan(sample_point("/nonexistent/file.tif", lat=7.0, lon=134.0))


def test_get_monthly_series_mocked(monkeypatch):
    adapter = ChirpsAdapter()

    def fake_sample(url, lat, lon, window=5):
        # return a deterministic value per month (year encoded in URL)
        import re

        m = re.search(r"(\d{4})\.(\d{2})\.cog", url)
        if not m:
            return float("nan")
        return float(m.group(2))  # month number as the value

    monkeypatch.setattr("cofa_forward.ingestion.chirps.sample_point", fake_sample)
    r = adapter.get_monthly_series(7.0, 134.0, "2020-01-01", "2020-03-31")
    assert r["ok"] is True
    assert r["n_months"] == 3
    assert list(r["series"].values) == [1.0, 2.0, 3.0]
    assert r["n_missing"] == 0


@pytest.mark.network
def test_live_chirps_small_window():
    adapter = ChirpsAdapter()
    # Pohnpei is a well-resolved island; July-September are wet months.
    r = adapter.get_monthly_series(6.96, 158.21, "2020-07-01", "2020-09-30")
    assert r["ok"]
    assert r["n_months"] == 3
    vals = r["series"].dropna()
    assert len(vals) > 0
    assert all(v >= 0 for v in vals)
