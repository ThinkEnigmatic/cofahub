"""PEAC seasonal rainfall outlook adapter (weather.gov/peac).

The Pacific ENSO Applications Climate (PEAC) Services publishes a monthly
seasonal rainfall outlook — an experimental consensus of 7 seasonal models —
for 14 stations across Hawaii and the US-Affiliated Pacific Islands, in tercile
(three-category) probabilistic form.

This adapter scrapes the page into structured fields: the season (e.g. ``SON
2024``), the last-updated date, and per-station "final outlook" + tercile
probabilities (``below:near:above``). Seven of the 14 stations are in the FAS
(Palau / FSM / RMI) and carry a ``geo_id`` for direct map/app linkage.

**Freshness guard.** PEAC's seasonal rainfall outlook has not been updated since
September 2024 (the Pacific ENSO Update newsletter is discontinued). The adapter
records ``last_updated`` and flags ``is_stale`` so the app can present the data
as historical rather than current. It never fabricates a newer outlook.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Any

from .base import BaseAdapter

_SOURCE_URL = "https://www.weather.gov/peac/rainfall_new"

# Month triplets for each 3-month season label.
_SEASON_MONTHS = {
    "DJF": ("December", "January", "February"),
    "JFM": ("January", "February", "March"),
    "FMA": ("February", "March", "April"),
    "MAM": ("March", "April", "May"),
    "AMJ": ("April", "May", "June"),
    "MJJ": ("May", "June", "July"),
    "JJA": ("June", "July", "August"),
    "JAS": ("July", "August", "September"),
    "ASO": ("August", "September", "October"),
    "SON": ("September", "October", "November"),
    "OND": ("October", "November", "December"),
    "NDJ": ("November", "December", "January"),
}

# The 14 stations on the page, mapped to region. FAS stations carry a geo_id.
_STATIONS = {
    "Koror": ("PW", "Palau", "PAL-KOR"),
    "Yap": ("FM", "Federated States of Micronesia", "FSM-YAP"),
    "Chuuk": ("FM", "Federated States of Micronesia", "FSM-CHUUK"),
    "Pohnpei": ("FM", "Federated States of Micronesia", "FSM-POH"),
    "Kosrae": ("FM", "Federated States of Micronesia", "FSM-KOS"),
    "Kwajalein": ("MH", "Republic of the Marshall Islands", "RMI-KWA"),
    "Majuro": ("MH", "Republic of the Marshall Islands", "RMI-MAJ"),
    "Guam": ("GU", "Guam", None),
    "Saipan": ("MP", "Commonwealth of the Northern Mariana Islands", None),
    "Pago Pago": ("AS", "American Samoa", None),
    "Lihue": ("US-HI", "Hawaii", None),
    "Honolulu": ("US-HI", "Hawaii", None),
    "Kahului": ("US-HI", "Hawaii", None),
    "Hilo": ("US-HI", "Hawaii", None),
}

_SEASON_RE = re.compile(r"\(\s*([A-Z]{3})\s*\)\s*(\d{4})")
_UPDATED_RE = re.compile(r"Last\s+Updated\s*:\s*([A-Za-z]+\s+\d{1,2}),\s*(?:&nbsp;|\s)*(\d{4})")
_PROB_RE = re.compile(r"\d{2}:\d{2}:\d{2}")

# A monthly product older than this many days is considered stale (6 months).
_STALE_DAYS = 180


class _TableCells(HTMLParser):
    """Collect table rows as lists of stripped cell texts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] = []
        self._cell: list[str] = []
        self._in_td = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "td":
            self._in_td = True
            self._cell = []
        elif tag == "tr":
            self._row = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._in_td:
            self._row.append(" ".join("".join(self._cell).split()))
            self._in_td = False
        elif tag == "tr":
            if self._row:
                self.rows.append(self._row)
            self._row = []

    def handle_data(self, data: str) -> None:
        if self._in_td:
            self._cell.append(data)


def parse_peac_outlook(raw_html: str, today: date | None = None) -> dict[str, Any]:
    """Parse the PEAC seasonal rainfall outlook HTML into structured fields."""
    today = today or date.today()
    out: dict[str, Any] = {"stations": []}

    m = _SEASON_RE.search(raw_html)
    if m:
        label = m.group(1)
        year = int(m.group(2))
        months = _SEASON_MONTHS.get(label)
        out["season_label"] = label
        out["year"] = year
        out["season"] = f"{label} {year}"
        out["season_full"] = (
            f"{months[0]}–{months[1]}–{months[2]} {year}" if months else out["season"]
        )

    m = _UPDATED_RE.search(raw_html)
    if m:
        try:
            out["last_updated"] = (
                datetime.strptime(f"{m.group(1)} {m.group(2)}", "%B %d %Y").date().isoformat()
            )
        except ValueError:
            out["last_updated"] = f"{m.group(1)} {m.group(2)}"

    parser = _TableCells()
    parser.feed(raw_html)
    for row in parser.rows:
        if len(row) < 3:
            continue
        name = row[0].strip()
        if name not in _STATIONS:
            continue
        prob = row[-1].strip()
        if not _PROB_RE.fullmatch(prob):
            continue
        country_code, region, geo_id = _STATIONS[name]
        final_outlook = row[-2].strip() if len(row) >= 3 else ""
        out["stations"].append(
            {
                "name": name,
                "country_code": country_code,
                "region": region,
                "geo_id": geo_id,
                "final_outlook": final_outlook,
                "probabilities": prob,
                "probabilities_parsed": {
                    "below": int(prob[0:2]),
                    "near": int(prob[3:5]),
                    "above": int(prob[6:8]),
                },
            }
        )

    if out.get("last_updated"):
        try:
            lu = datetime.strptime(out["last_updated"], "%Y-%m-%d").date()
            out["stale_days"] = (today - lu).days
            out["is_stale"] = out["stale_days"] > _STALE_DAYS
        except ValueError:
            out["is_stale"] = True
    else:
        out["is_stale"] = True

    return out


class PeacRainfallOutlookAdapter(BaseAdapter):
    source_id = "noaa-peac-rainfall-outlook"
    source_url = _SOURCE_URL
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 30.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def get_outlook(self) -> dict[str, Any]:
        """Fetch and parse the PEAC seasonal rainfall outlook."""
        res = self.fetch_text(self.source_url)
        if not res.ok:
            return {
                "ok": False,
                "error": res.error,
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        try:
            parsed = parse_peac_outlook(res.data)
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": f"parse failed: {exc}",
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        if not parsed.get("stations"):
            return {
                "ok": False,
                "error": "no station outlooks found (PEAC markup changed?)",
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
                "calculation_method": "HTML scrape of the official PEAC seasonal rainfall outlook",
                "notes": (
                    "Experimental consensus of 7 seasonal models, tercile form. "
                    "Tercile cut-offs based on CPC 1991-2020 climatology."
                ),
            },
            **parsed,
        }

    def check_availability(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "available": True,
            "note": "live PEAC seasonal rainfall outlook (weather.gov/peac; see freshness guard)",
        }
