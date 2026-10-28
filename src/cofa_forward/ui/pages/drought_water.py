"""Drought & Water — drought indicators, thresholds, and freshwater framework."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ...climate.climatology import compute_location_climatology
from ...drought.alerts import evaluate_alerts
from ...drought.percentiles import category_from_percentile, empirical_percentile
from ...drought.rainfall_metrics import rolling_totals
from ...drought.spi import note as spi_note
from ...visualization.charts import rainfall_timeseries, rolling_totals_chart
from ..components.common import page_header, render_plotly, sample_banner
from ..state import (
    get_real_rainfall,
    get_sample_rainfall,
    load_config,
    load_registry,
)


def render() -> None:
    cfg = load_config()
    registry = load_registry()
    page_header("Drought & Water", "Rainfall deficits, percentiles, and freshwater context")

    d = cfg.drought

    names = {e.geo_id: e.name for e in registry.all()}
    geo_id = st.selectbox(
        "Location", options=list(names.keys()), format_func=lambda g: f"{names[g]} ({g})"
    )
    entity = registry.by_id(geo_id)

    # ---- Data source selection ---- #
    use_real = st.toggle(
        "Use real rainfall (ERA5 via Open-Meteo)",
        value=False,
        help="Fetch ~34 years of daily ERA5 reanalysis rainfall for this location. "
        "Cached for 24h; falls back to labeled sample data on failure.",
    )
    real_result = None
    if use_real:
        with st.spinner("Fetching ERA5 rainfall…"):
            real_result = get_real_rainfall(geo_id, entity.latitude, entity.longitude)
        if real_result.get("ok"):
            daily = real_result["series"]
            st.success(
                f"Real ERA5 rainfall: {real_result['n_days']} days "
                f"({real_result['n_missing']} missing), retrieved {real_result['retrieved_at']}.",
                icon="🟢",
            )
            st.caption(
                "~25 km reanalysis — regional model estimate; individual-atoll "
                "conditions may differ."
            )
        else:
            st.error(f"Real rainfall fetch failed ({real_result.get('error')}); using sample data.")
            sample_banner()
            daily = get_sample_rainfall(geo_id)
    else:
        sample_banner()
        daily = get_sample_rainfall(geo_id)

    clim = compute_location_climatology(
        daily, d["baseline_start"], d["baseline_end"], d["baseline_min_years"]
    )
    monthly = clim["monthly"]
    rolling = rolling_totals(daily, windows=(1, 3, 6, 12), min_days_frac=0.8)

    latest = clim["latest"]
    cat = (
        category_from_percentile(latest.get("percentile"), d["percentile_categories"])
        if latest.get("percentile") is not None
        else "no data"
    )

    # ---- Latest indicators ---- #
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Latest month rainfall",
        f"{latest['total_mm']:.0f} mm" if latest["total_mm"] is not None else "n/a",
    )
    c2.metric(
        "Anomaly", f"{latest['anomaly_pct']:+.0f}%" if latest["anomaly_pct"] is not None else "n/a"
    )
    pct = latest.get("percentile")
    c3.metric("Rainfall percentile", f"{pct:.0%}" if pct is not None else "n/a")
    c4.metric("Drought category", cat)
    st.caption(
        f"Baseline: {d['baseline_start']}–{d['baseline_end']} (valid: {clim['baseline_valid']})."
    )

    st.divider()

    # ---- Charts ---- #
    st.subheader("Monthly rainfall vs climatology")
    render_plotly(
        rainfall_timeseries(monthly, clim["climatology"], title="Monthly rainfall"),
        key="drought_monthly",
    )

    st.subheader("Rolling rainfall totals")
    render_plotly(
        rolling_totals_chart(rolling, title="Rolling N-month totals"),
        key="drought_rolling",
    )

    st.divider()

    # ---- Alert thresholds ---- #
    st.subheader("Analyst alert thresholds")
    thresholds = cfg.alert_thresholds()

    # Compute a couple of indicators from the selected series to evaluate against.
    last_daily = daily.dropna()
    last_daily = float(last_daily.iloc[-1]) if len(last_daily) else float("nan")
    rolling3 = rolling["rain_3m_mm"].dropna()
    rolling6 = rolling["rain_6m_mm"].dropna()
    pct3 = (
        empirical_percentile(float(rolling3.iloc[-1]), rolling3) if len(rolling3) else float("nan")
    )
    pct6 = (
        empirical_percentile(float(rolling6.iloc[-1]), rolling6) if len(rolling6) else float("nan")
    )

    indicators = {
        "daily_precipitation_mm": last_daily,
        "rolling_rainfall_3m_percentile": pct3,
        "rolling_rainfall_6m_percentile": pct6,
    }
    results = evaluate_alerts(thresholds, indicators)

    rows = []
    for r in results:
        val = r["value"]
        val_txt = f"{val:.2f}" if isinstance(val, (int, float)) and val == val else "n/a"
        rows.append(
            {
                "Threshold": r["name"],
                "Indicator": r["indicator"],
                "Value": val_txt,
                "Fired": "⚠️ yes" if r["fired"] else "no",
                "Rule": f"{r['threshold'].get('operator')} {r['threshold'].get('value')}",
            }
        )
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption(
        "These are INTERNAL analyst watch levels, not official government warnings. "
        "Values are computed from the selected data source (real ERA5 or labeled sample)."
    )

    st.divider()

    # ---- Freshwater framework ---- #
    st.subheader("Freshwater vulnerability")
    fw = cfg.freshwater
    st.info(
        "Freshwater risk is **not** equated with a rainfall anomaly. Meteorological "
        "drought is shown above; actual water shortage requires additional inputs.",
        icon="💧",
    )
    st.write(
        "**Available (non-meteorological) inputs:** "
        + (", ".join(fw.get("available_inputs") or []) or "none")
    )
    st.write("**Missing inputs (not fabricated into a score):**")
    for m in fw.get("missing_inputs", []):
        st.markdown(f"- {m}")
    st.caption(fw.get("note"))

    st.divider()
    st.subheader("Standardized Precipitation Index (SPI)")
    st.info(spi_note(), icon="📐")
    st.caption("Percentile-based indicators are implemented first per the build plan.")
