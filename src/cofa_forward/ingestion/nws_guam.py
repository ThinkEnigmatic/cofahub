"""NWS Guam (WFO Tiyan) advisory adapter.

NWS Guam issues tropical cyclone advisories and island-specific watches/warnings
for the Marianas and Micronesia (including Palau, FSM, and RMI). This adapter
parses the Public Advisory (TCP) text product; the structured ``api.weather.gov/
alerts`` endpoint is also available for zone-based active alerts.
"""

from __future__ import annotations

import re

from .base import BaseAdapter

TEXT_BASE = "https://tgftp.nws.noaa.gov/data/raw/wt"
API_BASE = "https://api.weather.gov"

_UA = {"User-Agent": "(cofa-forward, weather-intel@example.com)"}


def _parse_latlon(s: str) -> dict | None:
    m = re.match(r"(\d+\.?\d*)([NS])\s+(\d+\.?\d*)([EW])", s)
    if not m:
        return None
    lat = float(m.group(1)) * (1 if m.group(2) == "N" else -1)
    lon = float(m.group(3)) * (1 if m.group(4) == "E" else -1)
    return {"lat": lat, "lon": lon}


def parse_nws_guam_tcp(text: str) -> dict:
    """Parse an NWS Guam Tropical Cyclone Public Advisory (TCP) text product."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    out: dict = {}

    parts = lines[0].split()
    if len(parts) >= 3:
        out["header"] = parts[0]
        out["agency"] = parts[1]
        out["issue_time"] = parts[2]

    for i, ln in enumerate(lines):
        if ln.strip() == "BULLETIN" and i + 1 < len(lines):
            headline = lines[i + 1].strip()
            out["headline"] = headline
            m = re.search(
                r"(Super Typhoon|Typhoon|Hurricane|Tropical Storm|Tropical Depression|Storm)"
                r"\s+([A-Za-z-]+)\s+\((\d+\w)\)\s+(?:Intermediate |Interim )?Advisory Number (\w+)",
                headline,
            )
            if m:
                out["storm_type"] = m.group(1)
                out["name"] = m.group(2)
                out["storm_id"] = m.group(3)
                out["advisory_number"] = m.group(4)
            break

    warnings: list[str] = []
    in_ww = False
    for ln in lines:
        if "WATCHES AND WARNINGS" in ln:
            in_ww = True
            continue
        if in_ww and ("SUMMARY OF" in ln or ln.strip() == "---"):
            in_ww = False
            continue
        if in_ww and re.search(r"\b(Watch|Warning)\b", ln) and "means that" not in ln:
            warnings.append(ln.strip())
    out["watches_warnings"] = warnings

    m = re.search(r"NEAR (\d+\.?\d*[NS]\s+\d+\.?\d*[EW])", text)
    if m:
        out["position"] = _parse_latlon(m.group(1))
    return out


class NwsGuamAdapter(BaseAdapter):
    source_id = "nws-guam"
    source_url = f"{TEXT_BASE}/wtpq31.pgum.tcp.pq1.txt"
    implementation_status = "implemented_and_tested"

    def __init__(self, cache=None, db=None, timeout: float = 30.0):
        super().__init__(cache=cache, db=db, timeout=timeout)
        self.session.headers.update(_UA)

    def get_advisory(self) -> dict:
        """Fetch and parse the latest NWS Guam TCP (Tropical Cyclone Public Advisory)."""
        res = self.fetch_text(self.source_url)
        if not res.ok:
            return {"ok": False, "error": res.error, "source": self.source_id}
        try:
            parsed = parse_nws_guam_tcp(res.data)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"parse failed: {exc}", "source": self.source_id}
        return {
            "ok": True,
            "source": self.source_id,
            "retrieved_at": res.retrieved_at,
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "text parse of NWS Guam TCP",
            },
            **parsed,
        }

    def get_active_alerts(self, lat: float, lon: float) -> dict:
        """Query api.weather.gov for active alerts at a point (structured JSON)."""
        url = f"{API_BASE}/alerts/active"
        res = self.fetch_json(url, params={"point": f"{lat},{lon}"})
        if not res.ok:
            return {"ok": False, "error": res.error, "source": self.source_id}
        alerts = []
        for f in res.data.get("features", []):
            p = f.get("properties", {})
            alerts.append(
                {
                    "event": p.get("event"),
                    "headline": p.get("headline"),
                    "severity": p.get("severity"),
                    "area": p.get("areaDesc"),
                    "sent": p.get("sent"),
                    "effective": p.get("effective"),
                    "expires": p.get("expires"),
                }
            )
        return {
            "ok": True,
            "source": self.source_id,
            "retrieved_at": res.retrieved_at,
            "n_alerts": len(alerts),
            "alerts": alerts,
        }

    def check_availability(self):
        return {"source_id": self.source_id, "available": True, "note": "live NWS Guam advisories"}
