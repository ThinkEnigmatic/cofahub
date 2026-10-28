"""Download and parse IBTrACS WP-basin tracks for the FAS region.

Usage:  uv run python scripts/ingest_ibtracs.py [--write] [--all]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.config import get_config  # noqa: E402
from cofa_forward.ingestion.ibtracs import FAS_BBOX, IbtracsAdapter  # noqa: E402
from cofa_forward.storage.cache import FileCache  # noqa: E402
from cofa_forward.storage.database import Database  # noqa: E402
from cofa_forward.storage.parquet_store import write_parquet  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write tracks to data/processed.")
    parser.add_argument(
        "--all", action="store_true", help="Keep the full WP basin (no FAS bbox filter)."
    )
    args = parser.parse_args()

    cfg = get_config()
    cfg.ensure_data_dirs()
    cache = FileCache(cfg.data_dir("cache"), cfg.cache_ttl_seconds)
    db = Database(cfg.data_root / "catalog.db")

    adapter = IbtracsAdapter(cache=cache, db=db)
    r = adapter.get_tracks(bbox=None if args.all else FAS_BBOX)
    if not r["ok"]:
        print(f"Fetch failed: {r['error']}")
        return 1

    print(
        f"IBTrACS: {r['n_points']} track points, {r['n_storms']} storms "
        f"{'(FAS bbox)' if not args.all else '(full WP basin)'}"
    )
    print(f"source={r['source']} retrieved_at={r['retrieved_at']} from_cache={r['from_cache']}")

    if args.write:
        out = cfg.data_dir("processed") / "ibtracs_fas_tracks.parquet"
        write_parquet(r["tracks"].reset_index(drop=True), out)
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
