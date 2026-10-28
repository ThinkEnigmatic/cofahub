"""Cyclone proximity calculations (tested)."""

from __future__ import annotations

import pandas as pd

from ..geography.spatial_attribution import haversine_distance


def track_distances(lat: float, lon: float, df: pd.DataFrame) -> pd.Series:
    """Distance (km) from a point to every track point."""
    return df.apply(lambda r: haversine_distance(lat, lon, r["lat"], r["lon"]), axis=1)


def closest_approach(lat: float, lon: float, df: pd.DataFrame) -> dict:
    """Minimum distance (km) from a location to a track, with time and index.

    Returns an empty dict if ``df`` is empty.
    """
    if df is None or len(df) == 0:
        return {}
    dist = track_distances(lat, lon, df)
    idx = dist.idxmin()  # index *label* of the closest point
    return {
        "distance_km": float(dist.loc[idx]),
        "time": df.loc[idx, "time"],
        "index": idx,
    }


def within_radius(lat: float, lon: float, df: pd.DataFrame, radius_km: float) -> pd.DataFrame:
    """Subset of track points within ``radius_km`` of a location (sorted by distance)."""
    dist = track_distances(lat, lon, df)
    subset = df[dist <= radius_km].copy()
    subset["distance_km"] = dist[dist <= radius_km]
    return subset.sort_values("distance_km")
