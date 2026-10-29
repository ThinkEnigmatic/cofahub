"""Degree Heating Weeks / coral-bleaching watch tests."""

from __future__ import annotations

import pandas as pd

from cofa_forward.climate.bleaching import bleaching_alert, degree_heating_weeks


def _sst(values: list[float]) -> pd.Series:
    idx = pd.date_range("2026-08-01", periods=len(values), freq="D")
    return pd.Series(values, index=idx)


def test_degree_heating_weeks_no_stress():
    # All SST below the bleaching threshold (29+1=30 C) -> DHW 0.
    s = _sst([29.0] * 90)
    assert degree_heating_weeks(s) == 0.0
    assert bleaching_alert(degree_heating_weeks(s)) == "No Stress"


def test_degree_heating_weeks_accumulates():
    # 31 C for the whole 12 weeks -> 1 C/day * 84 days / 7 = 12 C-weeks.
    s = _sst([31.0] * 84)
    dhw = degree_heating_weeks(s)
    assert abs(dhw - 12.0) < 1e-6
    assert bleaching_alert(dhw) == "Alert Level 1 (significant bleaching)"


def test_degree_heating_weeks_insufficient():
    s = _sst([31.0] * 10)
    assert degree_heating_weeks(s) is None
    assert bleaching_alert(None) is None


def test_bleaching_alert_levels():
    assert bleaching_alert(2.0) == "No Stress"
    assert bleaching_alert(5.0) == "Watch"
    assert bleaching_alert(9.0) == "Warning (bleaching likely)"
    assert bleaching_alert(15.0) == "Alert Level 1 (significant bleaching)"
    assert bleaching_alert(25.0) == "Alert Level 2 (severe bleaching/mortality)"
