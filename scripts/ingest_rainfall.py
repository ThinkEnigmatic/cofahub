"""Fetch historical daily rainfall (ERA5 archive) for a registry location.

Usage:  uv run python scripts/ingest_rainfall.py --geo PAL-KOR --start 1991-01-01 --end 2020-12-31
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
from cofa_forward.ingestion.rainfall import OpenMeteoArchiveAdapter  # noqa: E402
from cofa_forward.storage.cache import FileCache  # noqa: E402
from cofa_forward.storage.database import Database  # noqa: E402
from cofa_forward.storage.parquet_store import write_parquet  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geo", default="PAL-KOR")
    parser.add_argument("--start", default="1991-01-01")
    parser.add_argument("--end", default="2020-12-31")
    args = parser.parse_args()

    cfg = get_config()
    registry = GeographyRegistry(cfg.geography_entities())
    entity = registry.by_id(args.geo)
    if entity is None:
        print(f"Unknown geo_id: {args.geo}")
        return 1

    cfg.ensure_data_dirs()
    cache = FileCache(cfg.data_dir("cache"), cfg.cache_ttl_seconds)
    db = Database(cfg.data_root / "catalog.db")

    adapter = OpenMeteoArchiveAdapter(config=cfg, cache=cache, db=db)
    result = adapter.get_rainfall(entity.latitude, entity.longitude, args.start, args.end)

    if not result.get("ok"):
        print(f"Fetch failed: {result.get('error')}")
        return 1

    series = result["series"].to_frame("precip_mm")
    series["geo_id"] = entity.geo_id
    out = cfg.data_dir("processed") / f"rainfall_{entity.geo_id}.parquet"
    write_parquet(series.reset_index().rename(columns={"index": "date"}), out)

    print(f"OK {entity.name}: {result['n_days']} days ({result['n_missing']} missing) -> {out}")
    print(f"resolution={result['spatial_resolution']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
