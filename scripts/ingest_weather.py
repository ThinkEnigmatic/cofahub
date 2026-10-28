"""Fetch a live forecast for a registry location and store it.

Usage:  uv run python scripts/ingest_weather.py --geo PAL-KOR [--days 16]
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
from cofa_forward.ingestion.weather import OpenMeteoForecastAdapter  # noqa: E402
from cofa_forward.storage.cache import FileCache  # noqa: E402
from cofa_forward.storage.database import Database  # noqa: E402
from cofa_forward.storage.parquet_store import write_parquet  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geo", default="PAL-KOR", help="Registry geo_id")
    parser.add_argument("--days", type=int, default=16)
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

    adapter = OpenMeteoForecastAdapter(config=cfg, cache=cache, db=db)
    result = adapter.get_forecast(entity.latitude, entity.longitude, forecast_days=args.days)

    if not result.get("ok"):
        print(f"Fetch failed: {result.get('error')}")
        return 1

    hourly = result["hourly"].copy()
    hourly["geo_id"] = entity.geo_id
    out = cfg.data_dir("processed") / f"forecast_{entity.geo_id}.parquet"
    write_parquet(hourly.reset_index().rename(columns={"index": "time"}), out)

    print(f"OK {entity.name}: {len(result['hourly'])} hourly rows -> {out}")
    print(
        f"source={result['source']} retrieved_at={result['retrieved_at']} "
        f"from_cache={result.get('from_cache')}"
    )
    print(f"current={ {k: v for k, v in result['current'].items()} }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
