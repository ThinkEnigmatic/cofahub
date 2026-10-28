"""COFA FORWARD — Streamlit application entry point.

Run with:  uv run streamlit run src/cofa_forward/ui/app.py
"""

from __future__ import annotations

import hmac
import os
import sys
from pathlib import Path

# Ensure the package is importable when run directly (robust to install mode/CWD).
_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st  # noqa: E402

from cofa_forward import __version__  # noqa: E402
from cofa_forward.logging_config import setup_logging  # noqa: E402
from cofa_forward.ui.sections import (  # noqa: E402
    data_health,
    drought_water,
    enso_climate,
    historical_impacts,
    island_profiles,
    overview,
    reports,
    tropical_cyclones,
    water_need,
    weather,
)

setup_logging()

st.set_page_config(
    page_title="COFA FORWARD",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Optional access gate (single shared password) ------------------------- #
# Active only when COFA_REQUIRE_AUTH=1 (set by the deployed launchd service).
# The password is read from ~/.config/cofa-forward/app_password (0600). This is a
# stopgap until Cloudflare Access is applied; it is NOT multi-user auth.
_PW_FILE = Path.home() / ".config" / "cofa-forward" / "app_password"


def _require_password() -> str | None:
    if os.environ.get("COFA_REQUIRE_AUTH") != "1":
        return None
    if _PW_FILE.exists():
        return _PW_FILE.read_text(encoding="utf-8").strip()
    return None


_REQUIRED_PW = _require_password()
if _REQUIRED_PW:
    if "cofa_authed" not in st.session_state:
        st.session_state["cofa_authed"] = False
    if not st.session_state["cofa_authed"]:
        st.title("🌏 COFA FORWARD")
        st.caption("Weather Operations & Anticipatory Climate Intelligence")
        pw = st.text_input("Password", type="password", key="cofa_pw")
        if st.button("Sign in", type="primary"):
            if hmac.compare_digest(pw, _REQUIRED_PW):
                st.session_state["cofa_authed"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.stop()

PAGES = {
    "Overview": overview.render,
    "Weather Operations": weather.render,
    "ENSO & Climate": enso_climate.render,
    "Drought & Water": drought_water.render,
    "Water Need Forecast": water_need.render,
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
