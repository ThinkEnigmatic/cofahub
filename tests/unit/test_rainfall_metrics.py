"""Rainfall accumulation / rolling-total tests (missing data never becomes zero)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from cofa_forward.drought.rainfall_metrics import monthly_totals, rolling_totals


def _daily():
    idx = pd.date_range("2020-01-01", "2020-03-31", freq="D")
    # 1 mm/day => Jan 31, Feb 29, Mar 31
    return pd.Series([1.0] * len(idx), index=idx, name="precip_mm")


def test_monthly_totals_known():
    monthly = monthly_totals(_daily())
    assert math.isclose(monthly.iloc[0], 31.0)
    assert math.isclose(monthly.iloc[1], 29.0)
    assert math.isclose(monthly.iloc[2], 31.0)


def test_rolling_totals_known():
    rolling = rolling_totals(_daily(), windows=(1, 3))
    # 3-month total over full Jan-Mar = 91
    assert math.isclose(rolling["rain_3m_mm"].iloc[-1], 91.0)
    assert math.isclose(rolling["rain_1m_mm"].iloc[-1], 31.0)


def test_missing_days_do_not_become_zero():
    idx = pd.date_range("2020-01-01", "2020-02-29", freq="D")
    daily = pd.Series(1.0, index=idx)
    feb = idx[(idx >= "2020-02-01") & (idx <= "2020-02-29")]
    daily = daily.drop(feb[10:])  # only 10 February days remain
    monthly = monthly_totals(daily, min_days_frac=0.8)
    # January complete -> 31; February incomplete (10/29 < 0.8) -> NaN
    assert math.isclose(monthly.iloc[0], 31.0)
    assert pd.isna(monthly.iloc[1])


def test_rolling_spanning_missing_month_is_nan():
    idx = pd.date_range("2020-01-01", "2020-03-31", freq="D")
    daily = pd.Series(1.0, index=idx)
    feb = idx[(idx >= "2020-02-01") & (idx <= "2020-02-29")]
    daily = daily.drop(feb[10:])  # Feb has only 10 days -> invalid month
    rolling = rolling_totals(daily, windows=(3,), min_days_frac=0.8)
    # 3-month rolling total spanning the invalid February must be NaN
    assert pd.isna(rolling["rain_3m_mm"].iloc[-1])


def test_requires_datetime_index():
    with pytest.raises(TypeError):
        monthly_totals(pd.Series([1.0, 2.0]))
