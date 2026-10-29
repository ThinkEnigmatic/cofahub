"""Open-Meteo Historical Weather (ERA5) archive adapter for rainfall/climatology.

Provides daily precipitation for climatology and anomalies (Phase 3 groundwork).
ERA5 is a ~25 km reanalysis — coarser than the forecast grid; see provenance.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from .base import BaseAdapter, FetchResult

logger = logging.getLogger("cofa_forward.ingestion.rainfall")


def normalize_archive_rainfall(payload: dict[str, Any]) -> pd.Series:
    """Extract a daily precipitation Series (mm) from an archive payload."""
    daily = payload.get("daily", {}) or {}
    if "time" not in daily:
        raise ValueError("archive payload missing daily.time")
    times = pd.to_datetime(daily["time"], utc=True)
    precip = daily.get("precipitation_sum", [])
    if len(precip) != len(times):
        raise ValueError("daily.precipitation_sum length mismatch")
    s = pd.Series(pd.to_numeric(precip, errors="coerce"), index=times, name="precip_mm")
    return s


class OpenMeteoArchiveAdapter(BaseAdapter):
    source_id = "open-meteo-archive"
    base_url = "https://archive-api.open-meteo.com/v1"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 30.0):
        if config is not None:
            base = config.env("OPEN_METEO_ARCHIVE_BASE_URL")
            if base:
                self.base_url = base.rstrip("/")
        super().__init__(cache=cache, db=db, timeout=timeout)
        self.source_url = f"{self.base_url}/archive"

    def _params(self, lat: float, lon: float, start: str, end: str) -> dict[str, Any]:
        return {
            "latitude": lat,
            "longitude": lon,
            "start_date": start,
            "end_date": end,
            "daily": "precipitation_sum",
            "timezone": "UTC",
        }

    def get_rainfall(self, lat: float, lon: float, start: str, end: str) -> dict[str, Any]:
        """Fetch daily precipitation for a point over [start, end]. Never raises."""
        res: FetchResult = self.fetch_json(self.source_url, self._params(lat, lon, start, end))
        if not res.ok:
            return {
                "ok": False,
                "error": res.error,
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        try:
            series = normalize_archive_rainfall(res.data)
        except (ValueError, KeyError) as exc:
            logger.warning("archive normalization failed: %s", exc)
            return {"ok": False, "error": f"normalization failed: {exc}", "source": self.source_id}
        return {
            "ok": True,
            "source": self.source_id,
            "source_url": self.source_url,
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "series": series,
            "n_days": int(len(series)),
            "n_missing": int(series.isna().sum()),
            "spatial_resolution": "~25 km (ERA5 reanalysis)",
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "retrieved_at": res.retrieved_at,
                "calculation_method": "nearest_grid_cell_attribution",
                "notes": "ERA5 reanalysis; ~25 km grid is coarse for individual atolls.",
            },
        }

    def get_daily_climate(self, lat: float, lon: float, start: str, end: str) -> dict[str, Any]:
        """Fetch daily precipitation + Tmax/Tmin for the water balance (one request)."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start,
            "end_date": end,
            "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
            "timezone": "UTC",
        }
        res: FetchResult = self.fetch_json(self.source_url, params)
        if not res.ok:
            return {"ok": False, "error": res.error, "source": self.source_id}
        try:
            daily = res.data["daily"]
            idx = pd.to_datetime(daily["time"], utc=True)
            df = pd.DataFrame(
                {
                    "precip_mm": pd.to_numeric(daily["precipitation_sum"], errors="coerce"),
                    "tmax_c": pd.to_numeric(daily["temperature_2m_max"], errors="coerce"),
                    "tmin_c": pd.to_numeric(daily["temperature_2m_min"], errors="coerce"),
                },
                index=idx,
            )
        except (KeyError, ValueError) as exc:
            return {"ok": False, "error": f"normalization failed: {exc}", "source": self.source_id}
        return {
            "ok": True,
            "source": self.source_id,
            "source_url": self.source_url,
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "series": df,
            "n_days": int(len(df)),
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "nearest_grid_cell_attribution",
                "notes": "ERA5 reanalysis (precipitation + 2m max/min temperature).",
            },
        }
