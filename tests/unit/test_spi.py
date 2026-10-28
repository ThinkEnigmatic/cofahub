"""Gamma SPI tests (special functions validated against reference values)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from cofa_forward.drought.spi import (
    digamma,
    gamma_fit_ml,
    gammaln,
    gammp,
    spi_gamma,
    trigamma,
)


# ---- special-function reference values ---- #
def test_gammaln_reference():
    assert math.isclose(gammaln(1.0), 0.0, abs_tol=1e-10)
    assert math.isclose(gammaln(0.5), 0.5723649429247001, rel_tol=1e-8)
    assert math.isclose(gammaln(5.0), math.log(24.0), rel_tol=1e-8)


def test_digamma_reference():
    assert math.isclose(digamma(1.0), -0.5772156649015329, rel_tol=1e-7)
    assert math.isclose(digamma(0.5), -1.9635100260214235, rel_tol=1e-6)
    assert math.isclose(digamma(10.0), 2.2517525890667214, rel_tol=1e-7)


def test_trigamma_reference():
    assert math.isclose(trigamma(1.0), math.pi**2 / 6.0, rel_tol=1e-7)


def test_gammp_reference():
    assert math.isclose(gammp(1.0, 1.0), 1 - math.exp(-1), rel_tol=1e-6)
    assert math.isclose(gammp(0.5, 1.0), math.erf(1.0), rel_tol=1e-5)
    assert math.isclose(gammp(2.0, 1.0), 1 - 2 * math.exp(-1), rel_tol=1e-6)


def test_gammp_boundaries():
    assert gammp(1.0, 0.0) == 0.0
    assert math.isclose(gammp(5.0, 1e6), 1.0, rel_tol=1e-6)


# ---- gamma MLE fit ---- #
def test_gamma_fit_recovers_parameters():
    rng = np.random.default_rng(42)
    data = rng.gamma(shape=3.0, scale=2.0, size=20000)
    shape, scale = gamma_fit_ml(data)
    assert abs(shape - 3.0) / 3.0 < 0.05
    assert abs(scale - 2.0) / 2.0 < 0.05


def test_gamma_fit_raises_on_all_zeros():
    with pytest.raises(ValueError):
        gamma_fit_ml(np.zeros(10))


# ---- SPI ---- #
def test_spi_gamma_constant_series_is_zero():
    s = pd.Series([10.0] * 100)
    spi = spi_gamma(s)
    assert np.allclose(spi.to_numpy(), 0.0, atol=1e-6)


def test_spi_gamma_zero_precipitation_handling():
    # 30% zeros, rest clearly wet values
    rng = np.random.default_rng(0)
    wet = rng.gamma(2.0, 20.0, 70)
    data = np.concatenate([np.zeros(30), wet])
    s = pd.Series(data)
    spi = spi_gamma(s)
    # zero-precipitation entries map to the zero-quantile (SPI < 0, finite)
    zero_spi = spi.to_numpy()[:30]
    assert np.all(np.isfinite(zero_spi))
    assert np.all(zero_spi < 0.0)


def test_spi_gamma_too_few_nonzero_returns_nan():
    s = pd.Series([0.0, 0.0, 0.0, 1.0, 0.0])
    spi = spi_gamma(s)
    assert spi.isna().all()


def test_spi_gamma_returns_series():
    s = pd.Series(np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]))
    spi = spi_gamma(s)
    assert isinstance(spi, pd.Series)
    assert len(spi) == 6
