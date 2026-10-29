"""Weather Operations — interactive map + live forecast + analytical panel."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ...ingestion.weather import OpenMeteoForecastAdapter
from ...units import convert
from ...visualization.charts import forecast_chart
from ...visualization.leaflet_maps import region_map
from ..components.common import (
    live_badge,
    page_header,
    render_folium,
    render_plotly,
    sample_banner,
    source_caption,
)
from ..state import (
    get_ai_model_status,
    get_boundaries,
    get_model_comparison,
    get_sample_forecast,
    load_config,
    load_registry,
    make_cache,
    make_db,
    units_imperial,
)

_WMO = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    80: "Rain showers",
    81: "Rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ hail",
    99: "Thunderstorm w/ hail",
}

_CURRENT_FIELDS = [
    ("temperature_2m", "Temperature", "°C"),
    ("relative_humidity_2m", "Relative humidity", "%"),
    ("precipitation", "Precipitation", "mm"),
    ("wind_speed_10m", "Wind speed", "m/s"),
    ("wind_direction_10m", "Wind direction", "°"),
    ("surface_pressure", "Surface pressure", "hPa"),
    ("weather_code", "Conditions", None),
]


def _render_current(current: dict, imperial: bool) -> None:
    cols = st.columns(4)
    for i, (var, label, unit) in enumerate(_CURRENT_FIELDS):
        if var not in current:
            continue
        val = current[var]
        with cols[i % 4]:
            if var == "weather_code":
                st.metric(label, _WMO.get(int(val), f"code {val}"))
            elif var == "temperature_2m" and imperial:
                st.metric(label, f"{convert(val, '°C', True):.1f} °F")
            elif var == "wind_speed_10m" and imperial:
                st.metric(label, f"{convert(val, 'm/s', True):.1f} knots")
            elif isinstance(val, (int, float)):
                st.metric(label, f"{val:.1f} {unit}")


def render() -> None:
    cfg = load_config()
    registry = load_registry()
    page_header("Weather Operations", "Current conditions and short-range forecast")

    imperial = units_imperial()

    # ---- Location selector ---- #
    names = {e.geo_id: e.name for e in registry.all()}
    geo_id = st.selectbox(
        "Monitoring location",
        options=list(names.keys()),
        format_func=lambda g: f"{names[g]} ({g})",
    )
    entity = registry.by_id(geo_id)

    left, right = st.columns([3, 2], gap="large")

    with left:
        render_folium(
            region_map(
                registry, center=cfg.map_center, title="FAS region", boundaries=get_boundaries()
            ),
            key="wx_map",
        )

    with right:
        st.subheader("Forecast for " + entity.name)
        if st.button("Fetch live forecast (Open-Meteo)", type="primary", width="stretch"):
            with st.spinner("Fetching live forecast…"):
                adapter = OpenMeteoForecastAdapter(config=cfg, cache=make_cache(), db=make_db())
                result = adapter.get_forecast(entity.latitude, entity.longitude)
                st.session_state["live_forecast"] = result
                st.session_state["live_geo_id"] = geo_id

        live = st.session_state.get("live_forecast")
        if live and st.session_state.get("live_geo_id") == geo_id:
            if live.get("ok"):
                live_badge(from_cache=live.get("from_cache", False))
                _render_current(live.get("current", {}), imperial)
                source_caption(
                    units="°C, mm, m/s, hPa (metric)",
                    valid_time=live.get("current_time").strftime("%Y-%m-%d %H:%M UTC")
                    if live.get("current_time")
                    else "",
                    init_time=live.get("init_time"),
                    source=live.get("source"),
                    resolution="~11 km model grid",
                )
                if not live.get("hourly", pd.DataFrame()).empty:
                    render_plotly(
                        forecast_chart(live["hourly"], title="Hourly forecast (live)"),
                        key="wx_live_chart",
                    )
            else:
                st.error(f"Live fetch failed: {live.get('error')}")
        else:
            st.caption("Sample forecast shown below (clearly labeled).")

    # ---- Sample fallback (always available) ---- #
    st.divider()
    sample_banner()
    sample_fc = get_sample_forecast(geo_id, entity.latitude, entity.longitude)
    st.subheader("Sample forecast (synthetic)")
    _render_current(
        {
            "temperature_2m": sample_fc["temperature_2m_c"].iloc[0],
            "relative_humidity_2m": sample_fc["relative_humidity_2m_pct"].iloc[0],
            "precipitation": sample_fc["precipitation_mm"].iloc[0],
            "wind_speed_10m": sample_fc["wind_speed_10m_ms"].iloc[0],
            "wind_direction_10m": sample_fc["wind_direction_deg"].iloc[0],
            "surface_pressure": sample_fc["surface_pressure_hpa"].iloc[0],
            "weather_code": 61,
        },
        imperial,
    )
    fc_df = sample_fc.copy()
    fc_df = fc_df.rename(
        columns={
            "temperature_2m_c": "temperature_2m",
            "precipitation_mm": "precipitation",
            "wind_speed_10m_ms": "wind_speed_10m",
            "relative_humidity_2m_pct": "relative_humidity_2m",
            "surface_pressure_hpa": "surface_pressure",
        }
    ).set_index("time")
    render_plotly(forecast_chart(fc_df, title="Hourly forecast (sample)"), key="wx_sample_chart")

    st.divider()

    # ---- Model comparison (Open-Meteo multi-model) ---- #
    st.subheader("Model comparison")
    var = st.selectbox("Variable", ["temperature_2m", "precipitation"], key="wx_model_var")
    if st.button("Load multi-model comparison", key="wx_model_load"):
        get_model_comparison.clear()
    with st.spinner("Fetching multiple models…"):
        mc = get_model_comparison(entity.latitude, entity.longitude, variable=var)
    if mc.get("ok"):
        st.success(
            f"{mc['n_models']} models available (retrieved {mc['retrieved_at']}).", icon="🟢"
        )
        df = mc["models"]
        fig = go.Figure()
        for col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    mode="lines",
                    name=col,
                    line=dict(width=1.5),
                    opacity=0.85,
                )
            )
        fig.update_layout(
            title=f"Model comparison — {var} ({entity.name})",
            template="plotly_white",
            height=340,
            margin=dict(l=10, r=10, t=40, b=10),
            yaxis_title=var,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        render_plotly(fig, key="wx_model_chart")
        st.caption(
            "Models: ECMWF IFS/AIFS, GFS, ICON, GEM (Open-Meteo multi-model API). "
            "Model disagreement is shown as-is — this is not a probability forecast."
        )
    else:
        st.info(f"Model comparison unavailable: {mc.get('error')}", icon="ℹ️")

    st.caption(
        "Scientific calculations are metric. Imperial units are a presentation "
        "preference only (toggle in the sidebar). Live forecast is Open-Meteo model "
        "output, not official station observations."
    )

    st.divider()

    # ---- AI global models (WeatherNext / NVIDIA Earth-2) ---- #
    st.subheader("AI global models")
    ai_models = get_ai_model_status()
    if ai_models:
        rows = [
            {
                "Model": r["name"],
                "Access": r["access"],
                "Status": r["status"],
                "Resolution": r["resolution"],
            }
            for r in ai_models
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption(
            "WeatherNext 3 and NVIDIA Earth-2 (FourCastNet/StormCast) are AI global "
            "forecast models. Both are credential/allowlist-gated — no keyless free "
            "hosted API exists — so they are wired in and reported honestly, and will "
            "populate the model comparison once access is approved. ECMWF AIFS, IFS, "
            "GFS, ICON, and GEM (above) are the working alternatives."
        )
    else:
        st.info("AI model status unavailable.", icon="ℹ️")
