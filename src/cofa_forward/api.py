"""COFAHUB JSON API — FastAPI wrapper over the COFA FORWARD data layer.

Exposes the live adapters/monitors as JSON for the React frontend. Uses plain
functions (no Streamlit) with a small TTL cache. Auth: a simple name/pass gate
(HTTP Basic) — the demo credential is COFAHUB / COFAREADY.
"""

from __future__ import annotations

import base64
import os
import secrets
import threading
import time
from functools import lru_cache
from typing import Annotated, Any

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import get_config
from .drought.monitor import drought_monitor_status
from .geography.registry import GeographyRegistry
from .guidance.national_plans import NATIONAL_PLANS

# Demo auth (overridable via env for real deployments).
AUTH_USER = os.environ.get("COFAHUB_USER", "COFAHUB")
AUTH_PASS = os.environ.get("COFAHUB_PASS", "COFAREADY")

security = HTTPBasic()
app = FastAPI(title="COFAHUB", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _auth(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> str:
    user = credentials.username
    passw = credentials.password
    # Constant-time compare to avoid timing attacks.
    u_ok = secrets.compare_digest(user.encode(), AUTH_USER.encode())
    p_ok = secrets.compare_digest(passw.encode(), AUTH_PASS.encode())
    if not (u_ok and p_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


def _camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def camelize(obj: Any) -> Any:
    """Recursively convert dict keys from snake_case to camelCase (for JSON)."""
    if isinstance(obj, dict):
        return {_camel(k): camelize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [camelize(x) for x in obj]
    return obj


# ------------------------------------------------------------------------- #
# TTL cache (process-local; the adapters also write a file cache).
# ------------------------------------------------------------------------- #
class TTLCache:
    def __init__(self, ttl: float = 1800.0):
        self.ttl = ttl
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str, fn):
        now = time.time()
        with self._lock:
            hit = self._data.get(key)
            if hit and now - hit[0] < self.ttl:
                return hit[1]
        val = fn()
        with self._lock:
            self._data[key] = (now, val)
        return val


CACHE = TTLCache()


# ------------------------------------------------------------------------- #
# Registry
# ------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _registry() -> GeographyRegistry:
    return GeographyRegistry(get_config().geography_entities())


def _station(geo_id: str) -> dict[str, Any]:
    e = _registry().by_id(geo_id)
    if e is None:
        raise HTTPException(status_code=404, detail=f"no station {geo_id}")
    return {
        "geoId": e.geo_id,
        "name": e.name,
        "country": e.country_code,
        "countryName": {
            "PW": "Palau",
            "FM": "Federated States of Micronesia",
            "MH": "Marshall Islands",
        }.get(e.country_code, e.country_code),
        "lat": e.latitude,
        "lon": e.longitude,
        "population": e.population,
        "entityType": e.entity_type,
    }


# ------------------------------------------------------------------------- #
# Data helpers (plain, no Streamlit)
# ------------------------------------------------------------------------- #
def _long_era5(lat: float, lon: float) -> pd.DataFrame:
    """ERA5 daily precip + tmax/tmin (1997→now), chunked."""
    from .ingestion.rainfall import OpenMeteoArchiveAdapter

    adapter = OpenMeteoArchiveAdapter(config=get_config())
    today = pd.Timestamp.today(tz="UTC").strftime("%Y-%m-%d")
    parts = []
    for start, end in (
        ("1997-01-01", "2006-12-31"),
        ("2007-01-01", "2016-12-31"),
        ("2017-01-01", today),
    ):
        r = adapter.get_daily_climate(lat, lon, start, end)
        if r.get("ok"):
            parts.append(r["series"])
    if not parts:
        return pd.DataFrame()
    df = pd.concat(parts)
    return df[~df.index.duplicated(keep="last")].sort_index()


def _drought_status(lat: float, lon: float) -> dict[str, Any]:
    df = _long_era5(lat, lon)
    if df.empty:
        return {"available": False}
    s = drought_monitor_status(df["precip_mm"])
    return {"available": True, **s}


def _marine(lat: float, lon: float) -> dict[str, Any]:
    from .climate.bleaching import bleaching_alert, degree_heating_weeks
    from .ingestion.marine import MarineAdapter

    adapter = MarineAdapter(cache=_file_cache())
    cur = adapter.get_marine(lat, lon)
    if not cur.get("ok"):
        return {"available": False}
    sst = adapter.get_sst_daily(lat, lon)
    dhw = degree_heating_weeks(sst["series"]) if sst.get("ok") else None
    c = cur["current"]
    return {
        "available": True,
        "waveHeightM": c.get("wave_height_m"),
        "wavePeriodS": c.get("wave_period_s"),
        "waveDirectionDeg": c.get("wave_direction_deg"),
        "sstC": c.get("sst_c"),
        "dhwCWeeks": dhw,
        "bleachingAlert": bleaching_alert(dhw),
    }


def _file_cache():
    from .storage.cache import FileCache

    cfg = get_config()
    cfg.ensure_data_dirs()
    return FileCache(cfg.data_dir("cache"), cfg.cache_ttl_seconds)


def _sea_level(geo_id: str) -> dict[str, Any]:
    from .ingestion.uhslc import FAS_GAUGES, UhslcAdapter

    if geo_id not in FAS_GAUGES:
        return {"available": False, "reason": "no tide gauge"}
    r = UhslcAdapter(cache=_file_cache()).get_latest(FAS_GAUGES[geo_id])
    if not r.get("ok"):
        return {"available": False, "reason": r.get("error")}
    return {
        "available": True,
        "station": r["station"],
        "latestMm": r["latest_mm"],
        "mean30Mm": r["mean30_mm"],
        "lastDate": r["last_date"],
    }


# ------------------------------------------------------------------------- #
# Endpoints
# ------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    return {"ok": True, "name": "COFAHUB", "version": "1.0.0"}


@app.get("/api/stations", dependencies=[Depends(_auth)])
def stations():
    return [_station(e.geo_id) for e in _registry().all()]


@app.get("/api/enso", dependencies=[Depends(_auth)])
def enso():
    from .climate.enso_analog import enso_analogs
    from .ingestion.enso import CpcOniAdapter

    def load():
        r = CpcOniAdapter(cache=_file_cache()).get_oni()
        if not r.get("ok"):
            return {"available": False}
        cur = r["latest"]["anom"]
        phase = "el_nino" if cur >= 0.5 else ("la_nina" if cur <= -0.5 else "neutral")
        return {
            "available": True,
            "phase": phase,
            "season": r["latest"]["season"],
            "year": r["latest"]["year"],
            "anom": cur,
            "analogs": enso_analogs(phase, abs(cur), get_config().enso_episodes(), r["series"]),
        }

    return camelize(CACHE.get("enso", load))


@app.get("/api/drought/{geo_id}", dependencies=[Depends(_auth)])
def drought(geo_id: str):
    s = _station(geo_id)
    return camelize(CACHE.get(f"drought:{geo_id}", lambda: _drought_status(s["lat"], s["lon"])))


@app.get("/api/rainfall/{geo_id}", dependencies=[Depends(_auth)])
def rainfall(geo_id: str):
    """Monthly precipitation + climatology series (for the chart)."""
    from .drought.percentiles import monthly_distributions
    from .drought.rainfall_metrics import monthly_totals

    s = _station(geo_id)

    def load():
        df = _long_era5(s["lat"], s["lon"])
        if df.empty:
            return {"available": False}
        monthly = monthly_totals(df["precip_mm"], min_days_frac=0.8)
        dists = monthly_distributions(monthly, "1991-01-01", "2020-12-31")
        clim = pd.Series(
            {m: d.median() for m, d in dists.items()},
            name="climatology",
        )
        # Last 36 months of actual + the 12-month climatology (repeated).
        recent = monthly.dropna().iloc[-36:]
        return {
            "available": True,
            "months": [t.strftime("%Y-%m") for t in recent.index],
            "values": [round(float(v), 1) for v in recent.values],
            "climatology": [round(float(clim.get(m.month, float("nan"))), 1) for m in recent.index],
        }

    return camelize(CACHE.get(f"rainfall:{geo_id}", load))


@app.get("/api/marine/{geo_id}", dependencies=[Depends(_auth)])
def marine(geo_id: str):
    s = _station(geo_id)
    return CACHE.get(f"marine:{geo_id}", lambda: _marine(s["lat"], s["lon"]))


@app.get("/api/sealevel/{geo_id}", dependencies=[Depends(_auth)])
def sealevel(geo_id: str):
    return CACHE.get(f"sealevel:{geo_id}", lambda: _sea_level(geo_id))


@app.get("/api/compound/{geo_id}", dependencies=[Depends(_auth)])
def compound(geo_id: str):
    from .hazards.compound import compound_flags

    s = _station(geo_id)

    def load():
        d = _drought_status(s["lat"], s["lon"])
        m = _marine(s["lat"], s["lon"])
        if not d.get("available") and not m.get("available"):
            return []
        return [
            {"text": f, "severity": "warning" if "Red" in f or "tropical cyclone" in f else "watch"}
            for f in compound_flags(
                drought_quintile=d.get("quintile"),
                peac_index=d.get("peac_index"),
                wave_height_m=m.get("waveHeightM"),
            )
        ]

    return CACHE.get(f"compound:{geo_id}", load)


@app.get("/api/verification/{geo_id}", dependencies=[Depends(_auth)])
def verification(geo_id: str):
    from .ingestion.ghcnd import FAS_STATIONS, GhcndAdapter
    from .ingestion.weather import OpenMeteoForecastAdapter
    from .intelligence.verification import bias, mae, pearson, rmse

    s = _station(geo_id)

    def load():
        fc = OpenMeteoForecastAdapter(config=get_config(), cache=_file_cache()).get_past_forecast(
            s["lat"], s["lon"], past_days=30
        )
        if not fc.get("ok"):
            return {"available": False}
        if geo_id in FAS_STATIONS:
            obs = GhcndAdapter(cache=_file_cache()).get_daily(FAS_STATIONS[geo_id][0])
            if not obs.get("ok"):
                return {"available": False}
            observed = obs["series"]["prcp_mm"]
            src = f"GHCNd {FAS_STATIONS[geo_id][0]}"
        else:
            df = _long_era5(s["lat"], s["lon"])
            observed = df["precip_mm"]
            src = "ERA5 (archive)"
        oi = observed.index.tz_localize(None)
        fi = fc["series"].index.tz_localize(None)
        common = oi.intersection(fi)
        if len(common) < 5:
            return {"available": False}
        o = pd.Series(observed.to_numpy(), index=oi).loc[common]
        f = pd.Series(fc["series"].to_numpy(), index=fi).loc[common]
        return {
            "available": True,
            "nDays": int(len(common)),
            "biasMm": bias(o, f),
            "maeMm": mae(o, f),
            "rmseMm": rmse(o, f),
            "correlation": pearson(o, f),
            "observedSource": src,
            "periodStart": common.min().strftime("%Y-%m-%d"),
            "periodEnd": common.max().strftime("%Y-%m-%d"),
        }

    return CACHE.get(f"verif:{geo_id}", load)


@app.get("/api/trends/{geo_id}", dependencies=[Depends(_auth)])
def trends(geo_id: str):
    from .climate.trends import trend_summary
    from .ingestion.ghcnd import FAS_STATIONS, GhcndAdapter

    if geo_id not in FAS_STATIONS:
        return {"available": False, "reason": "no station record"}

    def load():
        r = GhcndAdapter(cache=_file_cache()).get_daily(FAS_STATIONS[geo_id][0])
        if not r.get("ok"):
            return {"available": False}
        df = r["series"]
        precip = df["prcp_mm"].resample("YE").sum(min_count=300)
        tmax = df["tmax_c"].resample("YE").mean()
        return {
            "available": True,
            "stationId": FAS_STATIONS[geo_id][0],
            "rainfall": trend_summary(precip, "annual rainfall", "mm"),
            "tmax": trend_summary(tmax, "annual mean Tmax", "°C"),
        }

    return camelize(CACHE.get(f"trends:{geo_id}", load))


@app.get("/api/plans", dependencies=[Depends(_auth)])
def plans():
    return camelize(NATIONAL_PLANS)


@app.get("/api/login")
def login(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    """Explicit login endpoint (returns ok on valid creds)."""
    _auth(credentials)
    token = base64.b64encode(
        f"{credentials.username}:{credentials.password}".encode()
    ).decode()
    return {"ok": True, "token": token, "user": credentials.username}


# ------------------------------------------------------------------------- #
# Static frontend (serve the React build when present) — SPA fallback.
# ------------------------------------------------------------------------- #
from pathlib import Path  # noqa: E402

from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

_WEB_DIR = Path(__file__).resolve().parents[2] / "apps" / "web" / "dist"

if _WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=_WEB_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path and (f := _WEB_DIR / path).is_file():
            return FileResponse(f)
        return FileResponse(_WEB_DIR / "index.html")
