"""Overview landing page — regional situation picture."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ...climate.enso_state import enso_state_from_config
from ...intelligence.synthesis import build_statements
from ...visualization.leaflet_maps import region_map
from ..components.common import evidence_badge, page_header, render_folium, sample_banner
from ..state import (
    get_all_indicators,
    get_boundaries,
    get_live_enso,
    load_config,
    load_registry,
)


def render() -> None:
    cfg = load_config()
    registry = load_registry()
    page_header(cfg.name, cfg.subtitle)

    sample_banner()

    indicators = get_all_indicators()
    enso = enso_state_from_config(cfg.enso_current)
    stmts = build_statements(indicators, cfg.enso_current)

    # ---- Row 1: map + situation ---- #
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader("Regional situation map")
        render_folium(
            region_map(registry, center=cfg.map_center, boundaries=get_boundaries()),
            key="overview_map",
        )

    with right:
        st.subheader("ENSO status")
        live_enso = get_live_enso()
        if live_enso.get("ok"):
            latest = live_enso["latest"]
            st.success(
                f"ONI {latest['season']} {latest['year']}: {latest['anom']:+.2f} °C "
                f"(derived: {live_enso['phase']})",
                icon="🟢",
            )
            st.caption(f"NOAA CPC ONI, retrieved {live_enso['retrieved_at']}.")
        elif enso.is_available:
            st.success(f"{enso.phase} (as of {enso.as_of})", icon="🟢")
            st.caption(f"Source: {enso.source}")
        else:
            st.info("Unavailable — live ONI fetch failed and no ENSO source configured", icon="ℹ️")
            st.caption("No phase is assumed.")

        st.subheader("Tropical cyclone activity")
        st.info("No confirmed active storms in available data", icon="🌀")
        st.caption("JMA active-storm integration is available on Tropical Cyclones / via scripts.")

        st.subheader("Active weather alerts")
        st.info("No official alerts are integrated", icon="🚨")
        st.caption("Official watches/warnings are Phase 5. None are fabricated.")

    st.divider()

    # ---- Row 2: evidence-linked summary ---- #
    st.subheader("Intelligence summary (evidence-linked)")
    for s in stmts:
        st.markdown(f"{evidence_badge(s['evidence_type'])} — {s['text']}")

    st.caption(
        "Tags distinguish observed conditions from forecasts, official outlooks, "
        "historical analogs, and analyst interpretation."
    )

    st.divider()

    # ---- Row 3: flagged locations + freshness ---- #
    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        st.subheader("Locations flagged for attention")
        flagged = [
            i for i in indicators if i.get("percentile") is not None and i["percentile"] < 0.2
        ]
        if flagged:
            rows = [
                {
                    "Location": i["name"],
                    "Rainfall percentile": f"{i['percentile']:.0%}",
                    "Category": i["percentile_category"],
                }
                for i in sorted(flagged, key=lambda x: x["percentile"])
            ]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.write("No locations currently below the 20th-percentile watch level.")

    with col_b:
        st.subheader("Data freshness")
        st.write("**Most recent data refresh:** sample (synthetic) data — not a live refresh.")
        st.write("**Source failures / stale datasets:** none recorded (no live sources fetched).")
        st.caption("Fetch a live forecast on the Weather Operations page to see real provenance.")

    st.divider()
    st.caption(
        "Baseline for percentile indicators: 1991–2020 (synthetic sample series). "
        "Percentiles are empirical, computed over validated monthly totals; missing "
        "months are never treated as zero rainfall."
    )
