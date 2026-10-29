"""PERSIANN-CDR precipitation adapter (NOAA Climate Data Record).

PERSIANN-CDR is a satellite-gauge-blended daily precipitation CDR (0.25°, 60S–60N,
1983–present, NOAA NCEI). It complements CHIRPS (which is land-masked) by covering
the ocean-adjacent atolls of the FAS. Daily netCDF files are served over plain HTTP
with byte-range support, so point extraction uses xarray over HTTP (no download).

Note: PERSIANN-CDR lags ~3–6 months behind real time (a "Final"-style CDR), so it is
for climatology / historical analysis, not nowcasting.
"""

from __future__ import annotations

import re
import tempfile
from datetime import date, timedelta
from typing import Any

import requests

from .base import BaseAdapter

_BASE = "https://www.ncei.noaa.gov/data/precipitation-persiann/access"


def _file_url(d: date, session: requests.Session | None = None) -> str:
    """Resolve a day's netCDF URL. The ``_cYYYYMMDD`` creation suffix varies per
    file, so list the year directory and match the day prefix."""
    stamp = d.strftime("%Y%m%d")
    prefix = f"PERSIANN-CDR_v01r01_{stamp}_c"
    url = f"{_BASE}/{d.year}/{prefix}.nc"
    return url


def _resolve_file_url(d: date, timeout: float = 30.0) -> str | None:
    """Find the exact filename for a day by listing its year directory."""
    stamp = d.strftime("%Y%m%d")
    listing_url = f"{_BASE}/{d.year}/"
    try:
        resp = requests.get(listing_url, timeout=timeout)
        resp.raise_for_status()
        m = re.search(rf'href="(PERSIANN-CDR_v01r01_{stamp}_c\d+\.nc)"', resp.text)
        if m:
            return f"{_BASE}/{d.year}/{m.group(1)}"
    except requests.RequestException:
        pass
    return None


def _fetch_cell(url: str, lat: float, lon: float, timeout: float = 60.0) -> float:
    """Download one day's netCDF and extract the nearest-cell value (mm)."""
    import xarray as xr

    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=True) as tmp:
        tmp.write(resp.content)
        tmp.flush()
        ds = xr.open_dataset(tmp.name, engine="netcdf4")
        with ds:
            v = ds["precipitation"].sel(lat=float(lat), lon=float(lon), method="nearest")
            # Point selection still carries the (size-1) time dimension.
            arr = v.values
            if getattr(arr, "ndim", 1) > 0:
                arr = arr.reshape(-1)
            val = float(arr[0]) if arr.size else float("nan")
            if val == val:  # not NaN
                return val
            return float("nan")


class PersiannCdrAdapter(BaseAdapter):
    source_id = "persiann-cdr"
    source_url = "https://www.ncei.noaa.gov/data/precipitation-persiann/access/"
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 60.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def get_daily(self, lat: float, lon: float, d: date) -> dict[str, Any]:
        """Extract one day's precipitation (mm) at a point (nearest 0.25° cell)."""
        url = _resolve_file_url(d, timeout=self.timeout)
        if url is None:
            return {"ok": False, "error": f"no file for {d.isoformat()}", "source": self.source_id}
        try:
            value = _fetch_cell(url, lat, lon, timeout=self.timeout)
        except Exception as exc:  # noqa: BLE001 - network/parse errors surface here
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "source": self.source_id}

        return {
            "ok": True,
            "source": self.source_id,
            "source_url": url,
            "date": d.isoformat(),
            "precip_mm": value,
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": url,
                "calculation_method": "nearest-grid-cell attribution (0.25°)",
                "notes": "PERSIANN-CDR satellite-gauge blend; not station observed.",
            },
        }

    def get_series(self, lat: float, lon: float, start: str, end: str) -> dict[str, Any]:
        """Daily precipitation (mm) for a date range, as a pandas Series.

        One HTTP fetch per day (each file is one day); a full year is ~365
        requests, so call with a bounded window (or use for targeted event
        reconstruction). Returns a Series indexed by date.
        """
        import pandas as pd

        start_d = date.fromisoformat(start)
        end_d = date.fromisoformat(end)
        if end_d < start_d:
            return {"ok": False, "error": "end before start", "source": self.source_id}

        values: dict[date, float] = {}
        errors: list[str] = []
        d = start_d
        while d <= end_d:
            url = _resolve_file_url(d, timeout=self.timeout)
            if url is None:
                errors.append(f"{d.isoformat()}: no file")
                d += timedelta(days=1)
                continue
            try:
                values[d] = _fetch_cell(url, lat, lon, timeout=self.timeout)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{d.isoformat()}: {type(exc).__name__}")
            d += timedelta(days=1)

        series = pd.Series(values, name="precip_mm")
        series.index = pd.to_datetime(series.index)
        return {
            "ok": bool(values),
            "source": self.source_id,
            "start": start,
            "end": end,
            "n_days": int(len(values)),
            "n_missing": int(len(errors)),
            "errors": errors[:10],
            "series": series,
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "nearest-grid-cell attribution (0.25°)",
            },
        }

    def check_availability(self):
        return {
            "source_id": self.source_id,
            "available": True,
            "note": "live PERSIANN-CDR (NCEI HTTP)",
        }
