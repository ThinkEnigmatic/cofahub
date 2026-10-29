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

import os
from pathlib import Path

import numpy as np

from .base import BaseAdapter

SHORT_NAME = "GPM_3IMERGDF"  # IMERG Final Run, daily (historical; ~3.5-month lag)
EARLY_SHORT_NAME = "GPM_3IMERGHHE"  # IMERG Early Run (near-real-time; ~4-hour lag)
LATE_SHORT_NAME = "GPM_3IMERGHHL"  # IMERG Late Run (near-real-time; ~14-hour lag)

_TOKEN_FILE = Path.home() / ".config" / "cofa-forward" / "earthdata_token"


def ensure_earthdata_token() -> None:
    """Load the Earthdata bearer token from the local token file if not in env.

    Makes the adapter self-contained: the operator stores the EDL bearer token at
    ``~/.config/cofa-forward/earthdata_token`` (0600) and it is exported as
    ``EARTHDATA_TOKEN`` automatically. The token is short-lived (~1 hour), so it
    must be refreshed periodically; this only avoids a manual export per process.
    """
    if os.environ.get("EARTHDATA_TOKEN"):
        return
    if _TOKEN_FILE.is_file():
        token = _TOKEN_FILE.read_text(encoding="utf-8").strip()
        if token:
            os.environ["EARTHDATA_TOKEN"] = token


_PRECIP_VARS = ("precipitation", "precipitationCal", "GPM_3IMERGDF")


def extract_precip(ds, lat: float, lon: float) -> float:
    """Extract daily precipitation at the nearest grid cell from an IMERG dataset.

    Handles a singleton ``time`` dimension and either ``(lat, lon)`` or
    ``(lon, lat)`` ordering (selection is by named dimension).
    """
    lat_arr = ds["lat"].values if "lat" in ds else ds["latitude"].values
    lon_arr = ds["lon"].values if "lon" in ds else ds["longitude"].values
    lat_i = int(np.abs(lat_arr - lat).argmin())
    lon_i = int(np.abs(lon_arr - lon).argmin())
    for var in _PRECIP_VARS:
        if var in ds:
            arr = ds[var].isel(lat=lat_i, lon=lon_i)
            if "time" in arr.dims:
                arr = arr.squeeze("time")
            return float(arr.values)
    raise KeyError(f"no precipitation variable found (looked for {_PRECIP_VARS})")


class ImergAdapter(BaseAdapter):
    source_id = "nasa-gpm-imerg"
    source_url = "https://gpm.nasa.gov/data/imerg"
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 60.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def login(self, strategy: str = "all"):
        """Authenticate with NASA Earthdata. Returns the auth session.

        Supports the EDL bearer token via the ``EARTHDATA_TOKEN`` environment
        variable (the "environment" strategy) or ``~/.netrc`` / interactive.
        """
        import earthaccess

        return earthaccess.login(strategy=strategy)

    def get_recent_daily(
        self, lat: float, lon: float, start: str, end: str, product: str = "final"
    ) -> dict:
        """Fetch daily IMERG precipitation at a point over [start, end].

        ``product`` selects the run: ``"final"`` (GPM_3IMERGDF, ~3.5-month lag,
        default), ``"early"`` (GPM_3IMERGHHE, ~4-hour lag), or ``"late"``
        (GPM_3IMERGHHL, ~14-hour lag). For near-real-time use ``"early"``/``"late"``;
        ``"final"`` only extends to a few months ago.

        Requires authentication (``EARTHDATA_TOKEN`` or ``~/.netrc``) AND a one-time
        acceptance of the GPM IMERG End User License Agreement (EULA) via the
        browser at https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ
        (the API returns HTTP 403 "EULA Acceptance Failure" until accepted).
        """
        import earthaccess

        short_name = {
            "final": SHORT_NAME,
            "early": EARLY_SHORT_NAME,
            "late": LATE_SHORT_NAME,
        }.get(product, product)

        ensure_earthdata_token()
        try:
            earthaccess.login(strategy="all")
            results = earthaccess.search_data(
                short_name=short_name,
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
            import xarray as xr

            files = earthaccess.open(results)
            for f in files:
                ds = xr.open_dataset(f, engine="h5netcdf")
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
            "available": True,
            "note": "live GPM IMERG (Earthdata token/.netrc)",
        }
