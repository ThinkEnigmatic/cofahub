"""Open-Meteo forecast adapter (live weather integration).

No API key required. Model output (~11 km grid), not official station
observations. Nearest-grid-cell attribution is applied to the requested point;
this is attribution of model data, NOT downscaling.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from ..geography.spatial_attribution import ATTRIBUTION_NOTE
from .base import BaseAdapter, FetchResult

logger = logging.getLogger("cofa_forward.ingestion.weather")

_CURRENT_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "weather_code",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
]
_HOURLY_VARS = [
    "temperature_2m",
    "precipitation",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
]
_DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
    "precipitation_probability_max",
]


def normalize_forecast(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize an Open-Meteo forecast JSON payload into DataFrames + metadata."""
    if payload is None or not isinstance(payload, dict):
        raise ValueError("forecast payload must be a JSON object")

    meta = {
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "elevation_m": payload.get("elevation"),
        "timezone": payload.get("timezone"),
        "generationtime_ms": payload.get("generationtime_ms"),
    }

    def _frame(section: str) -> pd.DataFrame:
        block = payload.get(section, {})
        if "time" not in block:
            return pd.DataFrame()
        df = pd.DataFrame({k: v for k, v in block.items() if k != "time"})
        df.index = pd.to_datetime(block["time"], utc=True)
        return df

    current = payload.get("current", {}) or {}
    current_clean = {k: v for k, v in current.items() if k != "time" and k != "interval"}

    return {
        "meta": meta,
        "current": current_clean,
        "current_time": pd.Timestamp(current.get("time"), tz="UTC")
        if current.get("time")
        else None,
        "hourly": _frame("hourly"),
        "daily": _frame("daily"),
        "hourly_units": payload.get("hourly_units", {}),
        "daily_units": payload.get("daily_units", {}),
        "attribution_note": ATTRIBUTION_NOTE,
    }


class OpenMeteoForecastAdapter(BaseAdapter):
    source_id = "open-meteo-forecast"
    base_url = "https://api.open-meteo.com/v1"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 20.0):
        if config is not None:
            base = config.env("OPEN_METEO_BASE_URL")
            if base:
                self.base_url = base.rstrip("/")
        super().__init__(cache=cache, db=db, timeout=timeout)
        self.source_url = f"{self.base_url}/forecast"

    def _params(self, lat: float, lon: float, forecast_days: int) -> dict[str, Any]:
        return {
            "latitude": lat,
            "longitude": lon,
            "current": ",".join(_CURRENT_VARS),
            "hourly": ",".join(_HOURLY_VARS),
            "daily": ",".join(_DAILY_VARS),
            "forecast_days": forecast_days,
            "timezone": "UTC",
            "windspeed_unit": "ms",
        }

    def get_forecast(self, lat: float, lon: float, forecast_days: int = 16) -> dict[str, Any]:
        """Fetch and normalize a forecast for a point. Never raises on network errors."""
        res: FetchResult = self.fetch_json(self.source_url, self._params(lat, lon, forecast_days))
        if not res.ok:
            return {
                "ok": False,
                "error": res.error,
                "source": self.source_id,
                "source_url": self.source_url,
                "retrieved_at": res.retrieved_at,
            }
        try:
            norm = normalize_forecast(res.data)
        except (ValueError, KeyError) as exc:
            logger.warning("forecast normalization failed: %s", exc)
            return {
                "ok": False,
                "error": f"normalization failed: {exc}",
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        return {
            "ok": True,
            "source": self.source_id,
            "source_url": self.source_url,
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "init_time": res.retrieved_at,
            "lead_time": f"0-{forecast_days * 24}h",
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "retrieved_at": res.retrieved_at,
                "init_time": res.retrieved_at,
                "calculation_method": "nearest_grid_cell_attribution",
                "notes": ATTRIBUTION_NOTE,
            },
            **norm,
        }

    def get_model_comparison(
        self,
        lat: float,
        lon: float,
        variable: str = "temperature_2m",
        models: list[str] | None = None,
        forecast_days: int = 7,
    ) -> dict:
        """Fetch one hourly variable from multiple models for comparison.

        Open-Meteo serves several models (ECMWF IFS/AIFS, GFS, ICON, GEM, …) via
        the ``models`` parameter; each returned column is ``{variable}_{model}``.
        """
        models = models or [
            "best_match",
            "ecmwf_aifs025",
            "ecmwf_ifs025",
            "gfs_global",
            "icon_global",
            "gem_global",
        ]
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": variable,
            "models": ",".join(models),
            "forecast_days": forecast_days,
            "timezone": "UTC",
        }
        res = self.fetch_json(self.source_url, params)
        if not res.ok:
            return {
                "ok": False,
                "error": res.error,
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        hourly = res.data.get("hourly", {}) or {}
        if "time" not in hourly:
            return {"ok": False, "error": "no hourly data", "source": self.source_id}
        times = pd.to_datetime(hourly["time"], utc=True)
        df = pd.DataFrame(
            {k.replace(f"{variable}_", ""): v for k, v in hourly.items() if k != "time"},
            index=times,
        )
        return {
            "ok": True,
            "source": self.source_id,
            "retrieved_at": res.retrieved_at,
            "variable": variable,
            "models": df,
            "n_models": int(df.shape[1]),
            "resolution": "model-native grid (attributed to the requested point)",
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "multi-model nearest-grid-cell attribution",
                "notes": "Model disagreement is shown, not a probability forecast.",
            },
        }
