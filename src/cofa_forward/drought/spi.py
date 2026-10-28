"""Standardized Precipitation Index (SPI) — normal-score variant.

The build plan defers full gamma-fit SPI in favour of percentile-based
indicators. This module provides a transparent, tested *normal-score transform*
(empirical percentile mapped to a standard-normal quantile via the stdlib
``statistics.NormalDist``), which is a non-parametric approximation of SPI.

Full gamma-distribution SPI (with zero-precipitation and fitting handling) is a
documented follow-up in docs/SCIENTIFIC_METHODS.md and remains disabled by
default in config.
"""

from __future__ import annotations

from statistics import NormalDist

import pandas as pd

_NORMAL = NormalDist()


def percentile_to_normal_score(p: float) -> float:
    """Map an empirical percentile (0..1) to a standard-normal quantile.

    Percentiles are clamped to a finite range to avoid ±infinity at the edges.
    """
    if pd.isna(p):
        return float("nan")
    p = min(max(float(p), 1e-3), 1 - 1e-3)
    return _NORMAL.inv_cdf(p)


def spi_from_percentile(p: float) -> float:
    """Non-parametric SPI estimate from an empirical percentile (0..1)."""
    return percentile_to_normal_score(p)


def note() -> str:
    return (
        "SPI shown here is a non-parametric normal-score transform of the empirical "
        "percentile, NOT a full gamma-fit SPI. It does not directly measure water "
        "availability. Full gamma-fit SPI is deferred (see SCIENTIFIC_METHODS.md)."
    )
