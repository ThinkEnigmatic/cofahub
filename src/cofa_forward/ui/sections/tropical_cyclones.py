"""Tropical Cyclones — historical tracks, proximity, and climatology."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ...cyclones.climatology import seasonal_summary
from ...cyclones.exposure import exposure_summary
from ...cyclones.proximity import closest_approach
from ...visualization.charts import track_map
from ..components.common import page_header, render_plotly, sample_banner
from ..state import (
    get_active_storms,
    get_real_tracks,
    get_sample_tracks,
    get_storm_details,
    load_config,
    load_registry,
)


def render() -> None:
    cfg = load_config()
    registry = load_registry()
    page_header("Tropical Cyclones", "Historical tracks, proximity, and climatology")

    tc_cfg = cfg.cyclone

    # ---- Active storms (JMA RSMC Tokyo) ---- #
    st.subheader("Active storms (JMA RSMC Tokyo)")
    if st.button("Check active storms (JMA)"):
        get_active_storms.clear()
        get_storm_details.clear()
    active = get_active_storms()
    if active.get("ok"):
        if active["n_active"] == 0:
            st.info(
                "No active tropical cyclones in the western North Pacific at "
                f"{active['retrieved_at']}. No storms are invented.",
                icon="🌀",
            )
        else:
            for s in active["storms"]:
                d = get_storm_details(s["tc_id"])
                if d.get("ok"):
                    a = d["analysis"]
                    pos = a.get("position") or {}
                    name = d["meta"].get("name_en") or s["tc_id"]
                    st.markdown(
                        f"**{name}** (JMA Typhoon {s['typhoon_number']}, {s['category']}) — "
                        f"{a.get('wind_sustained_kt')} kt sustained, {a.get('pressure_hpa')} hPa, "
                        f"at {pos.get('lat', 0):.1f}°N {pos.get('lon', 0):.1f}°E · "
                        f"{len(d['forecasts'])} forecast points. "
                        f"_(analysis {d['meta'].get('issue_utc')})_"
                    )
        st.caption(f"Source: JMA RSMC Tokyo ({active['retrieved_at']}).")
    else:
        st.info("Active-storm check unavailable (offline?). No storms are invented.", icon="🌀")

    st.divider()

    # ---- Historical tracks (sample or real IBTrACS) ---- #
    use_real = st.toggle(
        "Real historical tracks (IBTrACS)",
        value=False,
        help="Download the ~114 MB WP-basin CSV and filter to the FAS region (cached 24h).",
    )
    if use_real:
        with st.spinner("Downloading IBTrACS WP basin…"):
            real = get_real_tracks()
        if real.get("ok"):
            tracks = real["tracks"]
            st.success(
                f"IBTrACS: {real['n_storms']} storms, {real['n_points']} points in the FAS region "
                f"(retrieved {real['retrieved_at']}).",
                icon="🟢",
            )
            st.caption(
                "Wind/pressure are the WMO (responsible-agency) values — "
                "JMA 10-min mean for this basin."
            )
        else:
            st.error(f"IBTrACS fetch failed ({real.get('error')}); using sample tracks.")
            sample_banner()
            tracks = get_sample_tracks()
    else:
        sample_banner()
        tracks = get_sample_tracks()

    render_plotly(track_map(tracks, center=cfg.map_center, title="Storm tracks"), key="tc_map")

    st.divider()

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Seasonal climatology")
        summ = seasonal_summary(tracks)
        st.write(f"Storms: **{summ['n_storms']}** · Track points: **{summ['n_points']}**")
        by_year = summ["by_year"].rename("storms")
        st.bar_chart(by_year)

    with right:
        st.subheader("Closest approach to a location")
        names = {e.geo_id: e.name for e in registry.all()}
        geo_id = st.selectbox(
            "Location", options=list(names.keys()), format_func=lambda g: f"{names[g]} ({g})"
        )
        entity = registry.by_id(geo_id)
        approaches = []
        for sid, grp in tracks.groupby("storm_id"):
            ca = closest_approach(entity.latitude, entity.longitude, grp)
            approaches.append((ca["distance_km"], sid, ca["time"]))
        approaches.sort(key=lambda x: x[0])
        for dist_km, sid, t in approaches[:10]:
            st.write(f"**{sid}** — closest approach {dist_km:.0f} km ({t})")

    st.divider()

    st.subheader("Exposure")
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
        "limitations) is implemented and unit-tested. Real IBTrACS tracks (toggle above) "
        "provide the historical sample; phase labels require joining to the ENSO episode catalog.",
        icon="🔬",
    )
    st.caption(
        "No causal claim is made from correlation, and no hard-coded multiplier is turned "
        "into an operational risk probability."
    )
