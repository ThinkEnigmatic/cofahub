"""Spatial attribution and distance calculations.

Attribution is explicit: we record WHICH method produced a derived value so that
a coarse-grid extraction over an atoll is never presented as atoll-accurate.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

EARTH_RADIUS_KM = 6371.0088


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lon points (tested)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def nearest_grid_cell(
    target_lat: float,
    target_lon: float,
    grid_lats: Sequence[float],
    grid_lons: Sequence[float],
) -> tuple[int, float]:
    """Return the index of the nearest grid cell and its distance (km).

    This is *spatial attribution* of existing model data, not downscaling.
    """
    if len(grid_lats) != len(grid_lons) or len(grid_lats) == 0:
        raise ValueError("grid_lats and grid_lons must be equal-length, non-empty sequences")
    best_idx, best_d = 0, float("inf")
    for i, (glat, glon) in enumerate(zip(grid_lats, grid_lons, strict=True)):
        d = haversine_distance(target_lat, target_lon, glat, glon)
        if d < best_d:
            best_idx, best_d = i, d
    return best_idx, best_d


def point_extraction(value_at_point: float, method: str = "nearest_grid_cell") -> dict:
    """Wrap a point-extracted value with its attribution metadata."""
    return {
        "value": value_at_point,
        "method": method,
        "downscaling": "none",  # never imply downscaling that was not performed
    }


ATTRIBUTION_NOTE = (
    "Regional model estimate; individual-atoll conditions may differ. "
    "Nearest-grid-cell attribution of model output does not make the data atoll-scale accurate."
)
