"""Spatial aggregation of per-location values to island/state/country level."""

from __future__ import annotations

import pandas as pd

from .registry import GeographyRegistry


def aggregate_by(
    registry: GeographyRegistry,
    values: pd.DataFrame,
    geo_id_col: str = "geo_id",
    value_col: str = "value",
    method: str = "mean",
) -> pd.DataFrame:
    """Aggregate per-location values up the hierarchy to every parent level.

    ``values`` must contain ``geo_id`` and ``value`` columns. The result includes
    one row per entity at each hierarchy level. Aggregation is simple
    mean/min/max (area-weighting is a planned enhancement requiring polygons).
    """
    if method not in ("mean", "min", "max", "sum"):
        raise ValueError(f"Unsupported aggregation method: {method}")

    agg = values.groupby(geo_id_col)[value_col].agg(method).to_dict()
    rows = []
    for entity in registry.all():
        leaves = _leaf_descendants(registry, entity.geo_id)
        vals = [agg[g] for g in leaves if g in agg]
        if not vals:
            continue
        if method == "mean":
            v = sum(vals) / len(vals)
        elif method == "min":
            v = min(vals)
        elif method == "max":
            v = max(vals)
        else:
            v = sum(vals)
        rows.append(
            {"geo_id": entity.geo_id, "name": entity.name, value_col: v, "n_leaves": len(vals)}
        )
    return pd.DataFrame(rows)


def _leaf_descendants(registry: GeographyRegistry, geo_id: str) -> list[str]:
    """Return geo_ids of entities in the subtree rooted at geo_id that have values."""
    children = registry.children(geo_id)
    if not children:
        return [geo_id]
    out: list[str] = []
    for c in children:
        out.extend(_leaf_descendants(registry, c.geo_id))
    return out
