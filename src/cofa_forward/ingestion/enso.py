"""ENSO ingestion (NOAA CPC ONI) — PLANNED (Phase 3).

Authoritative ENSO classification must come from CPC. This adapter is not wired
in yet; the app currently reports ENSO status as "unavailable" (see enso.yaml).
"""

from __future__ import annotations

from .base import BaseAdapter


class CpcOniAdapter(BaseAdapter):
    source_id = "noaa-cpc-enso"
    source_url = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
    implementation_status = "planned"

    def check_availability(self):
        return {
            "source_id": self.source_id,
            "available": False,
            "note": "Not implemented (Phase 3). Do not use an unaudited estimate as authoritative.",
        }
