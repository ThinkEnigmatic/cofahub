"""Location exposure to tropical cyclone tracks."""

from __future__ import annotations

import pandas as pd

from ..geography.registry import GeographyRegistry
from .proximity import closest_approach


def exposed_locations(
    registry: GeographyRegistry,
    track_df: pd.DataFrame,
    radius_km: float,
) -> list[dict]:
    """Return registry locations whose closest approach to the track is within a radius.

    Each result records the closest-approach distance and time. This is a
    proximity exposure estimate only — it does NOT estimate wind impacts, which
    require storm size, intensity, and track uncertainty.
    """
    out = []
    for entity in registry.all():
        ca = closest_approach(entity.latitude, entity.longitude, track_df)
        if not ca or ca["distance_km"] > radius_km:
            continue
        out.append(
            {
                "geo_id": entity.geo_id,
                "name": entity.name,
                "distance_km": round(ca["distance_km"], 1),
                "closest_time": ca["time"],
            }
        )
    out.sort(key=lambda x: x["distance_km"])
    return out


def exposure_summary(
    registry: GeographyRegistry,
    track_df: pd.DataFrame,
    thresholds_km: list[int],
) -> list[dict]:
    """Count locations within each approach threshold for a track."""
    out = []
    for r in thresholds_km:
        locs = exposed_locations(registry, track_df, r)
        out.append(
            {"radius_km": r, "n_locations": len(locs), "locations": [loc["name"] for loc in locs]}
        )
    return out
