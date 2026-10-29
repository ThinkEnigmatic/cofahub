"""Long-term climate trends (linear + Mann-Kendall).

Multi-decadal change is the context every other indicator sits inside: is this
atoll getting drier/wetter/warmer, and is local sea level rising faster than the
global mean? These are deterministic, assumption-light trend estimators over a
date-indexed series (monthly or annual).

* :func:`linear_trend` — ordinary least-squares slope (per year).
* :func:`theil_sen_slope` — robust (median-of-pairwise-slopes) trend slope.
* :func:`mann_kendall` — Kendall's tau trend test with an asymptotic two-sided
  p-value (with tie correction).

Missing values are dropped before fitting. A series must have ≥ ``min_points``
values to produce a trend; otherwise the result is all-NaN (never fabricated).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _year_frac(index: pd.DatetimeIndex) -> np.ndarray:
    return index.year.values + (index.day_of_year.values - 1) / 365.25


def _clean(series: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("series must have a DatetimeIndex")
    s = series.dropna()
    return _year_frac(s.index), s.to_numpy(dtype=float)


def linear_trend(series: pd.Series, min_points: int = 10) -> tuple[float, float]:
    """Ordinary least-squares slope and intercept (per year) of a date-indexed series.

    Returns ``(slope_per_year, intercept)``; NaN when fewer than ``min_points``
    valid points.
    """
    x, y = _clean(series)
    if len(x) < min_points:
        return float("nan"), float("nan")
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)


def theil_sen_slope(series: pd.Series, min_points: int = 10) -> float:
    """Robust trend slope (Sen's slope, median of pairwise slopes), per year."""
    x, y = _clean(series)
    n = len(x)
    if n < min_points:
        return float("nan")
    slopes = []
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            if dx > 0:
                slopes.append((y[j] - y[i]) / dx)
    return float(np.median(slopes)) if slopes else float("nan")


def mann_kendall(series: pd.Series, min_points: int = 10) -> dict:
    """Mann-Kendall trend test.

    Returns ``{"tau": float, "p_value": float, "trend": "increasing"|"decreasing"|
    "no trend"|None}``. Ties are handled with the standard tie-correction
    variance; the two-sided p-value uses the normal approximation.
    """
    _, y = _clean(series)
    n = len(y)
    if n < min_points:
        return {"tau": float("nan"), "p_value": float("nan"), "trend": None}

    s = 0
    for i in range(n):
        for j in range(i + 1, n):
            s += int(y[j] > y[i]) - int(y[j] < y[i])

    # Tie correction for the variance.
    _, counts = np.unique(y, return_counts=True)
    tie_sum = float((counts * (counts - 1) * (2 * counts + 5)).sum())
    denom = n * (n - 1) * (2 * n + 5)
    var_s = (denom - tie_sum) / 18.0

    if var_s <= 0:
        return {"tau": float("nan"), "p_value": float("nan"), "trend": "no trend"}

    tau = s / (n * (n - 1) / 2.0)
    z = (s - math.copysign(1, s)) / math.sqrt(var_s) if s != 0 else 0.0
    p_value = 2.0 * (1.0 - _norm_cdf(abs(z)))

    trend = ("increasing" if tau > 0 else "decreasing") if p_value < 0.05 else "no trend"
    return {"tau": float(tau), "p_value": float(p_value), "trend": trend}


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def trend_summary(series: pd.Series, name: str, unit: str, min_points: int = 10) -> dict:
    """One-line trend summary for a date-indexed series.

    ``slope_per_year`` and ``slope_per_decade`` use the OLS slope; ``sen_slope`` is
    the robust Theil–Sen estimate; ``mk`` carries the Mann-Kendall significance.
    """
    slope, intercept = linear_trend(series, min_points)
    mk = mann_kendall(series, min_points)
    return {
        "name": name,
        "unit": unit,
        "n_points": int(series.dropna().size),
        "start": series.dropna().index.min().strftime("%Y") if not series.dropna().empty else None,
        "end": series.dropna().index.max().strftime("%Y") if not series.dropna().empty else None,
        "slope_per_year": slope,
        "slope_per_decade": slope * 10 if slope == slope else float("nan"),
        "intercept": intercept,
        "sen_slope_per_year": theil_sen_slope(series, min_points),
        "mann_kendall": mk,
        "verdict": mk.get("trend"),
    }
