"""El Niño Comparison — now vs the last major El Niño emergency, per location.

Select an atoll/country and compare the current precipitation cycle against the
benchmark El Niño droughts (1997-98, 2015-16, 2023-24), aligned by event onset,
plus documented crisis timing and media/relief reporting for the location.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ...drought.el_nino_comparison import build_comparison
from ...drought.el_nino_history import CRISIS, EL_NINO_EVENTS, LAST_MAJOR_EMERGENCY, REGIONAL_NOTE
from ..components.common import page_header, render_plotly
from ..state import (
    get_el_nino_comparison_rainfall,
    load_registry,
)

_EVENT_COLORS = {
    "2015-16": "#dc2626",  # last major emergency — red
    "1997-98": "#7c3aed",  # purple
    "2023-24": "#0891b2",  # cyan
    "current": "#059669",  # green — the "now" curve
}


def _aligned_figure(comparison: dict) -> go.Figure:
    """Rolling 6-month rainfall % of normal, each event aligned to its onset."""
    fig = go.Figure()

    for ev in EL_NINO_EVENTS:
        e = comparison["events"][ev["id"]]
        y = e["rolling6_pct_aligned"]
        if y.dropna().empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=list(range(len(y))),
                y=y.values,
                mode="lines",
                name=e["label"],
                line=dict(color=_EVENT_COLORS[ev["id"]], width=2),
                hovertemplate=(f"{e['label']}<br>month %{{x}}: %{{y:.0f}}%<extra></extra>"),
            )
        )

    # Current cycle (aligned to "now" going backwards).
    cur = comparison["current"]["rolling6_pct"]
    if not cur.dropna().empty:
        fig.add_trace(
            go.Scatter(
                x=list(range(len(cur))),
                y=cur.values,
                mode="lines",
                name="Current cycle (trailing 24 mo)",
                line=dict(color=_EVENT_COLORS["current"], width=3, dash="dot"),
            )
        )

    # 100% reference line.
    fig.add_hline(y=100, line=dict(color="#9ca3af", width=1, dash="dash"), annotation_text="normal")
    # 50% "severe deficit" line.
    fig.add_hline(
        y=50,
        line=dict(color="#f59e0b", width=1, dash="dot"),
        annotation_text="50% (severe deficit)",
    )

    fig.update_layout(
        title="Rolling 6-month rainfall (% of normal), aligned to El Niño onset",
        template="plotly_white",
        height=420,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="Months since onset",
        yaxis_title="% of normal (6-mo rolling)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return fig


def _current_vs_last_figure(comparison: dict, last_id: str) -> go.Figure:
    """Side-by-side: current trailing months vs the last major emergency's aligned months."""
    cur = comparison["current"]["monthly"]
    last = comparison["events"][last_id]["monthly_aligned"]
    clim = comparison["climatology"]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["Current cycle", "2015–16 emergency (aligned)"],
        shared_yaxes=True,
    )

    def _add(col: int, series: pd.Series | None, label: str, color: str) -> None:
        if series is None or series.dropna().empty:
            return
        pct = pd.Series(index=series.index, dtype=float)
        for t in series.index:
            c = clim.get(t.month)
            pct[t] = float(series[t]) / float(c) * 100.0 if c else float("nan")
        fig.add_trace(
            go.Bar(
                x=[str(d.date())[:7] for d in series.index],
                y=pct.values,
                name=label,
                marker_color=color,
            ),
            row=1,
            col=col,
        )

    _add(1, cur, "Current", _EVENT_COLORS["current"])
    _add(2, last, "2015–16", _EVENT_COLORS["2015-16"])

    fig.add_hline(y=100, line=dict(color="#9ca3af", width=1, dash="dash"), row=1, col=1)
    fig.add_hline(y=100, line=dict(color="#9ca3af", width=1, dash="dash"), row=1, col=2)
    fig.update_layout(
        template="plotly_white",
        height=340,
        margin=dict(l=10, r=10, t=50, b=10),
        yaxis_title="% of normal (monthly)",
        showlegend=False,
    )
    return fig


