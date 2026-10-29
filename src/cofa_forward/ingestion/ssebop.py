"""USGS SSEBop actual evapotranspiration adapter (FEWS NET monthly ET).

SSEBop (operational Simplified Surface Energy Balance) is the USGS 1-km monthly
**actual** evapotranspiration — the "actual ET" complement to the Hargreaves
*potential* ET the app already computes, and the ET source the USGS western-
Pacific water-budget release uses.

Constraints (documented honestly):
* The free FEWS NET portal serves monthly actual ET from **Jan 2003 → Jun 2021**
  only; later years are behind the ScienceBase "manager" (login required).
* SSEBop is **land-only**: tiny atolls (Majuro, Kwajalein) fall in nodata ocean
  pixels, so ET is sampled with a max-valid-pixel window heuristic (like CHIRPS)
  and may still be unavailable for the smallest atolls. High islands (Pohnpei,
  Kosrae, Yap, Weno, Babeldaob) yield valid ET.

The monthly zip is ~73 MB (global); the adapter downloads once and caches, then
samples the point via rasterio.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

import rasterio

from .base import BaseAdapter

_BASE = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/eta/downloads"
NODATA = -32768.0


def monthly_url(yyyymm: str) -> str:
    return f"{_BASE}/m{yyyymm}.zip"


def sample_et(tif_path: str, lat: float, lon: float, window: int = 5) -> float:
    """Sample actual ET (mm) at a lat/lon using the max-valid-pixel window.

    Returns NaN when the window is entirely nodata (e.g. a tiny atoll with no
    land pixel at 1 km).
    """
    half = window // 2
    with rasterio.open(tif_path) as ds:
        row, col = ds.index(lon, lat)
        r0 = max(0, row - half)
        c0 = max(0, col - half)
        block = ds.read(1, window=((r0, r0 + window), (c0, c0 + window)))
    valid = block[block > NODATA]
    if valid.size == 0:
        return float("nan")
    return float(valid.max())


class SsebopAdapter(BaseAdapter):
    source_id = "usgs-ssebop"
    source_url = _BASE
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 120.0):
        super().__init__(cache=cache, db=db, timeout=timeout)
        self.raw_dir = (
            Path(config.data_dir("raw")) / "ssebop" if config else Path("data/raw/ssebop")
        )

    def _tif_path(self, yyyymm: str) -> str:
        dest_dir = self.raw_dir / yyyymm
        tif = dest_dir / f"m{yyyymm}_modisSSEBopETv4_actual_mm.tif"
        if not tif.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            zip_path = self.raw_dir / f"m{yyyymm}.zip"
            if not zip_path.exists():
                resp = self.session.get(monthly_url(yyyymm), stream=True, timeout=self.timeout)
                resp.raise_for_status()
                with open(zip_path, "wb") as fh:
                    for chunk in resp.iter_content(512 * 1024):
                        fh.write(chunk)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(dest_dir)
        return str(tif)

    def get_et(self, lat: float, lon: float, yyyymm: str) -> dict:
        """Actual ET (mm) for a single month at a point."""
        try:
            tif = self._tif_path(yyyymm)
            et = sample_et(tif, lat, lon)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "source": self.source_id}
        return {
            "ok": True,
            "source": self.source_id,
            "yyyymm": yyyymm,
            "et_mm": et,
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": monthly_url(yyyymm),
                "calculation_method": "max-valid-pixel in 5x5 window (1 km, land-only)",
                "notes": "SSEBop actual ET (land-only); tiny atolls may be nodata.",
            },
        }

    def get_et_series(self, lat: float, lon: float, months: list[str]) -> dict:
        """Actual ET (mm) for a list of YYYYMM months (heavy: ~73 MB/month)."""
        import pandas as pd

        values = []
        errors = []
        for yyyymm in months:
            r = self.get_et(lat, lon, yyyymm)
            if r.get("ok") and r["et_mm"] == r["et_mm"]:
                values.append((yyyymm, r["et_mm"]))
            elif not r.get("ok"):
                errors.append(f"{yyyymm}: {r.get('error')}")
        series = pd.Series(
            [v for _, v in values],
            index=pd.to_datetime([f"{m[:4]}-{m[4:]}-01" for m, _ in values]),
            name="et_mm",
        ).sort_index()
        return {
            "ok": True,
            "source": self.source_id,
            "series": series,
            "n_months": int(len(series)),
            "errors": errors,
        }

    def check_availability(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "available": True,
            "note": "live USGS SSEBop (FEWS NET, Jan 2003–Jun 2021)",
        }
