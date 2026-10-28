"""Anomaly and baseline-validity tests."""

from __future__ import annotations

import math

import pandas as pd

from cofa_forward.drought import anomalies


def _monthly(years=30):
    """Flat monthly series of 100 mm/month for 'years' years."""
    idx = pd.date_range("1991-01-01", periods=years * 12, freq="MS")
    return pd.Series([100.0] * len(idx), index=idx)


def test_climatology_is_mean_per_month():
    monthly = _monthly(30)
    clim = anomalies.monthly_climatology(monthly, "1991-01-01", "2020-12-31")
    assert len(clim) == 12
    assert all(math.isclose(v, 100.0) for v in clim)


def test_anomaly_zero_when_matches_climatology():
    monthly = _monthly(30)
    clim = anomalies.monthly_climatology(monthly, "1991-01-01", "2020-12-31")
    anom = anomalies.anomaly(monthly, clim, 15, "1991-01-01", "2020-12-31")
    assert all(math.isclose(v, 0.0) for v in anom.dropna())


def test_anomaly_detects_deviation():
    baseline = _monthly(30)  # 1991-01..2020-12, all 100 mm
    clim = anomalies.monthly_climatology(baseline, "1991-01-01", "2020-12-31")
    extra = pd.Series([150.0], index=pd.DatetimeIndex([pd.Timestamp("2021-01-01")]))
    full = pd.concat([baseline, extra])
    anom = anomalies.anomaly(full, clim, 15, "1991-01-01", "2020-12-31")
    assert math.isclose(anom.loc["2021-01-01"], 50.0, rel_tol=1e-6)


def test_baseline_invalid_rejects_anomaly():
    # only 3 years of data -> below min_years=15
    idx = pd.date_range("2018-01-01", periods=3 * 12, freq="MS")
    monthly = pd.Series([100.0] * len(idx), index=idx)
    clim = anomalies.monthly_climatology(monthly, "2018-01-01", "2020-12-31")
    assert not anomalies.baseline_is_valid(monthly, "2018-01-01", "2020-12-31", 15)
    anom = anomalies.anomaly(monthly, clim, 15, "2018-01-01", "2020-12-31")
    assert anom.isna().all()


def test_anomaly_percent():
    baseline = _monthly(30)
    clim = anomalies.monthly_climatology(baseline, "1991-01-01", "2020-12-31")
    extra = pd.Series([150.0], index=pd.DatetimeIndex([pd.Timestamp("2021-01-01")]))
    full = pd.concat([baseline, extra])
    pct = anomalies.anomaly_percent(full, clim, 15, "1991-01-01", "2020-12-31")
    assert math.isclose(pct.loc["2021-01-01"], 50.0, rel_tol=1e-6)
