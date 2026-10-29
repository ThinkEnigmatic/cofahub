"""Offline basemap tile helpers (OpenStreetMap, XYZ scheme).

The macOS app can run fully offline — including map imagery — by pre-fetching
OpenStreetMap tiles into ``data/tiles/{z}/{x}/{y}.png`` and serving them from a
local tile server (``cofa_forward.tileserver``). OSM is used for offline imagery
because it is openly licensed (ODbL, attribution required), permits caching for
light personal use, and extends to high zoom — unlike the satellite basemaps
(Esri has usage restrictions on bulk caching; NASA GIBS true-colour caps at ~zoom
9 where atolls are only a few pixels).

Tiles are stored in the standard OSM/XYZ scheme (``y`` origin at the top/north),
matching ``https://tile.openstreetmap.org/{z}/{x}/{y}.png`` so the offline server
is a drop-in host swap.
"""

from __future__ import annotations

import math
import time
from pathlib import Path

import requests

OSM_TILE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = (
    "COFA-FORWARD/0.3 (personal offline weather-intelligence app; "
    "light one-time tile prefetch; contact: owner)"
)

# Freely Associated States bounding box (lon_min, lat_min, lon_max, lat_max).
FAS_BBOX = (130.0, 0.0, 175.0, 13.0)


def tile_x(lon: float, z: int) -> int:
    """Tile X for a longitude at zoom z (Web Mercator, XYZ)."""
    return int((lon + 180.0) / 360.0 * (1 << z))


def tile_y(lat: float, z: int) -> int:
    """Tile Y for a latitude at zoom z (Web Mercator, XYZ; origin at north)."""
    lat = max(-85.0511, min(85.0511, lat))
    lat_rad = math.radians(lat)
    return int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * (1 << z))


def bbox_tiles(
    lon_min: float, lat_min: float, lon_max: float, lat_max: float, z: int
) -> list[tuple[int, int, int]]:
    """All ``(z, x, y)`` tiles at zoom ``z`` intersecting a lat/lon bounding box."""
    n = 1 << z
    x0 = max(0, tile_x(lon_min, z))
    x1 = min(n - 1, tile_x(lon_max, z))
    y0 = max(0, tile_y(lat_max, z))  # north edge -> smaller y
    y1 = min(n - 1, tile_y(lat_min, z))
    return [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def plan_tiles(
    region_bbox: tuple[float, float, float, float] = FAS_BBOX,
    region_zooms: range | list[int] = range(0, 10),
    points: list[tuple[float, float]] | None = None,
    point_span: float = 0.5,
    point_zooms: range | list[int] = range(10, 12),
) -> list[tuple[int, int, int]]:
    """Plan the tile list: the region bbox across ``region_zooms`` plus a small
    window (``point_span`` degrees) around each ``points`` entry across
    ``point_zooms``. Deduplicates.
    """
    tiles: set[tuple[int, int, int]] = set()
    for z in region_zooms:
        tiles.update(bbox_tiles(*region_bbox, z))
    for z in point_zooms:
        for lat, lon in points or []:
            tiles.update(
                bbox_tiles(
                    lon - point_span, lat - point_span, lon + point_span, lat + point_span, z
                )
            )
    return sorted(tiles)


def fetch_tiles(
    dest_dir: Path | str,
    tiles: list[tuple[int, int, int]],
    *,
    url: str = OSM_TILE,
    delay: float = 1.0,
    timeout: float = 20.0,
) -> dict[str, int]:
    """Download tiles into ``dest_dir/{z}/{x}/{y}.png`` (skipping cached ones).

    Returns counts ``{"ok": n, "cached": n, "missing": n, "failed": n}``. A 404 is
    counted as ``missing`` (no tile written) and is not an error; other HTTP
    failures count as ``failed``. Polite to OSM: a valid User-Agent + a delay.
    """
    dest_dir = Path(dest_dir)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    ok = cached = missing = failed = 0
    for z, x, y in tiles:
        path = dest_dir / str(z) / str(x) / f"{y}.png"
        if path.exists():
            cached += 1
            continue
        try:
            resp = session.get(url.format(z=z, x=x, y=y), timeout=timeout)
            if resp.status_code == 404:
                missing += 1
            elif resp.status_code == 200:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(resp.content)
                ok += 1
            else:
                failed += 1
        except requests.RequestException:
            failed += 1
        time.sleep(delay)
    return {"ok": ok, "cached": cached, "missing": missing, "failed": failed}
