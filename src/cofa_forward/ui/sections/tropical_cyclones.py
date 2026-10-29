"""Tropical Cyclones — historical tracks, proximity, and climatology."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ...cyclones.climatology import seasonal_summary
from ...cyclones.exposure import exposure_summary
from ...cyclones.proximity import closest_approach
from ...hazards.compound import compound_flags
from ...visualization.leaflet_maps import track_map
from ..components.common import page_header, render_folium, sample_banner
from ..state import (
    get_active_storms,
    get_drought_monitor,
    get_himawari_image,
    get_jtwc_warnings,
    get_marine,
    get_nws_guam_advisory,
    get_real_tracks,
    get_sample_tracks,
    get_sea_level,
    get_sst_bleaching,
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

    # ---- JTWC warnings (1-min wind + quadrant radii) ---- #
    st.subheader("JTWC warnings (1-minute wind)")
    if st.button("Check JTWC warnings"):
        get_jtwc_warnings.clear()
    jtwc = get_jtwc_warnings()
    if jtwc.get("n_active"):
        for w in jtwc["storms"]:
            pos = w.get("position") or {}
            st.markdown(
                f"**{w['name']}** ({w['storm_type']}, warning {w['warning_number']}) — "
                f"**{w.get('wind_kt')} kt** (1-min), gusts {w.get('gusts_kt')} kt, "
                f"at {pos.get('lat', 0):.1f}°N {pos.get('lon', 0):.1f}°E, "
                f"moving {w.get('movement_dir_deg')}° @ {w.get('movement_speed_kt')} kt · "
                f"{len(w.get('forecasts', []))} forecast points."
            )
        st.caption(
            "JTWC 1-minute sustained wind differs from JMA's 10-minute mean. "
            "Quadrant wind radii (34/50/64 kt) are parsed and available."
        )
    else:
        st.info("No active JTWC warnings at this time (or unavailable offline).", icon="🌀")

    st.divider()

    # ---- NWS Guam advisories (FAS island-specific) ---- #
    st.subheader("NWS Guam advisories (island-specific)")
    if st.button("Check NWS Guam advisory"):
        get_nws_guam_advisory.clear()
    nwsg = get_nws_guam_advisory()
    if nwsg.get("ok"):
        if nwsg.get("headline"):
            st.markdown(f"**{nwsg['headline']}**")
        if nwsg.get("watches_warnings"):
            st.markdown("Watches / warnings in effect:")
            for w in nwsg["watches_warnings"]:
                st.markdown(f"- {w}")
        else:
            st.caption("No watches/warnings currently in effect.")
        st.caption(f"Source: NWS Guam (Tiyan) {nwsg.get('retrieved_at')}.")
    else:
        st.info("NWS Guam advisory unavailable (offline?).", icon="🌀")

    st.divider()

    # ---- Satellite imagery (Himawari-9) ---- #
    st.subheader("Satellite view — Himawari-9")
    hima = get_himawari_image()
    if hima.get("ok"):
        st.image(
            hima.get("image_url") or hima.get("image_path"),
            caption=(
                f"Himawari-9 full disk (composite), {hima['time']} UTC. "
                "The Freely Associated States are in the western-Pacific portion "
                "(upper-left of the disk)." + (" (offline snapshot)" if hima.get("offline") else "")
            ),
            width=700,
        )
        st.caption(
            "10-minute cadence; JMA/NICT Himawari real-time web. No storm tracks "
            "are overlaid here yet."
        )
    else:
        st.info("Satellite imagery unavailable (offline?).", icon="🛰️")

    st.divider()

    # ---- Coastal & marine conditions (waves, SST, sea level, compound risk) ---- #
    st.subheader("Coastal & marine conditions")
    names = {e.geo_id: e.name for e in registry.all()}
    c_geo = st.selectbox(
        "Location",
        options=list(names.keys()),
        format_func=lambda g: f"{names[g]} ({g})",
        key="coastal_loc",
    )
    c_entity = registry.by_id(c_geo)
    with st.spinner("Fetching marine + sea-level data…"):
        marine = get_marine(c_entity.latitude, c_entity.longitude)
        sea = get_sea_level(c_geo)
        monitor = get_drought_monitor(c_geo, c_entity.latitude, c_entity.longitude)
    if marine.get("ok"):
        cur = marine["current"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wave height", f"{cur['wave_height_m']:.1f} m")
        m2.metric("Wave period", f"{cur['wave_period_s']:.0f} s")
        m3.metric("Wave direction", f"{cur['wave_direction_deg']:.0f}°")
        m4.metric("Sea-surface temp", f"{cur['sst_c']:.1f} °C")
        mx = marine["daily"]["wave_height_max_m"].max()
        st.caption(
            f"Significant wave height; daily max over the next {len(marine['daily'])} days is "
            f"{mx:.1f} m. Open-Meteo marine (~11 km grid)."
        )
    else:
        st.info(f"Marine data unavailable: {marine.get('error')}", icon="🌊")

    if sea.get("ok"):
        st.caption(
            f"Tide gauge ({sea['station']}): {sea['latest_mm']:.0f} mm as of {sea['last_date']}."
        )

    # Coral bleaching watch (simplified Degree Heating Weeks).
    with st.spinner("Computing bleaching watch…"):
        bleach = get_sst_bleaching(c_entity.latitude, c_entity.longitude)
    if bleach.get("ok") and bleach.get("dhw_c_weeks") is not None:
        st.caption(
            f"🌡️ Bleaching watch: DHW {bleach['dhw_c_weeks']:.1f} °C-weeks — "
            f"{bleach['alert']} (12-week SST {bleach['sst_mean12w_c']:.1f} °C). "
            "Simplified NOAA Coral Reef Watch method (fixed western-Pacific MMM); "
            "not the official per-pixel DHW product."
        )

    # Compound risk (drought × waves × sea level × cyclones).
    if marine.get("ok") and monitor.get("ok") and monitor.get("status"):
        m = monitor["status"]
        flags = compound_flags(
            drought_quintile=m.get("quintile"),
            peac_index=m.get("peac_index"),
            wave_height_m=marine["current"].get("wave_height_m"),
        )
        if flags:
            st.warning("**Compound-hazard flags**", icon="⚠️")
            for f in flags:
                st.markdown(f"- {f}")
        else:
            st.caption("No compound drought/marine hazard flags active.")

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

    render_folium(track_map(tracks, center=cfg.map_center, title="Storm tracks"), key="tc_map")

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
