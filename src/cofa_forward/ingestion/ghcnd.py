"""NOAA GHCN-Daily (GHCNd) adapter — in-situ station ground truth.

GHCNd provides quality-assured daily precipitation and temperature from land
stations worldwide. For the Freely Associated States this is the *only*
independent ground truth against which the app's satellite/reanalysis layers
(ERA5, CHIRPS, IMERG) can be validated. The seven airport WMO/GSN stations map
1:1 to the registry.

Data: NCEI HTTPS CSV ``…/global-historical-climatology-network-daily/access/{id}.csv``
(public domain). PRCP is reported in millimetres.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .base import BaseAdapter

_ACCESS = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access"

# The seven FAS airport (WMO/GSN) stations: geo_id -> (GHCNd id, WMO id).
FAS_STATIONS: dict[str, tuple[str, str]] = {
    "PAL-KOR": ("PSW00040309", "91408"),  # Koror, Palau
    "FSM-YAP": ("FMW00040308", "91413"),  # Yap Island WSO AP
    "FSM-CHUUK": ("FMW00040505", "91334"),  # Chuuk (Weno) WSO AP
    "FSM-POH": ("FMW00040504", "91348"),  # Pohnpei WSO
    "FSM-KOS": ("FMC00914395", "91356"),  # Kosrae
    "RMI-KWA": ("RMW00040604", "91366"),  # Kwajalein
    "RMI-MAJ": ("RMW00040710", "91376"),  # Majuro WBAS AP
}

# Daily PRCP sanity cap (mm). The GHCNd record contains occasional non-physical
# accumulations (e.g. 3805 mm/day); values above this are dropped and counted.
_PRCAP_MAX_MM = 500.0

# GHCNd quality flags (2nd field of the *_ATTRIBUTES column) that indicate a
# failed QA check — these observations are dropped.
_QA_FLAGS = set("DGIKLMNORS WXZ")


def station_url(station_id: str) -> str:
    return f"{_ACCESS}/{station_id}.csv"


def parse_ghcnd(csv_text: str) -> pd.DataFrame:
    """Parse a GHCNd ``access`` CSV into a clean daily DataFrame.

    Returns a DataFrame indexed by DATE with columns ``prcp_mm``, ``tmax_c``,
    ``tmin_c``, with QA-failed and non-physical values dropped (NaN).
    """
    import io

    df = pd.read_csv(io.StringIO(csv_text), parse_dates=["DATE"], low_memory=False)
    out = pd.DataFrame(index=df["DATE"])
    for col, outcol, cap in (
        ("PRCP", "prcp_mm", _PRCAP_MAX_MM),
        ("TMAX", "tmax_c", None),
        ("TMIN", "tmin_c", None),
    ):
        vals = pd.to_numeric(df[col], errors="coerce")
        attrs = df[f"{col}_ATTRIBUTES"].astype(str)
        qflag = attrs.str.split(",").str[1].fillna("")
        bad = qflag.apply(lambda q: any(c in _QA_FLAGS for c in q))
        if cap is not None:
            bad = bad | (vals > cap)
        vals = vals.where(~bad)
        out[outcol] = vals
    out = out.sort_index()
    return out[~out.index.duplicated(keep="last")]


class GhcndAdapter(BaseAdapter):
    source_id = "noaa-ghcnd"
    source_url = "https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily"
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 60.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def get_daily(self, station_id: str) -> dict:
        """Fetch a station's full daily record (PRCP/TMAX/TMIN, QA-filtered)."""
        url = station_url(station_id)
        res = self.fetch_text(url)
        if not res.ok:
            return {"ok": False, "error": res.error, "source": self.source_id}
        try:
            df = parse_ghcnd(res.data)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"parse failed: {exc}", "source": self.source_id}
        if df.empty:
            return {"ok": False, "error": "no usable observations", "source": self.source_id}
        return {
            "ok": True,
            "source": self.source_id,
            "source_url": url,
            "station_id": station_id,
            "series": df,
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": url,
                "calculation_method": "GHCNd daily CSV; QA-flagged + >500 mm/day PRCP dropped",
                "notes": "In-situ airport station; the independent ground truth.",
            },
        }

    def get_monthly(self, station_id: str, min_days_frac: float = 0.8) -> dict:
        """Monthly precipitation totals from the daily record (guard against gaps)."""
        r = self.get_daily(station_id)
        if not r.get("ok"):
            return r
        df = r["series"]
        monthly = df["prcp_mm"].resample("ME").sum(min_count=1)
        # completeness guard: drop months with too few days (mirrors rainfall_metrics).
        n_days = df["prcp_mm"].resample("ME").size()
        dim = df["prcp_mm"].resample("ME").apply(lambda s: s.index.days_in_month[0])
        monthly = monthly.where(n_days / dim >= min_days_frac)
        monthly.index = monthly.index.to_period("M").to_timestamp(how="end")
        return {
            "ok": True,
            "source": self.source_id,
            "station_id": station_id,
            "series": monthly.rename("precip_mm"),
            "n_months": int(len(monthly)),
            "n_missing": int(monthly.isna().sum()),
            "provenance": r["provenance"],
        }

    def check_availability(self) -> dict[str, Any]:
        return {"source_id": self.source_id, "available": True, "note": "live NCEI GHCNd"}
