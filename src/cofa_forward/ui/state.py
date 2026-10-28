"""Cached app state for the Streamlit UI.

All expensive loads (config, geography, synthetic sample data, computed
indicators) are cached so reruns are fast and the app never re-downloads or
re-synthesizes data on every interaction.
"""

from __future__ import annotations

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
