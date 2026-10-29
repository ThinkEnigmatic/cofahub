"""Open-Meteo Marine API adapter — waves and sea-surface temperature.

Waves and SST complete the coastal-hazard picture alongside the UHSLC tide
gauges: significant wave height + period + direction (current and daily max) and
current sea-surface temperature. Significant wave height is the standard "how big
are the seas" measure; combined with tide + sea-level anomaly it drives the
atoll overwash/inundation that closed RMI schools in 2024.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .base import BaseAdapter

_BASE = "https://marine-api.open-meteo.com/v1/marine"


class MarineAdapter(BaseAdapter):
    source_id = "open-meteo-marine"
    source_url = _BASE
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 30.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def get_marine(self, lat: float, lon: float, forecast_days: int = 7) -> dict[str, Any]:
        """Current + daily-max wave/SST conditions at a point."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "wave_height,wave_period,wave_direction,sea_surface_temperature",
            "daily": "wave_height_max,wave_period_max,wave_direction_dominant",
            "timezone": "UTC",
            "forecast_days": forecast_days,
        }
        res = self.fetch_json(self.source_url, params)
        if not res.ok:
            return {"ok": False, "error": res.error, "source": self.source_id}
        cur = res.data.get("current", {}) or {}
        daily = res.data.get("daily", {}) or {}
        if not cur or "time" not in daily:
            return {"ok": False, "error": "no marine data", "source": self.source_id}
        idx = pd.to_datetime(daily["time"], utc=True)
        series = pd.DataFrame(
            {
                "wave_height_max_m": pd.to_numeric(
                    daily.get("wave_height_max", []), errors="coerce"
                ),
                "wave_period_max_s": pd.to_numeric(
                    daily.get("wave_period_max", []), errors="coerce"
                ),
            },
            index=idx,
        )
        return {
            "ok": True,
            "source": self.source_id,
            "source_url": self.source_url,
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "current": {
                "wave_height_m": cur.get("wave_height"),
                "wave_period_s": cur.get("wave_period"),
                "wave_direction_deg": cur.get("wave_direction"),
                "sst_c": cur.get("sea_surface_temperature"),
                "time": cur.get("time"),
            },
            "daily": series,
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "nearest_grid_cell_attribution (best_match model)",
                "notes": "Significant wave height; ~11 km marine grid.",
            },
        }

    def check_availability(self) -> dict[str, Any]:
        return {"source_id": self.source_id, "available": True, "note": "live Open-Meteo marine"}
