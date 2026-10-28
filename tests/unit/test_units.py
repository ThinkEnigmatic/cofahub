"""Unit-conversion tests."""

from __future__ import annotations

import math

import pytest

from cofa_forward.units import (
    celsius_to_fahrenheit,
    convert,
    display_unit,
    fahrenheit_to_celsius,
    km_to_miles,
    mm_to_inches,
    mps_to_knots,
)


def test_celsius_fahrenheit_roundtrip():
    assert math.isclose(fahrenheit_to_celsius(celsius_to_fahrenheit(25.0)), 25.0)
    assert math.isclose(celsius_to_fahrenheit(0.0), 32.0)
    assert math.isclose(celsius_to_fahrenheit(100.0), 212.0)


def test_known_conversions():
    assert math.isclose(mm_to_inches(25.4), 1.0)
    assert math.isclose(km_to_miles(1.609344), 1.0)
    assert math.isclose(mps_to_knots(0.514444), 1.0, rel_tol=1e-5)


def test_convert_metric_to_imperial():
    assert math.isclose(convert(25.0, "°C", True), 77.0)
    assert math.isclose(convert(10.0, "m/s", True), 19.438, rel_tol=1e-3)


def test_convert_imperial_to_metric():
    assert math.isclose(convert(77.0, "°C", False), 25.0)


def test_display_unit():
    assert display_unit("°C", True) == "°F"
    assert display_unit("m/s", True) == "knots"
    assert display_unit("mm", False) == "mm"


def test_unsupported_unit_raises():
    with pytest.raises(KeyError):
        convert(1.0, "parsecs", True)
