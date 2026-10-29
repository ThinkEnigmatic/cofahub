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

    These thresholds mirror the U.S. Drought Monitor's precipitation-percentile
    bands (D0 20–30th … D4 0–2nd percentile). **This is a local
    precipitation-percentile approximation, NOT the official U.S. Drought
    Monitor** — the USDM blends many indicators (SPI, soil moisture, streamflow)
    and is the authoritative D0–D4 ranking (it added the U.S.-Affiliated Pacific
    Islands in 2019). Use this only as a separate, clearly-labelled local
    estimate alongside the official USDM category.
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


QUINTILE_LABELS = ("Drier", "Dry", "Typical", "Wet", "Wetter")


def quintile_index(p: float) -> str | None:
    """Map an empirical percentile (0..1) to the quintile Rainfall Index.

    Five equal quintiles of the climatological distribution, matching the USGS
    western-Pacific drought-monitoring methodology (Senay et al. 2026, DOI
    10.5066/P1RXUMV3): **Drier** (0–20th), **Dry** (20–40th), **Typical**
    (40–60th), **Wet** (60–80th), **Wetter** (80–100th percentile).
    """
    if pd.isna(p):
        return None
    if p < 0.20:
        return "Drier"
    if p < 0.40:
        return "Dry"
    if p < 0.60:
        return "Typical"
    if p < 0.80:
        return "Wet"
    return "Wetter"


def peac_index(monthly_mm: float) -> str | None:
    """The PEAC 4/8-inch Index — an absolute-threshold drought traffic light.

    Adapted from the Pacific ENSO Applications Climate Center, applied to the
    latest month's precipitation (baseline-independent). Exact thresholds from
    the USGS R scripts (Senay et al. 2026, ``3_IMERG_Monthly_Drought_Monitor.R``):

    * < 101.6 mm (< 4 in) → **Red** (drought concern)
    * 101.6–203.2 mm (4–8 in) → **Yellow** (adequate)
    * > 203.2 mm (> 8 in) → **Dark Green** (sufficient)
    """
    if pd.isna(monthly_mm):
        return None
    if monthly_mm < 101.6:
        return "Red"
    if monthly_mm <= 203.2:
        return "Yellow"
    return "Dark Green"


def classify_quintile(value: float, dist: pd.Series) -> str | None:
    """Classify a value against the quintile thresholds of a distribution.

    Faithfully mirrors the USGS R script (``3_IMERG_Monthly_Drought_Monitor.R``):
    the thresholds are ``quantile(dist, c(0.2, 0.4, 0.6, 0.8))`` using R's
    default type-7 (Hyndman–Fan) interpolation — which equals pandas
    ``interpolation="linear"`` — and the value is classified with the R if/else
    chain (``< Q20 → Drier, < Q40 → Dry, < Q60 → Typical, < Q80 → Wet, else
    Wetter``).

    This differs subtly from :func:`quintile_index` (which takes an already-
    computed *rank*); use this where the goal is to reproduce the USGS index from
    raw values.
    """
    if pd.isna(value) or dist is None:
        return None
    d = dist.dropna()
    if d.empty:
        return None
    q = d.quantile([0.2, 0.4, 0.6, 0.8], interpolation="linear")
    if value < q.iloc[0]:
        return "Drier"
    if value < q.iloc[1]:
        return "Dry"
    if value < q.iloc[2]:
        return "Typical"
    if value < q.iloc[3]:
        return "Wet"
    return "Wetter"
