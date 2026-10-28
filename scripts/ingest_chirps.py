"""Fetch CHIRPS v3 monthly rainfall for a location and write a Parquet series.

Usage:  uv run python scripts/ingest_chirps.py --geo PAL-KOR [--start 1991-01-01] [--end 2024-12-31]
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
from cofa_forward.ingestion.chirps import ChirpsAdapter  # noqa: E402
from cofa_forward.storage.parquet_store import write_parquet  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geo", default="PAL-KOR")
    parser.add_argument("--start", default="1991-01-01")
    parser.add_argument("--end", default="2024-12-31")
    args = parser.parse_args()

    cfg = get_config()
    registry = GeographyRegistry(cfg.geography_entities())
    entity = registry.by_id(args.geo)
    if entity is None:
        print(f"Unknown geo_id: {args.geo}")
        return 1

    adapter = ChirpsAdapter()
    r = adapter.get_monthly_series(entity.latitude, entity.longitude, args.start, args.end)
    if not r["ok"]:
        print(f"Fetch failed: {r.get('error')}")
        return 1

    print(
        f"CHIRPS {entity.name}: {r['n_months']} months, {r['n_missing']} masked/missing "
        f"({r['spatial_resolution']})."
    )
    cfg.ensure_data_dirs()
    out = cfg.data_dir("processed") / f"chirps_{entity.geo_id}.parquet"
    write_parquet(r["series"].reset_index().rename(columns={"index": "date"}), out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
