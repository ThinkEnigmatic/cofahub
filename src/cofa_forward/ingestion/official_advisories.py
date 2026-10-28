"""Official advisories/watches/warnings ingestion — PLANNED (Phase 5).

No active storms, warnings, or forecast tracks are invented. When no confirmed
storm data is available, the UI states the actual data coverage and retrieval
time rather than assuming zero risk.
"""

from __future__ import annotations

from .base import BaseAdapter


class OfficialAdvisoriesAdapter(BaseAdapter):
    source_id = "official-advisories"
    source_url = ""
    implementation_status = "planned"

    def check_availability(self):
        return {
            "source_id": self.source_id,
            "available": False,
            "note": "Not implemented (Phase 5). No official advisory source is wired in.",
        }
