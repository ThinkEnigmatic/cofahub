"""NASA GPM IMERG precipitation adapter (Earthdata login required).

IMERG provides global 0.1° satellite precipitation. Access requires a free NASA
Earthdata account; ``earthaccess`` handles authentication (``.netrc`` or
interactive). This adapter is for near-real-time daily rainfall extraction — for
historical climatology CHIRPS/ERA5 (already integrated) are more practical
(IMERG granules are large and global).

Status: ``implemented_but_not_verified`` — unit-tested with mocks; live
verification requires Earthdata credentials (not present in this environment).
"""

from __future__ import annotations

import numpy as np

from .base import BaseAdapter

SHORT_NAME = "GPM_3IMERGDF"  # IMERG Final Run, daily

_PRECIP_VARS = ("precipitationCal", "precipitation", "GPM_3IMERGDF")


def extract_precip(ds, lat: float, lon: float) -> float:
    """Extract daily precipitation at the nearest grid cell from an IMERG dataset."""
    lat_arr = ds["lat"].values if "lat" in ds else ds["latitude"].values
    lon_arr = ds["lon"].values if "lon" in ds else ds["longitude"].values
    lat_i = int(np.abs(lat_arr - lat).argmin())
    lon_i = int(np.abs(lon_arr - lon).argmin())
    for var in _PRECIP_VARS:
        if var in ds:
            return float(ds[var].isel(lat=lat_i, lon=lon_i).values)
    raise KeyError(f"no precipitation variable found (looked for {_PRECIP_VARS})")


class ImergAdapter(BaseAdapter):
    source_id = "nasa-gpm-imerg"
    source_url = "https://gpm.nasa.gov/data/imerg"
    implementation_status = "implemented_but_not_verified"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 60.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def login(self, strategy: str = "netrc"):
        """Authenticate with NASA Earthdata. Returns the auth session."""
        import earthaccess

        return earthaccess.login(strategy=strategy)

    def get_recent_daily(self, lat: float, lon: float, start: str, end: str) -> dict:
        """Fetch daily IMERG precipitation at a point over [start, end].

        Downloads the (global) daily granules for the requested days via
        earthaccess and extracts the nearest grid cell. Requires prior
        ``earthaccess.login`` (or ``.netrc`` credentials).
        """
        import earthaccess

        try:
            results = earthaccess.search_data(
                short_name=SHORT_NAME,
                temporal=(start, end),
                count=60,
            )
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": f"search failed (is Earthdata authenticated?): {exc}",
                "source": self.source_id,
            }
        if not results:
            return {"ok": False, "error": "no granules found", "source": self.source_id}

        values = []
        try:
            datasets = earthaccess.open(results)
            for ds in datasets:
                values.append(extract_precip(ds, lat, lon))
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"extraction failed: {exc}", "source": self.source_id}

        import pandas as pd

        times = [g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"] for g in results]
        series = pd.Series(values, index=pd.to_datetime(times), name="precip_mm")
        return {
            "ok": True,
            "source": self.source_id,
            "series": series.sort_index(),
            "n_days": int(len(series)),
            "spatial_resolution": "0.1 deg (~11 km)",
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "nearest_grid_cell extraction of IMERG daily",
                "notes": "Satellite estimate; Earthdata login required.",
            },
        }

    def check_availability(self):
        return {
            "source_id": self.source_id,
            "available": False,
            "note": "requires NASA Earthdata login (earthaccess)",
        }
