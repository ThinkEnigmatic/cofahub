"""Deterministic intelligence indicators.

Computes a structured, traceable set of per-location indicators from validated
rainfall series and configuration. Every value retains its method + source.
"""

from __future__ import annotations

import pandas as pd

from ..climate.climatology import compute_location_climatology
from ..drought.percentiles import category_from_percentile
from ..drought.rainfall_metrics import rolling_totals
from ..timeutil import format_iso, now_utc


def compute_location_indicators(
    geo_id: str,
    name: str,
    daily: pd.Series,
    baseline_start: str,
    baseline_end: str,
    min_years: int,
    percentile_categories: list[dict],
) -> dict:
    """Compute a compact indicator dict for one location."""
    rolling = rolling_totals(daily, windows=(1, 3, 6, 12), min_days_frac=0.8)
    clim = compute_location_climatology(daily, baseline_start, baseline_end, min_years)

    latest = clim["latest"]
    pct = latest.get("percentile")
    category = (
        category_from_percentile(pct, percentile_categories) if pct is not None else "no data"
    )

    # Latest valid rolling values (most recent month with complete windows)
    last_roll = rolling.dropna(how="all")
    roll_vals = {}
    if len(last_roll):
        row = last_roll.iloc[-1]
        for w in (1, 3, 6, 12):
            roll_vals[f"rain_{w}m_mm"] = (
                float(row[f"rain_{w}m_mm"]) if pd.notna(row[f"rain_{w}m_mm"]) else None
            )

    return {
        "geo_id": geo_id,
        "name": name,
        "baseline_valid": clim["baseline_valid"],
        "latest_month": format_iso(latest["month"]) if latest["month"] is not None else None,
        "latest_total_mm": latest["total_mm"],
        "anomaly_mm": latest["anomaly_mm"],
        "anomaly_pct": latest["anomaly_pct"],
        "percentile": pct,
        "percentile_category": category,
        "rolling": roll_vals,
        "computed_at": format_iso(now_utc()),
        "method": "percentile-based (empirical), rolling totals over validated monthly sums",
    }


def indicators_table(indicators: list[dict]) -> pd.DataFrame:
    """Flatten a list of location indicator dicts into a DataFrame."""
    rows = []
    for ind in indicators:
        row = {
            "geo_id": ind["geo_id"],
            "name": ind["name"],
            "baseline_valid": ind["baseline_valid"],
            "latest_month": ind["latest_month"],
            "latest_total_mm": ind["latest_total_mm"],
            "anomaly_mm": ind["anomaly_mm"],
            "anomaly_pct": ind["anomaly_pct"],
            "percentile": ind["percentile"],
            "category": ind["percentile_category"],
        }
        for k, v in ind.get("rolling", {}).items():
            row[k] = v
        rows.append(row)
    return pd.DataFrame(rows)
