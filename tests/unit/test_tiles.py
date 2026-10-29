"""Offline basemap tile helpers (OSM XYZ scheme) tests."""

from __future__ import annotations

from cofa_forward.visualization.tiles import (
    FAS_BBOX,
    bbox_tiles,
    plan_tiles,
    tile_x,
    tile_y,
)


def test_tile_xy_origin():
    # At z=1 the world is 2x2; (lon 0, lat 0) sits in the bottom-right tile.
    assert tile_x(0.0, 1) == 1
    assert tile_y(0.0, 1) == 1


def test_tile_x_monotonic():
    assert tile_x(130.0, 10) < tile_x(175.0, 10)


def test_tile_y_north_smaller():
    # North (larger latitude) -> smaller y (origin at top).
    assert tile_y(13.0, 10) < tile_y(0.0, 10)


def test_bbox_tiles_world_at_z0():
    assert bbox_tiles(*FAS_BBOX, 0) == [(0, 0, 0)]


def test_bbox_tiles_within_bounds():
    tiles = bbox_tiles(*FAS_BBOX, 5)
    n = 1 << 5
    assert tiles
    for z, x, y in tiles:
        assert z == 5
        assert 0 <= x < n and 0 <= y < n


def test_plan_tiles_dedup_and_shape():
    tiles = plan_tiles(
        region_bbox=FAS_BBOX,
        region_zooms=[3],
        points=[(7.1, 171.2)],
        point_span=0.5,
        point_zooms=[3],
    )
    assert len(tiles) == len(set(tiles))  # deduplicated
    assert all(len(t) == 3 for t in tiles)
    # The point window at z3 must include the tile holding (171.2, 7.1).
    assert (3, tile_x(171.2, 3), tile_y(7.1, 3)) in tiles
