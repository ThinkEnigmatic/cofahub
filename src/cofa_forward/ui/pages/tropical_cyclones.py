"""Tropical Cyclones — historical tracks, proximity, climatology."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ...cyclones.climatology import seasonal_summary
from ...cyclones.exposure import exposure_summary
from ...cyclones.proximity import closest_approach
from ...visualization.charts import track_map
from ..components.common import page_header, render_plotly, sample_banner
from ..state import get_sample_tracks, load_config, load_registry


def render() -> None:
    cfg = load_config()
    registry = load_registry()
    page_header("Tropical Cyclones", "Historical tracks, proximity, and climatology")

    sample_banner()
    tracks = get_sample_tracks()
    tc_cfg = cfg.cyclone

    st.warning(
        "No official active-storm or forecast-track source is wired in. When no confirmed "
        "storms are available, the platform states the actual data coverage and retrieval "
        "time rather than assuming zero risk — and never invents storms.",
        icon="🌀",
    )

    render_plotly(
        track_map(tracks, center=cfg.map_center, title="Sample storm tracks"), key="tc_map"
    )

    st.divider()

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Seasonal climatology (sample)")
        summ = seasonal_summary(tracks)
        st.write(f"Storms: **{summ['n_storms']}** · Track points: **{summ['n_points']}**")
        by_year = summ["by_year"].rename("storms")
        st.bar_chart(by_year)
        st.caption("Sample synthetic tracks — not real storms.")

    with right:
        st.subheader("Closest approach to a location")
        names = {e.geo_id: e.name for e in registry.all()}
        geo_id = st.selectbox(
            "Location", options=list(names.keys()), format_func=lambda g: f"{names[g]} ({g})"
        )
        entity = registry.by_id(geo_id)
        for sid, grp in tracks.groupby("storm_id"):
            ca = closest_approach(entity.latitude, entity.longitude, grp)
            st.write(f"**{sid}** — closest approach {ca['distance_km']:.0f} km at {ca['time']}")

    st.divider()

    st.subheader("Exposure (sample)")
    thresholds = tc_cfg.get("approach_thresholds_km", [100, 200, 300])
    summ_exp = exposure_summary(registry, tracks, thresholds)
    st.dataframe(pd.DataFrame(summ_exp), width="stretch", hide_index=True)
    st.caption(
        "Proximity exposure only — distance alone does not estimate wind impact, which "
        "requires storm size, intensity, and track uncertainty."
    )

    st.divider()

    st.subheader("ENSO-conditioned analysis")
    st.info(
        "ENSO-conditioned cyclone analysis (counts by phase, with sample sizes and "
        "limitations) is implemented and unit-tested. It requires a real historical track "
        "dataset (IBTrACS, Phase 5) to be meaningful; sample tracks are shown until then.",
        icon="🔬",
    )
    st.caption(
        "No causal claim is made from correlation, and no hard-coded multiplier is turned "
        "into an operational risk probability."
    )
