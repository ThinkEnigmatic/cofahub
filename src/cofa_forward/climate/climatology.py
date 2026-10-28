"""Location climatology helpers.

Thin, deterministic wrappers over the drought/anomaly primitives that produce a
per-location summary for island profiles and the overview.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from ..drought import anomalies, percentiles, rainfall_metrics


def compute_location_climatology(
    daily: pd.Series,
    baseline_start: str,
    baseline_end: str,
    min_years: int,
) -> dict[str, Any]:
    """Compute a climatological summary dict for one location from daily rainfall."""
    monthly = rainfall_metrics.monthly_totals(daily, min_days_frac=0.8)
    return _from_monthly(monthly, baseline_start, baseline_end, min_years)


def compute_monthly_climatology(
    monthly: pd.Series,
    baseline_start: str,
    baseline_end: str,
    min_years: int,
) -> dict[str, Any]:
    """Compute a climatological summary from an already-monthly rainfall series."""
    return _from_monthly(monthly, baseline_start, baseline_end, min_years)


def _from_monthly(
    monthly: pd.Series,
    baseline_start: str,
    baseline_end: str,
    min_years: int,
) -> dict[str, Any]:
    """Shared climatological summary for a monthly rainfall series."""
    climatology = anomalies.monthly_climatology(monthly, baseline_start, baseline_end)
    valid = anomalies.baseline_is_valid(monthly, baseline_start, baseline_end, min_years)

    anom = anomalies.anomaly(monthly, climatology, min_years, baseline_start, baseline_end)
    anom_pct = anomalies.anomaly_percent(
        monthly, climatology, min_years, baseline_start, baseline_end
    )
    pctile = percentiles.monthly_percentiles(monthly, baseline_start, baseline_end)

    latest_month = monthly.dropna()
    latest_ts = latest_month.index[-1] if len(latest_month) else None
    latest = {
        "month": latest_ts,
        "total_mm": float(latest_month.iloc[-1]) if len(latest_month) else None,
        "anomaly_mm": float(anom.loc[latest_ts])
        if latest_ts is not None and latest_ts in anom.index and pd.notna(anom.loc[latest_ts])
        else None,
        "anomaly_pct": float(anom_pct.loc[latest_ts])
        if latest_ts is not None
        and latest_ts in anom_pct.index
        and pd.notna(anom_pct.loc[latest_ts])
        else None,
        "percentile": float(pctile.loc[latest_ts])
        if latest_ts is not None and latest_ts in pctile.index and pd.notna(pctile.loc[latest_ts])
        else None,
    }

    return {
        "monthly": monthly,
        "climatology": climatology,
        "baseline_valid": valid,
        "latest": latest,
        "anomaly_mm": anom,
        "anomaly_pct": anom_pct,
        "percentile": pctile,
    }
