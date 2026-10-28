"""Water-balance (water-need forecast) tests."""

from __future__ import annotations

import math

import pandas as pd

from cofa_forward.drought.water_balance import (
    catchment_area_m2,
    forecast_water_balance,
    required_rainfall_mm,
    water_demand_lpd,
)


def _forecast(mm_list):
    return pd.Series(mm_list, index=pd.date_range("2026-10-28", periods=len(mm_list), freq="D"))


def test_water_demand():
    assert water_demand_lpd(100, 100.0) == 10000.0


def test_catchment_area():
    assert catchment_area_m2(100, 10.0) == 1000.0


def test_required_rainfall_mm():
    # 1000 people × 100 L/person/day × 7 days = 700,000 L over 7 days
    demand = 700000.0
    area = 1000 * 10.0  # 1000 people × 10 m2
    mm = required_rainfall_mm(demand, area, 0.8)
    assert math.isclose(mm, demand / (area * 0.8))


def test_required_rainfall_invalid_returns_nan():
    assert math.isnan(required_rainfall_mm(100.0, 0.0, 0.8))
    assert math.isnan(required_rainfall_mm(100.0, 10.0, 0.0))


def test_balance_surplus():
    # constant 10 mm/day over 7 days, high population demand
    b = forecast_water_balance(
        100,
        _forecast([10.0] * 7),
        per_capita_lpd=100.0,
        per_person_catchment_m2=10.0,
        collection_efficiency=0.8,
    )
    # daily supply = 10 mm * (100*10 m2) * 0.8 = 8000 L; demand = 10000 L -> deficit
    assert b["verdict"] == "deficit"
    assert b["forecast_mm"] == 70.0
    assert b["required_mm"] == 87.5  # 700000 / (1000*0.8)
    assert b["balance_mm"] == 70.0 - 87.5
    assert len(b["per_day"]) == 7
    assert b["missing_inputs"] == ["storage_capacity"]


def test_balance_deficit():
    b = forecast_water_balance(
        100,
        _forecast([2.0] * 7),
        per_capita_lpd=100.0,
        per_person_catchment_m2=10.0,
        collection_efficiency=0.8,
    )
    assert b["verdict"] == "deficit"
    assert b["balance_mm"] < 0


def test_balance_no_population():
    b = forecast_water_balance(
        None,
        _forecast([10.0]),
        per_capita_lpd=100.0,
        per_person_catchment_m2=10.0,
        collection_efficiency=0.8,
    )
    assert b["verdict"] == "no data"
    assert "population" in b["missing_inputs"]


def test_balance_no_forecast():
    b = forecast_water_balance(
        100,
        pd.Series(dtype=float),
        per_capita_lpd=100.0,
        per_person_catchment_m2=10.0,
        collection_efficiency=0.8,
    )
    assert b["verdict"] == "no data"


def test_balance_horizon_days():
    b = forecast_water_balance(
        100,
        _forecast([5.0] * 10),
        per_capita_lpd=100.0,
        per_person_catchment_m2=10.0,
        collection_efficiency=0.8,
        horizon_days=3,
    )
    assert b["horizon_days"] == 3
    assert b["forecast_mm"] == 15.0


def test_balance_storage_recorded():
    b = forecast_water_balance(
        100,
        _forecast([5.0] * 3),
        per_capita_lpd=100.0,
        per_person_catchment_m2=10.0,
        collection_efficiency=0.8,
        storage_l=50000,
    )
    assert b["missing_inputs"] == []
    assert b["assumptions"]["storage_l"] == 50000
