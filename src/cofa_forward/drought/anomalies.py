"""Rainfall climatology and anomalies against a documented baseline.

An anomaly is only computed when the baseline is valid (enough years). If the
baseline is insufficient or invalid, the result is NaN and flagged — never a
silently-wrong number.
"""

from __future__ import annotations

import pandas as pd


def monthly_climatology(
    monthly: pd.Series,
    baseline_start: str,
    baseline_end: str,
) -> pd.Series:
    """Mean rainfall by calendar month over a baseline window.

    Parameters
    ----------
    monthly:
        Monthly rainfall totals (mm), DatetimeIndex (month-end).
    baseline_start / baseline_end:
        ISO date bounds (inclusive). Months outside this window are ignored.

    Returns
    -------
    Series indexed by calendar month (1..12) of baseline means.
    """
    if not isinstance(monthly.index, pd.DatetimeIndex):
        raise TypeError("monthly series must have a DatetimeIndex")
    start = pd.Timestamp(baseline_start)
    end = pd.Timestamp(baseline_end)
    window = monthly.loc[(monthly.index >= start) & (monthly.index <= end)]
    return window.groupby(window.index.month).mean()


def baseline_years(monthly: pd.Series, baseline_start: str, baseline_end: str) -> int:
    """Count distinct years with at least one valid month in the baseline window."""
    start = pd.Timestamp(baseline_start)
    end = pd.Timestamp(baseline_end)
    window = monthly.loc[(monthly.index >= start) & (monthly.index <= end)].dropna()
    return window.index.year.nunique()


def baseline_is_valid(
    monthly: pd.Series,
    baseline_start: str,
    baseline_end: str,
    min_years: int,
) -> bool:
    """True when the baseline has at least ``min_years`` years of data."""
    return baseline_years(monthly, baseline_start, baseline_end) >= min_years


def anomaly(
    monthly: pd.Series,
    climatology: pd.Series,
    min_years: int,
    baseline_start: str,
    baseline_end: str,
) -> pd.Series:
    """Monthly rainfall anomaly (mm) vs climatology.

    Only months whose baseline is valid (``>= min_years``) receive a value;
    others are NaN.
    """
    if not baseline_is_valid(monthly, baseline_start, baseline_end, min_years):
        return pd.Series(index=monthly.index, dtype=float)
    clim = monthly.index.month.map(climatology)
    return (monthly - clim).where(clim.notna())


def anomaly_percent(
    monthly: pd.Series,
    climatology: pd.Series,
    min_years: int,
    baseline_start: str,
    baseline_end: str,
) -> pd.Series:
    """Rainfall anomaly as a percentage of normal.

    ``(obs - clim) / clim * 100``. NaN when the baseline is invalid or the
    climatological mean is zero/missing.
    """
    base = anomaly(monthly, climatology, min_years, baseline_start, baseline_end)
    clim = monthly.index.month.map(climatology)
    pct = base / clim * 100.0
    return pct.where(clim.notna() & (clim != 0))
