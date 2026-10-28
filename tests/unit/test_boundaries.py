"""Boundaries adapter tests (offline: synthetic SHP + GeoTIFF)."""

from __future__ import annotations

import math

import numpy as np
import rasterio
import shapefile
from rasterio.transform import from_origin

from cofa_forward.ingestion.boundaries import (
    parse_admin_shp,
    parse_geojson,
    zonal_population,
)


def _write_shp(path: str, points, name: str, pcode: str, level: int = 1) -> str:
    w = shapefile.Writer(path, shapeType=shapefile.POLYGON)
    w.field(f"ADM{level}_EN", "C")
    w.field(f"ADM{level}_PCODE", "C")
    w.poly([points])
    w.record(name, pcode)
    w.close()
    return path


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


def test_parse_admin_shp(tmp_path):
    p = _write_shp(
        str(tmp_path / "adm1.shp"),
        [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)],
        "Test Atoll",
        "XX01",
        level=1,
    )
    records = parse_admin_shp(p, 1)
    assert len(records) == 1
    assert records[0]["name"] == "Test Atoll"
    assert records[0]["pcode"] == "XX01"
    assert records[0]["geometry"]["type"] == "Polygon"


def test_zonal_population_full_and_empty(tmp_path):
    arr = np.full((10, 10), 10.0, dtype="float32")  # total 1000
    p = _make_tif(tmp_path / "wp.tif", arr, lon_min=150.0, lat_max=10.0, res=0.01)
    full = {
        "type": "Polygon",
        "coordinates": [[[150.0, 10.0], [150.1, 10.0], [150.1, 9.9], [150.0, 9.9], [150.0, 10.0]]],
    }
    assert math.isclose(zonal_population(full, p), 1000.0, rel_tol=0.05)

    far = {
        "type": "Polygon",
        "coordinates": [[[160.0, 10.0], [160.1, 10.0], [160.1, 9.9], [160.0, 9.9], [160.0, 10.0]]],
    }
    assert zonal_population(far, p) == 0.0


def test_zonal_population_ignores_nodata(tmp_path):
    arr = np.full((10, 10), -99999.0, dtype="float32")
    arr[2:5, 2:5] = 5.0  # 9 cells * 5 = 45 in the center
    p = _make_tif(tmp_path / "wp.tif", arr, lon_min=150.0, lat_max=10.0, res=0.01)
    center = {
        "type": "Polygon",
        "coordinates": [
            [[150.02, 9.98], [150.05, 9.98], [150.05, 9.95], [150.02, 9.95], [150.02, 9.98]]
        ],
    }
    val = zonal_population(center, p)
    assert val > 0
    assert val <= 45.0


def test_parse_geojson():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "properties": {"shapeName": "Koror", "shapeISO": "PW-150"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[134.4, 7.3], [134.5, 7.3], [134.5, 7.4], [134.4, 7.3]]],
                },
            }
        ],
    }
    records = parse_geojson(geojson)
    assert len(records) == 1
    assert records[0]["name"] == "Koror"
    assert records[0]["pcode"] == "PW-150"
    assert records[0]["geometry"]["type"] == "Polygon"
