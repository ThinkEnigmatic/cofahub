"""Explicit, tested unit conversions.

Scientific calculations are always performed in metric (SI). Imperial units are a
presentation-only preference. Every conversion factor here is explicit and
covered by tests.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class _Factor:
    to_metric: float  # multiply imperial value by this to get metric
    metric: str
    imperial: str


# Registry: metric_unit -> (imperial_unit, factor from imperial to metric)
_REGISTRY: dict[str, _Factor] = {
    "°C": _Factor(1.8, "°C", "°F"),  # handled specially (offset), kept for naming
    "mm": _Factor(1 / 25.4, "mm", "in"),
    "m/s": _Factor(0.514444, "m/s", "knots"),
    "km": _Factor(1 / 1.609344, "km", "mi"),
    "km/h": _Factor(1 / 1.609344, "km/h", "mph"),
    "hPa": _Factor(1 / 33.8639, "hPa", "inHg"),
}

_LINEAR_OFFSETS: dict[str, float] = {}


def _linear(metric_value: float, metric_unit: str, to_metric_factor: float) -> float:
    # metric -> imperial = divide by factor; imperial -> metric = multiply by factor
    return metric_value / to_metric_factor


def celsius_to_fahrenheit(c: float) -> float:
    """Convert Celsius to Fahrenheit (explicit offset conversion)."""
    return c * 9.0 / 5.0 + 32.0


def fahrenheit_to_celsius(f: float) -> float:
    """Convert Fahrenheit to Celsius (explicit offset conversion)."""
    return (f - 32.0) * 5.0 / 9.0


def mm_to_inches(mm: float) -> float:
    return mm / 25.4


def inches_to_mm(inches: float) -> float:
    return inches * 25.4


def mps_to_knots(mps: float) -> float:
    return mps / 0.514444


def knots_to_mps(knots: float) -> float:
    return knots * 0.514444


def km_to_miles(km: float) -> float:
    return km / 1.609344


def miles_to_km(mi: float) -> float:
    return mi * 1.609344


def hpa_to_inhg(hpa: float) -> float:
    return hpa / 33.8639


def inhg_to_hpa(inhg: float) -> float:
    return inhg * 33.8639


CONVERTERS_METRIC_TO_IMPERIAL = {
    "°C": celsius_to_fahrenheit,
    "mm": mm_to_inches,
    "m/s": mps_to_knots,
    "km": km_to_miles,
    "km/h": km_to_miles,
    "hPa": hpa_to_inhg,
}

CONVERTERS_IMPERIAL_TO_METRIC = {
    "°C": fahrenheit_to_celsius,
    "mm": inches_to_mm,
    "m/s": knots_to_mps,
    "km": miles_to_km,
    "km/h": miles_to_km,
    "hPa": inhg_to_hpa,
}

IMPERIAL_UNIT = {
    "°C": "°F",
    "mm": "in",
    "m/s": "knots",
    "km": "mi",
    "km/h": "mph",
    "hPa": "inHg",
}


def convert(value: float, metric_unit: str, to_imperial: bool) -> float:
    """Convert a scalar between metric and imperial presentation units.

    Parameters
    ----------
    value:
        Numeric value in ``metric_unit`` (if ``to_imperial``) or in the imperial
        equivalent (if not ``to_imperial``).
    metric_unit:
        Canonical metric unit ("°C", "mm", "m/s", "km", "km/h", "hPa").
    to_imperial:
        True to convert metric -> imperial, False for imperial -> metric.

    Raises
    ------
    KeyError
        If ``metric_unit`` is not a supported conversion.
    """
    if to_imperial:
        fn = CONVERTERS_METRIC_TO_IMPERIAL.get(metric_unit)
    else:
        fn = CONVERTERS_IMPERIAL_TO_METRIC.get(metric_unit)
    if fn is None:
        raise KeyError(f"Unsupported unit for conversion: {metric_unit!r}")
    return fn(value)


def display_unit(metric_unit: str, imperial: bool) -> str:
    """Return the presentation unit label for a metric unit."""
    return IMPERIAL_UNIT.get(metric_unit, metric_unit) if imperial else metric_unit
