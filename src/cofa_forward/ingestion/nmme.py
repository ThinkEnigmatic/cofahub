"""NMME seasonal multi-model ensemble forecast adapter.

The North American Multi-Model Ensemble provides gridded (1°) seasonal forecasts
from ~6 coupled models, published monthly on the CPC FTP server as NetCDF3.
This adapter extracts the ensemble-mean forecast at the nearest grid cell for a
FAS location and assembles a multi-model seasonal outlook.

Files: ``<model>.<var>.<yyyymm>.ENSMEAN.fcst.nc`` under ``netcdf/<cycle>/<model>/``.
Variables: ``prate`` (mm/s), ``tmp2m`` (2m temp), ``tmpsfc`` (surface temp).
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from .base import BaseAdapter

NMME_BASE = "https://ftp.cpc.ncep.noaa.gov/International/nmme/netcdf"

MODELS = ["CanESM5", "CFSv2", "GEM5.2_NEMO", "NASA_GEOS5v2", "NCAR_CCSM4", "NCAR_CESM1"]

_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

VARIABLES = {"prate": "mm/s", "tmp2m": "K", "tmpsfc": "K"}


def cycle_to_yyyymm(cycle: str) -> str:
    """``oct2026ic`` -> ``202610``."""
    m = re.match(r"([a-z]{3})(\d{4})ic", cycle.lower())
    if not m:
        raise ValueError(f"unexpected cycle name: {cycle!r}")
    month = _MONTHS[m.group(1)]
    return f"{m.group(2)}{month:02d}"


def cycle_year_month(cycle: str) -> tuple[int, int]:
    m = re.match(r"([a-z]{3})(\d{4})ic", cycle.lower())
    if not m:
        raise ValueError(f"unexpected cycle name: {cycle!r}")
    return int(m.group(2)), _MONTHS[m.group(1)]


def parse_cycle_listing(html: str) -> list[str]:
    """Extract cycle directory names (e.g. ``oct2026ic``) from an FTP HTML listing."""
    names = re.findall(r"([a-z]{3}\d{4}ic)/?", html.lower())
    return sorted(set(names), key=cycle_year_month)


def target_months(values) -> pd.DatetimeIndex:
    """Decode NMME 'target' values (months since 1960-01) into month labels."""
    base = pd.Timestamp("1960-01-01")
    return pd.DatetimeIndex([base + pd.DateOffset(months=int(v)) for v in values])


def extract_point(ds: xr.Dataset, lat: float, lon: float) -> pd.Series:
    """Extract the 12-month forecast at the nearest grid cell."""
    lat_i = int(np.abs(ds["lat"].values - lat).argmin())
    lon_i = int(np.abs(ds["lon"].values - lon).argmin())
    vals = ds["fcst"][:, lat_i, lon_i].values
    return pd.Series(vals, index=target_months(ds["target"].values), name="fcst")


def prate_to_mm_day(series: pd.Series) -> pd.Series:
    """Convert precipitation rate (mm/s) to mm/day."""
    return series * 86400.0


class NmmeAdapter(BaseAdapter):
    source_id = "noaa-nmme"
    source_url = NMME_BASE
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 60.0):
        super().__init__(cache=cache, db=db, timeout=timeout)
        self.raw_dir = Path(config.data_dir("raw")) / "nmme" if config else Path("data/raw/nmme")

    def list_cycles(self) -> list[str]:
        res = self.fetch_text(f"{NMME_BASE}/")
        if not res.ok:
            return []
        return parse_cycle_listing(res.data)

    def latest_cycle(self) -> str | None:
        cycles = self.list_cycles()
        if not cycles:
            return None
        return max(cycles, key=cycle_year_month)

    def _file_url(self, cycle: str, model: str, variable: str) -> str:
        yyyymm = cycle_to_yyyymm(cycle)
        return f"{NMME_BASE}/{cycle}/{model}/{model}.{variable}.{yyyymm}.ENSMEAN.fcst.nc"

    def _open(self, url: str, model: str, variable: str, cycle: str) -> xr.Dataset:
        dest = self.raw_dir / f"{model}_{variable}_{cycle}.nc"
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            resp = self.session.get(url, stream=True, timeout=self.timeout)
            resp.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(256 * 1024):
                    fh.write(chunk)
        return xr.open_dataset(dest, decode_times=False)

    def get_forecast(
        self, lat: float, lon: float, variable: str = "prate", model: str = "CanESM5"
    ) -> dict:
        """Extract one model's 12-month ensemble-mean forecast at a point."""
        cycle = self.latest_cycle()
        if cycle is None:
            return {"ok": False, "error": "no NMME cycles available", "source": self.source_id}
        url = self._file_url(cycle, model, variable)
        try:
            ds = self._open(url, model, variable, cycle)
            series = extract_point(ds, lat, lon)
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": f"{model} fetch/parse failed: {exc}",
                "source": self.source_id,
            }
        if variable == "prate":
            series = prate_to_mm_day(series)
        return {
            "ok": True,
            "source": self.source_id,
            "cycle": cycle,
            "model": model,
            "variable": variable,
            "units": "mm/day" if variable == "prate" else VARIABLES.get(variable, ""),
            "series": series,
            "resolution": "1 deg (~110 km) global grid",
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": url,
                "calculation_method": "nearest_grid_cell extraction of ENSMEAN",
                "notes": "1-deg model ensemble mean; coarse for individual atolls.",
            },
        }

    def get_multimodel(self, lat: float, lon: float, variable: str = "prate") -> dict:
        """Assemble a multi-model seasonal outlook (ensemble mean + spread)."""
        rows = {}
        for model in MODELS:
            r = self.get_forecast(lat, lon, variable=variable, model=model)
            if r.get("ok"):
                rows[model] = r["series"]
        if not rows:
            return {"ok": False, "error": "no models available", "source": self.source_id}

        df = pd.DataFrame(rows)
        mean = df.mean(axis=1)
        spread = df.std(axis=1)
        return {
            "ok": True,
            "source": self.source_id,
            "cycle": self.latest_cycle(),
            "variable": variable,
            "units": "mm/day" if variable == "prate" else VARIABLES.get(variable, ""),
            "models": df,
            "ensemble_mean": mean,
            "ensemble_std": spread,
            "n_models": int(df.shape[1]),
            "resolution": "1 deg (~110 km) global grid",
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "multi-model ENSMEAN nearest-grid-cell extraction",
                "notes": (
                    "Model spread reflects inter-model disagreement, not "
                    "within-model ensemble spread."
                ),
            },
        }

    def check_availability(self):
        return {"source_id": self.source_id, "available": True, "note": "live NMME (CPC FTP)"}
