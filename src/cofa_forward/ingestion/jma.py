"""JMA RSMC Tokyo-Typhoon Center active-storm adapter.

The Japan Meteorological Agency is the WMO-designated RSMC for the western North
Pacific. Its typhoon JSON endpoints (unauthenticated, machine-readable) provide
the authoritative active-storm list and per-storm advisory details (position,
10-min sustained wind, pressure, forecast track with 70% probability circles).
"""

from __future__ import annotations

from .base import BaseAdapter

BASE = "https://www.jma.go.jp/bosai/typhoon/data"


def _tofloat(value) -> float | None:
    if value is None or value == "" or value == "-":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _part_name(part) -> str:
    if isinstance(part, dict):
        return part.get("en", part.get("jp", ""))
    return str(part)


def _position(p: dict) -> dict | None:
    deg = (p.get("position") or {}).get("deg")
    if deg and len(deg) >= 2:
        return {"lat": float(deg[0]), "lon": float(deg[1])}
    return None


def _max_radius(warnings: list | None) -> float | None:
    if not warnings:
        return None
    vals = []
    for w in warnings:
        r = (w.get("range") or {}).get("km")
        if r is not None:
            vals.append(float(r))
    return max(vals) if vals else None


def normalize_jma_spec(payload: list) -> dict:
    """Normalize a JMA specifications.json payload into a structured dict."""
    title = analysis = None
    forecasts: list[dict] = []
    for p in payload or []:
        name = _part_name(p.get("part"))
        if name == "title":
            title = p
        elif name == "Analysis":
            analysis = p
        elif name and "Forecast" in name:
            forecasts.append(p)

    def wind(p: dict) -> dict:
        mw = p.get("maximumWind") or {}
        sus = mw.get("sustained") or {}
        gust = mw.get("gust") or {}
        return {
            "wind_sustained_kt": _tofloat(sus.get("kt")),
            "wind_sustained_ms": _tofloat(sus.get("m/s")),
            "wind_gust_kt": _tofloat(gust.get("kt")),
        }

    meta = {}
    if title:
        issue = title.get("issue") or {}
        name = title.get("name") or {}
        meta = {
            "typhoon_number": title.get("typhoonNumber"),
            "name_en": name.get("en"),
            "name_jp": name.get("jp"),
            "category": (title.get("category") or {}).get("en"),
            "issue_utc": issue.get("UTC"),
        }

    analysis_out = {}
    if analysis:
        analysis_out = {
            "position": _position(analysis),
            "pressure_hpa": _tofloat(analysis.get("pressure")),
            "gale_radius_km": _max_radius(analysis.get("galeWarning")),
            "storm_radius_km": _max_radius(analysis.get("stormWarning")),
            **wind(analysis),
        }

    fc_out = []
    for p in forecasts:
        validtime = p.get("validtime") or {}
        pc = p.get("probabilityCircleRadius") or {}
        fc_out.append(
            {
                "hours": p.get("advancedHours"),
                "valid_utc": validtime.get("UTC"),
                "position": _position(p),
                "pressure_hpa": _tofloat(p.get("pressure")),
                "wind_sustained_kt": _tofloat(
                    (p.get("maximumWind") or {}).get("sustained", {}).get("kt")
                ),
                "probability_circle_km": _tofloat(pc.get("km")),
            }
        )

    return {"meta": meta, "analysis": analysis_out, "forecasts": fc_out}


class JmaTyphoonAdapter(BaseAdapter):
    source_id = "jma-rsmc-tokyo"
    base = BASE
    source_url = f"{BASE}/targetTc.json"
    implementation_status = "implemented_and_tested"

    def __init__(self, cache=None, db=None, timeout: float = 30.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def active_storms(self) -> dict:
        """List currently tracked western North Pacific tropical cyclones."""
        res = self.fetch_json(f"{self.base}/targetTc.json")
        if not res.ok:
            return {"ok": False, "error": res.error, "source": self.source_id}
        storms = []
        for item in res.data or []:
            storms.append(
                {
                    "tc_id": item.get("tropicalCyclone"),
                    "typhoon_number": item.get("typhoonNumber"),
                    "category": item.get("category"),
                    "issue": item.get("issue"),
                }
            )
        return {
            "ok": True,
            "source": self.source_id,
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "n_active": len(storms),
            "storms": storms,
        }

    def storm_details(self, tc_id: str) -> dict:
        """Fetch normalized advisory details for a storm (e.g. 'TC2637')."""
        res = self.fetch_json(f"{self.base}/{tc_id}/specifications.json")
        if not res.ok:
            return {"ok": False, "error": res.error, "source": self.source_id, "tc_id": tc_id}
        try:
            norm = normalize_jma_spec(res.data)
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": f"normalize failed: {exc}",
                "source": self.source_id,
                "tc_id": tc_id,
            }
        return {
            "ok": True,
            "source": self.source_id,
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "tc_id": tc_id,
            **norm,
        }

    def check_availability(self):
        return {"source_id": self.source_id, "available": True, "note": "live JMA RSMC Tokyo JSON"}
