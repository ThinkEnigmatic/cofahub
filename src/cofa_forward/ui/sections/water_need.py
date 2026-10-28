"""Water Need Forecast — modeled rainfall-driven deficit/surplus per island/atoll."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ...drought.water_balance import balance_table, forecast_water_balance
from ..components.common import page_header
from ..state import get_forecast_daily_precip, load_config, load_registry

_VERDICT_ICON = {"deficit": "🔴", "surplus": "🟢", "balanced": "⚪", "no data": "⚪"}


def render() -> None:
    cfg = load_config()
    registry = load_registry()
    page_header(
        "Water Need Forecast",
        "Modeled rainfall-driven deficit/surplus per island and atoll",
    )

    wb = cfg.freshwater["water_balance"]
    horizon = st.slider("Forecast horizon (days)", 1, 16, 7)

    if st.button("Refresh forecasts", type="primary"):
        get_forecast_daily_precip.clear()

    # Target the micro level: islands, atolls, and monitoring locations (plus states).
    targets = [
        e
        for e in registry.all()
        if e.entity_type in ("island", "atoll", "monitoring_location", "state")
    ]

    rows = []
    with st.spinner(f"Fetching {len(targets)} forecasts and computing water balance…"):
        for e in targets:
            base = {
                "geo_id": e.geo_id,
                "name": e.name,
                "entity_type": e.entity_type,
                "population": e.population,
            }
            if e.population is None:
                rows.append({**base, "verdict": "no data", "note": "no population figure"})
                continue
            fc = get_forecast_daily_precip(e.geo_id, e.latitude, e.longitude, days=horizon)
            if not fc["ok"]:
                rows.append({**base, "verdict": "no data", "note": "forecast unavailable"})
                continue
            override = wb.get("per_entity", {}).get(e.geo_id, {})
            bal = forecast_water_balance(
                e.population,
                fc["series"],
                per_capita_lpd=override.get("per_capita_lpd", wb["per_capita_lpd"]),
                per_person_catchment_m2=override.get(
                    "per_person_catchment_m2", wb["per_person_catchment_m2"]
                ),
                collection_efficiency=override.get(
                    "collection_efficiency", wb["collection_efficiency"]
                ),
                horizon_days=horizon,
                storage_l=override.get("storage_l", wb.get("storage_l")),
            )
            bal["geo_id"] = e.geo_id
            bal["name"] = e.name
            bal["entity_type"] = e.entity_type
            rows.append(bal)

    df = balance_table(rows)
    df["verdict_display"] = df["verdict"].map(lambda v: f"{_VERDICT_ICON.get(v, '')} {v}")

    st.subheader(f"Deficit / surplus over the next {horizon} days")
    st.dataframe(
        df[
            [
                "name",
                "entity_type",
                "population",
                "daily_demand_l",
                "required_mm",
                "forecast_mm",
                "balance_mm",
                "verdict_display",
            ]
        ].rename(
            columns={
                "daily_demand_l": "daily demand (L)",
                "required_mm": "required rain (mm)",
                "forecast_mm": "forecast rain (mm)",
                "balance_mm": "balance (mm)",
                "verdict_display": "verdict",
            }
        ),
        width="stretch",
        hide_index=True,
    )

    st.caption(
        f"Assumptions (documented planning defaults, not measured): "
        f"{wb['per_capita_lpd']} L/person/day, {wb['per_person_catchment_m2']} m²/person "
        f"catchment, {wb['collection_efficiency']} collection efficiency. "
        "A negative balance means forecast rainfall is projected to fall short of demand "
        "(modeled rainfall-driven deficit), not an actual confirmed shortage."
    )

    st.divider()

    # ---- Per-entity detail ---- #
    st.subheader("Per-entity detail")
    names = {e.geo_id: e.name for e in targets}
    geo_id = st.selectbox(
        "Entity", options=list(names.keys()), format_func=lambda g: f"{names[g]} ({g})"
    )
    row = next((r for r in rows if r.get("geo_id") == geo_id), None)
    if row and row.get("per_day"):
        st.markdown(f"**{row['name']}** — {row['population']:,} people")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Daily demand", f"{row['daily_demand_l']:,.0f} L")
        c2.metric("Required rain", f"{row['required_mm']:.1f} mm")
        c3.metric("Forecast rain", f"{row['forecast_mm']:.1f} mm")
        c4.metric("Balance", f"{row['balance_mm']:+.1f} mm")
        per_day = pd.DataFrame(row["per_day"]).rename(
            columns={
                "date": "date",
                "precip_mm": "rain (mm)",
                "demand_l": "demand (L)",
                "supply_l": "supply (L)",
                "net_l": "net (L)",
                "cumulative_net_l": "cumulative net (L)",
            }
        )
        st.dataframe(per_day, width="stretch", hide_index=True)
        st.caption(row.get("note", ""))
        if row.get("missing_inputs"):
            st.caption("Missing inputs: " + ", ".join(row["missing_inputs"]))
    elif row:
        st.info(f"{row['name']}: {row.get('note', 'no data')}", icon="ℹ️")

    st.divider()
    st.caption(
        "Forecast precipitation source: Open-Meteo (model output, ~11 km). "
        "Rainfall is attributed to each island's representative point — regional model "
        "estimate; individual-atoll conditions may differ."
    )
