"""ENSO & Climate — anticipatory intelligence workspace."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ...climate.enso_state import enso_state_from_config
from ...visualization.maps import metric_map
from ..components.common import page_header, render_plotly, sample_banner
from ..state import get_all_indicators, load_config, load_registry


def render() -> None:
    cfg = load_config()
    registry = load_registry()
    page_header("ENSO & Climate", "ENSO state, outlooks, and historical episodes")

    enso = enso_state_from_config(cfg.enso_current)
    thresholds = cfg.oni_thresholds

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("Current ENSO status")
        if enso.is_available:
            st.success(f"{enso.phase} (as of {enso.as_of})", icon="🟢")
            st.caption(f"Source: {enso.source}")
        else:
            st.info("Unavailable — no authoritative ENSO source configured", icon="ℹ️")
            st.caption("CPC ONI ingestion is planned (Phase 3). No phase is assumed.")
        st.markdown(
            f"**ONI thresholds (NOAA CPC):** El Niño ≥ {thresholds.get('el_nino')} °C, "
            f"La Niña ≤ {thresholds.get('la_nina')} °C (3-month running mean of Niño-3.4 "
            f"anomaly, {thresholds.get('base_period')} baseline)."
        )
        st.caption("Official outlook timestamp: not available (no source wired in).")

    with col2:
        st.subheader("Seasonal outlook")
        st.info("No official seasonal outlook is integrated yet", icon="ℹ️")
        st.caption("Seasonal/subseasonal outlooks are planned. No outlook is fabricated.")

    st.divider()

    # ---- Historical episode catalog ---- #
    st.subheader("Historical ENSO episode catalog")
    episodes = cfg.enso_episodes()
    rows = [
        {
            "Episode": e.id,
            "Phase": e.phase or "—",
            "Start": e.start or "—",
            "Peak": e.peak or "—",
            "End": e.end or "—",
            "Intensity": e.intensity or "—",
            "Status": e.verification_status,
        }
        for e in episodes
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption(
        "Episodes are SEED periods with approximate ONI-based windows — NOT verified "
        "exact start/peak/end dates. Validate against NOAA CPC ONI before production use."
    )

    st.divider()

    # ---- Historical analog comparison ---- #
    st.subheader("Historical analog comparison")
    st.info(
        "Analogs are selected with an explainable numeric similarity over ENSO phase, "
        "intensity, and rainfall anomaly — not a language-model score. The analog engine "
        "is implemented and unit-tested; a live dataset to feed it arrives with the ERA5 "
        "climatology workflow (Phase 3).",
        icon="🔬",
    )
    phase = st.selectbox("Filter episodes by phase", ["all", "el_nino", "la_nina"])
    if phase != "all":
        sel = [e for e in episodes if e.phase == phase]
        st.write(f"{len(sel)} episode(s) in phase **{phase}**.")
    st.caption("A historical analog is contextual evidence, not a forecast of what happens next.")

    st.divider()

    # ---- Rainfall anomaly map ---- #
    st.subheader("Rainfall anomaly by location (sample)")
    sample_banner()
    indicators = get_all_indicators()
    anomaly_pct = {
        i["geo_id"]: i["anomaly_pct"] for i in indicators if i.get("anomaly_pct") is not None
    }
    render_plotly(
        metric_map(
            registry,
            anomaly_pct,
            center=cfg.map_center,
            title="Latest month rainfall anomaly (% of normal)",
            colorbar_title="% of normal",
            colorscale="RdYlBu",
        ),
        key="enso_anomaly_map",
    )
    st.caption(
        "Anomaly requires a valid baseline (≥15 years). % of normal = (obs − clim) / clim × 100. "
        "Synthetic sample series shown; real anomalies arrive with ERA5 climatology."
    )
