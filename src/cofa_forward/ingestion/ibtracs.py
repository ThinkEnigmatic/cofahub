"""IBTrACS historical tropical cyclone track adapter.

Downloads the western North Pacific (WP) basin CSV (v04r01) and normalizes it to
the canonical track schema. The WMO wind/pressure fields are the responsible
agency's values (JMA 10-min mean for the WP basin); per-agency fields (USA/Tokyo)
are retained so wind-speed averaging periods are always explicit.
"""

from __future__ import annotations

import io

import pandas as pd

from .base import BaseAdapter

WP_CSV_URL = (
    "https://www.ncei.noaa.gov/data/"
    "international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/"
    "access/csv/ibtracs.WP.list.v04r01.csv"
)

FAS_BBOX = {"lat_min": 3.0, "lat_max": 11.0, "lon_min": 131.0, "lon_max": 173.0}


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(pd.NA, index=df.index, dtype="Float64")
    return pd.to_numeric(df[col], errors="coerce")


def _str(df: pd.DataFrame, col: str, default: str = "") -> pd.Series:
    if col not in df.columns:
        return pd.Series(default, index=df.index)
    return df[col].astype("string").fillna(default)


def parse_ibtracs(path_or_buffer) -> pd.DataFrame:
    """Parse an IBTrACS CSV into the canonical track schema.

    The IBTrACS CSV has two header rows (column names, then units); the units row
    is skipped. Returns columns: storm_id, name, time (UTC), lat, lon, wind_kt,
    pressure_hpa, agency, basin, usa_wind_kt, jma_wind_kt.
    """
    df = pd.read_csv(path_or_buffer, skiprows=[1], low_memory=False)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    out = pd.DataFrame(
        {
            "storm_id": _str(df, "SID"),
            "name": _str(df, "NAME"),
            "time": pd.to_datetime(df["ISO_TIME"], errors="coerce", utc=True),
            "lat": _num(df, "LAT"),
            "lon": _num(df, "LON"),
            "wind_kt": _num(df, "WMO_WIND"),
            "pressure_hpa": _num(df, "WMO_PRES"),
            "agency": _str(df, "WMO_AGENCY"),
            "basin": _str(df, "BASIN", "WP"),
            "usa_wind_kt": _num(df, "USA_WIND"),
            "jma_wind_kt": _num(df, "TOKYO_WIND"),
        }
    )
    return out


def filter_bbox(
    df: pd.DataFrame,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
) -> pd.DataFrame:
    """Subset a track table to a lat/lon bounding box."""
    return df[
        (df["lat"] >= lat_min)
        & (df["lat"] <= lat_max)
        & (df["lon"] >= lon_min)
        & (df["lon"] <= lon_max)
    ]


class IbtracsAdapter(BaseAdapter):
    source_id = "noaa-ibtracs"
    source_url = WP_CSV_URL
    implementation_status = "implemented_and_tested"

    def __init__(self, cache=None, db=None, timeout: float = 180.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def get_tracks(self, bbox: dict | None = None, max_rows: int | None = None) -> dict:
        """Download and parse the WP basin track table. Never raises on errors."""
        res = self.fetch_text(self.source_url)
        if not res.ok:
            return {
                "ok": False,
                "error": res.error,
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        try:
            df = parse_ibtracs(io.StringIO(res.data))
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": f"parse failed: {exc}",
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        if bbox:
            df = filter_bbox(df, **bbox)
        if max_rows is not None:
            df = df.head(max_rows)
        return {
            "ok": True,
            "source": self.source_id,
            "source_url": self.source_url,
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "n_points": int(len(df)),
            "n_storms": int(df["storm_id"].nunique()) if len(df) else 0,
            "tracks": df,
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "retrieved_at": res.retrieved_at,
                "calculation_method": "CSV parse + WMO wind/pressure selection",
                "notes": "WMO wind/pressure = responsible agency (JMA 10-min for WP).",
            },
        }

    def check_availability(self):
        return {
            "source_id": self.source_id,
            "available": True,
            "note": "live IBTrACS v04r01 WP CSV",
        }
