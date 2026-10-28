"""Standardized Precipitation Index (SPI).

Two estimators are provided:

1. ``spi_from_percentile`` — a non-parametric *normal-score* transform of the
   empirical percentile (no distribution assumption).
2. ``spi_gamma`` — the classical gamma-distribution SPI (Edwards & McKee 1997),
   with a maximum-likelihood gamma fit (Thom initialization + Newton refinement)
   and explicit zero-precipitation handling via a mixed distribution.

The gamma functions (log-gamma, digamma, trigamma, regularized incomplete gamma)
are implemented in pure NumPy/math (no SciPy) so the package stays light, and
are validated against known reference values in the test suite.
"""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pandas as pd

_NORMAL = NormalDist()


# --------------------------------------------------------------------------- #
# Special functions (Lanczos / Numerical Recipes style)
# --------------------------------------------------------------------------- #
_GAMMA_COF = [
    76.18009172947146,
    -86.50532032941677,
    24.01409824083091,
    -1.231739572450155,
    0.1208650973866179e-2,
    -0.5395239384953e-5,
]


def gammaln(xx: float) -> float:
    """Natural log of the gamma function (Lanczos approximation)."""
    x = xx
    y = xx
    tmp = x + 5.5
    tmp -= (x + 0.5) * math.log(tmp)
    ser = 1.000000000190015
    for cof in _GAMMA_COF:
        y += 1.0
        ser += cof / y
    return -tmp + math.log(2.5066282746310005 * ser / x)


def digamma(x: float) -> float:
    """Digamma function ψ(x) for x > 0 (recursion + asymptotic series)."""
    if x <= 0:
        raise ValueError("digamma requires x > 0")
    result = 0.0
    while x < 7.0:
        result -= 1.0 / x
        x += 1.0
    inv = 1.0 / x
    inv2 = inv * inv
    inv4 = inv2 * inv2
    inv6 = inv4 * inv2
    inv8 = inv4 * inv4
    inv10 = inv8 * inv2
    result += (
        math.log(x)
        - 0.5 * inv
        - inv2 / 12.0
        + inv4 / 120.0
        - inv6 / 252.0
        + inv8 / 240.0
        - inv10 * (5.0 / 660.0)
    )
    return result


def trigamma(x: float) -> float:
    """Trigamma function ψ′(x) for x > 0 (recursion + asymptotic series)."""
    if x <= 0:
        raise ValueError("trigamma requires x > 0")
    result = 0.0
    while x < 7.0:
        result += 1.0 / (x * x)
        x += 1.0
    inv = 1.0 / x
    inv2 = inv * inv
    inv3 = inv2 * inv
    inv5 = inv3 * inv2
    inv7 = inv5 * inv2
    inv9 = inv7 * inv2
    inv11 = inv9 * inv2
    return (
        result
        + inv
        + 0.5 * inv2
        + inv3 / 6.0
        - inv5 / 30.0
        + inv7 / 42.0
        - inv9 / 30.0
        + inv11 * (5.0 / 66.0)
    )


def _gser(a: float, x: float, eps: float = 3e-7, itmax: int = 300) -> float:
    """Regularized lower incomplete gamma via series (for x < a + 1)."""
    gln = gammaln(a)
    ap = a
    total = 1.0 / a
    delta = total
    for _ in range(1, itmax + 1):
        ap += 1.0
        delta *= x / ap
        total += delta
        if abs(delta) < abs(total) * eps:
            return total * math.exp(-x + a * math.log(x) - gln)
    raise RuntimeError("gser: series did not converge")


