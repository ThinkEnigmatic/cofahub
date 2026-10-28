"""Cached app state for the Streamlit UI.

All expensive loads (config, geography, synthetic sample data, computed
indicators) are cached so reruns are fast and the app never re-downloads or
re-synthesizes data on every interaction.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..climate.climatology import compute_location_climatology  # noqa: F401 (re-export convenience)
from ..config import Config, get_config
from ..geography.registry import GeographyRegistry
from ..intelligence.indicators import compute_location_indicators
from ..sample_data import (
    synthetic_daily_rainfall,
    synthetic_forecast,
    synthetic_impacts,
    synthetic_tracks,
)
from ..storage.cache import FileCache
from ..storage.database import Database


@st.cache_resource(show_spinner=False)
def load_config() -> Config:
    return get_config()


@st.cache_resource(show_spinner=False)
def load_registry() -> GeographyRegistry:
    cfg = load_config()
    return GeographyRegistry(cfg.geography_entities())


@st.cache_data(show_spinner=False)
def get_sample_rainfall(geo_id: str, years: int = 30):
    return synthetic_daily_rainfall(geo_id, years=years)


@st.cache_data(show_spinner=False)
def get_sample_forecast(geo_id: str, lat: float, lon: float):
    return synthetic_forecast(geo_id, lat, lon)


@st.cache_data(show_spinner=False)
def get_sample_tracks():
    return synthetic_tracks()


@st.cache_data(show_spinner=False)
def get_sample_impacts():
    return synthetic_impacts()


@st.cache_data(show_spinner=False)
def get_all_indicators() -> list[dict]:
    """Compute per-location drought/climatology indicators (sample-based)."""
    cfg = load_config()
    registry = load_registry()
    d = cfg.drought
    out = []
    for e in registry.all():
        daily = get_sample_rainfall(e.geo_id)
        ind = compute_location_indicators(
            geo_id=e.geo_id,
            name=e.name,
            daily=daily,
            baseline_start=d["baseline_start"],
            baseline_end=d["baseline_end"],
            min_years=d["baseline_min_years"],
            percentile_categories=d["percentile_categories"],
        )
        out.append(ind)
    return out


@st.cache_data(show_spinner=False)
def get_location_climatology(geo_id: str) -> dict:
    cfg = load_config()
    d = cfg.drought
    daily = get_sample_rainfall(geo_id)
    return compute_location_climatology(
        daily, d["baseline_start"], d["baseline_end"], d["baseline_min_years"]
    )


def make_cache() -> FileCache:
    cfg = load_config()
    cfg.ensure_data_dirs()
    return FileCache(cfg.data_dir("cache"), cfg.cache_ttl_seconds)


def make_db() -> Database:
    cfg = load_config()
    cfg.ensure_data_dirs()
    return Database(cfg.data_root / "catalog.db")


def units_imperial() -> bool:
    return st.session_state.get("units", "metric") == "imperial"


@st.cache_data(ttl=3600, show_spinner=False)
def get_live_enso() -> dict:
    """Fetch the current CPC Oceanic Niño Index (cached for 1 hour)."""
    from ..ingestion.enso import CpcOniAdapter

    adapter = CpcOniAdapter(cache=make_cache())
    return adapter.get_oni()


@st.cache_data(ttl=86400, show_spinner=False)
def get_real_rainfall(geo_id: str, lat: float, lon: float, start: str = "1991-01-01") -> dict:
    """Fetch real daily rainfall (ERA5 via Open-Meteo) for a location, cached 24h."""
    from ..ingestion.rainfall import OpenMeteoArchiveAdapter

    adapter = OpenMeteoArchiveAdapter(config=load_config(), cache=make_cache())
    return adapter.get_rainfall(lat, lon, start, "2024-12-31")


@st.cache_data(ttl=86400, show_spinner=False)
def get_real_tracks() -> dict:
    """Fetch real IBTrACS WP-basin tracks filtered to the FAS bounding box."""
    from ..ingestion.ibtracs import FAS_BBOX, IbtracsAdapter

    adapter = IbtracsAdapter(cache=make_cache())
    return adapter.get_tracks(bbox=FAS_BBOX)


@st.cache_data(ttl=1800, show_spinner=False)
def get_active_storms() -> dict:
    """Fetch current western North Pacific tropical cyclones from JMA."""
    from ..ingestion.jma import JmaTyphoonAdapter

    adapter = JmaTyphoonAdapter(cache=make_cache())
    return adapter.active_storms()


@st.cache_data(ttl=600, show_spinner=False)
def get_jtwc_warnings() -> dict:
    """Fetch current JTWC tropical cyclone warnings (1-min wind + radii)."""
    from ..ingestion.jtwc import JtwcAdapter

    adapter = JtwcAdapter(cache=make_cache())
    return adapter.get_active_warnings()


@st.cache_data(ttl=600, show_spinner=False)
def get_himawari_image(width: int = 550) -> dict:
    """Latest Himawari-9 full-disk satellite image (cached 10 min)."""
    from ..ingestion.himawari import HimawariAdapter

    return HimawariAdapter().latest_full_disk(width=width)


@st.cache_data(ttl=1800, show_spinner=False)
def get_nws_guam_advisory() -> dict:
    """Latest NWS Guam tropical cyclone advisory (TCP) + watches/warnings."""
    from ..ingestion.nws_guam import NwsGuamAdapter

    adapter = NwsGuamAdapter(cache=make_cache())
    return adapter.get_advisory()


@st.cache_data(ttl=1800, show_spinner=False)
def get_storm_details(tc_id: str) -> dict:
    from ..ingestion.jma import JmaTyphoonAdapter

    adapter = JmaTyphoonAdapter(cache=make_cache())
    return adapter.storm_details(tc_id)


@st.cache_data(ttl=3600, show_spinner=False)
def get_forecast_daily_precip(geo_id: str, lat: float, lon: float, days: int = 16) -> dict:
    """Fetch the daily forecast precipitation (mm) series for a location."""
    from ..ingestion.weather import OpenMeteoForecastAdapter

    adapter = OpenMeteoForecastAdapter(config=load_config(), cache=make_cache())
    r = adapter.get_forecast(lat, lon, forecast_days=days)
    if not r.get("ok") or r["daily"].empty:
        return {"ok": False, "error": r.get("error"), "series": pd.Series(dtype=float)}
    return {
        "ok": True,
        "series": r["daily"]["precipitation_sum"],
        "retrieved_at": r["retrieved_at"],
    }


@st.cache_data(ttl=86400, show_spinner=False)
def get_chirps_monthly(geo_id: str, lat: float, lon: float) -> dict:
    """Fetch the CHIRPS v3 monthly rainfall series for a location (cached 24h).

    Issues one HTTP range request per month — slow on first call (~1-2 min for a
    full baseline). Land-masked product; see the adapter docs.
    """
    from ..ingestion.chirps import ChirpsAdapter

    adapter = ChirpsAdapter()
    return adapter.get_monthly_series(lat, lon, "1991-01-01", "2024-12-31")


@st.cache_data(ttl=86400, show_spinner=False)
def get_worldpop_population(
    geo_id: str, country_code: str, lat: float, lon: float, radius_km: float = 10.0
) -> dict:
    """WorldPop population (UN-adjusted 2020) within a radius of a point."""
    from ..ingestion.population import WorldPopAdapter

    adapter = WorldPopAdapter(config=load_config())
    try:
        pop = adapter.population_within_radius(country_code, lat, lon, radius_km)
        return {"ok": True, "population": pop, "radius_km": radius_km}
    except Exception as exc:  # noqa: BLE001 - network/download errors surface here
        return {"ok": False, "error": str(exc)}


@st.cache_data(ttl=86400, show_spinner=False)
def get_zonal_population(geo_id: str, name: str, country_code: str) -> dict:
    """WorldPop population within the actual administrative boundary (FSM/RMI/PW)."""
    from ..ingestion.boundaries import BoundariesAdapter, match_by_name, zonal_population
    from ..ingestion.population import WorldPopAdapter

    if country_code.upper() not in ("FM", "MH", "PW"):
        return {"ok": False, "error": f"no boundaries for country {country_code}"}
    try:
        iso3 = WorldPopAdapter.iso3(country_code)
        ba = BoundariesAdapter(config=load_config())
        record = match_by_name(name, ba.get_admin(iso3, level=1))
        if record is None:
            return {"ok": False, "error": f"no boundary match for {name}"}
        wpa = WorldPopAdapter(config=load_config())
        pop = zonal_population(record["geometry"], wpa.raster_path(iso3))
        return {"ok": True, "population": pop, "pcode": record["pcode"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


@st.cache_data(ttl=86400, show_spinner=False)
def get_nmme_multimodel(lat: float, lon: float, variable: str = "prate") -> dict:
    """Fetch the NMME multi-model seasonal forecast for a location (cached 24h)."""
    from ..ingestion.nmme import NmmeAdapter

    adapter = NmmeAdapter(config=load_config())
    return adapter.get_multimodel(lat, lon, variable=variable)


@st.cache_data(ttl=1800, show_spinner=False)
def get_model_comparison(lat: float, lon: float, variable: str = "temperature_2m") -> dict:
    """Fetch one hourly variable from multiple weather models (cached 30 min)."""
    from ..ingestion.weather import OpenMeteoForecastAdapter

    adapter = OpenMeteoForecastAdapter(config=load_config(), cache=make_cache())
    return adapter.get_model_comparison(lat, lon, variable=variable)


@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_model_status() -> list[dict]:
    """Report the access status of AI global models (WeatherNext, NVIDIA Earth-2)."""
    from ..ingestion.nvidia_earth2 import NvidiaEarth2Adapter
    from ..ingestion.weathernext import WeatherNextAdapter

    cfg = load_config()
    results = []

    wn = WeatherNextAdapter(config=cfg)
    wn_avail = wn.check_availability()
    results.append(
        {
            "name": "Google WeatherNext 3",
            "access": "Google Cloud allowlist (form)",
            "status": (
                "available (credentials present)"
                if wn_avail.get("available")
                else "requires allowlist approval"
            ),
            "resolution": "0.05°/0.1°/0.25°, hourly, 64 members, 15-day",
        }
    )

    nv = NvidiaEarth2Adapter(config=cfg)
    nv_avail = nv.check_availability()
    results.append(
        {
            "name": "NVIDIA Earth-2 (FourCastNet/StormCast)",
            "access": "open weights (self-host) / NVIDIA NIM key (paid)",
            "status": (
                "available (API key present)"
                if nv_avail.get("available")
                else "no keyless free hosted API"
            ),
            "resolution": "0.25° (FourCastNet) / 3-km regional (StormCast)",
        }
    )
    return results
