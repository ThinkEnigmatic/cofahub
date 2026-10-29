"""Precipitation comparison: current cycle vs the last major El Niño emergency.

For a selected location, fetch a long ERA5 daily precipitation series, split it
into the benchmark El Niño windows (1997-98, 2015-16, 2023-24) and the current
cycle, and align each to the event onset so the drought *shape* is comparable.

Everything is a precipitation-percentile / anomaly computation over real data —
no synthetic numbers and no fabricated crisis thresholds. The "crisis" timing is
reported from the documented record (``el_nino_history``), not re-derived.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd

from .el_nino_history import EL_NINO_EVENTS

_BASELINE_START = "1991-01-01"
_BASELINE_END = "2020-12-31"


def _monthly(daily: pd.Series) -> pd.Series:
    """Monthly precipitation totals (mm) from a daily series (tz-naive index)."""
    if daily is None or daily.empty:
        return pd.Series(dtype=float)
    idx = daily.index
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_localize(None)
    s = pd.Series(daily.values, index=idx)
    m = s.resample("MS").sum()
    return m.dropna()


def _monthly_climatology(monthly: pd.Series, baseline_start: str, baseline_end: str) -> pd.Series:
    """Mean monthly precipitation (mm) over the baseline window, keyed by month 1..12."""
    if monthly.empty:
        return pd.Series(dtype=float)
    base = monthly[(monthly.index >= baseline_start) & (monthly.index <= baseline_end)]
    if base.empty:
        return pd.Series(dtype=float)
    return base.groupby(base.index.month).mean()


def _align_to_onset(monthly: pd.Series, onset_ym: str, months: int = 36) -> pd.Series:
    """Slice a monthly series to a window anchored at ``onset_ym`` (YYYY-MM).

    Returns a Series indexed by ``month_index`` (0 = onset month) of precipitation
    (mm). Gaps are NaN (missing stays missing).
    """
    onset = pd.Timestamp(onset_ym)
    idx = pd.date_range(onset, periods=months, freq="MS")
    return monthly.reindex(idx)


def rolling_anomaly_pct(monthly: pd.Series, climatology: pd.Series, window: int = 6) -> pd.Series:
    """Rolling ``window``-month rainfall as % of the same-month climatology total.

    A value of 100 = exactly normal; <50 is severe deficit.
    """
    if monthly.empty or climatology.empty:
        return pd.Series(dtype=float)
    clim_total = pd.Series(index=monthly.index, dtype=float)
    for t in monthly.index:
        months = [(t - pd.DateOffset(months=k)).month for k in range(window)]
        clim_total[t] = float(climatology.reindex(months).sum())
    rolling = monthly.rolling(window, min_periods=window).sum()
    return (rolling / clim_total * 100.0).replace([float("inf"), float("-inf")], float("nan"))


def build_comparison(daily: pd.Series, now: date | None = None) -> dict:
    """Compute the now-vs-past comparison for a location's daily rainfall series.

    Returns a dict with ``monthly``, ``climatology``, and per-event aligned
    monthly + rolling-% curves, plus a ``current`` window (the trailing 24 months
    aligned to "now").
    """
    now = now or datetime.now(UTC).date()
    monthly = _monthly(daily)
    climatology = _monthly_climatology(monthly, _BASELINE_START, _BASELINE_END)
    anom6 = rolling_anomaly_pct(monthly, climatology, window=6)

    events = {}
    for ev in EL_NINO_EVENTS:
        aligned = _align_to_onset(monthly, ev["onset"], months=36)
        events[ev["id"]] = {
            "label": ev["label"],
            "onset": ev["onset"],
            "peak": ev["peak"],
            "recovery": ev["recovery"],
            "strength": ev["strength"],
            "monthly_aligned": aligned,
            "rolling6_pct_aligned": rolling_anomaly_pct(aligned, climatology, window=6),
        }

    # Current cycle: trailing 24 months ending last month.
    current_start = pd.Timestamp(now).to_period("M").start_time - pd.DateOffset(months=23)
    current_monthly = monthly[monthly.index >= current_start]
    current_anom6 = anom6[anom6.index >= current_start]

    return {
        "monthly": monthly,
        "climatology": climatology,
        "rolling6_pct": anom6,
        "events": events,
        "current": {
            "label": "Current cycle",
            "start": str(current_start.date()),
            "monthly": current_monthly,
            "rolling6_pct": current_anom6,
        },
        "latest_month": str(monthly.index[-1].date()) if not monthly.empty else None,
        "baseline": f"{_BASELINE_START}–{_BASELINE_END}",
    }
