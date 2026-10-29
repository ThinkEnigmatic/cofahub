"""ENSO & Climate — anticipatory intelligence workspace."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ...climate.enso_state import enso_state_from_config
from ...visualization.leaflet_maps import metric_map
from ..components.common import page_header, render_folium, render_plotly, sample_banner
from ..state import (
    get_all_indicators,
    get_enso_analogs,
    get_enso_discussion,
    get_live_enso,
    get_nmme_multimodel,
    get_peac_outlook,
    get_sea_level,
    load_config,
    load_registry,
)


def render() -> None:
    cfg = load_config()
    registry = load_registry()
    page_header("ENSO & Climate", "ENSO state, outlooks, and historical episodes")

    enso = enso_state_from_config(cfg.enso_current)
    thresholds = cfg.oni_thresholds

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("Current ENSO status")
        if st.button("Refresh live ENSO (CPC ONI)", use_container_width=True):
            get_live_enso.clear()
        live = get_live_enso()
        if live.get("ok"):
            latest = live["latest"]
            st.success(
                f"ONI {latest['season']} {latest['year']}: **{latest['anom']:+.2f} °C** "
                f"(derived phase: **{live['phase']}**)",
                icon="🟢",
            )
            st.caption(
                f"Source: NOAA CPC ONI ({latest['date']}); retrieved {live['retrieved_at']}. "
                f"Phase derived from the ≥5-consecutive-season criterion — the official "
                f"status statement is the CPC Diagnostic Discussion."
            )
        elif enso.is_available:
            st.success(f"{enso.phase} (as of {enso.as_of})", icon="🟢")
            st.caption(f"Source: {enso.source}")
        else:
            st.info(
                f"Live ONI fetch failed: {live.get('error', 'no data')}. "
                "No authoritative ENSO source configured.",
                icon="ℹ️",
            )
            st.caption("CPC ONI is the primary source; the fetch above should succeed when online.")
        st.markdown(
            f"**ONI thresholds (NOAA CPC):** El Niño ≥ {thresholds.get('el_nino')} °C, "
            f"La Niña ≤ {thresholds.get('la_nina')} °C (3-month running mean of Niño-3.4 "
            f"anomaly, {thresholds.get('base_period')} baseline)."
        )

    with col2:
        st.subheader("Official status statement")
        if st.button("Refresh (CPC Diagnostic Discussion)", use_container_width=True):
            get_enso_discussion.clear()
        disc = get_enso_discussion()
        if disc.get("ok"):
            st.markdown(f"**ENSO Alert System Status: {disc['alert_status']}**")
            st.caption(f"Issued {disc.get('issue_date')} · retrieved {disc.get('retrieved_at')}.")
            if disc.get("synopsis"):
                st.write(disc["synopsis"])
        else:
            st.info("Diagnostic Discussion unavailable (offline?).", icon="ℹ️")
        st.caption("Authoritative CPC status statement — not a derived phase.")

    st.divider()

    # ---- Seasonal outlook (NMME multi-model) ---- #
    st.subheader("Seasonal outlook — NMME multi-model precipitation")
    names = {e.geo_id: e.name for e in registry.all()}
    s_geo = st.selectbox(
        "Location",
        options=list(names.keys()),
        format_func=lambda g: f"{names[g]} ({g})",
        key="nmme_loc",
    )
    s_entity = registry.by_id(s_geo)
    if st.button("Load NMME seasonal forecast", key="nmme_load"):
        get_nmme_multimodel.clear()
    with st.spinner("Downloading NMME model forecasts (~18 MB, cached)…"):
        mm = get_nmme_multimodel(s_entity.latitude, s_entity.longitude)
    if mm.get("ok"):
        st.success(
            f"NMME {mm['cycle']} — {mm['n_models']} models, ensemble-mean precipitation.",
            icon="🟢",
        )
        fig = go.Figure()
        for col in mm["models"].columns:
            fig.add_trace(
                go.Scatter(
                    x=mm["models"].index,
                    y=mm["models"][col],
                    mode="lines+markers",
                    name=col,
                    line=dict(width=1, dash="dot"),
                    opacity=0.7,
                )
            )
        mean = mm["ensemble_mean"]
        std = mm["ensemble_std"]
        fig.add_trace(
            go.Scatter(
                x=mean.index,
                y=mean.values,
                mode="lines+markers",
                name="Ensemble mean",
                line=dict(color="#dc2626", width=3),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=mean.index.tolist() + mean.index.tolist()[::-1],
                y=(mean + std).tolist() + (mean - std).tolist()[::-1],
                fill="toself",
                fillcolor="rgba(220,38,38,0.15)",
                line=dict(width=0),
                name="±1σ model spread",
                showlegend=True,
            )
        )
        fig.update_layout(
            title=f"NMME seasonal precipitation — {s_entity.name} (mm/day)",
            template="plotly_white",
            height=360,
            margin=dict(l=10, r=10, t=40, b=10),
            yaxis_title="mm/day",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        render_plotly(fig, key="nmme_chart")
        st.caption(
            "1° (~110 km) grid, ensemble mean across the NMME models. Model spread "
            "reflects inter-model disagreement; coarse for individual atolls. "
            "This is a model forecast, not an official outlook."
        )
    else:
        st.info(f"NMME forecast unavailable: {mm.get('error')}", icon="ℹ️")

    st.divider()

    # ---- PEAC seasonal rainfall outlook (official, tercile) ---- #
    st.subheader("PEAC seasonal rainfall outlook (official consensus)")
    if st.button("Refresh (PEAC)", key="peac_refresh"):
        get_peac_outlook.clear()
    peac = get_peac_outlook()
    if peac.get("ok"):
        if peac.get("is_stale"):
            st.warning(
                f"⚠️ This outlook is for **{peac.get('season', '?')}** and was last updated "
                f"**{peac.get('last_updated', 'unknown')}** "
                f"(~{peac.get('stale_days', '?')} days ago). PEAC's seasonal rainfall outlook "
                "has not been updated recently — treat it as historical context, not a current "
                "forecast.",
                icon="🕰️",
            )
        else:
            st.success(
                f"PEAC outlook for {peac.get('season', '?')} (updated {peac.get('last_updated')})."
            )
        fas = [s for s in peac["stations"] if s["geo_id"]]
        rows = [
            {
                "Station": s["name"],
                "Region": s["region"],
                "Final outlook": s["final_outlook"],
                "Below / Near / Above": s["probabilities"],
            }
            for s in fas
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption(
            "Tercile probabilities (below-average : near-average : above-average rainfall), "
            "an experimental consensus of 7 seasonal models. Tercile cut-offs use the CPC "
            "1991–2020 climatology. Source: weather.gov/peac."
        )
    else:
        st.info(f"PEAC outlook unavailable: {peac.get('error')}", icon="ℹ️")

    st.divider()

    # ---- Sea level (UHSLC tide gauges) ---- #
    st.subheader("Sea level — tide gauges (UHSLC)")
    sea_geo = st.selectbox(
        "Tide-gauge location",
        options=list(names.keys()),
        format_func=lambda g: f"{names[g]} ({g})",
        key="sealevel_loc",
    )
    sea = get_sea_level(sea_geo)
    if sea.get("ok"):
        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Latest daily sea level", f"{sea['latest_mm']:.0f} mm", help="Above the station datum."
        )
        c2.metric("30-day mean", f"{sea['mean30_mm']:.0f} mm")
        c3.metric("As of", sea["last_date"])
        st.caption(
            f"Station {sea['station']} — UHSLC Fast Delivery (hourly → daily mean). "
            "El Niño raises western-Pacific sea level (the RMI/FSM king-tide flooding); "
            "the PEAC seasonal sea-level outlook was discontinued January 2020."
        )
    else:
        st.info(f"No tide gauge for {names[sea_geo]} ({sea.get('error')}).", icon="🌊")

    st.divider()

    # ---- ENSO analog selection ---- #
    st.subheader("Historical ENSO analogs")
    with st.spinner("Ranking historical episodes…"):
        analog = get_enso_analogs()
    if analog.get("ok"):
        st.caption(
            f"Current ONI **{analog['current_oni']:+.2f} °C** (phase {analog['phase']}). "
            "Nearest historical episodes by peak-ONI proximity."
        )
        for a in analog["analogs"]:
            st.write(
                f"- **{a['episode_id']}** ({a['intensity'] or 'n/a'}): peak ONI "
                f"{a['peak_oni']:+.1f} °C, similarity {a['similarity']:.2f} "
                f"({a['start']} → {a['end']})."
            )
        st.caption(
            "A historical analog is contextual evidence, not a forecast — see the "
            "El Niño Comparison page for what each episode did in the FAS."
        )
    else:
        st.info(f"Analog selection unavailable: {analog.get('error')}", icon="🔬")

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
    render_folium(
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
