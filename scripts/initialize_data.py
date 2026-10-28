"""Generate clearly-labeled sample datasets into data/samples/.

Usage:  uv run python scripts/initialize_data.py [--force]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.config import get_config  # noqa: E402
from cofa_forward.sample_data import (  # noqa: E402
    synthetic_daily_rainfall,
    synthetic_forecast,
    synthetic_impacts,
    synthetic_tracks,
)
from cofa_forward.storage.parquet_store import write_parquet  # noqa: E402


def build_sample_data() -> dict[str, Path]:
    cfg = get_config()
    cfg.ensure_data_dirs()
    samples = cfg.data_dir("samples")
    registry = list(cfg.geography_entities())

    rainfall_frames = []
    for e in registry:
        s = synthetic_daily_rainfall(e.geo_id).to_frame("precip_mm")
        s["geo_id"] = e.geo_id
        s["label"] = "sample"
        rainfall_frames.append(s)

    import pandas as pd

    rainfall = pd.concat(rainfall_frames)
    rainfall.index.name = "date"

    forecast = synthetic_forecast("PAL-KOR", 7.342, 134.478)
    tracks = synthetic_tracks()
    impacts = synthetic_impacts()

    paths = {
        "rainfall": write_parquet(rainfall.reset_index(), samples / "rainfall_sample.parquet"),
        "forecast": write_parquet(forecast, samples / "forecast_sample.parquet"),
        "tracks": write_parquet(tracks, samples / "tracks_sample.parquet"),
        "impacts": samples / "impacts_sample.csv",
    }
    impacts.to_csv(paths["impacts"], index=False)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate sample datasets.")
    parser.add_argument("--force", action="store_true", help="Regenerate even if present.")
    args = parser.parse_args()

    cfg = get_config()
    samples = cfg.data_dir("samples")
    marker = samples / "rainfall_sample.parquet"
    if marker.exists() and not args.force:
        print(f"Sample data already exists at {samples}; use --force to regenerate.")
        return 0

    paths = build_sample_data()
    for name, p in paths.items():
        print(f"wrote {name}: {p}")
    print("Done. Sample data is clearly labeled and never confused with live data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
