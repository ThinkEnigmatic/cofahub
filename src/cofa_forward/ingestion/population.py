"""Population / exposure ingestion — PLANNED (Phase 6/7).

Only integrate after checking license, coverage, resolution, and fitness for
purpose. Not wired in yet.
"""

from __future__ import annotations

from .base import BaseAdapter


class PopulationAdapter(BaseAdapter):
    source_id = "worldpop-population"
    source_url = "https://www.worldpop.org/"
    implementation_status = "planned"

    def check_availability(self):
        return {
            "source_id": self.source_id,
            "available": False,
            "note": "Not implemented (Phase 6/7).",
        }
