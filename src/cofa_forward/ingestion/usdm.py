"""U.S. Drought Monitor (USDM) adapter — the official D0–D4 drought ranking.

The USDM is the source of truth for the D0–D4 drought categories. It added
coverage of the U.S.-Affiliated Pacific Islands (USAPI) — which includes the
Freely Associated States (Palau, FSM, RMI) — in 2019. The map is released every
Thursday (data valid the preceding Tuesday) by the National Drought Mitigation
Center / NOAA / USDA.

The vector data for the islands lives in the **OCONUS** shapefile bundle
(``shapefiles_o/USDM_{data-valid-date}_O.zip``), whose ``.dbf`` table carries a
``Dx`` field per named island/atoll: ``NO`` (no drought), ``D0``–``D4``, and
``ND`` (no data), plus an ``Impact`` field (``S`` short-term / ``L`` long-term).

Only a subset of atolls are individually ranked — the USDM labels the larger /
monitored islands and groups the rest. This adapter maps those names onto the
registry ``geo_id`` values and leaves the rest unranked (never guessed).
"""

from __future__ import annotations

import datetime as dt
import io
import json
import struct
import zipfile
from pathlib import Path
from typing import Any

import requests

from ..timeutil import format_iso, now_utc

SOURCE_ID = "noaa-usdm"
SOURCE_NAME = "U.S. Drought Monitor (USDM)"
OCONUS_URL_TMPL = "https://droughtmonitor.unl.edu/data/shapefiles_o/USDM_{date}_O.zip"

# USDM island/atoll name -> registry geo_id. Only the islands the USDM ranks.
USDM_NAME_TO_GEO: dict[str, str] = {
    "Majuro": "RMI-MAJ",
    "Kwajalein": "RMI-KWA",
    "Wotje": "RMI-WOT",
    "Utirik": "RMI-UTR",
    "Jaluit": "RMI-JAL",
    "Chuuk Lagoon": "FSM-CHUUK",
    "Kapingamarangi": "FSM-POH-KAP",
    "Kosrae": "FSM-KOS",
    "Nukuoro": "FSM-POH-NUK",
    "Pohnpei": "FSM-POH",
    "Ulithi": "FSM-YAP-ULI",
    "Woleai": "FSM-YAP-WOL",
    "Yap": "FSM-YAP",
    "Koror": "PAL-KOR",
}

# USDM "Dx" codes.
LEVEL_KEYS = ("NO", "D0", "D1", "D2", "D3", "D4")


def _read_dbf(data: bytes) -> list[dict[str, str]]:
    """Parse a minimal .dbf table into a list of records (no dependencies)."""
    if len(data) < 33:
        return []
    n_records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    # field descriptors: 32 bytes each, after the 32-byte header, until 0x0D
    fields: list[tuple[str, str, int]] = []
    pos = 32
    while pos < header_len:
        b = data[pos]
        if b == 0x0D:
            break
        name = data[pos : pos + 11].split(b"\x00")[0].decode("ascii", "ignore")
        ftype = chr(data[pos + 11])
        flen = data[pos + 16]
        fields.append((name, ftype, flen))
        pos += 32
    rec_len = sum(flen for _, _, flen in fields)
    records: list[dict[str, str]] = []
    cursor = header_len
    for _ in range(n_records):
        if cursor + 1 + rec_len > len(data):
            break
        cursor += 1  # deletion flag
        rec = {}
        off = 0
        for name, _ftype, flen in fields:
            rec[name] = data[cursor + off : cursor + off + flen].decode("ascii", "ignore").strip()
            off += flen
        records.append(rec)
        cursor += rec_len
    return records


def _discover_latest(session: requests.Session, timeout: float) -> tuple[str, bytes] | None:
    """Find the most recent USDM OCONUS shapefile (released weekly, data valid Tuesdays)."""
    today = dt.date.today()
    tue = today - dt.timedelta(days=(today.weekday() - 1) % 7)
    for i in range(4):  # try the last 4 Tuesdays
        d = tue - dt.timedelta(weeks=i)
        url = OCONUS_URL_TMPL.format(date=d.strftime("%Y%m%d"))
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 200 and resp.content[:2] == b"PK":
                return d.isoformat(), resp.content
        except requests.RequestException:
            continue
    return None


def parse_oconus(zip_bytes: bytes) -> list[dict[str, str]]:
    """Extract the island records from an OCONUS shapefile bundle."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        dbf = next((n for n in zf.namelist() if n.lower().endswith(".dbf")), None)
        if dbf is None:
            return []
        return _read_dbf(zf.read(dbf))


def snapshot_path(root: Path) -> Path:
    return root / "data" / "snapshot" / "usdm" / "latest.json"


def _is_fresh(path: Path, ttl_seconds: int) -> bool:
    return path.exists() and (now_utc().timestamp() - path.stat().st_mtime) < ttl_seconds


class UsdmAdapter:
    """Fetch + parse the official USDM D0–D4 ranking for the FAS, disk-cached."""

    source_id = SOURCE_ID
    source_name = SOURCE_NAME

    def __init__(self, root: Path, timeout: float = 30.0, ttl_seconds: int = 24 * 3600):
        self.root = root
        self.timeout = timeout
        self.ttl_seconds = ttl_seconds
        self.session = requests.Session()

    def get_latest(self, force: bool = False) -> dict[str, Any]:
        """Return the latest USDM status; cached to disk between refreshes."""
        path = snapshot_path(self.root)
        if not force and _is_fresh(path, self.ttl_seconds):
            try:
                return json.loads(path.read_text())
            except (OSError, ValueError):
                pass

        found = _discover_latest(self.session, self.timeout)
        if found is None:
            # fall back to any existing snapshot, even if stale
            if path.exists():
                try:
                    return json.loads(path.read_text())
                except (OSError, ValueError):
                    pass
            return {"ok": False, "error": "USDM OCONUS shapefile unavailable"}

        date, zip_bytes = found
        records = parse_oconus(zip_bytes)
        stations: dict[str, dict[str, Any]] = {}
        for rec in records:
            name = rec.get("Name", "").strip()
            geo = USDM_NAME_TO_GEO.get(name)
            if not geo:
                continue
            dx = rec.get("Dx", "").strip()
            level = dx if dx in LEVEL_KEYS and dx not in ("NO", "ND") else None
            impact = rec.get("Impact", "").strip().strip("()") or None
            stations[geo] = {"level": level, "impact": impact, "usdmName": name}

        result: dict[str, Any] = {
            "ok": True,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "date": date,
            "source_url": OCONUS_URL_TMPL.format(date=date.replace("-", "")),
            "retrieved_at": format_iso(now_utc()),
            "stations": stations,
            "note": (
                "Official U.S. Drought Monitor D0–D4 categories for the U.S.-Affiliated "
                "Pacific Islands. Only the islands the USDM ranks individually are listed; "
                "others are unranked. D0 abnormally dry; D1–D4 moderate to exceptional drought."
            ),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2))
        return result

    def level_for(self, geo_id: str, force: bool = False) -> dict[str, Any] | None:
        """Return the USDM status for one geo_id, or None if not individually ranked."""
        latest = self.get_latest(force=force)
        if not latest.get("ok"):
            return None
        return latest.get("stations", {}).get(geo_id)
