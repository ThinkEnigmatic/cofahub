"""Build per-location climatology tables (from archive data when available, else sample).

Usage:  uv run python scripts/build_climatology.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.climate.climatology import compute_location_climatology  # noqa: E402
from cofa_forward.config import get_config  # noqa: E402
from cofa_forward.sample_data import synthetic_daily_rainfall  # noqa: E402
from cofa_forward.storage.parquet_store import write_parquet  # noqa: E402


def main() -> int:
    cfg = get_config()
    d = cfg.drought
    cfg.ensure_data_dirs()

    for e in cfg.geography_entities():
        # Prefer processed archive data; fall back to synthetic sample (clearly labeled).
        processed = cfg.data_dir("processed") / f"rainfall_{e.geo_id}.parquet"
        if processed.exists():
            import pandas as pd

            df = pd.read_parquet(processed)
            daily = pd.Series(df["precip_mm"].values, index=pd.to_datetime(df["date"], utc=True))
            label = "archive"
        else:
            daily = synthetic_daily_rainfall(e.geo_id)
            label = "sample"

        clim = compute_location_climatology(
            daily, d["baseline_start"], d["baseline_end"], d["baseline_min_years"]
        )
        out = {
            "geo_id": e.geo_id,
            "label": label,
            "baseline_valid": clim["baseline_valid"],
            "latest_month": str(clim["latest"]["month"])
            if clim["latest"]["month"] is not None
            else None,
            "latest_total_mm": clim["latest"]["total_mm"],
            "anomaly_pct": clim["latest"]["anomaly_pct"],
            "percentile": clim["latest"]["percentile"],
        }
        rows = [out]
        import pandas as pd

        df_out = pd.DataFrame(rows)
        write_parquet(df_out, cfg.data_dir("processed") / f"climatology_{e.geo_id}.parquet")
        print(f"{e.geo_id:<10} {label:<8} baseline_valid={clim['baseline_valid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
