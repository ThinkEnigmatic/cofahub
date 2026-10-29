"""Coral-bleaching risk from sea-surface temperature (Degree Heating Weeks).

The reef-dependent FAS economies depend on coral. NOAA Coral Reef Watch defines
**Degree Heating Weeks (DHW)** as the accumulated temperature anomaly above the
bleaching threshold (the local **MMM** — maximum monthly mean SST — plus 1 °C)
over a trailing 12-week window, expressed in °C-weeks.

This module is a **simplified watch**, not the official NOAA CRW product: it uses
a fixed ``mmm_c`` for the western Pacific (~29.0 °C) instead of the per-pixel MMM
climatology. The alert levels below are the standard NOAA CRW DHW thresholds.
"""

from __future__ import annotations

import pandas as pd


def degree_heating_weeks(
    sst_daily: pd.Series, mmm_c: float = 29.0, weeks: int = 12
) -> float | None:
    """Simplified Degree Heating Weeks from a daily-SST series (°C).

    DHW = Σ max(0, SST − (MMM + 1 °C)) over the trailing ``weeks``, divided by 7.
    Returns None when there are fewer than ``weeks * 7`` valid observations.
    """
    s = sst_daily.dropna()
    needed = weeks * 7
    if len(s) < needed:
        return None
    window = s.iloc[-needed:]
    anomaly = (window - (mmm_c + 1.0)).clip(lower=0.0)
    return float(anomaly.sum() / 7.0)


def bleaching_alert(dhw: float | None) -> str | None:
    """Map a DHW value to the NOAA Coral Reef Watch alert level.

    Thresholds (°C-weeks): <4 No Stress, 4–8 Watch, 8–12 Warning (bleaching
    likely), 12–20 Alert Level 1 (significant), ≥20 Alert Level 2 (severe).
    """
    if dhw is None:
        return None
    if dhw < 4.0:
        return "No Stress"
    if dhw < 8.0:
        return "Watch"
    if dhw < 12.0:
        return "Warning (bleaching likely)"
    if dhw < 20.0:
        return "Alert Level 1 (significant bleaching)"
    return "Alert Level 2 (severe bleaching/mortality)"
