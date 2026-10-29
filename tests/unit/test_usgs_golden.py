"""Golden cross-check: reproduce the USGS R-script classification verbatim.

Transcribes the exact logic of ``3_IMERG_Monthly_Drought_Monitor.R`` (Senay et
al. 2026, DOI 10.5066/P1RXUMV3) into Python, and asserts that the app's
``classify_quintile`` / ``peac_index`` / ``drought_monitor_status`` reproduce the
R results exactly.

Key transcription notes:
* R ``quantile(x, probs=c(.2,.4,.6,.8))`` uses the default type-7 (Hyndman-Fan)
  interpolation == pandas ``.quantile(interpolation="linear")``.
* R ``if/else`` chain for the Rainfall Index and ``case_when`` for PEAC are
  reproduced 1:1.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cofa_forward.drought.monitor import drought_monitor_status
from cofa_forward.drought.percentiles import classify_quintile, peac_index

# --- The R script's logic, transcribed literally ----------------------------


def _r_quantile(x, probs):
    return np.quantile(x, probs, method="linear")


def _r_rain_index(value, hist_vals):
    """R: q1 <- quantile(hist_vals, c(.2,.4,.6,.8)); if/else chain."""
    q = _r_quantile(hist_vals, [0.2, 0.4, 0.6, 0.8])
    if value < q[0]:
        return "Drier"
    if value < q[1]:
        return "Dry"
    if value < q[2]:
        return "Typical"
    if value < q[3]:
        return "Wet"
    return "Wetter"


def _r_peac(value):
    """R: case_when(is.na(v)~NA, v<101.6~'Red', v<=203.2~'Yellow', TRUE~'Dark Green')."""
    if pd.isna(value):
        return None
    if value < 101.6:
        return "Red"
    if value <= 203.2:
        return "Yellow"
    return "Dark Green"


# --- Tests ------------------------------------------------------------------


@pytest.mark.parametrize("value", [50.0, 100.0, 101.5, 101.6, 150.0, 203.2, 203.3, 400.0])
def test_peac_index_matches_r(value):
    assert peac_index(value) == _r_peac(value)


@pytest.mark.parametrize(
    "value",
    [0.0, 1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 500.0],
)
def test_classify_quintile_matches_r(value):
    # A 25-value historical distribution (25 years of one calendar month).
    hist = pd.Series(np.linspace(10.0, 490.0, 25))
    assert classify_quintile(value, hist) == _r_rain_index(value, hist.values)


def test_classify_quintile_boundary_uses_type7_interpolation():
    # A distribution where the type-7 20th percentile lands BETWEEN two order
    # statistics — a value at exactly that interpolation point must classify the
    # same way as R, not as a naive rank would.
    hist = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    # R type-7 Q20 of 1..5: h = (5-1)*0.2+1 = 1.8 -> interpolate x_1=1, x_2=2 -> 1.8
    q20 = float(pd.Series(hist).quantile(0.2, interpolation="linear"))
    assert np.isclose(q20, 1.8)
    assert classify_quintile(1.5, hist) == "Drier"  # 1.5 < 1.8
    assert classify_quintile(2.0, hist) == "Dry"  # 2.0 >= 1.8


def test_monitor_matches_r_on_constructed_series():
    # Build a daily series whose latest month is a known low value, then compare
    # the monitor's 1-month Rainfall Index + PEAC index to the R transcription.
    idx = pd.date_range("2020-01-01", periods=3 * 365, freq="D")
    vals = [5.0] * len(idx)
    # Last month very dry (10 mm total) but last month is October.
    for i in range(len(idx) - 31, len(idx)):
        vals[i] = 10.0 / 31.0  # ~10 mm over the month
    daily = pd.Series(vals, index=idx, dtype=float)
    status = drought_monitor_status(daily, baseline_start="2020-01-01", baseline_end="2022-12-31")
    latest = status["monthly_mm"]
    # PEAC index must match R exactly for the latest month's total.
    assert status["peac_index"] == _r_peac(latest)
    # 1-month Rainfall Index: recompute the per-month distribution from the
    # series and compare to the R transcription.
    monthly = daily.resample("ME").sum()
    hist = monthly[monthly.index.month == monthly.index[-1].month].dropna().iloc[:-1]
    assert status["rain_index_1m"] == _r_rain_index(latest, hist.values)
