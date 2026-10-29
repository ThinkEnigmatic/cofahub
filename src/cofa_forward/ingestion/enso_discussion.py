"""NOAA CPC ENSO Diagnostic Discussion adapter (official ENSO status statement).

The Diagnostic Discussion is the authoritative ENSO status statement (issued
monthly on the second Thursday). Unlike the ONI (which yields a *derived* phase),
this page carries the official **ENSO Alert System Status** (e.g. "El Niño
Advisory") and a prose synopsis. This adapter scrapes the HTML into structured
fields: issue date, alert status, synopsis, and the outlook summary paragraph.

No machine-readable file is published for this product, so it is parsed from the
HTML (best-effort; the fields degrade gracefully if CPC changes its markup).
"""

from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

from .base import BaseAdapter

_SOURCE_URL = (
    "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.html"
)

_ALERT_RE = re.compile(
    r"ENSO\s+Alert\s+System\s+Status:\s*(?P<status>[A-Za-zÀ-ÿ\s]+?(?:Advisory|Watch|Final|None))",
    re.I | re.S,
)
_SYNOPSIS_RE = re.compile(r"Synopsis:\s*(?P<synopsis>.+?)(?=\n\s*(?:\w|\b))", re.I | re.S)
_DATE_RE = re.compile(
    r"issued\s+by\s+CLIMATE\s+PREDICTION\s+CENTER[^0-9]*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    re.I | re.S,
)


def _strip_html(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    return re.sub(r"[ \t\r]+", " ", text)


def parse_enso_discussion(raw_html: str) -> dict[str, Any]:
    """Parse the Diagnostic Discussion HTML into structured fields."""
    text = _strip_html(raw_html)

    out: dict[str, Any] = {}

    m = _DATE_RE.search(text)
    if m:
        try:
            out["issue_date"] = datetime.strptime(m.group(1), "%d %B %Y").date().isoformat()
        except ValueError:
            out["issue_date"] = m.group(1)

    m = _ALERT_RE.search(text)
    if m:
        out["alert_status"] = m.group("status").strip()

    m = _SYNOPSIS_RE.search(text)
    if m:
        synopsis = re.sub(r"\s+", " ", m.group("synopsis")).strip()
        out["synopsis"] = synopsis

    # Outlook summary: the paragraph beginning "In summary," (or the tail of the synopsis).
    m = re.search(
        r"In summary,\s*(?P<summary>.+?)(?=\n\s*(?:This discussion|The next))",
        text,
        re.I | re.S,
    )
    if m:
        out["outlook_summary"] = re.sub(r"\s+", " ", m.group("summary")).strip()

    return out


class CpcEnsoDiscussionAdapter(BaseAdapter):
    source_id = "noaa-cpc-enso-discussion"
    source_url = _SOURCE_URL
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 30.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def get_discussion(self) -> dict[str, Any]:
        """Fetch and parse the official ENSO Diagnostic Discussion."""
        res = self.fetch_text(self.source_url)
        if not res.ok:
            return {
                "ok": False,
                "error": res.error,
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        try:
            parsed = parse_enso_discussion(res.data)
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": f"parse failed: {exc}",
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        if not parsed.get("alert_status") and not parsed.get("synopsis"):
            return {
                "ok": False,
                "error": "no alert status or synopsis found (CPC markup changed?)",
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        return {
            "ok": True,
            "source": self.source_id,
            "source_url": self.source_url,
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "HTML scrape of the official CPC Diagnostic Discussion",
                "notes": "Authoritative ENSO status statement (not a derived phase).",
            },
            **parsed,
        }

    def check_availability(self):
        return {
            "source_id": self.source_id,
            "available": True,
            "note": "live CPC ENSO Diagnostic Discussion (HTML scrape)",
        }
