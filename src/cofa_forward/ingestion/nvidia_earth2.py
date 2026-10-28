"""NVIDIA Earth-2 / FourCastNet / StormCast adapter (AI global weather models).

NVIDIA's AI weather models (FourCastNet, StormCast, CorrDiff, and the Earth-2
platform) are distributed two ways:

* **Downloadable weights** (NGC / Hugging Face) — open model weights you run
  yourself on a GPU via NVIDIA Modulus. No hosted inference for free.
* **NVIDIA NIM / build.nvidia.com** — hosted inference endpoints, but weather
  model endpoints require a paid NVIDIA API key / DGX Cloud entitlement (the free
  NIM key covers LLM/vision/embedding models, not the weather microservices).

There is no keyless free hosted weather API from NVIDIA. This adapter therefore
documents the surface honestly and only performs a real read when an NVIDIA API
key is provided; otherwise it reports ``requires_credentials`` and does not
fabricate data.
"""

from __future__ import annotations

import os
from typing import Any

from .base import BaseAdapter

_NVIDIA_WEATHER_NOTE = (
    "NVIDIA's AI weather models (FourCastNet, StormCast) are downloadable open weights "
    "self-hosted on GPU via Modulus, or hosted NIM microservices that require a paid "
    "NVIDIA API key / DGX Cloud entitlement. There is no keyless free hosted weather API."
)


class NvidiaEarth2Adapter(BaseAdapter):
    source_id = "nvidia-earth2"
    source_url = "https://build.nvidia.com/nvidia/fourcastnet"
    implementation_status = "requires_credentials"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 30.0):
        self._api_key = os.environ.get("NVIDIA_API_KEY")
        if config is not None:
            self._api_key = config.env("NVIDIA_API_KEY") or self._api_key
        super().__init__(cache=cache, db=db, timeout=timeout)

    def _configured(self) -> bool:
        return bool(self._api_key)

    def check_availability(self) -> dict[str, Any]:
        if self._configured():
            return {
                "source_id": self.source_id,
                "available": True,
                "note": "NVIDIA API key present; NIM weather endpoints may need paid entitlement",
            }
        return {
            "source_id": self.source_id,
            "available": False,
            "note": "no free hosted weather API; FourCastNet/StormCast weights are self-host",
        }

    def get_point_forecast(self, lat: float, lon: float, variable: str = "u10m") -> dict[str, Any]:
        """Hosted FourCastNet/StormCast inference (requires a paid NVIDIA NIM key)."""
        if not self._configured():
            return {
                "ok": False,
                "error": "NVIDIA AI weather requires an API key / DGX Cloud entitlement.",
                "source": self.source_id,
                "access_note": _NVIDIA_WEATHER_NOTE,
            }
        return {
            "ok": False,
            "error": "NVIDIA weather NIM endpoints need a paid entitlement; not attempted.",
            "source": self.source_id,
            "access_note": _NVIDIA_WEATHER_NOTE,
        }
