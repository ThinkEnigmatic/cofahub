"""Hargreaves PET + meteorological water-balance tests."""

from __future__ import annotations

import pandas as pd

from cofa_forward.drought.pet import (
    extraterrestrial_radiation_mm,
    hargreaves_pet_daily,
    water_balance_monthly,
)


def test_extraterrestrial_radiation_reasonable():
    # At the equator, Ra is ~15 mm/day (water-equivalent) year-round; at 7°N it
    # stays in a tight tropical band. Values must be positive and plausible.
    for doy in (1, 90, 180, 270, 360):
        ra = extraterrestrial_radiation_mm(7.0, doy)
        assert 10.0 < ra < 18.0


def test_extraterrestrial_radiation_higher_lat_less_extreme():
    # Higher latitude has a wider seasonal swing but stays positive.
    ra = extraterrestrial_radiation_mm(45.0, 172)
    assert ra > 0


def test_hargreaves_pet_daily_tropical():
    idx = pd.date_range("2020-01-01", periods=10, freq="D")
    tmax = pd.Series([30.0] * 10, index=idx)
    tmin = pd.Series([24.0] * 10, index=idx)
    pet = hargreaves_pet_daily(tmax, tmin, 7.0)
    # Tropical PET ~3-7 mm/day.
    assert pet.between(2.0, 8.0).all()


def test_hargreaves_pet_zero_diurnal_range():
    # When Tmax == Tmin, the sqrt term is 0 -> PET 0 (no missing-data crash).
    idx = pd.date_range("2020-01-01", periods=3, freq="D")
    pet = hargreaves_pet_daily(
        pd.Series([28.0] * 3, index=idx), pd.Series([28.0] * 3, index=idx), 7.0
    )
    assert (pet == 0.0).all()


def test_water_balance_monthly_shape():
    idx = pd.date_range("2020-01-01", periods=90, freq="D")
    precip = pd.Series([8.0] * 90, index=idx)
    tmax = pd.Series([30.0] * 90, index=idx)
    tmin = pd.Series([24.0] * 90, index=idx)
    wb = water_balance_monthly(precip, tmax, tmin, 7.0)
    assert set(wb.columns) == {"precip_mm", "pet_mm", "balance_mm"}
    # balance = P - PET, so precip_mm - pet_mm == balance_mm.
    assert (wb["balance_mm"] - (wb["precip_mm"] - wb["pet_mm"])).abs().max() < 1e-6
    # 8 mm/day rain vs ~5 mm/day PET -> surplus.
    assert (wb["balance_mm"] > 0).all()
