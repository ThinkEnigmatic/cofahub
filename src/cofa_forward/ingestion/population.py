"""WorldPop population adapter.

WorldPop publishes ~1 km population-count GeoTIFFs (EPSG:4326, nodata -99999),
UN-adjusted. This adapter downloads a country grid and extracts population at a
point or within a radius, providing a real spatial-population layer for exposure
analysis (cyclone proximity, water demand, drought exposure).

Population totals are UN-adjusted (2020), so they can differ from national
censuses; WorldPop is used here for SPATIAL distribution, not as the census of
record. This is documented wherever population figures are shown.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import rasterio

from .base import BaseAdapter

BASE_URL = "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km"
NODATA = -99999.0

# ISO-3166 alpha-2 (registry) -> alpha-3 (WorldPop file naming)
ISO2_TO_ISO3 = {"PW": "PLW", "FM": "FSM", "MH": "MHL"}


def _haversine_km_vec(lat0, lon0, lat_arr, lon_arr) -> np.ndarray:
    """Vectorized great-circle distance (km) from (lat0, lon0) to arrays."""
    phi0 = math.radians(lat0)
    phi1 = np.radians(lat_arr)
    dphi = np.radians(lat_arr - lat0)
    dlmb = np.radians(lon_arr - lon0)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi0) * np.cos(phi1) * np.sin(dlmb / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


def population_at(raster_path: str, lat: float, lon: float) -> float:
    """Population at the nearest grid cell to a point (count)."""
    with rasterio.open(raster_path) as ds:
        row, col = ds.index(lon, lat)
        if not (0 <= row < ds.height and 0 <= col < ds.width):
            return float("nan")
        v = ds.read(1, window=((row, row + 1), (col, col + 1)))[0, 0]
    return float(v) if v is not None and v > NODATA else float("nan")


def population_within_radius(raster_path: str, lat: float, lon: float, radius_km: float) -> float:
    """Total population (sum of valid pixels) within ``radius_km`` of a point.

    Uses a circular distance mask (great-circle). Returns the sum of population
    counts in the pixels whose centers fall inside the circle.
    """
    with rasterio.open(raster_path) as ds:
        dlat = radius_km / 111.0
        dlon = radius_km / (111.0 * max(math.cos(math.radians(lat)), 1e-6))
        r0, c0 = ds.index(lon - dlon, lat + dlat)
        r1, c1 = ds.index(lon + dlon, lat - dlat)
        if r0 > r1:
            r0, r1 = r1, r0
        if c0 > c1:
            c0, c1 = c1, c0
        r0 = max(0, r0)
        c0 = max(0, c0)
        r1 = min(ds.height - 1, r1)
        c1 = min(ds.width - 1, c1)
        window = ((r0, r1 + 1), (c0, c1 + 1))
        block = ds.read(1, window=window)
        t = ds.transform  # full affine; maps absolute (row, col) corner -> world
        nrows, ncols = block.shape
        row_abs, col_abs = np.meshgrid(np.arange(r0, r1 + 1), np.arange(c0, c1 + 1), indexing="ij")
        lon_grid = t.c + (col_abs + 0.5) * t.a + (row_abs + 0.5) * t.b
        lat_grid = t.f + (col_abs + 0.5) * t.d + (row_abs + 0.5) * t.e
        dist = _haversine_km_vec(lat, lon, lat_grid, lon_grid)
        valid = block > NODATA
        within = valid & (dist <= radius_km)
        return float(block[within].sum())


class WorldPopAdapter(BaseAdapter):
    source_id = "worldpop-population"
    source_url = BASE_URL
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 60.0):
        super().__init__(cache=cache, db=db, timeout=timeout)
        self.raw_dir = (
            Path(config.data_dir("raw")) / "worldpop" if config else Path("data/raw/worldpop")
        )

    @staticmethod
    def iso3(country_code: str) -> str:
        return ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())

    def raster_path(self, iso3: str, year: int = 2020) -> str:
        """Download (once) and return the local path to a country population grid."""
        iso3 = iso3.upper()
        low = iso3.lower()
        url = f"{BASE_URL}/{year}/{iso3}/{low}_ppp_{year}_1km_Aggregated.tif"
        dest = self.raw_dir / f"{low}_{year}.tif"
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            resp = self.session.get(url, stream=True, timeout=self.timeout)
            resp.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(256 * 1024):
                    fh.write(chunk)
        return str(dest)

    def population_at(self, country_code: str, lat: float, lon: float, year: int = 2020) -> float:
        return population_at(self.raster_path(self.iso3(country_code), year), lat, lon)

    def population_within_radius(
        self, country_code: str, lat: float, lon: float, radius_km: float, year: int = 2020
    ) -> float:
        return population_within_radius(
            self.raster_path(self.iso3(country_code), year), lat, lon, radius_km
        )

    def check_availability(self):
        return {"source_id": self.source_id, "available": True, "note": "live WorldPop 1km grids"}
