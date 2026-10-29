"""Drought monitor — the USGS western-Pacific drought-monitoring methodology.

Replicates the monthly drought monitor of the USGS data release "Hydro-climatic
datasets … western Pacific Island nations" (Senay, Kagone, Dwomoh & Andersen
2026, DOI 10.5066/P1RXUMV3), verified against the release's R scripts
(``3_IMERG_Monthly_Drought_Monitor.R``, downloaded 2026-10-29). For each location
and the latest month it reports four drought indices:

* **1-/3-/6-Month Rainfall Index** — the quintile class (Drier/Dry/Typical/Wet/
  Wetter) of the current month's precipitation and its rolling 3- and 6-month
  sums, each compared against the same-calendar-month distribution over a
  ``baseline_start``–``baseline_end`` baseline.
* **PEAC 4/8-inch Index** — an absolute traffic light on the latest month's
  precipitation: Red (<101.6 mm), Yellow (101.6–203.2 mm), Dark Green (>203.2 mm).

The USGS pipeline runs on NASA IMERG Early Run with a 2000–2024 baseline. This
module is source-agnostic: the app feeds it ERA5 or CHIRPS (both of which cover
ocean-adjacent atolls more reliably than IMERG's land-masked grids) with a
1991–2020 baseline. It is an independent implementation of the published,
verified method — not the USGS CSV.
"""

from __future__ import annotations

import pandas as pd

from .percentiles import (
    classify_quintile,
    drought_level,
    empirical_percentile,
    monthly_distributions,
    peac_index,
)
from .rainfall_metrics import monthly_totals, rolling_totals


def drought_monitor_status(
    daily: pd.Series,
    baseline_start: str = "1991-01-01",
    baseline_end: str = "2020-12-31",
    windows: tuple[int, ...] = (1, 3, 6),
) -> dict:
    """Compute the drought-monitor status for the latest month of a daily series.

    Returns the latest month, monthly precipitation, climatological median,
    percentile, and all four drought indices (1-/3-/6-month Rainfall Index +
    PEAC 4/8-inch Index), plus rolling totals. Every value is ``None``/NaN where
    data is missing — nothing is fabricated.
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
    # 1-month Rainfall Index: classify the latest month against the per-month
    # distribution's quintile thresholds (R type-7 quantile — matches USGS).
    indices: dict[str, str | None] = {"rain_index_1m": classify_quintile(latest, dist)}
    for w in windows:
        col = f"rain_{w}m_mm"
        s = rolling[col].dropna()
        roll[f"rain_{w}m_mm"] = float(s.iloc[-1]) if len(s) else None
        if w > 1:
            # 3-/6-month Rainfall Index: classify the rolling sum against the
            # same-calendar-month rolling sums within the baseline (matches USGS).
            rdist = monthly_distributions(rolling[col], baseline_start, baseline_end).get(
                latest_month.month, pd.Series(dtype=float)
            )
            indices[f"rain_index_{w}m"] = classify_quintile(roll[f"rain_{w}m_mm"], rdist)

    return {
        "latest_month": latest_month.strftime("%Y-%m"),
        "monthly_mm": latest,
        "clim_median_mm": median,
        "percentile": float(percentile) if pd.notna(percentile) else None,
        "quintile": classify_quintile(latest, dist),
        "d0_d4": drought_level(percentile),
        "peac_index": peac_index(latest),
        **indices,
        **roll,
    }


def _empty_status(windows: tuple[int, ...]) -> dict:
    roll = {f"rain_{w}m_mm": None for w in windows}
    indices = {f"rain_index_{w}m": None for w in windows if w > 1}
    return {
        "latest_month": None,
        "monthly_mm": None,
        "clim_median_mm": None,
        "percentile": None,
        "quintile": None,
        "d0_d4": None,
        "peac_index": None,
        **indices,
        **roll,
    }
