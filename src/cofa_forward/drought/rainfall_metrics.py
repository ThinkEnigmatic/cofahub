"""Rainfall accumulation and rolling totals with explicit missing-data handling.

Missing months must NEVER silently become zero rainfall. A month with too many
missing days is dropped (NaN), and a rolling total that spans a dropped month is
itself NaN.
"""

from __future__ import annotations

import pandas as pd


def monthly_totals(daily: pd.Series, min_days_frac: float = 0.8) -> pd.Series:
    """Aggregate daily rainfall (mm) to monthly totals, guarding against gaps.

    Parameters
    ----------
    daily:
        ``pd.Series`` of daily precipitation indexed by a ``DatetimeIndex``.
    min_days_frac:
        Minimum fraction of days that must be present for a month to be valid.
        Months below this threshold become NaN (never zero).

    Returns
    -------
    ``pd.Series`` of monthly totals indexed by month-end, with NaN for
    incomplete months.
    """
    if not isinstance(daily.index, pd.DatetimeIndex):
        raise TypeError("daily series must have a DatetimeIndex")
    if not (0.0 < min_days_frac <= 1.0):
        raise ValueError("min_days_frac must be in (0, 1]")

    df = pd.DataFrame({"precip": daily})
    df["ym"] = df.index.to_period("M")
    grp = df.groupby("ym")["precip"]
    total = grp.sum(min_count=1)
    n_days = grp.size()
    days_in_month = df["ym"].dt.days_in_month.groupby(df["ym"]).first()

    completeness = n_days / days_in_month
    total = total.where(completeness >= min_days_frac)
    # Reindex to a month-end DatetimeIndex for clean rolling alignment.
    total.index = total.index.to_timestamp(how="end")
    total = total.sort_index()
    return total


def rolling_totals(
    daily: pd.Series,
    windows: list[int] | tuple[int, ...] = (1, 3, 6, 12),
    min_days_frac: float = 0.8,
) -> pd.DataFrame:
    """Compute rolling N-month rainfall totals.

    Returns a DataFrame with one column per window (``rain_{n}m_mm``), indexed by
    month-end. A rolling sum requires all ``n`` contributing months to be valid;
    otherwise the value is NaN.
    """
    monthly = monthly_totals(daily, min_days_frac=min_days_frac)
    out = {}
    for w in windows:
        out[f"rain_{w}m_mm"] = monthly.rolling(w, min_periods=w).sum()
    return pd.DataFrame(out)


def daily_to_monthly_series(daily: pd.Series) -> pd.Series:
    """Convenience alias returning the monthly total series (full-month only)."""
    return monthly_totals(daily, min_days_frac=1.0)
