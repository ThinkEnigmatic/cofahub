"""IBTrACS historical track ingestion — PLANNED (Phase 5)."""

from __future__ import annotations

from .base import BaseAdapter


class IbtracsAdapter(BaseAdapter):
    source_id = "noaa-ibtracs"
    source_url = "https://www.ncei.noaa.gov/products/international-best-track-archive"
    implementation_status = "planned"

    def check_availability(self):
        return {
            "source_id": self.source_id,
            "available": False,
            "note": "Not implemented (Phase 5). Sample tracks are used until then.",
        }
