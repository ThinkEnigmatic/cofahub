"""Geography registry and spatial-attribution tests."""

from __future__ import annotations

import math

from cofa_forward.geography.aggregation import aggregate_by, aggregate_by_area
from cofa_forward.geography.spatial_attribution import (
    haversine_distance,
    nearest_grid_cell,
)
from cofa_forward.schemas import GeoEntity


def _ents():
    return [
        GeoEntity(
            geo_id="PAL",
            name="Palau",
            entity_type="country",
            country_code="PW",
            latitude=7.5,
            longitude=134.5,
        ),
        GeoEntity(
            geo_id="PAL-KOR",
            name="Koror",
            entity_type="island",
            country_code="PW",
            parent_geo_id="PAL",
            latitude=7.34,
            longitude=134.48,
        ),
        GeoEntity(
            geo_id="RMI",
            name="Marshall Islands",
            entity_type="country",
            country_code="MH",
            latitude=7.1,
            longitude=171.2,
        ),
    ]


def test_haversine_known():
    # 1 degree of longitude at the equator is ~111.19 km
    d = haversine_distance(0.0, 0.0, 0.0, 1.0)
    assert math.isclose(d, 111.195, rel_tol=1e-3)


def test_haversine_zero():
    assert haversine_distance(10.0, 20.0, 10.0, 20.0) == 0.0


def test_nearest_grid_cell():
    idx, dist = nearest_grid_cell(0.0, 0.0, [0.0, 5.0, 10.0], [0.0, 0.5, 0.0])
    assert idx == 0
    assert dist < 1.0


def test_nearest_grid_cell_validation():
    import pytest

    with pytest.raises(ValueError):
        nearest_grid_cell(0.0, 0.0, [1.0], [])


def test_registry_hierarchy(registry):
    parents = registry.parents("PAL-KOR")
    assert [p.geo_id for p in parents] == ["PAL"]
    path = registry.hierarchy_path("PAL-KOR")
    assert [p.geo_id for p in path] == ["PAL", "PAL-KOR"]
    assert len(registry.countries()) == 3


def test_registry_nearest():
    from cofa_forward.geography.registry import GeographyRegistry

    reg = GeographyRegistry(_ents())
    ent, dist = reg.nearest(7.35, 134.48)
    assert ent.geo_id == "PAL-KOR"
    assert dist < 5.0


def test_aggregation(tmp_path):
    import pandas as pd

    from cofa_forward.geography.registry import GeographyRegistry

    reg = GeographyRegistry(_ents())
    values = pd.DataFrame(
        [
            {"geo_id": "PAL-KOR", "value": 10.0},
        ]
    )
    out = aggregate_by(reg, values, value_col="value", method="mean")
    kor = out[out["geo_id"] == "PAL-KOR"].iloc[0]
    assert kor["value"] == 10.0
    # country PAL aggregates its child leaf
    pal = out[out["geo_id"] == "PAL"].iloc[0]
    assert pal["value"] == 10.0


def test_aggregate_by_area_weighted():
    import pandas as pd

    from cofa_forward.geography.registry import GeographyRegistry

    # Two islands under one country with very different areas: the area-weighted
    # mean must tilt toward the larger island, unlike the simple mean.
    ents = [
        GeoEntity(
            geo_id="C",
            name="Country",
            entity_type="country",
            country_code="PW",
            latitude=7.0,
            longitude=134.0,
        ),
        GeoEntity(
            geo_id="C-BIG",
            name="Big",
            entity_type="island",
            country_code="PW",
            parent_geo_id="C",
            latitude=7.0,
            longitude=134.0,
        ),
        GeoEntity(
            geo_id="C-SML",
            name="Small",
            entity_type="island",
            country_code="PW",
            parent_geo_id="C",
            latitude=7.0,
            longitude=134.0,
        ),
    ]
    reg = GeographyRegistry(ents)
    values = pd.DataFrame([{"geo_id": "C-BIG", "value": 100.0}, {"geo_id": "C-SML", "value": 0.0}])
    areas = {"C-BIG": 900.0, "C-SML": 100.0}
    out = aggregate_by_area(reg, values, areas, value_col="value")
    country = out[out["geo_id"] == "C"].iloc[0]
    # Weighted mean = (100*900 + 0*100) / 1000 = 90.0 (simple mean would be 50).
    assert math.isclose(country["value"], 90.0)
    assert country["n_leaves"] == 2

    # A leaf without an area is excluded from the parent's weighted mean.
    out2 = aggregate_by_area(reg, values, {"C-BIG": 900.0}, value_col="value")
    country2 = out2[out2["geo_id"] == "C"].iloc[0]
    assert math.isclose(country2["value"], 100.0)
    assert country2["n_leaves"] == 1
