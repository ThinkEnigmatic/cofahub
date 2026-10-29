"""Prefetch OpenStreetMap basemap tiles for offline use.

Downloads OSM tiles covering the Freely Associated States region (low zoom) plus
a window around each registry location (higher zoom) into ``data/tiles/``, served
offline by ``cofa_forward.tileserver``.

Usage:
    uv run python scripts/prefetch_tiles.py [--region-zoom-max 9] \
        [--point-zoom-min 10 --point-zoom-max 12]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.config import get_config  # noqa: E402
from cofa_forward.geography.registry import GeographyRegistry  # noqa: E402
from cofa_forward.visualization.tiles import FAS_BBOX, fetch_tiles, plan_tiles  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region-zoom-max", type=int, default=9)
    parser.add_argument("--point-zoom-min", type=int, default=10)
    parser.add_argument("--point-zoom-max", type=int, default=11)
    args = parser.parse_args()

    cfg = get_config()
    registry = GeographyRegistry(cfg.geography_entities())
    points = [(e.latitude, e.longitude) for e in registry.all()]

    tiles = plan_tiles(
        region_bbox=FAS_BBOX,
        region_zooms=range(0, args.region_zoom_max + 1),
        points=points,
        point_zooms=range(args.point_zoom_min, args.point_zoom_max + 1),
    )

    dest = cfg.data_root / "tiles"
    print(
        f"Prefetching {len(tiles)} OSM tiles "
        f"(region z0-{args.region_zoom_max}, {len(points)} points "
        f"z{args.point_zoom_min}-{args.point_zoom_max}) → {dest}"
    )
    result = fetch_tiles(dest, tiles)
    print(
        f"  ok={result['ok']} cached={result['cached']} "
        f"missing={result['missing']} failed={result['failed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
