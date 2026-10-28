"""Atoll/island water-need forecast (modeled water balance).

Deterministic and clearly labeled as a MODELED estimate. It computes, for a
location, the rainfall required to meet a population's water demand over a
forecast horizon and compares it against forecast rainfall to flag a projected
deficit or surplus.

Scientific-integrity rules enforced here:

* Meteorological drought, hydrological stress, reported shortage, and modeled
  future risk are distinct concepts. This module produces *modeled future water
  risk* only — never a claim of actual shortage.
* Assumptions (per-capita demand, catchment area, collection efficiency) are
  documented, configurable planning defaults, NOT measured site data. Missing
  inputs are listed explicitly rather than fabricated.

Units: 1 mm of rain over 1 m² = 1 litre, so ``supply_l = precip_mm * area_m2 * eff``.
"""

from __future__ import annotations

import pandas as pd


def water_demand_lpd(population: int | float, per_capita_lpd: float) -> float:
    """Daily water demand in litres: population × per-capita litres/person/day."""
    return float(population) * float(per_capita_lpd)


def catchment_area_m2(population: int | float, per_person_catchment_m2: float) -> float:
    """Assumed effective rainwater catchment area (m²) for a population."""
    return float(population) * float(per_person_catchment_m2)


def required_rainfall_mm(demand_liters: float, catchment_m2: float, efficiency: float) -> float:
    """Rainfall (mm) needed to satisfy ``demand_liters`` via catchment of ``efficiency``.

    Returns NaN when catchment/efficiency are non-positive.
    """
    if catchment_m2 <= 0 or efficiency <= 0:
        return float("nan")
    return demand_liters / (catchment_m2 * float(efficiency))


def forecast_water_balance(
    population: int | float | None,
    forecast_precip_mm: pd.Series,
    *,
    per_capita_lpd: float,
    per_person_catchment_m2: float,
    collection_efficiency: float,
    horizon_days: int | None = None,
    storage_l: float | None = None,
) -> dict:
    """Compute a modeled water deficit/surplus over a forecast horizon.

    Parameters
    ----------
    population:
        Number of people (None → no-data result).
    forecast_precip_mm:
        Daily forecast precipitation (mm), date-indexed (any timezone; only the
        values matter).
    per_capita_lpd / per_person_catchment_m2 / collection_efficiency:
        Documented planning defaults (see config/freshwater.yaml).
    horizon_days:
        Number of forecast days to use (default: all available).
    storage_l:
        Optional known storage capacity (litres). If absent, storage is treated
        as 0 (conservative) and reported as a missing input.

    Returns
    -------
    dict with population, daily_demand_l, catchment_m2, required_mm,
    forecast_mm, balance_mm, balance_l, verdict, per_day, assumptions,
    missing_inputs, note.
    """
    missing: list[str] = []
    if population is None or population <= 0:
        return {
            "verdict": "no data",
            "missing_inputs": ["population"],
            "note": "No population figure is available for this location.",
            "assumptions": {},
            "per_day": [],
        }

    if forecast_precip_mm is None or len(forecast_precip_mm) == 0:
        return {
            "verdict": "no data",
            "missing_inputs": ["forecast_precipitation"],
            "note": "No forecast precipitation available.",
            "assumptions": {},
            "per_day": [],
        }

    daily_demand = water_demand_lpd(population, per_capita_lpd)
    area = catchment_area_m2(population, per_person_catchment_m2)

    if storage_l is None:
        missing.append("storage_capacity")

    series = forecast_precip_mm.astype(float)
    if horizon_days is not None:
        series = series.iloc[:horizon_days]

    total_forecast_mm = float(series.sum())
    total_demand_l = daily_demand * len(series)
    required_mm = required_rainfall_mm(total_demand_l, area, collection_efficiency)
    balance_mm = total_forecast_mm - required_mm
    balance_l = balance_mm * area * collection_efficiency

    # per-day balance
    per_day = []
    cumulative = 0.0
    for ts, precip in series.items():
        supply_l = precip * area * collection_efficiency
        net_l = supply_l - daily_demand
        cumulative += net_l
        per_day.append(
            {
                "date": str(ts),
                "precip_mm": float(precip),
                "demand_l": round(daily_demand, 0),
                "supply_l": round(supply_l, 0),
                "net_l": round(net_l, 0),
                "cumulative_net_l": round(cumulative, 0),
            }
        )

    tol = 0.01 * required_mm if required_mm and required_mm == required_mm else 1.0
    if balance_mm == balance_mm and abs(balance_mm) <= tol:
        verdict = "balanced"
    elif balance_mm > 0:
        verdict = "surplus"
    else:
        verdict = "deficit"

    return {
        "population": int(population),
        "daily_demand_l": round(daily_demand, 0),
        "catchment_m2": round(area, 0),
        "horizon_days": int(len(series)),
        "required_mm": round(required_mm, 1) if required_mm == required_mm else None,
        "forecast_mm": round(total_forecast_mm, 1),
        "balance_mm": round(balance_mm, 1),
        "balance_l": round(balance_l, 0),
        "verdict": verdict,
        "per_day": per_day,
        "assumptions": {
            "per_capita_lpd": per_capita_lpd,
            "per_person_catchment_m2": per_person_catchment_m2,
            "collection_efficiency": collection_efficiency,
            "storage_l": storage_l,
        },
        "missing_inputs": missing,
        "note": (
            "Modeled water-balance estimate using documented planning defaults, not "
            "measured catchment/storage/desalination data. It indicates projected "
            "rainfall-driven deficit/surplus, NOT an actual water shortage."
        ),
    }


def balance_table(balances: list[dict]) -> pd.DataFrame:
    """Flatten a list of balance dicts (keyed by location) into a DataFrame."""
    rows = []
    for b in balances:
        rows.append(
            {
                "geo_id": b.get("geo_id"),
                "name": b.get("name"),
                "entity_type": b.get("entity_type"),
                "population": b.get("population"),
                "daily_demand_l": b.get("daily_demand_l"),
                "required_mm": b.get("required_mm"),
                "forecast_mm": b.get("forecast_mm"),
                "balance_mm": b.get("balance_mm"),
                "verdict": b.get("verdict"),
            }
        )
    return pd.DataFrame(rows)
