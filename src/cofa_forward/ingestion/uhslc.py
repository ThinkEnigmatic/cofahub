"""University of Hawaii Sea Level Center (UHSLC) tide-gauge adapter.

Sea level is the most ENSO-coupled, atoll-critical variable the FAS face — a
strong El Niño can raise western-Pacific sea level by tens of centimetres,
driving the king-tide and inundation flooding the RMI/FSM experience. The PEAC
seasonal sea-level outlook was **discontinued January 2020**; UHSLC is the
authoritative current source.

Data: UHSLC Fast Delivery via its ERDDAP server (``global_hourly_fast``), freely
accessible. ``sea_level`` is reported in millimetres above the station datum.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import pandas as pd

from .base import BaseAdapter

_ERDDAP = "https://uhslc.soest.hawaii.edu/erddap/tabledap/global_hourly_fast.csv"

# The FAS tide gauges (UHSLC station name): geo_id -> station name.
FAS_GAUGES: dict[str, str] = {
    "PAL-KOR": "Malakal",  # Palau (Malakal Island, Koror)
    "FSM-YAP": "Yap",
    "FSM-CHUUK": "Chuuk",
    "FSM-POH": "Pohnpei",
    "RMI-KWA": "Kwajalein",
    "RMI-MAJ": "Majuro",
    # No UHSLC tide gauge for Kosrae.
}


def query_url(station: str, start: str, end: str) -> str:
    start = pd.Timestamp(start).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = pd.Timestamp(end).strftime("%Y-%m-%dT%H:%M:%SZ")
    # ERDDAP requires string constraints to be double-quoted.
    quoted = f'"{station}"'
    sel = f"time,sea_level&station_name={quote(quoted)}"
    return f"{_ERDDAP}?{sel}&time>={start}&time<={end}"


class UhslcAdapter(BaseAdapter):
    source_id = "uhslc-tide-gauge"
    source_url = "https://uhslc.soest.hawaii.edu/"
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 60.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def get_daily(self, station: str, days: int = 90) -> dict:
        """Daily mean sea level (mm) for the last ``days`` days at a station."""
        end = datetime.now(UTC)
        start = end - timedelta(days=days)
        url = query_url(station, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        res = self.fetch_text(url)
        if not res.ok:
            return {"ok": False, "error": res.error, "source": self.source_id}
        try:
            import io

            df = pd.read_csv(io.StringIO(res.data), skiprows=[1], parse_dates=["time"])
            df = df.set_index("time")
            s = pd.to_numeric(df["sea_level"], errors="coerce")
            daily = s.resample("D").mean()
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"parse failed: {exc}", "source": self.source_id}
        daily = daily.dropna()
        if daily.empty:
            return {"ok": False, "error": "no sea-level data in range", "source": self.source_id}
        return {
            "ok": True,
            "source": self.source_id,
            "source_url": self.source_url,
            "station": station,
            "series": daily.rename("sea_level_mm"),
            "n_days": int(len(daily)),
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "UHSLC Fast Delivery hourly -> daily mean",
                "notes": "Sea level in mm above the station datum (not an anomaly).",
            },
        }

    def get_latest(self, station: str, days: int = 90) -> dict:
        """Recent daily sea level plus a simple 30-day mean (mm)."""
        r = self.get_daily(station, days=days)
        if not r.get("ok"):
            return r
        s = r["series"]
        latest = float(s.iloc[-1])
        mean30 = float(s.iloc[-30:].mean()) if len(s) >= 30 else float(s.mean())
        r["latest_mm"] = latest
        r["mean30_mm"] = mean30
        r["last_date"] = s.index[-1].strftime("%Y-%m-%d")
        return r

    def check_availability(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "available": True,
            "note": "live UHSLC tide gauges (ERDDAP)",
        }
