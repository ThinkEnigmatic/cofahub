"""Fetch current western North Pacific tropical cyclones from JMA RSMC Tokyo.

Usage:  uv run python scripts/ingest_jma.py [--details]
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
from cofa_forward.ingestion.jma import JmaTyphoonAdapter  # noqa: E402
from cofa_forward.storage.cache import FileCache  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--details", action="store_true", help="Print full advisory details per storm."
    )
    args = parser.parse_args()

    cfg = get_config()
    cfg.ensure_data_dirs()
    cache = FileCache(cfg.data_dir("cache"), cfg.cache_ttl_seconds)

    adapter = JmaTyphoonAdapter(cache=cache)
    r = adapter.active_storms()
    if not r["ok"]:
        print(f"Fetch failed: {r['error']}")
        return 1

    print(f"JMA RSMC Tokyo — {r['n_active']} active storm(s)")
    for s in r["storms"]:
        print(f"  {s['tc_id']}  Typhoon {s['typhoon_number']}  category={s['category']}")

    if args.details:
        for s in r["storms"]:
            d = adapter.storm_details(s["tc_id"])
            if not d["ok"]:
                print(f"  {s['tc_id']}: details failed: {d['error']}")
                continue
            print(
                json.dumps(
                    {
                        "name": d["meta"].get("name_en"),
                        "analysis": d["analysis"],
                        "forecast_points": len(d["forecasts"]),
                    },
                    default=str,
                    indent=2,
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
