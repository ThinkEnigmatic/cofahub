"""Drought monitor (USGS western-Pacific method) tests."""

from __future__ import annotations

import pandas as pd

from cofa_forward.drought.monitor import drought_monitor_status


def _daily(years: int = 3, mm_per_day: float = 5.0) -> pd.Series:
    idx = pd.date_range("2020-01-01", periods=years * 365, freq="D")
    # Deterministic seasonal rainfall: 5 mm/day base + seasonal sine.
    seasonal = 5.0 + 3.0 * pd.Series(
        [((i % 365) / 365.0) * 6.28 for i in range(len(idx))], index=idx
    ).apply(lambda x: __import__("math").sin(x))
    return (mm_per_day + seasonal).rename("precip_mm")


def test_drought_monitor_status_fields():
    daily = _daily()
    status = drought_monitor_status(daily, baseline_start="2020-01-01", baseline_end="2022-12-31")
    assert status["latest_month"] is not None
    assert status["monthly_mm"] > 0
    assert status["clim_median_mm"] > 0
    assert status["percentile"] is not None
    assert status["quintile"] in ("Drier", "Dry", "Typical", "Wet", "Wetter")
    assert status["d0_d4"] in ("D0", "D1", "D2", "D3", "D4", None)
    assert status["peac_index"] in ("Red", "Yellow", "Dark Green")
    assert status["rain_index_1m"] in ("Drier", "Dry", "Typical", "Wet", "Wetter")
    # Rolling totals + 3-/6-month Rainfall Indices present.
    for w in (1, 3, 6):
        assert status.get(f"rain_{w}m_mm") is not None
    for w in (3, 6):
        assert status.get(f"rain_index_{w}m") in ("Drier", "Dry", "Typical", "Wet", "Wetter")


def test_drought_monitor_empty_series():
    daily = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    status = drought_monitor_status(daily)
    assert status["latest_month"] is None
    assert status["quintile"] is None
    assert status["d0_d4"] is None
    assert status["monthly_mm"] is None


def test_drought_monitor_dry_quintile():
    # A series whose final month is far below the baseline should classify Drier/D0+.
    idx = pd.date_range("2020-01-01", periods=3 * 365, freq="D")
    vals = [5.0] * len(idx)
    # Make the last month very dry.
    for i in range(len(idx) - 30, len(idx)):
        vals[i] = 0.5
    daily = pd.Series(vals, index=idx, dtype=float)
    status = drought_monitor_status(daily, baseline_start="2020-01-01", baseline_end="2022-12-31")
    assert status["quintile"] in ("Drier", "Dry")
    assert status["d0_d4"] in ("D1", "D2", "D3", "D4")
