"""Forecast verification tests."""

from __future__ import annotations

import math

import pandas as pd

from cofa_forward.intelligence.verification import (
    bias,
    mae,
    pearson,
    rmse,
    verify,
)


def _pair():
    idx = pd.date_range("2026-01-01", periods=5, freq="D")
    obs = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx)
    fcst = pd.Series([1.0, 2.0, 3.0, 4.0, 6.0], index=idx)  # last point off by +1
    return obs, fcst


def test_bias():
    obs, fcst = _pair()
    assert math.isclose(bias(obs, fcst), 0.2)  # mean error = 1/5


def test_mae():
    obs, fcst = _pair()
    assert math.isclose(mae(obs, fcst), 0.2)


def test_rmse():
    obs, fcst = _pair()
    assert math.isclose(rmse(obs, fcst), math.sqrt(0.2))


def test_pearson_high_when_linear():
    obs, fcst = _pair()
    assert pearson(obs, fcst) > 0.98


def test_verify_time_matches_only():
    obs = pd.Series([1.0, 2.0, 3.0], index=pd.date_range("2026-01-01", periods=3))
    fcst = pd.Series([9.0, 9.0], index=pd.date_range("2026-01-02", periods=2))
    res = verify(obs, fcst)
    assert res["n"] == 2  # only overlapping dates are compared


def test_verify_no_overlap():
    obs = pd.Series([1.0], index=pd.date_range("2026-01-01", periods=1))
    fcst = pd.Series([1.0], index=pd.date_range("2026-02-01", periods=1))
    res = verify(obs, fcst)
    assert res["n"] == 0
    assert "no time-matched" in res["note"]


def test_verify_skill_score():
    obs = pd.Series([10.0, 10.0, 10.0, 10.0], index=pd.date_range("2026-01-01", periods=4))
    perfect = pd.Series([10.0, 10.0, 10.0, 10.0], index=obs.index)
    res = verify(obs, perfect, climatology=12.0)
    assert res["rmse"] == 0.0
    assert res["skill_score"] == 1.0
