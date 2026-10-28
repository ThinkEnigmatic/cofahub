"""Fetch the authoritative CPC Oceanic Niño Index and derive the current phase.

Usage:  uv run python scripts/ingest_enso.py [--write]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.config import get_config  # noqa: E402
from cofa_forward.ingestion.enso import CpcOniAdapter  # noqa: E402
from cofa_forward.storage.cache import FileCache  # noqa: E402
from cofa_forward.storage.database import Database  # noqa: E402
from cofa_forward.storage.parquet_store import write_parquet  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write", action="store_true", help="Write the ONI series to data/processed."
    )
    args = parser.parse_args()

    cfg = get_config()
    cfg.ensure_data_dirs()
    cache = FileCache(cfg.data_dir("cache"), cfg.cache_ttl_seconds)
    db = Database(cfg.data_root / "catalog.db")

    adapter = CpcOniAdapter(cache=cache, db=db)
    r = adapter.get_oni()
    if not r["ok"]:
        print(f"Fetch failed: {r['error']}")
        return 1

    latest = r["latest"]
    print(
        f"ONI: {latest['season']} {latest['year']} = {latest['anom']:+.2f} °C "
        f"(as of {latest['date']})"
    )
    print(f"Derived phase: {r['phase']} ({r['persistence_seasons']} consecutive seasons)")
    print(f"source={r['source']} retrieved_at={r['retrieved_at']} from_cache={r['from_cache']}")

    if args.write:
        out = cfg.data_dir("processed") / "oni.parquet"
        write_parquet(r["series"].reset_index(drop=True), out)
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
