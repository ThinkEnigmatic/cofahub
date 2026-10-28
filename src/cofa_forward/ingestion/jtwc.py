"""JTWC tropical cyclone warning adapter.

The Joint Typhoon Warning Center publishes ATCF-style text warnings (WMO header
WTPN31–35 PGTW) on the NWS text mirror. This adapter parses the full warning:
storm identity, position, 1-minute sustained wind, gusts, quadrant wind radii,
movement, and the forecast track. Complements the JMA adapter (which reports
10-minute sustained wind and probability circles).
"""

from __future__ import annotations

import re

from .base import BaseAdapter

BASE = "https://tgftp.nws.noaa.gov/data/raw/wt"

_QUAD = {"NORTHEAST": "NE", "SOUTHEAST": "SE", "SOUTHWEST": "SW", "NORTHWEST": "NW"}


def _parse_latlon(s: str) -> dict | None:
    m = re.match(r"(\d+\.?\d*)([NS])\s+(\d+\.?\d*)([EW])", s)
    if not m:
        return None
    lat = float(m.group(1)) * (1 if m.group(2) == "N" else -1)
    lon = float(m.group(3)) * (1 if m.group(4) == "E" else -1)
    return {"lat": lat, "lon": lon}


def parse_jtwc_warning(text: str) -> dict:
    """Parse a JTWC warning text into a structured dict."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    out: dict = {}

    parts = lines[0].split()
    if len(parts) >= 3:
        out["header"] = parts[0]
        out["agency"] = parts[1]
        out["issue_time"] = parts[2]

    for ln in lines:
        if ln.startswith("SUBJ/"):
            m = re.search(r"([A-Z][A-Z ]+?)\s+(\d+\w)\s+\(([^)]+)\)\s+WARNING NR (\d+)", ln)
            if m:
                out["storm_type"] = m.group(1).strip()
                out["storm_id"] = m.group(2)
                out["name"] = m.group(3)
                out["warning_number"] = m.group(4)
            break

    # Current position: the "NEAR ..." line (forecast points use "---", not NEAR).
    m = re.search(r"NEAR (\d+\.?\d*[NS]\s+\d+\.?\d*[EW])", text)
    if m:
        out["position"] = _parse_latlon(m.group(1))

    # Current wind (skip the "MAX SUSTAINED WINDS BASED ON ..." header line).
    m = re.search(r"MAX SUSTAINED WINDS - (\d+) KT, GUSTS (\d+) KT", text)
    if m:
        out["wind_kt"] = int(m.group(1))
        out["gusts_kt"] = int(m.group(2))

    m = re.search(r"MOVEMENT PAST SIX HOURS - (\d+) DEGREES AT (\d+) KTS", text)
    if m:
        out["movement_dir_deg"] = int(m.group(1))
        out["movement_speed_kt"] = int(m.group(2))

    # Wind radii (current section, before FORECASTS). Radii span two line forms:
    #   "RADIUS OF 064 KT WINDS - 025 NM NORTHEAST QUADRANT"  (first quadrant)
    #   "                          030 NM NORTHWEST QUADRANT"  (continuation)
    radii: dict[int, dict[str, int]] = {}
    current_kt: int | None = None
    for ln in lines:
        if "FORECASTS:" in ln:
            break
        m = re.search(
            r"RADIUS OF (\d+) KT WINDS - (\d+) NM "
            r"(NORTHEAST|SOUTHEAST|SOUTHWEST|NORTHWEST) QUADRANT",
            ln,
        )
        if m:
            current_kt = int(m.group(1))
            radii.setdefault(current_kt, {})[_QUAD[m.group(3)]] = int(m.group(2))
            continue
        m2 = re.search(r"(\d+) NM (NORTHEAST|SOUTHEAST|SOUTHWEST|NORTHWEST) QUADRANT", ln)
        if m2 and current_kt is not None:
            radii.setdefault(current_kt, {})[_QUAD[m2.group(2)]] = int(m2.group(1))
    out["wind_radii_nm"] = radii

    forecasts = []
    full = "\n".join(lines)
    for m in re.finditer(
        r"(\d+) HRS, VALID AT:\s*\n\s*(\d+Z) --- (\d+\.?\d*[NS]\s+\d+\.?\d*[EW])"
        r"\s*\n\s*MAX SUSTAINED WINDS - (\d+) KT",
        full,
    ):
        forecasts.append(
            {
                "hours": int(m.group(1)),
                "valid_time": m.group(2),
                "position": _parse_latlon(m.group(3)),
                "wind_kt": int(m.group(4)),
            }
        )
    out["forecasts"] = forecasts
    return out


class JtwcAdapter(BaseAdapter):
    source_id = "jtwc-advisories"
    source_url = f"{BASE}/wtpn31.pgtw..txt"
    implementation_status = "implemented_and_tested"

    def __init__(self, cache=None, db=None, timeout: float = 30.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def get_warning(self, wtpn_id: str = "wtpn31") -> dict:
        """Fetch and parse one JTWC warning file (wtpn31 .. wtpn35)."""
        url = f"{BASE}/{wtpn_id}.pgtw..txt"
        res = self.fetch_text(url)
        if not res.ok:
            return {"ok": False, "error": res.error, "source": self.source_id}
        try:
            parsed = parse_jtwc_warning(res.data)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"parse failed: {exc}", "source": self.source_id}
        if not parsed.get("storm_id"):
            return {"ok": False, "error": "no active storm in this file", "source": self.source_id}
        return {
            "ok": True,
            "source": self.source_id,
            "retrieved_at": res.retrieved_at,
            "wind_averaging": "1-minute sustained",
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": url,
                "calculation_method": "text parse of JTWC ATCF warning",
                "notes": "1-min sustained wind differs from JMA's 10-min mean.",
            },
            **parsed,
        }

    def get_active_warnings(self) -> dict:
        """Check wtpn31..wtpn35 and return all active JTWC storms."""
        storms = []
        errors = []
        for i in range(1, 6):
            r = self.get_warning(f"wtpn3{i}")
            if r.get("ok"):
                storms.append(r)
            elif "no active storm" not in (r.get("error") or ""):
                errors.append(r.get("error"))
        return {
            "ok": True,
            "source": self.source_id,
            "n_active": len(storms),
            "storms": storms,
            "errors": errors,
        }

    def check_availability(self):
        return {"source_id": self.source_id, "available": True, "note": "live JTWC text warnings"}
