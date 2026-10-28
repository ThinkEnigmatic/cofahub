"""Geographic registry.

Loads entities from config and provides lookups and hierarchy traversal. The
registry is data-driven: a complete, validated FAS inventory can replace the
seed YAML without changing this code.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from ..schemas import GeoEntity


class GeographyRegistry:
    def __init__(self, entities: Iterable[GeoEntity]):
        self._by_id: dict[str, GeoEntity] = {e.geo_id: e for e in entities}
        self._children: dict[str | None, list[str]] = {}
        for e in entities:
            self._children.setdefault(e.parent_geo_id, []).append(e.geo_id)

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, geo_id: str) -> bool:
        return geo_id in self._by_id

    def by_id(self, geo_id: str) -> GeoEntity | None:
        return self._by_id.get(geo_id)

    def all(self) -> list[GeoEntity]:
        return list(self._by_id.values())

    def children(self, parent_id: str | None) -> list[GeoEntity]:
        ids = self._children.get(parent_id, [])
        return [self._by_id[i] for i in ids if i in self._by_id]

    def countries(self) -> list[GeoEntity]:
        return [e for e in self._by_id.values() if e.entity_type == "country"]

    def of_type(self, entity_type: str) -> list[GeoEntity]:
        return [e for e in self._by_id.values() if e.entity_type == entity_type]

    def parents(self, geo_id: str) -> list[GeoEntity]:
        """Return the ancestor chain (root-most first), excluding the entity itself."""
        chain: list[GeoEntity] = []
        current = self._by_id.get(geo_id)
        seen: set[str] = set()
        while current is not None and current.parent_geo_id and current.parent_geo_id not in seen:
            seen.add(current.parent_geo_id)
            parent = self._by_id.get(current.parent_geo_id)
            if parent is None:
                break
            chain.append(parent)
            current = parent
        return list(reversed(chain))

    def hierarchy_path(self, geo_id: str) -> list[GeoEntity]:
        """Full path root -> entity (inclusive)."""
        path = self.parents(geo_id)
        entity = self._by_id.get(geo_id)
        if entity:
            path.append(entity)
        return path

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([e.model_dump() for e in self._by_id.values()])

    def nearest(self, lat: float, lon: float) -> tuple[GeoEntity, float]:
        """Return the nearest entity and its distance (km) to a point."""
        from .spatial_attribution import haversine_distance

        best: tuple[GeoEntity, float] | None = None
        for e in self._by_id.values():
            d = haversine_distance(lat, lon, e.latitude, e.longitude)
            if best is None or d < best[1]:
                best = (e, d)
        assert best is not None
        return best
