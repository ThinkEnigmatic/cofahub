"""Drought & Water — drought indicators, thresholds, and freshwater framework."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ...climate.climatology import compute_location_climatology, compute_monthly_climatology
from ...drought.alerts import evaluate_alerts
from ...drought.percentiles import (
    category_from_percentile,
    drought_level,
    empirical_percentile,
    quintile_index,
)
from ...drought.rainfall_metrics import rolling_totals
from ...drought.spi import note as spi_note
from ...visualization.charts import rainfall_timeseries, rolling_totals_chart
from ..components.common import page_header, render_plotly, sample_banner
from ..state import (
    get_chirps_monthly,
    get_drought_monitor,
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
    source = st.radio(
        "Rainfall data source",
        ["Sample (synthetic)", "ERA5 (Open-Meteo)", "CHIRPS v3 (satellite)"],
        index=0,
        horizontal=True,
    )

    if source == "ERA5 (Open-Meteo)":
        with st.spinner("Fetching ERA5 rainfall…"):
            real_result = get_real_rainfall(geo_id, entity.latitude, entity.longitude)
        if real_result.get("ok"):
            daily = real_result["series"]
            st.success(
                f"ERA5 rainfall: {real_result['n_days']} days "
                f"({real_result['n_missing']} missing), retrieved {real_result['retrieved_at']}.",
                icon="🟢",
            )
            st.caption(
                "~25 km reanalysis — regional model estimate; individual-atoll "
                "conditions may differ."
            )
            clim = compute_location_climatology(
                daily, d["baseline_start"], d["baseline_end"], d["baseline_min_years"]
            )
            monthly = clim["monthly"]
            rolling = rolling_totals(daily, windows=(1, 3, 6, 12), min_days_frac=0.8)
        else:
            st.error(f"ERA5 fetch failed ({real_result.get('error')}); using sample data.")
            sample_banner()
            daily = get_sample_rainfall(geo_id)
            clim = compute_location_climatology(
                daily, d["baseline_start"], d["baseline_end"], d["baseline_min_years"]
            )
            monthly = clim["monthly"]
            rolling = rolling_totals(daily, windows=(1, 3, 6, 12), min_days_frac=0.8)
    elif source == "CHIRPS v3 (satellite)":
        with st.spinner("Fetching CHIRPS v3 monthly rainfall (this can take ~1–2 min)…"):
            chirps = get_chirps_monthly(geo_id, entity.latitude, entity.longitude)
        if chirps.get("ok") and len(chirps["series"].dropna()) > 0:
            st.success(
                f"CHIRPS v3 rainfall: {chirps['n_months']} months "
                f"({chirps['n_missing']} masked/missing).",
                icon="🟢",
            )
            st.caption(
                "0.05° satellite estimate, land-masked. Sub-pixel islands use the "
                "max-valid-pixel heuristic; ERA5 is preferred for ocean-adjacent atolls."
            )
            monthly = chirps["series"]
            clim = compute_monthly_climatology(
                monthly, d["baseline_start"], d["baseline_end"], d["baseline_min_years"]
            )
            daily = None
            rolling = pd.DataFrame(
                {f"rain_{w}m_mm": monthly.rolling(w, min_periods=w).sum() for w in (1, 3, 6, 12)}
            )
        else:
            st.error("CHIRPS fetch failed or returned no land pixels; using sample data.")
            sample_banner()
            daily = get_sample_rainfall(geo_id)
            clim = compute_location_climatology(
                daily, d["baseline_start"], d["baseline_end"], d["baseline_min_years"]
            )
            monthly = clim["monthly"]
            rolling = rolling_totals(daily, windows=(1, 3, 6, 12), min_days_frac=0.8)
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
    d_level = drought_level(pct)
    c4.metric(
        "Drought level (D0–D4)",
        d_level if d_level else ("none" if pct is not None else "n/a"),
        help="Precipitation-percentile approximation of the USDM D0–D4 scale.",
    )
    q = quintile_index(pct)
    st.caption(
        f"Baseline: {d['baseline_start']}–{d['baseline_end']} (valid: {clim['baseline_valid']}). "
        f"Category: {cat}. "
        f"**Quintile Rainfall Index: {q or 'n/a'}** "
        "(Drier/Dry/Typical/Wet/Wetter — USGS western-Pacific method)."
    )

    st.divider()

    # ---- Live drought monitor (USGS western-Pacific method on ERA5) ---- #
    st.subheader("Drought monitor — quintile Rainfall Index (live, ERA5)")
    with st.spinner("Computing drought monitor from ERA5…"):
        monitor = get_drought_monitor(geo_id, entity.latitude, entity.longitude)
    if monitor.get("ok"):
        m = monitor["status"]
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Latest month", m.get("latest_month") or "n/a")
        m2.metric("Monthly rainfall", f"{m['monthly_mm']:.0f} mm" if m["monthly_mm"] else "n/a")
        m3.metric(
            "Climatological median",
            f"{m['clim_median_mm']:.0f} mm" if m["clim_median_mm"] else "n/a",
        )
        m4.metric("Quintile Rainfall Index", m.get("quintile") or "n/a")
        m5.metric("D0–D4", m.get("d0_d4") or ("none" if m.get("percentile") is not None else "n/a"))
        roll = " · ".join(
            f"{w}m={m[f'rain_{w}m_mm']:.0f} mm" if m.get(f"rain_{w}m_mm") else f"{w}m=n/a"
            for w in (1, 3, 6)
        )
        st.caption(
            f"Rolling totals: {roll}. Computed from ERA5 ({monitor['source']}) using the "
            "USGS western-Pacific method (Senay et al. 2026, DOI 10.5066/P1RXUMV3) — an "
            "independent implementation, not the USGS CSV (which is Cloudflare-gated on "
            "ScienceBase and covers FSM/RMI/Nauru/Solomon, not Palau)."
        )
    else:
        st.info(f"Drought monitor unavailable: {monitor.get('error')}", icon="ℹ️")

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
    if daily is not None:
        last_vals = daily.dropna()
        last_daily = float(last_vals.iloc[-1]) if len(last_vals) else float("nan")
    else:
        last_daily = float("nan")  # monthly series: no daily precip indicator
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
        "Values are computed from the selected data source."
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
