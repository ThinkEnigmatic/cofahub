"""Potential evapotranspiration (Hargreaves) and the meteorological water balance.

Drought is a *water balance* (precipitation minus evapotranspiration), not just
rainfall. This module computes daily Hargreaves (1985) potential
evapotranspiration from temperature alone — the standard temperature-based PET
for data-sparse settings — and the resulting ``P − PET`` water balance.

Hargreaves PET = 0.0023 × Ra × (Tmean + 17.8) × √(Tmax − Tmin), where Ra is the
extraterrestrial radiation (mm/day water-equivalent) for the latitude and day of
year. PET is *potential* ET (the atmospheric demand); actual ET is lower when
water is scarce (the USGS SSEBop product, available 2003–2021, would supply that
— see docs/analysis-roadmap.md).
"""

from __future__ import annotations

import math

import pandas as pd


def extraterrestrial_radiation_mm(lat_deg: float, doy: int) -> float:
    """Daily extraterrestrial radiation (mm/day water-equivalent) at a latitude.

    Standard solar-geometry (Allen et al. 1998): inverse Earth–Sun distance,
    solar declination, and sunset hour angle, with the solar constant converted
    from MJ/m²/day to mm/day via ×0.408.
    """
    phi = math.radians(lat_deg)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * doy / 365.0)
    delta = 0.409 * math.sin(2.0 * math.pi * doy / 365.0 - 1.39)
    cos_ws = -math.tan(phi) * math.tan(delta)
    cos_ws = max(-1.0, min(1.0, cos_ws))  # clamp for polar day/night
    ws = math.acos(cos_ws)
    ra_mj = (
        (24.0 * 60.0 / math.pi)
        * 0.0820
        * dr
        * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))
    )
    return 0.408 * ra_mj  # mm/day


def hargreaves_pet_daily(tmax_c: pd.Series, tmin_c: pd.Series, lat_deg: float) -> pd.Series:
    """Daily Hargreaves PET (mm/day) from daily Tmax/Tmin (°C), date-indexed.

    Requires a ``DatetimeIndex`` (used only for the day-of-year, so timezone is
    irrelevant). Missing temperature yields NaN PET.
    """
    if not isinstance(tmax_c.index, pd.DatetimeIndex):
        raise TypeError("tmax_c must have a DatetimeIndex")
    doy = tmax_c.index.day_of_year
    ra = pd.Series([extraterrestrial_radiation_mm(lat_deg, d) for d in doy], index=tmax_c.index)
    tmean = (tmax_c + tmin_c) / 2.0
    td = (tmax_c - tmin_c).clip(lower=0.0)
    return 0.0023 * ra * (tmean + 17.8) * (td**0.5)


def water_balance_monthly(
    precip_mm: pd.Series,
    tmax_c: pd.Series,
    tmin_c: pd.Series,
    lat_deg: float,
) -> pd.DataFrame:
    """Monthly water balance = precipitation − PET (mm), date-indexed by month-end.

    Returns a DataFrame with ``precip_mm``, ``pet_mm`` and ``balance_mm`` columns.
    A positive balance is a water surplus, negative a deficit. This is a
    *meteorological* water balance — it ignores soil/groundwater storage, runoff,
    and human abstraction, and PET overstates actual ET in dry conditions.
    """
    pet = hargreaves_pet_daily(tmax_c, tmin_c, lat_deg)
    p = precip_mm.resample("ME").sum(min_count=1)
    e = pet.resample("ME").sum(min_count=1)
    return pd.DataFrame({"precip_mm": p, "pet_mm": e, "balance_mm": p - e})
