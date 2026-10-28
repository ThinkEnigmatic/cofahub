"""Empirical percentile and SPI (normal-score) tests."""

from __future__ import annotations

import math

import pandas as pd

from cofa_forward.drought.percentiles import (
    category_from_percentile,
    empirical_percentile,
    monthly_percentiles,
)
from cofa_forward.drought.spi import percentile_to_normal_score


def test_empirical_percentile_midpoint():
    dist = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    assert math.isclose(empirical_percentile(3.0, dist), 0.5)
    assert math.isclose(empirical_percentile(1.0, dist), 0.1)
    assert math.isclose(empirical_percentile(5.0, dist), 0.9)


def test_empirical_percentile_ignores_nan():
    dist = pd.Series([1.0, 2.0, None, 3.0, 4.0, 5.0])
    assert math.isclose(empirical_percentile(3.0, dist), 0.5)


def test_empirical_percentile_empty_is_nan():
    assert pd.isna(empirical_percentile(1.0, pd.Series(dtype=float)))


def test_monthly_percentiles_basic():
    idx = pd.date_range("1991-01-01", periods=24, freq="MS")
    monthly = pd.Series(list(range(24)), index=idx, dtype=float)
    pct = monthly_percentiles(monthly, "1991-01-01", "1993-12-31")
    assert len(pct) == 24
    assert all(0.0 <= v <= 1.0 for v in pct.dropna())


def test_category_bins():
    cats = [
        {"min": 0.0, "max": 0.1, "label": "Extreme dry"},
        {"min": 0.1, "max": 0.2, "label": "Severe dry"},
        {"min": 0.2, "max": 0.8, "label": "Near normal"},
        {"min": 0.8, "max": 1.01, "label": "Wet"},
    ]
    assert category_from_percentile(0.05, cats) == "Extreme dry"
    assert category_from_percentile(0.15, cats) == "Severe dry"
    assert category_from_percentile(0.5, cats) == "Near normal"
    assert category_from_percentile(float("nan"), cats) == "no data"


def test_normal_score():
    assert math.isclose(percentile_to_normal_score(0.5), 0.0, abs_tol=1e-6)
    assert math.isclose(percentile_to_normal_score(0.975), 1.96, abs_tol=0.01)
    assert math.isclose(percentile_to_normal_score(0.025), -1.96, abs_tol=0.01)
    assert pd.isna(percentile_to_normal_score(float("nan")))
