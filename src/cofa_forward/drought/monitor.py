"""Drought monitor — the USGS western-Pacific drought-monitoring methodology.

Replicates Component 1 of the USGS data release "Drought Monitoring and 7-Day
Precipitation Forecasting for western Pacific Nations from 2000–2026" (Senay,
Kagone, Dwomoh & Andersen 2026, DOI 10.5066/P1RXUMV3): for each location and
month it reports observed monthly precipitation, the climatological median,
rolling 1-/3-/6-month totals, the **quintile Rainfall Index** (Drier/Dry/Typical/
Wet/Wetter) and the D0–D4 severity level.

The USGS pipeline runs on NASA IMERG Early Run. This module is source-agnostic:
it computes the same indicators from any daily/monthly rainfall series. The app
feeds it ERA5 or CHIRPS, both of which cover ocean-adjacent atolls more reliably
than IMERG's land-masked grids. This is an independent implementation of the
published method — **not** the USGS CSV (which is Cloudflare-gated on
ScienceBase).
"""

from __future__ import annotations

import pandas as pd

from .percentiles import (
    drought_level,
    empirical_percentile,
    monthly_distributions,
    quintile_index,
)
from .rainfall_metrics import monthly_totals, rolling_totals


def drought_monitor_status(
    daily: pd.Series,
    baseline_start: str = "1991-01-01",
    baseline_end: str = "2020-12-31",
    windows: tuple[int, ...] = (1, 3, 6),
) -> dict:
    """Compute the drought-monitor status for the latest month of a daily series.

    Every value is ``None``/NaN where the data is missing — nothing is fabricated.
    """
    monthly = monthly_totals(daily, min_days_frac=0.8)
    valid = monthly.dropna()
    if valid.empty:
        return _empty_status(windows)

    latest_month = valid.index[-1]
    latest = float(valid.iloc[-1])

    dists = monthly_distributions(monthly, baseline_start, baseline_end)
    dist = dists.get(latest_month.month, pd.Series(dtype=float))
    percentile = empirical_percentile(latest, dist) if len(dist) else float("nan")
    median = float(dist.median()) if len(dist) else float("nan")

    rolling = rolling_totals(daily, windows=windows, min_days_frac=0.8)
    roll: dict[str, float | None] = {}
    for w in windows:
        col = f"rain_{w}m_mm"
        s = rolling[col].dropna()
        roll[f"rain_{w}m_mm"] = float(s.iloc[-1]) if len(s) else None

    return {
        "latest_month": latest_month.strftime("%Y-%m"),
        "monthly_mm": latest,
        "clim_median_mm": median,
        "percentile": float(percentile) if pd.notna(percentile) else None,
        "quintile": quintile_index(percentile),
        "d0_d4": drought_level(percentile),
        **roll,
    }


def _empty_status(windows: tuple[int, ...]) -> dict:
    roll = {f"rain_{w}m_mm": None for w in windows}
    return {
        "latest_month": None,
        "monthly_mm": None,
        "clim_median_mm": None,
        "percentile": None,
        "quintile": None,
        "d0_d4": None,
        **roll,
    }