def _gcf(a: float, x: float, eps: float = 3e-7, itmax: int = 300) -> float:
    """Regularized upper incomplete gamma via continued fraction (Q = 1 - P)."""
    gln = gammaln(a)
    b = x + 1.0 - a
    c = 1.0 / 1e-30
    d = 1.0 / b
    h = d
    for i in range(1, itmax + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-30:
            d = 1e-30
        c = b + an / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return math.exp(-x + a * math.log(x) - gln) * h


def gammp(a: float, x: float) -> float:
    """Regularized lower incomplete gamma P(a, x) = γ(a,x)/Γ(a)."""
    if a <= 0:
        raise ValueError("a must be > 0")
    if x < 0:
        raise ValueError("x must be >= 0")
    if x == 0:
        return 0.0
    if x < a + 1.0:
        return _gser(a, x)
    return 1.0 - _gcf(a, x)


# --------------------------------------------------------------------------- #
# Gamma MLE fit
# --------------------------------------------------------------------------- #
def gamma_fit_ml(data) -> tuple[float, float]:
    """Maximum-likelihood gamma fit returning (shape, scale).

    Uses Thom (1958) approximation as the initial guess, refined by
    Newton–Raphson on the digamma/trigamma equations. Zeros are excluded by the
    caller (they are handled separately in the SPI mixed distribution).
    """
    x = np.asarray(data, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        raise ValueError("no finite values to fit")

    mean = float(x.mean())
    positive = x[x > 0]
    if positive.size == 0:
        raise ValueError("all values are zero; cannot fit gamma")
    logmean = float(np.log(positive).mean())

    a_param = math.log(mean) - logmean
    if a_param <= 0:
        # near-zero variance: very large shape (approaches normal)
        return 1e6, mean / 1e6

    shape = (1.0 + math.sqrt(1.0 + 4.0 * a_param / 3.0)) / (4.0 * a_param)
    for _ in range(50):
        f = math.log(shape) - digamma(shape) - a_param
        fp = 1.0 / shape - trigamma(shape)
        if fp == 0:
            break
        shape_new = shape - f / fp
        if shape_new <= 0 or not math.isfinite(shape_new):
            break
        if abs(shape_new - shape) < 1e-8:
            shape = shape_new
            break
        shape = shape_new

    scale = mean / shape
    return float(shape), float(scale)


def gamma_cdf(x: float, shape: float, scale: float) -> float:
    """Gamma cumulative distribution function at x (x >= 0)."""
    if x <= 0:
        return 0.0
    return gammp(shape, x / scale)


# --------------------------------------------------------------------------- #
# SPI estimators
# --------------------------------------------------------------------------- #
def percentile_to_normal_score(p: float) -> float:
    """Map an empirical percentile (0..1) to a standard-normal quantile."""
    if pd.isna(p):
        return float("nan")
    p = min(max(float(p), 1e-3), 1 - 1e-3)
    return _NORMAL.inv_cdf(p)


def spi_from_percentile(p: float) -> float:
    """Non-parametric SPI estimate from an empirical percentile (0..1)."""
    return percentile_to_normal_score(p)


def spi_gamma(series) -> pd.Series:
    """Gamma-distribution SPI (Edwards & McKee 1997).

    Fits a gamma distribution to the non-zero values and uses a mixed
    distribution for zero precipitation: H(x) = q + (1−q)·G(x), with q the
    fraction of zeros. SPI = Φ⁻¹(H(x)). A series with fewer than 2 non-zero
    values yields all-NaN.
    """
    s = pd.Series(series)
    x = s.to_numpy(dtype=float)
    q = float((x == 0).sum()) / len(x) if len(x) else 0.0
    nonzero = x[np.isfinite(x) & (x > 0)]
    if nonzero.size < 2:
        return pd.Series(np.full(len(x), np.nan), index=s.index, name="spi")
    if float(nonzero.std()) < 1e-12:
        # Constant (zero-variance) series: every value is at the median -> SPI 0.
        return pd.Series(np.zeros(len(x)), index=s.index, name="spi")

    shape, scale = gamma_fit_ml(nonzero)
    out = np.empty(len(x), dtype=float)
    for i, val in enumerate(x):
        if not np.isfinite(val):
            out[i] = np.nan
        elif val <= 0:
            out[i] = percentile_to_normal_score(q)
        else:
            p = q + (1.0 - q) * gamma_cdf(val, shape, scale)
            out[i] = percentile_to_normal_score(p)
    return pd.Series(out, index=s.index, name="spi")


def note() -> str:
    return (
        "SPI is a precipitation-only indicator and does not directly measure water "
        "availability. Gamma-distribution SPI (spi_gamma) uses a maximum-likelihood "
        "fit with zero-precipitation handling; a non-parametric normal-score transform "
        "(spi_from_percentile) is also available."
    )
