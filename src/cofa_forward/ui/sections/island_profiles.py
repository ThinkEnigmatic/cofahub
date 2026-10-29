"""Island Profiles — reusable country/state/island/atoll profile page."""

from __future__ import annotations

import streamlit as st

from ...cyclones.proximity import closest_approach
from ...impacts.event_catalog import load_catalog
from ...visualization.charts import rainfall_timeseries
from ..components.common import page_header, render_plotly, sample_banner
from ..state import (
    get_all_indicators,
    get_ghcnd_trends,
    get_location_climatology,
    get_sample_forecast,
    get_sample_impacts,
    get_sample_tracks,
    get_worldpop_population,
    get_zonal_population,
    load_registry,
)


def render() -> None:
    registry = load_registry()
    page_header("Island Profiles", "Per-entity geography, conditions, and climatology")

    sample_banner()

    names = {e.geo_id: e.name for e in registry.all()}
    geo_id = st.selectbox(
        "Entity", options=list(names.keys()), format_func=lambda g: f"{names[g]} ({g})"
    )
    e = registry.by_id(geo_id)
    hierarchy = registry.hierarchy_path(geo_id)

    st.subheader(e.name)
    st.caption(" → ".join(f"{h.name} ({h.entity_type})" for h in hierarchy))

    # ---- Geography / identity ---- #
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Geographic identity**")
        st.write(f"- geo_id: `{e.geo_id}`")
        st.write(f"- Country code: `{e.country_code}`")
        st.write(f"- Entity type: {e.entity_type}")
        st.write(f"- Coordinates: {e.latitude:.4f}, {e.longitude:.4f} (point, seed)")
        if e.area_km2:
            st.write(f"- Area: ~{e.area_km2} km² (approximate)")
        if e.population:
            st.write(f"- Population: ~{e.population:,} ({e.population_year}, approximate)")
        st.write(f"- Data coverage: {e.data_coverage or 'n/a'}")
        if e.notes:
            st.caption(e.notes)
    with right:
        st.markdown("**Population exposure (WorldPop)**")
        if e.population:
            # Prefer the accurate zonal (boundary) sum for all three countries.
            zonal = get_zonal_population(e.geo_id, e.name, e.country_code)
            if zonal.get("ok") and zonal.get("population") == zonal.get("population"):
                st.metric(
                    f"WorldPop within {e.name} boundary",
                    f"{zonal['population']:,.0f}",
                )
                st.caption(
                    "UN-adjusted 2020 (~1 km grid) summed within the administrative "
                    "boundary (HDX COD-AB for FSM/RMI; geoBoundaries for Palau). "
                    "Differs from the census total above (UN-adjusted, 1-km resolution)."
                )
            else:
                wp = get_worldpop_population(e.geo_id, e.country_code, e.latitude, e.longitude)
                if wp.get("ok") and wp.get("population") == wp.get("population"):
                    st.metric(
                        f"WorldPop population within {wp['radius_km']:.0f} km",
                        f"{wp['population']:,.0f}",
                    )
                    st.caption(
                        "UN-adjusted 2020 (~1 km grid) near the reference point. "
                        "No matching administrative boundary; this point+radius "
                        "estimate undercounts long/irregular atolls."
                    )
                else:
                    st.caption("WorldPop population unavailable (offline or no land pixels).")
        st.markdown("**Geometry source**")
        st.info(
            "Point location from the seed registry. Administrative polygons are "
            "used for population: HDX COD-AB (FSM/RMI, CC BY-IGO) and geoBoundaries "
            "(Palau, ODbL/OSM). Coarse-grid model values are regional estimates."
        )

    st.divider()

    # ---- Current conditions + forecast (sample) ---- #
    st.subheader("Current conditions & short-range forecast (sample)")
    fc = get_sample_forecast(geo_id, e.latitude, e.longitude)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperature", f"{fc['temperature_2m_c'].iloc[0]:.1f} °C")
    c2.metric("Wind", f"{fc['wind_speed_10m_ms'].iloc[0]:.1f} m/s")
    c3.metric("Humidity", f"{fc['relative_humidity_2m_pct'].iloc[0]:.0f} %")
    c4.metric("Pressure", f"{fc['surface_pressure_hpa'].iloc[0]:.0f} hPa")

    st.divider()

    # ---- Rainfall + climatology ---- #
    st.subheader("Rainfall time series & climatology")
    clim = get_location_climatology(geo_id)
    st.caption("Sample monthly series (synthetic).")
    render_plotly(
        rainfall_timeseries(
            clim["monthly"], clim["climatology"], title=f"Monthly rainfall — {e.name}"
        ),
        key=f"profile_rain_{geo_id}",
    )

    # Drought indicators
    indicators = {i["geo_id"]: i for i in get_all_indicators()}
    ind = indicators.get(geo_id)
    if ind:
        st.subheader("Drought indicators")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Percentile", f"{ind['percentile']:.0%}" if ind.get("percentile") is not None else "n/a"
        )
        c2.metric(
            "Anomaly",
            f"{ind['anomaly_pct']:+.0f}%" if ind.get("anomaly_pct") is not None else "n/a",
        )
        c3.metric("Baseline valid", str(ind.get("baseline_valid")))
        c4.metric("Category", ind.get("percentile_category", "no data"))
        roll = ind.get("rolling", {})
        if roll:
            st.caption(
                "Rolling totals (mm): "
                + ", ".join(
                    f"{k.replace('rain_', '').replace('m_mm', 'm')}={v:.0f}"
                    for k, v in roll.items()
                    if v is not None
                )
            )

    st.divider()

    # ---- Climate trends (GHCNd station record) ---- #
    st.subheader("Climate trends (station record)")
    with st.spinner("Computing trends from the station record…"):
        trends = get_ghcnd_trends(geo_id)
    if trends.get("ok"):
        st.caption(
            f"Station {trends['station_id']} (WMO {trends['wmo']}), "
            f"{trends['rainfall']['start']}–{trends['rainfall']['end']}."
        )
        for key, label in (("rainfall", "Annual rainfall"), ("tmax", "Annual mean Tmax")):
            t = trends[key]
            if t["slope_per_decade"] == t["slope_per_decade"]:
                arrow = (
                    "↗"
                    if t["verdict"] == "increasing"
                    else ("↘" if t["verdict"] == "decreasing" else "→")
                )
                st.write(
                    f"{arrow} **{label}**: {t['slope_per_decade']:+.1f} {t['unit']}/decade "
                    f"(Mann-Kendall {t['mann_kendall']['trend']}, "
                    f"p={t['mann_kendall']['p_value']:.3f})."
                )
            else:
                st.write(f"**{label}**: insufficient record for a trend.")
        st.caption(
            "Trend = ordinary least-squares slope per decade over the station record; "
            "significance by Mann-Kendall. Gauge data only — not adjusted for instrument "
            "or station moves."
        )
    else:
        st.caption(f"Climate trends unavailable: {trends.get('error')}.")

    st.divider()

    # ---- Cyclone exposure ---- #
    st.subheader("Tropical cyclone exposure (sample)")
    tracks = get_sample_tracks()
    for sid, grp in tracks.groupby("storm_id"):
        ca = closest_approach(e.latitude, e.longitude, grp)
        st.write(f"**{sid}** — closest approach {ca['distance_km']:.0f} km ({ca['time']})")
    st.caption("Sample tracks; real exposure analysis requires IBTrACS (Phase 5).")

    # ---- Impacts ---- #
    st.subheader("Documented impacts (sample)")
    imp = load_catalog(get_sample_impacts()).by_geo_id(geo_id)
    if len(imp):
        st.dataframe(imp, width="stretch", hide_index=True)
    else:
        st.write("No impacts recorded for this entity in the sample catalog.")

    st.divider()
    st.caption(
        "All values are synthetic sample data or seed registry fields. Source links and "
        "last-updated timestamps are shown once real providers are fetched."
    )
