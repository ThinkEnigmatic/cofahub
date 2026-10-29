"""Leaflet (folium) map builder tests — offline, no tile fetch."""

from __future__ import annotations

import pandas as pd

from cofa_forward.config import get_config
from cofa_forward.geography.registry import GeographyRegistry
from cofa_forward.visualization.leaflet_maps import (
    BASEMAPS,
    _gibs_date,
    _resolved_basemap,
    metric_map,
    region_map,
    track_map,
)


def _registry() -> GeographyRegistry:
    cfg = get_config()
    return GeographyRegistry(cfg.geography_entities())


def test_basemaps_include_nasa_and_esri():
    assert any("Esri" in k for k in BASEMAPS)
    assert any("NASA" in k for k in BASEMAPS)
    assert any("OpenStreetMap" in k for k in BASEMAPS)


def test_resolved_basemap_dated_layer_has_url():
    spec = _resolved_basemap("NASA MODIS Terra (daily)")
    assert spec["url"].startswith("https://gibs.earthdata.nasa.gov/")
    assert "{z}" in spec["url"] and "{x}" in spec["url"] and "{y}" in spec["url"]


def test_gibs_date_is_iso():
    d = _gibs_date()
    assert len(d) == 10 and d.count("-") == 2


def test_region_map_builds_folium_map():
    m = region_map(_registry(), center=(6.5, 152.0))
    html = m.get_root().render()
    assert "arcgisonline" in html  # Esri satellite basemap present
    assert "gibs.earthdata.nasa.gov" in html  # NASA GIBS basemap present


def test_region_map_renders_boundaries():
    boundaries = [
        {
            "geo_id": "RMI-MAJ",
            "name": "Majuro",
            "country_code": "MH",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[171.0, 7.0], [171.3, 7.0], [171.3, 7.2], [171.0, 7.0]]],
            },
        }
    ]
    m = region_map(_registry(), center=(6.5, 152.0), boundaries=boundaries)
    html = m.get_root().render()
    assert "Majuro" in html
    assert "Administrative boundaries" in html


def test_region_map_empty_boundaries_ok():
    m = region_map(_registry(), center=(6.5, 152.0), boundaries=[])
    assert m.get_root().render()  # no exception


def test_track_map_adds_polylines():
    tracks = pd.DataFrame(
        {
            "storm_id": ["S1", "S1", "S1"],
            "time": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"], utc=True),
            "lat": [7.0, 8.0, 9.0],
            "lon": [134.0, 135.0, 136.0],
            "wind_kt": [30, 40, 50],
        }
    )
    m = track_map(tracks, center=(6.5, 152.0))
    html = m.get_root().render()
    assert "S1" in html


def test_metric_map_colors_missing_values_grey():
    m = metric_map(_registry(), values={"PAL": 1.0}, center=(6.5, 152.0))
    html = m.get_root().render()
    assert "#9ca3af" in html  # grey for missing
