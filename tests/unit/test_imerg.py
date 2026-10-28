"""IMERG adapter tests (offline: extract_precip with a synthetic dataset)."""

from __future__ import annotations

import math

import numpy as np
import pytest
import xarray as xr

from cofa_forward.ingestion.imerg import extract_precip


def _synthetic_ds():
    lat = np.linspace(60, -60, 1200)  # 0.1 deg
    lon = np.linspace(-180, 180, 3600)
    precip = np.full((1200, 3600), 2.5, dtype="float32")
    return xr.Dataset(
        {"precipitationCal": (("lat", "lon"), precip)},
        coords={"lat": lat, "lon": lon},
    )


def test_extract_precip():
    ds = _synthetic_ds()
    v = extract_precip(ds, lat=7.3, lon=134.5)
    assert math.isclose(v, 2.5)


def test_extract_precip_fallback_variable():
    ds = _synthetic_ds().rename({"precipitationCal": "precipitation"})
    assert math.isclose(extract_precip(ds, 7.3, 134.5), 2.5)


def test_extract_precip_no_variable_raises():
    ds = xr.Dataset(
        {"other": (("lat", "lon"), np.zeros((3, 3)))},
        coords={"lat": [1.0, 0.0, -1.0], "lon": [0.0, 1.0, 2.0]},
    )
    with pytest.raises(KeyError):
        extract_precip(ds, 0.0, 0.0)
