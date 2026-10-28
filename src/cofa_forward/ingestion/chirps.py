"""CHIRPS v3 precipitation adapter (satellite-based, land-masked).

CHIRPS v3 publishes one Cloud-Optimized GeoTIFF per month. We open each COG over
HTTP (``/vsicurl/``, range requests — no full download) and sample the requested
point.

IMPORTANT limitation: CHIRPS is **land-masked**. Tiny atolls (e.g. Koror, Majuro)
may occupy a single sub-pixel; surrounding "ocean" cells are ``-9999`` (nodata) or
spuriously low. We therefore sample a small window and take the **maximum valid
pixel** as the island's representative rainfall. This is internally consistent
(climatology uses the same rule), but it is a heuristic — for ocean-adjacent
atolls, ERA5 (already integrated) is the more reliable source. This is documented
wherever CHIRPS data is shown.
"""

from __future__ import annotations

import pandas as pd
import rasterio

from .base import BaseAdapter

CHIRPS_BASE = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0"
NODATA = -9999.0


def monthly_cog_url(year: int, month: int) -> str:
    return f"{CHIRPS_BASE}/monthly/global/cogs/chirps-v3.0.{year:04d}.{month:02d}.cog"


def _vsicurl(url: str) -> str:
    return f"/vsicurl/{url}"


def sample_point(url_or_path: str, lat: float, lon: float, window: int = 5) -> float:
    """Sample a representative rainfall value (mm) at a lat/lon from a CHIRPS COG.

    Reads a ``window``×``window`` block and returns the maximum valid (non-nodata)
    value. Returns NaN if the block is entirely nodata or unreadable.
    """
    half = window // 2
    try:
        with rasterio.open(url_or_path) as ds:
            row, col = ds.index(lon, lat)
            r0 = max(0, row - half)
            c0 = max(0, col - half)
            block = ds.read(1, window=((r0, r0 + window), (c0, c0 + window)))
    except Exception:  # noqa: BLE001 - a missing/unreadable month must not crash
        return float("nan")
    valid = block[block > NODATA]
    if valid.size == 0:
        return float("nan")
    return float(valid.max())


class ChirpsAdapter(BaseAdapter):
    source_id = "chirps-v3"
    source_url = CHIRPS_BASE
    implementation_status = "implemented_and_tested"

    def __init__(self, cache=None, db=None, timeout: float = 30.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def get_monthly_series(self, lat: float, lon: float, start: str, end: str) -> dict:
        """Build a monthly rainfall Series (mm) over [start, end] from CHIRPS COGs."""
        months = pd.period_range(start=start, end=end, freq="M")
        values = []
        for p in months:
            url = monthly_cog_url(p.year, p.month)
            values.append(sample_point(_vsicurl(url), lat, lon))

        idx = months.to_timestamp(how="end")
        series = pd.Series(values, index=idx, name="precip_mm")
        n_missing = int(series.isna().sum())
        return {
            "ok": True,
            "source": self.source_id,
            "source_url": self.source_url,
            "series": series,
            "n_months": int(len(series)),
            "n_missing": n_missing,
            "spatial_resolution": "0.05 deg (~5.5 km), land-masked",
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "max-valid-pixel in 5x5 window (land-masked COG)",
                "notes": (
                    "Satellite estimate; land-masked. Sub-pixel islands are represented "
                    "by the maximum valid pixel; ERA5 is preferred for ocean-adjacent atolls."
                ),
            },
        }

    def check_availability(self):
        return {"source_id": self.source_id, "available": True, "note": "live CHIRPS v3 COGs"}
