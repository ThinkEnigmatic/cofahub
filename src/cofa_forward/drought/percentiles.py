"""Empirical percentile indicators for rainfall.

Percentile-based drought indicators are implemented before SPI (see build plan).
The empirical percentile of a value against a historical distribution is a
transparent, assumption-light severity measure.
"""

from __future__ import annotations

import pandas as pd


def empirical_percentile(value: float, distribution: pd.Series) -> float:
    """Empirical percentile rank (0..1) of ``value`` within ``distribution``.

    Uses the "average" (midpoint) ranking: the fraction of values strictly less
    than ``value`` plus half the fraction equal to ``value``. NaN entries in the
    distribution are ignored.
    """
    dist = distribution.dropna()
    if len(dist) == 0:
        return float("nan")
    n = len(dist)
    lt = (dist < value).sum()
    eq = (dist == value).sum()
    return float((lt + 0.5 * eq) / n)


def monthly_distributions(
    monthly: pd.Series,
    baseline_start: str,
    baseline_end: str,
) -> dict[int, pd.Series]:
    """Return per-calendar-month historical distributions within the baseline."""
    if not isinstance(monthly.index, pd.DatetimeIndex):
        raise TypeError("monthly series must have a DatetimeIndex")
    start = pd.Timestamp(baseline_start)
    end = pd.Timestamp(baseline_end)
    window = monthly.loc[(monthly.index >= start) & (monthly.index <= end)].dropna()
    return {m: window[window.index.month == m] for m in range(1, 13)}


def monthly_percentiles(
    monthly: pd.Series,
    baseline_start: str,
    baseline_end: str,
) -> pd.Series:
    """Percentile rank of each month against its calendar-month baseline distribution."""
    dists = monthly_distributions(monthly, baseline_start, baseline_end)
    out = []
    for ts, val in monthly.items():
        m = ts.month
        out.append(empirical_percentile(val, dists.get(m, pd.Series(dtype=float))))
    return pd.Series(out, index=monthly.index, dtype=float)


def category_from_percentile(p: float, categories: list[dict]) -> str:
    """Map an empirical percentile (0..1) to a severity label using config bins.

    ``categories`` is a list of ``{min, max, label}`` dicts; the first matching
    bin wins.
    """
    if pd.isna(p):
        return "no data"
    for c in categories:
        lo = c.get("min", 0.0)
        hi = c.get("max", 1.0)
        if lo <= p < hi:
            return c["label"]
    return "no data"


def drought_level(p: float) -> str | None:
    """Map an empirical percentile (0..1) to a D0–D4 drought category.

    These thresholds mirror the US Drought Monitor's precipitation-percentile
    bands (D0 abnormally dry … D4 exceptional). **This is a
    precipitation-percentile approximation, NOT the official US Drought Monitor**
    — which is US-only and blends many indicators (SPI, soil moisture,
    streamflow). The FAS is outside the USDM; use this as an internal
    precipitation-drought scale only.
    """
    if pd.isna(p):
        return None
    if p < 0.02:
        return "D4"
    if p < 0.05:
        return "D3"
    if p < 0.10:
        return "D2"
    if p < 0.20:
        return "D1"
    if p < 0.30:
        return "D0"
    return None
