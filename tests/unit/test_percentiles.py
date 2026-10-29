"""Empirical percentile and SPI (normal-score) tests."""

from __future__ import annotations

import math

import pandas as pd

from cofa_forward.drought.percentiles import (
    category_from_percentile,
    drought_level,
    empirical_percentile,
    monthly_percentiles,
    quintile_index,
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


def test_drought_level():
    assert drought_level(0.01) == "D4"
    assert drought_level(0.03) == "D3"
    assert drought_level(0.07) == "D2"
    assert drought_level(0.15) == "D1"
    assert drought_level(0.25) == "D0"
    assert drought_level(0.5) is None  # not in drought
    assert drought_level(float("nan")) is None


def test_drought_level_bands():
    assert drought_level(0.01) == "D4"
    assert drought_level(0.03) == "D3"
    assert drought_level(0.07) == "D2"
    assert drought_level(0.15) == "D1"
    assert drought_level(0.25) == "D0"
    assert drought_level(0.5) is None
    assert drought_level(float("nan")) is None


def test_quintile_index_bands():
    assert quintile_index(0.05) == "Drier"
    assert quintile_index(0.20) == "Dry"
    assert quintile_index(0.39) == "Dry"
    assert quintile_index(0.40) == "Typical"
    assert quintile_index(0.59) == "Typical"
    assert quintile_index(0.60) == "Wet"
    assert quintile_index(0.79) == "Wet"
    assert quintile_index(0.80) == "Wetter"
    assert quintile_index(0.99) == "Wetter"
    assert quintile_index(1.0) == "Wetter"
    assert quintile_index(float("nan")) is None


def test_peac_index_thresholds():
    from cofa_forward.drought.percentiles import peac_index

    assert peac_index(50.0) == "Red"  # < 101.6 mm (4 in)
    assert peac_index(101.5) == "Red"
    assert peac_index(101.6) == "Yellow"  # 101.6-203.2 (4-8 in)
    assert peac_index(150.0) == "Yellow"
    assert peac_index(203.2) == "Yellow"  # <= 203.2
    assert peac_index(203.3) == "Dark Green"  # > 203.2 mm (8 in)
    assert peac_index(float("nan")) is None
