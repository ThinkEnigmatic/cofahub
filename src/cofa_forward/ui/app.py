"""COFA FORWARD — Streamlit application entry point.

Run with:  uv run streamlit run src/cofa_forward/ui/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the package is importable when run directly (robust to install mode/CWD).
_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st  # noqa: E402

from cofa_forward import __version__  # noqa: E402
from cofa_forward.logging_config import setup_logging  # noqa: E402
from cofa_forward.ui.pages import (  # noqa: E402
    data_health,
    drought_water,
    enso_climate,
    historical_impacts,
    island_profiles,
    overview,
    reports,
    tropical_cyclones,
    weather,
)

setup_logging()

st.set_page_config(
    page_title="COFA FORWARD",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "Overview": overview.render,
    "Weather Operations": weather.render,
    "ENSO & Climate": enso_climate.render,
    "Drought & Water": drought_water.render,
    "Tropical Cyclones": tropical_cyclones.render,
    "Historical Impacts": historical_impacts.render,
    "Island Profiles": island_profiles.render,
    "Reports": reports.render,
    "Data Sources & System Health": data_health.render,
}

with st.sidebar:
    st.title("🌏 COFA FORWARD")
    st.caption(f"v{__version__} — {'Weather Ops & Anticipatory Climate Intelligence'}")
    st.session_state["units"] = st.radio(
        "Units",
        ["metric", "imperial"],
        index=0,
        help="Presentation preference; scientific calculations are metric.",
    )
    st.divider()
    choice = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")

PAGES[choice]()
