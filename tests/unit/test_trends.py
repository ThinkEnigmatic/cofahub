"""Climate trend estimators (linear, Theil-Sen, Mann-Kendall) tests."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from cofa_forward.climate.trends import (
    linear_trend,
    mann_kendall,
    theil_sen_slope,
    trend_summary,
)


def _series(slope: float, n: int = 40, noise: float = 0.0, start="1980-01-01"):
    idx = pd.date_range(start, periods=n, freq="YS")
    y = slope * np.arange(n) + np.random.default_rng(0).normal(0, noise, n)
    return pd.Series(y, index=idx)


def test_linear_trend_recovers_slope():
    s = _series(slope=2.0, noise=0.0)
    slope, _ = linear_trend(s)
    assert math.isclose(slope, 2.0, rel_tol=1e-6)


def test_linear_trend_insufficient_points():
    s = _series(slope=1.0, n=5)
    slope, intercept = linear_trend(s, min_points=10)
    assert math.isnan(slope) and math.isnan(intercept)


def test_theil_sen_slope_robust():
    s = _series(slope=1.0, n=30, noise=0.5)
    sen = theil_sen_slope(s)
    assert math.isclose(sen, 1.0, abs_tol=0.3)


def test_mann_kendall_increasing():
    s = _series(slope=2.0, n=30, noise=0.1)
    mk = mann_kendall(s)
    assert mk["trend"] == "increasing"
    assert mk["tau"] > 0.9
    assert mk["p_value"] < 0.01


def test_mann_kendall_no_trend():
    s = _series(slope=0.0, n=40, noise=5.0)
    mk = mann_kendall(s)
    assert mk["trend"] == "no trend"


def test_mann_kendall_decreasing():
    s = _series(slope=-1.5, n=30, noise=0.1)
    assert mann_kendall(s)["trend"] == "decreasing"


def test_trend_summary_shape():
    s = _series(slope=1.0, n=20, noise=0.2)
    ts = trend_summary(s, "rainfall", "mm")
    assert ts["name"] == "rainfall"
    assert ts["unit"] == "mm"
    assert ts["n_points"] == 20
    assert ts["slope_per_decade"] == ts["slope_per_year"] * 10
    assert ts["verdict"] == "increasing"