def _crisis_context(geo_id: str, parent_geo_id: str | None, country_code: str) -> None:
    """Show documented crisis timing + media/relief reporting for the location."""
    entry = None
    for key in (
        geo_id,
        parent_geo_id or "",
        "PAL" if country_code == "PW" else "",
        "FSM" if country_code == "FM" else "",
        "RMI" if country_code == "MH" else "",
    ):
        if key and key in CRISIS:
            entry = CRISIS[key]
            break

    if entry is None:
        st.info(
            REGIONAL_NOTE["summary"]
            + " No location-specific emergency record was found in the research corpus; "
            "the regional pattern applies.",
            icon="🌐",
        )
        st.caption(
            "Sources: " + ", ".join(f"[{s['name']}]({s['url']})" for s in REGIONAL_NOTE["sources"])
        )
        return

    # Last major emergency first, then the others chronologically.
    order = [LAST_MAJOR_EMERGENCY] + [
        e["id"] for e in EL_NINO_EVENTS if e["id"] != LAST_MAJOR_EMERGENCY
    ]
    for ev_id in order:
        if ev_id not in entry:
            continue
        f = entry[ev_id]
        ev_label = next((e["label"] for e in EL_NINO_EVENTS if e["id"] == ev_id), ev_id)
        subtitle = "last major emergency" if ev_id == LAST_MAJOR_EMERGENCY else "benchmark"
        with st.expander(f"{ev_label} — {subtitle}"):
            if f.get("emergency"):
                st.markdown(f"**Crisis / emergency:** {f['emergency']}")
            if f.get("rainfall"):
                st.markdown(f"**Precipitation at crisis:** {f['rainfall']}")
            if f.get("response"):
                st.markdown(f"**Relief response:** {f['response']}")
            if f.get("sources"):
                st.markdown("**Media / relief reporting:**")
                for s in f["sources"]:
                    st.markdown(f"- [{s['name']}]({s['url']})")


def render() -> None:
    registry = load_registry()
    page_header(
        "El Niño Comparison",
        "Current precipitation vs the last major El Niño emergency, per atoll/country",
    )

    names = {e.geo_id: e.name for e in registry.all()}
    # Countries + atolls + islands (exclude pure "state" to reduce clutter unless parent).
    geo_id = st.selectbox(
        "Atoll or country",
        options=list(names.keys()),
        format_func=lambda g: f"{names[g]} ({g})",
    )
    entity = registry.by_id(geo_id)

    st.caption(
        "Precipitation is ERA5 reanalysis (~25 km) — a regional estimate; individual-atoll "
        "conditions can differ. Crisis timing is from the documented record, not re-derived."
    )

    with st.spinner("Fetching ~30 years of ERA5 rainfall…"):
        rain = get_el_nino_comparison_rainfall(geo_id, entity.latitude, entity.longitude)

    if not rain.get("ok"):
        st.error(f"Rainfall fetch failed ({rain.get('error')}).")
        return

    daily = rain["series"]
    comparison = build_comparison(daily)

    # ---- Latest month metric strip ---- #
    clim = comparison["climatology"]
    monthly = comparison["monthly"]
    if not monthly.empty and not clim.empty:
        lm = monthly.iloc[-1]
        lm_month = monthly.index[-1].month
        lm_clim = clim.get(lm_month)
        lm_pct = float(lm) / float(lm_clim) * 100.0 if lm_clim else float("nan")
        st.metric(
            f"Latest month rainfall ({comparison['latest_month']})",
            f"{lm:.0f} mm",
            f"{lm_pct:.0f}% of normal",
        )

    st.divider()

    render_plotly(_aligned_figure(comparison), key="elnino_aligned")
    st.caption(
        "Curves aligned to El Niño onset (month 0). The red 2015–16 line is the last major "
        "emergency; the green dotted line is the current cycle. Below 50% (amber line) is "
        "a severe deficit."
    )

    st.divider()

    render_plotly(
        _current_vs_last_figure(comparison, LAST_MAJOR_EMERGENCY), key="elnino_now_vs_last"
    )
    st.caption("Monthly rainfall as % of normal — current (left) vs 2015–16 emergency (right).")

    st.divider()

    st.subheader("Crisis history & relief reporting")
    _crisis_context(geo_id, entity.parent_geo_id, entity.country_code)

    st.divider()
    st.caption(
        "Baseline for % of normal: 1991–2020 ERA5. This is contextual analysis, not a "
        "forecast and not an official warning."
    )
