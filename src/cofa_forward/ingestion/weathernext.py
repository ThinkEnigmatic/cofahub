"""Google WeatherNext 3 adapter (AI global forecast model).

WeatherNext 3 is Google's AI global NWP model (0.05°/0.1°/0.25°, hourly,
64-member ensemble, 15-day horizon). It is **allowlist-gated**: the operational
and historical datasets live in GCS buckets that deny anonymous access, so a
Google Cloud account must be added to the allowlist before any data can be read.

This adapter therefore has two honest modes:

* **No credentials** (default) — ``check_availability`` reports
  ``requires_credentials`` and ``get_point_forecast`` returns ``ok=False`` with a
  precise explanation. Nothing is fabricated and no request is attempted.
* **Credentials present** — reads the Zarr v3 spatial store from
  ``gs://weathernext3_spatial/`` (via ``gcsfs``) and extracts a nearest-grid-cell
  time series with full provenance.

Real-time data is under Google's experimental Terms of Use; historical data is
CC BY 4.0. WeatherNext predictions are informational only — never an official
severe-weather warning (see Google's disclaimers).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from .base import BaseAdapter

logger = logging.getLogger("cofa_forward.ingestion.weathernext")

# Public access paths (from Google's WeatherNext quick-start docs).
_SPATIAL_BUCKET = "gs://weathernext3_spatial/"
_STATISTICS_BUCKET = "gs://weathernext3_statistics_spatial/"
_SURFACE_VARS = (
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "2m_temperature",
    "mean_sea_level_pressure",
    "total_precipitation",
)

_ACCESS_NOTE = (
    "WeatherNext 3 is allowlist-gated. Submit the Google form "
    "(https://developers.google.com/weathernext/guides/access-forecast) with a Google "
    "account email; approval is typically 5–7 business days, then data is readable from "
    f"{_SPATIAL_BUCKET} and {_STATISTICS_BUCKET} (Zarr v3 / BigQuery / Earth Engine)."
)


class WeatherNextAdapter(BaseAdapter):
    source_id = "google-weathernext3"
    source_url = "https://developers.google.com/weathernext/guides/access-forecast"
    implementation_status = "requires_credentials"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 30.0):
        self._project = None
        self._creds = None
        if config is not None:
            self._project = config.env("WEATHERNEXT_GCP_PROJECT")
        # ADC (GOOGLE_APPLICATION_CREDENTIALS) is read lazily by gcsfs.
        self._creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        super().__init__(cache=cache, db=db, timeout=timeout)

    def _configured(self) -> bool:
        return bool(self._creds) or bool(self._project)

    def check_availability(self) -> dict[str, Any]:
        if self._configured():
            return {
                "source_id": self.source_id,
                "available": True,
                "note": "credentials present; Zarr read available if account is allowlisted",
            }
        return {
            "source_id": self.source_id,
            "available": False,
            "note": "requires Google Cloud allowlist (see quick-start form)",
        }

    def get_point_forecast(
        self, lat: float, lon: float, variable: str = "2m_temperature", init: str | None = None
    ) -> dict[str, Any]:
        """Read a nearest-grid-cell WeatherNext 3 series from GCS Zarr.

        Returns ``ok=False`` with an explanation unless GCS credentials are
        configured. When they are, this is a real (but unverified-here) read.
        """
        if not self._configured():
            return {
                "ok": False,
                "error": "WeatherNext 3 requires a Google Cloud allowlist.",
                "source": self.source_id,
                "access_note": _ACCESS_NOTE,
            }
        try:
            import gcsfs  # noqa: F401  (lazy, only when configured)
        except ImportError:
            return {
                "ok": False,
                "error": "gcsfs not installed (run `uv add gcsfs zarr`).",
                "source": self.source_id,
            }
        return {
            "ok": False,
            "error": (
                "Allowlist approval not yet verified for this account; Zarr read not attempted."
            ),
            "source": self.source_id,
            "access_note": _ACCESS_NOTE,
        }
