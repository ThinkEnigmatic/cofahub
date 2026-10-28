"""Historical impacts ingestion — PLANNED (Phase 6).

A structured sample catalog (clearly labeled) drives the Historical Impacts page
until authoritative reports are imported and indexed.
"""

from __future__ import annotations

from .base import BaseAdapter


class HistoricalImpactsAdapter(BaseAdapter):
    source_id = "historical-impacts"
    source_url = ""
    implementation_status = "planned"

    def check_availability(self):
        return {
            "source_id": self.source_id,
            "available": False,
            "note": "Not implemented (Phase 6). Sample catalog is used until then.",
        }
