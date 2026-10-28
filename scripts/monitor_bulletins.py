"""Poll bulletin sources and record any new or updated bulletins.

Usage:  uv run python scripts/monitor_bulletins.py [--all]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.config import get_config  # noqa: E402
from cofa_forward.ingestion.bulletins import BulletinMonitor  # noqa: E402
from cofa_forward.storage.cache import FileCache  # noqa: E402
from cofa_forward.storage.database import Database  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Also print unchanged sources.")
    args = parser.parse_args()

    cfg = get_config()
    cfg.ensure_data_dirs()
    cache = FileCache(cfg.data_dir("cache"), cfg.cache_ttl_seconds)
    db = Database(cfg.data_root / "catalog.db")

    monitor = BulletinMonitor(cfg, cache=cache, db=db)
    updates = monitor.check_all()

    print(f"Bulletin monitor: {len(updates)} new/updated bulletin(s).")
    for u in updates:
        print(f"  NEW  {u['name']} ({u['source_id']}) @ {u['retrieved_at']}")
        print(f"       {json.dumps(u['summary'], ensure_ascii=False, default=str)}")

    if args.all:
        for s in cfg.bulletin_sources():
            r = monitor.check(s)
            if not r.get("changed"):
                print(f"  same {s['name']} ({s['id']}) — no change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
